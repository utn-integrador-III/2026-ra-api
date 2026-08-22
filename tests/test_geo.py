from app.utils.geo import haversine_m, bearing_deg, turn_angle, distance_text


def test_haversine_zero_for_same_point():
    assert haversine_m(9.93, -84.08, 9.93, -84.08) == 0


def test_haversine_matches_known_distance():
    d = haversine_m(9.9300, -84.0800, 9.9310, -84.0800)
    assert 100 < d < 120


def test_bearing_north_and_east():
    assert bearing_deg(0, 0, 1, 0) == 0
    east = bearing_deg(0, 0, 0, 1)
    assert 89 < east < 91


def test_turn_angle_signs():
    assert turn_angle(90, 180) > 0
    assert turn_angle(90, 0) < 0
    assert turn_angle(10, 10) == 0


def test_distance_text_meters_and_km():
    assert distance_text(250) == "250 m"
    assert distance_text(1500) == "1.5 km"
