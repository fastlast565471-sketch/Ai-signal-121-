import os
from http.server import HTTPServer

from api.bot import handler


def run():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"AI Signal Bot listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run()
