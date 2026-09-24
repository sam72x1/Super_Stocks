# -*- coding: utf-8 -*-
"""🎨 **رسمُ الشموع** — لمُعرِّف الشارت: صورةُ المقارنة بالعين (الشرطُ الثالث للثقة) والمجموعةُ المصنوعة.

**دالّةٌ نقيّة** `render_candles(bars, …)` ⟵ `(صورة PIL، meta)` بلا شبكة ولا حالة:
  • نمطا تريدنج فيو (فاتح/داكن) بألوان الصعود/الهبوط المعتادة (#26a69a / #ef5350) — لأن الغرضَ
    **مطابقةُ شكل الأصل** لا تصميمٌ جديد · ومحورُ السعر يمينًا بتسمياتٍ «مستديرة» · خطّيٌّ أو لوغاريتميّ.
  • `marks` = تسمياتُ أعلى/أدنى الشاشة كما يرسمها التطبيق · `hlines` = خطوطٌ أفقيّةٌ مرسومة (خطوطُ فيصل).
  • `meta` تحمل **الحقيقةَ المرسومة** (تسمياتُ المحور بمواضعها · صناديقُ الشموع) ⇒ تقيس دقّةَ قراءة البكسل.
⚠️ **النصُّ داخل الصورة إنجليزيٌّ/أرقام**: خطوطُ الجلسة بلا تشكيلٍ عربيّ (لا raqm) فيتقطّع العربيّ.
"""
from __future__ import annotations

import math

THEMES = {
    "light": {"bg": (255, 255, 255), "grid": (236, 239, 244), "text": (60, 64, 72),
              "up": (38, 166, 154), "down": (239, 83, 80), "axis": (180, 186, 196)},
    "dark": {"bg": (19, 23, 34), "grid": (42, 46, 57), "text": (209, 212, 220),
             "up": (38, 166, 154), "down": (239, 83, 80), "axis": (80, 86, 100)},
}
FAISAL_LINE_COLORS = {"support": (230, 40, 40), "entry": (90, 30, 150), "resistance": (20, 20, 20),
                      "target": (40, 110, 230), "orange": (230, 160, 40)}


def _font(size: int):
    from PIL import ImageFont                                         # noqa: PLC0415
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def nice_ticks(lo: float, hi: float, n: int = 8) -> list:
    """تسمياتُ محورٍ «مستديرة» بين lo وhi (خطوةُ 1/2/2.5/5 × 10^k)."""
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo:
        return [lo]
    raw = (hi - lo) / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=10 * mag)
    start = math.ceil(lo / step) * step
    out, v = [], start
    while v <= hi + 1e-12:
        out.append(round(v, 10))
        v += step
    return out


def fmt_price(v: float, decimals: int = None) -> str:
    if decimals is None:
        decimals = 3 if abs(v) < 100 else 2
    return f"{v:.{decimals}f}"


def render_candles(bars: list, width: int = 900, height: int = 640, theme: str = "light",
                   title: str = "", marks=None, hlines=None, log_scale: bool = False,
                   decimals: int = None, axis_w: int = 90, margin: int = 24):
    """الشموعُ `[{o,h,l,c}]` ⟵ `(صورة، meta)`. `marks=[(فهرس، سعر، نصّ)]` · `hlines=[(سعر، لون، نصّ)]`."""
    from PIL import Image, ImageDraw                                  # noqa: PLC0415
    th = THEMES.get(theme, THEMES["light"])
    img = Image.new("RGB", (width, height), th["bg"])
    d = ImageDraw.Draw(img)
    f_small, f_title = _font(13), _font(16)
    top = margin + (26 if title else 0)
    bottom = height - margin
    left, right = margin, width - axis_w
    his = [b["h"] for b in bars] + [p for p, _, _ in (hlines or [])]
    los = [b["l"] for b in bars] + [p for p, _, _ in (hlines or [])]
    hi, lo = max(his), min(los)
    padv = (hi - lo) * 0.06 or max(abs(hi) * 0.05, 1e-6)
    hi, lo = hi + padv, lo - padv
    if log_scale:
        lo = max(lo, min(b["l"] for b in bars) * 0.9, 1e-6)

    def y_of(p: float) -> float:
        if log_scale:
            p = max(p, 1e-9)
            return bottom - (math.log(p) - math.log(lo)) / (math.log(hi) - math.log(lo)) * (bottom - top)
        return bottom - (p - lo) / (hi - lo) * (bottom - top)

    ticks = nice_ticks(lo, hi)
    meta = {"axis": [], "candles": [], "marks": [], "hlines": [], "box": (left, top, right, bottom),
            "log": log_scale, "theme": theme}
    for t in ticks:
        y = y_of(t)
        if y < top or y > bottom:
            continue
        d.line([(left, y), (right, y)], fill=th["grid"], width=1)
        txt = fmt_price(t, decimals)
        d.text((right + 8, y - 8), txt, fill=th["text"], font=f_small)
        meta["axis"].append((y, txt))
    n = len(bars)
    step = (right - left) / max(n, 1)
    body_w = max(1, int(step * 0.62))
    for i, b in enumerate(bars):
        cx = left + step * (i + 0.5)
        col = th["up"] if b["c"] >= b["o"] else th["down"]
        yh, yl = y_of(b["h"]), y_of(b["l"])
        yo, yc = y_of(b["o"]), y_of(b["c"])
        d.line([(cx, yh), (cx, yl)], fill=col, width=1)
        y0, y1 = min(yo, yc), max(yo, yc)
        if y1 - y0 < 1:
            y1 = y0 + 1
        d.rectangle([cx - body_w / 2, y0, cx + body_w / 2, y1], fill=col)
        meta["candles"].append({"x": cx, "top": yh, "bottom": yl, "body_top": y0, "body_bottom": y1,
                                "up": b["c"] >= b["o"]})
    for p, col, txt in hlines or []:
        y = y_of(p)
        color = FAISAL_LINE_COLORS.get(col, col) if isinstance(col, str) else col
        d.line([(left, y), (right, y)], fill=color, width=2)
        label = txt or fmt_price(p, decimals)
        tw = d.textlength(label, font=f_small)
        d.rectangle([right + 2, y - 10, right + 12 + tw, y + 9], fill=color)
        d.text((right + 7, y - 8), label, fill=(255, 255, 255), font=f_small)
        meta["hlines"].append((y, label))
    for i, p, txt in marks or []:
        cx = left + step * (i + 0.5)
        y = y_of(p)
        d.line([(cx, y), (cx + 26, y)], fill=th["text"], width=1)
        d.text((cx + 30, y - 8), txt, fill=th["text"], font=f_small)
        meta["marks"].append((cx, y, txt))
    if title:
        d.text((margin, margin - 4), title, fill=th["text"], font=f_title)
    return img, meta


def side_by_side(left_img, right_img, height: int = 700, gap: int = 16, bg=(255, 255, 255),
                 captions=("", "")):
    """صورتان جنبًا إلى جنب بارتفاعٍ واحد (للمقارنة بالعين) مع تعليقٍ فوق كلٍّ منهما."""
    from PIL import Image, ImageDraw                                  # noqa: PLC0415

    def fit(im):
        w, h = im.size
        return im.resize((max(1, int(w * height / h)), height))

    a, b = fit(left_img.convert("RGB")), fit(right_img.convert("RGB"))
    cap_h = 30 if any(captions) else 0
    out = Image.new("RGB", (a.width + b.width + gap, height + cap_h), bg)
    out.paste(a, (0, cap_h))
    out.paste(b, (a.width + gap, cap_h))
    if cap_h:
        d = ImageDraw.Draw(out)
        f = _font(16)
        d.text((6, 6), captions[0], fill=(30, 30, 30), font=f)
        d.text((a.width + gap + 6, 6), captions[1], fill=(30, 30, 30), font=f)
    return out
