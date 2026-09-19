# -*- coding: utf-8 -*-
"""🧾📐 استخراجُ مستويات فيصل من الكاتالوج إلى **جدولٍ بنيويٍّ يُقاس عليه**.

**بحثٌ/توثيقٌ فقط:** لا يمسّ الفرزَ ولا حالةَ البوت ولا يرسل شيئًا. يقرأ
`FAISAL_IMAGES_CATALOG.md` ويكتب `faisal_levels_table.tsv` (+ ملخّصًا على الشاشة).

القاعدة: **كلُّ صفٍّ يحمل رقمَ سطر الكاتالوج والنصَّ الخام** ⇒ قابلٌ للتحقّق
سطرًا سطرًا (قفلُ `LVT1` يشترط ظهورَ الرقم على سطره). **ولا يُستنتَج تاريخٌ من
رقم الصورة**: التاريخُ إمّا من اسم الملفّ (`_20260905_`) أو من عنوان الدفعة
(أضعف — تاريخُ الاستلام لا تاريخُ الشارت)، وإلّا فارغ.

مفتاحُ الألوان (من رأس الكاتالوج): 🔴 دعم/وقف · ⚫ مقاومة · 🟣 طلب/دخول ·
🔵 هدفٌ بلا مقاومة · 🟠/🟢 غيرُ مفسَّرٍ عند فيصل (يُحفَظ كما هو).
"""
import csv
import re
import sys

CAT = "FAISAL_IMAGES_CATALOG.md"
OUT = "faisal_levels_table.tsv"
DERIVED = "faisal_derived_dates.tsv"      # ملفٌّ جانبيٌّ: تواريخُ **مُشتقّة** بمرساةٍ مقيسة
DERIVED_METHODS = {"indicator", "price"}  # مجموعةٌ مُغلَقة — ولا عضوَ يُضاف بلا أداةٍ تُعيد اشتقاقَه
#   `indicator` ⟵ faisal_indicator_anchor (نطاق recheck) · `price` ⟵ faisal_price_anchor (نطاق recheck)

COLOUR = {"🔴": "red", "⚫": "black", "🟣": "purple", "🔵": "blue",
          "🟠": "orange", "🟢": "green", "🟡": "yellow",
          "أحمر": "red", "أسود": "black", "بنفسجي": "purple", "أزرق": "blue",
          "أخضر": "green", "برتقالي": "orange", "أصفر": "yellow"}
ROLE = {"red": "support", "black": "resistance", "purple": "bid_entry",
        "blue": "target_clean", "orange": "unmapped", "green": "unmapped",
        "yellow": "unmapped"}

RE_EMOJI = re.compile(r"(🔴|⚫|🟣|🔵|🟠|🟢|🟡)\s?((?:\d+(?:\.\d+)?)(?:/\d+(?:\.\d+)?)*)")
RE_OLD = re.compile(r"((?:\d+\.\d+)(?:/\d+\.\d+)*)\((أحمر|أسود|بنفسجي|أزرق|أخضر|برتقالي|أصفر)[^)]*\)")
RE_IMG = re.compile(r"(?:TG|X|CH|APP|WA|IMG)_[A-Za-z0-9_./]+")
RE_FDATE = re.compile(r"_(20\d{2})(\d{2})(\d{2})_")
RE_HDATE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
RE_SYM = re.compile(r"\b([A-Z]{2,6})\b")


AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
RE_FRAME_WORD = re.compile(r"(أسبوعيّ?|الأسبوعي|شهري|4\s?س|4 ساعات|يوميّ?|اليومي|\d+\s?د\b|دقيقة|دقائق|لحظي)")


def frame_before(line: str, pos: int, fallback: str) -> str:
    """الفريمُ = آخرُ كلمةِ فريمٍ **قبل** موضع المستوى في السطر نفسِه (شارتان في
    صفٍّ واحد: «أسبوعيّ 🟣… ⟵⟶ يوميّ ⚫…»)، وإلّا فريمُ الصفّ/القسم."""
    seg = line[:pos].translate(AR_DIGITS)
    hits = list(RE_FRAME_WORD.finditer(seg))
    if not hits:
        return fallback
    f = frame_of(hits[-1].group(1))
    return f if f != "unknown" else fallback


def frame_of(txt: str) -> str:
    t = (txt or "").translate(AR_DIGITS)
    if re.search(r"أسبوع", t):
        return "weekly"
    if re.search(r"شهري", t):
        return "monthly"
    if re.search(r"4\s?س|4 ساعات|4h", t):
        return "h4"
    if re.search(r"\d+\s?د\b|دقيقة|دقائق|ساعت|ساعة|30د|5د|15د|لحظي", t):
        return "intraday"
    if re.search(r"يومي|يوميّ", t):
        return "daily"
    return "unknown"


def load_derived(path: str = DERIVED) -> dict:
    """الملفُّ الجانبيُّ للتواريخ المُشتقّة: `(رمز, سطر)` ⟶ `(تاريخ, طريقة)`.

    **فاشلٌ-آمن:** غيابُ الملفّ ⇒ قاموسٌ فارغ ⇒ الجدولُ كما كان بت-بت. والصفُّ
    الذي طريقتُه خارج `DERIVED_METHODS` أو تاريخُه غيرُ `YYYY-MM-DD` **يُسقَط**.
    """
    out = {}
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return out
    with fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            m = (r.get("method") or "").strip()
            d = (r.get("date") or "").strip()
            if m not in DERIVED_METHODS or not RE_HDATE.fullmatch(d):
                continue
            try:
                out[((r.get("symbol") or "").strip(), int(r["line"]))] = (d, m)
            except (KeyError, TypeError, ValueError):
                continue
    return out


def apply_derived(rows: list, derived: dict) -> int:
    """يملأ تاريخَ الصفوف **الفارغة وحدَها** من الملفّ الجانبيّ بوسمِ مصدرٍ مستقلّ.

    🔒 **لا يدهس مصدرًا مسجَّلًا** (`filename`/`header`): المسجَّلُ أقوى من المُشتقّ،
    والوسمُ يبقى مميَّزًا فتقرأ كلُّ تجربةٍ أنّ التاريخَ **مُشتقٌّ لا مسجَّل**.
    يُرجع عددَ ما طُبِّق.
    """
    n = 0
    for r in rows:
        if r["date"]:
            continue
        hit = derived.get((r["symbol"], r["line"]))
        if not hit:
            continue
        r["date"], r["date_source"] = hit
        n += 1
    return n


def main() -> int:
    lines = open(CAT, encoding="utf-8").read().splitlines()
    rows = []
    sec_sym = sec_frame = sec_imgs = ""
    batch_date = ""
    for i, raw in enumerate(lines, 1):
        l = raw.strip()
        if l.startswith("## "):
            sec_sym = sec_frame = sec_imgs = ""
            m = RE_HDATE.search(l)
            batch_date = m.group(1) if m else ""
            continue
        if l.startswith("### "):
            h = l[4:]
            m = RE_SYM.match(h)
            sec_sym = m.group(1) if m else ""
            sec_frame = frame_of(h)
            sec_imgs = " ".join(RE_IMG.findall(h))
            continue
        sym, frame, imgs = sec_sym, sec_frame, sec_imgs
        # صفُّ جدولٍ: | `IMG` | SYM frame | ... |
        if l.startswith("|") and l.count("|") >= 4:
            cells = [c.strip() for c in l.strip("|").split("|")]
            if len(cells) >= 2 and RE_IMG.search(cells[0]):
                imgs = " ".join(RE_IMG.findall(cells[0]))
                m = RE_SYM.match(cells[1].replace("$", ""))
                sym = m.group(1) if m else sym
                frame = frame_of(cells[1])
        # رأسُ نقطةٍ داخليّ: "- **ACCL — ٤س (8107/8108)**: …"
        mb = re.match(r"^-\s*\*\*([A-Z]{2,6})\s*[—-]\s*([^(*]+?)\s*(\(([^)]*)\))?\*\*", l)
        if mb:
            sym = mb.group(1)
            frame = frame_of(mb.group(2))
            if mb.group(4):
                imgs = " ".join(("IMG_" + x.strip()) if x.strip().isdigit() else x.strip()
                                for x in mb.group(4).split("/"))
        # سطرُ فريمٍ فرعيّ داخل قسم: "- 4س:" / "- يومي 7028:" / "- الأسبوعي (6476):"
        mm = re.match(r"^-\s*(يومي|يوميّ|الأسبوعي|أسبوعي|4س|4 ساعات|30د|5د|15د|دقيقة|شهري)[^:]{0,20}:", l)
        if mm:
            frame = frame_of(mm.group(1))
            sub = RE_IMG.findall(l)
            if sub:
                imgs = " ".join(sub)
        # التاريخ: من اسم الملفّ أوّلًا (أقوى) · ثمّ عنوانُ الدفعة (أضعف)
        date, dsrc = "", ""
        fm = RE_FDATE.search(imgs)
        if fm:
            date, dsrc = f"{fm.group(1)}-{fm.group(2)}-{fm.group(3)}", "filename"
        elif batch_date:
            date, dsrc = batch_date, "header"
        auto = any(x.startswith(("CH_", "APP_")) for x in imgs.split())
        found = []
        for m in RE_EMOJI.finditer(l):
            col = COLOUR[m.group(1)]
            fr = frame_before(l, m.start(), frame)
            for v in m.group(2).split("/"):
                found.append((col, v, m.group(0), fr))
        for m in RE_OLD.finditer(l):
            col = COLOUR[m.group(2)]
            fr = frame_before(l, m.start(), frame)
            for v in m.group(1).split("/"):
                found.append((col, v, m.group(0), fr))
        for col, v, snippet, fr in found:
            try:
                lv = float(v)
            except ValueError:
                continue
            rows.append({"line": i, "images": imgs, "symbol": sym, "date": date,
                         "date_source": dsrc, "frame": fr, "colour": col,
                         "role": ROLE.get(col, "unmapped"), "level": lv,
                         "auto_chart": int(auto), "raw": snippet})
    from collections import Counter
    n_der = apply_derived(rows, load_derived())
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    # ── ملخّصٌ صادق ────────────────────────────────────────────────────────
    print(f"🧾📐 صفوفُ المستويات المستخرَجة: {len(rows)} ⟶ {OUT}")
    print("   بالدور:", dict(Counter(r["role"] for r in rows)))
    print("   بالفريم:", dict(Counter(r["frame"] for r in rows)))
    print("   بمصدر التاريخ:", dict(Counter(r["date_source"] or "none" for r in rows)))
    _per = Counter(r["date_source"] for r in rows if r["date_source"] in DERIVED_METHODS)
    print(f"   📅 مُشتقٌّ (ملفٌّ جانبيّ): {n_der} صفًّا ⟵ {DERIVED} · بالطريقة: {dict(_per)}"
          " (لا يدهس مسجَّلًا · ولا يُقرأ مسجَّلًا)")
    syms = {r["symbol"] for r in rows if r["symbol"]}
    print(f"   رموزٌ متمايزة: {len(syms)} · بلا رمز: {sum(1 for r in rows if not r['symbol'])}")
    print(f"   شارتاتٌ آليّة (CH_/APP_): {sum(r['auto_chart'] for r in rows)}")
    gov = [r for r in rows if r["role"] == "support" and r["frame"] == "daily"
           and not r["auto_chart"]]
    g_f = [r for r in gov if r["date_source"] == "filename"]
    g_h = [r for r in gov if r["date_source"] == "header"]
    g_i = [r for r in gov if r["date_source"] in DERIVED_METHODS]
    g_by = Counter(r["date_source"] for r in g_i)
    print()
    print("═══ المجتمعُ القابلُ للقياس (دعمٌ أحمر · يوميّ · غيرُ آليّ) ═══")
    print(f"   إجمالًا: {len(gov)} صفًّا من {len({r['symbol'] for r in gov})} رمزًا")
    print(f"   مؤرَّخٌ باسم الملفّ: {len(g_f)} · مؤرَّخٌ بعنوان الدفعة: {len(g_h)} · "
          f"مُشتقٌّ: {len(g_i)} {dict(g_by)} · "
          f"بلا تاريخ: {len(gov)-len(g_f)-len(g_h)-len(g_i)}")
    print("   ⚠️ تاريخُ العنوان = تاريخُ استلام الدفعة لا تاريخُ الشارت (أضعف).")
    print("   ⚠️ والمُشتقُّ **مُشتقٌّ لا مسجَّل** — وسمُ كلّ طريقةٍ مستقلٌّ عمدًا "
          "وتُعيد أداتُها اشتقاقَه بنطاق `recheck`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
