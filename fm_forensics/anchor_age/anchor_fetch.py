# -*- coding: utf-8 -*-
"""📺 T-ANCHOR-AGE · runner fetch (TradingView is blocked from the session sandbox). Read-only · no Telegram · no production state.

Daily regular-session bars, adjustment=splits, through the production function `Super_stock.tv_download` (what the bot itself
reads since 2026-09-30) for data/fetch_symbols.json ⟶ data/anchor_bars.json.gz in the shape of fm_forensics/data/bars_*.json.gz
(the GEN5 archive shape · `gen5_features.load_bars`)."""
import datetime as dt
import gzip
import json
import os
import sys

os.environ.setdefault("FAISAL_ONLY", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import Super_stock as S          # noqa: E402

START = os.environ.get("AA_START") or "2025-10-01"


def main():
    syms = json.load(open(os.path.join(HERE, "data", "fetch_symbols.json"), encoding="utf-8"))["symbols"]
    print(f"رموز: {len(syms)} · start={START}")
    frames, rep = S.tv_download(syms, START)
    print("📺", S._tv_bars_line(rep))
    out = {"meta": {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "start": START, "asked": len(syms),
                    "got": len(frames), "rep": {k: v for k, v in rep.items() if k != "gate"},
                    "source": "tradingview · regular session · adjustment=splits · Super_stock.tv_download"}, "daily": {}}
    for s, df in frames.items():
        out["daily"][s] = [[i.strftime("%Y-%m-%d"), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume)]
                           for i, r in df.iterrows()]
    path = os.path.join(HERE, "data", "anchor_bars.json.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    last = max((v[-1][0] for v in out["daily"].values() if v), default=None)
    print(f"💾 {path} · {os.path.getsize(path)} بايت · daily {len(out['daily'])} · آخرُ شمعة {last}")


if __name__ == "__main__":
    main()
