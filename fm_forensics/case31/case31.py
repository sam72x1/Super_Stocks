#!/usr/bin/env python3
"""🗂️🔬 `T-CASE31` — «الملف الجنائي لمنفجري الشهر» (العقد `T_CASE31_prereg.md` · أمرُ المالك 2026-11-20 · آخرُ بحث) — قراءةٌ وتحليلٌ فقط.

  verify            — ⓪ التحقّق: لكلّ رمزٍ في كون البوت بدايةُ الحركة وقاعُها وقمّتُها والنسبةُ الحاكمة بأسعارٍ مسوّاة · إسقاطُ التقسيم وخطأ البيانات ·
                      إكمالُ القائمة (‏+100% وذراع ‏+50%) منذ 2026-09-29 · وأنواعُ كلّ انفجار.
🔒 لا تلغرام · لا CONFIG يُسنَد · لا Polygon · المخرجاتُ بياناتٌ تحت `fm_forensics/case31/out/` · والعقدُ والفهرسُ ببصمتيهما (خروج 11).
"""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import case31_catalog as CAT                                      # noqa: E402

CONTRACT = os.path.join(HERE, "T_CASE31_prereg.md")
CONTRACT_SHA = "0086212ce08a3c99d40e8bc51f611161b0c535edf93dd4d06e211223a5add7af"                                                 # يُملأ قبل الدمج · فارغٌ ⟵ خروج 11
CATALOG_SHA = "50edfc023c15f922b0652d32301469df9e676c4d039daa76c447e18fcbdfc317"
OUT = os.path.join(HERE, "out")
# قائمةُ المالك كما وصلت (الرمز: نسبةُ الصعود كما وصلته) — تُتحقَّق في ⓪ ولا تُعدَّل
OWNER_LIST = {"PLCE": 124, "RDAC": 122, "AKAN": 102, "CHSN": 241, "INO": 214, "TANH": 182, "LABT": 182, "AEHL": 178, "GP": 174,
              "VCIG": 168, "ESLA": 159, "SDA": 145, "VIVS": 143, "FCUV": 136, "WHLR": 133, "ONFO": 129, "SHFS": 122, "AIMD": 119,
              "XLAB": 118, "SVRE": 111, "ONEG": 108, "CVKD": 107, "SMX": 106, "SAIQ": 101, "GCTK": 100, "OMH": 433, "SLS": 156,
              "ULBI": 145, "GIBO": 118, "CASK": 2857, "SNDK": 678}
WIN_FROM, MONTH_FROM, WIN_TO = "2026-09-29", "2026-10-20", "2026-11-20"      # §⓪-ب النوافذ بتاريخ بداية الحركة
GIT_FROM = "2026-08-16"                                           # أوّلُ لقطةٍ لـ«تحت المتابعة»
REF_WIN = 20                                                      # أدنى إغلاقٍ في العشرين قبل الزناد
START_C, START_H = 1.15, 1.30                                     # بدايةُ الحركة: إغلاقٌ 1.15× أو أعلى 1.30× إغلاق السابقة
PEAK_AFTER = 10                                                   # القمّةُ حتى الزناد + 10 جلسات
X100, X50 = 1.00, 0.50                                            # الحاكمة: منفجر +100% · ذراع +50%
ONE_CANDLE = 0.60                                                 # شمعةٌ واحدة: أكبرُ مدى يوميّ 60% من الحركة
RS_RECENT_DAYS = 60                                               # تقسيمٌ عكسيّ حديث قبل يوم القرار
SPLIT_NEAR = 5                                                    # تقسيمٌ في [b−5، p+5] جلسات
SPLIT_GAP_TOL = 0.20                                              # فجوةُ يوم التنفيذ تطابق النسبة ضمن 20% = غيرُ مسوّاة
SRC_RATIO = 1.5                                                   # اختلافُ المصدرين
NEWS_BEFORE = 3                                                   # المحفّز: من 3 جلسات قبل البداية إلى يومها
OFFER_AFTER = 10                                                  # الطرحُ اللاحق: 10 جلسات بعد البداية (وصف)
TV_DAILY_N = 320
RC_OK, RC_DATA, RC_ONCE, RC_BLIND, RC_FREEZE, RC_CONTRACT = 0, 5, 7, 8, 9, 11
OFFER_FORMS = ("424B", "S-1", "F-1", "S-3", "F-3")
NEWS_FORMS = ("8-K", "6-K")
KEYWORDS = (                                                      # §①-ط نوعُ المحفّز بالكلمات (أوّلُ مطابقةٍ بالترتيب)
    ("ذكاء اصطناعي", ("artificial intelligence", " ai ", "ai-", " ai,", "machine learning", "nvidia", "gpu", "data center", "llm")),
    ("كريبتو", ("bitcoin", "crypto", "ethereum", "solana", "token", "blockchain", "digital asset", "treasury strategy", "stablecoin")),
    ("FDA/سريريّ", ("fda", "phase 1", "phase 2", "phase 3", "clinical", "trial", "topline", "breakthrough", "orphan", "ind ", "nda", "bla")),
    ("استحواذ/اندماج", ("acquisition", "acquire", "merger", "merge", "buyout", "takeover", "tender offer", "going private", "strategic alternatives")),
    ("نتائج", ("quarter results", "earnings", "financial results", "revenue", "guidance", "fiscal")),
    ("طرح/تمويل", ("offering", "private placement", "pipe", "registered direct", "financing", "warrant", "convertible", "atm ")),
    ("شراكة/عقد", ("partnership", "agreement", "contract", "collaboration", "order", "awarded", "license", "mou", "distribution")),
    ("امتثال إدراج", ("nasdaq", "compliance", "deficiency", "minimum bid", "delisting", "listing")),
)
ITEM_TYPES = {"1.01": "شراكة/عقد", "2.02": "نتائج", "3.01": "امتثال إدراج", "3.02": "طرح/تمويل", "2.01": "استحواذ/اندماج",
              "5.02": "غيره", "7.01": "غيره", "8.01": "غيره"}


def log(m=""):
    print(m, flush=True)


def sha_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def contract_ok():
    try:
        return bool(CONTRACT_SHA) and sha_of(CONTRACT) == CONTRACT_SHA and CAT.sha() == CATALOG_SHA
    except OSError:
        return False


# ══ ⓪-ب الحركة ويومُ القرار (نقيّة · rows = [(يوم, o, h, l, c, v)] تصاعديًّا · مسوّاة) ═══════════════════════════════════════════
def find_events(rows, lo, hi, mult=2.0):
    """⟵ أحداثُ الزناد (أعلى الجلسة يبلغ `mult` × أدنى إغلاق العشرين قبلها) التي زنادُها في [lo، hi] · حدثٌ بعد حدث يبدأ بعد قمّة سابقه."""
    n = len(rows)
    days = [r[0] for r in rows]
    H, L, C = [r[2] for r in rows], [r[3] for r in rows], [r[4] for r in rows]
    out, i, floor = [], REF_WIN, -1                                # floor = قمّةُ الحدث السابق: الحدثُ التالي يلزمه قاعُ إغلاقٍ بعدها
    while i < n:
        if days[i] < lo:
            i += 1
            continue
        if days[i] > hi:
            break
        ref = min(C[i - REF_WIN:i])
        if ref > 0 and H[i] >= mult * ref:
            b = max(j for j in range(i - REF_WIN, i) if C[j] == ref)          # جلسةُ قاع الإغلاق (الأحدثُ عند التساوي)
            if b <= floor:                                                    # الحركةُ نفسُها (قاعُها قبل قمّة سابقتها) ⟵ ليست حدثًا جديدًا
                i += 1
                continue
            s = next((j for j in range(b + 1, i + 1)
                      if C[j - 1] > 0 and (C[j] >= START_C * C[j - 1] or H[j] >= START_H * C[j - 1])), b + 1)
            d = s - 1
            pe = min(n - 1, i + PEAK_AFTER)
            p = max(range(s, pe + 1), key=lambda j: (H[j], -j))               # أعلى High (الأبكرُ عند التساوي)
            low = min(L[b:s + 1])
            gov = (H[p] / C[d] - 1.0) if C[d] > 0 else None
            move = H[p] - C[d]
            big = max((H[j] - C[j - 1]) for j in range(s, p + 1))
            out.append({"t0": days[i], "b": days[b], "s": days[s], "D": days[d], "p": days[p], "close_D": C[d], "low": low, "top": H[p],
                        "gov": gov, "low_top": (H[p] / low - 1.0) if low > 0 else None, "sessions": p - s + 1,
                        "one_candle": bool(move > 0 and big / move >= ONE_CANDLE), "peak_open": pe == n - 1 and p == n - 1,
                        "ix": {"b": b, "s": s, "D": d, "p": p, "t0": i}})
            floor = p
            i = max(i, p) + 1
            continue
        i += 1
    return out


def event_class(ev):
    g = ev.get("gov")
    if g is None:
        return "غير مقيس"
    return "x100" if g >= X100 else ("x50" if g >= X50 else "دون")


def one_day(ev, rows):
    """بلغت الحاكمةُ حدَّ صنفها في جلسة البداية نفسِها."""
    thr = X100 if event_class(ev) == "x100" else X50
    s, d = ev["ix"]["s"], ev["ix"]["D"]
    return bool(rows[d][4] > 0 and rows[s][2] / rows[d][4] - 1.0 >= thr)


def window_of(ev):
    s = ev["s"]
    return "الشهر" if MONTH_FROM <= s <= WIN_TO else ("قبل الشهر" if WIN_FROM <= s < MONTH_FROM else "قبل النافذة")


def pick_events(rows):
    """⟵ (أحداثُ زناد الضعف، أحداثُ زناد 1.5× غيرُ المتداخلة معها) — لكلٍّ صنفُه بالحاكمة."""
    e2 = find_events(rows, WIN_FROM, WIN_TO, 2.0)
    spans = [(e["ix"]["b"], e["ix"]["p"]) for e in e2]
    e15 = [e for e in find_events(rows, WIN_FROM, WIN_TO, 1.5)
           if not any(a <= e["ix"]["s"] <= z or a <= e["ix"]["p"] <= z or (e["ix"]["b"] <= a and e["ix"]["p"] >= z) for a, z in spans)]
    return e2, e15


def unadjusted_splits(rows, splits, lo_ix, hi_ix):
    """⟵ التقسيماتُ (يوم، نسبةُ ياهو) التي يومُ تنفيذها في [lo_ix−5، hi_ix+5] وفجوةُ افتتاحه تطابق 1÷النسبة ضمن 20% = الشموعُ غيرُ مسوّاة به."""
    ix = {r[0]: k for k, r in enumerate(rows)}
    out = []
    for day, ratio in splits or []:
        k = ix.get(day)
        if k is None or k < 1 or not ratio or ratio <= 0 or not (lo_ix - SPLIT_NEAR <= k <= hi_ix + SPLIT_NEAR):
            continue
        pc = rows[k - 1][4]
        if pc <= 0:
            continue
        gap, want = rows[k][1] / pc, 1.0 / float(ratio)
        if abs(gap / want - 1.0) <= SPLIT_GAP_TOL and abs(want - 1.0) > 0.05:
            out.append((day, float(ratio)))
    return out


def apply_splits(rows, splits):
    """(نقيّة) تسويةُ شموعٍ غير مسوّاة: ما قبل يوم التنفيذ يُضرب سعرُه في 1÷النسبة ويُقسم حجمُه عليها."""
    out = [list(r) for r in rows]
    for day, ratio in splits:
        f = 1.0 / float(ratio)
        for r in out:
            if r[0] < day:
                r[1], r[2], r[3], r[4] = r[1] * f, r[2] * f, r[3] * f, r[4] * f
                r[5] = r[5] / f if f else r[5]
    return [tuple(r) for r in out]


def second_source(ev, rows2):
    """⟵ (نسبةُ إغلاق D، نسبةُ أعلى p، الحاكمةُ في المصدر الثاني) أو None إن غاب اليومان."""
    ix = {r[0]: r for r in rows2 or []}
    a, b = ix.get(ev["D"]), ix.get(ev["p"])
    if not a or not b or a[4] <= 0 or ev["close_D"] <= 0 or ev["top"] <= 0:
        return None
    return {"rD": a[4] / ev["close_D"], "rP": b[2] / ev["top"], "gov2": b[2] / a[4] - 1.0}


def drop_reason(ev, cls, rows, rows2, splits):
    """⟵ (سببُ الإسقاط أو None، وسمُ المصدر) بقواعد §⓪-ب (أ) (ب) (ج) بترتيبها."""
    un = unadjusted_splits(rows, splits, ev["ix"]["b"], ev["ix"]["p"])
    if un:
        fixed = apply_splits(rows, un)
        e2, e15 = pick_events(fixed)
        still = [event_class(e) for e in e2 + e15 if e["s"] == ev["s"] or e["D"] == ev["D"]]
        keep = ("x100" in still) if cls == "x100" else any(c in ("x100", "x50") for c in still)
        if not keep:
            return f"(أ) تقسيمٌ غيرُ مسوّى {un[0][0]} بنسبة {un[0][1]:g}", "مصدران"
    cmp_ = second_source(ev, rows2)
    if cmp_ is None:
        return None, "مصدرٌ واحد"
    if cls == "x100" and cmp_["gov2"] < X50:
        return f"(ج) الحاكمةُ في ياهو {cmp_['gov2'] * 100:.0f}% دون 50%", "مصدران"
    for k in ("rD", "rP"):
        if cmp_[k] > SRC_RATIO or cmp_[k] < 1.0 / SRC_RATIO:
            return f"(ب) المصدران يختلفان ×{cmp_[k]:.2f} في {'إغلاق D' if k == 'rD' else 'أعلى p'}", "مصدران"
    return None, "مصدران"


def rs_recent(splits, d_day):
    """تقسيمٌ عكسيّ (نسبةُ ياهو دون 1) خلال `RS_RECENT_DAYS` يومًا تقويميًّا حتى يوم القرار ⟵ (يوم، نسبة) أو None."""
    d0 = dt.date.fromisoformat(d_day)
    best = None
    for day, ratio in splits or []:
        if ratio and ratio < 1 and 0 <= (d0 - dt.date.fromisoformat(day)).days <= RS_RECENT_DAYS:
            best = (day, ratio) if best is None or day > best[0] else best
    return best


def news_type(text, items=""):
    """(نقيّة) نوعُ المحفّز من عنوانٍ أو بنود 8-K — أوّلُ مطابقة · وإلّا «غيره»."""
    t = " " + (text or "").lower() + " "
    for name, keys in KEYWORDS:
        if any(k in t for k in keys):
            return name
    for it in (items or "").split(","):
        if it.strip() in ITEM_TYPES:
            return ITEM_TYPES[it.strip()]
    return "غيره"


def catalyst(filings, news, days, s_ix):
    """⟵ {status: بخبر/بلا خبر/غير مقيس, type, items:[…], offer_after:[…]} · `filings` [(تاريخ, نموذج, بنود, وصف)] أو None · `news` [(تاريخ, عنوان)] أو None."""
    lo, hi = days[max(0, s_ix - NEWS_BEFORE)], days[s_ix]
    hi_off = days[min(len(days) - 1, s_ix + OFFER_AFTER)]
    hits, off = [], []
    for d, form, items, desc in filings or []:
        if lo <= d <= hi and form.startswith(NEWS_FORMS):
            hits.append({"d": d, "src": form, "t": (desc or "") + (f" [{items}]" if items else ""), "type": news_type(desc, items)})
        if hi < d <= hi_off and form.startswith(OFFER_FORMS):
            off.append({"d": d, "form": form})
    for d, title in news or []:
        if lo <= d <= hi:
            hits.append({"d": d, "src": "ياهو", "t": title, "type": news_type(title)})
    if filings is None and news is None:
        st = "غير مقيس"
    else:
        st = "بخبر" if hits else "بلا خبر"
    typ = next((h["type"] for h in hits if h["type"] != "غيره"), "غيره" if hits else None)
    return {"status": st, "type": typ, "items": hits[:6], "offer_after": off[:4], "partial": filings is None or news is None}


# ══ الجلب (على الرنر) ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
def git_symbols(since=GIT_FROM):
    """رموزُ كلّ لقطات `near_watch.json` و`weekly_watchlist.json` منذ `since` (قراءةُ تاريخ git)."""
    syms = set()
    for path in ("near_watch.json", "weekly_watchlist.json"):
        try:
            revs = subprocess.run(["git", "log", "--format=%H", f"--since={since}", "--", path], cwd=ROOT, capture_output=True,
                                  text=True, check=False).stdout.split()
        except OSError:
            revs = []
        for rev in revs:
            try:
                js = json.loads(subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True,
                                               check=False).stdout or "{}")
            except ValueError:
                continue
            if path == "near_watch.json":
                syms.update(k for k in js if isinstance(js.get(k), dict))
            else:
                for key in ("stocks", "pullback", "removed"):
                    syms.update(str(x.get("symbol")) for x in js.get(key) or [] if isinstance(x, dict) and x.get("symbol"))
    return {s.upper() for s in syms if s and s != "None"}


def tv_daily(symbols, n=TV_DAILY_N):
    """{رمز: rows} من مِقبس TradingView (يوميّ · نظاميّ · مسوّى بالتقسيم) · والمتعذّرُ غائب."""
    import Super_stock as S
    import tv_data as TV
    tmap = S._tv_ticker_map() or {}
    full = {s: tmap.get(s) or f"NASDAQ:{s}" for s in symbols}
    got = TV.fetch_many(sorted(set(full.values())), interval="1D", n=n, workers=6, retry_pass=True)
    out = {}
    for s, f in full.items():
        bars = got.get(f)
        if bars:
            out[s] = [(TV.ny_day(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4]), float(b[5] or 0.0)) for b in bars]
    return out, tmap


def yahoo_daily(sym):
    """شموعُ ياهو اليوميّة المسوّاة بالتقسيم (سنة) ⟵ rows أو None."""
    try:
        import yfinance as yf
        df = yf.Ticker(sym).history(period="1y", interval="1d", auto_adjust=False)
        if df is None or not len(df):
            return None
        return [(ix.date().isoformat(), float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"]), float(r["Volume"] or 0))
                for ix, r in df.iterrows() if r["Close"] == r["Close"]]
    except Exception:                                            # noqa: BLE001
        return None


def yahoo_splits(sym):
    """[(يوم, نسبة)] من ياهو أو None عند التعذّر."""
    try:
        import yfinance as yf
        sp = yf.Ticker(sym).splits
        return [(ix.date().isoformat(), float(v)) for ix, v in sp.items()] if sp is not None else None
    except Exception:                                            # noqa: BLE001
        return None


def yahoo_news(sym):
    """[(يوم, عنوان)] من ياهو (المتاحُ الحديث وحدَه) أو None."""
    try:
        import yfinance as yf
        out = []
        for it in yf.Ticker(sym).news or []:
            c = it.get("content") or it
            title = c.get("title")
            when = c.get("pubDate") or c.get("displayTime")
            if not when and it.get("providerPublishTime"):
                when = dt.datetime.fromtimestamp(int(it["providerPublishTime"]), tz=dt.timezone.utc).isoformat()
            if title and when:
                out.append((str(when)[:10], str(title)))
        return out
    except Exception:                                            # noqa: BLE001
        return None


_EDGAR = {}


def edgar_filings(sym):
    """[(تاريخ, نموذج, بنود, وصف)] من `submissions` (الأحدثُ أوّلًا) أو None (لا CIK أو تعذّر)."""
    if sym in _EDGAR:
        return _EDGAR[sym]
    import requests
    import Super_stock as S
    out = None
    cik = S.sec_cik_map().get(sym.upper())
    if cik:
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=S.SEC_UA, timeout=40)
            r.raise_for_status()
            rec = ((r.json().get("filings") or {}).get("recent")) or {}
            n = len(rec.get("form") or [])
            g = lambda k, i: ((rec.get(k) or [""] * n)[i] or "")  # noqa: E731
            out = [(g("filingDate", i), g("form", i).strip(), g("items", i), g("primaryDocDescription", i)) for i in range(n)]
        except Exception:                                        # noqa: BLE001
            out = None
        time.sleep(0.15)
    _EDGAR[sym] = out
    return out


# ══ ⓪ verify ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def pct(x):
    return "—" if x is None else f"{x * 100:.0f}%"


def verify_rows(sym, rows, rows2, splits, filings, news):
    """(نقيّة) صفوفُ جدول التحقّق لرمزٍ واحد من شموعه ومادّته."""
    e2, e15 = pick_events(rows)
    days = [r[0] for r in rows]
    out = []
    for ev, trig in [(e, 2.0) for e in e2] + [(e, 1.5) for e in e15]:
        cls = event_class(ev)
        why, src = (None, "—") if cls in ("دون", "غير مقيس") else drop_reason(ev, cls, rows, rows2, splits)
        rs = rs_recent(splits, ev["D"]) if splits is not None else None
        cat = catalyst(filings, news, days, ev["ix"]["s"])
        out.append({"sym": sym, "trig": trig, "cls": cls, "win": window_of(ev), "drop": why, "src": src,
                    **{k: ev[k] for k in ("b", "D", "s", "p", "close_D", "low", "top", "gov", "low_top", "sessions", "one_candle", "peak_open")},
                    "one_day": one_day(ev, rows), "rs_recent": rs, "rs_known": splits is not None, "cat": cat})
    return out


def best_effort(rows):
    """للرمز بلا حدث: أعلى High في النافذة ÷ أدنى إغلاقٍ قبله في النافذة (وصفٌ يشرح الغياب)."""
    w = [r for r in rows if WIN_FROM <= r[0] <= WIN_TO]
    if not w:
        return None
    best = None
    lo = None
    for r in w:
        if lo is not None and lo > 0:
            v = r[2] / lo - 1.0
            best = v if best is None or v > best else best
        lo = r[4] if lo is None or r[4] < lo else lo
    return best


def mode_verify():
    import Super_stock as S
    uni0 = {s.upper() for s in S.get_universe()}
    gsy = git_symbols()
    uni = sorted(uni0 | gsy | set(OWNER_LIST))
    log(f"🗂️ كونُ البوت: ناسداك {len(uni0)} · لقطاتُ git {len(gsy)} · قائمةُ المالك {len(OWNER_LIST)} ⟵ {len(uni)} رمزًا")
    bars, tmap = tv_daily(uni)
    miss = [s for s in uni if s not in bars]
    for s in [x for x in miss if x in OWNER_LIST or x in gsy][:400]:        # ياهو احتياطًا لما يهمّ
        r = yahoo_daily(s)
        if r:
            bars[s] = r
    log(f"📺 شموعٌ يوميّة: {len(bars)} من {len(uni)} · تعذّر {len(uni) - len(bars)}")
    if len(bars) < 0.5 * len(uni):
        log(f"⛔ التغطيةُ دون النصف — خروج {RC_DATA}")
        return RC_DATA
    cand = {}
    for s, rows in bars.items():
        if len(rows) <= REF_WIN + 1:
            continue
        e2, e15 = pick_events(rows)
        if s in OWNER_LIST or any(event_class(e) in ("x100", "x50") for e in e2 + e15):
            cand[s] = rows
    log(f"🔎 مرشّحون (حدثٌ حاكمتُه 50% فأكثر أو من قائمة المالك): {len(cand)}")
    table, absent = [], []
    for j, s in enumerate(sorted(cand)):
        rows = cand[s]
        rows2, splits = yahoo_daily(s), yahoo_splits(s)
        filings, news = edgar_filings(s), yahoo_news(s)
        got = verify_rows(s, rows, rows2, splits, filings, news)
        for g in got:
            g["owner"] = OWNER_LIST.get(s)
            g["tracked"] = s in gsy
        table += got
        if s in OWNER_LIST and not any(g["cls"] in ("x100", "x50") for g in got):
            absent.append({"sym": s, "owner": OWNER_LIST[s], "best": best_effort(rows), "bars": len(rows)})
        if j % 25 == 0:
            log(f"   … {j + 1}/{len(cand)}")
    for s in OWNER_LIST:
        if s not in bars:
            absent.append({"sym": s, "owner": OWNER_LIST[s], "best": None, "bars": 0})
    os.makedirs(OUT, exist_ok=True)
    payload = {"made": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "universe": len(uni), "bars": len(bars),
               "missing": len(uni) - len(bars), "candidates": len(cand), "table": table, "absent": absent,
               "contract_sha": CONTRACT_SHA, "catalog_sha": CATALOG_SHA}
    with open(os.path.join(OUT, "verify.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    md = verify_md(payload)
    with open(os.path.join(OUT, "VERIFY.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    return RC_OK


def _row_md(g):
    c = g["cat"]
    kinds = " · ".join([("يومٌ واحد" if g["one_day"] else f"{g['sessions']} جلسات"), ("شمعةٌ واحدة" if g["one_candle"] else "موجات"),
                        ("بعد تقسيمٍ عكسيّ " + g["rs_recent"][0] if g["rs_recent"] else ("لا تقسيمَ حديث" if g["rs_known"] else "التقسيم غير مقيس"))])
    news = c["status"] + (f" ({c['type']})" if c.get("type") else "") + (" ⚠️جزئيّ" if c.get("partial") and c["status"] != "غير مقيس" else "")
    return (f"| {g['sym']} | {g['owner'] if g.get('owner') is not None else '—'} | {g['win']} | {g['D']} | {g['s']} | {g['p']} | "
            f"{g['close_D']:.4g} | {g['low']:.4g} | {g['top']:.4g} | **{pct(g['gov'])}** | {pct(g['low_top'])} | {kinds} | {news} | "
            f"{g['src']}{' · القمّةُ قد لا تكون اكتملت' if g.get('peak_open') else ''} |")


def verify_md(P):
    T = P["table"]
    head = ("| السهم | نسبةُ المالك | النافذة | يوم القرار | البداية | القمّة | إغلاق القرار | القاع | القمّة$ | الحاكمة | قاع⟵قمّة | النوع | "
            "المحفّز | المصدر |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    keep = [g for g in T if not g["drop"]]
    x100 = [g for g in keep if g["cls"] == "x100" and g["win"] != "قبل النافذة"]
    x50 = [g for g in keep if g["cls"] == "x50" and g["win"] != "قبل النافذة"]
    dropped = [g for g in T if g["drop"]]
    owner100 = sorted({g["sym"] for g in x100 if g.get("owner") is not None})
    owner50 = sorted({g["sym"] for g in x50 if g.get("owner") is not None} - set(owner100))
    L = ["# 🗂️ `T-CASE31` ⓪ — جدولُ التحقّق من القائمة وأنواعُ الانفجار (مولَّدٌ آليًّا · لا يُعدَّل باليد)", "",
         f"- الكون {P['universe']:,} رمزًا · بشموعٍ يوميّة {P['bars']:,} · تعذّر {P['missing']:,} · مرشّحون {P['candidates']:,} · صُنع {P['made']}",
         f"- **منفجرو ‏+100% (الحاكمة = أعلى القمّة ÷ إغلاق يوم القرار − 1):** {len(x100)} حدثًا — في «الشهر» "
         f"{sum(1 for g in x100 if g['win'] == 'الشهر')} · «قبل الشهر» {sum(1 for g in x100 if g['win'] == 'قبل الشهر')}",
         f"- من قائمة المالك (31): ‏+100% {len(owner100)} · ذراع ‏+50% {len(owner50)} · مُسقَط "
         f"{len({g['sym'] for g in dropped if g.get('owner') is not None})} · بلا حدثٍ بتعريف العقد {len(P['absent'])}",
         f"- مُكمَّلٌ من الكون (ليس في القائمة): ‏+100% {len({g['sym'] for g in x100 if g.get('owner') is None})} رمزًا · "
         f"ذراع ‏+50% {len({g['sym'] for g in x50 if g.get('owner') is None})} رمزًا", ""]
    for title, rows_ in (("## ① قائمةُ المالك — ‏+100% بتعريف العقد", [g for g in x100 if g.get("owner") is not None]),
                         ("## ② قائمةُ المالك — ذراع ‏+50% (الحاكمة بين 50% و100%)", [g for g in x50 if g.get("owner") is not None]),
                         ("## ③ مُكمَّلٌ من كون البوت — ‏+100%", [g for g in x100 if g.get("owner") is None]),
                         ("## ④ مُكمَّلٌ من كون البوت — ذراع ‏+50%", [g for g in x50 if g.get("owner") is None])):
        L += [title, "", head] + [_row_md(g) for g in sorted(rows_, key=lambda g: (g["win"], g["s"], g["sym"]))] + [""]
    L += ["## ⑤ المُسقَطون (تقسيمٌ أو خطأ بيانات) بأسبابهم", "", "| السهم | نسبةُ المالك | يوم القرار | القمّة | الحاكمة قبل الإسقاط | السبب |",
          "|---|---|---|---|---|---|"]
    L += [f"| {g['sym']} | {g['owner'] if g.get('owner') is not None else '—'} | {g['D']} | {g['p']} | {pct(g['gov'])} | {g['drop']} |"
          for g in sorted(dropped, key=lambda g: g["sym"])] + [""]
    L += ["## ⑥ من قائمة المالك بلا حدثٍ بتعريف العقد", "", "| السهم | نسبةُ المالك | أكبرُ (أعلى ÷ أدنى إغلاقٍ قبله) في النافذة | الشموع |", "|---|---|---|---|"]
    L += [f"| {a['sym']} | {a['owner']} | {pct(a['best'])} | {a['bars']} |" for a in sorted(P["absent"], key=lambda a: a["sym"])] + [""]
    ev = [g for g in x100 if g["win"] == "الشهر"]
    if ev:
        n = len(ev)
        cnt = lambda f: sum(1 for g in ev if f(g))                 # noqa: E731
        L += ["## ⑦ أنواعُ منفجري «الشهر» (‏+100%)", "",
              f"- بخبر {cnt(lambda g: g['cat']['status'] == 'بخبر')} · بلا خبر {cnt(lambda g: g['cat']['status'] == 'بلا خبر')} · "
              f"غير مقيس {cnt(lambda g: g['cat']['status'] == 'غير مقيس')} من {n}",
              f"- يومٌ واحد {cnt(lambda g: g['one_day'])} · عدّة أيام {n - cnt(lambda g: g['one_day'])}",
              f"- شمعةٌ واحدة {cnt(lambda g: g['one_candle'])} · موجات {n - cnt(lambda g: g['one_candle'])}",
              f"- بعد تقسيمٍ عكسيّ حديث {cnt(lambda g: bool(g['rs_recent']))} · لا {cnt(lambda g: g['rs_known'] and not g['rs_recent'])} · "
              f"غير مقيس {cnt(lambda g: not g['rs_known'])}",
              f"- أودع طرحًا خلال {OFFER_AFTER} جلسات بعد البداية (وصف): {cnt(lambda g: bool(g['cat']['offer_after']))} من {n}", ""]
    return "\n".join(L) + "\n"


def main(argv):
    if not contract_ok():
        log(f"⛔ العقدُ أو فهرسُ السمات لا يطابق بصمتَه — خروج {RC_CONTRACT}")
        return RC_CONTRACT
    if os.environ.get("POLYGON_API_KEY"):
        os.environ.pop("POLYGON_API_KEY")                         # العقد §⓪-أ: لا Polygon في أيّ مسار
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "verify":
        return mode_verify()
    log("الاستعمال: case31.py verify")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
