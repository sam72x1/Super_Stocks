#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔁 T-REPLAY10 — إعادة تشغيل أمينة لآلة القائمة الحيّة.

**السبب:** المراجعة الخصومية أثبتت أن `backtest_portfolio` **يستبعد `outcome=="no_fill"`
قبل تخصيص السعة** — و`outcome` لا يُعرف وقت الإشارة ⇒ **نظرٌ مستقبليّ**. وأن سعتَه 15
بينما الإنتاج 10، وأنه يحرّر الخانة **بأيامٍ تقويمية لا جلسات**.

**هذي الوحدة تُصلح الثلاثة**، والمواصفات مثبَّتة في `replay10_prereg.md` §②:

  • **لا استبعاد مسبق:** كل مرشّحٍ مختار يحجز خانةً من تاريخ إشارته.
  • **السعة 10 = سقف الاختيار الجديد**؛ المحمولون (`carried`) لا يُحتسبون ضدّها.
  • **الوقف ⇒ يُزال** · **الهدف ⇒ يحرّر الخانة ويبقى متابَعًا** · النافذة ⇒ يُزال.
  • **الزمن بجلسات** (فهرس الجلسة) لا `ordinals` تقويمية.
  • **لا خانتان لرمزٍ واحد** متزامنًا.

🔒 **بحث/قياس فقط — خارج مسار الفرز والإنتاج.** دوالّ نقيّة بلا I/O ولا شبكة؛
الجالبات تُحقَن. لا تُستورَد في `Super_stock.py`.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

CAPACITY = 10          # سقف الاختيار الجديد (= WATCHLIST_SIZE الحيّ)

# أسباب الإزالة — مفردات ثابتة تُقارَن بالحيّ في البوّابة أ
R_STOP = "stopped"
R_WINDOW = "window"
R_HIT_HELD = "hit_held"        # بلغ هدفًا: يحرّر الخانة ويبقى محمولًا


@dataclass(frozen=True)
class Candidate:
    """مرشّحٌ ليومٍ واحد. `session` = **فهرس الجلسة** لا تاريخ تقويميّ."""
    session: int
    symbol: str
    readiness: float | None = None
    h4_confirm: float = 0.0
    score: float = 0.0
    rr: float = 0.0
    seq: int = 0                # ترتيب الظهور الأصليّ (لـFIFO وكسر التعادل الحتميّ)
    payload: dict = field(default_factory=dict, compare=False)


@dataclass
class Holding:
    symbol: str
    entered: int                # جلسة الدخول
    holds_slot: bool = True     # هل يحجز خانةً من السعة؟
    reason: str | None = None   # سبب المغادرة (يُملأ عند الخروج)


# ─────────────────────────── المُرتِّبات (الأذرع) ───────────────────────────
def rank_actual(c: Candidate):
    """R0 — المُرتِّب الفعليّ: readiness → h4_confirm → score → rr.
    ⚠️ `h4_confirm` = 0 تاريخيًّا **وحيًّا** (يُحسب في `enrich` بعد `select_top`)،
    وهذا مُعلَن في التسجيل المسبق §② ولا يُدَّعى تمثيلُه."""
    rdy = c.readiness
    return (-(rdy if rdy is not None else -1.0), -c.h4_confirm, -c.score, -c.rr, c.seq)


def rank_fifo(c: Candidate):
    """R1 — الأقدم إشارةً أولًا (شاهد ضبط)."""
    return (c.seq,)


def make_rank_random(seed: int) -> Callable[[Candidate], tuple]:
    """R2 — عشوائيّ **حتميّ** بالبذرة: ترتيبٌ ثابتٌ لكل (بذرة، رمز، جلسة).
    يُبنى بالتجزئة لا بمولّدٍ عام ⇒ **قابل لإعادة الإنتاج** ومستقلٌّ عن ترتيب النداء."""
    def _key(c: Candidate):
        h = hashlib.sha256(f"{seed}|{c.session}|{c.symbol}".encode()).digest()
        return (int.from_bytes(h[:8], "big"), c.seq)
    return _key


# ─────────────────────────── آلة الحالة ───────────────────────────
def replay(
    candidates: Iterable[Candidate],
    *,
    outcome_of: Callable[[Candidate], tuple[str, int]],
    ranker: Callable[[Candidate], tuple] = rank_actual,
    capacity: int = CAPACITY,
    sessions: Iterable[int] | None = None,
) -> dict:
    """يُعيد تشغيل آلة القائمة جلسةً بجلسة.

    `outcome_of(c)` → `(reason, sessions_held)` حيث `reason ∈ {stopped, hit_held,
    window}` و`sessions_held` **عدد الجلسات** من الدخول حتى الحدث. **يُستدعى فقط
    بعد أن تُختار الصفقة** — فلا يدخل نتيجتَه أيُّ قرار تخصيص (إصلاح `P0-01`).

    `sessions` (اختياريّ) = **فهرس الجلسات الكامل**؛ يُمرَّر ليكون `daily` كثيفًا
    (لبوّابة الصلاحية). ⚠️ **والخروجات تُصرَّف بشرط `≤ s` لا `== s`** — لأن الحدث قد
    يقع في جلسةٍ **بلا مرشّحين**، فمطابقةُ التساوي كانت تُبقي الاسم محجوزًا للأبد
    (عيبٌ حقيقيّ أمسكه القفل ③ عند أول تشغيل).

    يرجّع: `taken` · `rejected_cap` · `rejected_dup` · `daily` (العضوية لكل جلسة) ·
    `slot_days` (مجموع أيام إشغال الخانات) · `max_size` (أقصى حجم قائمة).
    """
    by_session: dict[int, list[Candidate]] = {}
    for c in candidates:
        by_session.setdefault(c.session, []).append(c)

    live: dict[str, Holding] = {}
    exits: dict[int, list[str]] = {}       # جلسة الخروج → رموز
    frees: dict[int, list[str]] = {}       # جلسة تحرير الخانة (الهدف) → رموز
    taken, rej_cap, rej_dup = [], 0, 0
    daily: dict[int, tuple[str, ...]] = {}
    slot_days = 0

    order = sorted(set(sessions) | set(by_session)) if sessions is not None \
        else sorted(by_session)
    for s in order:
        # ① أخرج ما انتهى **قبل** قرار اليوم — بشرط `≤ s` لا `== s` (الحدث قد يقع
        #    في جلسةٍ بلا مرشّحين، فالمطابقة بالتساوي تحجز الخانة أبدًا)
        for k in [k for k in exits if k <= s]:
            for sym in exits.pop(k):
                live.pop(sym, None)
        for k in [k for k in frees if k <= s]:
            for sym in frees.pop(k):
                h = live.get(sym)
                if h is not None:
                    h.holds_slot = False    # الهدف يحرّر الخانة والاسم يبقى محمولًا

        # ② خصّص السعة على مرشّحي اليوم — **بلا أيّ معرفةٍ بنتيجتهم**
        used = sum(1 for h in live.values() if h.holds_slot)
        for c in sorted(by_session.get(s, ()), key=ranker):
            if c.symbol in live:
                rej_dup += 1
                continue
            if used >= capacity:
                rej_cap += 1
                continue
            live[c.symbol] = Holding(c.symbol, entered=s)
            used += 1
            taken.append(c)
            # ③ الآن فقط تُقرأ النتيجة — لجدولة الخروج لا للاختيار
            reason, held = outcome_of(c)
            end = s + max(int(held), 0)
            if reason == R_HIT_HELD:
                frees.setdefault(end, []).append(c.symbol)
            else:
                exits.setdefault(end, []).append(c.symbol)
            live[c.symbol].reason = reason

        daily[s] = tuple(sorted(live))
        slot_days += sum(1 for h in live.values() if h.holds_slot)

    return {
        "taken": taken, "rejected_cap": rej_cap, "rejected_dup": rej_dup,
        "daily": daily, "slot_days": slot_days,
        "max_size": max((len(v) for v in daily.values()), default=0),
        "capacity": capacity,
    }


# ─────────────────────────── بوّابة الصلاحية أ ───────────────────────────
def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """تطابق مجموعتين. مجموعتان فارغتان ⇒ 1.0 (اتفاقٌ تامّ على الفراغ)."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def gate_a(observed: dict[int, Sequence[str]], produced: dict[int, Sequence[str]]) -> dict:
    """**البوّابة أ (حاكمة):** تُغذّى الآلة بتيّار الأحداث المرصود من التاريخ الحيّ،
    فيجب أن تُعيد إنتاج العضوية اليومية. العتبة المسجَّلة: **متوسط Jaccard ≥ 0.95**.
    ترجّع التفاصيل يومًا بيوم ليُنشَر أضعفُها لا المتوسط وحده."""
    days = sorted(set(observed) | set(produced))
    per = {d: jaccard(observed.get(d, ()), produced.get(d, ())) for d in days}
    mean = (sum(per.values()) / len(per)) if per else 0.0
    return {
        "per_day": per, "mean": mean, "n_days": len(per),
        "worst": min(per.values()) if per else 0.0,
        "passed": bool(per) and mean >= 0.95,
        "threshold": 0.95,
    }


# ─────────────────────── جسر صفقات المحرّك → مرشّحي الإعادة ───────────────────────
def session_index(dates: Iterable[str]) -> dict[str, int]:
    """تاريخ ISO → **فهرس جلسة**. الفهرس = موضع التاريخ في **اتّحاد تواريخ الدخول
    والخروج مرتَّبةً تصاعديًّا**.

    ⚖️ **ولماذا يكفي هذا بدل تقويم تداولٍ كامل:** آلة الحالة لا تسأل إلا «في هذي
    اللحظة، مَن ما زال حيًّا؟» — والاسم حيٌّ من تاريخ دخوله حتى تاريخ خروجه. فما دام
    **كل** تاريخ دخولٍ وخروجٍ ممثَّلًا بنقطةٍ في الفهرس، فترتيب الأحداث — وبالتالي
    المزاحمة على السعة — **يُحفَظ بدقّة**. الأيام الخالية من أيّ حدثٍ لا تغيّر شيئًا،
    فطيّها لا يُفقد معلومة. (والمدد المطبوعة «جلسات فهرسية» لا أيامَ تقويم.)"""
    return {d: i for i, d in enumerate(sorted({str(d) for d in dates if d}))}


def r_unit(trade: dict) -> float | None:
    """عائد الصفقة **بوحدة المخاطرة** من عائد التنفيذ الفعليّ (`ret_a`) — لا إعادة
    بناءٍ اسمية (إصلاح `P0-05`). المخاطرة = `(دخول − وقف)/دخول`، فالوقف يساوي −1R
    بالضبط، ويصير «صافي R» قابلًا للجمع عند حجمٍ ثابت المخاطرة.

    **غير المُعبَّأة ⇒ 0.0** (لا تنفيذ **لكنها استهلكت خانة** — والكلفة تظهر في
    المقام وفي إزاحتها لغيرها، وهذا بعينه ما يقيسه إصلاح `P0-01`)."""
    try:
        e, s = float(trade["entry"]), float(trade["stop"])
    except (TypeError, ValueError, KeyError):
        return None
    if e <= 0 or e - s <= 0:
        return None
    ret = trade.get("ret_a")
    if ret is None:
        return 0.0
    try:
        return float(ret) / ((e - s) / e * 100.0)
    except (TypeError, ValueError):
        return None


def candidates_from_trades(trades: Sequence[dict]) -> tuple[list, dict, Callable]:
    """يبني `(مرشّحون، فهرس الجلسات، outcome_of)` من صفقات محرّك الباكتيست.

    **تُشترط الحقول** `date` و`exit_date` (يضيفهما `BT_REPLAY10`) — وغيابُها يعني أن
    العلم كان **خاملًا**، فتُرجَع قائمةٌ فارغة ويُكتشَف ذلك صراحةً بدل تفسير صفرٍ
    مفبرك (قاعدة «أثبت أن التجربة اشتغلت» قبل تفسير أيّ نتيجة).

    **الترتيب الأصليّ `seq`** يُبنى من `(التاريخ، الرمز)` فيكون **حتميًّا** مستقلًّا عن
    ترتيب ورود الصفقات ⇒ FIFO وكسر التعادل قابلان لإعادة الإنتاج."""
    rows = [t for t in trades if t.get("date") and t.get("exit_date")]
    idx = session_index([t["date"] for t in rows] + [t["exit_date"] for t in rows])
    rows = sorted(rows, key=lambda t: (str(t["date"]), str(t.get("symbol") or "")))
    cands = [
        Candidate(session=idx[str(t["date"])], symbol=str(t.get("symbol") or ""),
                  readiness=t.get("readiness"), score=float(t.get("score") or 0.0),
                  rr=float(t.get("rr") or 0.0), seq=i, payload=t)
        for i, t in enumerate(rows)
    ]

    def outcome_of(c: Candidate):
        t = c.payload
        held = max(idx[str(t["exit_date"])] - idx[str(t["date"])], 0)
        oc = t.get("outcome")
        if oc == "win":
            return (R_HIT_HELD, held)      # بلغ هدفًا: يحرّر الخانة ويبقى متابَعًا
        if oc == "loss":
            return (R_STOP, held)
        return (R_WINDOW, held)            # `open`/`no_fill`: يُزال بانتهاء النافذة

    return cands, idx, outcome_of


def net_r_per_day(taken: Sequence[Candidate], n_sessions: int) -> float:
    """**المقياس الأساسيّ المسجَّل:** صافي R لليوم عند إجمالي مخاطرةٍ ثابت."""
    if n_sessions <= 0:
        return 0.0
    tot = sum(v for v in (r_unit(c.payload) for c in taken) if v is not None)
    return tot / float(n_sessions)


# ─────────────────────── الاستدلال المسجَّل ───────────────────────
def _pct(vals: Sequence[float], q: float) -> float:
    if not vals:
        return 0.0
    xs = sorted(vals)
    k = min(max(int(round(q * (len(xs) - 1))), 0), len(xs) - 1)
    return xs[k]


def block_bootstrap_ci(taken: Sequence[Candidate], sess_of_month: dict,
                       n: int = 10000, seed: int = 12345,
                       level: float = 0.95) -> dict:
    """**‏`block bootstrap` بالكتلة الشهرية:** تُعاد معاينة **الأشهر** بالإحلال (لا
    الصفقات) — فيُحترَم ارتباط صفقات الشهر الواحد. الإحصاء = `مجموع R ÷ مجموع
    الجلسات` على الأشهر المعادة، فيبقى «صافي R/يوم» بلا انحياز مقام."""
    by_month: dict[str, float] = {m: 0.0 for m in sess_of_month}
    for c in taken:
        m = str(c.payload.get("date"))[:7]
        v = r_unit(c.payload)
        if v is not None and m in by_month:
            by_month[m] += v
    months = sorted(sess_of_month)
    if not months:
        return {"lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        pick = [months[rng.randrange(len(months))] for _ in months]
        den = sum(sess_of_month[m] for m in pick)
        out.append((sum(by_month[m] for m in pick) / den) if den else 0.0)
    a = (1.0 - level) / 2.0
    return {"lo": _pct(out, a), "hi": _pct(out, 1.0 - a), "n": len(months)}


def cluster_bootstrap_ci(taken: Sequence[Candidate], n_sessions: int,
                         n: int = 10000, seed: int = 54321,
                         level: float = 0.95) -> dict:
    """**‏`cluster` بالرمز:** تُعاد معاينة **الرموز** بالإحلال (صفقات الرمز الواحد
    مرتبطة). المقام يبقى عدد الجلسات الفعليّ."""
    by_sym: dict[str, float] = {}
    for c in taken:
        v = r_unit(c.payload)
        if v is not None:
            by_sym[c.symbol] = by_sym.get(c.symbol, 0.0) + v
    syms = sorted(by_sym)
    if not syms or n_sessions <= 0:
        return {"lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(seed)
    out = [sum(by_sym[syms[rng.randrange(len(syms))]] for _ in syms) / n_sessions
           for _ in range(n)]
    a = (1.0 - level) / 2.0
    return {"lo": _pct(out, a), "hi": _pct(out, 1.0 - a), "n": len(syms)}


def randomization_test(observed: float, null_draws: Sequence[float]) -> dict:
    """**‏`randomization inference`:** توزيعُ العدم = أذرع R2 (ترتيبٌ عشوائيّ داخل
    متنافسي اليوم نفسه). يرجّع `p` أحادية (كسر العيّنات التي بلغت المرصود فأكثر)
    و`p` ثنائية، وفاصل ‏90% لفرق `(المرصود − العشوائيّ)` — وهو الفاصل الذي يُقارَن
    بهامش التكافؤ المسجَّل ‏±0.05R/يوم."""
    if not null_draws:
        return {"p_one": 1.0, "p_two": 1.0, "d_lo": 0.0, "d_hi": 0.0, "n": 0}
    ge = sum(1 for v in null_draws if v >= observed)
    le = sum(1 for v in null_draws if v <= observed)
    n = len(null_draws)
    p_one = (ge + 1) / (n + 1)
    diffs = [observed - v for v in null_draws]
    return {"p_one": p_one, "p_two": min(1.0, 2.0 * min(ge + 1, le + 1) / (n + 1)),
            "d_lo": _pct(diffs, 0.05), "d_hi": _pct(diffs, 0.95),
            "d_mean": sum(diffs) / n, "n": n}
