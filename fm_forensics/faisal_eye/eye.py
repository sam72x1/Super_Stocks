#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""👁️ `T-FAISAL-EYE` — «عين فيصل» · المرحلة أ (العقد `T_FAISAL_EYE_prereg.md` · أمرُ المالك 2026-11-21).

  mask           — محلّيّ: نسخٌ محجوبةُ التاريخ لصور الاختبار الأربعين في `.scratch/` (مُتجاهَل · لا يُدفع).
  fetch          — رنر GitHub: شموعُ TradingView (1D · 240 · 1W) ومعاملاتُ ياهو لرموز الاختبار والمؤرَّخ ⟵ `data/bars/*.json.gz`.
  cand <id>      — محلّيّ: مرشَّحاتُ صورةٍ من بطاقتها ⟵ رسمٌ في `.scratch/` بلا تواريخ · والقرارُ يُكتب في الدفتر بيدي.
  score          — الدفترُ المودَع مقابل الحقيقة ⟵ `out/TEST.json|md` · **مرّةً واحدة**.
🔒 قياسٌ فقط: لا تلغرام · لا Polygon · لا أسرار · لا CONFIG يُسنَد · ولا تنادي أيَّ أداةٍ من `fm_forensics/date_candles/` (v1 · v2 مقفلان).
رموزُ الخروج: 0 تمّ · 5 مادّةٌ ناقصة · 7 صدر · 8 مُغلَق · 11 عقدٌ متغيّر.
"""
import bisect
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "T_FAISAL_EYE_prereg.md")
CONTRACT_SHA = "c82db6b982bb51a5c0828a92ce743d148500411c3fe5c1eff5f9d76164caa98c"                                                # يُملأ قبل الدمج · فارغٌ أو مخالف ⟵ خروج 11
DATA = os.path.join(HERE, "data")
BARS = os.path.join(DATA, "bars")
OUT = os.path.join(HERE, "out")
SCRATCH = os.path.join(HERE, ".scratch")                           # مُتجاهَل في .gitignore — الصورُ لا تُدفع
IMAGES = os.path.join(ROOT, "faisal_images")
REREAD = os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl")
HEADER = os.path.join(ROOT, "fm_forensics", "date_candles", "data", "header_dates.tsv")
OCR = os.path.join(ROOT, "fm_forensics", "date_candles", "data", "header_ocr.jsonl")
CARDS = os.path.join(DATA, "eye_cards.jsonl")
LEDGER = os.path.join(DATA, "eye_ledger.jsonl")
RC_OK, RC_DATA, RC_ONCE, RC_CLOSED, RC_CONTRACT = 0, 5, 7, 8, 11
CLOSED = False

TEST_IDS = ("IMG_0142", "IMG_0320", "IMG_0500", "IMG_0587", "IMG_0698", "TG_1823", "TG_1833", "TG_1834", "TG_1838", "TG_1851", "TG_1964",
            "TG_1997", "TG_2109", "TG_2112", "TG_2117", "TG_2121", "TG_2171", "TG_2196", "TG_2213", "TG_50575", "TG_50579", "TG_50818",
            "TG_50833", "TG_57872", "TG_57873", "TG_57879", "TG_57891", "TG_58046", "TG_58397", "TG_58423", "TG_58525", "TG_76004",
            "TG_76013", "TG_76016", "TG_76017", "TG_76019", "TG_76025", "TG_82792", "X_20260827_labt_supports_wait", "X_20260905_12")
SEEN_DATES = ("TG_76009", "TG_76014", "TG_82796", "TG_2095")       # تواريخُها رأيتُها في المحادثة — العقد §①-2
PX_TOL, CHG_TOL = 0.02, 1.0                                        # السعرُ ±2% (نصُّ المالك) · والتغيّرُ ±1 نقطة (هندسيّ)
N_TOL = 0.15                                                       # «عددُ الشموع تقريبًا» ±15% (هندسيّ)
MAX_CAND = 8
MIN_ANSWERED, HIT_MIN = 10, 0.85
DATE_FROM = "2023-01-01"
FRAMES = {"1D": "1D", "4H": "240", "1W": "1W"}
RIYADH = dt.timezone(dt.timedelta(hours=3))
DATE_RX = [re.compile(p) for p in (r"20\d\d", r"\d{1,2}/\d{1,2}/\d{2,4}", r"\d{4}/\d{1,2}/\d{1,2}", r"\d{1,2}/\d{1,2}\s*-\s*\d{1,2}:\d{2}",
                                     r"\d{1,2}:\d{2}\s*(ص|م|AM|PM|am|pm)", r"\bE[DS]T\b",
                                     r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
                                     r"(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)")]


def log(m=""):
    print(m, flush=True)


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def contract_ok():
    try:
        return bool(CONTRACT_SHA) and sha_of(CONTRACT) == CONTRACT_SHA
    except OSError:
        return False


def closed():
    return bool(CLOSED) and os.environ.get("FAISAL_EYE_REOPEN", "") != "1"


def guard_score(out_dir=None):
    out_dir = OUT if out_dir is None else out_dir
    if not contract_ok():
        return RC_CONTRACT
    if os.path.exists(os.path.join(out_dir, "TEST.json")):
        return RC_ONCE
    return RC_OK


# ══ المجموعات (نقيّة على الملفّات) ══════════════════════════════════════════════════════════════════════════════════════════════
def records():
    with open(REREAD, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def header_rows():
    with open(HEADER, encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r.get("conf") == "واثق"]


def dated_set():
    """المؤرَّخ سابقًا (العقد §③): «واثق» بطابع الرأس برمزٍ واحد ∪ سجلّ العين EXACT برمزٍ واحد ⟵ {id: {sym, src}}."""
    out = {}
    for r in header_rows():
        if r["symbol"] and "," not in r["symbol"]:
            out[r["file"]] = {"sym": r["symbol"], "src": "header"}
    for r in records():
        if r.get("id") and r.get("dprec") == "EXACT" and len(r.get("tk") or []) == 1 and r["id"] not in out:
            out[r["id"]] = {"sym": r["tk"][0], "src": "exact"}
    return out


def test_set():
    """مجموعةُ الاختبار الثابتة ⟵ {id: سجلّ العين} — وتُعاد فحصًا من التعريف (EXACT · رمزٌ واحد · خارج الـ55 والأربع)."""
    hdr = {r["file"] for r in header_rows()}
    got = {r["id"]: r for r in records() if r.get("id") and r.get("dprec") == "EXACT" and len(r.get("tk") or []) == 1
           and r["id"] not in hdr and r["id"] not in SEEN_DATES}
    return got


def image_path(i):
    for ext in ("jpg", "jpeg", "png"):
        p = os.path.join(IMAGES, f"{i}.{ext}")
        if os.path.exists(p):
            return p
    return None


def ocr_date_bands(path, pad=10):
    """OCR محلّيّ (tesseract · الأصلُ والمعكوس · عتبتان · تكبير 2×) ⟵ أشرطةٌ أفقيّة (y1، y2) لكلّ كلمةٍ تطابق نمطَ تاريخ (العقد §②-1 · تعديلٌ معلَن)."""
    import subprocess
    from PIL import Image, ImageOps
    g = Image.open(path).convert("L")
    out = []
    tmp = os.path.join(SCRATCH, "_ocr_tmp.png")
    for inv in (False, True):
        base = ImageOps.invert(g) if inv else g
        for thr in (110, 160):
            img = base.point(lambda v, t=thr: 255 if v > t else 0).resize((g.width * 2, g.height * 2))
            img.save(tmp)
            try:
                tsv = subprocess.run(["tesseract", tmp, "stdout", "-l", "eng", "--psm", "11", "tsv"], capture_output=True, text=True,
                                     timeout=120).stdout
            except Exception:                                    # noqa: BLE001
                continue
            for ln in tsv.splitlines()[1:]:
                t = ln.split("\t")
                if len(t) > 11 and t[11].strip() and any(rx.search(t[11]) for rx in DATE_RX + [re.compile(r"\d+/\d+/\d+")]):
                    y, h = int(t[7]) // 2, int(t[9]) // 2
                    out.append((max(0, y - pad), y + h + pad))
    return out


def date_boxes(lines, pad=4):
    """أسطرُ OCR [(نصّ، x1، y1، x2، y2، ثقة)] ⟵ مستطيلاتُ الحجب لكلّ سطرٍ يطابق نمطَ تاريخٍ أو ساعة (العقد §②-1)."""
    out = []
    for ln in lines or []:
        txt = str(ln[0])
        if any(rx.search(txt) for rx in DATE_RX):
            x1, y1, x2, y2 = (int(v) for v in ln[1:5])
            out.append((max(0, x1 - pad), max(0, y1 - pad), x2 + pad, y2 + pad))
    return out


# ══ الحقيقة والمرشَّحات (نقيّة) ════════════════════════════════════════════════════════════════════════════════════════════════
def truth_ny(rec):
    """تاريخُ سجلّ العين «YYYY-MM-DD HH:MM» بتوقيت الرياض ⟵ وقتُ نيويورك."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.strptime(rec["date"], "%Y-%m-%d %H:%M").replace(tzinfo=RIYADH)
    return t.astimezone(ZoneInfo("America/New_York"))


def truth_index(frame, bars, t_ny):
    """⟵ رقمُ آخر شمعةٍ مكتملة عند `t_ny` في الفريم (العقد §②-6) أو None."""
    if frame == "1D":
        day = t_ny.date().isoformat()
        cut = day if t_ny.hour >= 16 else (t_ny.date() - dt.timedelta(days=1)).isoformat()
        k = bisect.bisect_right([b[0] for b in bars], cut) - 1
    elif frame == "4H":
        ts = int(t_ny.timestamp())
        k = bisect.bisect_right([int(b[0]) + 4 * 3600 for b in bars], ts) - 1
    elif frame == "1W":
        k = bisect.bisect_right([b[0] for b in bars], t_ny.date().isoformat()) - 1
    else:
        return None
    return k if k >= 0 else None


def bar_day(frame, b):
    if frame == "4H":
        import tv_data as TV
        return TV.ny_day(int(b[0]))
    return b[0]


def split_factor(splits, end_day):
    """حاصلُ نِسب ياهو بعد نهاية النافذة (عكسيٌّ 1:10 = 0.1) ⟵ السعرُ يومَها = المسوّى × المعامل."""
    f = 1.0
    for d, r in splits or []:
        if d > end_day and r and r > 0:
            f *= float(r)
    return f


def _ok(a, b, tol=PX_TOL):
    return a is not None and b is not None and b > 0 and abs(a / b - 1.0) <= tol


def numbers_of(card):
    return [k for k in ("last", "chg", "top", "bottom") if card.get(k) is not None]


def candidates(card, bars, splits):
    """بطاقة ⟵ [(e، المعامل، طولُ النافذة)] تعبر كلَّ الأرقام المطبوعة (العقد §②-3) · مرتّبةٌ بالنهاية · ورقمان على الأقلّ وإلّا []."""
    if len(numbers_of(card)) < 2:
        return []
    n0 = int(card.get("n") or 0)
    frame = card["frame"]
    lens = sorted({max(2, int(round(n0 * (1 + d)))) for d in (-N_TOL, -N_TOL / 2, 0.0, N_TOL / 2, N_TOL)}) if n0 else [0]
    out = []
    for e in range(1, len(bars)):
        d_end = bar_day(frame, bars[e])
        if d_end < DATE_FROM:
            continue
        hit = None
        for f in sorted({1.0, split_factor(splits, d_end)}):
            c = float(bars[e][4]) * f
            if card.get("last") is not None and not _ok(c, card["last"]):
                continue
            if card.get("chg") is not None:
                p = float(bars[e - 1][4])
                if not (p > 0 and abs((float(bars[e][4]) / p - 1.0) * 100.0 - card["chg"]) <= CHG_TOL):
                    continue
            for n in lens:
                if card.get("top") is None and card.get("bottom") is None:
                    hit = (e, f, n0)
                    break
                if n < 2 or e - n + 1 < 0:
                    continue
                w = bars[e - n + 1:e + 1]
                if card.get("top") is not None and not _ok(max(float(b[2]) for b in w) * f, card["top"]):
                    continue
                if card.get("bottom") is not None and not _ok(min(float(b[3]) for b in w) * f, card["bottom"]):
                    continue
                hit = (e, f, n)
                break
            if hit:
                break
        if hit:
            out.append(hit)
    return out


def day_numbers(card, daily, splits):
    """بلا شموع (العقد §②-5): أيّامُ يوافق فيها الإغلاقُ × المعامل السعرَ ±2% والتغيّرُ ±1 نقطة ⟵ [e]."""
    if card.get("last") is None or card.get("chg") is None:
        return []
    out = []
    for e in range(1, len(daily)):
        if daily[e][0] < DATE_FROM:
            continue
        f = split_factor(splits, daily[e][0])
        p = float(daily[e - 1][4])
        if any(_ok(float(daily[e][4]) * g, card["last"]) for g in {1.0, f}) and p > 0 \
                and abs((float(daily[e][4]) / p - 1.0) * 100.0 - card["chg"]) <= CHG_TOL:
            out.append(e)
    return out


def verdict_of(row):
    """صفُّ الدفتر ⟵ هل هو مُجاب؟ «مطابق» (شكل) أو «يوم واحد» (أرقام)."""
    return row.get("verdict") in ("مطابق", "يوم واحد")


def score_rows(ledger, cards, bars_of, truth_of):
    """⟵ (الصفوف المقيَّمة، الملخّص) — الإصابةُ ±1 شمعة من شمعة الحقيقة في فريم البطاقة (العقد §②-6 · §②-7 · §②-8)."""
    rows, ans, hit = [], 0, 0
    for i in TEST_IDS:
        L = ledger.get(i) or {"verdict": "بلا دفتر"}
        c = cards.get(i) or {}
        r = {"id": i, "verdict": L.get("verdict"), "frame": c.get("frame"), "kind": c.get("kind")}
        if verdict_of(L):
            ans += 1
            fr = "1D" if L["verdict"] == "يوم واحد" else c.get("frame")
            bars = (bars_of(c.get("sym")) or {}).get(fr) or []
            k = truth_index(fr, bars, truth_of(i)) if bars else None
            e = L.get("e")
            ok = k is not None and e is not None and abs(int(e) - int(k)) <= 1
            hit += int(ok)
            r.update(e=e, truth=k, hit=ok, dist=(None if k is None or e is None else int(e) - int(k)))
        rows.append(r)
    n = len(TEST_IDS)
    leaks = sum(1 for i in TEST_IDS if (cards.get(i) or {}).get("kind") == "leak")
    summ = {"n": n, "leaks": leaks, "answered": ans, "hits": hit, "answer_rate": ans / n if n else None, "hit_rate": (hit / ans) if ans else None}
    summ["pass"] = bool(ans >= MIN_ANSWERED and summ["hit_rate"] is not None and summ["hit_rate"] >= HIT_MIN)
    return rows, summ


# ══ الأوضاع ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _load_jsonl(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(x) for x in fh if x.strip()]
    return {r["id"]: r for r in rows}


def load_bars(sym):
    p = os.path.join(BARS, f"{sym}.json.gz")
    if not os.path.exists(p):
        return None
    with gzip.open(p) as fh:
        return json.loads(fh.read().decode("utf-8"))


def mode_mask():
    from PIL import Image, ImageDraw
    os.makedirs(SCRATCH, exist_ok=True)
    ocr = {}
    with open(OCR, encoding="utf-8") as fh:
        for x in fh:
            j = json.loads(x)
            ocr[j["id"]] = j.get("lines") or []
    done = 0
    for i in TEST_IDS:
        p = image_path(i)
        if not p:
            log(f"⛔ {i}: لا صورة")
            continue
        im = Image.open(p).convert("RGB")
        dr = ImageDraw.Draw(im)
        boxes = date_boxes(ocr.get(i)) + [(0, y1, im.width, y2) for y1, y2 in ocr_date_bands(p)]
        for b in boxes:
            dr.rectangle(b, fill=(0, 0, 0))
        im.save(os.path.join(SCRATCH, f"mask_{i}.png"))
        done += 1
        log(f"🖤 {i}: محجوب {len(boxes)}")
    log(f"✅ {done}/{len(TEST_IDS)}")
    return RC_OK


def mode_fetch():
    import Super_stock as S
    import tv_data as TV
    syms = sorted({v["sym"] for v in dated_set().values()})
    log(f"🧺 الرموز {len(syms)}")
    tmap = S._tv_ticker_map() or {}
    full = {s: tmap.get(s) or f"NASDAQ:{s}" for s in syms}
    got = {}
    for fr, iv, n, ext in (("1D", "1D", 1500, False), ("4H", "240", 5000, True), ("1W", "1W", 400, False)):
        g = TV.fetch_many(sorted(set(full.values())), interval=iv, n=n, extended=ext, workers=4, retry_pass=True)
        got[fr] = g
        log(f"📺 {fr}: {sum(1 for s in syms if g.get(full[s]))}/{len(syms)}")
    os.makedirs(BARS, exist_ok=True)
    for s in syms:
        rec = {}
        for fr in FRAMES:
            b = got[fr].get(full[s]) or []
            if fr == "4H":
                rec[fr] = [[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5] or 0.0)] for x in b]
            else:
                rec[fr] = [[TV.ny_day(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5] or 0.0)] for x in b]
        try:
            import yfinance as yf
            sp = yf.Ticker(s).splits
            rec["splits"] = [[ix.date().isoformat(), float(v)] for ix, v in sp.items()] if sp is not None else []
        except Exception:                                            # noqa: BLE001
            rec["splits"] = None
        rec["tv"] = full[s]
        with gzip.open(os.path.join(BARS, f"{s}.json.gz"), "wb") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")).encode("utf-8"))
    log("✅ الجلب")
    return RC_OK


def render(card, bars, cands, out_png, masked_png):
    """الأصلُ المحجوب ‏+ حتى 8 مرشَّحاتٍ شموعًا بلا تواريخ ⟵ PNG في `.scratch/` · ويُرجع {حرف: e}."""
    from PIL import Image, ImageDraw
    W, H = 380, 260
    letters = "ABCDEFGH"
    org = Image.open(masked_png).convert("RGB")
    s = 560.0 / org.height
    org = org.resize((max(1, int(org.width * s)), 560))
    canvas = Image.new("RGB", (org.width + 4 * W + 20, max(560, 2 * H + 10)), (255, 255, 255))
    canvas.paste(org, (0, 0))
    dr = ImageDraw.Draw(canvas)
    mp = {}
    for k, (e, f, n) in enumerate(cands[:MAX_CAND]):
        n = n or int(card.get("n") or 40)
        w = bars[max(0, e - n + 1):e + 1]
        x0, y0 = org.width + 10 + (k % 4) * W, (k // 4) * (H + 10)
        hi = max(float(b[2]) for b in w)
        lo = min(float(b[3]) for b in w)
        rng = (hi - lo) or 1.0
        cw = (W - 20) / max(1, len(w))
        dr.rectangle((x0, y0, x0 + W - 6, y0 + H), outline=(180, 180, 180))
        for j, b in enumerate(w):
            o, h, l, c = (float(v) for v in b[1:5])
            X = x0 + 10 + j * cw + cw / 2
            Y = lambda v: y0 + 10 + (hi - v) / rng * (H - 20)            # noqa: E731
            col = (38, 166, 91) if c >= o else (220, 53, 69)
            dr.line((X, Y(h), X, Y(l)), fill=col)
            dr.rectangle((X - max(1, cw * 0.35), min(Y(o), Y(c)), X + max(1, cw * 0.35), max(Y(o), Y(c)) + 1), fill=col)
        dr.text((x0 + 6, y0 + 4), letters[k], fill=(0, 0, 0))
        mp[letters[k]] = {"e": e, "f": f, "n": n}
    canvas.save(out_png)
    return mp


def mode_cand(i):
    cards = _load_jsonl(CARDS)
    c = cards.get(i)
    if not c:
        log(f"⛔ {i}: لا بطاقة")
        return RC_DATA
    B = load_bars(c["sym"])
    if not B:
        log(f"⛔ {i}: لا شموع لـ{c['sym']}")
        return RC_DATA
    os.makedirs(SCRATCH, exist_ok=True)
    if c.get("kind") == "numbers" or c.get("frame") not in FRAMES:      # العقد §②-3: فريمٌ غيرُ 1D/4H/1W ⟵ أرقامٌ فقط
        days = day_numbers(c, B.get("1D") or [], B.get("splits"))
        res = {"id": i, "kind": "numbers", "days": days}
        log(json.dumps({"id": i, "n_days": len(days), "e": days[:3]}, ensure_ascii=False))
    else:
        bars = B.get(c["frame"]) or []
        cs = candidates(c, bars, B.get("splits"))
        res = {"id": i, "kind": "candles", "n_cand": len(cs)}
        if 0 < len(cs) <= MAX_CAND:
            res["map"] = render(c, bars, cs, os.path.join(SCRATCH, f"cand_{i}.png"), os.path.join(SCRATCH, f"mask_{i}.png"))
        log(json.dumps({"id": i, "n_cand": len(cs)}, ensure_ascii=False))
    with open(os.path.join(SCRATCH, f"cand_{i}.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False)
    return RC_OK


def mode_score(out_dir=None):
    out_dir = OUT if out_dir is None else out_dir
    rc = guard_score(out_dir)
    if rc:
        log(f"⛔ الحارس — خروج {rc}")
        return rc
    cards, ledger, T = _load_jsonl(CARDS), _load_jsonl(LEDGER), test_set()
    if not cards or not ledger:
        log(f"⛔ البطاقاتُ أو الدفترُ غائب — خروج {RC_DATA}")
        return RC_DATA
    rows, summ = score_rows(ledger, cards, load_bars, lambda i: truth_ny(T[i]))
    res = {"rows": rows, "summary": summ, "cards_sha": sha_of(CARDS), "ledger_sha": sha_of(LEDGER), "contract_sha": CONTRACT_SHA}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "TEST.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    md = render_test(res)
    with open(os.path.join(out_dir, "TEST.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    return RC_OK


def render_test(res):
    s = res["summary"]
    pct = lambda x: "—" if x is None else f"{x * 100:.1f}%"           # noqa: E731
    L = ["# 👁️ `T-FAISAL-EYE` — اختبارُ الدقّة الأعمى (المرحلة أ)", "",
         f"- الصور {s['n']} · المُجاب {s['answered']} (نسبةُ الإجابة {pct(s['answer_rate'])}) · المصيب ±1 شمعة {s['hits']} "
         f"(نسبةُ الإصابة {pct(s['hit_rate'])}) · البوّابة: 85% فأكثر و10 مُجاب فأكثر ⟵ **{'تعبر' if s['pass'] else 'لا تعبر'}**", "",
         "| الصورة | النوع | الفريم | الحكم | فرقُ الشموع | إصابة |", "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        d = r.get("dist")
        L.append(f"| `{r['id']}` | {r.get('kind') or '—'} | {r.get('frame') or '—'} | {r.get('verdict')} | {'—' if d is None else d} | "
                 f"{'—' if 'hit' not in r else ('✅' if r['hit'] else '❌')} |")
    L += ["", f"> البطاقات `{res['cards_sha'][:12]}` · الدفتر `{res['ledger_sha'][:12]}` — أُودعا قبل التصحيح."]
    return "\n".join(L) + "\n"


def main(argv):
    if closed():
        log(f"🔒 `T-FAISAL-EYE` مُغلَقٌ مُنفَّذًا — الفتحُ إقرارُ المالك `FAISAL_EYE_REOPEN=1` · خروج {RC_CLOSED}")
        return RC_CLOSED
    if len(argv) >= 2 and argv[1] == "mask":
        return mode_mask()
    if len(argv) >= 2 and argv[1] == "fetch":
        return mode_fetch()
    if len(argv) >= 3 and argv[1] == "cand":
        return mode_cand(argv[2])
    if len(argv) >= 2 and argv[1] == "score":
        return mode_score()
    log(__doc__)
    return RC_DATA


if __name__ == "__main__":
    sys.exit(main(sys.argv))
