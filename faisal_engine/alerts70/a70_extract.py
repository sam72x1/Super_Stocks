"""ALERTS70 — extract the historical live-alert record from git history (research · offline · read-only).

Source: every commit of op_entry_state.json. operator_entry_live.py stamps that file *after* each successful
Telegram send (liquidity-stage cards and «هنا الدخول» cards) and pushes it at once (git_save), so the first commit
in which a stage appears is an upper bound on the send time (the trigger minute itself is stored as anchor_ms).

Outputs (data/):
  liq_alerts.csv.gz    one row per liquidity anchor (symbol, NY date, anchor_ms): first commit time of M1 / M5 / M30,
                       anchor price/low/open, prev_close when stored, vol_x, peak_usd, trigger tag, re-arm number
  entry_alerts.csv.gz  one row per «هنا الدخول» stamp (symbol, date, first commit time)
  oe_days.json         per NY date: first/last commit (monitoring window), commits, LIQ keys evaluated
Run from the repo root:  python3 faisal_engine/alerts70/a70_extract.py   (--check verifies the outputs)
"""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")
STATE = "op_entry_state.json"
UTC = dt.timezone.utc
# 🔒 OFFLINE: the clone is partial (blob:none) — git would download missing history blobs from the remote on demand.
#    GIT_ALLOW_PROTOCOL=file makes any such fetch fail at once; only objects already in the local store are read.
GIT_ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")


def ny_date(ts_utc):
    """NY calendar date for a UTC datetime (EDT throughout 2026-08-17 .. 2026-10-09: UTC-4)."""
    return (ts_utc - dt.timedelta(hours=4)).date().isoformat()


def commits():
    r = subprocess.run(["git", "log", "--reverse", "--format=C %H %cI", "--raw", "--no-abbrev", "--", STATE],
                       cwd=ROOT, capture_output=True, text=True, check=True, env=GIT_ENV)
    out, cur = [], None
    for line in r.stdout.splitlines():
        if line.startswith("C "):
            _c, h, t = line.split()
            cur = (h, dt.datetime.fromisoformat(t).astimezone(UTC))
        elif line.startswith(":") and cur is not None:
            blob = line.split()[3]
            if not blob.startswith("0000"):
                out.append((cur[0], cur[1], blob))
    return out


def local_blobs():
    """Blob ids present in the local object store (enumeration never fetches)."""
    r = subprocess.run(["git", "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)"],
                       cwd=ROOT, capture_output=True, text=True, env=GIT_ENV)
    return {ln.split()[0] for ln in r.stdout.splitlines() if ln.endswith(" blob")}


def stream_blobs(blobs):
    """Yield parsed JSON for each blob id, in order, through one `git cat-file --batch` process (local ids only)."""
    p = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         env=GIT_ENV)
    try:
        for b in blobs:
            p.stdin.write((b + "\n").encode())
            p.stdin.flush()
            hdr = p.stdout.readline().decode().split()
            size = int(hdr[2])
            raw = p.stdout.read(size)
            p.stdout.read(1)
            try:
                yield json.loads(raw)
            except Exception:                                             # noqa: BLE001
                yield None
    finally:
        p.stdin.close()
        p.wait()


LIQ_KEEP = ("anchor_ms", "anchor_price", "anchor_low", "anchor_open", "prev_close", "pre_hi", "pre_usd", "vol_x",
            "peak_usd", "trig", "rearm_n", "updates")


def extract():
    allc = commits()
    have = local_blobs()
    cs = [c for c in allc if c[2] in have]
    liq = {}          # (sym, date, anchor_ms) -> row
    ent = {}          # (sym, date) -> row
    days = {}
    for h, t, b in allc:                      # monitoring windows from commit times (no blob needed)
        d = ny_date(t)
        dd = days.setdefault(d, {"first": t.isoformat(), "last": t.isoformat(), "commits": 0, "local": 0,
                                 "last_local": None, "liq_keys": set(), "liq_anchored": set()})
        dd["last"] = t.isoformat()
        dd["commits"] += 1
    for (h, t, _b), st in zip(cs, stream_blobs([c[2] for c in cs])):
        d = ny_date(t)
        dd = days[d]
        dd["local"] += 1
        dd["last_local"] = t.isoformat()
        if not isinstance(st, dict):
            continue
        for k, v in st.items():
            if k.startswith("LIQ:") and isinstance(v, dict):
                sym = k[4:]
                vd = v.get("date") or d
                if vd == d:
                    dd["liq_keys"].add(sym)
                am = v.get("anchor_ms")
                sent = v.get("sent") or []
                if not am or not sent:
                    continue
                if vd == d:
                    dd["liq_anchored"].add(sym)
                key = (sym, vd, int(am))
                row = liq.get(key)
                if row is None:
                    row = {"symbol": sym, "date": vd, "anchor_ms": int(am), "first_commit": t.isoformat()}
                    liq[key] = row
                for kk in LIQ_KEEP:
                    if v.get(kk) is not None and row.get(kk) is None:
                        row[kk] = v.get(kk)
                for stg in ("M1", "M5", "M30"):
                    if stg in sent and not row.get(f"t_{stg}"):
                        row[f"t_{stg}"] = t.isoformat()
                k2 = v.get("k2") or {}
                if k2 and row.get("k2_c3") is None:
                    for kk in ("c3", "c4", "v2", "v3", "j1"):
                        row[f"k2_{kk}"] = k2.get(kk)
            elif not k.startswith(("LIQ:", "PRE:")) and isinstance(v, str) and len(v) == 10:
                key = (k, v)
                if key not in ent:
                    ent[key] = {"symbol": k, "date": v, "first_commit": t.isoformat()}
    return cs, liq, ent, days


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


def write(out_dir=DATA):
    os.makedirs(out_dir, exist_ok=True)
    cs, liq, ent, days = extract()
    lf = ["symbol", "date", "anchor_ms", "first_commit", "t_M1", "t_M5", "t_M30"] + list(LIQ_KEEP) + \
         ["k2_c3", "k2_c4", "k2_v2", "k2_v3", "k2_j1"]
    _wcsv(os.path.join(out_dir, "liq_alerts.csv.gz"), sorted(liq.values(), key=lambda r: (r["anchor_ms"], r["symbol"])), lf)
    _wcsv(os.path.join(out_dir, "entry_alerts.csv.gz"), sorted(ent.values(), key=lambda r: (r["first_commit"], r["symbol"])),
          ["symbol", "date", "first_commit"])
    dj = {d: {"first": v["first"], "last": v["last"], "commits": v["commits"], "local_snapshots": v["local"],
              "last_local": v["last_local"], "final_local": v["last_local"] == v["last"],
              "liq_keys": len(v["liq_keys"]), "liq_anchored": len(v["liq_anchored"]),
              "evaluated_symbols": sorted(v["liq_keys"])}
          for d, v in sorted(days.items())}
    json.dump({"commits_total": sum(v["commits"] for v in days.values()), "commits_local": len(cs),
               "first": cs[0][1].isoformat(), "last": cs[-1][1].isoformat(), "days": dj},
              open(os.path.join(out_dir, "oe_days.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    return len(cs), len(liq), len(ent), len(days)


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        write(tmp)
        bad = [f for f in ("liq_alerts.csv.gz", "entry_alerts.csv.gz", "oe_days.json")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    print(write())
