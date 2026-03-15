# ===== FILE: src/ctrl_mid.py =====

from hierarchical_controller import HierarchicalController


class CtrlMid(HierarchicalController):
    """
    Средний уровень — тактика:
    - go_to_flag: движение к указанному флагу (по ключу)
    - scan_field: обзор поля (поворот пока не найдём мяч)
    - go_to_ball: движение к мячу
    - stay: стоять на месте (вратарь)

    Ориентация ТОЛЬКО по видимым объектам, без координат.
    """

    def __init__(self, home_flag, role, side):
        super().__init__()
        self.home_flag = home_flag  # ключ флага (например "fplc")
        self.role = role
        self.side = side
        self.action = "go_to_flag"
        self.target_flag = home_flag
        self.scan_steps = 0

    def process(self, input_data):
        result = dict(input_data)
        result["cmd"] = None
        result["mid_action"] = self.action

        if self.action == "go_to_flag":
            result["cmd"] = self._go_to_flag(input_data)
        elif self.action == "scan_field":
            result["cmd"] = self._scan_field(input_data)
        elif self.action == "go_to_ball":
            result["cmd"] = self._go_to_ball(input_data)
        elif self.action == "return_home":
            self.target_flag = self.home_flag
            self.action = "go_to_flag"
            result["cmd"] = self._go_to_flag(input_data)

        return result

    def merge(self, own_result, upper_result):
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result["command"]
            if "new_action" in upper_result:
                new_act = upper_result["new_action"]
                if isinstance(new_act, dict):
                    # {"action": "go_to_flag", "flag": "fprc"}
                    self.action = new_act.get("action", "go_to_flag")
                    if "flag" in new_act:
                        self.target_flag = new_act["flag"]
                else:
                    self.action = new_act
                return self.process(own_result).get("cmd")
        return own_result.get("cmd")

    def _go_to_flag(self, data):
        """Движение к целевому флагу по видимости."""
        flags = data.get("flags", {})
        target = self.target_flag

        if target in flags:
            obj = flags[target]
            dist = obj.get("dist", 9999)
            angle = obj.get("dir", 0)

            if dist < 3:
                # Достигли флага — переходим к обзору
                self.action = "scan_field"
                self.scan_steps = 0
                return ("turn", "60")

            if abs(angle) > 10:
                return ("turn", str(int(angle)))

            power = min(100, int(dist * 2 + 30))
            return ("dash", str(power))

        # Флаг не виден — крутимся
        return ("turn", "45")

    def _scan_field(self, data):
        """Обзор поля — крутимся пока не увидим мяч."""
        ball = data.get("ball")
        if ball:
            self.scan_steps = 0
            return None  # Мяч виден — передаём управление наверх

        self.scan_steps += 1
        if self.scan_steps > 12:
            self.scan_steps = 0
        return ("turn", "30")

    def _go_to_ball(self, data):
        """Движение к мячу."""
        ball = data.get("ball")
        if not ball:
            return ("turn", "45")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            return None  # Мяч достигнут — верхний уровень решит

        if abs(angle) > 10:
            return ("turn", str(int(angle)))

        power = min(100, int(dist * 6 + 40))
        return ("dash", str(power))