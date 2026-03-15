# ===== FILE: src/ctrl_high_defender.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighDefender(HierarchicalController):
    """
    Верхний уровень для защитника:
    - Если мяч рядом — отбить в сторону чужих ворот или вперёд
    - Если мяч на своей половине и близко — перехватить
    - Иначе — держать позицию
    """

    def __init__(self, side, home_pos):
        super().__init__()
        self.side = side
        self.home_pos = home_pos
        self.last_action = None

    def process(self, input_data):
        # Немедленная реакция: мяч рядом
        if input_data.get("can_kick"):
            self.last_action = "kick"
            goal_opp = input_data.get("goal_opp")
            # Ищем тиммейта для паса
            teammates = input_data.get("teammates", [])
            if teammates:
                # Пас ближайшему тиммейту
                closest = min(teammates, key=lambda t: t.get("dist", 9999))
                angle = closest.get("dir", 0)
                dist = closest.get("dist", 10)
                power = min(100, int(dist * 3 + 30))
                return ("kick", f"{power} {int(angle)}")
            if goal_opp:
                angle = goal_opp.get("dir", 0)
                return ("kick", f"80 {int(angle)}")
            return ("kick", "40 0")

        # Мяч на своей половине — перехватить
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            x = input_data.get("x")
            hx = self.home_pos[0]

            # Определяем, на своей ли половине мяч
            on_own_half = True
            if x is not None:
                if self.side == "l" and x > 5:
                    on_own_half = False
                elif self.side == "r" and x < -5:
                    on_own_half = False

            if ball_dist < 20 and on_own_half:
                self.last_action = "defend"
                return {"new_action": "go_to_ball"}

        # Вернуться на позицию
        if self.last_action == "defend":
            self.last_action = None
            return {"new_action": "return_home"}

        return None