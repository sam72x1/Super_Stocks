#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏳ `T-WAIT-RSI27` — «سحب السيولة المتوقّع = RSI 27» سياسةَ دخول (العقد
`wait_rsi27_prereg.md` مدفوعٌ `c3437f3` **قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال (§①):** على صفقات الفارز الإنتاجية نفسِها، هل أمرُ حدٍّ أدنى عند **سعر RSI 27**
(سحبُ السيولة المتوقّع عند فيصل) — بالهدف `t1` نفسِه ووقفٍ بنفس النسبة — يُحسّن التوقّعَ
بوحدة `R₀` الثابتة مع احتساب ما لم يُعبَّأ صفرًا، **وبفاصلِ ثقةٍ لا يلامس الصفر**، **وبإشارةٍ
تصمد خارج العيّنة (2026)**؟

**بيانات فيصل حرفيًّا:** GWAV ص91 «سحب السيوله المتوقع من 2.70 **يمثل هدف الشورت = RSI 27**»
(شارتٌ **أسبوعيّ**) · `TG_2043` «RSI بين **23**-27» · وقفُه البنيويّ تحت الدعم.

🔴 **حدُّ صدقٍ مُعلَن:** `R27` داخلَ العيّنة على 2023-2025 (= `W27` من `T-WAIT-LOWER`) ⇒ تكرارُها
**بوّابةُ صلاحية `V-R4`** لا دليل — والجديدُ: الفاصل · التفكيك · الأسبوعيّ · 23 · و2026 خارج العيّنة.

**المحرّك — إعادةُ استعمالٍ بالاسم:** صفقاتُ `backtest_symbol` الإنتاجية · `tranche_arms.plan_at`
· `_resolve_arm` · `rsi_target_price` · `tranche_arms.r_fixed`.
🔒 `Super_stock.py` لا يُمَسّ بحرف · قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import json
import os
import sys

import numpy as np

from tranche_arms import FLOOR_DECIDED, plan_at, r_fixed, r_own   # بالاسم — لا نسخ

OUT_ROWS = "wait_rsi27_rows.jsonl"

# §③ — خمسُ أذرعٍ ولا سادسة (مثبَّتةٌ في العقد · إضافةُ ذراعٍ بعد الأرقام ممنوعة)
ARMS = ("R0", "R27", "R23", "R27w", "R27abs")
RSI_TARGET = 27.0                       # فيصل (GWAV): «هدف الشورت = RSI 27»
RSI_LOW = 23.0                          # فيصل (TG_2043): «RSI بين 23-27» — حدُّه الأدنى
GOV = "R27"                             # §③ — الحاكمة: سعرُ RSI 27 اليوميّ
CONTRACT_YEARS = ("2023", "2024", "2025")   # §② — سنواتُ الحكم؛ غيرُها وصفيٌّ خارج العقد
V_R0_MIN_PCT = 99.0                     # §④ `V-R0`
WR1_MIN_R = 0.05                        # §④ `WR1` (المجمَّع — يُحكَم في `wait_rsi27_result.md`)
WR2_MIN_FILL_RATIO = 0.30               # §④ `WR2`
WR3_MIN_FILL = 50                       # §④ `WR3` — تعبئةُ الحاكمة خارج العيّنة
BOOT_N = 2000                           # §④ `WR1` — عيّناتُ البوتستراب
BOOT_SEED = 27                          # §④ `WR1` — البذرة (حتميّ)
# §④ `V-R4` — أرقامُ `T-WAIT-LOWER` المنشورة (`wait_lower_result.md`): تُعاد بت-بت وإلّا عطبُ أداة
REF = {"2023": {"r0": -0.2602, "r27": -0.1887, "n": 1620, "fill27": 779},
       "2024": {"r0": -0.1807, "r27": -0.0748, "n": 1591, "fill27": 680},
       "2025": {"r0": -0.2172, "r27": -0.1312, "n": 1606, "fill27": 678}}


def _log(m):
    print(m, flush=True)


def weekly_closes(close, signal_ts):
    """§③ `R27w` — إغلاقاتُ الأسابيع (نهايةُ الجمعة) حتى شمعة الإشارة **كما يراها شارتُ فيصل
    الأسبوعيّ**: إن لم تكن شمعةُ الإشارة جمعةً فالأسبوعُ الجاري ناقصٌ **فتُسقَط شمعتُه** ليكون
    إغلاقُه هو المجهولَ الذي يحلّه `rsi_target_price`؛ وإلّا فالأسبوعُ التالي. نقيّة."""
    import pandas as pd                                          # noqa: PLC0415
    c = pd.Series(close).astype(float).dropna()
    if not isinstance(c.index, pd.DatetimeIndex) or not len(c):
        return c.iloc[0:0]
    wk = c.resample("W-FRI").last().dropna()
    try:
        partial = pd.Timestamp(signal_ts).weekday() != 4
    except (TypeError, ValueError):
        partial = True
    if partial and len(wk):
        wk = wk.iloc[:-1]
    return wk


def wr_entries(entry0, rsi27, rsi23, rsi27w):
    """§③ — أسعارُ الدخول للأذرع الخمس. **القيدُ الواحد:** لا ذراعَ تدخل **فوق** خطّة الإنتاج
    (`min(·, entry0)`) — «ممنوع الدخول … انتظر» منعٌ لا إذنُ ملاحقة. `None` (RSI عند الهدف أو
    تحته أصلًا) ⇒ السحبُ وقع ⇒ خطّةُ الإنتاج كما هي. `R27abs` دخولُ `R27` نفسُه (يفترق بالوقف)."""
    e0 = float(entry0)
    cap = lambda v: (min(float(v), e0) if v is not None else e0)  # noqa: E731
    out = {"R0": e0, "R27": cap(rsi27), "R23": cap(rsi23), "R27w": cap(rsi27w)}
    out["R27abs"] = out["R27"]
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
    """يحسم الأذرعَ الخمس على **نفس الشموع ونفس الهدف** — المتغيّرُ سعرُ الدخول (ومعه وقفٌ
    بنفس النسبة، إلّا `R27abs` بوقف فيصل المطلق). يرجّع (صفّ، None) أو (None، سبب)."""
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
    closes = df["Close"].iloc[:i]
    try:
        ref = float(closes.iloc[-1])                             # إغلاقُ شمعة الإشارة = سعرُ التحليل
    except Exception:                                            # noqa: BLE001
        return None, "بلا سعرِ تحليل"
    if not ref > 0:
        return None, "بلا سعرِ تحليل"
    try:
        rsi27 = S.rsi_target_price(closes, RSI_TARGET)
    except Exception:                                            # noqa: BLE001
        rsi27 = None
    try:
        rsi23 = S.rsi_target_price(closes, RSI_LOW)
    except Exception:                                            # noqa: BLE001
        rsi23 = None
    try:
        wk = weekly_closes(closes, df.index[i - 1])
        rsi27w = S.rsi_target_price(wk, RSI_TARGET) if len(wk) else None
    except Exception:                                            # noqa: BLE001
        rsi27w = None
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)
    ents = wr_entries(entry0, rsi27, rsi23, rsi27w)

    row = {"symbol": sym, "date": tr["date"], "ref": round(ref, 4),
           "stop0": round(stop0, 4), "t1": round(t1, 4),
           "rsi27": (round(rsi27, 4) if rsi27 is not None else None),
           "rsi23": (round(rsi23, 4) if rsi23 is not None else None),
           "rsi27w": (round(rsi27w, 4) if rsi27w is not None else None),
           "prod_o": tr.get("outcome"), "prod_ret": tr.get("ret_a")}
    for name in ARMS:
        entry = ents[name]
        if name == "R0":
            stop = stop0                        # حرفيًّا — تطابقٌ بت-بت مع الإنتاج (`V-R0`)
        elif name == "R27abs":
            stop = stop0                        # وقفُ فيصل البنيويّ لا يتحرّك مع الدخول
            if entry - stop <= 0:               # الدخولُ تحت الوقف ⇒ لا صفقة — يُعدّ ولا يُخفى
                row[f"e_{name}"] = round(entry, 4)
                row[f"s_{name}"] = round(stop, 4)
                row[f"o_{name}"], row[f"ret_{name}"] = "skip", None
                row[f"bite_{name}"] = bool(entry < entry0 - 1e-12)
                row[f"k_{name}"] = None
                continue
        else:
            stop = stop_for(entry, entry0, stop0)
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


def r0_of(r, name):
    """`R₀` لصفٍّ وذراع (بوحدة `entry0 − stop0` الثابتة) · `no_fill`/`skip` = 0."""
    o = r.get(f"o_{name}")
    if o in (None, "no_fill", "skip"):
        return 0.0
    v = r_fixed(r.get(f"ret_{name}"), r.get(f"e_{name}"), r.get("e_R0"), r["stop0"])
    return v if v is not None else 0.0


def agg(rows, name):
    """§④: **`no_fill`/`skip` = صفرُ عائدٍ ويدخل المقام** — فالمقامُ واحدٌ للأذرع الخمس
    وقلّةُ التعبئة تُحسَب لا تُخفى. `R₀` بوحدة `entry0 − stop0` الثابتة."""
    fx, ow, n_fill, wins, bite, skip = [], [], 0, 0, 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if r.get(f"bite_{name}"):
            bite += 1
        if o == "skip":
            skip += 1
            fx.append(0.0)
            ow.append(0.0)
            continue
        if o == "no_fill":
            fx.append(0.0)
            ow.append(0.0)
            continue
        n_fill += 1
        if o == "win":
            wins += 1
        fx.append(r0_of(r, name))
        w = r_own(r.get(f"ret_{name}"), r.get(f"e_{name}"), r.get(f"s_{name}"))
        ow.append(w if w is not None else 0.0)
    n = len(fx)
    rets = [r.get(f"ret_{name}") for r in rows
            if r.get(f"o_{name}") not in (None, "no_fill", "skip")
            and r.get(f"ret_{name}") is not None]
    return {"n": n, "n_fill": n_fill, "skip": skip,
            "fill_pct": (n_fill / n * 100.0) if n else 0.0,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "r_fixed": (sum(fx) / n) if n else 0.0,
            "r_own": (sum(ow) / n) if n else 0.0,
            "ret_avg": (sum(rets) / len(rets)) if rets else 0.0,
            "bite_pct": (bite / n * 100.0) if n else 0.0}


def decomp(rows, gov=GOV):
    """§④-ب تفكيكُ الحافة: `B0` لا تبنيد · `B1` كلتاهما مُعبَّأة (+ مصفوفةُ الانتقال) ·
    `B2` الحاكمةُ لم تُعبَّأ و`R0` مُعبَّأة (= ما تجنّبته) · `B3` `R0` لم تُعبَّأ.
    ومجموعُ السلال = الفرقُ الكلّيّ (هويّةٌ تُفحَص في `identity_ok`). نقيّة."""
    b = {k: {"n": 0, "sum": 0.0} for k in ("B0", "B1", "B2", "B3")}
    trans = {}
    total = 0.0
    for r in rows:
        o0, og = r.get("o_R0"), r.get(f"o_{gov}")
        if o0 is None or og is None:
            continue
        d = r0_of(r, gov) - r0_of(r, "R0")
        total += d
        if not r.get(f"bite_{gov}"):
            k = "B0"
        elif o0 == "no_fill":
            k = "B3"
        elif og in ("no_fill", "skip"):
            k = "B2"
        else:
            k = "B1"
            key = f"{o0}->{og}"
            trans[key] = trans.get(key, 0) + 1
        b[k]["n"] += 1
        b[k]["sum"] += d
    n = sum(v["n"] for v in b.values())
    for v in b.values():
        v["mean_per_row"] = (v["sum"] / n) if n else 0.0            # إسهامُ السلّة في المتوسّط الكلّيّ
        v["share_pct"] = (v["sum"] / total * 100.0) if abs(total) > 1e-12 else 0.0
    ident = abs(sum(v["sum"] for v in b.values()) - total) < 1e-9
    return {"n": n, "total_mean": (total / n) if n else 0.0, "buckets": b,
            "transitions": trans, "identity_ok": ident}


def bootstrap_ci(diffs, n_boot=BOOT_N, seed=BOOT_SEED):
    """§④ `WR1` — فاصلُ بوتستراب مزدوج 95% لمتوسّط الفروق (إعادةُ معايَنةِ الصفوف بأزواجها ·
    حتميّ بالبذرة). يرجّع (الحدّ الأدنى، المتوسّط، الحدّ الأعلى) أو None لعيّنةٍ فارغة."""
    d = np.asarray([float(x) for x in diffs], dtype=float)
    m = len(d)
    if m == 0:
        return None
    rng = np.random.default_rng(int(seed))
    means = np.empty(int(n_boot), dtype=float)
    for j in range(int(n_boot)):
        means[j] = d[rng.integers(0, m, m)].mean()
    return (float(np.percentile(means, 2.5)), float(d.mean()),
            float(np.percentile(means, 97.5)))


def report(rows, year, issues, ref="auto"):
    """يطبع البوّابات والجدول والتفكيك والفاصل. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    descriptive = str(year) not in CONTRACT_YEARS
    if ref == "auto":
        ref = REF.get(str(year))
    tag = " (وصفيّةٌ خارج العقد — تُطبَع ولا تحكم)" if descriptive else ""
    _log(f"\n⏳ T-WAIT-RSI27 · سنة {year}{tag} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4
    dates = sorted(r["date"] for r in rows if r.get("date"))
    _log(f"   📅 مدى الصفقات: {dates[0]} ⟶ {dates[-1]}")

    # `V-R0` — حسمُ `R0` يطابق حسمَ الإنتاج (وإلّا فالأساسُ مفبرَك)
    same0 = sum(1 for r in rows if r.get("o_R0") == r.get("prod_o"))
    pct0 = same0 / len(rows) * 100.0
    _log(f"   🔒 `V-R0`: حسمُ `R0` = حسمُ الإنتاج في {same0} من {len(rows)} ({pct0:.2f}%)")
    if pct0 < V_R0_MIN_PCT:
        m = next(r for r in rows if r.get("o_R0") != r.get("prod_o"))
        _log(f"   ⛔ `V-R0` تفرّق — {m['symbol']}/{m['date']}: {m.get('o_R0')} "
             f"مقابل {m.get('prod_o')}")
        return 3

    a = {name: agg(rows, name) for name in ARMS}

    # `V-R1` — تعبئةُ الحاكمة لا تتجاوز تعبئةَ `R0` بالبناء
    _log(f"   🔒 `V-R1`: تعبئةُ `{GOV}` {a[GOV]['n_fill']} ≤ تعبئةُ `R0` {a['R0']['n_fill']}")
    if a[GOV]["n_fill"] > a["R0"]["n_fill"]:
        _log("   ⛔ `V-R1` مخالفة — القيدُ `min(·, entry0)` لا يعمل")
        return 3

    # `V-R2` — تفرّقُ **الحاكمة** عن `R0`: الوصفيُّ المتطابق يُطبَع ولا يُسقط
    same = [name for name in ARMS[1:]
            if all(r.get(f"o_{name}") == r.get("o_R0")
                   and r.get(f"ret_{name}") == r.get("ret_R0") for r in rows)]
    if same:
        _log(f"   ℹ️ أذرعٌ لم تتفرّق عن `R0`: {' · '.join(same)}")
    if GOV in same:
        _log(f"   ⛔ `V-R2` الحاكمةُ `{GOV}` لم تتفرّق عن `R0` ⇒ `no-op`")
        return 4

    # `V-R4` — سنواتُ الحكم تُعيد أرقامَ `T-WAIT-LOWER` المنشورة بت-بت (إثباتُ سلامة الأداة)
    if ref:
        got = (round(a["R0"]["r_fixed"], 4), round(a[GOV]["r_fixed"], 4),
               len(rows), a[GOV]["n_fill"])
        exp = (ref["r0"], ref["r27"], ref["n"], ref["fill27"])
        ok4 = all(abs(float(g) - float(e)) < 5e-5 for g, e in zip(got, exp))
        _log(f"   🔒 `V-R4`: R0/{GOV}/الصفوف/تعبئة{GOV} = {got} مقابل المنشور {exp} ⇒ "
             f"{'✅ بت-بت' if ok4 else '⛔ تفرّق'}")
        if not ok4:
            _log("   ⛔ `V-R4` الأداةُ لا تُعيد المنشور ⇒ عطبُ أداةٍ أو انزياحُ إنتاج — لا يُقرأ رقم")
            return 3

    if not descriptive and (a["R0"]["n_fill"] < FLOOR_DECIDED
                            or a[GOV]["n_fill"] < FLOOR_DECIDED):
        _log(f"   ⛔ الأرضية: المُعبَّأة {a['R0']['n_fill']}/{a[GOV]['n_fill']} "
             f"دون {FLOOR_DECIDED} ⇒ لا حكم")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ الثابت · و`no_fill`/`skip`=0R يدخل المقام) ─")
    for name in ARMS:
        x = a[name]
        mark = " 🥇" if name == GOV else ""
        extra = f" · skip {x['skip']}" if name == "R27abs" else ""
        _log(f"   │ {name}{mark}: R₀ {x['r_fixed']:+.4f} · تعبئة {x['fill_pct']:.1f}% "
             f"({x['n_fill']}) · ربح {x['win_pct']:.2f}% · عائدٌ محقَّق {x['ret_avg']:+.2f}% "
             f"· يبنّد {x['bite_pct']:.1f}%{extra} · [R بوحدتها {x['r_own']:+.4f}]")
    _log("   └───────────────────────────────────────────────────────────")
    for name in ARMS[1:]:
        _log(f"   📐 {name}−R0 بـR₀ = {a[name]['r_fixed'] - a['R0']['r_fixed']:+.4f}"
             f"   (بوحدةِ كلّ ذراع: {a[name]['r_own'] - a['R0']['r_own']:+.4f} "
             f"— **غيرُ قابلٍ للمقارنة**)")

    # §④-ب — تفكيكُ الحافة على الصفوف
    dc = decomp(rows, GOV)
    _log(f"   🔬 تفكيكُ {GOV}−R0 (الكلّيّ {dc['total_mean']:+.4f}R · الهويّة "
         f"{'✅' if dc['identity_ok'] else '⛔'}):")
    for k, lab in (("B0", "لا تبنيد"), ("B1", "كلتاهما مُعبَّأة"),
                   ("B2", "الحاكمةُ لم تُعبَّأ (ما تجنّبته)"), ("B3", "R0 لم تُعبَّأ")):
        v = dc["buckets"][k]
        _log(f"      {k} {lab}: n={v['n']} · إسهامٌ {v['mean_per_row']:+.4f}R "
             f"({v['share_pct']:+.1f}% من الفرق)")
    _log("      انتقالُ B1 (R0→الحاكمة): " + (" · ".join(
        f"{k} {v}" for k, v in sorted(dc["transitions"].items())) or "—"))

    # §④ — فاصلُ البوتستراب للسنة (المجمَّعُ يُحسَب من PAIRS بعد الثلاث)
    diffs = [r0_of(r, GOV) - r0_of(r, "R0") for r in rows
             if r.get("o_R0") is not None and r.get(f"o_{GOV}") is not None]
    ci = bootstrap_ci(diffs)
    if ci:
        _log(f"   📏 بوتستراب 95% لـ{GOV}−R0 (سنةٌ واحدة · n={len(diffs)}): "
             f"[{ci[0]:+.4f}, {ci[2]:+.4f}] · المتوسّط {ci[1]:+.4f}")

    d_gov = a[GOV]["r_fixed"] - a["R0"]["r_fixed"]
    fill_ratio = (a[GOV]["n_fill"] / a["R0"]["n_fill"]) if a["R0"]["n_fill"] else 0.0
    if descriptive:
        _log(f"   ⚖️ `WR3` (خارج العيّنة — وصفيّة): {GOV}−R0 = {d_gov:+.4f}R · تعبئةُ {GOV} "
             f"{a[GOV]['n_fill']} ⇒ {'✅ موجبٌ وقابلٌ للقراءة' if (d_gov > 0 and a[GOV]['n_fill'] >= WR3_MIN_FILL) else ('🔴 غيرُ موجب' if a[GOV]['n_fill'] >= WR3_MIN_FILL else '⚠️ دون 50 تعبئة — لا يُقرأ')}")
        _log(f"   🔮 `WR-P5` {GOV}−R0 في [+0.03, +0.15] بتعبئة ≥ {WR3_MIN_FILL}: "
             f"{'✅' if (0.03 <= d_gov <= 0.15 and a[GOV]['n_fill'] >= WR3_MIN_FILL) else '🔴'} ({d_gov:+.4f})")
    else:
        _log(f"   ⚖️ `WR1` (شقُّ السنة): {GOV}−R0 = {d_gov:+.4f}R ⇒ "
             f"{'✅ موجب' if d_gov > 0 else '🔴 غيرُ موجب'}")
        _log(f"   ⚖️ `WR2`: تعبئةُ {GOV}/R0 = {fill_ratio:.3f} ⇒ "
             f"{'✅' if fill_ratio >= WR2_MIN_FILL_RATIO else '🔴'} (الحدّ {WR2_MIN_FILL_RATIO})")
    # §⑤ — التنبّؤاتُ القابلةُ للقراءة بسنةٍ واحدة (تُنشَر كما وقعت)
    b1, b2 = dc["buckets"]["B1"], dc["buckets"]["B2"]
    _log(f"   🔮 `WR-P2` (سنة): B2 > 100% من الفرق و B1 ≤ 0: "
         f"{'✅' if (b2['share_pct'] > 100.0 and b1['sum'] <= 0) else '🔴'} "
         f"(B2 {b2['share_pct']:+.1f}% · B1 {b1['mean_per_row']:+.4f}R)")
    _log(f"   🔮 `WR-P3` (سنة): تعبئةُ R23 < R27: "
         f"{'✅' if a['R23']['n_fill'] < a['R27']['n_fill'] else '🔴'} "
         f"({a['R23']['n_fill']} مقابل {a['R27']['n_fill']})")
    _log(f"   🔮 `WR-P4` (سنة): R27w تبنّد < 50% وفرقُها في [0, فرقُ R27]: "
         f"{'✅' if (a['R27w']['bite_pct'] < 50.0 and 0.0 <= (a['R27w']['r_fixed'] - a['R0']['r_fixed']) <= d_gov) else '🔴'} "
         f"(يبنّد {a['R27w']['bite_pct']:.1f}% · Δ {a['R27w']['r_fixed'] - a['R0']['r_fixed']:+.4f})")
    _log(f"   🔮 `WR-P6` (سنة): R27abs skip ≥ 40% وفرقُها < +0.02: "
         f"{'✅' if (a['R27abs']['skip'] / max(len(rows), 1) >= 0.40 and (a['R27abs']['r_fixed'] - a['R0']['r_fixed']) < 0.02) else '🔴'} "
         f"(skip {a['R27abs']['skip'] / max(len(rows), 1) * 100:.1f}% · Δ {a['R27abs']['r_fixed'] - a['R0']['r_fixed']:+.4f})")

    _log("SUMMARY " + json.dumps(
        {"year": str(year), "descriptive": descriptive, "arms": a, "decomp": dc,
         "ci_year": ci, "n_rows": len(rows), "dates": [dates[0], dates[-1]],
         "wr1_year_ok": bool(d_gov > 0), "d_gov": d_gov, "fill_ratio": fill_ratio},
        ensure_ascii=False))
    _log("PAIRS " + json.dumps(
        {"year": str(year), "gov": GOV, "arms": list(ARMS),
         "p": [[r["symbol"], r["date"]] + [round(r0_of(r, nm), 6) for nm in ARMS]
               for r in rows if all(r.get(f"o_{nm}") is not None for nm in ARMS)]},
        ensure_ascii=False))
    for r in rows:                                   # الصفوفُ في السجلّ (مضيفُ الملفّات محجوب)
        _log("ROW " + json.dumps(r, ensure_ascii=False))
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
    # §② — نفسُ أعلام `T-TRANCHE`/`T-WAIT-LOWER` ⇒ المجتمعُ نفسُه (ميزانيةٌ واحدة للتجارب)
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    # 🔒 `V-R3` بوّابةُ اللقطة (‏`SNAP1`): سنةُ اللقطة **تطابق** سنةَ القياس — وإلّا
    #    قِيست سنةٌ على مجتمعِ سنةٍ أخرى (مقيسٌ حيًّا: 153 صفقة مقابل 1606).
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return 4
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · نافذة {fwd}ج · سبريد {spread} · "
         f"وقفُ القاع {'مشحون' if S.CONFIG.get('PIVOT_STOP_AT_LOW') else 'مُطفأ'} · "
         f"الأذرع " + " · ".join(ARMS) + f" · الحاكمة {GOV} · RSI {RSI_TARGET}/{RSI_LOW}")
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
