#!/usr/bin/env python3
"""🌘 مولِّدُ `T_REBUILD_shadow.md` — تقريرُ أسبوع الظلّ من `data/shadow/shadow_report_<as_of>.json` بايتًا (بلا شبكة).

أمرُ المالك 2026-10-29 «في تقرير الظل اذكر لكل سهم: أعمق هبوط من سعر الإدراج قبل أي صعود» · وصفٌ لا حكم · لا تلغرام · لا شحن.
الاستعمال: `python3 fm_forensics/rebuild/shadow_doc.py` (يكتب) · `--check` (يطابق بايتًا).
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHADOW = os.path.join(HERE, "data", "shadow")
DOC = os.path.join(HERE, "T_REBUILD_shadow.md")
RE_REPORT = re.compile(r"shadow_report_(\d{4}-\d{2}-\d{2})\.json$")


def latest_report() -> str:
    fs = sorted(f for f in glob.glob(os.path.join(SHADOW, "shadow_report_*.json")) if RE_REPORT.search(f))
    return fs[-1] if fs else ""


def _pct(v) -> str:
    return "—" if v is None else f"{v:.2f}%"


def render(rep: dict, name: str) -> str:
    L = ["# T-REBUILD — تقريرُ أسبوع الظلّ: أعمقُ هبوطٍ من سعر الإدراج قبل أيّ صعود", "",
         f"> مولَّدٌ من `data/shadow/{name}` بـ`shadow_doc.py` (لا يُحرَّر باليد) · as_of **{rep['as_of']}** · التشغيلة "
         f"`{rep.get('run', '—')}` · main `{str(rep.get('main_sha', '—'))[:9]}` · {rep.get('note', '')}",
         f"> التعريف: {rep.get('definition', '')}", ""]
    ents = rep.get("entries") or []
    by = collections.defaultdict(list)
    for e in ents:
        by[e["session"]].append(e)
    st = collections.Counter(e.get("status") for e in ents)
    L += ["## ⓪ الخلاصة (وصفٌ لا حكم)", "",
          f"- القوائمُ المحفوظة: {len(rep.get('files') or [])} ({' · '.join(rep.get('files') or [])}) · الأسهم: {len(ents)}",
          f"- صعد فوق سعر الإدراج: {st.get('rose', 0)} · لم يصعد بعد: {st.get('not_yet', 0)} · بلا شموع: {st.get('no_bars', 0)} · "
          f"بلا مرجع: {st.get('no_ref', 0)}",
          f"- تعديلُ مقياس (سعرُ الإدراج المُعاد يخالف المسجَّل أكثر من 2%): {sum(1 for e in ents if e.get('ref_rescaled'))}", ""]
    for d in sorted(by):
        rows = sorted(by[d], key=lambda e: (-(e.get("score") or 0), e["symbol"]))
        ext = any("sessions_since" in e for e in rows)   # أعمدةُ 2026-11-05 حين يحملها التقرير وحدَها (تقريرُ 11-04 بايتًا كما هو)
        L += [f"## جلسة {d} — {len(rows)} سهمًا", "",
              "| السهم | الدرجة | سعرُ الإدراج (إغلاق D−1) | أعمقُ هبوط | تاريخُه | أوّلُ صعود | تعديلُ مقياس |"
              + (" أعلى صعود حتى تاريخه | تاريخُه | أعمقُ هبوط حتى تاريخه | تاريخُه | جلساتٌ منذ الإدراج |" if ext else ""),
              "|---|---|---|---|---|---|---|" + ("---|---|---|---|---|" if ext else "")]
        for e in rows:
            ref = "—" if e.get("ref") is None else f"{e['ref']:.4g} ({e.get('ref_date', '')})"
            rise = e.get("first_rise") or ("لم يصعد بعد" if e.get("status") == "not_yet" else e.get("status", "—"))
            L.append(f"| {e['symbol']} | {e.get('score', '—')} | {ref} | {_pct(e.get('deepest_pct'))} | {e.get('deepest_date') or '—'} | "
                     f"{rise} | {'نعم' if e.get('ref_rescaled') else 'لا'} |"
                     + (f" {_pct(e.get('max_rise_pct'))} | {e.get('max_rise_date') or '—'} | {_pct(e.get('deepest_to_date_pct'))} | "
                        f"{e.get('deepest_to_date_date') or '—'} | {e.get('sessions_since', '—')} |" if ext else ""))
        L.append("")
    L += ["## ما لا يقوله هذا التقرير", "",
          "- وصفٌ لحركة السعر بعد الإدراج لا حكمٌ على الدرجة ولا على القائمة · والقرارُ بعد أسبوع الظلّ للمالك (لا تلغرام ولا شحن).",
          "- «أوّلُ صعود» إغلاقٌ يوميٌّ فوق سعر الإدراج · والأعمقُ أدنى Low حتى يومه شاملًا (ترتيبُ ما داخل اليوم مجهول ⟵ متشائم).", ""]
    return "\n".join(L)


def main(argv) -> int:
    f = latest_report()
    if not f:
        print("⛔ لا تقرير ظلٍّ محفوظ")
        return 2
    body = render(json.load(open(f, encoding="utf-8")), os.path.basename(f))
    if "--check" in argv:
        same = os.path.exists(DOC) and open(DOC, encoding="utf-8").read() == body
        print("✅ الوثيقةُ = المولِّد بايتًا" if same else "❌ الوثيقةُ تختلف عن المولِّد")
        return 0 if same else 1
    open(DOC, "w", encoding="utf-8").write(body)
    print(f"🌘 {DOC} ⟵ {os.path.basename(f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
