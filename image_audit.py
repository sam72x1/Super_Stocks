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


# 🔄 V3.1 (2026-10-02 · عطلٌ مُثبَت): الماسحُ كان يعرف `IMG_xxxx` وحدَها ⟵ صورُ العائلات الأخرى (TG_ · X_ · CH_ · EDU_ · APP_ · WA_)
#    تُعَدّ «لم تُقرأ بعد» ولو وثّقها الكاتالوجُ باسمها (التقرير قال 638 والمقيسُ 23 بلا سجلٍّ — faisal_method_v3/v31/reconcile_v31.json).
FAMILY_RE = re.compile(r"\b((?:TG|X|CH|EDU|APP|WA|NEW)_\d{8}_[0-9A-Za-z_]+|TG_\d{3,6}(?![0-9A-Za-z_]))")   # أسماءُ ملفّاتٍ لا رموزُ دفعةٍ محلّيّة
V31_RECORD = os.path.join("faisal_method_v3", "v31", "reconcile_v31.json")
V3_VISUAL = [os.path.join("faisal_method_v3", "data", "visual_review.json"),
             os.path.join("faisal_method_v3", "data", "visual_review_v31.json")]


def scan_docs(paths):
    """يجمع معرّفات الصور المذكورة في ملفات التوثيق → set: `IMG_xxxx` (وصيغُها) ‏+ أسماءُ العائلات الأخرى حرفًا.
    نقيّة (تقبل نصوصًا)."""
    seen = set()
    for txt in paths:
        for m in re.finditer(r"IMG[_\-]?(\d{3,5})", txt or "", re.I):
            seen.add(f"IMG_{m.group(1)}")
        for m in FAMILY_RE.finditer(txt or ""):
            seen.add(m.group(1).rstrip("_"))
    return seen


def _not_a_missing_image(token, have):
    """إحالةٌ ليست صورةً غائبة: قالبٌ (`_NN`) أو بادئةُ اسمٍ مرفوع (`X_20260918_27` ⟵ `X_20260918_27_CUPR`). نقيّة."""
    return bool(re.search(r"_NN(_|$)", token)) or any(h.startswith(token + "_") for h in have)


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


def build(state=None, docs=None, files=None, also=None):
    """يبني السجلّ: لكل صورة معرّف · ملف · بصمة · موثّقة؟ · الحالة اليدوية · السبب.
    `docs`/`files` قابلان للحقن (اختبار بلا قرص). نقيّة بالنسبة للحقن.
    `also`: معرّفاتٌ لها سجلٌّ مكتوبٌ لكلّ صورة خارج المسح النصّيّ (مراجعةٌ بصريّة · ذكرٌ بمدًى أو رمزِ دفعة — V3.1)."""
    state = dict(state or {})
    mentioned = scan_docs(docs if docs is not None else _doc_texts())
    also = set(also or ())
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
        doc = iid in mentioned or iid in also
        ps = prev.get("status")
        if ps == "unread" and doc:          # 🔄 V3.1: الحالةُ الآليّة كانت تُثبَّت «unread» للأبد ولو وُثّقت الصورةُ بعدها
            ps = None
        rows.append({
            "id": iid, "file": os.path.basename(p), "sha": sha,
            "documented": doc,
            "status": ps or ("confirmed" if doc else "unread"),
            "note": prev.get("note") or "",
            "duplicate_of": dup if dup and dup != iid else None,
        })
    # معرّفات موثّقة بلا ملف مرفوع (وثّقناها من المحادثة) — تُدرَج للاكتمال
    have = {r["id"] for r in rows}
    for iid in sorted(mentioned - have):
        if _not_a_missing_image(iid, have):
            continue
        prev = state.get(iid) or {}
        rows.append({"id": iid, "file": "", "sha": "", "documented": True,
                     "status": prev.get("status") or "confirmed",
                     "note": prev.get("note") or "موثّقة من المحادثة بلا ملف مرفوع",
                     "duplicate_of": None})
    rows.sort(key=lambda r: r["id"])
    return rows


def _v31_documented():
    """سجلُّ V3.1 لكلّ صورة (إن وُجد): ذكرٌ في الوثائق بأيّ طريقةٍ مسجَّلة ‏+ المراجعاتُ البصريّة. فاشلةٌ-آمنة ⟵ set()."""
    out = set()
    try:
        rec = json.load(open(V31_RECORD, encoding="utf-8"))
        out |= {k for k, v in rec["corpus"]["per_image_record"].items() if v}
    except Exception:                                    # noqa: BLE001
        pass
    for p in V3_VISUAL:
        try:
            d = json.load(open(p, encoding="utf-8"))
            out |= set(d.get("new", d) if isinstance(d, dict) else ())
        except Exception:                                # noqa: BLE001
            pass
    out.discard("meta")
    out.discard("amend")
    return out


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
    rows = build(state, also=_v31_documented())
    for r in rows:                      # ثبّت الحالة المحسوبة في الحالة الدائمة (والآليّةُ «unread» تُرقّى حين تُوثَّق)
        if (state.get(r["id"]) or {}).get("status") in (None, "unread"):
            state[r["id"]] = {"status": r["status"], "note": r["note"]}
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
