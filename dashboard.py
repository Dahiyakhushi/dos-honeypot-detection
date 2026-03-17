

import sqlite3
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import collections
import argparse

def get_recent_events(db_file, minutes=60):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    since = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).isoformat() + "Z"
    cur.execute("SELECT ts_utc, client_ip FROM connections WHERE ts_utc >= ? ORDER BY ts_utc ASC", (since,))
    rows = cur.fetchall()
    conn.close()
    return rows

def aggregate_per_minute(rows, minutes=60):
    now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    buckets = [now - datetime.timedelta(minutes=i) for i in range(minutes-1, -1, -1)]
    counts = collections.Counter()
    ips = collections.Counter()
    for ts_text, ip in rows:
        try:
            ts = datetime.datetime.fromisoformat(ts_text.rstrip("Z"))
            minute = ts.replace(second=0, microsecond=0)
            counts[minute] += 1
            ips[ip] += 1
        except Exception:
            continue
    x = buckets
    y = [counts[b] for b in buckets]
    return x, y, ips

def animate(i, db_file, minutes, ax_time, ax_bar):
    rows = get_recent_events(db_file, minutes=minutes)
    x, y, ips = aggregate_per_minute(rows, minutes=minutes)

    ax_time.clear()
    ax_time.plot(x, y, "-o", color="tab:blue")
    ax_time.set_title(f"Connections per minute (last {minutes} minutes) — total events: {len(rows)}")
    ax_time.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.setp(ax_time.get_xticklabels(), rotation=45, ha="right")
    ax_time.set_ylabel("Connections")

    ax_bar.clear()
    top = ips.most_common(8)
    if top:
        ips_labels, ips_counts = zip(*top)
        ax_bar.barh(range(len(ips_labels)), ips_counts, color="tab:orange")
        ax_bar.set_yticks(range(len(ips_labels)))
        ax_bar.set_yticklabels(ips_labels)
        ax_bar.invert_yaxis()
        ax_bar.set_title("Top source IPs (last window)")
    else:
        ax_bar.text(0.5, 0.5, "No events yet", ha="center", va="center")
        ax_bar.set_axis_off()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="honeypot_logs.db", help="SQLite DB file")
    parser.add_argument("--minutes", type=int, default=30, help="Window size in minutes for plotting")
    parser.add_argument("--interval", type=int, default=3000, help="Refresh interval in ms")
    args = parser.parse_args()

    plt.style.use("ggplot")## try seaborn-darkgrid insted of ggplot
    fig, (ax_time, ax_bar) = plt.subplots(ncols=2, figsize=(12,5), gridspec_kw={'width_ratios':[2,1]})

    anim = FuncAnimation(fig, animate, fargs=(args.db, args.minutes, ax_time, ax_bar),
                         interval=args.interval)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
