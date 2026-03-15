def create_defender_ta():
    TRUE_FUNC = lambda *args, **kwargs: True

    def normalize_angle(angle):
        while angle > 180: angle -= 360
        while angle < -180: angle += 360
        return angle

    def update_timers(*keys):
        def func(mgr, s):
            for key in keys:
                s[key] = mgr.time_cycle
        return func

    # ── Условия ──────────────────────────────────────────

    def ball_not_visible(mgr, s):
        return not mgr.getVisible("b")

    def ball_visible(mgr, s):
        return mgr.getVisible("b")

    def ball_kickable(mgr, s):
        return mgr.getVisible("b") and mgr.getDistance("b") <= 1

    def ball_very_dangerous(mgr, s):
        return mgr.getVisible("b") and mgr.getDistance("b") <= 10

    def ball_dangerous(mgr, s):
        return mgr.getVisible("b") and mgr.getDistance("b") <= 20

    def ball_safe(mgr, s):
        return mgr.getVisible("b") and mgr.getDistance("b") > 20

    def can_see_own_goal(mgr, s):
        return mgr.getVisible(mgr.own_goal_key())

    def near_own_goal(mgr, s):
        goal = mgr.own_goal_key()
        if not mgr.getVisible(goal):
            return False
        dist = mgr.getDistance(goal)
        return 5 <= dist <= 18

    def too_far_from_goal(mgr, s):
        goal = mgr.own_goal_key()
        if not mgr.getVisible(goal):
            return True
        return mgr.getDistance(goal) > 25

    def too_close_to_goal(mgr, s):
        goal = mgr.own_goal_key()
        return mgr.getVisible(goal) and mgr.getDistance(goal) < 4

    def teammate_too_close(mgr, s):
        closest = mgr.getClosestTeammate()
        return closest is not None and closest[1].get("dist", 9999) < 5

    def i_am_closer_to_ball(mgr, s):
        return not mgr.teammate_is_closer_to_ball()

    def teammate_closer_to_ball(mgr, s):
        return mgr.teammate_is_closer_to_ball()

    def ball_dangerous_and_i_closer(mgr, s):
        return ball_dangerous(mgr, s) and i_am_closer_to_ball(mgr, s)

    def ball_dangerous_and_teammate_closer(mgr, s):
        return ball_dangerous(mgr, s) and teammate_closer_to_ball(mgr, s)

    def ball_very_dangerous_and_i_closer(mgr, s):
        return ball_very_dangerous(mgr, s) and i_am_closer_to_ball(mgr, s)

    def ball_very_dangerous_and_teammate_closer(mgr, s):
        return ball_very_dangerous(mgr, s) and teammate_closer_to_ball(mgr, s)

    # ── Действия ─────────────────────────────────────────

    def search_spin(mgr, s):
        return ("turn", "50")

    def scan_for_ball(mgr, s):
        """Ищем мяч — поворачиваемся шагами по 40°"""
        s['scan_count'] = s.get('scan_count', 0) + 1
        return ("turn", "40")

    def watch_ball(mgr, s):
        """Активно следим за мячом — поворачиваемся к нему"""
        s['scan_count'] = 0
        if not mgr.getVisible("b"):
            return ("turn", "40")
        angle = mgr.getAngle("b")
        dist = mgr.getDistance("b")
        if abs(angle) > 5:
            return ("turn", str(int(angle)))
        # Смотрим на мяч — стоим, но если мяч далеко,
        # чуть подаёмся вперёд чтобы быть готовым
        if dist > 25:
            return ("dash", "15")
        return ("turn", "2")

    def go_to_goal_area(mgr, s):
        goal = mgr.own_goal_key()
        if not mgr.getVisible(goal):
            return ("turn", "50")

        angle = mgr.getAngle(goal)
        dist = mgr.getDistance(goal)

        if dist > 18:
            if abs(angle) > 10:
                return ("turn", str(int(angle)))
            return ("dash", "100")

        if dist > 12:
            if abs(angle) > 10:
                return ("turn", str(int(angle)))
            return ("dash", "70")

        if dist > 5:
            zone_offset = -12 if mgr.is_upper_defender() else 12
            return ("turn", str(zone_offset))

        away = normalize_angle(angle + 180)
        if abs(away) < 30:
            return ("dash", "40")
        return ("turn", str(int(away)))

    def move_away_from_teammate(mgr, s):
        closest = mgr.getClosestTeammate()
        if closest:
            teammate_dir = closest[1].get("dir", 0)
            away = normalize_angle(teammate_dir + 180)
            if abs(away) < 30:
                return ("dash", "50")
            return ("turn", str(int(away)))
        offset = -20 if mgr.is_upper_defender() else 20
        return ("turn", str(offset))

    def intercept_ball(mgr, s):
        if not mgr.getVisible("b"):
            return ("turn", "30")
        angle = mgr.getAngle("b")
        dist = mgr.getDistance("b")
        if abs(angle) > 10:
            return ("turn", str(int(angle)))
        if dist > 5:
            return ("dash", "100")
        elif dist > 2:
            return ("dash", "80")
        return ("dash", "60")

    def clear_ball(mgr, s):
        enemy_goal = mgr.enemy_goal_key()
        own_goal = mgr.own_goal_key()

        if mgr.getVisible(enemy_goal):
            return ("kick", f"100 {int(mgr.getAngle(enemy_goal))}")

        closest = mgr.getClosestTeammate()
        if closest:
            key, obj = closest
            angle = int(obj.get("dir", 0))
            dist = obj.get("dist", 10)
            power = min(100, int(dist * 5) + 30)
            return ("kick", f"{power} {angle}")

        if mgr.getVisible(own_goal):
            away = normalize_angle(mgr.getAngle(own_goal) + 180)
            return ("kick", f"100 {int(away)}")

        return ("kick", "100 0")

    def hold_and_watch(mgr, s):
        if mgr.getVisible("b"):
            angle = mgr.getAngle("b")
            if abs(angle) > 8:
                return ("turn", str(int(angle)))
            dist = mgr.getDistance("b")
            if dist > 15:
                return ("dash", "30")
            return ("turn", "2")
        return ("turn", "25")

    # ── Автомат ──────────────────────────────────────────

    ta = {
        '__start__': 'find_goal',

        # ═══ Ищем ворота ════════════════════════════════
        'find_goal': [
            (ball_kickable, clear_ball, 'find_goal'),
            (can_see_own_goal, go_to_goal_area, 'go_to_position'),
            (TRUE_FUNC, search_spin, 'find_goal'),
        ],

        # ═══ Идём на позицию ════════════════════════════
        'go_to_position': [
            (ball_kickable, clear_ball, 'go_to_position'),
            (ball_very_dangerous, intercept_ball, 'intercept'),
            (near_own_goal, watch_ball, 'on_position'),
            (teammate_too_close, move_away_from_teammate, 'go_to_position'),
            (TRUE_FUNC, go_to_goal_area, 'go_to_position'),
        ],

        # ═══ На позиции ═════════════════════════════════
        # Приоритет: 1) мяч у ног  2) опасность  3) наблюдение  4) поиск  5) позиция
        'on_position': [
            # 1. Мяч у ног — выбиваем
            (ball_kickable, clear_ball, 'on_position'),

            # 2. Мяч очень опасно — оба бегут
            (ball_very_dangerous_and_i_closer, intercept_ball, 'intercept'),
            (ball_very_dangerous_and_teammate_closer, intercept_ball, 'intercept'),

            # 3. Мяч опасно — ближний бежит, дальний страхует
            (ball_dangerous_and_i_closer, intercept_ball, 'intercept'),
            (ball_dangerous_and_teammate_closer, hold_and_watch, 'cover'),

            # 4. Мяч виден и безопасен — СЛЕДИМ ЗА НИМ
            (ball_safe, watch_ball, 'on_position'),

            # 5. Мяч виден (среднее расстояние) — следим
            (ball_visible, watch_ball, 'on_position'),

            # 6. Мяч НЕ виден — ИЩЕМ ЕГО (крутимся)
            (ball_not_visible, scan_for_ball, 'search_ball_on_position'),

            # 7. Ничего — на всякий случай
            (TRUE_FUNC, scan_for_ball, 'search_ball_on_position'),
        ],

        # ═══ Ищем мяч находясь на позиции ═══════════════
        # Отдельное состояние чтобы не путать с наблюдением
        'search_ball_on_position': [
            (ball_kickable, clear_ball, 'on_position'),
            (ball_very_dangerous, intercept_ball, 'intercept'),
            (ball_dangerous_and_i_closer, intercept_ball, 'intercept'),

            # Нашли мяч — возвращаемся к наблюдению
            (ball_visible, watch_ball, 'on_position'),

            # Долго ищем (>9 поворотов = 360°) — проверяем позицию
            (
                lambda mgr, s: s.get('scan_count', 0) > 9,
                search_spin,
                'check_position',
            ),

            # Продолжаем искать
            (TRUE_FUNC, scan_for_ball, 'search_ball_on_position'),
        ],

        # ═══ Проверяем что не уплыли с позиции ══════════
        'check_position': [
            (ball_kickable, clear_ball, 'check_position'),
            (ball_very_dangerous, intercept_ball, 'intercept'),
            (ball_visible, watch_ball, 'on_position'),
            (too_far_from_goal, search_spin, 'find_goal'),
            (teammate_too_close, move_away_from_teammate, 'on_position'),
            (too_close_to_goal, lambda mgr, s: ("dash", "30"), 'on_position'),
            # Всё ок — обратно наблюдать
            (TRUE_FUNC, scan_for_ball, 'search_ball_on_position'),
        ],

        # ═══ Перехватываю мяч ════════════════════════════
        'intercept': [
            (ball_kickable, clear_ball, 'return_to_position'),

            (
                lambda mgr, s: ball_visible(mgr, s) and mgr.getDistance("b") > 30,
                watch_ball,
                'return_to_position',
            ),

            (
                lambda mgr, s: too_far_from_goal(mgr, s) and not ball_very_dangerous(mgr, s),
                search_spin,
                'return_to_position',
            ),

            (
                lambda mgr, s: teammate_too_close(mgr, s) and teammate_closer_to_ball(mgr, s),
                hold_and_watch,
                'cover',
            ),

            (ball_visible, intercept_ball, 'intercept'),
            (TRUE_FUNC, scan_for_ball, 'intercept'),
        ],

        # ═══ Страхую ════════════════════════════════════
        'cover': [
            (ball_kickable, clear_ball, 'return_to_position'),

            (
                lambda mgr, s: ball_very_dangerous(mgr, s) and i_am_closer_to_ball(mgr, s),
                intercept_ball,
                'intercept',
            ),

            (
                lambda mgr, s: not ball_dangerous(mgr, s),
                watch_ball,
                'return_to_position',
            ),

            (teammate_too_close, move_away_from_teammate, 'cover'),
            (TRUE_FUNC, hold_and_watch, 'cover'),
        ],

        # ═══ Возвращаюсь на позицию ═════════════════════
        'return_to_position': [
            (ball_kickable, clear_ball, 'return_to_position'),
            (ball_very_dangerous, intercept_ball, 'intercept'),
            (near_own_goal, watch_ball, 'on_position'),
            (can_see_own_goal, go_to_goal_area, 'return_to_position'),
            (TRUE_FUNC, search_spin, 'find_goal'),
        ],
    }

    return ta
