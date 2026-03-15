# ===== FILE: src/ctrl_low.py =====

import math
from hierarchical_controller import HierarchicalController
from flags import FLAGS


class CtrlLow(HierarchicalController):
    """
    Нижний уровень — восприятие:
    - Выделяет мяч, флаги, своих, чужих
    - Определяет can_kick
    - Оценивает кто ближе к мячу (теорема косинусов)
    - Разбирает heard-сообщения для пасов
    """

    def __init__(self, team, side, role):
        super().__init__()
        self.team = team
        self.side = side
        self.role = role
        self.player_number = 0
        self.role_key = ""

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
            "role_key": self.role_key,
            "ball": None,
            "can_kick": False,
            "goal_own": None,
            "goal_opp": None,
            "flags": {},
            "teammates": [],
            "opponents": [],
            # Координация
            "teammate_near_ball": False,
            "i_am_closest_to_ball": True,
            # Пасы
            "pass_to_me": False,  # мне кричали "pass"
            "best_pass_target": None,  # лучший тиммейт для паса
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

        # Оценка кто ближе к мячу
        self._evaluate_ball_proximity(result)

        # Выбор лучшего для паса
        self._find_best_pass_target(result)

        # Разбор heard
        last_heard = input_data.get("last_heard_msg")
        if last_heard == "pass":
            result["pass_to_me"] = True

        return result

    def _evaluate_ball_proximity(self, result):
        ball = result["ball"]
        if not ball:
            return

        my_ball_dist = ball.get("dist", 9999)
        ball_dir = ball.get("dir", 0)

        for t in result["teammates"]:
            t_dist = t.get("dist", 9999)
            t_dir = t.get("dir", 0)

            angle_diff = math.radians(abs(ball_dir - t_dir))
            t_to_ball_sq = (my_ball_dist ** 2 + t_dist ** 2
                            - 2 * my_ball_dist * t_dist * math.cos(angle_diff))
            t_to_ball = math.sqrt(max(0, t_to_ball_sq))

            if t_to_ball < 2.0:
                result["teammate_near_ball"] = True
                result["i_am_closest_to_ball"] = False
                return

            if t_to_ball < my_ball_dist - 2:
                result["i_am_closest_to_ball"] = False

    def _find_best_pass_target(self, result):
        """
        Выбирает лучшего тиммейта для паса:
        - Предпочитает тех кто дальше от наших ворот (ближе к чужим)
        - Не слишком далеко (< 35) чтобы пас дошёл
        - Не слишком близко (> 5) чтобы имело смысл
        - Без противников на пути (грубая проверка)
        """
        teammates = result["teammates"]
        if not teammates:
            return

        goal_opp = result["goal_opp"]
        opponents = result["opponents"]

        best = None
        best_score = -9999

        for t in teammates:
            t_dist = t.get("dist", 9999)
            t_dir = t.get("dir", 0)

            # Фильтр по расстоянию
            if t_dist > 35 or t_dist < 3:
                continue

            # Базовый счёт: предпочитаем средние расстояния
            score = 50 - abs(t_dist - 15)

            # Бонус если тиммейт в направлении чужих ворот
            if goal_opp:
                goal_dir = goal_opp.get("dir", 0)
                dir_diff = abs(t_dir - goal_dir)
                if dir_diff < 40:
                    score += 30  # В направлении ворот
                elif dir_diff < 70:
                    score += 10

            # Штраф если противник на пути паса
            for opp in opponents:
                opp_dist = opp.get("dist", 9999)
                opp_dir = opp.get("dir", 0)
                # Противник между мной и тиммейтом, и примерно в том же направлении
                if opp_dist < t_dist and abs(opp_dir - t_dir) < 15:
                    score -= 40  # Пас скорее всего перехватят

            if score > best_score:
                best_score = score
                best = t

        if best and best_score > 0:
            result["best_pass_target"] = best

    
    def merge(self, own_result, upper_result):
        # Словарь с command+say — пробросить как есть
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result  # {command: (...), say: "pass"}
            if "new_action" in upper_result:
                own_result["new_action"] = upper_result["new_action"]
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        if isinstance(own_result, dict) and "cmd" in own_result:
            return own_result["cmd"]
        return None