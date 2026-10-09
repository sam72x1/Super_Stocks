# -*- coding: utf-8 -*-
"""🧭🏁 إعادةُ بناء الكون الكامل لعقد الترتيب (RANKING_PROTOCOL.md §②) — تعمل على رنر GitHub (TradingView/ياهو/SEC محجوبةٌ من
الجلسة). قراءةٌ فقط · لا تلغرام · لا حالةَ إنتاج · البوتُ المجمَّد والمحرّكُ يُستدعيان كما هما.

الأوضاع (data/rank/):
  universe            ⟵ universe.json   (get_universe() ∪ رموزُ جدران اللمستين المخزَّنة — لا رمزَ من مجموعة فيصل)
  bars                ⟵ bars.json.gz    (TradingView يوميّ مسوّى من 2024-05-01 · بلا قصّ MIN_BARS)
  splits --shard i/n  ⟵ parts/splits_i.json   (_fetch_splits_dq = ياهو ∪ تقويم ناسداك · التعذّر None)
  sec --shard i/n     ⟵ parts/sec_i.json      (أوّلُ إيداعٍ في «recent» + نشراتُ 424B1/4/5 بتواريخها)
  compute --shard i/n ⟵ parts/rows_i.csv.gz   (لكلّ جلسةٍ ورمز: البوتُ المجمَّد + المحرّك · شموعٌ < الجلسة ضمن 800 يوم)
  assemble            ⟵ rows.csv.gz · splits.json · sec.json.gz · sessions.csv · manifest.json"""
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time

os.environ.setdefault("FAISAL_ONLY", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("FE_RANK_DATA") or os.path.join(HERE, "data", "rank")
PARTS = os.path.join(OUT, "parts")
BARS_START = "2024-05-01"
SESS_FROM, SESS_TO = "2026-07-09", "2026-10-08"
CAL_MIN_SYMBOLS = int(os.environ.get("FE_CAL_MIN") or 1000)   # engineering — يومٌ في التقويم إن حمل شموعَ 1000 رمزٍ فأكثر (يُخفَّض للتجربة الجافّة وحدَها)
STALE_SESSIONS = 10             # engineering — آخرُ شمعةٍ قبل الجلسة خلال 10 جلسات وإلّا خارج الكون (موقوف/مشطوب)
ANCHOR_REASON = "M_لا_مستوى_مختبر"
OFFERING_FORMS = ("424B1", "424B4", "424B5")
POOL = ("TRIGGER", "READY", "WATCH", "FOCUS", "HOLD")
COLS = ["date", "symbol", "nbars", "last_bar", "bot_res", "bot_gate", "bot_reason", "bot_rank_key", "bot_in_band", "bot_readiness",
        "bot_score", "bot_rr", "eng_stage", "eng_first_failed", "frame", "post_split_since", "post_split_result", "tech_state", "v4_state",
        "state_rule", "rules_passed", "blocks", "missing_n", "missing_rules", "offering", "splits_known", "last_rsplit", "decisive_level",
        "close", "vs_bottom_pct", "in_zone", "hold_sessions", "sessions_in_zone", "bottom_date", "rise_pct", "undercut_pct", "rsi14",
        "vol_vs_20d", "v4_rule_ids"]


def _p(*a):
    return os.path.join(OUT, *a)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _shard(args):
    i, n = 0, 1
    if "--shard" in args:
        i, n = (int(x) for x in args[args.index("--shard") + 1].split("/"))
    return i, n


def _S():
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    import Super_stock as S                                  # noqa: E402
    return S


# ---------------------------------------------------------------- universe
def mode_universe():
    S = _S()
    nas = S.get_universe() or []
    man = json.load(open(os.path.join(HERE, "data", "universe_manifest.json"), encoding="utf-8"))
    walls = sorted({s for v in man["anchor_wall"].values() for s in v})
    syms = sorted(set(nas) | set(walls))
    os.makedirs(OUT, exist_ok=True)
    json.dump({"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "nasdaq": len(nas), "wall_symbols": len(walls),
               "wall_only": len(set(walls) - set(nas)), "symbols": syms}, open(_p("universe.json"), "w"), indent=0)
    print(f"🌐 الكون: ناسداك {len(nas)} ∪ جدران {len(walls)} (خارج ناسداك اليوم {len(set(walls) - set(nas))}) = {len(syms)}")


def _universe():
    return json.load(open(_p("universe.json")))["symbols"]


# ---------------------------------------------------------------- bars
def mode_bars():
    S = _S()
    import tv_data as TV
    syms = _universe()
    tmap = S._tv_ticker_map()
    full = {s: S._tv_full_name(s, tmap) for s in syms}
    n = S._tv_bars_n(BARS_START)
    t0 = time.time()
    got = TV.fetch_many(sorted(set(full.values())), interval="1D", n=n, workers=S.TV_BARS_WORKERS, gate=S.TVBarsGate(),
                        stagger=S.TV_BARS_STAGGER_S, retry_pass=True, retry_pause=S.TV_BARS_RETRY_PAUSE_S) or {}
    daily, none, empty = {}, [], []
    for s in syms:
        b = got.get(full[s])
        if b is None:
            none.append(s); continue
        rows = {}
        for x in b:
            try:
                d = TV.ny_day(x[0])
            except Exception:                                     # noqa: BLE001
                continue
            if d >= BARS_START and all(v is not None for v in x[1:6]):
                rows[d] = [d, round(float(x[1]), 6), round(float(x[2]), 6), round(float(x[3]), 6), round(float(x[4]), 6), float(x[5])]
        if not rows:
            empty.append(s); continue
        daily[s] = [rows[d] for d in sorted(rows)]
    meta = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "start": BARS_START, "n_requested": n,
            "asked": len(syms), "got": len(daily), "none": none, "empty": empty, "map": "scan" if tmap else "nasdaq",
            "secs": round(time.time() - t0, 1), "source": "tradingview · regular session · adjustment=splits"}
    with gzip.open(_p("bars.json.gz"), "wt", encoding="utf-8") as f:
        json.dump({"meta": meta, "daily": daily}, f, separators=(",", ":"))
    print(f"📺 شموع: {len(daily)} من {len(syms)} · تعذّر {len(none)} · فارغ {len(empty)} · {meta['secs']}ث")


def _bars():
    return json.load(gzip.open(_p("bars.json.gz"), "rt", encoding="utf-8"))


# ---------------------------------------------------------------- splits
def mode_splits(args):
    S = _S()
    i, n = _shard(args)
    syms = _universe()[i::n]
    budget = float(os.environ.get("FE_SPLIT_BUDGET_S") or 2400)
    out, t0, ok, fail = {}, time.time(), 0, 0
    for s in syms:
        if time.time() - t0 > budget:
            break
        try:
            sp = S._fetch_splits_dq(s)
            if sp is None:
                out[s] = None; fail += 1
            elif isinstance(sp, list):
                out[s] = [[str(d)[:10], float(r)] for d, r in sp]; ok += 1
            else:
                out[s] = [[str(d)[:10], float(r)] for d, r in sp.items()]; ok += 1
        except Exception:                                         # noqa: BLE001
            out[s] = None; fail += 1
    os.makedirs(PARTS, exist_ok=True)
    json.dump({"shard": f"{i}/{n}", "asked": len(syms), "ok": ok, "fail": fail, "not_asked": len(syms) - ok - fail, "splits": out},
              open(os.path.join(PARTS, f"splits_{i}.json"), "w"))
    print(f"🧾 تقسيمات {i}/{n}: معلوم {ok} · مجهول {fail} · لم يُسأل {len(syms) - ok - fail}")


# ---------------------------------------------------------------- SEC
def mode_sec(args):
    import requests
    i, n = _shard(args)
    syms = _universe()[i::n]
    ua = {"User-Agent": (os.environ.get("SEC_CONTACT") or "SuperStocks research bot research@example.com"), "Accept-Encoding": "gzip, deflate"}

    def get(url):
        for k in range(3):
            try:
                r = requests.get(url, headers=ua, timeout=40)
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 404:
                    return {"_status": 404}
            except Exception:                                     # noqa: BLE001
                pass
            time.sleep(1.5 * (k + 1))
        return None
    tick = get("https://www.sec.gov/files/company_tickers.json") or {}
    cmap = {v["ticker"].upper(): int(v["cik_str"]) for v in tick.values() if isinstance(v, dict) and v.get("ticker")}
    out, ok = {}, 0
    for s in syms:
        cik = cmap.get(s.upper()) or cmap.get(s.upper().replace(".", "-"))
        if not cik:
            out[s] = {"status": "no_cik"}; continue
        sub = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        time.sleep(0.12)
        if not sub or "filings" not in sub:
            out[s] = {"status": "error", "cik": cik}; continue
        rec = sub["filings"].get("recent") or {}
        forms, dates = rec.get("form") or [], rec.get("filingDate") or []
        ds = [d for d in dates if d]
        out[s] = {"status": "ok", "cik": cik, "first": (min(ds) if ds else None), "n": len(ds),
                  "off": sorted([[f, d] for f, d in zip(forms, dates) if f in OFFERING_FORMS and d], key=lambda x: x[1])}
        ok += 1
    os.makedirs(PARTS, exist_ok=True)
    json.dump({"shard": f"{i}/{n}", "asked": len(syms), "ok": ok, "cik_map": len(cmap), "sec": out},
              open(os.path.join(PARTS, f"sec_{i}.json"), "w"))
    print(f"🏛️ SEC {i}/{n}: ok {ok} من {len(syms)} · خريطة {len(cmap)}")


def sec_filings(rec):
    """سجلُّ SEC المضغوط ⟵ قائمةُ إيداعاتٍ بشكل المحرّك (`offering_state` يقرأ النماذج والتواريخ وحدَها) · غيرُ ok ⟵ None."""
    if not rec or rec.get("status") != "ok":
        return None
    out = [{"form": f, "filingDate": d} for f, d in rec.get("off") or []]
    if rec.get("first"):
        out.append({"form": "_FIRST_RECENT", "filingDate": rec["first"]})
    return out


# ---------------------------------------------------------------- calendar
def calendar(daily):
    c = {}
    for rows in daily.values():
        for r in rows:
            c[r[0]] = c.get(r[0], 0) + 1
    return sorted(d for d, k in c.items() if k >= CAL_MIN_SYMBOLS)


def sessions(cal):
    return [d for d in cal if SESS_FROM <= d <= SESS_TO]


def window_start(T, days):
    return (dt.date.fromisoformat(T) - dt.timedelta(days=int(days))).isoformat()


def eligible(rows_before, T, cal):
    """في الكون عند T: شمعةٌ قبل T فأكثر · وآخرُها خلال STALE_SESSIONS جلسة (موضعُها في التقويم بالبحث الثنائيّ)."""
    import bisect
    if not rows_before or T not in cal:
        return False
    k_last = bisect.bisect_right(cal, rows_before[-1][0]) - 1
    return k_last >= 0 and cal.index(T) - k_last <= STALE_SESSIONS


# ---------------------------------------------------------------- per-symbol evaluation
_MISS_RX = re.compile(r"\(((?:R4|FE)-[A-Z0-9-]+?)\)")


def bot_eval(S, L, sym, rows):
    """البوتُ المجمَّد = `analyze_ticker` الإنتاجيّ بلا تعطيل (شروطُ `p3lib.run_gates` نفسُها) ⟵ (نتيجة، سبب، r كامل)."""
    df = L.frame(rows)
    S._REJECT_REASONS.pop(sym, None)
    for k in ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M4"):
        S.CONFIG[k] = 0
    S._BT_SPLITS_CTX = None
    if len(df) < S.CONFIG["MIN_BARS"]:
        return "TOO_FEW_BARS", "MIN_BARS", None
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            r = S.analyze_ticker(sym, df)
        except Exception as e:                                   # noqa: BLE001
            return "ERROR", type(e).__name__, None
    if r:
        return "PASS", "", r
    return "REJECT", S._REJECT_REASONS.get(sym, "?"), None


def row_for(S, L, E, sym, rows_all, T, splits, sec):
    rows = [r for r in rows_all if r[0] < T and r[0] >= window_start(T, S.CONFIG["HISTORY_DAYS"])]
    out = {k: "" for k in COLS}
    out.update(date=T, symbol=sym, nbars=len(rows), last_bar=(rows[-1][0] if rows else ""))
    res, why, r = bot_eval(S, L, sym, rows)
    out.update(bot_res=res, bot_gate=("" if res == "PASS" else ("DEPTH" if res == "TOO_FEW_BARS" else L.reason_gate(why))),
               bot_reason=why)
    if r:
        try:
            out["bot_rank_key"] = json.dumps([float(x) for x in S.rank_key(r)])
            out["bot_in_band"] = int(bool(S.in_entry_band(r)))
        except Exception:                                        # noqa: BLE001
            out["bot_rank_key"] = ""
        out.update(bot_readiness=r.get("readiness"), bot_score=r.get("score"), bot_rr=r.get("rr"))
    ctx = {"splits": ([(d, x) for d, x in splits] if splits is not None else None), "sec_filings": sec_filings(sec),
           "float_shares": None, "short_available": None, "groups": None, "operator_press": None}
    rec = E.evaluate(sym, rows, T, ctx, label="HISTORICAL")
    st = rec["stage"]
    ff = rec.get("first_failed") or {}
    scr = rec.get("screen") or {}
    ps = (scr.get("frames") or {}).get("POST_SPLIT") or {}
    out.update(eng_stage=st, eng_first_failed=ff.get("rule", ""), frame=scr.get("frame") or "", post_split_since=ps.get("since", ""),
               post_split_result=ps.get("result", ""), splits_known=int(splits is not None),
               last_rsplit=((rec.get("corporate_actions") or {}).get("last_reverse_split") or ""))
    if st in POOL or res == "PASS":
        v4 = rec.get("v4") or {}
        setup = rec.get("setup") or {}
        stc = setup.get("structure") or {}
        loc = setup.get("price_location") or {}
        mc = setup.get("market_context") or {}
        val = rec.get("validity") or {}
        miss = rec.get("missing_data") or []
        ts = v4.get("tech_state") or ""
        out.update(tech_state=ts, v4_state=v4.get("state") or "", state_rule=(E.V4.STATE_RULE.get(ts, "") if ts else ""),
                   rules_passed="|".join(rec.get("rules_passed") or []), blocks="|".join(b["rule"] for b in rec.get("blocks") or []),
                   missing_n=len(miss), missing_rules="|".join(m.group(1) for x in miss for m in [_MISS_RX.search(x)] if m),
                   offering=("" if "offering_pending" not in val else str(val.get("offering_pending"))),
                   decisive_level=v4.get("decisive_level"), close=loc.get("close"), vs_bottom_pct=loc.get("vs_bottom_pct"),
                   in_zone=("" if loc.get("in_zone") is None else int(bool(loc.get("in_zone")))), hold_sessions=stc.get("hold_sessions"),
                   sessions_in_zone=stc.get("sessions_in_zone"), bottom_date=stc.get("bottom_date") or "", rise_pct=stc.get("rise_pct"),
                   undercut_pct=stc.get("undercut_pct"), rsi14=mc.get("rsi14"), vol_vs_20d=mc.get("volume_vs_20d"),
                   v4_rule_ids="|".join(v4.get("rule_ids") or []))
    return out


def _work(args):
    sym, rows_all, sess, splits, sec, cal = args
    S = _S()
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "phase3"))
    sys.path.insert(0, HERE)
    import p3lib as L                                         # noqa: E402
    import engine as E                                        # noqa: E402
    out = []
    for T in sess:
        before = [r for r in rows_all if r[0] < T]
        if not eligible(before, T, cal):
            continue
        try:
            out.append(row_for(S, L, E, sym, rows_all, T, splits, sec))
        except Exception as e:                                   # noqa: BLE001
            r = {k: "" for k in COLS}
            r.update(date=T, symbol=sym, bot_res="ERROR", eng_stage="ERROR", eng_first_failed=type(e).__name__)
            out.append(r)
    return out


def mode_compute(args):
    import multiprocessing as mp
    i, n = _shard(args)
    B = _bars()
    daily = B["daily"]
    splits = json.load(open(_p("splits.json")))["splits"] if os.path.exists(_p("splits.json")) else {}
    sec = json.load(gzip.open(_p("sec.json.gz"), "rt"))["sec"] if os.path.exists(_p("sec.json.gz")) else {}
    cal = calendar(daily)
    sess = sessions(cal)
    syms = sorted(daily)[i::n]
    daily = {s: daily[s] for s in syms}
    B = None
    t0 = time.time()
    jobs = [(s, daily[s], sess, splits.get(s), sec.get(s), cal) for s in syms]
    procs = int(os.environ.get("FE_PROCS") or os.cpu_count() or 2)
    rows = []
    with mp.get_context("fork").Pool(procs) as pool:
        for k, part in enumerate(pool.imap(_work, jobs, chunksize=4)):
            rows.extend(part)
            if k % 50 == 0:
                print(f"… {k + 1}/{len(jobs)} رموز · {len(rows)} صفًّا · {time.time() - t0:.0f}ث", flush=True)
    os.makedirs(PARTS, exist_ok=True)
    with gzip.open(os.path.join(PARTS, f"rows_{i}.csv.gz"), "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(sorted(rows, key=lambda r: (r["date"], r["symbol"])))
    print(f"🧮 shard {i}/{n}: {len(syms)} رموز × {len(sess)} جلسات ⟵ {len(rows)} صفًّا · {time.time() - t0:.0f}ث")


# ---------------------------------------------------------------- assemble
def mode_assemble():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for f in sorted(os.listdir(PARTS)):
        if f.startswith("rows_"):
            with gzip.open(os.path.join(PARTS, f), "rt", encoding="utf-8") as g:
                rows.extend(csv.DictReader(g))
    rows.sort(key=lambda r: (r["date"], r["symbol"]))
    with gzip.open(_p("rows.csv.gz"), "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    by = {}
    for r in rows:
        d = by.setdefault(r["date"], {"universe": 0, "bot_pass": 0, "anchor_wall": 0, "pool": 0, "errors": 0,
                                      **{f"stage_{s}": 0 for s in POOL + ("REJECTED", "INSUFFICIENT_DATA")}})
        d["universe"] += 1
        d["bot_pass"] += int(r["bot_res"] == "PASS")
        d["anchor_wall"] += int(r["bot_reason"] == ANCHOR_REASON)
        d["pool"] += int(r["eng_stage"] in POOL)
        d["errors"] += int(r["bot_res"] == "ERROR" or r["eng_stage"] == "ERROR")
        k = f"stage_{r['eng_stage']}"
        if k in d:
            d[k] += 1
    keys = ["date", "universe", "bot_pass", "anchor_wall", "pool", "errors"] + [f"stage_{s}" for s in POOL + ("REJECTED", "INSUFFICIENT_DATA")]
    with open(_p("sessions.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows([{"date": d, **v} for d, v in sorted(by.items())])
    man = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "run_id": os.environ.get("GITHUB_RUN_ID"),
           "commit": os.environ.get("GITHUB_SHA"), "sessions": len(by), "rows": len(rows),
           "sess_from": SESS_FROM, "sess_to": SESS_TO, "bars_start": BARS_START, "stale_sessions": STALE_SESSIONS,
           "cal_min_symbols": CAL_MIN_SYMBOLS, "files": {}}
    for f in ("universe.json", "bars.json.gz", "splits.json", "sec.json.gz", "rows.csv.gz", "sessions.csv"):
        if os.path.exists(_p(f)):
            man["files"][f] = {"sha256": _sha(_p(f)), "bytes": os.path.getsize(_p(f))}
    for f in sorted(os.listdir(PARTS)):
        if f.endswith(".json") and (f.startswith("splits_") or f.startswith("sec_")):
            j = json.load(open(os.path.join(PARTS, f)))
            man.setdefault("parts", {})[f] = {k: v for k, v in j.items() if k not in ("splits", "sec")}
    json.dump(man, open(_p("manifest.json"), "w"), indent=1)
    print(f"📦 {len(rows)} صفًّا · {len(by)} جلسة")


def mode_merge():
    """يجمع أجزاءَ التقسيمات وSEC قبل compute (كلُّ جوبِ حسابٍ يحتاجها كاملة)."""
    sp, se = {}, {}
    for f in sorted(os.listdir(PARTS)):
        if f.startswith("splits_") and f.endswith(".json"):
            sp.update(json.load(open(os.path.join(PARTS, f)))["splits"])
        if f.startswith("sec_") and f.endswith(".json"):
            se.update(json.load(open(os.path.join(PARTS, f)))["sec"])
    json.dump({"splits": sp}, open(_p("splits.json"), "w"), separators=(",", ":"))
    with gzip.open(_p("sec.json.gz"), "wt", encoding="utf-8") as f:
        json.dump({"sec": se}, f, separators=(",", ":"))
    print(f"🧩 تقسيمات {len(sp)} (مجهول {sum(1 for v in sp.values() if v is None)}) · SEC {len(se)} (ok {sum(1 for v in se.values() if v.get('status') == 'ok')})")


if __name__ == "__main__":
    a = sys.argv[1:]
    m = a[0] if a else ""
    {"universe": lambda: mode_universe(), "bars": lambda: mode_bars(), "splits": lambda: mode_splits(a), "sec": lambda: mode_sec(a),
     "merge": lambda: mode_merge(), "compute": lambda: mode_compute(a), "assemble": lambda: mode_assemble()}[m]()
