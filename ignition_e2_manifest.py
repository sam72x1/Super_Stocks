# -*- coding: utf-8 -*-
"""🔬 E2 (مراجعة Codex 4 · P0-4) — manifest + سلسلة SHA-256 للتحقّق من سلامة المقاطع.

كل مقطع (open/close) يولّد **manifest مقفول** (canonical JSON) بـSHA-256 واحد فوق ملفّاته الخام.
الـhandoff يحمل `manifest_sha256` + `previous_segment_manifest_sha256` فتتشكّل **سلسلة تحقّق**:
- `close` يرفض المسح لو manifest الـopen مفقود/تالف/hash لا يطابق.
- الـassembler يرفض الدمج لو السلسلة غير متطابقة.

**نقيّة/قابلة للاختبار · فاشلة-آمنة في القراءة، صارمة في التحقّق (fail-closed للـconfirmatory).**
🔒 قياس/سلامة فقط — لا يمسّ الفرز/التنبيه/الاختيار · لا LOGIC_VERSION.
"""
import hashlib
import json
import os

MANIFEST_VERSION = 1
# ملفّات المقطع الخام المشمولة بالـhash (manifest.json نفسه مُستثنى — يشير إليها).
MANIFEST_FILES = ("candidates.jsonl", "deliveries.jsonl", "symbol_sessions.jsonl",
                  "minute_paths.jsonl.gz", "session.json")


def canonical_json(obj):
    """JSON قانوني حتمي (مفاتيح مرتّبة · بلا مسافات) — أساس الـhash القابل للتكرار."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text):
    try:
        if isinstance(text, str):
            text = text.encode("utf-8")
        return hashlib.sha256(text).hexdigest()
    except Exception:
        return None


def file_sha256(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def raw_files_sha256(segment_dir):
    """{filename: sha256} للملفّات الموجودة (يتخطّى الغائب)."""
    out = {}
    for name in MANIFEST_FILES:
        p = os.path.join(segment_dir, name)
        if os.path.exists(p):
            out[name] = file_sha256(p)
    return out


def build_manifest(*, session_date, segment, segment_id, source_commit, workflow_run_id,
                   expected_segment_start, expected_segment_end, alerted_symbols, candidate_ids,
                   symbols_union, loops_started, loops_completed, segment_dir,
                   previous_segment_manifest_sha256=None):
    """يبني manifest المقطع (بلا `manifest_sha256` — يُحسب بـ`finalize_manifest`)."""
    return {
        "manifest_version": MANIFEST_VERSION, "session_date": session_date, "segment": segment,
        "segment_id": segment_id, "source_commit": source_commit, "workflow_run_id": workflow_run_id,
        "expected_segment_start": expected_segment_start, "expected_segment_end": expected_segment_end,
        "alerted_symbols": sorted(alerted_symbols or []), "candidate_ids": sorted(candidate_ids or []),
        "symbols_union": sorted(symbols_union or []),
        "loops_started": loops_started, "loops_completed": loops_completed,
        "raw_files_sha256": raw_files_sha256(segment_dir),
        "previous_segment_manifest_sha256": previous_segment_manifest_sha256,
    }


def manifest_sha256(manifest):
    """SHA-256 فوق canonical JSON للـmanifest (بعد نزع `manifest_sha256` نفسه إن وُجد)."""
    m = {k: v for k, v in (manifest or {}).items() if k != "manifest_sha256"}
    return sha256_hex(canonical_json(m))


def write_manifest(segment_dir, manifest):
    """يكتب manifest.json (مع manifest_sha256 المضمَّن). يرجّع الـhash أو None. فاشل-آمن."""
    try:
        h = manifest_sha256(manifest)
        out = dict(manifest)
        out["manifest_sha256"] = h
        tmp = os.path.join(segment_dir, "manifest.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(canonical_json(out))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, os.path.join(segment_dir, "manifest.json"))
        return h
    except Exception:
        return None


def read_manifest(segment_dir):
    try:
        p = os.path.join(segment_dir, "manifest.json")
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def verify_manifest(manifest, segment_dir, expect_session_date=None, expect_segment=None):
    """يتحقّق: بنية · تطابق hash الـmanifest · تطابق hash كل ملف خام · (اختياريًّا) التاريخ/الدور.
    يرجّع (ok, reasons[]). **صارم** — أي عدم تطابق = فشل (لا يُبتلَع)."""
    reasons = []
    if not isinstance(manifest, dict):
        return (False, ["manifest_missing_or_unreadable"])
    stored = manifest.get("manifest_sha256")
    if not stored or stored != manifest_sha256(manifest):
        reasons.append("manifest_hash_mismatch")
    if expect_session_date is not None and manifest.get("session_date") != expect_session_date:
        reasons.append("session_date_mismatch")
    if expect_segment is not None and manifest.get("segment") != expect_segment:
        reasons.append("segment_role_mismatch")
    current = raw_files_sha256(segment_dir)
    for name, h in (manifest.get("raw_files_sha256") or {}).items():
        if current.get(name) != h:
            reasons.append("raw_hash_mismatch(%s)" % name)
    return (not reasons, reasons)


def verify_chain(open_manifest, close_manifest):
    """يتحقّق أن `close.previous_segment_manifest_sha256 == open.manifest_sha256`.
    يرجّع (ok, reasons[])."""
    reasons = []
    if not isinstance(open_manifest, dict) or not isinstance(close_manifest, dict):
        return (False, ["chain_manifest_missing"])
    op_h = open_manifest.get("manifest_sha256") or manifest_sha256(open_manifest)
    prev = close_manifest.get("previous_segment_manifest_sha256")
    if not prev:
        reasons.append("chain_previous_missing")
    elif prev != op_h:
        reasons.append("chain_hash_mismatch")
    if open_manifest.get("session_date") != close_manifest.get("session_date"):
        reasons.append("chain_session_date_mismatch")
    return (not reasons, reasons)
