#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏳ `T-WAIT-LOWER` — «انتظر اقل سعر 10% او 20% تحت» (العقد `wait_lower_prereg.md`
مدفوعٌ **قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال (§①):** على صفقات الفارز الإنتاجية نفسِها، هل حدٌّ أدنى **تحت سعر التحليل**
بـ10% (الحاكمة) أو 20% أو عند **سعر RSI 27** يُحسّن التوقّعَ بوحدة `R₀` الثابتة —
مع احتساب ما لم يُعبَّأ **صفرًا في المقام**؟

**المصدر:** فيصل حرفيًّا (دليلُ طريقة فيصل ص54 · 13/06/2026): «اذا حللنا سهم ارتكاز
ممنوع الدخول · تابع السهم اقل سعر … انتظر اقل سعر 10% او 20% تحت» · و(GWAV ص91):
«سحب السيوله المتوقع … يمثل هدف الشورت = RSI 27».

**المحرّك — إعادةُ استعمالٍ بالاسم:** صفقاتُ `backtest_symbol` الإنتاجية · إعادةُ الخطّة
بـ`tranche_arms.plan_at` (تنادي `analyze_ticker` عند الفهرس نفسِه) · الحسمُ بـ`_resolve_arm`
الإنتاجيّة · سعرُ RSI 27 بـ`rsi_target_price` الإنتاجيّة · و`R₀` بـ`tranche_arms.r_fixed`.

🔒 `Super_stock.py` لا يُمَسّ بحرف · قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import json
import os
import sys

from tranche_arms import FLOOR_DECIDED, plan_at, r_fixed, r_own   # بالاسم — لا نسخ

OUT_ROWS = "wait_lower_rows.jsonl"

# §③ — أربعُ أذرعٍ ولا خامسة (مثبَّتةٌ في العقد · إضافةُ ذراعٍ بعد الأرقام ممنوعة)
ARMS = ("W0", "W10", "W20", "W27")
WAIT_PCT = {"W10": 10.0, "W20": 20.0}   # نصُّ فيصل: «10% او 20% تحت»
RSI_TARGET = 27.0                       # نصُّ فيصل (GWAV): «هدف الشورت = RSI 27»
GOV = "W10"                             # §③ — الحاكمة: أصغرُ انتظارٍ في نصّه
V_W0_MIN_PCT = 99.0                     # §④ `V-W0`
WL1_MIN_R = 0.05                        # §④ `WL1` (المجمَّع — يُحكَم في `wait_lower_result.md`)
WL2_MIN_FILL_RATIO = 0.30               # §④ `WL2`


def _log(m):
    print(m, flush=True)


def wl_entries(ref, entry0, rsi27):
    """§③ — أسعارُ الدخول للأذرع الأربع. **القيدُ الواحد:** لا ذراعَ تدخل **فوق**
    خطّة الإنتاج (`min(·, entry0)`) — فالنصُّ «ممنوع الدخول … انتظر اقل سعر» منعٌ
    لا إذنُ ملاحقة. `W27`: إن كان RSI عند 27 أو تحته أصلًا (`rsi27=None`) فالسحبُ
    وقع ⇒ خطّةُ الإنتاج كما هي."""
    e0 = float(entry0)
    out = {"W0": e0}
    for name, pct in WAIT_PCT.items():
        out[name] = min(float(ref) * (1.0 - pct / 100.0), e0)
    out["W27"] = (min(float(rsi27), e0) if rsi27 is not None else e0)
    return out


def stop_for(entry_w, entry0, stop0):
    """§③ — وقفُ الذراع **بنفس نسبة** الإنتاج: `entry_w × (stop0 / entry0)`."""
    try:
        e0 = float(entry0)
        if e0 <= 0:
            return None
        return float(entry_w) * (float(stop0) / e0)
    except (TypeError, ValueError):
        return None


def arms_for(S, sym, df, tr, fwd, spread):
    """يحسم الأذرعَ الأربع على **نفس الشموع ونفس الهدف** — المتغيّرُ سعرُ الدخول
    (ومعه وقفٌ بنفس النسبة). يرجّع (صفّ، None) أو (None، سبب)."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    entry0 = sum(pl["tranches"]) / len(pl["tranches"])          # متوسّطُ الدفعات كالإنتاج حرفيًّا
    stop0, t1 = pl["stop"], pl["t1"]
    if entry0 - stop0 <= 0:
        return None, "وقفٌ فوق الدخول"
    try:
        ref = float(df["Close"].iloc[i - 1])                    # إغلاقُ شمعة الإشارة = سعرُ التحليل
    except Exception:                                            # noqa: BLE001
        return None, "بلا سعرِ تحليل"
    if not ref > 0:
        return None, "بلا سعرِ تحليل"
    try:
        rsi27 = S.rsi_target_price(df["Close"].iloc[:i], RSI_TARGET)
    except Exception:                                            # noqa: BLE001
        rsi27 = None
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)
    ents = wl_entries(ref, entry0, rsi27)

    row = {"symbol": sym, "date": tr["date"], "ref": round(ref, 4),
           "stop0": round(stop0, 4), "t1": round(t1, 4),
           "rsi27": (round(rsi27, 4) if rsi27 is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a")}
    for name in ARMS:
        entry = ents[name]
        # `W0` وقفُها `stop0` **حرفيًّا** (لا `entry0×(stop0/entry0)` — تطابقٌ بت-بت مع الإنتاج ·
        #  ملحق §④ 2026-09-09) · والأذرعُ الأخرى بنفس النسبة.
        stop = stop0 if name == "W0" else stop_for(entry, entry0, stop0)
        if stop is None or entry - stop <= 0:
            return None, "وقفٌ غيرُ صالح"
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop, t1, filled,
                                     spread=spread)
        row[f"e_{name}"] = round(entry, 4)
        row[f"s_{name}"] = round(stop, 4)
        row[f"o_{name}"] = o
        row[f"ret_{name}"] = (round(rt, 1) if rt is not None else None)
        row[f"bite_{name}"] = bool(entry < entry0 - 1e-12)
        row[f"k_{name}"] = filled
    # §③-ب — قراءةٌ ثانية للحاكمة بالوقف **المطلق** `stop0` (وصفيّةٌ لا تحكم)
    e_g = ents[GOV]
    if e_g - stop0 > 0:
        filled = next((k for k in range(len(fut)) if lo[k] <= e_g), None)
        o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, e_g, stop0, t1, filled,
                                     spread=spread)
        row["o_GOVabs"] = o
        row["ret_GOVabs"] = (round(rt, 1) if rt is not None else None)
    else:
        row["o_GOVabs"], row["ret_GOVabs"] = "skip", None
    return row, None


def _selfcheck_readonly() -> bool:
    """قراءةٌ فقط (كـ`TV6`): صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها هي).
    الملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
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


def agg(rows, name):
    """§④: **`no_fill` = صفرُ عائدٍ ويدخل المقام** — فالمقامُ واحدٌ للأذرع الأربع
    وقلّةُ التعبئة تُحسَب لا تُخفى. `R₀` بوحدة `entry0 − stop0` الثابتة."""
    fx, ow, n_fill, wins, bite = [], [], 0, 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if r.get(f"bite_{name}"):
            bite += 1
        if o == "no_fill":
            fx.append(0.0)
            ow.append(0.0)
            continue
        n_fill += 1
        if o == "win":
            wins += 1
        v = r_fixed(r.get(f"ret_{name}"), r.get(f"e_{name}"), r.get("e_W0"),
                    r["stop0"])
        w = r_own(r.get(f"ret_{name}"), r.get(f"e_{name}"), r.get(f"s_{name}"))
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
            "ret_avg": (sum(rets) / len(rets)) if rets else 0.0,
            "bite_pct": (bite / n * 100.0) if n else 0.0}


def agg_abs(rows):
    """§③-ب — القراءةُ الثانية للحاكمة بالوقف المطلق (`skip` يُعدّ ولا يُخفى)."""
    fx, n_fill, wins, skip = [], 0, 0, 0
    for r in rows:
        o = r.get("o_GOVabs")
        if o is None:
            continue
        if o == "skip":
            skip += 1
            fx.append(0.0)
            continue
        if o == "no_fill":
            fx.append(0.0)
            continue
        n_fill += 1
        if o == "win":
            wins += 1
        v = r_fixed(r.get("ret_GOVabs"), r.get(f"e_{GOV}"), r.get("e_W0"), r["stop0"])
        fx.append(v if v is not None else 0.0)
    n = len(fx)
    return {"n": n, "n_fill": n_fill, "skip": skip,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "r_fixed": (sum(fx) / n) if n else 0.0}


def report(rows, year, issues):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    _log(f"\n⏳ T-WAIT-LOWER · سنة {year} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4

    # `V-W0` — حسمُ `W0` يطابق حسمَ الإنتاج (وإلّا فالأساسُ مفبرَك)
    same0 = sum(1 for r in rows if r.get("o_W0") == r.get("prod_o"))
    pct0 = same0 / len(rows) * 100.0
    _log(f"   🔒 `V-W0`: حسمُ `W0` = حسمُ الإنتاج في {same0} من {len(rows)} ({pct0:.2f}%)")
    if pct0 < V_W0_MIN_PCT:
        m = next(r for r in rows if r.get("o_W0") != r.get("prod_o"))
        _log(f"   ⛔ `V-W0` تفرّق — {m['symbol']}/{m['date']}: {m.get('o_W0')} "
             f"مقابل {m.get('prod_o')}")
        return 3

    a = {name: agg(rows, name) for name in ARMS}

    # `V-W1` — تعبئةُ الحاكمة لا تتجاوز تعبئةَ `W0` بالبناء
    _log(f"   🔒 `V-W1`: تعبئةُ `{GOV}` {a[GOV]['n_fill']} ≤ تعبئةُ `W0` {a['W0']['n_fill']}")
    if a[GOV]["n_fill"] > a["W0"]["n_fill"]:
        _log("   ⛔ `V-W1` مخالفة — القيدُ `min(·, entry0)` لا يعمل")
        return 3

    # `V-W2` — تفرّقُ **الحاكمة** عن `W0` (ملحق §④ 2026-09-09): الوصفيُّ المتطابق
    #  يُطبَع ولا يُسقط القياس — وإلّا حجب ذراعٌ وصفيٌّ متدهور الحاكمةَ.
    same = [name for name in ARMS[1:]
            if all(r.get(f"o_{name}") == r.get("o_W0")
                   and r.get(f"ret_{name}") == r.get("ret_W0") for r in rows)]
    if same:
        _log(f"   ℹ️ أذرعٌ لم تتفرّق عن `W0`: {' · '.join(same)}")
    if GOV in same:
        _log(f"   ⛔ `V-W2` الحاكمةُ `{GOV}` لم تتفرّق عن `W0` ⇒ `no-op`")
        return 4

    if a["W0"]["n_fill"] < FLOOR_DECIDED or a[GOV]["n_fill"] < FLOOR_DECIDED:
        _log(f"   ⛔ الأرضية: المُعبَّأة {a['W0']['n_fill']}/{a[GOV]['n_fill']} "
             f"دون {FLOOR_DECIDED} ⇒ لا حكم")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ الثابت · و`no_fill`=0R يدخل المقام) ─")
    for name in ARMS:
        x = a[name]
        mark = " 🥇" if name == GOV else ""
        _log(f"   │ {name}{mark}: R₀ {x['r_fixed']:+.4f} · تعبئة {x['fill_pct']:.1f}% "
             f"({x['n_fill']}) · ربح {x['win_pct']:.2f}% · عائدٌ محقَّق {x['ret_avg']:+.2f}% "
             f"· يبنّد {x['bite_pct']:.1f}% · [R بوحدتها {x['r_own']:+.4f}]")
    _log("   └───────────────────────────────────────────────────────────")
    for name in ARMS[1:]:
        _log(f"   📐 {name}−W0 بـR₀ = {a[name]['r_fixed'] - a['W0']['r_fixed']:+.4f}"
             f"   (بوحدةِ كلّ ذراع: {a[name]['r_own'] - a['W0']['r_own']:+.4f} "
             f"— **غيرُ قابلٍ للمقارنة**)")
    ab = agg_abs(rows)
    _log(f"   📎 §③-ب `{GOV}` بالوقف المطلق `stop0` (وصفيّة): R₀ {ab['r_fixed']:+.4f} · "
         f"تعبئة {ab['n_fill']} · ربح {ab['win_pct']:.2f}% · skip {ab['skip']}")

    # §④ — شقُّ السنة من `WL1` و`WL2` (المجمَّعُ يُحكَم في الملفّ بعد الثلاث)
    d_gov = a[GOV]["r_fixed"] - a["W0"]["r_fixed"]
    fill_ratio = (a[GOV]["n_fill"] / a["W0"]["n_fill"]) if a["W0"]["n_fill"] else 0.0
    _log(f"   ⚖️ `WL1` (شقُّ السنة): {GOV}−W0 = {d_gov:+.4f}R ⇒ "
         f"{'✅ موجب' if d_gov > 0 else '🔴 غيرُ موجب'}")
    _log(f"   ⚖️ `WL2`: تعبئةُ {GOV}/W0 = {fill_ratio:.3f} ⇒ "
         f"{'✅' if fill_ratio >= WL2_MIN_FILL_RATIO else '🔴'} (الحدّ {WL2_MIN_FILL_RATIO})")
    # §⑤ — التنبّؤاتُ القابلةُ للقراءة بسنةٍ واحدة (تُنشَر كما وقعت)
    _log(f"   🔮 `WL-P1` تعبئةُ W10/W0 في [0.35, 0.60]: "
         f"{'✅' if 0.35 <= fill_ratio <= 0.60 else '🔴'} ({fill_ratio:.3f})")
    _log(f"   🔮 `WL-P3` تعبئةُ W27 < W10: "
         f"{'✅' if a['W27']['n_fill'] < a['W10']['n_fill'] else '🔴'} "
         f"({a['W27']['n_fill']} مقابل {a['W10']['n_fill']})")
    _log(f"   🔮 `WL-P4` ربحُ W20 بين المُعبَّأ > W0 والتوقّعُ الكامل أدنى: "
         f"{'✅' if (a['W20']['win_pct'] > a['W0']['win_pct'] and a['W20']['r_fixed'] < a['W0']['r_fixed']) else '🔴'} "
         f"(ربح {a['W20']['win_pct']:.1f}/{a['W0']['win_pct']:.1f} · R₀ {a['W20']['r_fixed']:+.4f}/{a['W0']['r_fixed']:+.4f})")
    _log(f"   🔮 `WL-P5` القيدُ يبنّد في أكثرَ من النصف لـW10: "
         f"{'✅' if a['W10']['bite_pct'] > 50.0 else '🔴'} ({a['W10']['bite_pct']:.1f}%)")

    _log("SUMMARY " + json.dumps(
        {"year": year, "arms": a, "gov_abs": ab, "n_rows": len(rows),
         "wl1_year_ok": bool(d_gov > 0), "d_gov": d_gov, "fill_ratio": fill_ratio},
        ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": year, "gov": GOV,
         "p": [[r["symbol"],
                round(r_fixed(r.get("ret_W0"), r.get("e_W0"), r.get("e_W0"),
                              r["stop0"]) or 0.0, 6)
                if r.get("o_W0") != "no_fill" else 0.0,
                round(r_fixed(r.get(f"ret_{GOV}"), r.get(f"e_{GOV}"),
                              r.get("e_W0"), r["stop0"]) or 0.0, 6)
                if r.get(f"o_{GOV}") != "no_fill" else 0.0]
               for r in rows if r.get("o_W0") is not None
               and r.get(f"o_{GOV}") is not None]},
        ensure_ascii=False))
    return 0


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ الأداةُ ليست قراءةً فقط")
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
    # §② — نفسُ أعلام `T-TRANCHE` ⇒ المجتمعُ نفسُه (ميزانيةٌ واحدة للتجارب)
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    # 🔒 `V-W3` بوّابةُ اللقطة (‏`SNAP1`): سنةُ اللقطة **تطابق** سنةَ القياس — وإلّا
    #    قِيست سنةٌ على مجتمعِ سنةٍ أخرى (مقيسٌ حيًّا: 153 صفقة مقابل 1606).
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return 4
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · نافذة {fwd}ج · سبريد {spread} · "
         f"وقفُ القاع {'مشحون' if S.CONFIG.get('PIVOT_STOP_AT_LOW') else 'مُطفأ'} · "
         f"الأذرع " + " · ".join(ARMS) + f" · الحاكمة {GOV}")
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
