# ===== FILE: src/ctrl_low.py =====

import math
from hierarchical_controller import HierarchicalController
from flags import FLAGS


class CtrlLow(HierarchicalController):

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
            "teammate_near_ball": False,
            "i_am_closest_to_ball": True,
            "pass_to_me": False,
            "best_pass_target": None,
        }

        if "b" in visible:
            result["ball"] = visible["b"]
            if visible["b"].get("dist", 9999) < 0.7:
                result["can_kick"] = True

        goal_own_key = "gl" if self.side == "l" else "gr"
        goal_opp_key = "gr" if self.side == "l" else "gl"

        if goal_own_key in visible:
            result["goal_own"] = visible[goal_own_key]
        if goal_opp_key in visible:
            result["goal_opp"] = visible[goal_opp_key]

        for key, obj in visible.items():
            if key in FLAGS:
                result["flags"][key] = obj

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

        self._evaluate_ball_proximity(result)
        self._find_best_pass_target(result)

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

            if t_to_ball < 1.5:
                result["teammate_near_ball"] = True
                result["i_am_closest_to_ball"] = False
                return

            if t_to_ball < my_ball_dist - 1.5:
                result["i_am_closest_to_ball"] = False

    def _find_best_pass_target(self, result):
        teammates = result["teammates"]
        if not teammates:
            return

        goal_opp = result["goal_opp"]
        goal_own = result["goal_own"]
        opponents = result["opponents"]

        best = None
        best_score = -9999

        for t in teammates:
            t_dist = t.get("dist", 9999)
            t_dir = t.get("dir", 0)

            if t_dist > 35 or t_dist < 3:
                continue

            score = 50 - abs(t_dist - 15)

            if goal_opp:
                goal_dir = goal_opp.get("dir", 0)
                dir_diff = abs(t_dir - goal_dir)
                if dir_diff > 180:
                    dir_diff = 360 - dir_diff
                if dir_diff < 40:
                    score += 30
                elif dir_diff < 70:
                    score += 10

            # Штраф за пас к своим воротам
            if goal_own:
                own_dir = goal_own.get("dir", 0)
                own_diff = abs(t_dir - own_dir)
                if own_diff > 180:
                    own_diff = 360 - own_diff
                if own_diff < 30:
                    score -= 50

            for opp in opponents:
                opp_dist = opp.get("dist", 9999)
                opp_dir = opp.get("dir", 0)
                if opp_dist < t_dist and abs(opp_dir - t_dir) < 15:
                    score -= 40

            if score > best_score:
                best_score = score
                best = t

        if best and best_score > 0:
            result["best_pass_target"] = best

    def merge(self, own_result, upper_result):
        if upper_result and isinstance(upper_result, dict):
            if "command" in upper_result:
                return upper_result
            if "new_action" in upper_result:
                own_result["new_action"] = upper_result["new_action"]
        if upper_result and isinstance(upper_result, tuple):
            return upper_result
        if isinstance(own_result, dict) and "cmd" in own_result:
            return own_result["cmd"]
        return None