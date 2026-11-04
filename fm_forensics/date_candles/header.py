#!/usr/bin/env python3
"""🕯️📅④ `T-DATE-CANDLES` الملحق 4 — «التاريخ من رأس الشارت» ‏+ شرطُ الوصول (قراءةٌ فقط · بلا شبكة).

`T_DATE_CANDLES_ADDENDUM_4.md` (مدموجٌ قبل أيّ رقم): لكلّ صورةٍ في `faisal_images/` — الطابعُ المطبوع من نصّ سجلّ العين وإلّا من القراءة
الآليّة (`data/header_ocr.jsonl` · أسطرُ `DHO` من `date_header.yml`) ⟵ الصيغُ `H1` · `H2` · `H3` · `X1` · `A1` (§④) ⟵ السنةُ بالوصول
(وبالشموع إن وُجدت) ⟵ شرطُ الوصول (§③) ⟵ الثقة (§⑤) ⟵ `data/header_dates.tsv` · والمقارنةُ بالـ20 من الشموع والعدّ (§⑥).
الأوضاع: `build` · `--check` (يعيد الجدولَ بايتًا) · `arrival` · والملحق 5: `levels` (الكتابةُ في جدول المستويات بوسم `stamp`) ·
`levels-check` · 🔒 والمحورُ مُغلَقٌ مُنفَّذًا (`closed.py`): كلُّ وضعٍ غيرِ `--check`/`levels-check` يخرج 8 بلا `DATE_CANDLES_REOPEN=1`.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
DATA = os.path.join(HERE, "data")
OCR = os.path.join(DATA, "header_ocr.jsonl")
ARRIVAL = os.path.join(DATA, "arrival.tsv")
TABLE = os.path.join(DATA, "header_dates.tsv")
CANDLES3 = os.path.join(DATA, "candles_table_v3.tsv")
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
FROZEN_REC_LINES = 913   # سجلُّ العين يومَ البناء (2026-11-04 · بعد سجلّات B46) — إلحاقيٌّ فالأوّلُ ثابت
CONSIST_DAYS = 7          # §④/§⑥: الطابعُ يومَ آخر الشمعة أو بعده بما لا يتجاوز 7 أيّام
RANK = {"H3": 0, "H1": 1, "H2": 2, "X1": 3, "A1": 4}
FULL = ("H1", "H2", "H3")
TZ = r"(EDT|EST|ET)\b"
RX = {
    "H3a": re.compile(r"(20\d\d)-(\d\d)-(\d\d)[ T](\d{1,2}):(\d\d)(?::\d\d)?\s*(AM|PM)?\s*" + TZ),
    "H3b": re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(20\d\d)\s+(\d{1,2}):(\d\d)(?::\d\d)?\s*(AM|PM)?\s*" + TZ),
    "H1": re.compile(r"(?<![\d/:])(\d{1,2})/(\d{1,2})(?:-|\s+)(\d{1,2}):(\d\d)(?::\d\d)?\s*" + TZ),
    "H2": re.compile(r"(?<![\d/:])(\d{1,2}):(\d\d)\s+(\d{1,2})/(\d{1,2})\s*" + TZ),
    "X1e": re.compile(r"مؤشّ?رٍ?[^·]{0,12}?على\s+(\d{1,2})/(\d{1,2})/(20\d\d)"),
    "X1o": re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(20\d\d)(?![\d:])(?=[^\n]*\b[OHLC]\s*[:=]?\s*\d)"),
}
OTHER_TZ = re.compile(r"\d{1,2}[:/]\d{1,2}[^·\n]{0,12}\b(EEST|EET|CEST|CET|GMT|BST|AST|PST|PDT|CST|CDT|MST|MDT)\b")
AXIS_EYE = re.compile(r"المحور[ًٌٍَُِّْ]*\s+([^·]{0,40})")
MD = re.compile(r"(?<![\d/:])(\d{1,2})/(\d{1,2})(?![\d/:])")


def _hh(h: int, ap) -> int:
    if ap == "PM" and h < 12:
        return h + 12
    if ap == "AM" and h == 12:
        return 0
    return h


def parse_text(text: str) -> tuple:
    """نصٌّ (سجلُّ العين أو سطرُ قراءةٍ آليّة) ⟵ ([طوابع]، توقيتٌ غيرُ نيويورك؟) — الطابع {code, y|None, m, d, hh|None, mi|None, raw}."""
    out = []
    t = text or ""
    for m in RX["H3a"].finditer(t):
        out.append({"code": "H3", "y": int(m.group(1)), "m": int(m.group(2)), "d": int(m.group(3)),
                    "hh": _hh(int(m.group(4)), m.group(6)), "mi": int(m.group(5)), "raw": m.group(0)})
    for m in RX["H3b"].finditer(t):
        # الملحق 5 §③: `DD/MM/YYYY` صيغةُ تطبيق فيصل · والحقلُ الثاني فوق 12 لا يكون شهرًا ⟵ `MM/DD/YYYY` كما كانت
        _a, _b = int(m.group(1)), int(m.group(2))
        _mo, _dd = (_a, _b) if _b > 12 else (_b, _a)
        out.append({"code": "H3", "y": int(m.group(3)), "m": _mo, "d": _dd,
                    "hh": _hh(int(m.group(4)), m.group(6)), "mi": int(m.group(5)), "raw": m.group(0)})
    taken = [m.span() for m in RX["H3a"].finditer(t)] + [m.span() for m in RX["H3b"].finditer(t)]
    free = lambda sp: not any(a < sp[1] and sp[0] < b for a, b in taken)   # noqa: E731
    for m in RX["H1"].finditer(t):
        if free(m.span()):
            out.append({"code": "H1", "y": None, "m": int(m.group(2)), "d": int(m.group(1)),
                        "hh": int(m.group(3)), "mi": int(m.group(4)), "raw": m.group(0)})
    for m in RX["H2"].finditer(t):
        if free(m.span()):
            out.append({"code": "H2", "y": None, "m": int(m.group(3)), "d": int(m.group(4)),
                        "hh": int(m.group(1)), "mi": int(m.group(2)), "raw": m.group(0)})
    for key in ("X1e", "X1o"):
        for m in RX[key].finditer(t):
            out.append({"code": "X1", "y": int(m.group(3)), "m": int(m.group(1)), "d": int(m.group(2)),
                        "hh": None, "mi": None, "raw": m.group(0)})
    for m in AXIS_EYE.finditer(t):
        mds = MD.findall(m.group(1))
        if mds:
            a, b = int(mds[-1][0]), int(mds[-1][1])
            mo, dd = (b, a) if a > 12 else (a, b)
            out.append({"code": "A1", "y": None, "m": mo, "d": dd, "hh": None, "mi": None, "raw": m.group(0)[:40]})
    ok, seen = [], set()
    for s in out:
        k = (s["code"], s["y"], s["m"], s["d"], s["hh"], s["mi"])
        if k in seen or not (1 <= s["m"] <= 12 and 1 <= s["d"] <= 31 and (s["hh"] is None or 0 <= s["hh"] <= 23)):
            continue
        seen.add(k)
        ok.append(s)
    return ok, bool(OTHER_TZ.search(t))


def parse_ocr(row: dict) -> tuple:
    """أسطرُ القراءة الآليّة ⟵ ([طوابع]، توقيتٌ آخر؟) — كـ`parse_text` على كلّ سطر · والمحورُ = السطرُ الذي فيه عنوانان `MM/DD` فأكثر
    (أكثرُها عناوين · ثمّ الأدنى) ⟵ الأيمنُ فيه."""
    out, other = [], False
    best_axis = None
    for txt, x0, y0, x1, y1, _c in row.get("lines") or []:
        st, ot = parse_text(txt)
        out += [s for s in st if s["code"] != "A1"]
        other = other or ot
        toks = [t for t in txt.split() if re.fullmatch(r"\d{2}/\d{2}", t)]
        if len(toks) >= 2 and not any(s["code"] in FULL for s in st):
            key = (len(toks), y0)
            if best_axis is None or key > best_axis[0]:
                best_axis = (key, toks[-1], txt)
    if best_axis:
        a, b = (int(v) for v in best_axis[1].split("/"))
        mo, dd = (b, a) if a > 12 else (a, b)
        if 1 <= mo <= 12 and 1 <= dd <= 31:
            out.append({"code": "A1", "y": None, "m": mo, "d": dd, "hh": None, "mi": None, "raw": best_axis[2][:40]})
    return out, other


def _dt(s: dict, y: int):
    try:
        if s["hh"] is None:
            return dt.datetime(y, s["m"], s["d"], 0, 0, tzinfo=NY), True
        return dt.datetime(y, s["m"], s["d"], s["hh"], s["mi"] or 0, tzinfo=NY), False
    except ValueError:
        return None, False


def resolve(s: dict, arrival: dt.datetime, candle_day: str = "", use_candle: bool = True):
    """§④: السنة (أكبرُ سنةٍ لا يتجاوز فيها الطابعُ الوصول · ومتّسقةٌ مع الشموع إن طُلب ووُجد) ⟵ (datetime، السبب) — والسببُ فارغٌ عند القبول."""
    years = [s["y"]] if s["y"] else [arrival.year, arrival.year - 1, arrival.year - 2]
    any_ok = None
    for y in years:
        d, day_only = _dt(s, y)
        if d is None:
            continue
        late = d.date() > arrival.date() if day_only else d > arrival
        if late:
            continue
        if any_ok is None:
            any_ok = d
        if use_candle and candle_day and s["code"] in ("H1", "H2", "H3", "A1"):
            cd = dt.date.fromisoformat(candle_day[:10])
            if not (cd <= d.date() <= cd + dt.timedelta(days=CONSIST_DAYS)):
                continue
        return d, ""
    if any_ok is None:
        return None, "بعد الوصول"
    return None, "يخالف الشموع"


def judge(stamps: list, arrival, candle_day: str = "", use_candle: bool = True) -> dict:
    """§④-§⑤: الأعلى رتبةً ثمّ الأحدثُ المقبول ⟵ {date, hour, code, conf, why, raw}."""
    if arrival is None:
        return {"conf": "لا", "why": "بلا تاريخ وصول"}
    if not stamps:
        return {"conf": "لا", "why": "بلا طابع"}
    best, why_last = None, ""
    for code in sorted({s["code"] for s in stamps}, key=lambda c: RANK[c]):
        acc = []
        for s in [x for x in stamps if x["code"] == code]:
            d, why = resolve(s, arrival, candle_day, use_candle)
            if d is not None:
                acc.append((d, s))
            else:
                why_last = why_last or why
        if acc:
            best = max(acc, key=lambda t: t[0])
            break
    if best is None:
        return {"conf": "لا", "why": why_last or "قراءةٌ غيرُ صالحة"}
    d, s = best
    conf = "واثق" if s["code"] in FULL else "مرجّح"
    return {"date": d.strftime("%Y-%m-%d"), "hour": "" if s["hh"] is None else d.strftime("%H:%M"), "code": s["code"],
            "conf": conf, "why": "", "raw": s["raw"]}


# ── البيانات ─────────────────────────────────────────────────────────────────────────────────────────────
def arrivals(files: list) -> dict:
    """§③: الوصول = أبكرُ (أوّلُ commit أضاف الملفّ — والنقلُ إلى المجلّد إضافةٌ (`--no-renames`) · تاريخُ الرسالة · collected_utc) بتوقيت نيويورك ⟵ {معرّف: datetime}."""
    first = {}
    out = subprocess.run(["git", "log", "--no-renames", "--diff-filter=A", "--format=@@%cI", "--name-only", "--", "faisal_images"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    cur = None
    for ln in out.splitlines():
        if ln.startswith("@@"):
            cur = dt.datetime.fromisoformat(ln[2:])
        elif ln.strip() and cur is not None:
            iid = os.path.splitext(os.path.basename(ln.strip()))[0]
            first[iid] = cur if iid not in first else min(first[iid], cur)
    meta = os.path.join(ROOT, "telegram_collect_meta.jsonl")
    if os.path.exists(meta):
        for ln in open(meta, encoding="utf-8"):
            try:
                x = json.loads(ln)
            except ValueError:
                continue
            nm = x.get("saved_name")
            if not nm:
                continue
            iid = os.path.splitext(nm)[0]
            for k in ("date", "collected_utc"):
                v = x.get(k)
                if v:
                    t = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
                    first[iid] = t if iid not in first else min(first[iid], t)
    return {i: first[i].astimezone(NY) for i in files if i in first}


def load(frozen: bool = True):
    """`frozen`: المجتمعُ صفوفُ `arrival.tsv` (الـ891 يومَ البناء) وسجلُّ العين أوّلُ `FROZEN_REC_LINES` سطرًا (إلحاقيٌّ) ⟵ `--check` لا يتغيّر
    بصورةٍ تصل بعد البناء · ووضعُ `arrival` يقرأ القرص."""
    recs = {}
    with open(os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl"), encoding="utf-8") as fh:
        for i, ln in enumerate(fh):
            if frozen and i >= FROZEN_REC_LINES:
                break
            if ln.strip():
                x = json.loads(ln)
                recs[x["id"]] = x
    files = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "faisal_images"))
                   if f.lower().endswith((".jpg", ".jpeg", ".png")))
    ocr = {}
    if os.path.exists(OCR):
        for ln in open(OCR, encoding="utf-8"):
            if ln.strip():
                x = json.loads(ln)
                ocr[x["id"]] = x
    candles = {}
    if os.path.exists(CANDLES3):
        for r in csv.DictReader(open(CANDLES3, encoding="utf-8"), delimiter="\t"):
            if r["label"] == "واثق":
                candles[r["file"]] = r["last_bar"]
    arr = {}
    if os.path.exists(ARRIVAL):
        for r in csv.DictReader(open(ARRIVAL, encoding="utf-8"), delimiter="\t"):
            arr[r["file"]] = dt.datetime.fromisoformat(r["arrival_ny"])
    if frozen and arr:
        files = sorted(arr)
    return recs, files, ocr, candles, arr


COLS = ["file", "symbol", "arrival_ny", "source", "code", "date", "hour", "conf", "why", "raw", "eye_codes", "ocr_codes",
        "candle_last", "candle_arrival_ok", "pure_date", "pure_conf", "recorded_date"]


def build_rows(recs, files, ocr, candles, arr) -> list:
    rows = []
    for f in files:
        r = recs.get(f) or {}
        txt = " · ".join(str(r.get(k) or "") for k in ("seen", "q", "note"))
        eye, eye_other = parse_text(txt)
        oc, oc_other = parse_ocr(ocr.get(f) or {})
        a = arr.get(f)
        cday = candles.get(f, "")
        src, st = ("eye", eye) if eye else (("ocr", oc) if oc else ("", []))
        j = judge(st, a, cday)
        if j["conf"] == "لا" and j["why"] == "بلا طابع" and (eye_other or oc_other):
            j["why"] = "توقيتٌ غيرُ نيويورك"
        pure = judge(st, a, "", use_candle=False)
        c_ok = "" if not cday else ("0" if a is not None and dt.date.fromisoformat(cday[:10]) > a.date() else "1")
        rd = r.get("date", "") if r.get("dprec") in ("EXACT", "DAY") else ""
        rows.append({"file": f, "symbol": ",".join(r.get("tk") or []), "arrival_ny": a.isoformat() if a else "",
                     "source": src if st else "", "code": j.get("code", ""), "date": j.get("date", ""), "hour": j.get("hour", ""),
                     "conf": j["conf"], "why": j["why"], "raw": (j.get("raw") or "").replace("\t", " "),
                     "eye_codes": ",".join(sorted({s["code"] for s in eye})), "ocr_codes": ",".join(sorted({s["code"] for s in oc})),
                     "candle_last": cday, "candle_arrival_ok": c_ok, "pure_date": pure.get("date", ""), "pure_conf": pure["conf"],
                     "recorded_date": rd})
    return rows


def _tsv(rows, cols) -> str:
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, delimiter="\t", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    return b.getvalue()


def ocr_agreement(recs, files, ocr) -> tuple:
    """§⑦ `P28`: حيث يحمل سجلُّ العين والقراءةُ الآليّة طابعًا كاملًا — توافقُ (اليوم، الشهر) لأيٍّ منهما ⟵ (يتّفق، الكلّ)."""
    agree = tot = 0
    for f in files:
        r = recs.get(f) or {}
        eye, _ = parse_text(" · ".join(str(r.get(k) or "") for k in ("seen", "q", "note")))
        oc, _ = parse_ocr(ocr.get(f) or {})
        e = {(s["d"], s["m"]) for s in eye if s["code"] in FULL}
        o = {(s["d"], s["m"]) for s in oc if s["code"] in FULL}
        if e and o:
            tot += 1
            agree += bool(e & o)
    return agree, tot


# ── العدّ ④ (§⑥) ─────────────────────────────────────────────────────────────────────────────────────────
def before_move(rows: list) -> dict:
    """«قبل الحركة» بـ`gt_audit` بالاسم: كلُّ بيانٍ وحدتُه صورةٌ لها طابعٌ «واثق» وطابعُه الأصليّ غيرُ مؤكَّد (خارج `OK`) يأخذ الطابعَ
    (يومُ القرار بقاعدة `stage_ledger`: قبل 16:00 نيويورك ⟵ جلسةُ اليوم · بعدها ⟵ التالية) ⟵ `classify` كما هو ⟵ {قبل، بعد، المتغيّر}."""
    sys.path.insert(0, os.path.join(ROOT, "faisal_engine"))
    import gt_audit as GA                                          # noqa: PLC0415
    import stage_ledger as SL                                      # noqa: PLC0415
    eps0, _u, _s, evid = GA.run()
    base = sorted(e["episode_id"] for e in eps0 if e["reliable_pre_move"])
    hdr = {r["file"]: r for r in rows if r["conf"] == "واثق" and r["hour"]}
    cases, _units = GA.load_rank()
    case_ix = {c["episode_id"]: c for c in cases}
    docs = GA.method_hits()
    changed, after = [], []
    for ep in evid["episodes"]:
        ep2 = json.loads(json.dumps(ep))
        touched = []
        for s in ep2["statements"]:
            img = (s.get("unit") or s["ref"].split(":")[0])
            h = hdr.get(img)
            if h and s.get("ts") not in GA.OK:
                hh, mi = (int(x) for x in h["hour"].split(":"))
                day = h["date"]
                first = SL.session_on_or_after(day)
                a = SL.next_session(day) if (first == day and hh * 60 + mi >= 16 * 60) else first
                s["ts"], s["asof"] = "STRONGLY_SUPPORTED", [a, a]
                touched.append((img, s["ref"], h["date"], h["hour"], a))
        row = GA.classify(ep2, case_ix[ep2["episode_id"]], docs)
        if row["reliable_pre_move"]:
            after.append(ep2["episode_id"])
        if touched:
            changed.append({"episode": ep2["episode_id"], "touched": touched, "relation": row["relation"],
                            "reliable_pre_move": row["reliable_pre_move"], "blockers": row.get("blockers", "")})
    return {"before": base, "after": sorted(after), "changed": changed}


def fsweep(rows: list) -> list:
    """`T-FSWEEP` (الملحق 2 §⑥-2 بحرفه): صورُ `SWEEP` بلا تاريخ منشورٍ مقبول ⟵ «واثق» بالطابع وتاريخُه D و`collected_utc − D` سبعةُ أيّامٍ
    أو أقلّ ⟵ «مؤهَّلٌ بملحق» — عدٌّ بلا كتابة."""
    import results as RS                                           # noqa: PLC0415
    last = {}
    for x in RS._jsonl(RS.FSWEEP_LEDGER):
        if x.get("image"):
            last[os.path.splitext(x["image"])[0]] = x
    by = {r["file"]: r for r in rows}
    out = []
    for k, v in sorted(last.items()):
        if v.get("decision") != "SWEEP" or v.get("date_source") in RS.FSWEEP_OK_SRC:
            continue
        r = by.get(k) or {}
        ok = False
        if r.get("conf") == "واثق" and v.get("collected_utc"):
            ok = (dt.date.fromisoformat(v["collected_utc"][:10]) - dt.date.fromisoformat(r["date"])).days <= 7
        out.append({"symbol": v.get("symbol"), "image": k, "conf": r.get("conf", "—"), "date": r.get("date", ""), "eligible": ok})
    return out

def known_truths(recs: dict, files: list) -> dict:
    """§⑥ الدقّة: المعروفُ تاريخُه بتعريف الملحق 2 §⑤ (`corpus.known_dates`: مرساةُ الرقم ثمّ EXACT/DAY في سجلّ العين) على صور القرص كلّها."""
    import corpus as CP                                            # noqa: PLC0415
    inv = {r["IMAGE_ID"]: r for r in json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit",
                                                               "MASTER_CORPUS_INVENTORY.json"), encoding="utf-8"))["rows"]}
    return {k: v["truth"] for k, v in CP.known_dates(recs, inv, set(files)).items()}


def hits_known(d: str, truth: str) -> bool:
    """§⑥: الطابعُ لا يتجاوز التاريخَ المعروف ولا يسبقه بأكثر من 7 أيّام."""
    a, b = dt.date.fromisoformat(d), dt.date.fromisoformat(truth[:10])
    return b - dt.timedelta(days=CONSIST_DAYS) <= a <= b


def summary(rows: list, recs, files, ocr) -> list:
    L = []
    c = collections.Counter(r["conf"] for r in rows)
    L.append(f"🧮 الصور {len(rows)} · واثق {c['واثق']} · مرجّح {c['مرجّح']} · لا {c['لا']}")
    for conf in ("واثق", "مرجّح"):
        g = [r for r in rows if r["conf"] == conf]
        L.append(f"   {conf}: " + " · ".join(f"{k} {v}" for k, v in collections.Counter((r['code'], r['source']) for r in g).most_common())
                 + f" · بلا تاريخٍ مسجَّلٍ قبلها {sum(1 for r in g if not r['recorded_date'])}")
    L.append("   «لا»: " + " · ".join(f"{k} {v}" for k, v in collections.Counter(r['why'] for r in rows if r['conf'] == 'لا').most_common()))
    a, t = ocr_agreement(recs, files, ocr)
    L.append(f"🔤 القراءةُ الآليّة توافق سجلَّ العين (يوم·شهر) في {a} من {t}" + (f" ({a / t:.0%})" if t else ""))
    L.append(f"🔤 صورٌ قُرئت آليًّا {sum(1 for f in files if f in ocr and not ocr[f].get('error'))} من {len(files)}")
    cand = [r for r in rows if r["candle_last"]]
    L.append(f"🕯️ الـ{len(cand)} بالشموع (قبل قيد الاتّساق): ")
    agree = dis = none = 0
    for r in sorted(cand, key=lambda r: r["file"]):
        cd = dt.date.fromisoformat(r["candle_last"][:10])
        if r["pure_date"]:
            pd = dt.date.fromisoformat(r["pure_date"])
            ok = cd <= pd <= cd + dt.timedelta(days=CONSIST_DAYS)
            agree += ok
            dis += not ok
            tag = "اتّفاق" if ok else "اختلاف"
        else:
            none += 1
            tag = "بلا طابع"
        L.append(f"   {r['file']} {r['symbol']} شموع {r['candle_last']} · طابع {r['pure_date'] or '—'} ({r['pure_conf']}) · {tag}"
                 f" · الوصول {'✅' if r['candle_arrival_ok'] == '1' else '❌ بعده'}")
    L.append(f"   ⟵ اتّفاق {agree} · اختلاف {dis} · بلا طابع {none} · شموعٌ بعد الوصول {sum(1 for r in cand if r['candle_arrival_ok'] == '0')}")
    kt = known_truths(recs, files)
    for conf in ("واثق", "مرجّح"):
        g = [r for r in rows if r["conf"] == conf and r["file"] in kt]
        h = sum(1 for r in g if hits_known(r["date"], kt[r["file"]]))
        L.append(f"🎯 الدقّةُ على المعروف تاريخُه «{conf}»: يصيب {h} من {len(g)}" + (f" ({h / len(g):.0%})" if g else ""))
        by = collections.defaultdict(lambda: [0, 0])
        for r in g:
            by[r["code"]][0] += hits_known(r["date"], kt[r["file"]])
            by[r["code"]][1] += 1
        if by:
            L.append("   " + " · ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(by.items())))
    bm = before_move(rows)
    L.append(f"⏳ «قبل الحركة»: قبل {len(bm['before'])} {bm['before']} ⟵ بعد {len(bm['after'])} {bm['after']}")
    for x in bm["changed"]:
        L.append(f"   {x['episode']}: {x['touched']} ⟵ {x['relation']} · موثوقٌ قبل الحركة {x['reliable_pre_move']} {x['blockers']}")
    fs = fsweep(rows)
    L.append(f"🧹 T-FSWEEP: سحوبٌ بلا تاريخٍ مقبول {len(fs)} ⟵ «مؤهَّلٌ بملحق» {sum(x['eligible'] for x in fs)} · "
             + " · ".join(f"{x['symbol']} {x['image']} ({x['conf']} {x['date']})" for x in fs))
    return L


# ── الملحق 5 §④: «واثق» الطابع ⟵ الوحداتُ غيرُ المؤرَّخة في جدول المستويات بوسم `stamp` (بلا دهس) ─────────────────────────────
#    ⚖️ النتيجة (`T_DATE_CANDLES_ADDENDUM_5_RESULT.md`): صفرُ وحدة — الـ55 كلُّها بلا وحدةٍ في الجدول ⟵ لا كتابة · و`stamp` لم يُضف
#    إلى `DERIVED_METHODS` ولا إلى `LVT2`/`LVD*` (صفرُ صفّ) · و`levels-check` يُثبت الصفرَ بايتًا.
RUN_ID = "41894850770"                     # التشغيلةُ الموثّقة (القراءةُ الآليّة للملحق 4 · `LVD2`)
LEVELS = os.path.join(ROOT, "faisal_levels_table.tsv")
SIDE = os.path.join(ROOT, "faisal_derived_dates.tsv")
METHOD = "stamp"
FP_RE = re.compile(r"^stamp:(H1|H2|H3) src:(eye|ocr) at:(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) raw:(.+)$")


def session_of(day: str) -> str:
    """§④: يومُ الطابع إن كان جلسةً (يومُ عملٍ ∧ `market_calendar.is_trading_day` — الدالّةُ لا تفحص نهايةَ الأسبوع) وإلّا آخرُ جلسةٍ قبله."""
    import market_calendar as MC                                   # noqa: PLC0415
    d = dt.date.fromisoformat(day)
    for _ in range(15):
        if d.weekday() < 5 and MC.is_trading_day(d.isoformat()):
            return d.isoformat()
        d -= dt.timedelta(days=1)
    return ""


def stamp_fingerprint(r: dict) -> str:
    """البصمة: قراءةٌ تُعرَب (`LVD5`) — الرمزُ والمصدرُ ولحظةُ الطابع ونصُّه الخامّ · بلا رقم صورة."""
    return f"stamp:{r['code']} src:{r['source']} at:{r['date']} {r['hour']} raw:{r['raw']}"


def parse_stamp_fingerprint(fp: str):
    """البصمة ⟵ {code, source, date, hour, raw} أو None — والذهابُ والإيابُ يعيدها كما هي."""
    m = FP_RE.match(fp or "")
    if not m:
        return None
    return {"code": m.group(1), "source": m.group(2), "date": m.group(3), "hour": m.group(4), "raw": m.group(5)}


def _sessions_apart(a: str, b: str) -> int:
    lo, hi = sorted((a, b))
    d, n = dt.date.fromisoformat(lo), 0
    while d.isoformat() < hi:
        d += dt.timedelta(days=1)
        if session_of(d.isoformat()) == d.isoformat():
            n += 1
    return n


def mapping_units() -> dict:
    """الصورةُ ⟵ وحداتُ الكاتالوج بخريطة الملحق 1 (ثقةٌ من `f0.MAP_FOUND`) — كطريقة `candles` بالاسم (`results.build`)."""
    import f0                                                      # noqa: PLC0415
    out = collections.defaultdict(list)
    for m in csv.DictReader(open(os.path.join(DATA, "image_map.tsv"), encoding="utf-8"), delimiter="\t"):
        if m["confidence"] in f0.MAP_FOUND and m["disk_file"]:
            for u in [x for x in (m.get("units") or "").split(",") if "|" in x]:
                sym, line = u.split("|", 1)
                out[os.path.splitext(m["disk_file"])[0]].append((sym, line))
    return out


def stamp_derived(rows: list, levels: list, mp: dict) -> tuple:
    """§④ نقيّةً: (صفوفُ الملفّ الجانبيّ، التعارض، الإحصاء). الوحدةُ المؤرَّخةُ بأيّ مصدرٍ غيرِ `stamp` لا تُمسّ ·
    و`stamp` القائمُ يُقرأ فارغًا (فالبناءُ يُعاد بايتًا قبل الكتابة وبعدها)."""
    unit_dates = {}
    for r in levels:
        unit_dates[(r["symbol"], r["line"])] = "" if r["date_source"] == METHOD else r["date"]
    st = collections.Counter()
    by_unit = collections.defaultdict(list)
    for r in rows:
        if r["conf"] != "واثق":
            continue
        st["wathiq"] += 1
        us = [u for u in mp.get(r["file"], []) if u in unit_dates]
        if not us:
            st["no_unit"] += 1
            continue
        free = [u for u in us if not unit_dates[u]]
        if not free:
            st["unit_dated"] += 1
            continue
        st["to_undated"] += 1
        for u in free:
            by_unit[u].append(r)
    der, conflict = [], []
    for u, rs in sorted(by_unit.items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
        days = sorted({session_of(x["date"]) for x in rs})
        if "" in days:
            conflict.append((u, days))
            continue
        if len(days) > 1 and _sessions_apart(days[0], days[-1]) > 1:
            conflict.append((u, days))
            continue
        x = sorted(rs, key=lambda x: (x["date"], x["hour"], x["file"]))[-1]
        der.append({"symbol": u[0], "line": u[1], "date": session_of(x["date"]), "method": METHOD,
                    "fingerprint": stamp_fingerprint(x), "max_diff": "", "witness": "واثق", "run_id": RUN_ID})
    return der, conflict, st


def _levels():
    return list(csv.DictReader(open(LEVELS, encoding="utf-8", newline=""), delimiter="\t"))


def stamp_build():
    recs, files, ocr, candles, arr = load()
    rows = build_rows(recs, files, ocr, candles, arr)
    return stamp_derived(rows, _levels(), mapping_units())


def recheck() -> dict:
    """`LVD1`: إعادةُ اشتقاق بصمات `stamp` **بلا شبكة** من الجدول المجمَّد ⟵ {(رمز، سطر): بصمة}."""
    der, _c, _s = stamp_build()
    return {(d["symbol"], int(d["line"])): d["fingerprint"] for d in der}


def write_levels(der: list) -> tuple:
    """يكتب `stamp` في الملفّ الجانبيّ (يستبدل صفوفَ `stamp` وحدَها) ثمّ يملأ الجدولَ **الفارغَ وحدَه** — بلا إعادة توليده من الكاتالوج."""
    side_rows = list(csv.DictReader(open(SIDE, encoding="utf-8", newline=""), delimiter="\t"))
    cols = list(side_rows[0].keys()) if side_rows else ["symbol", "line", "date", "method", "fingerprint", "max_diff", "witness", "run_id"]
    keep = [r for r in side_rows if r.get("method") != METHOD]
    new = [{k: d.get(k, "") for k in cols} for d in der]
    if [r for r in side_rows if r.get("method") == METHOD] != new:        # لا تغيّر ⟵ لا كتابة (الملفّ بايتًا كما هو)
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=cols, delimiter="\t")         # فاصلُ الأسطر الافتراضيّ \r\n كما كتبه الأصل
        w.writeheader()
        w.writerows(keep + new)
        open(SIDE, "w", encoding="utf-8", newline="").write(b.getvalue())
    tbl = _levels()
    tcols = list(tbl[0].keys())
    dm = {(d["symbol"], d["line"]): d["date"] for d in der}
    n = cleared = 0
    for r in tbl:
        if r["date_source"] == METHOD:
            r["date"], r["date_source"] = "", ""
            cleared += 1
        k = (r["symbol"], r["line"])
        if not r["date"] and k in dm:
            r["date"], r["date_source"] = dm[k], METHOD
            n += 1
    if n or cleared:
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=tcols, delimiter="\t")
        w.writeheader()
        w.writerows(tbl)
        open(LEVELS, "w", encoding="utf-8", newline="").write(b.getvalue())
    return len(der), n


def main(argv) -> int:
    import closed                                                  # noqa: PLC0415  🔒 الملحق 5 §⑤
    _rc = closed.gate("header", argv)
    if _rc is not None:
        return _rc
    mode = argv[1] if len(argv) > 1 else "build"
    recs, files, ocr, candles, arr = load(frozen=(mode != "arrival"))
    if mode == "arrival":
        a = arrivals(files)
        rows = [{"file": f, "arrival_ny": a[f].isoformat()} for f in files if f in a]
        open(ARRIVAL, "w", encoding="utf-8").write(_tsv(rows, ["file", "arrival_ny"]))
        print(f"⏱️ الوصول: {len(rows)} من {len(files)}")
        return 0
    rows = build_rows(recs, files, ocr, candles, arr)
    if mode in ("levels", "levels-check"):
        der, conflict, st = stamp_derived(rows, _levels(), mapping_units())
        if mode == "levels-check":
            side = [r for r in csv.DictReader(open(SIDE, encoding="utf-8", newline=""), delimiter="\t") if r.get("method") == METHOD]
            tbl = {(r["symbol"], r["line"]): r["date"] for r in _levels() if r["date_source"] == METHOD}
            same = ([{k: r[k] for k in der[0]} for r in side] == der if der else not side) and \
                tbl == {(d["symbol"], d["line"]): d["date"] for d in der}
            print("✅ تواريخُ stamp مطابقة (الملفُّ الجانبيّ والجدول)" if same else "❌ تواريخُ stamp تختلف")
            return 0 if same else 1
        n_side, n_rows = write_levels(der)
        print(f"🧾 «واثق» {st['wathiq']} صورة: بلا وحدةٍ في الجدول {st['no_unit']} · على وحدةٍ مؤرَّخةٍ أصلًا {st['unit_dated']} · "
              f"على وحدةٍ غيرِ مؤرَّخة {st['to_undated']}")
        print(f"🧾 كُتب: {n_side} وحدة ({n_rows} صفًّا) بوسم {METHOD} · تعارض {len(conflict)} {conflict}")
        for d in der:
            print(f"   {d['symbol']}|{d['line']} ⟵ {d['date']} · {d['fingerprint']}")
        return 0
    body = _tsv(rows, COLS)
    if mode == "--check":
        same = open(TABLE, encoding="utf-8").read() == body
        print("✅ جدولُ الطابع مطابقٌ بايتًا" if same else "❌ جدولُ الطابع يختلف")
        return 0 if same else 1
    open(TABLE, "w", encoding="utf-8").write(body)
    print("\n".join(summary(rows, recs, files, ocr)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
