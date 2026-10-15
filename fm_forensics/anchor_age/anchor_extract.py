"""T-ANCHOR-AGE · extraction (research only · read-only · no network · no production state written).

Reads the public git history of origin/main and writes data/snapshots.json.gz:
  watch     — for each UTC commit date, the LAST commit of weekly_watchlist.json that date; every ACTIVE stock with the
              fields the entry decision reads (pivot · tranches · stop · last_price · price_bar · price_state · bars_after ·
              interp.entry_mode · ref_bar · added · cont_status) and the production verdict `Super_stock.entry_status`
              evaluated on the record exactly as stored (the function is pure on the record).
  near      — near_watch.json rows seen by each run (last_seen == run date), symbol and price only.
  walls     — reject_log.json: the newest entry of each commit (run date → {symbol: wall}).

  python3 fm_forensics/anchor_age/anchor_extract.py            write data/snapshots.json.gz
  python3 fm_forensics/anchor_age/anchor_extract.py --symbols  write data/fetch_symbols.json (what the runner fetches)

Exit 8 (axis closed «اقفل عمر المرساة» 2026-10-15) before reading anything unless ANCHOR_AGE_REOPEN=1 literally.
"""
import datetime as dt
import gzip
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REF = "origin/main"
SNAP = os.path.join(HERE, "data", "snapshots.json.gz")
SYMS = os.path.join(HERE, "data", "fetch_symbols.json")
FIVE = ("SXTC", "DKI", "RETO", "DLXY", "HUBC")
EXTRA = ("ANPA",)
KEEP = ("symbol", "added", "ref_bar", "pivot", "tranches", "stop", "stop_hi", "last_price", "price_bar", "price_state",
        "bars_after", "cont_status", "status", "tier")


def _git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, check=False).stdout


def _commits(path):
    out = []
    for line in _git("log", REF, "--format=%H %cI", "--", path).splitlines():
        h, t = line.split()
        out.append((h, dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc)))
    return sorted(out, key=lambda x: x[1])


def _last_per_date(commits):
    by = {}
    for h, t in commits:
        by[t.date().isoformat()] = (h, t)          # sorted ascending ⟶ the last one of the date wins
    return [by[d] for d in sorted(by)]


def _status(S, s):
    try:
        st = S.entry_status(s)
        return {"status": st.get("status"), "reason": st.get("reason") or ""}
    except Exception as e:                                       # noqa: BLE001
        return {"status": None, "reason": f"error {type(e).__name__}"}


def extract():
    os.environ.setdefault("FAISAL_ONLY", "1")
    sys.path.insert(0, ROOT)
    import Super_stock as S                                     # noqa: E402
    watch = []
    for h, t in _last_per_date(_commits("weekly_watchlist.json")):
        try:
            w = json.loads(_git("show", f"{h}:weekly_watchlist.json"))
        except Exception:                                        # noqa: BLE001
            continue
        rows = []
        for s in w.get("stocks") or []:
            if not isinstance(s, dict) or s.get("status") != "active":
                continue
            em = (s.get("interp") or {}).get("entry_mode") or {}
            r = {k: s.get(k) for k in KEEP}
            r["mode"] = em.get("mode")
            r["zone"] = em.get("entry_zone")
            r["mode_reason"] = em.get("reason")
            r["prod"] = _status(S, s)
            rows.append(r)
        watch.append({"commit": h, "utc": t.isoformat(timespec="seconds"), "logic_version": w.get("logic_version"),
                      "week_start": w.get("week_start"), "stocks": rows})
    near = []
    for h, t in _commits("near_watch.json"):
        try:
            d = json.loads(_git("show", f"{h}:near_watch.json"))
        except Exception:                                        # noqa: BLE001
            continue
        if not isinstance(d, dict) or not d:
            continue
        D = max((v.get("last_seen") or "") for v in d.values() if isinstance(v, dict))
        near.append({"commit": h, "utc": t.isoformat(timespec="seconds"), "run_date": D,
                     "rows": {k: v.get("price") for k, v in d.items() if isinstance(v, dict) and v.get("last_seen") == D}})
    walls = {}
    for h, t in _commits("reject_log.json"):
        try:
            d = json.loads(_git("show", f"{h}:reject_log.json"))
        except Exception:                                        # noqa: BLE001
            continue
        ents = [e for e in d if isinstance(e, dict) and "walls" in e] if isinstance(d, list) else []
        for e in ents:
            walls[e["date"]] = {sym: wl for wl, lst in e["walls"].items() for sym in lst}
    out = {"meta": {"ref": REF, "head": _git("rev-parse", REF).strip(), "watch_days": len(watch), "near_runs": len(near),
                    "wall_dates": len(walls)}, "watch": watch, "near": near, "walls": walls}
    os.makedirs(os.path.dirname(SNAP), exist_ok=True)
    with gzip.open(SNAP, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, sort_keys=True)
    n = sum(len(x["stocks"]) for x in watch)
    print(f"💾 {os.path.relpath(SNAP, ROOT)} · days {len(watch)} · stock-days {n} · near runs {len(near)} · wall dates {len(walls)}")


def symbols():
    with gzip.open(SNAP, "rt", encoding="utf-8") as f:
        d = json.load(f)
    s = set(FIVE) | set(EXTRA)
    for x in d["watch"]:
        s |= {r["symbol"] for r in x["stocks"]}
    for x in d["near"]:
        s |= set(x["rows"])
    out = sorted(s)
    with open(SYMS, "w", encoding="utf-8") as f:
        json.dump({"symbols": out, "n": len(out), "from": d["meta"]["head"]}, f, ensure_ascii=False, indent=0)
    print(f"💾 {os.path.relpath(SYMS, ROOT)} · {len(out)} رمزًا")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    sys.path.insert(0, HERE)
    import anchor_age as AA                                     # 🔒 the axis closure (exit 8 before reading git history)
    rc = AA.closed_exit("anchor_extract.py")
    if rc is not None:
        return rc
    symbols() if "--symbols" in argv else extract()
    return 0


if __name__ == "__main__":
    sys.exit(main())
