# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Верхний уровень — вратарь:
    - Мяч рядом → пас защитнику или выбить ОТ своих ворот
    - Мяч близко к воротам → бросок
    - Иначе → позиция у ворот
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None

    def process(self, input_data):
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            teammate_near = input_data.get("teammate_near_ball", False)

            if ball_dist < 15 and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

        if self.last == "defend":
            self.last = None
            return {"new_action": "return_home"}

        return None

    def _kick_decision(self, data):
        best_target = data.get("best_pass_target")
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")

        # Пас тиммейту (проверяем что не в сторону своих ворот)
        if best_target:
            angle = best_target.get("dir", 0)
            if not self._is_toward_own_goal(angle, goal_own):
                dist = best_target.get("dist", 10)
                power = min(100, int(dist * 4 + 30))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        # Бить в чужие ворота
        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return ("kick", f"100 {int(angle)}")

        # Выбить ПОДАЛЬШЕ от своих ворот
        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            return ("kick", f"100 {int(safe_angle)}")

        # Ничего не видим — бить вперёд (в сторону чужой половины)
        return ("kick", "80 0")

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
        """Возвращает угол в противоположную сторону."""
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite