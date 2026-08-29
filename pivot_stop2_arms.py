#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🛑② `T-PIVOT-BOTTOM-2` — «قس الوقف من جديد» (العقد `pivot_stop2_prereg.md`
مدفوعٌ **قبل هذا الملفّ**).

**السؤال (§②):** بالدفعات نفسِها والشموع نفسِها والتعبئة نفسِها، ما أثرُ
**الوقفِ المشحون فعلًا** (‏= `tranches[0]` = المِرساة) مقابل **‏7% تحتها** —
**وكم يبعد عن الرقم المنشور؟**

**العيبُ المُصلَح (§①):** الأداةُ السابقة استعملت `r["pivot"]` وقفًا وهو
**قاعُ نافذةِ 25** بينما مِرساةَ الدفعات والوقف `tested_level` بنافذة **‏30**
⇒ **`tested ≤ pivot`** ⇒ ما قِيس ليس ما شُحن.

🔒 **`Super_stock.py` و`pivot_stop_arms.py` لا يُمَسّان بحرف** (سابقةُ
`CAP15`: أرقامُ السابقة منشورةٌ وقابلةٌ للإعادة) — هذي أداةٌ مستقلّة.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import json
import os
import sys

FLOOR_DECIDED = 100          # §④-4 — رقمٌ مُعادٌ من `T-EXIT` لا مخترَع
OUT_ROWS = "pivot_stop2_rows.jsonl"

# §⑤ — أرقامُ `T-PIVOT-BOTTOM` المنشورة (تُعاد بت-بت وإلّا عطبُ أداة)
PUB_B0 = {"2023": -0.2010, "2024": -0.1243, "2025": -0.0912}
PUB_B1 = {"2023": -0.0906, "2024": -0.0621, "2025": -0.0715}
PUB_TOL = 1e-3


def _log(m):
    print(m, flush=True)


def r0_of(ret, entry, stop0):
    """§④ — العائدُ بوحدةِ مخاطرة **الإنتاج القديم** `R₀ = entry − stop(C0)`.
    **منقولةٌ حرفيًّا** من `pivot_stop_arms.r0_of` فلا يتفرّق مقياسان."""
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
    الحقول المدوَّرة). يرجّع (entry, stop0, t1, pivot, tranches) أو None."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        trs = [float(x) for x in r["tranches"]]
        entry = sum(trs) / len(trs)
        return (entry, float(r["stop"][0]), float(r["t1"]),
                r.get("pivot"), trs)
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def arms_for(S, sym, df, tr, fwd, spread):
    """يحسم الأذرعَ الثلاث على **نفس الشموع ونفس الدخول ونفس التعبئة** —
    المتغيّرُ **الوقفُ وحدَه**."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    entry, stop0, t1, pivot, trs = pl
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)
    # 🔒 التعبئةُ **واحدةٌ للأذرع الثلاث** (الدخولُ لم يتغيّر) ⇒ مقارنةٌ مزدوجة
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)

    o0, r0, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop0, t1, filled,
                                  spread=spread)
    row = {"symbol": sym, "date": tr["date"], "entry": round(entry, 4),
           "stop0": round(stop0, 4), "t1": round(t1, 4),
           "tr0": round(trs[0], 4),
           "pivot": (round(float(pivot), 4) if pivot is not None else None),
           "o0": o0, "ret0": (round(r0, 1) if r0 is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a")}

    # `C1` — **المشحونُ حيًّا**: الوقفُ = أدنى دفعة = `round(_anchor,2)`
    if entry - trs[0] > 0:
        o1, r1, _, _ = S._resolve_arm(hi, lo, cl, op, entry, trs[0], t1,
                                      filled, spread=spread)
        row["oC1"] = o1
        row["retC1"] = (round(r1, 1) if r1 is not None else None)
    else:
        row["skipC1"] = "الوقفُ فوق الدخول"

    # `C2` — وقفُ الأداة السابقة (‏`r["pivot"]`) بشرطها نفسِه
    if pivot is None:
        row["skipC2"] = "بلا مِرساة"
    elif entry - float(pivot) <= 0:
        row["skipC2"] = "الوقفُ فوق الدخول"
    else:
        o2, r2, _, _ = S._resolve_arm(hi, lo, cl, op, entry, float(pivot), t1,
                                      filled, spread=spread)
        row["oC2"] = o2
        row["retC2"] = (round(r2, 1) if r2 is not None else None)
    return row, None


def _selfcheck_readonly() -> bool:
    """`RV6` — قراءةٌ فقط: صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها
    هي). الملفُّ الوحيدُ المسموحُ فتحُه للكتابة `OUT_ROWS`."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist",
              "save_op_entry_state", "record_new_alerts", "save_near_watch"}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    ok = (n.args and isinstance(n.args[0], ast.Name)
                          and n.args[0].id == "OUT_ROWS")
                    if not ok:
                        return False
    return True


def agg(rs, key_o, key_r):
    """**منقولةٌ حرفيًّا** من `pivot_stop_arms.report.agg` (مقياسٌ واحد)."""
    r0s = [r0_of(r[key_r], r["entry"], r["stop0"]) for r in rs]
    r0s = [v for v in r0s if v is not None]
    win = sum(1 for r in rs if r[key_o] == "win")
    rets = [r[key_r] for r in rs if r[key_r] is not None]
    return {"n": len(rs), "win_pct": (win / len(rs) * 100.0) if rs else 0.0,
            "r0": (sum(r0s) / len(r0s)) if r0s else 0.0,
            "ret_avg": (sum(rets) / len(rets)) if rets else 0.0,
            "n_r0": len(r0s)}


def report(rows, year, issues):
    """خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    _log(f"\n🛑② T-PIVOT-BOTTOM-2 · سنة {year} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4

    # `RV7` — إعادةُ حسم `C0` تطابق المخزَّن بت-بت
    bad = [r for r in rows
           if r["o0"] != r["prod_o"] or r["ret0"] != r["prod_ret"]]
    _log(f"   🔒 `RV7`: {len(rows) - len(bad)} من {len(rows)} مطابقةٌ بت-بت "
         f"لمحرّك الإنتاج")
    if bad:
        b = bad[0]
        _log(f"   ⛔ `RV7` تفرّق — {b['symbol']}/{b['date']}: "
             f"{b['o0']}/{b['ret0']} مقابل {b['prod_o']}/{b['prod_ret']}")
        return 3

    # `RV5` — حضورُ المِرساة
    have = [r for r in rows if r.get("pivot") is not None]
    cov = len(have) / len(rows) * 100.0
    _log(f"   🔒 `RV5`: `pivot` حاضرٌ في {cov:.1f}%")
    if cov < 95.0:
        _log("   ⛔ `RV5` غائبٌ في أكثرَ من 5%")
        return 3

    # `RV3` — الوقفُ المشحون **يساوي أدنى دفعةٍ مساواةً تامّة**
    n_eq = sum(1 for r in rows if r.get("oC1") is not None)
    _log(f"   🔒 `RV3`: `C1` = `tranches[0]` بالبناء · صفوفٌ قابلةٌ للقياس "
         f"{n_eq} من {len(rows)}")
    skip1 = sum(1 for r in rows if r.get("skipC1"))
    skip2 = sum(1 for r in rows if r.get("skipC2"))
    _log(f"   📏 `RP6`: «الوقفُ فوق الدخول» — `C1` {skip1} "
         f"({skip1 / len(rows) * 100:.2f}%) · `C2` {skip2} "
         f"({skip2 / len(rows) * 100:.2f}%)")

    # `RV4` — دعوى «`tested ≤ pivot`» تُختبَر لا تُفترَض
    both = [r for r in rows if r.get("pivot") is not None]
    viol = [r for r in both if r["tr0"] > r["pivot"] + 1e-9]
    diff = [r for r in both if abs(r["tr0"] - r["pivot"]) > 1e-9]
    gaps = sorted(abs(r["pivot"] / r["tr0"] - 1.0) * 100.0
                  for r in diff if r["tr0"])
    _log(f"   🔒 `RV4`: `stop(C1) ≤ stop(C2)` في "
         f"{len(both) - len(viol)} من {len(both)} · مخالفات {len(viol)}")
    _log(f"   📏 `RP2`: `pivot` يخالف المِرساة في {len(diff)} من {len(both)} "
         f"({len(diff) / len(both) * 100 if both else 0:.1f}%) · وسيطُ الفجوة "
         f"{(gaps[len(gaps) // 2] if gaps else 0.0):.2f}% · أقصاها "
         f"{(gaps[-1] if gaps else 0.0):.2f}%")
    if viol:
        v = viol[0]
        _log(f"   ⛔ `RV4` مكذَّبة — {v['symbol']}/{v['date']}: "
             f"tr0={v['tr0']} pivot={v['pivot']} ⇒ استدلالُ `§①` خاطئ")
        return 3

    # ═══ المقامُ (1): بوّابتا الإعادة على صفوف الأداة السابقة حرفيًّا ═══
    use = [r for r in rows if r.get("oC2") is not None]
    g0 = agg([r for r in use if r["o0"] != "no_fill"], "o0", "ret0")
    g2 = agg([r for r in use if r["oC2"] != "no_fill"], "oC2", "retC2")
    p0, p1 = PUB_B0.get(str(year)), PUB_B1.get(str(year))
    _log(f"   🔒 `RV0`: `C0@use` {g0['r0']:+.4f} مقابل المنشور "
         f"{p0 if p0 is not None else '—'}")
    _log(f"   🔒 `RV1`: `C2@use` {g2['r0']:+.4f} مقابل المنشور "
         f"{p1 if p1 is not None else '—'}")
    if p0 is not None and abs(g0["r0"] - p0) > PUB_TOL:
        _log("   ⛔ `RV0` لا يُعيد `B0` ⇒ عطبُ أداةٍ لا نتيجة")
        return 3
    if p1 is not None and abs(g2["r0"] - p1) > PUB_TOL:
        _log("   ⛔ `RV1` لا يُعيد `B1` ⇒ عطبُ أداةٍ لا نتيجة")
        return 3

    # ═══ المقامُ (2): الحكمُ على الصفوف كلِّها ═══
    d0 = [r for r in rows if r["o0"] != "no_fill"]
    d1 = [r for r in rows if r.get("oC1") is not None
          and r["oC1"] != "no_fill"]
    if len(d0) < FLOOR_DECIDED or len(d1) < FLOOR_DECIDED:
        _log(f"   ⛔ الأرضية: المحسومة {len(d0)}/{len(d1)} دون "
             f"{FLOOR_DECIDED} ⇒ لا حكم")
        return 4
    a0 = agg(d0, "o0", "ret0")
    a1 = agg(d1, "oC1", "retC1")
    if all(r.get("oC1") == r["o0"] and r.get("retC1") == r["ret0"]
           for r in rows if r.get("oC1") is not None):
        _log("   ⛔ `RV2` `C1` لم يتفرّق عن `C0` ⇒ `no-op`")
        return 4
    if all(r.get("oC1") == r.get("oC2") and r.get("retC1") == r.get("retC2")
           for r in use):
        _log("   ⛔ `RV2` `C1` لم يتفرّق عن `C2` ⇒ العيبُ لم يكن ذا أثر")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ · المقامُ الصفوفُ كلُّها) ────")
    for nm, a in (("C0 (‏7% تحت المِرساة)", a0),
                  ("C1 (‏المشحونُ = أدنى دفعة) 🥇", a1)):
        _log(f"   │ {nm}: R₀ {a['r0']:+.4f} · محسومة {a['n']} · "
             f"ربح {a['win_pct']:.2f}% · عائدٌ محقَّق {a['ret_avg']:+.2f}%")
    _log(f"   │ [وصفيًّا @use] C0 {g0['r0']:+.4f} · C2 {g2['r0']:+.4f} · "
         f"فرقُ المنشور {g2['r0'] - g0['r0']:+.4f}")
    _log("   └────────────────────────────────────────────────────────")
    _log(f"   📐 **C1−C0 بـR₀ = {a1['r0'] - a0['r0']:+.4f}**  "
         f"(‏والمنشورُ كان {(p1 - p0) if (p0 is not None and p1 is not None) else 0:+.4f})")

    _log("SUMMARY " + json.dumps(
        {"year": year, "C0": a0, "C1": a1, "C0_use": g0, "C2_use": g2,
         "skip_c1": skip1, "skip_c2": skip2, "n_diff_pivot": len(diff),
         "n_both": len(both), "cov": round(cov, 2), "n_rows": len(rows)},
        ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": year,
         "p": [[r["symbol"],
                round(r0_of(r["ret0"], r["entry"], r["stop0"]) or 0.0, 6),
                round(r0_of(r["retC1"], r["entry"], r["stop0"]) or 0.0, 6)]
               for r in rows
               if r.get("oC1") is not None
               and (r["o0"] != "no_fill" or r["oC1"] != "no_fill")]},
        ensure_ascii=False))
    return 0


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ `RV6` الأداةُ ليست قراءةً فقط")
        return 3
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
    # 🛑🔒 وقفُ الارتكاز يُرجَع إلى ‏7% **قسرًا** (سابقةُ `CAP15`): `C0` هو
    #     الإنتاجُ **القديم** ويجب أن يُعيد `B0` بت-بت، و`C1` يُبنى هنا من
    #     `tranches[0]` صراحةً — فلا يختلط المشحونُ بالمرجع.
    S.CONFIG["PIVOT_STOP_AT_LOW"] = False
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · وقفُ المرجع "
         f"{S.CONFIG['STOP_BELOW_LOW_PCT']} · الأذرع C0/C1/C2")
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
