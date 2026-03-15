# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Вратарь — всегда следит за мячом, агрессивно выходит.
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — отбить
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        ball = input_data.get("ball")

        # 2. Мяч виден
        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            teammate_near = input_data.get("teammate_near_ball", False)

            # Мяч очень близко — бросок
            if ball_dist < 20 and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

            # Мяч далеко — следить (поворачиваться к мячу)
            if abs(ball_angle) > 5:
                return ("turn", str(int(ball_angle)))

            # Мяч в поле зрения, далеко — стоим, смотрим
            if self.last == "defend":
                self.last = None
                return {"new_action": "return_home"}

            return ("turn", "0")  # Стоим на месте, мяч виден

        # 3. Мяч не виден — быстро искать
        if self.last == "defend":
            self.last = None
            return {"new_action": "return_home"}

        return ("turn", "40")

    def _kick_decision(self, data):
        best_target = data.get("best_pass_target")
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")

        if best_target:
            angle = best_target.get("dir", 0)
            if not self._is_toward_own_goal(angle, goal_own):
                dist = best_target.get("dist", 10)
                power = min(100, int(dist * 5 + 30))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return ("kick", f"100 {int(angle)}")

        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            return ("kick", f"100 {int(safe_angle)}")

        return ("kick", "100 0")

    def _is_toward_own_goal(self, kick_angle, goal_own):
        if not goal_own:
            return False
        own_angle = goal_own.get("dir", 0)
        diff = abs(kick_angle - own_angle)
        if diff > 180:
            diff = 360 - diff
        return diff < 45

    def _opposite_angle(self, angle):
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite