from flask import Flask, jsonify
import time
import requests
app = Flask(__name__)

LB_URL = "http://localhost/compute"

@app.route("/rt_stats")
def rt():
    start = time.time()
    try:
        requests.get(LB_URL)
    except:
        return jsonify({"error": "request failed"})
    end = time.time()

    return jsonify({
        "response_time_ms": (end - start) * 1000
    })

app.run(host="0.0.0.0", port=9200)

