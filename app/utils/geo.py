import math

EARTH_RADIUS_M = 6371000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos coordenadas GPS (línea recta)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def distance_text(meters: float) -> str:
    if meters < 1000:
        return f"{int(meters)} m"
    return f"{meters / 1000:.1f} km"


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Rumbo inicial en grados (0-360, 0=norte, 90=este) para ir de punto 1 a punto 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def turn_angle(bearing_in: float, bearing_out: float) -> float:
    """Diferencia angular con signo entre dos rumbos, en (-180, 180].
    Positivo = giro a la derecha, negativo = giro a la izquierda."""
    diff = (bearing_out - bearing_in + 180) % 360 - 180
    return diff
