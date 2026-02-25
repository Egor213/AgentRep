import argparse
import sys

from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="RoboCup 2D agent")
    parser.add_argument("--team", type=str, default="teamA", help="Имя команды")
    parser.add_argument("--x", type=int, default=-15, help="Начальная координата X")
    parser.add_argument("--y", type=int, default=0, help="Начальная координата Y")
    parser.add_argument(
        "--rotation", type=float, default=10, help="Скорость вращения (только для lab 1)"
    )
    parser.add_argument("--goalie", action="store_true", help="Регистрация как вратарь")
    args = parser.parse_args()

    rotation = args.rotation or 0.0

    agent = Agent(
        team_name=args.team,
        is_goalie=args.goalie,
    )

    try:
        agent.run(start_pos=(args.x, args.y), rotation_speed=rotation)
    except KeyboardInterrupt:
        print("\nПрерывание по Ctrl+C")
        agent.stop()
    except Exception as e:
        print(f"Ошибка: {e}")
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
