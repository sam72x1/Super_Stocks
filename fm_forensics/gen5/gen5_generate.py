"""GEN5 · stage A — generation on the five known stocks (no verdict; selection on the dependent variable).

For each generation event E: decision sessions t = E−20 … E−1, features from bars[0..t] (gen5_features.features_at),
float/available as the bot knew them at t (gen5_pit). The identity gates are not applied.
Output: data/gen5_generation_days.csv (one row per event × decision day) and a printed summary.

Events (checked on the split-adjusted TradingView archive before use, see GEN5_PREREG.md §1):
  SXTC 2026-10-07 (close +126%) · RETO 2026-09-15 (close +677%) · DLXY 2026-09-16 (close +448%)
  DKI 2026-10-07 (intraday high +168%, close +23% — a move the daily close detector does not see)
  HUBC — no explosion in the data (the register's 2026-09-15 +1756% is the 1:25 reverse split of 09-14);
         its last 40 sessions are printed for description only and never used to generate.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen5_features as G   # noqa: E402
import gen5_pit as P        # noqa: E402

EVENTS = [("SXTC", "2026-10-07", "close"), ("RETO", "2026-09-15", "close"), ("DLXY", "2026-09-16", "close"),
          ("DKI", "2026-10-07", "intraday")]
DESCRIBE_ONLY = [("HUBC", "2026-10-09")]
WIN = 20
OUT = os.path.join(HERE, "data", "gen5_generation_days.csv")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    syms = {e[0] for e in EVENTS} | {e[0] for e in DESCRIBE_ONLY}
    bars = G.load_bars(syms)
    splits = G.load_splits()
    cal = sorted({d for df in bars.values() for d in df.index.strftime("%Y-%m-%d")})
    jobs = []
    for sym, e, kind in EVENTS:
        df = bars[sym]
        ix = list(df.index.strftime("%Y-%m-%d"))
        k = ix.index(e)
        for j in range(k - WIN, k):
            jobs.append((sym, e, kind, df, j, k - j))
    for sym, last in DESCRIBE_ONLY:
        df = bars[sym]
        ix = list(df.index.strftime("%Y-%m-%d"))
        k = ix.index(last)
        for j in range(k - 40, k + 1):
            jobs.append((sym, "none", "describe", df, j, None))
    dates = sorted({job[3].index[job[4]].strftime("%Y-%m-%d") for job in jobs})
    nxt = {t: cal[cal.index(t) + 1] if cal.index(t) + 1 < len(cal) else t for t in dates}
    pit = P.PIT(dates, nxt)
    rows = []
    for sym, e, kind, df, j, lead in jobs:
        f = G.features_at(df, j, splits.get(sym))
        fl, fls = pit.float_at(sym, f["t"])
        av, avs = pit.avail_at(sym, f["t"])
        fz = G.fires(f)
        rows.append({"sym": sym, "event": e, "kind": kind, "lead": lead, **f,
                     "float": fl, "float_src": fls, "avail": av, "avail_src": avs,
                     **{"F_" + k: v for k, v in fz.items()}})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"rows {len(rows)} → {os.path.relpath(OUT, G.ROOT)}")
    for sym, e, kind in EVENTS + [(s, "none", "describe") for s, _ in DESCRIBE_ONLY]:
        rs = [r for r in rows if r["sym"] == sym and r["event"] == e]
        print(f"\n== {sym} event {e} ({kind})")
        print("lead t        close  stab pc  br    bnc   swp  held rsi  rmin vol  ret5   gapB gapA dRS  flt        avl")
        for r in rs:
            print(f"{str(r['lead']):>4} {r['t']} {r['close']:>6} {str(r['stab_bars_after']):>3}{'h' if r['stab_held'] else '-'} "
                  f"{str(r['pc_stage']):>2} {str(r['pc_branch'] or ''):5} {str(r['pc_bounce']):>5} {str(r['pc_sweep_pct']):>5} "
                  f"{str(r['pc_held']):>3} {str(r['rsi']):>5} {str(r['rsi_min20']):>5} {str(r['vol_ratio']):>5} "
                  f"{str(r['ret5']):>6} {'Y' if r['gap_below_unfilled'] else '-':>3} {r['gap_above_n']:>3} "
                  f"{str(r['days_since_rsplit']):>4} {str(r['float']):>10} {str(r['avail']):>8}")


if __name__ == "__main__":
    main()
