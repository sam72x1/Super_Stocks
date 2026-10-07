# -*- coding: utf-8 -*-
"""
🧊🔒 FAISAL V4 — FINAL PROSPECTIVE VALIDATION PROTOCOL (العقد `FINAL_PROTOCOL_prereg.md` · مدموجٌ قبل أيّ رقم).

الحلقة: FREEZE V4 ⟶ CAPTURE NEW CASE ⟶ RUN V4 BLIND ⟶ SEAL RESULT ⟶ REVEAL FAISAL ⟶ COMPARE ⟶ RECORD ⟶ REPEAT.

هذه الأداةُ **لا تمسّ V4** (FV41) ولا خطَّ بياناته: تقرأ السجلَّ الإلحاقيّ (`ledger.py`) وقيودَ V4 المختومة وبيانَ التجميد وجردَ EX ودفعاتِ الاستلام،
وتحسب: هويّةَ الحقبة (المعرّفاتُ الخمسة · §②) · السلامةَ I1-I12 · الأصنافَ السبعة والفحوصَ الثمانية · المصدريّةَ وثقتَها · كائنَي القرار ·
المطابقةَ · المكوّنات · النظرَ المستقبليّ LA1-LA6 · التنوّع · المقاييسَ والحالةَ النهائيّة · وكتلةَ الإخراج بنصّ المالك.

⚖️ حتميّة: `build()` بلا شبكة ولا ساعةٍ ولا كتابة (السويّةُ تُعيده فيطابق المدفوع بايتًا بايتًا) · و`write()` وحدَه يكتب مخرجاتِ `final_protocol/` ·
والكتابةُ في السجلّ الإلحاقيّ (`seal` · `reveal`) أوامرُ صريحةٌ في الجلسة لا تجري في السويّة.
🔒 بلا تلغرام · بلا أسرار · بلا حالة إنتاج.
"""
import ast
import collections
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V3 = os.path.join(ROOT, "faisal_method_v3")
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (ROOT, V4, V3, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import freeze as FZ              # noqa: E402
import ledger as LG              # noqa: E402
import runner as RN              # noqa: E402 — يستورد المحرّكَ المجمَّد (decision_engine)

E = sys.modules["decision_engine"]

FP_VERSION = "V4-FINAL-PROTOCOL 1.0 (2026-10-07)"
CONTRACT = "faisal_method_v41/FINAL_PROTOCOL_prereg.md"
OUT_DIR = os.path.join(HERE, "final_protocol")
EPOCH_FILE = os.path.join(OUT_DIR, "EPOCH_FREEZE.json")
STATUS_JSON = os.path.join(OUT_DIR, "PROTOCOL_STATUS.json")
STATUS_MD = os.path.join(OUT_DIR, "PROTOCOL_STATUS.md")
LEDGER_MD = os.path.join(OUT_DIR, "CASE_LEDGER.md")
FR_MD = os.path.join(OUT_DIR, "FALSE_READY_FORENSICS.md")
FINAL_MD = os.path.join(OUT_DIR, "FINAL_PROSPECTIVE_VALIDATION_REPORT.md")
PROSPECTIVE_MD = os.path.join(OUT_DIR, "PROSPECTIVE_STATUS.md")      # STEP 11 (أمرُ «BEGIN REAL PROSPECTIVE VALIDATION»)
INTAKE_DIR = os.path.join(OUT_DIR, "intake")
REVEAL_DIR = os.path.join(OUT_DIR, "reveal")
META_FILE = os.path.join(ROOT, "telegram_collect_meta.jsonl")
INVENTORY = os.path.join(HERE, "corpus_audit", "MASTER_CORPUS_INVENTORY.json")
B48_DIR = os.path.join(HERE, "batches", "B48_20261007")
B48_MANIFEST = os.path.join(B48_DIR, "PROSPECTIVE_BATCH_48_MANIFEST.json")
B48_ANN = os.path.join(B48_DIR, "input_annotations.json")
CASES_V4 = os.path.join(V4, "results", "cases_v4.json")
GOLDEN = os.path.join(V3, "v31", "golden_cases_v31.json")
CORPUS = os.path.join(V3, "image_corpus.json")
VISUAL_V4 = os.path.join(V4, "data", "visual_pass_v4.jsonl")

# ── العقد: ثوابتُ مسجَّلة قبل الرقم (§②-§⑱) ─────────────────────────────────────
V4_COMMIT = "7c8826c25e745668d33facabb2efbc488e997fb7"   # commit التجميد الرسميّ (#550)
WINDOW_START = LG.WINDOW_START                             # 2026-10-03
FREEZE_DATE = "2026-10-02"                                 # آخرُ تغييرٍ في نواة المحرّك ⟵ المدوّنةُ كلُّها قبله
N_MIN = 43                                                 # V41 §⑨
WILSON_MIN = 10                                            # V41 §⑧
Z = 1.96
READY_COVER = 5                                            # 🧩 تغطيةُ الصنف (engineering · §⑱)
READY_VALID_N = 43                                         # V41 §⑨: استدعاءُ READY يحتاج ≈43 READY
READY_V4_MIN = 10
BANDS = ((10, "VERY_PRELIMINARY"), (25, "PRELIMINARY"), (43, "MEANINGFUL"))
SAME_CASE_DAYS = 3                                         # C4 (batch_intake.case_overlap)
CYCLE_SESSIONS = int(E.PARAMS["CYCLE_BARS"][0])            # C5/C8: نافذةُ الـ120 = CYCLE_BARS المجمَّد
LEVEL_TOL = float(E.PARAMS["LEVEL_TOL_PCT"][0]) / 100.0    # المكوّنات: ±2% «دقة الخطأ لاتتجاوز 2٪»
PX_TOL = 0.15                                              # = v4_eval.PX_TOL (فحصُ المقياس)
SCALE_FACTORS = (10.0, 0.1)                                # LA5
LOW_DIV_RUN = 20                                           # §⑬ (رقمُ المالك)
RETENTION_HOURS = 24                                       # حفظُ تلغرام
DUP_DHASH256_MAX, DUP_PHASH_MAX = 24, 10                   # V3 corpus_build (BB4: «و»)

CLASSES7 = ("NEW_PROSPECTIVE", "DUPLICATE", "DERIVATIVE", "CONTAMINATED", "PRE_EXISTING", "UNKNOWN", "INSUFFICIENT_CONTEXT")
MATCH_CLASSES = ("MATCH", "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN", "MISMATCH_WAIT_REJECT",
                 "MISMATCH_REJECT_WAIT", "FAISAL_UNKNOWN", "UNRESOLVED")
MISMATCH_CLASSES = ("FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN", "MISMATCH_WAIT_REJECT", "MISMATCH_REJECT_WAIT")
EVIDENCE_CLASSES = ("DIRECT", "STRONG_INFERENCE", "WEAK_INFERENCE")
CONFIDENCE = ("HIGH", "MEDIUM", "LOW", "UNKNOWN")
PRIMARY_CONF = ("HIGH", "MEDIUM")
PROV_FIELDS = ("CASE_ID", "SOURCE", "SOURCE_MESSAGE_ID", "CAPTURE_TIMESTAMP", "ORIGINAL_POST_TIMESTAMP", "FORWARD_TYPE",
               "PUBLIC_CHANNEL_METADATA", "IMAGE_HASH", "PERCEPTUAL_HASH", "TICKER", "TIMEFRAME", "DATE_VISIBLE",
               "PROVENANCE_CONFIDENCE")
CRITICAL = ("SOURCE", "SOURCE_MESSAGE_ID", "CAPTURE_TIMESTAMP", "ORIGINAL_POST_TIMESTAMP", "FORWARD_TYPE", "IMAGE_HASH",
            "PERCEPTUAL_HASH", "TICKER", "TIMEFRAME")
FORWARD_TYPES = ("none", "channel", "chat", "user", "hidden_user", "legacy")
COMPONENTS = ("ENTRY", "INVALIDATION", "STOP", "TARGET")
COMPONENT_STATUS = ("MATCH", "MISMATCH", "FAISAL_NOT_STATED", "FAISAL_NONE", "V4_NOT_AVAILABLE", "SCALE_MISMATCH")
FR_CAUSES = ("IMPLEMENTATION_BUG", "DATA_BUG", "MISSING_CONTEXT", "EXTERNAL_INFORMATION", "TIMEFRAME", "LOCATION",
             "ENTRY_TIMING", "VALIDITY", "DISCRETION", "UNKNOWN")
V4_2_FIELDS = ("CASE_ID", "OBSERVATION", "EVIDENCE", "WHY_V4_FAILED", "POSSIBLE_MISSING_RULE", "GENERALIZATION_STATUS",
               "CONTRADICTING_CASES")
FINAL_STATES = ("VALIDATED", "PARTIALLY_VALIDATED", "NOT_VALIDATED", "INSUFFICIENT_SAMPLE", "VALIDATION_BLOCKED")
OUTPUT_KEYS = ("V4_FROZEN", "V4_COMMIT", "CORPUS_AUDIT", "VALID_PROSPECTIVE_CASES", "EXCLUDED_CASES", "MATCHES", "MISMATCHES",
               "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN", "V4_UNKNOWN", "FAISAL_UNKNOWN", "ALWAYS_WAIT_MATCH",
               "V4_BEATS_BASELINE", "READY_CLASS_VALIDATED", "METHODOLOGY_CHANGED", "LOOKAHEAD", "PROVENANCE",
               "CURRENT_STATUS", "FINAL_VALIDATION_STATE")
# STEP 11 من أمر المالك «FAISAL V4 — BEGIN REAL PROSPECTIVE VALIDATION» (2026-10-07) — بترتيبه حرفًا
PROSPECTIVE_KEYS = ("TOTAL_RECEIVED", "NEW_PROSPECTIVE", "DUPLICATES", "DERIVATIVES", "CONTAMINATED", "INSUFFICIENT_CONTEXT",
                    "VALID_CASES", "MATCHES", "MISMATCHES", "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN",
                    "READY_PRECISION", "READY_RECALL", "WAIT_PRECISION", "WAIT_RECALL", "REJECT_PRECISION", "REJECT_RECALL",
                    "V4_UNKNOWN", "FAISAL_UNKNOWN", "ALWAYS_WAIT_MATCH", "V4_BEATS_BASELINE", "CURRENT_SAMPLE_STATUS")
CTX_KEYS = frozenset(("groups", "offering_pending", "operator_press", "short_available"))
MECH_PREFIX = ("ctb_log:", "live:", "UNAVAILABLE")
# CASE_0001 قبل العقد: الدليلُ مكتوبٌ في §⑩ — والاقتباسُ يُفحص حرفيًّا مقابل قيد فيصل المختوم
LEGACY_EVIDENCE = {"CASE_0001": ("DIRECT", "مراقبه مبكره")}
# قاعدةُ وقف V4 المجمَّد (§⑮) — بالاسم هنا وحدَه: السويّةُ تقرؤه ولا تكتبه حرفيًّا، فمراجعةُ المصدريّة (`provenance.TESTED`) لا تعدّ
# القاعدةَ «مُختبَرة» بقفلٍ يفحص المقارنةَ لا سلوكَ القاعدة
STOP_RULE = "R4-STOP-01"
EXT_CATEGORIES = (("split", ("تقسيم", "split")), ("float", ("فلوت", "float")), ("short_borrow", ("شورت", "اقتراض", "short")),
                  ("offering", ("طرح", "تخفيف", "offering")), ("news", ("خبر", "اعلان", "إعلان", "news")),
                  ("country", ("امريكي", "أمريكي", "صيني", "country")), ("app", ("تطبيق", "app")))

# ── ① البصمات القانونيّة ─────────────────────────────────────────────────────
canon = RN.canon
sha = RN.sha


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _j(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_DOC_HOSTS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)


def _is_doc(stmt):
    return isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str)


def canon_ast(node):
    """شجرةٌ قانونيّة لا تتأثّر بنسخة بايثون: بلا docstring · بلا حقلٍ فارغ (3.13 يحذفها) · بلا `type_params` (3.12+) — والتعليقاتُ ليست في الشجرة."""
    if isinstance(node, ast.AST):
        out = []
        for f in node._fields:
            if f == "type_params":
                continue
            v = getattr(node, f, None)
            if f == "body" and isinstance(node, _DOC_HOSTS) and isinstance(v, list) and v and _is_doc(v[0]):
                v = v[1:]
            if v is None or (isinstance(v, list) and not v):
                continue
            out.append([f, canon_ast(v)])
        return [type(node).__name__, out]
    if isinstance(node, list):
        return [canon_ast(x) for x in node]
    return repr(node)


# ── ② إغلاقُ خطّ البيانات (DATA_PIPELINE_VERSION · §②) ─────────────────────────
PIPELINE_MODULES = {"runner": "faisal_method_v41/runner.py", "tv_data": "tv_data.py", "Super_stock": "Super_stock.py",
                    "market_calendar": "market_calendar.py", "v4_run": "faisal_method_v4/v4_run.py", "ctb_harvest": "ctb_harvest.py"}
PIPELINE_ENTRIES = tuple(("runner", n) for n in ("fetch_rows", "fetch_splits", "live_borrow", "validity_context", "load_ctb",
                                                  "snapshot", "firewall", "decide", "run_case", "is_session",
                                                  "prev_trading_days", "next_trading_day")) + (("ctb_harvest", "harvest"),)
PIPELINE_PINS = ("yfinance", "websocket-client", "requests", "pandas", "numpy")


def _names_defined(stmt):
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [stmt.name]
    if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        tg = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        return [n.id for x in tg for n in ast.walk(x) if isinstance(n, ast.Name)]
    if isinstance(stmt, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
        out = []
        for blk in ("body", "orelse", "finalbody"):
            for s in getattr(stmt, blk, None) or []:
                out += _names_defined(s)
        for h in getattr(stmt, "handlers", None) or []:
            for s in h.body:
                out += _names_defined(s)
        return out
    return []


def _defs(tree):
    """الأسماءُ المعرَّفة على مستوى الوحدة ⟵ عُقدُها العلويّة (الدالّة · الصنف · الإسناد · والمركَّبُ العلويّ الذي يعرّفها)."""
    t = {}
    for stmt in tree.body:
        for nm in _names_defined(stmt):
            lst = t.setdefault(nm, [])
            if not any(x is stmt for x in lst):
                lst.append(stmt)
    return t


def _aliases(nodes, mods):
    """أسماءُ الاستيراد ⟵ (الوحدة · الاسم أو None) للوحدات المتتبَّعة وحدَها — من العُقد المعطاة (بلا ما داخل دوالَّ أخرى)."""
    out = {}
    for node in nodes:
        for x in ast.walk(node):
            if isinstance(x, ast.Import):
                for a in x.names:
                    if a.name in mods:
                        out[a.asname or a.name] = (a.name, None)
            elif isinstance(x, ast.ImportFrom) and x.module in mods:
                for a in x.names:
                    out[a.asname or a.name] = (x.module, a.name)
    return out


def _top_imports(tree):
    nodes = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            nodes.append(stmt)
        elif isinstance(stmt, (ast.If, ast.Try)):
            nodes += [s for s in ast.walk(stmt) if isinstance(s, (ast.Import, ast.ImportFrom))]
    return nodes


_PARSE_CACHE = {}


def pipeline_components(sources=None, entries=PIPELINE_ENTRIES):
    """الإغلاقُ الساكن من مداخل الجلب ⟵ {«وحدة.اسم»: بصمة} (§②). `sources` = {وحدة: نصّ} للحقن (السويّة · الشهادة على commit قديم)."""
    srcs = sources if sources is not None else {m: open(os.path.join(ROOT, p), encoding="utf-8").read()
                                                for m, p in PIPELINE_MODULES.items()}
    mods = set(srcs)
    tabs, top = {}, {}
    for m, src in srcs.items():
        key = (sha_bytes(src.encode("utf-8")), tuple(sorted(mods)))
        if key not in _PARSE_CACHE:                      # الشجرةُ لا تُعدَّل ⟵ ذاكرةٌ بالبصمة آمنة (السويّةُ تحسب الإغلاقَ مرارًا)
            t = ast.parse(src)
            _PARSE_CACHE[key] = (_defs(t), _aliases(_top_imports(t), mods))
        tabs[m], top[m] = _PARSE_CACHE[key]
    seen, queue = set(), list(entries)
    while queue:
        m, nm = queue.pop()
        if (m, nm) in seen or m not in tabs or nm not in tabs[m]:
            continue
        seen.add((m, nm))
        for node in tabs[m][nm]:
            al = dict(top[m])
            al.update(_aliases([node], mods))
            for x in ast.walk(node):
                if isinstance(x, ast.Name):
                    if x.id in al and al[x.id][1]:
                        queue.append(al[x.id])
                    elif x.id in tabs[m] and x.id not in al:
                        queue.append((m, x.id))
                elif isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in al and al[x.value.id][1] is None:
                    queue.append((al[x.value.id][0], x.attr))
    return {f"{m}.{nm}": sha([canon_ast(n) for n in tabs[m][nm]]) for m, nm in sorted(seen)}


def requirement_pins(text=None):
    text = text if text is not None else open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8").read()
    pins = {}
    for line in text.splitlines():
        s = line.split("#", 1)[0].strip()
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+)\s*==\s*([^\s;]+)", s)
        if m and m.group(1).lower() in PIPELINE_PINS:
            pins[m.group(1).lower()] = m.group(2)
    return dict(sorted(pins.items()))


def pipeline_version(components, pins):
    return sha({"components": components, "pins": pins})


# ── ③ هويّةُ V4 (المعرّفاتُ الخمسة) ───────────────────────────────────────────
def v4_identity(root=ROOT, components=None, pins=None):
    man = FZ.load()
    cur = FZ.current_revision(man)
    snap = FZ.config_snapshot(root)
    cfg = {k: snap[k] for k in ("engine_version", "rules_version", "params", "state_decision", "state_rule")}
    comps = pipeline_components() if components is None else components
    pins = requirement_pins() if pins is None else pins
    return {"V4_COMMIT": V4_COMMIT, "V4_FREEZE_ID": cur["freeze_id"], "V4_FREEZE_REV": cur["rev"],
            "V4_REVISIONS": len(man["revisions"]), "V4_CONFIG_HASH": sha(cfg), "V4_RULE_REGISTRY_HASH": sha(snap["rules"]),
            "V4_TOOL_VERSION": {"engine": snap["engine_version"], "rules": snap["rules_version"], "runner": RN.RUNNER_VERSION,
                                "freeze": FZ.FREEZE_VERSION},
            "DATA_PIPELINE_VERSION": pipeline_version(comps, pins), "DATA_PIPELINE_COMPONENTS": comps, "DATA_PIPELINE_PINS": pins}


def _git_show(rev, path):
    try:
        r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, timeout=60)
        return r.stdout if r.returncode == 0 else None
    except Exception:                                                   # noqa: BLE001
        return None


def git_attest(man=None):
    """شهادةٌ لمرّةٍ واحدة (تحتاج تاريخ git): كلُّ ملفٍّ مجمَّدٍ عند `V4_COMMIT` = بصمةَ البيان."""
    man = man or FZ.load()
    files = FZ.current_revision(man)["files"]
    bad, missing = [], []
    for p, h in sorted(files.items()):
        b = _git_show(V4_COMMIT, p)
        if b is None:
            missing.append(p)
        elif sha_bytes(b) != h:
            bad.append(p)
    return {"commit": V4_COMMIT, "checked": len(files), "mismatch": bad, "missing": missing, "ok": not bad and not missing}


def legacy_attest(ident, ledger=None):
    """قراراتُ V4 المختومة قبل الحقبة (بلا `pipeline_version` في meta): إغلاقُ خطّ البيانات عند commit تشغيلتها = إغلاقُ الحقبة؟"""
    lg = ledger or LG.Ledger()
    out = {}
    for e in lg.entries("v4"):
        rec = lg.read(e["path"])
        meta = rec.get("meta") or {}
        if meta.get("pipeline_version"):
            continue
        rev = meta.get("commit")
        srcs = {m: (_git_show(rev, p) or b"").decode("utf-8") for m, p in PIPELINE_MODULES.items()} if rev else None
        req = (_git_show(rev, "requirements.txt") or b"").decode("utf-8") if rev else ""
        if not rev or not all(srcs.values()):
            out[e["case_id"]] = {"run_commit": rev, "equal": False, "differ": ["SOURCES_UNAVAILABLE"]}
            continue
        comps = pipeline_components(srcs)
        pins = requirement_pins(req)
        differ = sorted(k for k in set(comps) | set(ident["DATA_PIPELINE_COMPONENTS"])
                        if comps.get(k) != ident["DATA_PIPELINE_COMPONENTS"].get(k))
        differ += [f"pin:{k}" for k in sorted(set(pins) | set(ident["DATA_PIPELINE_PINS"])) if pins.get(k) != ident["DATA_PIPELINE_PINS"].get(k)]
        out[e["case_id"]] = {"run_commit": rev, "run_id": meta.get("run_id"), "pipeline_version_at_run": pipeline_version(comps, pins),
                             "equal": not differ, "differ": differ}
    return out


def meta_prefix(path=META_FILE):
    if not os.path.exists(path):
        return {"path": os.path.relpath(path, ROOT), "bytes": 0, "sha256": sha_bytes(b"")}
    with open(path, "rb") as f:
        b = f.read()
    return {"path": os.path.relpath(path, ROOT), "bytes": len(b), "sha256": sha_bytes(b)}


def build_epoch(utc, ledger=None):
    ident = v4_identity()
    return {"epoch": 1, "declared_utc": utc, "reason": "INITIAL", "contract": CONTRACT, "protocol_tool": FP_VERSION,
            "owner_order": "FAISAL V4 — FINAL PROSPECTIVE VALIDATION PROTOCOL (2026-10-07)", **ident,
            "V4_COMMIT_ATTESTATION": git_attest(), "LEGACY_CASES": legacy_attest(ident, ledger), "META_PREFIX": meta_prefix()}


def load_epochs(path=EPOCH_FILE):
    return _j(path, {}) or {}


def current_epoch(path=EPOCH_FILE):
    eps = (load_epochs(path).get("epochs") or [])
    return eps[-1] if eps else None


# ── ④ السلامة I1-I12 (PHASE 18) ───────────────────────────────────────────────
def _meta_prefix_ok(rec, root=ROOT):
    p = os.path.join(root, rec["path"])
    if not os.path.exists(p):
        return rec["bytes"] == 0, "الملفّ غائب"
    with open(p, "rb") as f:
        b = f.read(rec["bytes"])
    size = os.path.getsize(p)
    ok = len(b) == rec["bytes"] and sha_bytes(b) == rec["sha256"]
    return ok, f"البادئة {rec['bytes']} بايت · الحجم الآن {size}" + ("" if ok else " ⟵ تغيّرت البادئة (ليس إلحاقًا)")


def _latest_cases(lg):
    out = {}
    for e in lg.entries("case"):
        out[e["case_id"]] = e
    return out


def _case_images_ok(lg, root=ROOT):
    bad = []
    for cid, e in sorted(_latest_cases(lg).items()):
        c = lg.read(e["path"])
        p = os.path.join(root, c.get("image") or "")
        if not c.get("image") or not os.path.exists(p):
            bad.append(f"{cid}:MISSING")
        elif sha_file(p) != c.get("image_sha256"):
            bad.append(f"{cid}:HASH")
    return not bad, bad


def _records_epoch_ok(lg, ep):
    bad = []
    for e in lg.entries("v4"):
        rec = lg.read(e["path"])
        pv = (rec.get("meta") or {}).get("pipeline_version")
        if pv:
            if pv != ep["DATA_PIPELINE_VERSION"]:
                bad.append(f"{e['case_id']}:PIPELINE")
        elif not (ep.get("LEGACY_CASES") or {}).get(e["case_id"], {}).get("equal"):
            bad.append(f"{e['case_id']}:LEGACY_UNATTESTED")
    return not bad, bad


def integrity(ep, ident, lg, case_rows, root=ROOT):
    """⟵ {checks: {I..: {ok · detail}} · ok}. أيُّ فشلٍ ⟵ VALIDATION_BLOCKED (§②)."""
    c = {}
    try:
        ok1, p1 = FZ.verify(FZ.load(), root=root)
    except Exception as e:                                              # noqa: BLE001
        ok1, p1 = False, [f"{type(e).__name__}"]
    c["I1_V4_FROZEN"] = (ok1, p1[:8])
    c["I2_FREEZE_ID"] = (ident["V4_FREEZE_ID"] == ep["V4_FREEZE_ID"], ident["V4_FREEZE_ID"][:16])
    c["I3_CONFIG_HASH"] = (ident["V4_CONFIG_HASH"] == ep["V4_CONFIG_HASH"], ident["V4_CONFIG_HASH"][:16])
    c["I4_RULE_REGISTRY_HASH"] = (ident["V4_RULE_REGISTRY_HASH"] == ep["V4_RULE_REGISTRY_HASH"], ident["V4_RULE_REGISTRY_HASH"][:16])
    c["I5_TOOL_VERSION"] = (ident["V4_TOOL_VERSION"] == ep["V4_TOOL_VERSION"], ident["V4_TOOL_VERSION"])
    dif = sorted(k for k in set(ident["DATA_PIPELINE_COMPONENTS"]) | set(ep["DATA_PIPELINE_COMPONENTS"])
                 if ident["DATA_PIPELINE_COMPONENTS"].get(k) != ep["DATA_PIPELINE_COMPONENTS"].get(k))
    dif += [f"pin:{k}" for k in sorted(set(ident["DATA_PIPELINE_PINS"]) | set(ep["DATA_PIPELINE_PINS"]))
            if ident["DATA_PIPELINE_PINS"].get(k) != ep["DATA_PIPELINE_PINS"].get(k)]
    c["I6_DATA_PIPELINE_VERSION"] = (ident["DATA_PIPELINE_VERSION"] == ep["DATA_PIPELINE_VERSION"] and not dif, dif[:12])
    c["I7_NO_REVISION"] = (ident["V4_FREEZE_REV"] == ep["V4_FREEZE_REV"] and ident["V4_REVISIONS"] == ep["V4_REVISIONS"],
                           f"rev {ident['V4_FREEZE_REV']} · revisions {ident['V4_REVISIONS']}")
    try:
        ok8, p8 = lg.verify({ep["V4_FREEZE_ID"]})
    except Exception as e:                                              # noqa: BLE001
        ok8, p8 = False, [f"{type(e).__name__}"]
    c["I8_LEDGER"] = (ok8, p8[:8])
    c["I9_META_PREFIX"] = _meta_prefix_ok(ep["META_PREFIX"], root)
    c["I10_CASE_IMAGES"] = _case_images_ok(lg, root)
    c["I11_RECORD_EPOCH"] = _records_epoch_ok(lg, ep)
    defect = sorted(r["CASE_ID"] for r in case_rows if (r.get("LOOKAHEAD") or {}).get("verdict") == "INVALIDATED_DEFECT")
    c["I12_NO_LOOKAHEAD_DEFECT"] = (not defect, defect)
    checks = {k: {"ok": bool(v[0]), "detail": v[1]} for k, v in c.items()}
    return {"checks": checks, "ok": all(v["ok"] for v in checks.values())}


# ── ⑤ الاستلام: الأصنافُ السبعة والفحوصُ الثمانية (PHASE 3 · RULE #3) ─────────
_LEGACY_MAP = {("DUPLICATE", "EXACT"): "DUPLICATE", ("DUPLICATE", "SEEN_FILE_ID"): "DUPLICATE",
               ("DERIVATIVE", "NEAR"): "DERIVATIVE", ("DERIVATIVE", "OCR"): "DERIVATIVE", ("DERIVATIVE", "VISUAL"): "DERIVATIVE",
               ("CONTAMINATED", "SAME_CASE"): "CONTAMINATED", ("CONTAMINATED", "SEEN_EXAMPLE"): "CONTAMINATED",
               ("CONTAMINATED", "HISTORICAL_BEFORE_WINDOW"): "PRE_EXISTING",
               ("UNKNOWN", "UNREADABLE"): "UNKNOWN", ("UNKNOWN", "NOT_REVIEWED"): "UNKNOWN",
               ("UNKNOWN", "AUTHOR_NOT_ESTABLISHED"): "UNKNOWN", ("UNKNOWN", "DATE_NOT_ESTABLISHED"): "INSUFFICIENT_CONTEXT"}


def map_legacy_class(cls, reason, exclusion, validation_case):
    """رموزُ B48 الخمسة ⟵ الأصنافُ السبعة (§⑦ — الرسمُ مكتوبٌ في العقد). المجهولُ ⟵ UNKNOWN (لا يُخترع صنف)."""
    head = str(reason or "").split(":")[0]
    if cls == "CLEAN_PROSPECTIVE":
        return ("NEW_PROSPECTIVE", "CLEAN") if validation_case else ("INSUFFICIENT_CONTEXT", str(exclusion or "NOT_ELIGIBLE").split(":")[0])
    return _LEGACY_MAP.get((cls, head), "UNKNOWN"), head or "—"


def classify7(c1, c2, c3, c6, contaminated, pre_existing, readable, reviewed, author_known, faisal, symbol, decision_stmt, date_ok):
    """الأسبقيّةُ المكتوبة (§⑦) ⟵ (الصنف · السبب). كلُّ مُدخَلٍ قائمةُ معرّفاتٍ أو قيمةٌ منطقيّة."""
    if c1:
        return "DUPLICATE", "C1:" + ",".join(c1)
    if c2 or c3 or c6:
        return "DERIVATIVE", ("C2:" + ",".join(c2)) if c2 else ("C3:" + ",".join(c3)) if c3 else ("C6:" + ",".join(c6))
    if contaminated:
        return "CONTAMINATED", contaminated
    if pre_existing:
        return "PRE_EXISTING", pre_existing
    if not readable:
        return "UNKNOWN", "UNREADABLE"
    if not reviewed:
        return "UNKNOWN", "NOT_REVIEWED"
    if not author_known:
        return "UNKNOWN", "AUTHOR_NOT_ESTABLISHED"
    if not faisal:
        return "INSUFFICIENT_CONTEXT", "NOT_FAISAL"
    if not symbol:
        return "INSUFFICIENT_CONTEXT", "NO_TICKER"
    if not decision_stmt:
        return "INSUFFICIENT_CONTEXT", "NO_DECISION"
    if not date_ok:
        return "INSUFFICIENT_CONTEXT", "DATE_NOT_ESTABLISHED"
    return "NEW_PROSPECTIVE", "—"


_DSPAN = re.compile(r"^(\d{4})-(\d{2})(?:-(\d)([\dx]))?")


def _last_day(y, m):
    return (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day


def date_span(s):
    """تاريخُ الجرد (قد يكون جزئيًّا: «2026-09-1x» · «2026-05» · «2026-07-03~» · «≤2026-09-01» · «2026-06-16+») ⟵ (من · إلى) أو None.
    محافظ: الجزئيُّ يُمدّ لمداه · «~» ±7 أيّام · «+» حتى تاريخ التجميد · «≤» ستّة أشهرٍ قبله · وبلا سنةٍ أو «UNK» ⟵ None."""
    s = str(s or "").strip()
    le = s.startswith("≤")
    s2 = s.lstrip("≤").strip()
    m = _DSPAN.match(s2)
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    if not (1 <= mo <= 12):
        return None
    if m.group(3) is None:
        lo, hi = dt.date(y, mo, 1), dt.date(y, mo, _last_day(y, mo))
        rest = s2[len(m.group(0)):]
        r2 = re.match(r"/(\d{2})", rest)
        if r2 and 1 <= int(r2.group(1)) <= 12:
            m2 = int(r2.group(1))
            hi = dt.date(y, m2, _last_day(y, m2))
    else:
        d1, d2 = m.group(3), m.group(4)
        if d2 == "x":
            a, b = int(d1 + "0"), int(d1 + "9")
            a, b = max(a, 1), min(b, _last_day(y, mo))
            if a > b:
                return None
            lo, hi = dt.date(y, mo, a), dt.date(y, mo, b)
        else:
            d = int(d1 + d2)
            if not (1 <= d <= _last_day(y, mo)):
                return None
            lo = hi = dt.date(y, mo, d)
        rest = s2[len(m.group(0)):]
        if rest.startswith("~"):
            lo, hi = lo - dt.timedelta(days=7), hi + dt.timedelta(days=7)
        elif rest.startswith("+"):
            hi = max(hi, dt.date.fromisoformat(FREEZE_DATE))
        r2 = re.match(r"/(\d{2})", rest)
        if r2 and 1 <= int(r2.group(1)) <= 12:
            m2 = int(r2.group(1))
            y2 = y + (m2 < mo)
            hi = dt.date(y2, m2, _last_day(y2, m2))
    if le:
        lo = hi - dt.timedelta(days=183)
    return lo.isoformat(), hi.isoformat()


def dev_units():
    """مجموعةُ التطوير لـC5 (صفوفُ جرد EX من مدوّنة V3 — لا B48 ولا مرفقَ الجلسة) ⟵ [(رمز · من · إلى · معرّف)] ‏+ عددُ غيرِ المؤرَّخ."""
    inv = (_j(INVENTORY, {}) or {}).get("rows") or []
    out, undated = [], collections.Counter()
    for r in inv:
        if " · V3" not in str(r.get("SOURCE")):
            continue
        span = date_span(r.get("DATE"))
        for t in r.get("TICKER") or []:
            t = str(t).upper()
            if not re.fullmatch(r"[A-Z][A-Z.\-]{0,6}", t):
                continue
            if span:
                out.append((t, span[0], span[1], "EX:" + str(r.get("IMAGE_ID"))))
            else:
                undated[t] += 1
    return out, dict(undated)


def v4_dev_decisions():
    """قراراتُ V4 التطويريّة لـC8: حالاتُ V4 (157) بتاريخ عبارتها ‏+ تواريخُ الذهبيّة ⟵ [(رمز · تاريخ · معرّف)]."""
    out = []
    for c in (_j(CASES_V4, {}) or {}).get("cases") or []:
        sd = c.get("statement_date")
        for t in c.get("tickers") or []:
            if sd and t:
                out.append((str(t).upper(), str(sd)[:10], "V4:" + c["case"]))
    for sym, g in ((_j(GOLDEN, {}) or {}).get("dates") or {}).items():
        if g.get("asof"):
            out.append((sym.upper(), g["asof"], "GOLDEN:" + sym))
    return out


def window_lo(decision_date, n=CYCLE_SESSIONS):
    return RN.prev_trading_days(decision_date, n)[-1]


def chart_window_hits(symbol, decision_date, units=None):
    """C5 🧩: الرمزُ في مجموعة التطوير بتاريخٍ يتقاطع مع [أوّل الـ120 جلسةً قبل القرار · يومه] ⟵ معرّفات."""
    if not symbol or not decision_date:
        return []
    units = dev_units()[0] if units is None else units
    lo = window_lo(decision_date)
    return sorted({u[3] for u in units if u[0] == symbol.upper() and u[1] <= decision_date and u[2] >= lo})


def v4_exposure_hits(symbol, decision_date, decisions=None):
    """C8 🧩: قرارُ V4 تطويريّ على الرمز داخل النافذة نفسِها ⟵ معرّفات."""
    if not symbol or not decision_date:
        return []
    decisions = v4_dev_decisions() if decisions is None else decisions
    lo = window_lo(decision_date)
    return sorted({d[2] for d in decisions if d[0] == symbol.upper() and lo <= d[1] <= decision_date})


def same_case_hits(symbol, decision_date, decisions=None, days=SAME_CASE_DAYS):
    """C4: الرمزُ ‏+ تاريخُ القرار ±3 أيّام في حالات V4 أو الذهبيّة (= batch_intake.case_overlap)."""
    if not symbol or not decision_date:
        return []
    decisions = v4_dev_decisions() if decisions is None else decisions
    d0 = dt.date.fromisoformat(decision_date)
    return sorted({d[2] for d in decisions if d[0] == symbol.upper() and abs((dt.date.fromisoformat(d[1]) - d0).days) <= days})


def corpus_index():
    """المدوّنةُ المجمَّدة لـC1/C2/C7: {sha256 · dhash256 · phash64 · id · file}."""
    return [{"id": i["id"], "file": i.get("file"), "sha256": i.get("sha256"), "dhash256": i.get("dhash256"), "phash64": i.get("phash64")}
            for i in (_j(CORPUS, {}) or {}).get("images") or []]


def _ham(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def perceptual_hits(fp, others):
    """C1/C2 مقابل قائمةٍ ({id · sha256 · dhash256 · phash64}) ⟵ (exact · near · nearest5)."""
    exact, near, dist = [], [], []
    for o in others:
        if fp.get("sha256") and o.get("sha256") == fp["sha256"]:
            exact.append(o["id"])
            continue
        if not (fp.get("dhash256") and fp.get("phash64") and o.get("dhash256") and o.get("phash64")):
            continue
        d, p = _ham(fp["dhash256"], o["dhash256"]), _ham(fp["phash64"], o["phash64"])
        dist.append((d + 4 * p, d, p, o["id"]))
        if d <= DUP_DHASH256_MAX and p <= DUP_PHASH_MAX:
            near.append(o["id"])
    dist.sort()
    return sorted(exact), sorted(near), [{"id": x[3], "dhash256_dist": x[1], "phash_dist": x[2]} for x in dist[:5]]


def corpus_refs(image_id, file_rel):
    """C7: المعرّفُ أو الملفّ في سجلّ المدوّنة المجمَّد أو المرور البصريّ لـV4 أو جرد EX كوحدةٍ تطويريّة."""
    hits = []
    if any(i.get("id") == image_id or i.get("file") == file_rel for i in (_j(CORPUS, {}) or {}).get("images") or []):
        hits.append("CORPUS")
    if os.path.exists(VISUAL_V4):
        with open(VISUAL_V4, encoding="utf-8") as f:
            if any(json.loads(line).get("unit") == image_id for line in f if line.strip()):
                hits.append("VISUAL_PASS_V4")
    inv = (_j(INVENTORY, {}) or {}).get("rows") or []
    if any(r.get("IMAGE_ID") == image_id and " · V3" in str(r.get("SOURCE")) for r in inv):
        hits.append("EX_DEV")
    return hits


# ── ⑥ المصدريّة (RULE #4 · §⑤) ────────────────────────────────────────────────
def _ny_date(utc_iso):
    try:
        from zoneinfo import ZoneInfo
        t = dt.datetime.fromisoformat(str(utc_iso).replace("Z", "+00:00"))
        return t.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:                                                   # noqa: BLE001
        return None


def provenance(tg, fp, ann, case_id=None):
    """الحقولُ الثلاثة عشر ‏+ الثقة ‏+ الحرجُ المجهول. `tg` صفُّ الجامع (أو `telegram` المانيفست) · `fp` البصمات · `ann` قراءةُ العين."""
    tg, fp, ann = tg or {}, fp or {}, ann or {}
    fwd = tg.get("forward") if isinstance(tg.get("forward"), dict) else None
    mv = int(tg.get("meta_v") or 1)
    if mv >= 2:
        ftype = tg.get("forward_type") if tg.get("forward_type") in FORWARD_TYPES else "UNKNOWN"
    else:
        ftype = (fwd or {}).get("type") if (fwd or {}).get("type") in FORWARD_TYPES else "UNKNOWN"
    if fwd and fwd.get("date"):
        opt, basis = fwd["date"], "FORWARD_METADATA"
    elif ann.get("post_timestamp_visible") and ann.get("post_timestamp_utc") and ann.get("post_timestamp_tz"):
        opt, basis = ann["post_timestamp_utc"], "VISIBLE_POST_TIMESTAMP"
    else:
        opt, basis = "UNKNOWN", "UNKNOWN"
    if ftype == "channel" and (fwd or {}).get("chat_username"):
        pcm = {k: fwd.get(k) for k in ("chat_title", "chat_username", "origin_message_id", "author_signature") if fwd.get(k)}
    elif ftype in FORWARD_TYPES:
        pcm = "N/A"
    else:
        pcm = "UNKNOWN"
    ph = {k: fp.get(k) for k in ("dhash256", "phash64")} if fp.get("dhash256") and fp.get("phash64") else "UNKNOWN"
    f = {"CASE_ID": case_id or "—", "SOURCE": "telegram_bot" + (f" · run {tg.get('run_id')}" if tg.get("run_id") else ""),
         "SOURCE_MESSAGE_ID": tg.get("message_id") if tg.get("message_id") is not None else "UNKNOWN",
         "CAPTURE_TIMESTAMP": tg.get("collected_utc") or fp.get("collected_utc") or "UNKNOWN",
         "ORIGINAL_POST_TIMESTAMP": opt, "FORWARD_TYPE": ftype, "PUBLIC_CHANNEL_METADATA": pcm,
         "IMAGE_HASH": fp.get("sha256") or "UNKNOWN", "PERCEPTUAL_HASH": ph,
         "TICKER": ann.get("symbol") or "UNKNOWN", "TIMEFRAME": ann.get("timeframe") or "UNKNOWN",
         "DATE_VISIBLE": ann.get("date_evidence") or ann.get("date_visible") or "UNKNOWN"}
    missing = [k for k in CRITICAL if f[k] in (None, "", "UNKNOWN")]
    if not missing:
        conf = "HIGH" if basis == "FORWARD_METADATA" else "MEDIUM"
    elif ann.get("decision_date") and f["CAPTURE_TIMESTAMP"] != "UNKNOWN":
        conf = "LOW"
    else:
        conf = "UNKNOWN"
    f["PROVENANCE_CONFIDENCE"] = conf
    return {"fields": f, "basis": basis, "missing_critical": missing, "meta_v": mv,
            "decision_date_from_post": _ny_date(opt) if basis != "UNKNOWN" else None}


def sample_of(conf):
    return "PRIMARY" if conf in PRIMARY_CONF else "SECONDARY"


# ── ⑦ كائنُ قرار V4 (PHASE 5-6) ───────────────────────────────────────────────
def decision_graph(d):
    """المسار: tech_state ⟵ STATE_DECISION ⟵ validity(context_input) ⟵ النهائيّ — بدوالّ المحرّك المجمَّد ⟵ (المسار · متّسق؟)."""
    ts = d.get("tech_state")
    base = E.STATE_DECISION.get(ts)
    blocks, missing = E.validity(d.get("context_input"))
    if base is None or base == "UNKNOWN":
        final = "UNKNOWN"
    elif any(b[0] == "REJECT" for b in blocks):
        final = "REJECT"
    elif base == "WAIT" or blocks:
        final = "WAIT"
    elif missing:
        final = "UNKNOWN"
    else:
        final = "READY"
    graph = [f"tech_state={ts}", f"STATE_DECISION={base}", f"validity.blocks={[b[1] for b in blocks]}",
             f"validity.missing={len(missing)}", f"final={final}"]
    return graph, final == d.get("state")


def v4_object(rec, case, ep):
    d = rec.get("decision") or {}
    st = d.get("structure") or {}
    pr = d.get("params") or {}
    pl = d.get("price_location") or {}
    mc = d.get("market_context") or {}
    sr = d.get("support_resistance") or {}

    def pv(k):
        return (pr.get(k) or {}).get("value")

    graph, ok = decision_graph(d)
    proto = case.get("protocol") or {}
    blind = {"symbol": case.get("symbol"), "decision_date": case.get("decision_date"), "timeframe": "1D"}
    hold, rise = st.get("hold_sessions"), st.get("rise_pct")
    return {"CASE_ID": rec.get("case_id"), "V4_VERSION": f"{d.get('engine')} · {d.get('rules_version')}",
            "V4_COMMIT": ep["V4_COMMIT"], "RUN_COMMIT": (rec.get("meta") or {}).get("commit"),
            "CONFIG_HASH": ep["V4_CONFIG_HASH"], "INPUT_HASH": proto.get("input_hash") or sha(blind),
            "CASE_SHA256": rec.get("case_sha256"), "SNAPSHOT_SHA256": rec.get("snapshot_sha256"),
            "DATA_AVAILABLE": {"firewall": (rec.get("firewall") or {}).get("verdict"), "bars": (rec.get("firewall") or {}).get("bars"),
                               "last_bar": (rec.get("firewall") or {}).get("last_bar"), "warns": (rec.get("firewall") or {}).get("warns"),
                               "context": rec.get("context_provenance")},
            "TIMEFRAME": d.get("timeframe"),
            "STRUCTURE": {k: st.get(k) for k in ("bottom", "bottom_body_low", "bottom_date", "depth_pct", "hold_sessions", "rise_pct",
                                                 "prior_base") if k in st},
            "PATTERN": [p.get("pattern") for p in d.get("patterns") or []],
            "BOTTOM_CYCLE": {"bottom": st.get("bottom"), "bottom_date": st.get("bottom_date"),
                             "cycle_high": mc.get("cycle_high"), "cycle_high_date": mc.get("cycle_high_date")},
            "5_SESSION_HOLD": {"value": hold, "required": pv("HOLD_MIN"),
                               "met": (hold is not None and pv("HOLD_MIN") is not None and hold >= pv("HOLD_MIN"))},
            "TEST_RISE": {"value": rise, "required": pv("RISE_TEST_PCT"),
                          "met": (rise is not None and pv("RISE_TEST_PCT") is not None and rise >= pv("RISE_TEST_PCT"))},
            "15_PERCENT_ZONE": {"zone": sr.get("zone"), "in_zone": pl.get("in_zone"), "zone_pct": pv("ZONE_PCT")},
            "HOLD_SWEEP_RETURN": {"depth_pct": st.get("depth_pct"), "sweep_max_pct": pv("SWEEP_MAX_PCT"), "hold_zone": pv("HOLD_ZONE")},
            "VALIDITY": {"blocking": d.get("blocking_reasons"), "missing": d.get("missing_information"),
                         "context_input": d.get("context_input")},
            "ENTRY_MECHANISM": d.get("entry"), "INVALIDATION": d.get("invalidation"), "TARGET": d.get("target"),
            "FINAL_DECISION": d.get("state"), "DECISION_REASON": (d.get("explain") or []) + (d.get("decision_reasons") or []),
            "DECISION_GRAPH": graph, "GRAPH_CONSISTENT": ok, "TECH_STATE": d.get("tech_state"),
            "FINAL_STATE": d.get("state"), "V4_RESULT_SHA256": rec.get("decision_sha256")}


# ── ⑧ قرارُ فيصل (PHASE 7) ───────────────────────────────────────────────────
def faisal_object(frec, case_id):
    frec = frec or {}
    ev, q, legacy = frec.get("evidence_class"), frec.get("evidence_quote"), False
    if ev is None and case_id in LEGACY_EVIDENCE:
        ev, q = LEGACY_EVIDENCE[case_id]
        legacy = True
    quote_ok = bool(q) and str(q) in str(frec.get("quote") or "")
    lab4 = frec.get("label4")
    if ev in ("DIRECT", "STRONG_INFERENCE") and quote_ok and lab4 in ("READY", "WAIT", "REJECT", "MIXED"):
        eff = lab4
    else:
        eff = "UNKNOWN"
    return {"label": frec.get("label"), "label4": lab4, "evidence_class": ev if ev in EVIDENCE_CLASSES else "INVALID_RECORD",
            "evidence_quote": q, "quote_verbatim": quote_ok, "effective_label": eff, "legacy": legacy,
            "components": frec.get("components_f") or {}, "px_f": frec.get("px_f"), "plan_f": frec.get("plan_f"),
            "pattern_f": frec.get("pattern_f"), "timeframe_f": frec.get("timeframe_f"),
            "external_codes": frec.get("external_codes") or [], "v4_2": frec.get("v4_2"),
            "false_ready_cause": frec.get("false_ready_cause")}


# ── ⑨ المطابقة (PHASE 8) ──────────────────────────────────────────────────────
def match_class(f_eff, v4_state):
    if f_eff in (None, "UNKNOWN"):
        return "FAISAL_UNKNOWN"
    if f_eff == "MIXED":
        return "UNRESOLVED"
    if v4_state == "UNKNOWN":
        return "FALSE_UNKNOWN"
    if v4_state == f_eff:
        return "MATCH"
    if v4_state == "READY":
        return "FALSE_READY"
    if v4_state == "WAIT":
        return "FALSE_WAIT" if f_eff == "READY" else "MISMATCH_WAIT_REJECT"
    if v4_state == "REJECT":
        return "FALSE_REJECT" if f_eff == "READY" else "MISMATCH_REJECT_WAIT"
    return "UNRESOLVED"


# ── ⑩ المكوّنات (PHASE 16) ────────────────────────────────────────────────────
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0


def v4_components(d):
    e = d.get("entry") or {}
    zone = [float(x) for x in (e.get("type1_bids") or []) if _num(x)]
    inv = [x for x in d.get("invalidation") or [] if isinstance(x, dict) and _num(x.get("price"))]
    bottom = (d.get("structure") or {}).get("bottom")
    return {"ENTRY": {"zone": sorted(zone)[:1] + sorted(zone)[-1:] if zone else [],
                      "points": [float(e["type2_liberation"])] if _num(e.get("type2_liberation")) else []},
            "STOP": sorted({float(x["price"]) for x in inv if STOP_RULE in str(x.get("rule"))}),
            "INVALIDATION": sorted({float(x["price"]) for x in inv} | ({float(bottom)} if _num(bottom) else set())),
            "TARGET": sorted({float(x["price"]) for x in d.get("target") or [] if isinstance(x, dict) and _num(x.get("price"))})}


def _near(p, q, tol=LEVEL_TOL):
    return abs(p / q - 1.0) <= tol


def compare_components(fcomp, v4c, scale):
    out = {}
    for c in COMPONENTS:
        f = (fcomp or {}).get(c)
        if f is None:
            out[c] = {"status": "FAISAL_NOT_STATED"}
            continue
        if f == "NONE":
            out[c] = {"status": "FAISAL_NONE"}
            continue
        prices = [float(p) for p in (f if isinstance(f, list) else [f]) if _num(p)]
        if scale == "MISMATCH":
            out[c] = {"status": "SCALE_MISMATCH", "faisal": prices}
            continue
        if c == "ENTRY":
            zone, pts = v4c["ENTRY"]["zone"], v4c["ENTRY"]["points"]
            if not zone and not pts:
                out[c] = {"status": "V4_NOT_AVAILABLE", "faisal": prices}
                continue
            hit = any((len(zone) == 2 and zone[0] * (1 - LEVEL_TOL) <= p <= zone[1] * (1 + LEVEL_TOL))
                      or any(_near(p, q) for q in pts + zone) for p in prices)
            out[c] = {"status": "MATCH" if hit else "MISMATCH", "faisal": prices, "v4": {"zone": zone, "points": pts}}
            continue
        v = v4c[c]
        if not v:
            out[c] = {"status": "V4_NOT_AVAILABLE", "faisal": prices}
            continue
        hit = any(_near(p, q) for p in prices for q in v)
        out[c] = {"status": "MATCH" if hit else "MISMATCH", "faisal": prices, "v4": v}
    return out


def scale_status(px_f, d):
    close = (d.get("price_location") or {}).get("close")
    if not _num(px_f) or not _num(close):
        return "UNCHECKED"
    return "MISMATCH" if abs(close / px_f - 1.0) > PX_TOL else "OK"


# ── ⑪ النظرُ المستقبليّ LA1-LA6 (PHASE 17) ─────────────────────────────────────
def run_case_blind():
    """LA4: `run_case` لا يقرأ من الحالة إلّا symbol وdecision_date (AST) ⟵ (ok · المفاتيح)."""
    import inspect
    tree = ast.parse(inspect.getsource(RN.run_case))
    keys, other = set(), []
    for x in ast.walk(tree):
        if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id == "case":
            keys.add(x.slice.value if isinstance(x.slice, ast.Constant) else "?")
        elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and isinstance(x.func.value, ast.Name) \
                and x.func.value.id == "case":
            other.append(x.func.attr)
    return keys <= {"symbol", "decision_date"} and not other, sorted(map(str, keys)) + other


def _scaled(rows, k):
    out = []
    for r in rows:
        r2 = list(r)
        for i in (1, 2, 3, 4):
            if i < len(r2) and _num(r2[i]):
                r2[i] = r2[i] * k
        if len(r2) > 5 and isinstance(r2[5], (int, float)) and not isinstance(r2[5], bool):
            r2[5] = r2[5] / k
        out.append(r2)
    return out


def lookahead(case, rec, snap_rows, order, decide=None):
    """⟵ {LA1..LA6 · verdict}: PASS · INVALIDATED_EXTERNAL (LA5 وحدَه) · INVALIDATED_DEFECT (LA1-LA4/LA6 ⟵ BLOCKED)."""
    decide = decide or RN.decide
    asof, sym = case["decision_date"], case["symbol"]
    d = rec.get("decision") or {}
    fw = rec.get("firewall") or {}
    dates = [str(r[0])[:10] for r in snap_rows]
    la = {"LA1_FUTURE_CANDLES": bool(dates) and all(x < asof for x in dates) and str(d.get("asof") or "") < asof
          and not any(str(f).startswith("F7") for f in fw.get("fails") or [])}
    ctx, prov = rec.get("context") or {}, rec.get("context_provenance") or {}
    la["LA2_BLIND_INPUT"] = (set(ctx) == CTX_KEYS and ctx == (d.get("context_input") or {})
                             and all(str(prov.get(k, "")).startswith(MECH_PREFIX) for k in CTX_KEYS)
                             and all(ctx.get(k) is None for k in ("groups", "offering_pending", "operator_press")))
    la["LA3_ORDER"] = bool(order.get("ok"))
    la["LA4_NO_IMAGE_TO_V4"] = run_case_blind()[0]
    try:
        la["LA6_REPLAY"] = sha(decide(snap_rows, asof, ctx, sym)) == rec.get("decision_sha256")
    except Exception:                                                   # noqa: BLE001
        la["LA6_REPLAY"] = False
    inv = True
    try:
        for k in SCALE_FACTORS:
            d2 = decide(_scaled(snap_rows, k), asof, ctx, sym)
            if d2.get("state") != d.get("state") or d2.get("tech_state") != d.get("tech_state"):
                inv = False
    except Exception:                                                   # noqa: BLE001
        inv = False
    if inv:
        la5 = "PASS_SCALE_INVARIANT"
    else:
        sp = (rec.get("meta") or {}).get("splits")
        run_day = str((rec.get("meta") or {}).get("utc") or "")[:10]
        if sp is None:
            la5 = "INVALIDATE_SPLITS_UNKNOWN"
        elif any(asof <= str(s[0])[:10] <= run_day for s in sp):
            la5 = "INVALIDATE_POST_DECISION_SPLIT"
        else:
            la5 = "PASS_NO_POST_DECISION_SPLIT"
    la["LA5_CORPORATE_ACTION"] = la5
    defect = not all(la[k] for k in ("LA1_FUTURE_CANDLES", "LA2_BLIND_INPUT", "LA3_ORDER", "LA4_NO_IMAGE_TO_V4", "LA6_REPLAY"))
    verdict = "INVALIDATED_DEFECT" if defect else ("INVALIDATED_EXTERNAL" if la5.startswith("INVALIDATE") else "PASS")
    return dict(la, verdict=verdict)


def ledger_order(lg, case_id):
    """LA3 من السلسلة: آخرُ نسخة حالة ⟵ قرارُ V4 لها ⟵ (إن وُجدت) كلمةُ فيصل بعده وب`after_v4_seq` = قيده."""
    cs = lg.entries("case", case_id)
    if not cs:
        return {"ok": False, "why": "NO_CASE"}
    c = cs[-1]
    vs = [e for e in lg.entries("v4", case_id) if e.get("case_version") == c["version"]]
    if not vs:
        return {"ok": True, "pending": "V4", "case_seq": c["seq"]}
    v = vs[-1]
    fs = lg.entries("faisal", case_id)
    ok = c["seq"] < v["seq"]
    out = {"case_seq": c["seq"], "v4_seq": v["seq"]}
    if fs:
        f = fs[-1]
        frec = lg.read(f["path"])
        ok = ok and v["seq"] < f["seq"] and frec.get("after_v4_seq") == v["seq"]
        out["faisal_seq"] = f["seq"]
    else:
        out["pending"] = "FAISAL"
    out["ok"] = ok
    return out


# ── ⑫ التنوّع (PHASE 11) ──────────────────────────────────────────────────────
def price_bucket(close):
    if not _num(close):
        return "UNKNOWN"
    return "<1" if close < 1 else "1-5" if close < 5 else "5-20" if close < 20 else "20+"


def ext_categories(codes):
    txt = " ".join(map(str, codes or [])).lower()
    cats = [k for k, words in EXT_CATEGORIES if any(w.lower() in txt for w in words)]
    return cats or (["other"] if codes else ["none"])


def diversity(rows):
    """الأبعادُ التسعة على حالات PRIMARY ‏+ LOW_DIVERSITY (20 متتالية بالمفتاح نفسِه) — وسمٌ لا استبعاد."""
    dims = collections.defaultdict(collections.Counter)
    run, best, prev = 0, 0, None
    for r in rows:
        dv = r["DIVERSITY"]
        for k, v in dv.items():
            for x in (v if isinstance(v, list) else [v]):
                dims[k][str(x)] += 1
        key = (r["V4"]["TECH_STATE"], r["FAISAL"]["effective_label"])
        run = run + 1 if key == prev else 1
        prev = key
        best = max(best, run)
    return {"dims": {k: dict(sorted(v.items())) for k, v in sorted(dims.items())}, "longest_same_setup_run": best,
            "LOW_DIVERSITY": best >= LOW_DIV_RUN}


# ── ⑬ المقاييس (PHASE 13-15) ──────────────────────────────────────────────────
def wilson(k, n):
    if not n:
        return None
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def newcombe(k1, n1, k2, n2):
    """فرقُ نسبتين مستقلّتين (نيوكومب الهجين · طريقة 10) ⟵ [أدنى · أعلى] أو None."""
    if not n1 or not n2:
        return None
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return [round(lo, 4), round(hi, 4)]


def _ratio(k, n):
    return round(k / n, 4) if n else "UNDEFINED"


def ready_structurally_impossible():
    """فحصُ FVO1 حيًّا: هل يترك السياقُ الآليّ القروبات والطرح والمضارب None دائمًا (فلا READY ولا REJECT)؟"""
    res = []
    for ctb, live in (([], None), ([{"symbol": "SYNT", "date": "2026-10-14", "shares_available": 100, "source": "x"}], None),
                      ([], lambda s: 5)):
        cx, _ = RN.validity_context("SYNT", "2026-10-15", ctb, "2026-10-15", live_borrow=live)
        bl, mi = E.validity(cx)
        res.append(all(cx[k] is None for k in ("groups", "offering_pending", "operator_press")) and bool(mi)
                   and not any(b[0] == "REJECT" for b in bl))
    return all(res)


def metrics(primary):
    """على حالات PRIMARY المكتملة غير المُبطلة ⟵ العدّاداتُ والدقّةُ والاستدعاءُ وخطُّ الأساس وV4_BEATS_BASELINE وREADY_CLASS_VALIDATED وP1."""
    cnt = collections.Counter(r["MATCH_CLASS"] for r in primary)
    comp = [r for r in primary if r["FAISAL"]["effective_label"] in ("READY", "WAIT", "REJECT")]
    n = len(comp)
    out = {"by_class": {k: cnt.get(k, 0) for k in MATCH_CLASSES}, "n_valid": len(primary), "n_comparable": n,
           "MATCHES": cnt.get("MATCH", 0), "MISMATCHES": sum(cnt.get(k, 0) for k in MISMATCH_CLASSES),
           "V4_UNKNOWN": sum(1 for r in primary if r["V4"]["FINAL_STATE"] == "UNKNOWN"),
           "FAISAL_UNKNOWN": cnt.get("FAISAL_UNKNOWN", 0), "UNRESOLVED": cnt.get("UNRESOLVED", 0)}
    cls = {}
    for s in ("READY", "WAIT", "REJECT"):
        tp = sum(1 for r in comp if r["FAISAL"]["effective_label"] == s and r["V4"]["FINAL_STATE"] == s)
        pred = sum(1 for r in comp if r["V4"]["FINAL_STATE"] == s)
        act = sum(1 for r in comp if r["FAISAL"]["effective_label"] == s)
        cls[s] = {"tp": tp, "v4": pred, "faisal": act, "precision": _ratio(tp, pred), "recall": _ratio(tp, act),
                  "precision_wilson": wilson(tp, pred) if pred >= WILSON_MIN else None,
                  "recall_wilson": wilson(tp, act) if act >= WILSON_MIN else None}
    out["per_class"] = cls
    fr = cnt.get("FALSE_READY", 0)
    nonready = sum(1 for r in comp if r["FAISAL"]["effective_label"] != "READY")
    out["FALSE_READY_RATE"] = _ratio(fr, n)
    out["FALSE_READY_RATE_WILSON"] = wilson(fr, n) if n >= WILSON_MIN else None
    out["FALSE_READY_FPR"] = _ratio(fr, nonready)
    aw = sum(1 for r in comp if r["FAISAL"]["effective_label"] == "WAIT")
    out["ALWAYS_WAIT_MATCH"] = aw
    out["exact_rate"] = _ratio(out["MATCHES"], n)
    out["always_wait_rate"] = _ratio(aw, n)
    out["exact_wilson"] = wilson(out["MATCHES"], n) if n >= WILSON_MIN else None
    b = sum(1 for r in comp if r["MATCH_CLASS"] == "MATCH" and r["FAISAL"]["effective_label"] != "WAIT")
    c = sum(1 for r in comp if r["MATCH_CLASS"] != "MATCH" and r["FAISAL"]["effective_label"] == "WAIT")
    if n == 0:
        beats = "UNKNOWN"
    elif b == 0:
        beats = "NO"
    elif b + c < WILSON_MIN:
        beats = "UNKNOWN"
    else:
        beats = "YES" if wilson(b, b + c)[0] > 0.5 else "NO"
    out["baseline_discordant"] = {"b_v4_only": b, "c_baseline_only": c}
    out["V4_BEATS_BASELINE"] = beats
    rd = cls["READY"]
    if ready_structurally_impossible():
        rv = "NO"
        out["READY_CLASS_BASIS"] = "STRUCTURAL (FVO1): V4 الأماميّ ∈ {WAIT · UNKNOWN}"
    elif rd["faisal"] >= READY_VALID_N and rd["v4"] >= READY_V4_MIN and wilson(rd["tp"], rd["faisal"])[0] >= 0.5 \
            and wilson(rd["tp"], rd["v4"])[0] >= 0.5:
        rv, out["READY_CLASS_BASIS"] = "YES", "CRITERIA_MET"
    elif rd["faisal"] >= WILSON_MIN and wilson(rd["tp"], rd["faisal"])[1] < 0.5:
        rv, out["READY_CLASS_BASIS"] = "NO", "RECALL_UPPER_BELOW_0.5"
    else:
        rv, out["READY_CLASS_BASIS"] = "UNKNOWN", "INSUFFICIENT_READY"
    out["READY_CLASS_VALIDATED"] = rv
    tr = {s for s, v in E.STATE_DECISION.items() if v == "TECH_READY"}
    fr_ready = [r for r in comp if r["FAISAL"]["effective_label"] == "READY"]
    fr_other = [r for r in comp if r["FAISAL"]["effective_label"] in ("WAIT", "REJECT")]
    k1 = sum(1 for r in fr_ready if r["V4"]["TECH_STATE"] in tr)
    k2 = sum(1 for r in fr_other if r["V4"]["TECH_STATE"] in tr)
    nc = newcombe(k1, len(fr_ready), k2, len(fr_other))
    out["P1_TECH_READY"] = {"faisal_ready": len(fr_ready), "tech_ready_given_ready": k1, "faisal_wait_reject": len(fr_other),
                            "tech_ready_given_wait_reject": k2, "newcombe95": nc,
                            "met": bool(len(fr_ready) >= READY_COVER and len(fr_other) >= READY_COVER and nc and nc[0] > 0)}
    out["coverage"] = {s: cls[s]["faisal"] for s in ("READY", "WAIT", "REJECT")}
    return out


def band(n):
    for lim, name in BANDS:
        if n < lim:
            return name
    return "MINIMUM_TARGET_REACHED"


def unexplained_failure(primary):
    bad_fr = any(r["MATCH_CLASS"] == "FALSE_READY" and (r["FAISAL"].get("false_ready_cause") or "UNKNOWN")
                 in ("UNKNOWN", "IMPLEMENTATION_BUG", "DATA_BUG") for r in primary)
    by = collections.defaultdict(list)
    for r in primary:
        if r["MATCH_CLASS"] in MISMATCH_CLASSES:
            by[r["MATCH_CLASS"]].append(((r["FAISAL"].get("v4_2") or {}).get("WHY_V4_FAILED") or "UNKNOWN"))
    sys_unknown = any(len(v) >= READY_COVER and collections.Counter(v).most_common(1)[0][0] == "UNKNOWN" for v in by.values())
    return bad_fr or sys_unknown


def final_state(integrity_ok, lookahead_ok, provenance_ok, collector, n_primary, m, unexplained):
    if not integrity_ok or not lookahead_ok or not provenance_ok or collector == "FAIL":
        return "VALIDATION_BLOCKED"
    cov = m["coverage"]
    if n_primary < N_MIN or cov["READY"] < READY_COVER:
        return "INSUFFICIENT_SAMPLE"
    if all(cov[s] >= READY_COVER for s in ("READY", "WAIT", "REJECT")) and m["V4_BEATS_BASELINE"] == "YES" \
            and m["READY_CLASS_VALIDATED"] == "YES" and not unexplained:
        return "VALIDATED"
    if m["by_class"]["FALSE_READY"] == 0 and (m["P1_TECH_READY"]["met"] or m["V4_BEATS_BASELINE"] == "YES"):
        return "PARTIALLY_VALIDATED"
    return "NOT_VALIDATED"


# ── ⑭ البناء: المرشَّحون · الحالات · الحالة ───────────────────────────────────
def legacy_candidates():
    """B48 (قبل العقد): أصنافُه الخمسة ⟵ السبعة (§⑦) ‏+ C5/C8 على NEW_PROSPECTIVE ‏+ مصدريّةُ كلّ صورة."""
    m = _j(B48_MANIFEST)
    if not m:
        return []
    ann = (_j(B48_ANN, {}) or {}).get("images") or {}
    units, _ = dev_units()
    decs = v4_dev_decisions()
    out = []
    for it in m["items"]:
        a = ann.get(it["image_id"]) or {}
        cls, why = map_legacy_class(it["class"], it["class_reason"], it.get("exclusion"), it.get("validation_case"))
        checks = {"C1": it["duplicate_status"].startswith("EXACT") or it["duplicate_status"] == "SEEN_FILE_ID",
                  "C2": it["derivative_status"].startswith("NEAR"), "C3": it["derivative_status"].startswith("OCR"),
                  "C6": bool(a.get("visual_derivative_of")), "C4": bool(a.get("same_case_of") or it.get("auto_same_case")),
                  "C7": False, "C5": [], "C8": []}
        if cls == "NEW_PROSPECTIVE":
            checks["C5"] = chart_window_hits(a.get("symbol"), a.get("decision_date"), units)
            checks["C8"] = v4_exposure_hits(a.get("symbol"), a.get("decision_date"), decs)
            checks["C7"] = bool(corpus_refs(it["image_id"], it.get("file")))
            if checks["C5"] or checks["C8"] or checks["C7"]:
                cls = "CONTAMINATED"
                why = "C5:" + ",".join(checks["C5"]) if checks["C5"] else "C8:" + ",".join(checks["C8"]) if checks["C8"] else "C7"
        fp = {k: it.get(k) for k in ("sha256", "dhash256", "phash64")}
        fp["collected_utc"] = it.get("collected_utc")
        tg = dict(it.get("telegram") or {}, collected_utc=it.get("collected_utc"))
        out.append({"batch": m["batch_id"], "image_id": it["image_id"], "file": it.get("file"), "class7": cls, "reason": why,
                    "legacy_class": it["class"], "legacy_reason": it["class_reason"], "checks": checks,
                    "symbol": a.get("symbol"), "decision_date": a.get("decision_date"),
                    "provenance": provenance(tg, fp, a)})
    return out


def protocol_candidates():
    """دفعاتُ الاستلام بعد العقد: `final_protocol/intake/<BATCH>/INTAKE.json` (يكتبها `seal`)."""
    out = []
    if os.path.isdir(INTAKE_DIR):
        for b in sorted(os.listdir(INTAKE_DIR)):
            doc = _j(os.path.join(INTAKE_DIR, b, "INTAKE.json"))
            if doc:
                out += doc.get("candidates") or []
    return out


def _case_unit(case):
    return case.get("unit_id") or os.path.splitext(os.path.basename(case.get("image") or ""))[0]


def case_rows(lg, ep, cands):
    """لكلّ حالةٍ مختومة: مصدريّتُها ⟵ عيّنتُها · كائنا القرار · المطابقة · المكوّنات · النظرُ المستقبليّ · التنوّع."""
    by_unit = {c["image_id"]: c for c in cands}
    rows = []
    for cid, ce in sorted(_latest_cases(lg).items()):
        case = lg.read(ce["path"])
        proto = case.get("protocol") or {}
        cand = by_unit.get(_case_unit(case)) or {}
        prov = json.loads(json.dumps(proto.get("provenance") or cand.get("provenance") or provenance({}, {}, {}, cid)))
        prov["fields"]["CASE_ID"] = cid
        conf = (prov.get("fields") or {}).get("PROVENANCE_CONFIDENCE", "UNKNOWN")
        row = {"CASE_ID": cid, "SYMBOL": case.get("symbol"), "DECISION_DATE": case.get("decision_date"),
               "LEGACY": not bool(proto), "PROVENANCE": prov, "PROVENANCE_CONFIDENCE": conf, "SAMPLE": sample_of(conf),
               "INTAKE_CLASS": cand.get("class7") or proto.get("intake", {}).get("class") or "UNKNOWN"}
        vs = [e for e in lg.entries("v4", cid) if e.get("case_version") == ce["version"]]
        if lg.entries("invalid", cid):
            row["STATUS"] = "INVALID_FOR_VALIDATION"
            row["INVALID"] = [lg.read(e["path"]) for e in lg.entries("invalid", cid)]
        if not vs:
            row.setdefault("STATUS", "PENDING_V4")
            rows.append(row)
            continue
        rec = lg.read(vs[-1]["path"])
        snap = lg.read(rec["snapshot_path"])["rows"]
        row["V4"] = v4_object(rec, case, ep)
        order = ledger_order(lg, cid)
        row["LOOKAHEAD"] = lookahead(case, rec, snap, order)
        fs = lg.entries("faisal", cid)
        if not fs:
            row.setdefault("STATUS", "PENDING_FAISAL")
            rows.append(row)
            continue
        frec = lg.read(fs[-1]["path"])
        fo = faisal_object(frec, cid)
        row["FAISAL"] = fo
        row["MATCH_CLASS"] = match_class(fo["effective_label"], row["V4"]["FINAL_STATE"])
        d = rec.get("decision") or {}
        row["COMPONENTS"] = compare_components(fo["components"], v4_components(d), scale_status(fo["px_f"], d))
        meta = rec.get("meta") or {}
        row["DIVERSITY"] = {"pattern": fo["pattern_f"] or "UNSPECIFIED", "v4_patterns": row["V4"]["PATTERN"] or ["NONE"],
                            "timeframe": fo["timeframe_f"] or case.get("timeframe_f") or "UNKNOWN", "ticker": case.get("symbol"),
                            "market_regime": ((meta.get("regime") or {}).get("state") if isinstance(meta.get("regime"), dict)
                                              else meta.get("regime")) or "UNKNOWN", "setup": row["V4"]["TECH_STATE"],
                            "decision": fo["effective_label"],
                            "price_range": price_bucket((d.get("price_location") or {}).get("close")),
                            "sector": meta.get("sector") or "UNKNOWN", "external_context": ext_categories(fo["external_codes"])}
        if row.get("STATUS") != "INVALID_FOR_VALIDATION":
            if (rec.get("firewall") or {}).get("verdict") != "VALID":
                row["STATUS"] = "INVALID_FOR_VALIDATION"
            elif row["LOOKAHEAD"]["verdict"] != "PASS":
                row["STATUS"] = "INVALIDATED_" + row["LOOKAHEAD"]["verdict"].split("_", 1)[1]
            else:
                row["STATUS"] = "COMPLETE"
        rows.append(row)
    return rows


def corpus_audit_status():
    n = ((_j(INVENTORY, {}) or {}).get("meta") or {}).get("numbers") or {}
    ok = (n.get("files_not_analyzed") == 0 and n.get("files_ocr_only") == 0 and n.get("needs_eye") == 0
          and n.get("high_info") == n.get("high_info_fully") and n.get("high_info"))
    return "COMPLETE" if ok else "INCOMPLETE"


def collector_row_ok(row, fp):
    """صفُّ صورةٍ محفوظةٍ من الجامع (meta_v 2) يحمل حقولَ §⑥ — والبصمةُ الإدراكيّة: مفتاحُها حاضر · وnull مقبولٌ حين تتعذّر عند الاستلام أيضًا ·
    وإن حُسبت في الطرفين فهي نفسُها (وإلّا تغيّر الملفُّ بعد الجمع). ⟵ (ok · الأسباب)."""
    why = [k for k in ("message_id", "date", "collected_utc", "run_id", "sha256", "forward_type") if not row.get(k)]
    for k in ("dhash256", "phash64"):
        if k not in row:
            why.append(k + ":ABSENT")
        elif row[k] is None and (fp or {}).get(k):
            why.append(k + ":NULL_BUT_READABLE")
        elif row[k] and (fp or {}).get(k) and row[k] != fp[k]:
            why.append(k + ":DIFFERS")
    if row.get("sha256") and (fp or {}).get("sha256") and row["sha256"] != fp["sha256"]:
        why.append("sha256:DIFFERS")
    return not why, why


def collector_status(cands):
    """قبولُ المسار الحيّ (§⑥): على صفوف `meta_v 2` التي دخلت الاستلام وحدَها (حتميّ) ⟵ LIVE_PENDING · PASS · FAIL."""
    rows = [c for c in cands if (c.get("provenance") or {}).get("meta_v", 1) >= 2 and c.get("saved")]
    if not rows:
        return {"simulated": "PASS_SIMULATED", "live": "LIVE_PENDING", "checked": 0, "bad": []}
    bad = [{"image_id": c["image_id"], "why": collector_row_ok(c.get("collector_row") or {}, c.get("fingerprint"))[1]}
           for c in rows if not collector_row_ok(c.get("collector_row") or {}, c.get("fingerprint"))[0]]
    return {"simulated": "PASS_SIMULATED", "live": "FAIL" if bad else "PASS", "checked": len(rows), "bad": bad}


def v4_2_candidates(rows):
    out = []
    for r in rows:
        if r.get("STATUS") == "COMPLETE" and r.get("MATCH_CLASS") in MISMATCH_CLASSES:
            q = (r["FAISAL"].get("v4_2") or {})
            out.append({k: (r["CASE_ID"] if k == "CASE_ID" else q.get(k, "PENDING_ANALYSIS")) for k in V4_2_FIELDS}
                       | {"MATCH_CLASS": r["MATCH_CLASS"], "SAMPLE": r["SAMPLE"]})
    return out


def build(ledger=None, epoch=None):
    """الحالةُ كاملةً — حتميّة · بلا شبكة · بلا كتابة."""
    lg = ledger or LG.Ledger()
    ep = epoch or current_epoch()
    if not ep:
        raise RuntimeError("لا حقبةَ مسجَّلة — `final_protocol.py epoch-init` أوّلًا (مرّةً واحدة)")
    ident = v4_identity()
    cands = legacy_candidates() + protocol_candidates()
    rows = case_rows(lg, ep, cands)
    integ = integrity(ep, ident, lg, rows)
    complete = [r for r in rows if r.get("STATUS") == "COMPLETE"]
    primary = [r for r in complete if r["SAMPLE"] == "PRIMARY"]
    secondary = [r for r in complete if r["SAMPLE"] == "SECONDARY"]
    m = metrics(primary)
    m2 = metrics(secondary)
    la_ok = not any(r.get("LOOKAHEAD", {}).get("verdict") == "INVALIDATED_DEFECT" for r in rows) \
        and all("LOOKAHEAD" in r for r in rows if "V4" in r)
    prov_ok = integ["checks"]["I8_LEDGER"]["ok"] and integ["checks"]["I9_META_PREFIX"]["ok"] \
        and integ["checks"]["I10_CASE_IMAGES"]["ok"] and all(not r["PROVENANCE"]["missing_critical"] for r in primary)
    col = collector_status(cands)
    unexpl = unexplained_failure(primary)
    state = final_state(integ["ok"], la_ok, prov_ok, col["live"], len(primary), m, unexpl)
    meth_changed = not all(integ["checks"][k]["ok"] for k in ("I1_V4_FROZEN", "I2_FREEZE_ID", "I3_CONFIG_HASH",
                                                               "I4_RULE_REGISTRY_HASH", "I5_TOOL_VERSION",
                                                               "I6_DATA_PIPELINE_VERSION", "I7_NO_REVISION"))
    by7 = collections.Counter(c["class7"] for c in cands)
    excluded = {"intake_not_new": sum(v for k, v in by7.items() if k != "NEW_PROSPECTIVE"), "secondary_provenance": 0,
                "invalid_data_quality": 0, "invalidated_lookahead": 0}
    for r in rows:                                     # سببٌ واحدٌ لكلّ حالة (متنافٍ · بالأسبقيّة) — لا عدَّ مزدوجًا
        if r["SAMPLE"] == "SECONDARY":
            excluded["secondary_provenance"] += 1
        elif r.get("STATUS") == "INVALID_FOR_VALIDATION":
            excluded["invalid_data_quality"] += 1
        elif str(r.get("STATUS", "")).startswith("INVALIDATED"):
            excluded["invalidated_lookahead"] += 1
    pending = sorted(r["CASE_ID"] for r in rows if str(r.get("STATUS", "")).startswith("PENDING") and r["SAMPLE"] == "PRIMARY")
    out = {"V4_FROZEN": "YES" if integ["checks"]["I1_V4_FROZEN"]["ok"] else "NO", "V4_COMMIT": ep["V4_COMMIT"],
           "CORPUS_AUDIT": corpus_audit_status(), "VALID_PROSPECTIVE_CASES": len(primary),
           "EXCLUDED_CASES": sum(excluded.values()), "MATCHES": m["MATCHES"], "MISMATCHES": m["MISMATCHES"],
           "FALSE_READY": m["by_class"]["FALSE_READY"], "FALSE_WAIT": m["by_class"]["FALSE_WAIT"],
           "FALSE_REJECT": m["by_class"]["FALSE_REJECT"], "FALSE_UNKNOWN": m["by_class"]["FALSE_UNKNOWN"],
           "V4_UNKNOWN": m["V4_UNKNOWN"], "FAISAL_UNKNOWN": m["FAISAL_UNKNOWN"], "ALWAYS_WAIT_MATCH": m["ALWAYS_WAIT_MATCH"],
           "V4_BEATS_BASELINE": m["V4_BEATS_BASELINE"], "READY_CLASS_VALIDATED": m["READY_CLASS_VALIDATED"],
           "METHODOLOGY_CHANGED": "YES" if meth_changed else "NO", "LOOKAHEAD": "PASS" if la_ok else "FAIL",
           "PROVENANCE": "PASS" if prov_ok else "FAIL", "CURRENT_STATUS": band(len(primary)), "FINAL_VALIDATION_STATE": state}
    sec = [{"CASE_ID": r["CASE_ID"], "SYMBOL": r["SYMBOL"], "MATCH_CLASS": r.get("MATCH_CLASS"),
            "PROVENANCE_CONFIDENCE": r["PROVENANCE_CONFIDENCE"], "missing_critical": r["PROVENANCE"]["missing_critical"]}
           for r in rows if r["SAMPLE"] == "SECONDARY"]
    return {"generated_by": "faisal_method_v41/final_protocol.py", "tool_version": FP_VERSION, "contract": CONTRACT,
            "epoch": {k: ep[k] for k in ("epoch", "V4_COMMIT", "V4_FREEZE_ID", "V4_CONFIG_HASH", "V4_RULE_REGISTRY_HASH",
                                         "V4_TOOL_VERSION", "DATA_PIPELINE_VERSION", "DATA_PIPELINE_PINS")}
            | {"components": len(ep["DATA_PIPELINE_COMPONENTS"]), "attestation_ok": ep["V4_COMMIT_ATTESTATION"]["ok"]},
            "integrity": integ, "output": out, "output_order": list(OUTPUT_KEYS),
            "supplementary": {"SECONDARY_TRACKED": sec, "secondary_metrics": {k: m2[k] for k in ("MATCHES", "MISMATCHES", "n_valid")},
                              "PENDING_PRIMARY": pending, "EXCLUDED_BREAKDOWN": excluded,
                              "INTAKE_BY_CLASS": {k: by7.get(k, 0) for k in CLASSES7}, "COLLECTOR": col,
                              "BASELINE_B": "NONE (لا خطَّ أساسٍ فنّيًّا مسجَّلًا مسبقًا — §⑭)",
                              "STRUCTURAL": "V4 الأماميّ ∈ {WAIT · UNKNOWN} (FVO1) ⟵ لا READY ولا REJECT · وكلُّ تطابقٍ لـV4 تطابقٌ لـALWAYS_WAIT"},
            "metrics": m, "diversity": diversity(primary), "candidates": cands, "cases": rows,
            "v4_2_candidates": v4_2_candidates(rows),
            "false_ready": [r["CASE_ID"] for r in rows if r.get("MATCH_CLASS") == "FALSE_READY"]}


# ── ⑮ العرض ───────────────────────────────────────────────────────────────────
def output_block(st):
    o = st["output"]
    lines = [f"{k} = {o[k]}" for k in OUTPUT_KEYS]
    s = st["supplementary"]
    ex = s["EXCLUDED_BREAKDOWN"]
    lines += ["— — —",
              "SECONDARY_TRACKED = " + (" · ".join(f"{x['CASE_ID']} {x['SYMBOL']} {x['MATCH_CLASS'] or 'PENDING'} "
                                                   f"(provenance {x['PROVENANCE_CONFIDENCE']})" for x in s["SECONDARY_TRACKED"]) or "0"),
              "PENDING_PRIMARY = " + (" · ".join(s["PENDING_PRIMARY"]) or "0"),
              "EXCLUDED_BREAKDOWN = " + " · ".join(f"{k} {v}" for k, v in ex.items()),
              "INTAKE_BY_CLASS = " + " · ".join(f"{k} {v}" for k, v in s["INTAKE_BY_CLASS"].items()),
              f"COLLECTOR = {s['COLLECTOR']['simulated']} · {s['COLLECTOR']['live']}",
              "INTEGRITY = " + ("PASS" if st["integrity"]["ok"] else "FAIL ⟵ " + " · ".join(
                  k for k, v in st["integrity"]["checks"].items() if not v["ok"])),
              f"BASELINE_B = {s['BASELINE_B']}", f"STRUCTURAL = {s['STRUCTURAL']}"]
    return lines


def _pct(x):
    return "—" if x in (None, "UNDEFINED") else (f"{x * 100:.1f}%" if isinstance(x, float) else str(x))


def render_status(st):
    o, m = st["output"], st["metrics"]
    ep = st["epoch"]
    L = ["# 🧊🔒 FAISAL V4 — FINAL PROSPECTIVE VALIDATION — الحالة", "",
         f"> مولَّدٌ من `faisal_method_v41/final_protocol.py` ({st['tool_version']}) · العقد `{st['contract']}` · **لا يُحرَّر باليد**.", "",
         "## ① كتلةُ الإخراج (FINAL OUTPUT)", "", "```"] + output_block(st) + ["```", "",
         "## ② الحقبة (EPOCH 1 · V4 FROZEN)", "",
         f"- **V4_COMMIT:** `{ep['V4_COMMIT']}` · شهادةُ الملفّات عنده: {'✅' if ep['attestation_ok'] else '⛔'}",
         f"- **freeze_id:** `{ep['V4_FREEZE_ID']}`",
         f"- **V4_CONFIG_HASH:** `{ep['V4_CONFIG_HASH']}` · **V4_RULE_REGISTRY_HASH:** `{ep['V4_RULE_REGISTRY_HASH']}`",
         f"- **V4_TOOL_VERSION:** {' · '.join(f'{k} `{v}`' for k, v in ep['V4_TOOL_VERSION'].items())}",
         f"- **DATA_PIPELINE_VERSION:** `{ep['DATA_PIPELINE_VERSION']}` ({ep['components']} مكوّنًا · "
         + " · ".join(f"{k}=={v}" for k, v in ep["DATA_PIPELINE_PINS"].items()) + ")", "",
         "## ③ السلامة I1-I12 (PHASE 18)", "", "| الفحص | الحكم | التفصيل |", "|---|---|---|"]
    for k, v in st["integrity"]["checks"].items():
        L.append(f"| `{k}` | {'✅' if v['ok'] else '⛔'} | {str(v['detail'])[:160]} |")
    L += ["", "## ④ المقاييس على PRIMARY (PHASE 13-15)", "",
          f"- **N الصالحة:** {m['n_valid']} · القابلة للمقارنة {m['n_comparable']} · **الشريط:** {o['CURRENT_STATUS']}",
          f"- **READY (أوّلًا):** V4 {m['per_class']['READY']['v4']} · فيصل {m['per_class']['READY']['faisal']} · "
          f"الدقّة {_pct(m['per_class']['READY']['precision'])} · الاستدعاء {_pct(m['per_class']['READY']['recall'])} · "
          f"FALSE_READY {o['FALSE_READY']} (المعدّل {_pct(m['FALSE_READY_RATE'])} · من غير READY {_pct(m['FALSE_READY_FPR'])})",
          f"- **WAIT:** الدقّة {_pct(m['per_class']['WAIT']['precision'])} · الاستدعاء {_pct(m['per_class']['WAIT']['recall'])} · "
          f"**REJECT:** الدقّة {_pct(m['per_class']['REJECT']['precision'])} · الاستدعاء {_pct(m['per_class']['REJECT']['recall'])}",
          f"- **التطابقُ التامّ:** {_pct(m['exact_rate'])} مقابل **ALWAYS_WAIT** {_pct(m['always_wait_rate'])} · "
          f"المتنافرة b {m['baseline_discordant']['b_v4_only']} / c {m['baseline_discordant']['c_baseline_only']} ⟵ "
          f"V4_BEATS_BASELINE **{o['V4_BEATS_BASELINE']}**",
          f"- **READY_CLASS_VALIDATED:** {o['READY_CLASS_VALIDATED']} ({m['READY_CLASS_BASIS']}) · "
          f"P1 (TECH_READY مقابل READY فيصل): {m['P1_TECH_READY']}",
          f"- **التنوّع:** أطولُ سلسلةٍ بالإعداد نفسِه {st['diversity']['longest_same_setup_run']} · LOW_DIVERSITY "
          f"{'نعم' if st['diversity']['LOW_DIVERSITY'] else 'لا'}", "",
          "## ⑤ الحالات", "", "| الحالة | الرمز | التاريخ | العيّنة (المصدريّة) | V4 (فنّيّ) | فيصل (الدليل) | المطابقة | النظرُ المستقبليّ | الحالة |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in st["cases"]:
        v = r.get("V4") or {}
        f = r.get("FAISAL") or {}
        L.append(f"| `{r['CASE_ID']}` | {r['SYMBOL']} | {r['DECISION_DATE']} | {r['SAMPLE']} ({r['PROVENANCE_CONFIDENCE']}) | "
                 f"{v.get('FINAL_STATE', '—')} ({v.get('TECH_STATE', '—')}) | {f.get('effective_label', '—')} "
                 f"({f.get('evidence_class', '—')}) | {r.get('MATCH_CLASS', '—')} | {(r.get('LOOKAHEAD') or {}).get('verdict', '—')} | "
                 f"{r.get('STATUS')} |")
    L += ["", "## ⑥ الاستلامُ بالأصناف السبعة (PHASE 3)", "",
          " · ".join(f"**{k}** {v}" for k, v in st["supplementary"]["INTAKE_BY_CLASS"].items()), "",
          "## ⑦ طابورُ V4.2 من التحقّق الأماميّ (PHASE 9)", "",
          f"- **V4_2_CANDIDATE:** {len(st['v4_2_candidates'])} — تُعرض في `docs/V4_2_RESEARCH_QUEUE.md` · **لا تدخل V4**.", ""]
    return "\n".join(L) + "\n"


def render_case_ledger(st):
    L = ["# CASE_LEDGER — سجلُّ الحالات والمرشَّحين (PHASE 12)", "",
         "> مولَّدٌ من `final_protocol.py` · كلُّ مرشَّحٍ بصنفه السبعيّ وسببه وفحوصه ومصدريّته — **بلا تعديلٍ مرحليّ**.", "",
         "## الملخّص", "", "```"] + [f"N = {st['output']['VALID_PROSPECTIVE_CASES']} · MATCH = {st['output']['MATCHES']} · "
                                    f"MISMATCH = {st['output']['MISMATCHES']} · FALSE_READY = {st['output']['FALSE_READY']} · "
                                    f"FALSE_WAIT = {st['output']['FALSE_WAIT']} · FALSE_REJECT = {st['output']['FALSE_REJECT']} · "
                                    f"FALSE_UNKNOWN = {st['output']['FALSE_UNKNOWN']}"] + ["```", "",
         "## المرشَّحون", "", "| الدفعة | الصورة | الصنف | السبب | C5 | C8 | الرمز | التاريخ | الثقة |", "|---|---|---|---|---|---|---|---|---|"]
    for c in st["candidates"]:
        L.append(f"| {c['batch']} | `{c['image_id']}` | **{c['class7']}** | {c['reason']} | {len(c['checks'].get('C5') or [])} | "
                 f"{len(c['checks'].get('C8') or [])} | {c.get('symbol') or '—'} | {c.get('decision_date') or '—'} | "
                 f"{c['provenance']['fields']['PROVENANCE_CONFIDENCE']} |")
    L += ["", "## الحالات (المصدريّةُ بالحقول الثلاثة عشر)", ""]
    for r in st["cases"]:
        f = r["PROVENANCE"]["fields"]
        L += [f"### {r['CASE_ID']} · {r['SYMBOL']} · {r['DECISION_DATE']} — {r['SAMPLE']}", "",
              "| الحقل | القيمة |", "|---|---|"] + [f"| `{k}` | {json.dumps(f.get(k), ensure_ascii=False)} |" for k in PROV_FIELDS]
        L += ["", f"- الحرجُ المجهول: {' · '.join(r['PROVENANCE']['missing_critical']) or 'لا شيء'} · أساسُ الطابع: {r['PROVENANCE']['basis']}"]
        if r.get("COMPONENTS"):
            L.append("- المكوّنات: " + " · ".join(f"{k} {v['status']}" for k, v in r["COMPONENTS"].items()))
        if r.get("LOOKAHEAD"):
            L.append("- النظرُ المستقبليّ: " + " · ".join(f"{k} {v}" for k, v in r["LOOKAHEAD"].items()))
        L.append("")
    return "\n".join(L) + "\n"


def render_false_ready(st):
    L = ["# FALSE_READY_FORENSICS — تحقيقُ «جاهز» الكاذب (PHASE 10)", "",
         "> مولَّدٌ من `final_protocol.py` · الأسبابُ العشرة: " + " · ".join(f"`{c}`" for c in FR_CAUSES)
         + " — و`EXTERNAL_INFORMATION` يلزمه دليلٌ مقتبس.", ""]
    if not st["false_ready"]:
        L += [f"**FALSE_READY = 0** — {st['supplementary']['STRUCTURAL']} (الحقبة 1).", ""]
    for cid in st["false_ready"]:
        r = next(x for x in st["cases"] if x["CASE_ID"] == cid)
        L += [f"## {cid} · {r['SYMBOL']}", f"- السبب: `{r['FAISAL'].get('false_ready_cause') or 'UNKNOWN'}`",
              f"- V4: {r['V4']['DECISION_GRAPH']}", f"- فيصل: «{r['FAISAL'].get('evidence_quote')}»", ""]
    return "\n".join(L) + "\n"


def _pr_txt(d, k):
    """دقّةٌ أو استدعاءٌ بكسره (المقامُ صفرٌ ⟵ «UNDEFINED» لا 0) ‏+ فترةُ ويلسون من 10 فأكثر."""
    den = d["v4"] if k == "precision" else d["faisal"]
    w = d.get(k + "_wilson")
    return f"{d[k]} ({d['tp']}/{den})" + (f" · Wilson95 {w}" if w else "")


def prospective_block(st):
    """STEP 11: المفاتيحُ بترتيب المالك ‏+ ما يوفّق المجموع ويُكمل STEP 9-10 (التطابقُ الإجماليّ · نسبةُ UNKNOWN · التنوّع)."""
    o, m, s = st["output"], st["metrics"], st["supplementary"]
    by7, pc = s["INTAKE_BY_CLASS"], m["per_class"]
    v = {"TOTAL_RECEIVED": len(st["candidates"]), "NEW_PROSPECTIVE": by7["NEW_PROSPECTIVE"], "DUPLICATES": by7["DUPLICATE"],
         "DERIVATIVES": by7["DERIVATIVE"], "CONTAMINATED": by7["CONTAMINATED"], "INSUFFICIENT_CONTEXT": by7["INSUFFICIENT_CONTEXT"],
         "VALID_CASES": o["VALID_PROSPECTIVE_CASES"]}
    for k in ("MATCHES", "MISMATCHES", "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT", "FALSE_UNKNOWN"):
        v[k] = o[k]
    for c in ("READY", "WAIT", "REJECT"):
        v[f"{c}_PRECISION"] = _pr_txt(pc[c], "precision")
        v[f"{c}_RECALL"] = _pr_txt(pc[c], "recall")
    for k in ("V4_UNKNOWN", "FAISAL_UNKNOWN", "ALWAYS_WAIT_MATCH", "V4_BEATS_BASELINE"):
        v[k] = o[k]
    v["CURRENT_SAMPLE_STATUS"] = f"{o['CURRENT_STATUS']} (N={o['VALID_PROSPECTIVE_CASES']} · الهدفُ الأدنى {N_MIN} — ليس برهانًا بذاته)"
    dv = st["diversity"]
    dline = " · ".join(f"{k} {json.dumps(dv['dims'].get(k, {}), ensure_ascii=False, sort_keys=True)}"
                       for k in ("pattern", "timeframe", "market_regime", "decision"))
    return [f"{k} = {v[k]}" for k in PROSPECTIVE_KEYS] + [
        "— — —",
        f"PRE_EXISTING = {by7['PRE_EXISTING']} · UNKNOWN = {by7['UNKNOWN']} (TOTAL_RECEIVED = مجموعُ الأصناف السبعة)",
        f"OVERALL_AGREEMENT = {m['exact_rate']} ({m['MATCHES']}/{m['n_comparable']}) · ALWAYS_WAIT = {m['always_wait_rate']}",
        f"UNKNOWN_RATE = {_ratio(m['V4_UNKNOWN'], m['n_valid'])} (V4_UNKNOWN / VALID_CASES)",
        f"DIVERSITY = {dline} · LOW_DIVERSITY {'YES' if dv['LOW_DIVERSITY'] else 'NO'}",
        f"FINAL_VALIDATION_STATE = {o['FINAL_VALIDATION_STATE']}"]


def render_prospective(st):
    """PROSPECTIVE_STATUS.md — يُولَّد بعد كلّ دفعة (STEP 11) مع حالة البروتوكول نفسِها."""
    sec = st["supplementary"]["SECONDARY_TRACKED"]
    L = ["# PROSPECTIVE_STATUS — حالةُ التحقّق الأماميّ الحقيقيّ (STEP 11)", "",
         f"> مولَّدٌ من `faisal_method_v41/final_protocol.py` ({st['tool_version']}) بعد كلّ دفعة · **لا يُحرَّر باليد** · V4 مجمَّد "
         f"(`{st['epoch']['V4_COMMIT'][:12]}`) · والحلقة: COLLECT ⟵ BLIND V4 ⟵ SEAL ⟵ REVEAL FAISAL ⟵ COMPARE ⟵ RECORD ⟵ REPEAT.", "",
         "```"] + prospective_block(st) + ["```", "",
         "- **خارجَ العيّنة الأساسيّة (يُتتبَّع ولا يُحسب):** " + (" · ".join(
             f"{x['CASE_ID']} {x['SYMBOL']} {x['MATCH_CLASS'] or 'PENDING'} (مصدريّة {x['PROVENANCE_CONFIDENCE']})" for x in sec) or "0"),
         "- **الدقّةُ والاستدعاء بكسرهما** · «UNDEFINED» حين المقامُ صفر · وفترةُ ويلسون من 10 فأكثر · بلا p.",
         f"- **{st['supplementary']['STRUCTURAL']}** ⟵ لا يُعلَن نجاحٌ من التطابق الإجماليّ وحدَه.", ""]
    return "\n".join(L) + "\n"


def render_final(st):
    """التقريرُ النهائيّ (PHASE 20) — يُولَّد عند PRIMARY 43 فأكثر وحدَه."""
    o, m = st["output"], st["metrics"]
    L = ["# FINAL_PROSPECTIVE_VALIDATION_REPORT", "", f"> مولَّدٌ من `final_protocol.py` ({st['tool_version']}).", "", "```"] \
        + output_block(st) + ["```", "",
                              f"- الإجماليّ {o['VALID_PROSPECTIVE_CASES']} · المستبعد {o['EXCLUDED_CASES']} ({st['supplementary']['EXCLUDED_BREAKDOWN']})",
                              f"- التطابق {o['MATCHES']} · عدمُه {o['MISMATCHES']} · {m['by_class']}",
                              f"- الدقّةُ والاستدعاء: {m['per_class']}",
                              f"- V4_UNKNOWN {o['V4_UNKNOWN']} · FAISAL_UNKNOWN {o['FAISAL_UNKNOWN']}",
                              f"- ALWAYS_WAIT {m['always_wait_rate']} مقابل V4 {m['exact_rate']} ⟵ {o['V4_BEATS_BASELINE']}",
                              f"- المكوّنات: {collections.Counter((k, v['status']) for r in st['cases'] for k, v in (r.get('COMPONENTS') or {}).items())}",
                              f"- عدمُ التطابق المتكرّر وأدلّةُ المعلومة الخارجيّة وفجوةِ المنهج: {st['v4_2_candidates']}"]
    return "\n".join(L) + "\n"


def rendered(st):
    out = {STATUS_JSON: json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
           STATUS_MD: render_status(st), LEDGER_MD: render_case_ledger(st), FR_MD: render_false_ready(st),
           PROSPECTIVE_MD: render_prospective(st)}
    if st["output"]["VALID_PROSPECTIVE_CASES"] >= N_MIN:
        out[FINAL_MD] = render_final(st)
    return out


def write(st=None):
    st = st or build()
    os.makedirs(OUT_DIR, exist_ok=True)
    for p, txt in rendered(st).items():
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
    return st


def check(st=None):
    """⟵ قائمةُ الملفّات المختلفة عن الإعادة (فارغة = مطابق) — وقبل 43 لا يوجد التقريرُ النهائيّ."""
    st = st or build()
    bad = []
    for p, txt in rendered(st).items():
        if not os.path.exists(p) or open(p, encoding="utf-8").read() != txt:
            bad.append(os.path.relpath(p, ROOT))
    if st["output"]["VALID_PROSPECTIVE_CASES"] < N_MIN and os.path.exists(FINAL_MD):
        bad.append("FINAL_REPORT_BEFORE_N_MIN")
    return bad


def guard(st=None):
    """للمشغّل والختم (PHASE 18): الحالةُ كاملة ⟵ (ok · الأسباب). VALIDATION_BLOCKED أو لا حقبة ⟵ رفض."""
    if not current_epoch():
        return False, ["NO_EPOCH"]
    st = st or build()
    if st["output"]["FINAL_VALIDATION_STATE"] != "VALIDATION_BLOCKED":
        return True, []
    why = [k for k, v in st["integrity"]["checks"].items() if not v["ok"]]
    why += [f"{k}=FAIL" for k in ("LOOKAHEAD", "PROVENANCE") if st["output"][k] == "FAIL"]
    if st["supplementary"]["COLLECTOR"]["live"] == "FAIL":
        why.append("COLLECTOR=FAIL")
    return False, why


# ── ⑯ الحلقة: الاستلام · الختم · الكشف (أوامرُ الجلسة) ───────────────────────────
def load_meta_rows(path=META_FILE):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
    return rows


def _fingerprint(path):
    import corpus_build as CB
    from PIL import Image
    with Image.open(path) as im:
        im.load()
        return {"sha256": sha_file(path), "dhash256": CB.bits_hex(CB.dhash_bits(im, 16)), "phash64": CB.bits_hex(CB.phash_bits(im)),
                "width": im.size[0], "height": im.size[1]}


def intake_scan(batch_id, images=None, meta_rows=None, ledger=None, img_dir=None):
    """صورٌ لم تُستلم بعد ⟵ بصماتُها وصفُّ الجامع وC1/C2 مقابل المدوّنة والمرشَّحين السابقين وأقربُ خمسٍ للعين (C3) — لا حكمَ بلا عين."""
    lg = ledger or LG.Ledger()
    img_dir = img_dir or os.path.join(ROOT, "faisal_images")
    images = images if images is not None else [os.path.basename(p) for p in LG.pending_new_images(lg)]
    meta_rows = load_meta_rows() if meta_rows is None else meta_rows
    by_msg = collections.defaultdict(list)
    for r in meta_rows:
        if r.get("message_id") is not None:
            by_msg[r["message_id"]].append(r)
    by_name = {}
    for r in meta_rows:
        if r.get("saved_name"):
            # صفُّ الحفظ من الطابور لا يعرف التوجيه (`forward_type` UNKNOWN) ⟵ يُكمَّل من أوّل صفٍّ للرسالة نفسِها يعرفه (§⑥)
            first = next((x for x in by_msg.get(r.get("message_id"), []) if x.get("forward_type") not in (None, "UNKNOWN")), {})
            merged = dict(r)
            for k in ("forward_type", "forward", "date", "meta_v"):
                if merged.get(k) in (None, "UNKNOWN") and first.get(k) is not None:
                    merged[k] = first[k]
            by_name[r["saved_name"]] = merged
    corpus = corpus_index()
    prior = []
    for e in lg.entries("candidate"):
        rec = lg.read(e["path"])
        p = os.path.join(ROOT, rec.get("image") or "")
        if os.path.exists(p):
            try:
                prior.append(dict(_fingerprint(p), id=rec["unit_id"]))
            except Exception:                                           # noqa: BLE001
                continue
    items = []
    for fn in sorted(images):
        p = os.path.join(img_dir, fn)
        try:
            fp = _fingerprint(p)
        except Exception as e:                                          # noqa: BLE001
            fp = {"error": type(e).__name__}
        ex_c, near_c, nearest = perceptual_hits(fp, corpus) if "sha256" in fp else ([], [], [])
        ex_p, near_p, _ = perceptual_hits(fp, prior) if "sha256" in fp else ([], [], [])
        row = by_name.get(fn) or {}
        items.append({"image_id": os.path.splitext(fn)[0], "file": f"faisal_images/{fn}", "fingerprint": fp,
                      "collector_row": row, "C1": ex_c + ex_p, "C2": near_c + near_p, "nearest_corpus": nearest,
                      "eye_review_required": True})
        prior.append(dict(fp, id=os.path.splitext(fn)[0]) if "sha256" in fp else {"id": fn})
    return {"batch_id": batch_id, "tool_version": FP_VERSION, "items": items}


EXCLUSION_OF = {"DUPLICATE": "DUPLICATE_OF", "DERIVATIVE": "DUPLICATE_OF", "CONTAMINATED": "DUPLICATE_OF",
                "PRE_EXISTING": "BEFORE_WINDOW"}


def _exclusion(cls, reason):
    if cls in EXCLUSION_OF:
        tgt = str(reason).split(":", 1)[1].split(",")[0] if ":" in str(reason) else ""
        return EXCLUSION_OF[cls] + (f":{tgt}" if cls != "PRE_EXISTING" and tgt else "")
    if cls == "INSUFFICIENT_CONTEXT":
        return {"NOT_FAISAL": "NOT_FAISAL", "NO_TICKER": "NO_TICKER", "NO_DECISION": "NO_DECISION"}.get(reason, "DATE_IMPRECISE")
    return "NOT_FAISAL" if reason == "AUTHOR_NOT_ESTABLISHED" else "NO_DECISION"


def plan_intake(scan, annotations, existing_cases, ep):
    """الأصنافُ السبعة لكلّ صورة (عينٌ إلزاميّة) ⟵ مرشَّحون وحالات (PHASE 3-4). نقيّة · ترفض صورةً بلا قراءة عين (لا تخطّيَ صامت)."""
    miss = [it["image_id"] for it in scan["items"] if it["image_id"] not in annotations]
    if miss:
        raise LG.SchemaError(f"صورٌ بلا قراءة عين: {miss[:8]} — لا تُختم دفعةٌ ناقصة")
    units, _ = dev_units()
    decs = v4_dev_decisions()
    cands, cases, by_key, n = [], [], {}, existing_cases
    for it in scan["items"]:
        a = annotations[it["image_id"]]
        fp = it["fingerprint"]
        sym, dd = (a.get("symbol") or "").upper() or None, a.get("decision_date")
        c4 = same_case_hits(sym, dd, decs) + list(a.get("same_case_of") or [])
        c5 = chart_window_hits(sym, dd, units) if sym and dd else []
        c8 = v4_exposure_hits(sym, dd, decs) if sym and dd else []
        c7 = corpus_refs(it["image_id"], it["file"])
        contaminated = ("C4:" + ",".join(c4) if c4 else "C5:" + ",".join(c5) if c5 else "C7:" + ",".join(c7) if c7
                        else "C8:" + ",".join(c8) if c8 else "SEEN_EXAMPLE:" + ",".join(a["seen_example_of"]) if a.get("seen_example_of")
                        else None)
        dmax = a.get("decision_date_max")
        pre = (f"BEFORE_WINDOW:{dd}" if dd and dd < WINDOW_START else f"BEFORE_WINDOW:≤{dmax}" if (not dd and dmax and dmax < WINDOW_START)
               else None)
        c3 = [x for x in (a.get("visual_review") or []) if x != "NONE"]
        cls, why = classify7(it["C1"], it["C2"], c3, list(a.get("derivative_of") or []), contaminated, pre,
                             "sha256" in fp, True, a.get("author") not in (None, "UNKNOWN"), bool(a.get("faisal_author")),
                             sym, bool(a.get("has_decision_statement")), bool(dd))
        tg = it.get("collector_row") or {}
        prov = provenance(tg, dict(fp, collected_utc=tg.get("collected_utc")), a)
        if cls == "NEW_PROSPECTIVE" and prov["decision_date_from_post"] and prov["decision_date_from_post"] != dd:
            raise LG.SchemaError(f"{it['image_id']}: تاريخُ القرار {dd} ≠ تاريخ نيويورك لطابع المنشور {prov['decision_date_from_post']} (§⑤)")
        cand = {"batch": scan["batch_id"], "image_id": it["image_id"], "file": it["file"], "class7": cls, "reason": why,
                "checks": {"C1": it["C1"], "C2": it["C2"], "C3": c3, "C4": c4, "C5": c5, "C6": list(a.get("derivative_of") or []),
                           "C7": c7, "C8": c8, "ocr": a.get("ocr_jaccard", "NOT_RUN"), "nearest_corpus": it["nearest_corpus"]},
                "symbol": sym, "decision_date": dd, "provenance": prov, "saved": bool(tg.get("saved_name") or "sha256" in fp),
                "fingerprint": {k: fp.get(k) for k in ("sha256", "dhash256", "phash64")},
                "collector_row": {k: tg[k] for k in ("message_id", "date", "collected_utc", "run_id", "sha256", "dhash256", "phash64",
                                                     "forward_type", "meta_v") if k in tg}}
        case = None
        if cls == "NEW_PROSPECTIVE":
            key = (sym, dd)
            if key in by_key:
                cand["class7"], cand["reason"] = "DUPLICATE", "SAME_DECISION:" + by_key[key]
            else:
                n += 1
                cid = f"CASE_{n:04d}"
                by_key[key] = cid
                blind = {"symbol": sym, "decision_date": dd, "timeframe": "1D"}
                case = {"case_id": cid, "symbol": sym, "decision_date": dd, "date_precision": "day",
                        "date_source": "forward_origin" if prov["basis"] == "FORWARD_METADATA" else "image_visible",
                        "timeframe_f": a.get("timeframe"), "image": it["file"], "image_sha256": fp["sha256"], "layer": str(a.get("layer") or "1"),
                        "capture_utc": tg.get("collected_utc") or tg.get("date"), "near_duplicates": [], "unit_id": it["image_id"],
                        "notes": f"{scan['batch_id']} · رسالة {tg.get('message_id')}",
                        "protocol": {"provenance": prov, "blind_input": blind, "input_hash": sha(blind),
                                     "v4_freeze": {k: ep[k] for k in ("epoch", "V4_COMMIT", "V4_FREEZE_ID", "V4_CONFIG_HASH",
                                                                      "V4_RULE_REGISTRY_HASH", "V4_TOOL_VERSION", "DATA_PIPELINE_VERSION")},
                                     "intake": {"class": "NEW_PROSPECTIVE", "batch": scan["batch_id"], "checks": cand["checks"]}}}
                cand["case_id"] = cid
        cands.append(cand)
        if case:
            cases.append(case)
    return cands, cases


def seal_batch(batch_id, utc, ledger=None, annotations=None, scan=None):
    """الختم (PHASE 4): `intake/<ID>/SCAN.json` ‏+ `annotations.json` ⟵ `INTAKE.json` ‏+ قيودُ المرشَّحين والحالات — قبل V4."""
    lg = ledger or LG.Ledger()
    ep = current_epoch()
    ok, why = guard() if ledger is None else (True, [])
    if not ok:
        raise LG.SchemaError(f"VALIDATION_BLOCKED {why} — لا ختم")
    bdir = os.path.join(INTAKE_DIR, batch_id)
    scan = scan or _j(os.path.join(bdir, "SCAN.json"))
    annotations = annotations if annotations is not None else (_j(os.path.join(bdir, "annotations.json"), {}) or {}).get("images") or {}
    n0 = len({e["case_id"] for e in lg.entries("case")})
    cands, cases = plan_intake(scan, annotations, n0, ep)
    for c in cands:
        dec = ("CASE:" + c["case_id"]) if c.get("case_id") else _exclusion(c["class7"], c["reason"])
        lg.record_candidate(c["image_id"], c["file"], (c["provenance"]["fields"]["IMAGE_HASH"]), dec, utc,
                            note=f"{batch_id} · {c['class7']} · {c['reason']}")
    for case in cases:
        lg.seal_case(case, utc)
    os.makedirs(bdir, exist_ok=True)
    with open(os.path.join(bdir, "INTAKE.json"), "w", encoding="utf-8") as f:
        json.dump({"batch_id": batch_id, "tool_version": FP_VERSION, "candidates": cands}, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return cands, cases


def reveal(case_id, ann, utc, ledger=None):
    """الكشف (PHASE 7): كلمةُ فيصل بعد ختم V4 وحدَه — والدليلُ حرفيّ (`evidence_quote` جزءٌ من `quote`)."""
    lg = ledger or LG.Ledger()
    if ann.get("evidence_class") not in EVIDENCE_CLASSES:
        raise LG.SchemaError("evidence_class خارج DIRECT · STRONG_INFERENCE · WEAK_INFERENCE")
    if ann["evidence_class"] != "WEAK_INFERENCE" and not (ann.get("evidence_quote") and ann["evidence_quote"] in (ann.get("quote") or "")):
        raise LG.SchemaError("evidence_quote ليس جزءًا حرفيًّا من الاقتباس")
    for k, v in (ann.get("components_f") or {}).items():
        if k not in COMPONENTS or not (v == "NONE" or (isinstance(v, list) and all(_num(x) for x in v))):
            raise LG.SchemaError(f"مكوّنٌ غيرُ صالح: {k}")
    if ann.get("false_ready_cause") is not None and ann["false_ready_cause"] not in FR_CAUSES:
        raise LG.SchemaError("false_ready_cause خارج الأسباب العشرة")
    rec = dict(ann, protocol_reveal=FP_VERSION)
    return lg.record_faisal(case_id, rec, utc)


def _now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def live_notes():
    """ما يتغيّر بالجامع وحدَه (لا يُكتب في الحالة المدفوعة): صورٌ تنتظر الاستلام · صفوفُ meta_v 2 · فجواتُ الحفظ."""
    rows = load_meta_rows()
    v2 = [r for r in rows if int(r.get("meta_v") or 1) >= 2]
    gaps = [r for r in v2 if r.get("kind") == "gap"]
    return [f"LIVE_PENDING_IMAGES = {len(LG.pending_new_images())}", f"LIVE_META_V2_ROWS = {len(v2)}",
            f"LIVE_RETENTION_GAPS = {len(gaps)}" + ((" ⟵ " + " · ".join(str(g.get("gap")) for g in gaps[-3:])) if gaps else "")]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "status"
    if cmd == "epoch-init":
        if current_epoch():
            print("⛔ الحقبةُ مسجَّلةٌ سلفًا — لا تُعدَّل (إلحاقيّ · حقبةٌ جديدة بإذن المالك)")
            return 2
        ep = build_epoch(_now_utc())
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(EPOCH_FILE, "w", encoding="utf-8") as f:
            json.dump({"protocol": "FAISAL V4 — FINAL PROSPECTIVE VALIDATION PROTOCOL", "contract": CONTRACT, "epochs": [ep]},
                      f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print(f"🧊 EPOCH 1 · V4_COMMIT {ep['V4_COMMIT'][:12]} · pipeline {ep['DATA_PIPELINE_VERSION'][:16]} · "
              f"attest {ep['V4_COMMIT_ATTESTATION']['ok']} · legacy {ep['LEGACY_CASES']}")
        return 0
    if cmd == "guard":
        ok, why = guard()
        print("🧊 GUARD", "PASS" if ok else "⛔ VALIDATION_BLOCKED " + " · ".join(why))
        return 0 if ok else 9
    if cmd == "intake-scan":
        bid = argv[1]
        doc = intake_scan(bid)
        bdir = os.path.join(INTAKE_DIR, bid)
        os.makedirs(bdir, exist_ok=True)
        with open(os.path.join(bdir, "SCAN.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print(f"📥 {bid}: {len(doc['items'])} صورة للعين")
        return 0
    if cmd == "seal":
        cands, cases = seal_batch(argv[1], _now_utc())
        print(f"🔏 {argv[1]}: مرشَّحون {len(cands)} · حالات {len(cases)}")
        return 0
    if cmd == "reveal":
        cid = argv[1]
        ann = _j(os.path.join(REVEAL_DIR, f"{cid}.json"))
        e = reveal(cid, ann, _now_utc())
        print(f"👁️ {cid}: قيد {e['seq']}")
        return 0
    st = build()
    if cmd == "write":
        write(st)
    if cmd == "check":
        bad = check(st)
        print("📋 FINAL PROTOCOL", "مطابق" if not bad else "⛔ مختلف: " + " · ".join(bad))
        if bad:
            return 1
    print("FPOUT " + canon(st["output"]))
    for line in output_block(st):
        print(line)
    if cmd == "status":
        for line in live_notes():
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
