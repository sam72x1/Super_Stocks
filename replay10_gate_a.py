#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚦 T-REPLAY10 — **البوّابة أ**: أمانة آلة الحالة (`replay10_prereg.md` §③).

**الفكرة:** تُغذّى الآلة بـ**تيّار الأحداث المرصود من التاريخ الحيّ نفسه** (لقطات
`weekly_watchlist.json` في git)، ثم **يجب أن تُعيد إنتاج العضوية اليومية المرصودة**.
هذا **يعزل آلة الحالة عن الفارز** — فلا يُخلط عيبُ المنطق باختلاف البيانات.

**العتبة المسجَّلة: متوسط Jaccard ‏≥ 0.95 · وصفر مخالفةٍ في سبب الإزالة.**
⚠️ **وحدُّ قوّةٍ مُعلَن مسبقًا:** العيّنة ‏13 يومًا و22 إضافة ⇒ **شرطٌ لازم لا كافٍ**.

🔒 قراءة/تحليل فقط — بلا شبكة، وبلا أيّ كتابةٍ لحالة الإنتاج.
"""
from __future__ import annotations

import json
import subprocess
import sys

import replay10 as RP


def live_snapshots(path: str = "weekly_watchlist.json") -> list[dict]:
    """كل لقطات الملفّ من git، **مرتَّبةً زمنيًّا تصاعديًّا** ومنزوعة التكرار باليوم
    (تُؤخذ **آخر** لقطةٍ في اليوم = حالة نهاية اليوم)."""
    out = subprocess.run(
        ["git", "log", "--follow", "--format=%H|%ad", "--date=short", "--", path],
        capture_output=True, text=True).stdout.strip()
    if not out:
        return []
    seen: dict[str, dict] = {}
    for line in reversed(out.split("\n")):          # الأقدم أولًا
        h, day = line.split("|")
        blob = subprocess.run(["git", "show", f"{h}:{path}"],
                              capture_output=True, text=True).stdout
        try:
            d = json.loads(blob)
        except Exception:
            continue
        seen[day] = d                                # آخر لقطةٍ في اليوم تفوز
    return [{"day": k, "wl": v} for k, v in sorted(seen.items())]


def observed_stream(snaps: list[dict]) -> tuple[dict, list, dict]:
    """يستخرج من اللقطات: العضوية اليومية المرصودة · تيّار الإضافات (مرشّحون بجاهزيتهم
    المخزَّنة) · وأحداث الخروج **كما وقعت فعلًا** (جلسة الخروج وسببه).

    **سبب الخروج يُقرأ من الحيّ لا يُخمَّن:** غيابُ الاسم مع `status=="stopped"` في
    اللقطة السابقة ⇒ `stopped` · وإلا ⇒ `window` (خروجٌ غير مُسمّى). و`hit` غير `None`
    ⇒ الاسم بلغ هدفًا (يحرّر الخانة ويبقى) — يُرصد **متى** ظهر ذلك أوّل مرّة.

    🔴 **ويدعم إعادة الدخول عبر «حلقات» (`episodes`)** — الصيغة الأولى كانت تحفظ
    خروجًا واحدًا لكل رمز، فسقط `PSTV` (دخل جلستَي 0-1 · غاب 2-3 مع إعادة بناء
    القائمة · ثم عاد من الجلسة 4). **أمسكه أوّل تشغيلٍ للبوّابة.**
    """
    days = [s["day"] for s in snaps]
    idx = {d: i for i, d in enumerate(days)}         # فهرس الجلسة = ترتيب اليوم
    observed: dict[int, tuple[str, ...]] = {}
    prev_syms: set[str] = set()
    prev_state: dict[str, dict] = {}
    adds: list[tuple[int, dict]] = []
    open_ep: dict[str, int] = {}                     # رمز → جلسة دخول الحلقة المفتوحة
    episodes: dict[str, list[dict]] = {}             # رمز → [{enter, exit, reason, hit}]

    for d in days:
        i = idx[d]
        st = {s["symbol"]: s for s in snaps[i]["wl"].get("stocks", [])}
        cur = set(st)
        observed[i] = tuple(sorted(cur))
        for sym in sorted(cur - prev_syms):
            adds.append((i, st[sym]))
            open_ep[sym] = i
            episodes.setdefault(sym, []).append(
                {"enter": i, "exit": None, "reason": None, "hit": None})
        for sym in sorted(prev_syms - cur):
            was = prev_state.get(sym, {})
            reason = RP.R_STOP if was.get("status") == "stopped" else RP.R_WINDOW
            if episodes.get(sym):
                episodes[sym][-1].update(exit=i, reason=reason)
            open_ep.pop(sym, None)
        for sym, s in st.items():
            if s.get("hit") and episodes.get(sym) and episodes[sym][-1]["hit"] is None:
                episodes[sym][-1]["hit"] = i
        prev_syms, prev_state = cur, st
    return observed, adds, {"episodes": episodes, "n_days": len(days),
                            "n_exits": sum(1 for v in episodes.values()
                                           for e in v if e["exit"] is not None),
                            "n_hits": sum(1 for v in episodes.values()
                                          for e in v if e["hit"] is not None),
                            "n_reentry": sum(1 for v in episodes.values() if len(v) > 1)}


def run() -> int:
    snaps = live_snapshots()
    if len(snaps) < 3:
        print("⛔ لقطاتٌ غير كافية — البوّابة أ لا تُقيَّم."); return 2
    observed, adds, ev = observed_stream(snaps)
    last = max(observed)

    cands, seq = [], 0
    for sess, s in adds:
        cands.append(RP.Candidate(session=sess, symbol=s["symbol"],
                                  readiness=s.get("readiness"),
                                  score=s.get("score") or 0.0,
                                  rr=s.get("rr") or 0.0, seq=seq))
        seq += 1

    def outcome_of(c: RP.Candidate):
        """**النتيجة المرصودة حيًّا** — لا تُستعمل في الاختيار، فقط لجدولة الخروج.
        **تُطابَق الحلقةُ بجلسة دخولها** (لا بالرمز وحده) ⇒ يدعم إعادة الدخول."""
        eps = ev["episodes"].get(c.symbol, [])
        ep = next((e for e in eps if e["enter"] == c.session), None)
        if ep is None:
            return (RP.R_WINDOW, last - c.session + 1)
        if ep["exit"] is not None:
            return (ep["reason"], max(ep["exit"] - c.session, 0))
        if ep["hit"] is not None:
            return (RP.R_HIT_HELD, max(ep["hit"] - c.session, 0))
        return (RP.R_WINDOW, last - c.session + 1)      # لم يخرج ضمن النافذة

    # ⚠️ السعة مرفوعة عمدًا: البوّابة أ تختبر **آلة الحالة** (الدخول/الخروج/الحمل)
    #    على تيّارٍ مرصود، لا قرار السعة (الذي لا نملك مرفوضيه تاريخيًّا).
    res = RP.replay(cands, outcome_of=outcome_of, capacity=10 ** 6,
                    sessions=range(0, last + 1))
    g = RP.gate_a(observed, res["daily"])

    print("🚦 البوّابة أ — أمانة آلة الحالة")
    print(f"   لقطات: {len(snaps)} · أيام: {ev['n_days']} · إضافات: {len(adds)} "
          f"· خروجات: {ev['n_exits']} · بلغت هدفًا: {ev['n_hits']} "
          f"· رموزٌ أعادت الدخول: {ev['n_reentry']}")
    print(f"   متوسط Jaccard: {g['mean']:.4f} (العتبة {g['threshold']}) "
          f"· أضعف يوم: {g['worst']:.4f}")
    bad = sorted((d, v) for d, v in g["per_day"].items() if v < 1.0)
    if bad:
        print(f"   أيام غير مطابقة ({len(bad)}):")
        for d, v in bad[:12]:
            o, p = set(observed.get(d, ())), set(res["daily"].get(d, ()))
            print(f"     جلسة {d} · J={v:.3f} · ناقص={sorted(o - p)} · زائد={sorted(p - o)}")
    print(f"   الحكم: {'✅ عبرت' if g['passed'] else '🔴 سقطت'}")
    print("   ⚠️ حدّ مُعلَن مسبقًا: العيّنة صغيرة ⇒ شرطٌ لازم لا كافٍ.")
    return 0 if g["passed"] else 1


if __name__ == "__main__":
    sys.exit(run())
