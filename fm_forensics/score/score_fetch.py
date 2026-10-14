"""T-SCORE stage D — runner-side fetch of today's daily bars for the near-watch members (TradingView is blocked in the session
container). Reads `data/today_symbols.txt`, writes `data/today_bars.json.gz` = {"daily": {sym: [[day, o, h, l, c, v], …]},
"meta": …}. Regular-session daily, split-adjusted, no login · read-only · no secrets · sends nothing.

    python3 fm_forensics/score/score_fetch.py
"""
import datetime as dt
import gzip
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SYMS_FILE = os.path.join(HERE, "data", "today_symbols.txt")
OUT = os.path.join(HERE, "data", "today_bars.json.gz")
DAILY_N = 320


def main():
    sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "1")
    import tv_data as TV
    import Super_stock as S
    syms = [x.strip().upper() for x in open(SYMS_FILE, encoding="utf-8").read().split() if x.strip()]
    t0 = time.monotonic()
    tmap = S._tv_ticker_map(None)
    full = {s: S._tv_full_name(s, tmap) for s in syms}
    names = sorted(set(full.values()))
    gate = S.TVBarsGate(budget=False)
    daily = TV.fetch_many(names, interval="1D", n=DAILY_N, workers=S.TV_BARS_WORKERS, gate=gate,
                          stagger=S.TV_BARS_STAGGER_S, retry_pass=True, retry_pause=S.TV_BARS_RETRY_PAUSE_S) or {}
    out = {"daily": {}}
    miss = []
    for s in syms:
        b = daily.get(full[s])
        if not b:
            miss.append(s)
            continue
        out["daily"][s] = [[TV.ny_day(x[0]), round(x[1], 6), round(x[2], 6), round(x[3], 6), round(x[4], 6),
                            round(float(x[5]), 1) if len(x) > 5 and x[5] is not None else 0.0] for x in b]
    out["meta"] = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "source": "tradingview · 1D regular · adjustment=splits · no login", "daily_n": DAILY_N,
                   "map": "scan" if tmap else "nasdaq", "secs": round(time.monotonic() - t0, 1), "gate": gate.summary(),
                   "asked": len(syms), "ok": len(out["daily"]), "missing": miss}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(json.dumps({k: v for k, v in out["meta"].items() if k != "missing"}), "missing", len(miss))


if __name__ == "__main__":
    main()
