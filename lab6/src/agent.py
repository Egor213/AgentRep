import time
from socket_client import SocketClient
from msg_parser import MsgParser
from taken import Taken
from ctrl_low import CtrlLow
from ctrl_middle import CtrlMiddle
from ctrl_high import CtrlHigh

class InitError(Exception):
    pass

class Agent:
    def __init__(self, team_name, version=7, is_goalie=False):
        self.team = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.side = None
        self.player_number = None
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        
        self.taken = Taken()
        self.controllers = [CtrlLow(), CtrlMiddle(), CtrlHigh()]
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
            raise InitError("Init failed")

    def _process_init_msg(self, data: str) -> bool:
        parsed = MsgParser.parse_msg(data)
        if not parsed or parsed[0] != "init": return False
        self.side = parsed[1]
        self.player_number = parsed[2]
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def process_message(self, msg: str):
        parsed = MsgParser.parse_msg(msg)
        if not parsed: return
        if parsed[0] == "see":
            self._process_see(parsed)
        elif parsed[0] == "hear":
            self._process_hear(parsed)

    def _process_hear(self, parsed: list):
        if len(parsed) < 4: return
        self.taken.set_hear(parsed)
        if parsed[2] == "referee":
            msg = str(parsed[3])
            if msg == "play_on": self.play_on = True
            elif msg.startswith("goal_"):
                self.play_on = False
                self.move(*self.start_pos)

    def _process_see(self, parsed: list):
        if not self.play_on: return
        input_data = self.taken.set_see(parsed, self.team, self.side)
        
        # Execute hierarchical controller
        decision = self.controllers[0].execute(input_data, self.controllers[1:])
        
        if decision:
            cmd, val = decision
            self.socket.send(f"({cmd} {val})")

    def run(self, start_pos: tuple[int, int]):
        self.start_pos = start_pos
        self.connect()
        self.move(*start_pos)
        self.running = True
        while self.running:
            data = self.socket.receive()
            if data: self.process_message(data)

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except: pass
