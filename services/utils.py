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
    n_abs = abs(n) % 100
    n1 = n_abs % 10
    if 11 <= n_abs <= 19: return forms[2]
    if 2 <= n1 <= 4:      return forms[1]
    if n1 == 1:           return forms[0]
    return forms[2]

def humanize_minutes(m: int) -> str:
    if m % 1440 == 0 and m > 0:
        d = m // 1440
        return f"{d} {ru_plural(d, ('день', 'дня', 'дней'))}"
    if m % 60 == 0 and m >= 60:
        h = m // 60
        return f"{h} {ru_plural(h, ('час', 'часа', 'часов'))}"
    return f"{m} {ru_plural(m, ('минуту', 'минуты', 'минут'))}"

def join_humanized(arr: list[int]) -> str:
    parts = [humanize_minutes(x) for x in sorted(set(arr))]
    if not parts: return ""
    if len(parts) == 1: return parts[0]
    return ", ".join(parts[:-1]) + " и " + parts[-1]



def norm_list(x):
    if isinstance(x, int):
        x = [x]
    if not isinstance(x, list):
        return []
    out = []
    for v in x:
        try:
            iv = int(str(v).replace(',', '.').split('.')[0])  # на всякий случай "3.5" -> "3"
            if iv >= 0:
                out.append(iv)
        except:
            continue
    return sorted(set(out))
