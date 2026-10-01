# -*- coding: utf-8 -*-
"""🔬📱 app_parity_probe — مِجَسٌّ مؤقّت (**يُحذف قبل الدمج**): هل تُعاد أرقامُ تطبيق «مراقب استراتيجية فيصل» من الشموع؟

المعيارُ والتنبّؤاتُ مكتوبةٌ قبل أيّ رقم في `faisal_batches/2026-10-01/APP_PARITY_PREREG.md` (§③):
  «مطابق» = الفرقُ لا يتجاوز نصفَ آخر خانةٍ معروضة · «مؤكَّد» = تعريفٌ يطابق كلَّ لقطةٍ يظهر فيها الحقل بمصدرٍ واحد ·
  وإلّا «غيرُ معروف» · و«قريب» (≤1%) وصفٌ لا يُحتسب · والمصدران (TradingView · ياهو) يُحكمان منفصلَين.
قراءةٌ فقط · بلا تلغرام · بلا كتابة حالة · بلا git.
"""
import datetime as dt
import math
import sys

import numpy as np
import pandas as pd

import tv_data as TV

try:
    import yfinance as yf
except Exception:                                                  # noqa: BLE001
    yf = None

D = dt.date.fromisoformat

# ── ① اللقطات (منقولةٌ من الصور بحرفها) ─────────────────────────────────────────────────────────────────────────
#   القيمةُ (value, decimals) ⟵ التسامح = نصفُ آخر خانة · والنسبُ بالنقاط المئويّة.
SNAPS = [
    dict(tag="NTCL-25", sym="NTCL", asof="2026-09-25", img="IMAGE-01..08",
         price=(2.12, 2), bottom=(1.735, 3), bottom_date="2026-09-03", hi_reb=(2.20, 2),
         reb=(26.8, 1), pull=(-3.6, 1), dist=(22.2, 1),
         split_date="2026-07-06", split_open=(4.26, 2), first4h=(6.00, 2),
         ema20=(2.1771, 4), ema30=(2.6988, 4), ema50=(4.8596, 4), rsi14=(41.31, 2), macd_pos=True,
         gap=(26.3, 1), rise20=(26.8, 1), rsi4h=(52.72, 2), macd4h_pos=True,
         float_=(1.96e6, -4), shares=(2.12e6, -4)),
    dict(tag="NTCL-15", sym="NTCL", asof="2026-09-15", img="IMAGE-10..12",
         price=(2.04, 2), bottom=(1.735, 3), bottom_date="2026-09-03", hi_reb=(2.20, 2),
         reb=(26.8, 1), dist=(17.6, 1), split_date="2026-07-06", split_open=(4.26, 2), first4h=(6.00, 2)),
    dict(tag="ELPW-05", sym="ELPW", asof="2026-09-04", img="IMAGE-13,18",
         price=(3.085, 3), bottom=(3.01, 2), bottom_date="2026-09-04", hi_reb=(3.27, 2),
         reb=(8.6, 1), pull=(-5.7, 1), dist=(2.5, 1), split_date="2026-08-10",
         split_open=(4.63, 2), first4h=(4.9793, 4), rsi14=(32.16, 2), macd_pos=True,
         gap=(58.3, 1), rise20=(54.4, 1)),
    dict(tag="ZNB-04", sym="ZNB", asof="2026-09-04", img="IMAGE-14",
         price=(1.60, 2), bottom=(1.55, 2), reb=(12.9, 1), dist=(3.2, 1),
         split_date="2026-07-27", split_open=(2.17, 2), first4h_cut=2.85),
    dict(tag="MSGY-x", sym="MSGY", asof=None, before="2026-09-22", img="IMAGE-09 (=TG_50592)",
         price=(2.08, 2), bottom=(1.73, 2), reb=(30.6, 1), dist=(20.2, 1)),
    dict(tag="GCTK-25", sym="GCTK", asof="2026-09-25", img="IMAGE-03",
         price=(1.82, 2), bottom=(1.77, 2), dist=(2.8, 1)),
    dict(tag="OMH-x", sym="OMH", asof=None, before="2026-09-27", img="TG_57876 (09-30)",
         price=(2.35, 2), bottom=(2.05, 2), reb=(27.8, 1), dist=(14.6, 1),
         split_date="2026-08-31", split_open=(3.53, 2)),
    dict(tag="CIIT-x", sym="CIIT", asof=None, before="2026-09-27", img="TG_57880/82 (09-30)",
         price=(2.75, 2), bottom=(2.26, 2), reb=(32.3, 1), dist=(21.7, 1)),
]


def tol(dec):
    return 0.5 * 10 ** (-dec) if dec >= 0 else 0.5 * 10 ** (-dec)


def match(v, target):
    if v is None or target is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    val, dec = target
    if abs(v - val) <= tol(dec) + 1e-12:
        return "✓"
    if val and abs(v / val - 1) <= 0.01:
        return "≈"
    return "✗"


# ── ② الشموع ───────────────────────────────────────────────────────────────────────────────────────────────────
def tv_frame(rows):
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
    df["t"] = [TV.ny_time(x) for x in df["ts"]]
    return df


def daily_tv(rows):
    df = tv_frame(rows)
    if df is None:
        return None
    df.index = pd.to_datetime([TV.ny_day(x) for x in df["ts"]])
    return df[["Open", "High", "Low", "Close", "Volume"]]


def yahoo_daily(sym):
    if yf is None:
        return None
    try:
        h = yf.Ticker(sym).history(period="2y", auto_adjust=False, actions=False)
        if h is None or h.empty:
            return None
        h.index = pd.to_datetime([x.date() for x in h.index])
        return h[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:                                         # noqa: BLE001
        print(f"   ⚠️ ياهو {sym}: {type(e).__name__}")
        return None


def yahoo_splits(sym):
    if yf is None:
        return []
    try:
        s = yf.Ticker(sym).splits
        return [(x.date().isoformat(), float(r)) for x, r in s.items()]
    except Exception:                                              # noqa: BLE001
        return []


def agg4h(frame, key):
    """شموعُ ساعةٍ ⟵ 4 ساعات بمفتاح تجميع (key(t) ⟵ معرّفُ الحاوية)."""
    if frame is None or frame.empty:
        return None
    g = frame.assign(k=[key(t) for t in frame["t"]]).groupby("k", sort=True)
    out = pd.DataFrame({"t": g["t"].first(), "Open": g["Open"].first(), "High": g["High"].max(),
                        "Low": g["Low"].min(), "Close": g["Close"].last()})
    return out.sort_values("t").reset_index(drop=True)


def key_et04(t):          # 04-08 · 08-12 · 12-16 · 16-20 نيويورك
    return (t.date().isoformat(), (t.hour - 4) // 4 if t.hour >= 4 else -1)


def key_utc(t):           # 00/04/08/12/16/20 UTC
    u = t.astimezone(dt.timezone.utc)
    return (u.date().isoformat(), u.hour // 4)


def key_reg0930(t):       # 09:30-13:30 · 13:30-16:00 (ساعاتُ TradingView النظاميّة تبدأ 09:30)
    m = t.hour * 60 + t.minute
    return (t.date().isoformat(), 0 if m < 13 * 60 + 30 else 1)


# ── ③ المؤشّرات ─────────────────────────────────────────────────────────────────────────────────────────────────
def rsi_wilder(c, n=14):
    import Super_stock as S
    return float(S.rsi(c, n).iloc[-1])


def rsi_cutler(c, n=14):
    d = c.diff()
    g, lo = d.clip(lower=0).rolling(n).mean(), (-d).clip(lower=0).rolling(n).mean()
    rs = g / lo.replace(0, np.nan)
    return float((100 - 100 / (1 + rs)).iloc[-1])


def rsi_ema(c, n=14):
    d = c.diff()
    g = d.clip(lower=0).ewm(span=n, adjust=False).mean()
    lo = (-d).clip(lower=0).ewm(span=n, adjust=False).mean()
    return float((100 - 100 / (1 + g / lo.replace(0, np.nan))).iloc[-1])


def ema_variants(c, n, split_from=None):
    out = {}
    out["full_adjFalse"] = float(c.ewm(span=n, adjust=False).mean().iloc[-1])
    out["full_adjTrue"] = float(c.ewm(span=n, adjust=True).mean().iloc[-1])
    if len(c) > n:
        seed = c.iloc[:n].mean()
        a, e = 2 / (n + 1), seed
        for x in c.iloc[n:]:
            e = a * x + (1 - a) * e
        out["full_smaSeed"] = float(e)
    for k in (100, 250):
        if len(c) >= k:
            out[f"last{k}"] = float(c.iloc[-k:].ewm(span=n, adjust=False).mean().iloc[-1])
    if split_from is not None:
        s = c[c.index >= pd.Timestamp(split_from)]
        if len(s):
            out["fromSplit"] = float(s.ewm(span=n, adjust=False).mean().iloc[-1])
            out["fromSplit_sma"] = float(s.iloc[-n:].mean()) if len(s) >= n else float("nan")
    return out


def macd_flags(c):
    f, s = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
    line = f - s
    sig = line.ewm(span=9, adjust=False).mean()
    h = line - sig
    return {"line>sig": bool(line.iloc[-1] > sig.iloc[-1]), "line>0": bool(line.iloc[-1] > 0),
            "hist_up": bool(h.iloc[-1] > h.iloc[-2]), "vals": (round(float(line.iloc[-1]), 4),
                                                         round(float(sig.iloc[-1]), 4))}


def rise20_variants(d):
    t = d.iloc[-20:]
    out = {"maxH/minL": (t["High"].max() / t["Low"].min() - 1) * 100,
           "C/C-20": (d["Close"].iloc[-1] / d["Close"].iloc[-21] - 1) * 100 if len(d) > 21 else float("nan"),
           "C/C-19": (d["Close"].iloc[-1] / d["Close"].iloc[-20] - 1) * 100 if len(d) > 20 else float("nan"),
           "maxC/minC": (t["Close"].max() / t["Close"].min() - 1) * 100}
    i = int(np.argmin(t["Low"].to_numpy()))
    out["maxH_after_minL"] = (t["High"].iloc[i:].max() / t["Low"].iloc[i] - 1) * 100
    return out


def gap_variants(d, split_from=None):
    out = {}
    o, h, lo, c = d["Open"], d["High"], d["Low"], d["Close"]
    fam = {"openUp": (o / c.shift(1) - 1) * 100, "trueUp": (lo / h.shift(1) - 1) * 100,
           "openAbs": (o / c.shift(1) - 1).abs() * 100, "trueDown": (lo.shift(1) / h - 1) * 100,
           "range": (h / lo - 1) * 100, "chg": (c / c.shift(1) - 1) * 100}
    wins = {"20": 20, "30": 30, "60": 60, "250": 250}
    for fn, ser in fam.items():
        for wn, w in wins.items():
            out[f"{fn}_{wn}"] = float(ser.iloc[-w:].max())
        if split_from is not None:
            s = ser[ser.index >= pd.Timestamp(split_from)]
            if len(s):
                out[f"{fn}_split"] = float(s.max())
    return out


def bottom_variants(d, split_from=None):
    out = {}
    for w in (20, 30, 40, 60):
        t = d.iloc[-w:]
        out[f"minL{w}"] = (float(t["Low"].min()), t["Low"].idxmin().date().isoformat())
        out[f"minC{w}"] = (float(t["Close"].min()), t["Close"].idxmin().date().isoformat())
    if split_from is not None:
        t = d[d.index >= pd.Timestamp(split_from)]
        if len(t):
            out["minL_split"] = (float(t["Low"].min()), t["Low"].idxmin().date().isoformat())
            out["minC_split"] = (float(t["Close"].min()), t["Close"].idxmin().date().isoformat())
    return out


def bot_view(d, s, sp):
    """قراءةُ البوت نفسِه على الشموع نفسِها (وصفٌ لا حكم): دورةُ الارتكاز · افتتاحُ يوم الحدث · قمّةُ ما بعد التقسيم ·
    متوسّطاتُ ما بعد التقسيم."""
    try:
        import Super_stock as S
        pc = S.pivot_cycle_state(d)
        print(f"   [bot] 🪜 {S.pivot_cycle_line(pc) or '—'}")
        if s.get("split_date"):
            spser = pd.Series({pd.Timestamp(a): r for a, r in sp}) if sp else pd.Series(dtype=float)
            print(f"   [bot] افتتاحُ يوم الحدث={S._event_day_open(d['Open'], D(s['split_date']))} · "
                  f"قمّةُ ما بعد التقسيم={S._post_split_high(d['High'], spser, d.index[-1])} · "
                  f"قيمةُ شمعة التقسيم={S._split_day_value(d['Close'], spser, d.index[-1])}")
            print(f"   [bot] {S.split_ma_lines(d, s['split_date']) or '— (متوسّطاتُ التقسيم)'}")
    except Exception as e:                                         # noqa: BLE001
        print(f"   [bot] تعذّر: {type(e).__name__}: {e}")


# ── ④ التشغيل ──────────────────────────────────────────────────────────────────────────────────────────────────
VERDICT = {}          # حقل ⟵ مصدر ⟵ مرشَّح ⟵ [✓/✗ لكلّ لقطة]


def note(field, src, cand, mark):
    VERDICT.setdefault(field, {}).setdefault(src, {}).setdefault(cand, []).append(mark)


def judge_line(field, src, cand_vals, target):
    for cand, v in cand_vals.items():
        note(field, src, cand, match(v, target))


def run():
    tmap = {}
    snap = TV.scan(["name", "close", "float_shares_outstanding"])
    if snap:
        tmap = TV.ticker_map(snap)
    snap2 = TV.scan(["name", "total_shares_outstanding"]) or {}       # حقلٌ إضافيّ — تعذّرُه لا يُسقط الأوّل
    print(f"🔎 الماسح: {len(snap or {})} صفًّا · الحقلُ الإضافيّ {len(snap2)}")
    syms = sorted({s["sym"] for s in SNAPS})
    ch = TV.Chart(timeout=25)
    data = {}
    for sym in syms:
        full = tmap.get(sym, f"NASDAQ:{sym}")
        d1 = ch.bars(full, "1D", n=700)
        h4r = ch.bars(full, "240", n=1500)
        h4x = ch.bars(full, "240", n=1500, extended=True)
        h1x = ch.bars(full, "60", n=5000, extended=True)
        h1r = ch.bars(full, "60", n=3000)
        sc = dict((snap or {}).get(full) or {})
        sc.update((snap2 or {}).get(full) or {})
        data[sym] = dict(full=full, d=daily_tv(d1), y=yahoo_daily(sym), sp=yahoo_splits(sym),
                         h4r=tv_frame(h4r), h4x=tv_frame(h4x), h1x=tv_frame(h1x), h1r=tv_frame(h1r), sc=sc)
        print(f"📥 {full}: يوميّ {len(d1 or [])} · 240ن {len(h4r or [])} · 240م {len(h4x or [])} · 60م {len(h1x or [])}"
              f" · 60ن {len(h1r or [])} · ياهو {0 if data[sym]['y'] is None else len(data[sym]['y'])} · تقسيمات ياهو "
              f"{[x for x in data[sym]['sp'] if x[0] >= '2026-01-01']} · ماسح فلوت {sc.get('float_shares_outstanding')}"
              f" قائمة {sc.get('total_shares_outstanding')}")
    ch.close()

    for s in SNAPS:
        sym = s["sym"]
        dd = data[sym]
        print(f"\n━━━━━━━━ {s['tag']} ({s['img']}) ━━━━━━━━")
        for src in ("tv", "yahoo"):
            d = dd["d"] if src == "tv" else dd["y"]
            if d is None or d.empty:
                print(f"   [{src}] لا شموع")
                continue
            asof = s.get("asof")
            if asof is None:              # ابحث عن الجلسة: إغلاقٌ يطابق السعر قبل الحدّ
                cand = d[(d.index <= pd.Timestamp(s["before"]))]
                cand = cand[(cand["Close"] - s["price"][0]).abs() <= tol(s["price"][1]) + 1e-9]
                if cand.empty:
                    print(f"   [{src}] لا جلسةَ إغلاقُها {s['price'][0]} قبل {s['before']} ⇒ تُتخطّى")
                    continue
                asof = cand.index[-1].date().isoformat()
                print(f"   [{src}] الجلسةُ المُستنتَجة بالإغلاق: {asof} (من {len(cand)} مرشَّحة: "
                      f"{[x.date().isoformat() for x in cand.index[-4:]]})")
            for shift_name, shift in (("D", 0), ("D-1", 1)):
                dd_ = d[d.index <= pd.Timestamp(asof)]
                if shift:
                    dd_ = dd_.iloc[:-1]
                if len(dd_) < 30:
                    continue
                tag = f"{src}/{shift_name}"
                last = dd_.index[-1].date().isoformat()
                c = dd_["Close"]
                note("price", tag, "close", match(float(c.iloc[-1]), s["price"]))
                bv = bottom_variants(dd_, s.get("split_date"))
                if "bottom" in s:
                    for k, (v, dte) in bv.items():
                        m = match(v, s["bottom"])
                        if m == "✓" and s.get("bottom_date") and dte != s["bottom_date"]:
                            m = "✓قيمة✗تاريخ"
                        note("bottom", tag, k, m)
                # أعلى ارتداد/ارتداد: من قاعِ أدنى Low في 60 (P1) شاملًا يومه
                bval, bdate = bv["minL60"]
                after = dd_[dd_.index >= pd.Timestamp(bdate)]
                after_x = dd_[dd_.index > pd.Timestamp(bdate)]
                hi_in = float(after["High"].max())
                hi_ex = float(after_x["High"].max()) if len(after_x) else float("nan")
                if "hi_reb" in s:
                    judge_line("hi_reb", tag, {"incl": hi_in, "excl": hi_ex}, s["hi_reb"])
                if "reb" in s:
                    judge_line("reb", tag, {"incl": (hi_in / bval - 1) * 100,
                                            "excl": (hi_ex / bval - 1) * 100 if math.isfinite(hi_ex) else None},
                               s["reb"])
                if "dist" in s:
                    note("dist", tag, "close/minL60", match((float(c.iloc[-1]) / bval - 1) * 100, s["dist"]))
                    note("dist", tag, "appPrice/appBottom",
                         match((s["price"][0] / s["bottom"][0] - 1) * 100, s["dist"]))
                if "pull" in s:
                    note("pull", tag, "appPrice/appHi", match((s["price"][0] / s["hi_reb"][0] - 1) * 100, s["pull"]))
                for n in (20, 30, 50):
                    k = f"ema{n}"
                    if k in s:
                        ev = ema_variants(c, n, s.get("split_date"))
                        judge_line(k, tag, ev, s[k])
                        print(f"   [{tag}] EMA{n}: " + " · ".join(f"{a}={b:.4f}" for a, b in ev.items()
                                                                if math.isfinite(b)) + f" (التطبيق {s[k][0]})")
                if "rsi14" in s:
                    rv = {"wilder": rsi_wilder(c), "cutler": rsi_cutler(c), "ema": rsi_ema(c),
                          "wilder_last250": rsi_wilder(c.iloc[-250:]) if len(c) >= 250 else float("nan")}
                    judge_line("rsi14", tag, rv, s["rsi14"])
                    print(f"   [{tag}] RSI14: " + " · ".join(f"{a}={b:.2f}" for a, b in rv.items()
                                                           if math.isfinite(b)) + f" (التطبيق {s['rsi14'][0]})")
                if s.get("macd_pos"):
                    mf = macd_flags(c)
                    for k in ("line>sig", "line>0", "hist_up"):
                        note("macd_pos", tag, k, "✓" if mf[k] else "✗")
                    print(f"   [{tag}] MACD (خطّ، إشارة)={mf['vals']} · line>sig={mf['line>sig']} · "
                          f"line>0={mf['line>0']} · hist_up={mf['hist_up']}")
                if "rise20" in s:
                    rv = rise20_variants(dd_)
                    judge_line("rise20", tag, rv, s["rise20"])
                    print(f"   [{tag}] صعود20: " + " · ".join(f"{a}={b:.1f}" for a, b in rv.items()
                                                            if math.isfinite(b)) + f" (التطبيق {s['rise20'][0]})")
                if "gap" in s:
                    gv = gap_variants(dd_, s.get("split_date"))
                    judge_line("gap", tag, gv, s["gap"])
                    hits = [a for a, b in gv.items() if match(b, s["gap"]) == "✓"]
                    print(f"   [{tag}] أكبر فجوة: مطابق {hits or '—'} · (openUp_60={gv.get('openUp_60', float('nan')):.1f}"
                          f" · trueUp_60={gv.get('trueUp_60', float('nan')):.1f} · range_60="
                          f"{gv.get('range_60', float('nan')):.1f} · chg_60={gv.get('chg_60', float('nan')):.1f})"
                          f" (التطبيق {s['gap'][0]})")
                if s.get("split_date") and "split_open" in s:
                    sd = d[d.index >= pd.Timestamp(s["split_date"])]
                    if len(sd):
                        note("split_open", src, "firstDailyOpen", match(float(sd["Open"].iloc[0]), s["split_open"]))
                if tag == "tv/D":
                    bot_view(dd_, s, dd["sp"])
                print(f"   [{tag}] آخر شمعة {last} · إغلاق {float(c.iloc[-1]):.4f} · قاع60 {bval:.4f} ({bdate}) · "
                      f"أعلى بعده {hi_in:.4f} · قيعان: " + " · ".join(f"{k}={v:.4f}@{t}" for k, (v, t) in bv.items()))
        # ── أعلى أوّل 4 ساعات · RSI/MACD 4H (TradingView وحدَه) ──
        if s.get("split_date"):
            sdt = D(s["split_date"])
            fr = {}
            for nm, f in (("240reg", dd["h4r"]), ("240ext", dd["h4x"])):
                if f is not None:
                    x = f[[t.date() == sdt for t in f["t"]]]
                    if len(x):
                        fr[nm] = float(x["High"].iloc[0])
            for nm, key, base in (("60x_et04", key_et04, dd["h1x"]), ("60x_utc", key_utc, dd["h1x"]),
                                  ("60r_0930", key_reg0930, dd["h1r"])):
                a = agg4h(base, key)
                if a is not None:
                    x = a[[t.date() == sdt for t in a["t"]]]
                    if len(x):
                        fr[nm] = float(x["High"].iloc[0])
            if dd["h1r"] is not None:
                x = dd["h1r"][[t.date() == sdt for t in dd["h1r"]["t"]]]
                if len(x):
                    fr["60r_first4"] = float(x["High"].iloc[:4].max())
                    fr["day_high_reg"] = float(x["High"].max())
            if dd["d"] is not None:
                x = dd["d"][dd["d"].index == pd.Timestamp(sdt)]
                if len(x):
                    fr["daily_high"] = float(x["High"].iloc[0])
            if "first4h" in s:
                judge_line("first4h", "tv", fr, s["first4h"])
            print(f"   [tv] أعلى أوّل 4 ساعات يوم {sdt}: " + " · ".join(f"{a}={b:.4f}" for a, b in fr.items())
                  + f" (التطبيق {s.get('first4h', (s.get('first4h_cut'), 0))[0]})")
        if "rsi4h" in s:
            ad = D(s["asof"])
            for nm, f in (("240reg", dd["h4r"]), ("240ext", dd["h4x"]),
                          ("60x_et04", agg4h(dd["h1x"], key_et04)), ("60x_utc", agg4h(dd["h1x"], key_utc)),
                          ("60r_0930", agg4h(dd["h1r"], key_reg0930))):
                if f is None or f.empty:
                    continue
                for cut_nm, cut in (("toD", ad), ("toD-1", ad - dt.timedelta(days=1))):
                    x = f[[t.date() <= cut for t in f["t"]]]
                    if len(x) < 40:
                        continue
                    cc = pd.Series(x["Close"].to_numpy())
                    r = rsi_wilder(cc)
                    note("rsi4h", "tv", f"{nm}/{cut_nm}", match(r, s["rsi4h"]))
                    mf = macd_flags(cc)
                    note("macd4h_pos", "tv", f"{nm}/{cut_nm}/line>sig", "✓" if mf["line>sig"] else "✗")
                    print(f"   [tv] RSI4H {nm}/{cut_nm}={r:.2f} · MACD4H {mf['vals']} (التطبيق {s['rsi4h'][0]})")
        if "float_" in s:
            sc = dd["sc"]
            for k, fld in (("float_", "float_shares_outstanding"), ("shares", "total_shares_outstanding")):
                v = sc.get(fld)
                print(f"   [tv-scan اليوم] {fld}={v} (التطبيق {s[k][0]:.0f} يوم 09-25)")

    # ── ⑤ الحكم — آخرُ الأسطر ──
    print("\n════════ JUDGE (مؤكَّد = يطابق كلَّ لقطةٍ يظهر فيها الحقل بمصدرٍ واحد) ════════")
    for field, bysrc in VERDICT.items():
        conf = []
        for src, cands in bysrc.items():
            for cand, marks in cands.items():
                if marks and all(m == "✓" for m in marks):
                    conf.append(f"{src}:{cand}({len(marks)})")
        near = []
        for src, cands in bysrc.items():
            for cand, marks in cands.items():
                if marks and all(m in ("✓", "≈") for m in marks) and not all(m == "✓" for m in marks):
                    near.append(f"{src}:{cand}")
        print(f"• {field}: " + (("✅ مؤكَّد ⟵ " + " · ".join(conf)) if conf else "❔ غيرُ معروف")
              + (f" ‖ قريب: {' · '.join(near[:6])}" if near else ""))
    return 0


if __name__ == "__main__":
    sys.exit(run())
