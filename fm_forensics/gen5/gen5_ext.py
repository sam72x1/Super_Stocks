"""GEN5 · addendum 1 — the extended-session outcome (pre-market + regular + after-hours) on split-adjusted TradingView bars.

Why (GEN5_ADDENDUM_1.md §①): the sealed run measured "exploded" on regular-session daily CLOSES only. The owner's binding
definition of an explosion in this project (`three_cond_daily.recent_explosion`, his order of 2026-09-26) is the highest price
of the pre-market, the regular session and the after-hours above a regular close. This module holds the pure functions that
apply that window (same thresholds, same references, same windows as the sealed contract) and the runner-side fetch.

Two parts:
  · pure functions (guarded in gen5_fix.py --guards): `day_sessions` · `day_ext` · `explosion_stats` · `control_moved_ext`
    · `realizations`;
  · `main()` — runs on a GitHub runner only (TradingView is blocked by this container's egress policy): fetches daily
    regular-session bars and 60-minute extended bars (both `adjustment=splits`) for `data/ext_symbols.txt`, and writes
    per-day session summaries to `data/gen5_ext.json.gz` (raw hourly bars kept for `data/ext_raw_symbols.txt` only).

No production import, no Telegram, no state written outside fm_forensics/gen5/data/.
"""
import datetime as dt
import gzip
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
EXT_FILE = os.path.join(DATA, "gen5_ext.json.gz")
SYMS_FILE = os.path.join(DATA, "ext_symbols.txt")
RAW_SYMS_FILE = os.path.join(DATA, "ext_raw_symbols.txt")
NY = ZoneInfo("America/New_York")

DAILY_N = 200            # daily bars requested (≈ 2026-01 → today; trimmed to DAILY_START)
DAILY_START = "2026-05-15"
HOURS_N = 1600           # 60-minute extended bars requested per symbol (≈ 100 sessions at 16 bars/day)
PRE_FROM, REG_OPEN, EXT_END = 4 * 60, 9 * 60 + 30, 20 * 60   # NY minutes
JUMP, RUN, GAIN = 1.5, 1.7, 2.0   # the sealed thresholds (EXPLOSION_PCT 50 · EXPLOSION_RUN_PCT 70 · +100%) — unchanged


_CLOSE = {}


def _close_min(day):
    """Regular close of `day` in NY minutes from the market calendar (16:00, or the early close) · cached per day."""
    if day not in _CLOSE:
        try:
            if ROOT not in sys.path:
                sys.path.insert(0, ROOT)
            import market_calendar as MC
            _CLOSE[day] = int((MC.session_info(day) or {}).get("close_ny_min") or 16 * 60)
        except Exception:                                        # noqa: BLE001
            _CLOSE[day] = 16 * 60
    return _CLOSE[day]


def _ny(ts):
    t = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


# ── pure functions ───────────────────────────────────────────────────────────────────────────────────
def day_sessions(hourly, close_min=_close_min):
    """hourly: [(ts_sec, high, ...)] 60-minute extended bars (bar OPEN time) ⟶
    {day: {"pre": [high, "HH:MM"] | None, "aft": [high, "HH:MM"] | None, "rh": high | None}}.
      pre = bars opening in [04:00, 09:30) — the 09:00 bar also holds 09:30–10:00 regular trades, harmless for a MAXIMUM
            because those trades never exceed the daily regular high (see `day_ext`);
      aft = bars opening in [regular close, 20:00) — pure after-hours (early closes from the calendar);
      rh  = highest pure-regular bar (opening in [10:00, close)) — only used to check the intraday/daily scale."""
    out = {}
    for b in hourly or []:
        try:
            day, m = _ny(b[0])
            hi = float(b[1])
        except Exception:                                        # noqa: BLE001
            continue
        if not hi > 0:
            continue
        rec = out.setdefault(day, {"pre": None, "aft": None, "rh": None})
        hhmm = f"{m // 60:02d}:{m % 60:02d}"
        cm = close_min(day)
        if PRE_FROM <= m < REG_OPEN:
            if rec["pre"] is None or hi > rec["pre"][0]:
                rec["pre"] = [hi, hhmm]
        elif cm <= m < EXT_END:
            if rec["aft"] is None or hi > rec["aft"][0]:
                rec["aft"] = [hi, hhmm]
        elif REG_OPEN + 30 <= m < cm:
            if rec["rh"] is None or hi > rec["rh"]:
                rec["rh"] = hi
    return out


def day_ext(day, reg_high, sess, covered):
    """Highest price of `day` and where it printed ⟶ (pre_or_regular_high, session, after_high | None, known).
    `covered` False ⟶ no extended data for this day (before the symbol's first hourly bar, or fetch failed): the regular
    high stands alone and known=False. A covered day with no pre/after bar had no extended trade (TradingView prints a
    bar only when a trade happens)."""
    if not covered:
        return reg_high, "regular", None, False
    s = (sess or {}).get(day) or {}
    pre = s.get("pre")
    if pre and pre[0] > reg_high:
        return pre[0], "pre " + pre[1], (s["aft"][0] if s.get("aft") else None), True
    return reg_high, "regular", (s["aft"][0] if s.get("aft") else None), True


def explosion_stats(rows, sess, cov_from, ref_idx, start_idx, horizon=20, gain=GAIN):
    """rows: [[date, o, h, l, c], …] daily regular bars · ref = close[ref_idx] · days start_idx … start_idx+horizon.
    Three separate peaks relative to ref (never one blended number):
      close_peak (regular closes) · reg_peak (regular highs) · ext_peak (pre + regular + after highs)
    each with its day and session; `realized` = first day whose extended peak ≥ gain × ref (E*); `complete` = every day of
    the window had extended coverage; `days` = sessions available (the window is cut at the data end)."""
    if ref_idx < 0 or ref_idx >= len(rows):
        return None
    ref = float(rows[ref_idx][4])
    if not ref > 0:
        return None
    best = {"close": (0.0, None, None), "reg": (0.0, None, None), "ext": (0.0, None, None)}
    realized, complete, days = None, True, 0
    for j in range(start_idx, min(start_idx + horizon, len(rows) - 1) + 1):
        d, h, c = rows[j][0], float(rows[j][2]), float(rows[j][4])
        days += 1
        covered = sess is not None and cov_from is not None and d >= cov_from
        pr, pr_s, aft, known = day_ext(d, h, sess, covered)
        complete = complete and known
        cand = {"close": (c, "close"), "reg": (h, "regular"), "ext": (pr, pr_s)}
        if aft is not None and aft > cand["ext"][0]:
            a = ((sess or {}).get(d) or {}).get("aft") or [aft, "?"]
            cand["ext"] = (aft, "after " + a[1])
        for k, (v, where) in cand.items():
            if v / ref > best[k][0]:
                best[k] = (v / ref, d, where)
        if realized is None and cand["ext"][0] >= gain * ref:
            realized = (j, d, cand["ext"][1])
    return {"ref_date": rows[ref_idx][0], "ref": ref,
            "close_peak": round(best["close"][0], 4), "close_day": best["close"][1],
            "reg_peak": round(best["reg"][0], 4), "reg_day": best["reg"][1],
            "ext_peak": round(best["ext"][0], 4), "ext_day": best["ext"][1], "ext_where": best["ext"][2],
            "realized_idx": realized[0] if realized else None, "realized_day": realized[1] if realized else None,
            "realized_where": realized[2] if realized else None, "complete": complete, "days": days}


def control_moved_ext(rows, sess, cov_from, k, win=20, ahead=20, jump=JUMP, run=RUN):
    """The sealed `control_moved` with the extended numerator (thresholds, references and window unchanged):
    in [k−19, k+20] a day whose pre/regular high ≥ 1.5 × the prior regular close, or whose after-hours high ≥ 1.5 × its own
    regular close, or whose highest price ≥ 1.7 × the running minimum regular close since k−20 ⟶ True (moved).
    No move found but a day lacked extended coverage ⟶ None (unknown — never treated as "did not explode")."""
    lo = max(1, k - win + 1)
    hi = min(len(rows) - 1, k + ahead)
    run_min = float(rows[lo - 1][4])
    unknown = False
    for j in range(lo, hi + 1):
        d, h, c = rows[j][0], float(rows[j][2]), float(rows[j][4])
        prev = float(rows[j - 1][4])
        covered = sess is not None and cov_from is not None and d >= cov_from
        pr, _w, aft, known = day_ext(d, h, sess, covered)
        unknown = unknown or not known
        top = max(pr, aft) if aft is not None else pr
        if prev > 0 and pr / prev >= jump:
            return True
        if aft is not None and c > 0 and aft / c >= jump:
            return True
        if run_min > 0 and top / run_min >= run:
            return True
        if c < run_min:
            run_min = c
    return None if unknown else False


def realizations(rows, sess, cov_from, lookback=20, gain=GAIN, group=10, since=None):
    """Generation only: days whose highest extended price ≥ gain × the lowest regular close of the previous `lookback`
    sessions (the register's run reference with the extended numerator); days within `group` sessions of the previous kept
    one belong to the same move ⟶ [(idx, day, where, ratio)] earliest of each move."""
    out = []
    for j in range(lookback, len(rows)):
        d = rows[j][0]
        if since and d < since:
            continue
        lo = min(float(r[4]) for r in rows[j - lookback:j])
        if not lo > 0:
            continue
        covered = sess is not None and cov_from is not None and d >= cov_from
        pr, w, aft, _k = day_ext(d, float(rows[j][2]), sess, covered)
        top, where = pr, w
        if aft is not None and aft > top:
            top, where = aft, "after " + (((sess or {}).get(d) or {}).get("aft") or [0, "?"])[1]
        if top >= gain * lo and not (out and j - out[-1][0] <= group):
            out.append((j, d, where, round(top / lo, 3)))
    return out


def split_unadjusted(rows, splits, lo_day, hi_day, tol=1.25):
    """Reverse splits (factor < 1, from `faisal_engine/data/rank/splits.json`) dated in (lo_day, hi_day] whose regular close
    jumps on that day by ≈ 1/factor (within ×`tol`) ⟶ the bars are NOT split-adjusted there (the WOK case) ⟶ [day, …].
    A genuine +1/factor move landing exactly on a split day is not credited (conservative)."""
    import math
    out = []
    ix = {r[0]: i for i, r in enumerate(rows)}
    for d, f in splits or []:
        try:
            f = float(f)
        except (TypeError, ValueError):
            continue
        if not (0 < f < 1) or not (lo_day < d <= hi_day) or d not in ix or ix[d] < 1:
            continue
        a, b = float(rows[ix[d] - 1][4]), float(rows[ix[d]][4])
        if a > 0 and b > 0 and abs(math.log(b / a) - math.log(1.0 / f)) <= math.log(tol):
            out.append(d)
    return out


def scale_ok(rows, sess):
    """Intraday/daily scale check: median of (pure-regular hourly high ÷ daily regular high) over shared days in [0.7, 1.05]
    (a split adjusted in one series and not the other shows as ≈ the split factor). None when fewer than 5 shared days."""
    r = sorted(s["rh"] / float(x[2]) for x in rows for s in [((sess or {}).get(x[0]) or {})]
               if s.get("rh") and float(x[2]) > 0)
    if len(r) < 5:
        return None
    m = r[len(r) // 2]
    return 0.7 <= m <= 1.05


def load():
    """{"meta", "daily": {sym: rows}, "sess": {sym: {day: {"pre"?, "aft"?}}} (days with an extended bar only),
    "cov": {sym: first hourly day | None}, "scale": {sym: bool | None}, "raw": {sym: [[ts, high, low], …]}}."""
    return json.load(gzip.open(EXT_FILE, "rt", encoding="utf-8"))


# ── runner-side fetch ────────────────────────────────────────────────────────────────────────────────
def main():
    sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "1")
    import tv_data as TV
    import Super_stock as S
    syms = [x.strip().upper() for x in open(SYMS_FILE, encoding="utf-8").read().split() if x.strip()]
    keep_raw = set(x.strip().upper() for x in open(RAW_SYMS_FILE, encoding="utf-8").read().split() if x.strip())
    t0 = time.monotonic()
    tmap = S._tv_ticker_map(None)
    full = {s: S._tv_full_name(s, tmap) for s in syms}
    names = sorted(set(full.values()))
    g1 = S.TVBarsGate(budget=False)
    daily = TV.fetch_many(names, interval="1D", n=DAILY_N, workers=S.TV_BARS_WORKERS, gate=g1,
                          stagger=S.TV_BARS_STAGGER_S, retry_pass=True, retry_pause=S.TV_BARS_RETRY_PAUSE_S) or {}
    t1 = time.monotonic()
    g2 = S.TVBarsGate(budget=False)
    hourly = TV.fetch_many(names, interval="60", n=HOURS_N, extended=True, workers=S.TV_BARS_WORKERS, gate=g2,
                           stagger=S.TV_BARS_STAGGER_S, retry_pass=True, retry_pause=S.TV_BARS_RETRY_PAUSE_S) or {}
    t2 = time.monotonic()
    out = {"daily": {}, "sess": {}, "cov": {}, "scale": {}, "raw": {}}
    cnt = {"asked": len(syms), "daily_ok": 0, "daily_none": [], "daily_empty": [], "hourly_ok": 0, "hourly_none": [],
           "hourly_empty": []}
    for s in syms:
        db = daily.get(full[s])
        if db is None:
            cnt["daily_none"].append(s)
        elif not db:
            cnt["daily_empty"].append(s)
        else:
            rows = [[TV.ny_day(b[0]), round(b[1], 6), round(b[2], 6), round(b[3], 6), round(b[4], 6)] for b in db
                    if TV.ny_day(b[0]) >= DAILY_START]
            if rows:
                out["daily"][s] = rows
                cnt["daily_ok"] += 1
            else:
                cnt["daily_empty"].append(s)
        hb = hourly.get(full[s])
        if hb is None:
            cnt["hourly_none"].append(s)
            out["cov"][s] = None
            continue
        if not hb:
            cnt["hourly_empty"].append(s)
            out["cov"][s] = None
            continue
        cnt["hourly_ok"] += 1
        full_sess = day_sessions([(b[0], b[2]) for b in hb])
        out["scale"][s] = scale_ok(out["daily"].get(s) or [], full_sess)
        out["sess"][s] = {d: {k: v[k] for k in ("pre", "aft") if v.get(k)} for d, v in full_sess.items()
                          if v.get("pre") or v.get("aft")}
        out["cov"][s] = TV.ny_day(hb[0][0])
        if s in keep_raw:
            out["raw"][s] = [[int(b[0]), round(b[2], 6), round(b[3], 6)] for b in hb]
    out["meta"] = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "source": "tradingview · 1D regular + 60 extended · adjustment=splits · no login",
                   "daily_n": DAILY_N, "hours_n": HOURS_N, "daily_start": DAILY_START,
                   "map": "scan" if tmap else "nasdaq", "secs_daily": round(t1 - t0, 1), "secs_hourly": round(t2 - t1, 1),
                   "gate_daily": g1.summary(), "gate_hourly": g2.summary(), "calls": dict(TV.CALLS),
                   "counts": {k: (v if isinstance(v, int) else len(v)) for k, v in cnt.items()},
                   "missing": {k: v for k, v in cnt.items() if isinstance(v, list)}}
    os.makedirs(DATA, exist_ok=True)
    with gzip.open(EXT_FILE, "wt", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(json.dumps(out["meta"]["counts"]), json.dumps({k: out["meta"][k] for k in ("secs_daily", "secs_hourly",
                                                                                      "gate_daily", "gate_hourly")}))


if __name__ == "__main__":
    main()
