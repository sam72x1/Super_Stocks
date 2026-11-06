#!/usr/bin/env python3
"""🚪📏 `T-RRGATE` — «بوّابة العائد/المخاطرة وطردُ OMH» (العقد `fm_forensics/rrgate/RRGATE_prereg.md` · مدموجٌ قبل أيّ رقم · #752).

الأوضاع (§⑦):
  local         (محلّيّ · تاريخُ git) أحداثُ ① وآليّتُها وسطرُ قاعدتها ⟵ `data/nw_events.json` · و② الراكضون وفئاتُهم مقابل الأساس.
  nw            (الرنر · Polygon) ① الركضُ بعد الخروج · السببُ الأدقّ بإعادة القياس · وبوّابةُ الصدق على الباقين المقيسين.
  pre           (الرنر · Polygon) ④ OMH وCHSN والجلساتُ الخمس قبل كلٍّ · والـ248 · وعيّنةُ الأساس.
  pit_prep · pit_shard · pit_assemble  (الرنر) ③ ثلاثُ سنوات PIT بآلة `T-REBUILD`/`T-SPLITGATES` بالاسم.
🔒 قراءةٌ فقط · لا تلغرام · لا تغييرَ على البوّابة ولا على «تحت المتابعة» · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import bisect
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "RRGATE_prereg.md")
CONTRACT_SHA = "45040d0d33b7b5959c11ed5a2203d90c80752ef140f47cb3d076af5dc4a505c9"
CONTRACT_RC = 9
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
RUNNERS = os.path.join(HERE, "data", "runners_60.json")
EVENTS = os.path.join(HERE, "data", "nw_events.json.gz")
OUT = os.path.join(HERE, "out")
RR_LABEL = "العائد/المخاطرة (دون الحدّ)"         # `near_watch_outside` لمعيار `rr` (جهة lo)
CATS = ("داخلَ الظرف", "العائد/المخاطرة وحدَه", "RSI", "غيرهما")
STALE_DAYS = 10                                    # = `Super_stock.NEAR_WATCH_STALE_DAYS` (§① «تقادم»)
RUN_PCT, RUN_WIN = 50.0, 10                        # §① «+50% خلال 10 جلسات»
EXP_PCT, EXP_WIN = 50.0, 20                        # §③ «+50% في 20 جلسة»
AGREE_MIN = 0.80                                   # §① بوّابةُ صدق إعادة القياس
FLOOR_CAT = 20                                     # §② فئةٌ دون 20 راكضًا «لا قياس»
B_FLOOR = 30                                       # §③ أرضيّةُ B لكلّ سنة
COVER_MIN = 0.85                                   # §③ تغطيةُ الشموع
SAMPLE_N, SAMPLE_SEED = 1000, "RRG4"               # §④ عيّنةُ الأساس
PRE_FROM, PRE_END = 4 * 60, 9 * 60 + 30            # §④ 04:00-09:29 نيويورك
FAIL_MAX = 0.05                                    # §④ دقائقُ متعذّرة فوق 5% ⟵ «لا قياس»
PIT_SEED = 20261106                                # §③ `cluster_boot`
NSHARDS = 20
PIT_SESS = ("2023-01-03", "2025-12-31")
HIGH_WIN = 320                                     # مرشِّحٌ مسبقٌ سوبرست: قمّةُ 320 جلسة ≥ قمّةِ 252 (`analyze_ticker` ‏`hi52`)
AUDIT_P = 0.01                                     # فحصُ السوبرست: 1% من المُستبعَدين يُقاس فعلًا
NW_FROM = "2024-06-01"                             # §① شموعُ إعادة القياس: 800 يوم قبل أوّل جلسة (2026-08-12)
WORKERS = 8
PRE_EVENTS = (("OMH", "2026-11-04"), ("CHSN", "2026-11-03"))
RULES = {   # الآليّة ⟵ (نصٌّ يحدّد سطرَها في `Super_stock.py` وقتَ التشغيل · اسمُ القاعدة)
    "رُقّي": ("for _r in results:", "`scan_market`: المرشَّحُ يُحذف من «تحت المتابعة»"),
    "قِيس فخرج": ("for _s in (_nw_meas - set(_nw_new)):",
                 "`scan_market`: قِيس اليومَ ولم يتأهّل (`near_watch_founded` · `NEAR_WATCH_MAX_OUT`=2)"),
    "تقادم": ("def near_watch_prune(", "`near_watch_prune`: غاب عن القياس أكثرَ من `NEAR_WATCH_STALE_DAYS`=10 أيّام"),
}


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _mod(name, rel):
    """وحدةٌ بحثيّةٌ من مسارها (بالاسم · لا نسخة)."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, *rel.split("/")))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _rebuild():
    return _mod("rrgate_rebuild", "fm_forensics/rebuild/rebuild.py")


def _split_gates():
    return _mod("rrgate_split_gates", "fm_forensics/split_gates/split_gates.py")


def _S():
    """`Super_stock` بأرقام الإنتاج الحيّة (`FAISAL_ONLY=1` · الظرفُ يُحمَّل نسبةً إلى ROOT)."""
    os.environ["FAISAL_ONLY"] = "1"
    os.chdir(ROOT)
    import Super_stock as S
    return S


def _days_between(a, b):
    try:
        return (dt.date.fromisoformat(str(b)[:10]) - dt.date.fromisoformat(str(a)[:10])).days
    except ValueError:
        return 10 ** 6


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def _p(x):
    return "—" if x is None else f"{x * 100:.1f}%"


# ── نقيّة (مقفولةٌ في السويّة) ──────────────────────────────────────────────────────────────────────────
def category(outside):
    """§② فئاتٌ متنافية بالترتيب: داخلَ الظرف · العائد/المخاطرة وحدَه · RSI (قاعُه أو الآن) · غيرهما."""
    o = [str(x) for x in (outside or [])]
    if not o:
        return CATS[0]
    if o == [RR_LABEL]:
        return CATS[1]
    if any(x.startswith("RSI") for x in o):
        return CATS[2]
    return CATS[3]


def mechanism(old, screen, promoted):
    """§① آليّةُ الخروج بالترتيب: «رُقّي» (ظهر في القائمة ولم يكن فيها) · «تقادم» (last_seen أقدمُ من 10 أيّام) · «قِيس فخرج»."""
    if promoted:
        return "رُقّي"
    if _days_between((old or {}).get("last_seen") or "", screen) > STALE_DAYS:
        return "تقادم"
    return "قِيس فخرج"


def rule_line(mech, path=None):
    """رقمُ سطر القاعدة في `Super_stock.py` وقتَ التشغيل (بنصّها لا بثابت) ⟵ int أو None."""
    path = path or os.path.join(ROOT, "Super_stock.py")
    with open(path, encoding="utf-8") as f:
        for i, ln in enumerate(f, 1):
            if RULES[mech][0] in ln:
                return i
    return None


def compare_verdict(k_run, n_run, k_base, n_base, floor=FLOOR_CAT):
    """§② «أكثرُ تمثيلًا» · «أقلّ» · «لا فرق» · «لا قياس» (الفئةُ دون `floor` راكضًا) — بعدم تداخل Wilson."""
    if k_run < floor:
        return "لا قياس"
    a, b = wilson(k_run, n_run), wilson(k_base, n_base)
    if None in a or None in b:
        return "لا قياس"
    if a[0] > b[1]:
        return "أكثرُ تمثيلًا"
    if a[1] < b[0]:
        return "أقلّ"
    return "لا فرق"


def run_after(rows, d, pct=RUN_PCT, win=RUN_WIN):
    """§① ⟵ (ركض؟، مكتمل؟): `rebuild.exploded` بالاسم للنافذة الكاملة · والناقصةُ «ركض قبل اكتمالها» (True، False) أو (None، False)."""
    y = _rebuild().exploded(rows, d, pct, win)
    if y is not None:
        return bool(y), True
    i = next((k for k, x in enumerate(rows) if x[0] >= d), None)
    if i is None or i < 1:
        return None, False
    ref, fut = rows[i - 1][4], rows[i:i + win]
    if ref and fut and max(x[2] for x in fut) >= ref * (1 + pct / 100.0):
        return True, False
    return None, False


def split_in_window(rows, splits, d, win=RUN_WIN):
    """§① تقسيمٌ منفَّذٌ في (آخر جلسةٍ قبل d، d+win−1] ⟵ يُستبعَد ويُعَدّ."""
    i = next((k for k, x in enumerate(rows) if x[0] >= d), None)
    if i is None or i < 1:
        return False
    lo, hi = rows[i - 1][0], rows[min(i + win - 1, len(rows) - 1)][0]
    return any(lo < str(s[0]) <= hi for s in splits or ())


def build_events(U, docs_of, prev0):
    """§① ⟵ (أحداثُ الخروج، الباقون) — نقيّة على المُدخلات · `docs_of(commit)` ⟵ near_watch.json · `prev0` = {N_commit · L} قبل أوّل جلسة."""
    def norm(doc):
        return {str(k).upper(): v for k, v in (doc or {}).items() if isinstance(v, dict)}
    seq = [prev0] + [U["days"][d] for d in U["sessions"]]
    events, stayers = [], []
    for d, a_inf, b_inf in zip(U["sessions"], seq, seq[1:]):
        a, b = norm(docs_of(a_inf.get("N_commit"))), norm(docs_of(b_inf.get("N_commit")))
        screen = max((str(v.get("last_seen") or "") for v in b.values()), default="")
        La, Lb = set(a_inf.get("L") or {}), set(b_inf.get("L") or {})
        for s in sorted(set(a) - set(b)):
            old = a[s]
            events.append({"sym": s, "day": d, "screen": screen, "mech": mechanism(old, screen, s in Lb and s not in La),
                           "old": {k: old.get(k) for k in ("first_seen", "last_seen", "n_out", "outside")},
                           "v_old": a_inf.get("N_commit"), "v_new": b_inf.get("N_commit")})
        for s in sorted(set(a) & set(b)):
            e = b[s]
            stayers.append({"sym": s, "day": d, "outside": list(e.get("outside") or []),
                            "measured": str(e.get("last_seen") or "") == screen,
                            "mkey": hashlib.sha256(json.dumps(e, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]})
    return events, stayers


def agreement_set(stayers):
    """§① الباقون المقيسون في فرز إصدارهم · قياسٌ واحدٌ لكلّ مدخلٍ متطابق (أوّلُ جلسةٍ يظهر فيها ⟵ شموعُها حتى ما قبلها)."""
    seen, out = set(), []
    for s in stayers:
        if s["measured"] and (s["sym"], s["mkey"]) not in seen:
            seen.add((s["sym"], s["mkey"]))
            out.append(s)
    return out


def runners_table(U, R, docs_of):
    """§② لكلّ راكض: في N؟ في L؟ وفئةُ مدخله عشيّةَ ركضه · والأساسُ: كلُّ (رمز، يوم) في N غيرِ راكضٍ بـ‏+50%."""
    cache = {}

    def doc(h):
        if h not in cache:
            cache[h] = {str(k).upper(): v for k, v in (docs_of(h) or {}).items() if isinstance(v, dict)}
        return cache[h]
    run50 = {(r["sym"], r["day"]): r for r in R["rows"]}
    rows, base = [], []
    for (s, d), r in sorted(run50.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        day = U["days"].get(d) or {}
        inN, inL = s in set(day.get("N") or ()), s in set(day.get("L") or {})
        e = doc(day.get("N_commit")).get(s) if inN else None
        rows.append({"sym": s, "day": d, "R": r["R"], "inN": inN, "inL": inL,
                     "cat": category((e or {}).get("outside")) if inN else None,
                     "rr_any": (RR_LABEL in ((e or {}).get("outside") or [])) if inN else None})
    for d in U["sessions"]:
        day = U["days"][d]
        dd = doc(day.get("N_commit"))
        for s in day.get("N") or ():
            if (s, d) not in run50:
                e = dd.get(s) or {}
                base.append({"sym": s, "day": d, "cat": category(e.get("outside")), "rr_any": RR_LABEL in (e.get("outside") or [])})
    return rows, base


def runners_lines(rows, base):
    out, verdicts = [], {}
    nb = len(base)
    for lab, sub in (("+50%", rows), ("+100%", [r for r in rows if r["R"] >= 1.0])):
        inN = [r for r in sub if r["inN"]]
        out.append(f"### الراكضون {lab}: {len(sub)} · في «تحت المتابعة» عشيّةَ ركضهم **{len(inN)}** ({_p(len(inN) / len(sub) if sub else None)}) · "
                   f"في القائمة {sum(1 for r in sub if r['inL'])} · في الاثنين {sum(1 for r in sub if r['inL'] and r['inN'])}")
        out += ["", f"| الفئة ({lab}) | الراكضون في N | الحصة [Wilson] | الأساس: غيرُ الراكضين في N ({nb}) | الحصة [Wilson] | الحكم |",
                "|---|---|---|---|---|---|"]
        for c in CATS + ("العائد/المخاطرة ضمن الخارج (وصفًا)",):
            if c in CATS:
                k, kb = sum(1 for r in inN if r["cat"] == c), sum(1 for b in base if b["cat"] == c)
            else:
                k, kb = sum(1 for r in inN if r["rr_any"]), sum(1 for b in base if b["rr_any"])
            w, wb = wilson(k, len(inN)), wilson(kb, nb)
            v = compare_verdict(k, len(inN), kb, nb) if (c in CATS and lab == "+50%") else "وصفًا"
            if lab == "+50%" and c in CATS:
                verdicts[c] = v
            out.append(f"| {c} | {k} | {_p(k / len(inN) if inN else None)} [{_p(w[0])}، {_p(w[1])}] | {kb} | "
                       f"{_p(kb / nb if nb else None)} [{_p(wb[0])}، {_p(wb[1])}] | **{v}** |")
        out.append("")
    return out, verdicts


def premarket_stats(bars, prev_close):
    """§④ (الحجمُ الدولاريّ 04:00-09:29، الفجوةُ عند آخر دقيقةٍ قبل 09:30، عددُ الدقائق) — bars = [(دقيقة، o، h، l، c، v)]."""
    pre = [b for b in bars or () if PRE_FROM <= b[0] < PRE_END]
    usd = sum(b[4] * b[5] for b in pre)
    gap = (pre[-1][4] / prev_close - 1.0) if (pre and prev_close) else None
    return usd, gap, len(pre)


def simulate_s(S, KS, ny_ts, day, bars, prev_close):
    """§④ «لو كان في الكون»: `kasih_scan.first_anchor` بالاسم على دقائق 04:00-09:29 ⟵ المرساة · J1 بنمط `target10_arms` (`f2_usd5` ⟵
    `_ignition_candle_class` ⟵ `kasih_j1`) و«لم يكتمل» إن لم تكتمل خمسُ دقائق M5 قبل 09:30 · وS = `shadow_flag` بسلّة `_bucket` ⟵ dict أو None."""
    import shadow_ready as SR
    from tierlink_probe import _bucket
    pre = [b for b in bars or () if PRE_FROM <= b[0] < PRE_END]
    rows = [(int(ny_ts(day, b[0]) * 1000), b[1], b[2], b[3], b[4], b[5]) for b in pre]
    e = KS.first_anchor(rows) if rows else None
    if not e:
        return None
    a_ms, ap = int(e["anchor_ms"]), float(e["price"])
    gp = (ap / prev_close - 1.0) * 100.0 if (ap and prev_close) else None
    j1 = None
    if prev_close and a_ms + int(KS.ENTRY5_MIN) * 60_000 <= int(ny_ts(day, PRE_END) * 1000):
        f2 = S._ignition_candle_class(KS.f2_usd5(rows, a_ms))[0]
        j1 = bool(S.kasih_j1({"stage": "M5", "class": (f2, ""), "anchor_price": ap, "prev_close": prev_close})[0])
    f = {"tod": "pre", "j1": "J1" if j1 else ("لا" if j1 is not None else "؟"), "gap": _bucket(gp, (10, 30), ("<10%", "10-30%", "≥30%"))}
    return {"anchor_ms": a_ms, "anchor_px": ap, "gap_pct": gp, "j1": j1, "S": bool(SR.shadow_flag(f))}


def arm_of(founded, outside):
    """§③ A «عبر كلَّه» = منهارٌ ∧ الخارجُ فارغ · B «إلّا العائد/المخاطرة» = منهارٌ ∧ الخارجُ = العائد/المخاطرة وحدَه · وإلّا None."""
    if not founded:
        return None
    o = list(outside or [])
    if not o:
        return "A"
    if o == [RR_LABEL]:
        return "B"
    return None


def cheap_drop(rows, i, win=HIGH_WIN):
    """§③ مرشِّحٌ مسبق: (1 − إغلاق D−1 ÷ أعلى High في `win` جلسةً قبل D) × 100 — حدٌّ أعلى لهبوط `analyze_ticker` (‏`win` ≥ 252 · والمقياسُ لا يغيّر النسبة)."""
    w = rows[max(0, i - win):i]
    if not w:
        return None
    hi = max(x[2] for x in w)
    return None if hi <= 0 else (1.0 - w[-1][4] / hi) * 100.0


def ret20(rows, i):
    if i < 21:
        return None
    a, b = rows[i - 21][4], rows[i - 1][4]
    return None if not a else b / a - 1.0


def _df(rows):
    import pandas as pd
    return pd.DataFrame({"Open": [x[1] for x in rows], "High": [x[2] for x in rows], "Low": [x[3] for x in rows],
                         "Close": [x[4] for x in rows], "Volume": [x[5] for x in rows]}, index=pd.to_datetime([x[0] for x in rows]))


def measure_at(S, sym, rows, splits, d, edges, lookback=None):
    """آلةُ «تحت المتابعة» بالاسم على الشموع قبل D بمقياس D−1 (`rebuild.asof_scale`) وآخرِ 800 يوم ⟵ (منهار؟، الخارج، القيم) أو None."""
    R = _rebuild()
    lb = R.HISTORY_DAYS if lookback is None else lookback
    lo = (dt.date.fromisoformat(d) - dt.timedelta(lb)).isoformat()
    sub = [x for x in R.asof_scale(rows, splits, d) if x[0] >= lo]
    if len(sub) < 60:
        return None
    m = S.near_watch_measure(sym, _df(sub), edges)
    if not m:
        return None
    return bool(S.near_watch_founded(m[0], edges)), list(m[1]), m[0]


# ── local: ① الأحداث · ② الراكضون ───────────────────────────────────────────────────────────────────────
def _count(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return out


def _git_json(h, path):
    if not h:
        return None
    p = subprocess.run(["git", "show", f"{h}:{path}"], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return None
    try:
        return json.loads(p.stdout)
    except ValueError:
        return None


def eligible_by_screen(path=None):
    """وصفًا لا آليّةَ عقد: مؤهَّلو كلِّ فرزٍ (`results`) من `fill_pool_log.jsonl` (منذ 2026-10-09) ⟵ {تاريخ الفرز: {رمز: نتيجةُ التعبئة}} ·
    والمؤهَّلُ يُحذف من «تحت المتابعة» بسطر `:14872` سواءٌ أُضيف إلى القائمة أم حجبته بوّابةٌ بعدها (DQ_HELD · BORROW_REJECT · …)."""
    path = path or os.path.join(ROOT, "fill_pool_log.jsonl")
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                cols = list(r.get("cols") or [])
                io = cols.index("outcome") if "outcome" in cols else None
                day = out.setdefault(str(r.get("date") or "")[:10], {})
                for x in r.get("rows") or ():
                    if x:
                        day[str(x[0]).upper()] = (x[io] if io is not None and io < len(x) else None) or "؟"
    except OSError:
        pass
    return out


def mode_local():
    import market_calendar as MC
    import gcross_runner as GR                                       # بالاسم: _commits · asof · list_members · CUTOFF_NY_MIN
    U, R = _load(UNIVERSE), _load(RUNNERS)
    d0 = dt.date.fromisoformat(U["sessions"][0]) - dt.timedelta(1)
    while not GR.V3.is_session(d0.isoformat(), MC.session_info):
        d0 -= dt.timedelta(1)
    ts0 = int(GR.V3.ny_ts(d0.isoformat(), GR.CUTOFF_NY_MIN))
    hn, hw = GR.asof(GR._commits("near_watch.json"), ts0), GR.asof(GR._commits("weekly_watchlist.json"), ts0)
    prev0 = {"N_commit": hn, "L": GR.list_members(_git_json(hw, "weekly_watchlist.json"))}
    cache = {}

    def docs_of(h):
        if h not in cache:
            cache[h] = _git_json(h, "near_watch.json")
        return cache[h]
    events, stayers = build_events(U, docs_of, prev0)
    elig = eligible_by_screen()
    for e in events:
        es = elig.get(e["screen"])
        e["eligible"] = None if es is None else (e["sym"] in es)
        e["fp_outcome"] = None if es is None else es.get(e["sym"])
    os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
    blob = json.dumps({"sessions": U["sessions"], "prev0": [d0.isoformat(), hn, hw], "events": events, "stayers": stayers},
                      ensure_ascii=False, sort_keys=True).encode("utf-8")
    with open(EVENTS, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:   # حتميٌّ بايتًا (بلا طابع زمن)
        gz.write(blob)
    log(f"# 🚪📏 `T-RRGATE` — المحلّيّ (① الأحداث · ② الراكضون) · الإصداراتُ {len(U['sessions']) + 1} ({d0.isoformat()} ⟵ {U['sessions'][-1]})")
    log("")
    log("## ① لماذا خرج OMH؟")
    omh = [e for e in events if e["sym"] == "OMH"]
    for e in omh:
        log(f"- **{e['day']}** (فرزُ {e['screen']} · `{str(e['v_old'])[:9]}` ⟵ `{str(e['v_new'])[:9]}`): first_seen {e['old']['first_seen']} · "
            f"last_seen {e['old']['last_seen']} · n_out {e['old']['n_out']} · الخارج {e['old']['outside']}")
        log(f"  ⟵ **«{e['mech']}»** — {RULES[e['mech']][1]} · `Super_stock.py:{rule_line(e['mech'])}` · ومؤهَّلٌ في سجلّ بِركة التعبئة يومَ فرزه: "
            f"{'غائبٌ عن السجلّ' if e['eligible'] is None else ('نعم — نتيجةُ التعبئة ' + str(e['fp_outcome']) if e['eligible'] else 'لا')}")
        if e["eligible"]:
            log(f"  ⚠️ **بالكود:** مؤهَّلٌ يومَ فرزه ⟵ حُذف من «تحت المتابعة» بسطر `Super_stock.py:{rule_line('رُقّي')}` (`for _r in results:`) "
                f"ولم يُضَف إلى القائمة ({e['fp_outcome']}) ⟵ **ليس العائدُ/المخاطرة** · وآليّةُ العقد (§① «رُقّي» = ظهر في القائمة) تسمّيه «{e['mech']}»")
    if not omh:
        log("- ⛔ OMH لم يخرج في الإصدارات الستّين")
    by = {}
    for e in events:
        by[e["mech"]] = by.get(e["mech"], 0) + 1
    ms = [e for e in events if e["mech"] == "قِيس فخرج"]
    log(f"\n**أحداثُ الخروج في الستّين:** {len(events)} · " + " · ".join(f"{k} {v}" for k, v in sorted(by.items())) +
        f" · ومن «قِيس فخرج» مؤهَّلٌ يومَ فرزه في سجلّ البِركة (وصفًا · السجلُّ منذ 10-09): "
        f"{sum(1 for e in ms if e['eligible'])} من {sum(1 for e in ms if e['eligible'] is not None)} (" +
        " · ".join(f"{k} {v}" for k, v in sorted(_count(e["fp_outcome"] for e in ms if e["eligible"]).items(), key=lambda kv: -kv[1])) + ") · "
        f"الباقون (رمز-جلسة) {len(stayers)} · المقيسون للاتّفاق {len(agreement_set(stayers))}")
    log("")
    log("## ② الراكضون عشيّةَ ركضهم")
    rows, base = runners_table(U, R, docs_of)
    lines, verdicts = runners_lines(rows, base)
    for ln in lines:
        log(ln)
    log("RRG_LOCAL_JSON " + json.dumps({"events": len(events), "by_mech": by, "stayers": len(stayers), "omh": omh,
                                        "runners50": len(rows), "inN50": sum(1 for r in rows if r["inN"]),
                                        "runners100": sum(1 for r in rows if r["R"] >= 1.0),
                                        "inN100": sum(1 for r in rows if r["R"] >= 1.0 and r["inN"]), "base": len(base),
                                        "verdicts": verdicts}, ensure_ascii=False, default=str))
    return 0


# ── nw: ① الركضُ · السببُ الأدقّ · بوّابةُ الصدق ────────────────────────────────────────────────────────────
def _splits_by(a, b, key):
    import pit_snapshot as PS
    by = {}
    for r in PS.fetch_all_splits(a, b, key):
        try:
            by.setdefault(str(r["ticker"]).upper(), []).append((str(r["execution_date"]), float(r["split_to"]) / float(r["split_from"])))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    for v in by.values():
        v.sort()
    return by


def _bars_many(syms, a, b, key):
    import pit_history as PH
    R = _rebuild()

    def one(s):
        df, why = PH.polygon_daily(s, a, b, key)
        return s, (R._rows(df) if df is not None else []), why.split("(")[0]
    out, diag = {}, {}
    with ThreadPoolExecutor(WORKERS) as ex:
        for n, (s, rows, why) in enumerate(ex.map(one, syms)):
            out[s] = rows
            diag[why] = diag.get(why, 0) + 1
            if n % 250 == 0:
                log(f"bars {n + 1}/{len(syms)} · {diag}")
    return out, diag


def nw_cause(m):
    if m is None:
        return None
    if not m[0]:
        return "لم ينهَر"
    if len(m[1]) > 2:
        return "خارج الظرف في 3 فأكثر"
    return "يتأهّل بإعادة القياس"


def mode_nw(key):
    import envelope_scan as EV
    S = _S()
    with gzip.open(EVENTS, "rt", encoding="utf-8") as f:
        E = json.load(f)
    edges = EV.load_edges() or {}
    log(f"🧾 FAISAL_ONLY={S.CONFIG.get('FAISAL_ONLY')} · حافّةُ rr {edges.get('rr')} · حافّةُ drop_pct {edges.get('drop_pct')}")
    agree_set = agreement_set(E["stayers"])
    syms = sorted({e["sym"] for e in E["events"]} | {s["sym"] for s in E["stayers"]})
    end = dt.date.today().isoformat()
    sp = _splits_by(NW_FROM, end, key)
    bars, diag = _bars_many(syms, NW_FROM, end, key)
    log(f"شموعٌ لـ{len(syms)} رمزًا: {diag} · تقسيماتٌ لـ{len(sp)}")
    agree = tot = 0
    mism = {}
    for s in agree_set:
        m = measure_at(S, s["sym"], bars.get(s["sym"]) or [], sp.get(s["sym"]), s["day"], edges)
        if m is None:
            continue
        tot += 1
        ok = set(m[1]) == set(s["outside"])
        agree += int(ok)
        if not ok:
            for x in set(m[1]) ^ set(s["outside"]):
                mism[x] = mism.get(x, 0) + 1
    rate = agree / tot if tot else None
    ok_cause = rate is not None and rate >= AGREE_MIN
    ev_rows = []
    for e in E["events"]:
        rws = bars.get(e["sym"]) or []
        m = measure_at(S, e["sym"], rws, sp.get(e["sym"]), e["day"], edges) if e["mech"] == "قِيس فخرج" else None
        excl = (not rws) or split_in_window(rws, sp.get(e["sym"]), e["day"])
        hit, full = (None, False) if excl else run_after(rws, e["day"])
        vals = None if m is None else {k: m[2].get(k) for k in ("price", "drop_pct", "best_spike", "rr", "rsi_now", "rsi_min", "dollar_vol")}
        ev_rows.append(dict(e, cause=nw_cause(m), remeasured=None if m is None else m[1], vals=vals, hit=hit, full=full, excl=bool(excl)))
    st_k = st_n = 0
    for s in E["stayers"]:
        rws = bars.get(s["sym"]) or []
        if not rws or split_in_window(rws, sp.get(s["sym"]), s["day"]):
            continue
        hit, full = run_after(rws, s["day"])
        if full:
            st_n += 1
            st_k += int(bool(hit))
    log("# 🚪📏 `T-RRGATE` ① — الركضُ بعد الخروج والسببُ الأدقّ")
    log(f"**بوّابةُ صدق إعادة القياس:** اتّفاقٌ {agree} من {tot} = {_p(rate)} (والمقيسون للاتّفاق {len(agree_set)}) ⟵ " +
        ("السببُ الأدقّ **يُعتمد**" if ok_cause else "**غيرُ موثوق** — الآليّةُ وحدَها تحكم") +
        " · أكثرُ المعايير اختلافًا: " + " · ".join(f"{k} {v}" for k, v in sorted(mism.items(), key=lambda kv: -kv[1])[:6]))
    for e in [x for x in ev_rows if x["sym"] == "OMH"]:
        log(f"- **OMH** {e['day']}: «{e['mech']}» · السببُ الأدقّ {e['cause']} · الخارجُ المعاد {e['remeasured']} · القيم {e['vals']} · "
            f"ركض +50% خلال 10: {e['hit']} (نافذةٌ {'كاملة' if e['full'] else 'ناقصة'}{' · مستبعَد' if e['excl'] else ''})")
    log("\n| الآليّة / السبب | الأحداث | نافذةٌ كاملة | ركض +50% خلال 10 | الحصة [Wilson] | ركض قبل اكتمالها | مستبعَد (تقسيم/بلا شموع) |")
    log("|---|---|---|---|---|---|---|")
    groups = {}
    for e in ev_rows:
        groups.setdefault(e["mech"], []).append(e)
        if e["mech"] == "قِيس فخرج" and ok_cause and e["cause"]:
            groups.setdefault("قِيس فخرج · " + e["cause"], []).append(e)
        if e["mech"] == "قِيس فخرج" and e.get("eligible"):
            groups.setdefault("وصفًا · مؤهَّلٌ يومَ فرزه لم يُضَف (منذ 10-09)", []).append(e)
            groups.setdefault(f"وصفًا · مؤهَّلٌ لم يُضَف · {e.get('fp_outcome')}", []).append(e)
    for g, es in sorted(groups.items()):
        fu = [e for e in es if e["full"]]
        k = sum(1 for e in fu if e["hit"])
        w = wilson(k, len(fu))
        log(f"| {g} | {len(es)} | {len(fu)} | {k} | {_p(k / len(fu) if fu else None)} [{_p(w[0])}، {_p(w[1])}] | "
            f"{sum(1 for e in es if not e['full'] and e['hit'])} | {sum(1 for e in es if e['excl'])} |")
    wb = wilson(st_k, st_n)
    log(f"| **الأساس: الباقون (رمز-جلسة)** | {len(E['stayers'])} | {st_n} | {st_k} | {_p(st_k / st_n if st_n else None)} [{_p(wb[0])}، {_p(wb[1])}] | — | — |")
    log("RRG_NW_JSON " + json.dumps({"agree": [agree, tot], "ok_cause": ok_cause, "stayers": [st_k, st_n],
                                     "omh": [x for x in ev_rows if x["sym"] == "OMH"],
                                     "groups": {g: [len(es), sum(1 for e in es if e["full"]), sum(1 for e in es if e["full"] and e["hit"])]
                                                for g, es in groups.items()}}, ensure_ascii=False, default=str))
    return 0


# ── pre: ④ البريماركت وقاعدةُ الظلّ ──────────────────────────────────────────────────────────────────
def mode_pre(key):
    S = _S()
    import kasih_scan as KS
    import market_calendar as MC
    import vwap_momentum_live as V
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())
    R, U = _load(RUNNERS), _load(UNIVERSE)
    pc_cache = {}

    def prev_close(sym, day):
        """إغلاقُ الأمس `adjusted=false` مسوًّى بتقسيمٍ يُنفَّذ يومَ day (`V4.price_factor` بالاسم · كـ`Day.prev_ref`)."""
        if (sym, day) in pc_cache:
            return pc_cache[(sym, day)]
        d0 = (dt.date.fromisoformat(day) - dt.timedelta(12)).isoformat()
        j = net.poly(f"/v2/aggs/ticker/{sym}/range/1/day/{d0}/{day}", {"adjusted": "false", "sort": "asc", "limit": 50})
        rs = [r for r in ((j or {}).get("results") or [])
              if dt.datetime.fromtimestamp(r["t"] / 1000, tz=V.NY).date().isoformat() < day]
        out = None
        if rs:
            sj, _ok = net.paged("/v3/reference/splits", {"ticker": sym, "execution_date": day, "limit": 10})
            spl = [(str(x.get("execution_date")), float(x["split_from"]), float(x["split_to"])) for x in sj or ()
                   if x.get("split_from") and x.get("split_to")]
            out = float(rs[-1]["c"]) * V.V4.price_factor(spl, day)
        pc_cache[(sym, day)] = out
        return out

    def bars_of(sym, day):
        by = net.minutes(sym, day, day)
        return None if by is None else (by.get(day) or [])

    def prior_sessions(day, n=5):
        out, d = [], dt.date.fromisoformat(day)
        while len(out) < n:
            d -= dt.timedelta(1)
            if V.V3.is_session(d.isoformat(), MC.session_info):
                out.append(d.isoformat())
        return out[::-1]
    log("# 🚪📏 `T-RRGATE` ④ — البريماركت وقاعدةُ الظلّ S")
    ev_out = {}
    for sym, day in PRE_EVENTS:
        log(f"\n## ${sym} {day} (والجلساتُ الخمس قبله)")
        log("| الجلسة | الحجمُ الدولاريّ 04:00-09:29 | الفجوة عند 09:29 | الخبر حتى 09:30 | المرساة قبل 09:30 | J1 | S |")
        log("|---|---|---|---|---|---|---|")
        for d in prior_sessions(day) + [day]:
            b, pc = bars_of(sym, d), prev_close(sym, d)
            usd, gap, npre = premarket_stats(b or [], pc)
            try:
                D = V.Day(net, d, MC, replay=True)
                _cat, detail, _x = D.cat_build(sym, D.cat_fetch(sym, V.V3.ny_ts(d, PRE_END)))
                news = V.news_brief(detail(PRE_END)) or "لا خبر"
            except Exception as ex:                                  # noqa: BLE001
                news = f"تعذّر ({type(ex).__name__})"
            sim = simulate_s(S, KS, V.V3.ny_ts, d, b, pc) if b else None
            ev_out[f"{sym}:{d}"] = {"usd": usd, "gap": gap, "news": news, "sim": sim, "bars": None if b is None else len(b)}
            anc = "—" if not sim else (f"{V._hm(int((sim['anchor_ms'] / 1000 - V.V3.ny_ts(d, 0)) // 60))} ${sim['anchor_px']:g} "
                                       f"({_p(None if sim['gap_pct'] is None else sim['gap_pct'] / 100)})")
            log(f"| {d}{' ⬅️' if d == day else ''} | ${usd:,.0f} ({npre} دقيقة) | {_p(gap)} | {str(news)[:80]} | {anc} | "
                f"{'—' if not sim else ('J1' if sim['j1'] else ('لا' if sim['j1'] is not None else 'لم يكتمل'))} | "
                f"{'—' if not sim else ('✅' if sim['S'] else '❌')} |")
    run100 = [r for r in R["rows"] if r["R"] >= 1.0]
    run50 = {(r["sym"], r["day"]) for r in R["rows"]}
    pool = sorted({(s, d) for d in U["sessions"] for s in set(U["days"][d].get("N") or ()) | set(U["days"][d].get("L") or {})} - run50)
    sample = random.Random(SAMPLE_SEED).sample(pool, min(SAMPLE_N, len(pool)))

    def one(item):
        sym, d = item
        b = bars_of(sym, d)
        if b is None:
            return "fail"
        sim = simulate_s(S, KS, V.V3.ny_ts, d, b, prev_close(sym, d))
        return "no_anchor" if not sim else ("S" if sim["S"] else "anchor_no_gap")
    res = {}
    for lab, items in (("+100%", [(r["sym"], r["day"]) for r in run100]), ("الأساس (عيّنة)", sample)):
        c = {"n": len(items), "fail": 0, "no_anchor": 0, "anchor_no_gap": 0, "S": 0}
        with ThreadPoolExecutor(WORKERS) as ex:
            for o in ex.map(one, items):
                c[o] += 1
        res[lab] = c
    log("\n## الـ248 (‏+100%) والأساس")
    log("| المجتمع | n | تعذّر | لا مرساة قبل 09:30 | مرساةٌ بلا فجوة 30% | **S التقطه** | الحصة [Wilson] |")
    log("|---|---|---|---|---|---|---|")
    for lab, c in res.items():
        m = c["n"] - c["fail"]
        w = wilson(c["S"], m)
        flag = "" if c["fail"] <= FAIL_MAX * c["n"] else " ⛔ لا قياس"
        log(f"| {lab} | {c['n']} | {c['fail']}{flag} | {c['no_anchor']} | {c['anchor_no_gap']} | **{c['S']}** | "
            f"{_p(c['S'] / m if m else None)} [{_p(w[0])}، {_p(w[1])}] |")
    prod = sum(1 for r in run100 if r.get("al_m") is not None and r["al_m"] < PRE_END)
    log(f"\nوصفًا: من الـ248 كانت له مِرساةُ «هنا الدخول» حقيقيّةٌ قبل 09:30: {prod} · نداءات {net.calls} · تعذّر {net.fails}")
    log("RRG_PRE_JSON " + json.dumps({"events": ev_out, "res": res, "prod_pre": prod}, ensure_ascii=False, default=str))
    return 0


# ── pit: ③ ثلاثُ سنوات PIT ────────────────────────────────────────────────────────────────────────────
def pit_symbol(S, sym, rows, splits_sym, member_days, edges, G5, floor_drop, audit_rng):
    """§③ صفوفُ رمزٍ واحد [[D، الذراع، منفجر؟، ret20]] للذراعين وحدَهما · والعدّادات · وفحصُ السوبرست (`audit_viol` يجب أن يبقى صفرًا)."""
    R = _rebuild()
    cnt = {"rows": 0, "no_history": 0, "stale": 0, "excl_split": 0, "excl_gap": 0, "pref_out": 0, "measured": 0, "no_measure": 0,
           "A": 0, "B": 0, "audit": 0, "audit_viol": 0}
    out = []
    if not rows:
        return out, cnt
    dates = [x[0] for x in rows]
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = R.gaps(rows)
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 60:
            cnt["no_history"] += 1
            continue
        if (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > R.STALE_DAYS:
            cnt["stale"] += 1
            continue
        sp, gq = R.row_guards(dates, i, d, unadj, gp)
        if sp:
            cnt["excl_split"] += 1
            continue
        if gq:
            cnt["excl_gap"] += 1
            continue
        cnt["rows"] += 1
        cd = cheap_drop(rows, i)
        if cd is None or cd < floor_drop:
            cnt["pref_out"] += 1
            if audit_rng.random() < AUDIT_P:
                cnt["audit"] += 1
                m = measure_at(S, sym, rows, splits_sym, d, edges)
                if m is not None and arm_of(m[0], m[1]) is not None:
                    cnt["audit_viol"] += 1
            continue
        m = measure_at(S, sym, rows, splits_sym, d, edges)
        cnt["measured"] += 1
        if m is None:
            cnt["no_measure"] += 1
            continue
        a = arm_of(m[0], m[1])
        if a is None:
            continue
        cnt[a] += 1
        out.append([d, a, R.exploded(rows, d, EXP_PCT, EXP_WIN), ret20(rows, i)])
    return out, cnt


def pit_entries(rows_by, sessions):
    """§③ الإدخالاتُ الجديدة لكلّ ذراع (`rebuild.new_entries` بالاسم) ⟵ [(ذراع، رمز، D، منفجر، ret20)]."""
    R = _rebuild()
    out = []
    for sym, rws in sorted(rows_by.items()):
        for arm in ("A", "B"):
            info = {r[0]: r for r in rws if r[1] == arm}
            for d in R.new_entries(list(info), sessions, R.WIN):
                r = info[d]
                out.append((arm, sym, d, r[2], r[3]))
    return out


def pit_stats(ents):
    """§③ الإحصاءُ والحكمُ بأدوات `split_gates` بالاسم (B = «الرفض» في `delta_raw`) ⟵ dict."""
    G = _split_gates()
    lab = [e for e in ents if e[3] is not None]
    cuts = G.mom_cuts([e[4] for e in lab])
    items = [(e[0] == "B", bool(e[3]), e[1], G.mom_bin(e[4], cuts)) for e in lab]
    raw, st = G.delta_raw(items), G.delta_strat(items)
    raw_ci = G.cluster_boot(items, G.delta_raw, seed=PIT_SEED)
    st_ci = G.cluster_boot(items, G.delta_strat, seed=PIT_SEED)
    years, floors = {}, True
    for y in ("2023", "2024", "2025"):
        it = [x for x, e in zip(items, lab) if e[2][:4] == y]
        years[y] = G.delta_raw(it)
        if sum(1 for x in it if x[0]) < B_FLOOR:
            floors = False
    arms = {}
    for a in ("A", "B"):
        es = [e for e in lab if e[0] == a]
        k = sum(1 for e in es if e[3])
        arms[a] = {"n": len(es), "syms": len({e[1] for e in es}), "k": k, "p": (k / len(es)) if es else None, "w": wilson(k, len(es))}
    return {"arms": arms, "raw": raw, "raw_ci": raw_ci, "strat": st, "strat_ci": st_ci, "years": years, "floors": floors,
            "unlabeled": len(ents) - len(lab), "cuts": cuts, "verdict": G.verdict(raw, raw_ci, st, st_ci, list(years.values()), floors, True)}


def mode_pit_prep(key):
    import market_calendar as MC
    import pit_universe as PU
    R = _rebuild()
    months = [(2022, 12)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
    snaps, union = {}, set()
    for d in R._first_sessions(months, MC):
        keep = sorted(r["ticker"] for r in PU.fetch_universe(d, key) if r.get("type") in ("CS", "ADRC"))
        snaps[d[:7]] = keep
        union |= set(keep)
        log(f"prep snapshot {d}: CS/ADRC {len(keep)}")
    sp = _splits_by(R.BARS_FROM, R.BARS_TO, key)
    prep = {"snapshots": snaps, "union": sorted(union), "splits": {s: v for s, v in sp.items() if s in union},
            "sessions": R.sessions_between(PIT_SESS[0], PIT_SESS[1], MC)}
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, "pit_prep.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(prep, f)
    log(f"🧊 pit_prep: الاتّحاد {len(union)} · لقطات {len(snaps)} · رموزٌ بتقسيمات {len(prep['splits'])} · جلسات {len(prep['sessions'])}")
    return 0


def mode_pit_shard(key, shard, nshards=NSHARDS, fetch_bars=None, prep=None):
    import envelope_scan as EV
    import pit_history as PH
    S = _S()
    R = _rebuild()
    R.install_stubs(S)
    G5 = R._gen5_ext()
    if prep is None:
        with gzip.open(os.path.join(OUT, "pit_prep.json.gz"), "rt", encoding="utf-8") as f:
            prep = json.load(f)
    edges = EV.load_edges() or {}
    floor_drop = float((edges.get("drop_pct") or [0])[0])
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], ()):
            member.setdefault(s, []).append(d)
    syms = prep["union"][shard::nshards]
    rng = random.Random(f"{PIT_SEED}:{shard}")
    rows_by, tot, diag = {}, {}, {}
    t0 = time.time()
    for n, sym in enumerate(syms):
        if fetch_bars is not None:
            rws, why = fetch_bars(sym)
        else:
            df, why = PH.polygon_daily(sym, R.BARS_FROM, R.BARS_TO, key)
            rws = R._rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        try:
            out, cnt = pit_symbol(S, sym, rws, prep["splits"].get(sym), member.get(sym, []), edges, G5, floor_drop, rng)
        except Exception as e:                                       # noqa: BLE001
            k = f"err:{type(e).__name__}"
            diag[k] = diag.get(k, 0) + 1
            continue
        if out:
            rows_by[sym] = out
        for k, v in cnt.items():
            tot[k] = tot.get(k, 0) + v
        if n % 25 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · {tot}")
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "floor_drop": floor_drop, "bars_diag": diag, "counts": tot, "rows": rows_by}
    if fetch_bars is None:
        os.makedirs(OUT, exist_ok=True)
        with gzip.open(os.path.join(OUT, f"pit_shard_{shard:02d}.json.gz"), "wt", encoding="utf-8") as f:
            json.dump(res, f)
    log(f"🗂️ shard {shard}: رموز {len(syms)} · {diag} · {tot}")
    return res


def mode_pit_assemble(in_dir):
    import glob
    prep_p = glob.glob(os.path.join(in_dir, "**", "pit_prep.json.gz"), recursive=True)
    if not prep_p:
        log("⛔ pit_prep.json.gz غائب")
        return 4
    with gzip.open(prep_p[0], "rt", encoding="utf-8") as f:
        prep = json.load(f)
    rows_by, tot, diag, nsym, shards = {}, {}, {}, 0, 0
    for p in sorted(glob.glob(os.path.join(in_dir, "**", "pit_shard_*.json.gz"), recursive=True)):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            sh = json.load(f)
        shards += 1
        rows_by.update(sh["rows"])
        nsym += sh["symbols"]
        for k, v in sh["counts"].items():
            tot[k] = tot.get(k, 0) + v
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
    cover = diag.get("ok", 0) / len(prep["union"]) if prep["union"] else 0.0
    st = pit_stats(pit_entries(rows_by, prep["sessions"]))
    why = []
    if shards < NSHARDS or nsym < len(prep["union"]):
        why.append(f"شظايا {shards} من {NSHARDS}")
    if cover < COVER_MIN:
        why.append(f"تغطيةُ الشموع {_p(cover)}")
    if tot.get("audit_viol"):
        why.append(f"المرشِّحُ المسبق أسقط {tot['audit_viol']} من الذراعين")
    if why:
        st["verdict"] = "لا قياس"
    log("# 🚪📏 `T-RRGATE` ③ — ثلاثُ سنوات PIT")
    log(f"الاتّحاد {len(prep['union'])} · رموزُ الشظايا {nsym} · شموعٌ {diag} · التغطية {_p(cover)} · العدّادات {tot}")
    log(f"فحصُ سوبرست المرشِّح المسبق: عيّنة {tot.get('audit', 0)} من المُستبعَدين · مخالفات {tot.get('audit_viol', 0)}")
    log("| الذراع | الإدخالات | الرموز | منفجرٌ +50% في 20 | الحصة [Wilson] |")
    log("|---|---|---|---|---|")
    for a, lab in (("A", "عبر كلَّه"), ("B", "عبر كلَّ شيءٍ إلّا العائد/المخاطرة")):
        x = st["arms"][a]
        log(f"| {a} {lab} | {x['n']} | {x['syms']} | {x['k']} | {_p(x['p'])} [{_p(x['w'][0])}، {_p(x['w'][1])}] |")
    f = lambda v: "—" if v is None else f"{v * 100:+.1f} نقطة"                                             # noqa: E731
    log(f"\nΔ = B − A: الخام {f(st['raw'])} [{f(st['raw_ci'][0])}، {f(st['raw_ci'][1])}] · المطبَّقُ بالزخم {f(st['strat'])} "
        f"[{f(st['strat_ci'][0])}، {f(st['strat_ci'][1])}] · السنوات " + " · ".join(f"{y} {f(v)}" for y, v in st["years"].items()) +
        f" · أرضيّةُ B ‏{B_FLOOR}/سنة {'✅' if st['floors'] else '❌'} · بلا وسم {st['unlabeled']}")
    log(f"⚖️ الحكم: **{st['verdict']}**" + (f" ({' · '.join(why)})" if why else "") +
        " — ويسقط إلى «لا قياس» إن سقطت بوّابةُ صدق إعادة القياس في ①")
    log("RRG_PIT_JSON " + json.dumps({"stats": st, "cover": cover, "counts": tot, "why": why}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("local", "nw", "pre", "pit_prep", "pit_shard", "pit_assemble"))
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--in", dest="in_dir", default=OUT)
    a = p.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — العقدُ المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    os.chdir(ROOT)
    if a.mode == "local":
        return mode_local()
    if a.mode == "pit_assemble":
        return mode_pit_assemble(a.in_dir)
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    if a.mode == "nw":
        return mode_nw(key)
    if a.mode == "pre":
        return mode_pre(key)
    if a.mode == "pit_prep":
        return mode_pit_prep(key)
    if not (0 <= a.shard < NSHARDS):
        log(f"⛔ --shard في [0، {NSHARDS})")
        return 2
    mode_pit_shard(key, a.shard)
    return 0


if __name__ == "__main__":
    sys.exit(main())
