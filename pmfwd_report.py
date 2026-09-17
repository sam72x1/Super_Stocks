#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅📡 `T-PMFWD` — الحاكمُ: يقرأ `pmfwd_log.jsonl` ويُصدر حكمَ §⑤ **بحرفه**.

🔒 **قراءةٌ فقط** — صفرُ إرسالٍ وصفرُ كتابةِ ملفٍّ وصفرُ إسنادٍ إلى `CONFIG`،
مُثبَتٌ بـ`selfcheck_readonly`/`no_config_assign` المستورَدتين بالاسم. وهنا
تنطبقان تمامًا، بخلاف الحصّاد الذي يكتب السجلَّ بتصميم العقد نفسِه (§⑨).

⚖️ **ولا يُصدر حكمًا قبل بلوغ الأرضيّة أو تاريخ الحسم** — وعندها يُنشَر
**معدّلُ التراكم المقيس** حتى لو سقطت الأرضيّة، فهو بذاته معلومة (§⑤).
"""
import datetime as _dt
import json
import statistics as _st
import sys

from link100_probe import wilson                                 # بالاسم
from optrade_arms import no_config_assign, selfcheck_readonly    # بالاسم

# ═══════════════ ⓪ الحدود — مثبَّتةٌ بالعقد §⑤ ═════════════════════════════════
LOG = "pmfwd_log.jsonl"
HIT_PCT = 20.0                         # الإصابة — عتبةُ `T-C-TRIGGER` المقيسة
PF1_MIN, PF2_MIN = 15.0, 10.0          # نقاطُ الفرق
PF3_MAX = 3.0                          # وسيطُ الكلفة بالرسائل
MIN_N = 50                             # الأرضيّةُ في **الشقَّين**
DECIDE_BY = "2026-12-31"               # تاريخُ الحسم
RC_OK, RC_NOKEY, RC_COVER, RC_NOROW = 0, 2, 3, 4
RC_GUARD, RC_NOVERDICT = 6, 9


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ═══════════════ ① القراءة ════════════════════════════════════════════════════
def load_rows(path: str = LOG):
    """صفوفُ السجلّ الصالحةُ للحكم — والمُقصى **يُعَدّ ويُطبَع** لا يُطوى."""
    ok, absent, short = [], 0, 0
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except Exception:                                # noqa: BLE001
                    continue
                if r.get("absent"):
                    absent += 1
                    continue
                if r.get("short_cover"):
                    short += 1
                    continue
                if r.get("mv") is None or not r.get("pm_usd"):
                    absent += 1
                    continue
                ok.append(r)
    except FileNotFoundError:
        return [], 0, 0
    return ok, absent, short


def hit_of(rows):
    """`(إصابات، عدد، نسبة٪)` — الإصابةُ `mv ≥ 20%` بنصّ §③."""
    n = len(rows)
    k = sum(1 for r in rows if (r.get("mv") or -1e9) >= HIT_PCT)
    return k, n, (100.0 * k / n if n else 0.0)


def gap_of(a_rows, b_rows):
    """الفرقُ بالنقاط ‏+ هل فاصلا ويلسون ‏95% **منفصلان** (بالاسم)."""
    ka, na, pa = hit_of(a_rows)
    kb, nb, pb = hit_of(b_rows)
    if not na or not nb:
        return {"pa": pa, "pb": pb, "ka": ka, "na": na, "kb": kb, "nb": nb,
                "gap": None, "disjoint": False}
    wa, wb = wilson(ka, na), wilson(kb, nb)                      # بالاسم
    return {"pa": pa, "pb": pb, "ka": ka, "na": na, "kb": kb, "nb": nb,
            "gap": pa - pb, "disjoint": bool(wa[0] > wb[1] or wb[0] > wa[1]),
            "wa": wa, "wb": wb}


def cost_median(rows):
    """وسيطُ عدد صفوف `F-PM` في اليوم = **الرسائلُ الإضافيّة** لو صارت قاعدةَ إشعار."""
    per = {}
    for r in rows:
        per.setdefault(r["day"], 0)
        if r.get("pm_usd") == ">1M":
            per[r["day"]] += 1
    return (_st.median(per.values()) if per else 0.0), len(per)


# ═══════════════ ② الحكم (§⑤ بحرفه) ══════════════════════════════════════════
def read_fwd_verdict(pf1, pf2, pf3, floor, due):
    """الفروعُ الثلاثةُ كلٌّ في سطرها.

    1. **تُوصى** — `PF1` و`PF2` و`PF3` والأرضيّةُ مستوفاة.
    2. **فشلت** — الأرضيّةُ قائمةٌ وسقط معيار.
    3. **لا حكم** — أرضيّةٌ ساقطةٌ عند تاريخ الحسم (أو قبله)."""
    if not floor:
        return RC_NOVERDICT, ("لا حكم",
                              "الأرضيّةُ ساقطةٌ" + ("" if due else " ولم يحن تاريخُ الحسم بعد"))
    if pf1 and pf2 and pf3:
        return RC_OK, ("تُوصى",
                       "تفصل **وتضيف** على طبقة السيولة وبكلفةٍ مقبولة ⇒ "
                       "يُقترَح سطرُ تسليمٍ على المالك ولا يُشحَن بهذا العقد")
    miss = [n for n, v in (("PF1", pf1), ("PF2", pf2), ("PF3", pf3)) if not v]
    return RC_OK, ("فشلت", "الأرضيّةُ قائمةٌ وسقط: " + " · ".join(miss))


def main() -> int:                                               # noqa: PLR0911, PLR0915
    src = open(__file__, encoding="utf-8").read()
    if not (selfcheck_readonly(src) and no_config_assign(src)):   # بالاسم
        _log("⛔ حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    rows, absent, short = load_rows()
    _log("🌅📡 T-PMFWD — الحكم (العقد `pmfwd_prereg.md` §⑤)")
    if not rows:
        _log("⛔ صفرُ صفٍّ صالحٍ في السجلّ — خروج 4")
        return RC_NOROW
    days = sorted({r["day"] for r in rows})
    syms = {r["sym"] for r in rows}
    _log(f"📚 صفوفٌ صالحة {len(rows)} · أيّامٌ {len(days)} "
         f"(‏{days[0]} ⟶ {days[-1]}) · رموزٌ فريدة {len(syms)} · "
         f"مُقصًى: غيابٌ {absent} · تغطيةٌ ناقصة {short}")

    pm = [r for r in rows if r.get("pm_usd") == ">1M"]
    no = [r for r in rows if r.get("pm_usd") != ">1M"]
    okf = [r for r in rows if r.get("fired_ok")]
    nf = [r for r in okf if not r.get("fired")]
    inf = [r for r in okf if r.get("fired")]
    nf_pm = [r for r in nf if r.get("pm_usd") == ">1M"]

    g1 = gap_of(pm, no)
    g2 = gap_of(nf_pm, [r for r in nf if r.get("pm_usd") != ">1M"])
    g3 = gap_of([r for r in inf if r.get("pm_usd") == ">1M"],
                [r for r in inf if r.get("pm_usd") != ">1M"])
    cost, n_days = cost_median(rows)

    d1 = "—" if g1["gap"] is None else f"{g1['gap']:+.1f}"
    d2 = "—" if g2["gap"] is None else f"{g2['gap']:+.1f}"
    s1 = "منفصلان" if g1["disjoint"] else "متداخلان"
    s2 = "منفصلان" if g2["disjoint"] else "متداخلان"
    _log("")
    _log(f"🥇 `F-PM` مقابل `F-NONE`: {g1['pa']:.1f}% ({g1['ka']}/{g1['na']}) "
         f"مقابل {g1['pb']:.1f}% ({g1['kb']}/{g1['nb']}) ⇒ فرقٌ {d1} نقطة · {s1}")
    _log(f"🥇 `C-LIQ` (داخلَ مُكمِّل الإطلاق): {g2['pa']:.1f}% "
         f"({g2['ka']}/{g2['na']}) مقابل {g2['pb']:.1f}% ({g2['kb']}/{g2['nb']}) "
         f"⇒ فرقٌ {d2} نقطة · {s2}")
    _log(f"   `F-IN` (وصفيّة · داخلَ الإطلاق): {g3['pa']:.1f}% "
         f"({g3['ka']}/{g3['na']}) مقابل {g3['pb']:.1f}% ({g3['kb']}/{g3['nb']})")
    _log(f"   `F-COST` (وصفيّة): وسيطُ العابرين في اليوم **{cost:.1f}** "
         f"على {n_days} يومًا")

    pf1 = bool(g1["gap"] is not None and g1["gap"] >= PF1_MIN and g1["disjoint"])
    pf2 = bool(g2["gap"] is not None and g2["gap"] >= PF2_MIN and g2["disjoint"])
    pf3 = bool(cost <= PF3_MAX)
    floor = bool(len(pm) >= MIN_N and len(nf_pm) >= MIN_N)
    due = _dt.date.today().isoformat() >= DECIDE_BY
    rate = (len(pm) / len(days)) if days else 0.0
    _log("")
    _log(f"🧱 الأرضيّة: `F-PM` {len(pm)}/{MIN_N} · `F-PM ∩ ¬fired` "
         f"{len(nf_pm)}/{MIN_N} ⇒ {'✅' if floor else '🔴'} · "
         f"**معدّلُ التراكم {rate:.2f} عابرًا/يوم** · تاريخُ الحسم {DECIDE_BY} "
         f"({'حان' if due else 'لم يحن'})")
    rc, (branch, why) = read_fwd_verdict(pf1, pf2, pf3, floor, due)
    _log(f"   PF1 {'✅' if pf1 else '🔴'} · PF2 {'✅' if pf2 else '🔴'} · "
         f"PF3 {'✅' if pf3 else '🔴'}")
    _log(f"⚖️ الحكم: **{branch}** — {why}")
    _log(f"🚪 رمزُ الخروج = {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
