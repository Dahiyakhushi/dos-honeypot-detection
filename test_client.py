import socket
import time
import argparse
import random
import string

def small_payload(size=40):
    s = ''.join(random.choices(string.ascii_letters + string.digits, k=max(1, size-10)))
    return f"TEST {time.time():.3f} {s}\n".encode()

def run(host, port, total, delay, payload_size):
    for i in range(total):
        try:
            with socket.create_connection((host, port), timeout=3) as s:
                p = small_payload(payload_size)
                s.sendall(p)
                try:
                    s.settimeout(0.5)
                    _ = s.recv(1024)
                except Exception:
                    pass
            print(f"[{i+1}/{total}] sent {len(p)} bytes to {host}:{port}")
        except Exception as e:
            print(f"[{i+1}/{total}] error connecting: {e}")
        if i < total-1:
            time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--total", type=int, default=10, help="Total connections to make")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between connections")
    parser.add_argument("--payload", type=int, default=40, help="Approx payload byte length")
    args = parser.parse_args()
    run(args.host, args.port, args.total, args.delay, args.payload)
