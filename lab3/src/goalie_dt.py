

def create_goalie_tree():
    tree = {
        "state": {
            "command": None,
            "ball_dist": 9999,
            "ball_angle": 0,
        },

        # ==================== root ====================
        "root": {
            "exec": lambda mgr, state: state.__setitem__("command", None),
            "next": "checkBallVisible",
        },

        # ========== Виден ли мяч? ==========
        "checkBallVisible": {
            "condition": lambda mgr, state: mgr.getVisible("b"),
            "trueCond": "updateBallInfo",
            "falseCond": "goToGoal",
        },

        "updateBallInfo": {
            "exec": lambda mgr, state: _update_ball_info(mgr, state),
            "next": "checkBallClose",
        },

        # ========== Мяч близко? (< 15) ==========
        "checkBallClose": {
            "condition": lambda mgr, state: state["ball_dist"] < 15,
            "trueCond": "ballCloseLogic",
            "falseCond": "goToGoal",
        },

        # ========== Логика близкого мяча ==========
        "ballCloseLogic": {
            "condition": lambda mgr, state: state["ball_dist"] < 2,
            "trueCond": "checkBallKickable",
            "falseCond": "checkBallKickable",
        },

        "tryCatch": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("catch", str(int(state["ball_angle"])))
            ),
            "next": "sendCommand",
        },

        "checkBallKickable": {
            "condition": lambda mgr, state: state["ball_dist"] < 0.7,
            "trueCond": "kickBall",
            "falseCond": "approachBall",
        },

        # --- Удар от ворот ---
        "kickBall": {
            "condition": lambda mgr, state: mgr.getVisible("gl"),
            "trueCond": "kickToGl",
            "falseCond": "kickToFltOrFlb",
        },

        "kickToGl": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"100 {int(mgr.getAngle('gl'))}")
            ),
            "next": "sendCommand",
        },

        "kickToFltOrFlb": {
            "condition": lambda mgr, state: mgr.getVisible("flt"),
            "trueCond": "kickToFlt",
            "falseCond": "kickToFlbOrWeak",
        },

        "kickToFlt": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"80 {int(mgr.getAngle('flt'))}")
            ),
            "next": "sendCommand",
        },

        "kickToFlbOrWeak": {
            "condition": lambda mgr, state: mgr.getVisible("flb"),
            "trueCond": "kickToFlb",
            "falseCond": "kickWeak",
        },

        "kickToFlb": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"80 {int(mgr.getAngle('flb'))}")
            ),
            "next": "sendCommand",
        },

        "kickWeak": {
            "exec": lambda mgr, state: state.__setitem__("command", ("kick", "30 90")),
            "next": "sendCommand",
        },

        # --- Приблизиться к мячу ---
        "approachBall": {
            "condition": lambda mgr, state: abs(state["ball_angle"]) > 5,
            "trueCond": "turnToBall",
            "falseCond": "dashToBall",
        },

        "turnToBall": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(state["ball_angle"])))
            ),
            "next": "sendCommand",
        },

        "dashToBall": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")),
            "next": "sendCommand",
        },

        # ==========================================================
        #  Возврат к воротам
        # ==========================================================
        "goToGoal": {
            "condition": lambda mgr, state: mgr.getVisible("gr"),
            "trueCond": "checkGoalDist",
            "falseCond": "searchGoal",
        },

        "searchGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")),
            "next": "sendCommand",
        },

        "checkGoalDist": {
            "condition": lambda mgr, state: mgr.getDistance("gr") > 5,
            "trueCond": "moveToGoal",
            "falseCond": "positionInGoal",
        },

        "moveToGoal": {
            "condition": lambda mgr, state: abs(mgr.getAngle("gr")) > 5,
            "trueCond": "turnToGoal",
            "falseCond": "dashToGoal",
        },

        "turnToGoal": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle("gr"))))
            ),
            "next": "sendCommand",
        },

        "dashToGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")),
            "next": "sendCommand",
        },

        # --- Позиционирование в воротах ---
        "positionInGoal": {
            "condition": lambda mgr, state: _need_adjustment(mgr),
            "trueCond": "adjustPosition",
            "falseCond": "faceBall",
        },

        "adjustPosition": {
            "exec": lambda mgr, state: _adjust_position(mgr, state),
            "next": "sendCommand",
        },

        # --- Смотреть на мяч ---
        "faceBall": {
            "condition": lambda mgr, state: mgr.getVisible("b"),
            "trueCond": "faceBallCheck",
            "falseCond": "faceBallSearch",
        },

        "faceBallCheck": {
            "condition": lambda mgr, state: abs(mgr.getAngle("b")) > 5,
            "trueCond": "turnFaceBall",
            "falseCond": "standStill",
        },

        "turnFaceBall": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle("b"))))
            ),
            "next": "sendCommand",
        },

        "faceBallSearch": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "30")),
            "next": "sendCommand",
        },

        "standStill": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "1")),
            "next": "sendCommand",
        },

        # ========== Отправка команды ==========
        "sendCommand": {
            "command": lambda mgr, state: state["command"],
        },
    }
    return tree


def _update_ball_info(mgr, state):
    state["ball_dist"] = mgr.getDistance("b")
    state["ball_angle"] = mgr.getAngle("b")


def _need_adjustment(mgr):
    """Нужна ли корректировка позиции в воротах (по fprc)."""
    if mgr.getVisible("fprc"):
        d = mgr.getDistance("fprc")
        if d < 10 or d > 18:
            return True
        if abs(mgr.getAngle("fprc")) > 30:
            return True
    return False


def _adjust_position(mgr, state):
    """Корректировка позиции вратаря."""
    if mgr.getVisible("fprc"):
        d = mgr.getDistance("fprc")
        angle = mgr.getAngle("fprc")
        if d > 18:
            if mgr.getVisible("gr") and abs(mgr.getAngle("gr")) > 5:
                state["command"] = ("turn", str(int(mgr.getAngle("gr"))))
            else:
                state["command"] = ("dash", "50")
        elif d < 10:
            state["command"] = ("dash", "-30")
        elif abs(angle) > 30:
            state["command"] = ("turn", str(int(angle / 2)))
        else:
            state["command"] = ("turn", "1")
    else:
        state["command"] = ("turn", "30")