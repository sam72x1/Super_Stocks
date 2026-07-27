# -*- coding: utf-8 -*-
"""
📸 سجلّ تغطية صور منهجية فيصل — أداة مستقلة (لا تمسّ البوت إطلاقًا).

الغرض (طلب المستخدم 2026-07-27): «برسل أكثر من 300 صورة بُني عليها البوت عشان نتأكد
ما نسينا شي». مع هذا العدد **الذاكرة وحدها لا تكفي** — فالحلّ سجلّ دائم يقول لكل صورة:
هل قُرئت؟ هل استُخرجت قاعدتها؟ هل نُفِّذت أم رُفضت أم ما زالت مفتوحة؟ ولماذا.

يقرأ:
  • ملفات الصور في `faisal_images/` (المعرّف من اسم الملف: `IMG_0153` أو `NEW_*`).
  • ذِكر كل معرّف في ملفات التوثيق (`FAISAL_IMAGES_CATALOG.md` · `CLAUDE.md` ·
    `HANDOFF.md` · بقية `*.md`) = دليل أنها قُرئت وسُجّلت.
  • الحالة اليدوية المتراكمة من `faisal_image_audit.json` (لا تُفقَد بين التشغيلات).

يكتب: `faisal_image_audit.json` (حالة قابلة للاستئناف) + `FAISAL_IMAGE_AUDIT.md`
(جدول للقراءة البشرية) — ويطبع ملخّصًا: كم موثّقة · كم متبقّية · وأول دفعة ينبغي قراءتها.

التشغيل: `python3 image_audit.py`  ·  لتعليم حالة: `python3 image_audit.py --set IMG_0153=implemented:"عتبة 20%"`
**قراءة/تتبّع فقط — بلا شبكة، ولا استيراد للبوت، ولا مسّ لأي منطق فرز.**
"""
import hashlib
import json
import os
import re
import sys
import datetime as dt

IMG_DIR = "faisal_images"
STATE = "faisal_image_audit.json"
REPORT = "FAISAL_IMAGE_AUDIT.md"
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic")
DOCS_SKIP = {REPORT}
VALID = ("implemented", "confirmed", "rejected", "open", "unread")
BATCH = 8                                    # حجم الدفعة الموصى لقراءة الصور


def image_id(fname):
    """معرّف الصورة من اسم الملف: `IMG_0153.jpeg` → `IMG_0153` · وإلا الاسم بلا امتداد.
    نقيّة · لا تعتمد على وجود الملف."""
    base = os.path.basename(str(fname))
    stem = os.path.splitext(base)[0]
    m = re.search(r"IMG[_\-]?(\d{3,5})", stem, re.I)
    return f"IMG_{m.group(1)}" if m else stem.strip().replace(" ", "_")


def scan_docs(paths):
    """يجمع كل معرّفات `IMG_xxxx` المذكورة في ملفات التوثيق → set. نقيّة (تقبل نصوصًا)."""
    seen = set()
    for txt in paths:
        for m in re.finditer(r"IMG[_\-]?(\d{3,5})", txt or "", re.I):
            seen.add(f"IMG_{m.group(1)}")
    return seen


def _doc_texts():
    out = []
    for f in sorted(os.listdir(".")):
        if f.endswith(".md") and f not in DOCS_SKIP:
            try:
                out.append(open(f, encoding="utf-8").read())
            except Exception:
                continue
    return out


def _sha(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return ""


def build(state=None, docs=None, files=None):
    """يبني السجلّ: لكل صورة معرّف · ملف · بصمة · موثّقة؟ · الحالة اليدوية · السبب.
    `docs`/`files` قابلان للحقن (اختبار بلا قرص). نقيّة بالنسبة للحقن."""
    state = dict(state or {})
    mentioned = scan_docs(docs if docs is not None else _doc_texts())
    if files is None:
        files = ([os.path.join(IMG_DIR, f) for f in sorted(os.listdir(IMG_DIR))
                  if f.lower().endswith(EXTS)] if os.path.isdir(IMG_DIR) else [])
    rows, by_sha = [], {}
    for p in files:
        iid = image_id(p)
        sha = _sha(p) if os.path.exists(p) else ""
        dup = by_sha.get(sha) if sha else None
        if sha:
            by_sha.setdefault(sha, iid)
        prev = state.get(iid) or {}
        rows.append({
            "id": iid, "file": os.path.basename(p), "sha": sha,
            "documented": iid in mentioned,
            "status": prev.get("status") or ("confirmed" if iid in mentioned
                                             else "unread"),
            "note": prev.get("note") or "",
            "duplicate_of": dup if dup and dup != iid else None,
        })
    # معرّفات موثّقة بلا ملف مرفوع (وثّقناها من المحادثة) — تُدرَج للاكتمال
    have = {r["id"] for r in rows}
    for iid in sorted(mentioned - have):
        prev = state.get(iid) or {}
        rows.append({"id": iid, "file": "", "sha": "", "documented": True,
                     "status": prev.get("status") or "confirmed",
                     "note": prev.get("note") or "موثّقة من المحادثة بلا ملف مرفوع",
                     "duplicate_of": None})
    rows.sort(key=lambda r: r["id"])
    return rows


def summarize(rows):
    """أرقام السجلّ + أول دفعة ينبغي قراءتها (غير الموثّقة، بحجم `BATCH`). نقيّة."""
    todo = [r for r in rows if not r["documented"] and not r["duplicate_of"]]
    return {
        "total": len(rows),
        "with_file": sum(1 for r in rows if r["file"]),
        "documented": sum(1 for r in rows if r["documented"]),
        "unread": len(todo),
        "duplicates": sum(1 for r in rows if r["duplicate_of"]),
        "by_status": {s: sum(1 for r in rows if r["status"] == s) for s in VALID
                      if any(r["status"] == s for r in rows)},
        "next_batch": [r["id"] for r in todo[:BATCH]],
    }


def render(rows, sm, today=None):
    """جدول Markdown للقراءة البشرية. نقيّة."""
    d = today or dt.date.today().isoformat()
    L = [f"# 📸 سجلّ تغطية صور منهجية فيصل — {d}", "",
         f"- **المجموع المُدرَج:** {sm['total']}  ·  **بملف مرفوع:** {sm['with_file']}",
         f"- **📗 موثّقة:** {sm['documented']}  ·  **📕 لم تُقرأ بعد:** {sm['unread']}"
         f"  ·  **مكرّرة:** {sm['duplicates']}", ""]
    if sm["next_batch"]:
        L += [f"**الدفعة التالية المقترحة ({len(sm['next_batch'])}):** "
              + " · ".join(sm["next_batch"]), ""]
    else:
        L += ["✅ **لا صورة غير مقروءة** — التغطية مكتملة على المرفوع حاليًا.", ""]
    L += ["| المعرّف | الملف | 📗 موثّقة | الحالة | ملاحظة |",
          "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['id']} | {r['file'] or '—'} | "
                 f"{'✅' if r['documented'] else '❌'} | {r['status']} | "
                 f"{r['note'] or ('مكرّرة لـ' + r['duplicate_of']) if r['duplicate_of'] else r['note'] or '—'} |")
    L += ["", "> **الحالات:** `implemented` نُفِّذت بالكود · `confirmed` تأكيد لما هو "
          "منفَّذ · `rejected` رُفضت بدليل (يُذكر) · `open` فرضية مفتوحة تحتاج تسجيلًا "
          "مسبقًا · `unread` لم تُقرأ بعد.",
          "> تُحدَّث بـ`python3 image_audit.py` بعد كل رفع، وبـ`--set` بعد قراءة كل دفعة."]
    return "\n".join(L)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8")) or {}
        except Exception:
            state = {}
    for a in argv:
        if not a.startswith("--set"):
            continue
        val = a.split("=", 1)[1] if "=" in a else ""
        iid, _, rest = val.partition("=")
        st, _, note = rest.partition(":")
        st = (st or "").strip() or "confirmed"
        if st not in VALID:
            print(f"⚠️ حالة غير معروفة: {st} (المسموح: {', '.join(VALID)})")
            return 2
        state[image_id(iid)] = {"status": st, "note": note.strip().strip('"')}
    rows = build(state)
    for r in rows:                      # ثبّت الحالة المحسوبة في الحالة الدائمة
        state.setdefault(r["id"], {"status": r["status"], "note": r["note"]})
    sm = summarize(rows)
    json.dump(state, open(STATE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    open(REPORT, "w", encoding="utf-8").write(render(rows, sm) + "\n")
    print(f"📸 مُدرَج {sm['total']} · بملف {sm['with_file']} · موثّقة "
          f"{sm['documented']} · لم تُقرأ {sm['unread']} · مكرّرة {sm['duplicates']}")
    if sm["next_batch"]:
        print("الدفعة التالية: " + " · ".join(sm["next_batch"]))
    print(f"كُتِب {REPORT} و{STATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
