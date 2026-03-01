from flags import FLAGS, obj_name_to_key
from geometry import (
    compute_position_two_flags,
    compute_position_three_flags,
)

class Taken:
    def __init__(self):
        self.hear_history = []
        self.ball_prev = None

    def set_hear(self, parsed_hear):
        # (hear Time Sender Message)
        if len(parsed_hear) < 4: return
        self.hear_history.insert(0, {
            "time": parsed_hear[1],
            "who": parsed_hear[2],
            "msg": parsed_hear[3]
        })
        if len(self.hear_history) > 10:
            self.hear_history.pop()

    def set_see(self, parsed_see, team, side):
        time = parsed_see[1]
        visible = {}
        for i in range(2, len(parsed_see)):
            obj_info = parsed_see[i]
            if not isinstance(obj_info, list) or len(obj_info) < 2: continue
            obj_name_raw = obj_info[0]
            if not isinstance(obj_name_raw, list): continue
            
            key = obj_name_to_key(obj_name_raw)
            entry = {"f": key, "dist": float(obj_info[1])}
            if len(obj_info) > 2: entry["angle"] = float(obj_info[2])
            visible[key] = entry

        # Compute my position
        my_pos = self._compute_pos(visible)
        
        # Prepare result
        res = {
            "time": time,
            "pos": {"x": my_pos[0], "y": my_pos[1]} if my_pos else None,
            "hear": self.hear_history,
            "ball": visible.get("b"),
            "ballPrev": self.ball_prev,
            "teamOwn": [],
            "team": [],
            "goal": visible.get("gr") if side == "l" else visible.get("gl"),
            "goalOwn": visible.get("gl") if side == "l" else visible.get("gr")
        }
        
        # Teammates and opponents
        for key, obj in visible.items():
            if key.startswith("p"):
                name = obj.get("f", []) # This is a bit complex in flags.py
                # For now simplify
                if team in str(key):
                    res["teamOwn"].append(obj)
                else:
                    res["team"].append(obj)
        
        self.ball_prev = res["ball"]
        return res

    def _compute_pos(self, visible):
        flag_observations = []
        for key, obj in visible.items():
            if key in FLAGS:
                flag_observations.append((key, obj["dist"]))
        if len(flag_observations) < 2: return None
        
        f1, d1 = flag_observations[0]
        f2, d2 = flag_observations[1]
        if len(flag_observations) >= 3:
            f3, d3 = flag_observations[2]
            return compute_position_three_flags(f1, d1, f2, d2, f3, d3)
        return compute_position_two_flags(f1, d1, f2, d2)
