# import socket
# import json
# import time
# import random

# HOST = '127.0.0.1'
# PORT = 65432

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect((HOST, PORT))

# print("Connected to Blender")

# while True:
#     blink = 1 if random.random() < 0.1 else 0
#     mouth = random.uniform(0.2, 0.6)

#     data = {
#         "blink": blink,
#         "mouth": mouth
#     }

#     sock.send(json.dumps(data).encode())
#     time.sleep(0.2)