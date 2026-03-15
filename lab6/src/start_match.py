# ===== FILE: src/start_match.py =====

"""
Запуск матча: teamA vs teamB (по 7 игроков).
    python start_match.py
"""

import subprocess
import sys
import time


def main():
    print("=" * 50)
    print("Матч: teamA vs teamB (формация 1-3-3)")
    print("=" * 50)

    print("\n--- teamA (side l) ---")
    p_a = subprocess.Popen([
        sys.executable, "start_team.py",
        "--team", "teamA",
        "--side", "l",
    ])
    time.sleep(3)

    print("\n--- teamB (side r) ---")
    p_b = subprocess.Popen([
        sys.executable, "start_team.py",
        "--team", "teamB",
        "--side", "r",
    ])

    print("\nМатч запущен! Ctrl+C для остановки.")

    try:
        p_a.wait()
        p_b.wait()
    except KeyboardInterrupt:
        print("\nОстановка матча...")
        p_a.terminate()
        p_b.terminate()
        p_a.wait()
        p_b.wait()
        print("Матч остановлен")


if __name__ == "__main__":
    main()