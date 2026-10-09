# -*- coding: utf-8 -*-
"""🧭🗂️ stage_ledger — سجلُّ أحداثٍ مصدريّ لسلوك فيصل الموثَّق (مهمّةُ «STAGE SEMANTICS RECONSTRUCTION» 2026-10-09).
بحثٌ فقط · لا إنتاج · لا تلغرام · لا شبكة · لا يقرأ المحرّك (المحرّكُ في stage_crosswalk.py بعد العقد).

المدخلات (ملتزَمةٌ كلُّها):
  faisal_method_v4/data/visual_pass_v4.jsonl        — مرورُ العين V4 (609 وحدة) · الاقتباسُ الحرفيّ «…» داخل g
  faisal_engine/data/stage/eye_reads.json           — قراءةُ عينٍ في هذه المهمّة (تأكيدٌ/تصحيحٌ لا يمحو V4 · وصورُ ما بعد V4)
  faisal_method_v41/batches/B48_20261007/faisal_annotations.json · final_protocol/reveal/CASE_000{2,3}.json — نصُّ الحالات الأماميّة (تحقّقُ تطابقٍ مع قراءة العين)
  fm_forensics/phase3/FAISAL_TIMELINE.csv            — للمصالحة فقط (لا يصنع حدثًا)
  fm_forensics/data/bars_2026-10-08.json.gz          — توفّرُ الشموع وتقويمُ الجلسات وحدَهما (لا مؤشّر ولا مرحلة)

المخرجات (faisal_engine/out/): stage_events.csv · stage_episodes.csv · stage_transitions.csv · stage_phase3_reconciliation.csv ·
stage_ledger_summary.json — حتميّةٌ بايتًا (`--check` يعيد التوليد ويقارن).

القواعد: الوسمُ الخامّ (RAW_LABEL/RAW_ACTION) نصٌّ حرفيٌّ من المصدر لا يُترجَم إلى مرحلة محرّك · المرصودُ والمستنتَج حقلان ·
الطابعُ من المصدر لا من رقم الملفّ · اللقطةُ تُثبت عضويّةَ التبويب الظاهر وحدَه · والغائبُ UNKNOWN."""
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("FE_STAGE_OUT") or os.path.join(HERE, "out")
VP = os.path.join(ROOT, "faisal_method_v4", "data", "visual_pass_v4.jsonl")
EYE = os.path.join(HERE, "data", "stage", "eye_reads.json")
B48 = os.path.join(ROOT, "faisal_method_v41", "batches", "B48_20261007", "faisal_annotations.json")
REVEAL = os.path.join(ROOT, "faisal_method_v41", "final_protocol", "reveal")
P3 = os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv")
BARS = os.path.join(ROOT, "fm_forensics", "data", "bars_2026-10-08.json.gz")

FAISAL_AUTHORS = ("F", "F_inferred")
DIRECT_AB = ("VISIBLE", "VISIBLE_OCR", "VISIBLE_LINKED", "VISIBLE_AVATAR", "VISIBLE_PROFILE", "EYE_VERIFIED")
# نصوصُ واجهة تطبيق «مراقب استراتيجية فيصل» (طرفٌ ثالث · عائلة APP) — تظهر داخل منشوراتٍ فلا تُنسَب لفيصل
APP_UI = ("مراقب استراتيجية فيصل", "مراقبة مبكرة", "قريب من الجاهزية", "مراقبة")

# ------------------------------------------------------------------ تطبيعٌ عربيٌّ بخريطة مواضع (الحرفيُّ يُستعاد من الأصل)
_MAP1 = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي"})
_DROP = set("ـًٌٍَُِّْ‏‎")


def norm_map(s):
    out, idx = [], []
    for i, ch in enumerate(s or ""):
        if ch in _DROP:
            continue
        out.append(ch.translate(_MAP1))
        idx.append(i)
    return "".join(out), idx


# ------------------------------------------------------------------ المعجم (على النصّ المطبَّع · الترتيبُ = الأولويّة · التداخلُ لا يُعَدّ مرّتين)
# RAW_LABEL: أسماءُ القوائم والمراحل والجاهزيّة · RAW_ACTION: الأفعالُ والنيّات
LEX = [
    ("LABEL", "ADD_TO_LIST", r"يضاف (لل|ل)?(مفضله|قائمه)|ضع لك قائمه|تضيف فيها قائمه"),
    ("LABEL", "UNDER_READINESS", r"تحت ال?جاهزيه"),
    ("LABEL", "READY_100", r"جاهز ?100"),
    ("LABEL", "NOT_READY", r"(غير|ماهو|مو|مب|ليس)[ .]{0,2}جاهز\w*"),
    ("LABEL", "READINESS_NOUN", r"جاهزيه"),
    ("LABEL", "READY", r"[جح]اهز\w*"),
    ("LABEL", "SORT", r"فرز( ?(اول|ثاني|2|1))?"),
    ("LABEL", "LIST", r"قائمتي|القائمه|قائمه|المفضله"),
    ("ACTION", "NO_ENTRY", r"لا ?تشري|(ما|ولا) ?دخلت\w*|(ما|ولا) ?شريت\w*|(?<!\w)ما ?دخل(?!\w)|غير صالح للدخول|لا ?تدخل"),
    ("ACTION", "OPERATOR_MONEY", r"(دولار|مليون|سيوله|الف) دخلت|دخول سيوله"),
    ("ACTION", "ENTRY_EXECUTED", r"دخلت\w*|دخلنا\w*|شريت\w*|اشتريت\w*|عززت"),
    ("ACTION", "ENTRY_STATED", r"دخولنا|اضافه كميات"),
    ("ACTION", "ENTRY_PLAN", r"ندخل\w*|نركب|نبي دخول|الدخول|دخول|الطلبات|طلبات"),
    ("ACTION", "EXIT", r"طلعت|خرجت|خروج|بعت|بعنا|جنيت|جني (ال)?ربح"),
    ("ACTION", "PRESS", r"شمع[هة] الضغط|ضغط\w*|يضغط\w*|تم الضغط"),
    ("ACTION", "WAIT", r"(ب|ل)?انتظار|ننتظر|انتظر\w*|ينتظر"),
    ("ACTION", "MONITOR", r"تحت المجهر|تحت (ال)?متابعه|تحت (ال)?مراقبه|(ال)?مراقبه|(ال)?متابعه|نتابع|نراقب|راقب\w*|تابع(ه)?(?!\w)"),
    ("ACTION", "INVALID", r"فشل|الغاء|ملغي|ابتعد"),
    ("ACTION", "TRANSITION_WORD", r"(?<!\w)(نقل|تنقل|انتقل)\w*"),
]
LEX_RE = [(k, n, re.compile(p)) for k, n, p in LEX]
NOT_MONITOR = re.compile(r"المتابعين|متابعين|كمتابع|متابع السهم|للمتابعين|احد المتابعين")
TECH_QUAL = re.compile(r"فنيا|فني|المؤشرات والشموع")
RECALL = re.compile(r"(?<!\w)(كان|كانت|ذكرنا|سابقا)(?!\w)")
PAST_PRESS = re.compile(r"تم الضغط|اثناء|ضغط اليوم|مع شمع[هة] الضغط|الضغط حصل|حصل الضغط|مع الضغط")
WAIT_PRESS = re.compile(r"(انتظار|ننتظر|بانتظار|انتظر|هل)\W{0,3}(\w+\W{0,3}){0,3}(ضغط|يضغط)")
Q_RE = re.compile(r"«([^»]*)»")
# إحالةٌ إلى ما سبق (واسعة · خامّ) — عمودٌ مستقلٌّ لا يأخذ من المعجم
CARRY = re.compile(r"ذكرنا|ذكرت|ذاكره قبل|سابقا|تحليل سابق|تم التحليل قبل|(ما ?زال|لازال) تحت|كان جاهز|كان سهم متابعه|كانت متابع\w*|نعطيك سهم|مازال تحت")


def lex(text):
    """[(kind, name, literal, start)] بترتيب الموضع — الحرفيُّ مقطوعٌ من النصّ الأصليّ لا المطبَّع."""
    n, idx = norm_map(text)
    taken, hits = [False] * len(n), []
    for kind, name, rx in LEX_RE:
        for m in rx.finditer(n):
            s, e = m.span()
            if s == e or any(taken[s:e]):
                continue
            if name == "MONITOR":
                ctx = n[max(0, s - 4):e + 8]
                if NOT_MONITOR.search(ctx):
                    continue
            for i in range(s, e):
                taken[i] = True
            lit = text[idx[s]:idx[e - 1] + 1]
            hits.append((kind, name, lit, s))
    return sorted(hits, key=lambda h: (h[3], h[1])), n


# ------------------------------------------------------------------ التقويمُ والشموع (توفّرٌ فقط)
_BARS = None


def _bars():
    global _BARS
    if _BARS is None:
        _BARS = json.load(gzip.open(BARS, "rt", encoding="utf-8"))
        _BARS["_cal"] = sorted({r[0] for rows in _BARS["daily"].values() for r in rows})
    return _BARS


def calendar():
    return _bars()["_cal"]


def session_on_or_after(day):
    cal = calendar()
    for d in cal:
        if d >= day:
            return d
    return None


def next_session(day):
    cal = calendar()
    for d in cal:
        if d > day:
            return d
    return None


def md_available(sym, asof):
    """الشموعُ متاحةٌ قبل يوم القرار؟ (الرمزُ في الملفّ المجمَّد ‏+ شمعةٌ واحدةٌ على الأقلّ قبل asof)"""
    if not sym or not asof:
        return "UNKNOWN"
    rows = _bars()["daily"].get(sym)
    if not rows:
        return "NO_BARS"
    return "YES" if rows[0][0] < asof else "NO_BARS_BEFORE"


# ------------------------------------------------------------------ الطوابع
PRINTED_RE = re.compile(r"(20\d\d)/(\d{1,2})/(\d{1,2})(?:\s*[·,]?\s*(\d{1,2}):(\d{2})\s*(ص|م))?")
RIYADH = dt.timezone(dt.timedelta(hours=3))


def _ny_offset(d):
    # التوقيتُ الصيفيّ في نيويورك 2025-03-09…2025-11-02 · 2026-03-08…2026-11-01 (قاعدةٌ ثابتةٌ لا شبكة)
    y = d.year
    start = {2025: dt.date(2025, 3, 9), 2026: dt.date(2026, 3, 8)}.get(y)
    end = {2025: dt.date(2025, 11, 2), 2026: dt.date(2026, 11, 1)}.get(y)
    if start and end and start <= d.date() < end:
        return dt.timedelta(hours=-4)
    return dt.timedelta(hours=-5)


def asof_from_printed(y, m, d, hh, mm, ampm):
    """منشورٌ بطابعٍ مطبوع (ساعةُ جهاز اللقطة · افتراضُ الرياض UTC+3 — مُعلَن) ⟵ يومُ القرار: الجلسةُ التي تكون شموعُها
    السابقةُ كلُّها مكتملةً لحظةَ النشر (قبل 16:00 نيويورك ⟵ جلسةُ اليوم نفسِه · بعدها ⟵ التالية)."""
    h = int(hh) % 12 + (12 if ampm == "م" else 0)
    t = dt.datetime(int(y), int(m), int(d), h, int(mm), tzinfo=RIYADH)
    ny = t.astimezone(dt.timezone.utc) + _ny_offset(t)
    day = ny.strftime("%Y-%m-%d")
    first = session_on_or_after(day)
    if first == day and ny.hour * 60 + ny.minute >= 16 * 60:
        return next_session(day), ny.strftime("%Y-%m-%d %H:%M NY")
    return first, ny.strftime("%Y-%m-%d %H:%M NY")


DECADE_RE = re.compile(r"^(20\d\d)-(\d\d)-(\d)x$")
EXACT_RE = re.compile(r"^(20\d\d)-(\d\d)-(\d\d)$")
MONTH_RE = re.compile(r"^(20\d\d)-(\d\d)$")


def _month_end(y, m):
    return (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).isoformat()


def prev_or_equal_session(day):
    cal = calendar()
    best = None
    for d in cal:
        if d <= day:
            best = d
        else:
            break
    return best


def window_for_range(a, b):
    """أيّامُ نشرٍ ممكنةٌ [a … b] بلا ساعةٍ ولا منطقةٍ زمنيّة ⟵ [أوّلُ جلسةٍ ≥ a … الجلسةُ بعد آخر جلسةٍ ≤ b] (نشرٌ بعد الإغلاق)."""
    lo = session_on_or_after(a)
    last = prev_or_equal_session(b)
    hi = next_session(last) if last else None
    if lo and hi and hi < lo:
        hi = lo
    return lo, hi


def window_from_recorded(d):
    """تاريخٌ مسجَّلٌ بلا ساعة ⟵ نافذةُ أيّام القرار (المنطقةُ الزمنيّة والساعةُ مجهولتان)."""
    d = (d or "").strip()
    m = EXACT_RE.match(d)
    if m:
        lo, hi = window_for_range(d, d)
        return "EXACT_DATE", lo, hi
    m = DECADE_RE.match(d)
    if m:
        y, mo, k = int(m.group(1)), int(m.group(2)), int(m.group(3))
        end = _month_end(y, mo)
        a = f"{y}-{mo:02d}-{max(1, k * 10):02d}"
        b = end if k == 3 else min(f"{y}-{mo:02d}-{k * 10 + 9:02d}", end)
        lo, hi = window_for_range(a, b)
        return "BOUNDED", lo, hi
    m = MONTH_RE.match(d)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        lo, hi = window_for_range(f"{y}-{mo:02d}-01", _month_end(y, mo))
        return "BOUNDED", lo, hi
    return "AMBIGUOUS", None, None


def timestamp(unit_d, printed, derived=None):
    """⟵ (TS_QUALITY, asof_lo, asof_hi, original_ts, ny_ts, mismatch)
    EXACT_PRINTED: طابعٌ مطبوعٌ بساعة · EXACT_DATE_PRINTED: تاريخٌ مطبوعٌ بلا ساعة · EXACT_DERIVED: مشتقٌّ من الظاهر إلى جلسةٍ واحدة ·
    RECORDED_UNVERIFIED: تاريخٌ مسجَّلٌ في V4 بلا طابعٍ مطبوعٍ يسنده · BOUNDED: مدى · AMBIGUOUS: لا يُحدَّد."""
    mismatch = ""
    if derived:
        return derived["quality"], derived["asof_lo"], derived["asof_hi"], derived["original"], derived.get("ny", ""), ""
    if printed:
        y, mo, da, hh, mm, ap = printed
        pd_ = f"{int(y):04d}-{int(mo):02d}-{int(da):02d}"
        if unit_d and EXACT_RE.match(unit_d):
            gap = abs((dt.date.fromisoformat(unit_d) - dt.date.fromisoformat(pd_)).days)
            if gap > 1:
                mismatch = f"PRINTED {pd_} vs RECORDED {unit_d}"
        if hh is not None:
            a, ny = asof_from_printed(y, mo, da, hh, mm, ap)
            return "EXACT_PRINTED", a, a, f"{y}/{mo}/{da} {hh}:{mm} {ap}", ny, mismatch
        lo, hi = window_for_range(pd_, pd_)
        return "EXACT_DATE_PRINTED", lo, hi, f"{y}/{mo}/{da}", "", mismatch
    q, lo, hi = window_from_recorded(unit_d)
    if q == "EXACT_DATE":
        q = "RECORDED_UNVERIFIED"
    return q, lo, hi, (unit_d or ""), "", mismatch


def find_printed(text):
    """أوّلُ طابعِ نشرٍ مطبوعٍ بسنةٍ صريحة وساعة (وإلّا أوّلُ تاريخٍ بسنةٍ صريحة) — من نصّ التفريغ الحرفيّ."""
    best = None
    for m in PRINTED_RE.finditer(text or ""):
        y, mo, da, hh, mm, ap = m.groups()
        if not (1 <= int(mo) <= 12 and 1 <= int(da) <= 31):
            continue
        if hh is not None:
            return (y, mo, da, hh, mm, ap)
        best = best or (y, mo, da, None, None, None)
    return best


# ------------------------------------------------------------------ تصنيفُ المفاهيم A-F من الأفعال الحرفيّة
def _recalled(hits, ntext, kinds):
    """هل يقع لفظٌ من kinds في مقطعٍ (بين « / ») فيه لفظُ استرجاع (كان · ذكرنا · سابقا)؟ ⟵ الحالةُ تخصّ زمنًا أسبق من النشر."""
    starts = [0] + [m.end() for m in re.finditer(r" / ", ntext)]
    ends = [m.start() for m in re.finditer(r" / ", ntext)] + [len(ntext)]
    for h in hits:
        if h[1] in kinds:
            for a, b in zip(starts, ends):
                if a <= h[3] < b and RECALL.search(ntext[a:b]):
                    return True
    return False


def concepts(hits, ntext, faisal, override=None):
    """A عضويّةُ قائمة · B مرحلةُ اختيار · C فعلٌ/نيّة · E زنادُ دخولٍ فعليّ · F مجهول — D (حالةُ المحرّك) لا تأتي من المصدر."""
    names = [h[1] for h in hits]
    override = override or {}
    A = "ADD_TO_LIST_STATED" if "ADD_TO_LIST" in names else ("LIST_TERM" if "LIST" in names else "")
    b = []
    for n in ("READY_100", "UNDER_READINESS", "READINESS_NOUN", "SORT", "NOT_READY", "READY"):
        if n in names:
            b.append(n)
    tech = bool(TECH_QUAL.search(ntext)) and any(n in ("READY", "NOT_READY") for n in names)
    recalled = _recalled(hits, ntext, ("READY", "NOT_READY")) or bool(override.get("readiness_recalled"))
    e_recalled = _recalled(hits, ntext, ("ENTRY_EXECUTED", "ENTRY_STATED", "OPERATOR_MONEY", "PRESS"))
    c = [n for n in ("WAIT", "MONITOR", "ENTRY_PLAN", "NO_ENTRY", "EXIT", "INVALID", "TRANSITION_WORD") if n in names]
    e = []
    if "ENTRY_EXECUTED" in names:
        e.append("ENTRY_EXECUTED")
    if "ENTRY_STATED" in names:
        e.append("ENTRY_STATED")
    if "OPERATOR_MONEY" in names:
        e.append("OPERATOR_MONEY_OBSERVED")
    if "PRESS" in names:
        if WAIT_PRESS.search(ntext):
            c.append("WAIT_FOR_PRESS")
        elif PAST_PRESS.search(ntext):
            e.append("PRESS_OBSERVED")
        else:
            c.append("PRESS_MENTION")
    if e and e_recalled:
        c.append("RECALLED_" + "+".join(e))         # حدثٌ مسترجَعٌ من زمنٍ أسبق ⟵ لا يُنسَب إلى يوم النشر
        e = []
    if not faisal:
        return dict(A="", B="", C="", E="", F="NON_FAISAL", tech=tech, recalled=recalled)
    f = "" if (A or b or c or e) else "UNKNOWN"
    return dict(A=A, B="+".join(b), C="+".join(c), E="+".join(e), F=f, tech=tech, recalled=recalled)


# ------------------------------------------------------------------ المصادر
def load_eye():
    if not os.path.exists(EYE):
        return {}
    d = json.load(open(EYE, encoding="utf-8"))
    return {r["id"]: r for r in d["reads"]}


def norm_sym(t):
    t = str(t or "").strip().upper().rstrip("?")
    if t in ("", "UNK", "UNKNOWN") or not re.fullmatch(r"[A-Z]{1,6}", t):
        return ""
    return t


def quotes_of(unit):
    """الاقتباساتُ الحرفيّة «…» من تفريغ V4 — مع وسم نصّ واجهة التطبيق (لا يُنسَب لفيصل)."""
    out = []
    for q in Q_RE.findall(unit.get("g") or ""):
        qs = q.strip()
        out.append((qs, "APP_UI" if qs in APP_UI else "SOURCE"))
    return out


def _event(u, author, ab, faisal, text, other, excerpt_src, ts, t, snap, er, st, dup):
    hits, ntext = lex(text)
    tsq, lo, hi, orig, ny, mismatch = ts
    con = concepts(hits, ntext, faisal, st)
    a_flag, a_basis = con["A"], ""
    sp = (st or {}).get("speaker", "")
    if sp == "APP_TAB":
        a_flag = ""                                          # عنوانُ التبويب نصُّ واجهة — العضويّةُ من الصفّ الظاهر وحدَه
    if snap and t and t in snap.get("visible_symbols", []):
        a_flag = "LIST_SNAPSHOT_VISIBLE"
        a_basis = f"tab «{snap['selected_tab']}» selected · {len(snap['visible_symbols'])} rows visible · other tabs {snap.get('other_tabs_contents', 'NOT SHOWN')}"
    eye_ok = bool(er) and bool(er.get("author_visible")) and sp in ("F", "APP_TAB")
    return dict(
        event_id="",
        identity=t,
        source_ref=u["id"],
        statement=(st or {}).get("key", "v4"),
        source_file=(er or {}).get("file") or _image_file(u["id"]),
        source_kind=(st or {}).get("channel") or u.get("k") or "",
        author=author,
        attribution_basis=ab,
        speaker=sp or "UNIT_AUTHOR (per-quote speaker not verified)",
        is_faisal=int(faisal),
        original_ts=orig,
        ny_ts=ny,
        capture_ts=(er or {}).get("capture_ts", ""),
        ts_quality=tsq,
        asof_lo=lo or "",
        asof_hi=hi or "",
        ts_flag=mismatch,
        excerpt=text,
        excerpt_other_speakers=other,
        excerpt_source=excerpt_src,
        v4_excerpt=" ‖ ".join(q for q, _ in quotes_of(u))[:400] if er else "",
        raw_label=" | ".join(f"«{h[2]}»" for h in hits if h[0] == "LABEL"),
        raw_label_class=" | ".join(h[1] for h in hits if h[0] == "LABEL"),
        raw_action=" | ".join(f"«{h[2]}»" for h in hits if h[0] == "ACTION"),
        raw_action_class=" | ".join(h[1] for h in hits if h[0] == "ACTION"),
        A_list=a_flag if (faisal or a_flag == "LIST_SNAPSHOT_VISIBLE") else "",
        A_basis=a_basis,
        B_stage="" if a_flag == "LIST_SNAPSHOT_VISIBLE" and sp == "APP_TAB" else con["B"],
        C_action="" if sp == "APP_TAB" else con["C"],
        E_trigger="" if sp == "APP_TAB" else con["E"],
        F_unknown="" if (a_flag or con["B"] or con["C"] or con["E"]) else (con["F"] or "UNKNOWN"),
        readiness_tech_qualified=int(con["tech"]),
        readiness_recalled=int(con["recalled"]),
        carry_forward=" | ".join(f"«{m}»" for m in _carry(text)),
        carry_forward_state=" | ".join(f"«{m}»" for m in _carry(text, STATE_CARRY)) if faisal else "",
        can_establish_membership=_membership(a_flag, snap, t),
        can_establish_transition=_transition_capable(hits, con),
        technical_only=int(bool(con["tech"]) and not (con["C"] or con["E"] or a_flag)) if faisal else 0,
        chart_only=int(not text),
        md_available=md_available(t, lo) if t else "N/A",
        identity_basis=(st or {}).get("identity_basis", "VISIBLE" if er and t else ("V4" if t else "")),
        duplicate_of=dup,
        v4_decision=u.get("dec") or "",
        v4_case=(er or {}).get("prospective_case") or u.get("case") or "",
        v4_rules=" | ".join(f"{r.get('eff')}: {r.get('txt')}" for r in (u.get("rules") or []))[:400],
        interpretation=_interpret(con, hits, st),
        eye_note=(er or {}).get("note", ""),
        evidence_class=_evidence_class(faisal, author, text, snap, sp),
        confidence=_confidence(faisal, ab, eye_ok, er, tsq),
        contradiction="",
    )


def unit_events(u, eye):
    """V4 ⟵ حدثٌ لكلّ (وحدة · رمز) من الاقتباسات «…» · وقراءةُ العين ⟵ حدثٌ لكلّ (عبارة · رمز) بطابع العبارة نفسِها.
    الوحدةُ/العبارةُ بلا رمزٍ حدثٌ عامٌّ (identity فارغة) إن حملت معجمًا."""
    er = eye.get(u["id"])
    author = (er or {}).get("author") or u.get("a") or "UNKNOWN"
    ab = "EYE_VERIFIED" if er and er.get("author_visible") else ((u.get("ab") or "NONE") if not er else "EYE_READ_AUTHOR_NOT_VISIBLE")
    evs = []
    if er:
        for st in er["statements"]:
            sp = st.get("speaker", "F")
            faisal = author in FAISAL_AUTHORS and sp in ("F", "APP_TAB")
            text = st["text"] if sp != "APP_TAB" else st["text"]
            if st.get("printed"):
                p = st["printed"]
                ts = timestamp(u.get("d"), (p["y"], p["m"], p["d"], p.get("hh"), p.get("mm"), p.get("ampm")))
            elif st.get("derived_ts"):
                dv = st["derived_ts"]
                q = dv["quality"] if dv.get("asof_lo") else "AMBIGUOUS"
                ts = (q, dv.get("asof_lo") or None, dv.get("asof_hi") or None, dv.get("original", ""), "", "")
            else:
                q, lo, hi, orig, ny, mm = timestamp(u.get("d"), None)
                ts = (q, lo, hi, orig, ny, "statement undated in the image; V4 unit date used")
            tickers = [norm_sym(x) for x in st.get("tickers") or []]
            if not tickers:
                if not lex(text)[0]:
                    continue
                tickers = [""]
            for t in tickers:
                evs.append(_event(u, author, ab, faisal, text, "", "EYE_2026-10-09", ts, t, st.get("list_snapshot"), er, st,
                                  st.get("duplicate_of", "")))
        return evs
    faisal = author in FAISAL_AUTHORS
    excerpts = quotes_of(u)
    text = " ‖ ".join(t for t, sp in excerpts if sp == "SOURCE")
    other = " ‖ ".join(f"[{sp}] {t}" for t, sp in excerpts if sp != "SOURCE")
    hits = lex(text)[0]
    ts = timestamp(u.get("d"), find_printed(u.get("g") or ""))
    tickers = [norm_sym(x) for x in (u.get("t") or [])]
    if not tickers or not any(tickers):
        if not hits:
            return []
        tickers = [""]
    for t in tickers:
        evs.append(_event(u, author, ab, faisal, text, other, "V4_TRANSCRIPTION", ts, t, None, None, None, u.get("dup_of") or ""))
    return evs


def _image_file(uid):
    for ext in (".jpg", ".png", ".jpeg", ".webp"):
        p = os.path.join("faisal_images", uid + ext)
        if os.path.exists(os.path.join(ROOT, p)):
            return p
    return ""


# إحالةٌ صريحةٌ إلى حالة انتباهٍ/جاهزيّةٍ/تحليلٍ سابقٍ لفيصل نفسِه على الرمز نفسِه (مادّةُ H3 · ضيّقةٌ ومحدَّدةٌ قبل أيّ مقارنة)
STATE_CARRY = re.compile(r"ذكرنا (متابع\w*|سابقا)|كان سهم متابعه|كان جاهز|(ما ?زال|لازال) تحت|تحليل سابق|ذاكره قبل|تم التحليل قبل|نعطيك سهم جاهز")


def _carry(text, rx=None):
    n, idx = norm_map(text)
    return [text[idx[m.start()]:idx[m.end() - 1] + 1] for m in (rx or CARRY).finditer(n)]


def _membership(a_flag, snap, t):
    if a_flag == "LIST_SNAPSHOT_VISIBLE":
        return "VISIBLE_TAB_ONLY"           # عضويّةُ التبويب الظاهر لحظةَ اللقطة — لا غيرُه ولا ما قبله وما بعده
    if a_flag == "ADD_TO_LIST_STATED":
        return "STATED_ADD"
    return "NO"


def _transition_capable(hits, con):
    names = {h[1] for h in hits}
    if "TRANSITION_WORD" in names and (con["B"] or con["A"]):
        return "STATED_RULE_OR_MOVE"
    if con["recalled"]:
        return "RECALLED_EARLIER_STATE"
    return "NO"


def _interpret(con, hits, st):
    parts = []
    if st and st.get("interpretation"):
        parts.append(st["interpretation"])
    if con["B"]:
        parts.append(f"readiness/stage vocabulary ({con['B']}){' — qualified technical' if con['tech'] else ''}{' — refers to an earlier time' if con['recalled'] else ''}")
    if "WAIT_FOR_PRESS" in con["C"]:
        parts.append("waits for operator pressure (not observed)")
    if "PRESS_OBSERVED" in con["E"]:
        parts.append("pressure described as having occurred")
    return " · ".join(parts)


def _evidence_class(faisal, author, text, snap, sp):
    if snap:
        return "LIST_SNAPSHOT"
    if author == "APP":
        return "APP_THIRD_PARTY"
    if not faisal:
        return "NON_FAISAL"
    if not text:
        return "CHART_ONLY"
    return "SOURCE_TEXT"


def _confidence(faisal, ab, eye_ok, er, tsq):
    """HIGH = مقروءٌ بالعين هنا والكاتبُ ظاهرٌ والمتكلّمُ فيصل · MEDIUM = تفريغُ V4 بكاتبٍ ظاهر أو قراءةُ عينٍ بكاتبٍ مستنتَج · LOW = غيرُه."""
    if not faisal:
        return "NOT_FAISAL"
    if eye_ok:
        return "HIGH"
    if er or ab in DIRECT_AB:
        return "MEDIUM"
    return "LOW"


def prospective_trace(eye):
    """نصُّ الحالات الأماميّة في قراءة العين = نصُّها المختوم في V4.1 (CASE_0001 النصّ ‏+ الردّ · CASE_0002/3 الاقتباس) — تتبّعٌ لا مصدرٌ ثانٍ."""
    out = {}
    b48 = json.load(open(B48, encoding="utf-8"))["cases"]["CASE_0001"]
    sealed = {"CASE_0001": b48["text"], "CASE_0002": json.load(open(os.path.join(REVEAL, "CASE_0002.json"), encoding="utf-8"))["quote"],
              "CASE_0003": json.load(open(os.path.join(REVEAL, "CASE_0003.json"), encoding="utf-8"))["quote"]}
    for img, r in sorted(eye.items()):
        cid = r.get("prospective_case")
        if cid:
            txt = r["statements"][0]["text"]
            out[cid] = sealed[cid] in txt
    return out


# ------------------------------------------------------------------ الحلقات والانتقالات
def episodes(events):
    """حلقةٌ = أحداثُ الرمز نفسِه التي تتقاطع نوافذُ أيّام قرارها (أو تشترك في حالةٍ مسمّاة) — لا يُحذف حدث."""
    by = {}
    for e in events:
        if e["identity"] and e["asof_lo"]:
            by.setdefault(e["identity"], []).append(e)
    eps = []
    for sym in sorted(by):
        evs = sorted(by[sym], key=lambda e: (e["asof_lo"], e["asof_hi"] or e["asof_lo"], e["event_id"]))
        cur = None
        for e in evs:
            hi = e["asof_hi"] or e["asof_lo"]
            if cur and (e["asof_lo"] <= cur["hi"] or (e["v4_case"] and e["v4_case"] in cur["cases"])):
                cur["events"].append(e)
                cur["hi"] = max(cur["hi"], hi)
                if e["v4_case"]:
                    cur["cases"].add(e["v4_case"])
            else:
                cur = dict(sym=sym, lo=e["asof_lo"], hi=hi, events=[e], cases={e["v4_case"]} if e["v4_case"] else set())
                eps.append(cur)
    for i, ep in enumerate(eps, 1):
        ep["id"] = f"EP{i:04d}"
        for e in ep["events"]:
            e["episode_id"] = ep["id"]
    return eps


def _ep_state(ep):
    """ما رُصد في الحلقة (فيصل وحدَه) — اتّحادُ المفاهيم المرصودة · وأفضلُ جودةِ طابع."""
    f = [e for e in ep["events"] if e["is_faisal"] or e["A_list"] == "LIST_SNAPSHOT_VISIBLE"]
    keys = {"A": set(), "B": set(), "C": set(), "E": set()}
    for e in f:
        for k, col in (("A", "A_list"), ("B", "B_stage"), ("C", "C_action"), ("E", "E_trigger")):
            for x in filter(None, (e[col] or "").split("+")):
                if k == "B" and e["readiness_recalled"]:
                    x = x + "(RECALLED)"
                keys[k].add(x)
    strict = any(e["ts_quality"] in ("EXACT_PRINTED", "EXACT_DATE_PRINTED", "EXACT_DERIVED") and e["confidence"] == "HIGH" for e in f)
    return keys, strict, f


def transitions(eps):
    """لكلّ زوجٍ متتالٍ من حلقات الرمز (بترتيب أيّام القرار لا أرقام الملفّات): ما رُصد قبلُ وبعدُ وحكمُ الانتقال.
    الفجوةُ ليست انتقالًا · والتاريخُ الدقيقُ للتغيّر مجهولٌ ما لم يُصرَّح به."""
    out = []
    by = {}
    for ep in eps:
        by.setdefault(ep["sym"], []).append(ep)
    for sym in sorted(by):
        seq = by[sym]
        for a, b in zip(seq, seq[1:]):
            ka, sa, fa = _ep_state(a)
            kb, sb, fb = _ep_state(b)
            if not fa or not fb:
                status, why = "UNKNOWN", "one side has no Faisal-attributed observation"
            else:
                ra = {x for x in ka["B"] if "RECALLED" not in x}
                rb = {x for x in kb["B"] if "RECALLED" not in x}
                pos_a = bool({"READY", "READY_100"} & ra); neg_a = "NOT_READY" in ra
                pos_b = bool({"READY", "READY_100"} & rb); neg_b = "NOT_READY" in rb
                stated = any(e["can_establish_transition"] != "NO" for e in fb)
                same = (ka == kb)
                if (pos_a and neg_a) or (pos_b and neg_b):
                    status, why = "CONTRADICTED", "READY and NOT_READY inside one episode window"
                elif stated:
                    status, why = "DIRECTLY_OBSERVED" if sb else "INFERRED", "later source states the move or recalls the earlier state"
                elif same:
                    status, why = "NO_CHANGE_OBSERVED", "same observed concepts on both occasions (continuity NOT claimed)"
                elif sa and sb and (ka["B"] or kb["B"]):
                    status, why = "STRONGLY_SUPPORTED", "two strict observations with different explicit labels; change date UNKNOWN"
                else:
                    status, why = "INFERRED", "observed concepts differ; timestamps or labels not strict"
            out.append(dict(identity=sym, from_episode=a["id"], to_episode=b["id"], from_window=f"{a['lo']}..{a['hi']}",
                            to_window=f"{b['lo']}..{b['hi']}", from_observed=_fmt(ka), to_observed=_fmt(kb),
                            from_strict=int(sa), to_strict=int(sb), status=status, why=why,
                            change_date="UNKNOWN (between windows)" if status in ("STRONGLY_SUPPORTED", "INFERRED") else ""))
    return out


def _fmt(k):
    return " ; ".join(f"{c}={'+'.join(sorted(v))}" for c, v in k.items() if v) or "NONE"


def contradictions(events):
    by = {}
    for e in events:
        if e["identity"] and e["is_faisal"] and e["asof_lo"]:
            by.setdefault(e["identity"], []).append(e)
    for sym, evs in by.items():
        for x in evs:
            notes = []
            if x["ts_flag"]:
                notes.append(x["ts_flag"])
            for y in evs:
                if y is x or not (x["asof_lo"] <= (y["asof_hi"] or y["asof_lo"]) and y["asof_lo"] <= (x["asof_hi"] or x["asof_lo"])):
                    continue
                xb = set((x["B_stage"] or "").split("+")) - {""}
                yb = set((y["B_stage"] or "").split("+")) - {""}
                if not x["readiness_recalled"] and not y["readiness_recalled"] and (
                        ("READY" in xb and "NOT_READY" in yb) or ("NOT_READY" in xb and "READY" in yb)):
                    notes.append(f"READY vs NOT_READY with {y['event_id']}")
            x["contradiction"] = " ; ".join(sorted(set(notes)))


# ------------------------------------------------------------------ المصالحةُ مع الخطّ الزمنيّ للمرحلة 3
def phase3_reconciliation(events):
    """كلُّ صفٍّ مرحليٍّ في FAISAL_TIMELINE (FOCUS/WATCH/READY/ENTRY) ⟵ ما يثبته المصدرُ فعلًا في هذا السجلّ."""
    idx = {}
    for e in events:
        idx.setdefault((e["source_ref"], e["identity"]), e)
    rows = []
    for r in csv.DictReader(open(P3, encoding="utf-8")):
        if r["FAISAL_STATE"] not in ("FOCUS", "WATCH", "READY", "ENTRY"):
            continue
        e = idx.get((r["EVIDENCE_ID"], r["TICKER"]))
        if not e:
            finding = "NO_LEDGER_EVENT"
        else:
            st = r["FAISAL_STATE"]
            if st == "FOCUS":
                finding = "LIST_MEMBERSHIP_ONLY (tab «قائمتي»; stage not shown)" if e["A_list"] == "LIST_SNAPSHOT_VISIBLE" else "FOCUS_WITHOUT_SOURCE_TERM"
            elif st == "READY":
                b = set(e["B_stage"].split("+"))
                if "READY" in b and not e["readiness_recalled"]:
                    finding = "EXPLICIT_READY_TERM" + (" (technical-qualified)" if e["readiness_tech_qualified"] else "")
                elif "READY" in b:
                    finding = "READY_TERM_RECALLED_EARLIER"
                elif e["E_trigger"]:
                    finding = f"NO_READY_TERM; source states {e['E_trigger']}"
                else:
                    finding = "NO_READY_TERM"
            elif st == "ENTRY":
                finding = f"SOURCE {e['E_trigger']}" if e["E_trigger"] else (f"PLAN_ONLY ({e['C_action']})" if "ENTRY_PLAN" in e["C_action"] else "NO_ENTRY_TERM_IN_VERBATIM")
            else:
                c = set(e["C_action"].split("+"))
                finding = "SOURCE_" + "+".join(sorted(c & {"WAIT", "MONITOR", "WAIT_FOR_PRESS"})) if c & {"WAIT", "MONITOR", "WAIT_FOR_PRESS"} else "NO_WAIT_OR_MONITOR_TERM_IN_VERBATIM"
        rows.append(dict(ticker=r["TICKER"], date=r["DATE"], evidence_id=r["EVIDENCE_ID"], phase3_state=r["FAISAL_STATE"],
                         decision_raw=r["DECISION_RAW"], event_id=(e or {}).get("event_id", ""), ts_quality=(e or {}).get("ts_quality", ""),
                         raw_label=(e or {}).get("raw_label", ""), raw_action=(e or {}).get("raw_action", ""), finding=finding))
    return rows


# ------------------------------------------------------------------ البناء
COLS = ["event_id", "identity", "identity_basis", "episode_id", "source_ref", "statement", "source_file", "source_kind", "author",
        "attribution_basis", "speaker", "is_faisal", "original_ts", "ny_ts", "capture_ts", "ts_quality", "asof_lo", "asof_hi", "ts_flag",
        "excerpt", "excerpt_other_speakers", "excerpt_source", "v4_excerpt", "duplicate_of", "raw_label", "raw_label_class", "raw_action", "raw_action_class", "A_list", "A_basis", "B_stage", "C_action",
        "E_trigger", "F_unknown", "readiness_tech_qualified", "readiness_recalled", "carry_forward", "carry_forward_state", "can_establish_membership",
        "can_establish_transition", "technical_only", "chart_only", "md_available", "v4_decision", "v4_case", "v4_rules",
        "interpretation", "eye_note", "evidence_class", "confidence", "contradiction"]


def build():
    eye = load_eye()
    units = [json.loads(line) for line in open(VP, encoding="utf-8")]
    seen = {u["id"] for u in units}
    events = []
    for u in sorted(units, key=lambda u: u["id"]):
        events += unit_events(u, eye)
    # صورُ ما بعد مرور V4 (دفعتا 48 و4 · والحالاتُ الأماميّة) المقروءةُ بالعين في هذه المهمّة
    for img in sorted(i for i in eye if i not in seen):
        u = {"id": img, "a": eye[img].get("author"), "d": None, "g": "", "t": [], "k": "post_v4_image", "dec": "", "rules": []}
        events += unit_events(u, eye)
    events.sort(key=lambda e: (e["identity"] == "", e["identity"], e["asof_lo"] or "9999", e["source_ref"]))
    for i, e in enumerate(events, 1):
        e["event_id"] = "SE" + hashlib.sha256(f"{e['source_ref']}|{e['statement']}|{e['identity']}".encode()).hexdigest()[:10]
        e.setdefault("episode_id", "")
    ids = [e["event_id"] for e in events]
    assert len(ids) == len(set(ids)), "duplicate event ids"
    eps = episodes(events)
    contradictions(events)
    trans = transitions(eps)
    recon = phase3_reconciliation(events)
    return events, eps, trans, recon


def summary(events, eps, trans, recon):
    f = [e for e in events if e["is_faisal"]]
    dated = [e for e in f if e["identity"] and e["asof_lo"]]
    cnt = lambda xs, k: dict(sorted(((v, sum(1 for x in xs if x[k] == v)) for v in {x[k] for x in xs})))  # noqa: E731
    strict_q = ("EXACT_PRINTED", "EXACT_DATE_PRINTED", "EXACT_DERIVED")
    s = dict(
        events_total=len(events),
        events_faisal=len(f),
        events_faisal_with_identity=sum(1 for e in f if e["identity"]),
        events_faisal_dated=len(dated),
        source_units_faisal_dated=len({e["source_ref"] for e in dated}),
        symbols_faisal_dated=len({e["identity"] for e in dated}),
        episodes_total=len(eps),
        episodes_with_faisal=sum(1 for ep in eps if any(e["is_faisal"] for e in ep["events"])),
        ts_quality_faisal=cnt(f, "ts_quality"),
        strict_timestamp_events=sum(1 for e in dated if e["ts_quality"] in strict_q and e["confidence"] == "HIGH"),
        direct_list_state_events=sum(1 for e in events if e["can_establish_membership"] != "NO"),
        direct_list_snapshot_events=sum(1 for e in events if e["A_list"] == "LIST_SNAPSHOT_VISIBLE"),
        explicit_readiness_events=sum(1 for e in dated if any(x in (e["B_stage"] or "") for x in ("READY", "READINESS", "UNDER", "SORT"))),
        explicit_readiness_not_recalled=sum(1 for e in dated if (e["B_stage"] and not e["readiness_recalled"])),
        technical_only_events=sum(1 for e in dated if e["technical_only"]),
        chart_only_events=sum(1 for e in dated if e["chart_only"]),
        unknown_events=sum(1 for e in dated if e["F_unknown"]),
        carry_forward_events=sum(1 for e in dated if e["carry_forward"]),
        carry_forward_symbols=sorted({e["identity"] for e in dated if e["carry_forward"]}),
        carry_forward_state_events=sum(1 for e in f if e["identity"] and e["carry_forward_state"]),
        carry_forward_state_symbols=sorted({e["identity"] for e in f if e["identity"] and e["carry_forward_state"]}),
        ambiguous_ts_faisal=sum(1 for e in f if e["ts_quality"] == "AMBIGUOUS"),
        concept_counts=dict(
            A_list=cnt([e for e in dated if e["A_list"]], "A_list"),
            B_stage=cnt([e for e in dated if e["B_stage"]], "B_stage"),
            C_action=sum(1 for e in dated if e["C_action"]),
            E_trigger=cnt([e for e in dated if e["E_trigger"]], "E_trigger")),
        transitions=cnt(trans, "status"),
        phase3_rows=len(recon),
        phase3_symbols=len({r["ticker"] for r in recon}),
        phase3_findings=cnt(recon, "finding"),
        eye_reads=len(load_eye()),
        eye_statements=sum(len(r["statements"]) for r in load_eye().values()),
        prospective_text_matches_sealed=prospective_trace(load_eye()),
        timezone_assumption="printed X/Telegram times read as device time in Asia/Riyadh (UTC+3) — stated assumption",
    )
    return s


def _csv(path, rows, cols):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write(out=OUT):
    os.makedirs(out, exist_ok=True)
    events, eps, trans, recon = build()
    _csv(os.path.join(out, "stage_events.csv"), events, COLS)
    eprows = []
    for ep in eps:
        k, strict, f = _ep_state(ep)
        eprows.append(dict(episode_id=ep["id"], identity=ep["sym"], asof_lo=ep["lo"], asof_hi=ep["hi"], n_events=len(ep["events"]),
                           n_faisal=len(f), events=" ".join(e["event_id"] for e in ep["events"]),
                           sources=" ".join(sorted({e["source_ref"] for e in ep["events"]})), observed=_fmt(k), strict=int(strict)))
    _csv(os.path.join(out, "stage_episodes.csv"), eprows, list(eprows[0]))
    _csv(os.path.join(out, "stage_transitions.csv"), trans, list(trans[0]) if trans else ["identity"])
    _csv(os.path.join(out, "stage_phase3_reconciliation.csv"), recon, list(recon[0]))
    s = summary(events, eps, trans, recon)
    with open(os.path.join(out, "stage_ledger_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(s, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    return s


FILES = ("stage_events.csv", "stage_episodes.csv", "stage_transitions.csv", "stage_phase3_reconciliation.csv", "stage_ledger_summary.json")


def check(out=None):
    """يعيد التوليد في مجلّدٍ مؤقّت ويقارن البصمات بالملتزَم ⟵ قائمةُ ما اختلف ([] = حتميّ)."""
    bad = []
    with tempfile.TemporaryDirectory(prefix="stage_ledger_") as tmp:
        write(tmp)
        for f in FILES:
            a = hashlib.sha256(open(os.path.join(tmp, f), "rb").read()).hexdigest()
            p = os.path.join(out or OUT, f)
            b = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
            if a != b:
                bad.append(f)
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = check()
        print("✅ regenerated identically" if not bad else f"❌ differs: {bad}")
        sys.exit(1 if bad else 0)
    s = write()
    print(json.dumps(s, ensure_ascii=False, indent=1))
