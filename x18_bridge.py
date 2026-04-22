from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import threading

# =============================
# CONFIG
# =============================

X18_IP = "192.168.1.9"  # 🔥 CAMBIAR POR TU IP REAL

client = SimpleUDPClient(X18_IP, 10024)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

state = {
    "vu": {str(i): 0 for i in range(1,17)},
    "fader": {str(i): 0 for i in range(1,17)}
}

scenes = {}

# =============================
# CONTROL API
# =============================

@app.route("/api/x18/fader/<ch>", methods=["POST"])
def set_fader(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/mix/fader", v)
    state["fader"][ch] = v
    return jsonify(ok=True)

@app.route("/api/x18/mute/<ch>", methods=["POST"])
def set_mute(ch):
    client.send_message(f"/ch/{ch}/mix/on", 0)
    return jsonify(ok=True)

@app.route("/api/x18/bus/<ch>/<bus>", methods=["POST"])
def set_bus(ch, bus):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/mix/{bus}/level", v)
    return jsonify(ok=True)

@app.route("/api/x18/eq/<ch>/<band>", methods=["POST"])
def set_eq(ch, band):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/eq/{band}/g", v)
    return jsonify(ok=True)

# =============================
# DINÁMICA (GATE + COMP)
# =============================

@app.route("/api/x18/gate/<ch>", methods=["POST"])
def set_gate(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/gate/thr", v)
    return jsonify(ok=True)

@app.route("/api/x18/comp/<ch>", methods=["POST"])
def set_comp(ch):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/dyn/ratio", v)
    return jsonify(ok=True)

# =============================
# ESCENAS
# =============================

@app.route("/api/x18/scene/save/<name>", methods=["POST"])
def save_scene(name):
    scenes[name] = state.copy()
    return jsonify(ok=True)

@app.route("/api/x18/scene/load/<name>", methods=["POST"])
def load_scene(name):
    if name in scenes:
        return jsonify(scenes[name])
    return jsonify(error="not found")

# =============================
# OSC RECEIVE (VU)
# =============================

def meter_handler(addr, *args):
    try:
        ch = addr.split("/")[2]
        val = args[0]

        state["vu"][ch] = val

        socketio.emit("vu", {
            "ch": ch,
            "value": val
        })

    except:
        pass

dispatcher = Dispatcher()
dispatcher.map("/meters/*", meter_handler)

def start_osc():
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 9000), dispatcher)
    server.serve_forever()

threading.Thread(target=start_osc, daemon=True).start()

# =============================
# STATUS
# =============================

@app.route("/status")
def status():
    return jsonify(state)

# =============================
# RUN
# =============================

socketio.run(app, host="0.0.0.0", port=5000)