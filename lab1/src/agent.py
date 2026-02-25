# ===== FILE: src/agent.py =====

import time
import math
from socket_client import SocketClient
from flags import FLAGS, obj_name_to_key
from msg_parser import MsgParser
from geometry import (
    compute_position_two_flags,
    compute_position_three_flags,
    compute_object_position,
)


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

        self.running = False

        self.rotation_speed = 0.0

        self.x = None
        self.y = None

        self.visible_objects = {}

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
        """
        До начала игры или после гола.
        -54 <= x <= 54
        -32 <= y <= 32
        """
        self.socket.send(f"(move {x} {y})")

    def turn(self, moment):
        """
        Повернуться относительно текущего положения.
        -180 <= moment <= 180
        """
        self.socket.send(f"(turn {moment})")

    def dash(self, power):
        """
        Дает ускорение игроку в направлении тела.
        -100 <= power <= 100
        """
        self.socket.send(f"(dash {power})")

    def kick(self, power, direction):
        """
        Пнуть мяч.
        -100 <= power <= 100
        """
        self.socket.send(f"(kick {power} {direction})")

    def catch_ball(self, direction):
        """
        Поймать мяч. Только для вратаря, расстояние до мяча не меньше 2.
        -180 <= direction <= 180
        """
        self.socket.send(f"(catch {direction})")

    def say(self, msg):
        """
        Передать аудиосообщение.
        """
        self.socket.send(f"(say {msg})")

    def turn_neck(self, angle):
        """
        Поворот головы
        """
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
        elif msg_type == "sense_body":
            self._process_sense_body(parsed)

    def _process_hear(self, parsed: list):
        pass

    def _process_sense_body(self, parsed: list):
        pass

    def _process_see(self, parsed: list):
        """
        ['see', 0, [['f', 'c'], 15, 0, 0, 0], [['f', 'r', 't'], 75.9, -27], 
        [['f', 'r', 'b'], 75.9, 27], [['f', 'g', 'r', 'b'], 68, 6], 
        [['g', 'r'], 67.4, 0], [['f', 'g', 'r', 't'], 68, -6], 
        [['f', 'p', 'r', 'b'], 54.6, 22], [['f', 'p', 'r', 'c'], 50.9, 0], 
        [['f', 'p', 'r', 't'], 54.6, -22], [['f', 't', 'r', 30], 59.7, -41],
        [['f', 't', 'r', 40], 67.4, -35], [['f', 't', 'r', 50], 75.9, -31], 
        [['f', 'b', 'r', 30], 59.7, 41], [['f', 'b', 'r', 40], 67.4, 35], 
        [['f', 'b', 'r', 50], 75.9, 31], [['f', 'r', 0], 72.2, 0], 
        [['f', 'r', 't', 10], 73, -8], [['f', 'r', 't', 20], 75.2, -15], 
        [['f', 'r', 't', 30], 78.3, -22], [['f', 'r', 'b', 10], 73, 8], 
        [['f', 'r', 'b', 20], 75.2, 15], [['f', 'r', 'b', 30], 78.3, 22], 
        [['b'], 14.9, 0, 0, 0], [['l', 'r'], 67.4, 90]]
        """
        if len(parsed) < 2:
            return

        see_time = parsed[1]
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
            entry = {"name": obj_name_raw}

            if len(params) >= 1:
                entry["dist"] = float(params[0])
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


    def _compute_my_position(self):
        flag_observations = []
        for key, obj in self.visible_objects.items():
            if key in FLAGS and "dist" in obj:
                flag_observations.append((key, obj["dist"]))

        if len(flag_observations) < 2:
            return

        flag_observations.sort(key=lambda fo: fo[1])

        f1_key, d1 = flag_observations[0]
        f2_key, d2 = flag_observations[1]

        if len(flag_observations) >= 3:
            f3_key, d3 = flag_observations[2]
            pos = compute_position_three_flags(f1_key, d1, f2_key, d2, f3_key, d3)
            if pos is None:
                pos = compute_position_two_flags(f1_key, d1, f2_key, d2, f3_key, d3)
        else:
            pos = compute_position_two_flags(f1_key, d1, f2_key, d2)

        if pos:
            self.x, self.y = pos
            print(f"[Position] x={self.x:.2f}, y={self.y:.2f}")


    def _compute_objects_positions(self):
        if self.x is None or self.y is None:
            return

        flag_for_ref = None
        for key, obj in self.visible_objects.items():
            if key in FLAGS and "dist" in obj and "dir" in obj:
                flag_for_ref = (key, obj["dist"], obj["dir"])
                break

        if flag_for_ref is None:
            return

        fk, fd, fa = flag_for_ref

        for key, obj in self.visible_objects.items():
            if key in FLAGS:
                continue
            if "dist" not in obj or "dir" not in obj:
                continue

            obj_dist = obj["dist"]
            obj_dir = obj["dir"]

            pos = compute_object_position(self.x, self.y, fk, fd, fa, obj_dist, obj_dir)

            if pos:
                obj["computed_x"] = pos[0]
                obj["computed_y"] = pos[1]
                name_parts = obj.get("name", [])

                if name_parts and name_parts[0] == "p":
                    team = name_parts[1] if len(name_parts) > 1 else "?"
                    num = name_parts[2] if len(name_parts) > 2 else "?"
                    print(f"[Object] Игрок {team}#{num}: x={pos[0]:.2f}, y={pos[1]:.2f}")
                elif name_parts and name_parts[0] == "b":
                    print(f"[Object] Мяч: x={pos[0]:.2f}, y={pos[1]:.2f}")

    def run(self, start_pos: tuple[int, int], rotation_speed: float = 0):
        self.connect()
        self.move(*start_pos)
        self.rotation_speed = rotation_speed
        self.running = True

        print(
            f"Агент запущен. Команда: {self.team}, номер: {self.player_number}, сторона: {self.side}"
        )
        print(f"Начальная позиция: {start_pos}, скорость вращения: {rotation_speed}")

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
