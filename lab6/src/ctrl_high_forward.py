# ===== FILE: src/ctrl_high_forward.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighForward(HierarchicalController):
    """
    Верхний уровень для нападающего:
    - Если мяч рядом — удар по воротам
    - Активно бежит за мячом если в зоне атаки
    - Занимает позицию для атаки
    """

    def __init__(self, side, home_pos, zone="center"):
        super().__init__()
        self.side = side
        self.home_pos = home_pos
        self.zone = zone
        self.last_action = None

    def process(self, input_data):
        # Мяч рядом — ударить по воротам
        if input_data.get("can_kick"):
            self.last_action = "kick"
            goal_opp = input_data.get("goal_opp")
            if goal_opp:
                angle = goal_opp.get("dir", 0)
                dist = goal_opp.get("dist", 9999)
                power = min(100, int(70 + dist))
                return ("kick", f"{power} {int(angle)}")
            # Не видим ворота — ведение мяча
            return ("kick", "10 45")

        # Мяч виден — бежать за ним агрессивнее чем другие
        ball = input_data.get("ball")
        if ball:
            ball_dist = ball.get("dist", 9999)
            teammates = input_data.get("teammates", [])

            # Нападающий бежит за мячом если он в пределах 30
            am_closest = True
            for t in teammates:
                # Только если тиммейт значительно ближе
                if t.get("dist", 9999) < ball_dist - 8:
                    am_closest = False
                    break

            if am_closest and ball_dist < 35:
                self.last_action = "go_ball"
                return {"new_action": "go_to_ball"}

        # Иначе — занять атакующую позицию
        if self.last_action in ("go_ball", "kick"):
            self.last_action = None
            return {"new_action": "position_attack"}

        return None