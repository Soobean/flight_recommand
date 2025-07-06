def flight_search_key(*args, **kwargs) -> str:
    request = args[0] if args else kwargs.get("request")
    if not request:
        return "flight_search:unknown"

    return (
        f"flight_search:{request.origin}:{request.destination}:"
        f"{request.departure_date}:{request.return_date}:{request.adults}"
    )


def duration_search_key(*args, **kwargs) -> str:
    request = args[0] if args else kwargs.get("request")
    if not request:
        return "duration_search:unknown"

    return (
        f"duration_search:{request.origin}:{request.destination}:"
        f"{request.departure_date}:{request.duration_days}:{request.adults}"
    )


def cheapest_dates_key(*args, **kwargs) -> str:
    request = args[0] if args else kwargs.get("request")
    if not request:
        return "cheapest_dates:unknown"

    return (
        f"cheapest_dates:{request.origin}:{request.destination}:"
        f"{request.departure_date}:{request.duration}:{request.flexibility_days}"
    )


def airport_info_key(*args, **kwargs) -> str:
    iata_code = args[0] if args else kwargs.get("iata_code")
    if not iata_code:
        return "airport_info:unknown"

    return f"airport_info:{iata_code.upper()}"


def popular_routes_key(*args, **kwargs) -> str:
    origin = kwargs.get("origin", "ICN")
    limit = kwargs.get("limit", 10)

    return f"popular_routes:{origin}:{limit}"
