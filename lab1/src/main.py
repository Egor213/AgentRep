import argparse
import sys

from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Labs")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--x", type=int, default=-15)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument(
        "--rotation",
        type=float,
        default=10,
    )
    parser.add_argument("--goalie", action="store_true")
    args = parser.parse_args()

    rotation = args.rotation or 0.0

    agent = Agent(
        team_name=args.team,
        is_goalie=args.goalie,
    )

    try:
        agent.run(start_pos=(args.x, args.y), rotation_angel=rotation)
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(e)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
