# -*- coding: utf-8 -*-
"""🔎📺 بصمةُ الشموع على TradingView — «أيُّ سهمٍ هذا الشارت؟» (أمرُ المالك 2026-10-07: «FAISAL CHART → TICKER
IDENTIFICATION · DO NOT GUESS — IDENTIFY THE EXACT STOCK» · «استخدم … بيانات الشارت التاريخية … تاريخ الأسعار»).

**قراءةٌ فقط:** بطاقةُ الاختبار الأعمى (شموعٌ مقروءةٌ بالبكسل · `chart_cards/blind/…` · بلا رمز) ⟵ أسهمُ NASDAQ/NYSE/AMEX من ماسح
TradingView ⟵ شموعُ كلِّ رمز (يوميّة · أسبوعيّة · 4 ساعات ممتدّة) ⟵ **كلُّ نافذةٍ بطول الشموع المقروءة تُقارَن بمعامل مقياسٍ حرّ**
(تقسيمٌ بعد لقطة الشارت يضرب الأسعارَ المسوّاة بثابتٍ واحد) ⟵ أفضلُ النوافذ مطبوعةً بشموعها مقابل البطاقة.

- المقياس: لوغاريتمُ O/H/L/C · `k` = متوسّطُ الفرق (مربّعاتٌ صغرى) · `rms` = جذرُ متوسّط مربّعات البواقي · `mx` = أكبرُ باقٍ.
- **لا حكمَ آليّ:** الأداةُ ترتّب وتطبع · والحكمُ (مطابقةُ التسلسل والتاريخ والتقسيم) يُكتب بيدٍ تذكر حدودَه.
- حدودٌ معلنة: كونُ اليوم وحدَه (المشطوبُ والمُعاد تسميتُه غائبان) · وشموعُ TradingView مسوّاةٌ بالتقسيم (`adjustment=splits`).

🔒 لا تلغرام · لا كتابةَ حالة · لا أسرار — جالبُ بياناتٍ وطابعٌ فقط.
"""
import datetime as dt
import json
import math
import os
import sys

import numpy as np

import tv_data as TV

FIELDS = ("o", "h", "l", "c")
TYPES = ("stock", "dr")              # أسهمٌ وإيصالاتُ إيداع — بلا صناديق ولا سندات
CHUNK = 400                          # رموزٌ لكلّ دفعة جلب (الذاكرةُ لا تحمل الكونَ كلَّه بشموعه)
TF_SPEC = {"1D": ("1D", False), "1W": ("1W", False), "240e": ("240", True)}


def log(m: str = "") -> None:
    print(m, flush=True)


def _num(x):
    """رقمُ البطاقة (نصٌّ أو {"v": …}) ⟵ float · وتعذّرُه ⟵ None."""
    if isinstance(x, dict):
        x = x.get("v")
    try:
        v = float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def card_ohlc(card: dict) -> np.ndarray:
    """شموعُ البطاقة ⟵ مصفوفةٌ (m×4) بالترتيب o,h,l,c — وأيُّ حقلٍ لا يُقرأ ⟵ ValueError (لا يُخمَّن)."""
    rows = []
    for i, b in enumerate(card.get("bars") or []):
        r = [_num((b or {}).get(f)) for f in FIELDS]
        if any(v is None for v in r):
            raise ValueError(f"الشمعة {i + 1} ناقصة")
        rows.append(r)
    if len(rows) < 5:
        raise ValueError("أقلُّ من خمس شموع")
    return np.array(rows, dtype=float)


def window_fit(ohlc: np.ndarray, ref: np.ndarray):
    """كلُّ نافذةٍ بطول `ref` في `ohlc` (n×4) ⟵ (rms, logk, mx) لكلّ بداية — `k` = سعرُ المصدر ÷ سعرُ البطاقة."""
    m = len(ref)
    if len(ohlc) < m:
        return None
    lw = np.log(np.clip(ohlc, 1e-9, None))
    win = np.lib.stride_tricks.sliding_window_view(lw, (m, 4))[:, 0]          # (T, m, 4)
    d = win - np.log(ref)[None, :, :]
    logk = d.mean(axis=(1, 2))
    res = d - logk[:, None, None]
    rms = np.sqrt((res ** 2).mean(axis=(1, 2)))
    mx = np.abs(res).max(axis=(1, 2))
    return rms, logk, mx


def best_windows(bars: list, ref: np.ndarray, keep: int = 3, gap: int = 5) -> list:
    """أفضلُ `keep` نوافذ متباعدة (لا تتداخل بداياتُها بأقلّ من `gap`) ⟵ [{i, rms, k, mx}]."""
    good = [b for b in (bars or []) if all(isinstance(x, (int, float)) and x > 0 for x in b[1:5])]
    if len(good) < len(ref):
        return []
    ohlc = np.array([[b[1], b[2], b[3], b[4]] for b in good], dtype=float)
    fit = window_fit(ohlc, ref)
    if fit is None:
        return []
    rms, logk, mx = fit
    out = []
    for i in np.argsort(rms):
        i = int(i)
        if any(abs(i - o["i"]) < gap for o in out):
            continue
        out.append({"i": i, "rms": float(rms[i]), "k": float(math.exp(logk[i])), "mx": float(mx[i]), "bars": good})
        if len(out) >= keep:
            break
    return out


def context(w: dict, m: int, after: int = 26) -> dict:
    """ما بعد النافذة بمقياس البطاقة: هل قمّتُها الأولى أعلى المدى الظاهر · وأعلى/أدنى ما بعدها · وآخرُ إغلاقٍ معروف."""
    bars, i, k = w["bars"], w["i"], w["k"]
    seg = bars[i:i + m + after]
    nxt = bars[i + m:i + m + after]
    first_h = bars[i][2]
    return {"start": TV.ny_day(bars[i][0]), "end": TV.ny_day(bars[i + m - 1][0]),
            "peak_is_max": all(b[2] <= first_h * 1.0005 for b in seg),
            "after_hi": round(max((b[2] for b in nxt), default=float("nan")) / k, 3) if nxt else None,
            "after_lo": round(min((b[3] for b in nxt), default=float("nan")) / k, 3) if nxt else None,
            "after_n": len(nxt),
            "last_close": round(bars[-1][4] / k, 3), "last_day": TV.ny_day(bars[-1][0]),
            "bars_after_window": len(bars) - (i + m)}


def print_pair(w: dict, ref: np.ndarray, sym: str, tf: str) -> None:
    """شموعُ النافذة (بمقياس البطاقة) مقابل البطاقة — شمعةً شمعة."""
    m, k, bars = len(ref), w["k"], w["bars"]
    log(f"   ↳ {sym} {tf} · k={k:.4f} · rms={w['rms']:.4f} · أكبرُ باقٍ={w['mx']:.4f}")
    for j in range(m):
        b = bars[w["i"] + j]
        mine = " ".join(f"{x / k:7.3f}" for x in b[1:5])
        card = " ".join(f"{x:7.3f}" for x in ref[j])
        log(f"     {j + 1:>2} {TV.ny_day(b[0])}  المصدر/k o h l c = {mine}   البطاقة = {card}")
    tail = bars[w["i"] + m:w["i"] + m + 30]
    if tail:
        log("     بعد النافذة (بمقياس البطاقة): " + " · ".join(
            f"{TV.ny_day(b[0])[5:]} {b[2] / k:.2f}/{b[3] / k:.2f}/{b[4] / k:.2f}" for b in tail))


def universe():
    """الكون ⟵ {«EXCH:SYM»: حقول} — الأسهمُ والإيصالاتُ وحدَها · وإن رفض الماسحُ عمودَي النوع والوصف ⟵ الكونُ كلُّه
    بعمودين (يُعلَن) · وتعذّرُه كلِّه ⟵ None."""
    snap = TV.scan(["name", "close", "type", "description"])
    if snap is not None:
        return {s: d for s, d in snap.items() if str((d or {}).get("type") or "").lower() in TYPES}
    log("⚠️ الماسحُ رفض عمودَي النوع والوصف ⟵ الكونُ كلُّه بلا تصفية نوع")
    return TV.scan(["name", "close"])


def search(card: dict, tfs, n_by_tf: dict, top: int, workers: int, symbols=None) -> int:
    ref = card_ohlc(card)
    m = len(ref)
    log(f"🔎 البطاقة {card.get('id')} · {m} شمعة · أعلاها {ref[:, 1].max():.3f} · أدناها {ref[:, 2].min():.3f}")
    uni = universe()
    if uni is None:
        log("⛔ الماسح تعذّر — لا كون ⟵ لا بحث (فاشلٌ-آمن · لا «لا يوجد»)")
        return 3
    tmap = TV.ticker_map(uni)
    syms = sorted({(x if ":" in x else tmap.get(x.upper(), "NASDAQ:" + x.upper())) for x in symbols}) if symbols \
        else sorted(uni)
    log(f"🌐 الكون: {len(syms)} رمزًا (NASDAQ/NYSE/AMEX · {'/'.join(TYPES)})")
    rc = 0
    for tf in tfs:
        interval, ext = TF_SPEC[tf]
        n = int(n_by_tf.get(tf) or 1500)
        found, fetched, failed, empty, short = [], 0, 0, 0, 0
        for c0 in range(0, len(syms), CHUNK):
            chunk = syms[c0:c0 + CHUNK]
            got = TV.fetch_many(chunk, interval=interval, n=n, extended=ext, workers=workers, retry_pass=True)
            for s in chunk:
                bars = got.get(s)
                if bars is None:
                    failed += 1
                    continue
                if not bars:
                    empty += 1
                    continue
                fetched += 1
                ws = best_windows(bars, ref)
                if not ws:
                    short += 1
                for w in ws:
                    w["sym"] = s
                    found.append(w)
            found.sort(key=lambda w: w["rms"])
            del found[max(200, top):]
            log(f"   … {tf}: {min(c0 + CHUNK, len(syms))}/{len(syms)} · جُلب {fetched} · تعذّر {failed} · "
                f"فارغ {empty} · أقصرُ من النافذة {short} · أفضلُ rms حتى الآن "
                f"{found[0]['rms']:.4f} ({found[0]['sym']})" if found else f"   … {tf}: لا نافذة بعد")
        cov = fetched / max(1, len(syms))
        log(f"\n══ {tf} · التغطية {fetched}/{len(syms)} = {cov:.1%} · تعذّر {failed} · فارغ {empty} ══")
        if cov < 0.80:
            log("⚠️ التغطيةُ دون 80% — «لا تطابق» هنا لا يُقرأ نفيًا")
            rc = max(rc, 4)
        log(f"{'#':>3} {'الرمز':<16} {'rms':>7} {'أكبر':>7} {'k':>9}  البداية ⟵ النهاية  "
            "القمّةُ أعلى المدى · بعدها أعلى/أدنى (بمقياس البطاقة) · آخرُ إغلاق")
        for r, w in enumerate(found[:top], 1):
            cx = context(w, m)
            d = uni.get(w["sym"], {})
            log(f"{r:>3} {w['sym']:<16} {w['rms']:7.4f} {w['mx']:7.4f} {w['k']:9.4f}  {cx['start']} ⟵ {cx['end']}  "
                f"{'✓' if cx['peak_is_max'] else '✗'} · {cx['after_hi']}/{cx['after_lo']} ({cx['after_n']}) · "
                f"{cx['last_close']} يوم {cx['last_day']} · {str(d.get('description') or '')[:40]}")
        for w in found[:5]:
            print_pair(w, ref, w["sym"], tf)
        log("JSON " + json.dumps({"tf": tf, "coverage": round(cov, 4), "top": [
            {"sym": w["sym"], "rms": round(w["rms"], 5), "mx": round(w["mx"], 5), "k": round(w["k"], 5),
             **context(w, m)} for w in found[:top]]}, ensure_ascii=False))
    log(f"\n📊 نداءاتُ TradingView: {TV.CALLS}")
    return rc


def main() -> int:
    path = (os.environ.get("CHART_ID_CARD") or "").strip()
    if not path:
        log("⛔ بلا بطاقة (CHART_ID_CARD)")
        return 2
    try:
        card = json.load(open(path, encoding="utf-8"))
        card_ohlc(card)
    except (OSError, ValueError) as e:
        log(f"⛔ البطاقة: {type(e).__name__}: {e}")
        return 2
    tfs = [t.strip() for t in (os.environ.get("CHART_ID_TF") or "1D").split(",") if t.strip()]
    bad = [t for t in tfs if t not in TF_SPEC]
    if bad:
        log(f"⛔ فريمٌ مجهول {bad} — المتاح {sorted(TF_SPEC)}")
        return 2
    n_by_tf = {"1D": int(os.environ.get("CHART_ID_N1D") or 1500), "1W": int(os.environ.get("CHART_ID_N1W") or 520),
               "240e": int(os.environ.get("CHART_ID_N4H") or 3000)}
    syms = [s.strip() for s in (os.environ.get("CHART_ID_SYMS") or "").split(",") if s.strip()]
    log(f"🕒 {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC · الفريمات {tfs} · الشموع {n_by_tf}")
    return search(card, tfs, n_by_tf, int(os.environ.get("CHART_ID_TOP") or 40),
               int(os.environ.get("CHART_ID_WORKERS") or 10), symbols=syms or None)


if __name__ == "__main__":
    sys.exit(main())
