"""Faisal condition atlas — point-in-time feature build (research only · offline · read-only).

For every pivot-day row of the READY NOW discovery dataset (`readynow/disc/data/rows.csv.gz`: identity M1-M3 from
bars <= t, corrected onset labels) this adds the atlas columns that earlier studies did not compute: validity grades,
Faisal's cycle and sweep conditions, compression near the annual low, indicator conditions (MACD cross, Klinger,
Full-Stochastic chop, Williams %R turn), gaps above, up/down volume, support touches, and candle patterns.

Every value at session index i is computed from bars[: i + 1] only. Arrays are computed once per symbol with causal
operations (rolling windows, EMA recursions, the Klinger recursion), and `point_features(b, i)` recomputes the same
values on bars truncated at i; `test_ca.py` compares the two on a random sample (look-ahead guard).

Candles use the bot's own detector `Super_stock._patterns_at` (hammer, inverted hammer, doji at support, green
marubozu, bullish engulfing, piercing «اختراق صاعد», morning star, three white soldiers) with the support = lowest low
of the last 30 sessions, as in `detect_candle_patterns`; the hanging man uses `_hanging_man`'s rule; the patterns the
bot does not detect (harami, inside bar, spinning top, shooting star, plain doji, long lower wick, red hammer, the
«group candle» proxy) are defined in `candles_at` below with explicit formulas.

Outputs: condition_atlas/data/ca_rows.csv.gz (sym, t + atlas columns) and data/build_meta.json
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_build.py   (--check regenerates and compares)
"""
import csv
import gzip
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(RN))
DATA = os.path.join(HERE, "data")
DISC = os.path.join(RN, "disc", "data")
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import pandas as pd                                                       # noqa: E402
import rn_build as B                                                      # noqa: E402  (READYNOW, read-only)

R = B.R
LOOK_LOW = B.LOOK_LOW            # 25 — the base-low window used by every READY NOW study (the tool's PIVOT_LOOKBACK)
YEAR = 250                       # «قاع سنوي» = lowest low of the last 250 sessions
SPIKE_RUN = 20                   # prior-spike run window (20 sessions, the bot's PRIOR_SPIKE_WINDOW reading)
CYCLE = 120                      # cycle-peak window (sessions)
SPLIT_WIN = 120                  # split-cycle window in sessions for the ÷2 band and the «not risen > 20%» check
SPLIT_DUP_DAYS = 7               # the bot's SPLIT_DUP_DAYS: same ratio within 7 days = one split
SUPPORT_WIN = 30                 # `detect_candle_patterns`: support = lowest low of the last 30 sessions
BOT_PATTERNS = {"مطرقة": "k_hammer", "مطرقة مقلوبة": "k_invhammer", "دوجي عند الدعم": "k_doji_sup",
                "ماروبوزو أخضر": "k_marubozu", "ابتلاع صاعد": "k_engulf", "اختراق صاعد": "k_piercing",
                "نجمة الصباح": "k_mstar", "ثلاثة جنود بيض": "k_soldiers"}
CANDLES = ("k_hammer", "k_hammer_red", "k_invhammer", "k_doji", "k_doji_sup", "k_marubozu", "k_engulf", "k_piercing",
           "k_mstar", "k_soldiers", "k_harami", "k_inside", "k_spin", "k_shoot", "k_hangman", "k_longwick",
           "k_groupc")
COLS = (["a_spike", "a_drop", "a_low250", "a_boom20", "a_rsplit_age", "a_rsplit_n", "a_split_rise", "a_half_ratio",
         "a_grp10", "b_rsi_min10", "b_peak_age", "b_test_ago", "b_sweep", "b_sweep_depth", "b_range5", "b_vmax3",
         "b_macd_x9", "b_gap_max", "b_kvo_up", "b_kvo_x5", "b_chop30", "b_wr_turn", "b_updn_v10", "b_touch5",
         "b_above3050", "b_sma20_slope5", "t_dip_low"]
        + list(CANDLES) + [k + "_3" for k in CANDLES] + ["k_wick_bounce", "k_doji_engulf"])


def _r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def _rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def reverse_splits(splits_sym, dates):
    """Reverse splits (ratio < 1) as session indices (first session on or after the split date), duplicates of the
    same ratio within SPLIT_DUP_DAYS calendar days collapsed to the earliest (the bot's `_dedupe_reverse_splits`)."""
    import datetime as dt
    out, last = [], None
    for d, r in sorted((d, float(r)) for d, r in (splits_sym or []) if r and float(r) < 1.0):
        if last and last[1] == r and (dt.date.fromisoformat(d) - dt.date.fromisoformat(last[0])).days <= SPLIT_DUP_DAYS:
            continue
        last = (d, r)
        k = int(np.searchsorted(np.array(dates), d, side="left"))
        if k < len(dates):
            out.append((k, d, r))
    return out


def candles_at(o, h, l, c, i):
    """Candle flags at bar i (bars <= i). The bot's detector supplies its eight reversal patterns; the rest are
    defined here (body = |c − o|, rng = h − l, up/dn = upper/lower wick):
      plain doji        body <= DOJI_BODY_MAX × rng (anywhere)
      red hammer        the bot's hammer with c < o («شمعة حمرا = صعود قصير الأمد», IMG_0569)
      harami (bullish)  previous red with body >= 0.4 × its range; today green, body inside the previous body,
                        body <= 0.6 × previous body
      inside bar        h <= previous h and l >= previous l
      spinning top      body <= 0.3 × rng, up >= body, dn >= body, not a doji
      shooting star     the bot's inverted-hammer shape (body <= 0.4 rng, up >= 2 body, small lower wick) with the
                        close within 3% of the 20-session high (after a rise)
      hanging man       the bot's hammer shape with the close within 3% of the 20-session high (`_hanging_man`)
      long lower wick   dn >= 0.5 × rng and dn >= 2 × body (any upper wick) — «ذيل شمعه طويل»
      group candle      rng >= 20% of the previous close and body <= 0.25 × rng («شمعه طويله … بدون جسم», a daily
                        proxy of Faisal's 4-hour rule in X_20260827_checklist_7points)"""
    S = R.S()
    out = {k: 0 for k in CANDLES}
    if i < 2:
        return out
    lo = max(0, i - SUPPORT_WIN + 1)
    support = float(np.min(l[lo: i + 1]))
    for p in S._patterns_at(o, h, l, c, i, support):
        if p in BOT_PATTERNS:
            out[BOT_PATTERNS[p]] = 1
    body, rng = abs(c[i] - o[i]), h[i] - l[i]
    if rng <= 0:
        return out
    up, dn = h[i] - max(o[i], c[i]), min(o[i], c[i]) - l[i]
    small_up = up <= max(body * 0.5, 0.10 * rng)
    small_dn = dn <= max(body * 0.5, 0.10 * rng)
    hammer_shape = body <= 0.40 * rng and dn >= 2.0 * body and small_up
    inv_shape = body <= 0.40 * rng and up >= 2.0 * body and small_dn
    hi20 = float(np.max(h[max(0, i - 19): i + 1]))
    near_top = hi20 > 0 and c[i] >= hi20 * 0.97
    doji_max = float(S.CONFIG["DOJI_BODY_MAX"])
    out["k_doji"] = int(body <= doji_max * rng)
    out["k_hammer_red"] = int(out["k_hammer"] and c[i] < o[i])
    pb, pr = abs(c[i - 1] - o[i - 1]), h[i - 1] - l[i - 1]
    out["k_harami"] = int(c[i - 1] < o[i - 1] and pr > 0 and pb >= 0.4 * pr and c[i] > o[i] and o[i] >= c[i - 1]
                          and c[i] <= o[i - 1] and body <= 0.6 * pb)
    out["k_inside"] = int(h[i] <= h[i - 1] and l[i] >= l[i - 1])
    out["k_spin"] = int(body <= 0.3 * rng and up >= body and dn >= body and not out["k_doji"])
    out["k_shoot"] = int(inv_shape and near_top)
    out["k_hangman"] = int(hammer_shape and near_top)
    out["k_longwick"] = int(dn >= 0.5 * rng and dn >= 2.0 * body)
    out["k_groupc"] = int(c[i - 1] > 0 and rng >= 0.20 * c[i - 1] and body <= 0.25 * rng)
    return out


def symbol_arrays(b, rsplits):
    """Every atlas column at every session of one symbol (value at i from bars <= i)."""
    S = R.S()
    o, h, l, c, v = b["o"], b["h"], b["l"], b["c"], b["v"]
    n = len(c)
    C, H, L, V = pd.Series(c), pd.Series(h), pd.Series(l), pd.Series(v)
    z = B.series(b)
    out = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        run20 = C / C.shift(1).rolling(SPIKE_RUN, min_periods=SPIKE_RUN).min() - 1.0
        out["a_spike"] = (run20.rolling(252, min_periods=1).max() * 100.0).to_numpy()
        out["a_drop"] = ((1.0 - C / H.rolling(252, min_periods=1).max()) * 100.0).to_numpy()
        out["a_low250"] = ((C / L.rolling(YEAR, min_periods=YEAR).min() - 1.0) * 100.0).to_numpy()
        rise = H / C.shift(1).rolling(5, min_periods=5).min() - 1.0
        out["a_boom20"] = (rise.rolling(20, min_periods=1).max() * 100.0).to_numpy()
    # splits (session index of each reverse split; known on and after that session)
    age = np.full(n, np.nan)
    cnt = np.zeros(n)
    srise = np.full(n, np.nan)
    half = np.full(n, np.nan)
    for k, _d, _r0 in rsplits:
        cnt[k:] += 1
    for i in range(n):
        ks = [k for k, _d, _r0 in rsplits if k <= i]
        if not ks:
            continue
        k = ks[-1]
        if i - k <= YEAR:
            age[i] = i - k
        if i - k <= SPLIT_WIN and o[k] > 0:
            hi = float(np.max(h[k: i + 1]))
            srise[i] = (hi / o[k] - 1.0) * 100.0
            half[i] = c[i] / (hi / 2.0) if hi > 0 else np.nan
    out["a_rsplit_age"], out["a_rsplit_n"], out["a_split_rise"], out["a_half_ratio"] = age, cnt, srise, half
    # group-candle proxy count over the last 10 sessions, and the candles
    kc = {k: np.zeros(n) for k in CANDLES}
    for i in range(n):
        for k, x in candles_at(o, h, l, c, i).items():
            kc[k][i] = x
    for k in CANDLES:
        out[k] = kc[k]
        out[k + "_3"] = pd.Series(kc[k]).rolling(3, min_periods=1).max().to_numpy()
    out["a_grp10"] = pd.Series(kc["k_groupc"]).rolling(10, min_periods=1).sum().to_numpy()
    # RSI minimum over the last 10 sessions (Faisal's 23–27 band; the app reads the lowest of the last 10)
    out["b_rsi_min10"] = pd.Series(z["rsi"]).rolling(10, min_periods=1).min().to_numpy()
    # cycle peak age: sessions since the highest high of the last CYCLE sessions (ties: the latest)
    pk = np.full(n, np.nan)
    for i in range(n):
        w = h[max(0, i - CYCLE + 1): i + 1]
        j = len(w) - 1 - int(np.argmax(w[::-1]))
        pk[i] = len(w) - 1 - j
    out["b_peak_age"] = pk
    # the base low of the last LOOK_LOW sessions, its first day, and the test peak after it
    tago = np.full(n, np.nan)
    touch = np.full(n, np.nan)
    sweep = np.zeros(n)
    sdep = np.full(n, np.nan)
    pbase = L.shift(1).rolling(LOOK_LOW, min_periods=LOOK_LOW).min().to_numpy()   # min low of [j−25, j−1]
    for i in range(LOOK_LOW, n):
        lo_w = l[i - LOOK_LOW + 1: i + 1]
        low = float(lo_w.min())
        if not low > 0:
            continue
        lowday = i - LOOK_LOW + 1 + int(np.argmax(lo_w <= low))
        seg = h[lowday: i + 1]
        tago[i] = (i - lowday) - int(np.argmax(seg))      # sessions since the first highest high after the low day
        touch[i] = float(np.sum(l[max(0, i - 19): i + 1] <= low * 1.05))
        # sweep: a low 5–15% below the prior 25-session base within the last 10 sessions, close back above that base
        best = None
        for j in range(max(LOOK_LOW, i - 9), i + 1):
            base = pbase[j]
            if base > 0 and base * 0.85 <= l[j] <= base * 0.95 and c[i] > base:
                dep = (1.0 - l[j] / base) * 100.0
                best = dep if best is None else max(best, dep)
        if best is not None:
            sweep[i], sdep[i] = 1, best
    out["b_test_ago"], out["b_touch5"], out["b_sweep"], out["b_sweep_depth"] = tago, touch, sweep, sdep
    with np.errstate(divide="ignore", invalid="ignore"):
        out["b_range5"] = ((H.rolling(5, min_periods=5).max() / L.rolling(5, min_periods=5).min() - 1.0)
                           * 100.0).to_numpy()
        base = V.rolling(50).median().shift(11)
        v1x = (V / base.where(base > 0)).to_numpy()
    out["b_vmax3"] = pd.Series(v1x).rolling(3, min_periods=1).max().to_numpy()
    up = z["macd"] > z["macd_sig"]
    cross = np.zeros(n, dtype=bool)
    cross[1:] = up[1:] & ~up[:-1]
    out["b_macd_x9"] = (pd.Series(cross.astype(float)).rolling(9, min_periods=1).max().to_numpy() > 0) & up
    # largest unfilled gap-down above the close within the last CYCLE sessions
    gaps = []                                              # (j, top, bottom, first session at or after j filling it)
    for j in range(1, n):
        top, bot = l[j - 1], h[j]
        if bot < top and bot > 0:
            f = next((k for k in range(j + 1, n) if h[k] >= top), n)
            gaps.append((j, top, bot, f))
    gap = np.full(n, np.nan)
    for i in range(1, n):
        best = 0.0
        for j, top, bot, f in gaps:
            if i - CYCLE + 1 <= j <= i and f > i and bot >= c[i]:
                best = max(best, (top / bot - 1.0) * 100.0)
        gap[i] = best
    out["b_gap_max"] = gap
    kvo, ksig = S.klinger(H, L, C, V)
    ku = (kvo > ksig).to_numpy()
    kx = np.zeros(n, dtype=bool)
    kx[1:] = ku[1:] & ~ku[:-1]
    out["b_kvo_up"] = ku
    out["b_kvo_x5"] = (pd.Series(kx.astype(float)).rolling(5, min_periods=1).max().to_numpy() > 0) & ku
    kline, _d = S.full_stoch(H, L, C)
    out["b_chop30"] = kline.diff().abs().rolling(29, min_periods=29).mean().to_numpy()
    wr = S.williams_r(H, L, C).to_numpy()
    turn = np.zeros(n, dtype=bool)
    turn[1:] = (wr[1:] > -80.0) & (wr[:-1] <= -80.0)
    out["b_wr_turn"] = pd.Series(turn.astype(float)).rolling(3, min_periods=1).max().to_numpy() > 0
    upd = np.full(n, np.nan)
    for i in range(10, n):
        cc, pc, vv = c[i - 9: i + 1], c[i - 10: i], v[i - 9: i + 1]
        u, d = vv[cc > pc], vv[cc < pc]
        if len(u) and len(d) and d.mean() > 0:
            upd[i] = u.mean() / d.mean()
    out["b_updn_v10"] = upd
    out["b_above3050"] = (c > z["ema30"]) & (c > z["ema50"])
    sma20 = C.rolling(20).mean()
    out["b_sma20_slope5"] = ((sma20 / sma20.shift(5) - 1.0) * 100.0).to_numpy()
    # «قبل يصعد بيوم يتم ضغط السهم … قريبا من القاع» (IMG_0531): today's low back within 5% of the prior 25-session
    # low after a high at least 10% above it during the previous 5 sessions
    dip = np.zeros(n)
    for i in range(LOOK_LOW + 1, n):
        base = float(l[i - LOOK_LOW: i].min())
        if base > 0 and l[i] <= base * 1.05 and float(np.max(h[i - 5: i])) >= base * 1.10:
            dip[i] = 1
    out["t_dip_low"] = dip
    # long lower wick at the base low, close now at least 5% above the wick (TG_57874)
    wb = np.zeros(n)
    for i in range(LOOK_LOW, n):
        low = float(l[i - LOOK_LOW + 1: i + 1].min())
        for j in range(max(0, i - 2), i + 1):
            if kc["k_longwick"][j] and l[j] <= low * 1.0000001 and c[i] >= l[j] * 1.05:
                wb[i] = 1
    out["k_wick_bounce"] = wb
    # TG_58382 (third-party education): a doji or morning star must be followed by a bullish engulfing
    de = np.zeros(n)
    for i in range(2, n):
        if kc["k_engulf"][i] and (kc["k_doji"][i - 1] or kc["k_doji"][i - 2] or kc["k_mstar"][i - 1]):
            de[i] = 1
    out["k_doji_engulf"] = de
    return out


def point_features(b, rsplits, i):
    """The same columns recomputed on bars truncated at i (look-ahead guard)."""
    t = {k: (b[k][: i + 1] if k in ("o", "h", "l", "c", "v") else b[k]) for k in ("o", "h", "l", "c", "v")}
    t["d"] = b["d"][: i + 1]
    sp = [(k, d, r) for k, d, r in rsplits if k <= i]
    a = symbol_arrays(t, sp)
    return {k: a[k][i] for k in COLS}


def _val(x):
    if isinstance(x, (bool, np.bool_)):
        return int(x)
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(f) else round(f, 4)


def build(out_dir=DATA):
    _meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    rows = _rd(os.path.join(DISC, "rows.csv.gz"))
    need = {}
    for r in rows:
        need.setdefault(r["sym"], []).append(r["t"])
    out = []
    for sym in sorted(need):
        b = bars.get(sym)
        if b is None:
            continue
        rs = reverse_splits(splits.get(sym), b["d"])
        a = symbol_arrays(b, rs)
        for t in sorted(need[sym]):
            i = b["ix"].get(t)
            if i is None:
                continue
            rec = {"sym": sym, "t": t}
            rec.update({k: _val(a[k][i]) for k in COLS})
            out.append(rec)
    os.makedirs(out_dir, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["sym", "t"] + list(COLS), lineterminator="\n")
    w.writeheader()
    for r in out:
        w.writerow({k: ("" if r.get(k) is None else r[k]) for k in ["sym", "t"] + list(COLS)})
    with gzip.GzipFile(os.path.join(out_dir, "ca_rows.csv.gz"), "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))
    meta = {"rows_in": len(rows), "rows_out": len(out), "symbols": len({r["sym"] for r in out}), "columns": list(COLS),
            "missing": {k: sum(1 for r in out if r.get(k) is None) for k in COLS}}
    json.dump(meta, open(os.path.join(out_dir, "build_meta.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    return meta


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("ca_rows.csv.gz", "build_meta.json") if _digest(os.path.join(tmp, f)) != _digest(
            os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    m = build()
    print(json.dumps({k: v for k, v in m.items() if k != "missing"}, indent=1))
    print("missing:", {k: v for k, v in m["missing"].items() if v})
