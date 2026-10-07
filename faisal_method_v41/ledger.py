# -*- coding: utf-8 -*-
"""
📒 FAISAL V4.1 — السجلُّ الأماميّ الإلحاقيّ (§25-27 · §29 · العقد `V41_prereg.md` §⑥).

الترتيبُ الإلزاميّ لكلّ حالة: **ختمُ المُدخَل** (`seal_case`) ⟵ **قرارُ V4 المجمَّد** (`record_v4` — يرفض بلا حالةٍ مختومة) ⟵ **ثمّ وحدَه كلمةُ
فيصل** (`record_faisal` — يرفض بلا قرار V4 مختومٍ قبله · FV48) ⟵ المقارنة. ولكلّ وحدةٍ جديدة سجلُّ مرشَّح (`record_candidate`) بقرار ضمٍّ أو
سببِ استبعادٍ من قائمةٍ ثابتة — لا تخطّيَ صامت.

⚖️ **إلحاقٌ فقط (FV47):** كلُّ قيدٍ ملفٌّ جديد لا يُعاد كتابتُه (`AppendOnlyError`) · والتصحيحُ نسخةٌ جديدة بـ`supersedes` · و`manifest.json`
سلسلةٌ (بصمةُ القيد السابق في كلّ قيد) تكشف الحذفَ وإعادةَ الترتيب والتحريرَ اللاحق (`verify` · FV44/FV46).
لا شبكةَ هنا ولا تلغرام · والطوابعُ الزمنيّةُ تُمرَّر صراحةً (حتميّةٌ في السويّة).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (V4, os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LEDGER_DIR = os.path.join(HERE, "prospective_validation")
WINDOW_START = "2026-10-03"           # العقد §⑥: أوّلُ يومٍ كاملٍ بعد آخر تغييرٍ في نواة المحرّك (d8b4937 · 2026-10-02 21:36 UTC)
KINDS = ("candidate", "case", "v4", "faisal", "invalid")
EXCLUSIONS = ("NOT_FAISAL", "NO_TICKER", "NO_DECISION", "DATE_IMPRECISE", "BEFORE_WINDOW", "DUPLICATE_OF")
LABELS = ("READY", "WAIT", "WATCH", "REJECT", "UNKNOWN", "MIXED")
L4 = {"READY": "READY", "WAIT": "WAIT", "WATCH": "WAIT", "REJECT": "REJECT", "UNKNOWN": "UNKNOWN", "MIXED": "MIXED"}  # = v4_cases.L4 ‏+ UNKNOWN/MIXED
# §18: سجلُّ الهدف — 50٪/70٪/100٪ لا يُفترض معناها: النصُّ حرفيًّا ومرجعُ النسبة (من الدخول؟ من القاع؟ من الارتفاع؟) أو UNKNOWN
TARGET_FIELDS = ("TARGET_SOURCE", "TARGET_FORMULA", "SOURCE_IMAGE", "ENTRY_PRICE", "SUPPORT_PRICE", "TARGET_PRICE", "PERCENTAGE",
                 "PERCENTAGE_TEXT", "PERCENTAGE_REFERENCE", "AUTHOR", "EVIDENCE_STATUS")
PCT_REFS = ("FROM_ENTRY", "FROM_BOTTOM", "OF_RISE", "OTHER", "UNKNOWN")
EVIDENCE = ("CONFIRMED", "SUPPORTED", "PROBABLE", "POSSIBLE", "CONTRADICTED", "UNKNOWN")
CASE_ID = re.compile(r"^CASE_\d{4}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# المخطّط (§25 · يُكتب في docs/V4_PROSPECTIVE_SCHEMA.json) — الحقولُ المطلوبة لكلّ نوع
SCHEMA = {
    "case": {"required": ["case_id", "symbol", "decision_date", "date_precision", "date_source", "timeframe_f", "image", "image_sha256",
                          "layer", "capture_utc", "near_duplicates"],
             "optional": ["decision_time", "post_url", "unit_id", "supersedes", "correction_reason", "notes"],
             "enums": {"date_precision": ["day"], "date_source": ["image_visible", "forward_origin", "owner_attested"],
                       "layer": ["1", "2"]},
             "note": "مُدخَلُ المحرّك وحدَه: الرمزُ والتاريخ — لا كلمةَ قرارٍ ولا مستوياتٍ لفيصل هنا (تُكتب بعد قرار V4)"},
    "v4": {"required": ["case_id", "case_path", "case_sha256", "freeze_id", "freeze_rev", "snapshot_path", "snapshot_sha256",
                        "decision", "decision_sha256", "firewall", "context", "context_provenance", "meta"],
           "note": "قرارُ V4 المجمَّد على لقطة الشموع قبل يوم القرار حصرًا ‏+ بصماتُ الجالبين وcommit التشغيلة"},
    "faisal": {"required": ["case_id", "label", "label4", "quote", "after_v4_seq", "v4_decision_sha256"],
               "optional": ["levels_f", "plan_f", "pattern_f", "targets_f", "entry_f", "invalidation_f", "external_codes",
                            "tech_ready_f", "orders_f", "support_f", "timeframe_f", "supersedes", "correction_reason", "notes"],
               "enums": {"label": list(LABELS), "label4": ["READY", "WAIT", "REJECT", "UNKNOWN", "MIXED"]},
               "target_fields": list(TARGET_FIELDS), "target_enums": {"PERCENTAGE_REFERENCE": list(PCT_REFS), "EVIDENCE_STATUS": list(EVIDENCE)},
               "note": "يُكتب بعد قرار V4 وحدَه · اقتباسٌ حرفيّ · والأهدافُ بنصّها ومرجعِ نسبتها (من الدخول/القاع/الارتفاع/UNKNOWN)"},
    "invalid": {"required": ["case_id", "reason", "detail"], "note": "INVALID_FOR_VALIDATION — يُعَدّ ويُعلَّل ولا يدخل المقاييس"},
    "candidate": {"required": ["unit_id", "image", "image_sha256", "decision"],
                  "enums": {"decision": ["CASE:<CASE_ID>"] + list(EXCLUSIONS)},
                  "note": "كلُّ وحدةٍ جديدة تصل المستودع بعد التجميد — لا تخطّيَ صامت"},
}


class LedgerError(Exception):
    pass


class AppendOnlyError(LedgerError):
    pass


class DecisionFreezeError(LedgerError):
    pass


class SchemaError(LedgerError):
    pass


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def file_bytes(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_schema(kind, obj):
    spec = SCHEMA[kind]
    miss = [k for k in spec["required"] if k not in obj]
    if miss:
        raise SchemaError(f"{kind}: حقولٌ ناقصة {miss}")
    for k, allowed in (spec.get("enums") or {}).items():
        if k in obj and obj[k] is not None and kind != "candidate" and obj[k] not in allowed:
            raise SchemaError(f"{kind}: {k}={obj[k]!r} خارج {allowed}")
    if kind == "faisal" and obj.get("targets_f") is not None:
        for t in obj["targets_f"]:
            tmiss = [k for k in TARGET_FIELDS if k not in (t or {})]
            if tmiss:
                raise SchemaError(f"هدفٌ بحقولٍ ناقصة {tmiss} (§18 — المجهولُ يُكتب UNKNOWN لا يُحذف)")
            if t["PERCENTAGE_REFERENCE"] not in PCT_REFS or t["EVIDENCE_STATUS"] not in EVIDENCE:
                raise SchemaError("مرجعُ النسبة أو حالةُ الدليل خارج القائمة (§18)")
    return True


class Ledger:
    def __init__(self, root=LEDGER_DIR):
        self.root = root
        self.man_path = os.path.join(root, "manifest.json")

    # ── التخزين ──────────────────────────────────────────────────────────────
    def manifest(self):
        if not os.path.exists(self.man_path):
            return {"schema": 1, "contract": "V41_prereg §⑥", "window_start": WINDOW_START, "entries": []}
        with open(self.man_path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, man):
        os.makedirs(self.root, exist_ok=True)
        with open(self.man_path, "wb") as f:
            f.write(file_bytes(man))

    def _write_new(self, rel, obj):
        path = os.path.join(self.root, rel)
        if os.path.exists(path):
            raise AppendOnlyError(f"موجودٌ سلفًا — الإلحاقُ فقط: {rel}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        b = file_bytes(obj)
        with open(path, "xb") as f:                      # «x» يرفض الكتابةَ فوق ملفٍّ قائم حتى في السباق
            f.write(b)
        return hashlib.sha256(b).hexdigest()

    def _append(self, kind, case_id, rel, file_sha, utc, **extra):
        man = self.manifest()
        ent = man["entries"]
        e = {"seq": len(ent) + 1, "kind": kind, "case_id": case_id, "path": rel, "sha256": file_sha,
             "prev": ent[-1]["entry_hash"] if ent else "GENESIS", "utc": utc}
        e.update(extra)
        e["entry_hash"] = sha(e)
        ent.append(e)
        self._save(man)
        return e

    def entries(self, kind=None, case_id=None):
        return [e for e in self.manifest()["entries"] if (kind is None or e["kind"] == kind)
                and (case_id is None or e["case_id"] == case_id)]

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return json.load(f)

    # ── القيود ───────────────────────────────────────────────────────────────
    def record_candidate(self, unit_id, image, image_sha256, decision, utc, note=""):
        ok = decision in EXCLUSIONS or bool(re.fullmatch(r"CASE:CASE_\d{4}", decision or "")) or (decision or "").startswith("DUPLICATE_OF:")
        if not ok:
            raise SchemaError(f"قرارُ المرشَّح خارج القائمة: {decision!r}")
        obj = {"unit_id": unit_id, "image": image, "image_sha256": image_sha256, "decision": decision, "note": note}
        check_schema("candidate", obj)
        n = len(self.entries("candidate", unit_id)) + 1
        rel = f"candidates/{unit_id}.v{n}.json"
        return self._append("candidate", unit_id, rel, self._write_new(rel, obj), utc)

    def seal_case(self, case, utc):
        check_schema("case", case)
        if not CASE_ID.match(case["case_id"]):
            raise SchemaError("case_id بصيغة CASE_0001")
        if not DATE.match(case["decision_date"] or ""):
            raise SchemaError("decision_date بصيغة YYYY-MM-DD")
        if case["decision_date"] < WINDOW_START:
            raise SchemaError(f"قبل نافذة الأهليّة {WINDOW_START} ⟵ مرشَّحٌ مستبعد (BEFORE_WINDOW) لا حالة")
        if case["near_duplicates"]:
            raise SchemaError("نسخةٌ قريبة من صورةٍ في المدوّنة ⟵ مرشَّحٌ مستبعد (DUPLICATE_OF) لا حالة")
        if str(case["capture_utc"])[:10] < case["decision_date"]:
            raise SchemaError("الالتقاطُ قبل تاريخ القرار — مستحيل")
        prior = self.entries("case", case["case_id"])
        ver = len(prior) + 1
        if ver > 1 and (case.get("supersedes") != ver - 1 or not case.get("correction_reason")):
            raise AppendOnlyError("التصحيحُ نسخةٌ جديدة بـsupersedes = السابقة وسببٍ مكتوب")
        rel = f"cases/{case['case_id']}.v{ver}.json"
        return self._append("case", case["case_id"], rel, self._write_new(rel, case), utc, version=ver)

    def record_v4(self, case_id, payload, snapshot_rows, utc, run_tag="r1"):
        cs = self.entries("case", case_id)
        if not cs:
            raise DecisionFreezeError("لا حالةَ مختومة — الختمُ قبل التشغيل")
        c = cs[-1]
        prior = [e for e in self.entries("v4", case_id) if e.get("case_version") == c["version"]]
        if prior and not (payload.get("meta") or {}).get("invalidates"):
            raise AppendOnlyError("قرارُ V4 لهذه النسخة مختومٌ سلفًا — لا إعادةَ إلّا بمراجعة تجميدٍ تُبطله (§30)")
        k = len(prior) + 1
        snap_rel = f"snapshots/{case_id}.v{c['version']}.{run_tag}{k}.bars.json"
        snap_sha = self._write_new(snap_rel, {"case_id": case_id, "rows": snapshot_rows})
        rec = dict(payload, case_id=case_id, case_path=c["path"], case_sha256=c["sha256"], snapshot_path=snap_rel,
                   snapshot_sha256=snap_sha, decision_sha256=sha(payload["decision"]))
        check_schema("v4", rec)
        rel = f"decisions/{case_id}.v{c['version']}.{run_tag}{k}.v4.json"
        return self._append("v4", case_id, rel, self._write_new(rel, rec), utc, case_version=c["version"], run=k)

    def record_faisal(self, case_id, faisal, utc):
        cs = self.entries("case", case_id)
        vs = [e for e in self.entries("v4", case_id) if cs and e.get("case_version") == cs[-1]["version"]]
        if not vs:
            raise DecisionFreezeError("كلمةُ فيصل لا تُسجَّل قبل قرار V4 المختوم (§26 · FV48)")
        v = vs[-1]
        prior = self.entries("faisal", case_id)
        n = len(prior) + 1
        if n > 1 and (faisal.get("supersedes") != n - 1 or not faisal.get("correction_reason")):
            raise AppendOnlyError("تصحيحُ كلمة فيصل نسخةٌ جديدة بـsupersedes وسبب")
        rec = dict(faisal, case_id=case_id, after_v4_seq=v["seq"], v4_decision_sha256=v["sha256"],
                   label4=L4.get(faisal.get("label"), faisal.get("label4")))
        check_schema("faisal", rec)
        rel = f"faisal/{case_id}.v{n}.json"
        return self._append("faisal", case_id, rel, self._write_new(rel, rec), utc, version=n)

    def record_invalid(self, case_id, reason, detail, utc):
        if not self.entries("case", case_id):
            raise DecisionFreezeError("لا حالةَ مختومة")
        obj = {"case_id": case_id, "reason": reason, "detail": detail}
        check_schema("invalid", obj)
        n = len(self.entries("invalid", case_id)) + 1
        rel = f"invalid/{case_id}.v{n}.json"
        return self._append("invalid", case_id, rel, self._write_new(rel, obj), utc)

    # ── التحقّق ──────────────────────────────────────────────────────────────
    def verify(self, freeze_ids=None):
        """⟵ (ok · مشكلات): السلسلة · بصماتُ القيود والملفّات · اليتامى · الترتيب (حالة ⟵ V4 ⟵ فيصل) · وتجميدُ المحرّك (FV44)."""
        probs = []
        man = self.manifest()
        prev = "GENESIS"
        seen_paths = set()
        first = {}
        for i, e in enumerate(man.get("entries") or []):
            body = {k: v for k, v in e.items() if k != "entry_hash"}
            if e.get("seq") != i + 1:
                probs.append(f"SEQ:{i + 1}")
            if e.get("prev") != prev:
                probs.append(f"CHAIN:{e.get('seq')}")
            if sha(body) != e.get("entry_hash"):
                probs.append(f"ENTRY_HASH:{e.get('seq')}")
            prev = e.get("entry_hash")
            p = os.path.join(self.root, e.get("path", ""))
            seen_paths.add(e.get("path"))
            if not os.path.exists(p):
                probs.append(f"MISSING_FILE:{e.get('path')}")
            elif sha_file(p) != e.get("sha256"):
                probs.append(f"FILE_HASH:{e.get('path')}")
            first.setdefault((e["case_id"], e["kind"]), e["seq"])
            if e["kind"] == "v4" and os.path.exists(p):
                rec = self.read(e["path"])
                if freeze_ids is not None and rec.get("freeze_id") not in freeze_ids:
                    probs.append(f"FOREIGN_ENGINE:{e['case_id']}")
                cs = [x for x in man["entries"][:i] if x["kind"] == "case" and x["case_id"] == e["case_id"]]
                if not cs or rec.get("case_sha256") != cs[-1]["sha256"]:
                    probs.append(f"CASE_LINK:{e['case_id']}")
                if sha(rec.get("decision")) != rec.get("decision_sha256"):
                    probs.append(f"DECISION_HASH:{e['case_id']}")
                sp = rec.get("snapshot_path") or ""
                seen_paths.add(sp)                    # اللقطةُ مُحالٌ إليها من القرار لا من البيان
                if not os.path.exists(os.path.join(self.root, sp)):
                    probs.append(f"MISSING_SNAPSHOT:{sp}")
                elif sha_file(os.path.join(self.root, sp)) != rec.get("snapshot_sha256"):
                    probs.append(f"SNAPSHOT_HASH:{sp}")
            if e["kind"] == "faisal" and os.path.exists(p):
                rec = self.read(e["path"])
                vs = [x for x in man["entries"][:i] if x["kind"] == "v4" and x["case_id"] == e["case_id"]]
                if not vs or rec.get("after_v4_seq") != vs[-1]["seq"] or rec.get("v4_decision_sha256") != vs[-1]["sha256"]:
                    probs.append(f"ORDER:{e['case_id']}")
        for (cid, kind), s in first.items():
            if kind == "v4" and not (first.get((cid, "case"), 10 ** 9) < s):
                probs.append(f"ORDER_V4:{cid}")
            if kind == "faisal" and not (first.get((cid, "v4"), 10 ** 9) < s):
                probs.append(f"ORDER_FAISAL:{cid}")
        for sub in ("cases", "decisions", "faisal", "snapshots", "invalid", "candidates"):
            d = os.path.join(self.root, sub)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    rel = f"{sub}/{fn}"
                    if rel not in seen_paths:
                        probs.append(f"ORPHAN:{rel}")
        return (not probs), probs

    def complete_cases(self):
        """الحالاتُ الصالحة للمقاييس: آخرُ نسخةٍ مختومة ‏+ آخرُ قرار V4 لها ‏+ كلمةُ فيصل · وبلا قيدِ INVALID."""
        out, invalid = [], []
        ids = sorted({e["case_id"] for e in self.entries("case")})
        for cid in ids:
            if self.entries("invalid", cid):
                invalid.append(cid)
                continue
            c = self.entries("case", cid)[-1]
            vs = [e for e in self.entries("v4", cid) if e.get("case_version") == c["version"]]
            fs = self.entries("faisal", cid)
            if vs and fs:
                out.append({"case": self.read(c["path"]), "v4": self.read(vs[-1]["path"]), "faisal": self.read(fs[-1]["path"])})
        return out, invalid


def pending_new_images(ledger=None, root=ROOT):
    """صورُ `faisal_images/` غيرُ المسجَّلة في المدوّنة المجمَّدة ولا في سجلّ المرشَّحين — تنتظر الالتقاط (تقريرٌ لا فشل)."""
    ledger = ledger or Ledger()
    with open(os.path.join(root, "faisal_method_v3", "image_corpus.json"), encoding="utf-8") as f:
        corpus = {i["file"] for i in json.load(f)["images"]}
    done = {e["case_id"] for e in ledger.entries("candidate")}
    img_dir = os.path.join(root, "faisal_images")
    out = []
    for fn in sorted(os.listdir(img_dir)) if os.path.isdir(img_dir) else []:
        rel = f"faisal_images/{fn}"
        if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and rel not in corpus and os.path.splitext(fn)[0] not in done:
            out.append(rel)
    return out


def near_duplicates(image_path, corpus_images=None, dmax=24, pmax=10):
    """نسخةٌ قريبة من صورةٍ في المدوّنة المجمَّدة (dHash256 ≤ 24 **و** pHash64 ≤ 10 — قاعدةُ V3 `corpus_build.dedup`) ⟵ قائمةُ المعرّفات (§⑤ · FV43).

    🔴 BB4 (2026-10-07 · دفعة B48 · قبل أيّ قرارٍ أماميّ): كانت «أو» ⟵ صورةٌ واحدة «قريبة» من 53 صورةً في عناقيدَ مختلفة · وعلى المدوّنة
    نفسِها تضيف «أو» 2,121 زوجًا pHash-فقط منها 2,119 عبر عناقيدَ فصلتها V3 (و«و» = 126 زوجًا: 123 في العنقود نفسِه والثلاثةُ أزواجُ
    «ليست تكرارًا» المراجَعةُ بصريًّا) ⟵ pHash64 وحدَه يلتقط تخطيطَ الواجهة (شاشة X الداكنة · التطبيق نفسُه) لا الصورة. قفل FV43b."""
    import corpus_build as CB          # V3: دوالّ البصمة الإدراكيّة نفسُها
    from PIL import Image
    if corpus_images is None:
        with open(os.path.join(ROOT, "faisal_method_v3", "image_corpus.json"), encoding="utf-8") as f:
            corpus_images = json.load(f)["images"]
    with Image.open(image_path) as im:
        d = CB.bits_hex(CB.dhash_bits(im, 16))
        p = CB.bits_hex(CB.phash_bits(im))
    return sorted(i["id"] for i in corpus_images
                  if CB.hamming_hex(d, i["dhash256"]) <= dmax and CB.hamming_hex(p, i["phash64"]) <= pmax)
