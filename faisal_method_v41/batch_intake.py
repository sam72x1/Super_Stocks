# -*- coding: utf-8 -*-
"""
🧾 FAISAL V4.1 — استلامُ دفعةٍ أماميّة (‏2026-10-07 · دفعةُ صور المالك «48» · العقد `V41_prereg.md` §⑥ · V4 مجمَّد FV41).

الصورُ **تقيس V4 ولا تدرّبه**: لا قاعدةَ ولا عتبةَ ولا حالةَ ذهبيّة تتغيّر بها (ما تُظهره يذهب إلى `V4_2_RESEARCH_QUEUE.md`).

المراحلُ ثلاثٌ وكلٌّ يُدفَع قبل التالية ⟵ **ترتيبُ git دليلُ الترتيب** (مُدخَلٌ مختوم ⟵ قرارُ V4 ⟵ ثمّ كلمةُ فيصل):
  `manifest`  ⟵ `PROSPECTIVE_BATCH_<N>_MANIFEST.json` و`_CONTAMINATION.md` — من ملفّات الصور وسجلّ بيانات الجامع
               (`telegram_collect_meta.jsonl`) ونصّ OCR المحفوظ و`input_annotations.json` (الرمزُ والتاريخُ والفريم والكاتب
               **ووجودُ عبارة قرار** — بلا كلمة القرار) · ثمّ قيودُ المرشَّحين والحالات في السجلّ الإلحاقيّ (`seal`).
  [`faisal_v41.yml` run على main ⟵ قراراتُ V4 المجمَّد مختومةٌ ومدفوعةٌ بيد Actions]
  `results`   ⟵ بعد قيود فيصل (`faisal_annotations.json` ⟵ `record_faisal`): `_RESULTS.json` و`_REPORT.md` و`BATCH_SEAL.json`.

🔒 لا شبكة · لا تلغرام · لا تشغيلَ لـV4 هنا (V4 يُشغَّل على Actions وحدَها بالمشغّل المجمَّد) · والأرقامُ كلُّها مولَّدةٌ لا محرَّرة.
⚠️ **حدُّ العمى (§4 من أمر المالك):** المحلّلُ نفسُه يفتح الصورة ليقرأ الرمزَ والتاريخ ⟵ يرى الشارتَ وما عليه. الضمانُ ليس عمى القارئ بل
   **أنّ V4 كودٌ مجمَّد** (FV41) مُدخَلُه الرمزُ والتاريخُ وحدَهما (FV48 بالـAST) **وأنّ كلمةَ فيصل لا تُكتب قبل قيد V4** (`ledger.verify`).
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V3 = os.path.join(ROOT, "faisal_method_v3")
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (V4, V3, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import corpus_build as CB      # noqa: E402 — بصماتُ V3 الإدراكيّة نفسُها وعتباتُها (لا رقمَ جديد)
import ledger as LG            # noqa: E402

BATCH_ID = "B48_20261007"
EXPECTED = 48                                   # ما قاله المالك — يُتحقَّق منه لا يُفترض
BATCH_DIR = os.path.join(HERE, "batches", BATCH_ID)
META_FILE = os.path.join(ROOT, "telegram_collect_meta.jsonl")
CORPUS = os.path.join(V3, "image_corpus.json")
CASES_V4 = os.path.join(V4, "results", "cases_v4.json")
GOLDEN = os.path.join(V3, "v31", "golden_cases_v31.json")
EVIDENCE = os.path.join(V3, "evidence_matrix.json")
VISUAL_V31 = os.path.join(V3, "data", "visual_review_v31.json")
INPUT_ANN = os.path.join(BATCH_DIR, "input_annotations.json")
FAISAL_ANN = os.path.join(BATCH_DIR, "faisal_annotations.json")
OCR_FILE = os.path.join(BATCH_DIR, "ocr_text.json")
OCR_ENGINE = "tesseract · eng+ara · psm 3"     # = محرّكُ مدوّنة V3 (corpus_build.collect_ocr)

CLASSES = ("CLEAN_PROSPECTIVE", "CONTAMINATED", "DUPLICATE", "DERIVATIVE", "UNKNOWN")
ERRORS = ("MATCH", "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN", "NOT_COMPARABLE")
CAUSES = ("NONE", "EXTERNAL_INFORMATION_GAP", "DATA_GAP", "DISCRETIONARY", "IMPLEMENTATION_BUG", "METHODOLOGY_GAP", "UNRESOLVED")
IMG_KINDS = ("photo", "document")
RECEIVED = ("saved", "dup", "seen", "perm_failed", "deferred", "failed")   # صورةٌ وصلت البوت (محفوظةً أو لا)


def _j(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha_obj(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 16), b""):
            h.update(ch)
    return h.hexdigest()


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True, default=str)
        f.write("\n")


# ── ① ما وصل: صفوفُ الجامع ⟵ عناصرُ الدفعة ────────────────────────────────────
def load_meta(path=META_FILE):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def batch_rows(rows, run_ids):
    """صفوفُ تشغيلات الدفعة (`run_ids` صريحة — لا «كلُّ ما في الملفّ») التي تحمل صورةً وصلت البوت ⟵ مرتّبةٌ برقم الرسالة.
    آخرُ صفٍّ لكلّ رسالةٍ يحكم (إعادةُ تشغيلٍ بعد إخفاقٍ عابر تكتب صفًّا جديدًا)."""
    keep = {}
    for r in rows:
        if str(r.get("run_id")) not in {str(x) for x in run_ids}:
            continue
        if r.get("kind") in IMG_KINDS and r.get("status") in RECEIVED:
            keep[r.get("message_id")] = r
    return [keep[k] for k in sorted(keep, key=lambda x: int(x or 0))]


def non_image_rows(rows, run_ids):
    """ما وصل في التشغيلات نفسِها بلا صورة: نصٌّ أو وسائطُ مرفوضة (فيديو/ملصق…) — يُعَدّ ولا يُهمَل."""
    return [r for r in rows if str(r.get("run_id")) in {str(x) for x in run_ids}
            and (r.get("kind") not in IMG_KINDS or str(r.get("status", "")).startswith("dropped"))]


# ── ② البصمات والنصّ ───────────────────────────────────────────────────────────
def fingerprint(path):
    """(sha256 · bytes · العرض · الارتفاع · الصيغة · dhash256 · phash64) — دوالُّ V3 نفسُها. فاشلةٌ ⟵ None (غيرُ قابلةٍ للقراءة)."""
    try:
        fp = CB.image_fingerprint(path)
    except Exception:                                                   # noqa: BLE001
        return None
    return {"sha256": sha_file(path), "bytes": os.path.getsize(path), "width": fp["width"], "height": fp["height"],
            "format": fp["format"], "dhash256": fp["dhash256"], "phash64": fp["phash64"]}


def ocr_image(path):
    """نصُّ OCR بمحرّك المدوّنة نفسِه (eng+ara · psm 3) — محلّيٌّ وحدَه (السويّةُ تقرأ المحفوظ ولا تُشغّله)."""
    p = subprocess.run(["tesseract", path, "-", "-l", "eng+ara", "--psm", "3"], capture_output=True, text=True)
    ver = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()
    return {"text": p.stdout, "engine": (ver[0] if ver else "tesseract") + " · eng+ara · psm 3"}


def tokens(text):
    return CB.tokens(text or "")


def tok_hash(tok):
    """بصمةُ كلمةٍ واحدة (16 خانة) — يُحفَظ نصُّ OCR للدفعة بصماتٍ لا نصًّا (فيه أسماءُ أفرادٍ في محادثاتٍ خاصّة · المستودعُ عامّ)
    وتُحسب جاكارد على البصمات نفسِها للطرفين ⟵ النتيجةُ = جاكارد النصّين حرفًا."""
    return hashlib.sha256(tok.encode("utf-8")).hexdigest()[:16]


def hashed_tokens(text):
    return {tok_hash(t) for t in tokens(text)}


def jaccard(a, b):
    return (len(a & b) / len(a | b)) if (a or b) else 0.0


# ── ③ التلوّث: مقابل المدوّنة المجمَّدة (722) ووحداتها ودلائل V3/V4 والذهبيّة وصور الدفعة السابقة لها ──────────
def corpus_index():
    c = _j(CORPUS)["images"]
    ev = _j(EVIDENCE, {}).get("by_unit") or {}
    v4c = _j(CASES_V4, {}).get("cases") or []
    in_case = {}
    for x in v4c:
        for s in (x.get("sids") or []) + (x.get("third_party_sids") or []):
            in_case.setdefault(str(s).split("#")[0], []).append(x["case"])
    for r in c:
        r["_tok"] = hashed_tokens(r.get("ocr_text"))
        r["_evidence"] = bool(ev.get(r.get("dup_cluster")))
        r["_v4_cases"] = sorted(set(in_case.get(r["id"], [])))
    return c


def near_hits(fp, toks, others, dmax=CB.DUP_DHASH256_MAX, pmax=CB.DUP_PHASH_MAX, jac=CB.DUP_OCR_JACCARD,
              min_tok=CB.DUP_OCR_MIN_TOKENS):
    """⟵ (exact · near · ocr · nearest) مقابل `others` بقاعدة V3 حرفًا (`corpus_build.dedup`): dHash256 ≤ 24 **و** pHash64 ≤ 10
    · ونصُّ OCR بتشابه جاكارد ≥ 0.85 على 15 كلمةً فأكثر في الطرفين («derivative_text»). (و«أو» تنقض عنقدةَ V3 نفسَها — BB4.)"""
    exact, near, ocr = [], [], []
    best = None
    for o in others:
        if o.get("sha256") == fp["sha256"]:
            exact.append(o["id"])
            continue
        d = CB.hamming_hex(fp["dhash256"], o["dhash256"])
        p = CB.hamming_hex(fp["phash64"], o["phash64"])
        if best is None or (d, p) < (best["dhash256_dist"], best["phash_dist"]):
            best = {"id": o["id"], "dhash256_dist": d, "phash_dist": p}
        if d <= dmax and p <= pmax:
            near.append({"id": o["id"], "dhash256_dist": d, "phash_dist": p})
        ot = o.get("_tok") or set()
        if len(toks) >= min_tok and len(ot) >= min_tok:
            jj = jaccard(toks, ot)
            if jj >= jac:
                ocr.append({"id": o["id"], "jaccard": round(jj, 4)})
    return sorted(exact), sorted(near, key=lambda x: x["id"]), sorted(ocr, key=lambda x: x["id"]), best


def classify(item, ann):
    """التصنيفُ (§2 من أمر المالك) بأسبقيّةٍ مكتوبةٍ قبل أيّ نتيجة ⟵ (الفئة · السبب). نقيّة.

    DUPLICATE  ⟵ نفسُ البايتات (SHA-256) لصورةٍ في المدوّنة أو أسبقَ في الدفعة · أو `file_id` سبق تنزيلُه (الجامع «seen»)
    DERIVATIVE ⟵ بصمةٌ إدراكيّة قريبة (dHash ≤ 24 **و** pHash ≤ 10 · BB4) أو نصُّ OCR شبهُ مطابق (≥ 0.85) — أو مراجعةٌ بصريّة تقول مقصوصٌ/معلَّم
    CONTAMINATED ⟵ الحالةُ نفسُها (الرمزُ والتاريخُ) في حالات V4 أو الذهبيّة · أو مثالٌ سبق أن رآه V3/V4 · أو تاريخُ القرار قبل
                   نافذة الأهليّة 2026-10-03 (مادّةٌ تاريخيّةٌ اكتُشفت متأخّرة)
    UNKNOWN    ⟵ الملفُّ غيرُ مقروء · أو لم يُقرأ بصريًّا بعد · أو الكاتبُ لا يُثبَت (صورةٌ بلا رأس منشورٍ ولا اسم) · أو تاريخُ القرار
                 لا يُثبَت (لا مصدرَ توجيهٍ ولا طابعٌ ظاهر) — **ولا يُفترض أنه فيصل لأنّ أسلوبَه يشبهه**
    CLEAN_PROSPECTIVE ⟵ ما سوى ذلك."""
    if item.get("duplicate_status") not in (None, "NONE"):
        return "DUPLICATE", item["duplicate_status"]
    if item.get("derivative_status") not in (None, "NONE"):
        return "DERIVATIVE", item["derivative_status"]
    if (ann or {}).get("visual_derivative_of"):
        return "DERIVATIVE", "VISUAL:" + ",".join(ann["visual_derivative_of"])
    if not item.get("accessible"):
        return "UNKNOWN", "UNREADABLE"
    if not ann:
        return "UNKNOWN", "NOT_REVIEWED"
    if ann.get("same_case_of"):
        return "CONTAMINATED", "SAME_CASE:" + ",".join(ann["same_case_of"])
    if ann.get("seen_example_of"):
        return "CONTAMINATED", "SEEN_EXAMPLE:" + ",".join(ann["seen_example_of"])
    dd = ann.get("decision_date")
    if dd and dd < LG.WINDOW_START:
        return "CONTAMINATED", f"HISTORICAL_BEFORE_WINDOW:{dd}"
    dmax = ann.get("decision_date_max")                      # حدٌّ أعلى فقط (مثل «أمس» على شمعة 10/02) — يكفي للحكم بأنه قبل النافذة
    if not dd and dmax and dmax < LG.WINDOW_START:
        return "CONTAMINATED", f"HISTORICAL_BEFORE_WINDOW:≤{dmax}"
    if ann.get("author") == "UNKNOWN":
        return "UNKNOWN", "AUTHOR_NOT_ESTABLISHED"
    if not dd:
        return "UNKNOWN", "DATE_NOT_ESTABLISHED"
    return "CLEAN_PROSPECTIVE", "—"


def _first_target(reason):
    """«EXACT:TG_1,TG_2» · «NEAR:…» · «VISUAL:…» · «SAME_CASE:…» ⟵ أوّلُ معرّف (لقرار المرشَّح «DUPLICATE_OF:<id>»)."""
    tail = str(reason or "").split(":", 1)[1] if ":" in str(reason or "") else ""
    return tail.split(",")[0] if tail else ""


def eligibility(cls, ann):
    """حالةُ تحقّقٍ أم مرشَّحٌ مستبعد (قائمةُ السجلّ الثابتة `ledger.EXCLUSIONS`) — النظيفُ وحدَه يصير حالة. نقيّة."""
    a = ann or {}
    r = str(a.get("_reason", ""))
    if cls in ("DUPLICATE", "DERIVATIVE") or (cls == "CONTAMINATED" and not r.startswith("HISTORICAL")):
        t = _first_target(r)
        return None, ("DUPLICATE_OF:" + t) if t else "DUPLICATE_OF"
    if cls == "CONTAMINATED":
        return None, "BEFORE_WINDOW"
    if cls == "UNKNOWN":
        if r == "AUTHOR_NOT_ESTABLISHED" or (a and not a.get("faisal_author")):
            return None, "NOT_FAISAL"
        return None, ("DATE_IMPRECISE" if r == "DATE_NOT_ESTABLISHED" else "NO_DECISION")
    if not a.get("faisal_author"):
        return None, "NOT_FAISAL"
    if not a.get("symbol"):
        return None, "NO_TICKER"
    if not a.get("has_decision_statement"):
        return None, "NO_DECISION"
    return "CASE", None


# ── ④ المقارنة (§7 · §12): نوعُ الخطأ وسببُه حقلان — مكتوبان قبل أيّ نتيجة ─────────────────────────────────────────
def compare(f_label4, v4, fw_verdict, f_external, f_discretionary, v4_consistent=True):
    """⟵ (ERROR · CAUSE). نقيّة.

    ERROR: MATCH (فيصل = V4) · FALSE_READY (V4 READY وفيصل لا) · FALSE_REJECT (V4 REJECT وفيصل لا) · FALSE_WAIT (V4 WAIT وفيصل READY/REJECT)
           · FALSE_UNKNOWN (V4 UNKNOWN وفيصل يقرّر) · NOT_COMPARABLE (فيصل MIXED/UNKNOWN).
    CAUSE (للخطأ وحدَه — MATCH ⟵ NONE): IMPLEMENTATION_BUG (مخرجُ V4 يناقض مواصفته) ⟵ DATA_GAP (جدارُ الجودة أو DATA_INSUFFICIENT) ⟵
           EXTERNAL_INFORMATION_GAP (V4 ينقصه بالبناء ما يعتمد عليه فيصل: قروب/طرح/مضارب/متاح — من `missing_information` أو نصّ فيصل)
           ⟵ DISCRETIONARY (نصُّ فيصل تقديريّ صريح) ⟵ METHODOLOGY_GAP (V4 قرّر من الشارت والمعلومةُ كلُّها فيه وفيصل خالف) ⟵ UNRESOLVED."""
    vs = (v4 or {}).get("state")
    if f_label4 not in ("READY", "WAIT", "REJECT"):
        return "NOT_COMPARABLE", "UNRESOLVED"
    if not v4_consistent:
        return ("MATCH" if f_label4 == vs else _err(vs)), "IMPLEMENTATION_BUG"
    if f_label4 == vs:
        return "MATCH", "NONE"
    err = _err(vs)
    if fw_verdict != "VALID" or (v4 or {}).get("tech_state") == "DATA_INSUFFICIENT":
        return err, "DATA_GAP"
    if (vs == "UNKNOWN" and (v4 or {}).get("missing_information")) or f_external:
        return err, "EXTERNAL_INFORMATION_GAP"
    if f_discretionary:
        return err, "DISCRETIONARY"
    if vs in ("WAIT", "READY", "REJECT"):
        return err, "METHODOLOGY_GAP"
    return err, "UNRESOLVED"


def _err(vs):
    return {"READY": "FALSE_READY", "REJECT": "FALSE_REJECT", "WAIT": "FALSE_WAIT", "UNKNOWN": "FALSE_UNKNOWN"}.get(vs, "NOT_COMPARABLE")


def case_overlap(symbol, date, cases=None, golden=None, days=3):
    """فحصٌ آليٌّ لـ«الحالةِ نفسِها»: الرمزُ ‏+ تاريخٌ ضمن ±`days` في حالات V4 الـ157 أو الذهبيّة (‏`golden_cases_v31.json`) ⟵ معرّفات. نقيّة."""
    import datetime as _dt
    if not symbol or not date:
        return []
    cases = (_j(CASES_V4, {}) or {}).get("cases") or [] if cases is None else cases
    golden = (_j(GOLDEN, {}) or {}).get("dates") or {} if golden is None else golden
    d0 = _dt.date.fromisoformat(date)
    out = []
    for c in cases:
        sd = c.get("statement_date")
        if symbol in (c.get("tickers") or []) and sd and abs((_dt.date.fromisoformat(sd) - d0).days) <= days:
            out.append("V4:" + c["case"])
    g = golden.get(symbol) or {}
    if g.get("asof") and abs((_dt.date.fromisoformat(g["asof"]) - d0).days) <= days:
        out.append("GOLDEN:" + symbol)
    return sorted(out)


# ── ⑤ المانيفست (§1) والتلوّث (§2) ─────────────────────────────────────────────
def _stem(name):
    return os.path.splitext(os.path.basename(str(name or "")))[0]


def build_manifest(run_ids, meta_rows=None, ocr_map=None, ann_map=None, corpus=None, img_dir=None):
    """⟵ المانيفست كاملًا من مُدخَلاته المحفوظة (صفوفُ الجامع · الصور · OCR المحفوظ · `input_annotations.json`). حتميّ:
    يُعاد في السويّة بلا شبكةٍ ولا tesseract فيطابق المدفوع (لا رقمَ باليد)."""
    meta_rows = load_meta() if meta_rows is None else meta_rows
    ocr_map = ((_j(OCR_FILE, {}) or {}).get("texts") or {}) if ocr_map is None else ocr_map
    ann_map = ((_j(INPUT_ANN, {}) or {}).get("images") or {}) if ann_map is None else ann_map
    corpus = corpus_index() if corpus is None else corpus
    img_dir = img_dir or os.path.join(ROOT, "faisal_images")
    rows = batch_rows(meta_rows, run_ids)
    items, prior = [], []
    for r in rows:
        st = r.get("status")
        fname = r.get("saved_name") or (r.get("matched") if st == "dup" else None)
        path = os.path.join(img_dir, fname) if fname else None
        fp = fingerprint(path) if (path and os.path.exists(path)) else None
        iid = _stem(r["saved_name"]) if st == "saved" else f"MSG_{r.get('message_id')}"
        o = (ocr_map.get(iid) or {}) if st == "saved" else {}
        txt = o.get("token_sha")
        toks = set(txt or [])
        dup, deriv = "NONE", "NONE"
        hits = {"exact_corpus": [], "near_corpus": [], "ocr_corpus": [], "exact_batch": [], "near_batch": [], "ocr_batch": [],
                "nearest_corpus": None}
        if st == "seen":
            dup = "SEEN_FILE_ID"
        elif st == "dup":
            dup = "EXACT:" + _stem(r.get("matched"))
        if fp and st == "saved":
            ec, nc, oc, best = near_hits(fp, toks, corpus)
            eb, nb, ob, _ = near_hits(fp, toks, prior)
            hits.update(exact_corpus=ec, near_corpus=nc, ocr_corpus=oc, exact_batch=eb, near_batch=nb, ocr_batch=ob,
                        nearest_corpus=best)
            if ec or eb:
                dup = "EXACT:" + ",".join(ec + eb)
            elif nc or nb:
                deriv = "NEAR:" + ",".join(sorted({x["id"] for x in nc + nb}))
            elif oc or ob:
                deriv = "OCR:" + ",".join(sorted({x["id"] for x in oc + ob}))
            prior.append(dict(fp, id=iid, _tok=toks))
        by_id = {c["id"]: c for c in corpus}
        units = sorted({by_id[x]["dup_cluster"] for x in hits["exact_corpus"] + [h["id"] for h in hits["near_corpus"] + hits["ocr_corpus"]]
                        if x in by_id})
        evid = sorted({x for x in hits["exact_corpus"] + [h["id"] for h in hits["near_corpus"] + hits["ocr_corpus"]]
                       if x in by_id and (by_id[x]["_evidence"] or by_id[x]["_v4_cases"])})
        item = {"image_id": iid, "file": (f"faisal_images/{fname}" if fname else None),
                "telegram": {k: r.get(k) for k in ("message_id", "update_id", "media_group_id", "status", "kind", "from_admin",
                                                    "run_id", "date", "forward", "caption", "links")},
                "telegram_file": r.get("file") or {}, "timestamp_sent_utc": r.get("date"), "collected_utc": r.get("collected_utc"),
                "source": "telegram_bot" + (f" ⟵ forward:{(r.get('forward') or {}).get('type')}" if r.get("forward") else ""),
                "sha256": (fp or {}).get("sha256"), "bytes": (fp or {}).get("bytes"),
                "width": (fp or {}).get("width"), "height": (fp or {}).get("height"), "format": (fp or {}).get("format"),
                "dhash256": (fp or {}).get("dhash256"), "phash64": (fp or {}).get("phash64"),
                "accessible": bool(fp) and st == "saved", "ocr_tokens": len(toks), "ocr_engine": OCR_ENGINE if txt is not None else None,
                "duplicate_status": dup, "derivative_status": deriv, "hits": hits, "corpus_units": units,
                "corpus_evidence_hits": evid}
        ann = ann_map.get(iid)
        if ann:
            auto = case_overlap(ann.get("symbol"), ann.get("decision_date"))
            item["auto_same_case"] = auto
            if auto:
                ann = dict(ann, same_case_of=sorted(set(ann.get("same_case_of") or []) | set(auto)))
        # 🔍 ظلُّ «أو» (BB4): ما كانت القاعدةُ القديمة ستَسِمه قريبًا — للإفصاح لا للحكم
        if fp and st == "saved":
            item["shadow_or_near_corpus"] = sum(1 for o in corpus if CB.hamming_hex(fp["phash64"], o["phash64"]) <= CB.DUP_PHASH_MAX
                                                or CB.hamming_hex(fp["dhash256"], o["dhash256"]) <= CB.DUP_DHASH256_MAX)
        cls, why = classify(item, ann)
        item["visual_review_status"] = ("INPUT_REVIEWED" if ann else "PENDING")
        item["provenance"] = {"telegram_forward": r.get("forward"), "author": (ann or {}).get("author"),
                              "layer": (ann or {}).get("layer"), "date_source": (ann or {}).get("date_source"),
                              "evidence": (ann or {}).get("provenance_evidence")}
        item["class"], item["class_reason"] = cls, why
        a2 = dict(ann or {}, _reason=why)
        kind, excl = eligibility(cls, a2) if cls == "CLEAN_PROSPECTIVE" or cls in CLASSES else (None, None)
        item["validation_case"] = kind == "CASE"
        item["exclusion"] = excl
        items.append(item)
    other = non_image_rows(meta_rows, run_ids)
    counts = {c: sum(1 for i in items if i["class"] == c) for c in CLASSES}
    return {"batch_id": BATCH_ID, "generated_by": "faisal_method_v41/batch_intake.py", "contract": "V41_prereg §⑥ · أمرُ المالك 2026-10-07",
            "expected_by_owner": EXPECTED, "run_ids": [str(x) for x in run_ids],
            "total_received": len(items), "received_not_image": len(other),
            "non_image": [{k: o.get(k) for k in ("message_id", "status", "date", "from_admin", "text", "caption")} for o in other],
            "count_matches_owner": len(items) == EXPECTED, "counts": counts,
            "shadow_or": {"images_flagged_by_or": sum(1 for i in items if (i.get("shadow_or_near_corpus") or 0) > 0),
                          "note": "قاعدةُ «أو» القديمة (BB4) — للإفصاح: كم صورةً كانت ستُوسَم «قريبة» من صورةٍ في المدوّنة"},
            "validation_cases": sum(1 for i in items if i["validation_case"]),
            "window_start": LG.WINDOW_START, "thresholds": {"DUP_DHASH256_MAX": CB.DUP_DHASH256_MAX, "DUP_PHASH_MAX": CB.DUP_PHASH_MAX,
                                                             "DUP_OCR_JACCARD": CB.DUP_OCR_JACCARD,
                                                             "DUP_OCR_MIN_TOKENS": CB.DUP_OCR_MIN_TOKENS},
            "corpus": {"images": len(corpus), "units": len({c["dup_cluster"] for c in corpus}), "file": "faisal_method_v3/image_corpus.json"},
            "items": items}


def render_contamination(m):
    """`PROSPECTIVE_BATCH_<N>_CONTAMINATION.md` من المانيفست وحدَه (لا رقمَ باليد)."""
    t = m["thresholds"]
    c = m["counts"]
    L = [f"# PROSPECTIVE_BATCH_{EXPECTED}_CONTAMINATION — فحصُ التلوّث ({m['batch_id']})", "",
         "> مولَّدٌ من `faisal_method_v41/batch_intake.py` (لا رقمَ باليد) · V4 مجمَّد · الصورُ **تقيس V4 ولا تدرّبه**.", "",
         "## ① القاعدة (مكتوبةٌ في الكود قبل أيّ نتيجة · `batch_intake.classify`)",
         f"- **DUPLICATE** = البايتاتُ نفسُها (SHA-256) لصورةٍ في المدوّنة ({m['corpus']['images']} صورة · {m['corpus']['units']} وحدة) أو أسبقَ في الدفعة ·"
         " أو `file_id` سبق تنزيلُه (الجامع «seen»).",
         f"- **DERIVATIVE** = بصمةٌ إدراكيّةٌ قريبة (dHash256 ≤ {t['DUP_DHASH256_MAX']} **و** pHash64 ≤ {t['DUP_PHASH_MAX']} — قاعدةُ V3 `corpus_build.dedup`"
         f" و`ledger.near_duplicates` · و«أو» القديمة كانت ستَسِم {m['shadow_or']['images_flagged_by_or']} صورةً — BB4)"
         f" · أو نصُّ OCR بجاكارد ≥ {t['DUP_OCR_JACCARD']} على {t['DUP_OCR_MIN_TOKENS']} كلمةً فأكثر · أو مراجعةٌ بصريّةٌ تقول مقصوصٌ/معلَّم.",
         "- **CONTAMINATED** = الحالةُ نفسُها (الرمزُ وتاريخُ القرار ±3 أيّام) في حالات V4 (157) أو الذهبيّة · أو مثالٌ رآه V3/V4 · أو تاريخُ القرار"
         f" (أو حدُّه الأعلى الظاهر) قبل نافذة الأهليّة **{m['window_start']}** (مادّةٌ تاريخيّة).",
         "- **UNKNOWN** = غيرُ مقروء · أو لم يُراجَع بصريًّا · أو الكاتبُ لا يُثبَت (صورةٌ بلا رأس منشورٍ ولا اسم — ولا يُفترض أنه فيصل)"
         " · أو تاريخُ القرار لا يُثبَت (لا مصدرَ توجيهٍ ولا طابعٌ ظاهر).",
         "- **CLEAN_PROSPECTIVE** = ما سوى ذلك — **وحدَه يدخل النتيجةَ الأساسيّة**.", "",
         "## ② الأعداد",
         f"- **TOTAL_RECEIVED {m['total_received']}** (صورٌ وصلت البوت في تشغيلات الجامع {', '.join('`' + x + '`' for x in m['run_ids'])})"
         f" · ما قاله المالك {m['expected_by_owner']} ⟵ **{'يطابق' if m['count_matches_owner'] else 'لا يطابق'}**"
         f" · رسائلُ بلا صورة {m['received_not_image']}.",
         "- " + " · ".join(f"**{k} {c[k]}**" for k in CLASSES),
         f"- **VALIDATION CASES {m['validation_cases']}** (نظيفٌ ‏+ فيصل ‏+ رمزٌ واحد ‏+ عبارةُ قرار — `V41_prereg §⑥`).", "",
         "## ③ لكلّ صورة",
         "| الصورة | الرسالة | أُرسلت | المصدر | الأبعاد | التكرار | الاشتقاق | أقربُ صورةٍ في المدوّنة (dHash/pHash) | الفئة | السبب | حالة؟ |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i in m["items"]:
        nb = i["hits"].get("nearest_corpus") or {}
        L.append(f"| `{i['image_id']}` | {i['telegram'].get('message_id')} | {i['timestamp_sent_utc'] or '—'} | {i['source']} | "
                 f"{i['width'] or '—'}×{i['height'] or '—'} | {i['duplicate_status']} | {i['derivative_status']} | "
                 f"{('`' + nb['id'] + '` ' + str(nb['dhash256_dist']) + '/' + str(nb['phash_dist'])) if nb else '—'} | "
                 f"**{i['class']}** | {i['class_reason']} | {'✅' if i['validation_case'] else (i['exclusion'] or '—')} |")
    L += ["", "## ④ ما لم يُفحص آليًّا (حدودٌ معلنة)",
          "- القصُّ الشديد (مقطعٌ صغيرٌ من شارتٍ أكبر) قد يفلت من البصمة الإدراكيّة ⟵ تغطّيه المقارنةُ بالحالة (الرمز ‏+ التاريخ) والمراجعةُ البصريّة.",
          "- «نفسُ الحالة» تُقرأ من الرمز وتاريخ القرار في `input_annotations.json` — وما لا رمزَ له يبقى UNKNOWN لا CLEAN."]
    return "\n".join(L) + "\n"


# ── ⑥ الختم في السجلّ الإلحاقيّ (قبل V4 · بلا كلمة فيصل) ─────────────────────────
def plan_seal(m, ann_map, existing_cases=0):
    """⟵ قائمةُ القيود المخطَّطة (مرشَّحٌ لكلّ صورةٍ محفوظة ‏+ حالةٌ للنظيف المؤهَّل) — نقيّة حتى تُنفَّذ بـ`apply_seal`.
    صورتان للرمز والتاريخ نفسِهما ⟵ حالةٌ واحدة (الأولى برقم الرسالة) والثانيةُ «DUPLICATE_OF:CASE_…» (لا عدَّ مزدوجًا)."""
    plan, by_key, n = [], {}, existing_cases
    for it in m["items"]:
        if it["telegram"]["status"] != "saved":
            continue                       # لا ملفَّ جديد في faisal_images ⟵ لا مرشَّح (المكرَّرُ مُبلَّغٌ في المانيفست)
        a = ann_map.get(it["image_id"]) or {}
        dec, case = it["exclusion"], None
        if it["validation_case"]:
            key = (a["symbol"], a["decision_date"])
            if key in by_key:
                dec = "DUPLICATE_OF:" + by_key[key]
            else:
                n += 1
                cid = f"CASE_{n:04d}"
                by_key[key] = cid
                dec = "CASE:" + cid
                case = {"case_id": cid, "symbol": a["symbol"], "decision_date": a["decision_date"], "date_precision": "day",
                        "date_source": a["date_source"], "timeframe_f": a.get("timeframe"), "image": it["file"],
                        "image_sha256": it["sha256"], "layer": str(a["layer"]), "capture_utc": it["timestamp_sent_utc"],
                        "near_duplicates": [], "unit_id": it["image_id"],
                        "notes": f"{BATCH_ID} · رسالة {it['telegram']['message_id']}"}
                if a.get("decision_time"):
                    case["decision_time"] = a["decision_time"]
                if a.get("post_url"):
                    case["post_url"] = a["post_url"]
        plan.append({"unit_id": it["image_id"], "image": it["file"], "sha256": it["sha256"], "decision": dec,
                     "note": f"{BATCH_ID} · {it['class']} · {it['class_reason']}", "case": case})
    return plan


def apply_seal(plan, utc, ledger=None):
    """يُنفّذ الخطّة في السجلّ (`record_candidate` ثمّ `seal_case`) ⟵ القيود. يتحقّق قبلها أنّ النسخةَ القريبة فارغةٌ فعلًا."""
    lg = ledger or LG.Ledger()
    out = []
    for p in plan:
        out.append(lg.record_candidate(p["unit_id"], p["image"], p["sha256"], p["decision"], utc, note=p["note"]))
        if p["case"]:
            nd = LG.near_duplicates(os.path.join(ROOT, p["image"]))
            if nd:
                raise LG.SchemaError(f"{p['unit_id']}: نسخةٌ قريبة {nd} — لا حالة")
            out.append(lg.seal_case(p["case"], utc))
    return out


# ── ⑦ النتائج (بعد قيد فيصل) ───────────────────────────────────────────────────
MISSING_KINDS = ("group information", "offering", "short availability", "float", "trader identity/context", "timestamp",
                 "another external factor", "manual judgment", "unavailable data")
_CTX_KIND = {"groups": "group information", "offering_pending": "offering", "operator_press": "trader identity/context",
             "short_available": "short availability"}


def batch_case_ids(lg, batch_id=BATCH_ID):
    """حالاتُ هذه الدفعة من السجلّ (ملاحظةُ الحالة تحمل معرّفَ الدفعة) — مرتّبة."""
    out = []
    for e in lg.entries("case"):
        c = lg.read(e["path"])
        if str(c.get("notes", "")).startswith(batch_id) and e["case_id"] not in out:
            out.append(e["case_id"])
    return sorted(out)


def v4_fields(rec):
    """حقولُ §5 من أمر المالك ⟵ من قيد V4 المختوم وحدَه."""
    d = rec.get("decision") or {}
    fw = rec.get("firewall") or {}
    prov = rec.get("context_provenance") or {}
    ext = sorted({_CTX_KIND.get(k, k) for k, v in prov.items() if str(v).startswith("UNAVAILABLE")})
    return {"V4_STATE": d.get("state"), "V4_TECH_STATE": d.get("tech_state"), "V4_REASON": d.get("explain"),
            "RULE_IDS": d.get("rule_ids") or [], "PATTERN": d.get("patterns") or [], "STRUCTURE": d.get("structure"),
            "SUPPORT": d.get("support_resistance"), "ENTRY": d.get("entry"), "INVALIDATION": d.get("invalidation"),
            "TARGET": d.get("target"), "DATA_QUALITY": {"verdict": fw.get("verdict"), "fails": fw.get("fails"), "warns": fw.get("warns"),
                                                         "bars": fw.get("bars"), "last_bar": fw.get("last_bar")},
            "EXTERNAL_DATA_REQUIRED": {"missing_information": d.get("missing_information") or [], "context_unavailable": ext},
            "BLOCKING": d.get("blocking_reasons") or [], "ASOF": d.get("asof")}


def build_results(manifest, f_ann_map, ledger=None, consistent=None):
    """⟵ `PROSPECTIVE_BATCH_<N>_RESULTS.json` — من المانيفست والسجلّ (V4 · فيصل) و`faisal_annotations.json`. حتميّ."""
    lg = ledger or LG.Ledger()
    if consistent is None:
        import analysis as AN                                   # noqa: PLC0415 — `consistent` بمواصفة V4 نفسِها
        consistent = AN.consistent
    rows = []
    for cid in batch_case_ids(lg):
        c_e = lg.entries("case", cid)[-1]
        case = lg.read(c_e["path"])
        vs = [e for e in lg.entries("v4", cid) if e.get("case_version") == c_e["version"]]
        fs = lg.entries("faisal", cid)
        inv = lg.entries("invalid", cid)
        v4 = lg.read(vs[-1]["path"]) if vs else None
        fr = lg.read(fs[-1]["path"]) if fs else None
        fa = f_ann_map.get(cid) or {}
        vf = v4_fields(v4) if v4 else {}
        d = (v4 or {}).get("decision") or {}
        ok = consistent({"tech_state": d.get("tech_state"), "state": d.get("state"), "missing": d.get("missing_information")}) if v4 else True
        err, cause = (compare((fr or {}).get("label4"), d, ((v4 or {}).get("firewall") or {}).get("verdict"),
                              bool(fa.get("external_refs")), bool(fa.get("discretionary")), ok) if (v4 and fr)
                      else ("NOT_COMPARABLE", "UNRESOLVED"))
        rows.append({"CASE_ID": cid, "symbol": case["symbol"], "decision_date": case["decision_date"], "date_source": case["date_source"],
                     "timeframe_f": case.get("timeframe_f"), "image": case["image"], "layer": case["layer"],
                     "v4_seq": vs[-1]["seq"] if vs else None, "faisal_seq": fs[-1]["seq"] if fs else None,
                     "order_ok": bool(vs and fs and vs[-1]["seq"] < fs[-1]["seq"]), "invalid": [lg.read(e["path"]) for e in inv],
                     **vf, "FAISAL_STATE": (fr or {}).get("label4"), "FAISAL_LABEL": (fr or {}).get("label"),
                     "FAISAL_QUOTE": (fr or {}).get("quote"), "FAISAL_EVIDENCE": fa.get("evidence"),
                     "FAISAL_EXTERNAL_REFS": fa.get("external_refs") or [], "FAISAL_DISCRETIONARY": bool(fa.get("discretionary")),
                     "pattern_f": (fr or {}).get("pattern_f"), "v4_consistent": ok, "ERROR": err, "CAUSE": cause,
                     "chart_alone": fa.get("chart_alone"), "missing_for_v4": fa.get("missing_for_v4") or []})
    return rows


STATES4 = ("READY", "WAIT", "REJECT", "UNKNOWN")


def aggregate(rows):
    """§10 · §15: الأعدادُ على النظيف وحدَه (الصفوفُ = حالاتُ الدفعة) — بلا ادّعاء دلالة (فاصلُ ويلسون حين N ≥ 10 فقط)."""
    import analysis as AN                                       # noqa: PLC0415
    comp = [r for r in rows if r["ERROR"] != "NOT_COMPARABLE" and not r["invalid"]]
    n = len(comp)
    exact = sum(1 for r in comp if r["ERROR"] == "MATCH")
    by_state = {}
    for s in STATES4:
        fs = [r for r in comp if r["FAISAL_STATE"] == s]
        by_state[s] = {"FAISAL": len(fs), "V4": sum(1 for r in comp if r["V4_STATE"] == s),
                       "agree": sum(1 for r in fs if r["V4_STATE"] == s),
                       "false_READY": sum(1 for r in comp if r["V4_STATE"] == "READY" and r["FAISAL_STATE"] == s and s != "READY"),
                       "false_WAIT": sum(1 for r in fs if r["V4_STATE"] == "WAIT" and s != "WAIT"),
                       "false_REJECT": sum(1 for r in fs if r["V4_STATE"] == "REJECT" and s != "REJECT"),
                       "false_UNKNOWN": sum(1 for r in fs if r["V4_STATE"] == "UNKNOWN" and s != "UNKNOWN")}

    def brk(key):
        out = {}
        for r in comp:
            k = str(key(r))
            o = out.setdefault(k, {"n": 0, "match": 0})
            o["n"] += 1
            o["match"] += r["ERROR"] == "MATCH"
        return dict(sorted(out.items()))
    err = {e: sum(1 for r in rows if r["ERROR"] == e) for e in ERRORS}
    cause = {c: sum(1 for r in rows if r["ERROR"] not in ("MATCH",) and r["CAUSE"] == c) for c in CAUSES}
    return {"N": n, "exact": exact, "exact_rate": (round(exact / n, 4) if n else None),
            "exact_wilson": (AN.wilson(exact, n) if n >= AN.WILSON_MIN else f"INSUFFICIENT (N={n} < {AN.WILSON_MIN})"),
            "always_wait_baseline": {"agree": sum(1 for r in comp if r["FAISAL_STATE"] == "WAIT"), "n": n},
            "by_state": by_state, "errors": err, "causes": cause,
            "invalid_for_validation": sum(1 for r in rows if r["invalid"]),
            "not_comparable": sum(1 for r in rows if r["ERROR"] == "NOT_COMPARABLE"),
            "breakdown": {"pattern": brk(lambda r: (r.get("pattern_f") or "UNSPECIFIED")),
                          "timeframe": brk(lambda r: r.get("timeframe_f") or "UNKNOWN"),
                          "decision_state": brk(lambda r: r["FAISAL_STATE"]),
                          "source": brk(lambda r: r.get("date_source")),
                          "provenance": brk(lambda r: f"layer {r.get('layer')}")}}


def final_block(m, agg, frozen, changed, n_cases):
    """كتلةُ §15 بنصّ المالك حرفًا — من الأرقام المولَّدة وحدَها."""
    c = m["counts"]
    cs = agg["causes"]
    return "\n".join([
        f"V4 FROZEN = {'YES' if frozen else 'NO'}",
        f"48 IMAGES RECEIVED = {m['total_received']}",
        f"CLEAN PROSPECTIVE = {c['CLEAN_PROSPECTIVE']}",
        f"CONTAMINATED = {c['CONTAMINATED']}",
        f"DUPLICATES = {c['DUPLICATE']}",
        f"VALIDATION CASES = {n_cases}",
        f"EXACT MATCH = {agg['exact']}",
        f"FALSE READY = {agg['errors']['FALSE_READY']}",
        f"FALSE WAIT = {agg['errors']['FALSE_WAIT']}",
        f"FALSE REJECT = {agg['errors']['FALSE_REJECT']}",
        f"FALSE UNKNOWN = {agg['errors']['FALSE_UNKNOWN']}",
        f"EXTERNAL INFORMATION GAPS = {cs['EXTERNAL_INFORMATION_GAP']}",
        f"DATA GAPS = {cs['DATA_GAP']}",
        f"METHODOLOGY GAPS = {cs['METHODOLOGY_GAP']}",
        f"UNRESOLVED = {cs['UNRESOLVED']}",
        f"V4 CHANGED DURING VALIDATION = {'YES — BATCH RESULT INVALIDATED' if changed else 'NO'}"])


def render_report(m, rows, agg, fz, final, seal=None):
    """`PROSPECTIVE_BATCH_<N>_REPORT.md` — الجوابُ أوّلًا (§11) ثمّ كتلةُ §15 حرفًا ثمّ التفصيل. كلُّ رقمٍ من JSON."""
    c = m["counts"]
    mism = [r for r in rows if r["ERROR"] not in ("MATCH",)]
    L = [f"# PROSPECTIVE_BATCH_{EXPECTED}_REPORT — دفعةُ المالك ({m['batch_id']})", "",
         "> مولَّدٌ من `faisal_method_v41/batch_intake.py` (لا رقمَ باليد) · V4 مجمَّد بت-بت · الصورُ **تقيس V4 ولا تدرّبه**.", "",
         "## ① الجوابُ أوّلًا (§11: هل طابق V4 قراراتِ فيصل **الجديدة** دون أن يتغيّر بعد رؤيتها؟)",
         (f"- حالاتٌ قورنت **{agg['N']}** · تطابقٌ تامّ **{agg['exact']}**" +
          (f" ({agg['exact_rate']:.1%})" if agg['exact_rate'] is not None else "") +
          f" · فاصلٌ: {agg['exact_wilson']} · وخطُّ «دائمًا WAIT» {agg['always_wait_baseline']['agree']}/{agg['always_wait_baseline']['n']}."),
         f"- **V4 لم يتغيّر أثناء التحقّق** (FV41 · بصمةُ التجميد `{fz['freeze_id'][:16]}…` قبل الدفعة وبعدها) — والترتيبُ مختومٌ في السجلّ:"
         " كلُّ قيد V4 قبل قيد فيصل لحالته.", "",
         "## ② كتلةُ §15", "```", final, "```", "",
         "## ③ الاستلام (§1 · §9)",
         f"- **TOTAL_RECEIVED {m['total_received']}** مقابل {m['expected_by_owner']} قالها المالك ⟵ "
         f"**{'يطابق' if m['count_matches_owner'] else 'لا يطابق'}** · رسائلُ بلا صورة {m['received_not_image']} · تشغيلاتُ الجامع "
         + ", ".join("`" + x + "`" for x in m["run_ids"]) + ".",
         "- " + " · ".join(f"{k} **{c[k]}**" for k in CLASSES) + " ⟵ التفصيلُ في `PROSPECTIVE_BATCH_48_CONTAMINATION.md`.", "",
         "## ④ التجميد (§3)",
         f"- commit التجميد الرسميّ `{fz['official_freeze_commit']}` · `FREEZE_ID {fz['freeze_id']}` · المراجعة {fz['rev']} · "
         f"`config_hash {fz['config_hash']}` · ملفّات {fz['n_files']} · آخرُ تغييرٍ في نواة المحرّك `{fz['engine_last_change_commit'][:7]}` "
         f"({fz['engine_last_change_utc']}).",
         f"- المحرّك `{fz['engine_version']}` · القواعد `{fz['rules_version']}` · المشغّل `{fz['runner_version']}` · بصمةُ رسم القرار "
         f"`{fz['decision_graph_sha256'][:16]}…` · بصمةُ رسم القواعد V3 `{fz['rule_graph_sha256'][:16]}…` · المدوّنة `{fz['corpus_sha256'][:16]}…` "
         f"({fz['corpus_images']} صورة) · حالاتُ V4 `{fz['cases_v4_sha256'][:16]}…` · ختمُ الاحتجاز `{fz['holdout_seal'][:16]}…`.", "",
         "## ⑤ العمى (§4) — الحدُّ بنصّه",
         "- **لم يكن عمًى تقنيًّا كاملًا ولا يُدّعى:** المحلّلُ نفسُه فتح كلَّ صورةٍ ليقرأ الرمزَ والتاريخَ والفريمَ ووجودَ عبارة القرار — فرأى"
         " الشارتَ وما عليه (حدٌّ مسجَّلٌ سلفًا في `V41_prereg §⑥`).",
         "- **الضماناتُ الفعليّة:** ① V4 كودٌ مجمَّد (FV41) لا يتغيّر برؤية أحد · ② مُدخَلُه الرمزُ وتاريخُ القرار والسياقُ الآليّ وحدَها (FV48 بالـAST)"
         " · ③ الحالاتُ خُتمت ودُمجت في main **قبل** تشغيل V4 · ④ V4 شُغّل على Actions وقيدُه دُفع بيد Actions · ⑤ كلمةُ فيصل كُتبت **بعد** قيد V4"
         " لحالتها (`ledger.verify` · ORDER) — وترتيبُ git نفسُه شاهد.", "",
         "## ⑥ لكلّ حالة (§5-7)",
         "| الحالة | الرمز | تاريخ القرار | فيصل | V4 (الفنّيّة) | الخطأ | السبب | جودةُ البيانات |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['CASE_ID']}` | {r['symbol']} | {r['decision_date']} | {r['FAISAL_STATE'] or '—'} | {r.get('V4_STATE') or '—'}"
                 f" ({r.get('V4_TECH_STATE') or '—'}) | **{r['ERROR']}** | {r['CAUSE']} | {(r.get('DATA_QUALITY') or {}).get('verdict') or '—'} |")
    L += ["", "## ⑦ حسب الفئة (§10 · النظيفُ وحدَه · بلا ادّعاء دلالة)", "",
          "| حالةُ فيصل | فيصل | V4 | اتّفاق | READY كاذب | WAIT كاذب | REJECT كاذب | UNKNOWN كاذب |", "|---|---|---|---|---|---|---|---|"]
    for s in STATES4:
        b = agg["by_state"][s]
        L.append(f"| {s} | {b['FAISAL']} | {b['V4']} | {b['agree']} | {b['false_READY']} | {b['false_WAIT']} | {b['false_REJECT']} | {b['false_UNKNOWN']} |")
    for k, title in (("pattern", "النموذج"), ("timeframe", "الفريم"), ("decision_state", "حالة القرار"), ("source", "مصدر التاريخ"),
                     ("provenance", "الطبقة")):
        L.append("")
        L.append(f"- **{title}:** " + (" · ".join(f"{kk} {vv['match']}/{vv['n']}" for kk, vv in agg["breakdown"][k].items()) or "—"))
    L += ["", "## ⑧ المعلومةُ الخارجيّة لكلّ خلاف (§12)"]
    if not mism:
        L.append("- لا خلاف.")
    for r in mism:
        L.append(f"- `{r['CASE_ID']}` {r['symbol']}: **{r['ERROR']} · {r['CAUSE']}** — هل يعيده V4 من الشارت وحدَه؟ "
                 f"**{r.get('chart_alone') or 'UNKNOWN'}** · الناقص: {', '.join(r.get('missing_for_v4') or []) or '—'} · "
                 f"V4 ينقصه بنفسه: {', '.join((r.get('EXTERNAL_DATA_REQUIRED') or {}).get('missing_information') or []) or '—'}")
    L += ["", "## ⑨ لا تغييرَ قواعد (§8)",
          "- ما ظهر من أنماطٍ ذهب إلى `V4_2_RESEARCH_QUEUE.md` (بندُ الدفعة) — **ولم يدخل V4 منه شيء**."]
    if seal:
        L += ["", "## ⑩ الختم (§13)", f"- `BATCH_SEAL.json` · بصمةُ الختم `{seal}`."]
    return "\n".join(L) + "\n"
