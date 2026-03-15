# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Верхний уровень — вратарь:
    - Мяч рядом → отбить (в сторону чужих ворот или вбок)
    - Мяч видим и близко → бросок к мячу
    - Иначе → вернуться к воротам, обзор
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — отбить
        if input_data.get("can_kick"):
            self.last = "kick"
            goal_opp = input_data.get("goal_opp")
            teammates = input_data.get("teammates", [])
            # Пас тиммейту если есть
            if teammates:
                best = min(teammates, key=lambda t: t.get("dist", 9999))
                angle = best.get("dir", 0)
                dist = best.get("dist", 10)
                power = min(100, int(dist * 4 + 30))
                return ("kick", f"{power} {int(angle)}")
            if goal_opp:
                return ("kick", f"100 {int(goal_opp.get('dir', 0))}")
            return ("kick", "60 45")

        # 2. Мяч близко — бежать к нему
        ball = input_data.get("ball")
        if ball and ball.get("dist", 9999) < 25:
            self.last = "defend"
            return {"new_action": "go_to_ball"}

        # 3. После защиты — вернуться
        if self.last == "defend":
            self.last = None
            return {"new_action": "return_home"}

        return None