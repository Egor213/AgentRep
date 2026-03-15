# ===== FILE: src/ctrl_high_defender.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighDefender(HierarchicalController):
    """
    Верхний уровень — защитник:
    - Мяч рядом → пас нападающему или выбить вперёд
    - Мяч близко и я ближайший → перехватить
    - Иначе → позиция у флага
    """

    def __init__(self, side, home_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — пас или выбить
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        # 2. Приём паса — бежать к мячу
        if input_data.get("pass_to_me"):
            self.last = "receive"
            return {"new_action": "receive_pass"}

        # 3. Перехват
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)

            if ball_dist < 15 and i_am_closest and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

        # 4. Вернуться
        if self.last in ("defend", "kick", "receive"):
            self.last = None
            return {"new_action": "return_home"}

        return None

    def _kick_decision(self, data):
        """Защитник: пас тиммейту ближе к чужим воротам."""
        best_target = data.get("best_pass_target")

        if best_target:
            angle = best_target.get("dir", 0)
            dist = best_target.get("dist", 10)
            power = min(100, int(dist * 3.5 + 25))
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        # Нет — выбить в сторону чужих ворот
        goal_opp = data.get("goal_opp")
        if goal_opp:
            return ("kick", f"80 {int(goal_opp.get('dir', 0))}")

        return ("kick", "60 0")