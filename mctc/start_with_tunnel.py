import os
import subprocess
import sys
import time
import threading

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pyngrok import ngrok

# Secrets live in .env (git-ignored) -- see .env.example
load_dotenv()
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "hamstring-reassign-evidence.ngrok-free.dev")


def start_uvicorn():
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
    ])


if __name__ == "__main__":
    if not NGROK_AUTH_TOKEN:
        sys.exit("NGROK_AUTH_TOKEN is not set. Add it to mctc/.env (see .env.example).")
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

    t = threading.Thread(target=start_uvicorn, daemon=True)
    t.start()
    time.sleep(2)

    print("\nStarting ngrok tunnel...")
    tunnel = ngrok.connect(8000, domain=NGROK_DOMAIN, bind_tls=True)
    public_url = tunnel.public_url

    print("\n" + "=" * 60)
    print("  MCTC is LIVE on the internet!")
    print("")
    print("  Admin Dashboard:")
    print("  " + public_url + "/admin-dashboard")
    print("")
    print("  iPhone scan URL:")
    print("  " + public_url + "/observe/BUS-DL1PD5222")
    print("")
    print("  API Docs: " + public_url + "/docs")
    print("=" * 60)
    print("\n  Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        ngrok.kill()
