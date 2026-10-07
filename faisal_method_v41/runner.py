# -*- coding: utf-8 -*-
"""
🏃 FAISAL V4.1 — المشغّلُ الأماميّ (§7-8 · §21-22 · §26 · العقد `V41_prereg.md` §⑥-⑦ · §⑯).

لكلّ حالةٍ مختومة: الشموعُ بمسار V4 المجمَّد نفسِه (`v4_run.resolve` · `v4_run.rows_of` · TradingView) ⟵ **لقطةٌ قبل يوم القرار حصرًا**
⟵ جدارُ الجودة F1-F9 ⟵ السياقُ آليًّا (المتاحُ من حصّاد الاقتراض · والباقي UNAVAILABLE بسببه) ⟵ **V4 المجمَّد على اللقطة نفسِها**
⟵ قيدٌ مختومٌ في السجلّ الإلحاقيّ. **والإعادةُ من اللقطة تُعيد المخرَج بايتًا بايتًا (FV50)** لأنّ التشغيلَ نفسَه يجري على اللقطة.

⚖️ المحرّكُ أعمى بالبناء: مُدخَلُه الرمزُ وتاريخُ القرار والسياقُ الآليّ — لا يفتح صورةً ولا سجلَّ فيصل (قفل FV48 بالـAST على `run_case`).
🔒 بلا تلغرام · بلا حالة إنتاج · والجالبون (`fetch_rows` · `fetch_splits` · `live_borrow`) محقونون في السويّة (بلا شبكة).
الأوضاع (`V41_MODE`): verify · smoke (رمزٌ وتاريخٌ تجريبيّان — **ليست حالةَ تحقّق** · لا كتابة) · run (الحالاتُ المختومة بلا قرار) · replay.
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (ROOT, V4, os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import decision_engine as E      # noqa: E402 — المجمَّد (FV41)
import ledger as LG              # noqa: E402
import market_calendar as MC     # noqa: E402

RUNNER_VERSION = "V41-RUNNER 1.0 (2026-10-07)"
MIN_BARS = 40                     # F1 (= R4-DATA-01)
WINDOW = 120                      # نافذةُ فحص F5/F6/F9 (= CYCLE_BARS)
MISS_WINDOW = 60                  # F3
MISS_FAIL = 3                     # F3: غيابُ 3 فأكثر ⟵ INVALID · 1-2 ⟵ WARN
SPLIT_TOL = math.log(1.25)        # F6: ±25% من نسبة التقسيم
SPLIT_MIN = math.log(1.5)         # F6: تقسيمٌ ذو معنى
SHORT_LOOKBACK = 3                # المتاح: لا يسبق القرارَ بأكثر من 3 جلسات
CTB_LOG = os.path.join(ROOT, "ctb_log.jsonl")
DEPS = ("tv_data.py", "market_calendar.py", "Super_stock.py", "faisal_method_v41/runner.py", "faisal_method_v41/ledger.py",
        "faisal_method_v41/freeze.py")
UNAVAILABLE = {
    "offering_pending": "UNAVAILABLE: لا تعريفَ آليٌّ مُتحقَّقٌ لـ«طرحٍ معلَّق» وقتَ النقطة (V41_prereg §⑥)",
    "groups": "UNAVAILABLE: لا مصدرَ نقطيٌّ لدخول القروبات",
    "operator_press": "UNAVAILABLE: لا مصدرَ لبصمة المضارب بعد انتهاء Polygon 2026-09-29 (CR-01)",
}


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ── التقويم ─────────────────────────────────────────────────────────────────
def _shift(d, k):
    import datetime as dt
    return (dt.date.fromisoformat(d) + dt.timedelta(days=k)).isoformat()


def is_session(d):
    """يومُ تداول = يومُ عملٍ ليس عطلة — `market_calendar.is_trading_day` لا يفحص نهايةَ الأسبوع بتصميمه (لكروناتِ أيّام العمل)."""
    import datetime as dt
    return dt.date.fromisoformat(str(d)[:10]).weekday() < 5 and MC.is_trading_day(str(d)[:10])


def prev_trading_days(asof, n):
    """آخرُ n أيّام تداولٍ قبل asof حصرًا (الأحدثُ أوّلًا)."""
    out, d = [], asof
    while len(out) < n:
        d = _shift(d, -1)
        if is_session(d):
            out.append(d)
    return out


def next_trading_day(d):
    while True:
        d = _shift(d, 1)
        if is_session(d):
            return d


# ── اللقطة وجدارُ الجودة ────────────────────────────────────────────────────
def snapshot(rows, asof):
    """الشموعُ قبل يوم القرار حصرًا (= قصُّ analyze_rows) — وهي وحدَها ما يُشغَّل عليه V4 ويُحفظ."""
    return [list(r) for r in rows if r and str(r[0])[:10] < asof]


def _bad(x):
    return x is None or (isinstance(x, float) and not math.isfinite(x))


def firewall(snap, asof, splits=None, exchange_status=None):
    """F1-F9 على اللقطة ⟵ {verdict · fails · warns}. «INVALID_FOR_VALIDATION» لا يدخل المقاييس ولا يُستبدَل صامتًا."""
    fails, warns = [], []
    dates = [str(r[0])[:10] for r in snap]
    if any(d >= asof for d in dates):
        fails.append("F7_FUTURE_LEAK")
    if len(snap) < MIN_BARS:
        fails.append(f"F1_INSUFFICIENT_HISTORY:{len(snap)}")
    if len(set(dates)) != len(dates):
        fails.append("F4_DUPLICATE_DATES")
    if any(_bad(x) for r in snap for x in (r[1:5] if len(r) >= 5 else [None])):
        fails.append("F9_MISSING_VALUES")
    win = dates[-WINDOW:]
    off = [d for d in win if not is_session(d)]
    if off:
        fails.append(f"F5_NON_SESSION_DATE:{off[:3]}")
    want_last = prev_trading_days(asof, 1)[0]
    if dates and dates[-1] != want_last:
        fails.append(f"F2_STALE:{dates[-1]}≠{want_last}")
    expect = set(prev_trading_days(asof, MISS_WINDOW))
    miss = sorted(expect - set(dates))
    if len(miss) >= MISS_FAIL:
        fails.append(f"F3_MISSING_SESSIONS:{len(miss)}")
    elif miss:
        warns.append(f"F3_MISSING_SESSIONS:{len(miss)}")
    if splits is None:
        warns.append("F6_SPLITS_UNVERIFIED")
    else:
        idx = {d: i for i, d in enumerate(dates)}
        for sd, ratio in splits:
            sd = str(sd)[:10]
            if not ratio or not win or sd < win[0] or sd >= asof or abs(math.log(ratio)) < SPLIT_MIN:
                continue
            i = next((idx[d] for d in dates if d >= sd), None)
            if i is None or i == 0:
                continue
            c0, c1 = snap[i - 1][4], snap[i][4]
            if c0 and c1 and c0 > 0 and c1 > 0 and abs(math.log(c1 / c0) - math.log(1.0 / ratio)) <= SPLIT_TOL:
                fails.append(f"F6_SPLIT_UNADJUSTED:{sd}:{ratio}")
    if exchange_status not in (None, "MATCH"):
        warns.append(f"F8_EXCHANGE:{exchange_status}")
    return {"verdict": "INVALID_FOR_VALIDATION" if fails else "VALID", "fails": fails, "warns": warns,
            "bars": len(snap), "last_bar": dates[-1] if dates else None}


# ── السياق (الصلاحيّة) آليًّا ────────────────────────────────────────────────
def load_ctb(path=CTB_LOG):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def validity_context(symbol, asof, ctb_rows, run_date, live_borrow=None):
    """⟵ (السياق · مصدرُ كلّ حقل). المتاحُ من الحصّاد بتاريخٍ لا يتجاوز يومَ القرار ولا يسبقه بأكثر من 3 جلسات ·
    وإلّا جلبٌ حيٌّ إن كان التشغيلُ خلال جلسةٍ من القرار · وإلّا None — والباقي UNAVAILABLE بسببه."""
    lo = prev_trading_days(asof, SHORT_LOOKBACK)[-1]
    hits = sorted((r for r in ctb_rows if r.get("symbol") == symbol and r.get("shares_available") is not None
                   and lo <= str(r.get("date"))[:10] <= asof), key=lambda r: str(r.get("date")))
    ctx = {"groups": None, "offering_pending": None, "operator_press": None, "short_available": None}
    prov = dict(UNAVAILABLE)
    if hits:
        ctx["short_available"] = int(hits[-1]["shares_available"])
        prov["short_available"] = f"ctb_log:{hits[-1]['date']}:{hits[-1].get('source')}"
    elif live_borrow is not None and run_date <= next_trading_day(asof):
        v = live_borrow(symbol)
        if v is not None:
            ctx["short_available"] = int(v)
            prov["short_available"] = f"live:{run_date}"
        else:
            prov["short_available"] = "UNAVAILABLE: الجلبُ الحيُّ تعذّر"
    else:
        prov["short_available"] = "UNAVAILABLE: لا صفَّ حصادٍ خلال 3 جلساتٍ قبل القرار والتشغيلُ بعد جلسةٍ منه"
    return ctx, prov


# ── التشغيل والإعادة ────────────────────────────────────────────────────────
def decide(snap, asof, ctx, symbol):
    """V4 المجمَّد على اللقطة — `analyze_rows` يقصّ عند asof (واللقطةُ مقصوصةٌ سلفًا)."""
    return E.analyze_rows(snap, asof_date=asof, context=ctx, symbol=symbol)


def deps_hashes(root=ROOT):
    return {p: (_sha_file(os.path.join(root, p)) if os.path.exists(os.path.join(root, p)) else None) for p in DEPS}


def run_case(case, rows, ctx, prov, splits=None, exchange_status=None, meta=None):
    """حالةٌ مختومة ⟵ (حمولةُ قيد V4 · اللقطة). لا يقرأ إلّا الرمزَ وتاريخَ القرار من الحالة."""
    symbol, asof = case["symbol"], case["decision_date"]
    snap = snapshot(rows, asof)
    fw = firewall(snap, asof, splits=splits, exchange_status=exchange_status)
    d = decide(snap, asof, ctx, symbol)
    if d.get("asof") and str(d["asof"]) >= asof:
        fw["fails"].append("F7_ENGINE_ASOF")
        fw["verdict"] = "INVALID_FOR_VALIDATION"
    payload = {"decision": d, "firewall": fw, "context": ctx, "context_provenance": prov,
               "freeze_id": (meta or {}).get("freeze_id"), "freeze_rev": (meta or {}).get("freeze_rev"),
               "meta": dict(meta or {}, runner=RUNNER_VERSION, snapshot_rows=len(snap),
                            snapshot_sha256=sha(snap), state=d.get("state"), tech_state=d.get("tech_state"))}
    return payload, snap


def replay(snap, case, ctx):
    """الإعادةُ من اللقطة المحفوظة ⟵ بصمةُ القرار (يجب أن تساوي `decision_sha256` المسجَّلة)."""
    return sha(decide(snap, case["decision_date"], ctx, case["symbol"]))


def freeze_meta():
    import freeze as FZ
    man = FZ.load()
    cur = FZ.current_revision(man)
    return {"freeze_id": cur["freeze_id"], "freeze_rev": cur["rev"]}, {r["freeze_id"] for r in man["revisions"]}


# ── الجالبون الحيّون (Actions وحدَها) ───────────────────────────────────────
def fetch_rows(symbol):
    import tv_data as TV
    import v4_run as R
    tmap = R._tmap()
    full, bars, tries = R.resolve(symbol, TV.Chart(timeout=30.0), tmap)
    if not full:
        return None, None, tries
    st = "MATCH" if tmap.get(symbol) == full else ("UNMAPPED" if not tmap.get(symbol) else "MISMATCH")
    return R.rows_of(bars), st, tries


def fetch_splits(symbol):
    try:
        import yfinance as yf
        s = yf.Ticker(symbol).splits
        return [(str(k)[:10], float(v)) for k, v in s.items()] if s is not None else []
    except Exception:                                                   # noqa: BLE001
        return None


def live_borrow(symbol):
    try:
        import Super_stock as S
        info = S.ce_borrow_info(symbol) or {}
        return info.get("shares_available")
    except Exception:                                                   # noqa: BLE001
        return None


def _today_ny():
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:                                                   # noqa: BLE001
        return dt.datetime.utcnow().date().isoformat()


def _now_utc():
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(name, obj):
    try:
        import v4_run as R
        R.emit(name, obj)
    except Exception as e:                                              # noqa: BLE001
        print(f"⚠️ emit تعذّر ({type(e).__name__})")


def mode_smoke():
    """تشغيلٌ تجريبيٌّ حيّ على رمزٍ وتاريخ — **ليس حالةَ تحقّق** (لا كلمةَ لفيصل · لا كتابة): يُثبت الجلبَ والجدارَ والمحرّكَ والإعادة."""
    sym = (os.environ.get("V41_SYMBOL") or "").strip().upper().lstrip("$")
    asof = (os.environ.get("V41_ASOF") or "").strip() or _today_ny()
    if not sym:
        print("⛔ V41_SYMBOL فارغ")
        return 2
    rows, st, tries = fetch_rows(sym)
    if not rows:
        print(f"⛔ لا شموع لـ{sym} · {tries}")
        return 2
    fm, _ = freeze_meta()
    ctx, prov = validity_context(sym, asof, load_ctb(), _today_ny(), live_borrow=live_borrow)
    case = {"case_id": "SMOKE", "symbol": sym, "decision_date": asof}
    meta = dict(fm, mode="smoke", commit=os.environ.get("GITHUB_SHA"), run_id=os.environ.get("GITHUB_RUN_ID"),
                deps=deps_hashes(), utc=_now_utc(), source="TradingView via v4_run.resolve", exchange=st)
    payload, snap = run_case(case, rows, ctx, prov, splits=fetch_splits(sym), exchange_status=st, meta=meta)
    h1 = sha(payload["decision"])
    h2, h3 = replay(snap, case, ctx), replay(json.loads(json.dumps(snap)), case, ctx)
    out = {"symbol": sym, "asof": asof, "state": payload["decision"].get("state"), "tech_state": payload["decision"].get("tech_state"),
           "firewall": payload["firewall"], "context_provenance": prov, "decision_sha256": h1, "replay_equal": h1 == h2 == h3,
           "snapshot_rows": len(snap), "freeze_id": fm["freeze_id"], "deps": meta["deps"], "exchange": st}
    print("V41SMOKE " + canon(out))
    _emit(f"v41_smoke_{sym}.json", {"summary": out, "payload": payload})
    return 0 if out["replay_equal"] else 3


def mode_run(ledger=None):
    """كلُّ حالةٍ مختومةٍ بلا قرار V4 لنسختها ⟵ تشغيلٌ وقيد (والـworkflow يُلحق السجلَّ بـmain)."""
    lg = ledger or LG.Ledger()
    fm, fids = freeze_meta()
    ctb = load_ctb()
    done = 0
    for cid in sorted({e["case_id"] for e in lg.entries("case")}):
        c = lg.entries("case", cid)[-1]
        if [e for e in lg.entries("v4", cid) if e.get("case_version") == c["version"]] or lg.entries("invalid", cid):
            continue
        case = lg.read(c["path"])
        rows, st, tries = fetch_rows(case["symbol"])
        if not rows:
            lg.record_invalid(cid, "DATA_UNAVAILABLE", f"لا شموع · {tries}", _now_utc())
            continue
        ctx, prov = validity_context(case["symbol"], case["decision_date"], ctb, _today_ny(), live_borrow=live_borrow)
        meta = dict(fm, mode="run", commit=os.environ.get("GITHUB_SHA"), run_id=os.environ.get("GITHUB_RUN_ID"),
                    deps=deps_hashes(), utc=_now_utc(), source="TradingView via v4_run.resolve", exchange=st)
        payload, snap = run_case(case, rows, ctx, prov, splits=fetch_splits(case["symbol"]), exchange_status=st, meta=meta)
        e = lg.record_v4(cid, payload, snap, _now_utc())
        if payload["firewall"]["verdict"] != "VALID":
            lg.record_invalid(cid, "DATA_QUALITY", payload["firewall"]["fails"], _now_utc())
        print(f"🧊 {cid} {case['symbol']} {case['decision_date']} ⟵ {payload['decision'].get('state')} "
              f"({payload['decision'].get('tech_state')}) · {payload['firewall']['verdict']} · قيد {e['seq']}")
        done += 1
    ok, probs = lg.verify(fids)
    print(f"📒 السجلّ: {'سليم' if ok else '⛔ ' + ' · '.join(probs[:8])} · شُغّلت {done}")
    return 0 if ok else 1


def mode_replay(ledger=None):
    lg = ledger or LG.Ledger()
    bad = []
    for e in lg.entries("v4"):
        rec = lg.read(e["path"])
        snap = lg.read(rec["snapshot_path"])["rows"]
        case = lg.read(rec["case_path"])
        if replay(snap, case, rec["context"]) != rec["decision_sha256"]:
            bad.append(e["case_id"])
    print(f"🔁 الإعادة: {len(lg.entries('v4'))} قرارًا · مختلفٌ {bad or 0}")
    return 0 if not bad else 4


def mode_verify(ledger=None):
    import freeze as FZ
    import holdout as HO
    ok1, p1 = FZ.verify(FZ.load())
    _, fids = freeze_meta()
    ok2, p2 = (ledger or LG.Ledger()).verify(fids)
    m = HO.load()
    ok3 = HO.seal_ok(m)
    pend = LG.pending_new_images()
    print(f"🧊 التجميد {'سليم' if ok1 else p1[:5]} · 📒 السجلّ {'سليم' if ok2 else p2[:5]} · 🚧 ختمُ الاحتجاز {'سليم' if ok3 else '⛔'} · "
          f"صورٌ جديدةٌ تنتظر الالتقاط {len(pend)}")
    return 0 if (ok1 and ok2 and ok3) else 1


def main():
    mode = (os.environ.get("V41_MODE") or "verify").strip()
    return {"verify": mode_verify, "smoke": mode_smoke, "run": mode_run, "replay": mode_replay}.get(mode, mode_verify)()


if __name__ == "__main__":
    sys.exit(main())
