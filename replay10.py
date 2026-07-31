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
