# ===== FILE: src/main.py =====

import argparse
import sys

from agent import Agent
from ctrl_low import CtrlLow
from ctrl_mid import CtrlMid
from ctrl_high_goalie import CtrlHighGoalie
from ctrl_high_defender import CtrlHighDefender
from ctrl_high_forward import CtrlHighForward


# Позиции флагов для каждой роли в зависимости от стороны
# side "l": свои ворота слева, атакуем вправо
# side "r": свои ворота справа, атакуем влево

ROLE_CONFIG = {
    "l": {
        "goalie": {
            "home_flag": "gl",
            "start_pos": (-50, 0),
        },
        "defender_top": {
            "home_flag": "fplt",
            "start_pos": (-36, -20),
        },
        "defender_center": {
            "home_flag": "fplc",
            "start_pos": (-36, 0),
        },
        "defender_bottom": {
            "home_flag": "fplb",
            "start_pos": (-36, 20),
        },
        "forward_top": {
            "home_flag": "fct",
            "attack_flag": "fprt",
            "start_pos": (-5, -20),
        },
        "forward_center": {
            "home_flag": "fc",
            "attack_flag": "fprc",
            "start_pos": (-10, 0),
        },
        "forward_bottom": {
            "home_flag": "fcb",
            "attack_flag": "fprb",
            "start_pos": (-5, 20),
        },
    },
    "r": {
        "goalie": {
            "home_flag": "gr",
            "start_pos": (-50, 0),
        },
        "defender_top": {
            "home_flag": "fprt",
            "start_pos": (-36, 20),
        },
        "defender_center": {
            "home_flag": "fprc",
            "start_pos": (-36, 0),
        },
        "defender_bottom": {
            "home_flag": "fprb",
            "start_pos": (-36, -20),
        },
        "forward_top": {
            "home_flag": "fct",
            "attack_flag": "fplt",
            "start_pos": (-5, 20),
        },
        "forward_center": {
            "home_flag": "fc",
            "attack_flag": "fplc",
            "start_pos": (-10, 0),
        },
        "forward_bottom": {
            "home_flag": "fcb",
            "attack_flag": "fplb",
            "start_pos": (-5, -20),
        },
    },
}


def create_agent(team, role_key, side_hint="l"):
    """
    Создаёт агента. side_hint используется для определения стартовых позиций.
    Реальный side обновляется после init от сервера.
    """
    config = ROLE_CONFIG[side_hint][role_key]
    home_flag = config["home_flag"]
    start_pos = config["start_pos"]
    is_goalie = role_key == "goalie"

    # Определяем базовый тип роли
    if role_key == "goalie":
        base_role = "goalie"
    elif role_key.startswith("defender"):
        base_role = "defender"
    else:
        base_role = "forward"

    low = CtrlLow(team=team, side=side_hint, role=base_role)
    mid = CtrlMid(home_flag=home_flag, role=base_role, side=side_hint)

    if base_role == "goalie":
        high = CtrlHighGoalie(side=side_hint)
    elif base_role == "defender":
        high = CtrlHighDefender(side=side_hint, home_flag=home_flag)
    else:
        attack_flag = config.get("attack_flag", "fc")
        high = CtrlHighForward(side=side_hint, home_flag=home_flag, attack_flag=attack_flag)

    controllers = [low, mid, high]

    agent = Agent(
        team_name=team,
        controllers=controllers,
        is_goalie=is_goalie,
        role=role_key,
        home_flag=home_flag,
    )

    return agent, start_pos


def main():
    parser = argparse.ArgumentParser(description="Lab 6: Team Play")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--role", type=str, default="forward_center",
                        choices=[
                            "goalie",
                            "defender_top", "defender_center", "defender_bottom",
                            "forward_top", "forward_center", "forward_bottom",
                        ])
    parser.add_argument("--side", type=str, default="l", choices=["l", "r"],
                        help="Ожидаемая сторона (для стартовых позиций)")
    args = parser.parse_args()

    agent, start_pos = create_agent(args.team, args.role, args.side)

    try:
        agent.run(start_pos=start_pos)
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(e)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()