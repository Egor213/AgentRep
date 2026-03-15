# ===== FILE: src/ctrl_low.py =====

from hierarchical_controller import HierarchicalController
from flags import FLAGS


class CtrlLow(HierarchicalController):
    """
    Нижний уровень — восприятие:
    - Выделяет мяч, флаги, своих, чужих
    - Определяет can_kick
    - Определяет свои/чужие ворота по side
    """

    def __init__(self, team, side, role):
        super().__init__()
        self.team = team
        self.side = side
        self.role = role

    def process(self, input_data):
        visible = input_data.get("visible", {})

        result = {
            "visible": visible,
            "play_on": input_data.get("play_on", False),
            "last_heard": input_data.get("last_heard_msg"),
            "referee_msg": input_data.get("referee_msg"),
            "team": self.team,
            "side": self.side,
            "player_number": self.player_number,
            "role": self.role,
            "ball": None,
            "can_kick": False,
            "goal_own": None,
            "goal_opp": None,
            "flags": {},
            "teammates": [],
            "opponents": [],
        }

        # Мяч
        if "b" in visible:
            result["ball"] = visible["b"]
            if visible["b"].get("dist", 9999) < 0.7:
                result["can_kick"] = True

        # Ворота
        goal_own_key = "gl" if self.side == "l" else "gr"
        goal_opp_key = "gr" if self.side == "l" else "gl"

        if goal_own_key in visible:
            result["goal_own"] = visible[goal_own_key]
        if goal_opp_key in visible:
            result["goal_opp"] = visible[goal_opp_key]

        # Флаги
        for key, obj in visible.items():
            if key in FLAGS:
                result["flags"][key] = obj

        # Игроки
        for key, obj in visible.items():
            name = obj.get("name", [])
            if not isinstance(name, list) or len(name) < 2:
                continue
            if name[0] == "p":
                team_name = str(name[1]).strip('"')
                if team_name == self.team:
                    result["teammates"].append(obj)
                else:
                    result["opponents"].append(obj)

        return result

    def merge(self, own_result, upper_result):
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result["command"]
            if "new_action" in upper_result:
                own_result["new_action"] = upper_result["new_action"]
        if isinstance(own_result, dict) and "cmd" in own_result:
            return own_result["cmd"]
        return None