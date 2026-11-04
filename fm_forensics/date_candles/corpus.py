#!/usr/bin/env python3
"""🕯️📅 `T-DATE-CANDLES` — الملحق 2: مجتمعُ المدوّنة كلِّها وبطاقاتُها الآليّة (قراءةٌ فقط · بلا شبكة).

`T_DATE_CANDLES_ADDENDUM_2.md` §②-§③ (مدموجٌ قبل أيّ رقم):
- **المجتمع:** كلُّ صورةٍ في `faisal_images/` لها سجلُّ عين **برمزٍ واحد** (`tk`) وفريمٍ واحدٍ مدعوم (الجرد `TIMEFRAME` · وإن غاب
  فمفرداتُ الفريم في نصّ سجلّ العين `seen`) ⟵ صورةٌ واحدةٌ لكلّ عنقودٍ مكرَّر (الأعلى دقّةً) · والمستبعَدُ بعدده وسببه.
- **البطاقة:** `auto_card.build_card` لكلّ صورة في المجتمع ⟵ `data/cards.jsonl` (الناجحةُ والفاشلةُ بسببها) — **بلا تاريخ**.
- **الفحصُ الجانبيّ:** صورُ المجتمع ذاتُ التاريخ المعروف (مرساةُ رقمٍ في الخريطة · أو تاريخٌ تقويميٌّ في سجلّ العين) تُوسَم
  `known` ⟵ تُطابَق بالطريقة نفسِها وتُطبع إصابتُها **ولا تُحكم**.

الأوضاع: `build` يبني البطاقات (يكتب `data/cards.jsonl` و`data/population2.json`) · `--check` يعيد البناءَ ويقارن بايتًا (خروج 1 عند الاختلاف) ·
`count` يطبع المجتمعَ والمستبعَد بلا بطاقات.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import population as POP1  # noqa: E402  (بُنيت للملحق 1: المرساةُ الرقميّة والتاريخُ التقويميّ)

CARDS = os.path.join(HERE, "data", "cards.jsonl")
POP_OUT = os.path.join(HERE, "data", "population2.json")
TF_MAP = {"D": "1D", "W": "1W", "4H": "4H", "2H": "2H", "1H": "1H", "30m": "30m"}
DUP_REL = ("EXACT", "NEAR", "RESIZE", "CROP")
# مفرداتُ الفريم في نصّ سجلّ العين — للصور التي لا صفَّ لها في الجرد أو صفُّها بلا فريم (مكتوبةٌ قبل أيّ عدّ)
FRAME_WORDS = {
    "1D": r"يوميّ|يومي|اليوميّ|اليومي|\b1D\b|daily",
    "1W": r"أسبوعيّ|أسبوعي|الأسبوعيّ|الأسبوعي|\b1W\b|weekly",
    "4H": r"4\s*ساعات|\b4\s*س\b|أربع ساعات|\b4H\b|4 hours",
    "2H": r"ساعتين|\b2H\b|2 hours",
    "1H": r"(?:على|شارت|فريم)\s+(?:ال)?ساعة|\b1H\b|1 hour",
    "30m": r"30\s*دقيقة|\b30\s*د\b|\b30m\b|30 mins",
}
UNSUPPORTED_WORDS = r"\b5\s*دقائق|\b15\s*دقيقة|\b[15]m\b|دقيقة واحدة|تيك|\btick\b"


def _rank(fid: str):
    p = fid.split("_")
    return (p[0], int(re.sub(r"\D", "", (p + [""])[1]) or 0), fid)


def frame_of(rec: dict, inv_row: dict) -> tuple:
    """(الفريم أو None، السبب) — الجردُ أوّلًا (قيمةٌ واحدةٌ مدعومة) ثمّ مفرداتُ النصّ (فريمٌ واحدٌ ولا مفردةَ غيرُ مدعومة)."""
    tf = (inv_row or {}).get("TIMEFRAME") or []
    if len(tf) == 1:
        return (TF_MAP[tf[0]], "") if tf[0] in TF_MAP else (None, f"فريمٌ غيرُ مدعوم ({tf[0]})")
    if len(tf) > 1:
        return None, "فريماتٌ متعدّدة في الصورة"
    txt = rec.get("seen") or ""
    hits = [k for k, rx in FRAME_WORDS.items() if re.search(rx, txt)]
    if re.search(UNSUPPORTED_WORDS, txt):
        return None, "فريمٌ غيرُ مدعوم (دقائقُ قصيرة أو تيك)"
    if len(hits) == 1:
        return hits[0], ""
    return None, ("فريماتٌ متعدّدة في الصورة" if hits else "لا فريمَ مقروء (ليست شارتَ أسعارٍ أو فريمٌ لم يُكتب)")


def population(recs: dict, inv: dict, disk: dict, known: dict) -> dict:
    """نقيّة: سجلّاتُ العين ‏+ الجرد ‏+ القرص {معرّف: (عرض، ارتفاع)} ‏+ المعروفُ تاريخُه {معرّف: {truth…}} ⟵
    {"members": […], "excluded": [{file, why}], "disk": عددُ الصور}."""
    members, ex = [], []
    by_cluster = collections.defaultdict(list)
    for fid in sorted(disk, key=_rank):
        rec = recs.get(fid)
        if rec is None:
            ex.append({"file": fid, "why": "بلا سجلّ عين"})
            continue
        tk = rec.get("tk") or []
        itk = (inv.get(fid) or {}).get("TICKER") or []
        if len(tk) != 1:
            ex.append({"file": fid, "why": "بلا رمزٍ واحد" if not tk else "أكثرُ من رمز"})
            continue
        if len(itk) == 1 and itk != tk:
            ex.append({"file": fid, "why": "رمزٌ متعارض بين سجلّ العين والجرد"})
            continue
        fr, why = frame_of(rec, inv.get(fid))
        if fr is None:
            ex.append({"file": fid, "why": why})
            continue
        ds = (inv.get(fid) or {}).get("DUPLICATE_STATUS") or {}
        root = ds.get("of") if ds.get("relation") in DUP_REL and ds.get("of") else fid
        by_cluster[root].append({"file": fid, "symbol": tk[0].upper(), "frame": fr, "px": disk[fid][0] * disk[fid][1]})
    for root, grp in sorted(by_cluster.items(), key=lambda kv: _rank(kv[0])):
        grp = sorted(grp, key=lambda g: (-g["px"], _rank(g["file"])))
        keep = grp[0]
        for g in grp[1:]:
            ex.append({"file": g["file"], "why": f"نسخةٌ في عنقود {root} (حُفظت {keep['file']})"})
        row = {"file": keep["file"], "symbol": keep["symbol"], "frame": keep["frame"], "cluster": root,
               "members": [g["file"] for g in grp]}
        k = next((known[g["file"]] for g in grp if g["file"] in known), None)
        if k:
            row["known"] = k
        members.append(row)
    return {"members": members, "excluded": ex, "disk": len(disk)}


def known_dates(recs: dict, inv: dict, disk: set) -> dict:
    """المعروفُ تاريخُه للفحص الجانبيّ: (A) مرساةُ الرقم في الملحق 1 ثمّ (C) التاريخُ التقويميُّ في سجلّ العين (EXACT · DAY)."""
    units, derived, mapping, _r, _i, _d = POP1.load()
    P = POP1.population(units, derived, mapping, recs, inv, disk)
    out = {}
    for r in P["A"]:
        out[r["file"]] = {"truth": r["truth"], "src": r["truth_src"]}
    for fid, x in recs.items():
        if fid in out or fid not in disk or x.get("dprec") not in POP1.DATE_PRECS:
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?$", str(x.get("date", "")).strip())
        if m:
            out[fid] = {"truth": m.group(1), "time": m.group(2) or "", "src": f"eye:{x['dprec']}"}
    return out


def load():
    recs = {}
    for ln in open(os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl"), encoding="utf-8"):
        if ln.strip():
            x = json.loads(ln)
            recs[x["id"]] = x
    inv = {r["IMAGE_ID"]: r for r in json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit",
                                                                    "MASTER_CORPUS_INVENTORY.json"), encoding="utf-8"))["rows"]}
    from PIL import Image                                          # noqa: PLC0415
    disk = {}
    d = os.path.join(ROOT, "faisal_images")
    for f in os.listdir(d):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            with Image.open(os.path.join(d, f)) as im:
                disk[os.path.splitext(f)[0]] = im.size
    return recs, inv, disk


def _ext(d: str, fid: str) -> str:
    for e in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
        if os.path.exists(os.path.join(d, fid + e)):
            return os.path.join(d, fid + e)
    raise FileNotFoundError(fid)


def build(recs, inv, disk) -> tuple:
    import auto_card as AC                                         # noqa: PLC0415
    import chart_pixels as P                                       # noqa: PLC0415
    known = known_dates(recs, inv, set(disk))
    pop = population(recs, inv, disk, known)
    lines = []
    for m in pop["members"]:
        card = AC.build_card(P.load_rgb(_ext(os.path.join(ROOT, "faisal_images"), m["file"])), recs[m["file"]]["seen"])
        card.update({"id": m["file"], "symbol": m["symbol"], "frame": m["frame"]})
        lines.append(json.dumps(card, ensure_ascii=False, sort_keys=True))
    return pop, lines


def summary(pop: dict, cards: list = None) -> list:
    out = [f"🖼️ صورُ القرص {pop['disk']} ⟵ المجتمع {len(pop['members'])} (منها معروفُ التاريخ للفحص الجانبيّ "
           f"{sum(1 for m in pop['members'] if m.get('known'))})"]
    why = collections.Counter(re.sub(r" \(حُفظت.*| في عنقود.*", "", e["why"]) for e in pop["excluded"])
    out.append("🚫 المستبعَد قبل البطاقة: " + " · ".join(f"{k} {v}" for k, v in why.most_common()))
    fr = collections.Counter(m["frame"] for m in pop["members"])
    out.append("🕯️ الفريمات: " + " · ".join(f"{k} {v}" for k, v in fr.most_common()))
    if cards is not None:
        ok = [c for c in cards if c.get("ok")]
        out.append(f"🃏 البطاقات: نجحت {len(ok)} من {len(cards)} ({len(ok) / max(1, len(cards)):.1%})")
        cw = collections.Counter(re.sub(r"\d+(?:\.\d+)?%?", "N", c.get("why", "")) for c in cards if not c.get("ok"))
        out.append("   أسبابُ الفشل: " + " · ".join(f"{k} {v}" for k, v in cw.most_common()))
    return out


def main(argv) -> int:
    mode = argv[1] if len(argv) > 1 else "count"
    recs, inv, disk = load()
    if mode == "count":
        pop = population(recs, inv, disk, known_dates(recs, inv, set(disk)))
        print("\n".join(summary(pop)))
        return 0
    pop, lines = build(recs, inv, disk)
    body = "\n".join(lines) + "\n"
    popj = json.dumps(pop, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if mode == "--check":
        same = open(CARDS, encoding="utf-8").read() == body and open(POP_OUT, encoding="utf-8").read() == popj
        print("✅ البطاقاتُ والمجتمعُ مطابقان بايتًا" if same else "❌ إعادةُ البناء تختلف عن الملفّ المدفوع")
        return 0 if same else 1
    os.makedirs(os.path.dirname(CARDS), exist_ok=True)
    open(CARDS, "w", encoding="utf-8").write(body)
    open(POP_OUT, "w", encoding="utf-8").write(popj)
    print("\n".join(summary(pop, [json.loads(x) for x in lines])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
