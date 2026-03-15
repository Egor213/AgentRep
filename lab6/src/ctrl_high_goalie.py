# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Верхний уровень для вратаря:
    - Немедленная реакция: если мяч рядом — отбить
    - Защита ворот: если мяч летит к воротам — бросок
    - Иначе: вернуться к воротам, обзор поля
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last_action = None

    def process(self, input_data):
        # Немедленная реакция
        immediate = self._immediate_reaction(input_data)
        if immediate:
            return immediate

        # Защита ворот
        defend = self._defend_goal(input_data)
        if defend:
            return defend

        # Если закончили защиту — вернуться
        if self.last_action == "defend":
            self.last_action = None
            return {"new_action": "return_home"}

        return None

    def _immediate_reaction(self, data):
        """Мяч рядом — ударить."""
        if data.get("can_kick"):
            self.last_action = "kick"
            goal_opp = data.get("goal_opp")
            if goal_opp:
                angle = goal_opp.get("dir", 0)
                return ("kick", f"100 {int(angle)}")
            return ("kick", "50 45")
        return None

    def _defend_goal(self, data):
        """Мяч видим и близко к воротам — бросок к мячу."""
        ball = data.get("ball")
        if not ball:
            return None

        ball_dist = ball.get("dist", 9999)
        goal_own = data.get("goal_own")

        # Если мяч достаточно близко (< 25) и ближе к нам, чем ближайший оппонент
        if ball_dist < 30:
            closest_opp = data.get("closest_opp_to_ball")
            should_go = False
            if closest_opp is None:
                should_go = True
            elif closest_opp.get("dist", 9999) + 2 > ball_dist:
                should_go = True

            if should_go:
                self.last_action = "defend"
                angle = ball.get("dir", 0)
                if abs(angle) > 5:
                    return ("turn", str(int(angle)))
                return ("dash", "100")

        return None