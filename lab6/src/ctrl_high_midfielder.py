# ===== FILE: src/ctrl_high_midfielder.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighMidfielder(HierarchicalController):
    """
    Верхний уровень для полузащитника:
    - Если мяч рядом — пас вперёд или ведение
    - Если мяч в зоне досягаемости и нет ближайшего тиммейта — перехват
    - Координация: не бежать к мячу если кто-то ближе
    """

    def __init__(self, side, home_pos, zone="center"):
        super().__init__()
        self.side = side
        self.home_pos = home_pos
        self.zone = zone  # "center", "left", "right"
        self.last_action = None

    def process(self, input_data):
        # Мяч рядом — ударить
        if input_data.get("can_kick"):
            self.last_action = "kick"
            goal_opp = input_data.get("goal_opp")
            teammates = input_data.get("teammates", [])

            # Если видим ворота и близко — бить
            if goal_opp and goal_opp.get("dist", 9999) < 25:
                angle = goal_opp.get("dir", 0)
                return ("kick", f"100 {int(angle)}")

            # Ищем тиммейта ближе к воротам для паса
            if teammates:
                best = None
                for t in teammates:
                    if best is None or t.get("dist", 9999) < best.get("dist", 9999):
                        best = t
                if best:
                    angle = best.get("dir", 0)
                    dist = best.get("dist", 10)
                    power = min(100, int(dist * 3 + 30))
                    return ("kick", f"{power} {int(angle)}")

            if goal_opp:
                angle = goal_opp.get("dir", 0)
                return ("kick", f"70 {int(angle)}")

            return ("kick", "30 0")

        # Мяч виден — решаем, бежать ли за ним
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            teammates = input_data.get("teammates", [])

            # Проверяем, есть ли тиммейт ближе к мячу
            am_closest = True
            for t in teammates:
                t_dist = t.get("dist", 9999)
                # Грубая оценка: если тиммейт сильно ближе к мячу
                if t_dist < ball_dist - 5:
                    am_closest = False
                    break

            if am_closest and ball_dist < 25:
                self.last_action = "go_ball"
                return {"new_action": "go_to_ball"}

        # Вернуться на позицию
        if self.last_action in ("go_ball", "kick"):
            self.last_action = None
            return {"new_action": "return_home"}

        return None