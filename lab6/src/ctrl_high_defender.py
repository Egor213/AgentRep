# ===== FILE: src/ctrl_high_defender.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighDefender(HierarchicalController):
    """
    Верхний уровень — защитник:
    - Мяч рядом → отбить / пас тиммейту
    - Мяч видим и близко (< 15) → перехватить
    - Иначе → держать позицию у своего флага
    """

    def __init__(self, side, home_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — отбить
        if input_data.get("can_kick"):
            self.last = "kick"
            goal_opp = input_data.get("goal_opp")
            teammates = input_data.get("teammates", [])

            if teammates:
                best = min(teammates, key=lambda t: t.get("dist", 9999))
                angle = best.get("dir", 0)
                dist = best.get("dist", 10)
                power = min(100, int(dist * 3 + 30))
                return ("kick", f"{power} {int(angle)}")

            if goal_opp:
                return ("kick", f"80 {int(goal_opp.get('dir', 0))}")
            return ("kick", "50 0")

        # 2. Мяч видим и близко — перехватить
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)

            # Защитник бежит только если мяч рядом (< 15)
            # И нет тиммейта который ещё ближе
            if ball_dist < 15:
                teammates = input_data.get("teammates", [])
                am_closest = True
                for t in teammates:
                    if t.get("dist", 9999) < ball_dist - 3:
                        am_closest = False
                        break
                if am_closest:
                    self.last = "defend"
                    return {"new_action": "go_to_ball"}

        # 3. Вернуться на позицию
        if self.last in ("defend", "kick"):
            self.last = None
            return {"new_action": "return_home"}

        return None