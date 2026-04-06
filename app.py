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
SORT_MODE = os.environ.get("SORT_MODE", "count_alpha") # count_alpha

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
    #sorted_items = sorted(store.items(), key=lambda x: x[1]["count"], reverse=True)
    sorted_items = sort_data(store)
    
    lines = []
    lines.append("📊 Inside Bars – Daily\n")
    lines.append("Ticker * Count")
    lines.append("------ * -----")

    for ticker, data in sorted_items:
        lines.append(f"{ticker} * {data['count']}")

    message = "\n".join(lines)

    sendResponse = {"content": ""}

    if OUTPUT_FORMAT == "embed":
        sendResponse = send_embed(sorted_items)
    if OUTPUT_FORMAT =="code":
        sendResponse = send_code_block(sorted_items)
    if OUTPUT_FORMAT == "image":
        sendResponse = send_image(sorted_items)

    
    return sendResponse
    
    #response = requests.post(DISCORD_WEBHOOK, json={"content": message})
    #response = discord_post(DISCORD_WEBHOOK, json={"content": "test message"})

    #logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
    #logging.info("hello world")

    #if response.status_code == 204:
    #    print("Message sent successfully!", flush=True)
    #    logging.info("Message sent successfully!")
    #else:
    #    print(f"Failed to send: {response.status_code} - {response.text}", flush=True)
    #    logging.info(f"Failed to send: {response.status_code} - {response.text}")
    #    if response.status_code == 429:
    #        logging.info({
    #            "remaining": response.headers.get("X-RateLimit-Remaining"),
    #            "reset_after": response.headers.get("X-RateLimit-Reset-After"),
    #        })

    store.clear()

    return embedResponse
#    return {"content": message}
#    return {"status": "sent", "count": len(sorted_items), "msg": message}



# ---------------------------
# FORMATTERS
# ---------------------------

def send_code_block(data):
    lines = []
    lines.append("📊 Inside Bars – Daily\n")
    lines.append("```")
    lines.append(f"{'Symbol':<9} {'xIB':>5}")
    lines.append(f"{'-'*9} {'-'*5}")

    for ticker, d in data:
        lines.append(f"{ticker:<9} {d['count']:>5}")

    lines.append("```")

    message = "\n".join(lines)

    logging.info({"content": message})

    response = {}
    for chunk in chunk_message(message):
        #discord_post(DISCORD_WEBHOOK, json={"content": chunk})
        response = requests.post(DISCORD_WEBHOOK, json={"content": chunk})


    #if response.status_code == 204:
    #    print("Message sent successfully!", flush=True)
    #    logging.info("Message sent successfully!")
    #else:
    #    print(f"Failed to send: {response.status_code} - {response.text}", flush=True)
    #    logging.info(f"Failed to send: {response.status_code} - {response.text}")
    #    if response.status_code == 429:
    #        logging.info({
    #            "remaining": response.headers.get("X-RateLimit-Remaining"),
    #            "reset_after": response.headers.get("X-RateLimit-Reset-After"),
    #        })

    success = False
    if response.status_code == 204:
        logging.info("Message sent successfully!")
        success = True
    else:
        print(f"Failed to send: {response.status_code} - {response.text}", flush=True)
        logging.info(f"Failed to send: {response.status_code} - {response.text}")
        if response.status_code == 429:
            logging.info({
                "remaining": response.headers.get("X-RateLimit-Remaining"),
                "reset_after": response.headers.get("X-RateLimit-Reset-After"),
            })

    return {"content": message, "success":  success}

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

    response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    
    if response.status_code == 204:
        logging.info("Message sent successfully!", flush=True)
        logging.info("Message sent successfully!")
    else:
        logging.info(f"Failed to send: {response.status_code} - {response.text}", flush=True)
        logging.info(f"Failed to send: {response.status_code} - {response.text}")
        logging.info({"embeds": [embed]})

    return {"embeds": [embed]}


def send_image(data):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.axis('off')

    table_data = [["Symbol", "xIB"]]
    for ticker, d in data:
        table_data.append([ticker, d["count"]])

    table = ax.table(cellText=table_data, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    plt.savefig("table.png", bbox_inches='tight')
    plt.close()

    with open("table.png", "rb") as f:
        requests.post(DISCORD_WEBHOOK, files={"file": f})

    return {"file": f}


def chunk_message(text, limit=2000):
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


import time
import requests


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {}


def discord_post(url, json=None, files=None, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=json, files=files, timeout=10)
        except requests.exceptions.RequestException as e:
            logging.info(f"[NETWORK ERROR] {e}")
            time.sleep(1)
            continue

        if response.status_code in (200, 204):
            return response

        data = safe_json(response)
        
        logging.info(data)
        
        logging.info({
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset_after": response.headers.get("X-RateLimit-Reset-After"),
        })

        if response.status_code == 429:
            retry_after = data.get("retry_after") or response.headers.get("X-RateLimit-Reset-After", 1)
            time.sleep(float(retry_after))
            continue

        logging.info(f"[ERROR] {response.status_code}: {response.text}")
        return response

    raise RuntimeError("Discord request failed after retries")

def sort_data(store):
    items = list(store.items())

    if SORT_MODE == "count_volume_alpha":
        return sorted(
            items,
            key=lambda x: (
                -x[1]["count"],
                -x[1].get("volume", 0),
                x[0]
            )
        )

    # default: count + alphabetical
    return sorted(
        items,
        key=lambda x: (-x[1]["count"], x[0])
    )


