#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️⏳🔁 `T-PRELINK §⑪` — «دخولُ التنبيه الثاني»: هل يربح التمركزُ على التنبيه المُعاد؟ (العقد `prelink_prereg.md §⑪`
— مدفوعٌ ومدموجٌ **قبل أيّ رقمٍ من هذا السؤال**).

المصدر: **صفوفُ الحاكمة نفسُها** (artifact `prelink-rows-36163255276`) — **لا شبكةَ ولا محاكاةَ جديدة**: `POS-0` و`C-MOM`
مقروءان من الصفوف كما بنتهما الحاكمة (§⑥ بحرفه) · والتحميلُ والهُويّةُ والمقطعُ **بالاسم** من `prelink_px`
(`load_rows` · `vx1` · `split_px` · `raw_card`) · والملخّصُ والفاصلُ بالاسم من `prelink_probe` (`pos_summary` · `boot_ci`).

⓪ `V-X1` قبل أيّ رقم (بت-بت مع المنشور) — وإلّا خروج 3.
① «ثانٍ» = `raw.days_since_anchor` من 1 إلى 5 (السلّةُ «≤5» المُعلَنة في §④-7) · «أوّل» = بلا مرساةٍ سابقة في 60 جلسة (القيمةُ غائبة).
② الفرعُ 1 = «الثاني» موجبٌ بفاصلٍ فوق الصفر **و**`POS-0 − C-MOM` بفاصلٍ فوق الصفر في كلّ سنةٍ من C **بالمجتمعين** (الكامل
   الحاكم · وفوق الدولار الحسّاسيّة) · 3 «لا قياس» إن كان «الثاني» دون `MIN_SECOND` صفًّا في سنة · وإلّا 2.

🔒 قراءةٌ فقط وبلا شبكة (`prelink_px._selfcheck` بالاسم على مصدر هذه الأداة).
الخروج: 0 قياس · 3 الصفوفُ غائبة أو `V-X1` ساقط أو «لا قياس» · 5 ليست قراءةً فقط/بلا شبكة.
"""
import sys

import prelink_px as X                                               # بالاسم — تحميل · هُويّة · مقطع
from prelink_px import P                                             # prelink_probe بالاسم نفسِه

SECOND_MIN, SECOND_MAX = 1, 5  # 🔒 §⑪-2: السلّةُ «≤5» المُعلَنة في §④-7 — لا بارامترَ جديد
MIN_SECOND = 300               # §⑪-5: «لا قياس» دونه في أيّ سنةٍ من C
YEARS = X.YEARS
POPS = (("full", "المجتمعُ الكامل (الحاكم)"), ("px", "فوق الدولار بسعر الكرت (الحسّاسيّة)"))


def log(msg=""):
    print(msg, flush=True)


def dsa(r):
    """`days_since_anchor` الخامّ — أو None (بلا مرساةٍ سابقة في 60 جلسة)."""
    v = (r.get("raw") or {}).get("days_since_anchor")
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None


def is_second(r):
    """«التنبيهُ الثاني»: مرساةٌ سابقةٌ للرمز نفسِه قبل 1-5 جلسات (حدّاها شاملان)."""
    d = dsa(r)
    return d is not None and SECOND_MIN <= d <= SECOND_MAX


def second_rows(rows):
    return [r for r in rows if is_second(r)]


def first_rows(rows):
    """«التنبيهُ الأوّل»: لا مرساةَ سابقة في 60 جلسة."""
    return [r for r in rows if dsa(r) is None]


def paired_diff(rows):
    """`POS-0 − C-MOM` للصفوف التي تحمل الاثنين ⟵ (متوسّط, أدنى, أعلى, n) أو None — بالفاصل نفسِه (`boot_ci` بالاسم)."""
    d = [r["pos"]["POS-0"] - r["pos"]["C-MOM"] for r in rows
         if r["pos"].get("POS-0") is not None and r["pos"].get("C-MOM") is not None]
    if not d:
        return None
    lo, hi = P.boot_ci(d)
    return (sum(d) / len(d), lo, hi, len(d))


def measure(pop_rows):
    """`pop_rows` = {وسم: صفوف} ⟵ {وسم: {second, first, diff, n_second}} — الملخّصُ بـ`pos_summary` بالاسم."""
    out = {}
    for tag, rows in pop_rows.items():
        sec = second_rows(rows)
        fst = first_rows(rows)
        out[tag] = {"n_second": len(sec), "second": P.pos_summary(sec, "POS-0"), "first": P.pos_summary(fst, "POS-0"),
                    "cmom_second": P.pos_summary(sec, "C-MOM"), "diff": paired_diff(sec)}
    return out


def pop_branch(res):
    """فرعُ مجتمعٍ واحد: «1» · «2» · «3» (§⑪-5) على سنوات C."""
    cs = [res.get(f"C{y}") or {} for y in YEARS]
    if any(c.get("n_second", 0) < MIN_SECOND for c in cs):
        return "3"
    ok = all(c.get("second") and c["second"]["mean"] > 0 and c["second"]["ci"][0] is not None and c["second"]["ci"][0] > 0
             and c.get("diff") and c["diff"][1] is not None and c["diff"][1] > 0 for c in cs)
    return "1" if ok else "2"


def branch(res_by_pop):
    """بالأضعف بين المجتمعين: «3» يغلب · ثمّ «2» · و«1» لا يكون إلّا بالاثنين."""
    bs = [pop_branch(res_by_pop[k]) for k, _l in POPS]
    if "3" in bs:
        return "3"
    return "1" if all(b == "1" for b in bs) else "2"


def _tri(vals):
    if any(v is False for v in vals):
        return "❌"
    if any(v is None for v in vals):
        return "⚪"
    return "✅"


def eval_predictions(res, br):
    """`res` = المجتمعُ الكامل ⟵ {RA-Pi: (✅/❌/⚪, شرح)} — بالمتوسّط كما §⑩-9."""
    cs = {y: res.get(f"C{y}") or {} for y in YEARS}
    p1 = [None if not cs[y].get("second") else cs[y]["second"]["mean"] < 0 for y in YEARS]
    better = [None if not (cs[y].get("second") and cs[y].get("first")) else cs[y]["second"]["mean"] > cs[y]["first"]["mean"] for y in YEARS]
    nb = sum(1 for v in better if v is True)
    nw = sum(1 for v in better if v is False)
    p2 = True if nb >= 2 else (False if nw >= 2 else None)
    neg = [None if not cs[y].get("diff") else cs[y]["diff"][0] < 0 for y in YEARS]
    nn = sum(1 for v in neg if v is True)
    npos = sum(1 for v in neg if v is False)
    p3 = True if nn >= 2 else (False if npos >= 2 else None)
    return {"RA-P1": (_tri(p1), "سالبٌ في الثلاث"), "RA-P2": (_tri([p2]), f"أقلُّ سلبًا في {nb} من 3"),
            "RA-P3": (_tri([p3]), f"الفرقُ سالبٌ في {nn} من 3"), "RA-P4": ("✅" if br == "2" else "❌", f"الفرع {br}")}


def _fmt_ps(ps):
    return "—" if not ps else f"{ps['mean']:+.3f}R [{ps['ci'][0]:+.2f},{ps['ci'][1]:+.2f}] ربح {ps['win']:.0f}% n={ps['n']}"


def _fmt_d(d):
    return "—" if not d else f"{d[0]:+.3f}R [{d[1]:+.2f},{d[2]:+.2f}] n={d[3]}"


def main() -> int:
    src = open(__file__, encoding="utf-8").read()
    if not X._selfcheck(src):
        log("⛔ الحارسُ الذاتيّ: الأداةُ ليست قراءةً فقط/بلا شبكة — خروج 5")
        return 5
    log(f"🕵️⏳🔁 T-PRELINK §⑪ «دخولُ التنبيه الثاني» · الحاكمة {X.GOV_RUN} · «ثانٍ» = مرساةٌ سابقة قبل {SECOND_MIN}-{SECOND_MAX} جلسات")
    pop = X.load_rows(X.ROWS_DIR)
    if pop is None:
        log("⛔ «لا قياس» — صفوفُ الحاكمة غائبة · خروج 3")
        return 3
    didx = X.calendar_index()
    z = P.z_bonf(X.n_tests())
    ok, lines = X.vx1(pop, didx, z)
    log(f"\n{'=' * 78}\n🔒 V-X1 — المجتمعُ الكامل يُعيد المنشورَ بت-بت (قبل أيّ رقم)\n{'=' * 78}")
    for ln in lines:
        log(ln)
    if not ok:
        log("⛔ V-X1 ساقط — الفرعُ 3 «لا قياس» ولا يُطبع رقم · خروج 3")
        return 3
    log("✅ V-X1 عابر")
    pops = {"full": {t: pop[t] for t in X.TAGS},
            "px": {t: X.split_px(pop[t], X.raw_card)[0] for t in X.TAGS}}
    res = {k: measure(v) for k, v in pops.items()}
    for key, label in POPS:
        log(f"\n{'=' * 78}\n💵 {label} — POS-0 بحرف §⑥ (دخولُ إغلاق يوم 0 · وقفٌ 2% تحت أدناه · +100% أو 10 جلسات · 1% للطرف)\n{'=' * 78}")
        for tag in X.TAGS:
            r = res[key][tag]
            log(f"   {tag}: الثاني {_fmt_ps(r['second'])} · الأوّل {_fmt_ps(r['first'])} · C-MOM على الثاني {_fmt_ps(r['cmom_second'])}")
            log(f"   {tag}: POS-0 − C-MOM على الثاني {_fmt_d(r['diff'])}")
    br = branch(res)
    pr = eval_predictions(res["full"], br)
    log(f"\n{'=' * 78}\n🏁🏁 الخلاصة — §⑪ «دخولُ التنبيه الثاني» (يُقرأ بالأضعف بين المجتمعين)\n{'=' * 78}")
    for key, label in POPS:
        cs = " · ".join(f"C{y} {res[key][f'C{y}']['second']['mean']:+.3f}R" if res[key][f"C{y}"]["second"] else f"C{y} —" for y in YEARS)
        ds = " · ".join(f"C{y} {_fmt_d(res[key][f'C{y}']['diff'])}" for y in YEARS)
        log(f"   ▸ {label}: فرعُه {pop_branch(res[key])} · الثاني {cs}")
        log(f"     POS-0 − C-MOM: {ds}")
    for k, (st, why) in pr.items():
        log(f"   🔮 {k}: {st} ({why})")
    names = {"1": "1 «دخولُ الثاني موجب» (قيدُ الإثبات الأماميّ · لا يُشحَن شيء)", "2": "2 «لا» — الدخولُ على التنبيه الثاني لا يربح بعد التكلفة",
             "3": "3 «لا قياس»"}
    log(f"\n🏁 الفرعُ {names[br]}")
    return 3 if br == "3" else 0


if __name__ == "__main__":
    sys.exit(main())
