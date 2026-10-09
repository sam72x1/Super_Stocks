# -*- coding: utf-8 -*-
"""HISTORICAL GROUND-TRUTH RECOVERY — an evidence audit of the 23 ranking episodes (22 evaluable + MI). EXPLORATORY.

What it does (research only, no production import, no fetch):
  1. validates the hand-curated evidence records (data/gt/episode_evidence.json) against the eye reads of the original images
     (data/gt/gt_eye_reads.json + data/stage/eye_reads.json): every excerpt is a substring of the eye-read text, every printed
     timestamp re-derives the recorded as-of, every ranking unit is accounted for, statuses use one fixed vocabulary;
  2. chooses, per episode, the earliest DEFENSIBLE selection statement (Faisal's own words, a selection category, not retrospective,
     author + ticker + timestamp all VERIFIED or STRONGLY_SUPPORTED);
  3. places it against the EXISTING move definition (Phase 3 prereg: MOVE_50_20 = max High of the 20 sessions from the as-of ≥
     close(as-of − 1) × 1.5; sensitivities MOVE_100_20 and MOVE_25_10) on the frozen ranking bars (faisal_engine/data/rank/bars.json.gz,
     sessions ≤ 2026-10-08; MI only from faisal_engine/data/universe_bars.json.gz);
  4. groups dependent observations into decision units and applies the decision gate fixed before any outcome was computed.

Relation rules (fixed before computing outcomes):
  AFTER_MOVE_BEGAN   the defensible statement itself (or the post it answers) says the stock had already moved
  PRE_MOVE           MOVE_50_20 reached, first on the 2nd session from the as-of or later
  NEAR_MOVE_START    MOVE_50_20 reached on the as-of session itself (daily bars cannot order the statement and the move)
  NO_QUALIFYING_MOVE no MOVE_50_20 within 20 observed sessions
  CENSORED           fewer than 20 sessions observed and no move yet
  AMBIGUOUS          the as-of window gives different relations at its two ends
  PRIOR_MOVE_20 (flag only): the same definition was already met from an earlier anchor inside the 20 sessions before the as-of.

Decision gate (fixed before computing outcomes): R = decision units with an OWN (not follower-prompted) PRE_MOVE defensible
selection. A if R ≥ 15 (the floor of the existing contracts: RANKING_PROTOCOL verdict 3, H6_PREREG); else B if R plus the units
whose only blocker is a named, recoverable original item that would make them PRE_MOVE reaches 15; else C.

  python3 faisal_engine/gt_audit.py            # writes out/gt_*.csv · out/gt_summary.json · GROUND_TRUTH_RESULT.md
  python3 faisal_engine/gt_audit.py --check    # regenerates into a temp dir and compares byte for byte (exit 0)
"""
import csv
import gzip
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import stage_ledger as SL  # noqa: E402  (calendar + printed-time → as-of, the rule already used by the stage audit)

EVID = os.path.join(HERE, "data", "gt", "episode_evidence.json")
GT_EYE = os.path.join(HERE, "data", "gt", "gt_eye_reads.json")
STAGE_EYE = os.path.join(HERE, "data", "stage", "eye_reads.json")
RANK_CASES = os.path.join(HERE, "out", "rank_cases.csv")
RANK_UNITS = os.path.join(HERE, "out", "rank_units.csv")
RANK_BARS = os.path.join(HERE, "data", "rank", "bars.json.gz")
UNIV_BARS = os.path.join(HERE, "data", "universe_bars.json.gz")
BARS_TO = "2026-10-08"
METHOD_DOCS = ("FAISAL_SOURCE_LEDGER.md", "faisal_engine/FAISAL_RULE_LEDGER.csv", "FAISAL_IMAGES_CATALOG.md",
               "FAISAL_METHODOLOGY_NOTES.md", "faisal_engine/FAISAL_METHOD_SPEC.md")
OUT = os.environ.get("FE_GT_OUT") or os.path.join(HERE, "out")
DOC = "GROUND_TRUTH_RESULT.md"
FILES = ("gt_units.csv", "gt_episodes.csv", "gt_summary.json", DOC)

STATUSES = ("VERIFIED", "STRONGLY_SUPPORTED", "INFERRED", "AMBIGUOUS", "UNKNOWN")
OK = ("VERIFIED", "STRONGLY_SUPPORTED")
D_ALL = ("ATTENTION", "LIST_MEMBERSHIP", "TECH_READINESS", "WAITING_CONDITION", "PRESSURE_OBSERVED", "ENTRY", "RETROSPECTIVE",
         "CHART_ANALYSIS_ONLY", "UNKNOWN_STATE")
SELECTION = ("ATTENTION", "LIST_MEMBERSHIP", "TECH_READINESS", "WAITING_CONDITION", "ENTRY")
ARTIFACTS = ("ORIGINAL_POST", "POST_HEADER_CROPPED", "POST_CONTINUATION", "REPLY", "QUOTE_POST", "POST_EMBEDDED_CHAT",
             "CHAT_SCREENSHOT", "CHART_ATTACHMENT", "APP_LIST_SNAPSHOT")
MOVE = (50, 20)
SENS = ((100, 20), (25, 10))
PRIOR_K = 20
FLOOR = 15
RANK_WORD = {"READY": ("TECH_READINESS",), "WATCH": ("ATTENTION", "WAITING_CONDITION"), "ENTRY": ("ENTRY",),
             "FOCUS": ("ATTENTION",)}
# names and handles visible in the images — the public repository must not carry them (checked)
PRIVATE = ("KHALID", "Majid", "majidx", "marwan", "Meshal", "iMeesh", "abdullah120", "vision2030z", "Moata", "qqqwww", "al_anq",
           "ياسر", "ابو سلطان", "ابو ضاري", "د باسم", "ابو عبدالملك", "عبدالله الراشد")


class AuditError(AssertionError):
    pass


def _need(cond, msg):
    if not cond:
        raise AuditError(msg)


# ------------------------------------------------------------------ inputs
def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_eye():
    stm, reads = {}, {}
    for p in (STAGE_EYE, GT_EYE):
        for r in load_json(p)["reads"]:
            _need(r["id"] not in reads, f"eye read {r['id']} defined twice")
            reads[r["id"]] = r
            for s in r["statements"]:
                stm[f"{r['id']}:{s['key']}"] = s
    return stm, reads


def load_rank():
    with open(RANK_CASES, encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    with open(RANK_UNITS, encoding="utf-8") as f:
        units = list(csv.DictReader(f))
    return cases, units


_BARS = {}


def bars(sym):
    """[[date,o,h,l,c,v], …] ≤ BARS_TO from the frozen ranking bars; the universe-test bars only when the symbol is absent."""
    if "rank" not in _BARS:
        _BARS["rank"] = json.load(gzip.open(RANK_BARS, "rt", encoding="utf-8"))["daily"]
        _BARS["univ"] = json.load(gzip.open(UNIV_BARS, "rt", encoding="utf-8"))["daily"]
    for src in ("rank", "univ"):
        rows = _BARS[src].get(sym)
        if rows:
            return src, [r for r in rows if r[0] <= BARS_TO]
    return None, []


def sha(path):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# ------------------------------------------------------------------ validation
def expected_asof(s_eye):
    p = s_eye.get("printed")
    if not p:
        return None
    if p.get("hh") is not None:
        a, _ = SL.asof_from_printed(p["y"], p["m"], p["d"], p["hh"], p["mm"], p["ampm"])
        return [a, a]
    d = f"{int(p['y']):04d}-{int(p['m']):02d}-{int(p['d']):02d}"
    return list(SL.window_for_range(d, d))


def validate(evid, stm, reads, units):
    cal = set(SL.calendar())
    seen_units = {}
    for ep in evid["episodes"]:
        _need(ep["statements"], f"{ep['episode_id']}: no statements")
        for s in ep["statements"]:
            ref = s["ref"]
            _need(ref in stm, f"{ref}: no eye read")
            _need(s["excerpt"] in stm[ref]["text"], f"{ref}: excerpt is not verbatim")
            _need(os.path.exists(os.path.join(ROOT, reads[ref.split(':')[0]]["file"])), f"{ref}: image file missing")
            for k in ("author", "identity", "ts"):
                _need(s[k] in STATUSES, f"{ref}: {k} status {s[k]!r} not in the vocabulary")
            _need(s["artifact"] in ARTIFACTS, f"{ref}: artifact {s['artifact']!r}")
            _need(s["D"] and all(d in D_ALL for d in s["D"]), f"{ref}: D {s['D']}")
            _need(s["role"] in ("UNIT", "SUPP"), f"{ref}: role")
            if s["ts"] in OK:
                _need(s["asof"] and len(s["asof"]) == 2 and s["asof"][0] <= s["asof"][1], f"{ref}: OK timestamp without an as-of window")
                _need(all(a in cal for a in s["asof"]), f"{ref}: as-of {s['asof']} is not a session")
            else:
                _need(s["asof"] is None, f"{ref}: {s['ts']} timestamp must not carry an as-of window")
            if s["ts"] == "VERIFIED":
                ex = expected_asof(stm[ref])
                _need(ex is not None, f"{ref}: VERIFIED timestamp without a printed time in the eye read")
                _need(ex == s["asof"], f"{ref}: printed time gives {ex}, recorded {s['asof']}")
            if s["retro"]:
                _need("RETROSPECTIVE" in s["D"], f"{ref}: retro flag without RETROSPECTIVE")
            if s["role"] == "UNIT":
                seen_units.setdefault(ep["ticker"], []).append(s["unit"])
            _need((s["role"] == "UNIT") == bool(s["unit"]), f"{ref}: unit field")
    want = {}
    for u in units:
        want.setdefault(u["ticker"], []).append(u["evidence_id"])
    _need({k: sorted(v) for k, v in want.items()} == {k: sorted(v) for k, v in seen_units.items()},
          "ranking units are not all accounted for (or extra ones are listed)")
    blob = json.dumps(evid, ensure_ascii=False) + open(GT_EYE, encoding="utf-8").read()
    for name in PRIVATE:
        _need(name not in blob, f"private name/handle {name!r} present")


# ------------------------------------------------------------------ outcomes
def outcomes(sym, asof):
    src, rows = bars(sym)
    if not rows:
        return {"src": src, "available": False}
    dates = [r[0] for r in rows]
    if asof not in dates or dates.index(asof) == 0:
        return {"src": src, "available": False}
    i = dates.index(asof)
    ref = rows[i - 1][4]
    after = rows[i:]
    out = {"src": src, "available": True, "ref_close": ref, "n_after": len(after)}
    for p, k in (MOVE,) + SENS:
        highs = [r[2] for r in after[:k]]
        hit = any(h >= ref * (1 + p / 100) for h in highs)
        out[f"MOVE_{p}_{k}"] = 1 if hit else (0 if len(after) >= k else None)
    first = next((j + 1 for j, r in enumerate(after[:MOVE[1]]) if r[2] >= ref * (1 + MOVE[0] / 100)), None)
    out["first_session_50"] = first
    out["max_gain_20"] = round((max(r[2] for r in after[:20]) / ref - 1) * 100, 1)
    prior = 0
    for j in range(max(1, i - PRIOR_K), i):
        if max(r[2] for r in rows[j:i]) >= rows[j - 1][4] * (1 + MOVE[0] / 100):
            prior = 1
            break
    out["PRIOR_MOVE_20"] = prior
    return out


def relation_at(sym, asof, states_move):
    o = outcomes(sym, asof)
    if states_move:
        return "AFTER_MOVE_BEGAN", o
    if not o["available"]:
        return "NO_BARS", o
    m = o[f"MOVE_{MOVE[0]}_{MOVE[1]}"]
    if m is None:
        return "CENSORED", o
    if m == 1:
        return ("NEAR_MOVE_START" if o["first_session_50"] == 1 else "PRE_MOVE"), o
    return "NO_QUALIFYING_MOVE", o


def relation(sym, window, states_move):
    lo, hi = window
    r_lo, o_lo = relation_at(sym, lo, states_move)
    r_hi, o_hi = relation_at(sym, hi, states_move)
    if r_lo == r_hi:
        return r_lo, o_lo, o_hi, ""
    return "AMBIGUOUS", o_lo, o_hi, f"{lo}:{r_lo} | {hi}:{r_hi}"


# ------------------------------------------------------------------ episodes
def _canon(img, groups):
    for g in groups:
        if img in g:
            return sorted(g)[0]
    return img


GLOBAL_SAME_POST = [["X_20260918_22_pipeline", "X_20260918_23_watchlist"], ["X_20260905_01", "X_20260905_02"],
                    ["X_20260827_amix_hcwb_ready", "X_20260827_amix_pressure_497", "X_20260827_amix_3m_inflow"]]


def method_hits():
    hits = {}
    for d in METHOD_DOCS:
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            hits[d] = open(p, encoding="utf-8").read()
    return hits


def is_candidate(s):
    return (bool(set(s["D"]) & set(SELECTION)) and not s["retro"] and s["author"] in OK and s["identity"] in OK
            and s["ts"] in OK and s["asof"] is not None)


def blockers(ep):
    """Why no defensible selection: the failing fields of the selection statements (or the absence of any)."""
    sel = [s for s in ep["statements"] if set(s["D"]) & set(SELECTION)]
    if not sel:
        return ["NO_SELECTION_STATEMENT"]
    non_retro = [s for s in sel if not s["retro"]]
    if not non_retro:
        return ["RETROSPECTIVE_ONLY"]
    out = set()
    for s in non_retro:
        for k, name in (("author", "AUTHOR"), ("identity", "IDENTITY"), ("ts", "TIMESTAMP")):
            if s[k] not in OK:
                out.add(f"{name}_{s[k]}")
    return sorted(out)


def classify(ep, rank_case, docs):
    sym = ep["ticker"]
    cands = sorted([s for s in ep["statements"] if is_candidate(s)],
                   key=lambda s: (s["asof"][0], bool(s["dup_of"]), s["role"] != "UNIT", s["ref"]))
    groups = GLOBAL_SAME_POST + ep.get("same_post", [])
    imgs = sorted({s["ref"].split(":")[0] for s in ep["statements"]})
    used = sorted({i for i in imgs if any(i in t for t in docs.values())})
    row = {"episode_id": ep["episode_id"], "ticker": sym, "rank_T_e": rank_case["T_e"], "rank_evaluable": rank_case["evaluable"],
           "rank_states": rank_case["states"], "n_units": sum(1 for s in ep["statements"] if s["role"] == "UNIT"),
           "n_observations": len({_canon(s["ref"].split(":")[0], groups) for s in ep["statements"] if s["role"] == "UNIT"}),
           "images_in_method_docs": " ".join(used)}
    if cands:
        d = cands[0]
        rel, o_lo, o_hi, why = relation(sym, d["asof"], d["states_move"])
        row.update({"defensible_ref": d["ref"], "defensible_role": d["role"], "author": d["author"], "identity": d["identity"],
                    "timestamp": d["ts"], "asof_lo": d["asof"][0], "asof_hi": d["asof"][1],
                    "D": "+".join(sorted(set(x for s in ep["statements"] for x in s["D"]))),
                    "defensible_D": "+".join(d["D"]), "excerpt": d["excerpt"], "origin": "PROMPTED" if d["prompted"] else "OWN",
                    "states_move": d["states_move"] or "", "relation": rel, "relation_note": why,
                    "MOVE_50_20": o_lo.get("MOVE_50_20"), "first_session_50": o_lo.get("first_session_50"),
                    "MOVE_100_20": o_lo.get("MOVE_100_20"), "MOVE_25_10": o_lo.get("MOVE_25_10"),
                    "max_gain_20": o_lo.get("max_gain_20"), "n_after": o_lo.get("n_after"),
                    "PRIOR_MOVE_20": o_lo.get("PRIOR_MOVE_20"), "bars_src": o_lo.get("src") or "",
                    "fully_supported": 1, "blockers": "",
                    "cluster": _canon(d["ref"].split(":")[0], groups),
                    "defensible_in_method_docs": int(d["ref"].split(":")[0] in used)})
        row["T_e_check"] = "MATCH" if d["asof"][0] <= rank_case["T_e"] <= d["asof"][1] else f"CORRECTED {rank_case['T_e']} → {d['asof'][0]}" + (
            f"…{d['asof'][1]}" if d["asof"][1] != d["asof"][0] else "")
        row["eligibility"] = "ELIGIBLE" if rel not in ("AMBIGUOUS", "NO_BARS") else "EXCLUDED"
        row["exclusion_reason"] = "" if row["eligibility"] == "ELIGIBLE" else f"RELATION_{rel}"
    else:
        b = blockers(ep)
        row.update({"defensible_ref": "", "defensible_role": "", "author": "", "identity": "", "timestamp": "", "asof_lo": "", "asof_hi": "",
                    "D": "+".join(sorted(set(x for s in ep["statements"] for x in s["D"]))), "defensible_D": "", "excerpt": "",
                    "origin": "", "states_move": "", "relation": "UNDETERMINED", "relation_note": "", "MOVE_50_20": None,
                    "first_session_50": None, "MOVE_100_20": None, "MOVE_25_10": None, "max_gain_20": None, "n_after": None,
                    "PRIOR_MOVE_20": None, "bars_src": "", "fully_supported": 0, "blockers": " ".join(b),
                    "cluster": ep["episode_id"], "defensible_in_method_docs": 0, "T_e_check": "NO_DEFENSIBLE_DATE",
                    "eligibility": "EXCLUDED", "exclusion_reason": " ".join(b)})
    row["reliable_pre_move"] = int(row["eligibility"] == "ELIGIBLE" and row["relation"] == "PRE_MOVE" and row["origin"] == "OWN")
    row["missing_items"] = len(ep.get("missing", []))
    row["corrections"] = len(ep.get("corrections", []))
    return row


def resolvable(ep, row):
    """A named, recoverable original item would make this episode an OWN PRE_MOVE selection?"""
    if row["reliable_pre_move"] or not ep.get("missing"):
        return 0
    if row["relation"] == "AMBIGUOUS" and "PRE_MOVE" in row["relation_note"] and row["origin"] == "OWN":
        return 1
    return 0


READS = {}


def unit_rows(evid, units):
    ix = {(u["ticker"], u["evidence_id"]): u for u in units}
    rows = []
    for ep in evid["episodes"]:
        for s in ep["statements"]:
            if s["role"] != "UNIT":
                continue
            u = ix[(ep["ticker"], s["unit"])]
            words = RANK_WORD.get(u["state"], ())
            win = s["asof"]
            rows.append({"episode_id": ep["episode_id"], "ticker": ep["ticker"], "unit": s["unit"], "rank_date": u["date"],
                         "rank_session": u["session"], "rank_state": u["state"], "statement": s["ref"], "artifact": s["artifact"],
                         "author": s["author"], "identity": s["identity"], "timestamp": s["ts"],
                         "asof": f"{win[0]}…{win[1]}" if win and win[0] != win[1] else (win[0] if win else ""),
                         "rank_session_in_asof": ("YES" if win and win[0] <= u["session"] <= win[1] else ("UNKNOWN" if not win else "NO")),
                         "D": "+".join(s["D"]), "rank_label_word_in_source": int(bool(set(words) & set(s["D"]))),
                         "retrospective": int(s["retro"]), "prompted": int(s["prompted"]), "states_move": s["states_move"] or "",
                         "duplicate_of": s["dup_of"] or "", "excerpt": s["excerpt"],
                         "sha256": sha(READS[s["ref"].split(":")[0]]["file"])})
    return rows


# ------------------------------------------------------------------ build
def run():
    evid = load_json(EVID)
    stm, reads = load_eye()
    cases, units = load_rank()
    validate(evid, stm, reads, units)
    READS.clear()
    READS.update(reads)
    case_ix = {c["episode_id"]: c for c in cases}
    _need(sorted(case_ix) == sorted(e["episode_id"] for e in evid["episodes"]), "episode ids differ from rank_cases.csv")
    docs = method_hits()
    eps = []
    for ep in evid["episodes"]:
        row = classify(ep, case_ix[ep["episode_id"]], docs)
        row["resolvable"] = resolvable(ep, row)
        eps.append(row)
    urows = unit_rows(evid, units)
    summ = summarize(eps, urows, evid)
    return eps, urows, summ, evid


def _open(e, has_missing):
    """Not yet decided against an OWN pre-move selection: censored/ambiguous/no bars, an undetermined episode that has a selection
    statement, or any episode with a named missing original item. Used only for the favourable bound (every open item counted as a
    success); the decision itself is the rule in summarize."""
    if e["relation"] in ("CENSORED", "AMBIGUOUS", "NO_BARS") and e["origin"] != "PROMPTED":
        return True
    if e["relation"] == "UNDETERMINED" and not any(b in e["blockers"] for b in ("NO_SELECTION_STATEMENT", "RETROSPECTIVE_ONLY")):
        return True
    return has_missing


def summarize(eps, urows, evid):
    ev = [e for e in eps if e["rank_evaluable"] == "1"]
    elig = [e for e in eps if e["eligibility"] == "ELIGIBLE"]
    rel = [e for e in eps if e["reliable_pre_move"]]
    by_rel = {}
    for e in eps:
        by_rel[e["relation"]] = by_rel.get(e["relation"], 0) + 1
    inf_amb = [e for e in eps if not e["fully_supported"] and any(x in e["blockers"] for x in ("INFERRED", "AMBIGUOUS", "UNKNOWN"))]
    inf_amb += [e for e in eps if e["relation"] == "AMBIGUOUS"]
    R = len({e["cluster"] for e in rel})
    R_res = len({e["cluster"] for e in eps if e["resolvable"]} - {e["cluster"] for e in rel})
    outcome = "A" if R >= FLOOR else ("B" if R + R_res >= FLOOR else "C")
    miss_ix = {ep["episode_id"]: bool(ep.get("missing")) for ep in evid["episodes"]}
    bound = {e["cluster"] for e in rel} | {e["cluster"] for e in eps if _open(e, miss_ix.get(e["episode_id"], False))}
    bound22 = {e["cluster"] for e in ev if e["reliable_pre_move"] or _open(e, miss_ix.get(e["episode_id"], False))}
    corr = [{"episode_id": ep["episode_id"], **c} for ep in evid["episodes"] for c in ep.get("corrections", [])]
    miss = [{"episode_id": ep["episode_id"], **m} for ep in evid["episodes"] for m in ep.get("missing", [])]
    return {
        "label": "EXPLORATORY",
        "episodes_total": len(eps), "episodes_rank_evaluable": len(ev),
        "units_total": len(urows), "unit_observations": sum(e["n_observations"] for e in eps),
        "units_rank_session_in_asof": {k: sum(1 for u in urows if u["rank_session_in_asof"] == k) for k in ("YES", "NO", "UNKNOWN")},
        "units_rank_label_word_in_source": sum(u["rank_label_word_in_source"] for u in urows),
        "units_retrospective": sum(u["retrospective"] for u in urows),
        "units_duplicate": sum(1 for u in urows if u["duplicate_of"]),
        "fully_source_supported": sorted(e["episode_id"] for e in eps if e["fully_supported"]),
        "eligible": sorted(e["episode_id"] for e in elig),
        "reliable_pre_move": sorted(e["episode_id"] for e in rel),
        "inferred_or_ambiguous": sorted({e["episode_id"] for e in inf_amb}),
        "excluded": {e["episode_id"]: e["exclusion_reason"] for e in sorted(eps, key=lambda x: x["episode_id"]) if e["eligibility"] != "ELIGIBLE"},
        "relations": dict(sorted(by_rel.items())),
        "prompted": sorted(e["episode_id"] for e in eps if e["origin"] == "PROMPTED"),
        "independent_units_eligible": len({e["cluster"] for e in elig}),
        "independent_units_reliable_pre_move": R,
        "resolvable_units": R_res,
        "clusters_eligible": sorted({e["cluster"] for e in elig}),
        "T_e_corrected": sorted(e["episode_id"] for e in eps if e["T_e_check"].startswith("CORRECTED")),
        "defensible_in_method_docs": sorted(e["episode_id"] for e in eps if e["defensible_in_method_docs"]),
        "evaluable22": {"fully_source_supported": sum(1 for e in ev if e["fully_supported"]),
                        "eligible": sum(1 for e in ev if e["eligibility"] == "ELIGIBLE"),
                        "reliable_pre_move": sorted(e["episode_id"] for e in ev if e["reliable_pre_move"]),
                        "excluded": sum(1 for e in ev if e["eligibility"] != "ELIGIBLE"),
                        "independent_units_eligible": len({e["cluster"] for e in ev if e["eligibility"] == "ELIGIBLE"}),
                        "independent_units_reliable_pre_move": len({e["cluster"] for e in ev if e["reliable_pre_move"]})},
        "favourable_bound": len(bound), "favourable_bound_22": len(bound22),
        "floor": FLOOR, "decision": outcome,
        "corrections": corr, "missing_items": miss,
    }


COLS_E = ["episode_id", "ticker", "rank_T_e", "rank_evaluable", "rank_states", "n_units", "n_observations", "defensible_ref", "defensible_role",
          "author", "identity", "timestamp", "asof_lo", "asof_hi", "T_e_check", "defensible_D", "D", "origin", "excerpt", "states_move",
          "relation", "relation_note", "MOVE_50_20", "first_session_50", "MOVE_100_20", "MOVE_25_10", "max_gain_20", "n_after",
          "PRIOR_MOVE_20", "bars_src", "fully_supported", "blockers", "eligibility", "exclusion_reason", "reliable_pre_move", "cluster",
          "resolvable", "images_in_method_docs", "defensible_in_method_docs", "corrections", "missing_items"]
COLS_U = ["episode_id", "ticker", "unit", "rank_date", "rank_session", "rank_state", "statement", "artifact", "author", "identity",
          "timestamp", "asof", "rank_session_in_asof", "D", "rank_label_word_in_source", "retrospective", "prompted", "states_move",
          "duplicate_of", "excerpt", "sha256"]


def _fmt(v):
    return "" if v is None else str(v)


def _csv(path, rows, cols):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([_fmt(r.get(c)) for c in cols])


def render(eps, urows, s):
    L = ["# GROUND_TRUTH_RESULT — generated by `faisal_engine/gt_audit.py` (do not edit by hand) · EXPLORATORY", "",
         f"- Episodes {s['episodes_total']} (ranking-evaluable {s['episodes_rank_evaluable']}) · ranking units {s['units_total']} = "
         f"{s['unit_observations']} distinct observations ({s['units_duplicate']} duplicate units)",
         f"- Fully source-supported episodes (author + ticker + timestamp VERIFIED/STRONGLY_SUPPORTED on a non-retrospective selection): "
         f"{len(s['fully_source_supported'])}",
         f"- Eligible: {len(s['eligible'])} · reliable OWN pre-move: {len(s['reliable_pre_move'])} · inferred/ambiguous: "
         f"{len(s['inferred_or_ambiguous'])} · excluded: {len(s['excluded'])}",
         f"- Independent decision units: eligible {s['independent_units_eligible']} · reliable pre-move {s['independent_units_reliable_pre_move']}"
         f" · resolvable by a named original item {s['resolvable_units']} · floor {s['floor']}",
         "- Relations: " + " · ".join(f"{k} {v}" for k, v in s["relations"].items()),
         f"- Ranking units whose ranking session lies in the source as-of: YES {s['units_rank_session_in_asof']['YES']} · NO "
         f"{s['units_rank_session_in_asof']['NO']} · UNKNOWN {s['units_rank_session_in_asof']['UNKNOWN']} · ranking label word present in the "
         f"source: {s['units_rank_label_word_in_source']}/{s['units_total']} · retrospective units {s['units_retrospective']}",
         f"- The 22 ranking-evaluable episodes alone: fully supported {s['evaluable22']['fully_source_supported']} · eligible "
         f"{s['evaluable22']['eligible']} · reliable OWN pre-move {len(s['evaluable22']['reliable_pre_move'])} · excluded "
         f"{s['evaluable22']['excluded']} · independent units eligible {s['evaluable22']['independent_units_eligible']} / reliable pre-move "
         f"{s['evaluable22']['independent_units_reliable_pre_move']}",
         f"- Favourable bound (every censored, ambiguous, undetermined-with-selection or missing-item episode counted as an OWN pre-move "
         f"success): {s['favourable_bound']} independent units ({s['favourable_bound_22']} among the ranking-evaluable) · floor {s['floor']}",
         f"- **Decision: {s['decision']}**", "", "## Episodes", "",
         "| Episode | T_e (ranking) | Defensible statement | Author · ticker · time | As-of | Source state | Origin | Relation (MOVE_50_20) | Eligibility | Unit |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    ab = {"VERIFIED": "V", "STRONGLY_SUPPORTED": "S", "INFERRED": "I", "AMBIGUOUS": "A", "UNKNOWN": "U", "": "—"}
    for e in sorted(eps, key=lambda x: x["episode_id"]):
        asof = e["asof_lo"] + (f"…{e['asof_hi']}" if e["asof_hi"] and e["asof_hi"] != e["asof_lo"] else "")
        relx = e["relation"] + (f" (first {e['first_session_50']})" if e["first_session_50"] else "") + (
            f" — {e['relation_note']}" if e["relation_note"] else "")
        L.append(f"| {e['episode_id']} | {e['rank_T_e']} | {e['defensible_ref'] or '—'} «{e['excerpt']}» | "
                 f"{ab[e['author']]}·{ab[e['identity']]}·{ab[e['timestamp']]} | {asof or '—'} | {e['defensible_D'] or e['D']} | "
                 f"{e['origin'] or '—'} | {relx} | {e['eligibility']}{(' — ' + e['exclusion_reason']) if e['exclusion_reason'] else ''} | {e['cluster']} |")
    L += ["", "## Ranking units", "", "| Unit | Episode | Ranking session · state | Source as-of | In window | Source state | Label word in source | Retro | Duplicate of |",
          "|---|---|---|---|---|---|---|---|---|"]
    for u in urows:
        L.append(f"| {u['unit']} | {u['episode_id']} | {u['rank_session']} · {u['rank_state']} | {u['asof'] or '—'} | {u['rank_session_in_asof']} | "
                 f"{u['D']} | {u['rank_label_word_in_source']} | {u['retrospective']} | {u['duplicate_of'] or '—'} |")
    L += ["", "## Corrections to prior interpretations", ""]
    for c in s["corrections"]:
        L.append(f"- **{c['episode_id']}** · {c['what']}: {c['prior']} ⟶ {c['corrected']} ({c['evidence']})")
    L += ["", "## Missing original items", ""]
    for m in s["missing_items"]:
        L.append(f"- **{m['episode_id']}** — unknown: {m['unknown']} · why: {m['why']} · needed: {m['artifact']} ({m['provenance']}) · effect: {m['effect']}")
    return "\n".join(L) + "\n"


def write(out=OUT, doc_dir=HERE):
    eps, urows, summ, _ = run()
    os.makedirs(out, exist_ok=True)
    _csv(os.path.join(out, "gt_episodes.csv"), sorted(eps, key=lambda x: x["episode_id"]), COLS_E)
    _csv(os.path.join(out, "gt_units.csv"), urows, COLS_U)
    with open(os.path.join(out, "gt_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    with open(os.path.join(doc_dir, DOC), "w", encoding="utf-8") as f:
        f.write(render(eps, urows, summ))
    return summ


def check():
    with tempfile.TemporaryDirectory() as td:
        write(td, td)
        bad = []
        for fn in FILES:
            mine = os.path.join(td, fn)
            ref = os.path.join(HERE if fn == DOC else OUT, fn)
            if not os.path.exists(ref) or open(mine, "rb").read() != open(ref, "rb").read():
                bad.append(fn)
    if bad:
        print("❌ differs:", ", ".join(bad))
        return 1
    print("✅ regenerated identically")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    s = write()
    print(json.dumps({k: s[k] for k in ("decision", "independent_units_reliable_pre_move", "resolvable_units", "relations")}, ensure_ascii=False))
