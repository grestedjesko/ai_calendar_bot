def format_duration(duration: int) -> str:
    total_minutes = int(duration // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    result = []

    if hours > 0:
        result.append(f"{hours} ч")
    if minutes > 0:
        result.append(f"{minutes} мин")

    return " ".join(result)