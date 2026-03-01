import time
from socket_client import SocketClient
from msg_parser import MsgParser
from taken import Taken
from ta_manager import TAManager
from goalie_ta import create_goalie_ta
from attacker_ta import create_attacker_ta

class InitError(Exception):
    pass

class Agent:
    def __init__(self, team_name, version=7, is_goalie=False):
        self.team = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.side = None
        self.player_number = None
        self.game_mode = None
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        
        self.taken = Taken()
        self.ta_manager = TAManager(create_goalie_ta() if is_goalie else create_attacker_ta())
        self.start_pos = (50, 0) if is_goalie else (-15, 0)

    def connect(self):
        goalie_str = " (goalie)" if self.is_goalie else ""
        cmd = f"(init {self.team} (version {self.version}){goalie_str})"
        self.socket.send(cmd)

        start = time.time()
        while time.time() - start < 5:
            data = self.socket.receive()
            if data and self._process_init_msg(data):
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
        self.game_mode = parsed[3] if len(parsed) > 3 else None
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def process_message(self, msg: str):
        parsed = MsgParser.parse_msg(msg)
        if not parsed: return
        
        msg_type = parsed[0]
        if msg_type == "see":
            self._process_see(parsed)
        elif msg_type == "hear":
            self._process_hear(parsed)

    def _process_hear(self, parsed: list):
        if len(parsed) < 4: return
        self.taken.set_hear(parsed)
        
        sender = parsed[2]
        message = parsed[3]
        if sender == "referee":
            msg_str = str(message)
            if msg_str in ("play_on",):
                self.play_on = True
            elif msg_str.startswith("kick_off"):
                self.play_on = True
            elif msg_str.startswith("goal_"):
                self.play_on = False
                self.move(*self.start_pos)

    def _process_see(self, parsed: list):
        if not self.play_on: return
        
        taken_data = self.taken.set_see(parsed, self.team, self.side)
        decision = self.ta_manager.update(taken_data)
        
        if decision:
            cmd, val = decision
            self.socket.send(f"({cmd} {val})")

    def run(self, start_pos: tuple[int, int]):
        self.start_pos = start_pos
        self.connect()
        self.move(*start_pos)
        self.running = True
        print(f"Agent {self.team}#{self.player_number} (TA) running...")
        
        while self.running:
            data = self.socket.receive()
            if data:
                self.process_message(data)

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except: pass
