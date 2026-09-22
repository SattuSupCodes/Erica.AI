import bpy
import socket
import json
import threading
import time

HOST = '127.0.0.1'
PORT = 65432
TIMEOUT = 1.0  # seconds
obj = bpy.data.objects['Head_Female']

latest_data = {"blink": 0, "mouth": 0}
last_update_time = 0.0


def extract_json(buf, callback):
    """Pull complete JSON objects (possibly multiple) out of a byte buffer."""
    while True:
        try:
            end = buf.index(b"}") + 1
        except ValueError:
            return buf
        try:
            msg = json.loads(buf[:end])
        except Exception:
            buf = buf[1:]
            continue
        buf = buf[end:]
        callback(msg)


def socket_listener():
    global latest_data, last_update_time

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(4)

    print("Blender avatar listening on", HOST, PORT)

    while True:
        conn = None
        try:
            conn, addr = sock.accept()
            print("Blender avatar connected by", addr)
            buf = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk

                def on_msg(msg):
                    global latest_data, last_update_time
                    latest_data = msg
                    last_update_time = time.time()

                buf = extract_json(buf, on_msg)
        except Exception as e:
            print("Blender listener error:", e)
            time.sleep(0.2)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            latest_data = {"blink": 0, "mouth": 0}
            print("Blender avatar disconnected. Waiting for Erica to reconnect...")


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