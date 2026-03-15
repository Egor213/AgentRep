# ===== FILE: src/ctrl_high_defender.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighDefender(HierarchicalController):
    """
    Защитник — постоянно следит за мячом, перехватывает на своей половине.
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
            return self._kick_decision(input_data)

        # 2. Приём паса
        if input_data.get("pass_to_me"):
            self.last = "receive"
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")

        # 3. Мяч виден
        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)

            # Мяч близко — перехватить
            if ball_dist < 20 and i_am_closest and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

            # Мяч далеко — следить за ним (поворачиваться)
            if abs(ball_angle) > 10:
                return ("turn", str(int(ball_angle)))

            # Мяч в поле зрения — стоим на позиции
            # Но проверяем что мы у своего флага
            flags = input_data.get("flags", {})
            if self.home_flag in flags:
                home_dist = flags[self.home_flag].get("dist", 9999)
                if home_dist > 5:
                    # Далеко от дома — вернуться но следить за мячом
                    if self.last in ("defend", "kick", "receive"):
                        self.last = None
                        return {"new_action": "return_home"}

            return ("turn", "0")  # Стоим, мяч видим

        # 4. Мяч не виден — искать
        if self.last in ("defend", "kick", "receive"):
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
                power = min(100, int(dist * 4 + 25))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return ("kick", f"90 {int(angle)}")

        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            return ("kick", f"90 {int(safe_angle)}")

        return ("kick", "60 90")

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