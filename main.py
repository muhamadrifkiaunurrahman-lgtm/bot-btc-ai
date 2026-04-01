import ccxt
import requests
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta
from flask import Flask

app = Flask(__name__)

def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"Status Kirim: {r.status_code}")
    except Exception as e:
        print(f"Error Jaringan: {e}")

def check_signal():
    exchange = ccxt.indodax()
    symbol = 'BTC/IDR'
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        df['ema_short'] = ta.ema(df['close'], length=20)
        df['ema_long'] = ta.ema(df['close'], length=50)
        
        last_rsi = df['rsi'].iloc[-1]
        last_macd = df['MACD_12_26_9'].iloc[-1]
        last_macd_signal = df['MACDs_12_26_9'].iloc[-1]
        last_price = df['close'].iloc[-1]
        last_ema_short = df['ema_short'].iloc[-1]
        last_ema_long = df['ema_long'].iloc[-1]
        
        formatted_price = "Rp {:,.0f}".format(last_price).replace(',', '.')
        waktu_wib = (datetime.utcnow() + timedelta(hours=7)).strftime('%d-%m-%Y %H:%M WIB')

        status = "Netral"
        ai_insight = "Pasar sedang konsolidasi."
        
        if last_rsi < 40 and last_macd > last_macd_signal and last_price > last_ema_short:
            status = "🟢 Beli (Bullish)"
            ai_insight = "AI mendeteksi pembalikan arah harga."
        elif last_rsi < 40:
            status = "🟡 Oversold"
            ai_insight = "Harga murah, tapi tren masih lemah."
        elif last_rsi > 70:
            status = "🔴 Jual (Overbought)"
            ai_insight = "Hati-hati, harga sudah terlalu tinggi."
        elif last_ema_short > last_ema_long:
            status = "🔵 Tren Naik"
            ai_insight = "Harga stabil di atas rata-rata."

        pesan = f"🤖 Bot AI SIKC Render\n\n📅 Waktu: {waktu_wib}\n💰 Harga: {formatted_price}\n📊 RSI: {last_rsi:.2f}\n\n🔥 Status AI: {status}\n💡 Analisis: {ai_insight}"
        send_telegram(pesan)
    except Exception as e:
        print(f"Logic Error: {e}")

@app.route('/')
def index():
    check_signal()
    return "Bot AI Render Berjalan!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
