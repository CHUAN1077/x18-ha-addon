from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import threading

X18_IP = "192.168.1.9"  # CAMBIAR

client = SimpleUDPClient(X18_IP, 10024)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

state = {"vu": {}, "fader": {}}

# =============================
# CONTROL
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

@app.route("/api/x18/bus/<ch>/<bus>", methods=["POST"])
def bus(ch, bus):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/mix/{bus}/level", v)
    return jsonify(ok=True)

@app.route("/api/x18/eq/<ch>/<band>", methods=["POST"])
def eq(ch, band):
    v = float(request.json["value"])
    client.send_message(f"/ch/{ch}/eq/{band}/g", v)
    return jsonify(ok=True)

# =============================
# OSC RECEIVE
# =============================

def meter_handler(addr, *args):
    ch = addr.split("/")[2]
    val = args[0]
    state["vu"][ch] = val
    socketio.emit("vu", {"ch": ch, "value": val})

dispatcher = Dispatcher()
dispatcher.map("/meters/*", meter_handler)

def start_osc():
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 9000), dispatcher)
    server.serve_forever()

threading.Thread(target=start_osc, daemon=True).start()

@app.route("/status")
def status():
    return jsonify(state)

socketio.run(app, host="0.0.0.0", port=5000)