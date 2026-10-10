#!/usr/bin/env python3
"""📏 T-BORROW-EQ — shadow (descriptive) comparison of the borrow gate's boundary.

Faisal's text «شورته تحت 20 الف» (`IMG_0151`) reads strictly: availability < 20,000 passes. The live gate
(`Super_stock.borrow_gate_recheck`) ejects only availability ABOVE the limit, so exactly 20,000 passes. The two rules differ on one
value only — a KNOWN availability equal to the limit — and this tool counts where that value occurs in persisted data.
Contract: `borrow_boundary_prereg.md` (merged before any count). Read-only · zero external requests · no production change ·
no outcome, price move or performance for any symbol.

Cohorts:
  P (decision-time) — rows of frozen pool records with a valid digest (`faisal_engine/data/pool_funnel_frozen.jsonl`).
  W (exploratory, NOT_DECISION_TIME) — the first stored `shares_available` of every watchlist member that first appears after the
    limit commit, extracted from git history into a frozen file (`borrow_boundary_w.json`). Members only (an ejected symbol is never
    stored) · the daily path refreshes availability after the fill and before saving, so a stored value is not the gate's value.

Modes: (default) build `borrow_boundary_shadow.json` + `.md` from the frozen inputs · `--check` rebuild in memory and compare bytes ·
`--refresh-w` re-extract W from git (needs full history · local only; `--check` and the suite never touch git).
"""
import ast
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "faisal_engine"))
import pool_funnel as PF  # noqa: E402  (frozen-record digest · JSONL loader)

F_POOL = os.path.join(HERE, "faisal_engine", "data", "pool_funnel_frozen.jsonl")
F_BOT = os.path.join(HERE, "Super_stock.py")
F_W = os.path.join(HERE, "borrow_boundary_w.json")
F_JSON = os.path.join(HERE, "borrow_boundary_shadow.json")
F_MD = os.path.join(HERE, "borrow_boundary_shadow.md")
WL_PATH = "weekly_watchlist.json"
LIMIT_COMMIT = "d0919f1ad"            # «طبّق 20» — BORROW_AVAIL_MAX 40,000 ⟶ 20,000 (2026-08-11T09:21:43Z)
SCHEMA = 1
OTHER_OUTCOMES = ("DUPLICATE", "DQ_HELD", "EXCLUDED")
# Written after the count — the contract is merged and is not edited; its errors are disclosed here, in every output.
DISCLOSURES = [
    "Contract error: the prereg says no archive entry measured equality at the limit. That is wrong — the #604 archive bullet ⑧ "
    "(2026-10-10) had already counted SKYQ and VBIO at exactly 20,000 (2 of 4 known additions in the renewal), 19 of 110 "
    "watchlist additions since 2026-08-11 at the limit, 77 of 471 `ctb_log` readings at or below 20,000 sitting on it, and "
    "described the values as quantized (15,000 · 20,000 · 25,000). The archive grep for this contract matched that line but "
    "it was read truncated.",
    "Consequence: T1, T3 and T4 were made with that bullet in memory and T2 with its quantization remark — none of the four "
    "predictions is blind. They are published as made and carry no evidential weight.",
    "This study therefore adds no new fact about the boundary: it re-derives #604's figures reproducibly from frozen inputs "
    "(exhaustive row states · consistency with the live rule · fill context · cohort labels · locks). The W denominator differs "
    "from #604's 110 by definition (here: members first seen after the limit commit with a numeric first value).",
]
STATES = ["KNOWN_BELOW", "KNOWN_AT_LIMIT", "KNOWN_ABOVE", "UNKNOWN", "NOT_EXAMINED", "OTHER_EXCLUSION"]
W_STATES = ["AT_LIMIT", "BELOW", "ABOVE", "NONE"]


# ───────────────────────── the live rule, read from the bot's code (never restated by hand)
def gate_rule(src=None):
    """(limit, op): the CONFIG literal `BORROW_AVAIL_MAX` and the comparison `borrow_gate_recheck` ejects with
    ("Gt" ⟵ eject above, the limit passes · "GtE" ⟵ the limit is ejected). None where the code does not say."""
    tree = ast.parse(open(F_BOT, encoding="utf-8").read() if src is None else src)
    limit, op = None, None
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "BORROW_AVAIL_MAX" and isinstance(v, ast.Constant):
                    limit = v.value
        if isinstance(n, ast.FunctionDef) and n.name == "borrow_gate_recheck":
            for c in ast.walk(n):
                if (isinstance(c, ast.Compare) and len(c.ops) == 1 and isinstance(c.comparators[0], ast.Name)
                        and c.comparators[0].id == "limit"):
                    op = type(c.ops[0]).__name__
    return limit, op


def passes(av, limit, rule):
    """«LE» = the live reading (eject above) · «LT» = Faisal's literal «below»."""
    return av <= limit if rule == "LE" else av < limit


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if v == v else None


# ───────────────────────── cohort P
def row_state(row, limit):
    """One of STATES (exhaustive, in this order): excluded before the gate · KNOWN by value · asked but unknown (a KNOWN state without a
    number reads as unknown — never zero) · never asked."""
    if row.get("outcome") in OTHER_OUTCOMES:
        return "OTHER_EXCLUSION"
    av = _num(row.get("av"))
    if row.get("av_state") == "KNOWN" and av is not None:
        return "KNOWN_BELOW" if av < limit else ("KNOWN_AT_LIMIT" if av == limit else "KNOWN_ABOVE")
    if row.get("av_state") in ("UNKNOWN", "KNOWN"):
        return "UNKNOWN"
    return "NOT_EXAMINED"


def consistency(row, state):
    """The recorded outcome must agree with the live rule (eject above): a contradiction means this reading of the rule is wrong."""
    o = row.get("outcome")
    if state == "KNOWN_ABOVE" and o not in ("BORROW_REJECT", "FLOAT_REJECT"):
        return f"{row.get('sym')}: above the limit but {o}"
    if state in ("KNOWN_BELOW", "KNOWN_AT_LIMIT") and o == "BORROW_REJECT":
        return f"{row.get('sym')}: at or below the limit but BORROW_REJECT"
    return None


def granularity(values):
    n = len(values)
    out = {"n": n}
    for step in (1000, 5000, 10000):
        k = sum(1 for v in values if v % step == 0)
        out[f"multiple_of_{step}"] = k
        out[f"share_{step}"] = round(k / n, 4) if n else None
    return out


def cohort_p(recs, limit):
    states = {s: 0 for s in STATES}
    at_limit, issues, records = [], [], []
    known_all, known_unseen = [], []
    for rec in sorted(recs, key=lambda r: str(r.get("ts", ""))):
        rows = PF._rows(rec)
        c = {s: 0 for s in STATES}
        member_diff = []
        for row in rows:
            st = row_state(row, limit)
            c[st] += 1
            states[st] += 1
            bad = consistency(row, st)
            if bad:
                issues.append(f"{rec.get('date')} {bad}")
            if st.startswith("KNOWN_"):
                av = _num(row.get("av"))
                known_all.append(av)
                if row.get("outcome") != "BORROW_REJECT":
                    known_unseen.append(av)
            if st == "KNOWN_AT_LIMIT":
                e = {"date": rec.get("date"), "run_id": rec.get("run_id"), "symbol": row.get("sym"), "outcome": row.get("outcome"),
                     "added": bool(row.get("added")), "round": row.get("round"), "av_src": row.get("av_src"),
                     "membership_difference": bool(row.get("added")), "source_semantics": "SOURCE_SEMANTICS_UNRESOLVED"}
                at_limit.append(e)
                if e["membership_difference"]:
                    member_diff.append(row.get("sym"))
        records.append({"date": rec.get("date"), "source": rec.get("source"), "run_id": rec.get("run_id"), "rows": len(rows),
                        "states": c, "membership_difference": member_diff,
                        "fill_context": {"rounds_used": rec.get("rounds_used"), "rounds_max": rec.get("rounds_max"),
                                         "not_examined": c["NOT_EXAMINED"], "replacement": "UNKNOWN" if member_diff else None}})
    label = "DIFFERS" if at_limit else "IDENTICAL_IN_DECISION_DATA"
    return {"records": records, "states": states, "at_limit": at_limit, "consistency_issues": issues, "label": label,
            "membership_difference": sum(1 for e in at_limit if e["membership_difference"]),
            "granularity_all_known": granularity(known_all), "granularity_unseen_known": granularity(known_unseen)}


# ───────────────────────── cohort W (frozen extraction; git only in --refresh-w)
def w_state(av, limit):
    v = _num(av)
    if v is None:
        return "NONE"
    return "BELOW" if v < limit else ("AT_LIMIT" if v == limit else "ABOVE")


def refresh_w(head="origin/main"):  # pragma: no cover — needs full git history; never called by build or --check
    import subprocess
    git = lambda *a: subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True, check=True).stdout  # noqa: E731
    lim = git("rev-parse", LIMIT_COMMIT).strip()
    head_sha = git("rev-parse", head).strip()
    base = json.loads(git("show", f"{lim}:{WL_PATH}"))
    seen = {(s.get("symbol"), s.get("added")) for s in base.get("stocks", [])}
    commits = [ln.split() for ln in git("rev-list", "--reverse", "--format=%H %cI", "--no-commit-header",
                                         f"{lim}..{head_sha}", "--", WL_PATH).splitlines() if ln.strip()]
    members, unreadable = [], 0
    for sha, when in commits:
        try:
            wl = json.loads(git("show", f"{sha}:{WL_PATH}"))
        except Exception:                                 # noqa: BLE001
            unreadable += 1
            continue
        ren = str(wl.get("renewed_at") or "")[:10]
        for s in wl.get("stocks", []):
            key = (s.get("symbol"), s.get("added"))
            if not key[0] or key in seen:
                continue
            seen.add(key)
            path = "UNDETERMINED" if not ren else ("RENEWAL" if s.get("added") == ren else "DAILY")
            members.append({"symbol": key[0], "added": key[1], "first_av": s.get("shares_available"), "first_commit": sha,
                            "first_commit_time": when, "path": path})
    doc = {"limit_commit": lim, "head": head_sha, "commits_read": len(commits), "unreadable": unreadable,
           "baseline_members_excluded": len({k for k in seen}) - len(members), "members": members}
    with open(F_W, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    return doc


def cohort_w(wdoc, limit):
    if not wdoc:
        return {"present": False}
    ms = wdoc.get("members") or []
    counts = {s: 0 for s in W_STATES}
    by_path = {}
    rows = []
    for m in ms:
        st = w_state(m.get("first_av"), limit)
        counts[st] += 1
        by_path.setdefault(m.get("path"), {s: 0 for s in W_STATES})[st] += 1
        if st == "AT_LIMIT":
            rows.append({k: m.get(k) for k in ("symbol", "added", "path", "first_commit_time")})
    return {"present": True, "label": "NOT_DECISION_TIME", "limit_commit": wdoc.get("limit_commit"), "head": wdoc.get("head"),
            "commits_read": wdoc.get("commits_read"), "unreadable": wdoc.get("unreadable"), "members": len(ms), "states": counts,
            "by_path": {k: by_path[k] for k in sorted(by_path)}, "at_limit": rows,
            "limit_day_members": sum(1 for m in ms if str(m.get("added")) <= "2026-08-11")}


# ───────────────────────── predictions (prereg §⑥ — published as they fall)
def predictions(p, w):
    g = p["granularity_unseen_known"]
    t2 = "NOT_TESTABLE" if not g["n"] else ("TRUE" if g["share_5000"] >= 0.95 else "FALSE")
    renew = [r for r in p["records"] if r["date"] == "2026-10-10" and r["source"] == "renew"]
    return {"T1": "TRUE" if p["states"]["KNOWN_AT_LIMIT"] == 0 else "FALSE", "T2": t2,
            "T3": "NOT_TESTABLE" if not w.get("present") else ("TRUE" if w["states"]["AT_LIMIT"] >= 1 else "FALSE"),
            "T4": "NOT_TESTABLE" if not renew else ("TRUE" if not renew[0]["membership_difference"] else "FALSE")}


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build(pool=F_POOL, wfile=F_W, src=None):
    limit, op = gate_rule(src)
    recs, bad = PF.load_jsonl(pool)
    ok = [r for r in recs if PF.record_sha(r) == r.get("sha")]
    wdoc = json.load(open(wfile, encoding="utf-8")) if os.path.exists(wfile) else None
    p = cohort_p(ok, float(limit)) if limit is not None else None
    w = cohort_w(wdoc, float(limit)) if limit is not None else {"present": False}
    return {"schema": SCHEMA, "contract": "borrow_boundary_prereg.md", "rule": {
                "limit": limit, "live_op": op, "live_reading": "LE (the limit passes)" if op == "Gt" else
                ("LT (the limit is ejected)" if op == "GtE" else "UNREAD"), "faisal_literal": "LT («تحت 20 الف» · IMG_0151)"},
            "inputs": {"pool": {"path": PF._rel(pool), "records": len(ok), "integrity_failed": len(recs) - len(ok) + len(bad),
                                "sha256": _digest([r.get("sha") for r in ok])},
                       "watchlist_history": {"path": PF._rel(wfile), "present": wdoc is not None,
                                             "sha256": _digest(wdoc) if wdoc is not None else None}},
            "P": p, "W": w, "predictions": predictions(p, w) if p else None,
            "disclosures": DISCLOSURES,
            "not_claimed": ["performance", "price move", "replacement symbol", "a production decision"]}


def render(doc):
    r, p, w = doc["rule"], doc["P"], doc["W"]
    L = ["# 📏 T-BORROW-EQ — the borrow gate's boundary in persisted data (shadow · descriptive)", "",
         "> Generated by `borrow_boundary_shadow.py` from frozen inputs — **do not edit by hand**; `--check` rebuilds and compares. "
         "Contract: `borrow_boundary_prereg.md` (merged before any count). Zero external requests · no production change · "
         "no outcome or performance for any symbol.", "",
         f"- Live rule (read from `borrow_gate_recheck`): limit **{r['limit']:,}** · comparison `{r['live_op']}` ⟶ **{r['live_reading']}**.",
         f"- Faisal's text: **{r['faisal_literal']}**. The two readings differ only on a KNOWN availability **equal** to the limit.", "",
         "## 1. Cohort P — decision-time rows of frozen pool records", "",
         f"Records read: **{doc['inputs']['pool']['records']}** (integrity failed: {doc['inputs']['pool']['integrity_failed']}).", "",
         "| state | rows | live (eject above) | literal (below) |", "|---|---|---|---|"]
    meaning = {"KNOWN_BELOW": ("passes", "passes"), "KNOWN_AT_LIMIT": ("**passes**", "**ejected**"),
               "KNOWN_ABOVE": ("ejected", "ejected"), "UNKNOWN": ("passes (benefit of doubt)", "passes (benefit of doubt)"),
               "NOT_EXAMINED": ("never asked", "never asked"), "OTHER_EXCLUSION": ("excluded before the gate", "excluded before the gate")}
    for s in STATES:
        L.append(f"| {s} | {p['states'][s]} | {meaning[s][0]} | {meaning[s][1]} |")
    L += ["", "| record | source | run | rows | at limit | membership difference | rounds used / max | not examined | replacement |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in p["records"]:
        fc = x["fill_context"]
        L.append(f"| {x['date']} | {x['source']} | {x['run_id']} | {x['rows']} | {x['states']['KNOWN_AT_LIMIT']} | "
                 f"{', '.join(x['membership_difference']) or '—'} | {fc['rounds_used']} / {fc['rounds_max']} | {fc['not_examined']} | "
                 f"{fc['replacement'] or '—'} |")
    L += ["", f"**Label: {p['label']}** — a description of the persisted decision data, not a judgement of either rule.", ""]
    if p["at_limit"]:
        L += ["| date | symbol | outcome | added | round | source of value | semantics |", "|---|---|---|---|---|---|---|"]
        for e in p["at_limit"]:
            L.append(f"| {e['date']} | {e['symbol']} | {e['outcome']} | {e['added']} | {e['round']} | {e['av_src']} | {e['source_semantics']} |")
        L.append("")
    ga, gu = p["granularity_all_known"], p["granularity_unseen_known"]
    L += ["**Granularity of KNOWN values** (description — the publisher's rounding is not documented, so a reported 20,000 is "
          "`SOURCE_SEMANTICS_UNRESOLVED`):", "",
          "| subset | n | multiples of 1,000 | of 5,000 | of 10,000 |", "|---|---|---|---|---|",
          f"| all KNOWN | {ga['n']} | {ga['multiple_of_1000']} | {ga['multiple_of_5000']} | {ga['multiple_of_10000']} |",
          f"| not rejected by the gate (unseen before the contract) | {gu['n']} | {gu['multiple_of_1000']} | {gu['multiple_of_5000']} | "
          f"{gu['multiple_of_10000']} |", "",
          f"Recorded outcome vs the live rule: **{len(p['consistency_issues'])}** contradictions"
          + (": " + " · ".join(p["consistency_issues"]) if p["consistency_issues"] else "") + ".", "",
          "## 2. Cohort W — watchlist members' first stored availability (NOT_DECISION_TIME)", ""]
    if not w.get("present"):
        L += ["Not extracted (`borrow_boundary_w.json` absent).", ""]
    else:
        L += [f"Git history of `{WL_PATH}` from `{w['limit_commit'][:9]}` to `{w['head'][:9]}`: **{w['commits_read']}** commits "
              f"(unreadable {w['unreadable']}) · **{w['members']}** members first seen after the limit commit "
              f"(added on or before 2026-08-11: {w['limit_day_members']}).", "",
              "| path | " + " | ".join(W_STATES) + " |", "|---|" + "---|" * len(W_STATES)]
        for k, v in w["by_path"].items():
            L.append(f"| {k} | " + " | ".join(str(v[s]) for s in W_STATES) + " |")
        L.append("| **all** | " + " | ".join(f"**{w['states'][s]}**" for s in W_STATES) + " |")
        L += ["", "Members only (an ejected symbol is never stored) · the daily path refreshes availability after the fill and before "
              "saving · RENEWAL = `added` equals the day of `renewed_at` (field absent before 2026-09-26 ⟶ UNDETERMINED) · "
              "so a first stored value is **not** the value the gate read.", ""]
        if w["at_limit"]:
            L += ["| symbol | added | path | first stored at |", "|---|---|---|---|"]
            for e in w["at_limit"]:
                L.append(f"| {e['symbol']} | {e['added']} | {e['path']} | {e['first_commit_time']} |")
            L.append("")
    pr = doc["predictions"]
    L += ["## 3. Predictions written before any count (prereg §⑥)", "",
          f"- T1 (weak) no KNOWN row at exactly the limit in P: **{pr['T1']}**",
          f"- T2 (moderate) 95% or more of the unseen KNOWN values in P are multiples of 5,000: **{pr['T2']}**",
          f"- T3 (weak) at least one W member first stored at exactly the limit: **{pr['T3']}**",
          f"- T4 (weak) no membership difference in the 2026-10-10 renewal: **{pr['T4']}**", "",
          "### ⚠️ Disclosed after the count", ""] + [f"- {x}" for x in doc["disclosures"]] + ["",
          "## 4. Limits", "",
          "- No production change: the limit, the comparison, membership, rounds, fill size and schedule are untouched; any finding is "
          "an owner option only.",
          "- A vacated slot's replacement is **UNKNOWN** (the next ranked rows were never enriched) and no success or failure is "
          "attributed to an unexamined symbol.",
          "- Not applied retroactively to GDHG · METCB · KMRK · CSAI · AFJK (owner's order).", ""]
    return "\n".join(L)


def write(doc):
    with open(F_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    with open(F_MD, "w", encoding="utf-8") as fh:
        fh.write(render(doc))


def main(argv):
    if "--refresh-w" in argv:
        d = refresh_w()
        print(f"W: {d['commits_read']} commits · {len(d['members'])} members")
        return 0
    doc = build()
    if "--check" in argv:
        j = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        okj = os.path.exists(F_JSON) and open(F_JSON, encoding="utf-8").read() == j
        okm = os.path.exists(F_MD) and open(F_MD, encoding="utf-8").read() == render(doc)
        print("check OK" if okj and okm else f"check FAILED (json={okj} md={okm})")
        return 0 if okj and okm else 1
    write(doc)
    print(f"P: {doc['P']['label']} · W present: {doc['W'].get('present')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
