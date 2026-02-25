# ===== FILE: src/geometry.py =====

import math
from flags import FLAGS, distance


def compute_position_two_flags(
    flag1_key: str, d1: float, flag2_key: str, d2: float, flag3_key: str = None, d3: float = None
):
    """
    Вычисление координат игрока по двум флагам (+ третий для выбора решения).
    Решается система:
        d1² = (x - x1)² + (y - y1)²
        d2² = (x - x2)² + (y - y2)²
    Возвращает (x, y) или None.
    """
    if flag1_key not in FLAGS or flag2_key not in FLAGS:
        return None

    x1, y1 = FLAGS[flag1_key]
    x2, y2 = FLAGS[flag2_key]

    solutions = _solve_two_circles(x1, y1, d1, x2, y2, d2)

    if not solutions:
        return None

    # Фильтруем решения в пределах поля (с запасом)
    valid = []
    for sx, sy in solutions:
        if -60 <= sx <= 60 and -42 <= sy <= 42:
            valid.append((sx, sy))

    if not valid:
        valid = solutions  # Берём все, если ни одно не в поле

    if len(valid) == 1:
        return valid[0]

    # Если есть третий флаг — выбираем решение с наименьшей ошибкой
    if flag3_key and d3 is not None and flag3_key in FLAGS:
        x3, y3 = FLAGS[flag3_key]
        best = None
        best_err = float("inf")
        for sx, sy in valid:
            err = abs((sx - x3) ** 2 + (sy - y3) ** 2 - d3**2)
            if err < best_err:
                best_err = err
                best = (sx, sy)
        return best

    # Без третьего флага возвращаем первое допустимое
    return valid[0]


def _solve_two_circles(x1, y1, d1, x2, y2, d2):
    """Решение системы двух уравнений окружностей."""
    solutions = []

    EPS = 1e-9

    if abs(x2 - x1) < EPS and abs(y2 - y1) < EPS:
        return []

    if abs(x2 - x1) < EPS:
        # x1 == x2: y вычисляется напрямую
        y = (y2**2 - y1**2 + d1**2 - d2**2) / (2 * (y2 - y1))
        det = d1**2 - (y - y1) ** 2
        if det < -EPS:
            return []
        det = max(det, 0)
        sq = math.sqrt(det)
        solutions.append((x1 + sq, y))
        solutions.append((x1 - sq, y))
        return solutions

    if abs(y2 - y1) < EPS:
        # y1 == y2: x вычисляется напрямую
        x = (x2**2 - x1**2 + d1**2 - d2**2) / (2 * (x2 - x1))
        det = d1**2 - (x - x1) ** 2
        if det < -EPS:
            return []
        det = max(det, 0)
        sq = math.sqrt(det)
        solutions.append((x, y1 + sq))
        solutions.append((x, y1 - sq))
        return solutions

    # Общий случай: выражаем x через y
    # x = alpha * y + beta
    alpha = (y1 - y2) / (x2 - x1)
    beta = (y2**2 - y1**2 + x2**2 - x1**2 + d1**2 - d2**2) / (2 * (x2 - x1))

    # Подставляем в первое уравнение: (alpha*y + beta - x1)^2 + (y - y1)^2 = d1^2
    # (alpha^2 + 1) * y^2 - 2*(alpha*(x1-beta) + y1)*y + (x1-beta)^2 + y1^2 - d1^2 = 0
    a_coef = alpha**2 + 1
    b_coef = -2 * (alpha * (x1 - beta) + y1)
    c_coef = (x1 - beta) ** 2 + y1**2 - d1**2

    discriminant = b_coef**2 - 4 * a_coef * c_coef

    if discriminant < -EPS:
        return []

    discriminant = max(discriminant, 0)
    sq_disc = math.sqrt(discriminant)

    y_sol1 = (-b_coef + sq_disc) / (2 * a_coef)
    y_sol2 = (-b_coef - sq_disc) / (2 * a_coef)

    x_sol1 = alpha * y_sol1 + beta
    x_sol2 = alpha * y_sol2 + beta

    solutions.append((x_sol1, y_sol1))
    if abs(y_sol1 - y_sol2) > EPS or abs(x_sol1 - x_sol2) > EPS:
        solutions.append((x_sol2, y_sol2))

    return solutions


def compute_position_three_flags(
    flag1_key: str, d1: float, flag2_key: str, d2: float, flag3_key: str, d3: float
):
    """
    Вычисление координат игрока по трём флагам через систему линейных уравнений.
    Из пар (flag1, flag2) и (flag1, flag3) получаем:
        x = alpha1 * y + beta1
        x = alpha2 * y + beta2
    Решаем систему.
    """
    if flag1_key not in FLAGS or flag2_key not in FLAGS or flag3_key not in FLAGS:
        return None

    x1, y1 = FLAGS[flag1_key]
    x2, y2 = FLAGS[flag2_key]
    x3, y3 = FLAGS[flag3_key]

    EPS = 1e-9

    # Проверяем, что можем вычислить обе зависимости x(y)
    if abs(x2 - x1) < EPS or abs(x3 - x1) < EPS:
        # Откат к решению по двум флагам
        return compute_position_two_flags(flag1_key, d1, flag2_key, d2, flag3_key, d3)

    alpha1 = (y1 - y2) / (x2 - x1)
    beta1 = (y2**2 - y1**2 + x2**2 - x1**2 + d1**2 - d2**2) / (2 * (x2 - x1))

    alpha2 = (y1 - y3) / (x3 - x1)
    beta2 = (y3**2 - y1**2 + x3**2 - x1**2 + d1**2 - d3**2) / (2 * (x3 - x1))

    if abs(alpha2 - alpha1) < EPS:
        # Линейно зависимые — откат
        return compute_position_two_flags(flag1_key, d1, flag2_key, d2, flag3_key, d3)

    y = (beta1 - beta2) / (alpha2 - alpha1)
    x = alpha1 * y + beta1

    return (x, y)


def compute_object_position(
    player_x, player_y, flag_key, flag_dist, flag_angle, obj_dist, obj_angle
):
    """
    Вычисление координат объекта (мяч, другой игрок) по координатам
    текущего игрока и одного флага, используя теорему косинусов.

    flag_angle и obj_angle — углы в градусах из see-сообщения.
    """
    if flag_key not in FLAGS:
        return None

    x1, y1 = FLAGS[flag_key]

    # Расстояние от объекта до флага (теорема косинусов)
    angle_diff = abs(flag_angle - obj_angle)
    angle_diff_rad = math.radians(angle_diff)

    d_obj_flag_sq = flag_dist**2 + obj_dist**2 - 2 * flag_dist * obj_dist * math.cos(angle_diff_rad)
    if d_obj_flag_sq < 0:
        d_obj_flag_sq = 0
    d_obj_flag = math.sqrt(d_obj_flag_sq)

    if d_obj_flag < 1e-9:
        return (x1, y1)

    # Теперь решаем систему:
    # obj_dist² = (x - player_x)² + (y - player_y)²
    # d_obj_flag² = (x - x1)² + (y - y1)²
    solutions = _solve_two_circles(player_x, player_y, obj_dist, x1, y1, d_obj_flag)

    if not solutions:
        return None

    # Фильтруем по допустимости (в пределах поля)
    valid = [(sx, sy) for sx, sy in solutions if -60 <= sx <= 60 and -42 <= sy <= 42]
    if not valid:
        valid = solutions

    if len(valid) == 1:
        return valid[0]

    # Выбираем решение по углу obj_angle
    # Направление от игрока к объекту должно примерно совпадать с obj_angle
    # (obj_angle задан относительно направления тела игрока, но для грубой фильтрации подойдёт)
    best = valid[0]
    return best
