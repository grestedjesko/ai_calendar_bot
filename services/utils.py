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


def ru_plural(n: int, forms: tuple[str, str, str]) -> str:
    # формы: (минута, минуты, минут) / (час, часа, часов) / (день, дня, дней)
    n_abs = abs(n) % 100
    n1 = n_abs % 10
    if 11 <= n_abs <= 19:
        return forms[2]
    if 2 <= n1 <= 4:
        return forms[1]
    if n1 == 1:
        return forms[0]
    return forms[2]

def format_offset(minutes: int) -> str:
    if minutes == 0:
        return "в момент начала"
    # дни / часы / минуты
    if minutes % 1440 == 0:
        d = minutes // 1440
        return f"за {d} {ru_plural(d, ('день', 'дня', 'дней'))}"
    if minutes % 60 == 0 and minutes >= 60:
        h = minutes // 60
        return f"за {h} {ru_plural(h, ('час', 'часа', 'часов'))}"
    return f"за {minutes} {ru_plural(minutes, ('минуту', 'минуты', 'минут'))}"

def humanize_reminders(items: list[int]) -> str:
    parts = [format_offset(int(x)) for x in sorted(set(items))]
    if not parts:
        return "за 30 минут и за 5 минут до начала"   # запасной текст
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " и " + parts[-1]