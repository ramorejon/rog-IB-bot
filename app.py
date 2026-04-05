from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import logging
import sys

app = Flask(__name__)

# In-memory store: { ticker: {count, timestamp} }
store = {}

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
OUTPUT_FORMAT = os.environ.get("OUTPUT_FORMAT", "code")  # code | embed | image

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

@app.route("/sendX", methods=["GET"])
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
    response = requests.post(DISCORD_WEBHOOK, json={"content": "test message"})

    #logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
    #logging.info("hello world")

    if response.status_code == 204:
        print("Message sent successfully!", flush=True)
        logging.info("Message sent successfully!")
    else:
        print(f"Failed to send: {response.status_code} - {response.text}", flush=True)
        logging.info(f"Failed to send: {response.status_code} - {response.text}")

    store.clear()

    return {"content": message}
#    return {"status": "sent", "count": len(sorted_items), "msg": message}



@app.route("/send", methods=["GET"])
def send():
    if not store:
        return {"status": "no data"}

    sorted_items = sorted(store.items(), key=lambda x: x[1]["count"], reverse=True)

    if OUTPUT_FORMAT == "embed":
        send_embed(sorted_items)
    elif OUTPUT_FORMAT == "image":
        send_image(sorted_items)
    else:
        send_code_block(sorted_items)

    store.clear()

    return {"status": "sent", "count": len(sorted_items)}


# ---------------------------
# FORMATTERS
# ---------------------------

def send_code_block(data):
    lines = []
    lines.append("📊 Inside Bars – Daily\n")
    lines.append("```")
    lines.append(f"{'Ticker':<8} {'Count':>5}")
    lines.append(f"{'-'*8} {'-'*5}")

    for ticker, d in data:
        lines.append(f"{ticker:<8} {d['count']:>5}")

    lines.append("```")

    message = "\n".join(lines)

    requests.post(DISCORD_WEBHOOK, json={"content": message})


def send_embed(data):
    embed = {
        "title": "📊 Inside Bars – Daily",
        "color": 5814783,
        "fields": []
    }

    for ticker, d in data:
        embed["fields"].append({
            "name": ticker,
            "value": f"{d['count']}",
            "inline": True
        })

    requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})


def send_image(data):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.axis('off')

    table_data = [["Ticker", "Count"]]
    for ticker, d in data:
        table_data.append([ticker, d["count"]])

    table = ax.table(cellText=table_data, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    plt.savefig("table.png", bbox_inches='tight')
    plt.close()

    with open("table.png", "rb") as f:
        requests.post(DISCORD_WEBHOOK, files={"file": f})






