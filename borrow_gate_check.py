#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔒📏 T-BORROW — قياسُ «المتاح للاقتراض» (`borrow_gate_prereg.md`).

**الجزآن المقيسان هنا (‏§③):**
🅐 **كلفةُ الحدود** ‏20K/40K/100K على القائمة الحيّة — **كلفةٌ لا حافّة**.
🅑 **فصلُ الفئات** من `ctb_log.jsonl` — **وصفيٌّ بمعيارٍ ثلاثيٍّ يُسقطه**.

🔒 **قراءةٌ محضة:** لا يستورد `Super_stock` ولا يكتب حالةً ولا يمسّ قرارًا. والحدودُ
الثلاثة والمعيارُ الثلاثيّ **مثبَّتةٌ في التسجيل قبل أيّ رقم** — ولا رابعَ يُضاف.

🐞 **وحارسُ اسمِ الحقل ليس زينة:** أوّلَ ما فحصتُ `ctb_log.jsonl` قرأتُ `available`/
`fee` — **والحقلان `shares_available`/`borrow_fee`** ⇒ خرجت «‏0 من 170 فيها متاح»
وكِدتُ أُبلغ المالك أن الحصادَ ميّت. ⇒ **صفرٌ موحَّدٌ في حقلٍ يجب أن يكون مملوءًا =
عطبُ قراءةٍ حتى يُنفى**، فالأداةُ **تسقط بصوتٍ عالٍ** (‏`rc=3`) ولا تطبع رقمًا.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

WATCH_FILE = os.environ.get("BORROW_WATCH_FILE", "weekly_watchlist.json")
CTB_FILE = os.environ.get("BORROW_CTB_FILE", "ctb_log.jsonl")
# §③-🅐 الحدودُ الثلاثة مثبَّتة: نصُّ فيصل · بوّابتُنا القائمة · مرجعٌ متساهل.
LINES = (20_000, 40_000, 100_000)
AVAIL, FEE = "shares_available", "borrow_fee"
# §③-🅑 فئاتُ المقارنة (أسماءُ `ctb_harvest` حرفيًّا — لا إعادةَ تسمية).
POS = ("faisal_exec", "faisal_entered")
NEG = ("faisal_negative",)
CTL = ("control_market",)
BOT = ("bot_selected", "bot_watchlist")
CRIT_RATIO, CRIT_POINTS, CRIT_N = 5.0, 30.0, 20     # المعيارُ الثلاثيّ المسجَّل


def load_watch(path: str = None) -> list:
    """أسهمُ القائمة الحيّة (‏`stocks`) — قراءةٌ فقط، وفشلُ الملفّ يُعلَن لا يُخمَّن."""
    with open(path or WATCH_FILE, encoding="utf-8") as fh:
        return (json.load(fh) or {}).get("stocks") or []


def load_ctb(path: str = None) -> list:
    """صفوفُ حصاد الاقتراض (‏JSONL يُلحَق فقط). السطرُ التالف **يُعدّ ويُعلَن**."""
    rows, bad = [], 0
    with open(path or CTB_FILE, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except ValueError:
                bad += 1
    if bad:
        print(f"⚠️ {bad} سطرًا تالفًا في {path or CTB_FILE} — يُعلَن ولا يُصمت.")
    return rows


def _num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def field_guard(rows: list, field: str, label: str) -> tuple[int, int]:
    """🐞 حارسُ اسمِ الحقل (‏§الرأس): يرجّع (كلّ، مملوء) — والمُنادي يُسقط عند صفر."""
    tot = len(rows)
    have = sum(1 for r in rows if _num(r.get(field)) is not None)
    print(f"  🔎 {label}: {have} من {tot} صفًّا تحمل «{field}»")
    return tot, have


def cost_lines(stocks: list, lines=LINES) -> dict:
    """🅐 كم يسقط وكم يبقى عند كلّ حدّ — **بالأسماء** (دالّةٌ نقيّة)."""
    vals = [(s.get("symbol"), _num(s.get(AVAIL))) for s in stocks]
    known = [(k, v) for k, v in vals if v is not None]
    unknown = [k for k, v in vals if v is None]
    out = {"n": len(vals), "known": len(known), "unknown": unknown, "lines": {}}
    for ln in lines:
        keep = sorted(k for k, v in known if v <= ln)
        drop = sorted(k for k, v in known if v > ln)
        out["lines"][ln] = {"keep": keep, "drop": drop}
    return out


def cohort_stats(rows: list, groups: dict) -> dict:
    """🅑 وسيطُ «المتاح» ونسبةُ «تحت 40 ألفًا» لكلّ مجموعة (نقيّة)."""
    out = {}
    for name, cohorts in groups.items():
        v = [x for r in rows if r.get("cohort") in cohorts
             for x in [_num(r.get(AVAIL))] if x is not None]
        if not v:
            out[name] = None
            continue
        under = sum(1 for x in v if x <= 40_000)
        out[name] = {"n": len(v), "median": st.median(v),
                     "under40k_pct": 100.0 * under / len(v), "under40k": under}
    return out


def separation_verdict(cs: dict) -> tuple[bool, list]:
    """§③-🅑 المعيارُ الثلاثيّ المسجَّل — يُقرأ **قبل** أيّ تفسير."""
    pos, ctl = cs.get("فيصل تنفيذ/دخول"), cs.get("شاهد السوق")
    lines, ok = [], True
    if not pos or not ctl:
        return False, [("—", False, "فئةٌ مقارنةٌ غائبة ⇒ لا حكم")]
    ratio = (ctl["median"] / pos["median"]) if pos["median"] > 0 else float("inf")
    c1 = ratio >= CRIT_RATIO
    lines.append(("①", c1, f"وسيطُ الشاهد ÷ وسيطُ فيصل = {ratio:.1f}× "
                           f"(المطلوب ≥{CRIT_RATIO:g}×)"))
    d = pos["under40k_pct"] - ctl["under40k_pct"]
    c2 = d >= CRIT_POINTS
    lines.append(("②", c2, f"فرقُ «تحت 40 ألفًا» = {d:+.0f} نقطة "
                           f"(المطلوب ≥{CRIT_POINTS:g})"))
    c3 = pos["n"] >= CRIT_N and ctl["n"] >= CRIT_N
    lines.append(("③", c3, f"العيّنة: فيصل={pos['n']} · الشاهد={ctl['n']} "
                           f"(المطلوب ≥{CRIT_N} لكلٍّ)"))
    for _t, o, _w in lines:
        ok = ok and o
    return ok, lines


def main() -> int:
    print("=" * 78)
    print("🔒📏 T-BORROW — «المتاح للاقتراض»: 🅐 كلفةُ الحدود · 🅑 فصلُ الفئات")
    print("=" * 78)

    # ── 🅐 ───────────────────────────────────────────────────────────────────
    stocks = load_watch()
    print(f"\n🅐 كلفةُ الحدود على القائمة الحيّة ({len(stocks)} سهمًا · "
          f"{os.path.basename(WATCH_FILE)}):")
    tot, have = field_guard(stocks, AVAIL, "القائمة")
    if tot and not have:
        print("⛔ **صفرٌ موحَّد في حقلٍ يجب أن يكون مملوءًا ⇒ عطبُ قراءةٍ لا نتيجة.**")
        return 3
    c = cost_lines(stocks)
    for s in sorted(stocks, key=lambda x: -(_num(x.get(AVAIL)) or -1)):
        a, f = _num(s.get(AVAIL)), _num(s.get(FEE))
        print(f"   {s.get('symbol',''):<7} متاح={('—' if a is None else f'{a:,.0f}'):>12}"
              f" · رسوم={('—' if f is None else f'{f:.2f}%'):>10}")
    for ln in LINES:
        d = c["lines"][ln]
        print(f"   ── حدّ {ln:,}: يبقى **{len(d['keep'])}** "
              f"({' · '.join(d['keep']) or '—'}) · يسقط **{len(d['drop'])}**")
    if c["unknown"]:
        print(f"   ⚠️ «المتاح» مجهولٌ لـ{len(c['unknown'])}: "
              f"{' · '.join(c['unknown'])} — **تعذّر ≠ صفر** فلا يُحسَب ساقطًا.")
    print("   ⚠️ **كلفةٌ لا حافّة** (‏§③-🅐): لا يُدَّعى من هذي الأرقام ربحٌ ولا خسارة.")

    # ── 🅑 ───────────────────────────────────────────────────────────────────
    rows = load_ctb()
    print(f"\n🅑 فصلُ الفئات من حصاد الاقتراض ({len(rows)} صفًّا):")
    tot2, have2 = field_guard(rows, AVAIL, "الحصاد")
    if tot2 and not have2:
        print("⛔ **صفرٌ موحَّد ⇒ عطبُ قراءةٍ لا نتيجة** (اسمُ الحقل أو الجالب).")
        return 3
    days = sorted({r.get("date") for r in rows if r.get("date")})
    print(f"  📅 {len(days)} يومًا: {days[0]} → {days[-1]}")
    cs = cohort_stats(rows, {"فيصل تنفيذ/دخول": POS, "فيصل سالب": NEG,
                             "قائمة البوت": BOT, "شاهد السوق": CTL})
    print(f"  {'المجموعة':<18}{'ن':>5}{'وسيطُ المتاح':>16}{'تحت 40 ألفًا':>16}")
    for k, v in cs.items():
        if v is None:
            print(f"  {k:<18}{'—':>5}{'غائبة':>16}{'—':>16}")
            continue
        share = f"{v['under40k']}/{v['n']} = {v['under40k_pct']:.0f}%"
        print(f"  {k:<18}{v['n']:>5}{v['median']:>16,.0f}{share:>18}")
    ok, lines = separation_verdict(cs)
    print("\n  🚧 المعيارُ الثلاثيّ المسجَّل (‏§③-🅑):")
    for t, o, w in lines:
        print(f"     {t} {'✅' if o else '⛔'} {w}")
    print("  " + ("🎯 **فصلٌ مستوفًى** (وصفيًّا)" if ok else
                  "🔴 **الفصلُ غيرُ مستوفًى بنصّ المعيار**"))
    print("  🔴 حدودُ صدقٍ إلزامية: الفئاتُ موسومةٌ **لاحقًا** للحدث (دائريّة) · "
          "و«المتاح» يتحرّك خمسَ مراتب يوميًّا · و9 أيامٍ ليست حكمًا · "
          "**والفصلُ ليس حافّة**: فيصل يختار قليلَ المتاح، لا أن قليلَه يربح.")
    print("\n🔒 و`M13`/`SHORT_GATE_MAX` **لم تُمَسّا ولا يُقترَح مسُّهما** (‏§④): "
          "كلفةٌ ووصفٌ لا يصلحان سندًا لتغيير بوّابة — والقرارُ للمالك.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
