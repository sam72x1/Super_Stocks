"""🎯🗂️ Fill-pool funnel evaluator — read-only (no network, no Telegram, no production state written).

What it answers (owner mission «PROSPECTIVE CANDIDATE-POOL CAPTURE», follow-up to #599, 2026-10-09): for each screening run,
how the ranked, data-quality-passed candidate pool flowed through the fill rounds — how many were examined, how many were never
examined, how many the borrow gate rejected with a KNOWN availability, how many passed with an UNKNOWN availability (benefit of
the doubt), how many were added, how many slots stayed empty, and the first cause of the shortfall. The per-run record is
written by the bot itself (`Super_stock.record_fill_pool` ⟶ `fill_pool_log.jsonl`, saved with the bot state by `git_save`).

Rules (mission §6): an unexamined name is never a failure and never a pass; an UNKNOWN availability is never counted as
passing the threshold; no cohort's pass rate is projected onto unexamined names; legacy runs (before the log existed) are
reported with what their logs actually recorded and every missing field is named NOT_COLLECTED.

Inputs (all frozen, so `--check` is reproducible):
  · `data/gate_fill_observations.json` — counts from the three post-parser-fix run logs (2026-10-07/08/09);
  · `data/gate_pool_evidence.json` — the 2026-10-09 run's examined names;
  · `data/pool_funnel_legacy.json` — per legacy run, the upper bound of names excluded from the fill (held ∪ stopped) taken
    from the committed watchlist at the run's head commit and at its own save commit (git history, no external request);
  · `data/pool_funnel_frozen.jsonl` — prospective records copied verbatim from `fill_pool_log.jsonl` (append-only, by key).
Outputs: `out/POOL_FUNNEL.json` · `POOL_FUNNEL_REPORT.md`.

Modes: (default) build · `--check` rebuild in memory and compare · `--live PATH` evaluate a live log and print, write nothing ·
`--freeze PATH` append records of PATH that are not yet frozen (never rewrites a frozen line) · `--legacy-snapshot` rebuild
`data/pool_funnel_legacy.json` from git history (explicit only).
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")
F_OBS = os.path.join(DATA, "gate_fill_observations.json")
F_EV = os.path.join(DATA, "gate_pool_evidence.json")
F_LEG = os.path.join(DATA, "pool_funnel_legacy.json")
F_FROZEN = os.path.join(DATA, "pool_funnel_frozen.jsonl")
F_JSON = os.path.join(OUT, "POOL_FUNNEL.json")
F_MD = os.path.join(HERE, "POOL_FUNNEL_REPORT.md")

SCHEMA = 1
COLS = ["sym", "rank", "pool_pos", "rk", "dq", "excl", "round", "outcome", "av", "av_state", "av_src", "added"]
OUTCOMES = ["DUPLICATE", "DQ_HELD", "EXCLUDED", "NOT_EXAMINED", "FLOAT_REJECT", "BORROW_REJECT", "PASSED_UNKNOWN_AV",
            "PASSED_KNOWN_AV"]
# mission §2 states (a row has exactly one letter; `added` is reported beside it, never inferred from counts)
STATE = {"DUPLICATE": "A", "DQ_HELD": "A", "EXCLUDED": "A", "NOT_EXAMINED": "B", "FLOAT_REJECT": "C", "BORROW_REJECT": "C",
         "PASSED_UNKNOWN_AV": "D"}
STATE_MEANING = {"A": "never a fill candidate (data-quality held · duplicate · already held or stopped)",
                 "B": "in the pool, never examined (below the fill cutoff)",
                 "C": "examined, rejected by a post-enrich gate with a known value (borrow or float)",
                 "D": "examined, availability UNKNOWN or malformed — passed the gate by benefit of the doubt",
                 "E": "examined, passed with a KNOWN availability, not added",
                 "F": "examined, passed with a KNOWN availability, added"}
LEGACY_RUNS = [("2026-10-07", "37589176908"), ("2026-10-08", "37747202124"), ("2026-10-09", "37902530011")]
NC = "NOT_COLLECTED"


def _rel(p):
    return os.path.relpath(p, ROOT)


def record_sha(rec):
    """Same digest as `Super_stock.fill_pool_sha` (sorted-key JSON without the `sha` field) — re-implemented so the
    evaluator never imports the bot; a suite lock pins the two together."""
    body = {k: v for k, v in (rec or {}).items() if k != "sha"}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_jsonl(path):
    """Records of a JSONL file; a line that is not a JSON object becomes an integrity error (never silently skipped)."""
    recs, bad = [], []
    if not path or not os.path.exists(path):
        return recs, bad
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError as e:
                bad.append(f"line {i}: not JSON ({e.__class__.__name__})")
                continue
            if not isinstance(r, dict):
                bad.append(f"line {i}: not an object")
                continue
            recs.append(r)
    return recs, bad


def _rows(rec):
    cols = rec.get("cols") or COLS
    return [dict(zip(cols, r)) for r in (rec.get("rows") or [])]


def _state(row):
    o = row.get("outcome")
    if o in STATE:
        return STATE[o]
    if o == "PASSED_KNOWN_AV":
        return "F" if row.get("added") else "E"
    return "?"


def _rk_le(a, b):
    """a ≤ b for two `rank_key` lists; None when not comparable (missing or mixed types)."""
    if a is None or b is None:
        return None
    try:
        return list(a) <= list(b)
    except TypeError:
        return None


def replay(rec):
    """Independent re-derivation from the rows and the trace. Returns (issues, derived) where `derived` holds the
    per-row outcome recomputed from the trace and the selection replayed with `select_top`'s rule (first k pool names in
    order, skipping excluded and already-selected names). Any disagreement with the recorded rows is an integrity issue."""
    issues = []
    rows = _rows(rec)
    if rec.get("rows_cut"):
        issues.append(f"rows cut at the cap ({rec['rows_cut']} not recorded) — selection replay limited to the recorded rows")
    # ① production order: rank strictly increasing · pool_pos increasing among DQ-passed rows · rank_key non-decreasing
    prev = None
    for r in rows:
        if prev is not None and not (isinstance(r.get("rank"), int) and r["rank"] > prev["rank"]):
            issues.append(f"rank not increasing at {r.get('sym')}")
        if prev is not None:
            le = _rk_le(prev.get("rk"), r.get("rk"))
            if le is False:
                issues.append(f"rank_key decreases at {r.get('sym')} (snapshot is not in production order)")
        prev = r
    _first = set()
    pp = []
    for r in rows:
        if r.get("dq") == "PASS" and r.get("sym") not in _first:
            pp.append(r.get("pool_pos"))
        _first.add(r.get("sym"))
    if any(b is not None and a is not None and b < a for a, b in zip(pp, pp[1:])):
        issues.append("pool_pos not increasing with rank (DQ filter must preserve order)")
    # ② outcome per row recomputed from the trace (same rule as the bot; first round wins)
    trace = rec.get("trace") if isinstance(rec.get("trace"), list) else []
    exam = {}
    for t in trace:
        fl, bw = set(t.get("fl") or []), set(t.get("bw") or [])
        a1, a2 = t.get("av_enrich") or {}, t.get("av_gate") or {}
        for s in t.get("sel") or []:
            if s in exam:
                continue
            if s in fl:
                out = "FLOAT_REJECT"
            elif s in bw:
                out = "BORROW_REJECT"
            else:
                av = a2.get(s, a1.get(s))
                out = "PASSED_UNKNOWN_AV" if (av is None or isinstance(av, str)) else "PASSED_KNOWN_AV"
            exam[s] = (int(t.get("r")), out)
    seen = set()
    for r in rows:
        s = r.get("sym")
        if s in seen:
            want = "DUPLICATE"
        elif r.get("dq") != "PASS":
            want = "DQ_HELD"
        elif r.get("excl"):
            want = "EXCLUDED"
        elif s in exam:
            want = exam[s][1]
            if r.get("round") != exam[s][0]:
                issues.append(f"{s}: recorded round {r.get('round')} ≠ trace round {exam[s][0]}")
        else:
            want = "NOT_EXAMINED"
        seen.add(s)
        if r.get("outcome") != want:
            issues.append(f"{s}: recorded outcome {r.get('outcome')} ≠ re-derived {want}")
        if r.get("outcome") not in OUTCOMES:
            issues.append(f"{s}: unknown outcome {r.get('outcome')}")
        if r.get("outcome") == "PASSED_KNOWN_AV" and not isinstance(r.get("av"), (int, float)):
            issues.append(f"{s}: KNOWN availability without a numeric value")
        if r.get("round") is None and r.get("av") is not None:
            issues.append(f"{s}: availability recorded for a name that was never examined")
    # ③ selection replay (select_top: first k names in pool order not excluded and not already selected)
    pool = [r.get("sym") for r in rows if r.get("dq") == "PASS"]
    excl = {r.get("sym") for r in rows if r.get("excl")}
    space = rec.get("space")
    kept = 0
    if isinstance(space, int) and not rec.get("rows_cut"):
        for t in trace:
            k = space - kept
            sel, chosen = [], set()
            for s in pool:
                if s in excl:
                    continue
                sel.append(s)
                chosen.add(s)
                if len(sel) >= k:
                    break
            if list(t.get("sel") or []) != sel:
                issues.append(f"round {t.get('r')}: trace selection ≠ replayed select_top ({len(t.get('sel') or [])} vs {len(sel)})")
            excl |= chosen
            kept += len(t.get("kept") or [])
    # ④ funnel recomputed from the rows
    uniq = [r for r in rows if r.get("outcome") != "DUPLICATE"]
    cnt = {o: sum(1 for r in uniq if r.get("outcome") == o) for o in OUTCOMES}
    f = rec.get("funnel") or {}
    re_f = {"ranked": len(rows), "duplicates": len(rows) - len(uniq), "dq_held": cnt["DQ_HELD"],
            "pool_unique": sum(1 for r in uniq if r.get("dq") == "PASS"), "excluded": cnt["EXCLUDED"],
            "examined": sum(1 for r in uniq if r.get("round") is not None), "not_examined": cnt["NOT_EXAMINED"],
            "float_reject": cnt["FLOAT_REJECT"], "borrow_reject": cnt["BORROW_REJECT"],
            "passed_known_av": cnt["PASSED_KNOWN_AV"], "passed_unknown_av": cnt["PASSED_UNKNOWN_AV"]}
    if not rec.get("rows_cut"):
        for k, v in re_f.items():
            if f.get(k) != v:
                issues.append(f"funnel.{k} recorded {f.get(k)} ≠ recomputed {v}")
        n_added_rows = sum(1 for r in uniq if r.get("added"))
        if f.get("added") is not None and n_added_rows > f["added"]:
            issues.append(f"more rows flagged added ({n_added_rows}) than names added ({f['added']})")
    return issues, re_f


def shortfall(rec, re_f):
    """First cause of the shortfall, re-derived (not copied): NONE · POOL_EXHAUSTED · ROUNDS_CAP · LOOP_ENDED · NO_FILL."""
    f = rec.get("funnel") or {}
    if rec.get("status") == "NO_FILL":
        return "NO_FILL"
    if not f.get("unfilled"):
        return "NONE"
    if re_f.get("not_examined", 0) == 0:
        return "POOL_EXHAUSTED"
    if int(rec.get("rounds_used") or 0) >= int(rec.get("rounds_max") or 0):
        return "ROUNDS_CAP"
    return "LOOP_ENDED"


def evaluate_record(rec):
    issues = []
    if rec.get("v") != SCHEMA:
        issues.append(f"schema v={rec.get('v')} (expected {SCHEMA})")
    if rec.get("sha") != record_sha(rec):
        issues.append("sha mismatch (record altered after it was written)")
    if rec.get("status") == "FILLED" and list(rec.get("cols") or []) != COLS:
        issues.append("unexpected columns")
    rp_issues, re_f = replay(rec) if rec.get("status") == "FILLED" else ([], {})
    issues += rp_issues
    rows = _rows(rec)
    seen, states = set(), {k: 0 for k in "ABCDEF"}
    added_unknown = 0
    not_examined = []
    for r in rows:
        if r.get("sym") in seen:
            continue
        seen.add(r.get("sym"))
        st = _state(r)
        if st in states:
            states[st] += 1
        if st == "D" and r.get("added"):
            added_unknown += 1
        if st == "B":
            not_examined.append(r.get("sym"))
    f = rec.get("funnel") or {}
    sf = shortfall(rec, re_f) if rec.get("status") == "FILLED" else "NO_FILL"
    if rec.get("status") == "FILLED" and f.get("shortfall") != sf:
        issues.append(f"shortfall recorded {f.get('shortfall')} ≠ re-derived {sf}")
    rounds = [{"r": t.get("r"), "selected": len(t.get("sel") or []), "float_rejected": len(t.get("fl") or []),
               "borrow_rejected": len(t.get("bw") or []), "kept": len(t.get("kept") or []),
               "second_chance": t.get("sc") if t.get("sc") is not None else NC}
              for t in (rec.get("trace") or [])]
    return {"key": rec.get("key"), "source": rec.get("source"), "date": rec.get("date"), "run_id": rec.get("run_id"),
            "run_url": rec.get("run_url"), "status": rec.get("status"), "no_fill": rec.get("no_fill"),
            "integrity": "OK" if not issues else "FAIL", "issues": issues,
            "counts": {"qualified": rec.get("n_qualified"), "pool_after_dq": f.get("pool_unique"),
                       "excluded_held_or_stopped": f.get("excluded"), "examined": f.get("examined"),
                       "not_examined": f.get("not_examined"), "borrow_reject_known": f.get("borrow_reject"),
                       "float_reject": f.get("float_reject"), "passed_unknown_av": f.get("passed_unknown_av"),
                       "passed_known_av": f.get("passed_known_av"), "added": f.get("added"),
                       "added_with_unknown_av": added_unknown, "free_slots": rec.get("space"), "unfilled": f.get("unfilled"),
                       "rounds_used": rec.get("rounds_used"), "rounds_max": rec.get("rounds_max")},
            "states": states, "shortfall": sf, "rounds": rounds,
            "not_examined_names": not_examined,
            "not_examined_availability": NC,
            "availability_timestamp": rec.get("borrow_asof", NC),
            "borrow_max": rec.get("borrow_max")}


def legacy():
    """The three post-fix runs from their logs. Only what was logged is a number; the rest is NOT_COLLECTED. The shortfall
    cause is ROUNDS_CAP only when a lower bound of unexamined eligible names is above zero (fill_picks ends with an
    unexamined eligible name and empty slots only at the rounds cap); otherwise NOT_DETERMINABLE."""
    obs = {str(o["run_id"]): o for o in json.load(open(F_OBS, encoding="utf-8"))["runs"]}
    ev = json.load(open(F_EV, encoding="utf-8"))
    leg = {str(x["run_id"]): x for x in json.load(open(F_LEG, encoding="utf-8"))["runs"]}
    r9 = ev.get("run_2026_10_09") or {}
    out = []
    for date, rid in LEGACY_RUNS:
        o, lg = obs[rid], leg.get(rid) or {}
        ex = o["filled"] + o["borrow_ejected"] + o["fl_ejected"]
        pool = o.get("pool_after_dq")
        ub = lg.get("excluded_upper")
        lb = (pool - ex - ub) if (pool is not None and ub is not None) else None
        if lb is not None and lb > 0 and o["rounds"] >= 4 and o["filled"] < o["space"]:
            cause, basis = "ROUNDS_CAP", (f"at least {lb} eligible names never examined (pool {pool} − examined {ex} − "
                                          f"held ∪ stopped ≤ {ub}) with {o['space'] - o['filled']} slots empty")
        else:
            cause, basis = "NOT_DETERMINABLE", ("pool size after the data-quality gate was not logged" if pool is None
                                                else "the lower bound of unexamined eligible names is not above zero")
        names_ok = (rid == str(r9.get("run_id")))
        out.append({"date": date, "run_id": rid, "integrity": "LEGACY_COUNTS", "free_slots": o["space"],
                    "qualified": r9.get("qualified") if names_ok else NC, "pool_after_dq": pool if pool is not None else NC,
                    "examined": ex, "not_examined_upper": (pool - ex) if pool is not None else NC,
                    "not_examined_lower": lb if lb is not None else NC, "excluded_upper": ub if ub is not None else NC,
                    "borrow_reject_known": o["borrow_ejected"], "float_reject": o["fl_ejected"],
                    "passed_gate_picks": o["filled"], "passed_unknown_av": NC, "passed_known_av": NC,
                    "added": len(lg.get("added_names") or []) if lg.get("added_names") is not None else NC,
                    "added_names": lg.get("added_names", NC), "unfilled": o["space"] - o["filled"], "rounds_used": o["rounds"],
                    "shortfall": cause, "shortfall_basis": basis,
                    "examined_names": ((list(r9.get("added") or []) + [x["symbol"] for x in r9.get("borrow_ejected") or []])
                                       if names_ok else NC),
                    "not_examined_names": NC, "not_examined_availability": NC, "ranking_keys": NC,
                    "evidence": {"run_url": f"https://github.com/sam72x1/Super_Stocks/actions/runs/{rid}",
                                 "head_commit": lg.get("head_commit"), "save_commit": lg.get("save_commit")}})
    return out


def legacy_snapshot():
    """Rebuild `data/pool_funnel_legacy.json` from git history (explicit only). For each legacy run: the watchlist at the
    run's head commit (its input) and at the bot-data commit it pushed (its output). held ∪ stopped at fill time is a subset
    of stocks ∪ removed at either commit ⇒ the union is an upper bound on names the fill excluded."""
    runs_meta = {"37589176908": ("5df082426", "3e17f20ee"), "37747202124": ("1165153e6", "a42606f3f"),
                 "37902530011": ("30e7d99ce", "993d79984")}
    rows = []
    for date, rid in LEGACY_RUNS:
        h, p = runs_meta[rid]

        def wl(c):
            return json.loads(subprocess.run(["git", "show", f"{c}:weekly_watchlist.json"], cwd=ROOT, capture_output=True,
                                             text=True, check=True).stdout)
        a, b = wl(h), wl(p)
        S = lambda w: {s["symbol"] for s in w["stocks"]}          # noqa: E731
        R = lambda w: {s["symbol"] for s in w["removed"]}         # noqa: E731
        u = sorted(S(a) | R(a) | S(b) | R(b))
        rows.append({"date": date, "run_id": rid, "head_commit": h, "save_commit": p, "excluded_upper": len(u),
                     "excluded_upper_names": u, "added_names": sorted(S(b) - S(a))})
    doc = {"what": "per legacy fill run: an upper bound of the names excluded from the fill (held ∪ stopped), from the committed "
                   "watchlist at the run's head commit (input) and at its bot-data save commit (output) — read from git history, "
                   "no external request", "frozen_at": "2026-10-09",
           "method": "excluded_upper = |stocks ∪ removed| over both commits ⊇ held ∪ stopped at fill time; added_names = stocks at "
                     "the save commit not present at the head commit", "runs": rows}
    with open(F_LEG, "w", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    return doc


def build(live=None):
    recs, bad = load_jsonl(live or F_FROZEN)
    keys = [r.get("key") for r in recs]
    dup_keys = sorted({k for k in keys if keys.count(k) > 1})
    ev = [evaluate_record(r) for r in recs]
    doc = {"what": "fill-pool funnel per screening run — read-only evaluation of the bot's own pool records",
           "source": _rel(live) if live else _rel(F_FROZEN), "schema": SCHEMA,
           "integrity": {"records": len(recs), "unreadable_lines": bad, "duplicate_keys": dup_keys,
                         "records_failing": sum(1 for e in ev if e["integrity"] != "OK")},
           "states": STATE_MEANING, "prospective": ev, "legacy": legacy() if not live else None,
           "rules": ["an unexamined name is neither a failure nor a pass", "UNKNOWN availability is never counted as passing",
                     "no cohort pass rate is projected onto unexamined names", "added is read from the record, never inferred"]}
    return doc


def report(doc):
    L = ["# Fill-pool funnel — prospective capture and legacy runs", "",
         "> Generated by `faisal_engine/pool_funnel.py` from frozen inputs — **do not edit by hand**; `--check` rebuilds and compares.",
         "> Read-only: no network, no Telegram, no production state. This is observability: it does not change which names the bot",
         "> selects, and it is not evidence that any threshold is Faisal's or that more slots can be filled.", "",
         "## 1. What is recorded now (from the next scheduled screening run)", "",
         "Each daily screen and weekly renewal appends one line to `fill_pool_log.jsonl` (saved with the bot state by `git_save` in "
         "`run_performance_system`; append-only; union-merged on a rebase conflict; at most "
         "400 rows per run with the cut announced in `rows_cut`; one line per run also when nothing is filled, with its reason). "
         "Each row is one ranked qualified name with its rank, `rank_key`, data-quality result, exclusion reason, fill round, outcome, "
         "availability value and state (KNOWN · UNKNOWN · MALFORMED · NOT_COLLECTED), the stage that supplied it (enrich · second "
         "chance), and whether it was added. No extra request is made to fill a field; what the run did not look up is NOT_COLLECTED. "
         "The availability source timestamp is not carried by the providers' fields the bot keeps ⇒ `borrow_asof = NOT_COLLECTED`.", "",
         "| state | meaning |", "|---|---|"]
    for k, v in doc["states"].items():
        L.append(f"| {k} | {v} |")
    it = doc["integrity"]
    L += ["", "## 2. Prospective records (frozen copies of the bot's log)", "",
          f"Records: **{it['records']}** · unreadable lines {len(it['unreadable_lines'])} · duplicate keys {len(it['duplicate_keys'])} · "
          f"failing integrity {it['records_failing']}.", ""]
    if not doc["prospective"]:
        L += ["**None yet.** The capture ships with this change; the first record appears after the next scheduled screening run. "
              "Freeze it with `python3 faisal_engine/pool_funnel.py --freeze fill_pool_log.jsonl`, then rebuild.", ""]
    else:
        L += ["| date | source | run | integrity | pool | excluded | examined | not examined | borrow reject (known) | passed UNKNOWN | "
              "passed KNOWN | added | unfilled | shortfall |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for e in doc["prospective"]:
            c = e["counts"]
            L.append(f"| {e['date']} | {e['source']} | {e['run_id'] or 'local'} | {e['integrity']} | {c['pool_after_dq']} | "
                     f"{c['excluded_held_or_stopped']} | {c['examined']} | {c['not_examined']} | {c['borrow_reject_known']} | "
                     f"{c['passed_unknown_av']} | {c['passed_known_av']} | {c['added']} | {c['unfilled']} | {e['shortfall']} |")
        L.append("")
    lg = doc.get("legacy") or []
    if lg:
        L += ["## 3. Legacy runs (before the log existed) — what their logs recorded", "",
              "| date | run | free slots | pool after DQ | examined | not examined (bounds) | borrow reject (known) | passed UNKNOWN | "
              "added | unfilled | first shortfall cause |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in lg:
            b = (f"{x['not_examined_lower']}–{x['not_examined_upper']}" if x["not_examined_lower"] != NC
                 else (f"≤ {x['not_examined_upper']}" if x["not_examined_upper"] != NC else NC))
            L.append(f"| {x['date']} | {x['run_id']} | {x['free_slots']} | {x['pool_after_dq']} | {x['examined']} | {b} | "
                     f"{x['borrow_reject_known']} | {x['passed_unknown_av']} | {x['added']} | {x['unfilled']} | {x['shortfall']} |")
        L += ["", "Basis of each cause:", ""]
        for x in lg:
            L.append(f"- {x['date']}: **{x['shortfall']}** — {x['shortfall_basis']}.")
        L += ["", "NOT_COLLECTED for every legacy run: the names of the unexamined pool, their rank keys and their availability, and "
              "the split of passing names into known and unknown availability. The excluded bound comes from the committed watchlist "
              "at each run's head and save commits (`data/pool_funnel_legacy.json`). The pool's unexamined names cannot be recovered "
              "from any existing record, so the question «would they pass the borrow gate?» stays not determinable for these runs; "
              "no cohort pass rate is substituted for it.", ""]
    L += ["## 4. Reproduce", "",
          "- `python3 faisal_engine/pool_funnel.py --check` — rebuilds both outputs from the frozen inputs and compares.",
          "- `python3 faisal_engine/pool_funnel.py --live fill_pool_log.jsonl` — evaluates the live log and prints; writes nothing.",
          "- `python3 faisal_engine/pool_funnel.py --freeze fill_pool_log.jsonl` — appends the records not yet frozen (by key); a "
          "frozen line is never rewritten.", ""]
    return "\n".join(L) + "\n"


def render(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n", report(doc)


def freeze(path):
    """Append to the frozen file every record of `path` whose key is not frozen yet and whose digest verifies."""
    have, _ = load_jsonl(F_FROZEN)
    keys = {r.get("key") for r in have}
    new, _bad = load_jsonl(path)
    add = [r for r in new if r.get("key") not in keys and r.get("sha") == record_sha(r)]
    rej = [r.get("key") for r in new if r.get("key") not in keys and r.get("sha") != record_sha(r)]
    with open(F_FROZEN, "a", encoding="utf-8") as f:
        for r in add:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(add), rej


def main(argv):
    if "--legacy-snapshot" in argv:
        d = legacy_snapshot()
        print(f"legacy snapshot: {len(d['runs'])} runs → {_rel(F_LEG)}")
        return 0
    if "--freeze" in argv:
        n, rej = freeze(argv[argv.index("--freeze") + 1])
        print(f"frozen +{n} · rejected (digest) {len(rej)}")
        return 1 if rej else 0
    if "--live" in argv:
        d = build(argv[argv.index("--live") + 1])
        print(json.dumps({"integrity": d["integrity"], "runs": [{k: e[k] for k in ("date", "source", "integrity", "counts",
                                                                                      "states", "shortfall", "issues")}
                                                                 for e in d["prospective"]]}, ensure_ascii=False, indent=1))
        return 0 if d["integrity"]["records_failing"] == 0 and not d["integrity"]["unreadable_lines"] else 1
    j, md = render(build())
    if "--check" in argv:
        ok = True
        for path, want in ((F_JSON, j), (F_MD, md)):
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if have != want:
                ok = False
                print(f"DIFF {_rel(path)}")
        d = json.loads(j)
        if d["integrity"]["records_failing"] or d["integrity"]["unreadable_lines"] or d["integrity"]["duplicate_keys"]:
            ok = False
            print("integrity failure in frozen records")
        print("check OK" if ok else "check FAILED")
        return 0 if ok else 1
    os.makedirs(OUT, exist_ok=True)
    with open(F_JSON, "w", encoding="utf-8") as f:
        f.write(j)
    with open(F_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"built {_rel(F_JSON)} · {_rel(F_MD)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
