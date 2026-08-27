#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚦 `T-RANK-DENSE` — «رتّب المرتب» (العقد `ranker_dense_prereg.md` مدفوعٌ
`2e5ddd9e` **قبل هذا الملفّ**).

**السؤال (§①):** على كثافةٍ حيّة، هل يوجد مفتاحُ ترتيبٍ مقيسٌ سلفًا يرفع صافيَ
`R` لليوم فوق مُرتِّب الإنتاج؟

**الفجوةُ التي تُصلحها (§⓪):** `backtest_symbol` يمشي بخطوةِ 5 **ويقفز `i += fwd`
(‏40 جلسة) بعد كلّ صفقة** ⇒ كثافةُ المرشّحين ‏1.03-2.08/جلسة بينما الجلسةُ الحيّة
تُنتج ‏59-109 ⇒ **المُرتِّبُ لم يُختبَر قطُّ في الحالة التي يعمل فيها.**

**المحرّك — إعادةُ استعمالٍ بالاسم:** `analyze_ticker` و`_resolve_arm` و
`_arm_a_exit_bar` و`in_entry_band` و`_pit_raw_price` **الإنتاجيّة**، والمحفظةُ
`replay10.replay` بلا تعديلِ حرف، والمرشّحون `replay10.candidates_from_trades`.

🔒 **`Super_stock.py` لا يُمَسّ بحرف.** الأداةُ تكرّر كتلةَ الدخول/التعبئة —
**ومقفولةٌ بـ`RV0`**: بوسيطَي `step=5, jump=True` تُنتج **صفقاتِ الإنتاج نفسَها
حقلًا حقلًا** وإلّا **خروج 3** (سابقةُ `V0` في `kasih_scan`).

🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import statistics
import sys

# ── §③ ثوابتُ العقد (لا خليّةَ ولا ذراعَ تُضاف بعد الأرقام) ───────────────────
DENSE_STEP = 1          # المِشيةُ الكثيفة — جلسةٌ جلسة
CAP = 15                # = `WATCHLIST_SIZE` الحيّ (يُقرأ من الإنتاج ويُقفَل)
N_SEEDS = 200           # شاهدُ الصدفة `Q3`
DENSITY_MIN = 40.0      # `RV1`: وسيطُ المرشّحين لكلّ جلسة (الحيُّ 59-109)
COV_MIN = 95.0          # `RV3`
FLOOR_SESSIONS = 40     # §④-4
FLOOR_TAKEN = 150       # §④-4
OUT_ROWS = "ranker_rows.jsonl"

# حقولُ الصفقة الإنتاجية التي تُقارَن بت-بت في `RV0` (كلُّ ما يُنتجه المحرّك)
RV0_FIELDS = ("symbol", "date", "entry", "stop", "t1", "outcome", "outcome_b",
              "ret_a", "ret_b", "outcome_legacy", "ret_legacy", "tier",
              "n_soft", "readiness", "behav_score", "fsto_chop",
              "fwd_max_gain", "max_draw_pct", "exploded",
              "exit_kind", "exit_date", "fill_date", "eligible_at",
              "rr", "score", "env_vals")


def _log(m):
    print(m, flush=True)


# ── المِشيةُ — كتلةُ الإنتاج نفسُها بوسيطَي مِشية ─────────────────────────────
def walk_symbol(S, sym, df, splits, lo_d, hi_d, *, step, jump, heavy):
    """يُنتج صفقاتِ رمزٍ واحد. `step=5, jump=True, heavy=True` ⇒ **صفقاتُ الإنتاج
    حرفيًّا** (بوّابة `RV0`) · `step=1, jump=False, heavy=False` ⇒ المِشيةُ الكثيفة.

    `heavy` يحكم الحقلين الثقيلين وحدهما (‏`behav_score`/`fsto_chop`) — **ولا
    تقرؤهما ذراعٌ واحدة**، فإسقاطُهما في الوضع الكثيف يوفّر الزمنَ ولا يمسّ قرارًا
    (وهما مقارَنان بت-بت في وضع البوّابة). تعذّرُ رمزٍ ⇒ قائمةٌ فارغة بلا انهيار."""
    C = S.CONFIG
    out = []
    n = len(df)
    fwd = int(C["BACKTEST_FORWARD_DAYS"])
    expl_thr = C["EXPLOSION_PCT"]
    spread = C.get("BT_SPREAD_PCT", 0.0) or 0.0
    i = int(C["MIN_BARS"])
    while i < n - fwd:
        try:
            d_iso = df.index[i - 1].date().isoformat()
        except Exception:                                        # noqa: BLE001
            d_iso = None
        if d_iso is None or (lo_d and d_iso < lo_d) or (hi_d and d_iso > hi_d):
            i += step
            continue
        try:
            r = S.analyze_ticker(sym, df.iloc[:i])
        except Exception:                                        # noqa: BLE001
            r = None
        if not r:
            i += step
            continue
        if splits is not None and S._pit_raw_price(
                r.get("price") or r["tranches"][-1], splits,
                df.index[i - 1]) < C["MIN_PRICE"]:
            i += step
            continue
        entry = sum(r["tranches"]) / len(r["tranches"])
        stop, t1 = r["stop"][0], r["t1"]
        fut = df.iloc[i:i + fwd]
        hi = fut["High"].values.astype(float)
        lo = fut["Low"].values.astype(float)
        cl = fut["Close"].values.astype(float)
        op = fut["Open"].values.astype(float)
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        fwd_max = max_draw = 0.0
        if filled is not None and entry > 0:
            fwd_max = (float(max(hi[filled:])) / entry - 1.0) * 100.0
            max_draw = (float(min(lo[filled:])) / entry - 1.0) * 100.0
        outcome, ret_a, outcome_b, ret_b = S._resolve_arm(
            hi, lo, cl, op, entry, stop, t1, filled, spread=spread)
        _lg_out, _lg_ret, _, _ = S._resolve_arm(
            hi, lo, cl, op, entry, stop, t1, filled, entry_intrabar=False,
            spread=spread)
        _xk, _xi = S._arm_a_exit_bar(hi, lo, cl, entry, stop, t1, filled)
        _rsi_lo = None
        for _f in (r.get("soft_fails") or []):
            if isinstance(_f, str) and "RSI" in _f:
                _rsi_lo = r.get("rsi_min")
                break
        t = {"symbol": sym, "date": str(df.index[i - 1].date()),
             "outcome_legacy": _lg_out,
             "ret_legacy": (round(_lg_ret, 1) if _lg_ret is not None else None),
             "entry": round(entry, 2), "stop": round(stop, 2),
             "t1": round(t1, 2), "outcome": outcome, "outcome_b": outcome_b,
             "ret_a": (round(ret_a, 1) if ret_a is not None else None),
             "ret_b": (round(ret_b, 1) if ret_b is not None else None),
             "tier": r.get("tier"),
             "n_soft": len(r.get("soft_fails") or []),
             "readiness": r.get("readiness"),
             "behav_score": (S.behavior_rise_profile(df.iloc[:i]).get("score")
                             if heavy else None),
             "fsto_chop": ((S.fsto_oscillation(S.full_stoch(
                 df["High"].iloc[:i], df["Low"].iloc[:i],
                 df["Close"].iloc[:i])[0]) or {}).get("chop") if heavy else None),
             "fwd_max_gain": round(fwd_max, 1),
             "max_draw_pct": round(max_draw, 1),
             "exploded": bool(filled is not None and fwd_max >= expl_thr),
             "exit_kind": _xk,
             "exit_date": (str(fut.index[_xi].date()) if len(fut) else None),
             "fill_date": (str(fut.index[filled].date())
                           if filled is not None and len(fut) else None),
             "eligible_at": (str(fut.index[0].date()) if len(fut) else None),
             "rr": r.get("rr"), "score": r.get("score"),
             "env_vals": {
                 "price": r.get("price"), "drop_pct": r.get("drop_pct"),
                 "best_spike": r.get("best_spike"),
                 "base_range": r.get("base_range"),
                 "dollar_vol": r.get("dollar_vol"),
                 "rsi_min": r.get("rsi_min", _rsi_lo), "rsi_now": r.get("rsi"),
                 "n_soft": len(r.get("soft_fails") or []),
                 "readiness": r.get("readiness"), "score": r.get("score"),
                 "rr": r.get("rr"),
                 "gain5": r.get("gain5"), "ma_above": r.get("ma_above"),
                 "gap_above_dist": r.get("gap_above_dist"),
                 "tf_count": r.get("tf_count"),
                 "in_band": S.in_entry_band(r)}}
        if not heavy:                       # §③: بنيةُ الضغط للمرشّح المقبول وحده
            t["press_cell"] = press_cell_at(df.iloc[:i])
        out.append(t)
        i += (fwd if jump else step)
    return out


def press_cell_at(seg):
    """🩸 §③: خليّةُ `T-FUSE` عند لحظة الإشارة — `press_read` و`swept_after_hold`
    و`cell_of` **الثلاثةِ بالاسم** (صفرُ عتبةٍ جديدة). بلا قراءةِ ضغطٍ ⇒ `None`."""
    try:
        import fuse_arms as FU                                   # noqa: PLC0415
        import press_radar as PR                                 # noqa: PLC0415
        pr = PR.press_read(seg)
        if not pr:
            return None
        return FU.cell_of(pr.get("swept_hold"), pr.get("hold_sessions"))
    except Exception:                                            # noqa: BLE001
        return None


# ── §③ الأذرع — خمسٌ ولا سادسة ────────────────────────────────────────────────
def _cell(c):
    return (c.payload or {}).get("press_cell")


def rank_press(c):
    """`Q1` 🥇 الحاكمة: **بنيةُ `F2`** (كنسٌ بعد حفظِ ثلاثِ جلساتٍ فأكثر) أوّلًا
    ثم مفاتيحُ الإنتاج حرفيًّا. سندُها `fuse_result.md`: ‏+0.225R وموجبةٌ في الثلاث."""
    import replay10 as RP                                        # noqa: PLC0415
    return (0 if _cell(c) == "F2" else 1,) + RP.rank_live(c)


def rank_fresh(c):
    """`Q2` شاهدُ التكذيب: **القاعُ الطازج `F1`** أوّلًا — و`T-FUSE` قاسته
    ‏−0.079R. تفوّقُه يعني أن المكسبَ لأيّ مفتاحٍ بنيويّ لا لبنية `F2` بعينها."""
    import replay10 as RP                                        # noqa: PLC0415
    return (0 if _cell(c) == "F1" else 1,) + RP.rank_live(c)


def arms():
    """(اسم، مُرتِّب) — **الترتيبُ والعددُ مثبَّتان في العقد §③.**"""
    import replay10 as RP                                        # noqa: PLC0415
    return [("Q0", RP.rank_live), ("Q1", rank_press),
            ("Q2", rank_fresh), ("Q4", RP.rank_fifo)]


# ── البوّابة `RV0` ────────────────────────────────────────────────────────────
def rv0(S, sample, hist, splits_map, lo_d, hi_d):
    """يُعيد إنتاجَ `backtest_symbol` الإنتاجية بت-بت على عيّنةِ رموز.
    يرجّع (عددُ الصفقات المقارَنة، أوّلُ تفرّقٍ أو None)."""
    n_cmp = 0
    # 🔬 علما الإلحاق (`BT_REPLAY10`/`BT_ENVVALS`) **يُرفعان هنا حصرًا** — بلاهما
    #    لا يُصدر محرّكُ الإنتاج `exit_date`/`env_vals` فتصير البوّابةُ حمراءَ
    #    بنيويًّا (نوعٌ آخرُ من القفل المكسور). ويُستعادان في `finally`.
    _sv = {k: S.CONFIG.get(k) for k in ("BT_REPLAY10", "BT_ENVVALS")}
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    try:
        return _rv0_loop(S, sample, hist, splits_map, lo_d, hi_d)
    finally:
        S.CONFIG.update(_sv)


def _rv0_loop(S, sample, hist, splits_map, lo_d, hi_d):
    n_cmp = 0
    for sym in sample:
        df = hist.get(sym)
        if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 60:
            continue
        sp = (splits_map or {}).get(sym)
        prod = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d), splits=sp)
        mine = walk_symbol(S, sym, df, sp, lo_d, hi_d,
                           step=int(S.CONFIG["BACKTEST_STEP"]), jump=True,
                           heavy=True)
        if len(prod) != len(mine):
            return n_cmp, f"{sym}: عددُ الصفقات {len(prod)} مقابل {len(mine)}"
        for a, b in zip(prod, mine):
            for k in RV0_FIELDS:
                if a.get(k) != b.get(k):
                    return n_cmp, f"{sym}/{a.get('date')}: {k} = {a.get(k)!r} مقابل {b.get(k)!r}"
            n_cmp += 1
    return n_cmp, None


# ── التقرير ───────────────────────────────────────────────────────────────────
def report(rows, year, n_syms, n_seen, n_cmp):
    """يطبع البوّابات وجدولَ الأذرع. رمزُ الخروج: 0 سليم · 3 عطبُ أداة/تغطية ·
    4 `no-op` أو كثافةٌ رقيقة (لا حكم)."""
    import replay10 as RP                                        # noqa: PLC0415
    _log(f"\n🚦 T-RANK-DENSE · سنة {year} · رموزٌ مُشِيَت {n_syms} من {n_seen}")
    cov = (n_syms / n_seen * 100.0) if n_seen else 0.0
    _log(f"   📏 التغطية {cov:.1f}% · صفقاتٌ كثيفة {len(rows)} · "
         f"قورنت في `RV0` {n_cmp}")
    if cov < COV_MIN:
        _log(f"   ⛔ `RV3` التغطية دون {COV_MIN:g}% ⇒ عطبُ أداة")
        return 3
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4

    dates = sorted({str(t["date"]) for t in rows})
    cands, idx, outcome_of = RP.candidates_from_trades(rows, extra_dates=dates)
    if not cands:
        _log("   ⛔ صفرُ مرشّحين (‏`date`/`exit_date` غائبان) ⇒ `no-op`")
        return 4
    sess = sorted(set(idx.values()))
    per = {}
    for c in cands:
        per[c.session] = per.get(c.session, 0) + 1
    dens = statistics.median(sorted(per.values())) if per else 0.0
    _log(f"   📊 الجلسات {len(sess)} · المرشّحون {len(cands)} · "
         f"وسيطُ المرشّحين لكلّ جلسة **{dens:.1f}** (الحيُّ 59-109)")
    if dens < DENSITY_MIN:
        _log(f"   ⛔ `RV1` الكثافةُ دون {DENSITY_MIN:g} ⇒ ما زالت رقيقةً ⇒ لا حكم")
        return 4
    if len(sess) < FLOOR_SESSIONS:
        _log(f"   ⛔ الأرضية: الجلسات {len(sess)} دون {FLOOR_SESSIONS} ⇒ لا حكم")
        return 4

    res, taken_sets, per_sess = {}, {}, {}
    for name, rk in arms():
        out = RP.replay(cands, outcome_of=outcome_of, ranker=rk,
                        capacity=CAP, sessions=sess)
        tk = out["taken"]
        # §④-2: صافي R **لكلّ جلسة** — لأن الفاصلَ المجمَّع عنقودُه الجلسة، ولا
        # يُشتقّ من متوسّطٍ سنويّ. تُطبَع في سطر `DIFFS` ويُجمَّع منها الفاصل.
        _ps = dict.fromkeys(sess, 0.0)
        for c in tk:
            v = RP.r_unit(c.payload)
            if v is not None:
                _ps[c.session] = _ps.get(c.session, 0.0) + v
        per_sess[name] = _ps
        res[name] = {
            "net_r_day": RP.net_r_per_day(tk, len(sess)),
            "taken": len(tk),
            "expl": sum(1 for c in tk if (c.payload or {}).get("exploded")),
            "cap": out["rejected_cap"], "slot_days": out["slot_days"]}
        taken_sets[name] = {(c.session, c.symbol) for c in tk}

    if taken_sets["Q1"] == taken_sets["Q0"]:
        _log("   ⛔ `RV2` `Q1` لم تتفرّق عن `Q0` إطلاقًا ⇒ `no-op` لا نتيجة")
        return 4
    if res["Q0"]["taken"] < FLOOR_TAKEN:
        _log(f"   ⛔ الأرضية: المأخوذون {res['Q0']['taken']} دون {FLOOR_TAKEN} ⇒ لا حكم")
        return 4

    draws = []
    for s in range(N_SEEDS):
        out = RP.replay(cands, outcome_of=outcome_of,
                        ranker=RP.make_rank_random(s), capacity=CAP, sessions=sess)
        draws.append(RP.net_r_per_day(out["taken"], len(sess)))
    p95 = RP._pct(sorted(draws), 0.95)
    med = statistics.median(sorted(draws))
    res["Q3"] = {"net_r_day": med, "taken": None, "expl": None,
                 "cap": None, "slot_days": None}

    _log("   ┌─ الأذرع (المقياسُ الحاكم: صافي R لليوم) ─────────────────────")
    for name in ("Q0", "Q1", "Q2", "Q4", "Q3"):
        v = res[name]
        extra = ("" if v["taken"] is None else
                 f" · مأخوذ {v['taken']} · منفجرٌ مُسلَّم {v['expl']} · "
                 f"مرفوضٌ بالسعة {v['cap']}")
        _log(f"   │ {name}: {v['net_r_day']:+.4f}{extra}")
    _log(f"   │ Q3 العشوائيّ: وسيط {med:+.4f} · مئين 95 {p95:+.4f} "
         f"(‏{N_SEEDS} بذرة)")
    _log("   └───────────────────────────────────────────────────────────")

    d1 = res["Q1"]["net_r_day"] - res["Q0"]["net_r_day"]
    d2 = res["Q2"]["net_r_day"] - res["Q0"]["net_r_day"]
    d4 = res["Q4"]["net_r_day"] - res["Q0"]["net_r_day"]
    _log(f"   📐 Q1−Q0 = {d1:+.4f} · Q2−Q0 = {d2:+.4f} · Q4−Q0 = {d4:+.4f} · "
         f"Q1 فوق مئين95؟ {'نعم' if res['Q1']['net_r_day'] > p95 else 'لا'}")
    cells = {}
    for c in cands:
        k = _cell(c) or "بلا قراءة"
        cells[k] = cells.get(k, 0) + 1
    tot = sum(cells.values()) or 1
    _log("   🩸 توزيعُ خلايا الضغط: " + " · ".join(
        f"{k} {v} ({v / tot * 100:.1f}%)" for k, v in sorted(cells.items())))
    _log("DIFFS " + json.dumps(
        {"year": year,
         "d": [round(per_sess["Q1"][k] - per_sess["Q0"][k], 6) for k in sess]},
        ensure_ascii=False))
    _log("SUMMARY " + json.dumps(
        {"year": year, "sessions": len(sess), "cands": len(cands),
         "density": round(dens, 2), "p95": round(p95, 4),
         "arms": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                      for kk, vv in v.items()} for k, v in res.items()},
         "cells": cells}, ensure_ascii=False))
    return 0


def main() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    if not year.isdigit():
        _log("⛔ BACKTEST_YEAR مطلوب")
        return 2
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if not frozen or not os.path.exists(frozen):
        _log("⛔ BT_FROZEN_PATH مطلوب (لقطةٌ مجمَّدة — بلاها لا point-in-time)")
        return 2
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2
    if int(S.CONFIG["WATCHLIST_SIZE"]) != CAP:
        _log(f"⛔ السعةُ الحيّة {S.CONFIG['WATCHLIST_SIZE']} لا تساوي {CAP}")
        return 3
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)}")

    smp = [s for s in syms if hist.get(s) is not None][::max(len(syms) // 12, 1)][:12]
    n_cmp, bad = rv0(S, smp, hist, splits_map, lo_d, hi_d)
    if bad:
        _log(f"   ⛔ `RV0` تفرّقٌ عن محرّك الإنتاج — {bad}")
        return 3
    if n_cmp == 0:
        _log("   ⛔ `RV0` صفرُ صفقةٍ قورنت ⇒ البوّابةُ عمياء")
        return 3
    _log(f"   ✅ `RV0` {n_cmp} صفقةً مطابقةً بت-بت لمحرّك الإنتاج")

    rows, n_ok = [], 0
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 60:
                continue
            n_ok += 1
            try:
                tr = walk_symbol(S, sym, df, (splits_map or {}).get(sym),
                                 lo_d, hi_d, step=DENSE_STEP, jump=False,
                                 heavy=False)
            except Exception as e:                               # noqa: BLE001
                _log(f"   ⚠️ {sym}: {type(e).__name__}")
                continue
            for t in tr:
                fh.write(json.dumps(t, ensure_ascii=False) + "\n")
            rows.extend(tr)
            if (k + 1) % 400 == 0:
                _log(f"   … {k + 1}/{len(syms)} · صفقات {len(rows)}")
    return report(rows, year, n_ok, len(syms), n_cmp)


if __name__ == "__main__":
    sys.exit(main())
