# ===== FILE: src/ctrl_low.py =====

from hierarchical_controller import HierarchicalController
from flags import FLAGS


class CtrlLow(HierarchicalController):
    """
    Нижний уровень:
    - Выделяет объекты из visible_objects (мяч, флаги, тиммейты, противники)
    - Определяет canKick (мяч рядом)
    - Определяет свои ворота, чужие ворота
    - Передаёт предобработанные данные наверх
    """

    def __init__(self, team, side, player_number, role):
        super().__init__()
        self.team = team
        self.side = side
        self.player_number = player_number
        self.role = role

    def process(self, input_data):
        visible = input_data.get("visible", {})
        x = input_data.get("x")
        y = input_data.get("y")
        play_on = input_data.get("play_on", False)
        last_heard = input_data.get("last_heard_msg")
        referee_msg = input_data.get("referee_msg")

        result = {
            "visible": visible,
            "x": x,
            "y": y,
            "play_on": play_on,
            "last_heard": last_heard,
            "referee_msg": referee_msg,
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
            "closest_opp_to_ball": None,
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

        # Тиммейты и противники
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

        # Ближайший противник к мячу (оценка по расстоянию)
        if result["ball"] and result["opponents"]:
            ball_dist = result["ball"].get("dist", 9999)
            for opp in result["opponents"]:
                opp_dist = opp.get("dist", 9999)
                # Грубая оценка: если противник ближе к нам чем мяч — он может быть ближе к мячу
                if opp_dist < ball_dist + 5:
                    if result["closest_opp_to_ball"] is None or opp_dist < result["closest_opp_to_ball"].get("dist", 9999):
                        result["closest_opp_to_ball"] = opp

        return result

    def merge(self, own_result, upper_result):
        # Верхний уровень возвращает команду или новое действие
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result["command"]
            if "new_action" in upper_result:
                own_result["new_action"] = upper_result["new_action"]
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        # Собственная команда (от среднего уровня через finalize)
        if "cmd" in own_result:
            return own_result["cmd"]
        return None