# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Верхний уровень — вратарь:
    - Мяч рядом → пас защитнику или выбить
    - Мяч близко к воротам → бросок
    - Иначе → позиция у ворот
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — пасуем или выбиваем
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        # 2. Мяч близко и никто не перехватывает
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            teammate_near = input_data.get("teammate_near_ball", False)

            if ball_dist < 15 and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

        # 3. Вернуться
        if self.last == "defend":
            self.last = None
            return {"new_action": "return_home"}

        return None

    def _kick_decision(self, data):
        """Вратарь: пас тиммейту или выбить подальше."""
        best_target = data.get("best_pass_target")

        if best_target:
            angle = best_target.get("dir", 0)
            dist = best_target.get("dist", 10)
            power = min(100, int(dist * 4 + 30))
            # Возвращаем команду + флаг say
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        # Нет хорошего тиммейта — выбить в сторону чужих ворот
        goal_opp = data.get("goal_opp")
        if goal_opp:
            return ("kick", f"100 {int(goal_opp.get('dir', 0))}")

        return ("kick", "70 0")