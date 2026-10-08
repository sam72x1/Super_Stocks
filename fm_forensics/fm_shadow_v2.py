"""🕯️ READY_NOW_V2 — مُقيِّمٌ ظلّيٌّ قراءةً فقط (العقد `fm_forensics/READY_NOW_V2_prereg.md` · المواصفة `READY_NOW_V2_SPEC.md`).

ليس إنتاجًا · ليس V4 · لا تلغرام · لا حالةَ إنتاج · لا اسمَ سهمٍ في المنطق. يقرأ ملفَّ شموع المِجَسّ (`fm_forensics/data/bars_*.json.gz`)
ويُخرج حالةَ كلّ رمزٍ لكلّ جلسة (UNSEEN/IDENTITY/FOCUS/WATCH/READY/TRIGGER/INVALIDATED) بالقواعد المسجَّلة مسبقًا، ثمّ يقيس
المقارِنين (READY NOW الحاليّ من لقطات git · والشروط الثلاثة المقرَّبة) على VAL وHOLDOUT ويكتب `READY_NOW_V2_SHADOW_RESULTS.csv`.
كلُّ رقمٍ في العقد ثابتٌ قبل أيّ نتيجة: 3/5 جلسات · منطقة 15% · سحب ≤ 13% · RSI 33 · إبطال 0.87 · نافذة 30 · استعادة خلال جلستين."""
import csv
import glob
import gzip
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# ── ثوابتُ العقد (لا تُعاير) ──
WIN, HOLD_WATCH, HOLD_READY, ZONE, SWEEP_MAX, RSI_MAX, RECLAIM_N, BOUNCE = 30, 3, 5, 0.15, 0.13, 33.0, 2, 0.10
INVALID = 1.0 - SWEEP_MAX
MIN_BARS = 40
# M1-M5 الحيّة (تُقرأ بالاسم من البوت إن أمكن · وإلّا القيمُ المطبوعة في الأساس 2026-10-08)
LIVE = {"M1": 0.40, "M2_LO": 71.72, "M2_HI": 99.95, "M3": 78.27, "M4": 120.0, "M5": 14300.0}


def _rsi(closes, period=14):
    """RSI14 بصيغة `Super_stock.rsi` (EWM alpha=1/period · adjust=False) بلا pandas."""
    out = [50.0] * len(closes)
    if len(closes) < period + 1:
        return out
    ag = al = 0.0
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        g, l = max(d, 0.0), max(-d, 0.0)
        if i <= period:
            ag += g / period; al += l / period
            if i == period:
                out[i] = 100.0 - 100.0 / (1.0 + (ag / al if al else float("inf"))) if (ag or al) else 50.0
            continue
        ag = ag + (g - ag) / period; al = al + (l - al) / period
        out[i] = 100.0 - 100.0 / (1.0 + (ag / al)) if al else 100.0
    return out


def identity(bars, i, splits):
    """M1–M5 على الشموع ≤ i · مع `split_restart`: مرجعُ M2 هو الأعلى بعد آخر تقسيمٍ عكسيّ داخل النافذة إن عُرف."""
    if i + 1 < MIN_BARS:
        return "UNKNOWN", {}
    w = bars[max(0, i - 251): i + 1]
    closes = [b[4] for b in w]; highs = [b[2] for b in w]; lows = [b[3] for b in w]; vols = [b[5] for b in w]
    price = closes[-1]
    if price < LIVE["M1"]:
        return "REJECT_M1", {}
    restart = 0
    if splits:
        for d, r in splits:
            if r and r < 1.0 and w[0][0] <= d <= w[-1][0]:
                restart = max(restart, next((k for k, b in enumerate(w) if b[0] >= d), 0))
    hi52 = max(highs[restart:]) if restart < len(highs) else max(highs)
    drop = (1.0 - price / hi52) * 100.0 if hi52 else 0.0
    if drop > LIVE["M2_HI"]:
        return "REJECT_M2_HI", {"drop": drop, "restart": restart}
    if drop < LIVE["M2_LO"]:
        return "REJECT_M2_LO", {"drop": drop}
    lo_before = min(lows[restart:]) if restart < len(lows) else min(lows)
    spike = (hi52 / lo_before - 1.0) * 100.0 if lo_before else 0.0
    if spike < LIVE["M3"]:
        return "REJECT_M3", {"spike": spike}
    base = w[-15:]
    rng = (max(b[2] for b in base) / min(b[3] for b in base) - 1.0) * 100.0 if min(b[3] for b in base) else 999
    if rng > LIVE["M4"]:
        return "REJECT_M4", {"range": rng}
    dv = sum(c * v for c, v in zip(closes[-20:], vols[-20:])) / max(1, len(closes[-20:]))
    if dv < LIVE["M5"]:
        return "REJECT_M5", {"dv": dv}
    return "IDENTITY", {"drop": drop, "spike": spike, "range": rng, "dv": dv, "restart": restart}


def run_symbol(bars, splits=None):
    """تُرجع لكلّ جلسة: (التاريخ · الحالة · L · hold · rsi_min · السبب). حتميّةٌ وبلا نظرٍ للأمام (الشموعُ ≤ i فقط)."""
    rsis = _rsi([b[4] for b in bars])
    out = []
    L = None; L_i = None; rsi_min = 101.0; bounced = False; sweep_i = None; state = "UNSEEN"
    for i, b in enumerate(bars):
        ident, info = identity(bars, i, splits)
        if ident != "IDENTITY":
            state = "UNSEEN" if ident == "UNKNOWN" else ident
            L = None; L_i = None; rsi_min = 101.0; bounced = False; sweep_i = None
            out.append((b[0], state, None, 0, None, ident)); continue
        lows30 = [x[3] for x in bars[max(0, i - WIN + 1): i + 1]]
        cur_low = min(lows30)
        if L is None or cur_low < L * INVALID and sweep_i is None:
            # قاعٌ جديد (أوّلُ قاعٍ · أو كسرٌ أعمق من مدى السحب بلا استعادة) ⟵ FOCUS من القاع الجديد
            if L is not None and cur_low < L * INVALID:
                out.append((b[0], "INVALIDATED", L, 0, None, "break>13%"))
            L = cur_low; L_i = i; rsi_min = rsis[i]; bounced = False; sweep_i = None
            state = "FOCUS"
            out.append((b[0], state, L, 0, round(rsi_min, 1), "new base")); continue
        rsi_min = min(rsi_min, rsis[i])
        low_i, close_i, high_i = b[3], b[4], b[2]
        # سحبٌ ثمّ استعادة
        if low_i < L * (1.0 - 0.05) and low_i >= L * INVALID:
            sweep_i = i if sweep_i is None else sweep_i
        reclaimed = sweep_i is not None and close_i > L and i - sweep_i <= RECLAIM_N
        if sweep_i is not None and i - sweep_i > RECLAIM_N and close_i <= L:
            # لم يستعد خلال جلستين ⟵ القاعُ الجديد هو ذيلُ السحب
            L = min(L, bars[sweep_i][3]); L_i = sweep_i; sweep_i = None; bounced = False
        hold = i - L_i
        if high_i >= L * (1.0 + BOUNCE):
            bounced = True
        in_zone = L <= close_i <= L * (1.0 + ZONE)
        if reclaimed:
            state = "TRIGGER"; reason = f"sweep {((1 - bars[sweep_i][3] / L) * 100):.1f}% reclaimed"; sweep_i = None
        elif hold >= HOLD_WATCH and rsi_min <= RSI_MAX and in_zone and (hold >= HOLD_READY or bounced):
            state = "READY"; reason = "zone+hold/bounce+rsi"
        elif hold >= HOLD_WATCH and rsi_min <= RSI_MAX:
            state = "WATCH"; reason = "hold≥3+rsi≤33"
        else:
            state = "FOCUS"; reason = "one touch / rsi>33 / hold<3"
        out.append((b[0], state, L, hold, round(rsi_min, 1), reason))
    return out


def three_cond_approx(bars, i, rsis):
    """تقريبُ «شروطك الثلاثة» على الشموع اليوميّة وحدَها: RSI<33 ∧ ثباتُ 5 جلسات فوق أدنى low في 25 ∧ لا انفجار 50% في 5.
    الفلوتُ والمتاح مجهولان ⟵ يُعدّان عابرَين (تفاؤلٌ للمقارِن كما نصّ العقد)."""
    if i < 30:
        return False
    w = bars[i - 24: i + 1]; lo = min(x[3] for x in w); lo_i = next(k for k, x in enumerate(w) if x[3] == lo)
    held = (len(w) - 1 - lo_i) >= 5
    recent = bars[i - 5: i + 1]; expl = max(x[2] for x in recent) / min(x[4] for x in recent) - 1.0 >= 0.5 if min(x[4] for x in recent) else False
    return rsis[i] < RSI_MAX and held and not expl


def load_bars(path=None):
    path = path or (sorted(glob.glob(os.path.join(HERE, "data", "bars_*.json.gz"))) or [None])[-1]
    if not path:
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def wilson(k, n, z=1.96):
    if n <= 0:
        return (None, None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(p, 4), round((c - r) / d, 4), round((c + r) / d, 4))


def main(argv):
    data = load_bars(argv[1] if len(argv) > 1 else None)
    if not data:
        print("⛔ لا ملفَّ شموع — شغّل fm_bars_probe.yml أوّلًا"); return 2
    anchors = {"DKI", "SXTC", "HUBC", "CRE"}   # مستثناةٌ من كلّ درجة (العقد) — تُطبع حالتُها وصفًا فقط
    states = {}
    for s, bars in data["daily"].items():
        sp = (data.get("splits") or {}).get(s)
        states[s] = run_symbol(bars, sp)
    os.makedirs(os.path.join(HERE, "shadow"), exist_ok=True)
    with open(os.path.join(HERE, "shadow", "v2_states.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["symbol", "date", "state", "L", "hold", "rsi_min", "reason"])
        for s, rows in states.items():
            for r in rows:
                w.writerow([s, *r])
    # ── HOLDOUT: منفجرو السجلّ ≥100% (بلا المراسي) مقابل ضبطٍ مطابَقٍ بالتاريخ ──
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json")))
    movers = [e for e in wl.get("explosions", []) if (e.get("gain") or 0) >= 100 and e["symbol"] not in anchors and e["symbol"] in states]
    import random; rnd = random.Random(20261008)
    pool = [s for s in states if s not in anchors and s not in {e["symbol"] for e in movers}]
    def state_before(sym, day, n=14):
        rows = [r for r in states[sym] if r[0] <= day][-n:]
        return [r[1] for r in rows]
    rank = {"UNSEEN": 0, "REJECT_M1": 0, "REJECT_M2_HI": 0, "REJECT_M2_LO": 0, "REJECT_M3": 0, "REJECT_M4": 0, "REJECT_M5": 0,
            "INVALIDATED": 0, "FOCUS": 1, "WATCH": 2, "READY": 3, "TRIGGER": 4}
    res = []
    m_watch = m_ready = c_watch = c_ready = n_m = n_c = 0
    rdays = json.load(open(os.path.join(ROOT, "fm_forensics", "shadow", "ready_days.json"))) if os.path.exists(os.path.join(ROOT, "fm_forensics", "shadow", "ready_days.json")) else {}
    cur_hits = 0; tc_hits = 0
    for e in movers:
        st = state_before(e["symbol"], e["expl_date"])
        if not st:
            continue
        n_m += 1
        best = max(rank.get(x, 0) for x in st)
        m_watch += best >= 2; m_ready += best >= 3
        ds = rdays.get(e["symbol"], []); cur_hits += any(e["expl_date"] >= d >= str(e["expl_date"])[:8] + "01" for d in ds)
        bars = data["daily"][e["symbol"]]; rs = _rsi([b[4] for b in bars])
        idx = [k for k, b in enumerate(bars) if b[0] <= e["expl_date"]]
        tc_hits += any(three_cond_approx(bars, k, rs) for k in idx[-14:]) if idx else 0
        ctrl = rnd.choice(pool) if pool else None
        if ctrl:
            sc = state_before(ctrl, e["expl_date"])
            if sc:
                n_c += 1; b2 = max(rank.get(x, 0) for x in sc); c_watch += b2 >= 2; c_ready += b2 >= 3
        res.append(dict(set="HOLDOUT", symbol=e["symbol"], date=e["expl_date"], gain=e.get("gain"), v2_best_state_14d=max(st, key=lambda x: rank.get(x, 0)),
                        current_ready_14d=bool(ds and any(d <= e["expl_date"] for d in ds[-14:])), three_cond_14d=bool(tc_hits)))
    summary = [
        dict(set="HOLDOUT", metric="movers_with_bars", value=n_m, wilson=""),
        dict(set="HOLDOUT", metric="V2 WATCH+ within 14d (movers)", value=m_watch, wilson=wilson(m_watch, n_m)),
        dict(set="HOLDOUT", metric="V2 READY+ within 14d (movers)", value=m_ready, wilson=wilson(m_ready, n_m)),
        dict(set="HOLDOUT", metric="V2 WATCH+ (matched control)", value=c_watch, wilson=wilson(c_watch, n_c)),
        dict(set="HOLDOUT", metric="V2 READY+ (matched control)", value=c_ready, wilson=wilson(c_ready, n_c)),
        dict(set="HOLDOUT", metric="THREE-COND approx within 14d (movers)", value=tc_hits, wilson=wilson(tc_hits, n_m)),
        dict(set="HOLDOUT", metric="CURRENT READY NOW within 14d (movers, from git snapshots)", value=cur_hits, wilson=wilson(cur_hits, n_m)),
    ]
    with open(os.path.join(HERE, "READY_NOW_V2_SHADOW_RESULTS.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["set", "metric", "value", "wilson_p_lo_hi"])
        for r in summary:
            w.writerow([r["set"], r["metric"], r["value"], r["wilson"]])
        w.writerow([]); w.writerow(["set", "symbol", "date", "gain", "v2_best_state_14d", "current_ready_14d", "three_cond_14d"])
        for r in res:
            w.writerow([r["set"], r["symbol"], r["date"], r["gain"], r["v2_best_state_14d"], r["current_ready_14d"], r["three_cond_14d"]])
    for r in summary:
        print(r)
    for a in sorted(anchors):
        if a in states:
            rows = states[a][-25:]
            print(a, "آخر 25 جلسة:", " ".join(f"{d[5:]}:{s[:3]}" for d, s, *_ in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
