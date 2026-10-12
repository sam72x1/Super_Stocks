"""Faisal condition atlas — historical data inventory, read from the files themselves (not from reports).

For each local source: path, kind, fields, record count, symbols, date range, completeness, whether it is available
point-in-time for a decision day T, original vs rebuilt, and the limits that matter for the atlas conditions.
No network, no write outside condition_atlas/data/.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_inventory.py   → data/inventory.json
"""
import csv
import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DATA = os.path.join(HERE, "data")


def p(*a):
    return os.path.join(ROOT, *a)


def _size(path):
    return os.path.getsize(path) if os.path.exists(path) else None


def _jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    return out


def _csvgz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _dates(vals):
    v = sorted(x for x in vals if x)
    return [v[0], v[-1]] if v else None


def bars(path, label):
    raw = json.load(gzip.open(path, "rt", encoding="utf-8"))
    d = raw["daily"]
    n_rows = sum(len(v) for v in d.values())
    first = _dates(v[0][0] for v in d.values() if v)
    last = _dates(v[-1][0] for v in d.values() if v)
    rec = {"source": label, "path": os.path.relpath(path, ROOT), "bytes": _size(path), "meta": raw.get("meta"),
           "symbols": len(d), "daily_rows": n_rows, "fields": ["date", "open", "high", "low", "close", "volume"],
           "first_date_range": first, "last_date_range": last,
           "rows_with_null_ohlc": sum(1 for v in d.values() for r in v if any(x is None for x in r[1:5]))}
    if "hourly" in raw:
        h = raw["hourly"]
        rec["hourly_symbols"] = sorted(h)
        rec["hourly_rows"] = {k: len(v) for k, v in h.items()}
    if "splits" in raw:
        rec["splits_symbols_with_events"] = sum(1 for v in raw["splits"].values() if v)
    return rec


def main():
    inv = []
    inv.append(dict(bars(p("faisal_engine", "data", "rank", "bars.json.gz"), "daily bars (rank universe)"),
                    pit="yes — every bar is dated; features read bars ≤ T; split-adjusted prices (ratios are "
                        "split-invariant; traded price = adjusted × later split ratios)",
                    original="original TradingView download 2026-10-09 (regular session, adjustment=splits); the "
                             "2026-10-09 bar is intraday-partial and dropped by the loader",
                    limits="no extended-hours bars; no intraday bars; 15 requested symbols missing; delisted symbols "
                           "absent (survivorship toward symbols listed on 2026-10-09)"))
    sp = json.load(open(p("faisal_engine", "data", "rank", "splits.json"), encoding="utf-8"))["splits"]
    ev = [(s, d, float(r)) for s, v in sp.items() for d, r in (v or [])]
    inv.append({"source": "split history", "path": "faisal_engine/data/rank/splits.json",
                "bytes": _size(p("faisal_engine", "data", "rank", "splits.json")), "symbols": len(sp),
                "symbols_with_events": sum(1 for v in sp.values() if v), "events": len(ev),
                "reverse_events": sum(1 for _s, _d, r in ev if r < 1), "forward_events": sum(1 for _s, _d, r in ev if r > 1),
                "reverse_since_2024_05": sum(1 for _s, d, r in ev if r < 1 and d >= "2024-05-01"),
                "date_range": _dates(d for _s, d, _r in ev), "fields": ["date", "ratio (<1 = reverse)"],
                "pit": "yes — dated events (a split is known on its date)",
                "original": "original Yahoo split history (snapshot)", "limits": "split announcements before the "
                "effective date are not recorded; duplicates of the same ratio within days occur (collapsed)"})
    inv.append(dict(bars(p("faisal_engine", "data", "universe_bars.json.gz"), "daily bars (universe test)"),
                    pit="yes", original="original TradingView download 2026-10-09 for the universe test",
                    limits="783 symbols from 2025-01-01 only"))
    inv.append(dict(bars(p("fm_forensics", "data", "bars_2026-10-08.json.gz"), "daily + hourly bars (Phase 6)"),
                    pit="yes for the bars present", original="original TradingView download 2026-10-08",
                    limits="hourly bars for 4 symbols only — no 4-hour frame can be rebuilt for the population"))
    sec = json.load(gzip.open(p("fm_forensics", "data", "sec_2026-10-08.json.gz"), "rt", encoding="utf-8"))
    syms = sec["symbols"]
    nf = sum(len(v.get("filings") or []) for v in syms.values())
    forms = {}
    for v in syms.values():
        for f in v.get("filings") or []:
            forms[f.get("form")] = forms.get(f.get("form"), 0) + 1
    offer = {k: forms[k] for k in forms if k and (k.startswith("424B") or k in ("S-1", "S-3", "F-1", "F-3", "EFFECT"))}
    inv.append({"source": "SEC submissions + share counts (Phase 6 universe)", "path": "fm_forensics/data/sec_2026-10-08.json.gz",
                "bytes": _size(p("fm_forensics", "data", "sec_2026-10-08.json.gz")), "meta": sec["meta"],
                "symbols": len(syms), "filings": nf, "offering_forms": offer,
                "symbols_with_share_counts": sum(1 for v in syms.values() if v.get("shares_outstanding")),
                "fields": ["filings: form, filingDate, acceptanceDateTime", "shares_outstanding: val, end, filed",
                           "public_float: val (USD), end, filed"],
                "pit": "yes by filing date — but only for 238 symbols chosen on 2026-10-08 (the bot's Phase 6 list)",
                "original": "original SEC EDGAR snapshot", "limits": "a selected, survivorship-biased subset; share "
                "counts are as reported (not split-normalised); no float in shares; not the population"})
    rn = _csvgz(p("faisal_engine", "readynow", "disc", "data", "rows.csv.gz"))
    inv.append({"source": "pivot-day rows (READY NOW discovery)", "path": "faisal_engine/readynow/disc/data/rows.csv.gz",
                "bytes": _size(p("faisal_engine", "readynow", "disc", "data", "rows.csv.gz")), "rows": len(rn),
                "symbols": len({r["sym"] for r in rn}), "date_range": _dates(r["t"] for r in rn),
                "labels": {k: sum(1 for r in rn if r["lab_on"] == k) for k in ("POS710", "NEG", "IN_EVENT", "CENSORED",
                                                                                "UNKNOWN_SPLIT")},
                "fields": list(rn[0].keys()), "pit": "features from bars ≤ T (guarded DG3/G1); labels use later bars "
                "(targets only)", "original": "rebuilt (READY70 detector + READYNOW conditions on the local bars)",
                "limits": "identity M1-M3 only (no float/short/news); decisions 2025-05-01 → 2026-10-07; labels "
                          "known up to 2026-08-27"})
    evs = _csvgz(p("faisal_engine", "readynow", "disc", "data", "events.csv.gz"))
    inv.append({"source": "explosion episodes", "path": "faisal_engine/readynow/disc/data/events.csv.gz", "rows": len(evs),
                "clean": sum(1 for e in evs if e["quality"] == "OK"), "date_range": _dates(e["onset"] for e in evs),
                "fields": list(evs[0].keys()), "pit": "no — retrospective labels (known once the +70% close prints)",
                "original": "rebuilt (the bot's scan_explosions semantics as-of each session)",
                "limits": "daily-close detector: intraday-only spikes are not events; 236 episodes on the 20-session "
                          "lookback edge"})
    ah = json.load(open(p("alerts_history.json"), encoding="utf-8")).get("alerts") or []
    inv.append({"source": "bot alert history", "path": "alerts_history.json", "rows": len(ah),
                "symbols": len({a.get("symbol") for a in ah}), "date_range": _dates(a.get("date") for a in ah),
                "fields": sorted({k for a in ah for k in a})[:20], "pit": "yes (dated)", "original": "original bot log",
                "limits": "bot candidates only, not the population"})
    a70 = _csvgz(p("faisal_engine", "alerts70", "data", "alerts.csv.gz"))
    inv.append({"source": "liquidity-anchor alerts (git history)", "path": "faisal_engine/alerts70/data/alerts.csv.gz",
                "rows": len(a70), "symbols": len({a.get("symbol") for a in a70}),
                "date_range": _dates(a.get("date") for a in a70), "fields": list(a70[0].keys()) if a70 else [],
                "pit": "yes (dated, intraday time)", "original": "rebuilt from git history of op_entry_state.json",
                "limits": "bot watch universe only; Polygon ended 2026-09-29"})
    ctb = _jsonl(p("ctb_log.jsonl"))
    inv.append({"source": "borrow harvest (ChartExchange)", "path": "ctb_log.jsonl", "rows": len(ctb),
                "symbols": len({r.get("sym") or r.get("symbol") for r in ctb}),
                "date_range": _dates(str(r.get("date") or r.get("day") or "")[:10] for r in ctb),
                "fields": sorted({k for r in ctb for k in r})[:15], "pit": "yes for the rows present",
                "original": "original harvest log", "limits": "starts 2026-08 and covers the bot's lists only — no "
                "borrow history for the pivot population"})
    cc = json.load(open(p("company_cache.json"), encoding="utf-8"))
    inv.append({"source": "company cache (float, short)", "path": "company_cache.json", "symbols": len(cc),
                "pit": "no — latest values, overwritten", "original": "original bot cache",
                "limits": "cannot be used as a historical float"})
    fp = _jsonl(p("fill_pool_log.jsonl"))
    inv.append({"source": "fill-pool log", "path": "fill_pool_log.jsonl", "rows": len(fp),
                "date_range": _dates(str(r.get("date") or r.get("t") or r.get("utc") or "")[:10] for r in fp),
                "pit": "yes", "original": "original log", "limits": "from 2026-10-08 (prospective)"})
    ps = _jsonl(p("presession_ledger.jsonl"))
    inv.append({"source": "pre-session ledger (pre-market / after-hours)", "path": "presession_ledger.jsonl",
                "rows": len(ps), "date_range": _dates(str(r.get("date") or r.get("day") or "")[:10] for r in ps),
                "pit": "yes", "original": "original log", "limits": "bot candidates only; Polygon-era (ended 2026-09-29)"})
    hf = _jsonl(p("hand_flow_log.jsonl"))
    inv.append({"source": "operator-flow harvest", "path": "hand_flow_log.jsonl", "rows": len(hf),
                "date_range": _dates(__import__("datetime").datetime.utcfromtimestamp(r["ts"]).date().isoformat()
                                     for r in hf if r.get("ts")),
                "pit": "yes", "original": "original log", "limits": "bot list only; tape-level detail not archived"})
    p6 = p("fm_forensics", "phase6", "data", "PHASE6_LEDGER.jsonl")
    inv.append({"source": "Phase 6 prospective ledger", "path": "fm_forensics/phase6/data/PHASE6_LEDGER.jsonl",
                "bytes": _size(p6), "pit": "prospective from 2026-10-08", "original": "original",
                "limits": "future collection — excluded from this historical study by instruction"})
    rr = _jsonl(p("fm_forensics", "reread", "data", "reread_records.jsonl"))
    auth = {}
    for r in rr:
        auth[r["au"]] = auth.get(r["au"], 0) + 1
    inv.append({"source": "eye-read register of the images", "path": "fm_forensics/reread/data/reread_records.jsonl",
                "rows": len(rr), "images": len({r["id"] for r in rr}), "by_author": auth,
                "faisal_quotes_nonempty": sum(1 for r in rr if r["au"] == "F" and (r.get("q") or "").strip()),
                "pit": "n/a (sources)", "original": "eye-read 2026-10-10",
                "limits": "dates often relative («6 س»); charts are screenshots, not data"})
    imgs = os.listdir(p("faisal_images"))
    inv.append({"source": "Faisal image corpus", "path": "faisal_images/", "files": len(imgs),
                "pit": "n/a", "original": "original images", "limits": "early IMG_6xxx-8xxx sources survive as text "
                "records only (e.g. IMG_6814, IMG_8057)"})
    os.makedirs(DATA, exist_ok=True)
    json.dump(inv, open(os.path.join(DATA, "inventory.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return inv


if __name__ == "__main__":
    for x in main():
        print(json.dumps({k: x[k] for k in x if k not in ("fields", "meta")}, ensure_ascii=False)[:400])
