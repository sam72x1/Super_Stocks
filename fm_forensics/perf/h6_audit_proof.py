# -*- coding: utf-8 -*-
"""H6 collection audit (2026-10-15) — reproducible proof of the two instrument defects and of the proposed fixes.

Read-only: nothing is written, nothing is fetched, no production module is changed. Each proposed fix is applied **in memory**
to a copy of the function's source, its lock is run against it, and the lock is run again against a mutation of the fix
(it must fail). Exit 0 only if every expectation below holds.

  python3 fm_forensics/perf/h6_audit_proof.py

D1 control pool frozen: `reject_log.json` stores at most REJECT_LOG_MAX_SYMS (400) symbols per wall; the anchor wall
   `M_لا_مستوى_مختبر` exceeds it from 2026-10-09 (407 → 432) and is written `sampled`; `collector.control_pool` refuses a
   sampled wall (contract §4) ⟶ every panel since falls back to the 2026-10-08 pool — and `h6_test status` reports
   `no_pool_days 0` (healthy).
D2 sessions counted on weekends: `h6_test.is_session` = `market_calendar.is_trading_day`, whose docstring says it does not
   check weekends ⟶ E5 «5 sessions» and E4 «30 sessions» are counted in calendar days.
"""
import json
import os
import random
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [ROOT, HERE, os.path.join(ROOT, "fm_forensics", "phase6")]
os.environ.setdefault("FAISAL_ONLY", "1")
WALL = "M_لا_مستوى_مختبر"
RESULTS = []


def ok(name, cond, why=""):
    RESULTS.append(bool(cond))
    print(("✅ " if cond else "❌ ") + name + ("" if cond else f" — {why}"))


def _compile(fn_src, globs, name):
    ns = {}
    exec(compile(textwrap.dedent(fn_src), f"<{name}>", "exec"), dict(globs), ns)
    return ns[name]


# ── D1 ─────────────────────────────────────────────────────────────────────────────────────────────
def d1():
    import inspect
    import Super_stock as S
    import collector as C
    rl = json.load(open(os.path.join(ROOT, "reject_log.json"), encoding="utf-8"))
    ents = [e for e in rl if isinstance(e, dict) and "walls" in e]
    newest = max(e["date"] for e in ents)
    pool_date, pool = C.control_pool(rl, newest)
    lag = [e["date"] for e in ents if pool_date < e["date"] <= newest]
    tail = [(e["date"], len(e["walls"].get(WALL) or []), (e.get("walls_n") or {}).get(WALL), WALL in (e.get("sampled") or []))
            for e in ents if e["date"] > pool_date]
    print(f"   newest entry {newest} · pool chosen {pool_date} ({len(pool)}) · newer entries refused {lag}")
    print(f"   anchor wall after the pool: {tail}")
    ok("D1-a the anchor wall is sampled in every entry after the pool, and the panel pool lags the newest entry",
       bool(lag) and all(s for *_, s in tail) and all(n > S.REJECT_LOG_MAX_SYMS for _, _, n, _ in tail), tail)
    panel = [json.loads(x) for x in open(os.path.join(ROOT, "fm_forensics", "phase6", "data", "PHASE6_CONTROL_PANEL.jsonl"),
                                         encoding="utf-8") if x.strip()]
    pds = [(p["obs_date"], p["pool_date"], p["status"]) for p in panel]
    print(f"   panel lines: {pds}")
    ok("D1-b every panel line since 2026-10-09 is OK and drawn from the 2026-10-08 pool",
       pds and all(pd == "2026-10-08" and st == "OK" for _, pd, st in pds), pds)
    import h6_test as H
    st = H.build_status(today=newest)[0]
    ok("D1-c and `h6_test status` reports the panel healthy (no_pool_days 0 · no pool date or lag field)",
       st["panel"]["no_pool_days"] == 0 and not any("pool" in k and k != "no_pool_days" for k in st["panel"]), st["panel"])

    # proposed fix F1: store the control wall in full (the other walls keep the cap and its sample, bit-identical)
    src = inspect.getsource(S.build_reject_snapshot)
    old_sig = "cap: int = REJECT_LOG_MAX_SYMS) -> dict:"
    new_sig = "cap: int = REJECT_LOG_MAX_SYMS, full_walls=(\"M_لا_مستوى_مختبر\",)) -> dict:"
    old_cut = "        if len(syms) <= cap:\n"
    new_cut = "        if len(syms) <= cap or key in full_walls:\n"
    ok("F1 anchors exist once in build_reject_snapshot", src.count(old_sig) == 1 and src.count(old_cut) == 1)
    fixed = _compile(src.replace(old_sig, new_sig).replace(old_cut, new_cut), vars(S), "build_reject_snapshot")
    mutant = _compile(src.replace(old_sig, new_sig.replace('("M_لا_مستوى_مختبر",)', "()")).replace(old_cut, new_cut), vars(S),
                      "build_reject_snapshot")

    def lock_h6p1(fn):
        """The proposed suite lock H6P1."""
        rnd = random.Random(20261015)
        good = True
        for w in range(300):
            n_a, n_b = rnd.randint(0, 900), rnd.randint(0, 900)
            reasons = {f"A{i:04d}": WALL for i in range(n_a)}
            reasons.update({f"B{i:04d}": "M5_سيولة" for i in range(n_b)})
            day = f"2026-10-{(w % 28) + 1:02d}"
            new, old = fn(reasons, day), S.build_reject_snapshot(reasons, day)
            others_same = ({k: v for k, v in new["walls"].items() if k != WALL} == {k: v for k, v in old["walls"].items() if k != WALL}
                           and [k for k in new["sampled"] if k != WALL] == [k for k in old["sampled"] if k != WALL])
            full = (new["walls"].get(WALL, []) == sorted(s for s, c in reasons.items() if c == WALL) and WALL not in new["sampled"]
                    and new["walls_n"] == old["walls_n"])
            picked = C.control_pool([{"date": "2026-10-08", "walls": {WALL: ["X"]}, "walls_n": {WALL: 1}, "sampled": []}, new], day)
            fresh = (picked[0] == day) if n_a else True
            good = good and others_same and full and fresh
        off = all(fn({f"A{i}": WALL for i in range(k)}, "2026-10-09", full_walls=()) == S.build_reject_snapshot(
            {f"A{i}": WALL for i in range(k)}, "2026-10-09") for k in (0, 10, 400, 401, 432, 900))
        return good and off
    ok("F1 lock H6P1 passes on the fix (300 worlds: control wall in full · others bit-identical · today's pool picked · switch off = bit-identical)",
       lock_h6p1(fixed))
    ok("F1 lock H6P1 fails on the mutation (exemption list emptied)", not lock_h6p1(mutant))
    ok("F1 lock H6P1 fails on the current production function (the defect)", not lock_h6p1(
        lambda r, d, full_walls=None: S.build_reject_snapshot(r, d)))


# ── D2 ─────────────────────────────────────────────────────────────────────────────────────────────
def d2():
    import inspect
    import h6_test as H
    print(f"   is_session 2026-10-10 (Sat) = {H.is_session('2026-10-10')} · add_sessions(2026-10-09, 5) = {H.add_sessions('2026-10-09', 5)} "
          f"· sessions_between(2026-10-09, 2026-10-16) = {H.sessions_between('2026-10-09', '2026-10-16')}")
    ok("D2-a the tool counts a Saturday and a Sunday as sessions",
       H.is_session("2026-10-10") and H.is_session("2026-10-11"))
    src = inspect.getsource(H.is_session)
    old = "        return bool(MC.is_trading_day(d))\n"
    new = "        return dt.date.fromisoformat(d).weekday() < 5 and bool(MC.is_trading_day(d))\n"
    ok("F2 anchor exists once in is_session", src.count(old) == 1)
    g = vars(H)
    fixed_is = _compile(src.replace(old, new), g, "is_session")
    mutant_is = _compile(src.replace(old, "        return bool(MC.is_trading_day(d)) or dt.date.fromisoformat(d).weekday() < 5\n"), g, "is_session")

    def with_is(fn, f):
        keep = H.is_session
        H.is_session = fn
        try:
            return f()
        finally:
            H.is_session = keep

    def lock_h6s1(fn):
        """The proposed suite lock H6S1 (weekends · a holiday · E5's +5 sessions · E4's 30 sessions)."""
        return with_is(fn, lambda: (not H.is_session("2026-10-10") and not H.is_session("2026-10-11")
                                    and not H.is_session("2026-11-26") and H.is_session("2026-10-12")
                                    and H.add_sessions("2026-10-09", 5) == "2026-10-16"
                                    and H.add_sessions("2026-11-25", 1) == "2026-11-27"
                                    and H.sessions_between("2026-10-09", "2026-10-16") == 5
                                    and H.sessions_between("2026-08-28", "2026-10-09") == 29))
    ok("F2 lock H6S1 passes on the fix", lock_h6s1(fixed_is))
    ok("F2 lock H6S1 fails on the mutation (weekday rule as an OR)", not lock_h6s1(mutant_is))
    ok("F2 lock H6S1 fails on the current tool (the defect)", not lock_h6s1(H.is_session))
    cur = json.dumps(H.build_status(today="2026-10-15")[0], sort_keys=True)
    fx = with_is(fixed_is, lambda: json.dumps(H.build_status(today="2026-10-15")[0], sort_keys=True))
    ok("F2 the fix leaves today's status bit-identical (no unit exists yet ⟹ nothing counted changes)", cur == fx)


if __name__ == "__main__":
    print("D1 · control pool")
    d1()
    print("D2 · session arithmetic")
    d2()
    print(("✅ all" if all(RESULTS) else "❌ failed") + f" ({sum(RESULTS)}/{len(RESULTS)})")
    sys.exit(0 if all(RESULTS) else 1)
