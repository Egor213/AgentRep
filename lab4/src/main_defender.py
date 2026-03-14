import argparse
import sys
import time
from socket_client import SocketClient
from msg_parser import MsgParser


class StaticDefender:
    """
    Статичный защитник для teamB.
    Занимает позицию и старается оставаться на месте через dash 0 и turn 0.
    """

    def __init__(self, team_name, pos_x, pos_y, version=7):
        self.team = team_name
        self.version = version
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.socket = SocketClient()
        self.running = False
        self.player_number = None
        self.side = None
        self.play_on = False
        self.at_position = False

    def connect(self):
        cmd = f"(init {self.team} (version {self.version}))"
        self.socket.send(cmd)

        start = time.time()
        while time.time() - start < 5:
            data = self.socket.receive()
            if data and self._process_init_msg(data):
                break
        else:
            self.stop()
            raise Exception("Не удалось получить подтверждение инициализации от сервера")

    def _process_init_msg(self, data: str) -> bool:
        parsed = MsgParser.parse_msg(data)
        if not parsed or parsed[0] != "init":
            return False
        self.side = parsed[1]
        self.player_number = parsed[2]
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def dash(self, power):
        self.socket.send(f"(dash {power})")

    def turn(self, angle):
        self.socket.send(f"(turn {angle})")

    def run(self):
        self.connect()
        # Перемещаемся на позицию до play_on
        self.move(self.pos_x, self.pos_y)
        print(f"Защитник {self.team} #{self.player_number}: цель ({self.pos_x}, {self.pos_y})")

        self.running = True
        while self.running:
            data = self.socket.receive()
            if data:
                parsed = MsgParser.parse_msg(data)
                if not parsed:
                    continue
                    
                if parsed[0] == "see":
                    # После play_on используем dash 0 для стояния на месте
                    if self.play_on:
                        # Отправляем dash 0 для минимизации движения
                        self.dash(0)
                        
                elif parsed[0] == "hear":
                    if len(parsed) >= 4 and parsed[2] == "referee":
                        msg = str(parsed[3])
                        if msg.startswith("play_on"):
                            self.play_on = True
                            # Пытаемся занять позицию прямо перед стартом
                            self.move(self.pos_x, self.pos_y)
                            print("play_on - защитник на позиции")
                        elif msg.startswith("goal_") or msg.startswith("kick_off"):
                            self.play_on = False
                            # После гола снова используем move
                            self.move(self.pos_x, self.pos_y)
                            print(f"Защитник возврат на позицию ({self.pos_x}, {self.pos_y})")

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Lab 4: Static Defender")
    parser.add_argument("--team", type=str, default="teamB")
    parser.add_argument("--x", type=float, default=47.0)
    parser.add_argument("--y", type=float, default=6.0)
    args = parser.parse_args()

    agent = StaticDefender(
        team_name=args.team,
        pos_x=args.x,
        pos_y=args.y,
    )

    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(e)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
