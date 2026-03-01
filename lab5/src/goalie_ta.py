import math

def create_goalie_ta():
    ta = {
        "current": "start",
        "state": {
            "variables": {"dist": 999},
            "timers": {"t": 0},
            "next": True,
            "synch": None,
            "local": {"goalie": True, "catch": 0}
        },
        "nodes": {
            "start": {"n": "start", "e": ["close", "near", "far"]},
            "close": {"n": "close", "e": ["catch"]},
            "catch": {"n": "catch", "e": ["kick"]},
            "kick": {"n": "kick", "e": ["start"]},
            "far": {"n": "far", "e": ["start"]},
            "near": {"n": "near", "e": ["intercept", "start"]},
            "intercept": {"n": "intercept", "e": ["start"]}
        },
        "edges": {
            "start_close": [{"guard": [{"s": "lt", "l": {"v": "dist"}, "r": 2}]}],
            "start_near": [{"guard": [
                {"s": "lt", "l": {"v": "dist"}, "r": 10},
                {"s": "gte", "l": {"v": "dist"}, "r": 2}
            ]}],
            "start_far": [{"guard": [{"s": "gte", "l": {"v": "dist"}, "r": 10}]}],
            "close_catch": [{"synch": "catch!"}],
            "catch_kick": [{"synch": "kick!"}],
            "kick_start": [{"synch": "goBack!", "assign": [{"n": "t", "v": 0, "type": "timer"}]}],
            "far_start": [
                {"guard": [{"s": "lt", "l": {"t": "t"}, "r": 10}], "synch": "ok!"},
                {"guard": [{"s": "gte", "l": {"t": "t"}, "r": 10}], "synch": "lookAround!", "assign": [{"n": "t", "v": 0, "type": "timer"}]}
            ],
            "near_start": [{"synch": "empty!", "assign": [{"n": "t", "v": 0, "type": "timer"}]}],
            "near_intercept": [{"synch": "canIntercept?"}],
            "intercept_start": [{"synch": "runToBall!", "assign": [{"n": "t", "v": 0, "type": "timer"}]}]
        },
        "actions": {
            "beforeAction": _before_action,
            "catch": _catch_action,
            "kick": _kick_action,
            "goBack": _go_back_action,
            "lookAround": _look_around_action,
            "canIntercept": _can_intercept_action,
            "runToBall": _run_to_ball_action,
            "ok": _ok_action,
            "empty": _empty_action
        }
    }
    return ta

def _before_action(taken, state):
    if taken.get("ball"):
        state["variables"]["dist"] = taken["ball"]["dist"]
    else:
        state["variables"]["dist"] = 999

def _catch_action(taken, state):
    if not taken.get("ball"):
        state["next"] = True
        return None
    angle = taken["ball"]["angle"]
    dist = taken["ball"]["dist"]
    state["next"] = False
    if dist > 0.5:
        if state["local"].get("goalie"):
            if state["local"]["catch"] < 3:
                state["local"]["catch"] += 1
                return ("catch", str(int(angle)))
            else:
                state["local"]["catch"] = 0
        if abs(angle) > 15: return ("turn", str(int(angle)))
        return ("dash", "20")
    state["next"] = True
    return None

def _kick_action(taken, state):
    state["next"] = True
    if not taken.get("ball"): return None
    if taken["ball"]["dist"] > 0.7: return None
    
    target = taken.get("goal") or (taken["teamOwn"][0] if taken["teamOwn"] else None)
    if target:
        return ("kick", f"{int(target['dist']*2+40)} {int(target['angle'])}")
    return ("kick", "10 45")

def _go_back_action(taken, state):
    state["next"] = False
    goal_own = taken.get("goalOwn")
    if not goal_own: return ("turn", "60")
    if abs(goal_own["angle"]) > 10: return ("turn", str(int(goal_own["angle"])))
    if goal_own["dist"] < 2:
        state["next"] = True
        return ("turn", "180")
    return ("dash", str(int(goal_own["dist"] * 2 + 20)))

def _look_around_action(taken, state):
    state["next"] = False
    state["synch"] = "lookAround!"
    if "look" not in state["local"]: state["local"]["look"] = "left"
    
    look = state["local"]["look"]
    if look == "left":
        state["local"]["look"] = "center"
        return ("turn", "-60")
    elif look == "center":
        state["local"]["look"] = "right"
        return ("turn", "60")
    elif look == "right":
        state["local"]["look"] = "back"
        return ("turn", "60")
    elif look == "back":
        state["local"]["look"] = "left"
        state["next"] = True
        state["synch"] = None
        return ("turn", "-60")
    state["next"] = True
    return None

def _can_intercept_action(taken, state):
    state["next"] = True
    ball = taken.get("ball")
    prev = taken.get("ballPrev")
    if not ball: return False
    if not prev: return True
    if ball["dist"] <= prev["dist"] + 0.5: return True
    return False

def _run_to_ball_action(taken, state):
    state["next"] = False
    ball = taken.get("ball")
    if not ball: return _go_back_action(taken, state)
    if ball["dist"] <= 2:
        state["next"] = True
        return None
    if abs(ball["angle"]) > 10:
        return ("turn", str(int(ball["angle"])))
    return ("dash", "100")

def _ok_action(taken, state):
    state["next"] = True
    return ("turn", "0")

def _empty_action(taken, state):
    state["next"] = True
    return None
