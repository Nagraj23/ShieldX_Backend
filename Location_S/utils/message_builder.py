def build_location_message(
    username: str,
    lat: float,
    lng: float,
    reason: str
) -> str:
    """
    Builds a user-friendly message based on the location reason.
    """
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"

    if reason == "SOS":
        return (
            f"🚨 SOS ALERT!\n"
            f"{username} needs immediate help.\n"
            f"📍 Location: {maps_link}"
        )

    if reason == "LOCATION_SHARE":
        return (
            f"📍 Location Shared\n"
            f"{username} shared their location.\n"
            f"📍 {maps_link}"
        )

    if reason == "JOURNEY_START":
        return (
            f"🧭 Journey Started\n"
            f"{username} has started their journey.\n"
            f"📍 Starting point: {maps_link}"
        )

    if reason == "JOURNEY_UPDATE":
        # Usually silent / no notification
        return (
            f"🧭 Journey Update\n"
            f"{username}'s current location:\n"
            f"{maps_link}"
        )

    if reason == "JOURNEY_END":
        return (
            f"🛑 Journey Ended\n"
            f"{username} has completed their journey.\n"
            f"📍 Last location: {maps_link}"
        )

    # Fallback (should never happen due to validation)
    return f"{username} location update: {maps_link}"
