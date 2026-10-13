"""T-HEAT — does pre-move heat separate the movers from matched controls INSIDE the bot's tracked population?
(research only · contract: T_HEAT_prereg.md, SHA-256 pinned below and checked before any read; changed ⇒ exit 9)

The two traits are T-LINK100's, called BY NAME (link100_probe.daily_feats, source pinned):
  VOLX3  vol_x ≥ 3   — volume of the decision day ÷ median volume of the 15 sessions t−19 … t−5
  RET5   ret5 > +20% — close[t] ÷ close[t−5] − 1 (the published bucket ">+20%", i.e. ≥ 0.20)
measured on decision days t whose bars end at t (the next open is the earliest action), on the frozen TradingView
archive (faisal_engine/data/rank/bars.json.gz · split-adjusted), in the window that ENDS K_GAP sessions before the anchor.

Anchors (both governing · the verdict is the weakest):
  O  onset — the first extended move (gen5_ext rule: pre/regular high ≥ 1.5 × prior close · after-hours ≥ 1.5 × own close ·
     highest price ≥ 1.7 × running minimum close) after a 20-session rule-free window, walked back from E*; the event must
     still reach 2 × close[O−1] (extended) within [O, O+20]. Controls get the SAME rule-free window (symmetric).
  B  E* — GEN5 addendum 1 anchor B (first session the extended price reaches 2 × close[E_reg−1]) · no window condition on
     either side (as the owner wrote it) · leaky by construction, so it can only LOWER the verdict.
Controls: same near-watch population, same anchor day, matched on rejection wall · price band · float band (GEN5 pick_controls),
that did NOT reach 2 × close[A−1] (extended) within [A, A+20]; those that moved ≥ 50 % / 70 % without the 2 × are kept and counted.

    python3 fm_forensics/heat/heat_test.py --guards   # synthetic guards only (no test-population read)
    python3 fm_forensics/heat/heat_test.py            # the sealed run (writes data/heat_result.json · data/heat_units.csv)
"""
import csv
import datetime as dt
import hashlib
import inspect
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN5 = os.path.join(ROOT, "fm_forensics", "gen5")
for _p in (GEN5, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import gen5_features as G   # noqa: E402
import gen5_pit as PIT      # noqa: E402
import gen5_test as T       # noqa: E402
import gen5_ext as X        # noqa: E402
import gen5_fix as F        # noqa: E402
import link100_probe as L   # noqa: E402

PREREG = os.path.join(HERE, "T_HEAT_prereg.md")
PREREG_SHA256 = "f3c68baadb4a1b9dd857a94c88e845bfe352dccd16a58da4ca37d55ea5ff6cb5"
DAILY_FEATS_SHA256 = "13f555f1c34c70b441e5440c8e04dac922f7368dbacfd6cd69bfc09e4a0a7d57"  # sha256 of inspect.getsource(L.daily_feats) + inspect.getsource(L._bucket)
OUT = os.path.join(HERE, "data", "heat_result.json")
UNITS_CSV = os.path.join(HERE, "data", "heat_units.csv")

K_GAP = 2                              # the window ends K_GAP sessions before the anchor (fixed before any number)
W_GOV = 5                              # governing window: decision days A−6 … A−2 (one trading week)
LEAD_MAX = 20                          # descriptive: single-day profile and the 19-day window A−20 … A−2
GOV_LEADS = tuple(range(K_GAP, K_GAP + W_GOV))
W19_LEADS = tuple(range(K_GAP, LEAD_MAX + 1))
RULE_WIN = 20                          # the rule-free window before an onset (= gen5 control window length)
HORIZON = 20                           # forward window [A, A+20]
TRAITS = ("VOLX3", "RET5", "UNION", "INTERSECT")
GOVERNING = "UNION"
MDE_MAX = 0.25                         # design MDE80 above this ⇒ «لا قياس» (primary readings only)
LAB_VX, LAB_R5 = "≥3", ">+20%"         # the published T-LINK100 buckets
ORDER = {"D": 0, "C": 1, "A0": 2, "A": 3}


# ── pins ─────────────────────────────────────────────────────────────────────────────────────────────
def daily_feats_sha():
    return hashlib.sha256((inspect.getsource(L.daily_feats) + inspect.getsource(L._bucket)).encode()).hexdigest()


def check_pins(prereg=PREREG, prereg_sha=None):
    """Contract, the T-LINK100 trait source and every GEN5 pin must match before any read; otherwise exit 9."""
    want = PREREG_SHA256 if prereg_sha is None else prereg_sha
    got = hashlib.sha256(open(prereg, "rb").read()).hexdigest() if os.path.exists(prereg) else None
    if got != want:
        print(f"⛔ contract changed or not pinned: {got} ≠ {want}")
        sys.exit(9)
    if daily_feats_sha() != DAILY_FEATS_SHA256:
        print(f"⛔ link100_probe.daily_feats changed: {daily_feats_sha()} ≠ {DAILY_FEATS_SHA256}")
        sys.exit(9)
    F.check_pins()


def _main_contract():
    """The contract as origin/main carries it (bytes), or None — read with `git show`, no network."""
    import subprocess
    rel = os.path.relpath(PREREG, ROOT).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def check_merged(read=None):
    """The owner's rule «merged into main before any number»: origin/main must carry the pinned contract, else exit 9."""
    blob = (read or _main_contract)()
    got = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if got != PREREG_SHA256:
        print(f"⛔ the pinned contract is not on origin/main ({got}) — merge it before any number (git fetch --force first)")
        sys.exit(9)


# ── pure helpers (guarded) ───────────────────────────────────────────────────────────────────────────
def tri_or(a, b):
    if a is True or b is True:
        return True
    if a is False and b is False:
        return False
    return None


def tri_and(a, b):
    if a is False or b is False:
        return False
    if a is True and b is True:
        return True
    return None


def day_traits(hist, t):
    """Traits at decision day t from hist[0 .. t] only — link100_probe.daily_feats(hist, t+1) reads hist[:t+1]."""
    if t < 0 or t >= len(hist):
        return {"VOLX3": None, "RET5": None}
    f = L.daily_feats(hist, t + 1, False)
    if not f:
        return {"VOLX3": None, "RET5": None}
    vx, r5 = f.get("vol_x"), f.get("ret5")
    return {"VOLX3": (vx == LAB_VX) if vx is not None else None,
            "RET5": (r5 == LAB_R5) if r5 is not None else None}


def window_eval(day_flags, leads):
    """day_flags: {lead: {VOLX3, RET5}} ⟶ ({trait: True/False/None}, {trait: earliest lead | None}).
    A trait fires if it is true on ≥ 1 day of the window; it is unknown only when every day is unknown.
    UNION = VOLX3 ∨ RET5 · INTERSECT = VOLX3 ∧ RET5 (both inside the window), three-valued."""
    out, lead = {}, {}
    for tr in ("VOLX3", "RET5"):
        vals = [(ld, (day_flags.get(ld) or {}).get(tr)) for ld in leads]
        fired = [ld for ld, v in vals if v is True]
        known = any(v is not None for _, v in vals)
        out[tr] = True if fired else (False if known else None)
        lead[tr] = max(fired) if fired else None
    out["UNION"] = tri_or(out["VOLX3"], out["RET5"])
    out["INTERSECT"] = tri_and(out["VOLX3"], out["RET5"])
    lu = [x for x in (lead["VOLX3"], lead["RET5"]) if x is not None]
    lead["UNION"] = max(lu) if lu else None
    lead["INTERSECT"] = min(lead["VOLX3"], lead["RET5"]) if out["INTERSECT"] is True else None
    return out, lead


def as01(v):
    return None if v is None else int(bool(v))


def first_rule_day(rows, sess, cov_from, k, win=RULE_WIN):
    """Twin of gen5_ext.control_moved_ext(rows, sess, cov_from, k, win, ahead=0) that also says WHERE ⟶ (j | None, unknown):
    j = the first session in [k−win+1, k] where the extended move rule fires; unknown = a day before j (or in the whole
    window when j is None) lacked extended coverage. Equivalence with control_moved_ext is guard H2."""
    lo = max(1, k - win + 1)
    hi = min(len(rows) - 1, k)
    if lo > hi:
        return None, False
    run_min = float(rows[lo - 1][4])
    unknown = False
    for j in range(lo, hi + 1):
        d, h, c = rows[j][0], float(rows[j][2]), float(rows[j][4])
        prev = float(rows[j - 1][4])
        covered = sess is not None and cov_from is not None and d >= cov_from
        pr, _w, aft, known = X.day_ext(d, h, sess, covered)
        unknown = unknown or not known
        top = max(pr, aft) if aft is not None else pr
        if prev > 0 and pr / prev >= X.JUMP:
            return j, unknown
        if aft is not None and c > 0 and aft / c >= X.JUMP:
            return j, unknown
        if run_min > 0 and top / run_min >= X.RUN:
            return j, unknown
        if c < run_min:
            run_min = c
    return None, unknown


def window_clean(rows, sess, cov_from, a, win=RULE_WIN):
    """Is [a−win, a−1] free of the extended move rule? ⟶ True / False / None (window not fully inside the data, or a day
    without extended coverage and no firing)."""
    if a - win - 1 < 0:
        return None
    j, unk = first_rule_day(rows, sess, cov_from, a - 1, win)
    if j is not None:
        return False
    return None if unk else True


def onset(rows, sess, cov_from, e_idx, win=RULE_WIN):
    """Anchor O: start at E*, and while the win sessions before the current anchor contain a rule day, move the anchor to the
    FIRST such day. Stops when [O−win, O−1] is rule-free ⟶ (O, "OK"); a window not fully covered ⟶ (None, "UNKNOWN")."""
    o = e_idx
    for _ in range(len(rows) + 1):
        if o - win - 1 < 0:
            return None, "UNKNOWN"
        j, unk = first_rule_day(rows, sess, cov_from, o - 1, win)
        if j is None:
            return (None, "UNKNOWN") if unk else (o, "OK")
        o = j
    return None, "UNKNOWN"


def forward(rows, sess, cov_from, a, horizon=HORIZON):
    """Outcome after anchor index a: reached 2 × close[a−1] (extended) in [a, a+horizon]? complete coverage? sessions
    available? moved by the rule in [a, a+horizon] (running minimum from close[a−1])?"""
    if a < 1 or a >= len(rows):
        return None
    st = X.explosion_stats(rows, sess, cov_from, a - 1, a, horizon)
    if st is None:
        return None
    mv = X.control_moved_ext(rows, sess, cov_from, a, win=1, ahead=horizon)
    return {"reached": st["realized_idx"] is not None, "complete": st["complete"], "days": st["days"], "moved": mv}


def design_mde80(n_e, n_c):
    """Data-free MDE (80 % power, two-sided 5 %, p = 0.5 worst case, controls treated as independent) = 2.8 × SE."""
    if not n_e or not n_c:
        return None
    return round(2.8 * (0.25 / n_e + 0.25 / n_c) ** 0.5, 4)


def branch(b, mde_rule=True):
    if not b["floors_met"]:
        return "D"
    if mde_rule and (b["design_mde80"] is None or b["design_mde80"] > MDE_MAX):
        return "D"
    ci = b["traits"][GOVERNING]["delta"]["ci95"]
    if not ci or ci[0] <= 0:
        return "C"
    return "A"


def anchor_verdict(primary, identity):
    """Primary (floors + design-MDE rule) and identity sensitivity (floors only). An unmeasurable identity caps A at A0."""
    p = branch(primary, True)
    if p == "D":
        return "D"
    s = branch(identity, False)
    if s == "D":
        return "A0" if p == "A" else p
    return min((p, s), key=lambda x: ORDER[x])


def final_verdict(per_anchor):
    return min(per_anchor.values(), key=lambda v: ORDER[v])


def match_controls(pool, ev):
    """gen5_test.pick_controls keys its deterministic tie-break on ev['E'] = the anchor day (GEN5: E is the anchor). Here the
    anchor day is ev['A'] — passed as 'E' (post-seal crash fix 2026-10-13: the first run died on KeyError 'E', no number
    printed or written)."""
    return T.pick_controls(pool, {**ev, "E": ev["A"]})


def hist_rows(df):
    """Archive DataFrame ⟶ [[date, open, high, low, close, volume], …] (the T-LINK100 row shape)."""
    ix = df.index.strftime("%Y-%m-%d")
    return [[d, float(o), float(h), float(lo), float(c), float(v)]
            for d, o, h, lo, c, v in zip(ix, df["Open"], df["High"], df["Low"], df["Close"], df["Volume"])]


def unit_traits(hist, k_arch, splits):
    """All trait readings of one unit at archive index k_arch (the anchor). A reverse split not adjusted in the archive inside
    (A−26, A−K_GAP] makes every reading unknown (symmetric for events and controls)."""
    lo_i, hi_i = max(0, k_arch - (LEAD_MAX + 6)), k_arch - K_GAP
    bad = X.split_unadjusted(hist, splits, hist[lo_i][0], hist[hi_i][0]) if hi_i > lo_i else []
    days = {}
    for ld in W19_LEADS:
        days[ld] = {"VOLX3": None, "RET5": None} if bad else day_traits(hist, k_arch - ld)
    gov, gov_lead = window_eval(days, GOV_LEADS)
    w19, _ = window_eval(days, W19_LEADS)
    c1, c7 = hist[k_arch - 1][4], hist[k_arch - 7][4] if k_arch >= 7 else None
    return {"gov": gov, "gov_lead": gov_lead, "w19": w19, "days": days, "split_unadjusted": bad,
            "runup": round(c1 / c7 - 1.0, 4) if c7 and c7 > 0 else None}


def boot(units, key, comp):
    """gen5_test.boot_delta on the `key` reading (gov · w19) — symbol-clustered, 4,000 · seed 20261013."""
    view = [{"sym": u["sym"], "ev": u[key], "ctrl": u["ctrl_" + key]} for u in units]
    return T.boot_delta(view, comp)


def block(units):
    n_sym = len({u["sym"] for u in units})
    n_c = sum(len(u["ctrl_gov"]) for u in units)
    res = {"events": len(units), "symbols": n_sym, "control_draws": n_c,
           "floors_met": len(units) >= T.FLOORS["events"] and n_sym >= T.FLOORS["symbols"],
           "design_mde80": design_mde80(len(units), n_c), "traits": {}, "w19": {}}
    for tr in TRAITS:
        e = [u["gov"][tr] for u in units if u["gov"][tr] is not None]
        cr = [x[tr] for u in units for x in u["ctrl_gov"] if x.get(tr) is not None]
        leads = sorted(u["gov_lead"][tr] for u in units if u["gov_lead"][tr] is not None)
        pe = round(sum(e) / len(e), 4) if e else None
        pc = round(sum(cr) / len(cr), 4) if cr else None
        view = [{"sym": u["sym"], "ev": u["gov"], "ctrl": u["ctrl_gov"]} for u in units]
        res["traits"][tr] = {"p_events": pe, "n_events": len(e), "p_controls": pc, "n_controls": len(cr),
                             "delta": boot(units, "gov", tr) if units else {"point": None, "ci95": None},
                             "mde80_boot": F.mde80(view, tr) if units else None,
                             "lr": round(pe / pc, 3) if pe is not None and pc else None,
                             "lead_earliest_median": leads[len(leads) // 2] if leads else None}
        e19 = [u["w19"][tr] for u in units if u["w19"][tr] is not None]
        c19 = [x[tr] for u in units for x in u["ctrl_w19"] if x.get(tr) is not None]
        res["w19"][tr] = {"p_events": round(sum(e19) / len(e19), 4) if e19 else None,
                          "p_controls": round(sum(c19) / len(c19), 4) if c19 else None,
                          "delta": boot(units, "w19", tr) if units else {"point": None, "ci95": None}}
    return res


# ── data-side pieces (mirror gen5_fix.run_anchor; the differences are the ones the contract names) ───────────
def build_events(D, pop, stats, anchor):
    acc = {"rows": len(pop), "no_fresh_bars": [], "qa_unverified": [], "qa_unverifiable": [], "split_unadjusted": [],
           "onset_unknown": [], "not_2x_from_onset": [], "dup_merged": [], "beyond_archive": [], "short_history": []}
    ver = {}
    for i, r in enumerate(pop):
        s, st = r["SYMBOL"], stats[i]
        if st is None:
            acc["no_fresh_bars"].append((s, r["EXPL_DATE"]))
            continue
        if st["status"] != "VERIFIED":
            key = {"UNVERIFIED": "qa_unverified", "UNVERIFIABLE": "qa_unverifiable",
                   "SPLIT_UNADJUSTED": "split_unadjusted"}[st["status"]]
            acc[key].append((s, r["EXPL_DATE"]))
            continue
        rows = D.fresh[s]
        e_idx = D.fidx(s, st["realized_day"])
        sess, cov = D.ext_sess(s)
        if anchor == "B":
            a_idx = e_idx
        else:
            a_idx, status = onset(rows, sess, cov, e_idx)
            if status != "OK":
                acc["onset_unknown"].append((s, r["EXPL_DATE"]))
                continue
            fw = forward(rows, sess, cov, a_idx)
            if not fw or not fw["reached"]:
                acc["not_2x_from_onset"].append((s, r["EXPL_DATE"], rows[a_idx][0]))
                continue
        ver.setdefault(s, []).append({"row": r, "A": rows[a_idx][0], "E_star": st["realized_day"], "a_fresh": a_idx})
    events = []
    for s, rs in ver.items():
        keep, drop = T.dedupe(rs, lambda x: D.cix.get(x["A"], 10 ** 6))
        acc["dup_merged"] += [(x["row"]["SYMBOL"], x["row"]["EXPL_DATE"]) for x in drop]
        df = D.arch.get(s)
        ix = list(df.index.strftime("%Y-%m-%d")) if df is not None else []
        for x in keep:
            if x["A"] not in ix or x["A"] not in D.cix:
                acc["beyond_archive"].append((s, x["row"]["EXPL_DATE"], x["A"]))
                continue
            k = ix.index(x["A"])
            if k < T.HIST:
                acc["short_history"].append((s, x["row"]["EXPL_DATE"]))
                continue
            events.append({"sym": s, "A": x["A"], "E_reg": x["row"]["EXPL_DATE"], "E_star": x["E_star"], "k": k,
                           "a_fresh": x["a_fresh"], "identity": x["row"]["WAS_PIVOT_IDENTITY"] == "True"})
    return events, acc


def run_anchor(D, pop, stats, anchor, hist):
    nwh, rjh = hist
    events, acc = build_events(D, pop, stats, anchor)
    acc.update({"no_pool": [], "few_controls": [], "ctrl_no_fresh": 0, "ctrl_short_follow": 0, "ctrl_reached_2x": 0,
                "ctrl_forward_unknown": 0, "ctrl_window_moved": 0, "ctrl_window_unknown": 0})
    need = set()
    for ev in events:
        kk = D.cix[ev["A"]]
        for j in range(kk - T.WIN, kk):
            need.add(D.cal[j])
    nxt = {t: D.cal[D.cix[t] + 1] for t in need}
    pit = PIT.PIT(sorted(need), nxt)
    nw_at = {t: T.pre_open(nwh, t, nxt[t]) for t in need}
    rj_at = {t: T.pre_open(rjh, t, nxt[t]) for t in need}

    def state(sym, A):
        kk = D.cix[A]
        lo = (dt.date.fromisoformat(A) - dt.timedelta(days=T.POOL_DAYS)).isoformat()
        for j in range(kk - 1, kk - T.WIN - 1, -1):
            t = D.cal[j]
            if t < lo:
                break
            sn = nw_at.get(t)
            if sn and sym in sn[2]:
                rj = rj_at.get(t)
                fl, _ = pit.float_at(sym, t)
                return {"t": t, "price": T.price_band(G._num(sn[2][sym].get("price"), 4)),
                        "wall": T.wall_group(T.wall_of(sym, rj[1]) if rj else None), "float": T.float_band(fl)}
        return None

    def traits_of(sym, A):
        df = D.arch[sym]
        ix = list(df.index.strftime("%Y-%m-%d"))
        return unit_traits(hist_rows(df), ix.index(A), D.splits.get(sym))

    units = []
    for ev in events:
        st = state(ev["sym"], ev["A"])
        if st is None:
            acc["no_pool"].append((ev["sym"], ev["A"]))
            continue
        ev.update(st)
        kk = D.cix[ev["A"]]
        lo = (dt.date.fromisoformat(ev["A"]) - dt.timedelta(days=T.POOL_DAYS)).isoformat()
        members = set()
        for j in range(kk - T.WIN, kk):
            t = D.cal[j]
            if t >= lo and nw_at.get(t):
                members |= set(nw_at[t][2])
        pool, info = [], {}
        for c in sorted(members - {ev["sym"]} - set(T.FIVE)):
            df = D.arch.get(c)
            if df is None:
                continue
            ix = list(df.index.strftime("%Y-%m-%d"))
            if ev["A"] not in ix or ix.index(ev["A"]) < T.HIST:
                continue
            rows = D.fresh.get(c)
            kc = D.fidx(c, ev["A"]) if rows else None
            if kc is None:
                acc["ctrl_no_fresh"] += 1
                continue
            if len(rows) - 1 - kc < T.CTRL_MIN_FOLLOW:
                acc["ctrl_short_follow"] += 1
                continue
            sess, cov = D.ext_sess(c)
            fw = forward(rows, sess, cov, kc)
            if fw is None:
                acc["ctrl_no_fresh"] += 1
                continue
            if fw["reached"]:
                acc["ctrl_reached_2x"] += 1
                continue
            if not fw["complete"]:
                acc["ctrl_forward_unknown"] += 1
                continue
            if anchor == "O":
                wc = window_clean(rows, sess, cov, kc)
                if wc is False:
                    acc["ctrl_window_moved"] += 1
                    continue
                if wc is None:
                    acc["ctrl_window_unknown"] += 1
                    continue
            cs = state(c, ev["A"])
            if cs is None:
                continue
            pool.append({"sym": c, **cs})
            info[c] = fw
        chosen, lvl = match_controls(pool, ev)
        if len(chosen) < T.FLOORS["min_ctrl"]:
            acc["few_controls"].append((ev["sym"], ev["A"], len(chosen)))
            continue
        et = traits_of(ev["sym"], ev["A"])
        rows_e = D.fresh[ev["sym"]]
        sess_e, cov_e = D.ext_sess(ev["sym"])
        u = {"sym": ev["sym"], "A": ev["A"], "E_reg": ev["E_reg"], "E_star": ev["E_star"], "identity": ev["identity"],
             "match_level": lvl,
             "gov": {tr: as01(et["gov"][tr]) for tr in TRAITS}, "gov_lead": et["gov_lead"],
             "w19": {tr: as01(et["w19"][tr]) for tr in TRAITS},
             "days": {ld: {k: as01(v) for k, v in et["days"][ld].items()} for ld in W19_LEADS},
             "split_unadjusted": et["split_unadjusted"], "runup": et["runup"],
             "window_clean": window_clean(rows_e, sess_e, cov_e, ev["a_fresh"]),
             "ctrl_gov": [], "ctrl_w19": [], "ctrl_days": [], "ctrl_syms": [], "ctrl_moved_fwd": [],
             "ctrl_fwd_days": [], "ctrl_runup": [], "ctrl_split_unadjusted": []}
        for c in chosen:
            ct = traits_of(c["sym"], ev["A"])
            u["ctrl_gov"].append({tr: as01(ct["gov"][tr]) for tr in TRAITS})
            u["ctrl_w19"].append({tr: as01(ct["w19"][tr]) for tr in TRAITS})
            u["ctrl_days"].append({ld: {k: as01(v) for k, v in ct["days"][ld].items()} for ld in W19_LEADS})
            u["ctrl_syms"].append(c["sym"])
            u["ctrl_moved_fwd"].append(info[c["sym"]]["moved"])
            u["ctrl_fwd_days"].append(info[c["sym"]]["days"])
            u["ctrl_runup"].append(ct["runup"])
            u["ctrl_split_unadjusted"].append(ct["split_unadjusted"])
        units.append(u)
    return summarize_anchor(units, acc)


def lead_profile(units):
    """Descriptive: for each single decision day A−lead (lead 2 … 20) the share of events / control draws where the trait
    is true (known days only)."""
    out = {}
    for ld in W19_LEADS:
        row = {}
        for tr in ("VOLX3", "RET5"):
            e = [u["days"][ld][tr] for u in units if u["days"][ld][tr] is not None]
            c = [d[ld][tr] for u in units for d in u["ctrl_days"] if d[ld][tr] is not None]
            row[tr] = {"p_events": round(sum(e) / len(e), 4) if e else None, "n_events": len(e),
                       "p_controls": round(sum(c) / len(c), 4) if c else None, "n_controls": len(c)}
        out[ld] = row
    return out


def leak_audit(units):
    """Pre-declared leakage reading (descriptive): rule days inside events' and controls' [A−20, A−1] windows (O: must be
    0 by construction) · E_reg inside the governing window · firing only on the last window day (lead 2) · run-up
    close[A−1] ÷ close[A−7] − 1 (median, events vs controls)."""
    def only_last(day_map):
        hits = [ld for ld in GOV_LEADS if (day_map.get(ld) or {}).get("VOLX3") or (day_map.get(ld) or {}).get("RET5")]
        return bool(hits) and set(hits) == {K_GAP}

    def med(xs):
        xs = sorted(x for x in xs if x is not None)
        return xs[len(xs) // 2] if xs else None
    ev_fired = [u for u in units if u["gov"]["UNION"] == 1]
    c_fired = [d for u in units for d, g in zip(u["ctrl_days"], u["ctrl_gov"]) if g["UNION"] == 1]
    e_reg_in = 0
    for u in units:
        a = dt.date.fromisoformat(u["A"])
        if dt.date.fromisoformat(u["E_reg"]) < a:
            e_reg_in += 1
    return {"events_window_not_clean": sum(1 for u in units if u["window_clean"] is not True),
            "events_window_moved": sum(1 for u in units if u["window_clean"] is False),
            "events_E_reg_before_anchor": e_reg_in,
            "events_fired_only_lead2": sum(1 for u in ev_fired if only_last(u["days"])), "events_fired": len(ev_fired),
            "controls_fired_only_lead2": sum(1 for d in c_fired if only_last(d)), "controls_fired": len(c_fired),
            "runup_median_events": med(u["runup"] for u in units),
            "runup_median_controls": med(x for u in units for x in u["ctrl_runup"]),
            "units_split_unadjusted": sum(1 for u in units if u["split_unadjusted"]),
            "controls_split_unadjusted": sum(1 for u in units for x in u["ctrl_split_unadjusted"] if x)}


def summarize_anchor(units, acc):
    moved = [m for u in units for m in u["ctrl_moved_fwd"]]
    res = {"accounting": {k: (v if isinstance(v, int) else len(v)) for k, v in acc.items()}, "accounting_detail": acc,
           "primary": block(units), "sensitivity_identity": block([u for u in units if u["identity"]]),
           "match_levels": {lv: sum(1 for u in units if u["match_level"] == lv) for lv in (0, 1, 2)},
           "controls_moved_without_2x": {"moved": sum(1 for m in moved if m is True), "draws": len(moved),
                                         "unknown": sum(1 for m in moved if m is None)},
           "controls_truncated_forward": sum(1 for u in units for d in u["ctrl_fwd_days"] if d < HORIZON + 1),
           "lead_profile": lead_profile(units), "leak_audit": leak_audit(units), "units": units}
    res["verdict"] = anchor_verdict(res["primary"], res["sensitivity_identity"])
    return res


def write_units_csv(res, path=UNITS_CSV):
    cols = ["anchor", "role", "sym", "event_sym", "A", "E_reg", "E_star", "identity", "match_level",
            "VOLX3", "RET5", "UNION", "INTERSECT", "w19_VOLX3", "w19_RET5", "w19_UNION", "lead_UNION",
            "moved_fwd", "fwd_days", "runup"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for an in ("O", "B"):
            for u in res["anchors"][an]["units"]:
                w.writerow([an, "event", u["sym"], u["sym"], u["A"], u["E_reg"], u["E_star"], u["identity"],
                            u["match_level"]] + [u["gov"][t] for t in TRAITS]
                           + [u["w19"][t] for t in ("VOLX3", "RET5", "UNION")]
                           + [u["gov_lead"]["UNION"], "", "", u["runup"]])
                for i, c in enumerate(u["ctrl_syms"]):
                    w.writerow([an, "control", c, u["sym"], u["A"], "", "", "", u["match_level"]]
                               + [u["ctrl_gov"][i][t] for t in TRAITS]
                               + [u["ctrl_w19"][i][t] for t in ("VOLX3", "RET5", "UNION")]
                               + ["", u["ctrl_moved_fwd"][i], u["ctrl_fwd_days"][i], u["ctrl_runup"][i]])


def run():
    check_pins()
    check_merged()
    D = F.Data()
    pop, _register = F.load_population()
    stats = [F.row_stats(D, r["SYMBOL"], r["EXPL_DATE"]) for r in pop]
    hist = (T.nearwatch_history(), T.reject_history())
    res = {"prereg_sha256": PREREG_SHA256, "daily_feats_sha256": DAILY_FEATS_SHA256,
           "constants": {"K_GAP": K_GAP, "W_GOV": W_GOV, "GOV_LEADS": list(GOV_LEADS), "LEAD_MAX": LEAD_MAX,
                         "RULE_WIN": RULE_WIN, "HORIZON": HORIZON, "MDE_MAX": MDE_MAX, "N_CTRL": T.N_CTRL,
                         "FLOORS": T.FLOORS, "BOOT": T.BOOT, "SEED": T.SEED},
           "anchors": {an: run_anchor(D, pop, stats, an, hist) for an in ("O", "B")}}
    res["verdicts"] = {an: res["anchors"][an]["verdict"] for an in ("O", "B")}
    res["final_verdict"] = final_verdict(res["verdicts"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_units_csv(res)
    report(res)
    return res


def report(res):
    for an in ("O", "B"):
        r = res["anchors"][an]
        print(f"\n######## anchor {an} · accounting {json.dumps(r['accounting'], ensure_ascii=False)}")
        print("match levels", r["match_levels"], "· controls moved without 2×", r["controls_moved_without_2x"],
              "· truncated forward", r["controls_truncated_forward"])
        print("leak audit", json.dumps(r["leak_audit"], ensure_ascii=False))
        print("lead profile (lead: VOLX3 E/C · RET5 E/C)")
        for ld, row in r["lead_profile"].items():
            print(f"  {ld:>2}: {row['VOLX3']['p_events']} / {row['VOLX3']['p_controls']}"
                  f" · {row['RET5']['p_events']} / {row['RET5']['p_controls']}")
        for name in ("primary", "sensitivity_identity"):
            b = r[name]
            print(f"== {name}: events {b['events']} · symbols {b['symbols']} · control draws {b['control_draws']}"
                  f" · floors {b['floors_met']} · design MDE80 {b['design_mde80']}")
            for tr in TRAITS:
                t = b["traits"][tr]
                w = b["w19"][tr]
                print(f"  {tr:9s} E {t['p_events']} (n {t['n_events']}) · C {t['p_controls']} (n {t['n_controls']})"
                      f" · Δ {t['delta']['point']} {t['delta']['ci95']} · boot MDE80 {t['mde80_boot']} · LR {t['lr']}"
                      f" · lead med {t['lead_earliest_median']} || w19 E {w['p_events']} C {w['p_controls']}"
                      f" Δ {w['delta']['point']} {w['delta']['ci95']}")
        print(f"verdict {an}: {r['verdict']}")
    print("\nverdicts", res["verdicts"], "· FINAL", res["final_verdict"])


# ── guards (synthetic; no test-population read) ─────────────────────────────────────────────────────
def guards():
    fails = []

    def chk(name, cond, info=""):
        print(("✅ " if cond else "❌ ") + name + (f"  [{info}]" if info and not cond else ""))
        if not cond:
            fails.append(name)

    def synth_hist(n=60, seed=1):
        r = random.Random(seed)
        out, c = [], 2.0
        base = dt.date(2026, 3, 2)
        for i in range(n):
            o = c
            c = max(0.05, c * (1 + r.uniform(-0.04, 0.04)))
            out.append([(base + dt.timedelta(days=i)).isoformat(), o, max(o, c) * 1.01, min(o, c) * 0.99, c,
                        r.uniform(1e5, 2e5)])
        return out

    # H1 — traits are link100_probe.daily_feats by name, and ignore every bar after t
    h = synth_hist()
    t = 40
    f = L.daily_feats(h, t + 1, False)
    z = day_traits(h, t)
    chk("H1a traits = link100 daily_feats buckets", z["VOLX3"] == (f["vol_x"] == "≥3") and z["RET5"] == (f["ret5"] == ">+20%"))
    h2 = [list(r) for r in h]
    for j in range(t + 1, len(h2)):
        h2[j][4] *= 9.0
        h2[j][5] *= 50.0
    chk("H1b no look-ahead (bars after t ignored)", day_traits(h2, t) == z)
    h3 = [list(r) for r in h]
    h3[t][5] = 10.0 * sorted(r[5] for r in h3[t - 19:t - 4])[7]
    h3[t][4] = h3[t - 5][4] * 1.25
    zz = day_traits(h3, t)
    chk("H1c a 10× volume day and +25 % in 5 sessions fire both traits", zz["VOLX3"] is True and zz["RET5"] is True, str(zz))
    h4 = [list(r) for r in h]
    h4[t][4] = h4[t - 5][4] * 1.199
    chk("H1d +19.9 % is not RET5", day_traits(h4, t)["RET5"] is False)

    # H2 — first_rule_day ≡ gen5_ext.control_moved_ext(ahead=0) (bool and unknown), on random windows
    agree = 0
    for s in range(400):
        r = random.Random(100 + s)
        n = 50
        rows, c = [], 1.0
        base = dt.date(2026, 5, 1)
        for i in range(n):
            o = c
            c = max(0.05, c * (1 + r.choice([0, 0, 0, 0.02, -0.02, 0.3, 0.55, -0.1])))
            rows.append([(base + dt.timedelta(days=i)).isoformat(), o, max(o, c) * (1 + r.choice([0, 0.05, 0.6])),
                         min(o, c), c])
        sess = {}
        for i in range(n):
            if r.random() < 0.15:
                sess[rows[i][0]] = {"pre": [rows[i][4] * r.choice([1.1, 1.6, 2.2]), "07:00"] if r.random() < 0.5 else None,
                                    "aft": [rows[i][4] * r.choice([1.1, 1.6]), "17:00"] if r.random() < 0.5 else None}
        cov = rows[r.choice([0, 10, 30])][0] if r.random() < 0.8 else None
        k = r.randint(21, n - 1)
        j, unk = first_rule_day(rows, sess, cov, k, 20)
        ref = X.control_moved_ext(rows, sess, cov, k, win=20, ahead=0)
        mine = True if j is not None else (None if unk else False)
        agree += (mine == ref)
    chk("H2 first_rule_day ≡ control_moved_ext(ahead=0) on 400 random windows", agree == 400, f"{agree}/400")
    base2 = dt.date(2026, 5, 1)
    g = [[(base2 + dt.timedelta(days=i)).isoformat(), 1.0, 1.0, 1.0, 1.0] for i in range(40)]
    for i, c in zip(range(25, 32), (1.1, 1.21, 1.331, 1.4641, 1.61051, 1.771561, 1.95)):
        g[i] = [g[i][0], c, c, c, c]                              # +10 %/day: no 50 % jump · run 1.61 on day 29 · 1.77 on day 30
    jj, _u = first_rule_day(g, {}, g[0][0], 35, 20)
    chk("H2b the run rule is 1.7 × (a gradual climb fires on its 1.77 day, not its 1.61 day)",
        jj == 30 and X.control_moved_ext(g, {}, g[0][0], 29, win=20, ahead=0) is False, str(jj))

    # H3 — onset walks back to the first leg, stops after a rule-free window, unknown when not covered
    def flat(n, start=1.0):
        base = dt.date(2026, 4, 1)
        return [[(base + dt.timedelta(days=i)).isoformat(), start, start * 1.01, start * 0.99, start] for i in range(n)]
    rows = flat(80)
    for j in range(60, 80):
        rows[j][4] = rows[j][2] = 2.5                            # one move on day 60
    cov = rows[0][0]
    chk("H3a single move: onset = the move day", onset(rows, {}, cov, 62) == (60, "OK"), str(onset(rows, {}, cov, 62)))
    rows2 = flat(90)
    rows2[50][2] = 1.6                                           # first leg: regular high +60 % on day 50, closes flat
    for j in range(58, 90):
        rows2[j][4] = rows2[j][2] = 2.6                          # second leg on day 58 (8 sessions later)
    chk("H3b two legs 8 apart: onset = first leg", onset(rows2, {}, cov, 60) == (50, "OK"), str(onset(rows2, {}, cov, 60)))
    rows3 = flat(100)
    rows3[40][2] = 1.6
    for j in range(70, 100):
        rows3[j][4] = rows3[j][2] = 2.6
    chk("H3c legs 30 apart: onset = later leg", onset(rows3, {}, cov, 70) == (70, "OK"), str(onset(rows3, {}, cov, 70)))
    chk("H3d no coverage ⟶ UNKNOWN", onset(rows, {}, None, 62) == (None, "UNKNOWN"))
    chk("H3e window before the data start ⟶ UNKNOWN", onset(rows, {}, cov, 15) == (None, "UNKNOWN"))
    rows_pm = flat(90)
    for j in range(58, 90):
        rows_pm[j][4] = rows_pm[j][2] = 2.6
    sess_pm = {rows_pm[50][0]: {"pre": [1.7, "06:00"], "aft": None}}
    chk("H3f a pre-market spike is a move day (onset 50 with it · 58 without)",
        onset(rows_pm, sess_pm, cov, 60) == (50, "OK") and onset(rows_pm, {}, cov, 60) == (58, "OK"))

    # H4 — three-valued window logic
    dm = {2: {"VOLX3": False, "RET5": None}, 3: {"VOLX3": True, "RET5": False}, 4: {"VOLX3": None, "RET5": None},
          5: {"VOLX3": False, "RET5": True}, 6: {"VOLX3": False, "RET5": False}}
    o, ld = window_eval(dm, GOV_LEADS)
    chk("H4a any-day firing and earliest lead", o["VOLX3"] is True and ld["VOLX3"] == 3 and o["RET5"] is True and ld["RET5"] == 5)
    chk("H4b union/intersect", o["UNION"] is True and o["INTERSECT"] is True and ld["UNION"] == 5 and ld["INTERSECT"] == 3)
    o2, _ = window_eval({ld_: {"VOLX3": None, "RET5": False} for ld_ in GOV_LEADS}, GOV_LEADS)
    chk("H4c unknown stays unknown", o2["VOLX3"] is None and o2["UNION"] is None and o2["INTERSECT"] is False)
    chk("H4d tri logic", tri_or(None, False) is None and tri_or(None, True) is True and tri_and(None, True) is None
        and tri_and(None, False) is False)

    # H5 — forward outcome: reached 2× · moved without 2× · quiet · uncovered
    base = flat(60)
    up = [list(r) for r in base]
    up[40][2] = 2.2
    fw = forward(up, {}, cov, 38)
    chk("H5a +120 % high within 20 ⟶ reached", fw["reached"] is True)
    mid = [list(r) for r in base]
    mid[40][2] = 1.6
    fw2 = forward(mid, {}, cov, 38)
    chk("H5b +60 % only ⟶ moved, not reached", fw2["reached"] is False and fw2["moved"] is True and fw2["complete"] is True)
    fw3 = forward(base, {}, cov, 38)
    chk("H5c quiet ⟶ neither", fw3["reached"] is False and fw3["moved"] is False)
    fw4 = forward(base, {}, None, 38)
    chk("H5d no coverage ⟶ incomplete (unknown, never «did not explode»)", fw4["complete"] is False)
    pm = forward(base, {base[45][0]: {"pre": [2.3, "07:00"], "aft": None}}, cov, 38)
    chk("H5e a pre-market 2× counts", pm["reached"] is True)

    # H6 — branches and verdicts
    def blk(n_e, n_sym, n_c, lo):
        return {"floors_met": n_e >= 30 and n_sym >= 20, "design_mde80": design_mde80(n_e, n_c),
                "traits": {GOVERNING: {"delta": {"ci95": [lo, lo + 0.2]}}}}
    chk("H6a floors", branch(blk(29, 25, 145, 0.1)) == "D")
    chk("H6b design MDE above 0.25 ⟶ D", branch(blk(36, 30, 180, 0.1)) == "D" and branch(blk(40, 30, 200, 0.1)) == "A")
    chk("H6c CI lower ≤ 0 ⟶ C", branch(blk(46, 45, 230, 0.0)) == "C" and branch(blk(46, 45, 230, -0.1)) == "C")
    chk("H6d identity D caps A at A0", anchor_verdict(blk(46, 45, 230, 0.05), blk(20, 20, 100, 0.05)) == "A0")
    chk("H6e identity C lowers A", anchor_verdict(blk(46, 45, 230, 0.05), blk(31, 31, 155, -0.01)) == "C")
    chk("H6f identity without the MDE rule", anchor_verdict(blk(46, 45, 230, 0.05), blk(31, 31, 155, 0.05)) == "A")
    chk("H6g final = weakest anchor", final_verdict({"O": "A", "B": "C"}) == "C" and final_verdict({"O": "D", "B": "A"}) == "D"
        and final_verdict({"O": "A0", "B": "A"}) == "A0")

    # H7 — constants as declared
    chk("H7 constants", (K_GAP, W_GOV, LEAD_MAX, RULE_WIN, HORIZON, MDE_MAX, GOVERNING) == (2, 5, 20, 20, 20, 0.25, "UNION")
        and GOV_LEADS == (2, 3, 4, 5, 6) and W19_LEADS[0] == 2 and W19_LEADS[-1] == 20
        and design_mde80(46, 230) == 0.2261 and design_mde80(37, 185) > 0.25)

    # H8 — a changed contract exits 9 before any read
    import tempfile
    tf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".md")
    tf.write("not the contract")
    tf.close()
    code = None
    try:
        check_pins(tf.name, "0" * 64)
    except SystemExit as e:
        code = e.code
    os.unlink(tf.name)
    chk("H8 contract pin ⟶ exit 9", code == 9)

    # H9 — a reverse split NOT adjusted inside the trait range makes every reading unknown (events and controls alike)
    hs = synth_hist(70, 3)
    k = 60
    for j in range(k - 10, len(hs)):
        hs[j][4] *= 10.0
        hs[j][1] *= 10.0
    ut = unit_traits(hs, k, [[hs[k - 10][0], 0.1]])
    chk("H9 unadjusted split ⟶ unknown", ut["split_unadjusted"] and ut["gov"]["UNION"] is None and ut["w19"]["UNION"] is None)
    ut2 = unit_traits(synth_hist(70, 3), k, [[hs[k - 10][0], 0.1]])
    chk("H9b adjusted series with a split date ⟶ read normally", not ut2["split_unadjusted"] and ut2["gov"]["VOLX3"] is not None)

    # H10 — no bar inside the gap is ever read: heat on A−1 (and on A) changes nothing
    hb = synth_hist(70, 5)
    k = 60
    base_t = unit_traits(hb, k, [])
    hb2 = [list(r) for r in hb]
    for j in (k - 1, k):
        hb2[j][5] *= 40.0
        hb2[j][4] *= 1.9
    chk("H10 gap guard (A−1 and A never read)", unit_traits(hb2, k, [])["gov"] == base_t["gov"]
        and unit_traits(hb2, k, [])["w19"] == base_t["w19"])

    # H11 — the rule-free window condition is the onset construction applied to controls
    cl = flat(60)
    cl[45][2] = 1.7
    chk("H11 window_clean: a rule day inside ⟶ False · quiet ⟶ True · no coverage ⟶ None",
        window_clean(cl, {}, cov, 50) is False and window_clean(flat(60), {}, cov, 50) is True
        and window_clean(flat(60), {}, None, 50) is None)

    def _exit_code(fn):
        try:
            fn()
            return 0
        except SystemExit as e:
            return e.code
    _pool = [{"sym": c, "wall": "W", "price": "P", "float": "F"} for c in ("C1", "C2", "C3", "C4", "C5", "C6", "C7")]
    _ev = {"sym": "X", "A": "2026-09-01", "E_reg": "2026-08-20", "wall": "W", "price": "P", "float": "F"}
    try:
        _got = match_controls(_pool, _ev)
    except Exception as _e:                      # noqa: BLE001
        _got = (f"⛔ {type(_e).__name__}", None)
    chk("H13 control matching runs on a heat event (no 'E' key) and ties break on the anchor day A",
        _got == T.pick_controls(_pool, {**_ev, "E": "2026-09-01"})
        and _got != T.pick_controls(_pool, {**_ev, "E": "2026-08-20"}))
    _pinned = open(PREREG, "rb").read()
    chk("H12 check_merged: absent from main ⟶ 9 · altered on main ⟶ 9 · the pinned bytes ⟶ passes",
        _exit_code(lambda: check_merged(lambda: None)) == 9
        and _exit_code(lambda: check_merged(lambda: _pinned + b" ")) == 9
        and _exit_code(lambda: check_merged(lambda: _pinned)) == 0)

    print(f"\nguards failed: {len(fails)}")
    return fails


if __name__ == "__main__":
    if "--guards" in sys.argv:
        sys.exit(1 if guards() else 0)
    run()
