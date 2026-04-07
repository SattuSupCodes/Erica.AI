import socket
import json
import random
import time

class ExpressionController:
    def __init__(self, sock):
        self.sock = sock
        self.last_blink = time.time()

    def send(self, blink=0, mouth=0):
        data = {
            "blink": blink,
            "mouth": mouth
        }
        try:
            self.sock.send(json.dumps(data).encode())
        except:
            pass

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
        self.current_mouth = getattr(self, "current_mouth", 0)
        target = random.uniform(0.1,0.2)
        self.current_mouth += (target - self.current_mouth)*0.2
        self.send(mouth = self.current_mouth)

    def speaking(self):
        self.current_mouth = getattr(self, "current_mouth", 0)
        target = random.uniform(0.3,0.6)
        self.current_mouth += (target - self.current_mouth)*0.3
        self.send(mouth = self.current_mouth)
    def apply(self,state):
        if state == "idle":
            self.idle()
        elif state == "thinking":
            self.thinking()
        elif state == "speaking":
            self.speaking()