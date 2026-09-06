#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚦📈 `T-C-TRIGGER` — هل `T-C` طبقةُ تسليمٍ أفضل من `R1`؟ (‏2023 · 2024 حُكمًا · 2025 ضبطًا)

العقد: `tc_trigger_prereg.md` **مدفوعٌ قبل هذا الملفّ**. أمرُ المالك «جميع ما سبق»
(‏2026-09-06) وفيها «سجّل T-C».

🔒 **قياسٌ/قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ مسٍّ بعتبةٍ إنتاجية ·
   و`Super_stock.py` و`pm_curve_scan.py` **بت-بت** (‏`V-T9`).
🔒 **ملفٌّ مستقلٌّ عمدًا** (‏§②): `PC6` في السويّة يشترط `PC.ARMS` مساواةً تامّة،
   فإضافةُ ذراعٍ داخل `pm_curve_scan.py` **تكسر قفلًا قائمًا**.
🔒 **مقياسٌ واحدٌ لا اثنان:** `summarize` هنا **تُعيد `PC.summarize` بت-بت** حين
   تُعطى `PC.ARMS` — مقفولٌ سلوكيًّا في السويّة (‏`TCA2`)، فلا تتفرّق قراءتان.
"""
from __future__ import annotations

import gzip
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import datetime as dt                                            # noqa: E402

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import pm_curve_scan as PC                                       # noqa: E402
import pm_radar_scan as PMR                                      # noqa: E402
import Super_stock as S                                          # noqa: E402

# ═══════════════ ثوابتُ العقد — **كلُّها مُعادةٌ لا مخترَعة** ═══════════════
MOVER_USD = PC.MOVER_USD                 # $100,000 = IGNITION_USD_OPERATOR
USD_FLOOR = PC.USD_FLOOR                 # $30,000  = LIQ_MIN_USD (مرشِّح R1)
LADDER = PC.LADDER                       # (30, 50, 100)
MIN_MOVERS = PC.MIN_MOVERS               # 100 — أرضيةُ TC4
COVERAGE_MIN = PC.COVERAGE_MIN           # 95.0 — V-T3

# §③: +20% = SPLIT_ROSE_MAX_PCT (faisal_verbatim · IMG_0153) بدلالةٍ مختلفةٍ مُعلَنة
LVL_HI = float(S.CONFIG["SPLIT_ROSE_MAX_PCT"])
# +10% = LIQ_PULSE_PCT (قرارُ مالك 2026-08-19)
LVL_LO = float(S.LIQ_PULSE_PCT)

UNION = "R1|T-C"
ARMS = ("R1", "T-C", "T-B", "T-E", UNION, "C-0", "C-NULL")
# ⛔ ممنوعتا الشحن بنصّ §③ (سوابقُ K-ORACLE · E-PSEUDO · R2/R3)
CONTROL_ARMS = ("C-0", "C-NULL", "T-E")

# 🔒 V-T0 — شاهدُ الضبط بت-بت على 2025 (منشورٌ في `presession_ceiling_result.md`)
V_T0_2025 = {
    "R1": {"msgs_median": 22.5, "msgs_total": 6084, "fruit30_pct": 12.5, "cap100": 54.8},
    "T-C": {"msgs_median": 18.0, "msgs_total": 4826, "fruit30_pct": 19.4, "cap100": 64.0},
}
CTRL_FROM, CTRL_TO = "2025-01-02", "2025-12-31"


def log(msg: str):
    print(msg, flush=True)


# ═══════════════════ ① الأذرعُ السبع ═══════════════════
def trigger_nolvl(rows, usd: float):
    """`C-NULL` ⛔ — **بلا شرطِ سعرٍ إطلاقًا**: أوّلُ دقيقةٍ مغلقةٍ يبلغ عندها مجموعُ
    سيولة البريماركت `usd`. ضابطةٌ تعزل **وجودَ** الشرط (‏§⑥-2) — ممنوعةُ الشحن."""
    cum = 0.0
    for b in rows:
        cum += b[4] * b[5]
        if cum >= usd:
            return (int(b[0]), float(b[4]))
    return None


def e_anchor(rows):
    """`T-E` ⛔ — `R1` **بإطفاء قفزة الحجم وحدَها** (`vol_mult=0.0`)؛ كلُّ ما عداها
    ثابتٌ بالبناء (نفسُ المرشِّح ونفسُ نقطة البدء ونفسُ دالّة الإنتاج).
    سقفٌ تشخيصيّ من صنف `K-ORACLE` — **لا يُقترَح إطفاؤها مهما كانت الأرقام**."""
    i0 = PMR.candidate_index(rows, USD_FLOOR)
    if i0 is None:
        return None
    e = PMR.replay_anchor(rows, i0 + 1, vol_mult=0.0)
    if not e:
        return None
    return (int(e["anchor_ms"]), float(e.get("anchor_price") or e.get("price") or 0.0))


def union_arm(a, b):
    """`R1∪T-C` — **الأبكرُ من الاثنين بالضبط** (‏`V-T6`). غيابُ أحدهما ⇒ الآخر."""
    if a and b:
        return a if a[0] <= b[0] else b
    return a or b


def day_rows(day, bars, prev_close):
    """صفوفُ يومٍ — سلّمُ المتحرّكين ثمّ الأذرعُ السبع. البنيةُ نفسُها التي
    يكتبها `pm_curve_scan` مع حقلٍ إضافيّ `last_ms` (عدّادُ الشمعة الأخيرة §⑥-4)."""
    out = []
    for sym, rws in bars.items():
        pc = prev_close.get(sym)
        if pc is None or not (PMR.PRICE_LO <= pc <= PMR.PRICE_HI):
            continue
        lad = {str(int(p)): PMR.mover_t30(rws, pc, pct=p) for p in LADDER}
        r1 = PC.r1_anchor(rws)
        tc = PC.trigger_ms(rws, pc, MOVER_USD, LVL_HI)
        arms = {
            "R1": r1,
            "T-C": tc,
            "T-B": PC.trigger_ms(rws, pc, MOVER_USD, LVL_LO),
            "T-E": e_anchor(rws),
            UNION: union_arm(r1, tc),
            "C-0": PC.trigger_ms(rws, pc, MOVER_USD, 0.0),
            "C-NULL": trigger_nolvl(rws, MOVER_USD),
        }
        if not any(lad.values()) and not any(arms.values()):
            continue
        out.append({"day": day, "symbol": sym, "prev_close": pc,
                    "last_ms": int(rws[-1][0]) if rws else None,
                    "mover": lad,
                    "arm": {k: (list(v) if v else None) for k, v in arms.items()},
                    "pre_usd": round(sum(b[4] * b[5] for b in rws))})
    return out


# ═══════════════════ ② المقاييس ═══════════════════
def summarize(rows, days, arms=ARMS) -> dict:
    """🔒 **نسخةُ `PC.summarize` مُعمَّمةً على الأذرع** — تُعيد مُخرَجَها بت-بت حين
    `arms = PC.ARMS` (مقفولٌ سلوكيًّا `TCA2`)."""
    res = {"n_days": len(days), "ladder": {}, "arms": {}}
    per_day = {a: {d: 0 for d in days} for a in arms}
    fruit = {a: [0, 0] for a in arms}
    for r in rows:
        t30 = r["mover"].get("30")
        for a in arms:
            v = r["arm"].get(a)
            if v:
                per_day[a][r["day"]] = per_day[a].get(r["day"], 0) + 1
                fruit[a][1] += 1
                fruit[a][0] += int(bool(t30) and v[0] < t30)
    for a in arms:
        msgs = sorted(per_day[a].values())
        res["arms"][a] = {"msgs_median": statistics.median(msgs) if msgs else 0,
                          "msgs_total": sum(msgs),
                          "fruit30_pct": (round(100.0 * fruit[a][0] / fruit[a][1], 1)
                                          if fruit[a][1] else None),
                          "fired": fruit[a][1]}
    for p in LADDER:
        key = str(int(p))
        mv = [r for r in rows if r["mover"].get(key)]
        cell = {"n": len(mv), "arms": {}}
        for a in arms:
            cap = [r for r in mv if r["arm"].get(a) and r["arm"][a][0] < r["mover"][key]]
            cap30 = [r for r in mv if r["arm"].get(a) and r["mover"].get("30")
                     and r["arm"][a][0] < r["mover"]["30"]]
            dl = [(r["arm"][a][1] / r["prev_close"] - 1) * 100 for r in cap
                  if r["prev_close"] and r["arm"][a][1]]
            cell["arms"][a] = {
                "captured": len(cap),
                "cap_pct": round(100.0 * len(cap) / len(mv), 1) if mv else None,
                "cap30_pct": round(100.0 * len(cap30) / len(mv), 1) if mv else None,
                "delay_median": round(statistics.median(dl), 1) if dl else None}
        res["ladder"][key] = cell
    return res


def paired(rows, a: str, b: str) -> dict:
    """🔴 **المقترنُ إلزاميّ (§④):** العدّادُ الحدّيّ داخل الصفّ الواحد — كم صفًّا
    يفيره `a` ولا يفيره `b` والعكس، ومَن منهما أبكر. **لا مقارنةَ بين مجموعتين.**"""
    only_a = only_b = both = a_first = b_first = tie = 0
    for r in rows:
        va, vb = r["arm"].get(a), r["arm"].get(b)
        if va and vb:
            both += 1
            if va[0] < vb[0]:
                a_first += 1
            elif vb[0] < va[0]:
                b_first += 1
            else:
                tie += 1
        elif va:
            only_a += 1
        elif vb:
            only_b += 1
    return {"only_a": only_a, "only_b": only_b, "both": both,
            "a_first": a_first, "b_first": b_first, "tie": tie}


def last_bar_counts(rows) -> dict:
    """§⑥-4 — المحور السابع: `T-C` **تستطيع** أن تفير على آخر شمعة، و`R1` **لا
    تستطيع بنيويًّا** (‏`closed = rows[:-1]` والبدءُ من `i0+1`). يُطبَع بالعدد."""
    out = {a: 0 for a in ARMS}
    for r in rows:
        lm = r.get("last_ms")
        if lm is None:
            continue
        for a in ARMS:
            v = r["arm"].get(a)
            if v and int(v[0]) == lm:
                out[a] += 1
    return out


# ═══════════════════ ③ الحكمان (§⑤) ═══════════════════
def verdict(res: dict) -> list:
    """`TC1`-`TC3` (أ) و`TC5`-`TC6` (ب) بحرفهما · و`TC4` أرضيةٌ تُرجع «لا حكم»."""
    out = []
    low = [k for k in ("30", "50", "100") if (res["ladder"].get(k) or {}).get("n", 0) < MIN_MOVERS]
    if low:
        return [("TC4 الأرضية", "⏸️",
                 "سلالمُ دون " + str(MIN_MOVERS) + ": "
                 + " · ".join(f"+{k}%={res['ladder'][k]['n']}" for k in low) + " ⇒ لا حكم")]
    m_r1 = float(res["arms"]["R1"]["msgs_median"])
    m_tc = float(res["arms"]["T-C"]["msgs_median"])
    m_un = float(res["arms"][UNION]["msgs_median"])
    base = max(1.0, m_r1)
    c1 = (m_tc / base) <= 1.00
    out.append(("TC1 كلفة T-C ÷ R1 ≤ 1.00", "✅" if c1 else "🔴",
                f"{m_tc}/{m_r1} = ×{m_tc / base:.2f}"))
    caps = [(k, res["ladder"][k]["arms"]["T-C"]["cap_pct"] or 0.0,
             res["ladder"][k]["arms"]["R1"]["cap_pct"] or 0.0) for k in ("30", "50", "100")]
    c2 = all(t >= r for _, t, r in caps)
    out.append(("TC2 التقاط T-C ≥ R1 في السلالم الثلاثة", "✅" if c2 else "🔴",
                " · ".join(f"+{k}%: {t} مقابل {r}" for k, t, r in caps)))
    f_tc = res["arms"]["T-C"]["fruit30_pct"] or 0.0
    f_r1 = res["arms"]["R1"]["fruit30_pct"] or 0.0
    c3 = f_tc >= f_r1
    out.append(("TC3 إثمار T-C ≥ R1", "✅" if c3 else "🔴", f"{f_tc}% مقابل {f_r1}%"))
    c5 = (m_un / base) <= 1.50
    out.append(("TC5 كلفةُ الاتّحاد ÷ R1 ≤ 1.50", "✅" if c5 else "🔴",
                f"{m_un}/{m_r1} = ×{m_un / base:.2f}"))
    gain = ((res["ladder"]["100"]["arms"][UNION]["cap_pct"] or 0.0)
            - (res["ladder"]["100"]["arms"]["R1"]["cap_pct"] or 0.0))
    c6 = gain >= 5.0
    out.append(("TC6 مكسبُ الاتّحاد عند +100% ≥ +5.0 نقاط", "✅" if c6 else "🔴",
                f"{gain:+.1f} نقطة"))
    out.append(("⚖️ (أ) التكرار", "✅" if (c1 and c2 and c3) else "🔴", "الثلاثةُ تلزم معًا"))
    out.append(("⚖️ (ب) الطبقةُ الموازية", "✅" if (c5 and c6) else "🔴", "الاثنان يلزمان معًا"))
    return out


# ═══════════════════ ④ بوّاباتُ الصلاحية (§⑦) ═══════════════════
def chain_ok(rows) -> bool:
    """`V-T4` — التداخلُ الرتيب بالبناء: `T-C ⇒ T-B ⇒ C-0 ⇒ C-NULL` (نفسُ الأرضية
    ومستوًى أخفّ ⇒ أبكرُ أو في الدقيقة نفسِها). أيُّ خرقٍ **عطبُ أداة**."""
    for r in rows:
        a = r["arm"]
        for hi, lo in (("T-C", "T-B"), ("T-B", "C-0"), ("C-0", "C-NULL")):
            if a.get(hi) and (not a.get(lo) or a[lo][0] > a[hi][0]):
                return False
    return True


def superset_ok(rows) -> bool:
    """`V-T5` — **`T-E ⊇ R1` بنيويًّا**: إطفاءُ بوّابةٍ لا يُنقص مِرساة."""
    return all(not r["arm"].get("R1") or r["arm"].get("T-E") for r in rows)


def union_ok(rows) -> bool:
    """`V-T6` — الاتّحادُ لكلّ صفّ = الأبكرُ من الاثنين **بالضبط**."""
    for r in rows:
        a = r["arm"]
        want = union_arm(a.get("R1"), a.get("T-C"))
        got = a.get(UNION)
        if (want is None) != (got is None):
            return False
        if want and int(want[0]) != int(got[0]):
            return False
    return True


def noop_ok(res: dict) -> bool:
    """`V-T8` — كلُّ ذراعٍ ضابطةٍ **تفترق عدديًّا** عن قرينتها، وإلّا فهي **غيابُ
    قياسٍ لا نتيجة** (بصمةُ `BT_CANDLE`)."""
    tot = {a: res["arms"][a]["msgs_total"] for a in ARMS}
    return (tot["C-0"] != tot["T-B"] and tot["C-NULL"] != tot["C-0"]
            and tot["T-E"] != tot["R1"])


def ctrl_ok(res: dict) -> list:
    """`V-T0` — شاهدُ الضبط بت-بت على 2025. يُرجع قائمةَ الفروق (فارغةٌ = عبَر)."""
    bad = []
    for a, want in V_T0_2025.items():
        got = res["arms"][a]
        c100 = res["ladder"]["100"]["arms"][a]
        for k in ("msgs_median", "msgs_total", "fruit30_pct"):
            if float(got[k]) != float(want[k]):
                bad.append(f"{a}.{k}: {got[k]} ≠ {want[k]}")
        if float(c100["cap_pct"]) != float(want["cap100"]):
            bad.append(f"{a}.cap100: {c100['cap_pct']} ≠ {want['cap100']}")
    return bad


# ═══════════════════ ⑤ المسار ═══════════════════
def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        log("⛔ V-T1 لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    d_from = (os.environ.get("TCA_FROM") or CTRL_FROM).strip()
    d_to = (os.environ.get("TCA_TO") or CTRL_TO).strip()
    is_ctrl = (d_from, d_to) == (CTRL_FROM, CTRL_TO)
    days = KS.weekdays(d_from, d_to)
    seed = KS.weekdays((dt.date.fromisoformat(d_from) - dt.timedelta(days=7)).isoformat(),
                       (dt.date.fromisoformat(d_from) - dt.timedelta(days=1)).isoformat())[-3:]
    log(f"🚦📈 T-C-TRIGGER — {d_from} ⟶ {d_to} · {len(days)} يوم أسبوع · كون "
        f"[{PMR.PRICE_LO}, {PMR.PRICE_HI}]$ · R1: مرشِّح ${USD_FLOOR:,.0f} + liq_stage_events · "
        f"T-C=(${MOVER_USD:,.0f} ∧ +{LVL_HI:g}%) · T-B=(∧ +{LVL_LO:g}%) · "
        f"T-E=R1 بلا قفزة حجم · C-0=(∧ +0%) · C-NULL=بلا شرطِ سعر · سلّم {LADDER} · وضع legacy"
        + (" · 🔒 **شاهدُ ضبطٍ بت-بت (V-T0)**" if is_ctrl else " · حكمٌ (§⑤)"))
    log("📒 المستويان مُعادان: +20% = SPLIT_ROSE_MAX_PCT (faisal_verbatim) · "
        "+10% = LIQ_PULSE_PCT (قرارُ مالك) — بدلالةٍ مختلفةٍ مُعلَنة، وصفرُ رقمٍ مخترَع.")
    prev_close: dict = {}
    rows_out, n_files, missing = [], 0, []
    fout = open("tc_arms_rows.jsonl", "w", encoding="utf-8")
    try:
        for di, day in enumerate(seed + days):
            seeding = di < len(seed)
            key = AH.day_key(day)
            mb, ep = AH.head_size_mb(key)
            if mb is None:
                if not seeding:
                    missing.append(day)
                continue
            dest = f"/tmp/tca-{day}.csv.gz"
            if not AH.download(key, dest, ep):
                if not seeding:
                    missing.append(day)
                continue
            try:
                with gzip.open(dest, "rt") as fh:
                    bars, closes, _dg = PMR.parse_pre(fh, prev_close, seeding, "legacy")
            except (OSError, KeyError, ValueError) as e:
                log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
                if not seeding:
                    missing.append(day)
                continue
            finally:
                try:
                    os.remove(dest)
                except OSError:
                    pass
            if seeding:
                prev_close.update(closes)
                log(f"🌱 بذرة إغلاق الأمس من {day}: {len(closes):,} رمزًا")
                continue
            n_files += 1
            rws = day_rows(day, bars, prev_close)
            for r in rws:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
            rows_out.extend(rws)
            log(f"📅 {day}: رموز {len(bars):,} · صفوف {len(rws)} · +100% "
                f"{sum(1 for r in rws if r['mover'].get('100'))} · R1 "
                f"{sum(1 for r in rws if r['arm'].get('R1'))} · T-C "
                f"{sum(1 for r in rws if r['arm'].get('T-C'))}")
            prev_close.update(closes)
    finally:
        fout.close()
    cov = 100.0 * n_files / len(days) if days else 0.0
    log(f"\n📦 ملفّات {n_files} من {len(days)} = {cov:.1f}% · مفقود {len(missing)}"
        + (": " + ", ".join(missing[:20]) if missing else "") + f" · صفوف {len(rows_out):,}")
    if n_files == 0 or not rows_out:
        log("⛔ V-T2 صفرُ صفوف — عطبُ أداةٍ لا نتيجة (خروج 4)")
        return 4
    if cov < COVERAGE_MIN:
        log(f"⛔ V-T3 التغطية {cov:.1f}% < {COVERAGE_MIN}% ⇒ عطبُ أداةٍ لا نتيجة (خروج 3)")
        return 3
    if not chain_ok(rows_out):
        log("⛔ V-T4 سلسلةُ الزنادات مكسورة (T-C⇒T-B⇒C-0⇒C-NULL) ⇒ عطبُ أداةٍ (خروج 3)")
        return 3
    if not superset_ok(rows_out):
        log("⛔ V-T5 خرقُ T-E ⊇ R1: إطفاءُ قفزة الحجم أنقص مِرساة ⇒ عطبُ أداةٍ (خروج 3)")
        return 3
    if not union_ok(rows_out):
        log("⛔ V-T6 الاتّحادُ ليس الأبكرَ من الاثنين ⇒ عطبُ أداةٍ (خروج 3)")
        return 3
    log("✅ V-T4/V-T5/V-T6 السلسلةُ والاحتواءُ والاتّحاد سليمةٌ بالبناء")
    res = summarize(rows_out, days)
    if not noop_ok(res):
        log("⛔ V-T8 ذراعٌ ضابطةٌ لا تفترق عدديًّا ⇒ غيابُ قياسٍ لا نتيجة (خروج 4)")
        return 4
    log("✅ V-T8 الضابطاتُ الثلاث تفترق عدديًّا")
    log(f"\n📨 الرسائل لكلّ ذراع على {res['n_days']} جلسة:")
    for a in ARMS:
        v = res["arms"][a]
        mark = " ⛔ ممنوعةُ الشحن" if a in CONTROL_ARMS else ""
        log(f"   {a:<8} وسيط {v['msgs_median']:>6} · مجموع {v['msgs_total']:>7,} · "
            f"إثمار+30% {v['fruit30_pct']}%{mark}")
    for key, cell in res["ladder"].items():
        log(f"\n【متحرّكو +{key}% (سيولة ≥${MOVER_USD:,.0f})】 n={cell['n']}")
        log(f"   {'ذراع':<8}{'التقاط':>10}{'٪':>8}{'قبل +30%':>10}{'تأخّر وسيط٪ (وصفيّ)':>22}")
        for a in ARMS:
            v = cell["arms"][a]
            log(f"   {a:<8}{v['captured']:>10}{str(v['cap_pct']):>8}"
                f"{str(v['cap30_pct']):>10}{str(v['delay_median']):>22}")
    if is_ctrl:
        bad = ctrl_ok(res)
        if bad:
            log("\n⛔ V-T0 شاهدُ الضبط سقط — عطبُ أداةٍ لا نتيجة (خروج 3): " + " · ".join(bad))
            return 3
        log("\n✅ V-T0 شاهدُ الضبط بت-بت: R1 و T-C يعيدان المنشور حرفيًّا "
            "(22.5/6,084/12.5%/54.8 · 18.0/4,826/19.4%/64.0)")
    log("\n🔗 المقترنُ داخل الصفّ (§④ — لا مقارنةَ بين مجموعتين):")
    for a, b in (("T-C", "R1"), (UNION, "R1"), ("T-B", "T-C"), ("C-NULL", "T-C"), ("T-E", "R1")):
        p = paired(rows_out, a, b)
        log(f"   {a} مقابل {b}: كلاهما {p['both']:,} · {a} وحدَه {p['only_a']:,} · "
            f"{b} وحدَه {p['only_b']:,} · الأبكر {a}={p['a_first']:,} {b}={p['b_first']:,} "
            f"تعادل {p['tie']:,}")
    lb = last_bar_counts(rows_out)
    log("\n🕯️ عدّادُ الشمعة الأخيرة (المحور 7 §①) — R1 لا تستطيع بنيويًّا: " +
        " · ".join(f"{a}={lb[a]:,}" for a in ARMS))
    log(f"\n⚖️ الحكم (§⑤ — {'شاهدُ ضبطٍ لا حكم' if is_ctrl else d_from[:4]}):")
    for nm, mark, det in verdict(res):
        log(f"   {mark} {nm}: {det}")
    if is_ctrl:
        log("   ⏸️ 2025 **سنةُ معايرةٍ لا حكم** (§⓪ — الفرضيّةُ وُلدت بعد رؤيتها).")
    log("\n⚠️ حدودُ صدقٍ (مكتوبةٌ قبل الأرقام · §⑨): سبعةُ محاورَ تفرّق T-C عن R1 فلا "
        "يُنسَب الفرقُ لشرط +20% وحدَه · وR1 لا تفير على آخر شمعةٍ بنيويًّا · لمسٌ لا تنفيذ "
        "· **ولا ربحيّةَ تُقاس** · المقامُ مشروط (الصفُّ يُكتَب إن فار سلّمٌ أو ذراع) · "
        "نطاقُ السعر لقطةُ اليوم مُطبَّقةٌ بأثرٍ رجعيّ · الرسائل ≠ التسليم · سنتا حكمٍ "
        "دون حدّنا (ثلاث) · وT-E سقفٌ تشخيصيٌّ ممنوعُ الشحن.")
    log("🔒 سقفُ النجاح (§⑩): **اقتراحٌ للمالك** — لا زنادَ يُشحَن ولا عتبةَ تُمَسّ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
