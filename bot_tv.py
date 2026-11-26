from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# ── 設定，同你 TradingView 一樣 ──
QTY = 5
PER_TRADE_LOSS = 300
DAY_GOAL = 500
DAY_LOSS = 500

position = 0  # 0 = 冇倉, 5 = 有倉
entry_price = 0
day_pnl = 0
c_locked = False
daily_locked = False
logs = []

def log(msg):
    logs.append(f"{time.strftime('%H:%M:%S')} {msg}")
    print(msg)
    if len(logs) > 50:
        logs.pop(0)

@app.route('/')
def home():
    return f"""
    <h1>TradingView Bot 行緊</h1>
    <p>有倉: {position}口 | 今日盈虧: ${day_pnl} | C停手: {c_locked} | 每日鎖: {daily_locked}</p>
    <p>Logs:</p>
    <p>{'<br>'.join(reversed(logs))}</p>
    <p>等 TradingView 訊號中...</p>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    global position, entry_price, day_pnl, c_locked, daily_locked
    try:
        data = request.get_json(force=True)
        action = data.get('action')
        log(f"收到 TradingView: {action}")

        if c_locked or daily_locked:
            log("已鎖住，唔做單")
            return jsonify({"status":"locked"})

        if action == "buy" and position == 0:
            position = QTY
            entry_price = data.get('price', 0)
            log(f"PAPER 買入 {QTY}口 MES @ {entry_price}")

        elif action == "sell_exit" and position > 0:
            # 呢度簡化：用假價計，實戰你會用真價
            log(f"PAPER 平倉 5m轉紅，倉已平")
            position = 0

        elif action == "close_all" and position > 0:
            log(f"PAPER 平倉 日限額/收市")
            position = 0
            daily_locked = True

        elif action == "c_lock":
            log("C規則觸發：第一單止損，今日停手")
            c_locked = True
            position = 0

        return jsonify({"status":"ok", "position": position})
    except Exception as e:
        log(f"錯誤: {e}")
        return jsonify({"status":"error", "msg": str(e)})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"=== TradingView Bot 已啟動，等訊號，Port {port} ===")
    app.run(host='0.0.0.0', port=port)