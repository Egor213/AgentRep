def create_defender_tree():
    """
    Дерево решений для защитника команды противника (teamB).
    Защитник стоит на месте у своих ворот независимо от сообщений сервера.
    Согласно заданию 4.2: два игрока противника должны стоять на месте
    около каждой штанги для предотвращения offside.
    """
    tree = {
        "state": {
            "status": "stand",  # всегда стоит на позиции
            "command": None,
        },
        "root": {
            "exec": lambda mgr, state: _root_exec(mgr, state),
            "next": "standGuard",
        },
        "standGuard": {
            "exec": lambda mgr, state: _stand_exec(mgr, state),
            "next": "sendCommand",
        },
        "sendCommand": {
            "command": lambda mgr, state: state["command"],
        }
    }
    return tree


def _root_exec(mgr, state):
    state["command"] = None


def _stand_exec(mgr, state):
    # Защитник просто стоит на месте, возможно небольшие повороты для "оживления"
    # Команда turn с минимальным углом или dash 0 для имитации стояния
    state["command"] = ("turn", "0")
