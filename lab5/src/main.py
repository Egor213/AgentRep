import argparse
import json
import sys
from controller import Controller

from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Labs")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--x", type=int, default=-15)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--goalie", action="store_true")
    parser.add_argument('--actions', type=str)
    args = parser.parse_args()

    if args.actions:
        actions = json.loads(args.actions)
    else:
        actions = []

    controller = Controller(
        actions,
        is_goalie=args.goalie
    )

    agent = Agent(
        team_name=args.team,
        is_goalie=args.goalie,
        controller=controller,
    )

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
