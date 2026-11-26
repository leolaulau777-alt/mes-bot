from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# ── Bot 狀態 ──
position = 0  # 0 = 冇倉, 5 = 做緊 5口多
c_locked = False  # C規則：第一單止損後今日停手
daily_locked = False

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# Render 用嚟 check 你係咪在生，UptimeRobot 都係 ping 呢個
@app.route("/", methods=["GET"])
def home():
    return f"Bot 在線 | 倉位: {position} | C停手: {c_locked} | 日鎖: {daily_locked}", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    global position, c_locked, daily_locked

    try:
        data = request.get_json(force=True)
    except:
        return jsonify({"status": "error", "msg": "JSON 格式錯誤"}), 400

    # 唔理大細階，全部轉做細階嚟認
    action = str(data.get("action", "")).lower().strip()
    log(f"收到訊號: {action} | 原始: {data}")

    # ── 1. buy：開多 ──
    if action == "buy":
        if c_locked:
            log("⛔ C已鎖，唔開新單")
            return jsonify({"status": "ignored", "reason": "c_lock"}), 200
        if daily_locked:
            log("⛔ 日限額已鎖，唔開新單")
            return jsonify({"status": "ignored", "reason": "daily_lock"}), 200
        if position != 0:
            log(f"⛔ 已有倉位 {position}，唔重複開")
            return jsonify({"status": "ignored", "reason": "already_in_position"}), 200
        
        # TODO: 喺呢度接你嘅券商落單，例如 IB / Topstep
        position = 5
        log("✅ 開多 5口 MES")
        return jsonify({"status": "ok", "action": "buy", "position": position}), 200

    # ── 2. sell_exit：5m反色，平多 ──
    elif action in ["sell_exit", "sell", "close_long"]:
        if position == 0:
            log("冇倉，唔使平")
            return jsonify({"status": "ignored", "reason": "no_position"}), 200
        
        # TODO: 喺呢度平倉
        position = 0
        log("✅ 5m反色，平咗多單")
        return jsonify({"status": "ok", "action": "sell_exit"}), 200

    # ── 3. close_all：到時間 / 到日限額，全部平 ──
    elif action == "close_all":
        if position != 0:
            position = 0
            log("✅ 日限額/收市，全部平倉")
        else:
            log("收到 close_all，但本身冇倉")
        daily_locked = True
        return jsonify({"status": "ok", "action": "close_all"}), 200

    # ── 4. c_lock：第一單止損，今日停手 ──
    elif action == "c_lock":
        c_locked = True
        log("🔒 C觸發：今日第一單止損，今日唔再開新單")
        return jsonify({"status": "ok", "action": "c_lock"}), 200

    else:
        log(f"⚠️ 唔識呢個 action: {action}")
        return jsonify({"status": "ignored", "reason": "unknown_action"}), 400

# 每日重設：Render 免費版會自己重啟，順便 reset 埋。
# 如果你升咗 $7 唔會重啟，就要自己喺呢度加定時 reset，
# 而家先用最簡單：你每日手動 restart 一次 Render 就 reset 晒。

if __name__ == "__main__":
    print("TradingView Bot 已啟動，等訊號，Port 10000", flush=True)
    app.run(host="0.0.0.0", port=10000)
