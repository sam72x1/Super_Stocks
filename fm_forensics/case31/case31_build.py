#!/usr/bin/env python3
"""🧱 `T-CASE31` — جمعُ المادّة وبناءُ صفوف السمات للذراع أ (العقد §②-§③) — قراءةٌ فقط.

  collect                  — يقرأ `out/verify.json` ⟵ خطّةُ الأيّام والضابطة من لقطات git ⟵ يجلب مرّةً واحدة: يوميّ و4 ساعات (TradingView) ·
                             تقسيماتُ ياهو والأوبشن · EDGAR · FINRA · هويّةُ الماسح · شموعُ الكون القصيرة (العدوى) · أدقُّ فريمٍ للمنفجرين ⟵ `case31_data/`.
  feat <k> <n> --dir D     — صفوفُ الشريحة k من n: (رمز × يوم قرار) بكلّ سمات الفهرس ⟵ `feat_<k>.json.gz`.
🔒 لا تلغرام · لا Polygon · لا CONFIG يُسنَد · وكلُّ سمةٍ من مادّةٍ مؤرَّخةٍ عند يوم القرار أو قبله.
"""
import datetime as dt
import gzip
import json
import os
import pickle
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import case31 as C                                                # noqa: E402
import case31_catalog as CAT                                      # noqa: E402

DATA = os.path.join(ROOT, "case31_data")
SNAP_MAX_GAP = 3                    # لقطةٌ أبعدُ من 3 أيّامٍ تقويميّة ⟵ ضابطةُ اليوم «غير مقيسة» (العقد §②)
WIN = 20                            # نافذةُ «لم تنفجر» بعد يوم القرار
TV_D_N, TV_H4_N, TV_UNI_N = 1500, 1100, 140
BORROW_DAYS = 7                     # آخرُ قراءةِ اقتراضٍ خلال 7 أيّام حتى يوم القرار
TOOL_DAYS, POST_DAYS = 20, 30
CN = ("China", "Hong Kong")
SECT = {"s_health": ("Health Technology", "Health Services"), "s_tech": ("Technology Services", "Electronic Technology"),
        "s_finance": ("Finance",), "s_consumer": ("Retail Trade", "Consumer Services", "Consumer Durables", "Consumer Non-Durables")}
TOOLS = {"tool20_split_hunter": ("split",), "tool20_split_filter": ("split_filter",), "tool20_method": ("method", "method_relaxed", "method_nogap"),
         "tool20_press": ("press",), "tool20_envelope": ("envelope",), "tool20_three": ("three",)}
MINUTE_FRAMES = ("1", "5", "15", "30", "60")
LEAD_MAX = 20                       # المهلة: حتى 20 جلسةً قبل يوم القرار


def log(m=""):
    print(m, flush=True)


def _dump(name, obj):
    os.makedirs(DATA, exist_ok=True)
    with gzip.open(os.path.join(DATA, name), "wb") as fh:
        pickle.dump(obj, fh, protocol=4)


def _load(d_in, name):
    for base, _dirs, files in os.walk(d_in):
        if name in files:
            with gzip.open(os.path.join(base, name), "rb") as fh:
                return pickle.load(fh)
    return None


# ══ لقطاتُ git ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False).stdout


def snapshots(path):
    """[(طابعُ الإيداع ISO-UTC، الإيداع)] تصاعديًّا لملفٍّ في تاريخ git."""
    out = []
    for ln in _git("log", "--format=%H %cI", "--since=2026-08-01", "--", path).splitlines():
        h, _, ts = ln.partition(" ")
        if h and ts:
            out.append((dt.datetime.fromisoformat(ts).astimezone(dt.timezone.utc).isoformat(), h))
    return sorted(out)


def snap_for(snaps, day):
    """(نقيّة) أوّلُ لقطةٍ بعد إغلاق يوم `day` (بعد 01:00 UTC من اليوم التالي) ضمن `SNAP_MAX_GAP` يومًا ⟵ (طابع، إيداع) أو None."""
    lo = dt.datetime.fromisoformat(day + "T00:00:00+00:00") + dt.timedelta(days=1, hours=1)
    hi = lo + dt.timedelta(days=SNAP_MAX_GAP)
    for ts, h in snaps:
        t = dt.datetime.fromisoformat(ts)
        if lo <= t <= hi:
            return ts, h
    return None


def measured_rows(js):
    """(نقيّة) صفوفُ اللقطة المقيسة في تشغيلتها: التي `last_seen` = أحدثُ تاريخٍ فيها."""
    rows = {k: v for k, v in (js or {}).items() if isinstance(v, dict) and v.get("last_seen")}
    if not rows:
        return {}
    top = max(v["last_seen"] for v in rows.values())
    return {k.upper(): v for k, v in rows.items() if v["last_seen"] == top}


def git_json(commit, path):
    try:
        return json.loads(_git("show", f"{commit}:{path}") or "{}")
    except ValueError:
        return {}


# ══ الخطّة ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def plan_from_verify(V):
    """(نقيّة) جدولُ ⓪ ⟵ {events: [...], days: [أيّامُ قرار ‏+100% في النافذتين]}: حدثٌ واحدٌ للرمز في كلّ نافذة (الأوّل) بعد الإسقاط."""
    seen, ev = set(), []
    for g in sorted(V.get("table") or [], key=lambda g: (g["s"], g["sym"])):
        if g.get("drop") or g["cls"] not in ("x100", "x50") or g["win"] == "قبل النافذة":
            continue
        key = (g["sym"], g["win"], g["cls"])
        if key in seen:
            continue
        seen.add(key)
        ev.append({k: g[k] for k in ("sym", "cls", "win", "D", "s", "p", "b", "close_D", "top", "low", "gov", "one_day", "one_candle",
                                     "sessions", "owner", "tracked")} | {"rs_recent": g.get("rs_recent"), "cat": g.get("cat")})
    days = sorted({e["D"] for e in ev if e["cls"] == "x100"})
    return {"events": ev, "days": days}


def sessions_before(days_all, day, k):
    """(نقيّة) الجلسةُ قبل `day` بـk جلسات من تقويمٍ مرتّب · None إن لم توجد."""
    try:
        i = days_all.index(day)
    except ValueError:
        return None
    return days_all[i - k] if i - k >= 0 else None


# ══ collect ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def tv_frames(symbols, tmap, interval, n, extended):
    import tv_data as TV
    full = {s: tmap.get(s) or f"NASDAQ:{s}" for s in symbols}
    got = TV.fetch_many(sorted(set(full.values())), interval=interval, n=n, extended=extended, workers=6, retry_pass=True)
    return {s: [(int(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4]), float(b[5] or 0.0)) for b in (got.get(f) or [])]
            for s, f in full.items() if got.get(f)}


def scan_identity():
    """هويّةُ السوق من ماسح TradingView (كما هي يومَ الجلب) — تُجرَّب مجموعةُ الأعمدة الكاملة ثمّ الأصغر."""
    import tv_data as TV
    for cols in (["name", "sector", "industry", "country", "float_shares_outstanding", "total_shares_outstanding", "market_cap_basic", "type",
                  "typespecs"],
                 ["name", "sector", "industry", "country", "float_shares_outstanding", "total_shares_outstanding", "market_cap_basic"],
                 ["name", "sector", "industry", "country"]):
        sn = TV.scan(cols)
        if sn:
            return {full.partition(":")[2]: dict(v, _full=full) for full, v in sn.items() if full.startswith(("NASDAQ:", "NYSE:", "AMEX:"))}, cols
    return {}, []


def edgar_full(sym):
    """⟵ {filings: [(تاريخ, نموذج, بنود, وصف)], sic, former: [(اسم, حتى)], category} أو None."""
    import requests
    import Super_stock as S
    cik = S.sec_cik_map().get(sym.upper())
    if not cik:
        return None
    try:
        r = requests.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=S.SEC_UA, timeout=40)
        r.raise_for_status()
        js = r.json()
        rec = ((js.get("filings") or {}).get("recent")) or {}
        n = len(rec.get("form") or [])
        g = lambda k, i: ((rec.get(k) or [""] * n)[i] or "")       # noqa: E731
        return {"filings": [(g("filingDate", i), g("form", i).strip(), g("items", i), g("primaryDocDescription", i)) for i in range(n)],
                "sic": str(js.get("sic") or ""), "category": js.get("category"),
                "former": [(x.get("name"), str(x.get("to") or "")[:10]) for x in js.get("formerNames") or []]}
    except Exception:                                            # noqa: BLE001
        return None
    finally:
        time.sleep(0.15)


def parse_finra(txt):
    """(نقيّة) ملفُّ FINRA اليوميّ ⟵ {رمز: (حجمُ الشورت، الحجمُ الكلّيّ في الملفّ)}."""
    out = {}
    for ln in (txt or "").splitlines():
        p = ln.split("|")
        if len(p) >= 5 and p[0].isdigit():
            try:
                out[p[1].upper()] = (float(p[2]), float(p[4]))
            except ValueError:
                continue
    return out


def finra_day(day):
    """{رمز: (شورت، كلّيّ)} ليومٍ مؤرَّخ من أرشيف FINRA المجّانيّ · {} عند التعذّر (مجهولٌ لا صفر)."""
    import requests
    import Super_stock as S
    url = f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day.replace('-', '')}.txt"
    for _try in range(2):
        try:
            r = requests.get(url, headers=S.UA, timeout=40)
            if r.status_code == 200 and r.text:
                return parse_finra(r.text)
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(1.0)
    return {}


def yahoo_options(sym):
    try:
        import yfinance as yf
        return bool(yf.Ticker(sym).options)
    except Exception:                                            # noqa: BLE001
        return None


def ledgers():
    """سجلّاتُ البوت من المستودع ⟵ {tools: {(أداة، رمز): [أيّام]}, borrow: {رمز: [(يوم، متاح، رسوم)]}, posts: {رمز: [أيّام]}}."""
    tools, borrow, posts = {}, {}, {}

    def lines(p):
        try:
            with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
                for ln in fh:
                    try:
                        yield json.loads(ln)
                    except ValueError:
                        continue
        except OSError:
            return

    for r in lines("hunter_ledger.jsonl"):
        if r.get("kind") == "candidate" and r.get("symbol") and r.get("session"):
            tools.setdefault((str(r.get("hunter")), r["symbol"].upper()), []).append(r["session"])
    for r in lines("press_radar_ledger.jsonl"):
        if r.get("symbol") and r.get("session"):
            tools.setdefault(("press", r["symbol"].upper()), []).append(r["session"])
    for r in lines("ctb_log.jsonl"):
        if r.get("symbol") and r.get("date"):
            borrow.setdefault(r["symbol"].upper(), []).append((r["date"], r.get("shares_available"), r.get("borrow_fee")))
    for r in lines("borrow_watch.jsonl"):
        if r.get("symbol") and r.get("date"):
            borrow.setdefault(r["symbol"].upper(), []).append((r["date"], r.get("available"), r.get("fee")))
    for r in lines("faisal_signals/FAISAL_SIGNAL_LEDGER.jsonl"):
        if r.get("symbol") and r.get("kind") != "retro":
            posts.setdefault(r["symbol"].upper(), []).append(str(r.get("recorded_utc") or "")[:10])
    for r in lines("fm_forensics/fsweep/data/FSWEEP_LEDGER.jsonl"):
        if r.get("symbol") and r.get("post_date") and str(r.get("author") or "").upper().startswith("FAISAL"):
            posts.setdefault(str(r["symbol"]).upper(), []).append(str(r["post_date"])[:10])
    try:
        import csv
        with open(os.path.join(ROOT, "fm_forensics", "phase6", "data", "PHASE6_MENTIONS.csv"), encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("canonical_ticker") and r.get("post_date") and str(r.get("is_faisal")) == "1":
                    posts.setdefault(r["canonical_ticker"].upper(), []).append(r["post_date"][:10])
    except OSError:
        pass
    return {"tools": tools, "borrow": borrow, "posts": posts}


def mode_collect():
    import Super_stock as S
    try:
        V = json.load(open(os.path.join(C.OUT, "verify.json"), encoding="utf-8"))
    except (OSError, ValueError):
        log(f"⛔ لا `out/verify.json` — شغّل verify أوّلًا · خروج {C.RC_DATA}")
        return C.RC_DATA
    plan = plan_from_verify(V)
    nw, wl = snapshots("near_watch.json"), snapshots("weekly_watchlist.json")
    log(f"🗂️ الخطّة: أحداث {len(plan['events'])} · أيّامُ قرار ‏+100% {len(plan['days'])} · لقطات near_watch {len(nw)} · weekly_watchlist {len(wl)}")
    pools, snaps_js = {}, {}
    for d in plan["days"]:
        sp = snap_for(nw, d)
        if not sp:
            pools[d] = None
            continue
        js = snaps_js.setdefault(sp[1], git_json(sp[1], "near_watch.json"))
        rows = measured_rows(js)
        sw = snap_for(wl, d)
        wj = git_json(sw[1], "weekly_watchlist.json") if sw else {}
        pools[d] = {"snap": sp[0], "rows": rows,
                    "in_list": sorted({str(x.get("symbol")).upper() for x in wj.get("stocks") or [] if isinstance(x, dict)}),
                    "in_pullback": sorted({str(x.get("symbol")).upper() for x in wj.get("pullback") or [] if isinstance(x, dict)})}
    need = set(e["sym"] for e in plan["events"])
    for d, p in pools.items():
        if p:
            need |= set(p["rows"])
    need = sorted(need)
    log(f"🧺 رموزُ الذراع أ: {len(need)} · أيّامٌ بلا لقطة: {[d for d, p in pools.items() if not p]}")
    tmap = S._tv_ticker_map() or {}
    bars_d = tv_frames(need, tmap, "1D", TV_D_N, False)
    log(f"📺 يوميّ {len(bars_d)}/{len(need)}")
    bars_h4 = tv_frames(need, tmap, "240", TV_H4_N, True)
    log(f"📺 4 ساعات {len(bars_h4)}/{len(need)}")
    uni = sorted({s.upper() for s in S.get_universe()} | set(need))
    bars_u = tv_frames(uni, tmap, "1D", TV_UNI_N, False)
    log(f"📺 كونٌ قصير {len(bars_u)}/{len(uni)}")
    ident, cols = scan_identity()
    log(f"🪪 الماسح: {len(ident)} رمزًا · أعمدة {cols}")
    splits, edg, opts = {}, {}, {}
    for j, s in enumerate(need):
        splits[s] = C.yahoo_splits(s)
        edg[s] = edgar_full(s)
        opts[s] = yahoo_options(s)
        if j % 100 == 0:
            log(f"   … ياهو/EDGAR {j + 1}/{len(need)}")
    import tv_data as TV
    all_days = sorted({TV.ny_day(b[0]) for s in ("AAPL", "MSFT") for b in bars_u.get(s, [])})
    lo_i = max(0, all_days.index(plan["days"][0]) - 12) if plan["days"] and plan["days"][0] in all_days else 0
    fin_days = [d for d in all_days[lo_i:] if not plan["days"] or d <= plan["days"][-1]]
    finra = {}
    for d in fin_days:
        m = finra_day(d)
        finra[d] = {s: m[s] for s in need if s in m}
    log(f"🩳 FINRA: {sum(1 for d in finra if finra[d])}/{len(fin_days)} يومًا")
    minute, exs = {}, sorted({e["sym"] for e in plan["events"] if e["cls"] == "x100"})
    starts = {}
    for e in plan["events"]:
        if e["cls"] == "x100":
            starts.setdefault(e["sym"], set()).add(e["s"])
    for s in exs:
        full = tmap.get(s) or f"NASDAQ:{s}"
        ch = TV.Chart()
        got, left = {}, set(starts.get(s) or ())
        for fr in MINUTE_FRAMES:                                   # من الأدقّ: يُكتفى بأوّل فريمٍ يغطّي كلَّ أيّام البداية
            b = ch.bars(full, interval=fr, n=5000, extended=True)
            if b:
                got[fr] = [(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5] or 0.0)) for x in b]
                left -= {TV.ny_day(x[0]) for x in b}
            if not left:
                break
        ch.close()
        minute[s] = got
    news = {s: {"news": C.yahoo_news(s)} for s in exs}
    _dump("plan.pkl.gz", {"plan": plan, "pools": pools, "all_days": all_days, "made": dt.datetime.utcnow().isoformat() + "Z"})
    _dump("bars_d.pkl.gz", bars_d)
    _dump("bars_h4.pkl.gz", bars_h4)
    _dump("bars_u.pkl.gz", bars_u)
    _dump("meta.pkl.gz", {"ident": ident, "ident_cols": cols, "splits": splits, "edgar": edg, "options": opts, "finra": finra,
                           "ledgers": ledgers(), "minute": minute, "news": news, "tmap": {s: tmap.get(s) for s in need}})
    cov = {"need": len(need), "daily": len(bars_d), "h4": len(bars_h4), "uni": len(bars_u), "ident": len(ident),
           "splits": sum(1 for v in splits.values() if v is not None), "edgar": sum(1 for v in edg.values() if v),
           "options": sum(1 for v in opts.values() if v is not None), "finra_days": sum(1 for d in finra if finra[d]),
           "minute": {s: sorted(minute[s]) for s in minute}, "days": plan["days"], "no_snapshot": [d for d, p in pools.items() if not p],
           "pool_sizes": {d: len(p["rows"]) for d, p in pools.items() if p}}
    os.makedirs(C.OUT, exist_ok=True)
    with open(os.path.join(C.OUT, "collect_coverage.json"), "w", encoding="utf-8") as fh:
        json.dump(cov, fh, ensure_ascii=False, indent=1)
    log("🧾 التغطية: " + json.dumps({k: v for k, v in cov.items() if k not in ("minute", "pool_sizes")}, ensure_ascii=False))
    return C.RC_OK


# ══ السماتُ غيرُ الشمعيّة (نقيّة · كلُّها بمادّةٍ مؤرَّخةٍ عند يوم القرار أو قبله) ════════════════════════════════════════════════
def _days_between(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def raw_factor(splits, day):
    """حاصلُ نِسب تقسيمات ياهو المنفّذة **بعد** `day` (يحوّل المسوّى إلى خامٍّ يومَها) · 1.0 بلا تقسيماتٍ لاحقة أو عند الجهل."""
    f = 1.0
    for d, r in splits or []:
        if d > day and r and r > 0:
            f *= float(r)
    return f


def short_features(finra, sym, day, days_all, vol_by_day=None):
    """`sh.*` من FINRA: حجمُ الشورت ÷ الحجم الكلّيّ في ملفّ اليوم نفسِه عند `day` ومتوسّطُه في 5 و10 جلسات."""
    out = {"sh.ratio_d": None, "sh.ratio5": None, "sh.ratio10": None, "sh.vol_d": None, "sh.vol_le40k": None}
    if day not in days_all:
        return out
    i = days_all.index(day)

    def ratio(d):
        rec = (finra.get(d) or {}).get(sym)
        if rec is None:
            return None, None
        sv, den = float(rec[0]), float(rec[1])                     # المقامُ = الحجمُ الكلّيّ في ملفّ FINRA نفسِه (المنشأُ نفسُه)
        return (sv / den if den > 0 else None), sv

    r0, sv0 = ratio(day)
    out["sh.ratio_d"], out["sh.vol_d"] = r0, sv0
    out["sh.vol_le40k"] = (sv0 <= 40_000) if sv0 is not None else None
    for k, name in ((5, "sh.ratio5"), (10, "sh.ratio10")):
        xs = [ratio(d)[0] for d in days_all[max(0, i - k + 1):i + 1]]
        xs = [x for x in xs if x is not None]
        out[name] = (sum(xs) / len(xs)) if len(xs) >= max(2, k // 2) else None
    return out


def edgar_features(E, day):
    """`ed.*` و`id.is_shell_sic`/`id.foreign_filer` من إيداعاتٍ بتاريخٍ عند `day` أو قبله."""
    names = ("n424b_90", "n424b_365", "age_424b", "n8k_30", "n8k_3", "n_form4_90", "n_13dg_90", "defic_days_left", "results_age",
             "shelf_active", "s1_365", "proxy_75", "nt_365", "defic_365", "name_change_365", "results_due30")
    out = {f"ed.{k}": None for k in names}
    out["id.is_shell_sic"] = out["id.foreign_filer"] = None
    if not E:
        return out
    F = [(d, f, it) for d, f, it, _desc in E["filings"] if d and d <= day]
    age = lambda d: _days_between(d, day)                          # noqa: E731
    cnt = lambda pred, w: sum(1 for d, f, it in F if age(d) <= w and pred(f, it))   # noqa: E731
    is424 = lambda f, it: f.startswith("424B")                     # noqa: E731
    out["ed.n424b_90"], out["ed.n424b_365"] = float(cnt(is424, 90)), float(cnt(is424, 365))
    a = [age(d) for d, f, it in F if f.startswith("424B")]
    out["ed.age_424b"] = float(min(a)) if a else None
    k8 = lambda f, it: f in ("8-K", "6-K")                         # noqa: E731
    out["ed.n8k_30"], out["ed.n8k_3"] = float(cnt(k8, 30)), float(cnt(k8, 3))
    out["ed.n_form4_90"] = float(cnt(lambda f, it: f == "4", 90))
    out["ed.n_13dg_90"] = float(cnt(lambda f, it: f.startswith(("SC 13D", "SC 13G", "SCHEDULE 13D", "SCHEDULE 13G")), 90))
    out["ed.shelf_active"] = bool(cnt(lambda f, it: f in ("S-3", "F-3", "S-3/A", "F-3/A", "S-3ASR", "F-3ASR"), 3 * 365))
    out["ed.s1_365"] = bool(cnt(lambda f, it: f in ("S-1", "F-1", "S-1/A", "F-1/A"), 365))
    out["ed.proxy_75"] = bool(cnt(lambda f, it: f in ("DEF 14A", "PRE 14A", "DEFA14A", "DEFM14A"), 75))
    out["ed.nt_365"] = bool(cnt(lambda f, it: f.startswith("NT "), 365))
    foreign = any(f in ("20-F", "6-K", "40-F") for d, f, it in F if age(d) <= 730)
    out["id.foreign_filer"] = bool(foreign)
    out["id.is_shell_sic"] = bool(E.get("sic") == "6770")
    if not foreign:
        dd = [age(d) for d, f, it in F if f == "8-K" and "3.01" in (it or "") and age(d) <= 365]
        out["ed.defic_365"] = bool(dd)
        out["ed.defic_days_left"] = float(max(0, 180 - min(dd))) if dd else None
    out["ed.name_change_365"] = bool(any(to and to <= day and _days_between(to, day) <= 365 for _nm, to in E.get("former") or []))
    ra = [age(d) for d, f, it in F if f in ("10-Q", "10-K", "20-F", "40-F") or (f == "8-K" and "2.02" in (it or ""))]
    if ra:
        out["ed.results_age"] = float(min(ra))
        out["ed.results_due30"] = bool(60 <= min(ra) <= 100)
    return out


def split_features(splits, day):
    out = {"cp.rs_n365": None, "cp.rs_n_all": None, "cp.rs_age_days": None, "cp.rs_le60": None}
    if splits is None:
        return out
    rs = [d for d, r in splits if r and r < 1 and d <= day]
    out["cp.rs_n_all"] = float(len(rs))
    out["cp.rs_n365"] = float(sum(1 for d in rs if _days_between(d, day) <= 365))
    out["cp.rs_age_days"] = float(_days_between(max(rs), day)) if rs else None
    out["cp.rs_le60"] = bool(rs and _days_between(max(rs), day) <= 60)
    return out


def identity_features(I, row, close_d, vol_d, vol20, n_bars, day):
    """`id.*` (الهويّة كما هي يومَ الجلب · وفلوتُ صفّ المتابعة يُقدَّم حين تاريخُه عند `day` أو قبله)."""
    out = {f"id.{k}": None for k in ("float", "shares", "mcap", "float_turn_d", "float_turn20", "age_sessions", "is_adr", "c_us", "c_cn_hk",
                                     "c_sg", "c_il", "c_other", "s_health", "s_tech", "s_finance", "s_consumer", "s_other")}
    I = I or {}
    fl = None
    if row and row.get("float") and str(row.get("float_date") or "9999") <= day:
        fl = float(row["float"])
    elif I.get("float_shares_outstanding"):
        fl = float(I["float_shares_outstanding"])
    sh = float(I["total_shares_outstanding"]) if I.get("total_shares_outstanding") else None
    out["id.float"], out["id.shares"] = fl, sh
    out["id.mcap"] = sh * close_d if sh and close_d else None
    out["id.float_turn_d"] = vol_d / fl if fl and vol_d is not None else None
    out["id.float_turn20"] = vol20 / fl if fl and vol20 is not None else None
    out["id.age_sessions"] = float(n_bars) if n_bars else None
    if "typespecs" in I or "type" in I:
        out["id.is_adr"] = bool(I.get("type") == "dr" or "dr" in (I.get("typespecs") or []))
    c = I.get("country")
    if c:
        out["id.c_us"], out["id.c_cn_hk"] = c == "United States", c in CN
        out["id.c_sg"], out["id.c_il"] = c == "Singapore", c == "Israel"
        out["id.c_other"] = not (out["id.c_us"] or out["id.c_cn_hk"] or out["id.c_sg"] or out["id.c_il"])
    s = I.get("sector")
    if s:
        hit = False
        for k, names in SECT.items():
            out[f"id.{k}"] = s in names
            hit = hit or s in names
        out["id.s_other"] = not hit
    return out


def bot_features(pool, pool5, pool10, sym, day, L):
    """`bot.*` و`bw.*` من لقطة يوم القرار وسجلّات الأدوات (كلُّها مؤرَّخةٌ عند `day` أو قبله)."""
    out = {f"bot.{k}": None for k in ("nw_days", "readiness", "score", "n_out", "readiness.d5", "readiness.d10")}
    row = (pool or {}).get("rows", {}).get(sym)
    out["bot.nw_tracked"] = bool(row)
    for k in ("wall_any", "wall_level", "wall_base", "blocked"):
        out[f"bot.{k}"] = None
    if row:
        out["bot.nw_days"] = float(max(0, _days_between(row.get("first_seen") or day, day)))
        for k in ("readiness", "score", "n_out"):
            out[f"bot.{k}"] = float(row[k]) if isinstance(row.get(k), (int, float)) else None
        code = (row.get("wall") or {}).get("code")
        out["bot.wall_any"], out["bot.wall_level"] = bool(code), code == "M_لا_مستوى_مختبر"
        out["bot.wall_base"], out["bot.blocked"] = code == "M4_base_واسعة", bool(row.get("blocked"))
        for k, pk in ((5, pool5), (10, pool10)):
            r2 = (pk or {}).get("rows", {}).get(sym)
            if r2 and isinstance(r2.get("readiness"), (int, float)) and out["bot.readiness"] is not None:
                out[f"bot.readiness.d{k}"] = out["bot.readiness"] - float(r2["readiness"])
    out["bot.in_list"] = (sym in pool["in_list"]) if pool else None
    out["bot.in_pullback"] = (sym in pool["in_pullback"]) if pool else None
    for name, hs in TOOLS.items():
        hit = any(0 <= _days_between(s_, day) <= TOOL_DAYS for h in hs for s_ in L["tools"].get((h, sym), []) if s_ <= day)
        out[f"bot.{name}"] = None if name == "tool20_three" else bool(hit)
    out["bot.faisal_post30"] = bool(any(p and p <= day and _days_between(p, day) <= POST_DAYS for p in L["posts"].get(sym, [])))
    br = [(d, a, fee) for d, a, fee in L["borrow"].get(sym, []) if d <= day and _days_between(d, day) <= BORROW_DAYS and a is not None]
    out["bw.avail"] = out["bw.fee"] = out["bw.avail_le20k"] = None
    if br:
        d, a, fee = max(br)
        out["bw.avail"], out["bw.fee"] = float(a), (float(fee) if fee is not None else None)
        out["bw.avail_le20k"] = bool(float(a) <= 20_000)
    return out


def contagion_index(bars_u, ident, days_all):
    """{يوم: {sector: {…}, industry: {…}, country: {…}}} = مجموعاتُ الرموز التي انفجرت (أعلاها 1.5 × إغلاق سابقتها) في ذلك اليوم."""
    import tv_data as TV
    out = {}
    for s, bars in bars_u.items():
        I = ident.get(s) or {}
        for i in range(1, len(bars)):
            if bars[i - 1][4] > 0 and bars[i][2] >= 1.5 * bars[i - 1][4]:
                d = TV.ny_day(bars[i][0])
                o = out.setdefault(d, {"sector": {}, "industry": {}, "country": {}})
                for k in ("sector", "industry", "country"):
                    if I.get(k):
                        o[k].setdefault(I[k], set()).add(s)
    return out


def contagion_features(cx, ident, sym, day, days_all):
    out = {"ct.sector3": None, "ct.industry3": None, "ct.country3": None}
    I = ident.get(sym) or {}
    if day not in days_all:
        return out
    i = days_all.index(day)
    for k in ("sector", "industry", "country"):
        if not I.get(k):
            continue
        hit = False
        for d in days_all[max(0, i - 2):i + 1]:
            grp = ((cx.get(d) or {}).get(k) or {}).get(I[k]) or set()
            hit = hit or bool(grp - {sym})
        out[f"ct.{k}3"] = hit
    return out


def label(rows_d, day, win=WIN):
    """(نقيّة) ⟵ (انفجر في [D+1، D+20]؟، عددُ الجلسات المتاحة بعد D، عائدُ الصفقة: شراءُ افتتاح D+1 وبيعُ إغلاق D+20 أو آخر شمعة) من يوميٍّ [(يوم,o,h,l,c,v)]."""
    ix = {r[0]: k for k, r in enumerate(rows_d)}
    i = ix.get(day)
    if i is None or rows_d[i][4] <= 0:
        return None, 0, None
    after = rows_d[i + 1:i + 1 + win]
    if not after:
        return None, 0, None
    x = max(r[2] for r in after) >= 2.0 * rows_d[i][4]
    ret = (after[-1][4] / after[0][1] - 1.0) if after[0][1] > 0 else None
    return bool(x), len(after), ret


def bot_reject(sym, df_cut):
    """سببُ رفض فرز البوت عند يوم القرار بأرقام الإنتاج (`analyze_ticker` على شموعٍ مقصوصة) ⟵ «مرشّح» أو رمزُ الرفض أو None."""
    try:
        import Super_stock as S
        S._REJECT_REASONS.pop(sym, None)
        r = S.analyze_ticker(sym, df_cut)
        return "مرشّح" if r else S._REJECT_REASONS.get(sym)
    except Exception:                                            # noqa: BLE001
        return None


def mode_feat(k, n, d_in):
    import pandas as pd
    import case31_feat as F
    import tv_data as TV
    P, meta = _load(d_in, "plan.pkl.gz"), _load(d_in, "meta.pkl.gz")
    bars_d, bars_h4, bars_u = _load(d_in, "bars_d.pkl.gz"), _load(d_in, "bars_h4.pkl.gz"), _load(d_in, "bars_u.pkl.gz")
    if not P or not meta or bars_d is None:
        log(f"⛔ مادّةُ collect ناقصة — خروج {C.RC_DATA}")
        return C.RC_DATA
    plan, pools, all_days = P["plan"], P["pools"], P["all_days"]
    cx = contagion_index(bars_u, meta["ident"], all_days)
    ev_by = {}
    for e in plan["events"]:
        ev_by.setdefault(e["D"], {})[e["sym"]] = e
    nw = snapshots("near_watch.json")
    snap_cache = {}

    def pool_at(day):
        if day is None:
            return None
        if day in pools and pools[day] is not None:
            return pools[day]
        if day not in snap_cache:
            sp = snap_for(nw, day)
            snap_cache[day] = {"rows": measured_rows(git_json(sp[1], "near_watch.json"))} if sp else None
        return snap_cache[day]

    jobs = {}
    for d in plan["days"]:
        syms = set((pools.get(d) or {}).get("rows", {})) | set(ev_by.get(d, {}))
        for s in syms:
            jobs.setdefault(s, set()).add(d)
    for e in plan["events"]:                                       # ذراع +50%: صفُّ المنفجر وحدَه (وصف)
        jobs.setdefault(e["sym"], set()).add(e["D"])
    mine = sorted(s for s in jobs if (sum(map(ord, s)) % n) == k)
    out, t0 = [], time.time()
    for j, s in enumerate(mine):
        rd = bars_d.get(s)
        if not rd:
            for d in sorted(jobs[s]):
                out.append({"sym": s, "D": d, "ok": False, "why": "بلا شموعٍ يوميّة"})
            continue
        rows_d = [(TV.ny_day(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in rd]
        dfD = pd.DataFrame([r[1:] for r in rows_d], columns=["Open", "High", "Low", "Close", "Volume"], index=pd.to_datetime([r[0] for r in rows_d]))
        rh = bars_h4.get(s) or []
        dfH = pd.DataFrame([b[1:] for b in rh], columns=["Open", "High", "Low", "Close", "Volume"],
                           index=pd.to_datetime([TV.ny_time(b[0]).replace(tzinfo=None) for b in rh])) if rh else None
        days_s = [r[0] for r in rows_d]
        vol_by = {r[0]: r[5] for r in rows_d}
        for d in sorted(jobs[s]):
            if d not in vol_by:
                out.append({"sym": s, "D": d, "ok": False, "why": "لا شمعةَ يومَ القرار"})
                continue
            i = days_s.index(d)
            rf = raw_factor(meta["splits"].get(s), d)
            f = F.with_deltas(dfD, dfH, d, rf)
            f.update(short_features(meta["finra"], s, d, all_days, vol_by))
            for kk in (5, 10):
                dprev = sessions_before(all_days, d, kk)
                sp = short_features(meta["finra"], s, dprev, all_days, vol_by) if dprev else {}
                for nm in ("sh.ratio_d", "sh.ratio5", "sh.ratio10", "sh.vol_d"):
                    a, b = f.get(nm), sp.get(nm)
                    f[f"{nm}.d{kk}"] = (a - b) if a is not None and b is not None else None
            pool = pools.get(d)
            row = (pool or {}).get("rows", {}).get(s)
            f.update(edgar_features(meta["edgar"].get(s), d))
            f.update(split_features(meta["splits"].get(s), d))
            f.update(identity_features(meta["ident"].get(s), row, rows_d[i][4], rows_d[i][5], sum(r[5] for r in rows_d[max(0, i - 19):i + 1]),
                                       len(rd) if len(rd) < TV_D_N else None, d))
            f["id.has_options"] = meta["options"].get(s)
            f.update(bot_features(pool, pool_at(sessions_before(all_days, d, 5)), pool_at(sessions_before(all_days, d, 10)), s, d, meta["ledgers"]))
            f.update(contagion_features(cx, meta["ident"], s, d, all_days))
            x, n_after, ret = label(rows_d, d)
            e = ev_by.get(d, {}).get(s)
            rec = {"sym": s, "D": d, "ok": True, "x20": x, "after": n_after, "ret": ret, "ev": (e["cls"], e["win"]) if e else None,
                   "in_pool": bool(row), "f": f}
            if e and e["cls"] == "x100":                           # للمنفجر وحدَه: المهلة (سماتُ الشموع في كلٍّ من 20 جلسةً قبله) وسببُ رفض الفرز يومَها
                rec["lead"] = [F.with_deltas(dfD, dfH, days_s[i - q], rf) for q in range(1, LEAD_MAX + 1) if i - q >= 80]
                rec["bot_reject"] = bot_reject(s, dfD.iloc[:i + 1])
                rec["row"] = row
                lo_i = days_s.index(e["s"]) if e["s"] in vol_by else i + 1
                rec["dd_before"] = (min(r[3] for r in rows_d[i + 1:lo_i + 1]) / rows_d[i + 1][1] - 1.0) if lo_i > i and rows_d[i + 1][1] > 0 else None
            out.append(rec)
        if j % 20 == 0:
            log(f"   … {j + 1}/{len(mine)} رمزًا · {len(out)} صفًّا · {time.time() - t0:.0f}ث")
    os.makedirs(C.OUT, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "case31_feat"), exist_ok=True)
    with gzip.open(os.path.join(ROOT, "case31_feat", f"feat_{k}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "of": n, "rows": out, "catalog_sha": CAT.sha()}, fh, ensure_ascii=False)
    if k == 0:
        with open(os.path.join(ROOT, "case31_feat", "plan_events.json"), "w", encoding="utf-8") as fh:
            json.dump(plan["events"], fh, ensure_ascii=False)
    log(f"🧮 الشريحة {k}/{n}: {len(mine)} رمزًا · {len(out)} صفًّا · سليم {sum(1 for r in out if r.get('ok'))}")
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        log(f"⛔ العقدُ أو الفهرسُ لا يطابق بصمتَه — خروج {C.RC_CONTRACT}")
        return C.RC_CONTRACT
    os.environ.pop("POLYGON_API_KEY", None)
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "collect":
        return mode_collect()
    if mode == "feat":
        d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else DATA
        return mode_feat(int(argv[2]), int(argv[3]), d_in)
    log("الاستعمال: case31_build.py collect | feat <k> <n> --dir D")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
