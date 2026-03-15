from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None
        self.step_without_home = 0
        self.ball_caught = False

    def _home_flag(self):
        return "gl" if self.side == "l" else "gr"

    def _dist_to_home(self, data):
        flags = data.get("flags", {})
        hf = self._home_flag()
        if hf in flags:
            return flags[hf].get("dist", None)
        goal_own = data.get("goal_own")
        if goal_own:
            return goal_own.get("dist", None)
        return None

    def process(self, input_data):
        if self.ball_caught:
            self.ball_caught = False
            self.last = "kick_after_catch"
            return self._kick_away(input_data)

        dist_home = self._dist_to_home(input_data)

        if not dist_home:
            self.step_without_home += 1
        
        ball = input_data.get("ball")

        if self.step_without_home > 63:
            if (not ball or "dist_change" not in ball or ball.get("dist_change") <= 0) or self.step_without_home > 99:
                self.step_without_home = 0
                self.last = "return"
                return {"new_action": "return_home"}

        if input_data.get("can_kick"):
            if ball:
                ball_angle = ball.get("dir", 0)
                ball_dist = ball.get("dist", 9999)
                if ball_dist < 2.0:
                    self.last = "catch"
                    self.ball_caught = True
                    return ("catch", str(int(ball_angle)))

            self.last = "kick"
            return self._kick_away(input_data)


        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            teammate_near = input_data.get("teammate_near_ball", False)

            if ball_dist < 2.0:
                self.last = "catch"
                self.ball_caught = True
                return ("catch", str(int(ball_angle)))


            if ball_dist > 15:
                if self.last == "return_":
                    if abs(ball_angle) > 5:
                        return ("turn", str(int(ball_angle)))
                    return None
                self.last = "return_"
                return {"new_action": "return_home"}

            if not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

            if dist_home and dist_home > 6:
                self.last = "return"
                return {"new_action": "return_home"}
            if abs(ball_angle) > 5:
                return ("turn", str(int(ball_angle)))
            return None

        if dist_home and dist_home > 4:
            self.last = "return"
            return {"new_action": "return_home"}


    def _kick_away(self, data):
        """Выбить мяч подальше от своих ворот."""
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
        return diff < 60

    def _opposite_angle(self, angle):
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite