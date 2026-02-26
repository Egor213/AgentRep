import argparse
import sys
from controller import Controller

from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Labs")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--x", type=int, default=-15)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--goalie", action="store_true")
    args = parser.parse_args()

    actions = [
        {"act": "flag", "fl": "frb"},
        # {"act": "flag", "fl": "gl"},
        # {"act": "flag", "fl": "fc"}, float division by zero словил)))
        {"act": "kick", "fl": "b", "goal": "gr"},
    ]
    controller = Controller(actions)

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
