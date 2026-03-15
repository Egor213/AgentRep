# ===== FILE: src/ctrl_high_forward.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighForward(HierarchicalController):
    """
    Нападающий — агрессивно бежит за мячом, ведёт к воротам, бьёт.
    Не стоит на месте — если мяч далеко, идёт навстречу.
    """

    def __init__(self, side, home_flag, attack_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.attack_flag = attack_flag
        self.last = None
        self.dribble_count = 0

    def process(self, input_data):
        # 1. Мяч рядом — бить/пасовать/вести
        if input_data.get("can_kick"):
            return self._kick_decision(input_data)

        # 2. Приём паса
        if input_data.get("pass_to_me"):
            self.last = "receive"
            self.dribble_count = 0
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")

        # 3. Мяч виден
        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)

            # Тиммейт у мяча — открыться для паса, идти к атакующему флагу
            if teammate_near and not i_am_closest:
                if self.last != "position":
                    self.last = "position"
                    return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}
                # Уже идём к позиции — следить за мячом
                if abs(ball_angle) > 15:
                    return ("turn", str(int(ball_angle)))
                return None

            # Я ближайший или мяч свободен — бежать за ним!
            if i_am_closest and ball_dist < 50:
                self.last = "go_ball"
                self.dribble_count = 0
                return {"new_action": "go_to_ball"}

            # Мяч далеко и я не ближайший — двигаться к атакующей позиции
            if ball_dist > 30:
                if self.last != "position":
                    self.last = "position"
                    return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

            # Мяч в среднем радиусе — бежать за ним
            if ball_dist < 40:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

        # 4. Мяч не виден — искать активно
        if self.last in ("go_ball", "kick", "receive", "dribble"):
            self.last = None
            return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

        return ("turn", "60")

    def _kick_decision(self, data):
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")
        best_target = data.get("best_pass_target")

        # Ворота видны и близко — БИТЬ!
        if goal_opp:
            goal_dist = goal_opp.get("dist", 9999)
            goal_angle = goal_opp.get("dir", 0)

            if goal_dist < 30:
                self.last = "kick"
                self.dribble_count = 0
                power = min(100, int(60 + goal_dist))
                return ("kick", f"{power} {int(goal_angle)}")

            # Ворота далеко — пас если есть тиммейт ближе к воротам
            if best_target:
                t_dir = best_target.get("dir", 0)
                t_dist = best_target.get("dist", 10)
                if not self._is_toward_own_goal(t_dir, goal_own):
                    t_goal_diff = abs(t_dir - goal_angle)
                    if t_goal_diff > 180:
                        t_goal_diff = 360 - t_goal_diff
                    if t_goal_diff < 50 and t_dist < 30:
                        self.last = "kick"
                        self.dribble_count = 0
                        power = min(100, int(t_dist * 4 + 25))
                        return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

            # Ведение мяча к воротам! Подбить мяч вперёд и бежать
            self.dribble_count += 1
            if self.dribble_count < 8:
                self.last = "dribble"
                return ("kick", f"8 {int(goal_angle)}")
            else:
                # Слишком долго ведём — пнуть сильнее
                self.dribble_count = 0
                self.last = "kick"
                power = min(100, int(40 + goal_dist))
                return ("kick", f"{power} {int(goal_angle)}")

        # Ворота не видны
        if best_target:
            t_dir = best_target.get("dir", 0)
            t_dist = best_target.get("dist", 10)
            if not self._is_toward_own_goal(t_dir, goal_own):
                self.last = "kick"
                self.dribble_count = 0
                power = min(100, int(t_dist * 4 + 25))
                return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

        # Ничего не видим — увести от своих ворот (подбить и вести)
        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            self.dribble_count += 1
            if self.dribble_count < 8:
                self.last = "dribble"
                return ("kick", f"8 {int(safe_angle)}")
            else:
                self.dribble_count = 0
                self.last = "kick"
                return ("kick", f"40 {int(safe_angle)}")

        # Совсем ничего — подбить вперёд
        self.last = "dribble"
        self.dribble_count += 1
        return ("kick", "8 0")

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