#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📐 `T-TRANCHE` — «سجّل تجربة الدفعات» (العقد `tranche_prereg.md` مدفوعٌ **قبل
هذا الملفّ**، وملحقُه §⑨ **قبل أيّ رقم**).

**السؤال (§①):** بالوقف المعتمَد (‏= المِرساة)، هل **رفعُ سلّم الدفعات فوقها**
أفضلُ من بدئه **عندها** — بوحدةِ مخاطرةٍ **واحدةٍ للأذرع الأربع**؟

**لماذا السؤال أصلًا:** جملةُ فيصل «‏1.50 قاع **دخوله طلبات من 1.60 ل 1.70** ·
**وقفه قاعه**» شُحن **نصفُها** ⇒ أدنى دفعةٍ صارت **تساوي** الوقفَ بالضبط.

**المحرّك — إعادةُ استعمالٍ بالاسم:** صفقاتُ `backtest_symbol` الإنتاجية، ثم
تُعاد خطّةُ كلّ صفقةٍ بنداء `analyze_ticker` **عند فهرسها نفسِه**، والحسمُ
بـ`_resolve_arm` **الإنتاجيّة** على شموع النافذة نفسِها.

🔒 **`Super_stock.py` لا يُمَسّ بحرف** — ولا علمَ جديد ولا عتبة. الإزاحةُ
تُطبَّق **داخل هذي الأداة** بصيغة الإنتاج نفسِها.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import json
import os
import sys

FLOOR_DECIDED = 100          # §④-4 — رقمٌ مُعادٌ من `T-EXIT` لا مخترَع
OUT_ROWS = "tranche_rows.jsonl"

# §③ — أربعُ أذرعٍ ولا خامسة (مثبَّتةٌ في العقد · إضافةُ ذراعٍ بعد الأرقام ممنوعة)
ARMS = (("P0", 0.0), ("P1", 2.0), ("P2", 5.0), ("P3", 7.0))
GOV = "P1"                   # §③ — الحاكمة: أصغرُ إزاحةٍ تحلّ المشكلة فعلًا


def _log(m):
    print(m, flush=True)


def ladder(anchor, off_pct, n_tr, step_pct):
    """سلّمُ الدفعات **بصيغة الإنتاج حرفيًّا** مع إزاحةِ بداية:
    `round(anchor * (1 + off + step*i), 2)` — التدويرُ بخانتين كالإنتاج،
    وبه يبقى `P0` مطابقًا لدفعات `analyze_ticker` بت-بت (‏`TV1`)."""
    off = float(off_pct) / 100.0
    step = float(step_pct) / 100.0
    return [round(float(anchor) * (1.0 + off + step * i), 2)
            for i in range(int(n_tr))]


def r_fixed(ret_pct, entry_k, entry_base, stop):
    """§④ — العائدُ بوحدةِ مخاطرةٍ **ثابتة** `R₀ = entry(P0) − stop`.
    `ret_pct` نسبةٌ من `entry_k` ⇒ تُحوَّل إلى دولاراتٍ للسهم ثم تُقسَم على
    `R₀`. **فالإزاحةُ الأوسع لا تُكافأ بصِغَر مقامها.**"""
    try:
        e_k, e_b, s = float(entry_k), float(entry_base), float(stop)
    except (TypeError, ValueError):
        return None
    if ret_pct is None or e_b - s <= 0:
        return None
    try:
        return (float(ret_pct) / 100.0 * e_k) / (e_b - s)
    except (TypeError, ValueError):
        return None


def r_own(ret_pct, entry_k, stop):
    """القراءةُ الثانية (تُنشَر ولا تحكم): `R` بوحدةِ **كلّ ذراعٍ هي**.
    🔴 موسومةٌ «غيرُ قابلةٍ للمقارنة» في العقد §④."""
    try:
        e, s = float(entry_k), float(stop)
    except (TypeError, ValueError):
        return None
    if ret_pct is None or e - s <= 0:
        return None
    try:
        return (float(ret_pct) / 100.0 * e) / (e - s)
    except (TypeError, ValueError):
        return None


def plan_at(S, sym, df, i):
    """خطّةُ الصفقة عند الفهرس `i` بنداء `analyze_ticker` **الإنتاجيّ** (لا من
    الحقول المدوَّرة). يرجّع dict أو None."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        return {"tranches": [float(x) for x in r["tranches"]],
                "stop": float(r["stop"][0]),
                "t1": float(r["t1"]),
                "pivot": (float(r["pivot"]) if r.get("pivot") is not None
                          else None),
                "rr_stop": (float(r["rr_stop"]) if r.get("rr_stop") is not None
                            else None)}
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct, s_hi):
    """يحسم الأذرعَ الأربع على **نفس الشموع ونفس الوقف** — المتغيّرُ بدايةُ
    السلّم وحدَها. يرجّع (صفّ، None) أو (None، سبب)."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    if pl["rr_stop"] is None:
        return None, "بلا `rr_stop`"
    # 🔑 استرجاعُ المِرساة غيرِ المدوَّرة: `rr_stop = _anchor × (1 − s_hi/100)`
    denom = 1.0 - float(s_hi) / 100.0
    if denom <= 0:
        return None, "أساسٌ تالف"
    anchor = pl["rr_stop"] / denom
    stop = pl["stop"]
    t1 = pl["t1"]
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)

    row = {"symbol": sym, "date": tr["date"], "stop": round(stop, 4),
           "t1": round(t1, 4), "anchor": round(anchor, 6),
           "prod_tr": [round(x, 4) for x in pl["tranches"]],
           "pivot": (round(pl["pivot"], 6) if pl["pivot"] is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a")}
    base_entry = None
    for name, off in ARMS:
        trs = ladder(anchor, off, n_tr, step_pct)
        entry = sum(trs) / len(trs)
        if name == "P0":
            base_entry = entry
            row["tr0"] = trs
        if entry - stop <= 0:                                    # `TV4`
            row[f"skip_{name}"] = True
            continue
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop, t1, filled,
                                     spread=spread)
        row[f"e_{name}"] = round(entry, 4)
        row[f"lo_{name}"] = trs[0]
        row[f"o_{name}"] = o
        row[f"ret_{name}"] = (round(rt, 1) if rt is not None else None)
    if base_entry is None:
        return None, "تعذّر الأساس"
    return row, None


def _selfcheck_readonly() -> bool:
    """`TV6` — قراءةٌ فقط: صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها
    هي). الملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
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


def report(rows, year, issues, gap_stats):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    _log(f"\n📐 T-TRANCHE · سنة {year} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4

    # `TV1` — سلّمُ `P0` يطابق دفعاتِ الإنتاج بت-بت
    mism = [r for r in rows if r.get("tr0") != r.get("prod_tr")]
    _log(f"   🔒 `TV1`: سلّمُ `P0` يطابق دفعاتِ الإنتاج في "
         f"{len(rows) - len(mism)} من {len(rows)}")
    if mism:
        m = mism[0]
        _log(f"   ⛔ `TV1` تفرّق — {m['symbol']}/{m['date']}: "
             f"{m.get('tr0')} مقابل {m.get('prod_tr')}")
        return 3

    # `TV3` — حضورُ المِرساة
    have = [r for r in rows if r.get("pivot") is not None]
    cov = len(have) / len(rows) * 100.0
    _log(f"   🔒 `TV3`: المِرساةُ (`pivot`) حاضرةٌ في {cov:.1f}%")
    if cov < 95.0:
        _log("   ⛔ `TV3` غائبةٌ في أكثرَ من 5% ⇒ العلمُ خامل")
        return 3

    # `TV4` — الوقفُ أدنى من أدنى دفعةٍ في كلّ ذراع (وفي `P0` **مساوٍ** بالبناء)
    eq0 = sum(1 for r in rows if abs(r["lo_P0"] - r["stop"]) < 1e-9)
    _log(f"   🔒 `TV4`: في `P0` الوقفُ **يساوي** أدنى دفعةٍ في {eq0} من "
         f"{len(rows)} ({eq0 / len(rows) * 100:.1f}%) — وهي المشكلةُ المشحونة")
    for name, _off in ARMS[1:]:
        bad = sum(1 for r in rows
                  if r.get(f"lo_{name}") is not None
                  and r[f"lo_{name}"] <= r["stop"])
        _log(f"   🔒 `TV4`: {name} الوقفُ ليس أدنى من أدنى دفعةٍ في {bad} صفقة")

    # §⑨-3 — تحجيمُ انحراف `T-PIVOT-BOTTOM`
    _log(f"   📏 §⑨-3 `pivot` يخالف المِرساة في {gap_stats['n_diff']} من "
         f"{gap_stats['n']} ({gap_stats['pct']:.1f}%) · وسيطُ الفجوة "
         f"{gap_stats['median_pct']:+.2f}% · أقصاها {gap_stats['max_pct']:+.2f}%")

    # `TV2` — التفرّق
    same = []
    for name, _off in ARMS[1:]:
        if all(r.get(f"o_{name}") == r.get("o_P0")
               and r.get(f"ret_{name}") == r.get("ret_P0") for r in rows):
            same.append(name)
    if same:
        _log(f"   ⛔ `TV2` لم تتفرّق عن `P0`: {' · '.join(same)} ⇒ `no-op`")
        return 4

    def agg(name):
        """§⑨-4: **`no_fill` = صفرُ عائدٍ ويدخل المقام** — فالمقامُ واحدٌ
        للأذرع الأربع وزيادةُ التعبئة تُحسَب لا تُخفى."""
        fx, ow, n_fill, wins = [], [], 0, 0
        for r in rows:
            o = r.get(f"o_{name}")
            if o is None:
                continue
            if o == "no_fill":
                fx.append(0.0)
                ow.append(0.0)
                continue
            n_fill += 1
            if o == "win":
                wins += 1
            v = r_fixed(r.get(f"ret_{name}"), r.get(f"e_{name}"),
                        r.get("e_P0"), r["stop"])
            w = r_own(r.get(f"ret_{name}"), r.get(f"e_{name}"), r["stop"])
            fx.append(v if v is not None else 0.0)
            ow.append(w if w is not None else 0.0)
        n = len(fx)
        rets = [r.get(f"ret_{name}") for r in rows
                if r.get(f"o_{name}") not in (None, "no_fill")
                and r.get(f"ret_{name}") is not None]
        return {"n": n, "n_fill": n_fill,
                "fill_pct": (n_fill / n * 100.0) if n else 0.0,
                "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
                "r_fixed": (sum(fx) / n) if n else 0.0,
                "r_own": (sum(ow) / n) if n else 0.0,
                "ret_avg": (sum(rets) / len(rets)) if rets else 0.0}

    a = {name: agg(name) for name, _ in ARMS}
    if a["P0"]["n_fill"] < FLOOR_DECIDED or a[GOV]["n_fill"] < FLOOR_DECIDED:
        _log(f"   ⛔ الأرضية: المُعبَّأة {a['P0']['n_fill']}/{a[GOV]['n_fill']} "
             f"دون {FLOOR_DECIDED} ⇒ لا حكم")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ الثابت · و`no_fill`=0R يدخل المقام) ─")
    for name, off in ARMS:
        x = a[name]
        mark = " 🥇" if name == GOV else ""
        _log(f"   │ {name} (‏إزاحة {off:+.1f}%){mark}: R₀ {x['r_fixed']:+.4f} · "
             f"تعبئة {x['fill_pct']:.1f}% ({x['n_fill']}) · ربح {x['win_pct']:.2f}% · "
             f"عائدٌ محقَّق {x['ret_avg']:+.2f}% · [R بوحدتها {x['r_own']:+.4f}]")
    _log("   └───────────────────────────────────────────────────────────")
    for name, _off in ARMS[1:]:
        _log(f"   📐 {name}−P0 بـR₀ = {a[name]['r_fixed'] - a['P0']['r_fixed']:+.4f}"
             f"   (بوحدةِ كلّ ذراع: {a[name]['r_own'] - a['P0']['r_own']:+.4f} "
             f"— **غيرُ قابلٍ للمقارنة**)")

    _log("SUMMARY " + json.dumps(
        {"year": year, "arms": a, "gap": gap_stats, "eq0": eq0,
         "n_rows": len(rows)}, ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": year, "gov": GOV,
         "p": [[r["symbol"],
                round(r_fixed(r.get("ret_P0"), r.get("e_P0"), r.get("e_P0"),
                              r["stop"]) or 0.0, 6)
                if r.get("o_P0") != "no_fill" else 0.0,
                round(r_fixed(r.get(f"ret_{GOV}"), r.get(f"e_{GOV}"),
                              r.get("e_P0"), r["stop"]) or 0.0, 6)
                if r.get(f"o_{GOV}") != "no_fill" else 0.0]
               for r in rows if r.get("o_P0") is not None
               and r.get(f"o_{GOV}") is not None]},
        ensure_ascii=False))
    return 0


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ `TV6` الأداةُ ليست قراءةً فقط")
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
    # §⑨-1: `P0` = **خطّةُ الإنتاج المشحونة كما هي** ⇒ العلمُ يبقى كما شحنه
    #        المالك (لا إجبارَ هنا)، فالمرجعُ واقعٌ لا إعادةُ بناء.
    if not S.CONFIG.get("PIVOT_STOP_AT_LOW"):
        _log("⛔ `P0` يشترط وقفَ القاع المشحون (`PIVOT_STOP_AT_LOW`) — مُطفأ")
        return 3
    n_tr = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step_pct = float(S.CONFIG["ENTRY_STEP_PCT"])
    s_hi = float(S.CONFIG["STOP_BELOW_LOW_PCT"][1])
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · دفعات {n_tr}×{step_pct}% "
         f"· أساسُ `rr` {s_hi}% · الأذرع " +
         " · ".join(f"{n}{o:+.0f}%" for n, o in ARMS))
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
                row, why = arms_for(S, sym, df, tr, fwd, spread, n_tr,
                                    step_pct, s_hi)
                if row is None:
                    issues[why] = issues.get(why, 0) + 1
                    continue
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    gaps = [abs(r["pivot"] / r["anchor"] - 1.0) * 100.0 for r in rows
            if r.get("pivot") and r.get("anchor")]
    diff = [g for g in gaps if g > 1e-9]
    srt = sorted(diff)
    gap_stats = {"n": len(gaps), "n_diff": len(diff),
                 "pct": (len(diff) / len(gaps) * 100.0) if gaps else 0.0,
                 "median_pct": (srt[len(srt) // 2] if srt else 0.0),
                 "max_pct": (max(srt) if srt else 0.0)}
    return report(rows, year, issues, gap_stats)


if __name__ == "__main__":
    sys.exit(main())
