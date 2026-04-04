from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# In-memory store: { ticker: {count, timestamp} }
store = {}

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

@app.route("/")
def home():
    return {"status": "running"}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    ticker = data.get("ticker")
    count = data.get("inside_count")

    if not ticker or count is None:
        return jsonify({"error": "invalid payload"}), 400

    # store latest signal
    store[ticker] = {
        "count": int(count),
        "time": datetime.utcnow()
    }

    return {"status": "received", "ticker": ticker}

@app.route("/send", methods=["GET"])
def send():
    if not store:
        return {"status": "no data"}

    # sort by count descending
    sorted_items = sorted(store.items(), key=lambda x: x[1]["count"], reverse=True)

    lines = []
    lines.append("📊 Inside Bars – Daily\n")
    lines.append("Ticker | Count")
    lines.append("------ | -----")

    for ticker, data in sorted_items:
        lines.append(f"{ticker} | {data['count']}")

    message = "\n".join(lines)

    requests.post(DISCORD_WEBHOOK, json={"content": message})

    store.clear()

    return {"status": "sent", "count": len(sorted_items)}