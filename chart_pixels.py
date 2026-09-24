# -*- coding: utf-8 -*-
"""🖼️ **قراءةُ البكسل** — احتياطُ مُعرِّف الشارت (`chart_finder_prereg.md §①-ب`).

تُستعمل **فقط لما لا يغطّيه النصّ** المقروء من الصورة: سلسلةُ الشموع (O/H/L/C بالبكسل ثم
بالسعر بعد معايرة المحور) ⟵ ترتيبُ المرشّحين بالشكل، أو أعلى/أدنى الشاشة حين لا تسميةَ لهما.

**دوالُّ نقيّة** (مصفوفةٌ داخلة ⟵ أرقامٌ خارجة) — لا شبكة ولا حالة:
  `candle_masks`   بكسلاتُ الشموع الصاعدة/الهابطة بالتدرّج اللونيّ، **بعد حذف الخطوط الأفقية
                   المرسومة** (خطوطُ فيصل الطويلة: أيُّ جريانٍ أفقيّ أطولُ من `LINE_MIN_FRAC` من العرض).
  `find_candles`   الأعمدةُ الملوّنة المتجاورة ⟵ شمعة: الذيلُ = أعلى/أدنى بكسل، والجسمُ = الصفوفُ
                   التي يغطّيها أغلبُ عرض الشمعة.
  `calibrate`      أزواجُ (بكسل، سعر) من تسميات المحور ⟵ دالّةُ تحويل (خطّيّ أو لوغاريتميّ بالمطابقة).
  `candles_to_ohlc` الشموعُ بالبكسل ⟵ O/H/L/C بالسعر مرتَّبةً يسارًا لليمين.
  `axis_label_rows` صفوفُ النصّ في شريط المحور ⟵ مراكزُها الرأسيّة (تُقرن بقيمٍ يقرؤها Claude).
  `overlay`        صورةُ تحقّقٍ: مستطيلاتُ الشموع المستخرجة فوق الأصل.
⚠️ **حدودٌ مُعلنة:** شموعٌ أضيقُ من بكسلين لا تُفصل · ألوانٌ غيرُ الأخضر/الأحمر تحتاج `hues` صريحة ·
والخطُّ/المساحة (لا شموع) ⟵ `find_candles` تُرجع `[]` فتُعلَن «لا شموع» ولا يُخمَّن.
"""
from __future__ import annotations

import math

import numpy as np

UP_HUES = ((70.0, 190.0),)                  # أخضرُ/فيروزيٌّ (تريدنج فيو #26a69a ≈ 174°)
DOWN_HUES = ((330.0, 360.0), (0.0, 22.0))   # أحمر (تريدنج فيو #ef5350 ≈ 1°)
SAT_MIN, VAL_MIN = 0.30, 0.30
LINE_MIN_FRAC = 0.22                        # جريانٌ أفقيٌّ أطولُ من 22% من العرض = خطٌّ مرسوم لا شمعة
BODY_COVER = 0.6                            # الجسمُ: صفٌّ يغطّيه 60% من عرض الشمعة فأكثر
MIN_CANDLE_PX = 1


def load_rgb(path_or_img) -> np.ndarray:
    """صورةٌ ⟵ مصفوفةُ `(ارتفاع، عرض، 3)` بالبايت."""
    from PIL import Image                                           # noqa: PLC0415
    img = path_or_img if hasattr(path_or_img, "convert") else Image.open(path_or_img)
    return np.asarray(img.convert("RGB"), dtype=np.uint8)


def rgb_to_hsv(rgb: np.ndarray):
    """‏(التدرّج بالدرجات 0-360، التشبّع 0-1، القيمة 0-1) لكلّ بكسل — متّجهيًّا."""
    a = rgb.astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=-1), a.min(axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-12
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = (60.0 * ((g[rm] - b[rm]) / d[rm])) % 360.0
    h[gm] = 60.0 * ((b[gm] - r[gm]) / d[gm]) + 120.0
    h[bm] = 60.0 * ((r[bm] - g[bm]) / d[bm]) + 240.0
    s = np.where(mx > 1e-12, d / np.where(mx > 1e-12, mx, 1.0), 0.0)
    return h, s, mx


def _in_ranges(h: np.ndarray, ranges) -> np.ndarray:
    m = np.zeros(h.shape, dtype=bool)
    for lo, hi in ranges:
        m |= (h >= lo) & (h <= hi)
    return m


def remove_long_runs(mask: np.ndarray, min_len: int) -> np.ndarray:
    """يحذف كلَّ جريانٍ أفقيٍّ متّصل أطولَ من `min_len` (خطٌّ مرسوم) — ويُبقي ما دونه."""
    out = mask.copy()
    H, W = mask.shape
    for y in range(H):
        row = mask[y]
        if not row.any():
            continue
        x = 0
        while x < W:
            if not row[x]:
                x += 1
                continue
            x2 = x
            while x2 < W and row[x2]:
                x2 += 1
            if x2 - x >= min_len:
                out[y, x:x2] = False
            x = x2
    return out


def candle_masks(rgb: np.ndarray, box=None, up_hues=UP_HUES, down_hues=DOWN_HUES):
    """بكسلاتُ الشموع داخل `box=(x0, y0, x1, y1)` ⟵ `(صاعد، هابط)` بعد حذف الخطوط الطويلة."""
    x0, y0, x1, y1 = box or (0, 0, rgb.shape[1], rgb.shape[0])
    h, s, v = rgb_to_hsv(rgb[y0:y1, x0:x1])
    col = (s >= SAT_MIN) & (v >= VAL_MIN)
    up = col & _in_ranges(h, up_hues)
    dn = col & _in_ranges(h, down_hues)
    min_len = max(8, int(LINE_MIN_FRAC * (x1 - x0)))
    return remove_long_runs(up, min_len), remove_long_runs(dn, min_len)


def find_candles(up: np.ndarray, dn: np.ndarray, x_off: int = 0, y_off: int = 0) -> list:
    """الأعمدةُ الملوّنة المتجاورة ⟵ شموعٌ `{x0,x1,top,bottom,body_top,body_bottom,up}`
    بإحداثيّات الصورة الأصل — مرتَّبةً يسارًا لليمين."""
    out = []
    for mask, is_up in ((up, True), (dn, False)):
        cols = mask.any(axis=0)
        W = mask.shape[1]
        x = 0
        while x < W:
            if not cols[x]:
                x += 1
                continue
            x2 = x
            while x2 < W and cols[x2]:
                x2 += 1
            seg = mask[:, x:x2]
            ys = np.where(seg.any(axis=1))[0]
            if ys.size:
                cover = seg.sum(axis=1) / float(x2 - x)
                body = np.where(cover >= BODY_COVER)[0] if (x2 - x) >= 3 else ys
                if body.size == 0:
                    body = ys
                out.append({"x0": x + x_off, "x1": x2 - 1 + x_off,
                            "top": int(ys.min()) + y_off, "bottom": int(ys.max()) + y_off,
                            "body_top": int(body.min()) + y_off,
                            "body_bottom": int(body.max()) + y_off, "up": is_up})
            x = x2
    out = [c for c in out if c["x1"] - c["x0"] + 1 >= MIN_CANDLE_PX]
    out.sort(key=lambda c: (c["x0"] + c["x1"]) / 2.0)
    return out


def calibrate(pairs, log_scale=None):
    """أزواجُ `(y، سعر)` (اثنان فأكثر) ⟵ `(دالّة y⟵سعر، هل لوغاريتميّ، أقصى خطأٍ نسبيّ للمطابقة)`.
    `log_scale=None` ⟵ يُختار الأصغرُ خطأً حين تكفي ثلاثةُ أزواج، وإلّا الخطّيّ."""
    pts = [(float(y), float(p)) for y, p in pairs if p is not None]
    if len(pts) < 2:
        return None, None, math.inf
    ys = np.array([p[0] for p in pts])
    ps = np.array([p[1] for p in pts])

    def fit(use_log):
        tgt = np.log(ps) if use_log else ps
        A = np.vstack([ys, np.ones_like(ys)]).T
        k, b = np.linalg.lstsq(A, tgt, rcond=None)[0]
        pred = k * ys + b
        pred_p = np.exp(pred) if use_log else pred
        span = float(ps.max() - ps.min()) or max(float(np.abs(ps).max()), 1e-9)
        err = float(np.max(np.abs(pred_p - ps)) / span)       # خطأُ المطابقة نسبةً لمدى المحور
        f = (lambda y, k=k, b=b: float(np.exp(k * y + b))) if use_log else \
            (lambda y, k=k, b=b: float(k * y + b))
        return f, err

    if log_scale is True or (log_scale is None and len(pts) >= 3 and (ps > 0).all()):
        f_log, e_log = fit(True)
        if log_scale is True:
            return f_log, True, e_log
        f_lin, e_lin = fit(False)
        return (f_log, True, e_log) if e_log < e_lin else (f_lin, False, e_lin)
    f_lin, e_lin = fit(False)
    return f_lin, False, e_lin


def candles_to_ohlc(candles: list, f) -> list:
    """شموعٌ بالبكسل ⟵ `[{o,h,l,c,up}]` بالسعر (y الأعلى = سعرٌ أعلى على الشاشة)."""
    out = []
    for c in candles:
        hi, lo = f(c["top"]), f(c["bottom"])
        bt, bb = f(c["body_top"]), f(c["body_bottom"])
        o, cl = (bb, bt) if c["up"] else (bt, bb)
        out.append({"o": o, "h": max(hi, lo), "l": min(hi, lo), "c": cl, "up": c["up"],
                    "x": (c["x0"] + c["x1"]) / 2.0})
    return out


def axis_label_rows(rgb: np.ndarray, x0: int, x1: int, y0: int = 0, y1: int = None,
                    min_gap: int = 3) -> list:
    """صفوفُ النصّ في شريط المحور [x0، x1) ⟵ مراكزُها الرأسيّة. النصُّ = بكسلاتٌ بعيدةٌ عن لون الخلفية
    (الوسيط) — تُجمع الصفوفُ المتّصلة (فجوةٌ أقلّ من `min_gap`) كتلةً واحدة."""
    y1 = rgb.shape[0] if y1 is None else y1
    strip = rgb[y0:y1, x0:x1].astype(np.int32)
    bg = np.median(strip.reshape(-1, 3), axis=0)
    diff = np.abs(strip - bg).sum(axis=-1) > 120
    rows = np.where(diff.sum(axis=1) >= 2)[0]
    out, start, prev = [], None, None
    for y in rows:
        if start is None:
            start = prev = y
            continue
        if y - prev >= min_gap:
            out.append((start + prev) / 2.0 + y0)
            start = y
        prev = y
    if start is not None:
        out.append((start + prev) / 2.0 + y0)
    return out


def series_corr(a: list, b: list) -> float:
    """ارتباطُ سلسلتين بعد مطابقة الطول (يُعاد أخذُ الأقصر عيّنةً على الأطول) — للترتيب بالشكل."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size < 3 or b.size < 3:
        return float("nan")
    n = min(a.size, b.size)
    ia = np.linspace(0, a.size - 1, n)
    ib = np.linspace(0, b.size - 1, n)
    aa = np.interp(ia, np.arange(a.size), a)
    bb = np.interp(ib, np.arange(b.size), b)
    if aa.std() < 1e-12 or bb.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(aa, bb)[0, 1])


def overlay(rgb: np.ndarray, candles: list, out_path: str) -> str:
    """🖼️ صورةُ التحقّق: مستطيلٌ لكلّ شمعةٍ مستخرجة (أزرق للصاعد · برتقاليّ للهابط) فوق الأصل."""
    from PIL import Image, ImageDraw                                 # noqa: PLC0415
    img = Image.fromarray(rgb).convert("RGB")
    d = ImageDraw.Draw(img)
    for c in candles:
        col = (40, 90, 255) if c["up"] else (255, 140, 0)
        d.rectangle([c["x0"] - 1, c["top"] - 1, c["x1"] + 1, c["bottom"] + 1], outline=col)
    img.save(out_path)
    return out_path


def pixel_summary(rgb: np.ndarray, box, pairs, log_scale=None, px_tol: float = 2.0):
    """ملخّصُ البكسل للبطاقة حين لا تسميةَ نصّيّة: أعلى/أدنى الشاشة وآخرُ إغلاق **بتسامحٍ مصرَّح**
    = `px_tol` بكسل × سعرُ البكسل عند ذلك المستوى (خطّيٌّ أو لوغاريتميّ بالمعايرة) ⟵ قاموسٌ أو `None`.
    يُكتب في البطاقة `{"v": …, "src": "pixel", "tol": …}` — فلا يُعامَل رقمُ البكسل معاملةَ النصّ."""
    x0, y0, x1, y1 = [int(v) for v in box]
    up, dn = candle_masks(rgb, box=(x0, y0, x1, y1))
    cands = find_candles(up, dn, x_off=x0, y_off=y0)
    f, is_log, err = calibrate(pairs, log_scale=log_scale)
    if f is None or not cands:
        return None
    hi_c = min(cands, key=lambda c: c["top"])
    lo_c = max(cands, key=lambda c: c["bottom"])
    last = max(cands, key=lambda c: (c["x0"] + c["x1"]) / 2.0)

    def tol_at(y):
        return px_tol * abs(f(y + 1) - f(y))
    last_y = last["body_top"] if last["up"] else last["body_bottom"]
    return {"n": len(cands), "log": is_log, "calib_err": err,
            "high": (f(hi_c["top"]), tol_at(hi_c["top"])),
            "low": (f(lo_c["bottom"]), tol_at(lo_c["bottom"])),
            "last": (f(last_y), tol_at(last_y))}
