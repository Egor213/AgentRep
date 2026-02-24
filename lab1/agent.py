import time
from socket_client import SocketClient
from flags import FLAGS
from msg_parser import MsgParser


class InitError(Exception):
    pass

class Agent:
    def __init__(self, team_name, version=7, is_goalie=False):
        self.team = team_name
        self.version = version
        self.running = False
        self.is_goalie = is_goalie
        self.side = None
        self.player_number = None
        self.game_mode = None
        self.socket = SocketClient()

    def connect(self):
        cmd = f"(init {self.team} (version {self.version}))"
        self.socket.send(cmd)

        start = time.time()
        while time.time() - start < 3:
            data = self.socket.receive()
            if self._process_init_msg(data):
                break
        else:
            self.stop()
            raise InitError("Не удалось получить подтверждение инициализации от сервера")

    def _process_init_msg(self, data: str) -> bool:
        parsed = MsgParser.parse_msg(data)
        if not parsed or parsed[0] != "init":
            return False
        
        self.side = parsed[1]
        self.player_number = parsed[2]
        self.game_mode = parsed[3]

        return True


    def move(self, x: str | int, y: str | int):
        """
        До начала игры или после гола.
        -54 <= x <= 54
        -32 <= y <= 32
        """
        cmd = f"(move {x} {y})"
        self.socket.send(cmd)


    def turn(self, moment: str | int):
        """
        Повернуться относительно текущего положения.
        -180 <= moment <= 180
        """
        cmd = f"(turn {moment})"
        self.socket.send(cmd)

    def turn_neck(self, moment: str | int):
        """
        Поворот головы
        """
        cmd = f"(turn_neck {moment})"
        self.socket.send(cmd)

    def kick(self, power: str | int, direction: str | int):
        """
        Пнуть мяч.
        -100 <= power <= 100
        """
        cmd = f"(kick {power} {direction})"
        self.socket.send(cmd)

    def catch(self, direction: str | int):
        """
        Поймать мяч. Только для вратаря, расстояние до мяча не меньше 2.
        -180 <= direction <= 180
        """
        cmd = f"(catch {direction})"
        self.socket.send(cmd)

    def dash(self, power: str | int):
        """
        Дает ускорение игроку в направлении тела.
        -100 <= power <= 100
        """
        cmd = f"(turn_neck {power})"
        self.socket.send(cmd)

    def say(self, msg: str):
        """
        Передать аудиосообщение.
        """
        cmd = f"(say {msg})"
        self.socket.send(cmd)

    def process_message(self, msg: str):
        parsed = MsgParser.parse_msg(msg)
        if parsed[0] == "see":
            _, _, *flags = parsed
            for flag_info in flags:
                flag_name = "".join(map(str, flag_info[0]))
                x, y = FLAGS[flag_name]



    def run(self, start_pos: tuple[int, int]):
        self.connect()
        self.move(*start_pos)
        self.running = True

        while self.running:
            data = self.socket.receive()
            self.process_message(data)




    def stop(self):
        self.running = False
        self.socket.send("(bye)")
        self.socket.close()