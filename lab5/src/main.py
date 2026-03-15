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
    parser.add_argument("--role", type=str, choices=["goalie", "attacker", "defender"], required=True)
    args = parser.parse_args()

    agent = Agent(
        team_name=args.team,
        role=args.role,
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
