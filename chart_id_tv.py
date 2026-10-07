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
TF_SPEC = {"1D": ("1D", False), "1W": ("1W", False), "240e": ("240", True), "a30": ("30", True)}
# «a30» = شموعُ 30 دقيقة ممتدّة تُجمَّع في شموعٍ أكبر بحدودٍ يوميّة (توقيتُ نيويورك) — لأن تطبيقاتٍ تقسم فريمَ الساعات
#    عند 09:30 لا عند 04/08/12/16 كما TradingView ⟵ الحدودُ فرضيّةٌ تُختبَر بالأرقام لا تُفترَض. «-HH:MM» آخرَ المجموعة = نهايتُها.
DEFAULT_ANCHORS = ("04:00,08:00,12:00,16:00;04:00,05:30,09:30,13:30,17:30;05:30,09:30,13:30,17:30;"
                   "04:00,09:30,13:30,16:00;09:30,13:30,-16:00")


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


def parse_anchors(spec: str) -> list:
    """«04:00,05:30,09:30;09:30,13:30,-16:00» ⟵ [(البدايات بالدقائق، النهاية)] — والنهايةُ الافتراضيّة 20:00 · وما لا يُقرأ ⟵ ValueError."""
    out = []
    for grp in [g.strip() for g in (spec or "").split(";") if g.strip()]:
        starts, end = [], 20 * 60
        for t in [x.strip() for x in grp.split(",") if x.strip()]:
            neg = t.startswith("-")
            hh, mm = t.lstrip("-").split(":")
            m = int(hh) * 60 + int(mm)
            if not (0 <= m <= 24 * 60):
                raise ValueError(f"وقتٌ خارج اليوم {t}")
            if neg:
                end = m
            else:
                starts.append(m)
        starts = sorted(set(starts))
        if not starts or starts[-1] >= end:
            raise ValueError(f"مجموعةُ حدودٍ فارغة أو بعد نهايتها {grp!r}")
        out.append((starts, end))
    return out


def aggregate(bars: list, starts: list, end: int) -> list:
    """شموعٌ صغيرة (ts بدايتُها) ⟵ شموعٌ أكبر بحدودٍ يوميّة بتوقيت نيويورك: الشمعةُ في المقطع الذي تبدأ فيه (آخرُ حدٍّ لا يتجاوزها) ·
    وما قبل أوّل حدٍّ أو من النهاية فصاعدًا يُسقَط · الافتتاحُ أوّلُها والإغلاقُ آخرُها والأعلى/الأدنى أقصاهما · وتوقيتُ الناتج بدايةُ مقطعه."""
    out, key = [], None
    for b in bars or []:
        t = TV.ny_time(b[0])
        m = t.hour * 60 + t.minute
        if m < starts[0] or m >= end:
            continue
        k = max(i for i, a in enumerate(starts) if a <= m)
        kk = (t.date(), k)
        if kk != key:
            seg0 = dt.datetime(t.year, t.month, t.day, starts[k] // 60, starts[k] % 60, tzinfo=TV.NY)
            out.append([int(seg0.timestamp()), b[1], b[2], b[3], b[4], b[5] if len(b) > 5 else 0.0])
            key = kk
        else:
            r = out[-1]
            r[2], r[3], r[4] = max(r[2], b[2]), min(r[3], b[3]), b[4]
            r[5] = (r[5] or 0.0) + (b[5] if len(b) > 5 and b[5] else 0.0)
    return out


def _stamp(ts: int, intraday: bool) -> str:
    return TV.ny_time(ts).strftime("%m-%d %H:%M") if intraday else TV.ny_day(ts)


def print_pair(w: dict, ref: np.ndarray, sym: str, tf: str) -> None:
    """شموعُ النافذة (بمقياس البطاقة) مقابل البطاقة — شمعةً شمعة."""
    m, k, bars = len(ref), w["k"], w["bars"]
    log(f"   ↳ {sym} {tf} · k={k:.4f} · rms={w['rms']:.4f} · أكبرُ باقٍ={w['mx']:.4f}")
    intra = not tf.startswith(("1D", "1W"))
    for j in range(m):
        b = bars[w["i"] + j]
        mine = " ".join(f"{x / k:7.3f}" for x in b[1:5])
        card = " ".join(f"{x:7.3f}" for x in ref[j])
        log(f"     {j + 1:>2} {_stamp(b[0], intra)}  المصدر/k o h l c = {mine}   البطاقة = {card}")
    tail = bars[w["i"] + m:w["i"] + m + 40]
    if tail:
        log("     بعد النافذة (بمقياس البطاقة · أعلى/أدنى/إغلاق): " + " · ".join(
            f"{_stamp(b[0], intra)} {b[2] / k:.3f}/{b[3] / k:.3f}/{b[4] / k:.3f}" for b in tail))


def universe():
    """الكون ⟵ {«EXCH:SYM»: حقول} — الأسهمُ والإيصالاتُ وحدَها · وإن رفض الماسحُ عمودَي النوع والوصف ⟵ الكونُ كلُّه
    بعمودين (يُعلَن) · وتعذّرُه كلِّه ⟵ None."""
    snap = TV.scan(["name", "close", "type", "description"])
    if snap is not None:
        return {s: d for s, d in snap.items() if str((d or {}).get("type") or "").lower() in TYPES}
    log("⚠️ الماسحُ رفض عمودَي النوع والوصف ⟵ الكونُ كلُّه بلا تصفية نوع")
    return TV.scan(["name", "close"])


def _variants(tf: str, anchors: list) -> list:
    """فريمٌ ⟵ [(وسم، تحويلُ الشموع)] — العاديُّ كما هو · و«a30» مجموعةٌ لكلّ حدودٍ يوميّة."""
    if tf != "a30":
        return [(tf, lambda b: b)]
    out = []
    for starts, end in anchors:
        lab = "a30[" + ",".join(f"{a // 60:02d}:{a % 60:02d}" for a in starts) + f"-{end // 60:02d}:{end % 60:02d}]"
        out.append((lab, (lambda st, en: (lambda b: aggregate(b, st, en)))(starts, end)))
    return out


def search(card: dict, tfs, n_by_tf: dict, top: int, workers: int, symbols=None, anchors=None) -> int:
    ref = card_ohlc(card)
    m = len(ref)
    anchors = anchors or parse_anchors(DEFAULT_ANCHORS)
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
        vars_ = _variants(tf, anchors)
        found = {lab: [] for lab, _ in vars_}
        fetched, failed, empty, short = 0, 0, 0, 0
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
                for lab, fn in vars_:
                    ws = best_windows(fn(bars), ref)
                    if not ws:
                        short += 1
                    for w in ws:
                        w["sym"] = s
                        found[lab].append(w)
            for lab in found:
                found[lab].sort(key=lambda w: w["rms"])
                del found[lab][max(200, top):]
            best = min((f[0] for f in found.values() if f), key=lambda w: w["rms"], default=None)
            log(f"   … {tf}: {min(c0 + CHUNK, len(syms))}/{len(syms)} · جُلب {fetched} · تعذّر {failed} · فارغ {empty} · "
                + (f"أفضلُ rms حتى الآن {best['rms']:.4f} ({best['sym']})" if best else "لا نافذة بعد"))
        cov = fetched / max(1, len(syms))
        log(f"\n══ {tf} · التغطية {fetched}/{len(syms)} = {cov:.1%} · تعذّر {failed} · فارغ {empty} · أقصرُ من النافذة {short} ══")
        if cov < 0.80:
            log("⚠️ التغطيةُ دون 80% — «لا تطابق» هنا لا يُقرأ نفيًا")
            rc = max(rc, 4)
        intra = tf not in ("1D", "1W")
        for lab, _ in vars_:
            rows = found[lab]
            log(f"\n── {lab} · أفضلُ {min(top, len(rows))} ──")
            log(f"{'#':>3} {'الرمز':<16} {'rms':>7} {'أكبر':>7} {'k':>9}  البداية ⟵ النهاية  "
                "القمّةُ أعلى المدى · بعدها أعلى/أدنى (بمقياس البطاقة) · آخرُ إغلاق")
            for r, w in enumerate(rows[:top], 1):
                cx = context(w, m)
                d = uni.get(w["sym"], {})
                st = _stamp(w["bars"][w["i"]][0], intra)
                en = _stamp(w["bars"][w["i"] + m - 1][0], intra)
                log(f"{r:>3} {w['sym']:<16} {w['rms']:7.4f} {w['mx']:7.4f} {w['k']:9.4f}  {st} ⟵ {en}  "
                    f"{'✓' if cx['peak_is_max'] else '✗'} · {cx['after_hi']}/{cx['after_lo']} ({cx['after_n']}) · "
                    f"{cx['last_close']} يوم {cx['last_day']} · {str(d.get('description') or '')[:40]}")
            for w in rows[:3]:
                print_pair(w, ref, w["sym"], lab)
            log("JSON " + json.dumps({"tf": lab, "coverage": round(cov, 4), "top": [
                {"sym": w["sym"], "rms": round(w["rms"], 5), "mx": round(w["mx"], 5), "k": round(w["k"], 5),
                 "start": _stamp(w["bars"][w["i"]][0], intra), **context(w, m)} for w in rows[:top]]},
                ensure_ascii=False))
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
               "240e": int(os.environ.get("CHART_ID_N4H") or 3000), "a30": int(os.environ.get("CHART_ID_N30") or 1400)}
    try:
        anchors = parse_anchors(os.environ.get("CHART_ID_ANCHORS") or DEFAULT_ANCHORS)
    except ValueError as e:
        log(f"⛔ الحدود: {e}")
        return 2
    syms = [s.strip() for s in (os.environ.get("CHART_ID_SYMS") or "").split(",") if s.strip()]
    log(f"🕒 {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC · الفريمات {tfs} · الشموع {n_by_tf}")
    return search(card, tfs, n_by_tf, int(os.environ.get("CHART_ID_TOP") or 40),
                  int(os.environ.get("CHART_ID_WORKERS") or 10), symbols=syms or None, anchors=anchors)


if __name__ == "__main__":
    sys.exit(main())
