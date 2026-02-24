import socket

class SocketClient:
    def __init__(self, host: str = "localhost", port: int = 6000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.setblocking(False)

    def send(self, msg: str) -> None:
        self.sock.sendto(msg.encode(), (self.host, self.port))

    def receive(self, bufsize: int = 4096) -> str | None:
        # try:
        #     data, _ = self.sock.recvfrom(bufsize)
        #     return data.decode()
        # except socket.error:
        #     return None
        data = self.sock.recv(bufsize)
        return data.decode()

    def close(self) -> None:
        self.sock.close()
