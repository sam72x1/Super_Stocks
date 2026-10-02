# -*- coding: utf-8 -*-
"""
🗂️ FAISAL METHOD V3 — بناء فهرس الصور الجنائيّ (قراءةٌ فقط · لا يمسّ الإنتاج).

المدخل: `faisal_images/` كما هي (لا تُعدَّل ولا تُنقل — الدليلُ الخامّ ثابت §5).
المخرَج: `faisal_method_v3/image_corpus.json` · `image_provenance.json` · `dedup_clusters.json`.

لكلّ صورة: SHA256 · dHash 64 و256 بت · pHash 64 · aHash · الأبعاد والحجم والصيغة ·
العائلة (TG/IMG/X/CH/EDU/APP/WA) · أوّلُ commit أضافها (تاريخ ورسالة) · نصُّ OCR
(Tesseract eng+ara — من `data/ocr_text.jsonl` المحفوظ) · حقولٌ مستخرَجة آليًّا من النصّ
(رموز · فريم · مؤشّرات · نسب · أسعار · كلمات النماذج · الكاتب) · والوثائق التي تذكرها.

⚖️ **الحقولُ الآليّة «مرشَّحة» لا «مؤكَّدة»:** مصدرُها OCR وقد يُخطئ ⇒ تُوسَم
`auto_ocr` · والتحقّقُ البصريّ يُسجَّل منفصلًا في `visual_review` (من `data/visual_review.json`).

التشغيل:
    python3 faisal_method_v3/corpus_build.py                    # يبني من الملفّات المحفوظة
    python3 faisal_method_v3/corpus_build.py --ocr-from DIR     # يجمع OCR من مجلّد ‎*.txt أوّلًا
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "faisal_images")
OUT_DIR = os.path.join(ROOT, "faisal_method_v3")
DATA = os.path.join(OUT_DIR, "data")
OCR_FILE = os.path.join(DATA, "ocr_text.jsonl")
VISUAL_FILE = os.path.join(DATA, "visual_review.json")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

# عتباتُ التكرار — مكتوبةٌ قبل أيّ عدّ (§7) وتُطبع في المخرَج.
DUP_DHASH256_MAX = 24      # من 256 بت (~9.4%) ⟵ «شبه مطابق»
DUP_PHASH_MAX = 10         # من 64 بت
DUP_OCR_JACCARD = 0.85     # تشابهُ نصّ OCR ⟵ «مشتقّ/مقصوص/معلَّم» مرشَّح
DUP_OCR_MIN_TOKENS = 15    # لا يُحكم بالنصّ على صورةٍ شبهِ خالية منه
# 🔴 البصمةُ تقترح والعينُ تحكم: «فيتو نصّ OCR» جُرِّب بعد أوّل مراجعةٍ بصريّة فأخطأ في 35 من
# 39 زوجًا (ضجيجُ OCR على نصّ الشارت) فأُسقط ⟵ الحكمُ النهائيّ من `data/dedup_review.json`
# (أزواجٌ «ليست تكرارًا» بقرارٍ بصريّ مسبَّب) — والمقترَحُ الآليّ والقرارُ البصريّ كلاهما في المخرَج.
REVIEW_FILE = os.path.join(DATA, "dedup_review.json")


# ── البصمات ───────────────────────────────────────────────────────────────
def _gray(im, w, h):
    return np.asarray(im.convert("L").resize((w, h), Image.LANCZOS), dtype=np.float64)


def dhash_bits(im, size=8):
    g = _gray(im, size + 1, size)
    return (g[:, 1:] > g[:, :-1]).flatten()


def ahash_bits(im, size=8):
    g = _gray(im, size, size)
    return (g > g.mean()).flatten()


def _dct_matrix(n):
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    c = np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    c[0] /= np.sqrt(2)
    return c * np.sqrt(2.0 / n)


_DCT32 = _dct_matrix(32)


def phash_bits(im):
    g = _gray(im, 32, 32)
    d = _DCT32 @ g @ _DCT32.T
    low = d[:8, :8].flatten()[1:]          # بلا مكوّن DC
    return np.concatenate([[False], low > np.median(low)])


def bits_hex(b):
    v = 0
    for x in b:
        v = (v << 1) | int(bool(x))
    return f"{v:0{(len(b) + 3) // 4}x}"


def hamming_hex(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


# ── استخراجٌ آليّ من OCR (مرشَّح لا مؤكَّد) ─────────────────────────────────
_TICKER_RE = re.compile(r"\$([A-Z]{2,5})\b")
_HEADER_TICKER_RE = re.compile(r"(?m)^\s*(?:[<«]?\s*\d*\s*)?([A-Z]{2,5})\s*$")
_TF_PATTERNS = [
    ("1m", r"\b1\s*min"), ("5m", r"\b5\s*mins?\b|فريم 5 دقايق|5 دقائق"),
    ("15m", r"\b15\s*mins?\b|15 دقيقة"), ("30m", r"\b30\s*mins?\b|30 دقيقه|30 دقيقة"),
    ("1h", r"\b1\s*hour\b|ساعة"), ("4h", r"\b4\s*hours?\b|4 ساعات|4س"),
    ("D", r"\bDaily\b|يومي"), ("W", r"\bWeekly\b|أسبوعي|اسبوعي"), ("M", r"\bMonthly\b|شهري"),
]
_INDICATORS = [
    ("RSI", r"RSI\s*\(?\s*\d*"), ("MACD", r"MACD"), ("KST", r"KST"), ("FSTO", r"FSTO|Stoch"),
    ("CCI", r"CCI"), ("EMA", r"EMA"), ("SMA/MA", r"\bMA\s*\d|\bSMA"), ("BOLL", r"BOLL|Bollinger"),
    ("WR", r"Williams|%R\b|\bWR\b"), ("DMI", r"DMI|ADX"), ("VOL", r"\bVOL\b|Volume"),
    ("KLINGER", r"Klinger|KVO"), ("ATR", r"\bATR\b"), ("FIB", r"Fib|فيبو|فيب"),
]
_PATTERN_WORDS = {
    "W_double_bottom": r"\bW\b|قاع مزدوج|القاع المزدوج|Double Bottom|double bottom",
    "M_double_top": r"\bM\b(?!ACD|A\b)|قمة مزدوجة|القمة المزدوجة|Double Top|double top",
    "neckline": r"عنق|neckline|Neckline",
    "head_shoulders": r"كتف|Head|Shoulder",
    "triangle": r"مثلث|[Tt]riangle",
    "flag_pennant": r"علم|[Ff]lag|[Pp]ennant|راية",
    "wedge": r"وتد|[Ww]edge",
    "channel": r"قناة|[Cc]hannel",
    "trendline": r"ترند|[Tt]rend",
    "elliott": r"إليوت|اليوت|Elliot|موجة|موجات|[Ww]ave",
    "butterfly_harmonic": r"فراش|[Bb]utterfly|هارمون",
    "liquidity_sweep": r"سحب سيول|سحب السيول|كنس|sweep",
    "gap": r"فجوة|فجوه|[Gg]ap\b",
    "support": r"دعم|[Ss]upport",
    "resistance": r"مقاوم|[Rr]esistance",
    "target": r"هدف|الهدف|أهداف|اهداف|[Tt]arget",
    "entry": r"دخول|[Ee]ntry",
    "stop": r"وقف|ستوب|ستوبلوس|[Ss]top",
    "split": r"تقسيم|[Ss]plit",
    "breakout": r"اختراق|كسر|[Bb]reakout",
    "retest": r"إعادة اختبار|اعادة اختبار|[Rr]etest|يختبر|اختبار",
    "structure_hh_hl": r"Higher High|Higher Low|Lower High|Lower Low|\bHH\b|\bHL\b|\bLH\b|\bLL\b|BOS|CHoCH",
}
_PCT_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*[%٪]|[%٪]\s*(\d{1,3}(?:\.\d+)?)")
_PRICE_RE = re.compile(r"(?<![\d.])(\d{1,4}\.\d{1,4})(?![\d.])")
_DATE_RE = re.compile(r"\b(20\d\d)/(\d{1,2})/(\d{1,2})\b")


def extract(text):
    t = text or ""
    out = {"tickers": [], "timeframes": [], "indicators": [], "pattern_words": [],
           "percents": [], "prices": [], "post_date": None, "author_signals": []}
    tick = set(_TICKER_RE.findall(t))
    for m in _HEADER_TICKER_RE.findall(t):
        if m not in {"RSI", "MACD", "KST", "CCI", "EMA", "BOLL", "VOL", "USD", "ET", "AM", "PM", "LTE", "OK"}:
            tick.add(m)
    out["tickers"] = sorted(tick)
    out["timeframes"] = [k for k, p in _TF_PATTERNS if re.search(p, t)]
    out["indicators"] = [k for k, p in _INDICATORS if re.search(p, t)]
    out["pattern_words"] = [k for k, p in _PATTERN_WORDS.items() if re.search(p, t)]
    pct = []
    for a, b in _PCT_RE.findall(t):
        v = a or b
        try:
            pct.append(float(v))
        except ValueError:
            pass
    out["percents"] = sorted(set(pct))
    out["prices"] = sorted({float(x) for x in _PRICE_RE.findall(t)})[:60]
    d = _DATE_RE.search(t)
    if d:
        y, mo, da = (int(x) for x in d.groups())
        if 1 <= mo <= 12 and 1 <= da <= 31:
            out["post_date"] = f"{y:04d}-{mo:02d}-{da:02d}"
    if re.search(r"@kisar_|\bFaisal\b|فيصل", t):
        out["author_signals"].append("faisal_handle_or_name")
    for h in sorted(set(re.findall(r"@([A-Za-z0-9_]{3,20})", t))):
        if h.lower() != "kisar_":
            out["author_signals"].append("@" + h)
    return out


def family(name):
    m = re.match(r"([A-Z]+)_", name)
    return m.group(1) if m else "OTHER"


def tokens(text):
    return {w for w in re.findall(r"[\w؀-ۿ.]{2,}", text or "") if not w.isdigit()}




# ── git ───────────────────────────────────────────────────────────────────
def git_first_adds():
    """أوّلُ commit أضاف كلَّ مسارٍ حاليّ (بلا كشف إعادة التسمية ⟵ المسارُ الحاليّ نفسُه)."""
    try:
        out = subprocess.run(
            ["git", "log", "--no-renames", "--diff-filter=A", "--name-only",
             "--format=C %H %aI %s", "HEAD", "--", "faisal_images/"],
            cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    except Exception:                                    # noqa: BLE001
        return {}
    first, cur = {}, None
    for line in out.splitlines():
        if line.startswith("C "):
            parts = line.split(" ", 3)
            cur = {"commit": parts[1], "date": parts[2], "subject": parts[3] if len(parts) > 3 else ""}
        elif line.strip() and cur:
            first[line.strip()] = cur            # git log من الأحدث ⟵ الأخيرُ المكتوب = الأقدم
    return first


def git_renames():
    try:
        out = subprocess.run(
            ["git", "log", "-M", "--diff-filter=R", "--name-status", "--format=C %H %aI",
             "HEAD", "--", "faisal_images/"],
            cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    except Exception:                                    # noqa: BLE001
        return {}
    ren, cur = defaultdict(list), None
    for line in out.splitlines():
        if line.startswith("C "):
            cur = line.split(" ")[1:3]
        elif line.startswith("R") and cur:
            p = line.split("\t")
            if len(p) == 3:
                ren[p[2]].append({"from": p[1], "commit": cur[0], "date": cur[1]})
    return ren


# ── الوثائق التي تذكر كلَّ صورة ──────────────────────────────────────────────
def doc_mentions(stems):
    skip = {os.path.join(OUT_DIR)}
    pat = re.compile(r"\b(" + "|".join(re.escape(s) for s in sorted(stems, key=len, reverse=True)) + r")\b")
    ment = defaultdict(set)
    for dp, dn, fn in os.walk(ROOT):
        if any(dp.startswith(s) for s in skip) or "/.git" in dp or "/faisal_images" in dp:
            continue
        for f in fn:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:                            # noqa: BLE001
                continue
            rel = os.path.relpath(p, ROOT)
            for m in pat.findall(txt):
                ment[m].add(rel)
    return {k: sorted(v) for k, v in ment.items()}


# ── OCR ───────────────────────────────────────────────────────────────────
def collect_ocr(src_dir):
    rows = []
    ver = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()
    for f in sorted(os.listdir(IMG_DIR)):
        if not f.lower().endswith(IMG_EXT):
            continue
        p = os.path.join(src_dir, f + ".txt")
        txt = open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else None
        rows.append({"file": f, "sha256": sha256_file(os.path.join(IMG_DIR, f)),
                     "engine": (ver[0] if ver else "tesseract") + " · eng+ara · psm 3",
                     "text": txt})
    os.makedirs(DATA, exist_ok=True)
    with open(OCR_FILE, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def load_ocr():
    if not os.path.exists(OCR_FILE):
        return {}
    out = {}
    for line in open(OCR_FILE, encoding="utf-8"):
        r = json.loads(line)
        out[r["file"]] = r
    return out


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def image_fingerprint(path):
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        fmt = im.format
        return {"width": w, "height": h, "format": fmt,
                "dhash64": bits_hex(dhash_bits(im, 8)),
                "dhash256": bits_hex(dhash_bits(im, 16)),
                "phash64": bits_hex(phash_bits(im)),
                "ahash64": bits_hex(ahash_bits(im, 8))}


# ── التكرار ───────────────────────────────────────────────────────────────
class _UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def dedup(records, not_dup=()):
    """not_dup: أزواجُ (a, b) حكمت المراجعةُ البصريّة أنها ليست تكرارًا ⟵ لا تُوصَل."""
    nd = {tuple(sorted(p[:2])) for p in not_dup}
    uf = _UF()
    edges = []
    by_sha = defaultdict(list)
    for r in records:
        by_sha[r["sha256"]].append(r["id"])
        uf.find(r["id"])
    for ids in by_sha.values():
        for x in ids[1:]:
            uf.union(ids[0], x)
            edges.append({"a": ids[0], "b": x, "kind": "exact"})
    tok = {r["id"]: tokens(r.get("ocr_text") or "") for r in records}
    vetoed = []
    n = len(records)
    for i in range(n):
        a = records[i]
        for j in range(i + 1, n):
            b = records[j]
            if a["sha256"] == b["sha256"]:
                continue
            d256 = hamming_hex(a["dhash256"], b["dhash256"])
            dp = hamming_hex(a["phash64"], b["phash64"])
            kind = None
            if d256 <= DUP_DHASH256_MAX and dp <= DUP_PHASH_MAX:
                if tuple(sorted((a["id"], b["id"]))) in nd:
                    vetoed.append({"a": a["id"], "b": b["id"], "dhash256_dist": d256, "phash_dist": dp,
                                   "by": "visual_review"})
                    continue
                kind = "resized" if (a["width"], a["height"]) != (b["width"], b["height"]) else "near"
            else:
                ta, tb = tok[a["id"]], tok[b["id"]]
                if len(ta) >= DUP_OCR_MIN_TOKENS and len(tb) >= DUP_OCR_MIN_TOKENS:
                    jac = len(ta & tb) / len(ta | tb)
                    if jac >= DUP_OCR_JACCARD and tuple(sorted((a["id"], b["id"]))) not in nd:
                        kind = "derivative_text"   # مقصوص/معلَّم/نفس المنشور بلقطةٍ أخرى — مرشَّح
            if kind:
                uf.union(a["id"], b["id"])
                edges.append({"a": a["id"], "b": b["id"], "kind": kind,
                              "dhash256_dist": d256, "phash_dist": dp})
    groups = defaultdict(list)
    for r in records:
        groups[uf.find(r["id"])].append(r["id"])
    clusters = []
    for k, ids in sorted(groups.items()):
        clusters.append({"cluster_id": "C" + k, "members": sorted(ids), "size": len(ids)})
    return clusters, edges, vetoed


def main():
    if "--ocr-from" in sys.argv:
        n = collect_ocr(sys.argv[sys.argv.index("--ocr-from") + 1])
        print(f"OCR rows: {n}")
    ocr = load_ocr()
    visual = json.load(open(VISUAL_FILE, encoding="utf-8")) if os.path.exists(VISUAL_FILE) else {}
    files = sorted(f for f in os.listdir(IMG_DIR) if f.lower().endswith(IMG_EXT))
    adds = git_first_adds()
    ren = git_renames()
    stems = [os.path.splitext(f)[0] for f in files]
    ment = doc_mentions(stems)
    recs = []
    for f in files:
        p = os.path.join(IMG_DIR, f)
        stem = os.path.splitext(f)[0]
        fp = image_fingerprint(p)
        o = ocr.get(f) or {}
        txt = o.get("text")
        rel = "faisal_images/" + f
        rec = {"id": stem, "file": rel, "family": family(f), "bytes": os.path.getsize(p),
               "sha256": sha256_file(p), **fp,
               "git_first_add": adds.get(rel), "git_renamed_from": ren.get(rel, []),
               "ocr_text": txt, "ocr_engine": o.get("engine"),
               "ocr_sha_match": (o.get("sha256") == sha256_file(p)) if o else None,
               "auto_ocr": extract(txt),
               "doc_mentions": ment.get(stem, []),
               "visual_review": visual.get(stem)}
        recs.append(rec)
    review = json.load(open(REVIEW_FILE, encoding="utf-8")) if os.path.exists(REVIEW_FILE) else {}
    clusters, edges, vetoed = dedup(recs, review.get("not_duplicate", []))
    cid = {m: c["cluster_id"] for c in clusters for m in c["members"]}
    for r in recs:
        r["dup_cluster"] = cid[r["id"]]
    meta = {"generated_by": "faisal_method_v3/corpus_build.py",
            "images": len(recs),
            "thresholds": {"DUP_DHASH256_MAX": DUP_DHASH256_MAX, "DUP_PHASH_MAX": DUP_PHASH_MAX,
                           "DUP_OCR_JACCARD": DUP_OCR_JACCARD, "DUP_OCR_MIN_TOKENS": DUP_OCR_MIN_TOKENS,
                           },
            "visual_not_duplicate_pairs": len(vetoed),
            "clusters_visually_reviewed": len(review.get("reviewed_clusters", [])),
            "clusters": len(clusters),
            "multi_member_clusters": sum(1 for c in clusters if c["size"] > 1),
            "independent_units": len(clusters),
            "edge_kinds": {k: sum(1 for e in edges if e["kind"] == k)
                           for k in ("exact", "near", "resized", "derivative_text")},
            "ocr_rows": sum(1 for r in recs if r["ocr_text"] is not None),
            "ocr_empty": sum(1 for r in recs if r["ocr_text"] is not None and not r["ocr_text"].strip()),
            "visual_reviewed": sum(1 for r in recs if r["visual_review"])}
    json.dump({"meta": meta, "images": recs},
              open(os.path.join(OUT_DIR, "image_corpus.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"meta": meta, "clusters": [c for c in clusters if c["size"] > 1], "edges": edges,
               "visual_not_duplicate": vetoed, "review": review},
              open(os.path.join(OUT_DIR, "dedup_clusters.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    prov = [{"id": r["id"], "file": r["file"], "sha256": r["sha256"], "family": r["family"],
             "git_first_add": r["git_first_add"], "git_renamed_from": r["git_renamed_from"],
             "doc_mentions": r["doc_mentions"], "dup_cluster": r["dup_cluster"]} for r in recs]
    json.dump({"meta": {"images": len(prov)}, "provenance": prov},
              open(os.path.join(OUT_DIR, "image_provenance.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
