# -*- coding: utf-8 -*-
"""📱🕯️ قارئُ بطاقة الشموع بأسلوب لقطات تطبيق فيصل (`T_DATE_CANDLES_ADDENDUM_6.md §④`) — قراءةٌ فقط · بلا شبكة (OCR محلّيّ).

الصورة ⟵ ① سطرُ «VOL(5,10,20)» (قراءةٌ آليّة) = أسفلُ لوحة السعر ⟵ ② حدودُ لقطة التطبيق (الخلفيّةُ البيضاء على صفّه) ⟵ ③ الفريم من
حبّة التبويب الخضراء الفاتحة فوق اللوحة (موضعُها النسبيّ) ⟵ ④ الشموع بأقنعة `chart_pixels` ومكوّنات `auto_card` وشبكته **بالاسم** ⟵
⑤ المعايرةُ من وسمَي التطبيق (أعلى ذيلٍ وأدنى ذيلٍ ظاهرَين يُكتبان رقمًا بجانبهما) ⟵ ⑥ بطاقةٌ بصيغة `auto_card` حرفًا.
🔒 لا تاريخَ يُقرأ ولا يُكتب في البطاقة (التاريخُ ناتجُ المطابقة وحدَها) · والطابعُ لا يدخل القارئ.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_card as AC  # noqa: E402  (بُنيت للملحق 2: مكوّناتٌ وشبكةٌ وشمعة على شارتات TradingView)
import chart_pixels as P  # noqa: E402  (بُنيت لمُعرِّف الشارت: أقنعةُ الشموع)

CARD_APP = 6                 # نسخةُ البطاقة (الملحق 6)
# ── المعلماتُ الحرّة (§④ — تُضبط على نصف المعايرة وحدَه ثمّ تُجمَّد ببصمة الملفّ) ──────────────────────────────
PANEL_OCR_SCALE = 4          # تكبيرُ قصاصة اللوحة لقراءة وسمَي القمّة والقاع
WHITE_MIN = 235              # بكسلٌ أبيض (خلفيّةُ التطبيق) = كلُّ قناةٍ فوقه
PILL_G_MIN, PILL_GR_MIN, PILL_GB_MIN = 235, 8, 2   # حبّةُ التبويب: أخضرُ فاتح (G عالٍ · G−R · G−B)
PILL_MIN_W = 14              # أدنى عرضٍ لجريان الحبّة (بكسل)
TAB_EDGES = (0.47, 0.655, 0.83)   # موضعُ الحبّة النسبيّ: <0.47 «4 ساعات» · <0.655 «أسبوعي» · <0.83 «يومي» · وإلّا «الكل»
HL_TOL = 12                  # أقصى بعدٍ رأسيٍّ بين مركز رقم الوسم وطرف الذيل (بكسل)
_NUM = re.compile(r"^\$?(\d{1,5}(?:[.,]\d{1,4})?)$")


def ocr_words(rgb: np.ndarray, scale: int = 4, box=None) -> list:
    """tesseract `--psm 11` ⟵ [(نص، x0، y0، x1، y1، ثقة)] بإحداثيّات الصورة الأصل · و`box`=(x0,y0,x1,y1) قصاصة."""
    from PIL import Image                                          # noqa: PLC0415
    ox, oy = 0, 0
    im = Image.fromarray(rgb.astype("uint8"))
    if box is not None:
        ox, oy = int(box[0]), int(box[1])
        im = im.crop(tuple(int(v) for v in box))
    W, H = im.size
    if W < 4 or H < 4:
        return []
    big = im.resize((W * scale, H * scale), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        big.save(t.name)
        out = subprocess.run(["tesseract", t.name, "stdout", "--psm", "11", "tsv"], capture_output=True, text=True,
                             timeout=180).stdout
    words = []
    for row in out.splitlines()[1:]:
        p = row.split("\t")
        if len(p) < 12 or not p[11].strip():
            continue
        x, y, w, h = (int(p[6]) / scale + ox, int(p[7]) / scale + oy, int(p[8]) / scale, int(p[9]) / scale)
        words.append((p[11].strip(), x, y, x + w, y + h, float(p[10])))
    return words


def app_bounds(rgb: np.ndarray, x: float, y: float):
    """حدودُ لقطة التطبيق على صفّ `y` حول `x`: أبعدُ بكسلٍ أبيض متّصلٍ يمينًا ويسارًا (يتسامح مع نصٍّ ملوّن بفجوةٍ حتى 40 بكسل)."""
    H, W = rgb.shape[:2]
    yy = int(min(max(y, 0), H - 1))
    row = (rgb[yy] >= WHITE_MIN).all(axis=1)
    xi = int(min(max(x, 0), W - 1))

    def walk(step):
        last, gap, i = xi, 0, xi
        while 0 <= i < W:
            if row[i]:
                last, gap = i, 0
            else:
                gap += 1
                if gap > 40:
                    break
            i += step
        return last
    return walk(-1), walk(1)


def _num(txt: str):
    m = _NUM.match(txt.replace(" ", ""))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


PILL_FILL_MIN = 0.50          # حبّةُ التبويب: نسبةُ امتلاء مستطيلها بالأخضر الفاتح (النصُّ داخلها يُنقصها)
PILL_W = (15, 120)            # عرضُ الحبّة (بكسل)
PILL_H = (9, 40)              # ارتفاعُها
BAND_TOP_PAD = 30             # أعلى اللوحة = أسفلُ الحبّة ‏+ هذا (يتخطّى صفَّ «VWAP»)
BAND_MAX_FRAC = 1.2           # أقصى ارتفاعٍ للّوحة = هذا × عرضُ التطبيق
PROFILE_MIN_COLS = 20         # أدنى أعمدةٍ ملوّنة في اللوحة
ERASE_PAD = 3                 # هامشُ محو مستطيل الكلمة من القناع (بكسل)
WORD_CONF = 30                # كلمةُ OCR بثقةٍ فوقها تُمحى من القناع (أرقامُ المحور والوسوم)


def white_box(rgb: np.ndarray, x: int, y: int):
    """مستطيلُ لقطة التطبيق حول (x, y): أبعدُ أبيض يمينًا ويسارًا على صفّ y ثمّ أعلى/أسفل على عمود المركز."""
    left, right = app_bounds(rgb, x, y)
    H = rgb.shape[0]
    cx = (left + right) // 2
    col = (rgb[:, cx] >= WHITE_MIN).all(axis=1)

    def walk(step):
        last, gap, i = y, 0, y
        while 0 <= i < H:
            if col[i]:
                last, gap = i, 0
            else:
                gap += 1
                if gap > 120:
                    break
            i += step
        return last
    return left, walk(-1), right, walk(1)


def find_pill(rgb: np.ndarray) -> list:
    """حبّاتُ التبويب المرشَّحة (أخضرُ فاتحٌ بامتلاءٍ وأبعادِ حبّة) من الأعلى ⟵ [(x0, y0, x1, y1)]."""
    a = rgb.astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (g >= PILL_G_MIN) & (g - r >= PILL_GR_MIN) & (g - b >= PILL_GB_MIN)
    best = []
    for c in AC.components(m):
        w, h = c["x1"] - c["x0"] + 1, c["y1"] - c["y0"] + 1
        if PILL_W[0] <= w <= PILL_W[1] and PILL_H[0] <= h <= PILL_H[1] and c["npx"] >= PILL_FILL_MIN * w * h \
                and w >= h:
            best.append((c["y0"], c["x0"], c["x1"], c["y1"]))
    return [(x0, y0, x1, y1) for y0, x0, x1, y1 in sorted(best)]


UP_SAT_MIN = 0.15            # أخضرُ التطبيق الفاتح (شموعٌ مجوّفة · ضغطُ JPEG يُضعف تشبّعَها) — أدنى من `chart_pixels.SAT_MIN`
DN_SAT_MIN = 0.20


def _colored(rgb: np.ndarray):
    """أقنعةُ الصاعد والهابط بتدرّجات `chart_pixels` وتشبّعٍ خاصٍّ بالتطبيق ⟵ (صاعد، هابط) بعد حذف الخطوط الطويلة."""
    h, s, v = P.rgb_to_hsv(rgb)
    up = (s >= UP_SAT_MIN) & (v >= P.VAL_MIN) & P._in_ranges(h, P.UP_HUES)
    dn = (s >= DN_SAT_MIN) & (v >= P.VAL_MIN) & P._in_ranges(h, P.DOWN_HUES)
    min_len = max(8, int(P.LINE_MIN_FRAC * rgb.shape[1]))
    return P.remove_long_runs(up, min_len), P.remove_long_runs(dn, min_len)


AXIS_FRAC = 0.12              # عمودُ أرقام المحور يسار اللوحة (نسبةٌ من عرضها)
AXIS_FIT_PX = 3.0             # أقصى بعد رقم المحور عن خطّه (بكسل)
VWAP_SEARCH = 120             # صفُّ «VWAP» يُبحث عنه تحت الحبّة بهذا المدى (بكسل)
PILL_TRIES = 3                # حبّاتٌ مرشَّحة من الأعلى تُجرَّب حتى يُقرأ «VOL» تحتها


def _panel(rgb: np.ndarray, pill) -> dict:
    """حبّة ⟵ {pill, app, tab_rel, frame, xl, xr, yt, yb, vb, words, band, vol_base}."""
    H = rgb.shape[0]
    px0, py0, px1, py1 = pill
    left, top_app, right, bot_app = white_box(rgb, (px0 + px1) // 2, (py0 + py1) // 2)
    rel = ((px0 + px1) / 2.0 - left) / float(max(1, right - left))
    frame = "4H" if rel < TAB_EDGES[0] else "1W" if rel < TAB_EDGES[1] else "1D" if rel < TAB_EDGES[2] else "line"
    out = {"pill": [px0, py0, px1, py1], "app": [left, top_app, right, bot_app], "tab_rel": round(rel, 3), "frame": frame}
    if frame == "line":
        return out
    xl, xr = left + 3, right - 3
    yt = py1 + BAND_TOP_PAD
    yb = min(bot_app, H - 1, int(yt + BAND_MAX_FRAC * (right - left)))
    if yb - yt < 20 or xr - xl < 20:
        return {**out, "vb": None}
    words = ocr_words(rgb, scale=PANEL_OCR_SCALE, box=(xl, py1 + 2, xr + 1, yb))
    vwap = [w for w in words if re.match(r"^VWAP", w[0], re.I) and w[2] <= py1 + VWAP_SEARCH]
    if vwap:
        yt = int(max(w[4] for w in vwap[:1])) + 3                  # أعلى اللوحة تحت صفّ «VWAP» مباشرةً
    vol = [w for w in words if re.match(r"^VO[LI1]", w[0], re.I) and w[2] > yt]
    dates = [w for w in words if re.match(r"^\d{1,2}/\d{2,4}$", w[0])]
    vb = None
    if vol:
        vb = min(w[2] for w in vol)
        dts = [w for w in dates if vb - 30 <= w[2] < vb]
        yb = int((min(w[2] for w in dts) if dts else vb) - 2)
    return {**out, "xl": xl, "xr": xr, "yt": yt, "yb": yb, "vb": vb, "words": words, "band": [yt, yb], "vol_base": vb}


def build_card_app(rgb: np.ndarray, words: list = None) -> dict:
    """صورةُ لقطة التطبيق ⟵ {"ok": True, …البطاقة} أو {"ok": False, "why": السبب, …التشخيص}. (`words` لا يُستعمل — توافق.)"""
    H, W = rgb.shape[:2]
    pills = find_pill(rgb)
    if not pills:
        return {"ok": False, "why": "لا حبّةَ تبويبٍ مظلَّلة (ليست لقطةَ تطبيق فيصل أو صغيرةٌ جدًّا)"}
    first = None
    for pill in pills[:PILL_TRIES]:
        got = _panel(rgb, pill)
        first = first or got
        if got.get("vb") is not None or got.get("frame") == "line":
            break
    else:
        got = first
    diag = {k: got[k] for k in ("pill", "app", "tab_rel", "frame", "band", "vol_base") if k in got}
    if got.get("frame") == "line":
        return {"ok": False, "why": "تبويبُ «الكل» — خطٌّ لا شموع", **diag}
    if got.get("vb") is None:
        return {"ok": False, "why": "لا سطرَ «VOL» تحت اللوحة", **diag}
    if got["yb"] - got["yt"] < 20:
        return {"ok": False, "why": "لوحةُ السعر أقصرُ من 20 بكسل", **diag}
    frame, xl, xr, yt, yb, words = got["frame"], got["xl"], got["xr"], got["yt"], got["yb"], got["words"]
    up, dn = _colored(rgb)
    words = words + ocr_words(rgb, scale=PANEL_OCR_SCALE, box=(xl, yt - 12, xr + 1, yb + 12))
    pct = [w[1] for w in words if "%" in w[0] and yt - 12 <= w[2] <= yb + 12 and w[1] > (xl + xr) / 2.0]
    if pct:
        xr = int(min(pct)) - ERASE_PAD                             # عمودُ النِّسَب يمين اللوحة ليس شموعًا
    up2, dn2 = up.copy(), dn.copy()
    for w in words:
        if w[5] >= WORD_CONF and re.match(r"^[-+~]?\d[\d.,]{2,}%?$", w[0].strip("“”\"'¥*")):
            a0, b0, a1, b1 = (int(w[1]) - ERASE_PAD, int(w[2]) - ERASE_PAD, int(w[3]) + ERASE_PAD + 1,
                              int(w[4]) + ERASE_PAD + 1)
            up2[b0:b1, a0:a1] = False
            dn2[b0:b1, a0:a1] = False
    m = (up2 | dn2)[yt:yb + 1, xl:xr + 1]
    occ = m.any(axis=0)
    cols = np.where(occ)[0]
    if cols.size < PROFILE_MIN_COLS:
        return {"ok": False, "why": f"أعمدةٌ ملوّنة {int(cols.size)} دون {PROFILE_MIN_COLS}", **diag}
    xa, xb = int(cols.min()), int(cols.max())
    tops = {int(j): int(np.argmax(m[:, j])) + yt for j in cols}
    bots = {int(j): int(m.shape[0] - 1 - np.argmax(m[::-1, j])) + yt for j in cols}
    y_hi, y_lo = min(tops.values()), max(bots.values())
    nums, seen = [], set()
    for w in words:
        if re.search(r"\d[.,]\d", w[0]) and (v := _num(w[0])) is not None and v > 0:
            key = (v, round((w[2] + w[4]) / 2.0))
            if key not in seen:
                seen.add(key)
                nums.append((v, (w[2] + w[4]) / 2.0, w[1]))
    hi_c = sorted((abs(cy - y_hi), v, cy) for v, cy, _ in nums if abs(cy - y_hi) <= HL_TOL)
    lo_c = sorted((abs(cy - y_lo), v, cy) for v, cy, _ in nums if abs(cy - y_lo) <= HL_TOL)
    # محورُ اليسار: أرقامٌ عشريّةٌ في أوّل `AXIS_FRAC` من عرض اللوحة ⟵ ميلُ السعر للبكسل (مساندٌ حين يغيب أحدُ الوسمَين)
    axis = sorted({(cy, v) for v, cy, x in nums if x <= xl + AXIS_FRAC * (xr - xl) and yt - 12 <= cy <= yb + 12})
    slope = None
    if len(axis) >= 2 and axis[-1][0] - axis[0][0] >= 20:
        ys_, vs_ = np.array([a[0] for a in axis]), np.array([a[1] for a in axis])
        sl, ic = np.polyfit(ys_, vs_, 1)
        if sl < 0 and float(np.abs(vs_ - (sl * ys_ + ic)).max()) <= abs(sl) * AXIS_FIT_PX:
            slope = float(sl)
    cover = cols.size / float(xb - xa + 1)
    diag.update({"y_hi": y_hi, "y_lo": y_lo, "x_span": [xa + xl, xb + xl], "cover": round(cover, 3),
                 "nums": [(v, round(cy, 1)) for v, cy, _ in nums][:20], "axis_slope": slope})
    if hi_c and lo_c and hi_c[0][1] > lo_c[0][1] and lo_c[0][2] - hi_c[0][2] >= 8:
        (_, v_hi, c_hi), (_, v_lo, c_lo) = hi_c[0], lo_c[0]
        a = (v_lo - v_hi) / float(c_lo - c_hi)                   # المِرساةُ مركزُ الوسم (خطُّه الأفقيّ عند طرف الذيل)
        cal = "hl"
    elif slope is not None and (hi_c or lo_c):
        _, v_hi, c_hi = (hi_c or lo_c)[0]
        a = slope
        v_lo = v_hi + (y_lo - c_hi) * a
        cal = "axis+" + ("hi" if hi_c else "lo")
    else:
        return {"ok": False, "why": "وسمُ القمّة أو القاع غيرُ مقروءٍ آليًّا", **diag}

    def f(y):
        return v_hi + (y - c_hi) * a
    if f(y_lo + 2) <= 0:
        return {"ok": False, "why": "سعرٌ غيرُ موجبٍ بعد المعايرة", **diag}
    prof = [[j - xa, round(f(tops[j]), 6), round(f(bots[j]), 6)] for j in sorted(tops)]
    return {"ok": True, "v": CARD_APP, "frame": frame, "hl": [v_hi, round(v_lo, 6)], "cal": cal, "px_price": round(abs(a), 8),
            "width": xb - xa + 1, "profile": prof, **diag}
