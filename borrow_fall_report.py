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
from zoneinfo import ZoneInfo  # noqa: E402
import market_calendar as MC  # noqa: E402

F_POOL = os.path.join(HERE, "faisal_engine", "data", "pool_funnel_frozen.jsonl")
F_CTB = os.path.join(HERE, "ctb_log.jsonl")
F_P6 = os.path.join(HERE, "fm_forensics", "phase6", "data", "PHASE6_LEDGER.jsonl")
F_WATCH = os.path.join(HERE, "borrow_watch.jsonl")
F_BOT = os.path.join(HERE, "Super_stock.py")
F_WF = os.path.join(HERE, ".github", "workflows", "daily_screener.yml")
F_JSON = os.path.join(HERE, "borrow_fall_status.json")
F_MD = os.path.join(HERE, "borrow_fall_status.md")
SCHEMA = 2
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


# ───────────────────────── time (every time field read with the semantics of the code that writes it)
# Writers (verified in the code, 2026-10-10): pool `date` = `dt.date.today()` on the runner and `ts`/`snap_ts` = UTC instants
# (`Super_stock.fill_pool_record`/`fill_pool_begin`); `ctb_log` `date` = `dt.date.today()` (`ctb_harvest.harvest`); Phase6
# `collected_utc` = the collector's start instant (`Collector.__init__`); `borrow_watch` `date` = the screen's `today_iso`. No workflow
# sets TZ, and the bot's own log clock matches the Actions UTC stamps, so a bare date is a UTC calendar day — never a New York session.
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
DAY = dt.timedelta(days=1)
EPS = dt.timedelta(microseconds=1)
PHASE6_MAX_LAG = dt.timedelta(minutes=40)   # `fm_phase6_collect.yml` timeout-minutes: 40 ⟶ a row is fetched within 40 min of collected_utc
TIME_SEMANTICS = {
    "pool": "UTC interval [snap_ts, ts] of the screening run that fetched the availability (both recorded)",
    "ctb_log": "UTC calendar day of the harvest run (dt.date.today() on the runner) — time of day not recorded",
    "phase6": f"UTC interval [collected_utc, collected_utc + {int(PHASE6_MAX_LAG.total_seconds() // 60)} min] (collector start + job timeout)",
    "borrow_watch": "UTC calendar day of the screening run (today_iso) — time of day not recorded",
    "source_asof": "NOT_COLLECTED — the time ChartExchange/IBKR published the value is recorded nowhere; never replaced by fetch time",
}


def _utc(s):
    """Aware UTC datetime from an ISO string; None for a missing or naive value (a time without a zone is not guessed)."""
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t.astimezone(UTC) if t.tzinfo is not None else None


def _day(date_iso):
    """The UTC calendar day `date_iso` as the interval [00:00, 24:00) UTC."""
    try:
        d = dt.date.fromisoformat(str(date_iso)[:10])
    except ValueError:
        return None, None
    lo = dt.datetime(d.year, d.month, d.day, tzinfo=UTC)
    return lo, lo + DAY - EPS


def _trading(d):
    return d.weekday() < 5 and not (d.isoformat() in MC.HOLIDAYS)


def session_close_utc(session_iso):
    """The UTC instant a session closes — New York close minute from `market_calendar` (early closes included) and the DST rule
    of the date (zoneinfo)."""
    d = dt.date.fromisoformat(session_iso)
    close = MC.session_info(session_iso).get("close_ny_min") or MC.REGULAR_CLOSE_NY_MIN
    return dt.datetime(d.year, d.month, d.day, close // 60, close % 60, tzinfo=NY).astimezone(UTC)


def decision_session(ts_utc):
    """The last session whose close is at or before `ts_utc` — the last session a decision at that instant could see."""
    t = _utc(ts_utc).astimezone(NY)
    d = t.date()
    if _trading(d):
        close = MC.session_info(d.isoformat()).get("close_ny_min")
        if close is not None and t.hour * 60 + t.minute >= close:
            return d.isoformat()
    d -= DAY
    while not _trading(d):
        d -= DAY
    return d.isoformat()


def sessions_after(session_iso, n):
    """The `n` trading days strictly after `session_iso` (weekends · `market_calendar.HOLIDAYS`)."""
    d, out = dt.date.fromisoformat(session_iso), []
    while len(out) < n:
        d += DAY
        if _trading(d):
            out.append(d.isoformat())
    return out


def window_bounds(session_iso, dec_ts):
    """Window = (decision instant, close of session 40]; session k covers (close of k-1, close of k] — the first one starts at the
    decision instant. Returns (sessions, bounds) with len(bounds) == len(sessions) + 1."""
    sess = sessions_after(session_iso, WINDOW_SESSIONS)
    return sess, [_utc(dec_ts)] + [session_close_utc(s) for s in sess]


def attribute(session_iso, dec_ts, lo, hi=None):
    """The window session an observation interval [lo, hi] belongs to: a session date · "BEFORE" (it may precede or meet the
    decision) · "AFTER" (wholly after the close of session 40) · None (it spans a session boundary — ambiguous)."""
    lo = _utc(lo) if isinstance(lo, str) else lo
    hi = lo if hi is None else (_utc(hi) if isinstance(hi, str) else hi)
    sess, b = window_bounds(session_iso, dec_ts)
    if lo <= b[0]:
        return "BEFORE"
    if lo > b[-1]:
        return "AFTER"
    for k, s in enumerate(sess, 1):
        if b[k - 1] < lo and hi <= b[k]:
            return s
    return None


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
    # As-of = the latest frozen pool record's UTC date (frozen copies change only by an explicit `--freeze`, so the build is stable).
    # Seeds: records dated up to the as-of day. Evidence: rows dated strictly BEFORE it — the horizon is 00:00 UTC of the as-of day, a
    # day still being appended to is never read, and a later same-day append cannot change a committed status.
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
def observations(recs, ctb_rows, p6_rows, w_rows, horizon_date=None):
    """Every availability reading as (symbol, date_field, value_or_None, source, ts, snap_ts). Value None = UNKNOWN attempt.
    Rows that were never attempted (pool NOT_COLLECTED · phase6 NOT_ATTEMPTED) are not observations at all. Pool records serve as
    evidence only when dated before the horizon day (`horizon_date`); later-dated ones are seeds only."""
    out = []
    for rec in recs:
        if horizon_date is not None and str(rec.get("date", "")) >= horizon_date:
            continue
        for row in PF._rows(rec):
            st = row.get("av_state")
            if st == "KNOWN":
                out.append((row.get("sym"), rec.get("date"), _num(row.get("av")), "pool", rec.get("ts"), rec.get("snap_ts")))
            elif st == "UNKNOWN":
                out.append((row.get("sym"), rec.get("date"), None, "pool", rec.get("ts"), rec.get("snap_ts")))
    for r in ctb_rows:
        out.append((r.get("symbol"), r.get("date"), _num(r.get("shares_available")), "ctb_log", None, None))
    for r in p6_rows:
        if r.get("status") == "NOT_ATTEMPTED":
            continue
        v = _num(r.get("value")) if r.get("status") == "OK" else None
        out.append((r.get("ticker"), str(r.get("collected_utc", ""))[:10], v, "phase6", r.get("collected_utc"), None))
    for r in w_rows:
        if r.get("kind") == "track":
            out.append((r.get("symbol"), r.get("date"), _num(r.get("available")), "borrow_watch", None, None))
    return [o for o in out if o[0] and o[1]]


def obs_interval(o):
    """[lo, hi] UTC for an observation tuple, by its source's time semantics (`TIME_SEMANTICS`); (None, None) if unreadable."""
    src, ts = o[3], (o[4] if len(o) > 4 else None)
    snap = o[5] if len(o) > 5 else None
    if ts:
        t = _utc(ts)
        if t is None:
            return None, None
        if src == "pool":
            s0 = _utc(snap) if snap else None
            return (s0 if s0 is not None and s0 <= t else t), t
        if src == "phase6":
            return t, t + PHASE6_MAX_LAG
        return t, t
    return _day(o[1])


def seeds(recs):
    """First BORROW_REJECT per symbol (records in time order) — the registered population."""
    first = {}
    for rec in sorted(recs, key=lambda r: (str(r.get("ts", "")), str(r.get("key", "")))):
        for row in PF._rows(rec):
            if row.get("outcome") != "BORROW_REJECT" or row.get("av_state") != "KNOWN":
                continue
            s = row.get("sym")
            if s and s not in first:
                first[s] = {"symbol": s, "seed_date": rec.get("date"), "seed_ts": rec.get("ts"), "seed_snap_ts": rec.get("snap_ts"),
                            "source": rec.get("source"), "run_id": rec.get("run_id"), "gate_max": rec.get("borrow_max"),
                            "av_seed": _num(row.get("av"))}
    return [first[k] for k in sorted(first)]


def classify(seed, obs, asof, fall_max):
    """Relation of every observation of the seed's symbol to its window, by instants (never by comparing a UTC date with a session
    date): BEFORE · ORDER_AMBIGUOUS (may precede or meet the decision) · IN · WINDOW_AMBIGUOUS (may fall after the close of session
    40) · AFTER. Only IN observations count; an IN observation is attributed to one session or, if it spans a boundary, to none.
    The horizon is 00:00 UTC of the as-of day: a session counts as elapsed only once its close is at or before it."""
    dec_hi = _utc(seed["seed_ts"])
    dec_lo = _utc(seed.get("seed_snap_ts")) or dec_hi
    dec_lo = dec_lo if dec_lo <= dec_hi else dec_hi
    sess = decision_session(seed["seed_ts"])
    sess_lo = decision_session(dec_lo.isoformat())
    win, b = window_bounds(sess, seed["seed_ts"])
    end = b[-1]
    horizon = _day(asof)[0]
    rel = {"BEFORE": 0, "ORDER_AMBIGUOUS": 0, "WINDOW_AMBIGUOUS": 0, "AFTER": 0}
    known, unknown, listed, covered = [], [], [], set()
    for o in obs:
        if o[0] != seed["symbol"]:
            continue
        if o[3] == "pool" and len(o) > 4 and o[4] == seed["seed_ts"]:
            continue                                   # the seed's own record: known-at-decision, not a follow-up
        lo, hi = obs_interval(o)
        if lo is None:
            continue
        if hi < dec_lo:
            r = "BEFORE"
        elif lo <= dec_hi:
            r = "ORDER_AMBIGUOUS"
        elif hi <= end:
            r = "IN"
        elif lo > end:
            r = "AFTER"
        else:
            r = "WINDOW_AMBIGUOUS"
        s_att = None
        if r == "IN":
            s_att = next((s for k, s in enumerate(win, 1) if b[k - 1] < lo and hi <= b[k]), None)
            (known if o[2] is not None else unknown).append((hi, o[3], o[1], o[2], s_att))
            if o[2] is not None and s_att:
                covered.add(s_att)
        else:
            rel[r] += 1
        if r != "BEFORE":
            listed.append({"source": o[3], "date_field": o[1], "time": "INSTANT" if (len(o) > 4 and o[4]) else "UTC_DAY",
                           "lo_utc": lo.isoformat(), "hi_utc": hi.isoformat(),
                           "value": "UNKNOWN" if o[2] is None else o[2], "relation": r, "session": s_att})
    known.sort(key=lambda x: (x[0], x[1]))
    below = [k for k in known if fall_max is not None and k[3] < float(fall_max)]
    closed = end <= horizon
    if below:
        state = "A_FELL_BELOW"
    elif known:
        state = "B_FULL" if (closed and len(covered) == len(win)) else "NOT_BELOW_PARTIAL"
    else:
        state = "NO_FOLLOWUP_UNKNOWN_ONLY" if unknown else "NO_FOLLOWUP_NONE"
    return {**seed, "decision_session": sess, "decision_session_ambiguous": sess_lo != sess,
            "first_session": win[0], "window_end": win[-1], "window_end_close_utc": end.isoformat(),
            "horizon_utc": horizon.isoformat(), "window": "CLOSED" if closed else "OPEN",
            "sessions_elapsed": sum(1 for x in b[1:] if x <= horizon),
            "calendar_beyond": any(MC.beyond_calendar(s) for s in win),
            "known_later": len(known), "unknown_later": len(unknown), "order_ambiguous": rel["ORDER_AMBIGUOUS"],
            "window_ambiguous": rel["WINDOW_AMBIGUOUS"], "after_window": rel["AFTER"], "before_decision": rel["BEFORE"],
            "observed_sessions": len(covered), "unattributed_known": sum(1 for k in known if not k[4]),
            "sources": sorted({k[1] for k in known}), "first_below_date": below[0][2] if below else None,
            "first_below_session": below[0][4] if below else None, "first_below_source": below[0][1] if below else None,
            "observations": listed, "source_asof": "NOT_COLLECTED", "state": state}


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
                     "ts": rec.get("ts"), "decision_session": decision_session(rec.get("ts")),
                     "states": dict(sorted(c.items()))})
    obs = observations(recs, ctb_rows, p6_rows, w_rows, horizon_date=asof)
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
        "W3_coverage_printed": "YES (per seed: known/unknown in window · ambiguous · after · observed sessions / elapsed sessions)",
        "W4_sample": f"NOT_MET (smaller arm {smaller} of {SAMPLE_MIN})" if smaller < SAMPLE_MIN else "MET",
        "W5_no_selection_effect": "READ_ONLY (this tool) · production harvester: BF9 lock",
    }
    return {
        "schema": SCHEMA, "asof": asof, "horizon_utc": _day(asof)[0].isoformat(), "window_sessions": WINDOW_SESSIONS,
        "fall_max": fall_max, "time_semantics": TIME_SEMANTICS,
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
         f"As of **{doc['asof']}** (UTC date) · evidence horizon **{doc['horizon_utc']}** (rows dated before the as-of day) · window = "
         f"(decision instant, close of session {doc['window_sessions']}] in New York sessions · fall threshold «below {f['fall_max']:,}» "
         "(`FAISAL_ENTRY_AVAIL_MAX`).", "",
         "**Time semantics of each source** (from the code that writes it — a bare date is a UTC day, never a New York session):", ""]
    L += [f"- `{k}`: {v}" for k, v in doc["time_semantics"].items()]
    L += ["",
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
          "| symbol | decision (UTC) | decision session | availability at seed | first → last session (close UTC) | window | "
          "elapsed | known in / unknown in | ambiguous order · window · after | observed sessions | sources | state |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in doc["seeds"]:
        L.append(f"| {p['symbol']} | {p['seed_ts']} | {p['decision_session']}{' ⚠️' if p['decision_session_ambiguous'] else ''} | "
                 f"{int(p['av_seed']):,} | {p['first_session']} → {p['window_end']} ({p['window_end_close_utc'][11:16]}Z) | "
                 f"{p['window']}{' ⚠️calendar' if p['calendar_beyond'] else ''} | {p['sessions_elapsed']} / {doc['window_sessions']} | "
                 f"{p['known_later']} / {p['unknown_later']} | {p['order_ambiguous']} · {p['window_ambiguous']} · {p['after_window']} | "
                 f"{p['observed_sessions']} | {', '.join(p['sources']) or '—'} | {p['state']} |")
    obs_rows = [(p["symbol"], o) for p in doc["seeds"] for o in p["observations"]]
    L += ["", f"Observations after the decision (any relation): **{len(obs_rows)}**" + ("" if obs_rows else " — none persisted."), ""]
    if obs_rows:
        L += ["| symbol | source | date field | time | interval UTC | value | relation | session |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {s} | {o['source']} | {o['date_field']} | {o['time']} | {o['lo_utc'][:16]} → {o['hi_utc'][:16]} | {o['value']} | "
              f"{o['relation']} | {o['session'] or '—'} |" for s, o in obs_rows]
    g = doc["gates"]
    L += ["", "## 4. Validity gates (prereg §⑤)", ""] + [f"- **{k}:** {v}" for k, v in g.items()]
    L += ["", f"## 5. Verdict: **{doc['verdict']}** — {doc['verdict_reason']}", "",
          "- Arm B («never fell») needs a KNOWN observation attributed to every session of a closed window; with the persisted sources "
          "the follow-up is sparse and rank-dependent, so NOT_BELOW_PARTIAL is reported separately and never counted as B. Missing "
          "observations are never read as «did not fall».",
          "- A UTC-day observation (no time of day) spans a session close, so it is never attributed to one session; on the last day of "
          "a window it is WINDOW_AMBIGUOUS and counted, not used. A session counts as elapsed only once its close is at or before the "
          "horizon.",
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
