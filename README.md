import os
import logging
import requests
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

logging.basicConfig(level=logging.INFO)

def get_market_data(symbol, interval="5min"):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 100,
        "apikey": TWELVE_DATA_API_KEY
    }
    response = requests.get(url, params=params, timeout=20)
    data = response.json()

    if "values" not in data:
        raise ValueError(data.get("message", "Market data পাওয়া যায়নি"))

    df = pd.DataFrame(data["values"])
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    return df.sort_index(ascending=False).reset_index(drop=True)

def analyze_market(df):
    close = df["close"]

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    ma20 = close.rolling(20).mean()

    if pd.isna(rsi.iloc[-1]) or pd.isna(ma20.iloc[-1]):
        return "WAIT", "পর্যাপ্ত ডেটা নেই"

    bullish = close.iloc[-1] > ma20.iloc[-1] and macd.iloc[-1] > signal.iloc[-1]
    bearish = close.iloc[-1] < ma20.iloc[-1] and macd.iloc[-1] < signal.iloc[-1]

    if bullish and rsi.iloc[-1] < 70:
        return "BUY / CALL", f"RSI: {rsi.iloc[-1]:.2f}; MACD ঊর্ধ্বমুখী"
    if bearish and rsi.iloc[-1] > 30:
        return "SELL / PUT", f"RSI: {rsi.iloc[-1]:.2f}; MACD নিম্নমুখী"

    return "WAIT", f"RSI: {rsi.iloc[-1]:.2f}; সংকেত পরিষ্কার নয়"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম! Forex ও Binary Options বিশ্লেষণ বট।\n"
        "উদাহরণ: /analyze EUR/USD"
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TWELVE_DATA_API_KEY:
        await update.message.reply_text("লাইভ ডেটার API Key এখনো সেট করা হয়নি।")
        return

    symbol = context.args[0] if context.args else "EUR/USD"

    try:
        df = get_market_data(symbol)
        result, reason = analyze_market(df)
        await update.message.reply_text(
            f"📊 {symbol}\n"
            f"Forex সংকেত: {result}\n"
            f"Binary Options: {result}\n"
            f"বিশ্লেষণ: {reason}\n"
            "⚠️ এটি সম্ভাব্য বিশ্লেষণ, নিশ্চিত ফল নয়।"
        )
    except Exception as error:
        await update.message.reply_text(f"ডেটা বিশ্লেষণ করা যায়নি: {error}")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN সেট করা হয়নি।")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.run_polling()

if __name__ == "__main__":
    main()
