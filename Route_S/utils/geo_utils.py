from math import radians, sin, cos, sqrt, atan2

EARTH_RADIUS = 6371000  # Earth radius in meters


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the distance between two GPS coordinates in meters.
    """

    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(d_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS * c


def has_user_moved(
    previous_lat: float,
    previous_lng: float,
    current_lat: float,
    current_lng: float,
    threshold: float = 10
) -> bool:
    """
    Returns True if user moved more than threshold (meters).
    """

    distance = haversine_distance(
        previous_lat,
        previous_lng,
        current_lat,
        current_lng,
    )

    return distance >= threshold


def is_valid_coordinate(lat: float, lng: float) -> bool:
    """
    Validate latitude and longitude.
    """

    return (
        -90 <= lat <= 90
        and -180 <= lng <= 180
    )