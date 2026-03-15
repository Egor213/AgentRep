# ===== FILE: src/main.py =====

import argparse
import sys

from agent import Agent
from ctrl_low import CtrlLow
from ctrl_mid import CtrlMid
from ctrl_high_goalie import CtrlHighGoalie
from ctrl_high_defender import CtrlHighDefender
from ctrl_high_midfielder import CtrlHighMidfielder
from ctrl_high_forward import CtrlHighForward


def create_agent(team, role, x, y, is_goalie=False, zone="center"):
    """Создаёт агента с иерархическим контроллером для заданной роли."""
    home_pos = (x, y)
    side = "l"  # Будет обновлено после init

    low = CtrlLow(team=team, side=side, player_number=0, role=role)
    mid = CtrlMid(home_pos=home_pos, role=role, side=side)

    if is_goalie:
        high = CtrlHighGoalie(side=side)
    elif role == "defender":
        high = CtrlHighDefender(side=side, home_pos=home_pos)
    elif role == "midfielder":
        high = CtrlHighMidfielder(side=side, home_pos=home_pos, zone=zone)
    elif role == "forward":
        high = CtrlHighForward(side=side, home_pos=home_pos, zone=zone)
    else:
        high = CtrlHighMidfielder(side=side, home_pos=home_pos)

    controllers = [low, mid, high]

    agent = Agent(
        team_name=team,
        controllers=controllers,
        is_goalie=is_goalie,
        role=role,
        home_pos=home_pos,
    )

    return agent


def main():
    parser = argparse.ArgumentParser(description="Lab 6: Team Play")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--role", type=str, default="midfielder",
                        choices=["goalie", "defender", "midfielder", "forward"])
    parser.add_argument("--x", type=float, default=-15)
    parser.add_argument("--y", type=float, default=0)
    parser.add_argument("--zone", type=str, default="center",
                        choices=["center", "left", "right"])
    args = parser.parse_args()

    is_goalie = args.role == "goalie"
    agent = create_agent(args.team, args.role, args.x, args.y, is_goalie, args.zone)

    try:
        agent.run(start_pos=(args.x, args.y))
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(e)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()