# ===== FILE: src/ctrl_mid.py =====

from hierarchical_controller import HierarchicalController


class CtrlMid(HierarchicalController):
    """
    Средний уровень:
    - Движение к заданной точке (home position)
    - Обзор поля
    - Движение к мячу
    - Перехват мяча
    """

    def __init__(self, home_pos, role, side):
        super().__init__()
        self.home_pos = home_pos  # (x, y) базовая позиция
        self.role = role
        self.side = side
        self.action = "return_home"
        self.scan_state = 0  # для обзора поля

    def process(self, input_data):
        result = dict(input_data)
        result["cmd"] = None
        result["mid_action"] = self.action

        if self.action == "return_home":
            result["cmd"] = self._action_return_home(input_data)
        elif self.action == "scan_field":
            result["cmd"] = self._action_scan_field(input_data)
        elif self.action == "go_to_ball":
            result["cmd"] = self._action_go_to_ball(input_data)
        elif self.action == "position_attack":
            result["cmd"] = self._action_position_attack(input_data)

        return result

    def merge(self, own_result, upper_result):
        """Верхний уровень может переопределить действие или дать команду."""
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result["command"]
            if "new_action" in upper_result:
                self.action = upper_result["new_action"]
                # Переиграть с новым действием
                return self.process(own_result).get("cmd")
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        return own_result.get("cmd")

    def _action_return_home(self, data):
        """Возврат на домашнюю позицию."""
        # Определяем ключ ближайшего флага к home
        goal_own = data.get("goal_own")
        flags = data.get("flags", {})
        x = data.get("x")
        y = data.get("y")

        # Если знаем свою позицию, проверяем расстояние до дома
        if x is not None and y is not None:
            hx, hy = self.home_pos
            dist_home = ((x - hx) ** 2 + (y - hy) ** 2) ** 0.5
            if dist_home < 3:
                self.action = "scan_field"
                return ("turn", "60")

        # Иначе ориентируемся на свои ворота
        if goal_own:
            angle = goal_own.get("dir", 0)
            dist = goal_own.get("dist", 9999)
            if abs(angle) > 10:
                return ("turn", str(int(angle)))
            if dist > 3:
                return ("dash", str(int(min(dist * 2 + 30, 100))))
            self.action = "scan_field"
            return ("turn", "180")

        return ("turn", "60")

    def _action_scan_field(self, data):
        """Обзор поля — медленный поворот."""
        ball = data.get("ball")
        if ball:
            # Мяч виден — переходим в режим готовности
            self.scan_state = 0
            return None  # Передаём управление верхнему уровню

        self.scan_state += 1
        if self.scan_state > 12:
            self.scan_state = 0
        return ("turn", "30")

    def _action_go_to_ball(self, data):
        """Движение к мячу."""
        ball = data.get("ball")
        if not ball:
            return ("turn", "45")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            return None  # Мяч достигнут, верхний уровень решит

        if abs(angle) > 10:
            return ("turn", str(int(angle)))

        power = min(100, int(dist * 6 + 40))
        return ("dash", str(power))

    def _action_position_attack(self, data):
        """Занять атакующую позицию (движение к позиции ближе к чужим воротам)."""
        goal_opp = data.get("goal_opp")
        if goal_opp:
            dist = goal_opp.get("dist", 9999)
            angle = goal_opp.get("dir", 0)
            if dist > 25:
                if abs(angle) > 15:
                    return ("turn", str(int(angle)))
                return ("dash", "70")
            return None  # На позиции
        return ("turn", "30")