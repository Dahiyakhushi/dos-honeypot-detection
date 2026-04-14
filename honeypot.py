import asyncio
import sqlite3
import datetime
import argparse

def init_db(db_file):
    conn = sqlite3.connect(db_file)
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            client_port INTEGER NOT NULL,
            bytes_received INTEGER NOT NULL,
            banner TEXT
        );
        """)
    conn.close()

def log_event(client_ip, client_port, bytes_received, banner, db_file):
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(db_file)
    with conn:
        conn.execute(
            "INSERT INTO connections (ts_utc, client_ip, client_port, bytes_received, banner) VALUES (?, ?, ?, ?, ?)",
            (ts, client_ip, client_port, bytes_received, banner)
        )
    conn.close()

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, db_file: str):
    peer = writer.get_extra_info("peername")
    if peer:
        client_ip, client_port = peer[0], peer[1]
    else:
        client_ip, client_port = "unknown", 0

    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=2.0)
        bytes_received = len(data) if data else 0
        banner = data[:200].decode(errors="replace") if data else None

        log_event(client_ip, client_port, bytes_received, banner, db_file)
        print(f"[{datetime.datetime.utcnow().isoformat()}Z] conn from {client_ip}:{client_port} bytes={bytes_received}")
    except asyncio.TimeoutError:
        log_event(client_ip, client_port, 0, None, db_file)
        print(f"[{datetime.datetime.utcnow().isoformat()}Z] conn from {client_ip}:{client_port} bytes=0 (timeout)")
    except Exception as e:
        log_event(client_ip, client_port, 0, f"error:{e!s}", db_file)
        print(f"[ERROR] handling {client_ip}:{client_port} -> {e!s}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def run_server(host: str, port: int, db_file: str):
    # create a handler that captures db_file
    async def _handler(reader, writer):
        await handle_client(reader, writer, db_file)

    server = await asyncio.start_server(_handler, host, port)
    addr = server.sockets[0].getsockname()
    print(f"Honeypot listening on {addr} — logs -> {db_file}")
    async with server:
        await server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description="Simple local honeypot logger")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2222, help="TCP port to listen on (default 2222)")
    parser.add_argument("--db", default="honeypot_logs.db", help="SQLite DB file (default honeypot_logs.db)")
    args = parser.parse_args()

    init_db(args.db)

    try:
        asyncio.run(run_server(host=args.host, port=args.port, db_file=args.db))
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()
