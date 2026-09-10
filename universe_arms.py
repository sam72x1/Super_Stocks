#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧭 `T-UNIVERSE` — «اعزل الكون» (العقد `universe_prereg.md` مدفوعٌ **قبل هذا
الملفّ** وقبل أيّ رقم · كوميت `dab2d19`).

**السؤال (§⓪):** لو ثبّتنا **مصدرَ الأسعار** و**إصدارَ الكود** و**يومَ التشغيل**،
وغيّرنا **عضويةَ الكون وحدَها**، كم يتحرّك الحكم؟

**آليّةُ العزل:** لقطةُ `PIT` الواحدة تحمل **الناجين والمشطوبين معًا** ⇒ تُمشى
**مرّةً واحدة** بمحرّك الإنتاج، ثمّ تُقسَّم صفقاتُها بعضويةِ الرمز في **كون
اليوم** (`get_universe` الإنتاجيّة):

    U-ALL  = كلُّ رموز اللقطة              (= تشغيلةُ PIT المنشورة نفسُها)
    U-SURV = الحاضرُ في كون اليوم           (= «باكتيستٌ ساذجٌ يُشغَّل اليوم»)
    U-DEL  = الغائبُ عنه                    (مشطوبٌ/مندمجٌ/مغيَّرُ الرمز)

⇒ `U-ALL = U-SURV ⊎ U-DEL` — فلا يتغيّر بين الذراعين إلّا **عضويةُ الكون**،
لأن المصدرَ واحدٌ والكودَ واحدٌ والشموعَ هي هي **وميزانيةَ المشي واحدةٌ بحكم
البناء** (مشيةٌ واحدةٌ تُقسَّم — درسُ `T-CLIFF`).

**المحرّك — إعادةُ استعمالٍ بالاسم:** `load_frozen_dataset` · `backtest_symbol`
· `get_universe` · `_bt_realized_r` **الإنتاجيّة**. لا نسخَ منطقٍ ولا إعادةَ
كتابةِ مشي، **وشرطُ التخطّي مطابقٌ لـ`run_backtest` حرفيًّا**
(`MIN_BARS + BACKTEST_FORWARD_DAYS`) وإلّا لَما أمكن أن يعبر `V-U1`.

🔒 `Super_stock.py` **لا يُمَسّ بحرف** · قراءةٌ فقط · لا إرسالَ ولا كتابةَ حالة
· الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import sys

OUT_ROWS = "universe_rows.jsonl"
SEED = 20260910              # §④ — مثبَّتةٌ في العقد قبل أيّ رقم
BOOT = 5000                  # §④ — عددُ عيّنات البوتستراب العنقوديّ
FLOOR_DECIDED = 30           # §④ — حدُّ العيّنة لدخول `G1`

# §⑤ `V-U1` — مجاميعُ تشغيلات `PIT` المنشورة (‏`pit_prereg §ملحق ③/⑤` +
# `survivorship_result.md §①`). المفتاحُ سنةٌ · القيمةُ
# (signals, decided, wins, losses, open, no_fill) و`None` = غيرُ منشور.
PUBLISHED = {
    "2023": (227, 168, 45, 123, None, None),
    "2024": (174, 137, 47, 90, 11, 26),
    "2025": (174, 121, 30, 91, 13, 40),
}

# §⑤ `V-U7` (ملحقُ 2026-09-10 — **قبل أيّ رقم**) — بصمةُ `Super_stock.py` الفعليّة.
# تشغيلاتُ `PIT` المنشورة جرت على `c15d5e14` (‏2026-08-07)، **وبين ذاك اليوم
# واليومَ شُحنت تغييراتٌ قراريّة** (‏«اقفل الباب» · «رقّهم» · `ANCHOR_MODE=
# tested_strict` · `PIVOT_STOP_AT_LOW`) ⇒ **إعادةُ إنتاجِ المنشور بكود اليوم
# مستحيلةٌ بنيويًّا**. لذا يُثبَّت الكودُ بالبصمة ويُعلَن أيُّهما جرى.
CODE_FP = {
    "d8e8fb0408c4a502": "PIT·c15d5e14 (2026-08-07 — كودُ تشغيلتَي 2024 و2025)",
    "fe4b89ca307fe7d6": "PIT·4e0d2681 (2026-08-12 — كودُ تشغيلة 2023)",
    "5b82b71b052d62be": "main (2026-09-10 — كودُ اليوم)",
}
# 🔴 **اكتشافٌ يُقال ولا يُطوى (ملحقُ 2026-09-10):** الجدولُ الثلاثيُّ المنشور
# **يخلط إصدارَي كود** — تشغيلتا 2024/2025 على `c15d5e14` وتشغيلةُ 2023 على
# `4e0d2681` (بينهما «اقفل الباب» وبوّابةُ الاقتراض). لذا `V-U1` تُقارَن
# **بكود سنتها هي** لا بكودٍ واحدٍ للثلاث.
PIT_CODE_BY_YEAR = {
    "2023": "fe4b89ca307fe7d6",
    "2024": "d8e8fb0408c4a502",
    "2025": "d8e8fb0408c4a502",
}


def _log(m):
    print(m, flush=True)


def _selfcheck_readonly() -> bool:
    """`V-U0` — قراءةٌ فقط بالـAST على مصدر هذي الأداة: صفرُ إرسالٍ وصفرُ كتابةِ
    حالة، والملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
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


def wilson(w, n):
    """فاصلُ Wilson 95% بالنقاط المئوية (نقيّة · `n=0` ⇒ `(0,0)`)."""
    if not n:
        return (0.0, 0.0)
    z = 1.959963985
    p = w / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, (c - h) * 100.0), min(100.0, (c + h) * 100.0))


def trades_digest(rows, first_n=None):
    """🔏 `V-U1ب` — بصمةُ **قائمة الصفقات نفسِها** لا مجاميعِها: `sha256` على
    «رمز تاريخ نتيجة» مرتّبةً. مجاميعُ متساويةٌ قد تخفي قائمتين مختلفتين
    (‏`227/168/45/123` تتحقّق بأكثرَ من تركيبة) — والبصمةُ لا تخفي.
    `first_n` يقرأ **بترتيب المشي** ليقابل سجلًّا مقصوصًا عند 200 سطر."""
    keys = [f"{r['symbol']} {r['date']} {r['outcome']}" for r in rows]
    if first_n is not None:
        keys = keys[:first_n]
    else:
        keys = sorted(keys)
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def arm_stats(rows, realized_r):
    """📊 مقاييسُ ذراعٍ كاملةً بلا انتقاء (§③) — `R` على **المحسومة** حصرًا،
    وهو نفسُ ما يطبعه `backtest_honest_summary` الإنتاجيّ."""
    dec = [r for r in rows if r["outcome"] in ("win", "loss")]
    wins = sum(1 for r in dec if r["outcome"] == "win")
    rs = [x for x in (realized_r(r) for r in dec) if x is not None]
    lo, hi = wilson(wins, len(dec))
    return {
        "signals": len(rows), "decided": len(dec), "wins": wins,
        "losses": len(dec) - wins,
        "open": sum(1 for r in rows if r["outcome"] == "open"),
        "no_fill": sum(1 for r in rows if r["outcome"] == "no_fill"),
        "win_rate": round(wins / len(dec) * 100.0, 1) if dec else 0.0,
        "R": round(sum(rs) / len(rs), 4) if rs else None,
        "n_R": len(rs), "wilson": [round(lo, 1), round(hi, 1)],
        "symbols": len({r["symbol"] for r in rows}),
    }


def se_two_prop(a, b):
    """§④ — الخطأُ المعياريّ لفرقِ نسبتين **مستقلّتين** بالنقاط المئوية.
    (‏`U-SURV` و`U-DEL` مجموعتا رموزٍ **مُفكَّكتان** ⇒ الاستقلالُ قائم.)"""
    na, nb = a["decided"], b["decided"]
    if not na or not nb:
        return None
    pa, pb = a["wins"] / na, b["wins"] / nb
    return round(math.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb) * 100.0, 2)


def boot_diff_r(rows_a, rows_b, realized_r, seed=SEED, n_boot=BOOT):
    """§④ — بوتستراب **عنقوديٌّ بالرمز** لفرقِ `R` (‏`A − B`): تُعاد المعاينةُ
    على **الرموز** لا الصفقات، لأن صفقاتِ الرمز الواحد ليست مستقلّة (درسُ
    `T-WAIT-23W`). البذرةُ مثبّتةٌ في العقد فالنتيجةُ تُعاد بالأمر نفسِه."""
    def by_sym(rows):
        acc = {}
        for r in rows:
            if r["outcome"] in ("win", "loss"):
                v = realized_r(r)
                if v is not None:
                    acc.setdefault(r["symbol"], []).append(v)
        return list(acc.values())

    ga, gb = by_sym(rows_a), by_sym(rows_b)
    if not ga or not gb:
        return None
    rng = random.Random(seed)
    out = []
    for _ in range(n_boot):
        sa = [v for _ in range(len(ga)) for v in rng.choice(ga)]
        sb = [v for _ in range(len(gb)) for v in rng.choice(gb)]
        if sa and sb:
            out.append(sum(sa) / len(sa) - sum(sb) / len(sb))
    if not out:
        return None
    out.sort()
    return {"lo": round(out[int(0.025 * len(out))], 4),
            "hi": round(out[min(len(out) - 1, int(0.975 * len(out)))], 4),
            "mid": round(out[len(out) // 2], 4), "n": len(out)}


def main() -> int:                                               # noqa: PLR0911
    if not _selfcheck_readonly():
        _log("⛔ `V-U0` الأداةُ ليست قراءةً فقط")
        return 3
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    if not year.isdigit():
        _log("⛔ BACKTEST_YEAR مطلوب")
        return 2
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if not frozen or not os.path.exists(frozen):
        _log("⛔ BT_FROZEN_PATH مطلوب (لقطةُ PIT المجمَّدة)")
        return 2
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415

    # ── `V-U5` — الإعداداتُ = تشغيلاتِ PIT المنشورة حرفيًّا (‏`pit_prereg §④`) ──
    fo, bp = int(S.CONFIG.get("FAISAL_ONLY", 1)), int(S.CONFIG.get("BT_POTENTIAL", 0))
    _log(f"🔒 `V-U5` الإعدادات: FAISAL_ONLY={fo} · BT_POTENTIAL={bp} "
         f"(المطلوب 0 و1)")
    if fo != 0 or bp != 1:
        _log("⛔ `V-U5` سقط — إعدادٌ يخالف تشغيلاتِ PIT المنشورة ⇒ لا مقارنة")
        return 5

    # ── `V-U7` — بصمةُ الكودِ الذي جرى فعلًا (لا وعدٌ في وصفِ التشغيلة) ──
    try:
        _fp = hashlib.sha256(
            open(S.__file__, "rb").read()).hexdigest()[:16]
    except Exception as e:                                       # noqa: BLE001
        _fp = f"⛔{type(e).__name__}"
    code_name = CODE_FP.get(_fp, "⚠️ إصدارٌ غيرُ معروف")
    is_pit_code = (_fp == PIT_CODE_BY_YEAR.get(year))
    _log(f"🔒 `V-U7` بصمةُ Super_stock.py = {_fp} ⇒ {code_name} · وكودُ منشور {year} = {PIT_CODE_BY_YEAR.get(year, '—')} ⇒ {'✅ هو هو' if is_pit_code else '⚠️ مختلف'}")

    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2
    # ── `V-U6` — سنةُ اللقطة تطابق سنةَ القياس (درسٌ مقيس: لقطةُ 2024 على 2025
    #    أعطت 153 صفقة مقابل 1606 = خروجٌ صفريٌّ صامت) ──
    if str(asof or "")[:4] != year:
        _log(f"⛔ `V-U6` اللقطة as-of {asof} لا تطابق سنةَ القياس {year}")
        return 4
    _log(f"🔒 `V-U6` سنةُ اللقطة {str(asof)[:4]} = سنةُ القياس {year}: ✅")

    # ── `V-U4` — كونُ اليوم: فشلُ الجلب يوقف (وإلّا صار الجميعُ «مشطوبًا») ──
    surv = set(S.get_universe() or [])
    _log(f"🔒 `V-U4` كونُ اليوم (`get_universe`): {len(surv)} رمزًا")
    if len(surv) < 1000:
        _log("⛔ `V-U4` سقط — كونُ اليوم أصغرُ من المعقول ⇒ تعذّرَ جلبٍ صامت")
        return 6

    syms = sorted(hist)
    n_surv_sym = sum(1 for s in syms if s in surv)
    n_del_sym = len(syms) - n_surv_sym
    _log(f"📦 اللقطة as-of {asof} · رموزُها {len(syms)} · منها في كون اليوم "
         f"{n_surv_sym} ({n_surv_sym / len(syms) * 100:.1f}%) · غائبٌ عنه "
         f"{n_del_sym} ({n_del_sym / len(syms) * 100:.1f}%)")
    # ── `V-U3` — الذراعان غيرُ صفريّتين ولا تبتلع إحداهما اللقطة ──
    v_u3 = n_surv_sym > 0 and n_del_sym > 0 and min(n_surv_sym, n_del_sym) / len(syms) > 0.01
    _log(f"🔒 `V-U3` الذراعان غيرُ صفريّتين وكلٌّ فوق 1%: "
         f"{'✅' if v_u3 else '⛔'}")
    if not v_u3:
        return 7

    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    min_bars = int(S.CONFIG["MIN_BARS"]) + int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    rows, issues, walked = [], {}, 0
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            if df is None or df.empty or len(df) < min_bars:
                continue
            walked += 1
            try:
                trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                        splits=(splits_map or {}).get(sym))
            except Exception as e:                               # noqa: BLE001
                issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
                continue
            for t in trs:
                if str(t.get("date", ""))[:4] != year:
                    continue                # مطابقةُ قصرِ `whole_year` الإنتاجيّ
                row = {"symbol": sym, "date": str(t.get("date")),
                       "outcome": t.get("outcome"), "entry": t.get("entry"),
                       "stop": t.get("stop"), "t1": t.get("t1"),
                       "surv": bool(sym in surv)}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · مشى {walked} · صفوف {len(rows)}")

    r_all = rows
    r_surv = [r for r in rows if r["surv"]]
    r_del = [r for r in rows if not r["surv"]]
    RR = S._bt_realized_r                                        # noqa: SLF001
    a_all, a_surv, a_del = (arm_stats(r_all, RR), arm_stats(r_surv, RR),
                            arm_stats(r_del, RR))

    _log("")
    _log(f"🧭 `T-UNIVERSE` · سنة {year} · مشى {walked} رمزًا من {len(syms)}"
         + (f" · أخطاء {issues}" if issues else ""))
    _log("")
    for nm, a in (("U-ALL ", a_all), ("U-SURV", a_surv), ("U-DEL ", a_del)):
        _log(f"   {nm}: إشارات {a['signals']:4d} · محسومة {a['decided']:4d} · "
             f"✅{a['wins']:3d} 🛑{a['losses']:3d} · عالقة {a['open']:3d} · "
             f"بلا تعبئة {a['no_fill']:3d} · نسبة {a['win_rate']:5.1f}% "
             f"[{a['wilson'][0]:.0f}-{a['wilson'][1]:.0f}] · "
             f"R {a['R'] if a['R'] is not None else '—'} · رموز {a['symbols']}")

    # ── `V-U2` — التقسيمُ يُتحقَّق منه **سلوكيًّا** لا يُفترَض من استقلال الرمز ──
    v_u2 = (a_surv["signals"] + a_del["signals"] == a_all["signals"]
            and a_surv["decided"] + a_del["decided"] == a_all["decided"]
            and a_surv["wins"] + a_del["wins"] == a_all["wins"]
            and not ({r["symbol"] for r in r_surv} & {r["symbol"] for r in r_del}))
    _log(f"🔒 `V-U2` U-SURV ⊎ U-DEL = U-ALL صفقةً صفقةً وبتقاطعٍ خالٍ: "
         f"{'✅' if v_u2 else '⛔'}")

    # ── `V-U1` — إعادةُ إنتاج مجاميع `PIT` المنشورة بت-بت ──
    pub = PUBLISHED.get(year)
    v_u1 = None
    if pub:
        got = (a_all["signals"], a_all["decided"], a_all["wins"], a_all["losses"],
               a_all["open"], a_all["no_fill"])
        cmp_ = [(g, p) for g, p in zip(got, pub) if p is not None]
        v_u1 = all(g == p for g, p in cmp_)
        _log(f"🔒 `V-U1` المنشور {pub} · المقيس {got} ⇒ "
             f"{'✅ مطابقٌ بت-بت' if v_u1 else '⛔ لا يطابق'}"
             + ("" if is_pit_code else
                "  ℹ️ (كودٌ غيرُ كود المنشور ⇒ `V-U1` **انتماءٌ لا صحّة**"
                " — لا تُبطل `G1` بنصّ ملحق 2026-09-10)"))
    else:
        _log(f"🔒 `V-U1` لا مجاميعَ منشورةً لسنة {year} ⇒ لا مقارنة")
    dig_all = trades_digest(r_all)
    dig_200 = trades_digest(r_all, first_n=200)
    _log(f"🔏 `V-U1ب` بصمةُ الصفقات: مرتّبةً {dig_all} · أوّلُ 200 بترتيب المشي "
         f"{dig_200} (تُقابَل بسجلّ التشغيلة المنشورة)")

    # ── `G1` الحاكمة (عيّنتان مُفكَّكتان) و`G2` الوصفيّة ──
    g1_wr = round(a_surv["win_rate"] - a_del["win_rate"], 2)
    g1_se = se_two_prop(a_surv, a_del)
    g1_r = (round(a_surv["R"] - a_del["R"], 4)
            if (a_surv["R"] is not None and a_del["R"] is not None) else None)
    boot = boot_diff_r(r_surv, r_del, RR)
    g2_wr = round(a_all["win_rate"] - a_surv["win_rate"], 2)
    g2_r = (round(a_all["R"] - a_surv["R"], 4)
            if (a_all["R"] is not None and a_surv["R"] is not None) else None)
    sd = (a_del["decided"] >= FLOOR_DECIDED)
    _log("")
    _log(f"🥇 `G1` (U-SURV − U-DEL): نسبة {g1_wr:+.2f} نقطة"
         + (f" · SE ±{g1_se} ⇒ {abs(g1_wr) / g1_se:.2f} انحراف" if g1_se else "")
         + (f" · R {g1_r:+.4f}" if g1_r is not None else "")
         + (f" · بوتستراب عنقوديّ [{boot['lo']:+.4f}, {boot['hi']:+.4f}]"
            if boot else ""))
    _log(f"   حدُّ العيّنة (§④): محسومةُ U-DEL {a_del['decided']} "
         f"{'✅ تدخل G1' if sd else '⛔ دون 30 ⇒ وصفيّةٌ لا تحكم'}")
    _log(f"📎 `G2` (U-ALL − U-SURV) الأثرُ التشغيليّ: نسبة {g2_wr:+.2f} نقطة"
         + (f" · R {g2_r:+.4f}" if g2_r is not None else ""))
    # ── `P3` — حصّةُ U-DEL من الإشارات مقابل حصّته من الرموز ──
    sh_sig = (a_del["signals"] / a_all["signals"] * 100.0) if a_all["signals"] else 0.0
    sh_sym = n_del_sym / len(syms) * 100.0
    _log(f"🔎 `P3` حصّةُ U-DEL: من الإشارات {sh_sig:.1f}% · من الرموز "
         f"{sh_sym:.1f}% ⇒ {'أعلى ✅' if sh_sig > sh_sym else 'ليست أعلى ⛔'}")

    _log("")
    _log("🔏 UNIVERSE_JSON " + json.dumps(
        {"year": year, "asof": asof, "walked": walked, "snapshot_syms": len(syms),
         "today_universe": len(surv), "surv_syms": n_surv_sym, "del_syms": n_del_sym,
         "U_ALL": a_all, "U_SURV": a_surv, "U_DEL": a_del,
         "G1": {"win_rate": g1_wr, "se": g1_se, "R": g1_r, "boot_R": boot,
                "floor_ok": sd},
         "G2": {"win_rate": g2_wr, "R": g2_r},
         "P3": {"signals_pct": round(sh_sig, 1), "symbols_pct": round(sh_sym, 1)},
         "digest": {"all_sorted": dig_all, "first200_walk": dig_200},
         "V": {"V_U1": v_u1, "V_U2": v_u2, "V_U3": v_u3, "V_U4": len(surv),
               "V_U5": [fo, bp], "V_U6": str(asof)[:4],
               "V_U7": {"fp": _fp, "name": code_name, "is_pit": is_pit_code}},
         "issues": issues}, ensure_ascii=False))
    if not v_u2:
        return 8
    if v_u1 is False and is_pit_code:
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
