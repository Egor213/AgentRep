# ===== FILE: src/ctrl_high_forward.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighForward(HierarchicalController):
    """
    Верхний уровень — нападающий:
    - Мяч рядом → удар по воротам ИЛИ пас другому нападающему
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
        # 1. Мяч рядом — бить или пасовать
        if input_data.get("can_kick"):
            self.last = "kick"
            return self._kick_decision(input_data)

        # 2. Приём паса — бежать к мячу
        if input_data.get("pass_to_me"):
            self.last = "receive"
            return {"new_action": "receive_pass"}

        # 3. Мяч виден
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            i_am_closest = input_data.get("i_am_closest_to_ball", True)
            teammate_near = input_data.get("teammate_near_ball", False)

            if teammate_near:
                # Тиммейт у мяча — открыться для паса
                if self.last != "position":
                    self.last = "position"
                    return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}
                return None

            if i_am_closest and ball_dist < 35:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

        # 4. Идти к атакующей позиции
        if self.last in ("go_ball", "kick", "receive"):
            self.last = None
            return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

        return None

    def _kick_decision(self, data):
        """
        Нападающий у мяча:
        1. Если ворота видны и близко (< 25) → бить
        2. Если есть тиммейт в лучшей позиции → пас
        3. Если ворота видны далеко → бить сильно
        4. Иначе → подкинуть вбок
        """
        goal_opp = data.get("goal_opp")
        best_target = data.get("best_pass_target")

        # Ворота близко — бить!
        if goal_opp:
            goal_dist = goal_opp.get("dist", 9999)
            goal_angle = goal_opp.get("dir", 0)

            if goal_dist < 25:
                power = min(100, int(70 + goal_dist))
                return ("kick", f"{power} {int(goal_angle)}")

            # Ворота далеко — пас если есть тиммейт ближе к воротам
            if best_target:
                t_dir = best_target.get("dir", 0)
                t_dist = best_target.get("dist", 10)

                # Пасуем если тиммейт ближе к воротам (по направлению)
                t_goal_diff = abs(t_dir - goal_angle)
                if t_goal_diff < 60 and t_dist < 30:
                    power = min(100, int(t_dist * 3.5 + 25))
                    return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

            # Бить по воротам всё равно
            power = min(100, int(50 + goal_dist))
            return ("kick", f"{power} {int(goal_angle)}")

        # Ворота не видны
        if best_target:
            t_dir = best_target.get("dir", 0)
            t_dist = best_target.get("dist", 10)
            power = min(100, int(t_dist * 3.5 + 25))
            return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

        # Ничего не видим — подкинуть вбок
        return ("kick", "10 45")