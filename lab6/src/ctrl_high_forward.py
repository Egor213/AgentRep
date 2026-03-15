# ===== FILE: src/ctrl_high_forward.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighForward(HierarchicalController):
    """
    Верхний уровень — нападающий:
    - Мяч рядом → удар по воротам
    - Мяч видим → бежать за ним (агрессивнее чем другие)
    - Иначе → идти к атакующему флагу
    """

    def __init__(self, side, home_flag, attack_flag):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.attack_flag = attack_flag  # флаг ближе к чужим воротам
        self.last = None

    def process(self, input_data):
        # 1. Мяч рядом — бить по воротам
        if input_data.get("can_kick"):
            self.last = "kick"
            goal_opp = input_data.get("goal_opp")
            if goal_opp:
                dist = goal_opp.get("dist", 9999)
                angle = goal_opp.get("dir", 0)
                power = min(100, int(70 + dist))
                return ("kick", f"{power} {int(angle)}")
            # Ворота не видим — подбить мяч вбок и попробовать увидеть
            return ("kick", "10 45")

        # 2. Мяч виден — бежать за ним
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            teammates = input_data.get("teammates", [])

            # Нападающий бежит за мячом агрессивнее (порог 30, отрыв 8)
            am_closest = True
            for t in teammates:
                if t.get("dist", 9999) < ball_dist - 8:
                    am_closest = False
                    break

            if am_closest and ball_dist < 35:
                self.last = "go_ball"
                return {"new_action": "go_to_ball"}

        # 3. Идти к атакующей позиции
        if self.last in ("go_ball", "kick"):
            self.last = None
            return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}

        return None