"""🔒📉 T-BORROW-FALL evaluator (`borrow_fall_prereg.md` §⑨) — read-only: no network, no Telegram, no production state.

What it answers today (owner mission «BORROW EVIDENCE RECOVERY», 2026-10-10): **can the registered question be evaluated from
what the repository actually persists — and where does the evidence disappear?** It never computes an outcome rate: the outcome
stage (+50 % within 40 sessions · `pre_move_pct`) is deliberately not built before the sample gate (§⑤ W4 · §⑥) — BLIND.

Population (§③, literally): every symbol the borrow gate ejected with a KNOWN availability above the gate's limit, read from the
bot's own persisted pool records (`fill_pool_log.jsonl`, frozen copies in `faisal_engine/data/pool_funnel_frozen.jsonl`, outcome
BORROW_REJECT, both the daily screen and the weekly renewal). The seed is the symbol's FIRST ejection; a later ejection never
resets it. The availability at the seed is known-at-decision; everything after it is observed-later.

Observations — persisted, append-only sources only (zero external requests; nothing is fetched to fill a gap):
  · later pool records (the symbol examined again at a later screening: its availability at that decision);
  · `ctb_log.jsonl` (the borrow harvester's daily rows, every cohort);
  · `fm_forensics/phase6/data/PHASE6_LEDGER.jsonl` (field `borrow_available`);
  · `borrow_watch.jsonl` — the registered harvester's own log, read if it exists in the repository.

Rules (mission §3 · prereg §④/§⑤):
  · an UNKNOWN availability (fetch failed · empty · NaN) is an attempt, never a value — never zero, never a fall, never a hold;
  · an observation is "later" only when its UTC date is strictly after the seed decision's UTC date (date-only sources carry no
    time of day, so a same-day row is SAME_DAY, never later — no look-ahead by ordering guesses);
  · in-window = observation date ≤ the 40th trading session after the seed's decision session (the registered horizon);
  · arm A ("fell below 10K") = a KNOWN later in-window observation strictly below `FAISAL_ENTRY_AVAIL_MAX` (prereg: «اقل من 10K»);
  · arm B ("never fell") is asserted only when the window is closed AND every trading day of it carries a KNOWN observation dated
    that day, all at or above the limit (B_FULL). Fewer observations, all at or above, is NOT_BELOW_PARTIAL — not B;
  · a seed with no KNOWN later observation is NO_FOLLOWUP (never counted as A or B).

The source timestamp of a ChartExchange value (its own as-of) is not recorded by any of these sources; it is reported as
NOT_COLLECTED and is never replaced by the collection time.

Modes: (default) build `borrow_fall_status.json` + `borrow_fall_status.md` · `--check` rebuild in memory with the stored as-of
and compare · `--asof YYYY-MM-DD` build as of that UTC date (default: the date of the latest frozen pool record; date-only
observation sources are read up to the day before it).
"""
import ast
import datetime as dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "faisal_engine"))
import pool_funnel as PF  # noqa: E402  (frozen-record digest · JSONL loader)
import market_calendar as MC  # noqa: E402

F_POOL = os.path.join(HERE, "faisal_engine", "data", "pool_funnel_frozen.jsonl")
F_CTB = os.path.join(HERE, "ctb_log.jsonl")
F_P6 = os.path.join(HERE, "fm_forensics", "phase6", "data", "PHASE6_LEDGER.jsonl")
F_WATCH = os.path.join(HERE, "borrow_watch.jsonl")
F_BOT = os.path.join(HERE, "Super_stock.py")
F_WF = os.path.join(HERE, ".github", "workflows", "daily_screener.yml")
F_JSON = os.path.join(HERE, "borrow_fall_status.json")
F_MD = os.path.join(HERE, "borrow_fall_status.md")
SCHEMA = 1
WINDOW_SESSIONS = 40          # prereg §④ «40 جلسة» · and the harvester's own comment (BORROW_WATCH_HORIZON «= نافذةُ الحسم المسجَّلة»)
SAMPLE_MIN = 30               # prereg §⑤ W4 / §⑥ (ج)

STATES = ("A_FELL_BELOW", "NOT_BELOW_PARTIAL", "B_FULL", "NO_FOLLOWUP_UNKNOWN_ONLY", "NO_FOLLOWUP_NONE")


# ───────────────────────── facts read from the bot's code (AST — the report flips by itself when the code changes)
def bot_facts(src=None, wf=None):
    """Constants and persistence facts from `Super_stock.py` / `daily_screener.yml`, by AST and text — never by importing the bot."""
    src = open(F_BOT, encoding="utf-8").read() if src is None else src
    wf = (open(F_WF, encoding="utf-8").read() if os.path.exists(F_WF) else "") if wf is None else wf
    tree = ast.parse(src)
    consts, config = {}, {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == "CONFIG" and isinstance(node.value, ast.Dict):
                for k, v in zip(node.value.keys, node.value.values):
                    if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                        config[k.value] = v.value
            elif isinstance(node.value, ast.Constant):
                consts[name] = node.value.value
    watch_name = consts.get("BORROW_WATCH_FILE")
    saved_lists, funcs_calling = [], set()
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(fn):
            if not isinstance(call, ast.Call):
                continue
            f = call.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm == "harvest_borrow_watch":
                funcs_calling.add(fn.name)
            if nm == "git_save" and call.args and isinstance(call.args[0], ast.List):
                saved_lists.append(sorted(e.id for e in call.args[0].elts if isinstance(e, ast.Name)))
    persisted_git = any("BORROW_WATCH_FILE" in lst for lst in saved_lists)
    persisted_artifact = bool(watch_name) and (watch_name in wf or "borrow_watch" in wf)
    due_unit = "UNKNOWN"
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == "borrow_watch_due":
            names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
            due_unit = "CALENDAR_DAYS" if "_iso_days_between" in names else "OTHER"
    return {
        "borrow_watch_file": watch_name,
        "horizon": consts.get("BORROW_WATCH_HORIZON"), "cap": consts.get("BORROW_WATCH_CAP"),
        "horizon_unit_in_code": due_unit,
        "fall_max": config.get("FAISAL_ENTRY_AVAIL_MAX"), "gate_max_config": config.get("BORROW_AVAIL_MAX"),
        "harvest_called_from": sorted(funcs_calling),
        "persisted_by_git_save": persisted_git,
        "persisted_by_artifact": persisted_artifact,
        "git_save_lists": len(saved_lists),
    }


# ───────────────────────── calendar
def _trading(d):
    return d.weekday() < 5 and not (d.isoformat() in MC.HOLIDAYS)


def decision_session(ts_utc):
    """The last regular session whose close is at or before `ts_utc` (New York time) — the session a decision could see."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromisoformat(str(ts_utc).replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
    d = t.date()
    if _trading(d):
        close = MC.session_info(d.isoformat()).get("close_ny_min")
        if close is not None and t.hour * 60 + t.minute >= close:
            return d.isoformat()
    d -= dt.timedelta(days=1)
    while not _trading(d):
        d -= dt.timedelta(days=1)
    return d.isoformat()


def sessions_after(session_iso, n):
    """The `n` trading days strictly after `session_iso`."""
    d, out = dt.date.fromisoformat(session_iso), []
    while len(out) < n:
        d += dt.timedelta(days=1)
        if _trading(d):
            out.append(d.isoformat())
    return out


# ───────────────────────── inputs (filtered as of a UTC date · each with a digest of what was read)
def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _digest(items):
    return hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def load_inputs(asof=None, pool=F_POOL, ctb=F_CTB, p6=F_P6, watch=F_WATCH):
    recs, bad = PF.load_jsonl(pool)
    recs_ok = [r for r in recs if PF.record_sha(r) == r.get("sha")]
    ctb_rows, ctb_bad = PF.load_jsonl(ctb)
    p6_rows, p6_bad = PF.load_jsonl(p6)
    w_rows, w_bad = PF.load_jsonl(watch)
    # As-of = the latest frozen pool record (frozen copies change only by an explicit `--freeze`, so the build is stable).
    # Date-only observation sources are read strictly BEFORE the as-of day: a day still being appended to is never read, so a
    # later same-day append cannot change a committed status (it is picked up when the as-of advances).
    asof = asof or max([str(r.get("date")) for r in recs_ok if r.get("date")] or ["1970-01-01"])
    recs_ok = [r for r in recs_ok if str(r.get("date", "")) <= asof]
    ctb_rows = [r for r in ctb_rows if str(r.get("date", "")) < asof]
    p6_rows = [r for r in p6_rows if str(r.get("collected_utc", ""))[:10] < asof and r.get("field") == "borrow_available"]
    w_rows = [r for r in w_rows if str(r.get("date", "")) < asof]
    inputs = {
        "pool": {"path": PF._rel(pool), "records": len(recs_ok), "integrity_failed": len(recs) - len(recs_ok) + len(bad),
                 "sha256": _digest([r.get("sha") for r in recs_ok])},
        "ctb_log": {"path": PF._rel(ctb), "rows": len(ctb_rows), "unreadable": len(ctb_bad), "sha256": _digest(ctb_rows)},
        "phase6": {"path": PF._rel(p6), "rows": len(p6_rows), "unreadable": len(p6_bad), "sha256": _digest(p6_rows)},
        "borrow_watch": {"path": PF._rel(watch), "present": os.path.exists(watch), "rows": len(w_rows),
                         "unreadable": len(w_bad), "sha256": _digest(w_rows)},
    }
    return asof, recs_ok, ctb_rows, p6_rows, w_rows, inputs


# ───────────────────────── decision-time availability states (every pool row)
def decision_state(row, gate_max):
    o, st, av = row.get("outcome"), row.get("av_state"), _num(row.get("av"))
    if o == "BORROW_REJECT":
        return "QUERIED_REJECTED_KNOWN" if st == "KNOWN" else "QUERIED_REJECTED_STATE_" + str(st)
    if o == "PASSED_KNOWN_AV":
        return "ELIGIBLE_PASSED_KNOWN"
    if o == "PASSED_UNKNOWN_AV":
        return "ELIGIBLE_PASSED_UNKNOWN"
    if o == "FLOAT_REJECT":
        if st == "KNOWN" and av is not None and gate_max is not None:
            return "PASSES_BORROW_FAILS_OTHER" if av <= float(gate_max) else "FAILS_OTHER_AND_ABOVE_BORROW"
        return "FAILS_OTHER_AV_" + str(st)
    if st == "UNKNOWN":
        return "QUERIED_UNKNOWN"
    return "NEVER_QUERIED_" + str(o)


# ───────────────────────── observations
def observations(recs, ctb_rows, p6_rows, w_rows):
    """Every availability reading as (symbol, date, value_or_None, source, decision_ts_or_None). Value None = UNKNOWN attempt.
    Rows that were never attempted (pool NOT_COLLECTED · phase6 NOT_ATTEMPTED) are not observations at all."""
    out = []
    for rec in recs:
        for row in PF._rows(rec):
            st = row.get("av_state")
            if st == "KNOWN":
                out.append((row.get("sym"), rec.get("date"), _num(row.get("av")), "pool", rec.get("ts")))
            elif st == "UNKNOWN":
                out.append((row.get("sym"), rec.get("date"), None, "pool", rec.get("ts")))
    for r in ctb_rows:
        out.append((r.get("symbol"), r.get("date"), _num(r.get("shares_available")), "ctb_log", None))
    for r in p6_rows:
        if r.get("status") == "NOT_ATTEMPTED":
            continue
        v = _num(r.get("value")) if r.get("status") == "OK" else None
        out.append((r.get("ticker"), str(r.get("collected_utc", ""))[:10], v, "phase6", r.get("collected_utc")))
    for r in w_rows:
        if r.get("kind") == "track":
            out.append((r.get("symbol"), r.get("date"), _num(r.get("available")), "borrow_watch", None))
    return [o for o in out if o[0] and o[1]]


def seeds(recs):
    """First BORROW_REJECT per symbol (records in time order) — the registered population."""
    first = {}
    for rec in sorted(recs, key=lambda r: (str(r.get("ts", "")), str(r.get("key", "")))):
        for row in PF._rows(rec):
            if row.get("outcome") != "BORROW_REJECT" or row.get("av_state") != "KNOWN":
                continue
            s = row.get("sym")
            if s and s not in first:
                first[s] = {"symbol": s, "seed_date": rec.get("date"), "seed_ts": rec.get("ts"), "source": rec.get("source"),
                            "run_id": rec.get("run_id"), "gate_max": rec.get("borrow_max"), "av_seed": _num(row.get("av"))}
    return [first[k] for k in sorted(first)]


def classify(seed, obs, asof, fall_max):
    sess = decision_session(seed["seed_ts"])
    win = sessions_after(sess, WINDOW_SESSIONS)
    w_end = win[-1]
    elapsed = [d for d in win if d <= asof]
    later = [o for o in obs if o[0] == seed["symbol"] and o[1] > seed["seed_date"] and o[1] <= w_end]
    same_day = [o for o in obs if o[0] == seed["symbol"] and o[1] == seed["seed_date"] and o[3] != "pool"]
    known = sorted((o for o in later if o[2] is not None), key=lambda o: (o[1], o[3]))
    unknown = [o for o in later if o[2] is None]
    below = [o for o in known if fall_max is not None and o[2] < float(fall_max)]
    obs_days = sorted({o[1] for o in known})
    closed = asof >= w_end
    if below:
        state = "A_FELL_BELOW"
    elif known:
        full = closed and all(d in obs_days for d in win)
        state = "B_FULL" if full else "NOT_BELOW_PARTIAL"
    else:
        state = "NO_FOLLOWUP_UNKNOWN_ONLY" if unknown else "NO_FOLLOWUP_NONE"
    return {**seed, "seed_session": sess, "window_end": w_end, "window": "CLOSED" if closed else "OPEN",
            "sessions_elapsed": len(elapsed), "known_later": len(known), "unknown_later": len(unknown),
            "same_day_other_source": len(same_day), "observed_days": len(obs_days),
            "sources": sorted({o[3] for o in known}), "first_below_date": below[0][1] if below else None,
            "source_asof": "NOT_COLLECTED", "state": state}


# ───────────────────────── build
def build(asof=None, facts=None, **paths):
    facts = bot_facts() if facts is None else facts
    asof, recs, ctb_rows, p6_rows, w_rows, inputs = load_inputs(asof, **paths)
    fall_max = facts["fall_max"]
    dstates, runs = {}, []
    for rec in sorted(recs, key=lambda r: str(r.get("ts", ""))):
        c = {}
        for row in PF._rows(rec):
            k = decision_state(row, rec.get("borrow_max"))
            c[k] = c.get(k, 0) + 1
            dstates[k] = dstates.get(k, 0) + 1
        runs.append({"date": rec.get("date"), "source": rec.get("source"), "run_id": rec.get("run_id"),
                     "decision_session": decision_session(rec.get("ts")), "states": dict(sorted(c.items()))})
    obs = observations(recs, ctb_rows, p6_rows, w_rows)
    per = [classify(s, obs, asof, fall_max) for s in seeds(recs)]
    counts = {k: sum(1 for p in per if p["state"] == k) for k in STATES}
    tracking = {
        "registered_tracker": "borrow_watch.jsonl (harvest_borrow_watch · up to "
                              f"{facts['cap']} ChartExchange lookups per daily run for due symbols)",
        "persisted": bool(facts["persisted_by_git_save"] or facts["persisted_by_artifact"]),
        "present_in_repo": inputs["borrow_watch"]["present"],
        "track_rows": sum(1 for r in w_rows if r.get("kind") == "track"),
    }
    if not tracking["persisted"]:
        failure = ("TRACKING_NEVER_PERSISTED: the harvester appends to borrow_watch.jsonl on the runner, but no git_save list and no "
                   "workflow artifact carries it, so every daily run starts from an empty log ⟶ no symbol is ever due ⟶ zero "
                   "tracking lookups ⟶ zero registered follow-up observations")
    elif not tracking["track_rows"]:
        failure = "TRACKING_PERSISTED_BUT_EMPTY: no track rows recorded yet"
    else:
        failure = None
    smaller = min(counts["A_FELL_BELOW"], counts["B_FULL"])
    gates = {
        "W1_wired": ("WIRED_DAILY_ONLY" if facts["harvest_called_from"] == ["run_daily_watchlist"]
                     else ("WIRED:" + ",".join(facts["harvest_called_from"]) if facts["harvest_called_from"] else "NOT_WIRED")),
        "W2_unknown_not_zero": "ENFORCED_HERE (UNKNOWN is an attempt, never a value)",
        "W3_coverage_printed": "YES (per seed: known_later · unknown_later · observed_days · sessions_elapsed)",
        "W4_sample": f"NOT_MET (smaller arm {smaller} of {SAMPLE_MIN})" if smaller < SAMPLE_MIN else "MET",
        "W5_no_selection_effect": "READ_ONLY (this tool) · production harvester: BF9 lock",
    }
    return {
        "schema": SCHEMA, "asof": asof, "window_sessions": WINDOW_SESSIONS, "fall_max": fall_max,
        "facts": facts, "inputs": inputs, "tracking": tracking, "failure_point": failure,
        "decision_states": dict(sorted(dstates.items())), "runs": runs,
        "seeds_n": len(per), "state_counts": counts, "seeds": per, "gates": gates,
        "verdict": "NO_VERDICT", "verdict_reason": "BLIND — outcomes are not computed before W4; " + (failure or "sample not met"),
    }


def render(doc):
    c, f, t = doc["state_counts"], doc["facts"], doc["tracking"]
    L = ["# 🔒📉 T-BORROW-FALL — evidence status (not a result)", "",
         "> Generated by `borrow_fall_report.py` from persisted inputs — **do not edit by hand**; `--check` rebuilds and compares.",
         "> No outcome rate is computed here (prereg §⑤ W4 · §⑥): **BLIND**. Zero external requests.", "",
         f"As of **{doc['asof']}** (UTC date) · window {doc['window_sessions']} sessions after the seed's decision session · "
         f"fall threshold «below {f['fall_max']:,}» (`FAISAL_ENTRY_AVAIL_MAX`).", "",
         "## 1. Where the registered evidence disappears", "",
         f"- Registered tracker: {t['registered_tracker']}.",
         f"- Persisted by `git_save`: **{f['persisted_by_git_save']}** · by a workflow artifact: **{f['persisted_by_artifact']}** · "
         f"file in the repository: **{t['present_in_repo']}** · track rows: **{t['track_rows']}**.",
         f"- Harvester called from: `{', '.join(f['harvest_called_from']) or '—'}` · its horizon in code counts "
         f"**{f['horizon_unit_in_code']}** ({f['horizon']}) while the prereg window is {doc['window_sessions']} sessions.",
         f"- **Failure point:** {doc['failure_point'] or 'none'}", "",
         "## 2. Decision-time availability states (every row of every persisted pool record)", "",
         "| state | rows |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in doc["decision_states"].items()]
    L += ["", "| run date | source | run | decision session | states |", "|---|---|---|---|---|"]
    L += [f"| {r['date']} | {r['source']} | {r['run_id']} | {r['decision_session']} | "
          + " · ".join(f"{k} {v}" for k, v in r["states"].items()) + " |" for r in doc["runs"]]
    L += ["", "## 3. Seeds (first ejection by the borrow gate) and their later observations", "",
          f"Seeds: **{doc['seeds_n']}** · " + " · ".join(f"{k} **{v}**" for k, v in c.items()), "",
          "| symbol | seed run date | session | availability at seed | window end | window | known later | unknown later | "
          "observed days / elapsed | sources | state |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in doc["seeds"]:
        L.append(f"| {p['symbol']} | {p['seed_date']} | {p['seed_session']} | "
                 f"{int(p['av_seed']):,} | {p['window_end']} | {p['window']} | {p['known_later']} | {p['unknown_later']} | "
                 f"{p['observed_days']} / {p['sessions_elapsed']} | {', '.join(p['sources']) or '—'} | {p['state']} |")
    g = doc["gates"]
    L += ["", "## 4. Validity gates (prereg §⑤)", ""] + [f"- **{k}:** {v}" for k, v in g.items()]
    L += ["", f"## 5. Verdict: **{doc['verdict']}** — {doc['verdict_reason']}", "",
          "- Arm B («never fell») needs a KNOWN observation on every trading day of a closed window; with the persisted sources the "
          "follow-up is sparse and rank-dependent, so NOT_BELOW_PARTIAL is reported separately and never counted as B.",
          "- The source's own as-of time (ChartExchange) is not recorded anywhere: `NOT_COLLECTED`, never replaced by collection time.",
          "", "## 6. Reproduce", "",
          "- `python3 borrow_fall_report.py --check` — rebuilds with the stored as-of from the same inputs and compares.", ""]
    return "\n".join(L)


def write(doc):
    with open(F_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    with open(F_MD, "w", encoding="utf-8") as fh:
        fh.write(render(doc))


def main(argv):
    if "--check" in argv:
        try:
            old = json.load(open(F_JSON, encoding="utf-8"))
        except (OSError, ValueError):
            print("check FAILED: no stored status")
            return 1
        doc = build(asof=old.get("asof"))
        ok = doc == old and render(doc) == open(F_MD, encoding="utf-8").read()
        print("check OK" if ok else "check FAILED: rebuilt status differs from the stored one")
        return 0 if ok else 1
    asof = argv[argv.index("--asof") + 1] if "--asof" in argv else None
    doc = build(asof=asof)
    write(doc)
    print(f"built {PF._rel(F_JSON)} · {PF._rel(F_MD)} · asof {doc['asof']} · seeds {doc['seeds_n']} · {doc['state_counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
