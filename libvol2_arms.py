#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔓💧🛑 `T-LIBVOL-2` — «سجّل وقف الكسر» (العقد `libvol2_prereg.md` مدفوعٌ
**قبل هذا الملفّ**).

**السؤال (§⓪):** الكسرُ بسيولة (ذراعُ `T-LIBVOL` حرفيًّا) — هل يصير مجديًا حين
يُعاد ضبطُ **الوقف** على **قاع شمعة الكسر** بدل وقف الأساس؟ المتغيّرُ الوقفُ وحدَه.

**المحرّك — إعادةُ استعمالٍ بالاسم:** صفقاتُ `backtest_symbol` الإنتاجية، وخطّةُ
كلّ صفقةٍ بـ`analyze_ticker` عند فهرسها، والحاجزُ `_liberation_levels`، والكسرُ
`_libvol_break`، والحسمُ `_resolve_arm` — **صفرُ منطقٍ منسوخ**.

🔒 **`Super_stock.py` لا يُمَسّ بحرف** — ولا علمَ جديد ولا عتبة.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import sys

FLOOR_YEAR = 30           # §④-4 — أرضيةُ السنة
OUT_ROWS = "libvol2_rows.jsonl"
# `LW0` — المنشورُ في `libvol_result.md §①` (‏`V1` كسرٌ بسيولة · بوقف الأساس)
PUBLISHED_V1 = {"2023": (-0.395, 201), "2024": (-0.392, 260), "2025": (-0.402, 241)}


def _log(m):
    print(m, flush=True)


def r0_of(ret, entry, stop0):
    """نقيّة (‏§③): العائدُ بوحدة مخاطرةِ **وقف الأساس** `R₀ = (entry − stop0)/entry`
    — تُقسَم عليها الأذرعُ كلُّها فلا يُكافأ الوقفُ الأضيق بصِغَر مقامه.
    مخاطرةٌ غيرُ موجبة أو عائدٌ غائب ⇒ `None` يُعَدّ."""
    try:
        e, s = float(entry), float(stop0)
    except (TypeError, ValueError):
        return None
    if e <= 0 or e - s <= 0 or ret is None:
        return None
    try:
        return float(ret) / ((e - s) / e * 100.0)
    except (TypeError, ValueError):
        return None


def plan_at(S, sym, df, i):
    """خطّةُ الصفقة عند الفهرس `i` بنداء `analyze_ticker` **الإنتاجيّ** (لا من
    الحقول المدوَّرة). يرجّع (r, entry, stop0, t1) أو None."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        entry = sum(r["tranches"]) / len(r["tranches"])
        return r, entry, float(r["stop"][0]), float(r["t1"])
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def break_stop(lo, idx):
    """نقيّة (‏§①): وقفُ `W1` = **قاعُ شمعة الكسر نفسُها** `lo[idx]` بلا هامشٍ
    ولا تدوير. `None` عند فهرسٍ خارج المدى."""
    try:
        return float(lo[int(idx)])
    except (TypeError, ValueError, IndexError):
        return None


def arms_for(S, sym, df, tr, fwd, spread):
    """يحسم الأذرعَ الثلاث على **نفس الشموع**: `W0` الأساس · `V1` كسرٌ بسيولة
    بوقف الأساس · `W1` كسرٌ بسيولة بوقفِ قاع شمعة الكسر. يرجّع (صفّ، سبب)."""
    try:
        pos = df.index.get_loc(__import__("pandas").Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    r, entry, stop0, t1 = pl
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)
    vo = fut["Volume"].values.astype(float)
    vol_prev = df["Volume"].iloc[max(0, i - 20):i].values
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    o0, r0, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop0, t1, filled,
                                  spread=spread)
    row = {"symbol": sym, "date": tr["date"], "entry": round(entry, 4),
           "stop0": round(stop0, 4), "t1": round(t1, 4),
           "stop_r": round(stop0, 2), "t1_r": round(t1, 2),
           "o0": o0, "ret0": (round(r0, 1) if r0 is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a")}
    level = S._liberation_levels(r)[0]
    row["level"] = (round(level, 4) if level else None)
    fr, idx, e = S._libvol_break(cl, vo, level, S.CONFIG["BT_LIB_WAIT"],
                                 S.CONFIG["VOL_SPIKE_MULT"], vol_prev)
    row["fill"] = fr
    corrected_arms(S, row, hi, lo, cl, op, vo, stop0, t1, level, vol_prev)   # §⑨ وصفيّ
    if fr != "filled":
        return row, None
    row["entry_v"] = round(e, 2)                    # كما يخزّنه `_libvol_augment`
    ov, rv, _, _ = S._resolve_arm(hi, lo, cl, op, e, stop0, t1, idx + 1,
                                  entry_intrabar=False)
    row["oV"] = ov
    row["retV"] = (round(rv, 1) if rv is not None else None)
    stop2 = break_stop(lo, idx)
    row["stop2"] = (round(stop2, 4) if stop2 is not None else None)
    row["loose"] = bool(stop2 is not None and stop2 < stop0)
    if stop2 is None or stop2 >= e:                  # §① — يُستبعَد ويُعَدّ
        row["skip"] = "الوقفُ عند الدخول"
        return row, None
    ow, rw, _, _ = S._resolve_arm(hi, lo, cl, op, e, stop2, t1, idx + 1,
                                  entry_intrabar=False)
    row["oW"] = ow
    row["retW"] = (round(rw, 1) if rw is not None else None)
    return row, None


def corrected_arms(S, row, hi, lo, cl, op, vo, stop0, t1, level, vol_prev):
    """§⑨ — ذراعان **وصفيّتان** بالمرجع المصحَّح (`list(vol_prev)` بدل المصفوفة
    التي تُميت المرجع): `V1c` بوقف الأساس · `W1c` بوقف قاع شمعة الكسر.
    **لا تحكمان** — تُطبَعان فقط. إلحاقٌ على الصفّ نفسِه."""
    frc, idxc, ec = S._libvol_break(cl, vo, level, S.CONFIG["BT_LIB_WAIT"],
                                    S.CONFIG["VOL_SPIKE_MULT"], list(vol_prev))
    row["fill_c"] = frc
    if frc != "filled":
        return row
    row["entry_c"] = round(ec, 2)
    ovc, rvc, _, _ = S._resolve_arm(hi, lo, cl, op, ec, stop0, t1, idxc + 1,
                                    entry_intrabar=False)
    row["oVc"], row["retVc"] = ovc, (round(rvc, 1) if rvc is not None else None)
    s2 = break_stop(lo, idxc)
    if s2 is None or s2 >= ec:
        row["skip_c"] = "الوقفُ عند الدخول"
        return row
    owc, rwc, _, _ = S._resolve_arm(hi, lo, cl, op, ec, s2, t1, idxc + 1,
                                    entry_intrabar=False)
    row["oWc"], row["retWc"] = owc, (round(rwc, 1) if rwc is not None else None)
    return row


def _agg(rs, key_o, key_r, ent):
    r0s = [v for v in (r0_of(r[key_r], r[ent], r["stop0"]) for r in rs) if v is not None]
    win = sum(1 for r in rs if r[key_o] == "win")
    rets = [r[key_r] for r in rs if r[key_r] is not None]
    return {"n": len(rs), "win_pct": (win / len(rs) * 100.0) if rs else 0.0,
            "r0": (sum(r0s) / len(r0s)) if r0s else 0.0,
            "ret_avg": (sum(rets) / len(rets)) if rets else 0.0, "n_r0": len(r0s)}


def _paired(diffs):
    n = len(diffs)
    if n < 2:
        return (sum(diffs) / n if n else None, None, None)
    m = sum(diffs) / n
    var = sum((d - m) ** 2 for d in diffs) / (n - 1)
    se = (var ** 0.5) / (n ** 0.5)
    return (m, m - 1.96 * se, m + 1.96 * se)


def report(S, rows, year, issues):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    _log(f"\n🔓💧🛑 T-LIBVOL-2 · سنة {year} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4
    # `LW0`-ب: إعادةُ حسم الأساس تطابق المخزَّن بت-بت (سابقةُ `BV0`)
    bad = [r for r in rows if r["o0"] != r["prod_o"] or r["ret0"] != r["prod_ret"]]
    _log(f"   🔒 `LW0`-ب: {len(rows) - len(bad)} من {len(rows)} مطابقةٌ بت-بت لمحرّك الإنتاج")
    if bad:
        b = bad[0]
        _log(f"   ⛔ تفرّق — {b['symbol']}/{b['date']}: {b['o0']}/{b['ret0']} "
             f"مقابل {b['prod_o']}/{b['prod_ret']}")
        return 3
    reasons = {}
    for r in rows:
        reasons[r.get("fill") or "?"] = reasons.get(r.get("fill") or "?", 0) + 1
    _log("   📦 أسبابُ التعبئة: " + " · ".join(f"{k}={v}" for k, v in sorted(reasons.items())))
    fil = [r for r in rows if r.get("fill") == "filled"]
    # `LW0`: `V1` يُعيد `libvol_result.md` بت-بت بـ`_arm_stats` نفسِها
    shaped = [{"entry_libv": r["entry_v"], "stop": r["stop_r"], "t1": r["t1_r"],
               "outcome_libv": r["oV"]} for r in fil]
    m, n, lo, hi = S._arm_stats(shaped, "outcome_libv", "entry_libv")
    pub = PUBLISHED_V1.get(str(year))
    _log(f"   🔒 `LW0`: `V1` بـ`_arm_stats` = {(m if m is not None else 0):+.3f}R · "
         f"{n} محسومة — المنشور {pub}")
    if pub is None or m is None or n != pub[1] or abs(round(m, 3) - pub[0]) > 0.001:
        _log("   ⛔ `LW0` لا يُعيد المنشورَ بت-بت ⇒ عطبُ أداةٍ أو مجتمعٍ — لا رقمَ ذراع")
        return 3
    skip = [r for r in fil if r.get("skip")]
    _log(f"   🔒 الوقفُ عند الدخول: {len(skip)} من {len(fil)} "
         f"({(len(skip) / len(fil) * 100) if fil else 0:.2f}%) — تُستبعَد وتُعلَن")
    use = [r for r in fil if r.get("oW") is not None]
    loose = sum(1 for r in use if r.get("loose"))
    _log(f"   📐 قاعُ شمعة الكسر **دون** وقف الأساس (وقفٌ أرخى): {loose} من {len(use)} "
         f"({(loose / len(use) * 100) if use else 0:.1f}%)")
    # `LW1`: `W1` تفترق عن `V1`
    if not any(r["oW"] != r["oV"] or r["retW"] != r["retV"] for r in use):
        _log("   ⛔ `LW1` `W1` لم تتفرّق عن `V1` إطلاقًا ⇒ `no-op` لا نتيجة")
        return 4
    decW = [r for r in use if r["oW"] in ("win", "loss")]
    decV = [r for r in use if r["oV"] in ("win", "loss")]
    pair0 = [r for r in decW if r["o0"] in ("win", "loss")]          # `W0` مقترن
    pairV = [r for r in decW if r["oV"] in ("win", "loss")]
    aW = _agg(decW, "oW", "retW", "entry_v")
    aV = _agg(decV, "oV", "retV", "entry_v")
    a0 = _agg(pair0, "o0", "ret0", "entry")
    aWc = _agg(pair0, "oW", "retW", "entry_v")
    _log("   ┌─ الأذرع (المقياسُ الحاكم: متوسّطُ R₀ بوحدةِ مخاطرةِ وقف الأساس) ──")
    for nm, a in (("W0 الأساس (مقترنًا على مُعبَّئي W1)", a0),
                  ("W1 كسرٌ بسيولة · وقفُ قاع شمعة الكسر (مقترنًا)", aWc),
                  ("W1 (كلّ المحسوم)", aW),
                  ("V1 كسرٌ بسيولة · وقفُ الأساس (= T-LIBVOL)", aV)):
        _log(f"   │ {nm}: R₀ {a['r0']:+.4f} · محسومة {a['n']} · ربح {a['win_pct']:.2f}% "
             f"· عائدٌ محقَّق {a['ret_avg']:+.2f}%")
    _log("   └────────────────────────────────────────────────────────")
    d0 = [r0_of(r["retW"], r["entry_v"], r["stop0"]) - r0_of(r["ret0"], r["entry"], r["stop0"])
          for r in pair0
          if r0_of(r["retW"], r["entry_v"], r["stop0"]) is not None
          and r0_of(r["ret0"], r["entry"], r["stop0"]) is not None]
    dV = [r0_of(r["retW"], r["entry_v"], r["stop0"]) - r0_of(r["retV"], r["entry_v"], r["stop0"])
          for r in pairV
          if r0_of(r["retW"], r["entry_v"], r["stop0"]) is not None
          and r0_of(r["retV"], r["entry_v"], r["stop0"]) is not None]
    g0 = _paired(d0)
    gV = _paired(dV)
    fmt = (lambda g: (f"{g[0]:+.4f}" if g[0] is not None else "—")
           + (f" [{g[1]:+.3f} · {g[2]:+.3f}]" if g[1] is not None else ""))
    _log(f"   📐 الحاكم `W1 − W0` (مقترنٌ · n={len(d0)}) = {fmt(g0)} R₀ · الحدُّ +0.15")
    _log(f"   📐 الثانويّ `W1 − V1` (أثرُ الوقف وحدَه · n={len(dV)}) = {fmt(gV)} R₀")
    # §⑨ — الذراعان الوصفيّتان بالمرجع المصحَّح (لا تحكمان)
    usec = [r for r in rows if r.get("oWc") is not None]
    decWc = [r for r in usec if r["oWc"] in ("win", "loss")]
    decVc = [r for r in rows if r.get("oVc") in ("win", "loss")]
    pair0c = [r for r in decWc if r["o0"] in ("win", "loss")]
    aWc2 = _agg(pair0c, "oWc", "retWc", "entry_c")
    a0c = _agg(pair0c, "o0", "ret0", "entry")
    aVc = _agg(decVc, "oVc", "retVc", "entry_c")
    d0c = [r0_of(r["retWc"], r["entry_c"], r["stop0"]) - r0_of(r["ret0"], r["entry"], r["stop0"])
           for r in pair0c
           if r0_of(r["retWc"], r["entry_c"], r["stop0"]) is not None
           and r0_of(r["ret0"], r["entry"], r["stop0"]) is not None]
    g0c = _paired(d0c)
    fills_c = {}
    for r in rows:
        fills_c[r.get("fill_c") or "?"] = fills_c.get(r.get("fill_c") or "?", 0) + 1
    _log("   ┌─ §⑨ وصفيٌّ لا يحكم — المرجعُ المصحَّح (عشرون سابقة فعلًا) ──")
    _log("   │ أسبابُ التعبئة: " + " · ".join(f"{k}={v}" for k, v in sorted(fills_c.items())))
    for nm, a in (("W0 (مقترنًا على W1c)", a0c), ("W1c وقفُ قاع الكسر", aWc2),
                  ("V1c وقفُ الأساس", aVc)):
        _log(f"   │ {nm}: R₀ {a['r0']:+.4f} · محسومة {a['n']} · ربح {a['win_pct']:.2f}% "
             f"· عائدٌ محقَّق {a['ret_avg']:+.2f}%")
    _log(f"   │ W1c − W0 (مقترنٌ · n={len(d0c)}) = {fmt(g0c)} R₀ — **وصفيّ**")
    _log("   └────────────────────────────────────────────────────────")
    _log("SUMMARY " + json.dumps(
        {"year": year, "W0": a0, "W1c": aWc, "W1": aW, "V1": aV,
         "diff_W1_W0": g0, "diff_W1_V1": gV, "n_pair0": len(d0), "n_pairV": len(dV),
         "corr": {"W0": a0c, "W1c": aWc2, "V1c": aVc, "diff": g0c, "n": len(d0c),
                  "fill": fills_c},
         "skip": len(skip), "loose": loose, "n_use": len(use), "fill": reasons,
         "n_rows": len(rows)}, ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": year, "p": [[r["symbol"], round(d, 6)] for r, d in zip(pair0, d0)]},
        ensure_ascii=False))
    if len(d0) < FLOOR_YEAR:
        _log(f"   ⛔ `LW3` الأرضية: المقترنة {len(d0)} دون {FLOOR_YEAR} ⇒ لا حكمَ لهذي السنة")
        return 4
    return 0


def main() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    if not year.isdigit():
        _log("⛔ BACKTEST_YEAR مطلوب")
        return 2
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if not frozen or not os.path.exists(frozen):
        _log("⛔ BT_FROZEN_PATH مطلوب (لقطةٌ مجمَّدة)")
        return 2
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2
    if str(asof or "")[:4] != str(year):                         # `LW2`
        _log(f"⛔ `LW2` اللقطة as-of {asof} لا تطابق سنةَ القياس {year} ⇒ خروج 4")
        return 4
    # 🔒 `CAP15`: المنشورُ في `libvol_result.md` قِيس **قبل** اعتماد وقف القاع
    #    (‏08-29) ⇒ يُرجَع الأساسُ قسرًا وإلّا سقط `LW0` بحقّ.
    S.CONFIG["PIVOT_STOP_AT_LOW"] = False
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · نافذة {S.CONFIG['BT_LIB_WAIT']} "
         f"· سيولة {S.CONFIG['VOL_SPIKE_MULT']}× · وقفُ الأساس {S.CONFIG['STOP_BELOW_LOW_PCT']}")
    rows, issues = [], {}
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 60:
                continue
            try:
                trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                        splits=(splits_map or {}).get(sym))
            except Exception as e:                               # noqa: BLE001
                issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
                continue
            for tr in trs:
                row, why = arms_for(S, sym, df, tr, fwd, spread)
                if row is None:
                    issues[why] = issues.get(why, 0) + 1
                    continue
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    return report(S, rows, year, issues)


if __name__ == "__main__":
    sys.exit(main())
