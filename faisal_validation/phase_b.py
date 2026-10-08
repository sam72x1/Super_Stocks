"""🧪 PHASE B — PROSPECTIVE VALIDATION of frozen V4 · contract `faisal_validation/PHASE_B_prereg.md` (merged before any number).

A read-only layer over the frozen FINAL PROTOCOL (`faisal_method_v41/final_protocol.py`, epoch 1):

  Phase A gate (seal CLOSED · id · cutoff · V4) ⟶ protocol state (`final_protocol.build`) ⟶ eligibility E1-E9 per item
  ⟶ append-only `PROSPECTIVE_LEDGER.jsonl` (hash chain · each event carries only what was known at its stage)
  ⟶ the protocol's own metrics / state functions on the Phase B set (+ the contract's stricter overlays)
  ⟶ the B21 artifacts and the owner's «FAISAL VALIDATION STATUS» block.

It never modifies V4, the protocol, its epoch or ledger, the collector or production; it sends nothing, schedules nothing and writes
only the six artifacts under `faisal_validation/` (mode "w", `_write`) and the ledger (mode "a", `_append_ledger`). Locks: PHB0-PHB9.

  python3 faisal_validation/phase_b.py status          ⟵ print the block (no write)
  python3 faisal_validation/phase_b.py write           ⟵ append the due ledger events + regenerate the artifacts
  python3 faisal_validation/phase_b.py check           ⟵ recomputation == committed artifacts · ledger sound · nothing due
  python3 faisal_validation/phase_b.py audit-history   ⟵ every committed ledger version is a byte prefix of the next (full clone)

Exit 9 = VALIDATION_BLOCKED by the Phase A gate: nothing past the gate is read and nothing is written.
"""
import collections
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PB_VERSION = "PHASE-B 1.0 (2026-10-08)"
CONTRACT = "faisal_validation/PHASE_B_prereg.md"
SEAL_ID = "PHA-ea12cb86a3f39a5b"
CUTOFF = "2026-10-08T01:29:04Z"                  # Phase A evidence cutoff = prospective_clock_starts_after (seal A14)
V4_COMMIT = "7c8826c25e745668d33facabb2efbc488e997fb7"
LEDGER_NAME = "PROSPECTIVE_LEDGER.jsonl"
LEDGER = os.path.join(HERE, LEDGER_NAME)
LEDGER_REL = "faisal_validation/" + LEDGER_NAME
COLLECTOR_OBS = os.path.join(HERE, "data", "collector_observation.json")
OUT = {"json": "PHASE_B_STATUS.json", "status": "FAISAL_VALIDATION_STATUS.md", "results": "FAISAL_PROSPECTIVE_RESULTS.csv",
       "errors": "FAISAL_PROSPECTIVE_ERRORS.md", "v5": "FAISAL_V5_CANDIDATES.md", "timeline": "FAISAL_VALIDATION_TIMELINE.md"}
GENESIS = "0" * 64

B15 = ("case_id", "capture_timestamp", "source", "provenance", "image_hash", "perceptual_hash", "ticker", "timeframe",
       "faisal_timestamp", "v4_commit", "v4_config_hash", "v4_decision", "v4_reason", "faisal_decision", "decision_match",
       "baseline_decisions", "classification", "external_context_status", "data_quality", "contamination_status", "notes")
CHAIN = ("seq", "event", "utc", "prev_sha256", "sha256")
PATH = ("CAPTURED", "SEALED_INPUT", "V4_SEALED", "REVEALED")
TERMINAL = ("EXCLUDED", "CLASSIFIED")
EVENTS = PATH + TERMINAL + ("CHECKPOINT",)
NEXT = {None: ("CAPTURED",), "CAPTURED": ("SEALED_INPUT", "EXCLUDED"), "SEALED_INPUT": ("V4_SEALED", "EXCLUDED"),
        "V4_SEALED": ("REVEALED", "EXCLUDED"), "REVEALED": ("CLASSIFIED", "EXCLUDED"), "EXCLUDED": (), "CLASSIFIED": ()}
# fields fixed at capture (never change afterwards) · fields first known at a later stage (never change once known)
IMMUTABLE = ("capture_timestamp", "source", "provenance", "image_hash", "perceptual_hash", "ticker", "timeframe", "faisal_timestamp",
             "v4_commit", "baseline_decisions", "contamination_status")
KNOWN_AT = {"v4_config_hash": "V4_SEALED", "v4_decision": "V4_SEALED", "v4_reason": "V4_SEALED", "faisal_decision": "REVEALED",
            "decision_match": "TERMINAL", "external_context_status": "TERMINAL", "data_quality": "TERMINAL"}
ELIG = {"E1": "captured after the Phase A seal", "E2": "not in the historical corpus", "E3": "not a duplicate",
        "E4": "not an informative derivative", "E5": "not previously exposed to V4", "E6": "Faisal decision recoverable",
        "E7": "provenance adequate", "E8": "input sufficient", "E9": "no decision leakage"}
DECIDED = ("READY", "WAIT", "REJECT")
LABELS = DECIDED + ("UNKNOWN",)
CHECKPOINTS = (10, 20, 30, 43)
N_MIN = 43                                       # = final_protocol.N_MIN (locked)
COVER = 5                                        # = final_protocol.READY_COVER, applied to REJECT as well (contract ⑨)
SETUP_MAX_SHARE = 0.5                            # ⑨ «one setup above half of PRIMARY» (engineering, pre-registered)
WILSON_MIN = 10                                  # = final_protocol.WILSON_MIN (locked)
PRIOR = (("READY", 13), ("WAIT", 93), ("REJECT", 4))   # Faisal's definite labels in the sealed A10 table (locked against the CSV)
EVIDENCE_OK = ("DIRECT", "STRONG_INFERENCE")
PROV_OK = ("HIGH", "MEDIUM")
LA_KEYS = ("LA1_FUTURE_CANDLES", "LA2_BLIND_INPUT", "LA3_ORDER", "LA4_NO_IMAGE_TO_V4", "LA6_REPLAY")
STATE_RANK = {"NOT_VALIDATED": 0, "PARTIALLY_VALIDATED": 1, "VALIDATED": 2}
# a disagreement's cause (protocol FR_CAUSES / V4.2 WHY_V4_FAILED) ⟶ the owner's error columns; anything else stays UNRESOLVED
CAUSE_COLUMN = {"IMPLEMENTATION_BUG": "IMPLEMENTATION_ERROR", "DATA_BUG": "IMPLEMENTATION_ERROR",
                "MISSING_CONTEXT": "EXTERNAL_CONTEXT", "EXTERNAL_INFORMATION": "EXTERNAL_CONTEXT",
                "TIMEFRAME": "METHODOLOGY_MISMATCH", "LOCATION": "METHODOLOGY_MISMATCH", "ENTRY_TIMING": "METHODOLOGY_MISMATCH",
                "VALIDITY": "METHODOLOGY_MISMATCH", "DISCRETION": "METHODOLOGY_MISMATCH"}
DIMENSIONS = ("PATTERN", "STRUCTURE", "ENTRY", "STOP", "TARGET", "DECISION", "FULL_FAISAL_AGREEMENT", "TRADING_EXPECTANCY")
V5_FIELDS = ("ID", "hypothesis", "evidence", "supporting cases", "contradictory cases", "source", "confidence", "expected impact",
             "overfitting risk", "reason implementation is forbidden", "future validation requirement")
OWNER_KEYS = ("V4_FROZEN", "V4_COMMIT", "EPOCH_INTEGRITY", "COLLECTOR_STATUS", "PRIMARY_CASES", "VALID_CASES", "EXCLUDED_CASES",
              "UNKNOWN_CASES", "FAISAL_READY", "FAISAL_WAIT", "FAISAL_REJECT", "V4_READY", "V4_WAIT", "V4_REJECT", "V4_UNKNOWN",
              "EXACT_AGREEMENT", "BASELINE_AGREEMENT", "V4_VS_BASELINE", "FALSE_READY", "FALSE_WAIT", "FALSE_REJECT",
              "FALSE_UNKNOWN", "EXTERNAL_CONTEXT_BLOCKED", "DATA_BLOCKED", "METHODOLOGY_MISMATCH", "IMPLEMENTATION_ERROR",
              "UNRESOLVED", "PATTERN_DIVERSITY", "TIMEFRAME_DIVERSITY", "REGIME_DIVERSITY", "LOOKAHEAD_TEST", "PROVENANCE_TEST",
              "CONTAMINATION_TEST", "FREEZE_TEST", "LEDGER_INTEGRITY", "VALIDATION_STATE", "V5_CANDIDATES", "TESTS", "CI",
              "MOST_IMPORTANT_FINDING", "BIGGEST_REMAINING_LIMITATION", "NEXT_ALLOWED_ACTION")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GateClosed(RuntimeError):
    """The Phase A gate is closed — Phase B must not read further."""


# ── hashing ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def record_sha(rec):
    return sha({k: v for k, v in rec.items() if k != "sha256"})


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── ⓪ Phase A gate ───────────────────────────────────────────────────────────────────────────────────────────────────
def phase_a_gate():
    """→ (gate, historical SHA256 set). The only door into Phase B: seal present, `phase_a.validate` clean, CLOSED, id/cutoff/V4."""
    why, hist, seal = [], set(), {}
    try:
        pa = _load("_pb_phase_a", "faisal_recovery/phase_a.py")
        fz = pa.load_frozen()
        why += [f"phase_a: {p}" for p in pa.validate(fz)]
        seal = fz["seal"]
        hist = {r["SHA256"] for r in fz["records"] if _HEX64.match(r.get("SHA256") or "")} | \
            {m["sha256"] for m in fz["manifest"] if _HEX64.match(m.get("sha256") or "")}
    except Exception as e:                                   # noqa: BLE001 — a broken seal is a closed gate, not a crash
        why.append(f"phase_a unreadable: {type(e).__name__}: {e}")
    for k, v in (("status", "CLOSED"), ("seal_id", SEAL_ID), ("evidence_cutoff_utc", CUTOFF),
                 ("prospective_clock_starts_after", CUTOFF), ("v4_commit", V4_COMMIT)):
        if seal.get(k) != v:
            why.append(f"seal {k} = {seal.get(k)!r} (expected {v!r})")
    return {"ok": not why, "why": why, "seal_id": seal.get("seal_id"), "cutoff": seal.get("evidence_cutoff_utc"),
            "historical_hashes": len(hist)}, hist


# ── ① the frozen protocol (read-only) ────────────────────────────────────────────────────────────────────────────────
def load_protocol():
    p = os.path.join(ROOT, "faisal_method_v41")
    if p not in sys.path:
        sys.path.insert(0, p)
    import final_protocol as fp                              # noqa: E402 — the frozen engine; read, never written
    return fp, fp.build()


def protocol_steps(fp):
    """{(kind, id): utc of the first protocol ledger entry} — candidate · case (seal) · v4 · faisal (reveal). Read-only."""
    out = {}
    for e in fp.LG.Ledger().entries():
        out.setdefault((e["kind"], e["case_id"]), e["utc"])
    return out


# ── ② items and eligibility E1-E9 ────────────────────────────────────────────────────────────────────────────────────
def _fields(prov):
    return (prov or {}).get("fields") or {}


def _prov(it):
    return ((it.get("case") or {}).get("PROVENANCE") or (it.get("cand") or {}).get("provenance") or {})


def _iso(x):
    """A UTC timestamp «YYYY-MM-DDTHH:MM:SSZ» or None (UNKNOWN / empty / a date only / unparsable)."""
    if not x or str(x).upper().startswith("UNKNOWN"):
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(Z|\+00:00)?$", str(x).strip())
    return f"{m.group(1)}T{m.group(2)}Z" if m and m.group(3) else None


def cutoff_ny_date():
    """The New-York calendar day of the cutoff: a decision dated by day only counts as after the cutoff only if that whole
    New-York day starts after it (conservative — a day that contains the cutoff is historical)."""
    t = dt.datetime.strptime(CUTOFF, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    return t.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def capture_ts(it):
    return _iso(_fields(_prov(it)).get("CAPTURE_TIMESTAMP"))


def image_sha(it):
    """The image SHA256 or None — «UNKNOWN» or a malformed value never counts as a hash (no false duplicate)."""
    h = _fields(_prov(it)).get("IMAGE_HASH")
    return h if isinstance(h, str) and _HEX64.match(h) else None


def faisal_when(it):
    """→ (precise UTC or None, New-York decision day or None) for Faisal's decision."""
    prec = _iso(_fields(_prov(it)).get("ORIGINAL_POST_TIMESTAMP"))
    day = (it.get("case") or {}).get("DECISION_DATE") or (it.get("cand") or {}).get("decision_date")
    day = day if isinstance(day, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) else None
    return prec, day


def items_of(st):
    """Protocol candidates ∪ cases, joined by image SHA256, ordered by capture time then id (deterministic). Pure."""
    by_img = collections.defaultdict(list)
    for c in st.get("cases") or []:
        by_img[_fields(c.get("PROVENANCE")).get("IMAGE_HASH")].append(c)
    out = []
    for cand in st.get("candidates") or []:
        lst = by_img.get(_fields(cand.get("provenance")).get("IMAGE_HASH"))
        out.append({"pb_id": f"PB:{cand.get('image_id')}", "cand": cand, "case": lst.pop(0) if lst else None})
    for lst in by_img.values():
        out += [{"pb_id": f"PB:{c.get('CASE_ID')}", "cand": None, "case": c} for c in lst]
    return sorted(out, key=lambda it: (capture_ts(it) or "9999", it["pb_id"]))


def is_historical(it):
    """Captured or dated on/before the cutoff ⟶ outside Phase B by definition (Phase A sealed that period). Pure."""
    cap = capture_ts(it)
    prec, day = faisal_when(it)
    if cap and cap <= CUTOFF:
        return "captured on/before the cutoff"
    if prec and prec <= CUTOFF:
        return "Faisal's post is timestamped on/before the cutoff"
    if not prec and day and day <= cutoff_ny_date():
        return "Faisal's decision day is on/before the cutoff's New-York day"
    return None


def _intake_failure(cand):
    """The intake verdict of a non-NEW_PROSPECTIVE candidate ⟶ its E-number (the protocol's own precedence decides the reason)."""
    cls, why = cand.get("class7") or "UNKNOWN", str(cand.get("reason") or "")
    head = why.split(":")[0]
    if cls == "INSUFFICIENT_CONTEXT":
        return {"DATE_NOT_ESTABLISHED": "E1", "NOT_FAISAL": "E6", "NO_DECISION": "E6"}.get(head, "E8"), f"intake {cls} {why}"
    if cls == "UNKNOWN":
        return ("E6" if head in ("AUTHOR_NOT_ESTABLISHED", "UNREADABLE") else "E8"), f"intake {cls} {why}"
    return "E8", f"intake {cls} {why}"


def eligibility(it, hist, used, hist_case_imgs):
    """→ {status, code, reason, stage}: status ∈ EXCLUDED · UNKNOWN · PENDING · PRIMARY (HISTORICAL is decided before).
    E1-E9 in order; a condition that cannot be evaluated yet stops the walk (PENDING), so a decided item never changes. Pure."""
    cand, case = it.get("cand") or {}, it.get("case")
    img = image_sha(it)
    chk = cand.get("checks") or {}
    cls = (case or {}).get("INTAKE_CLASS") or cand.get("class7") or "UNKNOWN"
    reason = str(cand.get("reason") or "")

    def out(status, code="", why="", stage="INTAKE"):
        return {"status": status, "code": code, "reason": (f"{code} {ELIG[code]}: {why}" if code else why), "stage": stage}
    prec, day = faisal_when(it)
    if capture_ts(it) is None:
        return out("EXCLUDED", "E1", "capture timestamp unknown")
    if prec is None and day is None:
        return out("EXCLUDED", "E1", "Faisal decision timestamp unknown")
    if (img in hist) or chk.get("C7"):
        return out("EXCLUDED", "E2", "image SHA256 sealed by Phase A" if img in hist else f"corpus reference {chk.get('C7')}")
    if chk.get("C1") or cls == "DUPLICATE" or (img and img in used):
        return out("EXCLUDED", "E3", "image already used by an earlier Phase B item" if img in used else f"intake {cls} {reason}")
    if any(chk.get(k) for k in ("C2", "C3", "C4", "C5", "C6")) or reason.startswith("SEEN_EXAMPLE") or cls == "DERIVATIVE" \
            or (cls == "CONTAMINATED" and not chk.get("C8")):
        return out("EXCLUDED", "E4", f"intake {cls} {reason}")
    if chk.get("C8") or cls == "PRE_EXISTING" or (case or {}).get("LEGACY") or img in hist_case_imgs:
        return out("EXCLUDED", "E5", f"intake {cls} {reason}" + (" · legacy case" if (case or {}).get("LEGACY") else ""))
    if cls != "NEW_PROSPECTIVE":
        code, why = _intake_failure(dict(cand, class7=cls))
        return out("EXCLUDED", code, why)
    if not case:
        return out("PENDING", why="awaiting the protocol seal")
    fa = case.get("FAISAL")
    if not fa:
        return out("PENDING", why=f"protocol {case.get('STATUS')} (Faisal not revealed)")
    lab, ev = fa.get("effective_label"), fa.get("evidence_class")
    if lab not in DECIDED:
        return out("UNKNOWN", "E6", f"Faisal's revealed label {lab}", "POST")
    if ev not in EVIDENCE_OK:
        return out("EXCLUDED", "E6", f"evidence class {ev}", "POST")
    if case.get("PROVENANCE_CONFIDENCE") not in PROV_OK:
        return out("EXCLUDED", "E7", f"provenance {case.get('PROVENANCE_CONFIDENCE')}", "POST")
    la = case.get("LOOKAHEAD") or {}
    st = str(case.get("STATUS") or "")
    if st == "INVALID_FOR_VALIDATION" or la.get("LA5_CORPORATE_ACTION") == "INVALIDATE":
        return out("EXCLUDED", "E8", st or "LA5 invalidation", "POST")
    if st.startswith("INVALIDATED") or la.get("verdict") != "PASS" or not all(la.get(k) is True for k in LA_KEYS):
        return out("EXCLUDED", "E9", f"{st} · lookahead {la.get('verdict')}", "POST")
    if st != "COMPLETE":
        return out("PENDING", why=f"protocol {st}")
    return out("PRIMARY", stage="POST")


# ── ③ external context (⑩) · baselines (⑤) ───────────────────────────────────────────────────────────────────────────
def external_context(case, fp):
    """→ (class, blocked, categories) from Faisal's own stated reasons — never from the chart's silence."""
    f = (case or {}).get("FAISAL") or {}
    if f.get("effective_label") not in DECIDED:
        return "DATA_INSUFFICIENT", False, []
    codes = f.get("external_codes") or []
    if codes:
        cats = fp.ext_categories(codes)
        ctx = (((case.get("V4") or {}).get("DATA_AVAILABLE") or {}).get("context") or {})
        short_ok = not str(ctx.get("short_available", "UNAVAILABLE")).startswith("UNAVAILABLE")
        return "EXTERNAL_REQUIRED", any(c != "short_borrow" or not short_ok for c in cats), cats
    stated = [k for k, v in (f.get("components") or {}).items() if v]
    if f.get("plan_f") or f.get("pattern_f") or stated:
        return "CHART_SUFFICIENT", False, []
    return "EXTERNAL_UNKNOWN", False, []


def historical_prior(case_id):
    """u = int(sha256(case_id)[:8], 16) / 2**32 ⟶ READY below 13/110 · REJECT from 106/110 · else WAIT (contract ⑤). Pure."""
    tot = sum(n for _, n in PRIOR)
    u = int(hashlib.sha256(str(case_id).encode("utf-8")).hexdigest()[:8], 16) / 2 ** 32
    if u < PRIOR[0][1] / tot:
        return "READY"
    if u >= (tot - PRIOR[2][1]) / tot:
        return "REJECT"
    return "WAIT"


# ── ④ the append-only ledger ─────────────────────────────────────────────────────────────────────────────────────────
def ledger_read(path=LEDGER):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def ledger_bytes(rows):
    return "".join(canon(r) + "\n" for r in rows).encode("utf-8")


def is_append_only(old, new):
    """The committed ledger must stay a byte prefix of every later version."""
    return new.startswith(old)


def ledger_verify(rows):
    """Every problem with the chain, the event paths, the blind-first masking and the immutable fields. Pure."""
    P, prev = [], GENESIS
    path, first, known, cps = {}, {}, {}, set()
    for i, r in enumerate(rows, 1):
        miss, extra = [k for k in B15 + CHAIN if k not in r], [k for k in r if k not in B15 + CHAIN]
        if miss or extra:
            P.append(f"#{i}: fields missing {miss[:3]} extra {extra[:3]}")
            prev = r.get("sha256", prev)
            continue
        if r["seq"] != i:
            P.append(f"#{i}: seq {r['seq']}")
        if r["prev_sha256"] != prev:
            P.append(f"#{i}: chain broken")
        if r["sha256"] != record_sha(r):
            P.append(f"#{i}: record hash")
        prev = r["sha256"]
        ev, cid = r["event"], r["case_id"]
        if ev == "CHECKPOINT":
            if not re.fullmatch(r"CHECKPOINT_(10|20|30|43)", str(cid)) or cid in cps:
                P.append(f"#{i}: checkpoint {cid}")
            cps.add(cid)
            continue
        seen = path.setdefault(cid, [])
        if ev not in NEXT.get(seen[-1] if seen else None, ()):
            P.append(f"#{i}: {cid} {ev} after {seen[-1] if seen else 'nothing'}")
        seen.append(ev)
        f0 = first.setdefault(cid, r)
        P += [f"#{i}: {cid} {k} changed after capture" for k in IMMUTABLE if r[k] != f0[k]]
        kn = known.setdefault(cid, {})
        for k, stage in KNOWN_AT.items():
            due = (ev in TERMINAL) if stage == "TERMINAL" else (stage in seen)
            if r[k] is not None and not due:
                P.append(f"#{i}: {cid} {k} present before {stage}")
            if k in kn and r[k] != kn[k]:
                P.append(f"#{i}: {cid} {k} changed once known")
            if r[k] is not None:
                kn.setdefault(k, r[k])
    return P


def make_record(prev_rows, event, fields, utc):
    rec = {k: fields.get(k) for k in B15}
    rec.update({"seq": len(prev_rows) + 1, "event": event, "utc": utc,
                "prev_sha256": prev_rows[-1]["sha256"] if prev_rows else GENESIS})
    rec["sha256"] = record_sha(rec)
    return rec


def due_events(it, el):
    """The ledger path an item must have now: an intake-level exclusion stops at capture; otherwise the protocol steps reached."""
    case = it.get("case") or {}
    if el["status"] == "EXCLUDED" and el["stage"] == "INTAKE":
        return ["CAPTURED", "EXCLUDED"]
    ev = ["CAPTURED"] + (["SEALED_INPUT"] if case else []) + (["V4_SEALED"] if case.get("V4") else []) + \
         (["REVEALED"] if case.get("FAISAL") else [])
    if el["status"] in ("EXCLUDED", "UNKNOWN"):
        ev.append("EXCLUDED")
    elif el["status"] == "PRIMARY":
        ev.append("CLASSIFIED")
    return ev


def event_fields(it, el, ext, ev):
    """The B15 fields of one event, masked to what was known at that stage (V4 from V4_SEALED · Faisal from REVEALED)."""
    cand, case = it.get("cand") or {}, it.get("case") or {}
    prov = _prov(it)
    f = _fields(prov)
    v4, fa = case.get("V4") or {}, case.get("FAISAL") or {}
    reached = PATH[:PATH.index(ev) + 1] if ev in PATH else PATH
    term = ev in TERMINAL
    prec, day = faisal_when(it)
    rec = {"case_id": it["pb_id"], "capture_timestamp": capture_ts(it), "source": f.get("SOURCE"),
           "provenance": {"confidence": f.get("PROVENANCE_CONFIDENCE"), "forward_type": f.get("FORWARD_TYPE"),
                          "basis": prov.get("basis"), "message_id": f.get("SOURCE_MESSAGE_ID")},
           "image_hash": f.get("IMAGE_HASH"), "perceptual_hash": f.get("PERCEPTUAL_HASH"), "ticker": f.get("TICKER"),
           "timeframe": f.get("TIMEFRAME"), "faisal_timestamp": prec or (day and f"{day} (New-York day)"), "v4_commit": V4_COMMIT,
           "baseline_decisions": {"ALWAYS_WAIT": "WAIT", "EXISTING_BASELINE": "NONE", "HISTORICAL_PRIOR": historical_prior(it["pb_id"])},
           "contamination_status": f"{cand.get('class7') or case.get('INTAKE_CLASS') or 'UNKNOWN'} {cand.get('reason') or ''}".strip(),
           "classification": el["status"] if term else "PENDING"}
    if "V4_SEALED" in reached and v4 and (el["stage"] == "POST" or el["status"] in ("PENDING", "PRIMARY")):
        rec.update(v4_config_hash=v4.get("CONFIG_HASH"), v4_decision=v4.get("FINAL_STATE"),
                   v4_reason=(v4.get("DECISION_REASON") or [None])[0] if isinstance(v4.get("DECISION_REASON"), list)
                   else v4.get("DECISION_REASON"))
    if "REVEALED" in reached and fa and (el["stage"] == "POST" or el["status"] in ("PENDING", "PRIMARY")):
        rec["faisal_decision"] = fa.get("effective_label")
    if term:
        rec.update(decision_match=case.get("MATCH_CLASS") if el["stage"] == "POST" else None,
                   external_context_status=ext, data_quality=case.get("STATUS") if el["stage"] == "POST" else "INTAKE_DECISION",
                   notes=el["reason"])
    else:
        rec["notes"] = {"CAPTURED": f"intake {rec['contamination_status']}", "SEALED_INPUT": f"protocol {case.get('CASE_ID')}",
                        "V4_SEALED": f"V4 result {str(v4.get('V4_RESULT_SHA256'))[:16]} · input {str(v4.get('INPUT_HASH'))[:16]}",
                        "REVEALED": f"evidence {fa.get('evidence_class')}"}[ev]
    return rec


def event_utc(it, el, ev, steps):
    """When the step happened, from the sealed protocol records — deterministic, never the wall clock. An intake-level decision is
    dated at intake; a post-reveal one at the last protocol step it read."""
    case = it.get("case") or {}
    cid, unit = case.get("CASE_ID"), (it.get("cand") or {}).get("image_id")
    cap = capture_ts(it)
    at = {"CAPTURED": cap, "SEALED_INPUT": steps.get(("case", cid)), "V4_SEALED": steps.get(("v4", cid)),
          "REVEALED": steps.get(("faisal", cid))}
    if ev in at:
        return at[ev] or cap
    if el["stage"] == "INTAKE":
        return max(cap, steps.get(("candidate", unit)) or cap)
    return max([u for u in at.values() if u] + [cap])


# ── ⑤ metrics and state — the frozen protocol decides; Phase B adds its overlays ───────────────────────────────────────
def frac(fp, k, n):
    """«k/n (p%) [Wilson 95%]» from n = 10 · «k/n (p%) LOW_POWER» below · «UNDEFINED (0/0)» at zero."""
    if not n:
        return f"UNDEFINED ({k}/{n})"
    w = fp.wilson(k, n) if n >= WILSON_MIN else None
    return f"{k}/{n} ({100 * k / n:.1f}%)" + (f" [{w[0]:.3f}, {w[1]:.3f}]" if w else " LOW_POWER")


def pb_metrics(rows):
    """Per-class false positives and baseline agreement on decided rows {faisal, v4, prior}. Pure."""
    n = len(rows)
    m = {"n": n, "faisal": {s: sum(r["faisal"] == s for r in rows) for s in DECIDED},
         "v4": {s: sum(r["v4"] == s for r in rows) for s in LABELS},
         "false": {s: sum(r["v4"] == s and r["faisal"] != s for r in rows) for s in DECIDED}}
    m["false"]["UNKNOWN"] = m["v4"]["UNKNOWN"]
    m["exact"] = sum(r["v4"] == r["faisal"] for r in rows)
    m["always_wait"] = sum(r["faisal"] == "WAIT" for r in rows)
    m["prior"] = sum(r["prior"] == r["faisal"] for r in rows)
    return m


def phase_b_state(gate_ok, ledger_ok, st, fp, main_recs, sens_recs, setups):
    """VALIDATION_BLOCKED ⟶ INSUFFICIENT_SAMPLE ⟶ the protocol's VALIDATED / PARTIALLY / NOT on main and on sensitivity, the lower."""
    if not gate_ok or not ledger_ok:
        return "VALIDATION_BLOCKED"
    o = st.get("output") or {}
    args = ((st.get("integrity") or {}).get("ok") is True, o.get("LOOKAHEAD") == "PASS", o.get("PROVENANCE") == "PASS",
            ((st.get("supplementary") or {}).get("COLLECTOR") or {}).get("live"))

    def on(recs):
        return fp.final_state(*args, len(recs), fp.metrics(recs), fp.unexplained_failure(recs))
    s_main = on(main_recs)
    if s_main not in STATE_RANK:
        return s_main
    n = len(main_recs)
    if fp.metrics(main_recs)["coverage"]["REJECT"] < COVER or (n and max(setups.values() or [0]) > SETUP_MAX_SHARE * n):
        return "INSUFFICIENT_SAMPLE"
    s_sens = on(sens_recs)
    return min(s_main, s_sens, key=STATE_RANK.get) if s_sens in STATE_RANK else s_sens


def collector_status(obs, live):
    """The protocol's live acceptance (only FAIL blocks) + the recorded Actions observation, with its time."""
    if not obs:
        return f"{live} · NO_OBSERVATION"
    sched = obs.get("runs_by_event", {}).get("schedule", 0)
    kind = ("NEVER_RUN" if not obs.get("runs_total") else "MANUAL_ONLY_SO_FAR" if not sched
            else "LAST_RUN_FAILED" if (obs.get("last_run") or {}).get("conclusion") != "success" else "SCHEDULED_ACTIVE")
    return (f"{live} · {kind} ({obs.get('runs_total')} runs: " + " · ".join(f"{k} {v}" for k, v in sorted(obs.get('runs_by_event', {}).items()))
            + f" · schedule `{obs.get('schedule')}` fired {sched} time(s) · last run {(obs.get('last_run') or {}).get('id')} "
            f"{(obs.get('last_run') or {}).get('conclusion')} · {obs.get('last_run_updates')} update(s) · observed {obs.get('observed_utc')})")


# ── ⑥ build ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def build(gate=None, protocol=None, ledger_rows=None, steps=None, collector=None):
    """→ (status, ledger rows after the due events, the new rows). Deterministic on its inputs (no wall clock)."""
    g, hist = gate if gate is not None else phase_a_gate()
    if not g["ok"]:
        raise GateClosed("; ".join(g["why"][:3]))
    fp, st = protocol if protocol is not None else load_protocol()
    rows = list(ledger_rows if ledger_rows is not None else ledger_read())
    steps = steps if steps is not None else protocol_steps(fp)
    obs = collector if collector is not None else _collector()
    lp = ledger_verify(rows)
    items = items_of(st)
    hist_case_imgs = {image_sha(it) for it in items if it.get("case") and is_historical(it)} - {None}
    have = collections.defaultdict(list)
    for r in rows:
        if r.get("event") != "CHECKPOINT":
            have[r.get("case_id")].append(r.get("event"))
    used, counts, new, out_rows, historical = set(), collections.Counter(), [], [], []
    for it in items:
        h = is_historical(it)
        if h:
            historical.append({"id": it["pb_id"], "why": h, "protocol_case": (it.get("case") or {}).get("CASE_ID")})
            continue
        el = eligibility(it, hist, used, hist_case_imgs)
        img = image_sha(it)
        if img:
            used.add(img)
        counts[el["status"]] += 1
        case = it.get("case")
        ext, blocked, cats = external_context(case, fp) if el["status"] == "PRIMARY" else (
            "DATA_INSUFFICIENT" if el["status"] == "UNKNOWN" or el["code"] == "E8" else "NOT_EVALUATED", False, [])
        ext_txt = ext + (" · VALIDATION_BLOCKED_EXTERNAL_CONTEXT" if blocked else "")
        due = due_events(it, el)
        got = have.get(it["pb_id"], [])
        if got != due[:len(got)]:
            lp.append(f"{it['pb_id']}: ledger events {got} are not a prefix of the due events {due} (regression)")
        else:
            for ev in due[len(got):]:
                new.append(make_record(rows + new, ev, event_fields(it, el, ext_txt, ev), event_utc(it, el, ev, steps)))
        div = (case or {}).get("DIVERSITY") or {}
        fa, v4 = (case or {}).get("FAISAL") or {}, (case or {}).get("V4") or {}
        out_rows.append({"case_id": it["pb_id"], "protocol_case": (case or {}).get("CASE_ID"), "status": el["status"],
                         "code": el["code"], "reason": el["reason"], "capture_timestamp": capture_ts(it),
                         "faisal_timestamp": faisal_when(it)[0] or faisal_when(it)[1], "ticker": _fields(_prov(it)).get("TICKER"),
                         "timeframe": div.get("timeframe") or _fields(_prov(it)).get("TIMEFRAME"),
                         "v4_decision": v4.get("FINAL_STATE"), "faisal_decision": fa.get("effective_label"),
                         "match_class": (case or {}).get("MATCH_CLASS"), "always_wait": "WAIT",
                         "historical_prior": historical_prior(it["pb_id"]), "external_context": ext_txt, "blocked": blocked,
                         "categories": cats, "setup": div.get("setup"), "pattern": div.get("pattern"),
                         "regime": div.get("market_regime"), "cause": fa.get("false_ready_cause") or (fa.get("v4_2") or {}).get("WHY_V4_FAILED"),
                         "components": {k: (v or {}).get("status") for k, v in ((case or {}).get("COMPONENTS") or {}).items()},
                         "image_hash": _fields(_prov(it)).get("IMAGE_HASH"), "_case": case})
    live = {r["case_id"] for r in out_rows}
    lp += [f"{cid}: in the ledger but no longer a Phase B item of the protocol state (regression)" for cid in sorted(set(have) - live)]
    all_rows = rows + new
    lp += ledger_verify(all_rows)
    primary = [r for r in out_rows if r["status"] == "PRIMARY"]
    main = [r for r in primary if not r["blocked"]]
    to_m = lambda rs: [{"faisal": r["faisal_decision"], "v4": r["v4_decision"], "prior": r["historical_prior"]} for r in rs]  # noqa: E731
    pm_main, pm_sens = pb_metrics(to_m(main)), pb_metrics(to_m(primary))
    fm_main = fp.metrics([r["_case"] for r in main])
    fm_sens = fp.metrics([r["_case"] for r in primary])
    setups = collections.Counter(r["setup"] or "UNKNOWN" for r in main)
    state = phase_b_state(g["ok"], not lp, st, fp, [r["_case"] for r in main], [r["_case"] for r in primary], setups)
    reached = [cp for cp in CHECKPOINTS if len(main) >= cp]
    for cp in reached:
        cid = f"CHECKPOINT_{cp}"
        if not any(r.get("case_id") == cid for r in all_rows):
            snap = {"n": len(main), "exact": pm_main["exact"], "always_wait": pm_main["always_wait"], "prior": pm_main["prior"],
                    "false": pm_main["false"], "v4_vs_baseline": fm_main["V4_BEATS_BASELINE"], "state": state}
            rec = make_record(all_rows, "CHECKPOINT", {"case_id": cid, "notes": canon(snap)},
                              max([r["utc"] for r in all_rows if r.get("event") in TERMINAL] or [CUTOFF]))
            all_rows.append(rec)
            new.append(rec)
    o = st.get("output") or {}
    integ = st.get("integrity") or {}
    for r in out_rows:
        r.pop("_case")
    status = {
        "generated_by": "faisal_validation/phase_b.py", "tool_version": PB_VERSION, "contract": CONTRACT, "seal_id": SEAL_ID,
        "cutoff": CUTOFF, "cutoff_ny_day": cutoff_ny_date(), "gate": g,
        "protocol": {"V4_FROZEN": o.get("V4_FROZEN"), "V4_COMMIT": o.get("V4_COMMIT"), "LOOKAHEAD": o.get("LOOKAHEAD"),
                     "PROVENANCE": o.get("PROVENANCE"), "integrity_ok": integ.get("ok") is True,
                     "integrity_failed": sorted(k for k, v in (integ.get("checks") or {}).items() if not v.get("ok")),
                     "config_hash": (st.get("epoch") or {}).get("V4_CONFIG_HASH"),
                     "collector_live": ((st.get("supplementary") or {}).get("COLLECTOR") or {}).get("live"),
                     "ready_structurally_impossible": bool(fp.ready_structurally_impossible()),
                     "candidates": len(st.get("candidates") or []), "cases": len(st.get("cases") or [])},
        "historical": {"count": len(historical), "items": historical},
        "counts": {k: counts.get(k, 0) for k in ("PRIMARY", "PENDING", "EXCLUDED", "UNKNOWN")},
        "excluded_by_code": dict(sorted(collections.Counter(r["code"] for r in out_rows if r["status"] == "EXCLUDED").items())),
        "primary": len(primary), "main": len(main), "blocked_external": len(primary) - len(main),
        "metrics_main": pm_main, "metrics_sensitivity": pm_sens,
        "protocol_metrics_main": {k: fm_main[k] for k in ("V4_BEATS_BASELINE", "baseline_discordant", "READY_CLASS_VALIDATED",
                                                          "coverage", "P1_TECH_READY", "per_class")},
        "protocol_metrics_sensitivity": {k: fm_sens[k] for k in ("V4_BEATS_BASELINE", "baseline_discordant", "coverage")},
        "setups": dict(sorted(setups.items())), "checkpoints_reached": reached,
        "ledger": {"records": len(all_rows), "head_sha256": all_rows[-1]["sha256"] if all_rows else GENESIS,
                   "file_sha256": hashlib.sha256(ledger_bytes(all_rows)).hexdigest(), "due_now": len(new), "problems": lp},
        "collector": obs, "collector_status": collector_status(obs, ((st.get("supplementary") or {}).get("COLLECTOR") or {}).get("live")),
        "state": state, "rows": out_rows}
    status["predictions"] = predictions(status)
    return status, all_rows, new


def _collector():
    try:
        with open(COLLECTOR_OBS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def predictions(st):
    """P1-P3 of the contract (⑰) by fixed rules — a wrong prediction is published, not removed. P1 is about the first build, so it
    is judged while no Phase B item exists and is not re-judged afterwards (its verdict stays in the git history of the JSON)."""
    rows = st["rows"]
    if rows:
        p1 = "FIRST_BUILD_ONLY (not re-judged once Phase B items exist — the first-build verdict is in the git history)"
    else:
        ok = (st["gate"]["ok"] and st["state"] == "INSUFFICIENT_SAMPLE" and st["protocol_metrics_main"]["V4_BEATS_BASELINE"] == "UNKNOWN"
              and st["historical"]["count"] == 48 and any(h["protocol_case"] == "CASE_0001" for h in st["historical"]["items"]))
        p1 = "HELD" if ok else "FAILED"
    p2 = all(r["v4_decision"] not in ("READY", "REJECT") for r in rows)
    p3 = st["protocol"]["ready_structurally_impossible"] and st["state"] != "VALIDATED"
    return {"P1": p1, "P2": ("HELD" if p2 else "FAILED") + (" (vacuous — 0 Phase B cases)" if not rows else ""),
            "P3": ("HELD (FVO1: V4's forward output ∈ {WAIT, UNKNOWN})" if p3 else "FAILED")}


# ── ⑦ the owner's block ──────────────────────────────────────────────────────────────────────────────────────────────
def _div(vals):
    c = collections.Counter(v or "UNKNOWN" for v in vals)
    return (f"{len(c)} distinct over {sum(c.values())} ({', '.join(f'{k} {v}' for k, v in sorted(c.items()))})" if c
            else "NONE (0 valid cases)")


def error_columns(st):
    """Disagreements in the main set by cause column (protocol causes; no cause recorded ⟶ UNRESOLVED)."""
    cols = collections.Counter()
    for r in st["rows"]:
        if r["status"] == "PRIMARY" and not r["blocked"] and r["v4_decision"] != r["faisal_decision"]:
            cols[CAUSE_COLUMN.get(str(r["cause"]), "UNRESOLVED")] += 1
    return cols


def block_values(st, fp):
    m, pm = st["metrics_main"], st["protocol_metrics_main"]
    n, pr = m["n"], st["protocol"]
    rows = st["rows"]
    main = [r for r in rows if r["status"] == "PRIMARY" and not r["blocked"]]
    cols = error_columns(st)
    lp = st["ledger"]["problems"]
    bad_primary = sum(1 for r in rows if r["status"] == "PRIMARY" and r["code"])
    find, limit, nxt = narrative(st)
    return {
        "V4_FROZEN": f"{pr['V4_FROZEN']} (protocol epoch 1 · I1-I12 {'PASS' if pr['integrity_ok'] else 'FAIL'})",
        "V4_COMMIT": pr["V4_COMMIT"],
        "EPOCH_INTEGRITY": "PASS" if pr["integrity_ok"] else "FAIL " + ", ".join(pr["integrity_failed"]),
        "COLLECTOR_STATUS": st["collector_status"],
        "PRIMARY_CASES": f"{st['primary']} of {N_MIN} minimum (HISTORICAL {st['historical']['count']} outside Phase B by definition)",
        "VALID_CASES": f"{n} (PRIMARY {st['primary']} minus {st['blocked_external']} external-context-blocked)",
        "EXCLUDED_CASES": f"{st['counts']['EXCLUDED']}" + (f" ({', '.join(f'{k} {v}' for k, v in st['excluded_by_code'].items())})"
                                                          if st["excluded_by_code"] else ""),
        "UNKNOWN_CASES": st["counts"]["UNKNOWN"],
        "FAISAL_READY": m["faisal"]["READY"], "FAISAL_WAIT": m["faisal"]["WAIT"], "FAISAL_REJECT": m["faisal"]["REJECT"],
        "V4_READY": m["v4"]["READY"], "V4_WAIT": m["v4"]["WAIT"], "V4_REJECT": m["v4"]["REJECT"], "V4_UNKNOWN": m["v4"]["UNKNOWN"],
        "EXACT_AGREEMENT": frac(fp, m["exact"], n),
        "BASELINE_AGREEMENT": (f"ALWAYS_WAIT {frac(fp, m['always_wait'], n)} · HISTORICAL_PRIOR {frac(fp, m['prior'], n)} · "
                               "EXISTING_BASELINE NONE (none pre-registered)"),
        "V4_VS_BASELINE": (f"{pm['V4_BEATS_BASELINE']} (vs ALWAYS_WAIT · b {pm['baseline_discordant']['b_v4_only']} · "
                           f"c {pm['baseline_discordant']['c_baseline_only']} · protocol rule)"),
        "FALSE_READY": frac(fp, m["false"]["READY"], n), "FALSE_WAIT": frac(fp, m["false"]["WAIT"], n),
        "FALSE_REJECT": frac(fp, m["false"]["REJECT"], n), "FALSE_UNKNOWN": frac(fp, m["false"]["UNKNOWN"], n),
        "EXTERNAL_CONTEXT_BLOCKED": st["blocked_external"],
        "DATA_BLOCKED": st["excluded_by_code"].get("E8", 0),
        "METHODOLOGY_MISMATCH": cols["METHODOLOGY_MISMATCH"],
        "IMPLEMENTATION_ERROR": cols["IMPLEMENTATION_ERROR"],
        "UNRESOLVED": cols["UNRESOLVED"] + cols["EXTERNAL_CONTEXT"],
        "PATTERN_DIVERSITY": _div(r["pattern"] for r in main),
        "TIMEFRAME_DIVERSITY": _div(r["timeframe"] for r in main),
        "REGIME_DIVERSITY": _div(r["regime"] for r in main),
        "LOOKAHEAD_TEST": f"{pr['LOOKAHEAD']} (protocol LA1-LA6) · E9 exclusions {st['excluded_by_code'].get('E9', 0)}",
        "PROVENANCE_TEST": f"{pr['PROVENANCE']} (protocol I8-I10) · E7 exclusions {st['excluded_by_code'].get('E7', 0)}",
        "CONTAMINATION_TEST": ("PASS" if not bad_primary else f"FAIL ({bad_primary})") + (
            f" · E2 {st['excluded_by_code'].get('E2', 0)} · E3 {st['excluded_by_code'].get('E3', 0)} · "
            f"E4 {st['excluded_by_code'].get('E4', 0)} · E5 {st['excluded_by_code'].get('E5', 0)} excluded"
            + (" · vacuous: 0 PRIMARY" if not st["primary"] else "")),
        "FREEZE_TEST": "PASS" if st["gate"]["ok"] and pr["integrity_ok"] and pr["V4_COMMIT"] == V4_COMMIT else "FAIL",
        "LEDGER_INTEGRITY": (("PASS" if not lp else f"FAIL ({len(lp)}: {lp[0][:80]})")
                             + f" · {st['ledger']['records']} record(s) · head {st['ledger']['head_sha256'][:16]}"),
        "VALIDATION_STATE": st["state"],
        "V5_CANDIDATES": 0,
        "TESTS": "test_bot.py — PHB0-PHB9 (the number is read from the CI log, never written by this tool)",
        "CI": "tests.yml on the PR and on main (read from the log)",
        "MOST_IMPORTANT_FINDING": find, "BIGGEST_REMAINING_LIMITATION": limit, "NEXT_ALLOWED_ACTION": nxt,
    }


def narrative(st):
    """Fixed-rule sentences (no free text): the finding · the limitation · the next allowed action."""
    sched = ((st.get("collector") or {}).get("runs_by_event") or {}).get("schedule", 0)
    lim = ("V4's forward output is {WAIT, UNKNOWN} by construction (FVO1: no source for groups · offering · operator), so READY and "
           "REJECT recall cannot exceed 0 and VALIDATED is unreachable in epoch 1"
           + ("; and the collector has never fired on its schedule (manual runs only)" if not sched else ""))
    intake = ("Forward Faisal's new posts (original timestamp kept) to the bot; then intake-scan ⟶ seal ⟶ run frozen V4 ⟶ reveal ⟶ "
              "phase_b.py write — no rule, threshold or baseline change")
    c = st["counts"]
    if not st["rows"]:
        return (f"0 prospective Faisal decisions exist after the cutoff {CUTOFF}: every protocol item ({st['historical']['count']}) "
                "is HISTORICAL, so Phase B has nothing to judge yet — no accuracy claim is possible", lim, intake)
    if st["primary"] == 0:
        return (f"{len(st['rows'])} Phase B item(s) after the cutoff (pending {c['PENDING']} · excluded {c['EXCLUDED']} · unknown "
                f"{c['UNKNOWN']}) and 0 PRIMARY — no accuracy claim is possible", lim, intake)
    if st["state"] == "INSUFFICIENT_SAMPLE":
        return (f"{st['main']} valid prospective case(s) of {N_MIN}; state INSUFFICIENT_SAMPLE",
                "Sample below the pre-registered floor (43 · READY 5 · REJECT 5 · no setup above half); " + lim,
                "Continue collecting under the same frozen rules; nothing changes at a checkpoint")
    return (f"{st['main']} valid prospective cases; state {st['state']}", "See FAISAL_PROSPECTIVE_ERRORS.md; " + lim,
            "Report the state; any improvement idea goes to FAISAL_V5_CANDIDATES.md only")


def output_block(st, fp):
    v = block_values(st, fp)
    return ["FAISAL VALIDATION STATUS", "========================"] + [f"{k} = {v[k]}" for k in OWNER_KEYS]


def blocked_block(gate):
    """The block when the Phase A gate is closed — nothing past the gate was read."""
    v = {k: "NOT_EVALUATED (Phase A gate closed)" for k in OWNER_KEYS}
    v.update(VALIDATION_STATE="VALIDATION_BLOCKED", FREEZE_TEST="FAIL", V4_COMMIT=V4_COMMIT,
             MOST_IMPORTANT_FINDING="Phase A gate closed: " + "; ".join(gate["why"][:2]),
             NEXT_ALLOWED_ACTION="Restore the sealed Phase A artifacts; never re-seal silently")
    return ["FAISAL VALIDATION STATUS", "========================"] + [f"{k} = {v[k]}" for k in OWNER_KEYS]


# ── ⑧ artifacts (B21) ────────────────────────────────────────────────────────────────────────────────────────────────
HEADER = ("> 🧾 Generated by `faisal_validation/phase_b.py` ({v}) — no number by hand · contract `{c}` · seal `{s}` · "
          "prospective clock starts after {u}\n")


def _hdr():
    return HEADER.format(v=PB_VERSION, c=CONTRACT, s=SEAL_ID, u=CUTOFF)


def render_json(st):
    return json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def render_status(st, fp):
    t = "# FAISAL_VALIDATION_STATUS — PHASE B\n\n" + _hdr()
    t += "\n```\n" + "\n".join(output_block(st, fp)) + "\n```\n"
    t += ("\n## Items\n\n| status | count |\n|---|---|\n" + f"| HISTORICAL (outside Phase B) | {st['historical']['count']} |\n"
          + "".join(f"| {k} | {v} |\n" for k, v in st["counts"].items()))
    t += ("\n**HISTORICAL** = captured or dated on/before the cutoff (a day-only date counts when its New-York day — "
          f"{st['cutoff_ny_day']} for this cutoff — is after it). Phase A sealed that period; these are not exclusions and never "
          "enter a denominator.\n")
    t += "\n## Per class (main analysis · per-class false positives)\n\n| class | Faisal | V4 | false | protocol precision | protocol recall |\n|---|---|---|---|---|---|\n"
    pc = st["protocol_metrics_main"]["per_class"]
    for s in DECIDED:
        t += (f"| {s} | {st['metrics_main']['faisal'][s]} | {st['metrics_main']['v4'][s]} | {st['metrics_main']['false'][s]} | "
              f"{pc[s]['precision']} | {pc[s]['recall']} |\n")
    sm, sp = st["metrics_sensitivity"], st["protocol_metrics_sensitivity"]
    t += (f"\n**Sensitivity (external-context-blocked cases included):** n {sm['n']} · exact {frac(fp, sm['exact'], sm['n'])} · "
          f"ALWAYS_WAIT {frac(fp, sm['always_wait'], sm['n'])} · V4_VS_BASELINE {sp['V4_BEATS_BASELINE']}. "
          "VALIDATED / PARTIALLY_VALIDATED need their criteria in both analyses (the lower state is reported).\n")
    t += "\n## Dimensions (B7 — never collapsed)\n\n" + "".join(f"- `{d}` = {dimension(st, d, fp)}\n" for d in DIMENSIONS)
    t += (f"\n## Checkpoints (B14)\n\nN = {', '.join(map(str, CHECKPOINTS))} — an immutable ledger event when reached; reached: "
          f"{st['checkpoints_reached'] or 'none'}. Nothing changes at a checkpoint.\n")
    t += "\n## Predictions (contract ⑰ — kept if wrong)\n\n" + "".join(f"- **{k}** {v}\n" for k, v in st["predictions"].items())
    t += ("\n## Error columns\n\n`METHODOLOGY_MISMATCH` = a disagreement whose recorded cause is TIMEFRAME · LOCATION · ENTRY_TIMING · "
          "VALIDITY · DISCRETION · `IMPLEMENTATION_ERROR` = IMPLEMENTATION_BUG · DATA_BUG · `UNRESOLVED` = no recorded cause, or an "
          "external-information cause on a case that was not blocked · `DATA_BLOCKED` = items excluded by E8 · "
          "`EXTERNAL_CONTEXT_BLOCKED` = PRIMARY cases out of the main denominator (⑩).\n")
    t += ("\n## Fixed, not recalculated\n\nThe development percentages are not recalculated in this mission: ENGINEERING 92.9% · "
          "METHODOLOGY 90.0% · VALIDATION 0.0% · PRODUCTION 0.0% (`FAISAL_PROJECT_DEVELOPMENT_AUDIT.md`).\n")
    return t


def dimension(st, d, fp):
    main = [r for r in st["rows"] if r["status"] == "PRIMARY" and not r["blocked"]]
    if d == "TRADING_EXPECTANCY":
        return "NOT_MEASURED (no outcome window was pre-registered in epoch 1; none is added later)"
    if not main:
        return "UNDEFINED (0/0)"
    if d == "DECISION":
        return frac(fp, sum(r["v4_decision"] == r["faisal_decision"] for r in main), len(main))
    if d in ("ENTRY", "STOP", "TARGET"):
        st_ = [r["components"].get(d) for r in main if r["components"].get(d) not in (None, "FAISAL_NOT_STATED", "FAISAL_NONE")]
        return frac(fp, sum(s == "MATCH" for s in st_), len(st_)) + " (protocol ±2% rule · NOT_STATED cases excluded)"
    if d == "FULL_FAISAL_AGREEMENT":
        ok = [r for r in main if r["v4_decision"] == r["faisal_decision"]
              and all(s in ("MATCH", "FAISAL_NOT_STATED", "FAISAL_NONE") for s in r["components"].values())]
        return frac(fp, len(ok), len(main))
    return "NOT_STATED unless Faisal states it (per case in FAISAL_PROSPECTIVE_RESULTS.csv)"


RESULT_COLS = ("case_id", "protocol_case", "status", "code", "reason", "capture_timestamp", "faisal_timestamp", "ticker", "timeframe",
               "v4_decision", "faisal_decision", "match_class", "always_wait", "historical_prior", "external_context", "setup",
               "pattern", "regime", "cause", "image_hash")


def render_results(st):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(RESULT_COLS), lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in st["rows"]:
        w.writerow(r)
    return buf.getvalue()


def render_errors(st):
    t = "# FAISAL_PROSPECTIVE_ERRORS — PHASE B (B6 · FALSE READY first)\n\n" + _hdr()
    main = [r for r in st["rows"] if r["status"] == "PRIMARY"]
    fr = [r for r in main if r["v4_decision"] == "READY" and r["faisal_decision"] != "READY"]
    other = [r for r in main if r["v4_decision"] != r["faisal_decision"] and r not in fr]
    t += (f"\n**FALSE READY {len(fr)}** · other disagreements {len(other)} · causes: protocol FR_CAUSES (IMPLEMENTATION_BUG · "
          "DATA_BUG · MISSING_CONTEXT · EXTERNAL_INFORMATION · TIMEFRAME · LOCATION · ENTRY_TIMING · VALIDITY · DISCRETION · UNKNOWN).\n")
    if not main:
        t += "\nNo PRIMARY case yet — no error to investigate. V4 is never patched from this file (B6 · B12).\n"
    for r in fr + other:
        t += (f"\n- `{r['case_id']}` ({r['protocol_case']}) V4 {r['v4_decision']} · Faisal {r['faisal_decision']} · "
              f"{r['match_class']} · cause `{r['cause'] or 'UNKNOWN (to be investigated with quoted evidence)'}`\n")
    return t


def render_v5(st):
    return ("# FAISAL_V5_CANDIDATES — PHASE B (B18)\n\n" + _hdr()
            + "\n**V5_CANDIDATES = 0.** No prospective evidence exists yet; nothing is implemented during Phase B (B12). "
              "A future entry needs every column below and is never implemented in epoch 1.\n\n| " + " | ".join(V5_FIELDS) + " |\n|"
            + "---|" * len(V5_FIELDS) + "\n")


def render_timeline(st, ledger_rows):
    t = "# FAISAL_VALIDATION_TIMELINE — PHASE B\n\n" + _hdr()
    t += (f"\n- **{CUTOFF}** — Phase A evidence cutoff · seal `{SEAL_ID}` CLOSED · the prospective clock starts after this instant.\n"
          f"- **Contract** — `{CONTRACT}` merged before any Phase B number (pinned by PHB0).\n"
          f"- **Collector** — {st['collector_status']}\n"
          f"- **Ledger** — {len(ledger_rows)} event(s), append-only and hash-chained (`{LEDGER_REL}`).\n")
    for r in ledger_rows:
        t += f"- `{r['utc']}` · #{r['seq']} {r['event']} · `{r['case_id']}`\n"
    return t


def rendered(st, ledger_rows, fp):
    return {OUT["json"]: render_json(st), OUT["status"]: render_status(st, fp), OUT["results"]: render_results(st),
            OUT["errors"]: render_errors(st), OUT["v5"]: render_v5(st), OUT["timeline"]: render_timeline(st, ledger_rows)}


def _write(name, text):
    if name not in OUT.values():
        raise ValueError(f"not a Phase B artifact: {name}")
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _append_ledger(new_rows):
    with open(LEDGER, "a", encoding="utf-8", newline="") as f:
        for r in new_rows:
            f.write(canon(r) + "\n")


def check(st, ledger_rows, new_rows, fp):
    bad = list(st["ledger"]["problems"])
    on_disk = b""
    if os.path.exists(LEDGER):
        with open(LEDGER, "rb") as f:
            on_disk = f.read()
    if on_disk != ledger_bytes(ledger_rows[:len(ledger_rows) - len(new_rows)]):
        bad.append("ledger file is not the canonical serialisation of its records")
    if new_rows:
        bad.append(f"{len(new_rows)} ledger event(s) due but not recorded (run write)")
    for name, text in rendered(st, ledger_rows, fp).items():
        try:
            with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
                if f.read() != text:
                    bad.append(f"artifact differs: {name}")
        except OSError:
            bad.append(f"artifact missing: {name}")
    return bad


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False).stdout


def audit_history():
    """Every committed version of the ledger is a byte prefix of the next, and the working file extends the last (full clone)."""
    if _git("rev-parse", "--is-shallow-repository").strip() == b"true":
        return 2, ["shallow clone — the history cannot be audited here (run in a full clone before every Phase B PR)"]
    shas = _git("log", "--format=%H", "--reverse", "--", LEDGER_REL).decode().split()
    vers = [_git("show", f"{s}:{LEDGER_REL}") for s in shas]
    if os.path.exists(LEDGER):
        with open(LEDGER, "rb") as f:
            vers.append(f.read())
    bad = [f"version {i + 1} is not a prefix of version {i + 2}" for i in range(len(vers) - 1) if not is_append_only(vers[i], vers[i + 1])]
    return (1 if bad else 0), bad or [f"{len(shas)} committed version(s) · append-only ✓"]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "status"
    if cmd == "audit-history":
        rc, msg = audit_history()
        print("📜 PHASE B ledger history:", " · ".join(msg))
        return rc
    g, hist = phase_a_gate()
    if not g["ok"]:
        print("⛔ VALIDATION_BLOCKED — Phase A gate: " + " · ".join(g["why"][:3]))
        print("\n".join(blocked_block(g)))
        return 9
    fp, pst = load_protocol()
    st, rows, new = build(gate=(g, hist), protocol=(fp, pst))
    if cmd == "write":
        _append_ledger(new)
        for name, text in rendered(st, rows, fp).items():
            _write(name, text)
        print(f"✍️ PHASE B: {len(new)} ledger event(s) appended · {len(OUT)} artifacts written")
    elif cmd == "check":
        bad = check(st, rows, new, fp)
        print("📋 PHASE B", "مطابق" if not bad else "⛔ " + " · ".join(bad[:5]))
        if bad:
            return 1
    print("\n".join(output_block(st, fp)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
