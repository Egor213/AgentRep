def create_attacker_ta():
    ta = {
        "current": "start",
        "state": {
            "variables": {"dist": 999, "angle": 0},
            "timers": {"t": 0},
            "next": True,
            "synch": None,
            "local": {}
        },
        "nodes": {
            "start": {"n": "start", "e": ["search", "run", "kick"]},
            "search": {"n": "search", "e": ["run"]},
            "run": {"n": "run", "e": ["kick", "search"]},
            "kick": {"n": "kick", "e": ["start"]}
        },
        "edges": {
            "start_search": [{"guard": [{"s": "gte", "l": {"v": "dist"}, "r": 999}], "assign": [{"n": "t", "v": 0, "type": "timer"}]}],
            "start_run": [{"guard": [{"s": "lt", "l": {"v": "dist"}, "r": 999}, {"s": "gt", "l": {"v": "dist"}, "r": 0.7}], "assign": [{"n": "t", "v": 0, "type": "timer"}]}],
            "start_kick": [{"guard": [{"s": "lte", "l": {"v": "dist"}, "r": 0.7}]}],
            
            "search_run": [{"guard": [{"s": "lt", "l": {"v": "dist"}, "r": 999}], "assign": [{"n": "t", "v": 0, "type": "timer"}]}],
            
            "run_kick": [{"guard": [{"s": "lte", "l": {"v": "dist"}, "r": 0.7}]}], 
            "run_search": [
                {"guard": [{"s": "gte", "l": {"v": "dist"}, "r": 999}], "assign": [{"n": "t", "v": 0, "type": "timer"}]},
                {"guard": [{"s": "gt", "l": {"t": "t"}, "r": 50}], "assign": [{"n": "t", "v": 0, "type": "timer"}]}
            ],
            
            "kick_start": [{}]
        },
        "actions": {
            "beforeAction": _before_action,
            "search": _search_action,
            "run": _run_action,
            "kick": _kick_action
        }
    }
    return ta

def _before_action(taken, state):
    if taken.get("ball"):
        state["variables"]["dist"] = taken["ball"]["dist"]
        state["variables"]["angle"] = taken["ball"]["angle"]
    else:
        state["variables"]["dist"] = 999
        state["variables"]["angle"] = 0

def _search_action(taken, state):
    # If ball is seen, let transition happen
    if state["variables"]["dist"] < 999:
        state["next"] = True
        return None
    
    # Otherwise turn to find it
    state["next"] = False
    return ("turn", "60")

def _run_action(taken, state):
    dist = state["variables"]["dist"]
    angle = state["variables"]["angle"]
    
    # Transitions
    if dist >= 999: # Lost ball
        state["next"] = True
        return None
    if dist <= 0.7: # Can kick
        state["next"] = True
        return None
    if state["timers"]["t"] > 50: # Stuck?
        state["next"] = True
        return None
        
    state["next"] = False
    if abs(angle) > 10:
        return ("turn", str(int(angle)))
    return ("dash", "80")

def _kick_action(taken, state):
    # Perform kick, then transition
    state["next"] = True
    
    goal = taken.get("goal")
    if not goal:
        pass
    
    kick_power = "100"
    kick_angle = "0"
    
    if goal:
        kick_angle = str(int(goal["angle"]))
    else:
        kick_angle = "0" # Kick forward blindly
        
    return ("kick", f"{kick_power} {kick_angle}")
