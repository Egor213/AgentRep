FL = "flag"
KI = "kick"


def create_player_tree(actions: list[dict]):

    tree = {
        # Состояние дерева(игрока)
        "state": {
            "next": 0,
            "sequence": actions,
            "action": None,
            "command": None,
            "teammate_dist": 9999,
            "teammate_angle": 0,
        },

        # Корень (exec узел)
        "root": {
            "exec": lambda mgr, state: _root_exec(mgr, state),
            "next": "checkTeammates",
        },

        # Выбор роли (cond узел)
        "checkTeammates": {
            "condition": lambda mgr, state: mgr.getTeammateCount() == 0,
            "trueCond": "leaderGoalVisible",   # не вижу никого -> я ведущий
            "falseCond": "followerInit",        # вижу тиммейта -> я ведомый
        },

        # ВЕДУЩИЙ

        # Проверка видимости объекта из action
        "leaderGoalVisible": {
            "condition": lambda mgr, state: mgr.getVisible(state["action"]["fl"]),
            "trueCond": "leaderRootNext", # цель видна
            "falseCond": "leaderRotate", # цель не видна
        },

        # Поворот, если цель не видна
        "leaderRotate": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "90")),
            "next": "sendCommand",
        },

        # Проверка на тип действия. Флаги или мяч
        "leaderRootNext": {
            "condition": lambda mgr, state: state["action"]["act"] == FL,
            "trueCond": "flagSeek", # Флаг
            "falseCond": "ballSeek", # Мяч
        },

        # ДЕЙСТВИЯ С ФЛАГОМ

        # Расстояние до флага
        "flagSeek": {
            "condition": lambda mgr, state: mgr.getDistance(state["action"]["fl"]) < 3,
            "trueCond": "closeFlag", # Флаг можно взять
            "falseCond": "farGoal", # Флаг нельзя взять
        },

        # Берем флаг
        "closeFlag": {
            "exec": lambda mgr, state: _advance_target(state),
            "next": "leaderRootNext",
        },

        # Проверка направления к цели
        "farGoal": {
            "condition": lambda mgr, state: abs(mgr.getAngle(state["action"]["fl"])) > 4,
            "trueCond": "rotateToGoal",
            "falseCond": "runToGoal",
        },

        # Поворот к цели
        "rotateToGoal": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle(state["action"]["fl"]))))
            ),
            "next": "sendCommand",
        },

        # Бег к цели
        "runToGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "100")),
            "next": "sendCommand",
        },

        # ДЕЙСТВИЯ С МЯЧОМ

        # Расстояние до мяча
        "ballSeek": {
            "condition": lambda mgr, state: mgr.getDistance(state["action"]["fl"]) < 0.7,
            "trueCond": "closeBall",
            "falseCond": "farGoal",
        },

        # Проверка видимости ворот 
        "closeBall": {
            "condition": lambda mgr, state: mgr.getVisible(state["action"].get("goal", "gr")),
            "trueCond": "ballGoalVisible",
            "falseCond": "ballGoalInvisible",
        },

        # Удар если ворота видны
        "ballGoalVisible": {
            "exec": lambda mgr, state: state.__setitem__(
                "command",
                ("kick", f"100 {int(mgr.getAngle(state['action'].get('goal', 'gr')))}")
            ),
            "next": "sendCommand",
        },

        # Удар вслепую по 45 градусов
        "ballGoalInvisible": {
            "exec": lambda mgr, state: state.__setitem__("command", ("kick", "10 45")),
            "next": "sendCommand",
        },

        # ВЕДОМЫЙ
        
        # Вычисление параметров ближайшего тиммейта
        "followerInit": {
            "exec": lambda mgr, state: _compute_follower_vars(mgr, state),
            "next": "followerTooClose",
        },

        # 3.2: dist < 1 и |angle| < 40, тогда turn 30
        "followerTooClose": {
            "condition": lambda mgr, state: (
                state["teammate_dist"] < 1
                and abs(state["teammate_angle"]) < 40
            ),
            "trueCond": "followerAvoidCollision",
            "falseCond": "followerCheckFar",
        },
        
        # Поворот на 30 градусов
        "followerAvoidCollision": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "30")),
            "next": "sendCommand",
        },

        # 3.3: dist > 10, то followerFarApproach, иначе followerCheckAngle
        "followerCheckFar": {
            "condition": lambda mgr, state: state["teammate_dist"] > 10,
            "trueCond": "followerFarApproach",
            "falseCond": "followerCheckAngle",
        },

        # 3.3.1: |angle| > 5, то turn на angle, иначе dash 80
        "followerFarApproach": {
            "condition": lambda mgr, state: abs(state["teammate_angle"]) > 5,
            "trueCond": "followerFarTurn",
            "falseCond": "followerFarDash",
        },

        # turn на angle
        "followerFarTurn": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(state["teammate_angle"])))
            ),
            "next": "sendCommand",
        },

        # dash 80
        "followerFarDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")),
            "next": "sendCommand",
        },

        # 3.4: angle > 40 или angle < 25, то turn angle-30, иначе followerCheckDist
        "followerCheckAngle": {
            "condition": lambda mgr, state: (
                state["teammate_angle"] > 40
                or state["teammate_angle"] < 25
            ),
            "trueCond": "followerAdjustAngle",
            "falseCond": "followerCheckDist",
        },

        # turn -30 
        "followerAdjustAngle": {
            "exec": lambda mgr, state: state.__setitem__(
                "command",
                ("turn", str(int(state["teammate_angle"] - 30)))
            ),
            "next": "sendCommand",
        },

        # 3.5: dist < 7, то dash 20, иначе dash 40
        "followerCheckDist": {
            "condition": lambda mgr, state: state["teammate_dist"] < 7,
            "trueCond": "followerSlowDash",
            "falseCond": "followerMediumDash",
        },

        "followerSlowDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "20")),
            "next": "sendCommand",
        },

        "followerMediumDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "40")),
            "next": "sendCommand",
        },

        # Отправка комманды
        "sendCommand": {
            "command": lambda mgr, state: state["command"],
        },
    }

    return tree


def _root_exec(mgr, state):
    """Инициализация: текущая цель, сброс команды."""
    if state["next"] >= len(state["sequence"]):
        state["next"] = 0
    state["action"] = state["sequence"][state["next"]]
    state["command"] = None


def _advance_target(state):
    state["next"] += 1
    if state["next"] >= len(state["sequence"]):
        state["next"] = 0
    state["action"] = state["sequence"][state["next"]]


def _compute_follower_vars(mgr, state):
    # Вычисляем ближайшего тиммейта
    closest = mgr.getClosestTeammate()
    if closest:
        _, obj = closest
        state["teammate_dist"] = obj.get("dist", 9999)
        state["teammate_angle"] = obj.get("dir", 0)
    else:
        state["teammate_dist"] = 9999
        state["teammate_angle"] = 0
    state["command"] = None