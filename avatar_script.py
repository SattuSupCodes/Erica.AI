import bpy
import socket
import json
import threading
import time

HOST = '127.0.0.1'
PORT = 65432
last_update_time = 0
TIMEOUT = 1.0  # seconds
obj = bpy.data.objects['Head_Female']

latest_data = {"blink": 0, "mouth": 0}

def socket_listener():
    global latest_data, last_update_time

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)

    print("Blender listening...")

    conn, addr = sock.accept()
    print("Connected by", addr)

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            msg = json.loads(data.decode())
            latest_data = msg
            last_update_time = time.time()

        except Exception as e:
            print("Error:", e)
            break


def apply_updates():
    global latest_data, last_update_time
    now = time.time()

    try:
        if now - last_update_time > TIMEOUT:
            obj.data.shape_keys.key_blocks["blink"].value = 0
            obj.data.shape_keys.key_blocks["mouth-open"].value = 0
        else:
                                                                               
           if "blink" in latest_data:
                obj.data.shape_keys.key_blocks["blink"].value = latest_data["blink"]

           if "mouth" in latest_data:
                obj.data.shape_keys.key_blocks["mouth-open"].value = latest_data["mouth"]
                
    except Exception as e:
        print("Update error:", e)

    return 0.05  


threading.Thread(target=socket_listener, daemon=True).start()


bpy.app.timers.register(apply_updates)