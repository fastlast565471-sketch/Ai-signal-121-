import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def send_response_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        self.send_response_json(200, {
            "status": "AI Signal Bot is running"
        })

    def do_POST(self):
        token = os.environ.get("TELEGRAM_BOT_TOKEN")

        if not token:
            self.send_response_json(500, {
                "error": "Bot token is not configured"
            })
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            update = json.loads(self.rfile.read(length))

            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            if chat_id and text:
                if text == "/start":
                    reply = (
                        "Welcome to AI Signal Bot!\n\n"
                        "Available commands:\n"
                        "/start - Start bot\n"
                        "/help - Help\n"
                        "/signals - Signal information\n\n"
                        "AI trading signals are coming soon."
                    )

                elif text == "/help":
                    reply = "Welcome! Use /signals to see signal information."

                elif text == "/signals":
                    reply = (
                        "AI Signal Service\n\n"
                        "EUR/USD: Waiting for market data\n"
                        "BTC/USD: Waiting for market data\n\n"
                        "No live signal is available yet."
                    )

                else:
                    reply = "Welcome! Type /start to use AI Signal Bot."

                url = (
                    f"https://api.telegram.org/bot{token}/sendMessage"
                )

                payload = json.dumps({
                    "chat_id": chat_id,
                    "text": reply
                }).encode("utf-8")

                request = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )

                urllib.request.urlopen(request, timeout=10).read()

            self.send_response_json(200, {"ok": True})

        except Exception:
            self.send_response_json(200, {"ok": True})
