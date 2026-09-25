import socket
import json
import random
import time


class BlenderLink:
    """Self-healing TCP link to the Blender avatar.

    Never raises on failure: if Blender is down or restarts, Erica keeps
    running and this silently reconnects on a backoff cadence.
    """

    def __init__(self, host="127.0.0.1", port=65432, connect_timeout=0.3, retry_interval=2.0):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.retry_interval = retry_interval
        self.sock = None
        self.last_attempt = -retry_interval

    @property
    def is_connected(self):
        return self.sock is not None

    def connect_now(self):
        now = time.time()
        if now - self.last_attempt < self.retry_interval:
            return self.sock is not None
        self.last_attempt = now
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.connect_timeout)
            s.connect((self.host, self.port))
            s.settimeout(None)
            self.sock = s
            return True
        except OSError:
            self.sock = None
            return False

    def send(self, payload):
        if self.sock is None and not self.connect_now():
            return False
        try:
            self.sock.sendall(json.dumps(payload).encode())
            return True
        except OSError:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
            return False


class ExpressionController:
    def __init__(self, host="127.0.0.1", port=65432):
        self.link = BlenderLink(host=host, port=port)
        self.last_blink = time.time()
        self.current_mouth = 0.0

    def send(self, blink=0, mouth=0):
        self.link.send({"blink": blink, "mouth": mouth})

    @property
    def is_connected(self):
        return self.link.is_connected

    def idle(self):
        now = time.time()
        if now - self.last_blink > random.uniform(2, 4):
            self.send(blink=1)
            time.sleep(0.1)
            self.send(blink=0)
            self.last_blink = now
        else:
            self.send(mouth=0)

    def thinking(self):
        target = random.uniform(0.1, 0.2)
        self.current_mouth += (target - self.current_mouth) * 0.2
        self.send(mouth=self.current_mouth)

    def speaking(self):
        target = random.uniform(0.3, 0.6)
        self.current_mouth += (target - self.current_mouth) * 0.3
        self.send(mouth=self.current_mouth)

    def apply(self, state):
        if state == "idle":
            self.idle()
        elif state == "thinking":
            self.thinking()
        elif state == "speaking":
            self.speaking()