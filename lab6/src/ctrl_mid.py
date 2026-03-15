# ===== FILE: src/ctrl_mid.py =====

from hierarchical_controller import HierarchicalController


class CtrlMid(HierarchicalController):
    """
    Средний уровень — тактика:
    - go_to_flag: движение к флагу
    - scan_field: обзор поля
    - go_to_ball: движение к мячу
    - return_home: возврат на базу
    - receive_pass: активное движение к мячу после крика "pass"
    """

    def __init__(self, home_flag, role, side):
        super().__init__()
        self.home_flag = home_flag
        self.role = role
        self.side = side
        self.action = "go_to_flag"
        self.target_flag = home_flag
        self.scan_steps = 0
        self.say_msg = None  # Сообщение для крика

    def process(self, input_data):
        result = dict(input_data)
        result["cmd"] = None
        result["mid_action"] = self.action
        self.say_msg = None

        # Если мне крикнули "pass" — переключиться на приём
        if input_data.get("pass_to_me") and self.action != "receive_pass":
            self.action = "receive_pass"

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
        elif self.action == "receive_pass":
            result["cmd"] = self._receive_pass(input_data)

        result["say_msg"] = self.say_msg
        return result

    def merge(self, own_result, upper_result):
        # Словарь с command+say — пробросить как есть
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result  # {command: (...), say: "pass"}
            if "new_action" in upper_result:
                new_act = upper_result["new_action"]
                if isinstance(new_act, dict):
                    self.action = new_act.get("action", "go_to_flag")
                    if "flag" in new_act:
                        self.target_flag = new_act["flag"]
                else:
                    self.action = new_act
                return self.process(own_result).get("cmd")
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        return own_result.get("cmd")

    def _go_to_flag(self, data):
        flags = data.get("flags", {})
        target = self.target_flag

        if target in flags:
            obj = flags[target]
            dist = obj.get("dist", 9999)
            angle = obj.get("dir", 0)

            if dist < 3:
                self.action = "scan_field"
                self.scan_steps = 0
                return ("turn", "60")

            if abs(angle) > 10:
                return ("turn", str(int(angle)))

            power = min(100, int(dist * 2 + 30))
            return ("dash", str(power))

        return ("turn", "45")

    def _scan_field(self, data):
        ball = data.get("ball")
        if ball:
            self.scan_steps = 0
            return None

        self.scan_steps += 1
        if self.scan_steps > 12:
            self.scan_steps = 0
        return ("turn", "30")

    def _go_to_ball(self, data):
        ball = data.get("ball")
        if not ball:
            self.action = "return_home"
            self.target_flag = self.home_flag
            return ("turn", "45")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            return None

        if abs(angle) > 10:
            return ("turn", str(int(angle)))

        power = min(100, int(dist * 6 + 40))
        return ("dash", str(power))

    def _receive_pass(self, data):
        """Приём паса — агрессивно бежим к мячу."""
        ball = data.get("ball")
        if not ball:
            # Мяч не виден — крутимся искать
            return ("turn", "30")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            # Мяч получен — переходим к обычной логике
            self.action = "scan_field"
            return None

        if abs(angle) > 5:
            return ("turn", str(int(angle)))

        # Бежим быстро
        power = min(100, int(dist * 8 + 50))
        return ("dash", str(power))