import heapq
import math
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session

from app.models.sidewalk_model import SidewalkNode, SidewalkEdge
from app.utils.geo import haversine_m, bearing_deg, turn_angle

# A partir de este ángulo (grados) una unión entre dos tramos se anuncia
# como giro; por debajo se considera "seguir recto".
TURN_THRESHOLD_DEG = 30

# Distancia máxima (m) para "enganchar" un origen/destino a la acera
# caminable más cercana. Si no hay ninguna dentro de este radio, no se
# puede armar una ruta guiada por el grafo.
MAX_SNAP_DISTANCE_M = 120

# Por debajo de esto no vale la pena agregar un punto extra al polyline
# (el origen/destino ya está prácticamente sobre la acera).
MIN_OFFPATH_POINT_M = 1.0

WALKING_SPEED_MPS = 1.3  # ~80 m/min, mismo supuesto que usa el frontend

VIRTUAL_START = "__origin__"
VIRTUAL_END = "__destination__"


class NoWalkableRouteError(Exception):
    """No existe (o no se puede alcanzar) un camino caminable entre origen y destino."""
    pass


@dataclass
class RouteStep:
    instruction: str
    turn: str  # 'start' | 'straight' | 'left' | 'right' | 'arrive'
    lat: float
    lng: float
    distance_to_next_m: float


@dataclass
class RouteResult:
    points: list  # [{lat, lng}, ...] en orden, incluye origen y destino reales
    steps: list  # list[RouteStep]
    distance_m: float
    duration_s: float


@dataclass
class SnapResult:
    perp_m: float  # distancia perpendicular desde el punto real hasta la acera
    lat: float  # punto proyectado sobre la acera
    lng: float
    edge: SidewalkEdge
    dist_to_a: float  # distancia a lo largo de la arista, desde la proyección hasta node_a
    dist_to_b: float  # ídem hasta node_b
    t: float  # 0..1, posición de la proyección entre node_a (0) y node_b (1)


def _build_graph(db: Session):
    nodes = {n.id: n for n in db.query(SidewalkNode).filter(SidewalkNode.is_active == True).all()}
    edges = [
        e for e in db.query(SidewalkEdge).filter(SidewalkEdge.is_active == True).all()
        if e.node_a_id in nodes and e.node_b_id in nodes
    ]

    adjacency: dict[str, list[tuple[str, float]]] = {nid: [] for nid in nodes}
    for e in edges:
        adjacency[e.node_a_id].append((e.node_b_id, e.distance_m))
        adjacency[e.node_b_id].append((e.node_a_id, e.distance_m))

    return nodes, edges, adjacency


def _snap_to_graph(nodes: dict, edges: list, lat: float, lng: float) -> Optional[SnapResult]:
    """Proyecta (lat, lng) sobre la arista caminable más cercana (no sobre
    el nodo más cercano). Así, dos lecturas de GPS a ambos lados de un
    mismo tramo dan el mismo punto de enganche en vez de saltar entre
    los nodos de los extremos con cada ligero movimiento/ruido del GPS.

    Usa una proyección plana local (equirectangular) — suficientemente
    precisa para las distancias cortas (decenas/cientos de metros) que
    maneja este grafo."""
    if not edges:
        return None

    cos_lat0 = math.cos(math.radians(lat))

    def to_xy(plat: float, plng: float) -> tuple[float, float]:
        return ((plng - lng) * cos_lat0 * 111320.0, (plat - lat) * 110540.0)

    best: Optional[SnapResult] = None

    for edge in edges:
        a, b = nodes[edge.node_a_id], nodes[edge.node_b_id]
        ax, ay = to_xy(a.latitude, a.longitude)
        bx, by = to_xy(b.latitude, b.longitude)
        abx, aby = bx - ax, by - ay
        ab2 = abx * abx + aby * aby

        t = 0.0 if ab2 == 0 else max(0.0, min(1.0, (-ax * abx + -ay * aby) / ab2))
        projx, projy = ax + t * abx, ay + t * aby
        perp = math.hypot(projx, projy)

        if best is None or perp < best.perp_m:
            proj_lat = lat + projy / 110540.0
            proj_lng = lng + projx / (cos_lat0 * 111320.0)
            best = SnapResult(
                perp_m=perp, lat=proj_lat, lng=proj_lng, edge=edge,
                dist_to_a=t * edge.distance_m, dist_to_b=(1 - t) * edge.distance_m, t=t,
            )

    return best


def _dijkstra(adjacency: dict, start_id: str, end_id: str) -> tuple[list, float]:
    dist = {start_id: 0.0}
    prev = {}
    visited = set()
    pq = [(0.0, start_id)]

    while pq:
        d, node_id = heapq.heappop(pq)
        if node_id in visited:
            continue
        visited.add(node_id)
        if node_id == end_id:
            break
        for neighbor_id, weight in adjacency.get(node_id, []):
            nd = d + weight
            if nd < dist.get(neighbor_id, float("inf")):
                dist[neighbor_id] = nd
                prev[neighbor_id] = node_id
                heapq.heappush(pq, (nd, neighbor_id))

    if end_id not in dist:
        return [], float("inf")

    path = [end_id]
    while path[-1] != start_id:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[end_id]


def _build_steps(points: list) -> list:
    """points: lista de dicts {lat, lng}. Genera instrucciones de giro
    comparando el rumbo del tramo entrante contra el saliente en cada
    punto intermedio."""
    steps = []
    n = len(points)

    if n < 2:
        return steps

    segment_dist = [
        haversine_m(points[i]["lat"], points[i]["lng"], points[i + 1]["lat"], points[i + 1]["lng"])
        for i in range(n - 1)
    ]

    steps.append(RouteStep(
        instruction="Iniciá la ruta",
        turn="start",
        lat=points[0]["lat"], lng=points[0]["lng"],
        distance_to_next_m=round(segment_dist[0]),
    ))

    for i in range(1, n - 1):
        bearing_in = bearing_deg(points[i - 1]["lat"], points[i - 1]["lng"], points[i]["lat"], points[i]["lng"])
        bearing_out = bearing_deg(points[i]["lat"], points[i]["lng"], points[i + 1]["lat"], points[i + 1]["lng"])
        angle = turn_angle(bearing_in, bearing_out)

        if angle > TURN_THRESHOLD_DEG:
            turn, instruction = "right", "Girá a la derecha"
        elif angle < -TURN_THRESHOLD_DEG:
            turn, instruction = "left", "Girá a la izquierda"
        else:
            turn, instruction = "straight", "Continuá recto"

        steps.append(RouteStep(
            instruction=instruction,
            turn=turn,
            lat=points[i]["lat"], lng=points[i]["lng"],
            distance_to_next_m=round(segment_dist[i]),
        ))

    steps.append(RouteStep(
        instruction="Llegaste a tu destino",
        turn="arrive",
        lat=points[-1]["lat"], lng=points[-1]["lng"],
        distance_to_next_m=0,
    ))

    return steps


def compute_route(
    db: Session, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float,
    walking_speed_mps: float = WALKING_SPEED_MPS,
) -> RouteResult:
    nodes, edges, adjacency = _build_graph(db)

    if not nodes or not edges:
        raise NoWalkableRouteError("No hay aceras registradas todavía")

    start_snap = _snap_to_graph(nodes, edges, origin_lat, origin_lng)
    end_snap = _snap_to_graph(nodes, edges, dest_lat, dest_lng)

    if start_snap.perp_m > MAX_SNAP_DISTANCE_M or end_snap.perp_m > MAX_SNAP_DISTANCE_M:
        raise NoWalkableRouteError("El origen o el destino están demasiado lejos de una acera conocida")

    # Grafo aumentado con dos nodos virtuales (origen/destino) enganchados
    # sobre su acera más cercana — se descarta después de esta consulta.
    graph = {nid: list(neigh) for nid, neigh in adjacency.items()}
    graph[VIRTUAL_START] = []
    graph[VIRTUAL_END] = []

    def _link_virtual(vid: str, snap: SnapResult):
        a_id, b_id = snap.edge.node_a_id, snap.edge.node_b_id
        graph[vid].append((a_id, snap.dist_to_a))
        graph[a_id].append((vid, snap.dist_to_a))
        graph[vid].append((b_id, snap.dist_to_b))
        graph[b_id].append((vid, snap.dist_to_b))

    _link_virtual(VIRTUAL_START, start_snap)
    _link_virtual(VIRTUAL_END, end_snap)

    # Si origen y destino cayeron sobre la misma acera, conectarlos directo
    # (si no, Dijkstra los haría "ir y volver" por uno de los extremos).
    if start_snap.edge.id == end_snap.edge.id:
        direct = abs(start_snap.t - end_snap.t) * start_snap.edge.distance_m
        graph[VIRTUAL_START].append((VIRTUAL_END, direct))
        graph[VIRTUAL_END].append((VIRTUAL_START, direct))

    path_ids, graph_distance = _dijkstra(graph, VIRTUAL_START, VIRTUAL_END)
    if not path_ids:
        raise NoWalkableRouteError("No hay un camino caminable entre origen y destino")

    points = [{"lat": origin_lat, "lng": origin_lng}]
    if start_snap.perp_m > MIN_OFFPATH_POINT_M:
        points.append({"lat": start_snap.lat, "lng": start_snap.lng})

    for nid in path_ids[1:-1]:  # sin los extremos virtuales
        node = nodes[nid]
        points.append({"lat": node.latitude, "lng": node.longitude})

    if end_snap.perp_m > MIN_OFFPATH_POINT_M:
        points.append({"lat": end_snap.lat, "lng": end_snap.lng})
    points.append({"lat": dest_lat, "lng": dest_lng})

    total_distance = start_snap.perp_m + graph_distance + end_snap.perp_m
    steps = _build_steps(points)

    return RouteResult(
        points=points,
        steps=steps,
        distance_m=round(total_distance, 1),
        duration_s=round(total_distance / walking_speed_mps),
    )
