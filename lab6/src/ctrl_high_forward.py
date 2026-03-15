# ===== FILE: src/ctrl_high_forward.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighForward(HierarchicalController):
    """
    Верхний уровень — нападающий:
    - Мяч рядом → удар по воротам ИЛИ пас (НИКОГДА не в свои ворота)
    - Приём паса → бежать к мячу
    - Мяч виден, я ближайший → бежать
    - Тиммейт у мяча → открыться для паса
    """

    def __init__(self, side, home_flag, attack_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.attack_flag = attack_flag
        self.last = None

    def process(self, input_data):
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        if input_data.get("pass_to_me"):
            self.last = "receive"
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)

            if teammate_near:
                if self.last != "position":
                    self.last = "position"
                    return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}
                return None

            if i_am_closest and ball_dist < 35:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

        if self.last in ("go_ball", "kick", "receive"):
            self.last = None
            return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

        return None

    def _kick_decision(self, data):
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")
        best_target = data.get("best_pass_target")

        # Ворота противника близко — бить!
        if goal_opp:
            goal_dist = goal_opp.get("dist", 9999)
            goal_angle = goal_opp.get("dir", 0)

            if goal_dist < 30:
                power = min(100, int(70 + goal_dist))
                return ("kick", f"{power} {int(goal_angle)}")

            # Далеко — пас если есть тиммейт в хорошей позиции
            if best_target:
                t_dir = best_target.get("dir", 0)
                t_dist = best_target.get("dist", 10)

                if not self._is_toward_own_goal(t_dir, goal_own):
                    t_goal_diff = abs(t_dir - goal_angle)
                    if t_goal_diff < 60 and t_dist < 30:
                        power = min(100, int(t_dist * 3.5 + 25))
                        return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

            # Бить по воротам всё равно
            power = min(100, int(50 + goal_dist))
            return ("kick", f"{power} {int(goal_angle)}")

        # Ворота противника не видны
        if best_target:
            t_dir = best_target.get("dir", 0)
            t_dist = best_target.get("dist", 10)
            if not self._is_toward_own_goal(t_dir, goal_own):
                power = min(100, int(t_dist * 3.5 + 25))
                return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

        # Ничего хорошего не видим — увести мяч от своих ворот
        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            return ("kick", f"30 {int(safe_angle)}")

        # Совсем ничего — подкинуть вбок
        return ("kick", "15 90")

    def _is_toward_own_goal(self, kick_angle, goal_own):
        """Проверяет, направлен ли удар в сторону своих ворот."""
        if not goal_own:
            return False
        own_angle = goal_own.get("dir", 0)
        diff = abs(kick_angle - own_angle)
        if diff > 180:
            diff = 360 - diff
        return diff < 40

    def _opposite_angle(self, angle):
        """Угол в противоположную сторону."""
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite