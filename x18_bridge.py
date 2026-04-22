from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/status")
def status():
    return jsonify({"status": "ok"})

app.run(host="0.0.0.0", port=5000)