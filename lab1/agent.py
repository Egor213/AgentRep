import time
from socket_client import SocketClient
from flags import FLAGS
from typing import Any, Callable, Union
from msg_parser import MsgParser


class Agent:
    def __init__(self, team_name, version=7):
        self.team = team_name
        self.version = version
        self.running = False
        self.socket = SocketClient()

    def _transform_value(self, value: Any, cast_type: Callable) -> Any:
        try:
            return cast_type(value)
        except Exception:
            return value

    def connect(self):
        cmd = f"(init {self.team} (version {self.version}))"
        self.socket.send(cmd)

    def move(self, x: Union[str, int], y: Union[str, int]):
        cmd = f"(move {self._transform_value(x, str)} {self._transform_value(y, str)})"
        self.socket.send(cmd)

    def turn(self, moment: Union[str, int]):
        cmd = f"(turn {self._transform_value(moment, int)})"
        self.socket.send(cmd)

    def process_message(self, msg: str):
        print(msg)
        parsed = MsgParser.parse_msg(msg)
        print(parsed)



    def run(self):
        self.connect()
        time.sleep(0.1)
        self.running = True
            
        while self.running:
            while self.running:
                data = self.socket.receive()
                if data is None:
                    break
                self.process_message(data)

            time.sleep(0.05)

    def stop(self):
        self.running = False
        self.socket.send("(bye)")
        self.socket.close()