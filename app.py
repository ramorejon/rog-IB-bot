from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import logging
import sys

import time
import requests



app = Flask(__name__)

# In-memory store: { ticker: {count, timestamp} }
store = {}

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
OUTPUT_FORMAT = os.environ.get("OUTPUT_FORMAT", "code")  # code | embed | image
SORT_MODE = os.environ.get("SORT_MODE", "count_alpha") # count_alpha
SEND_SECRET = os.environ.get("SEND_SECRET")

SEND_COUNT = 0


@app.route("/")
def home():
    global SEND_COUNT  # Tells Python to use the global variable
    return {"status": "running", "sendcount": SEND_COUNT}

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
    global SEND_COUNT  # Tells Python to use the global variable
    secret = request.args.get("key")
    if secret != SEND_SECRET:
        return {"error": "unauthorized"}, 403
    
    if not store:
        return {"status": "no data"}

    SEND_COUNT +=1
    # sort by count descending
    #sorted_items = sorted(store.items(), key=lambda x: x[1]["count"], reverse=True)
    sorted_items = sort_data(store)

    
    sendResponse = {"content": ""}

    if OUTPUT_FORMAT == "embed":
        sendResponse = send_embed(sorted_items)
    if OUTPUT_FORMAT =="code":
        sendResponse = send_code_block(sorted_items)
    if OUTPUT_FORMAT == "image":
        sendResponse = send_image(sorted_items)

    return sendResponse
    
    store.clear()

#    return {"content": message}
#    return {"status": "sent", "count": len(sorted_items), "msg": message}



@app.route("/sendtest", methods=["GET"])
def sendtest():
    global SEND_COUNT  # Tells Python to use the global variable
    secret = request.args.get("key")
    if secret != SEND_SECRET:
        return {"error": "unauthorized"}, 403

    SEND_COUNT +=1
    # store latest signal
    store["AAPL"] = {
        "count": 4,
        "time": datetime.utcnow()
    }
    store["QCOM"] = {
        "count": 3,
        "time": datetime.utcnow()
    }
    store["NVDA"] = {
        "count": 1,
        "time": datetime.utcnow()
    }
    store["AMD"] = {
        "count": 1,
        "time": datetime.utcnow()
    }

    
    # sort by count descending
    sorted_items = sort_data(store)
    
    sendResponse = {"content": ""}

    if OUTPUT_FORMAT == "embed":
        sendResponse = send_embed(sorted_items)
    if OUTPUT_FORMAT =="code":
        sendResponse = send_code_block(sorted_items)
    if OUTPUT_FORMAT == "image":
        sendResponse = send_image(sorted_items)
    
    return sendResponse

    store.clear()


# ---------------------------
# FORMATTERS
# ---------------------------
def send_code_block(data):
    lines = []
    lines.append("Ticker   Count")
    lines.append("-------- -----")

    for ticker, d in data:
        lines.append(f"{ticker:<9} {d['count']:>5}")

    chunks = chunk_code_block_lines(lines)
    #for chunk in chunks:
        #message = "📊 Inside Bars – Daily\n\n```" + "\n".join(chunk) + "```"
        #discord_post(DISCORD_WEBHOOK, json={"content": message})

    for i, chunk in enumerate(chunks):
        header = "📊 Inside Bars – Daily\n\n" if i == 0 else ""
        message = header + "```" + "\n".join(chunk) + "```"
        #response = discord_post(DISCORD_WEBHOOK, json={"content": message})
        response = requests.post(DISCORD_WEBHOOK, json={"content": message})
        time.sleep(2) 
        
    success = False
    if response.status_code == 204:
        logging.info("Message sent successfully!")
        success = True
    else:
        print(f"Failed to send P: {response.status_code} - {response.text}", flush=True)
        logging.info(f"Failed to send L: {response.status_code} - {response.text} ", flush=True)
        if response.status_code == 429:
            print(f"Remaining:{response.headers.get("X-RateLimit-Remaining")} \nReset_after: {response.headers.get("X-RateLimit-Reset-After")}", flush=True)
            logging.info({
                "remaining": response.headers.get("X-RateLimit-Remaining"),
                "reset_after": response.headers.get("X-RateLimit-Reset-After"),
            })
    message = "\n".join(lines)
    return {"content": message, "success":  success}


                    
def send_code_blockXXX(data):
    global SEND_COUNT  # Tells Python to use the global variable
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
    for chunk in chunk_message(message,1000):
        #response = discord_post(DISCORD_WEBHOOK, json={"content": chunk})
        response = requests.post(DISCORD_WEBHOOK, json={"content": chunk})
        time.sleep(2) 
    #for chunk in chunk_message(message, 40):
        #print(f"Chunk:{chunk}", flush=True)
    print(f"SENDCOUNT:{SEND_COUNT}", flush=True)

    #response = requests.post(DISCORD_WEBHOOK, json={"content": message})
    

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
        print(f"Failed to send P: {response.status_code} - {response.text}", flush=True)
        logging.info(f"Failed to send L: {response.status_code} - {response.text} ", flush=True)
        if response.status_code == 429:
            print(f"Remaining:{response.headers.get("X-RateLimit-Remaining")} \nReset_after: {response.headers.get("X-RateLimit-Reset-After")}", flush=True)
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

    # Prepare data
    table_data = [["Ticker", "Count"]]
    for ticker, d in data:
        table_data.append([ticker, d["count"]])

    rows = len(table_data)

    # Dynamic sizing (tight)
    fig_height = max(1, rows * 0.35)
    fig, ax = plt.subplots(figsize=(3, fig_height))  # narrow width
    ax.axis('off')

    # Create table with controlled column widths
    table = ax.table(
        cellText=table_data,
        loc='center',
        colWidths=[0.6, 0.4]  # tighter columns
    )

    # Styling
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Reduce padding / spacing
    table.scale(1, 1.2)

    # Header styling
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_height(0.08)
        else:
            cell.set_height(0.06)

    # row striping
    for (row, col), cell in table.get_celld().items():
        if row > 0 and row % 2 == 0:
            cell.set_facecolor("#f2f2f2")
    
    # Tight layout (critical)
    plt.tight_layout(pad=0.2)

    # Save tightly cropped
    plt.savefig("table.png", bbox_inches='tight', dpi=200)
    plt.close()

    with open("table.png", "rb") as f:
        requests.post(DISCORD_WEBHOOK, files={"file": f})




def send_imageX(data):
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


def chunk_code_block_lines(lines, max_chars=1900):
    chunks = []
    current_chunk = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # newline

        if current_len + line_len > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_len = 0

        current_chunk.append(line)
        current_len += line_len

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


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


