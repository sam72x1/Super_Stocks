#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📡🩸 T-SLIP-NBBO — الانزلاقُ على **العرضِ القائم** (العقد: `slip_nbbo_prereg.md`).

**السؤال:** عند إطلاق الوقف، ما أفضلُ طلبٍ (`NBB`) كان قائمًا في تلك المِلّي
ثانية؟ وهل يصمد فارقُ «وقفه قاعه» (‏`P1` مقابل `P0`) على سعرِ التنفيذ الحقيقيّ؟

**نموذجُ الأمر خطوتان لا واحدة (‏§②):** ① الإطلاق = صفقةٌ عند الوقف أو دونه
(‏`/v3/trades` بطابعها الزمنيّ) ② التنفيذ = **`NBB` السائد لحظتها**
(‏`/v3/quotes`). ⇒ السعرُ المقيسُ **هو** التعبئة لا تقريبٌ لها، فلا ذراعَ
مقصوصة (‏التباسُ `Q2`/`Q2c` في `T-SLIP` يزول من أصله).

🔒 **إعادةُ استعمالٍ بالاسم — صفرُ منطقِ قياسٍ منسوخ:** المِشيةُ والخطط من
`gold_entry_arms.walk_symbol_gold(..., with_plan=True)` · والجلسةُ والزنادُ
وحارسُ المقياس وحسابُ `R` والإحصاءُ من **`slip_arms`** بالاسم · وشموعُ الدقيقة
من `event_exec.hist_minute_bars` عبر `slip_arms.fetch_day`.
**الجديدُ الوحيد جالبان بطابعٍ زمنيّ** — `event_exec.hist_quotes`/`hist_trades`
**تُسقطان الطابع** ولا تُمَسّان (أرقامُهما منشورة · سابقة `CAP15`).

🔴 **وحارسُ المقياس الخامّ `V2b`:** الخططُ **معدَّلة** والاقتباساتُ **خامٌّ
دائمًا**، و`scale_ok` يقارن معدَّلًا بمعدَّل فلا يرى الفرق ⇒ يُشتقّ معاملٌ من
دقيقة الزناد نفسِها ويُتحقَّق **بثلاث نِسَبٍ مستقلّة**، وما لا يُتحقَّق
**يُستبعَد باسمه** (مِجَسُّ الجدوى رأى تقسيمَ 1:30 = معاملَ 0.0333).

قراءةٌ/قياسٌ فقط · **صفرُ مسٍّ بالإنتاج** · لا `LOGIC_VERSION` · الإنتاجُ لا
يستورد هذا الملفّ.
"""
from __future__ import annotations

import json
import os
import sys
import time

# ═══ ثوابتُ العقد — مثبَّتةٌ قبل أيّ رقم ═══
NARMS = ("N0", "N1", "N2", "N3")       # §③: أربعةٌ ولا خامسة
GOV_N = "N1"                            # الحاكمة: NBB السائد لحظة الإطلاق
LOOKBACK_MS = int(os.environ.get("NB_LOOKBACK_MS") or 300_000)   # §② خمسُ دقائق
LAT_MS = int(os.environ.get("NB_LAT_MS") or 1000)                # §③ زمنُ التوجيه
RAW_TOL = float(os.environ.get("NB_RAW_TOL") or 0.02)            # §②-ب V2b
QLIMIT = int(os.environ.get("NB_QLIMIT") or 25000)
TLIMIT = int(os.environ.get("NB_TLIMIT") or 5000)
# 🔴 هامشُ سعرٍ **نسبيّ** مقاسٌ على مصدره لا على ضجيج الآلة: المعاملُ
# **مشتقٌّ بقسمة** (‏`صفقةٌ خامّة ÷ إغلاقٌ معدَّل`) وكلاهما مُقرَّبٌ عند المزوّد
# ⇒ خطأُ اشتقاقٍ نسبيٌّ ‏≈1e-5. والهامشُ ‏5e-4 **أكبرُ منه بمرتبتين وأصغرُ من
# عُشر سنتٍ** في فئتنا (‏0.40-10.00$ · التكُّ 0.1%-2.5%) ⇒ لا يُبدّل حكمًا
# اقتصاديًّا ويمنع ضجيجَ رحلةِ الذهاب والإياب (درسُ `ES9`).
PX_EPS = 5e-4
MAX_FETCH = int(os.environ.get("NB_MAX_FETCH") or 40000)
WORKERS = int(os.environ.get("NB_WORKERS") or 8)
# 🔗 `V4` تكاملٌ عبر الأدوات — أحداثُ الوقف المنشورة في `slip_result.md §①`
EVN = {"2023": 4255, "2024": 4902, "2025": 4895}


def _log(m):
    print(m, flush=True)


# ═══════════════════ دوالُّ نقيّة (تُختبَر مباشرةً) ═══════════════════
def raw_factor(bar, trades, tol=None):
    """نقيّة (‏`V2b`): معاملُ تحويلِ **الخام ⟶ المعدَّل** مشتقًّا من دقيقة
    الزناد نفسِها، **بلا أيّ نداءٍ إضافيّ**.

    `factor = آخرُ صفقةٍ خامّة ÷ إغلاقِ الشمعة المعدَّل` (فإغلاقُ الشمعة **هو**
    آخرُ صفقةٍ فيها) — **ويُتحقَّق بنسبتين مستقلّتين** (القاع والقمّة).
    ترجع `(factor, verified)`؛ وتعذّرٌ ⇒ `(None, False)` — لا يُخمَّن ولا يُصحَّح."""
    t = RAW_TOL if tol is None else float(tol)
    try:
        c, lo_, hi_ = float(bar["c"]), float(bar["l"]), float(bar["h"])
        ps = [float(x["p"]) for x in (trades or []) if x.get("p") is not None]
    except (TypeError, ValueError, KeyError):
        return None, False
    if not ps or any(x != x or x <= 0 for x in (c, lo_, hi_)):
        return None, False
    f = ps[-1] / c                       # الصفقاتُ مرتَّبةٌ تصاعديًّا زمنيًّا
    if f != f or f <= 0:
        return None, False
    ok = True
    for raw, adj in ((min(ps), lo_), (max(ps), hi_)):
        r = raw / adj
        if r != r or r <= 0 or abs(r / f - 1.0) > t:
            ok = False
    return f, ok


def trigger_ms(trades, stop_raw):
    """نقيّة: طابعُ **أوّلِ صفقةٍ سعرُها عند الوقف الخامّ أو دونه**. لا شيء ⇒
    None (‏`no_trade_trigger` — يُعَدّ ولا يُفتَرض)."""
    try:
        s = float(stop_raw)
    except (TypeError, ValueError):
        return None
    # الهامشُ `PX_EPS` مسوَّغٌ عند تعريفه — يمنع إسقاطَ زنادٍ صحيحٍ بسبب
    # خطأِ اشتقاقِ المعامل، ولا يُدخل زنادًا اقتصاديًّا مختلفًا.
    for x in trades or []:
        try:
            p, t = float(x["p"]), int(x["t"])
        except (TypeError, ValueError, KeyError):
            continue
        if p <= s * (1.0 + PX_EPS):
            return t
    return None


def prevailing(quotes, t_ms):
    """نقيّة: **الاقتباسُ السائد** عند `t_ms` = آخرُ اقتباسٍ طابعُه عنده أو قبله.
    ‏`NBBO` دالّةٌ درجيّة، ولهذا تُجلَب نافذةُ رجوعٍ (‏§②). لا شيء ⇒ None."""
    try:
        t = int(t_ms)
    except (TypeError, ValueError):
        return None
    out = None
    for q in quotes or []:
        try:
            qt, b = int(q["t"]), float(q["bid"])
        except (TypeError, ValueError, KeyError):
            continue
        if qt > t:
            break                        # مرتَّبةٌ تصاعديًّا ⇒ لا حاجةَ للبقيّة
        if b > 0:
            out = q
    return out


def nbbo_fills(bar, trades, quotes, stop):
    """نقيّة: أسعارُ التعبئة الأربعة (‏§③) لحدثِ وقفٍ واحد **في فضاء الخطة
    المعدَّل**. ترجع `(الحالة، قاموسٌ أو None)` — والحالةُ **مُسمّاةٌ دائمًا**."""
    try:
        st = float(stop)
        t0 = int(bar["t"])
    except (TypeError, ValueError, KeyError):
        return "no_minutes", None
    f, ok = raw_factor(bar, trades)
    if not ok or not f:
        return "raw_scale_unverified", None
    tms = trigger_ms(trades, st * f)
    if tms is None:
        return "no_trade_trigger", None
    p1 = prevailing(quotes, tms)
    if p1 is None:
        return "no_quotes", None
    p2 = prevailing(quotes, tms + LAT_MS) or p1
    lows = [float(q["bid"]) for q in (quotes or [])
            if q.get("bid") and float(q["bid"]) > 0
            and tms <= int(q["t"]) < t0 + 60_000]
    n1 = float(p1["bid"]) / f
    n3 = (min(lows) / f) if lows else n1
    return "ok", {
        "N0": st, "N1": n1, "N2": float(p2["bid"]) / f, "N3": n3,
        "factor": f, "trigger_ms": tms,
        "bid_size": p1.get("bid_size"),
        "ask": (float(p1["ask"]) / f) if p1.get("ask") else None,
        "bid_above_stop": bool(n1 > st * (1.0 + PX_EPS)),
    }


# ═══════════════════ الجلب (فاشلٌ-آمن · بطابعٍ زمنيّ) ═══════════════════
def _fetch(path, sym, start_ms, end_ms, limit, tries=3):
    """نداءٌ خامٌّ عبر `event_exec._get` **بالاسم** (مفتاحٌ وأخطاءٌ موحّدة).
    ترجع `(النتائج، بلغ السقف؟)` — والسقفُ **يُعلَن ولا يُقصّ صامتًا**."""
    import event_exec as EX                                      # noqa: PLC0415
    url = f"https://api.polygon.io/v3/{path}/{str(sym).upper()}"
    par = {"timestamp.gte": int(start_ms) * 1_000_000,
           "timestamp.lt": int(end_ms) * 1_000_000,
           "order": "asc", "sort": "timestamp", "limit": int(limit)}
    for a in range(tries):
        j = EX._get(url, params=par)
        if j is not None:
            rs = j.get("results") or []
            return rs, bool(len(rs) >= int(limit))
        if a + 1 < tries:
            time.sleep(0.4 * (a + 1))
    return None, False


def fetch_quotes(sym, start_ms, end_ms):
    """اقتباساتُ `NBBO` **بطابعها الزمنيّ** (‏`hist_quotes` تُسقطه ولا تُمَسّ)."""
    rs, trunc = _fetch("quotes", sym, start_ms, end_ms, QLIMIT)
    if rs is None:
        return None, False
    out = []
    for q in rs:
        ts = q.get("sip_timestamp")
        if ts is None or q.get("bid_price") is None:
            continue
        out.append({"t": int(ts) // 1_000_000, "bid": q.get("bid_price"),
                    "ask": q.get("ask_price"), "bid_size": q.get("bid_size")})
    out.sort(key=lambda x: x["t"])
    return out, trunc


def fetch_trades(sym, start_ms, end_ms):
    """الصفقاتُ **بطابعها الزمنيّ** (‏`hist_trades` تُسقطه ولا تُمَسّ)."""
    rs, trunc = _fetch("trades", sym, start_ms, end_ms, TLIMIT)
    if rs is None:
        return None, False
    out = []
    for t in rs:
        ts = t.get("sip_timestamp")
        if ts is None or t.get("price") is None:
            continue
        out.append({"t": int(ts) // 1_000_000, "p": t.get("price"),
                    "s": t.get("size")})
    out.sort(key=lambda x: x["t"])
    return out, trunc


def _window(key):
    """جلبُ نافذةٍ واحدة: (اقتباساتٌ بنافذة رجوع · صفقاتُ دقيقة الزناد)."""
    sym, _day, t0 = key
    q, qt = fetch_quotes(sym, t0 - LOOKBACK_MS, t0 + 60_000)
    tr, tt = fetch_trades(sym, t0, t0 + 60_000)
    return {"q": q, "t": tr, "trunc": bool(qt or tt)}


def main() -> int:                                               # noqa: C901
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    import gold_entry_arms as GE                                 # noqa: PLC0415
    import slip_arms as SL                                       # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    out_p = os.environ.get("NB_OUT") or "slip_nbbo_events.jsonl"
    _log(f"\n{'=' * 78}\n📡🩸 T-SLIP-NBBO — سنة {year}\n{'=' * 78}")
    _log(f"📐 أذرعُ التنفيذ: {' · '.join(NARMS)} · الحاكمة {GOV_N} "
         f"(‏NBB السائد لحظةَ الإطلاق) · الأذرعُ المقيسة {' · '.join(SL.PARMS)}"
         f" · نافذةُ رجوعٍ {LOOKBACK_MS // 1000}ث · زمنُ توجيهٍ {LAT_MS}مِلّي"
         f" · حارسُ الخامّ {RAW_TOL * 100:.1f}%")
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ اللقطةُ فارغة ⇒ خروج 2.")
        return 2
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")

    # ① المِشية — نفسُ محرّك `T-GOLD-ENTRY`/`T-SLIP` بالاسم
    recs, n_syms = [], 0
    yr = year if year and year != "?" else None
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        recs.extend(GE.walk_symbol_gold(sym, df, year=yr, with_plan=True))
        if n_syms % 800 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(recs)}")
    _log(f"🚶 حلقات {len(recs)} · رموزٌ مُشيت {n_syms}")
    if not recs:
        _log("⛔ صفرُ حلقات (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    # ② أحداثُ الوقف + بوّابةُ التكامل `V4`
    days, ev_n = {}, 0
    for e in recs:
        pl = e.get("plan") or {}
        for a in SL.PARMS:
            p = pl.get(a) or {}
            if e[a][0] and e[a][1] == "loss" and p.get("date"):
                days.setdefault((e["sym"], p["date"]), None)
                ev_n += 1
    exp = EVN.get(str(year))
    _log(f"🩸 أحداثُ وقفٍ {ev_n} · أزواجٌ فريدة (رمز، تاريخ) {len(days)}")
    if exp is not None and ev_n != exp:
        _log(f"⛔ `V4`: أحداثُ الوقف {ev_n} ولا تطابق المنشورَ {exp} في "
             f"`slip_result.md §①` ⇒ **عطبُ أداةٍ لا نتيجة** ⇒ خروج 3.")
        return 3
    if exp is not None:
        _log(f"🔗 `V4` تكاملٌ عبر الأدوات: {ev_n} = المنشور ✅")

    # ③ شموعُ الدقيقة (‏`slip_arms.fetch_day` بالاسم) ثم نوافذُ الزناد
    import concurrent.futures as _cf                             # noqa: PLC0415
    t0 = time.time()
    with _cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(SL.fetch_day, k[0], k[1]): k for k in days}
        for i, f in enumerate(_cf.as_completed(futs), 1):
            days[futs[f]] = f.result()
            if i % 800 == 0:
                _log(f"  … شموع {i}/{len(days)} ({time.time() - t0:.0f}ث)")
    _log(f"⬇️ الشموع: {len(days)} زوجًا في {time.time() - t0:.0f}ث")

    why = {"no_minutes": 0, "scale_mismatch": 0, "no_trigger": 0,
           "raw_scale_unverified": 0, "no_trade_trigger": 0, "no_quotes": 0,
           "quotes_truncated": 0, "budget_cut": 0, "fetch_failed": 0}
    # الحدثُ ⟶ نافذته: (رمز، تاريخ، طابعُ دقيقة الزناد)
    ev, wins = [], {}
    for e in recs:
        pl = e.get("plan") or {}
        for a in SL.PARMS:
            p = pl.get(a) or {}
            if not (e[a][0] and e[a][1] == "loss" and p.get("date")):
                continue
            bars = days.get((e["sym"], p["date"]))
            sess = SL.session_slice(bars) if bars else []
            if not sess:
                why["no_minutes"] += 1
                continue
            if not SL.scale_ok(sess[-1]["c"], p.get("dclose")):
                why["scale_mismatch"] += 1
                continue
            k = SL.trigger_index(sess, p["stop"])
            if k is None:
                why["no_trigger"] += 1
                continue
            bar = sess[k]
            key = (e["sym"], p["date"], int(bar["t"]))
            wins.setdefault(key, None)
            ev.append({"e": e, "arm": a, "p": p, "bar": bar, "key": key,
                       "gap": bool(sess[0]["o"] <= float(p["stop"]))})
    keys = sorted(wins)
    _log(f"🪟 نوافذُ الزناد الفريدة: {len(keys)} (لأحداثٍ مؤهَّلة {len(ev)})")
    if len(keys) > MAX_FETCH:
        _log(f"⚠️ قصٌّ مُعلَن: السقف {MAX_FETCH} ⇒ يُقصّ {len(keys) - MAX_FETCH}"
             f" نافذةً (‏`budget_cut`) — لا قصَّ صامت.")
        cut = set(keys[MAX_FETCH:])
        keys = keys[:MAX_FETCH]
    else:
        cut = set()

    # ④ الاقتباسات + الصفقات لكلّ نافذة
    t0 = time.time()
    with _cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_window, k): k for k in keys}
        for i, f in enumerate(_cf.as_completed(futs), 1):
            wins[futs[f]] = f.result()
            if i % 500 == 0:
                _log(f"  … نوافذ {i}/{len(keys)} ({time.time() - t0:.0f}ث)")
    _log(f"⬇️ النوافذ: {len(keys)} في {time.time() - t0:.0f}ث")

    # ⑤ التعبئة لكلّ حدث
    cache, rows = {}, []
    for it in ev:
        p, key = it["p"], it["key"]
        ck = (key, round(float(p["stop"]), 6))
        if ck in cache:
            st, fl = cache[ck]
        elif key in cut:
            st, fl = "budget_cut", None
            cache[ck] = (st, fl)
        else:
            w = wins.get(key) or {}
            # 🔴 **عطلُ الجلب ≠ غيابُ السوق** — يُفصلان باسمَين لا يُخلطان
            #    (‏«حكمٌ سالبٌ بلا سببٍ مُسمًّى يخفي تشخيصَه»): `None` = رمى
            #    المنفذُ بعد المحاولات · و`[]` = نافذةٌ صامتةٌ فعلًا.
            if w.get("q") is None or w.get("t") is None:
                st, fl = "fetch_failed", None
            elif w.get("trunc"):
                st, fl = "quotes_truncated", None
            elif not w["t"]:
                st, fl = "no_trade_trigger", None
            elif not w["q"]:
                st, fl = "no_quotes", None
            else:
                st, fl = nbbo_fills(it["bar"], w["t"], w["q"], p["stop"])
            cache[ck] = (st, fl)
        if st != "ok":
            why[st] += 1
            continue
        rows.append({"sym": it["e"]["sym"], "i": it["e"]["i"], "arm": it["arm"],
                     "date": p["date"], "avg": p["avg"], "stop": p["stop"],
                     "gap": it["gap"], **{q: fl[q] for q in NARMS},
                     "factor": fl["factor"], "bid_size": fl["bid_size"],
                     "ask": fl["ask"], "bid_above_stop": fl["bid_above_stop"],
                     "same_bar": bool(p.get("same_bar"))})
    meas = len(rows)
    cov = 100.0 * meas / max(ev_n, 1)
    _log(f"\n🩺 `V3` التغطية: {meas} من {ev_n} = {cov:.1f}% · مستبعَدون: "
         + " · ".join(f"{k}={v}" for k, v in sorted(why.items())))
    if cov < SL.COV_MIN:
        _log(f"⚠️ التغطيةُ دون {SL.COV_MIN}% ⇒ **النتيجةُ جزئيّةٌ** ويُصرَّح بذلك.")
    try:
        with open(out_p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        _log(f"💾 {out_p}: {len(rows)} صفًّا")
    except Exception as _e:                                      # noqa: BLE001
        _log(f"⚠️ تعذّر حفظُ الصفوف: {type(_e).__name__}")

    fmap = {(r["sym"], r["i"], r["arm"]): r for r in rows}

    def r_of(e, a, q):
        _el, oc, rw = e[a]
        if oc == "win":
            return rw
        r = fmap.get((e["sym"], e["i"], a))
        if r is None or q == "N0":
            return -1.0
        return SL.loss_r(r["avg"], r["stop"], r[q])

    dec = {a: [e for e in recs if e[a][0] and e[a][1] in ("win", "loss")]
           for a in SL.PARMS}
    E = {a: {q: (sum(r_of(e, a, q) for e in dec[a]) / len(dec[a])
                 if dec[a] else None) for q in NARMS} for a in SL.PARMS}

    # ⑥ `V0` مِرساةُ التكامل
    _log("\n🔗 `V0` مِرساةُ التكامل (‏`N0` يجب أن يعيد `gold_entry_result §①`):")
    bad = 0
    for a in SL.PARMS:
        pub = (SL.PUB.get(str(year)) or {}).get(a)
        got = (len(dec[a]), E[a]["N0"])
        okk = (pub is not None and got[0] == pub[0]
               and got[1] is not None and abs(got[1] - pub[1]) < 5e-4)
        bad += 0 if okk else 1
        _log(f"  {a}: محسومة={got[0]} · E(N0)={got[1]:+.3f} · "
             f"المنشور={pub} {'✅ مطابق' if okk else '🔴 متفرّق'}")
    if bad:
        _log("⛔ `V0` سقطت ⇒ **عطبُ أداةٍ لا نتيجة** ⇒ خروج 3.")
        return 3

    # ⑦ `V1` حارسُ الـ`no-op`
    _log("\n🔎 `V1` حارسُ الـ`no-op` (خسائرُ تغيّر سعرُ تعبئتها عن الوقف):")
    chg = {q: sum(1 for r in rows if abs(r[q] - r["stop"]) > 1e-9)
           for q in NARMS}
    for q in NARMS:
        _log(f"  {q}: {chg[q]} من {meas}")
    if chg.get(GOV_N, 0) == 0:
        _log("⛔ `V1`: صفرُ تغيّرٍ في الذراع الحاكمة ⇒ `no-op` ⇒ خروج 4.")
        return 4

    # ⑧ التوزيعات
    _log("\n📉 توزيعُ الانزلاق تحت `N1` (‏% من مستوى الوقف · موجبٌ = أسوأ):")
    for a in SL.PARMS:
        rs = [r for r in rows if r["arm"] == a]
        if not rs:
            continue
        pc = SL._stats([100.0 * (r["stop"] - r["N1"]) / r["stop"] for r in rs])
        rr = SL._stats([-1.0 - SL.loss_r(r["avg"], r["stop"], r["N1"])
                        for r in rs])
        ab = sum(1 for r in rs if r["bid_above_stop"])
        fx = sum(1 for r in rs if abs(r["factor"] - 1.0) > 1e-6)
        _log(f"  {a}: ن={pc['n']} · وسيط={pc['med']:+.2f}% متوسّط={pc['avg']:+.2f}%"
             f" p90={pc['p90']:+.2f}% ⟵⟶ بوحدة المخاطرة: وسيط={rr['med']:+.3f}R"
             f" متوسّط={rr['avg']:+.3f}R p90={rr['p90']:+.3f}R · طلبٌ فوق الوقف="
             f"{ab} ({100.0 * ab / pc['n']:.1f}%) · معاملُ تقسيمٍ ≠ 1: {fx}"
             f" ({100.0 * fx / pc['n']:.1f}%)")
    bs = SL._stats([float(r["bid_size"]) for r in rows
                    if r.get("bid_size") is not None])
    sp = SL._stats([100.0 * (r["ask"] - r["N1"]) / r["N1"] for r in rows
                    if r.get("ask") and r["N1"] > 0])
    _log(f"  📚 حجمُ الطلب عند التعبئة (لوتات): وسيط={bs['med']:.0f} ·"
         f" متوسّط={bs['avg']:.0f} · ن={bs['n']}   |   السبريد عندها:"
         f" وسيط={sp['med']:.2f}% · متوسّط={sp['avg']:.2f}%")

    # ⑨ الجدول والفوارق
    _log(f"\n📊 `E` لكلّ صفقةٍ محسومة (سنة {year}):")
    _log("الذراع" + "".join(f"{q:>10}" for q in NARMS))
    for a in SL.PARMS:
        _log(f"{a:<8}" + "".join(
            f"{E[a][q]:>+10.3f}" if E[a][q] is not None else f"{'—':>10}"
            for q in NARMS))
    if any(E[a][q] is None for a in (SL.PARMS[0], SL.PARMS[1]) for q in NARMS):
        _log("⛔ `E` غيرُ محسوبٍ لذراعٍ حاكمة (مقامٌ فارغ) ⇒ خروج 4.")
        return 4
    _log("\n🎯 الفارقُ P1−P0 تحت كلّ ذراعِ تنفيذ:")
    for q in NARMS:
        _log(f"  {q}: {E['P1'][q] - E['P0'][q]:+.3f}R")
    d0 = E["P1"]["N0"] - E["P0"]["N0"]
    _log(f"  ↳ العامليّة: العرضُ القائم (‏N1−N0) = "
         f"{(E['P1']['N1'] - E['P0']['N1']) - d0:+.3f}R · "
         f"زمنُ التوجيه (‏N2−N1) = "
         f"{(E['P1']['N2'] - E['P0']['N2']) - (E['P1']['N1'] - E['P0']['N1']):+.3f}R"
         f" · ذيلُ الدقيقة (‏N3−N1) = "
         f"{(E['P1']['N3'] - E['P0']['N3']) - (E['P1']['N1'] - E['P0']['N1']):+.3f}R")
    for q in ("N0", GOV_N):
        ra = [r_of(e, "P1", q) for e in dec["P0"]]
        rb = [r_of(e, "P0", q) for e in dec["P0"]]
        lo_, hi_, m = SL._paired(ra, rb)
        _log(f"  فاصلُ 95% للفرق المقترن تحت {q}: "
             f"{(sum(ra) - sum(rb)) / max(m, 1):+.3f}"
             f"{f' [{lo_:+.3f},{hi_:+.3f}]' if lo_ is not None else ''} ن={m}")
    _log("\n⚠️ `NBBO` قمّةُ الدفتر لا عمقُه · وبلا نمذجةِ طابورٍ أو تعبئةٍ"
         " جزئيّة ⇒ **أرضيّةُ ضررٍ لا سقفُه** · ومجموعةُ الخسائر ثابتةٌ بقاع"
         " الشمعة المعدَّلة ولا يُعاد تقريرُها (‏§⑨-1 من العقد).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
