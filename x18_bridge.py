from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import threading

# =============================
# 🔴 CAMBIAR SOLO ESTO
# =============================
X18_IP = "192.168.1.9"  # 👈 HOY: IP EMULADOR / MAÑANA: X18 REAL

# =============================

client = SimpleUDPClient(X18_IP, 10024)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

state = {"vu": {}}

# =============================
# API CONTROL
# =============================

@app.route("/api/x18/fader/<ch>", methods=["POST"])
def fader(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/mix/fader", v)
    return jsonify(ok=True)

@app.route("/api/x18/mute/<ch>", methods=["POST"])
def mute(ch):
    client.send_message(f"/ch/{ch}/mix/on", 0)
    return jsonify(ok=True)

@app.route("/api/x18/gate/<ch>", methods=["POST"])
def gate(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/gate/thr", v)
    return jsonify(ok=True)

@app.route("/api/x18/comp/<ch>", methods=["POST"])
def comp(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/dyn/ratio", v)
    return jsonify(ok=True)

# =============================
# OSC RECEIVE (VU)
# =============================

def meter(addr, *args):
    ch = addr.split("/")[2]
    val = args[0]
    state["vu"][ch] = val
    socketio.emit("vu", {"ch": ch, "value": val})

dispatcher = Dispatcher()
dispatcher.map("/meters/*", meter)

def osc():
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 9000), dispatcher)
    server.serve_forever()

threading.Thread(target=osc, daemon=True).start()

@app.route("/status")
def status():
    return jsonify(state)

socketio.run(app, host="0.0.0.0", port=5000)