# -*- coding: utf-8 -*-
"""
🧮 FAISAL V3.1 — مطابقةُ تلغرام والمدوَّنة (§3 · §4) · قراءةٌ فقط · لا شبكة · لا حالةَ إنتاج.

    python3 faisal_method_v3/v31_reconcile.py     ⟵ faisal_method_v3/v31/reconcile_v31.json

① **تلغرام (§3):** دفعةُ `TG_58042`…`TG_58052` — كلُّ صورةٍ بمصدرها الفعليّ:
   رقمُ الرسالة وطابعُ إرسالها من `file_reference` داخل `file_id` المحفوظ في `telegram_collect_state.json`
   (ترميزُ Bot API: base64 ثمّ RLE للأصفار ⟵ ‏4 بايتات رقمُ الرسالة · ‏4 بايتات زمنُ الإرسال) — لا من الذاكرة ولا من اقتباس.
   ⇒ **العددُ يحدّده المصدر:** كم file_id يحمل رقمَ رسالةٍ في الدفعة · ومتى أُرسل كلٌّ منها.
② **المدوَّنة (§4):** القيمةُ في V3 · والقيمةُ المتحقَّقة في V3.1 · والسبب — لكلّ عدّ:
   مكتشَف · قابلٌ للوصول · قابلٌ للفحص · مفحوص (بأيّ طريقةٍ مسجَّلة) · فريد · مطابقٌ تمامًا · شبهُ مطابق · مشتقّ · وإحالاتٌ بلا ملفّ.
   البصماتُ تُعاد حسابًا من الملفّات بدوالّ `corpus_build` النقيّة نفسِها (لا يُنادى `main` فلا يُكتب ملفٌّ من V3).

⚖️ ما لا يُقال: «مفحوص» = له سجلٌّ مكتوبٌ لكلّ صورة (وثيقةٌ تذكرها باسمها أو بمدًى أو برمز دفعتها · أو مراجعةٌ بصريّة ·
   أو عضويّةُ عنقودِ تكرارٍ رُوجع بالعين) — لا «فتحتُها ذهنيًّا» · والكشفُ بالمدى ورمزِ الدفعة آليٌّ ⟵ يُطبع لكلّ صورةٍ طريقتُه.
"""
import base64
import collections
import hashlib
import json
import os
import re
import struct
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

IMG_DIR = os.path.join(ROOT, "faisal_images")
STATE = os.path.join(ROOT, "telegram_collect_state.json")
CATALOG = os.path.join(ROOT, "FAISAL_IMAGES_CATALOG.md")
OUT_DIR = os.path.join(HERE, "v31")
OUT = os.path.join(OUT_DIR, "reconcile_v31.json")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
EXT_ALL = IMG_EXT + (".heic", ".gif", ".bmp", ".tif", ".tiff")

TG_BATCH = [f"TG_{n}" for n in range(58042, 58053)]          # §3: المدى الذي تذكره المهمّة كلُّه
TG_CATALOG_HEAD = "## §ثلاثة وثلاثون"                         # قسمُ الدفعة في الكاتالوج
SEND_GROUP_GAP_S = 60                                         # إرسالان يفصلهما أكثرُ من دقيقة = إرسالان (هندسيّ · يُطبع)


# ── ① تلغرام ─────────────────────────────────────────────────────────────────
def rle_decode(b):
    """فكُّ ترميز Bot API: البايتُ 0 يتبعه عددُ الأصفار. نقيّة."""
    out, i = bytearray(), 0
    while i < len(b):
        if b[i] == 0 and i + 1 < len(b):
            out += b"\x00" * b[i + 1]
            i += 2
        else:
            out.append(b[i])
            i += 1
    return bytes(out)


def file_ref(fid):
    """(رقمُ الرسالة · زمنُ الإرسال بثواني يونكس) من file_id صورةٍ أو None. نقيّة · فاشلةٌ-آمنة."""
    try:
        raw = base64.urlsafe_b64decode(fid + "=" * (-len(fid) % 4))
        d = rle_decode(raw)
        ln = d[8]
        ref = d[9:9 + ln]
        if len(ref) < 9:
            return None
        return int.from_bytes(ref[1:5], "big"), int.from_bytes(ref[5:9], "big")
    except Exception:                                   # noqa: BLE001
        return None


def send_groups(stamps, gap=SEND_GROUP_GAP_S):
    """يجمع الطوابعَ المرتّبة في إرسالات: فرقٌ فوق gap ثانيةً = إرسالٌ جديد. نقيّة."""
    groups = []
    for t in sorted(stamps):
        if groups and t - groups[-1][-1] <= gap:
            groups[-1].append(t)
        else:
            groups.append([t])
    return groups


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def catalog_rows(text, head=TG_CATALOG_HEAD):
    """صفوفُ جدول قسم الدفعة في الكاتالوج: {المعرّف: [الخلايا]}. نقيّة."""
    i = text.find(head)
    if i < 0:
        return {}
    j = text.find("\n## ", i + len(head))
    sec = text[i:j if j > 0 else len(text)]
    rows = {}
    for ln in sec.splitlines():
        m = re.match(r"\|\s*`(TG_\d+)`\s*\|(.*)\|\s*$", ln)
        if m:
            rows[m.group(1)] = [c.strip() for c in m.group(2).split("|")]
    return rows


def telegram_reconcile(state, corpus, evidence_keys, cat_text, img_dir=IMG_DIR, batch=TG_BATCH):
    refs = {}
    for fid in state.get("seen_file_ids", []):
        r = file_ref(fid)
        if r:
            refs.setdefault(r[0], []).append(r[1])
    by_id = {r["id"]: r for r in corpus["images"]}
    members = collections.defaultdict(list)
    for r in corpus["images"]:
        members[r["dup_cluster"]].append(r["id"])
    cat = catalog_rows(cat_text)
    per = []
    for tid in batch:
        mid = int(tid.split("_")[1])
        p = os.path.join(img_dir, tid + ".jpg")
        rec = by_id.get(tid)
        row = cat.get(tid)
        cl = rec["dup_cluster"] if rec else None
        dup_of = sorted(x for x in members.get(cl, []) if x != tid) if cl else []
        tag = None
        if row:
            m = re.search(r"`(faisal_verbatim|faisal_adopted|inferred|engineering|third_party|unsourced)`", row[-1])
            tag = m.group(1) if m else None
        per.append({
            "id": tid, "message_id": mid,
            "sent_utc": _iso(min(refs[mid])) if mid in refs else None,
            "file_id_in_state": mid in refs,
            "exists": os.path.exists(p),
            "accessible": os.path.exists(p) and os.access(p, os.R_OK),
            "sha256": _sha(p) if os.path.exists(p) else None,
            "sha_matches_corpus": bool(rec) and os.path.exists(p) and rec["sha256"] == _sha(p),
            "in_corpus": bool(rec),
            "ocr": bool(rec and (rec.get("ocr_text") or "").strip()),
            "catalogued": bool(row),
            "visually_inspected": bool(row),          # صفُّ الكاتالوج = قراءةٌ بالعين (V3 §ثلاثة وثلاثون)
            "author_or_source": row[0] if row else None,
            "dup_cluster": cl, "duplicate_of": dup_of,
            "used_as_evidence": bool(cl and cl in evidence_keys and not dup_of),
            "evidence_status": tag,
        })
    stamps = [min(refs[x["message_id"]]) for x in per if x["message_id"] in refs]
    groups = send_groups(stamps)
    sends = [{"sent_utc": _iso(g[0]), "count": len(g),
              "ids": [x["id"] for x in per if x["message_id"] in refs and min(refs[x["message_id"]]) in g]}
             for g in groups]
    tot = {
        "TELEGRAM_TOTAL_REFERENCED": len(per),
        "TELEGRAM_TOTAL_ACCESSIBLE": sum(x["accessible"] for x in per),
        "TELEGRAM_TOTAL_INSPECTED": sum(x["visually_inspected"] for x in per),
        "TELEGRAM_TOTAL_USED_AS_EVIDENCE": sum(x["used_as_evidence"] for x in per),
        "TELEGRAM_TOTAL_UNAVAILABLE": sum(not x["accessible"] for x in per),
        "TELEGRAM_TOTAL_DUPLICATES": sum(bool(x["duplicate_of"]) for x in per),
    }
    return {"per_image": per, "sends": sends, "totals": tot,
            "send_group_gap_s": SEND_GROUP_GAP_S,
            "decoded_file_ids": sum(len(v) for v in refs.values()),
            "state_file_ids": len(state.get("seen_file_ids", []))}


# ── ② المدوَّنة ───────────────────────────────────────────────────────────────
_TOK = re.compile(r"[A-Za-z]+_[0-9A-Za-z_]+")
_FAM = re.compile(r"\b(IMG_\d{3,5}|(?:TG|X|APP|CH|EDU|WA|NEW)_\d{8}_[A-Za-z0-9_]+|TG_\d{3,6})\b")
_RNG = re.compile(r"`?([A-Z]+_(?:\d{8}_)?)(\d+)(?:\.\w+)?`?\s*(?:…|\.\.\.|–|-|⟶|→)\s*`?(?:\1)?_?(\d+)(?:\.\w+)?`?")
_PREF = re.compile(r"\b((?:X|TG|CH|EDU|APP|WA|NEW)_\d{8}_)")
_CODE = re.compile(r"\b(X|CH|TG|WA|APP|EDU)_(\d{2}(?:/\d{2})*)(?:_([A-Za-z][A-Za-z0-9_]*))?")


def load_docs(root=ROOT):
    """كلُّ ‎*.md في المستودع ‏+ faisal_images/README.md · عدا faisal_method_v3/ (وثائقُ هذه المهمّة لا تُعَدّ سجلًّا سابقًا لنفسها)
    وعدا FAISAL_IMAGE_AUDIT.md (تقريرٌ آليّ يُعدّد الأسماء ولا يقرأ الصور)."""
    docs = {}
    rd = os.path.join(root, "faisal_images", "README.md")          # فهرسُ الصور نفسُه وثيقةٌ (وصفٌ لكلّ دفعة) لا صورة
    if os.path.exists(rd):
        docs["faisal_images/README.md"] = open(rd, encoding="utf-8", errors="ignore").read()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", "faisal_images", "faisal_method_v3", "node_modules")]
        for f in fn:
            if f.endswith(".md") and f != "FAISAL_IMAGE_AUDIT.md":
                p = os.path.join(dp, f)
                try:
                    docs[os.path.relpath(p, root)] = open(p, encoding="utf-8", errors="ignore").read()
                except Exception:                       # noqa: BLE001
                    pass
    return docs


def doc_record(stems, docs):
    """لكلّ صورة: طرقُ ذكرها في الوثائق {exact · range · abbrev · short_name · batch_code · img_bare} ومواضعُها. نقيّة."""
    S = set(stems)
    how, where = collections.defaultdict(set), collections.defaultdict(set)

    def hit(s, m, d):
        how[s].add(m)
        where[s].add(d)
    for d, t in docs.items():
        for m in set(_TOK.findall(t)):
            m2 = m.rstrip("_")
            if m2 in S:
                hit(m2, "exact", d)
        for m in _RNG.finditer(t):
            pfx, a, b = m.group(1), m.group(2), m.group(3)
            ia, ib = int(a), int(b)
            if ib < ia or ib - ia > 200:
                continue
            for k in range(ia, ib + 1):
                for cand in (f"{pfx}{k:0{len(a)}d}", f"{pfx}{k}"):
                    if cand in S:
                        hit(cand, "range", d)
        for line in t.splitlines():
            pf = set(_PREF.findall(line))
            if pf:
                for ab in re.findall(r"(?<![A-Za-z0-9])_(\d{2,3}(?:_[A-Za-z0-9]+)?)(?=[.`\s·,)]|$)", line):
                    for p in pf:
                        if p + ab in S:
                            hit(p + ab, "abbrev", d)
                        if re.fullmatch(r"\d{2,3}", ab):
                            for s in S:
                                if s.startswith(p + ab + "_"):
                                    hit(s, "abbrev", d)
            if "IMG_" in line or "IMG-" in line:
                for a, b in re.findall(r"(?<![\d.])(\d{4})\s*[-–]\s*(\d{4})(?![\d.])", line):
                    ia, ib = int(a), int(b)
                    if 0 <= ib - ia <= 60:
                        for k in range(ia, ib + 1):
                            if f"IMG_{k:04d}" in S:
                                hit(f"IMG_{k:04d}", "img_bare", d)
                for n in re.findall(r"(?<![\d.$])(\d{4})(?![\d.%])", line):
                    if f"IMG_{n}" in S and n not in ("2023", "2024", "2025", "2026"):
                        hit(f"IMG_{n}", "img_bare", d)
        for sec in re.split(r"\n(?=#{1,2} )", t):     # رمزُ دفعةٍ محلّيّ لا يُقرأ إلّا مع تاريخه في القسم نفسِه
            dates = set(re.findall(r"\b(20\d{6})\b", sec)) | {x.replace("-", "") for x in re.findall(r"\b(20\d\d-\d\d-\d\d)\b", sec)}
            for date in dates:
                for m in _CODE.finditer(sec):
                    fam, nums, suf = m.group(1), m.group(2), m.group(3)
                    for n in nums.split("/"):
                        base = f"{fam}_{date}_{n}"
                        for s in S:
                            if s.startswith(base) and (suf is None or s.endswith(suf) or s == base):
                                nxt = s[len(base):]
                                if nxt == "" or nxt.startswith("_"):
                                    hit(s, "batch_code", d)
    for s in stems:
        m = re.match(r"^((?:X|TG|CH|EDU|APP|WA|NEW)_(\d{8})_)(.+)$", s)
        if not m:
            continue
        pfx, date, rest = m.groups()
        if not re.search(r"[A-Za-z]", rest) or len(rest) < 5:
            continue
        pat = re.compile(r"\b" + re.escape(rest) + r"(?:\.\w+)?\b")
        iso = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        for d, t in docs.items():
            if (pfx in t or date in t or iso in t) and pat.search(t):
                hit(s, "short_name", d)
    return how, where


def doc_only_refs(stems, docs):
    """إحالاتٌ في الوثائق بلا ملفّ — بعد إسقاط ما ليس إحالةً لصورةٍ غائبة:
    بادئةُ اسمٍ موجود (`X_20260918_27` ⟵ `X_20260918_27_CUPR`) · وقالبٌ (`_NN_`) · واسمٌ ينتهي بشرطة. نقيّة."""
    S = set(stems)
    raw = collections.defaultdict(set)
    for d, t in docs.items():
        for m in _FAM.findall(t):
            raw[m].add(d)
    equiv = {}                                   # «A ≡ B»: الصورةُ نفسُها محفوظةٌ باسمٍ آخر (مكرَّرٌ لم يُحفظ ثانيةً) — «=» وحدَها
    #                                              تُستعمل في الوثائق بمعنى «قاعدتُها مبنيّة» (`= IMG_0080 مبنيّ`) فلا تُقرأ تطابقًا
    pair = re.compile(r"`?(" + _FAM.pattern[2:-2] + r")`?\s*≡\s*`?(" + _FAM.pattern[2:-2] + r")`?")
    for d, t in docs.items():
        for m in pair.finditer(t):
            a, b = m.group(1), m.group(m.lastindex)
            if a not in S and b in S:
                equiv.setdefault(a, b)
            elif b not in S and a in S:
                equiv.setdefault(b, a)
    dropped = {}
    keep = {}
    for tok, ds in raw.items():
        if tok in S:
            continue
        if tok.endswith("_") or re.search(r"_NN(_|$)", tok):
            dropped[tok] = "قالبٌ لا اسم"
        elif any(s.startswith(tok + "_") for s in S):
            dropped[tok] = "بادئةُ اسمٍ موجود (إحالةٌ مختصرة لملفٍّ في المدوَّنة)"
        elif tok in equiv:
            dropped[tok] = f"مكرَّرٌ لم يُحفظ ثانيةً ≡ {equiv[tok]} (المحتوى في المدوَّنة)"
        else:
            keep[tok] = sorted(ds)
    return keep, dropped


def corpus_reconcile(corpus, dedup, review, vr3, vr31, source_access, docs, img_dir=IMG_DIR, uploads_dir=None):
    import corpus_build as CB          # دوالُّه النقيّة وحدَها — لا يُنادى main()
    files = sorted(os.listdir(img_dir))
    imgs = [f for f in files if f.lower().endswith(EXT_ALL)]
    stems = [os.path.splitext(f)[0] for f in imgs]
    v3 = {r["id"]: r for r in corpus["images"]}
    recs, sha_mis, fp_mis, unreadable = [], [], [], []
    for f in imgs:
        p = os.path.join(img_dir, f)
        stem = os.path.splitext(f)[0]
        try:
            fp = CB.image_fingerprint(p)
        except Exception as e:                           # noqa: BLE001
            unreadable.append([stem, type(e).__name__])
            continue
        sha = CB.sha256_file(p)
        recs.append({"id": stem, "sha256": sha, **fp, "ocr_text": (v3.get(stem) or {}).get("ocr_text")})
        o = v3.get(stem)
        if o and o["sha256"] != sha:
            sha_mis.append(stem)
        if o and any(o.get(k) != fp.get(k) for k in ("dhash64", "dhash256", "phash64", "ahash64", "width", "height")):
            fp_mis.append(stem)
    clusters, edges, vetoed = CB.dedup(recs, review.get("not_duplicate", []))
    by_sha = collections.defaultdict(list)
    for r in recs:
        by_sha[r["sha256"]].append(r["id"])
    v3_multi = {tuple(c["members"]) for c in dedup["clusters"]}
    new_multi = {tuple(c["members"]) for c in clusters if c["size"] > 1}
    reviewed = {tuple(sorted(c["members"])) for c in review.get("reviewed_clusters", [])}
    in_rev = {m for c in clusters if c["size"] > 1 and tuple(sorted(c["members"])) in reviewed for m in c["members"]}
    how, where = doc_record(stems, docs)
    vis3 = set(vr3)
    vis31 = set(vr31.get("new", {}))
    inspected = {s for s in stems if how[s] or s in vis3 or s in vis31 or s in in_rev}
    no_rec_v3_rules = sorted(s for s in stems if not (how[s] or s in vis3 or s in in_rev))
    # اشتقاقٌ بصريٌّ لم تلتقطه البصمة (V3.1 بالعين) ⟵ وحداتٌ مدموجة
    cid = {m: c["cluster_id"] for c in clusters for m in c["members"]}
    uf = {c["cluster_id"]: c["cluster_id"] for c in clusters}

    def find(x):
        while uf[x] != x:
            uf[x] = uf[uf[x]]
            x = uf[x]
        return x
    vis_edges = []
    for k, x in sorted(vr31.get("new", {}).items()):
        for rel in ("derivative_of", "same_drawing_as"):
            o = x.get(rel)
            if o and o in cid and k in cid:
                a, b = find(cid[k]), find(cid[o])
                vis_edges.append({"a": k, "b": o, "kind": rel, "merged": a != b})
                if a != b:
                    uf[a] = b
    units_v31 = len({find(c["cluster_id"]) for c in clusters})
    keep, dropped = doc_only_refs(stems, docs)
    v3_doc_only = next((set(s["ids"]) for s in source_access["sources"] if s["id"] == "SRC-DOC-ONLY-IMAGES"), set())
    up = None
    if uploads_dir and os.path.isdir(uploads_dir):
        ups = sorted(os.listdir(uploads_dir))
        up_imgs = [u for u in ups if u.lower().endswith(EXT_ALL)]
        up_sha = {_sha(os.path.join(uploads_dir, u)) for u in up_imgs}
        corp_sha = {r["sha256"] for r in recs}
        up = {"files": len(ups), "images": len(up_imgs), "unique_by_sha": len(up_sha),
              "exact_in_corpus": len(up_sha & corp_sha), "not_in_corpus_by_sha": len(up_sha - corp_sha),
              "other": collections.Counter(os.path.splitext(u)[1].lower() for u in ups if u not in up_imgs)}
    cm = corpus["meta"]
    ek = {k: sum(1 for e in edges if e["kind"] == k) for k in ("exact", "near", "resized", "derivative_text")}
    rows = [
        ["discovered", cm["images"], len(imgs), "ملفّاتُ الصور في faisal_images/ (‏+ صورةٌ في جذر المستودع ليست دليلًا: operating_standard_v1.jpg)"],
        ["accessible", cm["images"], len(imgs) - len([f for f in imgs if not os.access(os.path.join(img_dir, f), os.R_OK)]), "كلُّ ملفٍّ مقروء"],
        ["inspectable", cm["images"], len(recs), "تفتحه PIL وتُحسب بصماتُه"],
        ["inspected_any_recorded_method", None, len(inspected),
         "V3 لم يعدّه لكلّ صورة · V3.1: وثيقةٌ تذكرها (اسمًا · مدًى · رمزَ دفعة · اسمًا مختصرًا) أو مراجعةٌ بصريّة V3/V3.1 أو عنقودٌ رُوجع"],
        ["inspected_without_v31_visual", None, len(stems) - len(no_rec_v3_rules), "قبل مراجعات V3.1 البصريّة"],
        ["visual_review_per_image", len(vis3), len(vis3) + len(vis31), "V3: ‏20 · V3.1: ‏+33 (كانت بلا سجلٍّ لكلّ صورة)"],
        ["unique_sha256", cm["images"], len(by_sha), "SHA256 كاملًا"],
        ["unique_units_hash_ocr", cm["independent_units"], len(clusters), "بصمةٌ ‏+ نصُّ OCR (عتباتُ V3 نفسُها) — يُعاد حسابُه فيطابق"],
        ["unique_units_after_v31_visual", cm["independent_units"], units_v31,
         "دمجُ ما رأته العينُ في V3.1 مشتقًّا (صورةٌ ثانيةٌ للشاشة نفسِها) أو الرسمَ نفسَه — حدٌّ أدنى"],
        ["exact_duplicates", cm["edge_kinds"]["exact"], ek["exact"], "لا ملفّان بـSHA256 واحد"],
        ["near_duplicates", cm["edge_kinds"]["near"], ek["near"], "dHash256 ≤ 24 وpHash ≤ 10 بالمقاس نفسِه"],
        ["resized", cm["edge_kinds"]["resized"], ek["resized"], "الشرطان نفسُهما بمقاسٍ مختلف"],
        ["derivative_text", cm["edge_kinds"]["derivative_text"], ek["derivative_text"], "تشابهُ نصّ OCR ‏0.85 فأكثر"],
        ["derivative_visual_v31", 0, sum(1 for e in vis_edges if e["kind"] == "derivative_of"),
         "تصويرُ الشاشة مرّتين/اقتباسُ الشارت نفسِه — فاتت البصمةَ (اختلافُ الزاوية والإضاءة)"],
        ["same_drawing_v31", 0, sum(1 for e in vis_edges if e["kind"] == "same_drawing_as"),
         "الرسمُ نفسُه منشورًا في قناةٍ تعليميّة وعند فيصل"],
        ["doc_only_references", len(v3_doc_only), len(keep),
         "معرّفاتٌ في الوثائق بلا ملفّ — بعد إسقاط القوالب والإحالات المختصرة لملفّاتٍ موجودة"],
    ]
    return {
        "table": [{"metric": a, "v3": b, "v31": c, "reason": d} for a, b, c, d in rows],
        "sha256_mismatch_vs_v3": sha_mis, "fingerprint_mismatch_vs_v3": fp_mis, "unreadable": unreadable,
        "cluster_sets_identical_to_v3": v3_multi == new_multi,
        "multi_member_clusters": len(new_multi), "multi_clusters_visually_reviewed": len(new_multi & reviewed),
        "vetoed_pairs": len(vetoed),
        "doc_record_methods": dict(collections.Counter(m for s in stems for m in how[s])),
        "no_record_before_v31_visual": no_rec_v3_rules,
        "no_record_after_v31": sorted(set(stems) - inspected),
        "visual_merge_edges": vis_edges,
        "doc_only": keep, "doc_only_dropped": dropped,
        "doc_only_new_vs_v3": sorted(set(keep) - v3_doc_only), "doc_only_v3_not_in_v31": sorted(v3_doc_only - set(keep)),
        "uploads": up,
        "per_image_doc_methods": {s: sorted(how[s]) for s in stems},
        "per_image_record": {s: sorted(how[s] | ({"visual_v3"} if s in vis3 else set()) | ({"visual_v31"} if s in vis31 else set())
                                       | ({"dup_cluster_reviewed"} if s in in_rev else set())) for s in stems},
    }


def transcript_images(path, corpus, uploads_dir=None, tmp_dir=None):
    """§5: صورُ سجلّ المحادثة (jsonl) — ما أرسله المالك (كتلةُ صورةٍ في رأس رسالته) منفصلًا عمّا أعادته أدواتي (tool_result) ·
    ومطابقةُ كلٍّ بالـSHA256 ثمّ بالبصمة (عتباتُ التكرار نفسُها) مع المدوَّنة والمرفقات. لا يُطبع محتوًى · يُكتب عددٌ وبصمة."""
    import base64 as _b64
    import tempfile
    import corpus_build as CB
    if not path or not os.path.exists(path):
        return {"status": "NOT_ON_THIS_MACHINE", "path": path}
    csha = {r["sha256"]: r["id"] for r in corpus["images"]}
    usha, ufp = {}, {}
    if uploads_dir and os.path.isdir(uploads_dir):
        for f in sorted(os.listdir(uploads_dir)):
            q = os.path.join(uploads_dir, f)
            usha[_sha(q)] = f
            if f.lower().endswith(EXT_ALL):
                try:
                    ufp[f] = CB.image_fingerprint(q)
                except Exception:                                # noqa: BLE001
                    pass
    owner, tool, first = collections.Counter(), collections.Counter(), {}
    raw = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if '"image"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:                                    # noqa: BLE001
                continue
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for blk in c:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") == "image" and (blk.get("source") or {}).get("type") == "base64":
                    b = _b64.b64decode(blk["source"]["data"])
                    h = hashlib.sha256(b).hexdigest()
                    owner[h] += 1
                    first.setdefault(h, o.get("timestamp"))
                    raw.setdefault(h, (b, blk["source"].get("media_type")))
                elif blk.get("type") == "tool_result" and isinstance(blk.get("content"), list):
                    for b2 in blk["content"]:
                        if isinstance(b2, dict) and b2.get("type") == "image" and (b2.get("source") or {}).get("type") == "base64":
                            tool[hashlib.sha256(_b64.b64decode(b2["source"]["data"])).hexdigest()] += 1
    tmp_dir = tmp_dir or tempfile.mkdtemp()
    unmatched = []
    for h in sorted(set(owner) - set(csha) - set(usha)):
        b, mt = raw[h]
        q = os.path.join(tmp_dir, h[:12] + {"image/png": ".png", "image/webp": ".webp"}.get(mt, ".jpg"))
        open(q, "wb").write(b)
        fp = CB.image_fingerprint(q)
        cands = [(CB.hamming_hex(fp["dhash256"], r["dhash256"]), CB.hamming_hex(fp["phash64"], r["phash64"]), "corpus:" + r["id"])
                 for r in corpus["images"]]
        cands += [(CB.hamming_hex(fp["dhash256"], u["dhash256"]), CB.hamming_hex(fp["phash64"], u["phash64"]), "upload:" + f)
                  for f, u in ufp.items()]
        d, ph, who = min(cands, key=lambda x: (x[0] + 4 * x[1], x[2]))
        unmatched.append({"sha256_12": h[:12], "first_seen": first[h], "nearest": who, "dhash256": d, "phash": ph,
                          "near_duplicate": d <= CB.DUP_DHASH256_MAX and ph <= CB.DUP_PHASH_MAX})
    uo = set(owner)
    return {"status": "ACCESSIBLE", "path": os.path.basename(path), "bytes": os.path.getsize(path),
            "owner_sent_blocks": sum(owner.values()), "owner_sent_unique": len(uo),
            "owner_sent_exact_in_corpus": len(uo & set(csha)), "owner_sent_exact_in_uploads": len(uo & set(usha)),
            "owner_sent_not_exact": len(unmatched),
            "owner_sent_not_exact_near_dup": sum(1 for x in unmatched if x["near_duplicate"]),
            "owner_sent_new": sum(1 for x in unmatched if not x["near_duplicate"]),
            "tool_result_blocks": sum(tool.values()), "tool_result_unique": len(tool),
            "unmatched_detail": unmatched}


def main(out=OUT, uploads_dir=None, transcript=None):
    J = lambda p: json.load(open(p, encoding="utf-8"))           # noqa: E731
    corpus = J(os.path.join(HERE, "image_corpus.json"))
    dedup = J(os.path.join(HERE, "dedup_clusters.json"))
    review = J(os.path.join(HERE, "data", "dedup_review.json"))
    vr3 = J(os.path.join(HERE, "data", "visual_review.json"))
    vr31 = J(os.path.join(HERE, "data", "visual_review_v31.json"))
    sa = J(os.path.join(HERE, "source_access.json"))
    em = J(os.path.join(HERE, "evidence_matrix.json"))
    ev_keys = set(em.get("by_unit", {}))                       # الوحداتُ التي استُشهد بها لقاعدةٍ ما (V3)
    tg = telegram_reconcile(J(STATE), corpus, ev_keys, open(CATALOG, encoding="utf-8").read())
    docs = load_docs()
    cr = corpus_reconcile(corpus, dedup, review, vr3, vr31, sa, docs, uploads_dir=uploads_dir)
    tx = transcript_images(transcript, corpus, uploads_dir) if transcript else {"status": "NOT_SCANNED"}
    res = {"tool": "v31_reconcile", "telegram": tg, "corpus": cr, "transcript": tx}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=dict)
    print(json.dumps(tg["totals"], ensure_ascii=False))
    for s in tg["sends"]:
        print("إرسال", s["sent_utc"], s["count"], s["ids"][0], "…", s["ids"][-1])
    for r in cr["table"]:
        print(f"{r['metric']:32} V3={r['v3']} · V3.1={r['v31']}")
    print("سجلُّ المحادثة:", json.dumps({k: v for k, v in tx.items() if k != "unmatched_detail"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    up = sys.argv[sys.argv.index("--uploads") + 1] if "--uploads" in sys.argv else None
    tr = sys.argv[sys.argv.index("--transcript") + 1] if "--transcript" in sys.argv else None
    raise SystemExit(main(uploads_dir=up, transcript=tr))
