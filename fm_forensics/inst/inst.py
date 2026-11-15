"""🏛️ `T-INST` «فلتر المؤسسات» — قياسٌ أماميٌّ وصفيّ (العقد `T_INST_prereg.md` · قبل أيّ رقم).

الأوضاع: `check` (بلا شبكة) · `capture` (finviz على الرنر ⟵ ① و②) · `sec` (EDGAR ⟵ ④ · `SEC_CONTACT`) · `measure` (Polygon ⟵ ③ بعد D20).
قراءةٌ وقياسٌ فقط: لا تلغرام · لا كتابةَ حالة · لا إنتاج · وكلُّ وضعٍ يخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from html import unescape
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_INST_prereg.md")
CONTRACT_SHA = "9e05c81c9b2c6907a76aa2a4be79407e5c9e01c9eecd6400ea1c8e6c82a2e3df"
CONTRACT_RC, KEY_RC, DATA_RC = 9, 3, 7
DATA_FILE = os.path.join(HERE, "data", "finviz_inst_20261115.json")
FILTERS = "cap_nano,exch_nasd,sh_instown_o20,sh_insttrans_o10,sh_price_u7"
SCREEN_URL = "https://finviz.com/screener.ashx?v={v}&f=" + FILTERS + "&r={r}"
OWNER_SAW = 31
D0, D_MOM, D20 = "2026-11-13", "2026-11-06", "2026-12-14"
WIN = 20
Q3 = ("2026-07-01", "2026-09-30")
Q2 = ("2026-04-01", "2026-06-30")
Q4 = ("2026-10-01", "2026-11-14")
F13_Q3 = ("2026-10-01", "2026-11-15")
F13_Q2 = ("2026-07-01", "2026-08-15")
MM_NAMES = ("citadel securities", "virtu", "hudson river trading", "jane street", "susquehanna", "two sigma securities", "g1 execution",
            "tower research", "optiver", "imc", "flow traders", "wolverine", "xtx", "jump", "drw", "group one", "simplex", "belvedere",
            "hap trading", "squarepoint", "millennium", "goldman sachs", "morgan stanley", "ubs", "barclays", "jefferies")
PLACEMENT_FORMS = ("D", "D/A")
ATM_PHRASE = "at-the-market"
MIN_I = 10
BOOT_B, BOOT_SEED = 2000, "TINST"


def log(*a):
    print(*a, flush=True)


def contract_ok():
    if not os.path.exists(CONTRACT):
        return False
    with open(CONTRACT, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest() == CONTRACT_SHA


# ── نقيّة ────────────────────────────────────────────────────────────────────────────────────────
class _Rows(HTMLParser):
    """صفوفُ الجداول: لكلّ <tr> نصوصُ خلاياه (td/th) ورمزُ أوّلِ رابط quote.ashx?t= فيه."""

    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._tick = [], None, None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self._row, self._tick = [], None
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "a" and self._row is not None and self._tick is None:
            m = re.search(r"quote\.ashx\?t=([A-Z][A-Z0-9.\-]*)", a.get("href") or "")
            if m:
                self._tick = m.group(1)

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append((self._row, self._tick))
            self._row = None


def screen_tickers(html):
    """🔧 (2026-11-15 · عطلٌ مُثبَت في `43758111383`/`43759650332`: المطبوع 31 والمستخرج 0 — finviz انتقل إلى جدول `fv-table` بلا <tr>
    وروابطُه `/quote?t=` لا `quote.ashx?t=`) — الرموزُ من وسوم <a> صفوف النتائج: الصنفُ `fv-table_row-link` (الجديد) أو `tab-link` (القديم)
    ورابطُ `quote?t=`/`quote.ashx?t=` · بترتيبها بلا تكرار أيًّا كان ترتيبُ الخصائص · وروابطُ التذييل (`tab-link` بلا رابط رمز) لا تُعَدّ."""
    out = []
    for tag in re.findall(r"<a\b[^>]*>", html or "", flags=re.I):
        if "tab-link" not in tag and "fv-table_row-link" not in tag:
            continue
        m = re.search(r"quote(?:\.ashx)?\?t=([A-Z][A-Z0-9.\-]*)", tag)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


_FV_CELL = re.compile(r'<[^>]*\bdata-column-id="([^"]+)"[^>]*>')
_FV_ROW = re.compile(r'data-row-index="\d+"[^>]*>\s*<a\b[^>]*fv-table_row-link[^>]*quote\?t=([A-Z][A-Z0-9.\-]*)')


def fv_rows(html):
    """جدولُ finviz الجديد (`fv-table`) ⟵ {رمز: {عنوانُ العمود أو معرّفُه: نصّ}} بأحسن جهد (وصفٌ لا يحكم) — العنوانُ من خلايا
    role="columnheader" بمعرّف العمود · والقيمةُ نصُّ الخليّة حتى الخليّة التالية بلا وسوم."""
    html = html or ""
    rows = [(m.start(), m.group(1)) for m in _FV_ROW.finditer(html)]
    ms = list(_FV_CELL.finditer(html))
    label, out = {}, {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else min(len(html), m.end() + 400)
        seg = html[m.end():end]
        seg = seg[:seg.find("</div>")] if "</div>" in seg else seg
        txt = " ".join(unescape(re.sub(r"<[^>]*>", " ", seg)).split())
        if 'role="columnheader"' in m.group(0):
            label.setdefault(m.group(1), txt)
            continue
        owner = None
        for pos, sym in rows:
            if pos < m.start():
                owner = sym
            else:
                break
        if owner:
            out.setdefault(owner, {})[m.group(1)] = txt
    return {sym: {label.get(k, k): v for k, v in d.items()} for sym, d in out.items()}


def parse_screen(html):
    """صفحةُ finviz ⟵ (العددُ الكلّيّ المطبوع أو None، الرأس، [(رمز، {عمود: نصّ})]) — **الرموزُ من `screen_tickers`** (لا من الجدول) ·
    والأعمدةُ بأحسن جهد: الرأسُ صفٌّ فيه خليّةٌ «Ticker» · وصفُّ الرمز يُقرن بالرأس إن تساوى الطولان وإلّا {} (وصفٌ لا يحكم)."""
    m = re.search(r"(\d[\d,]*)\s*Total", html or "")
    total = int(m.group(1).replace(",", "")) if m else None
    p = _Rows()
    p.feed(html or "")
    head = next((r for r, _t in p.rows if any(c.strip() == "Ticker" for c in r)), None)
    rowmap = {}
    for r, t in p.rows:
        if t and t not in rowmap and t in r:
            rowmap[t] = dict(zip(head, r)) if head and len(r) == len(head) else {}
    if not rowmap:
        rowmap = fv_rows(html)
    return total, head, [(t, rowmap.get(t, {})) for t in screen_tickers(html)]


def merge_pages(pages):
    """[(total, head, rows)] ⟵ (العدد، رموزٌ بترتيبها بلا تكرار، {رمز: صفّ})."""
    total, order, rows = None, [], {}
    for t, _h, rs in pages:
        total = total if total is not None else t
        for s, row in rs:
            if s not in rows:
                order.append(s)
                rows[s] = row
    return total, order, rows


def overlap(tickers, near_watch, watch_stocks):
    """② ⟵ {«تحت المتابعة»: [...] · «القائمة»: [(رمز، موقوف؟)]}."""
    nw = set(near_watch)
    wl = {s.get("symbol"): bool(s.get("stopped") or s.get("status") == "stopped") for s in watch_stocks or [] if s.get("symbol")}
    return {"near_watch": [t for t in tickers if t in nw], "watchlist": [(t, wl[t]) for t in tickers if t in wl]}


def is_mm(name):
    low = " ".join(str(name or "").lower().split())
    return any(re.search(r"(^|[^a-z])" + re.escape(k) + r"([^a-z]|$)", low) for k in MM_NAMES)


def new_holders(q3_names, q2_names):
    """④ ⟵ مُودِعو الثالث وليسوا في الثاني (مطبَّعٌ: حروفٌ صغيرة · مسافاتٌ مفردة · بلا «(CIK …)»)."""
    norm = lambda n: " ".join(re.sub(r"\(CIK[^)]*\)", "", str(n)).lower().split())
    old = {norm(n) for n in q2_names}
    seen, out = set(), []
    for n in q3_names:
        k = norm(n)
        if k and k not in old and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def issuer_query(title):
    """اسمُ المُصدِر للبحث النصّيّ: بلا لاحقةٍ قانونيّة (Inc · Corp · Ltd · plc · Co) وبلا فواصلَ في آخره."""
    t = re.sub(r"[,.]", " ", str(title or ""))
    words = t.split()
    while words and words[-1].lower() in ("inc", "corp", "corporation", "ltd", "limited", "plc", "co", "company", "nv", "sa", "ag"):
        words.pop()
    return " ".join(words)


def offering_flags(filings, lo, hi):
    """submissions (form، تاريخ، items) ⟵ {الطرحُ المسجَّل · خاصّ D · PIPE 8-K 3.02} في [lo، hi]."""
    out = {"registered": [], "placement_d": [], "pipe_302": []}
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "tblock"))
    import tblock as TB
    for f in filings:
        form, d, items = f.get("form"), f.get("date") or "", str(f.get("items") or "")
        if not (lo <= d <= hi):
            continue
        if form in TB.OFFER_FORMS:
            out["registered"].append((form, d))
        elif form in PLACEMENT_FORMS:
            out["placement_d"].append((form, d))
        elif form == "8-K" and "3.02" in items:
            out["pipe_302"].append((form, d))
    return out


def outcome(bars, d0, d1, d20, win=WIN):
    """③: bars = [(يوم، high، close)] مرتّبة ⟵ (حصّة50، حصّة100، عددُ الجلسات) أو (None، None، n) لأقلَّ من win جلسة أو بلا إغلاق D0."""
    c0 = next((c for d, _h, c in bars if d == d0), None)
    w = [h for d, h, _c in bars if d1 <= d <= d20]
    if c0 is None or c0 <= 0 or len(w) < win:
        return None, None, len(w)
    r = max(w) / c0 - 1
    return r >= 0.5, r >= 1.0, len(w)


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def quintile_edges(xs):
    v = sorted(xs)
    return [v[int(len(v) * k / 5)] for k in (1, 2, 3, 4)] if len(v) >= 5 else []


def quintile_of(x, edges):
    return sum(1 for e in edges if x >= e)


def mom_adj_diff(rows, key):
    """③ ضابطُ الزخم: rows [(grp، q، hit)] ⟵ Σ_q n_I (p_I − p_R) ÷ Σ n_I على الأخماس التي فيها المجموعتان (أو None)."""
    num = den = 0.0
    for q in sorted({q for _g, q, _h in rows}):
        a = [h for g, qq, h in rows if qq == q and g == "I"]
        b = [h for g, qq, h in rows if qq == q and g == "R"]
        if a and b:
            num += len(a) * (sum(a) / len(a) - sum(b) / len(b))
            den += len(a)
    return num / den if den else None


def boot_adj(units, b=BOOT_B, seed=BOOT_SEED):
    """units [(sym، grp، q، hit)] ⟵ (التقدير، (2.5%، 97.5%)) بإعادة سحب الرموز داخل كلّ مجموعة."""
    est = mom_adj_diff([(g, q, h) for _s, g, q, h in units], None)
    if est is None:
        return None, (None, None)
    rng = random.Random(seed)
    I = [u for u in units if u[1] == "I"]
    R = [u for u in units if u[1] == "R"]
    xs = []
    for _ in range(b):
        smp = [I[rng.randrange(len(I))] for _ in I] + [R[rng.randrange(len(R))] for _ in R]
        v = mom_adj_diff([(g, q, h) for _s, g, q, h in smp], None)
        if v is not None:
            xs.append(v)
    xs.sort()
    return est, (xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]) if xs else (None, None)


# ── الجلب ────────────────────────────────────────────────────────────────────────────────────────
def _get(url, headers, tries=4, as_json=False):
    """GET بإعادة · و429 (خنقُ finviz) يُمهَل أطول · والتعذّرُ يُطبع بحالته (لا صمت)."""
    import requests
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=40)
            last = r.status_code
            if r.status_code == 200:
                return r.json() if as_json else r.text
        except Exception as e:                                   # noqa: BLE001
            last = type(e).__name__
        time.sleep((15 if last == 429 else 2) * (i + 1))
    log(f"⚠️ تعذّر {url.split('?')[0]} · آخرُ حالة {last}")
    return None


UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"}


def fetch_screen(view):
    pages = []
    for k in range(10):
        html = _get(SCREEN_URL.format(v=view, r=1 + 20 * k), UA)
        if html is None:
            return None
        t, h, rs = parse_screen(html)
        if not rs:
            i = html.find("quote?t=")
            log(f"🔍 v={view} r={1 + 20 * k}: المطبوع {t} · رموزٌ 0 · الطول {len(html)} · مقتطف: {html[max(0, i - 300):i + 300] if i >= 0 else html[:600]!r}")
            for _kw in ("quote?t=", "quote.ashx", "/quote/", "ticker", "Ticker", "styled-row", "screener-body-table", "tab-link", "<tr"):
                _ix = [mm.start() for mm in re.finditer(re.escape(_kw), html)]
                log(f"🔍 «{_kw}» ×{len(_ix)}" + (f" · أوّلها: {html[max(0, _ix[min(2, len(_ix) - 1)] - 200):_ix[min(2, len(_ix) - 1)] + 300]!r}" if _ix else ""))
            try:
                os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
                open(os.path.join(HERE, "out", f"raw_v{view}_r{1 + 20 * k}.html"), "w", encoding="utf-8").write(html)
            except OSError:
                pass
        pages.append((t, h, rs))
        got = len({s for _t, _h, rr in pages for s, _r in rr})
        if not rs or (t is not None and got >= t):
            break
        time.sleep(4)
    return merge_pages(pages)


def mode_capture():
    a = fetch_screen(111)
    b = fetch_screen(131)
    if a is None or b is None:
        log("⛔ تعذّر جلبُ finviz — «لا مادّة»")
        return DATA_RC
    total, order, _rows = a
    _t2, order2, own = b
    if not order or (total is not None and total != len(order)):
        log(f"⛔ finviz: المطبوع {total} والمجلوب {len(order)} — «لا مادّة»")
        return DATA_RC
    nw = json.load(open(os.path.join(ROOT, "near_watch.json"), encoding="utf-8"))
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8"))
    ov = overlap(order, list(nw), wl.get("stocks") or [])
    snap = {"captured_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "filters": FILTERS, "finviz_total": total,
            "owner_saw": OWNER_SAW, "tickers": order, "ownership": {s: own.get(s) for s in order}, "near_watch": sorted(nw),
            "watchlist": [s.get("symbol") for s in wl.get("stocks") or []], "overlap": ov, "run": os.environ.get("GITHUB_RUN_ID"),
            "own_view_tickers": order2}
    log("")
    log("=" * 70)
    log(f"🏛️ T-INST ① الالتقاط · {snap['captured_utc']} · finviz {total} (رآه المالك {OWNER_SAW}) · التشغيلة {snap['run']}")
    for s in order:
        r = own.get(s) or {}
        log(f"   {s}: السعر {r.get('Price')} · Inst Own {r.get('Inst Own')} · Inst Trans {r.get('Inst Trans')} · Float {r.get('Float')}")
    log(f"② في «تحت المتابعة» ({len(nw)}): {len(ov['near_watch'])} — {ov['near_watch']}")
    log(f"② في القائمة ({len(snap['watchlist'])}): {len(ov['watchlist'])} — {ov['watchlist']}")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(snap, open(os.path.join(HERE, "out", "capture.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("INST_CAPTURE_JSON " + json.dumps(snap, ensure_ascii=False))
    return 0


def _sec_list(contact):
    j = _get("https://www.sec.gov/files/company_tickers.json", {"User-Agent": contact}, as_json=True)
    return {v["ticker"].upper(): (int(v["cik_str"]), v["title"]) for v in (j or {}).values()} if j else None


def _f13(name, lo, hi, contact):
    """⟵ (المُودِعون، العددُ الكلّيّ) أو (None، None)."""
    import urllib.parse
    names, total, frm = [], None, 0
    for _ in range(10):
        q = urllib.parse.quote(f'"{name}"')
        j = _get(f"https://efts.sec.gov/LATEST/search-index?q={q}&forms=13F-HR&dateRange=custom&startdt={lo}&enddt={hi}&from={frm}",
                 {"User-Agent": contact}, as_json=True)
        if j is None:
            return None, None
        hits = (j.get("hits") or {})
        total = (hits.get("total") or {}).get("value")
        hs = hits.get("hits") or []
        for h in hs:
            names.extend((h.get("_source") or {}).get("display_names") or [])
        frm += len(hs)
        if not hs or (total is not None and frm >= total):
            break
        time.sleep(0.3)
    return names, total


def mode_sec(tickers=None):
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not contact:
        log("⛔ SEC_CONTACT غيرُ مضبوط — لا ④")
        return KEY_RC
    if tickers is None:
        cap = os.path.join(HERE, "out", "capture.json")
        src = cap if os.path.exists(cap) else DATA_FILE
        if not os.path.exists(src):
            log("⛔ لا مادّةَ التقاط — ④ ينتظر ①")
            return DATA_RC
        tickers = json.load(open(src, encoding="utf-8"))["tickers"]
    m = _sec_list(contact)
    if m is None:
        log("⛔ تعذّر جلبُ خريطة SEC — «لا قياس»")
        return DATA_RC
    res, any_hits = {}, False
    for s in tickers:
        cik, title = m.get(s, (None, None))
        row = {"cik": cik, "title": title}
        if cik:
            sub = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", {"User-Agent": contact}, as_json=True) or {}
            rc = (sub.get("filings") or {}).get("recent") or {}
            fl = [{"form": f, "date": d, "items": it, "doc": doc, "acc": acc}
                  for f, d, it, doc, acc in zip(rc.get("form", []), rc.get("filingDate", []), rc.get("items", []) or [""] * len(rc.get("form", [])),
                                                rc.get("primaryDocument", []), rc.get("accessionNumber", []))]
            for nm, (lo, hi) in (("q2", Q2), ("q3", Q3), ("q4", Q4)):
                row[nm] = offering_flags(fl, lo, hi)
            atm = []
            for f in fl:
                if f["form"] in ("424B5", "424B3") and Q3[0] <= f["date"] <= Q3[1]:
                    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{f['acc'].replace('-', '')}/{f['doc']}"
                    txt = _get(url, {"User-Agent": contact}) or ""
                    if ATM_PHRASE in txt.lower():
                        atm.append((f["form"], f["date"]))
                    time.sleep(0.15)
            row["q3_atm"] = atm
            row["preceded"] = bool(atm or row["q3"]["placement_d"] or row["q3"]["pipe_302"])
            qn = issuer_query(title)
            n3, t3 = _f13(qn, *F13_Q3, contact)
            n2, t2 = _f13(qn, *F13_Q2, contact)
            row.update({"query": qn, "f13_q3_total": t3, "f13_q2_total": t2})
            if n3 is not None and n2 is not None:
                any_hits = any_hits or bool(t3 or t2)
                nh = new_holders(n3, n2)
                row["new_holders"] = [(n, "صانع سوق/كمّيّ" if is_mm(n) else "صندوق/آخر") for n in nh]
            time.sleep(0.2)
        res[s] = row
    log("")
    log("=" * 70)
    log(f"🏛️ T-INST ④ الحائزون الجدد والطروحات · التشغيلة {os.environ.get('GITHUB_RUN_ID')} · قائمةُ صنّاع السوق ({len(MM_NAMES)}): {', '.join(MM_NAMES)}")
    mm = fund = 0
    for s, r in res.items():
        nh = r.get("new_holders")
        if nh:
            mm += sum(1 for _n, k in nh if k.startswith("صانع"))
            fund += sum(1 for _n, k in nh if not k.startswith("صانع"))
        log(f"   {s} ({r.get('title')} · بحث «{r.get('query')}»): 13F الثالث {r.get('f13_q3_total')} · الثاني {r.get('f13_q2_total')} · "
            f"جدد {len(nh) if nh is not None else '—'} {nh if nh else ''} · طرحٌ في الثالث: ATM {r.get('q3_atm')} · D {(r.get('q3') or {}).get('placement_d')} · "
            f"PIPE {(r.get('q3') or {}).get('pipe_302')} · مسجَّل {(r.get('q3') or {}).get('registered')} ⟵ سبق؟ {r.get('preceded')}")
    pre = sum(1 for r in res.values() if r.get("preceded"))
    log(f"④ الحائزون الجدد: صانعُ سوق/كمّيّ {mm} · صندوق/آخر {fund}" + ("" if any_hits else " · ⚪ «لا قياس»: البحثُ النصّيّ لم يُرجع أيَّ 13F"))
    log(f"④ سبقه طرحٌ في الربع الثالث: {pre} من {len(res)}")
    print("INST_SEC_JSON " + json.dumps(res, ensure_ascii=False, default=str))
    return 0


def mode_measure():
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return KEY_RC
    if not os.path.exists(DATA_FILE):
        log("⛔ مادّةُ الالتقاط غيرُ مدموجة — «لا قياس»")
        return DATA_RC
    if dt.date.today().isoformat() <= D20:
        log(f"⛔ النافذةُ لم تكتمل (D20 = {D20}) — لا قراءة قبلها")
        return DATA_RC
    sys.path.insert(0, ROOT)
    import pit_history as PH
    snap = json.load(open(DATA_FILE, encoding="utf-8"))
    I = list(snap["tickers"])
    R = [s for s in snap["near_watch"] if s not in set(I)]
    data, diag = {}, {}
    for s in I + R:
        df, why = PH.polygon_daily(s, D_MOM, D20, key)
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        if df is None:
            continue
        data[s] = [(i.date().isoformat() if hasattr(i, "date") else str(i)[:10], float(h), float(c))
                   for i, h, c in zip(df.index, df["High"], df["Close"])]
    units, excl = [], []
    r5 = {}
    for s, bars in data.items():
        c0 = next((c for d, _h, c in bars if d == D0), None)
        cm = next((c for d, _h, c in bars if d == D_MOM), None)
        if c0 and cm:
            r5[s] = c0 / cm - 1
    edges = quintile_edges(list(r5.values()))
    for g, syms in (("I", I), ("R", R)):
        for s in syms:
            h50, h100, n = outcome(data.get(s) or [], D0, "2026-11-16", D20)
            if h50 is None or s not in r5:
                excl.append((g, s, n))
                continue
            units.append((s, g, quintile_of(r5[s], edges), int(h50), int(h100)))
    log("")
    log("=" * 70)
    log(f"🏛️ T-INST ③ · D0 {D0} · D1…D20 2026-11-16…{D20} · التشغيلة {os.environ.get('GITHUB_RUN_ID')} · الشموع {diag}")
    out = {}
    for lab, ix in (("+50%", 3), ("+100%", 4)):
        row = {}
        for g in ("I", "R"):
            hs = [u[ix] for u in units if u[1] == g]
            row[g] = (sum(hs), len(hs), wilson(sum(hs), len(hs)))
        nI = row["I"][1]
        est, ci = boot_adj([(u[0], u[1], u[2], u[ix]) for u in units]) if nI >= MIN_I else (None, (None, None))
        out[lab] = {"I": row["I"], "R": row["R"], "adj": est, "ci": ci}
        f = lambda t: f"{t[0]}/{t[1]} = {100 * t[0] / t[1]:.1f}% [{100 * t[2][0]:.1f}، {100 * t[2][1]:.1f}]" if t[1] else "—"
        log(f"   {lab}: I {f(row['I'])} · R {f(row['R'])} · الفرقُ المضبوط بالزخم "
            f"{'⚪ لا قياس (I دون 10)' if est is None else f'{100 * est:+.1f} نقطة [{100 * ci[0]:+.1f}، {100 * ci[1]:+.1f}]'}")
    log(f"   خارج الحصّة (أقلّ من {WIN} جلسة أو بلا إغلاق): {len(excl)} — {[e for e in excl if e[0] == 'I']}")
    print("INST_MEASURE_JSON " + json.dumps({"out": out, "excluded": excl, "n_units": len(units)}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="check", choices=("check", "capture", "sec", "measure"))
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقد مطابق")
        return 0
    return {"capture": mode_capture, "sec": mode_sec, "measure": mode_measure}[a.mode]()


if __name__ == "__main__":
    sys.exit(main())
