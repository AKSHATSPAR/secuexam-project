#!/usr/bin/env python3
"""Print the best local-network URL for opening SecuExam on a phone."""

from __future__ import annotations

import socket


def detect_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def main() -> None:
    lan_ip = detect_lan_ip()
    print("\nSecuExam mobile access")
    print("=" * 28)
    print(f"Local laptop URL : http://127.0.0.1:5050")
    print(f"Phone LAN URL    : http://{lan_ip}:5050")
    print("\nUse the phone LAN URL when your phone and laptop are on the same Wi-Fi.")
    print("If you need a public HTTPS link for install/demo, run:")
    print("  npx localtunnel --port 5050")
    print()


if __name__ == "__main__":
    main()
