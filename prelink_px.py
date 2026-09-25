#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️⏳💵 `T-PRELINK §⑩` — «فوق الدولار»: الشروطُ نفسُها بعد استبعاد أسهم السنتات (العقد `prelink_prereg.md §⑩`
— مدفوعٌ ومدموجٌ **قبل أيّ رقمٍ من المقطع** · PR #448).

المصدر: **صفوفُ الحاكمة نفسُها** (artifact `prelink-rows-36163255276`) من `PRELINK_ROWS_DIR` — **لا شبكةَ ولا Polygon**
⇒ المقطعُ جزءٌ من المجتمع المنشور لا مجتمعٌ آخر. والحكمُ **بالدوالّ نفسِها بالاسم** من `prelink_probe`:
`report_set` · `print_verdicts` · `classify_links` · `positioning` · `pos_summary` · `rate` · `wilson` · `z_bonf`.

⓪ **`V-X1` قبل أيّ رقمٍ من المقطع:** المجتمعُ الكامل من الصفوف يُعيد المنشورَ بت-بت (الصفوف · `late100_10` · متوسّطُ
   `POS-0` بثلاث خانات · تجديدُ المرساة على C · **والفرعُ 2**) — وإلّا خروج 3 «لا قياس» ولا يُطبع رقمٌ من المقطع.
① «فوق الدولار» = **سعرُ الكرت الخامُّ لحظةَ التنبيه ≥ `PX_MIN`** (الحاكم · `a.entry`) · والحسّاسيّة **إغلاقُ يوم 0 الخامّ**
   (`close0 × entry ÷ entry_adj`) · والحكمُ **بالأضعف** بين التعريفين · والحدُّ **ثابتٌ هنا لا مُدخَل** (§⑩-2).
② `V-X2`: السعرُ الخامّ حاضرٌ في ‏≥95% من صفوف كلّ مجتمع وإلّا يُطبع النقصُ ويُقيَّد الحكم · وصفٌّ بلا سعرٍ يُعَدّ ولا يُخمَّن.
③ التنبّؤات `PX-P1`…`PX-P6` تُقرأ **آليًّا** بقواعد §⑩-9 المكتوبة قبل التشغيل (لا تفسيرَ بعد الرقم).

🔒 قراءةٌ فقط وبلا شبكة (`_selfcheck` بالـAST: لا كتابةَ ملفٍّ إطلاقًا · لا إرسال · لا `requests`/`subprocess`/جلب).
الخروج: 0 قياس · 3 الصفوفُ غائبة أو `V-X1` ساقط · 5 ليست قراءةً فقط/بلا شبكة.
"""
import ast
import collections
import json
import os
import statistics
import sys

import prelink_probe as P                                            # بالاسم — لا نسخَ للحكم

ROWS_DIR = os.environ.get("PRELINK_ROWS_DIR") or "prelink_rows"
PX_MIN = 1.00                  # 🔒 §⑩-2: ثابتٌ لا مُدخَل (لا تجربةَ عتبةٍ بعد الرقم)
PX_EPS = 1e-9                  # سعرٌ محسوبٌ 0.9999999999 = دولارٌ لا سنت (خطأُ فاصلةٍ عائمة لا سعر)
YEARS = ("2023", "2024", "2025")
TAGS = ("A",) + tuple(f"C{y}" for y in YEARS)
GOV_RUN = "36163255276"        # الحاكمة (§⑩-3)
MIN_RAW = 0.95                 # V-X2
REARM_MIN = 0.80               # PX-P6
OWNER_A = ("rsi14", "float_d", "avail_d", "owner3")                 # §⑩-5 ② على A
OWNER_C = ("rsi14",)                                                 # وعلى C (لا فلوتَ ولا متاحَ رجعيًّا)
# 🔒 المنشورُ في الحاكمة (prelink_result.md · §⑩-4) — V-X1 يُقارن به حرفًا
PUB_ROWS = {"A": 413, "C2023": 10842, "C2024": 14299, "C2025": 19010}
PUB_LATE = {"A": (35, 411), "C2023": (560, 10842), "C2024": (1046, 14299), "C2025": (1205, 19010)}
PUB_POS0 = {"A": "-0.545", "C2023": "-0.322", "C2024": "-0.240", "C2025": "-0.280"}
PUB_REARM = {"C2023": (523, 560), "C2024": (953, 1046), "C2025": (1111, 1205)}
PUB_REARM_A = (20, 35)         # وصفيٌّ خارجَ V-X1 (الحاكمةُ بنته من المراسي كلِّها لا من الصفوف)
PUB_BRANCH = "2 «لا رابط» بالمعيار الستّة"
NET_MODS = {"requests", "urllib", "urllib3", "http", "socket", "subprocess", "aiohttp"}
NET_CALLS = {"_get", "grouped_day", "build_series", "anchors_A", "trades_day", "quotes_close", "ticker_daily_adj",
             "sec_recent_filings", "fetch_day", "daily_range", "load_all_splits", "urlopen", "system", "popen", "_dump_rows"}


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── الحارسُ الذاتيّ ───────────────────────────
def _selfcheck(src=None) -> bool:
    """قراءةٌ فقط **وبلا شبكة** (AST): حارسُ `prelink_probe` بالاسم (لا `_dump_rows` هنا ⇒ لا كتابةَ ملفٍّ إطلاقًا)
    ‏+ لا استيرادَ لمكتبة شبكةٍ أو `subprocess` ‏+ لا وصولَ إلى `.requests` ‏+ لا نداءَ جلبٍ من الأداة الحاكمة."""
    try:
        src = src if src is not None else open(__file__, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:                                                # noqa: BLE001
        return False
    if not P._selfcheck_readonly(src):
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in NET_MODS for a in n.names):
            return False
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in NET_MODS:
            return False
        if isinstance(n, ast.Attribute) and n.attr in ("requests", "subprocess"):
            return False
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in NET_CALLS:
                return False
    return True


# ─────────────────────────── الصفوف ───────────────────────────
def load_rows(d):
    """⟵ {"A": صفوف, "C2023": …} أو None إن غاب ملفّ · ومفاتيحُ `k` تعود أعدادًا (JSON يجعلها نصوصًا فتعمى الأفواج)."""
    out = {}
    for tag in TAGS:
        fn = f"{P.ROWS_PREFIX}A.jsonl" if tag == "A" else f"{P.ROWS_PREFIX}C_{tag[1:]}.jsonl"
        path = os.path.join(d, fn)
        if not os.path.exists(path):
            log(f"⛔ الصفوفُ غائبة: {path}")
            return None
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                r["k"] = {int(kk): vv for kk, vv in (r.get("k") or {}).items()}
                rows.append(r)
        out[tag] = rows
    return out


def raw_card(r):
    """سعرُ الكرت الخامّ لحظةَ التنبيه (A ‏`e5` بالاسم · C ‏`entry` = سعرُ دقيقةِ المرساة) — أو None."""
    e = (r.get("a") or {}).get("entry")
    try:
        e = float(e)
    except (TypeError, ValueError):
        return None
    return e if e > 0 else None


def raw_close0(r):
    """إغلاقُ يوم 0 الخامّ = `close0 × entry ÷ entry_adj` (‏`entry_adj = entry × fac0` ⇒ يُزيل تسويةَ التقسيم) — أو None."""
    e = raw_card(r)
    o = r.get("o") or {}
    ea, c0 = o.get("entry_adj"), o.get("close0")
    try:
        ea, c0 = float(ea), float(c0)
    except (TypeError, ValueError):
        return None
    if e is None or ea <= 0 or c0 <= 0:
        return None
    return c0 * e / ea


PX_DEFS = (("card", "سعرُ الكرت الخامّ (الحاكم)", raw_card), ("close0", "إغلاقُ يوم 0 الخامّ (الحسّاسيّة)", raw_close0))


def split_px(rows, getpx, px_min=PX_MIN):
    """⟵ (فوق الحدّ, تحت الحدّ, بلا سعر) — الحدُّ **شاملٌ** (‏1.00 فوق) · وبلا سعرٍ يُعَدّ ولا يُخمَّن."""
    above, below, none = [], [], []
    for r in rows:
        p = getpx(r)
        if p is None:
            none.append(r)
        elif p + PX_EPS >= px_min:
            above.append(r)
        else:
            below.append(r)
    return above, below, none


def calendar_index():
    """فهرسُ أيّام التداول 2022-2026 بالاسم (`year_days`) — الفروقُ بين يومين هي نفسُها في لوحة الحاكمة."""
    days = []
    for y in ("2022", "2023", "2024", "2025", "2026"):
        days += P.year_days(y)
    return {d: i for i, d in enumerate(days)}


def rearm_counts(rows_sub, rows_year, didx):
    """تجديدُ المرساة قبل القمّة بين متأخّري `rows_sub` — **والمراسي من صفوف السنة كلِّها** (§⑩-3 · كما في الحاكمة):
    التنبيهُ التالي على الرمز نفسِه تنبيهٌ ولو كان دون الدولار."""
    abs_ = collections.defaultdict(list)
    for r in rows_year:
        abs_[r["sym"]].append(didx[r["day0"]])
    late = [r for r in rows_sub if r["o"].get("late100_10")]
    k = sum(1 for r in late if any(0 < g - didx[r["day0"]] <= (r["o"].get("days_to_peak") or 0) for g in abs_[r["sym"]]))
    return k, len(late)


def n_tests():
    """عددُ الاختبارات بصيغة الحاكمة حرفًا (‏58 ⇒ z=3.33)."""
    return len(P.FEATS_SPEC) + len(P.FEATS_A_ONLY) + len(P.COMBOS) + len(P.COMBOS_K) + 1 + 12 + 1


def verdicts(pop, z):
    """⟵ (vA, vA2, vC, vC2) بـ`report_set` بالاسم — مع/بدون صفوف التقسيم كما في الحاكمة."""
    ra = pop.get("A") or []
    rc = {y: pop.get(f"C{y}") or [] for y in YEARS}
    vA = P.report_set(ra, "A", P.MIN_N_A, z, halves=True)
    vA2 = P.report_set([r for r in ra if not r["o"].get("split_in_win")], "A", P.MIN_N_A, z, halves=True)
    vC = {y: P.report_set(rows, f"C{y}", P.MIN_N_C, z) for y, rows in rc.items()}
    vC2 = {y: P.report_set([r for r in rows if not r["o"].get("split_in_win")], f"C{y}", P.MIN_N_C, z) for y, rows in rc.items()}
    return vA, vA2, vC, vC2


def branch_text(links, momentum_only):
    """نصُّ الفرع كما تطبعه الحاكمة (للهُويّة)."""
    if links:
        return f"1 «رابطٌ مقيس» — {links} (قيدَ الإثبات الأماميّ · لا يُشحَن شيء)"
    return "2 «لا رابط» بالمعيار الستّة" + (f" — ويفصل زخمًا/مرساةً لا رابطًا: {momentum_only}" if momentum_only else "")


# ─────────────────────────── V-X1 ───────────────────────────
def vx1(pop, didx, z):
    """⟵ (ok, أسطر): المجتمعُ الكامل يُعيد المنشورَ بت-بت — وإلّا لا رقمَ من المقطع."""
    ok, lines = True, []
    for tag in TAGS:
        rows = pop.get(tag) or []
        miss = sum(1 for r in rows if r.get("day0") not in didx)
        if miss:
            ok = False
            lines.append(f"   ❌ {tag}: {miss} صفًّا يومُ 0 فيه خارجَ التقويم")
    if not ok:
        return ok, lines
    for tag in TAGS:
        rows = pop.get(tag) or []
        good = len(rows) == PUB_ROWS[tag]
        ok = ok and good
        lines.append(f"   صفوف {tag}: {len(rows):,} — المنشور {PUB_ROWS[tag]:,} {'✅' if good else '❌'}")
    for tag in TAGS:
        got = P.rate(pop.get(tag) or [], "late100_10")
        good = tuple(got) == PUB_LATE[tag]
        ok = ok and good
        lines.append(f"   late100_10 {tag}: {got[0]}/{got[1]} — المنشور {PUB_LATE[tag][0]}/{PUB_LATE[tag][1]} {'✅' if good else '❌'}")
    for tag in TAGS:
        ps = P.pos_summary(pop.get(tag) or [], "POS-0")
        got = "—" if ps is None else f"{ps['mean']:+.3f}"
        good = got == PUB_POS0[tag]
        ok = ok and good
        lines.append(f"   POS-0 {tag}: {got} — المنشور {PUB_POS0[tag]} {'✅' if good else '❌'}")
    for y in YEARS:
        rows = pop.get(f"C{y}") or []
        got = rearm_counts(rows, rows, didx)
        good = tuple(got) == PUB_REARM[f"C{y}"]
        ok = ok and good
        lines.append(f"   تجديدُ المرساة C{y}: {got[0]}/{got[1]} — المنشور {PUB_REARM[f'C{y}'][0]}/{PUB_REARM[f'C{y}'][1]} {'✅' if good else '❌'}")
    vA, vA2, vC, vC2 = verdicts(pop, z)
    links, mom = P.classify_links(vA, vA2, vC, vC2, emit=lambda _s: None)
    br = branch_text(links, mom)
    good = br == PUB_BRANCH
    ok = ok and good
    lines.append(f"   الفرع: {br} — المنشور {PUB_BRANCH} {'✅' if good else '❌'}")
    ra = pop.get("A") or []
    a_rearm = rearm_counts(ra, ra, didx)
    lines.append(f"   (وصفيٌّ خارجَ V-X1) تجديدُ المرساة A من الصفوف: {a_rearm[0]}/{a_rearm[1]} — المنشور {PUB_REARM_A[0]}/{PUB_REARM_A[1]} من المراسي كلِّها")
    return ok, lines


# ─────────────────────────── الأساسُ داخل المقطع (§⑩-5 ①) ───────────────────────────
def base_block(rows, tag, didx, rows_year):
    """الآفاق · التصنيف · المراسي ÷ الشاهدين · المتأخّرون وتجديدُ المرساة ⟵ مقاييسُ التنبّؤات."""
    m = {}
    for h in P.HORIZONS:
        k, n = P.rate(rows, f"late100_{h}")
        k5, n5 = P.rate(rows, f"late50_{h}")
        lo, hi = P.wilson(k, n) if n else (0, 0)
        log(f"   {tag} · أفق {h}: +100% {k}/{n} = {k / n * 100 if n else 0:.1f}% [{lo:.0f}·{hi:.0f}] · +50% {k5}/{n5} = {k5 / n5 * 100 if n5 else 0:.1f}%")
    log(f"   {tag} · التصنيف: {dict(collections.Counter(r['o'].get('cls') for r in rows))}")
    cm = [r for r in rows if r["ctrl"].get("CM") and r["ctrl"]["CM"].get("late100_10") is not None]
    cr = [r for r in rows if r["ctrl"].get("CR") and r["ctrl"]["CR"].get("late100_10") is not None]
    k, n = P.rate(rows, "late100_10")
    pa = k / n if n else None
    pm = (sum(1 for r in cm if r["ctrl"]["CM"]["late100_10"]) / len(cm)) if cm else None
    pr = (sum(1 for r in cr if r["ctrl"]["CR"]["late100_10"]) / len(cr)) if cr else None
    m["late"], m["pa"], m["pm"], m["n_cm"] = (k, n), pa, pm, len(cm)
    m["cm_ratio"] = (pa / pm) if (pa is not None and pm) else None
    log(f"   {tag} · الشاهدان (late100_10): CM {P.fmt(pm * 100 if pm is not None else None)}% (n={len(cm)}) ⇒ {P.fmt(m['cm_ratio'])}× · "
        f"CR {P.fmt(pr * 100 if pr is not None else None)}% (n={len(cr)}) ⇒ {P.fmt(pa / pr if (pa is not None and pr) else None)}× (CR وصفٌ لا حكم)")
    late = [r for r in rows if r["o"].get("late100_10")]
    rk, rn = rearm_counts(rows, rows_year, didx)
    m["rearm"] = (rk, rn)
    if late:
        dtp = [r["o"]["days_to_peak"] for r in late if r["o"].get("days_to_peak") is not None]
        mdd = [r["o"]["mdd_before_peak"] for r in late if r["o"].get("mdd_before_peak") is not None]
        held = [r["o"]["held_low0_to_peak"] for r in late if r["o"].get("held_low0_to_peak") is not None]
        log(f"   {tag} · المتأخّرون (+100%/10): n={len(late)} · وسيطُ الأيّام حتى القمّة {P.fmt(statistics.median(dtp) if dtp else None)} · "
            f"وسيطُ أقصى الهبوط قبلها {P.fmt(statistics.median(mdd) if mdd else None)}% · صمد فوق low0 {sum(held)}/{len(held)} · "
            f"مرساةٌ جديدة قبل القمّة {rk}/{rn}" + (" (من صفوف A — وصفيّ)" if tag.startswith("A") else ""))
    s3 = [r for r in rows if r["f"].get("owner3") is not None]
    n3 = sum(1 for r in s3 if r["f"]["owner3"] == "نعم")
    k3 = sum(1 for r in s3 if r["f"]["owner3"] == "نعم" and r["o"].get("late100_10"))
    m["owner3_n"], m["owner3_known"] = n3, len(s3)
    if tag.startswith("A"):
        log(f"   {tag} · شروطُ المالك الثلاث مجتمعةً (مؤرَّخًا): معلومةٌ {len(s3)} · استوفاها {n3} · انفجر متأخّرًا منها {k3}")
    log(f"   {tag} · صفوفٌ بتقسيمٍ داخل النافذة (V-P2): {sum(1 for r in rows if r['o'].get('split_in_win'))}")
    return m


# ─────────────────────────── التنبّؤات (§⑩-7 بقواعد §⑩-9) ───────────────────────────
def _r3(v):
    return "—" if v is None else f"{v:+.3f}"


def _ci(ci):
    return "" if not ci or ci[0] is None else f"[{ci[0]:+.2f},{ci[1]:+.2f}]"


def _tri(vals):
    """✅ كلُّها صحيحة · ❌ واحدةٌ تُكذّبه · ⚪ لا تكذيبَ لكن فيها «لا حكم»."""
    if any(v is False for v in vals):
        return "❌"
    if any(v is None for v in vals):
        return "⚪"
    return "✅"


def eval_predictions(res):
    """`res` = مقاييسُ تعريفٍ واحد ⟵ {PX-Pi: (✅/❌/⚪, شرح)} — القواعدُ مكتوبةٌ في §⑩-9 قبل التشغيل."""
    out = {}
    r1 = [None if res["cm_ratio"].get(y) is None else (1.0 <= res["cm_ratio"][y] <= 2.0) for y in YEARS]
    out["PX-P1"] = (_tri(r1), " · ".join(f"C{y} {P.fmt(res['cm_ratio'].get(y))}×" for y in YEARS))
    r2 = [None if res["rsi_c1"].get(y) is None else (res["rsi_c1"][y] is False) for y in YEARS]
    out["PX-P2"] = (_tri(r2), " · ".join(f"C{y} ①={res['rsi_c1'].get(y)}" for y in YEARS))
    out["PX-P3"] = ("✅" if res["owner3_n"] < P.MIN_N_A else "❌", f"استوفاها {res['owner3_n']} (الحدّ {P.MIN_N_A})")
    out["PX-P4"] = ("✅" if not res["links"] else "❌", f"روابط {res['links'] or '—'}")
    p5a = [None if res["pos0"].get(y) is None else (res["pos0"][y] < 0) for y in YEARS]
    neg_d = sum(1 for y in YEARS if res["diff"].get(y) is not None and res["diff"][y] < 0)
    nonneg_d = sum(1 for y in YEARS if res["diff"].get(y) is not None and res["diff"][y] >= 0)
    d_ok = True if neg_d >= 2 else (False if nonneg_d >= len(YEARS) - 1 else None)   # «سالبٌ في سنتين على الأقلّ»
    p5 = _tri(p5a + [d_ok])
    out["PX-P5"] = (p5, " · ".join(f"C{y} POS-0 {_r3(res['pos0'].get(y))} فرق {_r3(res['diff'].get(y))}" for y in YEARS))
    r6 = [None if not res["rearm"].get(y) or not res["rearm"][y][1] else (res["rearm"][y][0] / res["rearm"][y][1] >= REARM_MIN) for y in YEARS]
    out["PX-P6"] = (_tri(r6), " · ".join(f"C{y} {res['rearm'].get(y, (0, 0))[0]}/{res['rearm'].get(y, (0, 0))[1]}" for y in YEARS))
    return out


# ─────────────────────────── التنفيذ ───────────────────────────
def main() -> int:                                                   # noqa: PLR0912, PLR0915
    if not _selfcheck():
        log("⛔ الحارسُ الذاتيّ: الأداةُ ليست قراءةً فقط/بلا شبكة — خروج 5")
        return 5
    log(f"🕵️⏳💵 T-PRELINK §⑩ «فوق الدولار» · الحاكمة {GOV_RUN} · الحدّ ${PX_MIN:.2f} (ثابت) · الصفوف من {ROWS_DIR}")
    pop = load_rows(ROWS_DIR)
    if pop is None:
        log("⛔ «لا قياس» — صفوفُ الحاكمة غائبة · خروج 3")
        return 3
    didx = calendar_index()
    nt = n_tests()
    z = P.z_bonf(nt)
    log(f"🧮 n_tests={nt} ⇒ z={z:.2f} (كالحاكمة)")
    log(f"\n{'=' * 78}\n🔒 V-X1 — المجتمعُ الكامل يُعيد المنشورَ بت-بت (قبل أيّ رقمٍ من المقطع)\n{'=' * 78}")
    ok, lines = vx1(pop, didx, z)
    for ln in lines:
        log(ln)
    if not ok:
        log("⛔ V-X1 ساقط — الفرعُ 3 «لا قياس» ولا يُطبع رقمٌ من المقطع · خروج 3")
        return 3
    log("✅ V-X1 عابر — الصفوفُ هي الحاكمةُ نفسُها")
    res, raw_ok, sizes = {}, {}, {}
    for dfn, label, getpx in PX_DEFS:
        log(f"\n{'#' * 78}\n💵 المقطع «فوق الدولار» بتعريف: {label}\n{'#' * 78}")
        sub, raw_ok[dfn], sizes[dfn] = {}, True, {}
        for tag in TAGS:
            above, below, none = split_px(pop[tag], getpx)
            sub[tag] = above
            share = 1 - len(none) / len(pop[tag]) if pop[tag] else 0
            good = share >= MIN_RAW
            raw_ok[dfn] = raw_ok[dfn] and good
            sizes[dfn][tag] = (len(above), len(below), len(none))
            log(f"   {tag}: فوق الدولار {len(above):,} · دونه {len(below):,} · بلا سعرٍ خامّ {len(none):,} "
                f"(V-X2 حاضرٌ {share * 100:.1f}% {'✅' if good else '⚠️ دون 95% — الحكمُ مقيَّد'})")
        log("\n📊 §⑩-5 ① الأساس داخل المقطع")
        rm = {}
        for tag in TAGS:
            rm[tag] = base_block(sub[tag], tag, didx, pop[tag])
        vA, vA2, vC, vC2 = verdicts(sub, z)
        P.print_verdicts({k: vA[k] for k in OWNER_A if k in vA}, f"👤 §⑩-5 ② شروطُ المالك على A — {label}")
        for y in YEARS:
            P.print_verdicts({k: vC[y][k] for k in OWNER_C if k in vC[y]}, f"👤 §⑩-5 ② شرطُ RSI على C{y} — {label}")
        P.print_verdicts(vA, f"🔗 §⑩-5 ③ A — الـ58 داخل المقطع — {label}")
        for y in YEARS:
            P.print_verdicts(vC[y], f"🔗 §⑩-5 ③ C{y} — الـ58 داخل المقطع — {label}")
        log(f"\n{'=' * 78}\n🏁 الحكمُ داخل المقطع (بالأضعف · مع/بدون صفوف التقسيم) — {label}\n{'=' * 78}")
        links, mom = P.classify_links(vA, vA2, vC, vC2)
        log(f"\n{'=' * 78}\n💵 §⑩-5 ④ التمركز داخل المقطع — {label}\n{'=' * 78}")
        pos_ok, diffs, pos_verdict = P.positioning(sub["A"], {y: sub[f"C{y}"] for y in YEARS})
        pos0 = {}
        for y in YEARS:
            ps = P.pos_summary(sub[f"C{y}"], "POS-0")
            pos0[y] = ps["mean"] if ps else None
        res[dfn] = {"label": label, "links": links, "mom": mom, "pos_verdict": pos_verdict, "pos_ok": pos_ok,
                    "cm_ratio": {y: rm[f"C{y}"]["cm_ratio"] for y in YEARS},
                    "rsi_c1": {y: (vC[y].get("rsi14") or {}).get("c1") for y in YEARS},
                    "owner3_n": rm["A"]["owner3_n"], "owner3_known": rm["A"]["owner3_known"],
                    "pos0": pos0, "diff": {y: (diffs[y][0] if y in diffs else None) for y in YEARS},
                    "diff_ci": {y: (diffs[y][1:3] if y in diffs else None) for y in YEARS},
                    "rearm": {y: rm[f"C{y}"]["rearm"] for y in YEARS},
                    "base": {tag: rm[tag] for tag in TAGS},
                    "owner": {"A": {k: vA.get(k) for k in OWNER_A}, **{f"C{y}": {k: vC[y].get(k) for k in OWNER_C} for y in YEARS}}}
    # ── الخلاصة (آخرُ الأسطر · تُقرأ وحدَها)
    links_both = [x for x in res["card"]["links"] if x in res["close0"]["links"]]
    mom_both = [x for x in res["card"]["mom"] if x in res["close0"]["mom"]]
    restricted = not all(raw_ok.values())
    log(f"\n{'=' * 78}\n🏁🏁 الخلاصة — §⑩ «فوق الدولار» (الحاكمة {GOV_RUN} · يُقرأ بالأضعف بين التعريفين)\n{'=' * 78}")
    log("   V-X1 ✅ (الصفوفُ هي الحاكمةُ نفسُها) · V-X2 " + " · ".join(f"{d} {'✅' if raw_ok[d] else '⚠️'}" for d in raw_ok))
    for dfn, r in res.items():
        log(f"\n   ▸ {r['label']}")
        for tag in TAGS:
            a, b, nn = sizes[dfn][tag]
            bm = r["base"][tag]
            k, n = bm["late"]
            kf, _nf = P.rate(pop[tag], "late100_10")
            log(f"     {tag}: المقطع {a:,} (دونه {b:,} · بلا سعر {nn:,}) · late100_10 {k}/{n} = {k / n * 100 if n else 0:.1f}% · "
                f"CM {P.fmt(bm['pm'] * 100 if bm['pm'] is not None else None)}% ⇒ {P.fmt(bm['cm_ratio'])}× · "
                f"من متأخّري المجتمع الكامل {k}/{kf} فوق الدولار")
        for tag, feats in r["owner"].items():
            for name, v in feats.items():
                if not isinstance(v, dict):
                    log(f"     👤 {tag} {name}: —")
                elif v.get("c1") is None:
                    log(f"     👤 {tag} {name} «{v.get('best')}»: {v.get('why', 'لا حكم')}")
                else:
                    log(f"     👤 {tag} {name} «{v['best']}»: {v['p'][0]:.1f}% ({v['k'][0]}/{v['n'][0]}) مقابل {v['p'][1]:.1f}% ({v['k'][1]}/{v['n'][1]}) · "
                        f"①{'✅' if v['c1'] else '❌'} ②{'✅' if v['c2'] else '❌'} ⑤{'✅' if v.get('c5') else '❌'} ⑥{'✅' if v.get('c6') else '❌'}")
        log(f"     🔗 روابط: {r['links'] or '—'} · زخمٌ/مرساة: {r['mom'] or '—'}")
        log("     💵 POS-0: " + " · ".join(f"C{y} {_r3(r['pos0'][y])}R" for y in YEARS)
            + " · POS-0 − C-MOM: " + " · ".join(f"C{y} {_r3(r['diff'][y])}R {_ci(r['diff_ci'][y])}" for y in YEARS)
            + f" ⇒ التمركز {'ممكن ✅' if r['pos_verdict'] else 'غيرُ ممكن ❌'}")
        log("     🔁 تجديدُ المرساة قبل القمّة: " + " · ".join(f"C{y} {r['rearm'][y][0]}/{r['rearm'][y][1]}" for y in YEARS))
    log("\n   🔮 التنبّؤات (§⑩-7 بقواعد §⑩-9 · الحاكمُ تعريفُ الكرت والحسّاسيّةُ بجواره):")
    pc, px0 = eval_predictions(res["card"]), eval_predictions(res["close0"])
    for key in pc:
        log(f"     {key}: الكرت {pc[key][0]} ({pc[key][1]}) · إغلاقُ يوم 0 {px0[key][0]}")
    if links_both:
        branch = f"1 «رابطٌ فوق الدولار» — {links_both} (قيدُ الإثبات الأماميّ · لا يُشحَن شيء)"
    else:
        branch = "2 «لا رابط فوق الدولار»" + (f" — ويفصل زخمًا/مرساةً لا رابطًا: {mom_both}" if mom_both else "")
    pos_both = res["card"]["pos_verdict"] and res["close0"]["pos_verdict"]
    log(f"\n🏁 الفرعُ {branch}" + (" · ⚠️ مقيَّدٌ بـV-X2" if restricted else ""))
    log(f"🏁 التمركزُ فوق الدولار: {'ممكنٌ بالتعريفين ✅' if pos_both else 'غيرُ ممكن ❌'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
