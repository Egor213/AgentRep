# ===== FILE: src/ctrl_mid.py =====

from hierarchical_controller import HierarchicalController


class CtrlMid(HierarchicalController):

    def __init__(self, home_flag, role, side):
        super().__init__()
        self.home_flag = home_flag
        self.role = role
        self.side = side
        self.action = "go_to_flag"
        self.target_flag = home_flag
        self.scan_steps = 0
        self.return_steps = 0  # счётчик шагов возврата (защита от зацикливания)

    def process(self, input_data):
        result = dict(input_data)
        result["cmd"] = None
        result["mid_action"] = self.action
        result["at_home"] = self._is_at_home(input_data)

        if input_data.get("pass_to_me") and self.action not in ("receive_pass",):
            self.action = "receive_pass"
            self.return_steps = 0

        if self.action == "go_to_flag":
            result["cmd"] = self._go_to_flag(input_data)
        elif self.action == "scan_field":
            result["cmd"] = self._scan_field(input_data)
        elif self.action == "go_to_ball":
            result["cmd"] = self._go_to_ball(input_data)
        elif self.action == "return_home":
            result["cmd"] = self._return_home(input_data)
        elif self.action == "receive_pass":
            result["cmd"] = self._receive_pass(input_data)
        elif self.action == "watch_ball":
            result["cmd"] = self._watch_ball(input_data)

        result["memory"].update(self.memory)
        return result

    def merge(self, own_result, upper_result):
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result
            if "new_action" in upper_result:
                new_act = upper_result["new_action"]
                if isinstance(new_act, dict):
                    new_action_name = new_act.get("action", "go_to_flag")
                    if "flag" in new_act:
                        self.target_flag = new_act["flag"]
                    self._switch_action(new_action_name)
                else:
                    self._switch_action(new_act)
                # Сразу выполняем новое действие
                return self.process(own_result).get("cmd")
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        return own_result.get("cmd")

    def _switch_action(self, new_action):
        """Переключение действия с сбросом счётчиков."""
        if new_action == "return_home":
            self.target_flag = self.home_flag
            self.return_steps = 0
        self.action = new_action

    def _is_at_home(self, data):
        """Проверяет, находится ли игрок у домашнего флага."""
        flags = data.get("flags", {})
        if self.home_flag in flags:
            dist = flags[self.home_flag].get("dist", 9999)
            return dist < 3
        return False

    def _return_home(self, data):
        """
        Возврат к домашнему флагу.
        Отдельное действие от go_to_flag — не переключается на scan_field.
        """
        flags = data.get("flags", {})
        target = self.home_flag

        if target in flags:
            obj = flags[target]
            dist = obj.get("dist", 9999)
            angle = obj.get("dir", 0)

            # Дошли до дома — переключаемся на наблюдение
            if dist < 3:
                self.action = "watch_ball"
                self.return_steps = 0
                return self._watch_ball(data)

            # Повернуться к флагу
            if abs(angle) > 10:
                return ("turn", str(int(angle)))

            # Бежать к флагу
            power = min(100, int(dist * 4 + 40))
            return ("dash", str(power))

        # Флаг не виден — крутимся, ищем
        self.return_steps += 1
        if self.return_steps > 12:
            # Слишком долго ищем — пробуем dash вперёд чтобы сменить обзор
            self.return_steps = 0
            return ("dash", "30")
        return ("turn", "60")

    def _go_to_flag(self, data):
        flags = data.get("flags", {})
        target = self.target_flag

        if target in flags:
            obj = flags[target]
            dist = obj.get("dist", 9999)
            angle = obj.get("dir", 0)

            if dist < 3:
                self.action = "scan_field"
                return ("turn", "60")

            if abs(angle) > 10:
                return ("turn", str(int(angle)))

            power = min(100, int(dist * 2 + 30))
            return ("dash", str(power))

        return ("turn", "60")

    def _scan_field(self, data):
        ball = data.get("ball")
        if ball:
            return None
        return ("turn", "60")

    def _go_to_ball(self, data):
        ball = data.get("ball")
        if not ball:
            return ("turn", "60")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            return None

        if abs(angle) > 5:
            return ("turn", str(int(angle)))

        power = min(100, int(dist * 8 + 50))
        return ("dash", str(power))

    def _receive_pass(self, data):
        ball = data.get("ball")
        if not ball:
            return ("turn", "40")

        angle = ball.get("dir", 0)
        dist = ball.get("dist", 9999)

        if dist < 0.7:
            self.action = "scan_field"
            return None

        if abs(angle) > 5:
            return ("turn", str(int(angle)))

        power = min(100, int(dist * 10 + 50))
        return ("dash", str(power))

    def _dribble(self, data):
        ball = data.get("ball")
        if not ball:
            self.action = "scan_field"
            return ("turn", "60")

        dist = ball.get("dist", 9999)
        if dist > 2.0:
            self.action = "go_to_ball"
            return self._go_to_ball(data)

        if dist < 0.7:
            return None

        angle = ball.get("dir", 0)
        if abs(angle) > 5:
            return ("turn", str(int(angle)))

        return ("dash", str(min(80, int(dist * 6 + 30))))

    def _watch_ball(self, data):
        """Стоять на месте, следить за мячом."""
        ball = data.get("ball")
        if not ball:
            return ("turn", "40")

        angle = ball.get("dir", 0)
        if abs(angle) > 5:
            return ("turn", str(int(ball.get("dir", 0))))

        return None