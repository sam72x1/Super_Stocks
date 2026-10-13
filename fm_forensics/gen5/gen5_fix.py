"""GEN5 · addendum 1 — the corrected run (extended-session outcome · split-adjusted · two anchors · weakest reading).

The sealed run (gen5_test.py · data/gen5_result.json · verdict C) is kept as published and is labelled «fallen by a
measurement defect» (GEN5_ADDENDUM_1.md §①). This runner changes ONLY what the addendum names:
  · the outcome window: "exploded" = the highest price of pre-market + regular + after-hours (gen5_ext), not the close;
  · the bars for the outcome: TradingView daily regular + 60-minute extended, both split-adjusted, fetched in one run;
  · a second, pre-declared event anchor B (the first session the +100% is realized, E*) next to the sealed anchor A
    (the register date); the verdict is the weakest of both anchors × (primary, identity).
Everything else is the sealed contract by name: H-CYCLE3 (RETEST) primary, RSI33 baseline, components, matching, 5 controls,
symbol-clustered bootstrap (gen5_test.boot_delta), floors, branches (gen5_test.verdict).

    python3 fm_forensics/gen5/gen5_fix.py --guards     # synthetic guards, no data needed
    python3 fm_forensics/gen5/gen5_fix.py              # needs data/gen5_ext.json.gz (fetched on a runner)
"""
import csv
import datetime as dt
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen5_features as G   # noqa: E402
import gen5_pit as PIT      # noqa: E402
import gen5_test as T       # noqa: E402
import gen5_ext as X        # noqa: E402

ADDENDUM = os.path.join(HERE, "GEN5_ADDENDUM_1.md")
ADDENDUM_SHA256 = "0c2e243acdc093da202487b6215ed4cfcf59502c760dc5f5ebfd59ff988184da"
EXT_PY = os.path.join(HERE, "gen5_ext.py")
EXT_SHA256 = "fbf505746b6e1e8216eda37016c390743a3c1de0071406498b8607dfd2be97f2"
OUT = os.path.join(HERE, "data", "gen5_fix_result.json")
ROWS_CSV = os.path.join(HERE, "data", "gen5_fix_rows.csv")
GEN_CSV = os.path.join(HERE, "data", "gen5_fix_generation.csv")
GEN_SINCE = "2026-07-01"
ORDER = {"D": 0, "C": 1, "B": 2, "A": 3}


def check_pins():
    """The sealed contract AND the addendum must be byte-identical to their pins, or exit 9 before any read."""
    T.check_contract()
    got = hashlib.sha256(open(ADDENDUM, "rb").read()).hexdigest() if os.path.exists(ADDENDUM) else None
    if got != ADDENDUM_SHA256:
        print(f"⛔ addendum changed or not pinned: {got} ≠ {ADDENDUM_SHA256}")
        sys.exit(9)
    gx = hashlib.sha256(open(EXT_PY, "rb").read()).hexdigest()
    if gx != EXT_SHA256:
        print(f"⛔ gen5_ext.py changed after the seal: {gx} ≠ {EXT_SHA256}")
        sys.exit(9)


def final_verdict(per_anchor):
    """Weakest reading across anchors (D < C < B < A) — each anchor's own verdict is gen5_test.verdict(primary, identity)."""
    return min(per_anchor.values(), key=lambda v: ORDER[v])


def anchor_b(rows_by_sym, ix_of_star):
    """Anchor B dedupe: per symbol, verified rows ordered by E*; a row whose E* is within DEDUP sessions of the kept one
    is the same move ⟶ dropped. Returns (keep, dropped)."""
    keep, dropped = [], []
    for sym, rs in rows_by_sym.items():
        k, d = T.dedupe(rs, ix_of_star)
        keep += k
        dropped += d
    return keep, dropped


def mde80(units, comp, reps=1000, seed=T.SEED):
    """Descriptive minimum detectable effect (80 % power, two-sided 5 %) = 2.8 × the symbol-clustered bootstrap SD of Δ."""
    by = {}
    for u in units:
        by.setdefault(u["sym"], []).append(u)
    syms = sorted(by)
    rng = random.Random(seed)

    def d(us):
        e = [u["ev"][comp] for u in us if u["ev"].get(comp) is not None]
        k = [sum(x[comp] for x in u["ctrl"] if x.get(comp) is not None)
             / max(1, sum(1 for x in u["ctrl"] if x.get(comp) is not None))
             for u in us if any(x.get(comp) is not None for x in u["ctrl"])]
        return (sum(e) / len(e) - sum(k) / len(k)) if e and k else None
    vals = [v for v in (d([u for t in (rng.choice(syms) for _ in syms) for u in by[t]]) for _ in range(reps))
            if v is not None]
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
    return round(2.8 * sd, 4)


def block(us):
    n_sym = len({u["sym"] for u in us})
    res = {"events": len(us), "symbols": n_sym,
           "floors_met": len(us) >= T.FLOORS["events"] and n_sym >= T.FLOORS["symbols"], "components": {}}
    for comp in T.COMPONENTS:
        e = [u["ev"][comp] for u in us if u["ev"][comp] is not None]
        cr = [x[comp] for u in us for x in u["ctrl"] if x.get(comp) is not None]
        leads = sorted(u["ev_lead"][comp] for u in us if u["ev_lead"][comp] is not None)
        res["components"][comp] = {
            "p_events": round(sum(e) / len(e), 4) if e else None, "n_events": len(e),
            "p_controls": round(sum(cr) / len(cr), 4) if cr else None, "n_controls": len(cr),
            "delta": T.boot_delta(us, comp) if us else {"point": None, "ci95": None},
            "lead_earliest_median": leads[len(leads) // 2] if leads else None}
    res["primary_vs_baseline"] = T.boot_delta(us, T.PRIMARY, base=T.BASELINE) if us else {"point": None, "ci95": None}
    res["mde80_primary"] = mde80(us, T.PRIMARY) if us else None
    return res


# ── data ─────────────────────────────────────────────────────────────────────────────────────────────
class Data:
    def __init__(self):
        e = X.load()
        self.meta = e["meta"]
        self.fresh = e["daily"]
        self.sess = e["sess"]
        self.cov = e["cov"]
        self.raw = e.get("raw") or {}
        self.arch = G.load_bars()
        self.splits = G.load_splits()
        self.scale = e.get("scale") or {}
        cnt = {}
        for df in self.arch.values():
            for d in df.index.strftime("%Y-%m-%d"):
                cnt[d] = cnt.get(d, 0) + 1
        self.cal = sorted(d for d, n in cnt.items() if n >= 0.5 * len(self.arch))
        self.cix = {d: i for i, d in enumerate(self.cal)}

    def ext_sess(self, s):
        """(sess, cov) for the extended reads — a symbol whose hourly scale disagrees with its daily scale is unknown."""
        if self.scale.get(s) is False:
            return None, None
        return self.sess.get(s), self.cov.get(s)

    def fidx(self, s, day):
        rows = self.fresh.get(s) or []
        for i, r in enumerate(rows):
            if r[0] == day:
                return i
        return None


def row_stats(D, s, e_day, horizon=20):
    rows = D.fresh.get(s)
    if not rows:
        return None
    k = D.fidx(s, e_day)
    if k is None or k < 1:
        return None
    sess, cov = D.ext_sess(s)
    st = X.explosion_stats(rows, sess, cov, k - 1, k, horizon)
    if st is None:
        return None
    end = rows[min(k + horizon, len(rows) - 1)][0]
    st["split_unadjusted"] = X.split_unadjusted(rows, D.splits.get(s), rows[k - 1][0], end)
    st["status"] = ("SPLIT_UNADJUSTED" if st["split_unadjusted"] else
                    "VERIFIED" if st["ext_peak"] >= T.QA_GAIN else
                    "UNVERIFIABLE" if not st["complete"] else "UNVERIFIED")
    st["close_qa"] = st["close_peak"] >= T.QA_GAIN
    return st


# ── stage A′ — generation on the five with the extended window ─────────────────────────────────────
def generation(D):
    syms = list(T.FIVE)
    events, rows_out = [], []
    for s in syms:
        rows = D.fresh.get(s) or []
        sess, cov = D.ext_sess(s)
        for j, day, where, ratio in X.realizations(rows, sess, cov, since=GEN_SINCE):
            st = X.explosion_stats(rows, sess, cov, j - 1, j, 20)
            events.append({"sym": s, "E": day, "where": where, "ratio_vs_min20": ratio,
                           "close_peak": st["close_peak"], "reg_peak": st["reg_peak"], "ext_peak": st["ext_peak"],
                           "ext_day": st["ext_day"], "ext_where": st["ext_where"]})
    dates, jobs = set(), []
    for ev in events:
        df = D.arch.get(ev["sym"])
        ix = list(df.index.strftime("%Y-%m-%d")) if df is not None else []
        if ev["E"] not in ix or ix.index(ev["E"]) < T.HIST:
            ev["features"] = "no archive window"
            continue
        k = ix.index(ev["E"])
        for j in range(k - T.WIN, k):
            jobs.append((ev, df, j, k - j))
            dates.add(ix[j])
    nxt = {t: D.cal[D.cix[t] + 1] if t in D.cix and D.cix[t] + 1 < len(D.cal) else t for t in dates}
    pit = PIT.PIT(sorted(dates), nxt)
    for ev, df, j, lead in jobs:
        f = G.features_at(df, j, D.splits.get(ev["sym"]))
        z = T.fires_ext(f)
        fl, _ = pit.float_at(ev["sym"], f["t"])
        av, _ = pit.avail_at(ev["sym"], f["t"])
        rows_out.append({"sym": ev["sym"], "event": ev["E"], "lead": lead, "t": f["t"], "pc_stage": f["pc_stage"],
                         "rsi": f["rsi"], "rsi_min20": f["rsi_min20"], "ret5": f["ret5"], "vol_ratio": f["vol_ratio"],
                         "float": fl, "avail": av, **{"F_" + c: z[c] for c in T.COMPONENTS}})
        ev.setdefault("fired", {})
        for c in T.COMPONENTS:
            if z[c]:
                ev["fired"][c] = max(ev["fired"].get(c, 0), lead)
    return events, rows_out


# ── stage C′ — the test with the extended window, two anchors ───────────────────────────────────────
def load_population():
    rows = list(csv.DictReader(open(T.CSV_FILE, encoding="utf-8")))
    tracked = [r for r in rows if r["NEAR_WATCH_14D"] in ("INSIDE", "OVERSOLD")]
    pop = [r for r in tracked if r["SYMBOL"] not in T.FIVE]
    assert len(tracked) == 107 and len(pop) == 100 and len({r["SYMBOL"] for r in pop}) == 53
    assert sum(r["WAS_PIVOT_IDENTITY"] == "True" for r in pop) == 67
    register = {}
    for r in rows:
        register.setdefault(r["SYMBOL"], []).append(r["EXPL_DATE"])
    return pop, register


def run_anchor(D, pop, register, stats, anchor, hist):
    """One full test under `anchor` ('A' register date · 'B' first realization day E*). Mirrors gen5_test.run with the
    extended QA (stats[i]['status']) and the extended control exclusion (gen5_ext.control_moved_ext)."""
    nwh, rjh = hist
    acc = {"rows": len(pop), "no_fresh_bars": [], "qa_unverified": [], "qa_unverifiable": [], "split_unadjusted": [],
           "dup_merged": [],
           "short_history": [], "beyond_archive": [], "no_pool": [], "few_controls": [],
           "ctrl_moved_ext": 0, "ctrl_unknown_ext": 0, "ctrl_no_fresh": 0}
    ver = {}
    for i, r in enumerate(pop):
        s, st = r["SYMBOL"], stats[i]
        if st is None:
            acc["no_fresh_bars"].append((s, r["EXPL_DATE"]))
            continue
        if st["status"] == "UNVERIFIED":
            acc["qa_unverified"].append((s, r["EXPL_DATE"]))
            continue
        if st["status"] == "UNVERIFIABLE":
            acc["qa_unverifiable"].append((s, r["EXPL_DATE"]))
            continue
        if st["status"] == "SPLIT_UNADJUSTED":
            acc["split_unadjusted"].append((s, r["EXPL_DATE"], st["split_unadjusted"]))
            continue
        e = r["EXPL_DATE"] if anchor == "A" else st["realized_day"]
        ver.setdefault(s, []).append({"row": r, "E": e, "st": st})
    events = []
    for s, rs in ver.items():
        keep, drop = T.dedupe(rs, lambda x: D.cix.get(x["E"], 10 ** 6))
        acc["dup_merged"] += [(x["row"]["SYMBOL"], x["row"]["EXPL_DATE"]) for x in drop]
        df = D.arch.get(s)
        ix = list(df.index.strftime("%Y-%m-%d")) if df is not None else []
        for x in keep:
            if x["E"] not in ix or x["E"] not in D.cix:
                acc["beyond_archive"].append((s, x["row"]["EXPL_DATE"], x["E"]))
                continue
            k = ix.index(x["E"])
            if k < T.HIST:
                acc["short_history"].append((s, x["row"]["EXPL_DATE"]))
                continue
            events.append({"sym": s, "E": x["E"], "E_reg": x["row"]["EXPL_DATE"], "k": k,
                           "identity": x["row"]["WAS_PIVOT_IDENTITY"] == "True", "kind": x["row"]["KIND"]})
    need = set()
    for ev in events:
        kk = D.cix[ev["E"]]
        for j in range(kk - T.WIN, kk):
            need.add(D.cal[j])
    nxt = {t: D.cal[D.cix[t] + 1] for t in need}
    pit = PIT.PIT(sorted(need), nxt)
    nw_at = {t: T.pre_open(nwh, t, nxt[t]) for t in need}
    rj_at = {t: T.pre_open(rjh, t, nxt[t]) for t in need}

    def state(sym, E):
        kk = D.cix[E]
        lo = (dt.date.fromisoformat(E) - dt.timedelta(days=T.POOL_DAYS)).isoformat()
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

    def window(sym, E):
        df = D.arch[sym]
        ix = list(df.index.strftime("%Y-%m-%d"))
        k = ix.index(E)
        return [(k - j, T.fires_ext(G.features_at(df, j, D.splits.get(sym)))) for j in range(k - T.WIN, k)]

    units = []
    for ev in events:
        st = state(ev["sym"], ev["E"])
        if st is None:
            acc["no_pool"].append((ev["sym"], ev["E"]))
            continue
        ev.update(st)
        kk = D.cix[ev["E"]]
        lo = (dt.date.fromisoformat(ev["E"]) - dt.timedelta(days=T.POOL_DAYS)).isoformat()
        members = set()
        for j in range(kk - T.WIN, kk):
            t = D.cal[j]
            if t >= lo and nw_at.get(t):
                members |= set(nw_at[t][2])
        pool = []
        for c in sorted(members - {ev["sym"]} - set(T.FIVE)):
            df = D.arch.get(c)
            if df is None:
                continue
            ix = list(df.index.strftime("%Y-%m-%d"))
            if ev["E"] not in ix or ix.index(ev["E"]) < T.HIST:
                continue
            if any(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(ev["E"])).days) <= T.REG_WINDOW_DAYS
                   for d in register.get(c, [])):
                continue
            rows = D.fresh.get(c)
            kc = D.fidx(c, ev["E"]) if rows else None
            if kc is None:
                acc["ctrl_no_fresh"] += 1
                continue
            if len(rows) - 1 - kc < T.CTRL_MIN_FOLLOW:
                continue
            sess, cov = D.ext_sess(c)
            mv = X.control_moved_ext(rows, sess, cov, kc)
            if mv is True:
                acc["ctrl_moved_ext"] += 1
                continue
            if mv is None:
                acc["ctrl_unknown_ext"] += 1
                continue
            cs = state(c, ev["E"])
            if cs is None:
                continue
            pool.append({"sym": c, **cs})
        chosen, lvl = T.pick_controls(pool, ev)
        if len(chosen) < T.FLOORS["min_ctrl"]:
            acc["few_controls"].append((ev["sym"], ev["E"], len(chosen)))
            continue
        ew = window(ev["sym"], ev["E"])
        u = {"sym": ev["sym"], "E": ev["E"], "E_reg": ev["E_reg"], "identity": ev["identity"], "match_level": lvl,
             "ev": {}, "ev_lead": {}, "ctrl": [], "ctrl_syms": []}
        for comp in T.COMPONENTS:
            fired, lead = T.window_fire(ew, comp)
            known = any(z.get(comp) is not None for _, z in ew)
            u["ev"][comp] = int(fired) if known else None
            u["ev_lead"][comp] = lead
        for c in chosen:
            cw = window(c["sym"], ev["E"])
            row = {}
            for comp in T.COMPONENTS:
                fired, _ = T.window_fire(cw, comp)
                known = any(z.get(comp) is not None for _, z in cw)
                row[comp] = int(fired) if known else None
            u["ctrl"].append(row)
            u["ctrl_syms"].append(c["sym"])
        units.append(u)
    res = {"accounting": {k: (v if isinstance(v, int) else len(v)) for k, v in acc.items()}, "accounting_detail": acc,
           "primary": block(units), "sensitivity_identity": block([u for u in units if u["identity"]]),
           "match_levels": {lv: sum(1 for u in units if u["match_level"] == lv) for lv in (0, 1, 2)}, "units": units}
    res["verdict"] = T.verdict(res["primary"], res["sensitivity_identity"])
    return res


def sealed_contamination(D):
    """D1 (descriptive): the sealed run's control draws re-read with the extended window — moved / unknown / clean."""
    sealed = json.load(open(T.OUT, encoding="utf-8"))
    out = {"draws": 0, "moved": [], "unknown": 0, "clean": 0, "no_fresh": 0}
    for u in sealed["units"]:
        for c in u["ctrl_syms"]:
            out["draws"] += 1
            rows = D.fresh.get(c)
            kc = D.fidx(c, u["E"]) if rows else None
            if kc is None:
                out["no_fresh"] += 1
                continue
            sess, cov = D.ext_sess(c)
            mv = X.control_moved_ext(rows, sess, cov, kc)
            if mv is True:
                out["moved"].append((c, u["E"], u["sym"]))
            elif mv is None:
                out["unknown"] += 1
            else:
                out["clean"] += 1
    return out


def run():
    check_pins()
    D = Data()
    pop, register = load_population()
    sealed = json.load(open(T.OUT, encoding="utf-8"))
    old_unver = {tuple(x) for x in sealed["accounting_detail"]["qa_unverified"]}
    stats = [row_stats(D, r["SYMBOL"], r["EXPL_DATE"]) for r in pop]
    hist = (T.nearwatch_history(), T.reject_history())
    res = {"prereg_sha256": T.PREREG_SHA256, "addendum_sha256": ADDENDUM_SHA256, "ext_meta": D.meta,
           "scale_mismatch": sorted(s for s, v in D.scale.items() if v is False)}
    res["anchors"] = {a: run_anchor(D, pop, register, stats, a, hist) for a in ("A", "B")}
    res["verdicts"] = {a: res["anchors"][a]["verdict"] for a in ("A", "B")}
    res["final_verdict"] = final_verdict(res["verdicts"])
    res["sealed_contamination"] = sealed_contamination(D)
    gen_events, gen_rows = generation(D)
    res["generation"] = gen_events
    table = []
    for r, st in zip(pop, stats):
        table.append({"sym": r["SYMBOL"], "E_reg": r["EXPL_DATE"], "kind": r["KIND"], "gain_reg": r["GAIN_PCT"],
                      "suspect_split": r["SUSPECT_SPLIT"], "identity": r["WAS_PIVOT_IDENTITY"],
                      "sealed_qa": "UNVERIFIED" if (r["SYMBOL"], r["EXPL_DATE"]) in old_unver else "VERIFIED",
                      **({k: st[k] for k in ("ref_date", "ref", "close_peak", "close_day", "reg_peak", "reg_day",
                                             "ext_peak", "ext_day", "ext_where", "realized_day", "realized_where",
                                             "complete", "days", "status", "split_unadjusted")}
                         if st else {"status": "NO_FRESH_BARS"})})
    res["rows"] = table
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    cols = ["sym", "E_reg", "kind", "gain_reg", "suspect_split", "identity", "sealed_qa", "status", "ref_date", "ref",
            "close_peak", "close_day", "reg_peak", "reg_day", "ext_peak", "ext_day", "ext_where", "realized_day",
            "realized_where", "complete", "days", "split_unadjusted"]
    with open(ROWS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(table)
    if gen_rows:
        with open(GEN_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(gen_rows[0].keys()))
            w.writeheader()
            w.writerows(gen_rows)
    return res


# ── guards (synthetic; no test-population read) ─────────────────────────────────────────────────────
def guards():
    fails = []

    def chk(name, cond):
        print(("✅ " if cond else "❌ ") + name)
        if not cond:
            fails.append(name)

    def ts(day, hh, mm):
        return int(dt.datetime.fromisoformat(f"{day}T{hh:02d}:{mm:02d}").replace(tzinfo=X.NY).timestamp())
    # X1 sessions by NY time, early close from the calendar (2026-11-27 closes 13:00)
    hb = [(ts("2026-09-01", 4, 0), 2.0), (ts("2026-09-01", 9, 0), 1.2), (ts("2026-09-01", 10, 0), 1.1),
          (ts("2026-09-01", 16, 0), 3.0), (ts("2026-11-27", 13, 0), 5.0), (ts("2026-11-27", 12, 0), 1.0)]
    s = X.day_sessions(hb)
    chk("X1 pre/after by NY time · early close 13:00 bar is after-hours",
        s["2026-09-01"]["pre"] == [2.0, "04:00"] and s["2026-09-01"]["aft"] == [3.0, "16:00"]
        and s["2026-09-01"]["rh"] == 1.1 and s["2026-11-27"]["aft"] == [5.0, "13:00"] and s["2026-11-27"]["rh"] == 1.0)
    # X2 day_ext: pre above the regular high is the peak; uncovered day is unknown
    chk("X2 day_ext: pre spike wins · regular wins otherwise · uncovered ⇒ unknown",
        X.day_ext("2026-09-01", 1.5, s, True)[:2] == (2.0, "pre 04:00")
        and X.day_ext("2026-09-01", 2.5, s, True)[:2] == (2.5, "regular")
        and X.day_ext("2026-09-01", 1.5, s, False)[3] is False)
    # X3 three separate peaks + realization day (close < regular < extended)
    rows = [["2026-08-31", 1, 1, 1, 1.0], ["2026-09-01", 1, 1.6, 1, 1.3], ["2026-09-02", 1, 1.2, 1, 1.1]]
    sess = {"2026-09-01": {"pre": None, "aft": [2.4, "17:00"], "rh": None}}
    st = X.explosion_stats(rows, sess, "2026-08-01", 0, 1, 20)
    chk("X3 close/regular/extended peaks kept apart · realized on the after-hours day",
        st["close_peak"] == 1.3 and st["reg_peak"] == 1.6 and st["ext_peak"] == 2.4 and st["ext_where"] == "after 17:00"
        and st["realized_day"] == "2026-09-01" and st["complete"] is True)
    # X4 extended-only mover caught by control_moved_ext and missed by the sealed close rule
    rws = [[f"2026-08-{d:02d}", 1, 1.05, 0.95, 1.0] for d in range(1, 29)]
    sess4 = {"2026-08-20": {"pre": [1.9, "06:00"], "aft": None, "rh": None}}
    quiet = X.control_moved_ext(rws, {}, "2026-07-01", 21)
    chk("X4 extended-only spike ⇒ moved · close rule blind · quiet ⇒ clean · uncovered quiet ⇒ unknown",
        X.control_moved_ext(rws, sess4, "2026-07-01", 21) is True
        and T.control_moved([r[4] for r in rws], 21) is False and quiet is False
        and X.control_moved_ext(rws, {}, "2026-08-25", 21) is None)
    # X5 realizations: one move = one event
    rw5 = [[f"d{i:03d}", 1, 1.0, 1, 1.0] for i in range(25)] + [["d025", 1, 2.5, 1, 2.2], ["d026", 1, 2.6, 1, 2.4],
                                                                    ["d027", 1, 1.0, 1, 1.0]]
    rz = X.realizations(rw5, {}, "d000")
    chk("X5 realizations: a two-day move is one event", [x[1] for x in rz] == ["d025"])
    # X6 anchor B dedupe collapses rows sharing a realization day
    rs = {"Q": [{"E": "a", "i": 10}, {"E": "a", "i": 10}, {"E": "b", "i": 40}]}
    keep, drop = anchor_b(rs, lambda x: x["i"])
    chk("X6 anchor B: rows realized on the same day are one event", len(keep) == 2 and len(drop) == 1)
    # X7 final verdict = weakest across anchors (D < C < B < A)
    chk("X7 final verdict is the weakest anchor",
        final_verdict({"A": "A", "B": "C"}) == "C" and final_verdict({"A": "B", "B": "A"}) == "B"
        and final_verdict({"A": "C", "B": "D"}) == "D" and final_verdict({"A": "A", "B": "A"}) == "A")
    # X8 scale check flags a split adjusted in one series only
    rw8 = [[f"2026-09-{d:02d}", 1, 2.0, 1, 1.5] for d in range(1, 11)]
    ok_s = {r[0]: {"pre": None, "aft": None, "rh": 1.9} for r in rw8}
    bad_s = {r[0]: {"pre": None, "aft": None, "rh": 0.08} for r in rw8}
    chk("X8 intraday/daily scale: same scale ok · split-only-in-one ⇒ mismatch",
        X.scale_ok(rw8, ok_s) is True and X.scale_ok(rw8, bad_s) is False)
    # X9 the sealed thresholds are unchanged in the extended module
    chk("X9 thresholds unchanged: jump 1.5 · run 1.7 · gain 2.0 · window 20",
        (X.JUMP, X.RUN, X.GAIN) == (T.CTRL_JUMP, T.CTRL_RUN, T.QA_GAIN) and T.WIN == 20)
    # X11 an unadjusted reverse split is caught; an adjusted one and a split outside the window are not
    rw11 = [["2026-09-01", 1, 1, 1, 1.0], ["2026-09-02", 1, 1, 1, 1.0], ["2026-09-03", 1, 10.5, 1, 10.0]]
    rw11b = [["2026-09-01", 1, 1, 1, 1.0], ["2026-09-02", 1, 1, 1, 1.0], ["2026-09-03", 1, 1.1, 1, 1.05]]
    chk("X11 split guard: 1:10 day with ×10 close ⇒ unadjusted · adjusted series or out-of-window split ⇒ none",
        X.split_unadjusted(rw11, [["2026-09-03", 0.1]], "2026-09-01", "2026-09-03") == ["2026-09-03"]
        and X.split_unadjusted(rw11b, [["2026-09-03", 0.1]], "2026-09-01", "2026-09-03") == []
        and X.split_unadjusted(rw11, [["2026-09-03", 0.1]], "2026-09-03", "2026-09-30") == [])
    # X10 each pin is enforced on its own before any read (the other pin set to the true hash)
    true_a = hashlib.sha256(open(ADDENDUM, "rb").read()).hexdigest() if os.path.exists(ADDENDUM) else None
    true_x = hashlib.sha256(open(EXT_PY, "rb").read()).hexdigest()
    keep = (globals()["ADDENDUM_SHA256"], globals()["EXT_SHA256"])

    def code_with(a, x):
        globals()["ADDENDUM_SHA256"], globals()["EXT_SHA256"] = a, x
        try:
            check_pins()
            return None
        except SystemExit as e:
            return e.code
    try:
        codes = (code_with("0" * 64, true_x), code_with(true_a, "0" * 64), code_with(true_a, true_x))
    finally:
        globals()["ADDENDUM_SHA256"], globals()["EXT_SHA256"] = keep
    chk("X10 a changed addendum ⇒ 9 · a changed gen5_ext ⇒ 9 · both true ⇒ passes", codes == (9, 9, None))
    print(f"\nguards failed: {len(fails)}")
    return 1 if fails else 0


def report(res):
    print(json.dumps({"verdicts": res["verdicts"], "final": res["final_verdict"]}, ensure_ascii=False))
    for a in ("A", "B"):
        r = res["anchors"][a]
        print(f"\n######## anchor {a} · accounting {json.dumps(r['accounting'], ensure_ascii=False)}")
        print(f"match levels {r['match_levels']}")
        for name in ("primary", "sensitivity_identity"):
            b = r[name]
            print(f"== {name}: events {b['events']} · symbols {b['symbols']} · floors {b['floors_met']} · "
                  f"MDE80 {b['mde80_primary']}")
            for comp, v in b["components"].items():
                print(f"  {comp:10s} E {v['p_events']} (n {v['n_events']}) · C {v['p_controls']} (n {v['n_controls']})"
                      f" · Δ {v['delta']['point']} {v['delta']['ci95']} · lead med {v['lead_earliest_median']}")
            print(f"  primary − baseline: {b['primary_vs_baseline']}")


if __name__ == "__main__":
    if "--guards" in sys.argv:
        sys.exit(guards())
    report(run())
