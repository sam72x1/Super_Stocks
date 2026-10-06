"""🩺 مِجَسٌّ مؤقّت ② (2026-10-06): (0) المحلّلُ المُصلَح حيًّا · (1) قفزاتُ hit100 في حسم الصيّادين 10-03 من ياهو وTradingView ·
(2) حصّةُ الموقع على 60 طلبًا متتاليًا بعد انتقاله إلى Next.js. يطبع ولا يكتب شيئًا · يُحذف بعد القراءة."""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Super_stock as S  # noqa: E402

SHARD = int(os.environ.get("CTB_SHARD", "0"))


def sentence(sym):
    import requests
    r = requests.get(f"https://chartexchange.com/symbol/nasdaq-{sym.lower()}/borrow-fee/", headers=S.BROWSER_UA, timeout=15)
    t = r.text or ""
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    m = re.search(r"there were\s*([\d,]+)\s*shares available with a fee of\s*([\d,.]+)\s*%", t)
    return (m.group(1), m.group(2)) if m else None


if SHARD == 0:
    for sym in ["GWAV", "LABT", "KMRK", "TRAW", "GEOS", "AAPL", "ZDAI", "CSAI"]:
        d = {}
        got = S.ce_borrow_info(sym, diag=d)
        print(f"FIX {sym}: parsed={got} diag={d} independent={sentence(sym)}", flush=True)
        time.sleep(1)

elif SHARD == 1:
    syms = ["IPST", "ZSTK", "XPON", "NAMI", "BOXL", "AVX", "JZ", "SUGP", "MWYN"]
    ref = {"IPST": 2.165, "ZSTK": 1.76, "XPON": 3.31, "NAMI": 2.91, "BOXL": 3.30, "AVX": 3.17, "JZ": 2.53, "SUGP": 1.96, "MWYN": 0.72}
    d0 = dt.date(2026, 8, 6)
    old = os.environ.pop("BARS_SOURCE", None)
    yh = S.download_history(syms) or {}
    try:
        tv, rep = S.tv_download(syms, "2025-12-01")
    except Exception as e:  # noqa: BLE001
        tv, rep = {}, f"EXC {type(e).__name__}"
    print("TV rep:", str(rep)[:300])
    for s in syms:
        for name, src in (("yahoo", yh), ("tv", tv)):
            df = src.get(s)
            if df is None or len(df) == 0:
                print(f"BARS {s} {name}: none")
                continue
            idx = [x.date() if hasattr(x, "date") else x for x in df.index]
            c0 = [float(c) for x, c in zip(idx, df["Close"].values) if x == d0]
            after = [(x, float(h), float(c)) for x, h, c in zip(idx, df["High"].values, df["Close"].values) if x > d0][:40]
            top = sorted(after, key=lambda r: -r[1])[:4]
            print(f"BARS {s} {name}: close@08-06={c0} ref={ref[s]} n_after={len(after)} "
                  f"top={[(str(a), round(b, 4), round(c, 4)) for a, b, c in top]} "
                  f"max_gain={round((top[0][1] / ref[s] - 1) * 100, 2) if top else None}")
        try:
            sp = S._fetch_splits(s)
            print(f"SPLITS {s}: {list(sp.items())[-5:] if hasattr(sp, 'items') else sp}")
        except Exception as e:  # noqa: BLE001
            print(f"SPLITS {s}: EXC {type(e).__name__}")

else:
    rows = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True, text=True).stdout
    seen = []
    for ln in open("hunter_ledger.jsonl", encoding="utf-8"):
        try:
            s = json.loads(ln).get("symbol")
        except Exception:  # noqa: BLE001
            continue
        if s and s not in seen:
            seen.append(s)
    syms = seen[-60:]
    seq, reasons = "", {}
    t0 = time.time()
    for s in syms:
        d = {}
        got = S.ce_borrow_info(s, diag=d)
        seq += "✓" if got else "✗"
        if not got:
            reasons[d.get("reason")] = reasons.get(d.get("reason"), 0) + 1
    print(f"QUOTA 60 sequential: {seq} · ok={seq.count('✓')} · reasons={reasons} · {time.time() - t0:.1f}s")
    import requests
    for s in ["GWAV", "KMRK"]:
        r = requests.get(f"https://chartexchange.com/symbol/nasdaq-{s.lower()}/", headers=S.BROWSER_UA, timeout=15)
        t = r.text or ""
        i = t.find(">Float<")
        print(f"OVERVIEW {s}: status={r.status_code} len={len(t)} float_parse={S._parse_ce_float(t)} "
              f"raw={t[max(0, i - 200):i + 300]!r}" if i >= 0 else f"OVERVIEW {s}: status={r.status_code} len={len(t)} no '>Float<'")
