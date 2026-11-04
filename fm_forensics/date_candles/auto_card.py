# -*- coding: utf-8 -*-
"""🕯️🤖 بطاقةُ شموعٍ آليّة من صورة (`T_DATE_CANDLES_ADDENDUM_2.md §③`) — قراءةٌ فقط · بلا شبكة · بلا تاريخ.

الصورةُ ⟵ **المعايرة** من خطوط فيصل المرسومة: كلُّ خطٍّ أفقيٍّ طويلٍ بلونه (`detect_lines`) يقابل الرقمَ الذي قرأه سجلُّ العين
لذلك اللون (`parse_lines` على `seen`) بترتيبه ⟵ ثلاثةُ أزواجٍ فأكثر ومطابقةٌ خطّيّةٌ أو لوغاريتميّة **بخطأٍ لا يتجاوز بكسلين**
(`CAL_TOL_PX`) ⟵ وإلّا «معايرةٌ لم تُتحقَّق» ولا بطاقة (لا يُخمَّن).
⟵ **الشموع** بقارئ البكسل (`chart_pixels.candle_masks` بعتباته كما هي) ⟵ مكوّناتٌ متّصلة ⟵ شكلُ شمعة (عرضُ الجسم = عرضُ
الإطار · مراكزُ الصفوف على عمودٍ واحد) ⟵ عنقودُ اللوحة الرأسيّ ⟵ حذفُ الحجم (قاعدةٌ مشتركة) ⟵ **شبكةٌ أفقيّة منتظمة** (خطوةُ
الشمعة) ⟵ شمعةٌ لكلّ موضع (والمفقودُ `None` يُقنَّع في المطابقة لا يُملأ).
⟵ البطاقة: الشموعُ بالسعر **كما ظهر على الشاشة يومَ اللقطة** (خامٌ قبل أيّ تقسيمٍ لاحق) · وتسامحُ كلِّ قيمةٍ بكسلان.

🔒 لا شبكة · لا كتابةَ إلّا ملفّ البطاقة · لا تاريخَ يُقرأ ولا يُكتب في البطاقة (التاريخُ ناتجُ المطابقة وحدَها).
"""
from __future__ import annotations

import collections
import itertools
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import chart_pixels as P  # noqa: E402  (بُنيت لـمُعرِّف الشارت: أقنعةُ الشموع ومعايرةُ المحور)

CARD_VERSION = 1        # v1 (الملحق 2) — بطاقاتُه في data/cards.jsonl مجمَّدة والافتراضُ هو هو
CARD_V2 = 2             # v2 (الملحق 3 §④) — data/cards_v2.jsonl
# ── العتبات (هندسيّة · مكتوبةٌ في الملحق 2 §③ قبل أيّ تشغيلٍ على المجتمع) ────────────────────────────
LINE_FRAC = 0.50        # خطٌّ مرسوم = جريانٌ أفقيٌّ متّصلٌ بلونه لا يقلّ عن نصف عرض الصورة
CAL_MIN_PAIRS = 3       # أزواجُ المعايرة: ثلاثةٌ فأكثر (اثنان يعرّفان الخطّ ولا يتحقّقان منه)
CAL_TOL_PX = 2.0        # أقصى خطأ المعايرة بالبكسل (= تسامحُ `chart_pixels.pixel_summary` الافتراضيّ px_tol=2)
MAX_CANDLE_W = 40       # أعرضُ شمعة (بكسل) — ما فوقه وسمُ محورٍ أو مستطيلُ نصّ
CSTD_MAX = 1.0          # انحرافُ مراكز صفوف المكوّن (بكسل) — الشمعةُ عمودٌ واحد · والسهمُ المرسوم مائل
CLUSTER_GAP_FRAC = 0.04  # فجوةٌ رأسيّةٌ فارغة لا تقلّ عن 4% من ارتفاع الصورة تفصل عنقودَ اللوحة عمّا فوقه وتحته
VOL_BASE_MIN = 5        # قاعدةُ الحجم: خمسةُ مكوّناتٍ فأكثر تشترك في أدنى صفٍّ (±1 بكسل)
LATTICE_RES = 0.35      # أقصى بعد مركز الشمعة عن موضعها في الشبكة (نسبةٌ من الخطوة)
MIN_BARS = 10           # أدنى شموعٍ حاضرة في البطاقة
MIN_COVER = 0.60        # أدنى نسبةٍ للحاضر من مدى الشبكة (أوّلُ موضعٍ ⟵ آخرُه)
MIN_STEP_PX = 2.0       # أصغرُ خطوةِ شمعةٍ تُفصل بها الشموع
MAX_GAP_BARS = 3        # أكثرُ من 3 مواضعَ فارغةٍ متتالية تقطع التسلسل ⟵ تُختار القطعةُ الأكثرُ شموعًا (وما بعدها شظايا وسومٍ لا شموع)

COLOR_WORDS = {
    "purple": ("بنفسج",),
    "black": ("أسود", "سوداء", "سود"),
    "blue": ("أزرق", "زرقاء", "زرق"),
    "red": ("أحمر", "حمراء", "حمر"),
    "green": ("أخضر", "خضراء", "خضر"),
    "yellow": ("أصفر", "صفراء", "صفر"),
    "orange": ("برتقال",),
}
HUE = {  # درجاتُ التدرّج لكلّ لون (والأسودُ بالقيمة لا بالتدرّج)
    "red": ((345.0, 360.0), (0.0, 15.0)),
    "orange": ((15.0, 45.0),),
    "yellow": ((45.0, 70.0),),
    "green": ((70.0, 175.0),),
    "blue": ((175.0, 250.0),),
    "purple": ((250.0, 345.0),),
}
_NUM = r"\d+(?:\.\d+)?"
_DIAC = "ً-ْٰـ"          # تشكيلٌ وتطويل
_NUM_LIST = re.compile(r"^[\s" + _DIAC + r"]*(?:[^\s\d·()]{0,8}[\s" + _DIAC + r"]+)?((?:" + _NUM
                       + r")(?:\s*(?:/|و|،|,(?!\d{3}))\s*" + _NUM + r")*)")
# ── القارئ v2 (الملحق 3 §④ — كلُّ تغييرٍ من سببٍ رأته العينُ في 3 صورٍ فأكثر من عيّنة الثلاثين · والافتراضُ v1 بت-بت) ──
_NUM_LIST_V2 = re.compile(r"^[\s" + _DIAC + r"]*(?:[^\s\d·()]{0,8}[\s" + _DIAC + r"]+)?((?:" + _NUM
                          + r")(?:(?:\s*(?:/|و|،|,(?!\d{3}))\s*|\s+)" + _NUM + r"(?![\d%@]))*)")
COLOR_WORDS_V2 = dict(COLOR_WORDS, purple=("بنفسج", "ورد"), blue=("أزرق", "زرقاء", "زرق", "فيروز", "كحل"))
V2_LINE_FRAC = 0.30     # R9: الشارتُ داخل لقطةٍ أعرض (منشور · قناة) فخطُّه أقصرُ من نصف عرض الصورة (مِجَسّ: TG_81003 ‏0.40 · IMG_8126 ‏0.46)
V2_MAX_PAIRS = 60       # أزواجٌ مرشَّحة (لون × رقم) فوقها لا بحث — حدُّ زمن
V2_HL = (re.compile(r"قم+[ّ]?[ةه][ًٌٍَُِّْ]*\s+(" + _NUM + r")(?![\d%@])"),
         re.compile(r"قاع[ًٌٍَُِّْ]*\s+(" + _NUM + r")(?![\d%@])"))   # R13: «قمّة X · قاع Y» وسما التطبيق لأعلى ذيلٍ وأدنى ذيل
V2_PIECE_GAP = 3        # R11/R7: قطعٌ في موضعٍ واحدٍ بينها أكثرُ من 3 بكسل (أو نصفُ الخطوة) ليست شمعةً واحدة (نصٌّ · سهم · وسم)
V2_WICK_SAT, V2_WICK_VAL = 0.10, 0.20   # R11: الذيلُ الرفيع في صورةٍ مضغوطة يفقد تشبّعَه (القناعُ 0.30) — يُتتبَّع في عمود الجسم وحدَه


def parse_lines(seen: str, version: int = 1) -> dict:
    """نصُّ سجلّ العين ⟵ {لون: [أرقامُ خطوطه بترتيب ورودها]} — الرقمُ يُقبل فقط إن **تلا كلمةَ اللون مباشرةً** (بعد تشكيلٍ أو
    كلمةٍ واحدة مثل «خطوطٌ زرقاء» أو «عند») · وما بعد «@» (طلب/عرض) أو «%» ليس خطًّا.
    و`version=2` (الملحق 3 §④): الأرقامُ المفصولة بمسافة («أسود 3.444 3.008») تُقرأ كلُّها · وكلماتُ ألوانٍ يكتبها سجلُّ العين
    لتدرّجٍ في القناع نفسِه (ورديّ ⟵ بنفسجيّ · فيروزيّ وكحليّ ⟵ أزرق)."""
    out = collections.defaultdict(list)
    words_of = COLOR_WORDS_V2 if version >= 2 else COLOR_WORDS
    num_list = _NUM_LIST_V2 if version >= 2 else _NUM_LIST
    for seg in re.split(r"[·|\n]", seen or ""):
        for col, words in words_of.items():
            for w in words:
                hit = False
                for m in re.finditer(w, seg):
                    tail = seg[m.end():]
                    mm = num_list.match(tail)
                    if not mm:
                        continue
                    nums = re.findall(_NUM, mm.group(1))
                    after = tail[mm.end(1):mm.end(1) + 1]
                    if after in ("%", "@"):
                        continue
                    out[col].extend(float(x) for x in nums)
                    hit = True
                if hit:
                    break                                    # «أزرق» و«زرقاء» لا يُعدّان مرّتين على المقطع نفسِه
    return {k: v for k, v in out.items() if v}


def _runs(row: np.ndarray):
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


LINE_SAT_MIN = 0.12     # الخطُّ الرفيع في صورةٍ مضغوطة يفقد تشبّعَه (مِجَسّ: أزرقُ TG_1806 تشبّعُه 0.26-0.31) · والشبكةُ رماديّةٌ ≈0
LINE_RUN_FRAC = 0.15    # وأطولُ جريانٍ فيه لا يقلّ عن 15% من العرض (الشموعُ تقطع الخطَّ فلا يُشترط جريانٌ واحدٌ بنصف العرض)
BLACK_V_MAX, BLACK_S_MAX = 0.50, 0.25   # مِجَسّ: الأسودُ الرفيع في IMG_0363 قيمتُه 0.40-0.58 · والخلفيّةُ 0.93-1.0


def color_masks(rgb: np.ndarray) -> dict:
    h, s, v = P.rgb_to_hsv(rgb)
    sat = (s >= LINE_SAT_MIN) & (v >= P.VAL_MIN)
    out = {c: sat & P._in_ranges(h, rng) for c, rng in HUE.items()}
    out["black"] = (v < BLACK_V_MAX) & (s < BLACK_S_MAX)
    return out


def detect_lines(rgb: np.ndarray, frac: float = LINE_FRAC) -> dict:
    """{لون: [y مركزُ كلِّ خطٍّ مرسوم]} — صفوفٌ يغطّي لونُها `frac` من العرض فأكثر **وفيها جريانٌ متّصلٌ** لا يقلّ عن `LINE_RUN_FRAC`
    · والصفوفُ المتجاورة (فجوةٌ لا تتجاوز صفّين) خطٌّ واحد (خطوطُ فيصل تعبر العرضَ كلَّه حتى وسمِها على المحور)."""
    H, W = rgb.shape[:2]
    need = int(math.ceil(frac * W))
    run_need = int(math.ceil(LINE_RUN_FRAC * W))
    out = {}
    for col, m in color_masks(rgb).items():
        rows = []
        for y in range(H):
            r = m[y]
            tot = int(r.sum())
            if tot < need:
                continue
            best = max((e - s for s, e in _runs(r)), default=0)
            if best >= run_need:
                rows.append(y)
        ys, grp = [], []
        for y in rows:
            if grp and y - grp[-1] > 2:
                ys.append(sum(grp) / len(grp))
                grp = []
            grp.append(y)
        if grp:
            ys.append(sum(grp) / len(grp))
        if ys:
            out[col] = ys
    return out


def _fit(pairs: list):
    """أزواجُ (y، سعر) ⟵ (f, is_log, err_px) بأصغر خطأٍ بين الخطّيّ واللوغاريتميّ · والخطأُ بالبكسل: أقصى |y المتوقَّع − y|."""
    ys = np.array([p[0] for p in pairs], dtype=float)
    ps = np.array([p[1] for p in pairs], dtype=float)
    best = (None, None, math.inf)
    for use_log in (False, True):
        if use_log and not (ps > 0).all():
            continue
        tgt = np.log(ps) if use_log else ps
        if np.ptp(tgt) <= 0:
            continue
        A = np.vstack([tgt, np.ones_like(tgt)]).T                    # y = a·سعر + b (الخطأُ بالبكسل مباشرة)
        a, b = np.linalg.lstsq(A, ys, rcond=None)[0]
        if not a < 0:                                                # الأعلى على الشاشة سعرٌ أكبر
            continue
        err = float(np.max(np.abs(a * tgt + b - ys)))
        if err < best[2]:
            f = (lambda y, a=a, b=b: float(math.exp((y - b) / a))) if use_log else \
                (lambda y, a=a, b=b: float((y - b) / a))
            best = (f, use_log, err)
    return best


def calibrate_lines(lines_px: dict, lines_val: dict):
    """أزواجُ (y، سعر) من الألوان التي **يتساوى فيها عددُ الخطوط المرصودة وعددُ أرقامها** (بالترتيب: الأعلى على الشاشة = الأكبر)
    ⟵ أكبرُ مجموعةِ ألوانٍ تتّسق أزواجُها (ثلاثةٌ فأكثر · خطأٌ لا يتجاوز `CAL_TOL_PX`) — فلونٌ عدُّه مصادفةٌ (سهمٌ أخضر وحدُّ
    شريط الطلب) يُستبعد ولا يُفسد المعايرة · والتعادلُ بأصغر خطأ ⟵ (f, is_log, err_px, pairs) أو (None, None, err, pairs)."""
    groups = []
    for col, ys in sorted(lines_px.items()):
        vals = sorted(set(lines_val.get(col) or []), reverse=True)
        if vals and len(vals) == len(ys):
            groups.append(list(zip(sorted(ys), vals)))
    best, best_err = None, math.inf
    for k in range(len(groups), 0, -1):
        for sub in itertools.combinations(groups, k):
            pairs = [p for g in sub for p in g]
            if len(pairs) < CAL_MIN_PAIRS:
                continue
            f, is_log, err = _fit(pairs)
            if f is None:
                continue
            if err <= CAL_TOL_PX and (best is None or len(pairs) > len(best[3])
                                      or (len(pairs) == len(best[3]) and err < best[2])):
                best = (f, is_log, err, pairs)
            best_err = min(best_err, err)
    if best is None:
        allp = [p for g in groups for p in g]
        return None, None, best_err, allp
    return best


def _fit_line(pairs: list, use_log: bool):
    """أزواجُ (y، سعر) ⟵ (a, b) لـ y = a·سعر + b (أو a·log سعر + b) بالمربّعات الصغرى · أو None."""
    ys = np.array([p[0] for p in pairs], dtype=float)
    ps = np.array([p[1] for p in pairs], dtype=float)
    if use_log and not (ps > 0).all():
        return None
    tgt = np.log(ps) if use_log else ps
    if np.ptp(tgt) <= 0:
        return None
    A = np.vstack([tgt, np.ones_like(tgt)]).T
    a, b = np.linalg.lstsq(A, ys, rcond=None)[0]
    return (a, b) if a < 0 else None


def calibrate_v2(lines_px: dict, lines_val: dict, hl: list = ()):
    """الملحق 3 §④ (R4 · R6 · R9 · R13): المرشَّحون = كلُّ (y خطٍّ مرصود، رقمٌ من لونه) ‏+ مرشَّحا القمّة/القاع `hl` [(y، سعر)] —
    **فلا يُشترط تساوي العدد** (خطٌّ زائدٌ من خلفيّةٍ أو خطٌّ مخفيٌّ لا يُسقط اللون) ⟵ لكلّ زوجين من رقمين مختلفين نموذجٌ خطّيٌّ
    ولوغاريتميّ ⟵ المتوافقون معه: لكلّ رقمٍ أقربُ y مرشَّحٍ له ضمن `CAL_TOL_PX` بلا تكرار y ⟵ الأكثرُ عددًا (ثمّ الأصغرُ خطأً)
    ⟵ مطابقةٌ نهائيّة على المتوافقين **وخطؤها لا يتجاوز `CAL_TOL_PX` وعددُهم 3 فأكثر** (القاعدتان كما هما · لا إرخاء)."""
    cands = []
    for col, ys in lines_px.items():
        for v in sorted(set(lines_val.get(col) or []), reverse=True):
            for y in ys:
                cands.append((float(y), float(v), col))
    for y, v in hl:
        cands.append((float(y), float(v), "hl"))
    if len(cands) > V2_MAX_PAIRS:
        cands = cands[:V2_MAX_PAIRS]
    vals = sorted({c[1] for c in cands})
    best = None
    for (y1, p1, _c1), (y2, p2, _c2) in itertools.combinations(cands, 2):
        if p1 == p2 or y1 == y2:
            continue
        for use_log in (False, True):
            ab = _fit_line([(y1, p1), (y2, p2)], use_log)
            if ab is None:
                continue
            a, b = ab
            used_y, inl = set(), []
            for v in vals:
                yp = a * (math.log(v) if use_log else v) + b
                opts = sorted((abs(c[0] - yp), c[0]) for c in cands if c[1] == v and c[0] not in used_y)
                if opts and opts[0][0] <= CAL_TOL_PX:
                    used_y.add(opts[0][1])
                    inl.append((opts[0][1], v))
            if len(inl) < CAL_MIN_PAIRS:
                continue
            ab2 = _fit_line(inl, use_log)
            if ab2 is None:
                continue
            a2, b2 = ab2
            err = max(abs(a2 * (math.log(v) if use_log else v) + b2 - y) for y, v in inl)
            key = (len(inl), -err)
            if err <= CAL_TOL_PX and (best is None or key > best[0]):
                best = (key, use_log, a2, b2, err, sorted(inl))
    if best is None:
        return None, None, math.inf, [(c[0], c[1]) for c in cands]
    _k, use_log, a, b, err, inl = best
    f = (lambda y, a=a, b=b: float(math.exp((y - b) / a))) if use_log else (lambda y, a=a, b=b: float((y - b) / a))
    return f, use_log, float(err), inl


def high_low_values(seen: str) -> tuple:
    """R13: «قمّة X» و«قاع Y» في نصّ سجلّ العين (وسما التطبيق لأعلى ذيلٍ وأدنى ذيلٍ ظاهرَين) ⟵ (X أو None، Y أو None) · وتكرارُ
    أحدِهما بقيمتين ⟵ None له (لا يُختار)."""
    out = []
    for rx in V2_HL:
        v = {float(x) for x in rx.findall(seen or "")}
        out.append(v.pop() if len(v) == 1 else None)
    return tuple(out)


def components(mask: np.ndarray) -> list:
    """مكوّناتٌ متّصلة (جوارٌ ثمانيّ) ⟵ [{x0,x1,y0,y1,npx,maxw,cstd,rows}] — `rows` = [(y, s, e)] جرياناتُ المكوّن."""
    parent = []

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    rows_all, prev = [], []
    for y in range(mask.shape[0]):
        cur = []
        if mask[y].any():
            for s, e in _runs(mask[y]):
                rid = len(parent)
                parent.append(rid)
                cur.append((int(s), int(e), rid))
                for ps, pe, pid in prev:
                    if ps <= e and s <= pe:
                        ra, rb = find(rid), find(pid)
                        if ra != rb:
                            parent[ra] = rb
        rows_all.append(cur)
        prev = cur
    comps = collections.defaultdict(list)
    for y, cur in enumerate(rows_all):
        for s, e, rid in cur:
            comps[find(rid)].append((y, s, e))
    out = []
    for runs in comps.values():
        width = collections.defaultdict(int)
        cen = collections.defaultdict(list)
        for y, s, e in runs:
            width[y] += e - s
            cen[y].append((s + e - 1) / 2.0)
        out.append({"x0": min(r[1] for r in runs), "x1": max(r[2] for r in runs) - 1,
                    "y0": min(r[0] for r in runs), "y1": max(r[0] for r in runs),
                    "npx": sum(e - s for _, s, e in runs), "maxw": max(width.values()),
                    "cstd": float(np.std([np.mean(v) for v in cen.values()])), "rows": runs})
    return out


def candle_like(c: dict) -> bool:
    w = c["x1"] - c["x0"] + 1
    return (c["npx"] >= 2 and w <= MAX_CANDLE_W and c["maxw"] >= w - 1 and c["cstd"] <= CSTD_MAX)


def _clusters(items: list, gap: float) -> list:
    """عناقيدُ رأسيّة: فتراتُ [y0، y1] المتداخلة أو التي بينها أقلُّ من `gap` ⟵ [[عناصر]]."""
    out, cur, hi = [], [], -math.inf
    for c in sorted(items, key=lambda c: c["y0"]):
        if cur and c["y0"] - hi > gap:
            out.append(cur)
            cur, hi = [], -math.inf
        cur.append(c)
        hi = max(hi, c["y1"])
    if cur:
        out.append(cur)
    return out


def _drop_volume(cs: list, key: str = "y1") -> tuple:
    """قاعدةُ الحجم: أدنى صفٍّ مشتركٍ (±1) بين `VOL_BASE_MIN` مكوّناتٍ فأكثر في أسفل العنقود ⟵ يُحذف ما يلامسها.
    و`key="wy1"` (v2): القاعدةُ بأسفل الذيل المتتبَّع — فشموعٌ تُغلق على السعر نفسِه بذيولٍ باهتة ليست أعمدةَ حجم."""
    if not cs:
        return cs, 0
    bots = collections.Counter(c[key] for c in cs)
    ymax = max(bots)
    base = [y for y in bots if y >= ymax - 1]
    n = sum(bots[y] for y in base)
    if n < VOL_BASE_MIN:
        return cs, 0
    keep = [c for c in cs if c[key] < ymax - 1]
    return keep, len(cs) - len(keep)


def _drop_contained(cs: list, wide: list) -> tuple:
    """ما يقع داخل إطار مكوّنٍ عريض (وسمُ سعرٍ على المحور · مستطيلُ نصٍّ ملوّن) ليس شمعة ⟵ يُحذف."""
    keep = [c for c in cs if not any(w["x0"] <= c["x0"] and c["x1"] <= w["x1"] and w["y0"] <= c["y0"]
                                     and c["y1"] <= w["y1"] for w in wide)]
    return keep, len(cs) - len(keep)


def _drop_dashes(cs: list) -> tuple:
    """خطٌّ متقطّع (خطُّ السعر الحاليّ): `VOL_BASE_MIN` قطعٍ فأكثر بارتفاعٍ لا يتجاوز 3 بكسل **تتطابق صفوفُها أعلى وأسفل** ⟵ تُحذف."""
    g = collections.Counter((c["y0"], c["y1"]) for c in cs if c["y1"] - c["y0"] <= 2)
    bad = {k for k, n in g.items() if n >= VOL_BASE_MIN}
    keep = [c for c in cs if (c["y0"], c["y1"]) not in bad]
    return keep, len(cs) - len(keep)


def lattice(cs: list):
    """مراكزُ x ⟵ (x0, الخطوة, [(موضع، مكوّن)]) — الخطوةُ الأوّليّة وسيطُ الفروق المتتالية (2 بكسل فأكثر) · ثمّ **تسلسلُ المواضع
    بالفروق المتتالية** (كلُّ فرقٍ يُقرَّب إلى أقرب مضاعفٍ للخطوة) فلا ينجرف الخطأُ على طول الشارت · ثمّ مطابقةٌ بالمربّعات الصغرى
    على الكلّ (مرّتين) · والمكوّنُ البعيدُ عن موضعه أكثرَ من `LATTICE_RES` خطوةٍ يُسقط."""
    xs = sorted({(c["x0"] + c["x1"]) / 2.0 for c in cs})
    d = [b - a for a, b in zip(xs, xs[1:]) if b - a >= MIN_STEP_PX]
    if len(d) < 3:
        return None
    step = float(np.median(d))
    if step < MIN_STEP_PX:
        return None
    idx = [0]
    for a, b in zip(xs, xs[1:]):
        idx.append(idx[-1] + max(0, int(round((b - a) / step))))
    xa, ia = np.array(xs, dtype=float), np.array(idx, dtype=float)
    ok = np.ones(len(xa), dtype=bool)
    x0 = xa[0]
    for _ in range(3):
        if ok.sum() < 3 or len(set(ia[ok])) < 2:
            return None
        A = np.vstack([ia[ok], np.ones(int(ok.sum()))]).T
        step, x0 = [float(v) for v in np.linalg.lstsq(A, xa[ok], rcond=None)[0]]
        if step < MIN_STEP_PX:
            return None
        ia = np.round((xa - x0) / step)
        ok = np.abs(xa - (x0 + ia * step)) <= LATTICE_RES * step
    out = []
    for c in cs:
        xc = (c["x0"] + c["x1"]) / 2.0
        i = round((xc - x0) / step)
        if abs(xc - (x0 + i * step)) <= LATTICE_RES * step:
            out.append((int(i), c))
    return x0, step, out


def _best_segment(bars: list) -> tuple:
    """أطولُ قطعةٍ بلا فجوةٍ فارغةٍ أطولَ من `MAX_GAP_BARS` (بعدد الشموع الحاضرة · والتعادلُ للأيمن: آخرُ الشارت هو اللقطة)
    ⟵ (القطعة، عددُ المواضع المحذوفة بعدها) — والمحذوفُ قبلها لا يُعَدّ (النافذةُ تبدأ حيث تبدأ القطعة)."""
    segs, cur, gap = [], [], 0
    for i, b in enumerate(bars):
        if b is None:
            gap += 1
            if gap > MAX_GAP_BARS and cur:
                segs.append(cur)
                cur = []
            continue
        if not cur:
            gap = 0
        cur.append(i)
        gap = 0
    if cur:
        segs.append(cur)
    if not segs:
        return bars, 0
    best = max(segs, key=lambda g: (len(g), g[-1]))
    a, b = best[0], best[-1]
    return bars[a:b + 1], len(bars) - 1 - b


def _bar(pieces: list, f):
    """قطعُ موضعٍ واحدٍ بلونٍ واحد ⟵ شمعة {o,h,l,c,up} بالسعر: الذيلُ أعلى/أدنى بكسل · والجسمُ الصفوفُ التي يغطّيها 60% من عرضه."""
    up = pieces[0]["up"]
    rows = collections.defaultdict(int)
    for c in pieces:
        for y, s, e in c["rows"]:
            rows[y] += e - s
    ys = sorted(rows)
    w = max(rows.values())
    body = [y for y in ys if rows[y] >= P.BODY_COVER * w] if w >= 3 else ys
    body = body or ys
    hi, lo = f(ys[0]), f(ys[-1])
    bt, bb = f(min(body)), f(max(body))
    o, cl = (bb, bt) if up else (bt, bb)
    return {"o": o, "h": max(hi, lo), "l": min(hi, lo), "c": cl, "up": up,
            "y_top": int(ys[0]), "y_bot": int(ys[-1])}


def build_card(rgb: np.ndarray, seen: str, version: int = 1) -> dict:
    """صورةٌ ‏+ نصُّ سجلّ عينها ⟵ {"ok": True, …البطاقة} أو {"ok": False, "why": السبب, …التشخيص}.
    `version=2` ⟵ القارئ v2 (`build_card_v2` · الملحق 3 §④) · والافتراضُ v1 بت-بت (الملحق 2 · بطاقاتُه مجمَّدة)."""
    if version >= 2:
        return build_card_v2(rgb, seen)
    H, W = rgb.shape[:2]
    vals = parse_lines(seen)
    if sum(len(v) for v in vals.values()) < CAL_MIN_PAIRS:
        return {"ok": False, "why": "أرقامُ خطوطٍ في سجلّ العين أقلُّ من ثلاثة", "line_vals": vals}
    lines = detect_lines(rgb)
    f, is_log, err, pairs = calibrate_lines(lines, vals)
    diag = {"line_vals": vals, "lines_px": {k: [round(y, 1) for y in v] for k, v in lines.items()},
            "pairs": [(round(y, 1), p) for y, p in pairs]}
    if f is None and len(pairs) < CAL_MIN_PAIRS:
        return {"ok": False, "why": "أزواجُ معايرةٍ متطابقةُ العدد أقلُّ من ثلاثة", **diag}
    if f is None:
        return {"ok": False, "why": f"المعايرةُ لم تُتحقَّق (أصغرُ خطأ {err:.2f} بكسل فوق {CAL_TOL_PX})",
                "cal_err_px": err, **diag}
    up, dn = P.candle_masks(rgb)
    cs, wide = [], []
    for m, is_up in ((up, True), (dn, False)):
        for c in components(m):
            if candle_like(c):
                c["up"] = is_up
                cs.append(c)
            elif c["x1"] - c["x0"] + 1 > MAX_CANDLE_W:
                wide.append(c)
    cs, n_boxed = _drop_contained(cs, wide)
    cs, n_dash = _drop_dashes(cs)
    y_lines = [y for y, _ in pairs]
    cl = _clusters(cs, CLUSTER_GAP_FRAC * H)
    lo_l, hi_l = min(y_lines), max(y_lines)
    pick = [k for k in cl if min(c["y0"] for c in k) <= hi_l and max(c["y1"] for c in k) >= lo_l]
    if not pick:
        return {"ok": False, "why": "لا عنقودَ شموعٍ يقطع مدى خطوط المعايرة", **diag}
    panel = [c for k in pick for c in k]
    panel, n_vol = _drop_volume(panel)
    lat = lattice(panel)
    if lat is None:
        return {"ok": False, "why": "لا شبكةَ أفقيّةً منتظمة للشموع", **diag}
    x0, step, placed = lat
    by = collections.defaultdict(list)
    for i, c in placed:
        by[i].append(c)
    i_min, i_max = min(by), max(by)
    bars, conflict = [], 0
    for i in range(i_min, i_max + 1):
        pcs = by.get(i)
        if not pcs:
            bars.append(None)
            continue
        if len({c["up"] for c in pcs}) > 1:
            conflict += 1
            bars.append(None)
            continue
        bars.append(_bar(pcs, f))
    bars, cut = _best_segment(bars)
    present = sum(b is not None for b in bars)
    cover = present / float(len(bars))
    out = {"v": CARD_VERSION, "log": bool(is_log), "cal_err_px": round(err, 3), "step_px": round(step, 3),
           "x0_px": round(x0, 2), "n_bars": len(bars), "n_present": present, "cover": round(cover, 3),
           "n_conflict": conflict, "n_volume_dropped": n_vol, "n_boxed_dropped": n_boxed,
           "n_dash_dropped": n_dash, "cut_after": cut, **diag}
    if present < MIN_BARS:
        return {"ok": False, "why": f"شموعٌ حاضرةٌ {present} دون {MIN_BARS}", **out}
    if cover < MIN_COVER:
        return {"ok": False, "why": f"تغطيةُ الشبكة {cover:.0%} دون {MIN_COVER:.0%}", **out}
    tol = [None if b is None else {k: _px_tol(f, b, k) for k in ("o", "h", "l", "c")} for b in bars]
    out["bars"] = [None if b is None else {k: round(b[k], 6) for k in ("o", "h", "l", "c")} | {"up": b["up"]}
                   for b in bars]
    out["tol"] = [None if t is None else {k: round(v, 6) for k, v in t.items()} for t in tol]
    out["ok"] = True
    return out


def _wick_mask(rgb: np.ndarray, lines_px: dict):
    """R11: قناعا الذيل المرخى (صاعد · هابط) بتدرّج الشموع نفسِه وتشبّعٍ `V2_WICK_SAT` وقيمةٍ `V2_WICK_VAL` ⟵ وصفوفُ الخطوط المرسومة
    (‏±1) تُعلَّم فلا يُحسب الخطُّ ذيلًا."""
    h, s, v = P.rgb_to_hsv(rgb)
    col = (s >= V2_WICK_SAT) & (v >= V2_WICK_VAL)
    line_rows = np.zeros(rgb.shape[0], dtype=bool)
    for ys in lines_px.values():
        for y in ys:
            line_rows[max(0, int(math.floor(y)) - 1):int(math.ceil(y)) + 2] = True
    return col & P._in_ranges(h, P.UP_HUES), col & P._in_ranges(h, P.DOWN_HUES), line_rows


def _extend_wick(mask: np.ndarray, line_rows: np.ndarray, xc: float, y_top: int, y_bot: int) -> tuple:
    """يُتتبَّع الذيلُ في عمود الجسم (‏±1) فوق `y_top` وتحت `y_bot`: يمضي ما دام بكسلُ الذيل حاضرًا · ويقفز صفًّا واحدًا فارغًا
    أو صفوفَ خطٍّ مرسوم إن تلاها ذيلٌ · ولا يُحسب صفُّ الخطّ نفسُه طرفًا ⟵ (y_top، y_bot) الجديدان."""
    H, W = mask.shape
    xs = [x for x in (int(round(xc)) - 1, int(round(xc)), int(round(xc)) + 1) if 0 <= x < W]

    def hit(y):
        return 0 <= y < H and not line_rows[y] and bool(mask[y, xs].any())

    def walk(y0, dy):
        y, last = y0, y0
        while True:
            nxt = y + dy
            if hit(nxt):
                y = last = nxt
                continue
            jump = nxt
            while 0 <= jump < H and line_rows[jump]:
                jump += dy
            for cand in (jump, jump + dy):
                if hit(cand):
                    y = last = cand
                    break
            else:
                return last
    return walk(y_top, -1), walk(y_bot, +1)


def _groups(pcs: list, step: float) -> list:
    """قطعُ الموضع الواحد ⟵ مجموعاتٌ متّصلةٌ رأسيًّا (فجوةٌ لا تتجاوز `V2_PIECE_GAP` أو نصفَ الخطوة)."""
    gap = max(V2_PIECE_GAP, 0.5 * step)
    groups, cur, lo = [], [], None
    for c in sorted(pcs, key=lambda c: c["y0"]):
        if cur and c["y0"] - lo > gap:
            groups.append(cur)
            cur = []
        lo = c["y1"] if not cur else max(lo, c["y1"])
        cur.append(c)
    if cur:
        groups.append(cur)
    return groups


def _pick_groups(by: dict, step: float) -> tuple:
    """R7/R11: الموضعُ بمجموعةٍ واحدة يُحفظ كما هو · والموضعُ بأكثر (نصٌّ · سهم · وسمٌ فوق الشمعة أو تحتها) تُختار مجموعتُه الأقربُ
    مركزًا رأسيًّا إلى متوسّط أقرب جارَين وحيدَي المجموعة يمينًا ويسارًا (السعرُ متّصلٌ من شمعةٍ لجارتها) — ولا جارَ ⟵ الأكثرُ بكسلًا
    ⟵ ({موضع: قطع}، عددُ القطع المُسقطة)."""
    gs = {i: _groups(p, step) for i, p in by.items()}
    cen = lambda g: (min(c["y0"] for c in g) + max(c["y1"] for c in g)) / 2.0      # noqa: E731
    single = sorted(i for i, g in gs.items() if len(g) == 1)
    out, dropped = {}, 0
    for i, g in gs.items():
        if len(g) == 1:
            out[i] = g[0]
            continue
        left = [j for j in single if j < i][-1:]
        right = [j for j in single if j > i][:1]
        nb = [cen(gs[j][0]) for j in left + right]
        if nb:
            ref = sum(nb) / len(nb)
            best = min(g, key=lambda gg: abs(cen(gg) - ref))
        else:
            best = max(g, key=lambda gg: sum(c["npx"] for c in gg))
        out[i] = best
        dropped += sum(len(gg) for gg in g) - len(best)
    return out, dropped


def _line_span(rgb: np.ndarray, lines_px: dict, pairs: list):
    """R6/R9: المدى الأفقيّ لخطوط المعايرة المرسومة ⟵ لكلّ خطٍّ جرياناتُ لونه في صفّه تُدمج عبر فجواتٍ لا تتجاوز
    `max(MAX_CANDLE_W, 5% من العرض)` (الشموعُ تقطع الخطّ) ⟵ عمودٌ يدخل المدى إن غطّاه **نصفُ الخطوط فأكثر** (خطوطُ فيصل تعبر الشارتَ
    كلَّه · فخطٌّ مقطوعٌ أو خطٌّ يلتحق بخلفيّةٍ ملوّنة لا يحرّك المدى وحدَه) ⟵ أطولُ قطعةٍ متّصلة ⟵ (x_أيسر، x_أيمن) · أو None
    (المعايرةُ من القمّة/القاع وحدَهما · أو مدًى أضيقُ من 20% من العرض)."""
    W = rgb.shape[1]
    gap = max(MAX_CANDLE_W, 0.05 * W)
    masks = color_masks(rgb)
    cover, n = np.zeros(W, dtype=int), 0
    for y, _p in pairs:
        for col, ys in lines_px.items():
            if not any(abs(y - yy) < 0.01 for yy in ys):
                continue
            segs = []
            for s0, e0 in _runs(masks[col][int(round(y))]):
                if segs and s0 - segs[-1][1] <= gap:
                    segs[-1][1] = e0
                else:
                    segs.append([s0, e0])
            if segs:
                s0, e0 = max(segs, key=lambda t: t[1] - t[0])
                cover[s0:e0] += 1
                n += 1
            break
    if n == 0:
        return None
    ok = cover * 2 >= n
    runs = _runs(ok)
    if not runs:
        return None
    s0, e0 = max(runs, key=lambda t: t[1] - t[0])
    if e0 - s0 < 0.20 * W:
        return None
    return int(s0), int(e0)


def build_card_v2(rgb: np.ndarray, seen: str) -> dict:
    """القارئ v2 (الملحق 3 §④): كـ`build_card` v1 إلّا — ① الأرقامُ بمسافة وكلماتُ الألوان الإضافيّة (`parse_lines(…, 2)`) ·
    ② الخطُّ ‏30% من العرض (`V2_LINE_FRAC`) · ③ المعايرةُ بلا شرط تساوي العدد ومعها وسما القمّة/القاع (`calibrate_v2` — 3 أزواجٍ ·
    بكسلان كما هما) · ④ قطعُ الموضع الواحد غيرُ المتّصلة: تبقى المجموعةُ الأقربُ إلى جارتيها (`_pick_groups`) · ⑤ الذيلُ يُتتبَّع بقناعٍ مرخًى في عمود الجسم
    (`_extend_wick`). والبوّابةُ البنيويّة (10 شموع · تغطية 60%) بلا تغيير."""
    H, W = rgb.shape[:2]
    vals = parse_lines(seen, 2)
    hi_v, lo_v = high_low_values(seen)
    n_nums = sum(len(v) for v in vals.values()) + (hi_v is not None) + (lo_v is not None)
    if n_nums < CAL_MIN_PAIRS:
        return {"ok": False, "why": "أرقامُ خطوطٍ وقمّةٍ وقاعٍ في سجلّ العين أقلُّ من ثلاثة", "line_vals": vals, "v": CARD_V2}
    lines = detect_lines(rgb, V2_LINE_FRAC)
    up, dn = P.candle_masks(rgb)
    cs, wide = [], []
    for m, is_up in ((up, True), (dn, False)):
        for c in components(m):
            if candle_like(c):
                c["up"] = is_up
                cs.append(c)
            elif c["x1"] - c["x0"] + 1 > MAX_CANDLE_W:
                wide.append(c)
    cs, n_boxed = _drop_contained(cs, wide)
    cs, n_dash = _drop_dashes(cs)
    wm_up, wm_dn, line_rows = _wick_mask(rgb, lines)
    for c in cs:
        xc = (c["x0"] + c["x1"]) / 2.0
        c["wy0"], c["wy1"] = _extend_wick(wm_up if c["up"] else wm_dn, line_rows, xc, c["y0"], c["y1"])
    cl = _clusters(cs, CLUSTER_GAP_FRAC * H)
    hl = []
    for k in cl:
        if len(k) >= MIN_BARS:
            if hi_v is not None:
                hl.append((min(c["wy0"] for c in k), hi_v))
            if lo_v is not None:
                hl.append((max(c["wy1"] for c in k), lo_v))
    f, is_log, err, pairs = calibrate_v2(lines, vals, hl)
    diag = {"v": CARD_V2, "line_vals": vals, "hl_vals": [hi_v, lo_v],
            "lines_px": {k: [round(y, 1) for y in v] for k, v in lines.items()},
            "pairs": [(round(y, 1), p) for y, p in pairs]}
    if f is None:
        return {"ok": False, "why": "المعايرةُ لم تُتحقَّق (لا ثلاثةُ أزواجٍ متّسقة ضمن بكسلين)", **diag}
    y_lines = [y for y, _ in pairs]
    lo_l, hi_l = min(y_lines), max(y_lines)
    span = _line_span(rgb, lines, pairs)
    diag["x_span"] = span
    cs_in = cs if span is None else [c for c in cs if span[0] <= (c["x0"] + c["x1"]) / 2.0 <= span[1]]
    # R9: الشارتُ الصغيرُ داخل لقطةٍ طويلة ⟵ فجوةُ العنقود من ارتفاعٍ لا يتجاوز ضعفَ عرض الشارت (وإلّا يلتحق الحجمُ بالشموع)
    gap_h = H if span is None else min(H, 2 * (span[1] - span[0]))
    cl_in = _clusters(cs_in, CLUSTER_GAP_FRAC * gap_h)
    pick = [k for k in cl_in if min(c["y0"] for c in k) <= hi_l and max(c["y1"] for c in k) >= lo_l]
    if not pick:
        return {"ok": False, "why": "لا عنقودَ شموعٍ يقطع مدى خطوط المعايرة", **diag}
    panel = [c for k in pick for c in k]
    panel, n_vol = _drop_volume(panel, key="wy1")
    lat = lattice(panel)
    if lat is None:
        return {"ok": False, "why": "لا شبكةَ أفقيّةً منتظمة للشموع", **diag}
    x0, step, placed = lat
    by = collections.defaultdict(list)
    for i, c in placed:
        by[i].append(c)
    i_min, i_max = min(by), max(by)
    picked, n_dropped_pieces = _pick_groups(by, step)
    bars, conflict = [], 0
    for i in range(i_min, i_max + 1):
        main = picked.get(i)
        if not main:
            bars.append(None)
            continue
        if len({c["up"] for c in main}) > 1:
            conflict += 1
            bars.append(None)
            continue
        b = _bar(main, f)
        yt = min(min(c["wy0"] for c in main), b["y_top"])
        yb = max(max(c["wy1"] for c in main), b["y_bot"])
        if yt < b["y_top"] or yb > b["y_bot"]:
            hi, lo = f(yt), f(yb)
            b.update({"h": max(hi, lo, b["h"]), "l": min(hi, lo, b["l"]), "y_top": int(yt), "y_bot": int(yb)})
        bars.append(b)
    n_full = len(bars)
    bars, cut = _best_segment(bars)
    present = sum(b is not None for b in bars)
    cover = present / float(len(bars))
    out = {**diag, "i0": i_min + n_full - cut - len(bars), "log": bool(is_log), "cal_err_px": round(err, 3), "step_px": round(step, 3), "x0_px": round(x0, 2),
           "n_bars": len(bars), "n_present": present, "cover": round(cover, 3), "n_conflict": conflict,
           "n_volume_dropped": n_vol, "n_boxed_dropped": n_boxed, "n_dash_dropped": n_dash,
           "n_pieces_dropped": n_dropped_pieces, "cut_after": cut}
    if present < MIN_BARS:
        return {"ok": False, "why": f"شموعٌ حاضرةٌ {present} دون {MIN_BARS}", **out}
    if cover < MIN_COVER:
        return {"ok": False, "why": f"تغطيةُ الشبكة {cover:.0%} دون {MIN_COVER:.0%}", **out}
    tol = [None if b is None else {k: _px_tol(f, b, k) for k in ("o", "h", "l", "c")} for b in bars]
    out["bars"] = [None if b is None else {k: round(b[k], 6) for k in ("o", "h", "l", "c")} | {"up": b["up"]}
                   for b in bars]
    out["tol"] = [None if t is None else {k: round(v, 6) for k, v in t.items()} for t in tol]
    out["ok"] = True
    return out


def _px_tol(f, b, k):
    """تسامحُ القيمة = `CAL_TOL_PX` بكسل × سعرُ البكسل عندها (خطّيٌّ أو لوغاريتميّ) — كتسامح `pixel_summary`."""
    y = b["y_top"] if k == "h" else b["y_bot"] if k == "l" else None
    if y is None:
        y = (b["y_top"] + b["y_bot"]) / 2.0
    return CAL_TOL_PX * abs(f(y + 1) - f(y))


if __name__ == "__main__":
    import json
    recs = {}
    for ln in open(os.path.join(REPO, "fm_forensics", "reread", "data", "reread_records.jsonl"), encoding="utf-8"):
        ln = ln.strip()
        if ln:
            r = json.loads(ln)
            recs[r["id"]] = r
    for p in sys.argv[1:]:
        iid = os.path.splitext(os.path.basename(p))[0]
        card = build_card(P.load_rgb(p), recs[iid]["seen"])
        print(iid, {k: v for k, v in card.items() if k not in ("bars", "tol")})
