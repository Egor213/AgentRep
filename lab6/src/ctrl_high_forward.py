from hierarchical_controller import HierarchicalController

SUPPORT_OFFSETS = {
    "forward_top": {"l": "frt10", "r": "flt10"},
    "forward_center": {"l": "fprc", "r": "fplc"},
    "forward_bottom": {"l": "frb10", "r": "flb10"},
}


class CtrlHighForward(HierarchicalController):

    def __init__(self, side, home_flag, attack_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.attack_flag = attack_flag
        self.last = None
        self.role_key = ""

    def process(self, input_data):
        if not self.role_key:
            self.role_key = input_data.get("role_key", "")

        if input_data.get("can_kick"):
            return self._kick_decision(input_data)

        if input_data.get("pass_to_me"):
            self.last = "receive"
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")

        if ball:
            ball_dist = ball.get("dist", 9999)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)
            teammates_closer = input_data.get("teammates_closer_to_ball", 0)

            if teammate_near and not i_am_closest:
                return self._go_support_position(input_data, ball)

            if teammates_closer >= 2:
                return self._go_support_position(input_data, ball)

            if teammates_closer >= 1 and ball_dist > 15:
                return self._go_support_position(input_data, ball)

            if i_am_closest and ball_dist < 50:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

            if ball_dist > 30:
                return self._go_support_position(input_data, ball)

            if ball_dist < 40:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

        if self.last in ("go_ball", "kick", "receive", "dribble"):
            self.last = None
            return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

        teams = input_data.get("teammates")
        if teams and len(teams) > 2:
            self.last = "return_home"
            return {"new_action": "return_home"}

        return ("turn", "60")

    def _go_support_position(self, input_data, ball):
        ball_angle = ball.get("dir", 0) if ball else 0

        support_flag = self._get_support_flag()

        if self.last != "support":
            self.last = "support"
            return {"new_action": {"action": "go_to_flag", "flag": support_flag}}

        if abs(ball_angle) > 10:
            return ("turn", str(int(ball_angle)))
        return None

    def _get_support_flag(self):
        side = self.side
        role = self.role_key

        if role in SUPPORT_OFFSETS:
            return SUPPORT_OFFSETS[role].get(side, self.attack_flag)

        return self.attack_flag

    def _kick_decision(self, data):
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")
        best_target = data.get("best_pass_target")

        if goal_opp:
            goal_dist = goal_opp.get("dist", 9999)
            goal_angle = goal_opp.get("dir", 0)

            if goal_dist < 30:
                self.last = "kick"
                power = min(100, int(60 + goal_dist))
                return ("kick", f"{power} {int(goal_angle)}")

            if best_target:
                t_dir = best_target.get("dir", 0)
                t_dist = best_target.get("dist", 10)

                if not self._is_toward_own_goal(t_dir, goal_own):
                    t_goal_diff = abs(t_dir - goal_angle)
                    if t_goal_diff > 180:
                        t_goal_diff = 360 - t_goal_diff
                    if t_goal_diff < 50 and t_dist < 30:
                        self.last = "kick"
                        power = min(100, int(t_dist * 4 + 25))
                        return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

            self.last = "kick"
            power = min(100, int(40 + goal_dist))
            return ("kick", f"{power} {int(goal_angle)}")

        if best_target:
            t_dir = best_target.get("dir", 0)
            t_dist = best_target.get("dist", 10)
            if not self._is_toward_own_goal(t_dir, goal_own):
                self.last = "kick"
                power = min(100, int(t_dist * 4 + 25))
                return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            self.last = "kick"
            return ("kick", f"40 {int(safe_angle)}")
        
        min_dist_flag = data.get("min_flag")
        if min_dist_flag and min_dist_flag[-1].isdigit():
            return ("kick", "20 -180")

        return ("kick", "20 40")

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