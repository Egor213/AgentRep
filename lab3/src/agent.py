# ===== FILE: src/agent.py =====

import time
from socket_client import SocketClient
from flags import FLAGS, obj_name_to_key
from msg_parser import MsgParser
from geometry import (
    compute_position_two_flags,
    compute_position_three_flags,
    compute_object_position,
)
from controller import Controller


class InitError(Exception):
    pass


class Agent:
    def __init__(self, team_name, controller, version=7, is_goalie=False):
        self.team = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.side = None
        self.player_number = None
        self.game_mode = None
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        self.x = None
        self.y = None
        self.visible_objects = {}
        self.controller = controller

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

    def turn(self, moment):
        self.socket.send(f"(turn {moment})")

    def dash(self, power):
        self.socket.send(f"(dash {power})")

    def kick(self, power, direction):
        self.socket.send(f"(kick {power} {direction})")

    def catch_ball(self, direction):
        self.socket.send(f"(catch {direction})")

    def say(self, msg):
        self.socket.send(f"(say {msg})")

    def turn_neck(self, angle):
        self.socket.send(f"(turn_neck {angle})")

    def _send_command(self, cmd: str, params: str):
        self.socket.send(f"({cmd} {params})")

    def process_message(self, msg: str):
        parsed = MsgParser.parse_msg(msg)
        if not parsed:
            return
        msg_type = parsed[0]
        if msg_type == "see":
            self._process_see(parsed)
        elif msg_type == "hear":
            self._process_hear(parsed)

    def _process_hear(self, parsed: list):
        if len(parsed) < 4:
            return
        sender = parsed[2]
        message = parsed[3] if len(parsed) > 3 else ""
        if sender == "referee":
            msg_str = str(message)
            print(f"рефери говорит: {msg_str}")
            if msg_str in ("play_on",):
                self.play_on = True
            elif msg_str.startswith("kick_off"):
                self.play_on = False
            elif msg_str.startswith("goal_"):
                self.play_on = False
                self.controller.reset()

    def _process_see(self, parsed: list):
        if len(parsed) < 2:
            return

        self.visible_objects = {}

        for i in range(2, len(parsed)):
            obj_info = parsed[i]
            if not isinstance(obj_info, list) or len(obj_info) < 2:
                continue
            obj_name_raw = obj_info[0]
            params = obj_info[1:]
            if not isinstance(obj_name_raw, list):
                continue

            key = obj_name_to_key(obj_name_raw)
            entry = {"name": obj_name_raw, "dist": float(params[0])}
            if len(params) >= 2:
                entry["dir"] = float(params[1])
            if len(params) >= 3:
                entry["dist_change"] = float(params[2])
            if len(params) >= 4:
                entry["dir_change"] = float(params[3])
            if len(params) >= 5:
                entry["body_facing_dir"] = float(params[4])
            if len(params) >= 6:
                entry["head_facing_dir"] = float(params[5])

            self.visible_objects[key] = entry

        self._compute_my_position()
        self._compute_objects_positions()

        decision = self.controller.decide(
            self.visible_objects, self.play_on,
            team=self.team, side=self.side or "",
            player_number=self.player_number or 0,
            x=self.x, y=self.y,
        )
        if decision:
            cmd, params = decision
            self._send_command(cmd, params)

    def _compute_my_position(self):
        flag_observations = []
        for key, obj in self.visible_objects.items():
            if key in FLAGS:
                flag_observations.append((key, obj["dist"]))
        if len(flag_observations) < 2:
            return

        f1_key, d1 = flag_observations[0]
        f2_key, d2 = flag_observations[1]

        if len(flag_observations) >= 3:
            f3_key, d3 = flag_observations[2]
            pos = compute_position_three_flags(f1_key, d1, f2_key, d2, f3_key, d3)
            if pos is None:
                pos = compute_position_two_flags(f1_key, d1, f2_key, d2)
        else:
            pos = compute_position_two_flags(f1_key, d1, f2_key, d2)

        if pos:
            self.x, self.y = pos

    def _compute_objects_positions(self):
        if self.x is None or self.y is None:
            return
        flag_for_ref = None
        for key, obj in self.visible_objects.items():
            if key in FLAGS and "dir" in obj:
                flag_for_ref = (key, obj["dist"], obj["dir"])
                break
        if flag_for_ref is None:
            return

        fk, fd, fa = flag_for_ref
        for key, obj in self.visible_objects.items():
            if key in FLAGS or "dir" not in obj:
                continue
            pos = compute_object_position(self.x, self.y, fk, fd, fa, obj["dist"], obj["dir"])
            if pos:
                obj["computed_x"] = pos[0]
                obj["computed_y"] = pos[1]

    def run(self, start_pos: tuple[int, int]):
        self.connect()
        self.move(*start_pos)
        self.running = True
        print(
            f"Команда: {self.team}, номер: {self.player_number}, "
            f"сторона: {self.side}, позиция: {start_pos}, "
            f"вратарь: {self.is_goalie}"
        )
        while self.running:
            data = self.socket.receive()
            if data:
                self.process_message(data)

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except Exception:
            pass
        print("Агент остановлен")