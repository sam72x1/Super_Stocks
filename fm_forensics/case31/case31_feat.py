#!/usr/bin/env python3
"""🧮 `T-CASE31` — مكتبةُ حساب السمات (العقد §③) — نقيّةٌ بلا شبكة.

كلُّ سمةٍ تُحسب من شموعٍ **مقصوصةٍ عند يوم القرار** (لا شيءَ بعده): `candle_features(dfD, dfH4)` تأخذ اليوميَّ و4 ساعات كما كانا
حتى نهاية ذلك اليوم وتُخرج **أسماءَ الفهرس بالضبط** (`case31_catalog` · ذراع `AB` عدا `sh.*` الذي يُملأ من FINRA) ·
و`features_asof` تقصّ ثمّ تحسب · و`with_deltas` تضيف `.d5`/`.d10` (القيمةُ عند اليوم ناقص قيمتها قبل 5 و10 جلسات محسوبةً كما كانت يومَها).
الأعمدة: Open · High · Low · Close · Volume · والفهرسُ طوابعُ زمنٍ تصاعديّة.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import case31_catalog as CAT                                      # noqa: E402

TAIL = 520                 # الشموعُ الداخلة في حساب الإطار (تكفي متوسّط 200 وسقف «منذ التقاطع» 250)
SINCE_CAP = 250
ROUNDS = (0.5, 1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100)
FIBS = (0.236, 0.382, 0.5, 0.618, 0.786)


def _f(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if (v != v or math.isinf(v)) else v


def _last(s):
    return _f(s.iloc[-1]) if len(s) else None


def _sma(s, n):
    return s.rolling(n).mean()


def _ema(s, n):
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def _wilder(s, n):
    return s.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def _since_flip(flag, valid):
    """شموعٌ منذ آخر تغيّرٍ في `flag` (مصفوفتان منطقيّتان) عند آخر شمعة · None إن لم تكن الأخيرةُ صالحة."""
    i = len(flag) - 1
    if i < 0 or not valid[i]:
        return None
    k = 0
    while i - k - 1 >= 0 and valid[i - k - 1] and flag[i - k - 1] == flag[i] and k < SINCE_CAP:
        k += 1
    return float(k)


def _cross10(a, b):
    """(تقاطعٌ صاعد، هابط) لـa فوق/تحت b في آخر 10 شموع."""
    d = (a - b).values
    up = dn = False
    for i in range(max(1, len(d) - 10), len(d)):
        if d[i] != d[i] or d[i - 1] != d[i - 1]:
            continue
        if d[i - 1] <= 0 < d[i]:
            up = True
        if d[i - 1] >= 0 > d[i]:
            dn = True
    return up, dn


def rsi(close, n):
    ch = close.diff()
    up, dn = _wilder(ch.clip(lower=0), n), _wilder((-ch).clip(lower=0), n)
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(h, l, c, n):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return _wilder(tr, n)


def psar(h, l, af0=0.02, af_max=0.2):
    """(صاعد؟، شموعٌ منذ الانقلاب) عند آخر شمعة — Parabolic SAR القياسيّ."""
    H, L = h.values, l.values
    n = len(H)
    if n < 3:
        return None, None
    bull, sar, ep, af, since = True, L[0], H[0], af0, 0
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if bull:
            sar = min(sar, L[i - 1], L[i - 2] if i > 1 else L[i - 1])
            if L[i] < sar:
                bull, sar, ep, af, since = False, ep, L[i], af0, 0
                continue
            if H[i] > ep:
                ep, af = H[i], min(af + af0, af_max)
        else:
            sar = max(sar, H[i - 1], H[i - 2] if i > 1 else H[i - 1])
            if H[i] > sar:
                bull, sar, ep, af, since = True, ep, H[i], af0, 0
                continue
            if L[i] < ep:
                ep, af = L[i], min(af + af0, af_max)
        since += 1
    return bull, float(min(since, SINCE_CAP))


# ══ الشموع (22 نمطًا · تعريفاتٌ كلاسيكيّة على الجسم والذيلين) ════════════════════════════════════════════════════════════════════
def _candle_flags(O, H, L, C):
    n = len(C)
    body, rng = np.abs(C - O), np.maximum(H - L, 1e-12)
    up, lo = H - np.maximum(O, C), np.minimum(O, C) - L
    green, red = C > O, C < O
    avg = pd.Series(body).rolling(10).mean().shift().values
    big = body > np.where(avg == avg, avg, body + 1)
    small = body <= 0.3 * rng
    P = {k: np.zeros(n, bool) for k in CAT.CANDLES}
    P["doji"] = body <= 0.1 * rng
    P["dragonfly"] = P["doji"] & (lo >= 0.6 * rng) & (up <= 0.1 * rng)
    P["gravestone"] = P["doji"] & (up >= 0.6 * rng) & (lo <= 0.1 * rng)
    P["spinning_top"] = small & ~P["doji"] & (up >= 0.25 * rng) & (lo >= 0.25 * rng)
    P["bull_marubozu"] = green & (body >= 0.9 * rng) & big
    ham = (lo >= 2 * body) & (up <= body) & (body > 0)
    inv = (up >= 2 * body) & (lo <= body) & (body > 0)
    dn5 = np.zeros(n, bool)
    up5 = np.zeros(n, bool)
    dn5[5:] = C[4:-1] < C[:-5]                                   # هابطٌ في 5 شموع قبلها
    up5[5:] = C[4:-1] > C[:-5]
    P["hammer"], P["hanging_man"] = ham & dn5, ham & up5
    P["inv_hammer"], P["shooting_star"] = inv & dn5, inv & up5
    for i in range(1, n):
        po, pc, o, c = O[i - 1], C[i - 1], O[i], C[i]
        P["inside_bar"][i] = H[i] <= H[i - 1] and L[i] >= L[i - 1]
        P["outside_bar"][i] = H[i] > H[i - 1] and L[i] < L[i - 1]
        if pc < po and c > o:
            P["bull_engulf"][i] = o <= pc and c >= po
            P["piercing"][i] = o < pc and (po + pc) / 2 < c < po
            P["bull_harami"][i] = o >= pc and c <= po and (c - o) < (po - pc)
        if pc > po and c < o:
            P["bear_engulf"][i] = o >= pc and c <= po
            P["dark_cloud"][i] = o > pc and po < c < (po + pc) / 2
            P["bear_harami"][i] = o <= pc and c >= po and (o - c) < (pc - po)
        P["tweezer_bottom"][i] = pc < po and c > o and abs(L[i] / L[i - 1] - 1) <= 0.002 if L[i - 1] > 0 else False
        if i >= 2:
            o2, c2 = O[i - 2], C[i - 2]
            P["morning_star"][i] = c2 < o2 and small[i - 1] and max(po, pc) < c2 and c > o and c > (o2 + c2) / 2
            P["evening_star"][i] = c2 > o2 and small[i - 1] and min(po, pc) > c2 and c < o and c < (o2 + c2) / 2
            P["three_soldiers"][i] = bool(green[i] and green[i - 1] and green[i - 2] and c > pc > c2 and o > po > o2)
            P["three_crows"][i] = bool(red[i] and red[i - 1] and red[i - 2] and c < pc < c2 and o < po < o2)
    return P


# ══ سماتُ إطارٍ واحد (المتوسّطات · المؤشّرات · البنية · الشموع) ═══════════════════════════════════════════════════════════════════
def tf_features(df, tf):
    """⟵ {اسمُ الفهرس: قيمة} لإطار `tf` من شموعٍ تنتهي عند لحظة القرار (آخرُ `TAIL` شمعة)."""
    d = df.tail(TAIL)
    o, h, l, c, v = (d[k].astype(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    n, f = len(d), {}
    px = _last(c) if n else None
    ok = bool(n >= 2 and px and px > 0)
    # ②-أ المتوسّطات
    for kind, fn in (("sma", _sma), ("ema", _ema)):
        mas = {L_: fn(c, L_) if ok and n >= L_ else None for L_ in CAT.MA_LENS}
        nab, kn = 0, 0
        for L_ in CAT.MA_LENS:
            m = mas[L_]
            mv = _last(m) if m is not None else None
            base = f"{tf}.{kind}{L_}"
            if mv is None or mv <= 0:
                f[base + ".dist"] = f[base + ".slope"] = f[base + ".above"] = f[base + ".since"] = None
                continue
            m5 = _f(m.iloc[-6]) if n >= 6 else None
            f[base + ".dist"] = px / mv - 1.0
            f[base + ".slope"] = (mv / m5 - 1.0) if m5 and m5 > 0 else None
            f[base + ".above"] = bool(px > mv)
            f[base + ".since"] = _since_flip((c > m).values, ~np.isnan(m.values))
            kn += 1
            nab += int(px > mv)
        for a, b in CAT.MA_PAIRS:
            base = f"{tf}.{kind}{a}x{b}"
            ma, mb = mas[a], mas[b]
            va, vb = (_last(ma) if ma is not None else None), (_last(mb) if mb is not None else None)
            if va is None or vb is None or vb <= 0:
                f[base + ".gap"] = f[base + ".xup10"] = f[base + ".xdn10"] = None
                continue
            f[base + ".gap"] = va / vb - 1.0
            f[base + ".xup10"], f[base + ".xdn10"] = _cross10(ma, mb)
        vals = [_last(mas[L_]) if mas[L_] is not None else None for L_ in CAT.MA_LENS]
        prs = [(x, y) for x, y in zip(vals, vals[1:]) if x is not None and y is not None]
        f[f"{tf}.{kind}.stack"] = (sum(1 for x, y in prs if x > y) / len(prs)) if prs else None
        f[f"{tf}.{kind}.nabove"] = float(nab) if kn else None
    # ②-ب المؤشّرات
    r14 = rsi(c, 14) if ok else None
    for k in (7, 14, 21):
        f[f"{tf}.rsi{k}"] = _last(rsi(c, k)) if ok and n > k else None
    bd = sd = None
    if ok and n >= 31 and r14 is not None:
        L10, P20, H10, Q20 = l.iloc[-10:], l.iloc[-30:-10], h.iloc[-10:], h.iloc[-30:-10]
        ra, rb = _f(r14.loc[L10.idxmin()]), _f(r14.loc[P20.idxmin()])
        rc, rd = _f(r14.loc[H10.idxmax()]), _f(r14.loc[Q20.idxmax()])
        bd = bool(L10.min() < P20.min() and ra is not None and rb is not None and ra > rb)
        sd = bool(H10.max() > Q20.max() and rc is not None and rd is not None and rc < rd)
    f[f"{tf}.rsi14.bulldiv"], f[f"{tf}.rsi14.beardiv"] = bd, sd
    if ok and n >= 35:
        line = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig = line.ewm(span=9, adjust=False).mean()
        f[f"{tf}.macd.line_p"], f[f"{tf}.macd.sig_p"] = _last(line) / px, _last(sig) / px
        f[f"{tf}.macd.hist_p"] = (_last(line) - _last(sig)) / px
        f[f"{tf}.macd.hist_pos"] = bool(_last(line) > _last(sig))
        f[f"{tf}.macd.xup10"], f[f"{tf}.macd.xdn10"] = _cross10(line, sig)
    else:
        for m in ("line_p", "sig_p", "hist_p", "hist_pos", "xup10", "xdn10"):
            f[f"{tf}.macd.{m}"] = None
    if ok and n >= 55:
        roc = lambda k: c.pct_change(k) * 100.0                    # noqa: E731
        kst = _sma(roc(10), 10) + 2 * _sma(roc(15), 10) + 3 * _sma(roc(20), 10) + 4 * _sma(roc(30), 15)
        ks = _sma(kst, 9)
        kv, sv = _last(kst), _last(ks)
        f[f"{tf}.kst.val"] = kv
        f[f"{tf}.kst.diff"] = (kv - sv) if kv is not None and sv is not None else None
        f[f"{tf}.kst.xup10"] = _cross10(kst, ks)[0] if sv is not None else None
    else:
        f[f"{tf}.kst.val"] = f[f"{tf}.kst.diff"] = f[f"{tf}.kst.xup10"] = None
    if ok and n >= 14:
        ll9, hh9 = l.rolling(9).min(), h.rolling(9).max()
        rsv = ((c - ll9) / (hh9 - ll9).replace(0, np.nan) * 100).fillna(50.0)
        K = rsv.ewm(alpha=1 / 3, adjust=False).mean()
        Dd = K.ewm(alpha=1 / 3, adjust=False).mean()
        f[f"{tf}.kdj.k"], f[f"{tf}.kdj.d"], f[f"{tf}.kdj.j"] = _last(K), _last(Dd), _last(3 * K - 2 * Dd)
    else:
        f[f"{tf}.kdj.k"] = f[f"{tf}.kdj.d"] = f[f"{tf}.kdj.j"] = None
    if ok and n >= 20:
        ll, hh = l.rolling(14).min(), h.rolling(14).max()
        sk = _sma((c - ll) / (hh - ll).replace(0, np.nan) * 100, 3)
        sdv = _sma(sk, 3)
        f[f"{tf}.stoch.k"], f[f"{tf}.stoch.d"] = _last(sk), _last(sdv)
        f[f"{tf}.stoch.xup10"] = _cross10(sk, sdv)[0]
        tp = (h + l + c) / 3
        ma = _sma(tp, 20)
        md = (tp - ma).abs().rolling(20).mean()
        f[f"{tf}.cci20"] = _last((tp - ma) / (0.015 * md.replace(0, np.nan)))
        f[f"{tf}.willr14"] = _last((hh - c) / (hh - ll).replace(0, np.nan) * -100)
        mf = tp * v
        pos = mf.where(tp > tp.shift(), 0.0).rolling(14).sum()
        neg = mf.where(tp < tp.shift(), 0.0).rolling(14).sum()
        f[f"{tf}.mfi14"] = _last(100 - 100 / (1 + pos / neg.replace(0, np.nan)))
    else:
        for m in ("stoch.k", "stoch.d", "stoch.xup10", "cci20", "willr14", "mfi14"):
            f[f"{tf}.{m}"] = None
    if ok and n >= 60:
        hlc = (h + l + c).values
        H_, L_a, V_ = h.values, l.values, v.values
        trend = np.where(np.diff(hlc, prepend=hlc[0]) > 0, 1.0, -1.0)
        dm = H_ - L_a
        cm = np.zeros(n)
        for i in range(1, n):
            cm[i] = (cm[i - 1] + dm[i]) if trend[i] == trend[i - 1] else (dm[i - 1] + dm[i])
        vf = pd.Series(V_ * np.abs(2 * np.divide(dm, np.where(cm == 0, np.nan, cm)) - 1) * trend * 100, index=c.index).fillna(0.0)
        kvo = vf.ewm(span=34, adjust=False).mean() - vf.ewm(span=55, adjust=False).mean()
        ksig = kvo.ewm(span=13, adjust=False).mean()
        f[f"{tf}.kvo.pos"], f[f"{tf}.kvo.above_sig"] = bool(_last(kvo) > 0), bool(_last(kvo) > _last(ksig))
    else:
        f[f"{tf}.kvo.pos"] = f[f"{tf}.kvo.above_sig"] = None
    if ok and n >= 30:
        upm, dnm = h.diff(), -l.diff()
        pdm = upm.where((upm > dnm) & (upm > 0), 0.0)
        mdm = dnm.where((dnm > upm) & (dnm > 0), 0.0)
        a14 = atr(h, l, c, 14)
        pdi = 100 * _wilder(pdm, 14) / a14.replace(0, np.nan)
        mdi = 100 * _wilder(mdm, 14) / a14.replace(0, np.nan)
        dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
        f[f"{tf}.adx14"], f[f"{tf}.pdi14"], f[f"{tf}.mdi14"] = _last(_wilder(dx, 14)), _last(pdi), _last(mdi)
        f[f"{tf}.di_diff"] = (f[f"{tf}.pdi14"] - f[f"{tf}.mdi14"]) if f[f"{tf}.pdi14"] is not None and f[f"{tf}.mdi14"] is not None else None
        f[f"{tf}.atr14_p"] = (_last(a14) / px) if _last(a14) is not None else None
        mid, sd_ = _sma(c, 20), c.rolling(20).std(ddof=0)
        up_, lo_ = mid + 2 * sd_, mid - 2 * sd_
        width = (up_ - lo_) / mid.replace(0, np.nan)
        wv = _last(width)
        f[f"{tf}.bb.width"] = wv
        f[f"{tf}.bb.pctb"] = _last((c - lo_) / (up_ - lo_).replace(0, np.nan))
        w120 = width.iloc[-120:].dropna()
        f[f"{tf}.bb.squeeze_rank"] = float((w120 < wv).mean()) if wv is not None and len(w120) >= 20 else None
        e20, a10 = c.ewm(span=20, adjust=False).mean(), atr(h, l, c, 10)
        ku, kl = e20 + 2 * a10, e20 - 2 * a10
        f[f"{tf}.kc.pos"] = _last((c - kl) / (ku - kl).replace(0, np.nan))
        f[f"{tf}.kc.squeeze"] = (bool(_last(up_) < _last(ku) and _last(lo_) > _last(kl))
                                 if None not in (_last(up_), _last(ku), _last(lo_), _last(kl)) else None)
        l20, h20 = l.rolling(20).min(), h.rolling(20).max()
        f[f"{tf}.don20.pos"] = _last((c - l20) / (h20 - l20).replace(0, np.nan))
        f[f"{tf}.don20.low_age"] = float(19 - int(np.argmin(l.values[-20:])))
        pb, ps = psar(h, l)
        f[f"{tf}.psar.bull"], f[f"{tf}.psar.since"] = pb, ps
    else:
        for m in ("adx14", "pdi14", "mdi14", "di_diff", "atr14_p", "bb.width", "bb.pctb", "bb.squeeze_rank", "kc.pos", "kc.squeeze",
                  "don20.pos", "don20.low_age", "psar.bull", "psar.since"):
            f[f"{tf}.{m}"] = None
    if ok and n >= 55:
        l55, h55 = l.rolling(55).min(), h.rolling(55).max()
        f[f"{tf}.don55.pos"] = _last((c - l55) / (h55 - l55).replace(0, np.nan))
    else:
        f[f"{tf}.don55.pos"] = None
    if ok and n >= 79:
        ten = (h.rolling(9).max() + l.rolling(9).min()) / 2
        kij = (h.rolling(26).max() + l.rolling(26).min()) / 2
        sa = ((ten + kij) / 2).shift(26)
        sb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
        a_, b_ = _last(sa), _last(sb)
        if a_ is None or b_ is None:
            for m in ("above_cloud", "below_cloud", "tk_bull", "chikou_bull", "thick_p"):
                f[f"{tf}.ichi.{m}"] = None
        else:
            f[f"{tf}.ichi.above_cloud"], f[f"{tf}.ichi.below_cloud"] = bool(px > max(a_, b_)), bool(px < min(a_, b_))
            f[f"{tf}.ichi.tk_bull"] = bool(_last(ten) > _last(kij))
            f[f"{tf}.ichi.chikou_bull"] = bool(px > float(c.iloc[-27]))
            f[f"{tf}.ichi.thick_p"] = abs(a_ - b_) / px
    else:
        for m in ("above_cloud", "below_cloud", "tk_bull", "chikou_bull", "thick_p"):
            f[f"{tf}.ichi.{m}"] = None
    if tf != "W":
        for nm, key in (("vwap_w", lambda ix: (ix.isocalendar().year, ix.isocalendar().week)), ("vwap_m", lambda ix: (ix.year, ix.month))):
            val = None
            if ok:
                kx = [key(ix) for ix in d.index]
                m_ = np.array([k == kx[-1] for k in kx])
                tpv = ((h + l + c) / 3 * v).values[m_].sum()
                vv = v.values[m_].sum()
                val = (px / (tpv / vv) - 1.0) if vv > 0 and tpv > 0 else None
            f[f"{tf}.{nm}.dist"] = val
    # ②-د البنية
    if ok and n >= 21:
        rg = (h - l).values
        f[f"{tf}.st.nr4"], f[f"{tf}.st.nr7"] = bool(rg[-1] <= rg[-4:].min()), bool(rg[-1] <= rg[-7:].min())
        g = (c > o).values
        f[f"{tf}.st.green10"], f[f"{tf}.st.green20"] = float(g[-10:].mean()), float(g[-20:].mean())
        lv, hv, run = l.values, h.values, 0
        while run < n - 1 and lv[-1 - run] > lv[-2 - run]:
            run += 1
        f[f"{tf}.st.hl_run"] = float(run)
        f[f"{tf}.st.inside10"] = float(sum(1 for i in range(n - 10, n) if hv[i] <= hv[i - 1] and lv[i] >= lv[i - 1]))
    else:
        for m in ("nr4", "nr7", "green10", "green20", "hl_run", "inside10"):
            f[f"{tf}.st.{m}"] = None
    # ②-ج الشموع
    if tf != "W":
        if ok and n >= 16:
            P = _candle_flags(o.values, h.values, l.values, c.values)
            for name in CAT.CANDLES:
                w = P[name][-10:]
                hit = np.nonzero(w)[0]
                f[f"{tf}.cdl.{name}.any10"] = bool(len(hit))
                f[f"{tf}.cdl.{name}.ago"] = float(9 - hit[-1]) if len(hit) else None
        else:
            for name in CAT.CANDLES:
                f[f"{tf}.cdl.{name}.any10"] = f[f"{tf}.cdl.{name}.ago"] = None
    return f


# ══ النماذج (تعريفاتُ العقد §③) ═════════════════════════════════════════════════════════════════════════════════════════════════
def _swing_lows(L, k=3):
    return [i for i in range(k, len(L) - k) if L[i] == L[i - k:i + k + 1].min()]


def _slope(y):
    x = np.arange(len(y), dtype=float)
    m = np.mean(y)
    return float(np.polyfit(x, y, 1)[0] / m) if m > 0 and len(y) >= 5 else 0.0


def patterns(H, L, C, V):
    """⟵ {dbl_bottom, w_break, inv_hs, fall_wedge, bull_flag, cup_handle, tri_asc, tri_desc, tri_sym, flat_base15, flat_base25, spring10, lps15}."""
    n = len(C)
    out = {k: None for k in ("dbl_bottom", "w_break", "inv_hs", "fall_wedge", "bull_flag", "cup_handle", "tri_asc", "tri_desc", "tri_sym",
                             "flat_base15", "flat_base25", "spring10", "lps15")}
    if n < 30:
        return out
    lo20 = L[-20:].min()
    w20 = (H[-20:].max() - lo20) / lo20 if lo20 > 0 else None
    out["flat_base15"] = bool(w20 is not None and w20 <= 0.15)
    out["flat_base25"] = bool(w20 is not None and w20 <= 0.25)
    off = max(0, n - 80)
    sw = [off + i for i in _swing_lows(L[off:])]
    db = wb = False
    for bi in range(len(sw)):
        for aj in range(bi):
            i, j = sw[aj], sw[bi]
            if j - i < 5 or j < n - 20 or L[i] <= 0 or L[j] <= 0 or i < n - 60:
                continue
            if abs(L[i] / L[j] - 1) > 0.03:
                continue
            peak = H[i:j + 1].max()
            if peak < 1.10 * max(L[i], L[j]) or L[i:].min() < 0.97 * min(L[i], L[j]):
                continue
            db = True
            wb = wb or bool(C[-1] > peak)
    out["dbl_bottom"], out["w_break"] = db, wb
    ih = False
    for x in range(len(sw)):
        for y in range(x + 1, len(sw)):
            for z in range(y + 1, len(sw)):
                a, b, c = sw[x], sw[y], sw[z]
                if c >= n - 20 and L[b] <= 0.97 * min(L[a], L[c]) and L[c] > 0 and abs(L[a] / L[c] - 1) <= 0.05:
                    ih = True
    out["inv_hs"] = ih
    sh, sl = _slope(H[-30:]), _slope(L[-30:])
    flat = 0.001
    out["tri_asc"] = bool(abs(sh) <= flat and sl > flat)
    out["tri_desc"] = bool(abs(sl) <= flat and sh < -flat)
    out["tri_sym"] = bool(sh < -flat and sl > flat)
    xs = np.arange(30, dtype=float)
    ph, pl = np.polyfit(xs, H[-30:], 1), np.polyfit(xs, L[-30:], 1)
    r0, r1 = (ph[1] - pl[1]), (ph[0] * 29 + ph[1]) - (pl[0] * 29 + pl[1])
    out["fall_wedge"] = bool(sh < 0 and sl < 0 and sh < sl and r0 > 0 and 0 < r1 < 0.7 * r0)
    flag = False
    for e in range(n - 15, n - 2):                               # e = آخرُ شمعة السارية
        for w in range(1, 6):
            s0 = e - w
            if s0 < 0 or C[s0] <= 0:
                continue
            pole = C[e] / C[s0] - 1
            if pole >= 0.30 and 3 <= (n - 1 - e) <= 15:
                rest = C[e + 1:]
                if len(rest) and rest.min() > C[e] - 0.5 * (C[e] - C[s0]) and C[-1] < C[e]:
                    flag = True
    out["bull_flag"] = flag
    cup = False
    if n >= 60:
        seg0 = max(0, n - 150)
        li = seg0 + int(np.argmax(H[seg0:n - 30])) if n - 30 > seg0 else None
        if li is not None:
            bi_ = li + int(np.argmin(L[li:n - 3])) if n - 3 > li else None
            if bi_ is not None and bi_ < n - 4:
                ri = bi_ + int(np.argmax(H[bi_:n - 3]))
                left, bot, right = H[li], L[bi_], H[ri]
                if left > 0 and right > 0 and 30 <= ri - li <= 120 and abs(right / left - 1) <= 0.10:
                    depth = (left - bot) / left
                    after = L[ri + 1:]
                    if 0.20 <= depth <= 0.60 and len(after) >= 3 and (right - after.min()) / right <= 0.15 and C[-1] >= 0.85 * right:
                        cup = True
    out["cup_handle"] = cup
    spring_at = None
    for j in range(max(60, n - 10), n):
        ref = L[j - 60:j].min()
        if ref > 0 and L[j] <= 0.98 * ref and C[j:min(n, j + 4)].max() > ref:
            spring_at = j
    out["spring10"] = spring_at is not None
    lps = False
    for j in range(max(60, n - 15), n - 2):
        ref = L[j - 60:j].min()
        if ref > 0 and L[j] <= 0.98 * ref and C[j:min(n, j + 4)].max() > ref:
            k = j + 1 + int(np.argmin(L[j + 1:]))
            if L[k] > L[j] and k >= 20 and V[k] < V[k - 20:k].mean():
                lps = True
    out["lps15"] = lps
    return out


def prior_explosions(C):
    """[مواضعُ الانفجارات السابقة] بتعريف `T-FPRINT`: إغلاقٌ ضعفُ أدنى إغلاق العشرين قبله · فاصلُ 40 جلسة."""
    out, last = [], -10_000
    for e in range(20, len(C)):
        if e - last < 40:
            continue
        mn = C[e - 20:e].min()
        if mn > 0 and C[e] >= 2 * mn:
            out.append(e)
            last = e
    return out


def daily_extra(full, raw_factor=1.0):
    """⟵ السماتُ اليوميّة غيرُ الإطاريّة (`D.bot.*` · `D.pat.*` · `D.wyck.*` · `D.fib.*` · `D.sr.*` · `D.gap.*` · `px.*` · `vol.*`) من اليوميّ
    الكامل حتى يوم القرار · `raw_factor` يحوّل الإغلاقَ المسوّى إلى خامٍّ يومَها (حاصلُ نِسب التقسيمات المنفّذة بعده)."""
    f = {}
    n = len(full)
    o, h, l, c, v = (full[k].astype(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    O, H, L, C, V = o.values, h.values, l.values, c.values, v.values
    ok = n >= 61 and C[-1] > 0
    px = C[-1] if n else None
    # دوالُّ البوت المحميّة كما هي
    bot_names = ("rsi14", "macd_hist_p", "kst_diff", "mfi", "willr", "atr_p", "bb_pctb", "stochrsi_k", "fsto_k", "cci14", "adx", "ema30_dist",
                 "ema50_dist", "klinger_bull")
    for m in bot_names:
        f[f"D.bot.{m}"] = None
    if ok:
        try:
            import Super_stock as S
            t = full.tail(TAIL)
            tc, th, tl, tv = t["Close"], t["High"], t["Low"], t["Volume"]
            f["D.bot.rsi14"] = _last(S.rsi(tc))
            ln, sg = S.macd(tc)
            f["D.bot.macd_hist_p"] = (_last(ln) - _last(sg)) / px if _last(ln) is not None and _last(sg) is not None else None
            k1, k2 = S.kst(tc)
            f["D.bot.kst_diff"] = (_last(k1) - _last(k2)) if _last(k1) is not None and _last(k2) is not None else None
            f["D.bot.mfi"] = _last(S.mfi(th, tl, tc, tv))
            f["D.bot.willr"] = _last(S.williams_r(th, tl, tc))
            a_ = _last(S.atr(th, tl, tc))
            f["D.bot.atr_p"] = a_ / px if a_ is not None else None
            f["D.bot.bb_pctb"] = _last(S.bollinger(tc)[3])
            f["D.bot.stochrsi_k"] = _last(S.stoch_rsi(tc)[0])
            f["D.bot.fsto_k"] = _last(S.full_stoch(th, tl, tc)[0])
            f["D.bot.cci14"] = _last(S.cci(th, tl, tc))
            f["D.bot.adx"] = _last(S.dmi_adx(th, tl, tc)[2])
            e30, e50 = S.ema(tc, 30), S.ema(tc, 50)
            f["D.bot.ema30_dist"] = px / e30 - 1.0 if e30 else None
            f["D.bot.ema50_dist"] = px / e50 - 1.0 if e50 else None
            ks = S.klinger_state(th, tl, tc, tv)
            f["D.bot.klinger_bull"] = bool(ks["kvo"] > ks["signal"]) if isinstance(ks, dict) and "kvo" in ks and "signal" in ks else None
        except Exception:                                        # noqa: BLE001 — دالّةٌ تعذّرت ⟵ سماتُها مجهولة
            pass
    pat = patterns(H[-TAIL:], L[-TAIL:], C[-TAIL:], V[-TAIL:]) if ok else {}
    for k in ("dbl_bottom", "w_break", "inv_hs", "fall_wedge", "bull_flag", "cup_handle", "tri_asc", "tri_desc", "tri_sym", "flat_base15",
              "flat_base25"):
        f[f"D.pat.{k}"] = pat.get(k)
    f["D.wyck.spring10"], f["D.wyck.lps15"] = pat.get("spring10"), pat.get("lps15")
    # فيبوناتشي والدعوم والمقاومات والفجوات
    f["D.fib.retr"] = f["D.fib.near_level"] = None
    for m in ("sup_tested", "sup_touches", "sup_dist", "res_tested", "res_touches", "res_dist"):
        f[f"D.sr.{m}"] = None
    for m in ("above_n", "above_dist", "below_n", "below_dist"):
        f[f"D.gap.{m}"] = None
    if ok:
        li = n - 60 + int(np.argmin(L[-60:]))
        hi_seg = H[max(0, li - 250):li]
        if len(hi_seg) and hi_seg.max() > L[li]:
            retr = (px - L[li]) / (hi_seg.max() - L[li])
            f["D.fib.retr"] = float(retr)
            f["D.fib.near_level"] = bool(any(abs(retr - x) <= 0.03 for x in FIBS))
        lows30, highs30 = L[-30:], H[-30:]
        base = lows30.min()
        hits = np.abs(lows30 / base - 1.0) <= 0.015 if base > 0 else np.zeros(30, bool)
        cl = int(sum(1 for k, x in enumerate(hits) if x and not (k and hits[k - 1])))
        f["D.sr.sup_tested"], f["D.sr.sup_touches"] = bool(cl >= 2), float(cl)
        f["D.sr.sup_dist"] = px / base - 1.0 if base > 0 else None
        top = highs30.max()
        hits = np.abs(highs30 / top - 1.0) <= 0.015
        cl = int(sum(1 for k, x in enumerate(hits) if x and not (k and hits[k - 1])))
        f["D.sr.res_tested"], f["D.sr.res_touches"] = bool(cl >= 2), float(cl)
        f["D.sr.res_dist"] = top / px - 1.0
        s0 = max(1, n - 250)
        above, below = [], []
        run_max = np.maximum.accumulate(H[::-1])[::-1]            # أعلى High من k إلى النهاية
        run_min = np.minimum.accumulate(L[::-1])[::-1]
        for k in range(s0, n):
            if H[k] < L[k - 1] and run_max[k] < L[k - 1] and H[k] >= px * 0 and L[k - 1] > px:      # فجوةٌ هابطة لم تُغطَّ كاملةً وحافّتُها فوق السعر
                bot_edge = max(run_max[k], px)
                if bot_edge <= 2 * px:
                    above.append(bot_edge / px - 1.0)
            if L[k] > H[k - 1] and run_min[k] > H[k - 1] and H[k - 1] < px:                         # فجوةٌ صاعدة لم تُغطَّ وحافّتُها تحت السعر
                below.append(px / min(run_min[k], px) - 1.0 if min(run_min[k], px) > 0 else 0.0)
        f["D.gap.above_n"], f["D.gap.below_n"] = float(len(above)), float(len(below))
        f["D.gap.above_dist"] = float(min(above)) if above else None
        f["D.gap.below_dist"] = float(min(below)) if below else None
    # السعر
    for m in ("close", "drop252", "atl_dist", "base20_w", "base40_w", "base60_w", "round_dist", "ret1", "ret5", "ret10", "ret20", "ret60",
              "range_d", "uwick5", "lwick10", "atl_age", "low60_age", "base_len", "below1_30", "expl_n", "expl_age", "sweep10", "sweep_reclaim",
              "near1", "expl_due"):
        f[f"px.{m}"] = None
    for m in ("usd_med20", "usd_d", "dry5_20", "spike_d", "updown20", "obv_slope10", "obv_slope20", "adl_slope10", "adl_slope20", "cmf20",
              "spike10"):
        f[f"vol.{m}"] = None
    if ok:
        raw = px * float(raw_factor or 1.0)
        f["px.close"] = raw
        hi252 = H[-252:].max()
        f["px.drop252"] = 1.0 - px / hi252 if hi252 > 0 else None
        ai = int(np.argmin(L))
        f["px.atl_dist"] = px / L[ai] - 1.0 if L[ai] > 0 else None
        f["px.atl_age"] = float(n - 1 - ai)
        f["px.low60_age"] = float(59 - int(np.argmin(L[-60:])))
        for w in (20, 40, 60):
            lo = L[-w:].min()
            f[f"px.base{w}_w"] = (H[-w:].max() - lo) / lo if lo > 0 else None
        k = 0
        while k < min(n - 1, SINCE_CAP) and 0.8 * px <= C[-1 - k - 1] <= 1.25 * px:
            k += 1
        f["px.base_len"] = float(k)
        sw = rec = False
        for j in range(n - 10, n):
            ref = L[j - 20:j].min()
            if ref > 0 and L[j] <= 0.98 * ref and C[j] > ref:
                sw = True
                rec = rec or bool(px > ref)
        f["px.sweep10"], f["px.sweep_reclaim"] = sw, bool(sw and rec)
        f["px.round_dist"] = float(min(abs(raw / r - 1.0) for r in ROUNDS))
        f["px.near1"] = bool(abs(raw - 1.0) <= 0.10)
        f["px.below1_30"] = float((C[-30:] * float(raw_factor or 1.0) < 1.0).sum())
        ex = prior_explosions(C)
        f["px.expl_n"] = float(len(ex))
        f["px.expl_age"] = float(n - 1 - ex[-1]) if ex else None
        if len(ex) >= 2:
            gaps_ = np.diff(ex)
            m_ = float(gaps_.mean())
            f["px.expl_due"] = bool(abs((n - 1 - ex[-1]) - m_) <= 0.25 * m_)
        else:
            f["px.expl_due"] = False
        for kk in (1, 5, 10, 20, 60):
            f[f"px.ret{kk}"] = (px / C[-1 - kk] - 1.0) if C[-1 - kk] > 0 else None
        f["px.range_d"] = (H[-1] - L[-1]) / px
        f["px.uwick5"] = float((H[-5:] / C[-5:] - 1.0).max())
        f["px.lwick10"] = float(((np.minimum(O[-10:], C[-10:]) - L[-10:]) / C[-10:]).max())
        usd = C * V
        f["vol.usd_med20"], f["vol.usd_d"] = float(np.median(usd[-20:])), float(usd[-1])
        m20 = V[-25:-5].mean()
        f["vol.dry5_20"] = float(V[-5:].mean() / m20) if m20 > 0 else None
        med = np.median(V[-21:-1])
        f["vol.spike_d"] = float(V[-1] / med) if med > 0 else None
        sp = False
        for j in range(n - 10, n):
            mj = np.median(V[j - 20:j])
            sp = sp or bool(mj > 0 and V[j] >= 3 * mj)
        f["vol.spike10"] = sp
        chg = np.diff(C[-21:])
        upv, dnv = V[-20:][chg > 0].sum(), V[-20:][chg < 0].sum()
        f["vol.updown20"] = float(upv / dnv) if dnv > 0 else None
        sign = np.sign(np.diff(C, prepend=C[0]))
        rng = np.where(H - L > 0, H - L, np.nan)
        mfm = np.nan_to_num(((C - L) - (H - C)) / rng)
        for w in (10, 20):
            tot = V[-w:].sum()
            f[f"vol.obv_slope{w}"] = float((sign[-w:] * V[-w:]).sum() / tot) if tot > 0 else None
            f[f"vol.adl_slope{w}"] = float((mfm[-w:] * V[-w:]).sum() / tot) if tot > 0 else None
        f["vol.cmf20"] = f["vol.adl_slope20"]
    return f


def weekly(full):
    """اليوميُّ حتى يوم القرار ⟵ أسبوعيٌّ (الأسبوعُ الجاري جزئيًّا)."""
    if not len(full):
        return full
    return full.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])


def candle_features(dfD, dfH4, raw_factor=1.0):
    """⟵ كلُّ سمات الشموع (`AB` عدا `sh.*`) من يوميٍّ و4 ساعات **مقصوصَين عند لحظة القرار**."""
    f = {}
    f.update(tf_features(dfD, "D"))
    h4 = dfH4 if dfH4 is not None else dfD.iloc[0:0]
    f.update(tf_features(h4, "H4"))
    f.update(tf_features(weekly(dfD), "W"))
    f.update(daily_extra(dfD, raw_factor))
    ph = patterns(h4["High"].values.astype(float)[-TAIL:], h4["Low"].values.astype(float)[-TAIL:], h4["Close"].values.astype(float)[-TAIL:],
                  h4["Volume"].values.astype(float)[-TAIL:]) if len(h4) >= 61 else {}
    f["H4.pat.dbl_bottom"], f["H4.pat.flat_base15"], f["H4.wyck.spring10"] = ph.get("dbl_bottom"), ph.get("flat_base15"), ph.get("spring10")
    return {k: (None if v is None else (bool(v) if isinstance(v, (bool, np.bool_)) else _f(v))) for k, v in f.items()}


def cut(dfD, dfH4, day):
    """قصُّ الإطارين عند نهاية `day` (يومُ نيويورك «YYYY-MM-DD»): اليوميُّ حتى شمعته · و4 ساعات حتى نهاية أفتره."""
    d_ = dfD[dfD.index.strftime("%Y-%m-%d") <= day]
    h_ = dfH4[dfH4.index.strftime("%Y-%m-%d") <= day] if dfH4 is not None and len(dfH4) else None
    return d_, h_


def features_asof(dfD, dfH4, day, raw_factor=1.0):
    d_, h_ = cut(dfD, dfH4, day)
    return candle_features(d_, h_, raw_factor)


def with_deltas(dfD, dfH4, day, raw_factor=1.0):
    """⟵ سماتُ يوم القرار + `.d5`/`.d10` (ناقص قيمتها قبل 5 و10 جلساتٍ يوميّة محسوبةً كما كانت يومَها) لكلّ رقميٍّ ذي دلتا في الفهرس."""
    d_, _h = cut(dfD, dfH4, day)
    days = d_.index.strftime("%Y-%m-%d")
    f0 = features_asof(dfD, dfH4, day, raw_factor)
    prev = {}
    for k in (5, 10):
        prev[k] = features_asof(dfD, dfH4, days[-1 - k], raw_factor) if len(days) > k else {}
    out = dict(f0)
    for name, kind, arm, delta in CAT.catalog():
        if not delta or arm != "AB" or name.startswith("sh."):
            continue
        for k in (5, 10):
            a, b = f0.get(name), prev[k].get(name)
            out[f"{name}.d{k}"] = (a - b) if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) else None
    return out


def expected_names():
    """أسماءُ `candle_features` المتوقَّعة من الفهرس (الأساسيّةُ `AB` عدا `sh.*`)."""
    return [n for n, _k, a, _d in CAT.catalog() if a == "AB" and not n.startswith("sh.")]
