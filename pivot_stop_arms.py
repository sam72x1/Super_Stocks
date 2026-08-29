#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🛑 `T-PIVOT-BOTTOM` — «سجّل وقف القاع للارتكاز» (العقد `pivot_stop_prereg.md`
مدفوعٌ **قبل هذا الملفّ**، وملحقُه §⑨ **قبل أيّ رقم**).

**السؤال (§①):** على مرشّحي الفارز، هل الوقفُ **عند مِرساة الدخول نفسِها**
(`pivot`) أفضلُ من **‏7% تحتها** — بوحدةِ مخاطرةٍ **واحدةٍ للطرفين**؟

**المحرّك — إعادةُ استعمالٍ بالاسم:** صفقاتُ `backtest_symbol` الإنتاجية، ثم
يُعاد استخراجُ خطّة كلّ صفقةٍ بنداء `analyze_ticker` **عند فهرسها نفسِه** (لا
من الحقول المدوَّرة)، والحسمُ بـ`_resolve_arm` **الإنتاجيّة**.

🔒 **`Super_stock.py` لا يُمَسّ بحرف** — ولا علمَ جديد ولا عتبة.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import sys

FLOOR_DECIDED = 100     # §④-4 — رقمٌ مُعادٌ من `T-EXIT` لا مخترَع
OUT_ROWS = "pivot_stop_rows.jsonl"


def _log(m):
    print(m, flush=True)


def r0_of(ret, entry, stop0):
    """نقيّة (‏§④): العائدُ بوحدة مخاطرة **الإنتاج** `R₀ = entry − stop(B0)`
    — تُقسَم عليها الأذرعُ كلُّها فلا يُكافأ وقفُ القاع بصِغَر مقامه (الفخُّ
    المقيس في `T-RECLAIM-INTRADAY`). مخاطرةٌ غيرُ موجبة ⇒ `None` يُعَدّ."""
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
    """يُعيد خطّةَ الصفقة عند الفهرس `i` بنداء `analyze_ticker` **الإنتاجيّ**
    (لا من الحقول المدوَّرة — التدويرُ يُزيح `filled` في الحالات الحدّية).
    يرجّع (entry, stop0, t1, pivot) أو None."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        entry = sum(r["tranches"]) / len(r["tranches"])
        return entry, float(r["stop"][0]), float(r["t1"]), r.get("pivot")
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def arms_for(S, sym, df, tr, fwd, spread):
    """يحسم الذراعين على **نفس الشموع ونفس التعبئة**: `B0` بوقف الإنتاج و`B1`
    بوقفٍ عند `pivot`. يرجّع صفًّا أو (None، سبب)."""
    try:
        pos = df.index.get_loc(__import__("pandas").Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    entry, stop0, t1, pivot = pl
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    o0, r0, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop0, t1, filled,
                                  spread=spread)
    row = {"symbol": sym, "date": tr["date"], "entry": round(entry, 4),
           "stop0": round(stop0, 4), "t1": round(t1, 4),
           "pivot": (round(float(pivot), 4) if pivot is not None else None),
           "o0": o0, "ret0": (round(r0, 1) if r0 is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a"),
           "rr0": tr.get("rr")}
    if pivot is None:
        row["skip"] = "بلا مِرساة"
        return row, None
    if entry - float(pivot) <= 0:                       # `BV3`
        row["skip"] = "الوقفُ فوق الدخول"
        return row, None
    o1, r1, _, _ = S._resolve_arm(hi, lo, cl, op, entry, float(pivot), t1,
                                  filled, spread=spread)
    row["o1"] = o1
    row["ret1"] = (round(r1, 1) if r1 is not None else None)
    # حدُّ `B2` الأدنى (‏§⑨): `rr` بالوقف الجديد على صفقات الإنتاج وحدها
    try:
        row["rr1"] = round((t1 - entry) / (entry - float(pivot)), 3)
    except (TypeError, ValueError, ZeroDivisionError):
        row["rr1"] = None
    return row, None


def report(rows, year, issues):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    _log(f"\n🛑 T-PIVOT-BOTTOM · سنة {year} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4
    # `BV0`: إعادةُ حسم `B0` تطابق المخزَّن بت-بت
    bad = [r for r in rows
           if r["o0"] != r["prod_o"] or r["ret0"] != r["prod_ret"]]
    _log(f"   🔒 `BV0`: {len(rows) - len(bad)} من {len(rows)} مطابقةٌ بت-بت "
         f"لمحرّك الإنتاج")
    if bad:
        b = bad[0]
        _log(f"   ⛔ `BV0` تفرّق — {b['symbol']}/{b['date']}: "
             f"{b['o0']}/{b['ret0']} مقابل {b['prod_o']}/{b['prod_ret']}")
        return 3
    # `BV2`: حضورُ المِرساة
    have = [r for r in rows if r.get("pivot") is not None]
    cov = len(have) / len(rows) * 100.0
    _log(f"   🔒 `BV2`: المِرساةُ حاضرةٌ في {cov:.1f}% من الصفقات")
    if cov < 95.0:
        _log("   ⛔ `BV2` المِرساةُ غائبةٌ في أكثرَ من 5% ⇒ العلمُ خامل")
        return 3
    over = [r for r in rows if r.get("skip") == "الوقفُ فوق الدخول"]
    _log(f"   🔒 `BV3`: الوقفُ فوق الدخول في {len(over)} صفقة "
         f"({len(over) / len(rows) * 100:.2f}%) — تُستبعَد وتُعلَن")
    use = [r for r in rows if r.get("o1") is not None]
    dec0 = [r for r in use if r["o0"] != "no_fill"]
    dec1 = [r for r in use if r["o1"] != "no_fill"]
    if len(dec0) < FLOOR_DECIDED:
        _log(f"   ⛔ الأرضية: المحسومة {len(dec0)} دون {FLOOR_DECIDED} ⇒ لا حكم")
        return 4
    if all(r["o0"] == r["o1"] and r["ret0"] == r["ret1"] for r in use):
        _log("   ⛔ `BV1` `B1` لم تتفرّق عن `B0` إطلاقًا ⇒ `no-op` لا نتيجة")
        return 4

    def agg(rs, key_o, key_r):
        r0s = [r0_of(r[key_r], r["entry"], r["stop0"]) for r in rs]
        r0s = [v for v in r0s if v is not None]
        win = sum(1 for r in rs if r[key_o] == "win")
        rets = [r[key_r] for r in rs if r[key_r] is not None]
        return {"n": len(rs), "win_pct": (win / len(rs) * 100.0) if rs else 0.0,
                "r0": (sum(r0s) / len(r0s)) if r0s else 0.0,
                "ret_avg": (sum(rets) / len(rets)) if rets else 0.0,
                "n_r0": len(r0s)}
    a0 = agg(dec0, "o0", "ret0")
    a1 = agg(dec1, "o1", "ret1")
    _log("   ┌─ الأذرع (المقياسُ الحاكم: متوسّطُ R₀ بوحدةِ مخاطرة الإنتاج) ──")
    for nm, a in (("B0 (‏7% تحت المِرساة)", a0), ("B1 (‏الوقفُ = المِرساة)", a1)):
        _log(f"   │ {nm}: R₀ {a['r0']:+.4f} · محسومة {a['n']} · "
             f"ربح {a['win_pct']:.2f}% · عائدٌ محقَّق {a['ret_avg']:+.2f}%")
    _log("   └────────────────────────────────────────────────────────")
    _log(f"   📐 B1−B0 بـR₀ = {a1['r0'] - a0['r0']:+.4f}")
    rr_up = [r for r in use if r.get("rr1") is not None and r.get("rr0") is not None]
    lifted = sum(1 for r in rr_up if r["rr0"] < 0.5 <= r["rr1"])
    _log(f"   📈 حدُّ `B2` الأدنى (‏§⑨ — لا يُقاس بل يُوصَف): **متوسّطُ** الارتفاع في "
         f"`rr` = ×{(sum(r['rr1'] / max(r['rr0'], 1e-9) for r in rr_up) / len(rr_up)) if rr_up else 0:.2f}"
         f" · و{lifted} صفقةً كان `rr` يَسِمها نقصًا فرفعه الجديدُ فوق الحدّ")
    _log("SUMMARY " + json.dumps(
        {"year": year, "B0": a0, "B1": a1, "over": len(over),
         "cov": round(cov, 2), "n_rows": len(rows)}, ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": year,
         "p": [[r["symbol"], round(r0_of(r["ret0"], r["entry"], r["stop0"]) or 0.0, 6),
                round(r0_of(r["ret1"], r["entry"], r["stop0"]) or 0.0, 6)]
               for r in use if r["o0"] != "no_fill" or r["o1"] != "no_fill"]},
        ensure_ascii=False))
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
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    # 🛑🔒 وقفُ الارتكاز يُرجَع إلى ‏7% **قسرًا** (سابقةُ `CAP15`): بعد اعتماد
    #     المالك (2026-08-29) صار وقفُ الإنتاج = المِرساة، وبه يصير `B0 ≡ B1`
    #     فتُصبح الأداةُ `no-op` ويُسقطها حارسُها `BV1`. فتُعاد الأرقامُ
    #     المنشورة بت-بت بإرجاع الأساس هنا صراحةً لا بالصمت.
    S.CONFIG["PIVOT_STOP_AT_LOW"] = False
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · وقفُ الإنتاج "
         f"{S.CONFIG['STOP_BELOW_LOW_PCT']}")
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
    return report(rows, year, issues)


if __name__ == "__main__":
    sys.exit(main())
