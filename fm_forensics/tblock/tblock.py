# -*- coding: utf-8 -*-
"""🧱 `T-BLOCK` «البلوك على العرض في أسهم الارتكاز» — العقد `T_BLOCK_prereg.md` (#812) والملحق 1 `T_BLOCK_addendum_1.md` (قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا جذور · لا H6.
الأوضاع: `check` (بلا شبكة) · `prep_a` · `shard_a` (SHARD · NSHARDS) · `prep_b` · `shard_b` · `assemble` — وكلُّها تخرج 9 إن تغيّرت بصمةُ العقد أو الملحق.
"""
import argparse
import bisect
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_BLOCK_prereg.md")
CONTRACT_SHA = "20d2f5ad290554b796547ee2cee3ae5e03e4055457aa01e6d084e289222807bd"
ADDENDUM_1 = os.path.join(HERE, "T_BLOCK_addendum_1.md")
ADDENDUM_1_SHA = "6baf218159c77eee96d1046aafac75ebc59abd2a638b60595cc13b08f22ccadb"
CONTRACT_RC = 9
OUT = os.path.join(HERE, "out")
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
UNIVERSE_SHA16 = "4ad48b184923cc27"
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
RUNNERS_SHA16 = "b845db7df41295c1"
NEAR_WATCH = "near_watch.json"

# §① الحدود (أ: فيصل `OPERATOR_MIN_SHARES` · ب وج: أمرُ المالك)
THR_SHARES = 1000
THR_FLOAT = (("b05", 0.005), ("b1", 0.01), ("b2", 0.02))
THR_USD = 25000.0
LABELS = ("a", "b05", "b1", "b2", "c")
GOV_LABELS = ("a", "c")
SESS_PRE, SESS_REG, SESS_POST = "pre", "reg", "post"
OP_NY, REG_NY, CLOSE_NY, END_NY = 4 * 60, 9 * 60 + 30, 16 * 60, 20 * 60
QUOTE_BACK_NS = 60 * 1_000_000_000
WIN_BACK_NS, WIN_FWD_NS, WIN_LIMIT = 1_000_000_000, 600 * 1_000_000_000, 1000   # الملحق ② «بحدّ 1,000» (كان 50 خلافًا له · TBK11)
ENTRY_BUDGET_S = 1200                                        # TBK11 · engineering: مهلةُ الإدخال الواحد (5 جلسات) ⟵ «تعذّر» يُعَدّ (العقد: «ومهلةٌ وتعذّرٌ يُعدّان»)
TRADE_PAGE, TRADE_PAGES = 50000, 80
GRID = tuple(range(OP_NY, END_NY, 15))                       # الملحق ③: شبكةُ 15 دقيقة لضابط الزخم
UP20, UP50 = 0.20, 0.50
RUN50, RUN100 = 0.5, 1.0
NEAR_LEVEL = 0.10                                            # §③ ضمن 10% من المستوى المختبر
HORIZONS = (5, 10, 20)
GOV_H = 20
WIN_DAYS = 5                                                 # D…D+4
BOOT_B, BOOT_SEED = 2000, "TBLK"
CI_GOV = 0.975
FLOOR_G = 30                                                 # §③ لكلّ مجموعة لكلّ سنة
FLOOR_RUN = 100                                              # §④
FAIL_MAX = 0.10
LEFT_MIN = 0.50
K4_ENTRIES = 4465
YEARS = ("2023", "2024", "2025")
SEC_SLEEP = 0.15
OFFER_FORMS = ("424B1", "424B2", "424B3", "424B4", "424B5", "424B7", "S-1", "S-1/A", "S-3", "S-3/A")
OFFER_PHRASES = ("at-the-market", "at the market offering", "registered direct", "underwritten public offering",
                 "securities purchase agreement", "equity distribution agreement", "sales agreement", "private placement",
                 "warrant inducement")
SPAC_NAME = re.compile(r"acquisition\s+corp(\.|oration)?\s*$", re.I)
OK_TYPES = ("CS", "ADRC")


def log(*a):
    print(*a, flush=True)


def _sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def contract_ok():
    return _sha(CONTRACT) == CONTRACT_SHA and _sha(ADDENDUM_1) == ADDENDUM_1_SHA


def _jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, default=str)


def _jload(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


# ── دوالُّ نقيّة ─────────────────────────────────────────────────────────────────────────────────
def excluded_conditions(results):
    """الملحق ①: رموزُ شروط الصفقة التي لا تحدّث آخرَ سعرٍ مجمَّع ⟵ {id: الاسم}."""
    out = {}
    for c in results or []:
        try:
            if "trade" not in (c.get("data_types") or ["trade"]):
                continue
            ur = ((c.get("update_rules") or {}).get("consolidated") or {})
            if ur.get("updates_open_close") is False:
                out[int(c["id"])] = str(c.get("name") or "")
        except (KeyError, TypeError, ValueError):
            continue
    return out


def labels_of(price, size, float_sh):
    """§① الحدودُ التي تعبرها صفقةٌ واحدة (كلٌّ وحده)."""
    out = []
    if size >= THR_SHARES:
        out.append("a")
    if float_sh and float_sh > 0:
        for lab, frac in THR_FLOAT:
            if size >= frac * float_sh:
                out.append(lab)
    if price * size >= THR_USD:
        out.append("c")
    return out


def session_of(minute):
    return SESS_PRE if minute < REG_NY else (SESS_REG if minute < CLOSE_NY else SESS_POST)


def ny_minute(ts_ns, NY):
    t = dt.datetime.fromtimestamp(ts_ns / 1e9, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


class TradeScan:
    """§① والملحق ①: يمرّ على صفقات اليوم المؤهَّلة بترتيبها · يحسب اتّجاهَ التيك · ويحفظ المرشَّحة وحدَها."""

    def __init__(self, excl, float_sh):
        self.excl, self.float_sh = set(excl or ()), float_sh
        self.last_px, self.dir = None, 0
        self.n_all, self.n_excl, self.cands = 0, 0, []

    def feed(self, tr):
        self.n_all += 1
        conds = tr.get("conditions") or ()
        if any(int(c) in self.excl for c in conds):
            self.n_excl += 1
            return
        px, sz = float(tr.get("price") or 0), float(tr.get("size") or 0)
        if px <= 0 or sz <= 0:
            return
        if self.last_px is not None and px != self.last_px:
            self.dir = 1 if px > self.last_px else -1
        tick_up = self.last_px is not None and self.dir == 1
        self.last_px = px
        labs = labels_of(px, sz, self.float_sh)
        if labs:
            ts = int(tr.get("sip_timestamp") or tr.get("participant_timestamp") or 0)
            self.cands.append({"ts": ts, "px": px, "sz": sz, "labs": labs, "tick_up": tick_up})


def _late(deadline, clock):
    return deadline is not None and clock() > deadline


def assign_ask(cands, fetch_asc, fetch_desc, deadline=None, clock=time.time):
    """الملحق ②: لكلّ مرشَّحة (تصاعديًّا) ⟵ `on_ask` و`src` («q» عرضٌ · «t» تيك) · ويرجع False إن تعذّر جلبٌ (يُعَدّ تعذّرًا لليوم).
    `fetch_asc(a_ns، b_ns، limit)` و`fetch_desc(a_ns، b_ns)` ⟵ [(ts، ask)] أو None."""
    cov = None
    for c in sorted(cands, key=lambda x: x["ts"]):
        if _late(deadline, clock):
            return False
        ts, q = c["ts"], None
        if cov is not None and cov[0] <= ts <= cov[1]:
            k = bisect.bisect_right(cov[2], ts)
            q = cov[3][k - 1] if k else None
        else:
            res = fetch_asc(ts - WIN_BACK_NS, ts + WIN_FWD_NS, WIN_LIMIT)
            if res is None:
                return False
            res = sorted(res)
            end = res[-1][0] if len(res) >= WIN_LIMIT else ts + WIN_FWD_NS
            if end >= ts:
                cov = (ts - WIN_BACK_NS, end, [x[0] for x in res], [x[1] for x in res])
                k = bisect.bisect_right(cov[2], ts)
                q = cov[3][k - 1] if k else None
            else:
                cov = None
        if q is None:
            res = fetch_desc(ts - QUOTE_BACK_NS, ts)
            if res is None:
                return False
            q = res[0][1] if res else None
        if q is not None and q > 0:
            c["src"], c["on_ask"] = "q", c["px"] >= q
        else:
            c["src"], c["on_ask"] = "t", bool(c["tick_up"])
    return True


def blocks_by_label(cands, NY, ask_only=False):
    """{label: [(ts، دقيقة، سعر، المصدر، الجلسة)] تصاعديًّا} للصفقات على العرض."""
    out = {lab: [] for lab in LABELS}
    for c in sorted(cands, key=lambda x: x["ts"]):
        if not c.get("on_ask") or (ask_only and c.get("src") != "q"):
            continue
        _d, m = ny_minute(c["ts"], NY)
        for lab in c["labs"]:
            out[lab].append((c["ts"], m, c["px"], c["src"], session_of(m)))
    return out


def first_reach(seq, level):
    """أوّلُ دقيقةٍ يبلغ فيها `high` المستوى ⟵ دقيقة أو None."""
    for b in seq:
        if b[2] >= level:
            return b[0]
    return None


def close_at(seq, minute):
    """إغلاقُ آخر شمعةٍ بدايتُها ≤ الدقيقة."""
    pre = [b for b in seq if b[0] <= minute]
    return pre[-1][4] if pre else None


def outcome_after(seq, minute, ref, next_highs):
    """الملحق ③: (+20 اليوم، +50 اليوم، +20 خمسًا، +50 خمسًا) من شموعٍ بعد الدقيقة ‏+ أعلى الجلسات الخمس التالية (None ⟵ الخمسُ غيرُ مقيسة)."""
    if not ref or ref <= 0:
        return None
    aft = [b[2] for b in seq if b[0] > minute]
    hd = max(aft) if aft else None
    d20 = hd is not None and hd >= ref * (1 + UP20)
    d50 = hd is not None and hd >= ref * (1 + UP50)
    if next_highs is None:
        return (d20, d50, None, None)
    h5 = max([x for x in ([hd] + list(next_highs)) if x is not None], default=None)
    return (d20, d50, h5 is not None and h5 >= ref * (1 + UP20), h5 is not None and h5 >= ref * (1 + UP50))


def direction_30(seq, minute, B):
    """⑥ والملحق ③: إغلاقُ الدقيقة الثلاثين بعد البلوك (أو آخرُ دقيقةٍ قبل 20:00 ⟵ «مقصوص») ⟵ (صعد/هبط/ثابت، مقصوص؟)."""
    tgt = minute + 30
    c = close_at(seq, tgt)
    cut = not any(b[0] >= tgt for b in seq)
    if c is None:
        return None, cut
    c4, b4 = round(c, 4), round(B, 4)
    return ("up" if c4 > b4 else ("down" if c4 < b4 else "flat")), cut


def momentum5(adj_closes, day):
    """الملحق ③: إغلاقُ الأمس ÷ إغلاق الجلسة السادسة قبل اليوم − 1 · `adj_closes` = [(يوم، إغلاقٌ مسوّى)] تصاعديًّا."""
    ix = bisect.bisect_left([d for d, _c in adj_closes], day)
    if ix < 6:
        return None
    a, b = adj_closes[ix - 1][1], adj_closes[ix - 6][1]
    return (a / b - 1.0) if b else None


def quintile_edges(xs):
    v = sorted(x for x in xs if x is not None)
    if len(v) < 5:
        return None
    return [v[int(len(v) * k / 5)] for k in (1, 2, 3, 4)]


def quintile_of(x, edges):
    if x is None or not edges:
        return None
    return bisect.bisect_right(edges, x)


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def z_of(conf):
    return statistics.NormalDist().inv_cdf(0.5 + conf / 2)


def newcombe(k1, n1, k2, n2, conf=CI_GOV):
    """فاصلُ Newcombe (الطريقة 10 · Wilson) لفرق نسبتين p1 − p2."""
    if not n1 or not n2:
        return None, (None, None)
    z = z_of(conf)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    return d, (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def adj_diff(units, key, a_grp="G2", b_grp="G0"):
    """§③: فرقٌ مضبوطٌ بالزخم = متوسّطٌ موزونٌ بعدد `a_grp` لفروق الحصّة داخل الأخماس (خمسٌ بلا أحد الطرفين يسقط ويُعَدّ)."""
    byq = {}
    for u in units:
        if u.get("q") is None or u.get(key) is None or u.get("grp") not in (a_grp, b_grp):
            continue
        byq.setdefault(u["q"], {}).setdefault(u["grp"], []).append(1.0 if u[key] else 0.0)
    num = den = 0.0
    dropped = 0
    for _q, g in byq.items():
        if not g.get(a_grp) or not g.get(b_grp):
            dropped += 1
            continue
        w = len(g[a_grp])
        num += w * (sum(g[a_grp]) / len(g[a_grp]) - sum(g[b_grp]) / len(g[b_grp]))
        den += w
    return (num / den if den else None), dropped


def boot_cluster(units, stat, b=BOOT_B, seed=BOOT_SEED, conf=CI_GOV, key="sym"):
    """بوتستراب عنقوديّ بالرمز ⟵ (التقدير، (أدنى، أعلى))."""
    est = stat(units)
    by = {}
    for u in units:
        by.setdefault(u[key], []).append(u)
    syms = sorted(by)
    if est is None or not syms:
        return est, (None, None)
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        smp = [u for s in (rng.choice(syms) for _ in syms) for u in by[s]]
        v = stat(smp)
        if v is not None:
            vals.append(v)
    if not vals:
        return est, (None, None)
    vals.sort()
    a = (1 - conf) / 2
    return est, (vals[int(a * len(vals))], vals[min(len(vals) - 1, int((1 - a) * len(vals)))])


def verdict7(lab_res):
    """§③ الحاكم ⑦ ⟵ «يُضيف» · «لا فرق قابل للكشف» · «لا قياس» — `lab_res[label]` = {floor_ok، fail_ok، est، ci، per_year}."""
    meas = {lab: r for lab, r in lab_res.items() if r.get("floor_ok") and r.get("fail_ok")}
    if len(meas) < len(lab_res):
        if not meas:
            return "لا قياس"
    for _lab, r in meas.items():
        lo = (r.get("ci") or (None, None))[0]
        if r.get("est") is not None and lo is not None and lo > 0 and r["est"] > 0 \
                and all((r.get("per_year") or {}).get(y) is not None and r["per_year"][y] > 0 for y in YEARS):
            return "يُضيف"
    if len(meas) < len(lab_res):
        return "لا قياس"
    return "لا فرق قابل للكشف"


def shards_complete(found, expected):
    """TBK10 ⟵ لا حكمَ على شرائحَ ناقصة: كلُّ شريحةٍ متوقّعة حاضرة (عطلُ `43057090925`: ثلاثُ شرائحَ أسقطتها خدمةُ الملفّات)."""
    return expected > 0 and found == expected


def verdict3(r):
    """§④ الحاكم ③ لحدٍّ واحد ⟵ «يسبق» · «يسبق متأخّرًا» · «لا يفرّق» · «لا قياس»."""
    if not r.get("floor_ok") or not r.get("fail_ok"):
        return "لا قياس"
    d, (lo, hi) = r.get("diff"), r.get("ci") or (None, None)
    if d is None or lo is None:
        return "لا قياس"
    if lo <= 0 <= hi or d <= 0:
        return "لا يفرّق"
    left = r.get("left_med")
    return "يسبق" if (left is not None and left >= LEFT_MIN) else "يسبق متأخّرًا"


def is_spac_or_other(ref):
    """§① والملحق ④ ⟵ (مستبعَد؟، السبب) · ومرجعٌ None ⟵ (False، «بلا مرجع»)."""
    if not ref:
        return False, "بلا مرجع"
    if str(ref.get("type") or "") not in OK_TYPES:
        return True, f"نوع {ref.get('type')}"
    if str(ref.get("sic_code") or "") == "6770":
        return True, "SPAC (SIC 6770)"
    if SPAC_NAME.search(str(ref.get("name") or "").strip()):
        return True, "SPAC (الاسم)"
    return False, None


def offer_hit(form, text):
    """⑤: نوعُ طرحٍ مباشرةً أو 8-K يحوي عبارةً من القائمة (غيرُ حسّاسٍ لحالة الأحرف)."""
    f = str(form or "").upper()
    if f in OFFER_FORMS:
        return True, f
    if f == "8-K" and text:
        low = text.lower()
        for p in OFFER_PHRASES:
            if p in low:
                return True, p
    return False, None


# ── الجلب (رنر) ─────────────────────────────────────────────────────────────────────────────────
_SESS = {}


def _session():
    import threading
    import requests
    k = threading.get_ident()
    if k not in _SESS:
        _SESS[k] = requests.Session()
    return _SESS[k]


def poly_get(url, key, params=None, tries=3):
    for i in range(tries):
        try:
            r = _session().get(url, params=params, headers={"Authorization": f"Bearer {key}"}, timeout=40)
            if r.status_code == 200:
                return r.json() or {}
            if r.status_code in (404,):
                return None
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


def fetch_conditions(key):
    j = poly_get("https://api.polygon.io/v3/reference/conditions", key,
                 {"asset_class": "stocks", "data_type": "trade", "limit": 1000})
    return (j or {}).get("results") if j else None


def ticker_ref(sym, day, key):
    j = poly_get(f"https://api.polygon.io/v3/reference/tickers/{sym}", key, {"date": day})
    return (j or {}).get("results") if j else None


def splits_of(sym, key):
    """[(يومُ التنفيذ، to/from)] بحسب اصطلاح `rebuild.asof_factor`."""
    j = poly_get("https://api.polygon.io/v3/reference/splits", key, {"ticker": sym, "limit": 1000})
    if j is None:
        return None
    out = []
    for x in j.get("results") or []:
        try:
            fr, to = float(x["split_from"]), float(x["split_to"])
            if fr > 0 and to > 0:
                out.append((x["execution_date"], to / fr))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def daily_bars(sym, d0, d1, key, adjusted):
    j = poly_get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}", key,
                 {"adjusted": "true" if adjusted else "false", "sort": "asc", "limit": 50000})
    if j is None:
        return None
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    return [(dt.datetime.fromtimestamp(b["t"] / 1000, NY).date().isoformat(), float(b["h"]), float(b["c"]))
            for b in j.get("results") or [] if b.get("c") is not None]


def scan_day_trades(sym, day, key, scan, NY, deadline=None, clock=time.time):
    """الملحق ①: صفقاتُ [04:00، 20:00) نيويورك صفحاتٍ ⟵ True أو False (تعذّر/سقف)."""
    a = int(dt.datetime.fromisoformat(day).replace(hour=4, tzinfo=NY).timestamp() * 1e9)
    b = int(dt.datetime.fromisoformat(day).replace(hour=20, tzinfo=NY).timestamp() * 1e9)
    url = f"https://api.polygon.io/v3/trades/{sym}"
    params = {"timestamp.gte": a, "timestamp.lt": b, "limit": TRADE_PAGE, "order": "asc", "sort": "timestamp"}
    for _p in range(TRADE_PAGES):
        if _late(deadline, clock):
            return False
        j = poly_get(url, key, params)
        if j is None:
            return False
        res = j.get("results") or []
        res.sort(key=lambda x: (int(x.get("sip_timestamp") or 0), int(x.get("sequence_number") or 0)))
        for tr in res:
            scan.feed(tr)
        nxt = j.get("next_url")
        if not nxt:
            return True
        url, params = nxt, None
    return False


def quote_fetchers(sym, key):
    url = f"https://api.polygon.io/v3/quotes/{sym}"

    def asc(a, b, limit):
        j = poly_get(url, key, {"timestamp.gte": a, "timestamp.lte": b, "order": "asc", "sort": "timestamp", "limit": limit})
        if j is None:
            return None
        return [(int(x.get("sip_timestamp") or 0), float(x.get("ask_price") or 0)) for x in j.get("results") or []]

    def desc(a, b):
        j = poly_get(url, key, {"timestamp.gte": a, "timestamp.lte": b, "order": "desc", "sort": "timestamp", "limit": 1})
        if j is None:
            return None
        return [(int(x.get("sip_timestamp") or 0), float(x.get("ask_price") or 0)) for x in j.get("results") or []]
    return asc, desc


def day_blocks(sym, day, key, excl, float_sh, NY, deadline=None):
    """رمزٌ-يومٌ ⟵ {ok، n_all، n_excl، n_cand، cands} · `ok` False ⟵ تعذّر (صفقاتٌ أو عروض)."""
    scan = TradeScan(excl, float_sh)
    ok = scan_day_trades(sym, day, key, scan, NY, deadline=deadline)
    if not ok:
        return {"ok": False, "n_all": scan.n_all}
    asc, desc = quote_fetchers(sym, key)
    ok = assign_ask(scan.cands, asc, desc, deadline=deadline)
    return {"ok": ok, "n_all": scan.n_all, "n_excl": scan.n_excl, "n_cand": len(scan.cands), "cands": scan.cands}


# ── جزءُ أ ──────────────────────────────────────────────────────────────────────────────────────
def _lvs():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "live_vs_shadow"))
    sys.path.insert(0, ROOT)
    import live_vs_shadow as LV
    return LV


YAHOO_SRC = ("ياهو", "yahoo")   # `float_src` في near_watch يُكتب «ياهو» بالعربيّة (عطلٌ مُثبَت في `43052070347`: صفرُ رمزٍ-يوم)


def nw_float(e):
    """فلوتُ مدخل near_watch بالملحق ④: حقلُ `float` موجبٌ ومصدرُه ياهو ⟵ العدد · وإلّا None."""
    if not isinstance(e, dict):
        return None
    f = e.get("float")
    src = str(e.get("float_src") or "").strip().lower()
    if isinstance(f, (int, float)) and not isinstance(f, bool) and f > 0 and src in YAHOO_SRC:
        return float(f)
    return None


def mode_prep_a(key):
    LV = _lvs()
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    if (_sha(UNIVERSE) or "")[:16] != UNIVERSE_SHA16 or (_sha(RUNNERS) or "")[:16] != RUNNERS_SHA16:
        log("⛔ بصمةُ المادّة المجمَّدة (الكون أو الراكضون) تغيّرت — لا تشغيل")
        return 9
    src = LV.source_days(U)
    sess = list(U["sessions"])
    uni = {d: sorted(LV.universe_of(U, d)) for d in sess}
    union = sorted({s for v in uni.values() for s in v})
    cond = fetch_conditions(key)
    if not cond:
        log("⛔ جدولُ الشروط متعذّر — لا قياس (الملحق ①)")
        return 6
    excl = excluded_conditions(cond)
    commits = LV._commits(NEAR_WATCH)
    flt = {}
    for d in sess:
        h = LV.commit_before(commits, LV.ny_ts(d, OP_NY))
        if not h:
            continue
        try:
            nw = json.loads(LV._show(h, NEAR_WATCH) or "{}")
        except ValueError:
            nw = {}
        m = {}
        for s in uni[d]:
            f = nw_float(nw.get(s))
            if f is not None:
                m[s] = f
        flt[d] = m
    _jdump({"sessions": sess, "src": src, "uni": uni, "union": union, "excl": excl, "float_nw": flt},
           os.path.join(OUT, "prep_a.json.gz"))
    log(f"🧱 جزءُ أ: الجلسات {len(sess)} · أيّامُ المصدر {len(src)} · رموزُ الاتّحاد {len(union)} · رموزٌ-أيّام "
        f"{sum(len(v) for v in uni.values())} · شروطٌ مستبعدة {len(excl)}: {sorted(excl.items())}")
    log(f"🧱 فلوتُ near_watch: أيّامٌ {len(flt)} · رموزٌ-أيّام بفلوت {sum(len(v) for v in flt.values())}")
    return 0


def symbol_a(sym, days, prep, key, NY, LV, S=None, yahoo_float=None):
    """رمزٌ واحد في جزء أ ⟵ (صفوفُ الأيّام، تشخيص)."""
    from tier_fwd_report import fetch_day
    ref = ticker_ref(sym, days[0], key)
    ex, why = is_spac_or_other(ref)
    diag = {"ref": why, "cik": (ref or {}).get("cik")}
    if ex:
        return [], dict(diag, excluded=True)
    sp = splits_of(sym, key)
    d0 = (dt.date.fromisoformat(days[0]) - dt.timedelta(days=20)).isoformat()
    d1 = (dt.date.fromisoformat(days[-1]) + dt.timedelta(days=14)).isoformat()
    raw = daily_bars(sym, d0, d1, key, adjusted=False) or []
    adj = daily_bars(sym, d0, d1, key, adjusted=True) or []
    adj_c = [(d, c) for d, _h, c in adj]
    raw_days = [d for d, _h, _c in raw]
    yf_now = None
    rows = []
    seqs = {}
    for d in days:
        fsrc, fl = "near_watch", (prep["float_nw"].get(d) or {}).get(sym)
        if fl is None:
            if yf_now is None:
                try:
                    yf_now = (yahoo_float or (lambda s: S._yahoo_float(s, strict=True)))(sym) or 0.0
                except Exception:                                # noqa: BLE001
                    yf_now = 0.0
            if yf_now:
                sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "rebuild"))
                import rebuild as RB
                fl, fsrc = yf_now / RB.asof_factor(sp or [], d), "yahoo_now"
            else:
                fl, fsrc = None, "none"
        r = {"sym": sym, "day": d, "src_day": d in prep["src"], "fsrc": fsrc, "float": fl}
        db = day_blocks(sym, d, key, prep["excl"], fl, NY)
        r["trades_ok"] = bool(db.get("ok"))
        bars = fetch_day(sym, d, key)
        seq = LV.day_seq(bars, d) if bars else []
        seqs[d] = seq
        r["bars_ok"] = bool(seq)
        _pd, p0 = LV.prev_close(raw, d)
        r["P0"] = p0
        R, top_m, H = LV.day_R(seq, p0) if seq and p0 else (None, None, None)
        r.update({"R": R, "H": H, "top_m": top_m})
        r["m20"] = first_reach(seq, p0 * (1 + UP20)) if (seq and p0) else None
        r["mom5"] = momentum5(adj_c, d)
        ix = bisect.bisect_right(raw_days, d)
        nxt = raw[ix:ix + 5]
        split5 = any(d < sd <= (nxt[-1][0] if nxt else d) for sd, _r in (sp or []))
        r["next_highs"] = [h for _d, h, _c in nxt] if (len(nxt) == 5 and not split5) else None
        r["split5"] = split5
        r["end5"] = nxt[-1][0] if len(nxt) == 5 else None
        r["close5"] = nxt[-1][2] if (len(nxt) == 5 and not split5) else None
        r["cik"] = diag["cik"]
        r["split_day"] = any(sd == d for sd, _r in (sp or []))
        if r["trades_ok"]:
            r["n_all"], r["n_excl"], r["n_cand"] = db["n_all"], db["n_excl"], db["n_cand"]
            for mode, ask_only in (("", False), ("_q", True)):
                bl = blocks_by_label(db["cands"], NY, ask_only=ask_only)
                for lab in LABELS:
                    v = bl[lab]
                    k = lab + mode
                    if not mode:
                        r["cnt_" + lab] = {f"{s}_{src}": sum(1 for x in v if x[4] == s and x[3] == src)
                                           for s in (SESS_PRE, SESS_REG, SESS_POST) for src in ("q", "t")}
                    r["first_" + k] = list(v[0][1:4]) if v else None
                    pre = [x for x in v if (r["m20"] is None or x[1] < r["m20"]) and (p0 and x[2] <= p0 * (1 + UP20))]
                    if pre:
                        _st = LV.after_stats(seq, pre[0][1], pre[0][2], p0) or {}
                        r["pre20_" + k] = [pre[0][1], pre[0][2], pre[0][3], _st.get("left")]
                    else:
                        r["pre20_" + k] = None
                    if not mode and v:
                        m, B = v[0][1], v[0][2]
                        r["out_" + lab] = outcome_after(seq, m, B, r["next_highs"])
                        r["dir_" + lab] = direction_30(seq, m, B)
                        r["ts_" + lab] = v[0][0]
        if seq and p0:
            r["grid"] = {}
            for g in GRID:
                ref = close_at(seq, g)
                o = outcome_after(seq, g, ref, r["next_highs"]) if ref else None
                r["grid"][g] = o
        rows.append(r)
    # (أ′) السهمُ نفسُه — الدقيقةُ الوسيطةُ لبلوكاته في أيّام المصدر · لكلّ حدّ
    for lab in LABELS:
        mins = [x["first_" + lab][0] for x in rows if x["src_day"] and x.get("first_" + lab)]
        if not mins:
            continue
        mm = int(statistics.median(mins))
        for x in rows:
            if x["src_day"] and x.get("trades_ok") and not x.get("first_" + lab):
                seq = seqs.get(x["day"]) or []
                ref = close_at(seq, mm)
                x["same_" + lab] = outcome_after(seq, mm, ref, x["next_highs"]) if ref else None
    return rows, diag


def mode_shard_a(key, shard, nshards):
    from zoneinfo import ZoneInfo
    from concurrent.futures import ThreadPoolExecutor
    NY = ZoneInfo("America/New_York")
    LV = _lvs()
    os.environ.setdefault("FAISAL_ONLY", "0")
    import Super_stock as S
    prep = _jload(os.path.join(OUT, "prep_a.json.gz"))
    syms = prep["union"][shard::nshards]
    days_of = {}
    for d in prep["sessions"]:
        for s in prep["uni"][d]:
            days_of.setdefault(s, []).append(d)
    t0 = time.time()
    rows, diags = [], {}

    def one(sym):
        try:
            return sym, symbol_a(sym, days_of[sym], prep, key, NY, LV, S=S)
        except Exception as e:                                   # noqa: BLE001 — يُعَدّ ويُسمّى
            return sym, ([], {"error": f"{type(e).__name__}: {e}"})
    done = 0
    with ThreadPoolExecutor(int(os.environ.get("TBLK_THREADS", "8"))) as pool:
        for sym, (rs, dg) in pool.map(one, syms):
            rows.extend(rs)
            diags[sym] = dg
            done += 1
            if done % 10 == 0:
                log(f"shard_a {shard}: {done}/{len(syms)} · {int(time.time() - t0)}ث · صفوف {len(rows)}")
    _jdump({"shard": shard, "rows": rows, "diag": diags}, os.path.join(OUT, f"a_{shard:02d}.json.gz"))
    log(f"shard_a {shard}: انتهت · رموز {len(syms)} · صفوف {len(rows)} · {int(time.time() - t0)}ث")
    return 0


# ── جزءُ ب ──────────────────────────────────────────────────────────────────────────────────────
def _tgl():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "tgtladder"))
    sys.path.insert(0, ROOT)
    import tgtladder as TGL
    return TGL


def mode_prep_b(key):
    TGL = _tgl()
    TGL.OUT = OUT                                                # الملحق ⑤: المادّةُ نفسُها في مجلّد هذه الأداة
    TGL.mode_prep(key)                                           # 🔧 يُرجع قاموسَ الوصف لا رمزَ خروج (`43031294361`: prep_b خرج 1 بعد نجاحه) · `TBK8`
    return 0 if os.path.exists(os.path.join(OUT, "prep.json.gz")) else 5


def window_groups(blocks, tested, lab):
    """§③: (المجموعة، يومُ أوّل بلوكٍ مؤهَّل) من بلوكات النافذة [(يوم، سعر)] لحدٍّ واحد."""
    q = [(d, p) for d, p in blocks if tested and abs(p / tested - 1.0) <= NEAR_LEVEL]
    if len(q) >= 2:
        return "G2", q[0][0]
    if len(q) == 1:
        return "G1", q[0][0]
    if not blocks:
        return "G0", None
    return "Gx", None


def entry_outcomes(rows, iS, n_list=HORIZONS):
    """أعلى `high` في S+1…S+n ÷ إغلاق S − 1 ‏≥ 50% ⟵ {n: bool} · ومؤشّرُ أوّل جلسةٍ تبلغ (≤20) أو None."""
    cS = rows[iS][4]
    out, first = {}, None
    for k in range(1, max(n_list) + 1):
        if iS + k >= len(rows):
            return None, None
        if first is None and rows[iS + k][2] >= cS * (1 + UP50):
            first = iS + k
    for n in n_list:
        out[n] = max(rows[iS + k][2] for k in range(1, n + 1)) >= cS * (1 + UP50)
    return out, first


def units_for_symbol(sym, rows, rec, splits_sym, key, excl, NY, yahoo_float):
    """جزءُ ب لرمزٍ واحد: إدخالاتُه المسجَّلة (D · المستوى · العامل) ⟵ وحداتُ ⑦ (والمستبعَدُ يُعَدّ بسببه)."""
    out = []
    ref = ticker_ref(sym, rec[0]["d"], key)
    ex, why_ref = is_spac_or_other(ref)
    sp = [(d_, r_) for d_, r_ in (splits_sym or [])]
    yf_now = None
    for e in rec:
        u = {"sym": sym, "d": e["d"], "y": e["d"][:4], "tested": e["tested"], "ref": why_ref}
        if ex:
            u["why"] = "مستبعَد " + str(why_ref)
            out.append(u)
            continue
        i = e["i"]
        if i + WIN_DAYS - 1 + GOV_H >= len(rows):
            u["why"] = "بلا S+20"
            out.append(u)
            continue
        iS = i + WIN_DAYS - 1
        wdays = [rows[i + k][0] for k in range(WIN_DAYS)]
        end20 = rows[iS + GOV_H][0]
        if any(e["d"] <= sd <= end20 for sd, _r in sp):
            u["why"] = "تقسيمٌ في النافذة"
            out.append(u)
            continue
        if yf_now is None:
            try:
                yf_now = yahoo_float(sym) or 0.0
            except Exception:                            # noqa: BLE001
                yf_now = 0.0
        fl = (yf_now / e["f"]) if (yf_now and e["f"]) else None
        u["float"] = fl
        blocks = {lab: [] for lab in LABELS}
        blocks_q = {lab: [] for lab in LABELS}
        fail = False
        srcs = {"q": 0, "t": 0}
        deadline = time.time() + ENTRY_BUDGET_S
        for wd in wdays:
            db = day_blocks(sym, wd, key, excl, fl, NY, deadline=deadline)
            if not db.get("ok"):
                fail = True
                break
            for c in db["cands"]:
                if c.get("on_ask"):
                    srcs[c["src"]] += 1
                    for lab in c["labs"]:
                        blocks[lab].append((wd, c["px"]))
                        if c["src"] == "q":
                            blocks_q[lab].append((wd, c["px"]))
        if fail:
            u["why"] = "تعذّر الصفقات/العروض"
            if time.time() > deadline:
                u["timeout"] = True
            out.append(u)
            continue
        outc, first = entry_outcomes(rows, iS)
        u["out"] = outc
        u["mom5"] = (rows[iS][4] / rows[iS - 5][4] - 1.0) if iS >= 5 and rows[iS - 5][4] else None
        u["srcs"] = srcs
        for lab in LABELS:
            g, fd = window_groups(blocks[lab], e["tested"], lab)
            gq, _fdq = window_groups(blocks_q[lab], e["tested"], lab)
            u["grp_" + lab], u["grpq_" + lab] = g, gq
            u["nblk_" + lab] = len(blocks[lab])
            if fd is not None and first is not None and first - iS <= GOV_H:
                u["to_run_" + lab] = first - [r_[0] for r_ in rows].index(fd)
        out.append(u)
    return out


def mode_shard_b(key, shard, nshards):
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    TGL = _tgl()
    TGL.OUT = OUT
    RB = TGL._rb()
    os.environ["FAISAL_ONLY"] = "0"
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "appdiff"))
    import appdiff as AD
    import Super_stock as S
    import pit_history as PH
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    prep_a = _jload(os.path.join(OUT, "prep_a.json.gz")) if os.path.exists(os.path.join(OUT, "prep_a.json.gz")) else None
    excl = (prep_a or {}).get("excl")
    if excl is None:
        cond = fetch_conditions(key)
        if not cond:
            log("⛔ جدولُ الشروط متعذّر — لا قياس (الملحق ①)")
            return 6
        excl = excluded_conditions(cond)
    cur, _piv = AD.cfgs_of(S, RB)
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    six = {d: n for n, d in enumerate(prep["sessions"])}
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                cache[(sym, day)] = None
        return cache[(sym, day)]
    rec = []

    def recorder(S_, RB_, sym, rows, i, sub, f, r0, hourly, d=None):
        rec.append({"d": d or rows[i][0], "i": i, "f": f, "tested": (r0.get("stop") or (None,))[0]})
        return {"h4": False}
    keep = TGL.entry_row
    TGL.entry_row = recorder
    syms = prep["union"][shard::nshards]
    out, tot, diag = [], {}, {}
    t0 = time.time()
    try:
        for n, sym in enumerate(syms):
            df, why = PH.polygon_daily(sym, RB.BARS_FROM, TGL.BARS_TO, key)
            rows = RB._rows(df) if df is not None else []
            diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
            rec.clear()
            _o, cnt = TGL.shard_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), six, prep["prev_of"], prep["finra"],
                                       _proxy, S, cur, G5, RB, key, hourly_fn=lambda s, dd: None)
            for k, v in cnt.items():
                tot[k] = tot.get(k, 0) + v
            if rec:
                t_s = time.time()
                us_ = units_for_symbol(sym, rows, list(rec), prep["splits"].get(sym), key, excl, NY,
                                       lambda s_: S._yahoo_float(s_, strict=True))
                out.extend(us_)
                if time.time() - t_s > 300:
                    log(f"shard_b {shard}: ⏱️ {sym} {int(time.time() - t_s)}ث · إدخالات {len(rec)} · مهلة {sum(1 for u in us_ if u.get('timeout'))}")
            if n % 25 == 0:
                log(f"shard_b {shard}: {n + 1}/{len(syms)} · {tot} · إدخالات {len(out)} · {int(time.time() - t0)}ث")
    finally:
        TGL.entry_row = keep
    _jdump({"shard": shard, "counts": tot, "bars_diag": diag, "units": out}, os.path.join(OUT, f"b_{shard:02d}.json.gz"))
    log(f"shard_b {shard}: انتهت · {tot} · وحدات {len(out)} · {int(time.time() - t0)}ث")
    return 0


# ── التجميع ─────────────────────────────────────────────────────────────────────────────────────
def part_b_results(units):
    """⑦ لكلّ حدّ ⟵ {floor_ok، fail_ok، est، ci، per_year، وصف}."""
    ok = [u for u in units if not u.get("why")]
    n_all = len(units)
    fails = sum(1 for u in units if u.get("why") == "تعذّر الصفقات/العروض")
    res = {}
    for lab in LABELS:
        us = []
        for u in ok:
            if not u.get("out"):
                continue
            us.append({"sym": u["sym"], "y": u["y"], "grp": u["grp_" + lab], "grpq": u["grpq_" + lab], "mom5": u.get("mom5"),
                       "o5": u["out"]["5"] if "5" in u["out"] else u["out"].get(5),
                       "o10": u["out"]["10"] if "10" in u["out"] else u["out"].get(10),
                       "o20": u["out"]["20"] if "20" in u["out"] else u["out"].get(20),
                       "to_run": u.get("to_run_" + lab)})
        edges = quintile_edges([x["mom5"] for x in us])
        for x in us:
            x["q"] = quintile_of(x["mom5"], edges)
        r = {"n": len(us), "groups": {}}
        for g in ("G2", "G1", "G0", "Gx"):
            gs = [x for x in us if x["grp"] == g]
            r["groups"][g] = {"n": len(gs), "by_year": {y: sum(1 for x in gs if x["y"] == y) for y in YEARS},
                              **{f"o{h}": (sum(1 for x in gs if x[f"o{h}"]), len(gs), wilson(sum(1 for x in gs if x[f"o{h}"]), len(gs)))
                                 for h in HORIZONS},
                              "to_run_mean": (statistics.mean([x["to_run"] for x in gs if x["to_run"] is not None])
                                              if any(x["to_run"] is not None for x in gs) else None),
                              "to_run_med": (statistics.median([x["to_run"] for x in gs if x["to_run"] is not None])
                                             if any(x["to_run"] is not None for x in gs) else None)}
        st = lambda xs: adj_diff(xs, f"o{GOV_H}")[0]
        est, ci = boot_cluster(us, st)
        r["est"], r["ci"] = est, ci
        r["dropped_q"] = adj_diff(us, f"o{GOV_H}")[1]
        r["per_year"] = {y: adj_diff([x for x in us if x["y"] == y], f"o{GOV_H}")[0] for y in YEARS}
        r["raw"] = {h: (lambda a, b: (a - b) if (a is not None and b is not None) else None)(
            (r["groups"]["G2"][f"o{h}"][0] / r["groups"]["G2"][f"o{h}"][1]) if r["groups"]["G2"][f"o{h}"][1] else None,
            (r["groups"]["G0"][f"o{h}"][0] / r["groups"]["G0"][f"o{h}"][1]) if r["groups"]["G0"][f"o{h}"][1] else None) for h in HORIZONS}
        r["adj_h"] = {h: adj_diff(us, f"o{h}")[0] for h in HORIZONS}
        r["adj_g2g1"] = adj_diff(us, f"o{GOV_H}", "G2", "G1")[0]
        usq = [dict(x, grp=x["grpq"]) for x in us]
        r["ask_only"] = boot_cluster(usq, st)
        r["floor_ok"] = all(r["groups"][g]["by_year"][y] >= FLOOR_G for g in ("G2", "G0") for y in YEARS)
        r["fail_ok"] = (fails / n_all) <= FAIL_MAX if n_all else False
        res[lab] = r
    meta = {"n_units": n_all, "ok": len(ok), "fails": fails, "timeouts": sum(1 for u in units if u.get("timeout")),
            "why": {w: sum(1 for u in units if u.get("why") == w) for w in sorted({u.get("why") for u in units if u.get("why")})}}
    return res, meta


def _rate(xs):
    v = [1.0 if x else 0.0 for x in xs if x is not None]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


def boot_sym_diff(pairs, b=BOOT_B, seed=BOOT_SEED, conf=0.95):
    """فرقُ متوسّطين بعنقود الرمز: `pairs[sym]` = (مجموعُ أ، عددُ أ، مجموعُ ب، عددُ ب) ⟵ (الفرق، (أدنى، أعلى))."""
    syms = sorted(s for s, v in pairs.items() if v[1] and v[3])
    if not syms:
        return None, (None, None)

    def st(ss):
        a = sum(pairs[s][0] for s in ss)
        na = sum(pairs[s][1] for s in ss)
        c = sum(pairs[s][2] for s in ss)
        nc = sum(pairs[s][3] for s in ss)
        return (a / na - c / nc) if (na and nc) else None
    est = st(syms)
    rng = random.Random(seed)
    vals = sorted(v for v in (st([rng.choice(syms) for _ in syms]) for _ in range(b)) if v is not None)
    if not vals:
        return est, (None, None)
    a_ = (1 - conf) / 2
    return est, (vals[int(a_ * len(vals))], vals[min(len(vals) - 1, int((1 - a_) * len(vals)))])


def boot_units_mean(units, b=BOOT_B, seed=BOOT_SEED, conf=0.95):
    """متوسّطُ قيمٍ بعنقود الرمز: `units` = [(sym، قيمة)]."""
    by = {}
    for s_, v in units:
        t = by.setdefault(s_, [0.0, 0])
        t[0] += v
        t[1] += 1
    syms = sorted(by)
    if not syms:
        return None, (None, None)
    st = lambda ss: (sum(by[s][0] for s in ss) / sum(by[s][1] for s in ss))
    est = st(syms)
    rng = random.Random(seed)
    vals = sorted(st([rng.choice(syms) for _ in syms]) for _ in range(b))
    a_ = (1 - conf) / 2
    return est, (vals[int(a_ * len(vals))], vals[min(len(vals) - 1, int((1 - a_) * len(vals)))])


OUTK = ("d20", "d50", "f20", "f50")


def part_a_results(rows, prep, runners, LV, alerts, NY):
    """①②③④⑥ من صفوف جزء أ (⑤ في `edgar_part`)."""
    src = list(prep["src"])
    byk = {(r["sym"], r["day"]): r for r in rows}
    univ = [(s, d) for d in src for s in prep["uni"][d]]
    n_univ = len(univ)
    excl = sum(1 for k in univ if k not in byk)
    tr_fail = sum(1 for k in univ if k in byk and not byk[k].get("trades_ok"))
    sess = prep["sessions"]
    six = {d: i for i, d in enumerate(sess)}
    res = {"n_univ": n_univ, "excluded": excl, "trade_fail": tr_fail,
           "fail_ok": (tr_fail / max(1, n_univ - excl)) <= FAIL_MAX if n_univ else False,
           "fsrc": {k: sum(1 for x in rows if x["src_day"] and x.get("fsrc") == k) for k in ("near_watch", "yahoo_now", "none")},
           "excl_trades": sum(x.get("n_excl") or 0 for x in rows), "all_trades": sum(x.get("n_all") or 0 for x in rows)}
    in_n = {d: set((prep.get("uni_n") or {}).get(d) or ()) for d in src}
    # ① العدّ
    one = {}
    for lab in LABELS:
        per_day, per_day_n, sd_with = [], [], 0
        split = {}
        for d in src:
            tot = tot_n = 0
            for s in prep["uni"][d]:
                c = (byk.get((s, d)) or {}).get("cnt_" + lab) or {}
                n = sum(c.values())
                tot += n
                tot_n += n if s in in_n[d] else 0
                sd_with += 1 if n else 0
                for k, v in c.items():
                    split[k] = split.get(k, 0) + v
            per_day.append(tot)
            per_day_n.append(tot_n)
        one[lab] = {"median_day": statistics.median(per_day) if per_day else None, "sum": sum(per_day),
                    "median_day_N": statistics.median(per_day_n) if per_day_n else None, "symdays_with": sd_with,
                    "share_symdays": sd_with / n_univ if n_univ else None, "by_sess_src": split}
    res["one"] = one
    # ② ما بعد البلوك (+ ⑥)
    src_rows = [x for x in rows if x["src_day"] and x.get("trades_ok") and x.get("bars_ok")]
    edges = quintile_edges([x.get("mom5") for x in src_rows])
    two, six_ = {}, {}
    for lab in LABELS:
        blk = [x for x in src_rows if x.get("first_" + lab) and x.get("out_" + lab)]
        ctrl = [x for x in src_rows if not x.get("first_" + lab) and x.get("grid")]
        g_rates = {}
        for x in ctrl:
            q = quintile_of(x.get("mom5"), edges)
            for g, o in (x["grid"] or {}).items():
                if o is None:
                    continue
                t = g_rates.setdefault((q, int(g)), [[0, 0] for _ in OUTK])
                for j, v in enumerate(o):
                    if v is not None:
                        t[j][0] += 1 if v else 0
                        t[j][1] += 1
        r = {"n_block": len(blk)}
        for j, k in enumerate(OUTK):
            r[k] = _rate([x["out_" + lab][j] for x in blk])
            pairs = {}
            for x in blk:
                v = x["out_" + lab][j]
                if v is None:
                    continue
                t = pairs.setdefault(x["sym"], [0.0, 0, 0.0, 0])
                t[0] += 1 if v else 0
                t[1] += 1
            for x in src_rows:
                v = (x.get("same_" + lab) or [None] * 4)[j]
                if v is None or x["sym"] not in pairs:
                    continue
                pairs[x["sym"]][2] += 1 if v else 0
                pairs[x["sym"]][3] += 1
            r["same_" + k] = boot_sym_diff(pairs)
            du = []
            for x in blk:
                v = x["out_" + lab][j]
                q = quintile_of(x.get("mom5"), edges)
                g = max([gg for gg in GRID if gg <= x["first_" + lab][0]] or [GRID[0]])
                t = (g_rates.get((q, g)) or [[0, 0]] * 4)[j]
                if v is None or not t[1]:
                    continue
                du.append((x["sym"], (1.0 if v else 0.0) - t[0] / t[1]))
            r["mom_" + k] = boot_units_mean(du)
        two[lab] = r
        dirs = [x.get("dir_" + lab) for x in blk if x.get("dir_" + lab)]
        cnt = {k: sum(1 for d_ in dirs if d_[0] == k) for k in ("up", "down", "flat")}
        by_dir = {k: {kk: _rate([x["out_" + lab][jj] for x in blk if (x.get("dir_" + lab) or [None])[0] == k])
                      for jj, kk in enumerate(OUTK)} for k in ("up", "down", "flat")}
        six_[lab] = {"n": len(dirs), "cnt": cnt, "cut": sum(1 for d_ in dirs if d_[1]), "by_dir": by_dir}
    res["two"], res["six"] = two, six_

    def prior_block(sym, d, k):
        """الملحق ③: بلوكٌ بالحدّ (والمصدر) في الجلسات الخمس السابقة التي كان فيها الرمزُ في الكون."""
        i = six.get(d)
        if i is None:
            return False
        cnt = 0
        for j in range(i - 1, -1, -1):
            dj = sess[j]
            if sym not in prep["uni"][dj]:
                continue
            if (byk.get((sym, dj)) or {}).get("first_" + k):
                return True
            cnt += 1
            if cnt >= 5:
                break
        return False
    # ③ ④
    run_keys = [(x["sym"], x["day"]) for x in runners if x["R"] >= RUN100 and x["day"] in set(src)]
    three, four = {}, {}
    al_min = {}
    for d, v in (alerts or {}).items():
        for s_, a in (v or {}).items():
            try:
                al_min[(s_, d)] = ny_minute(int(a["ms"]) * 1_000_000, NY)[1]
            except (KeyError, TypeError, ValueError):
                continue
    for lab in LABELS:
        for mode in ("", "_q"):
            k = lab + mode
            rr, nr = [], []
            for (s_, d) in run_keys:
                r = byk.get((s_, d))
                if not r or not r.get("trades_ok") or not r.get("bars_ok") or r.get("R") is None:
                    continue
                pre = r.get("pre20_" + k)
                prior = (not pre) and prior_block(s_, d, k)
                rr.append({"sym": s_, "day": d, "hit": bool(pre or prior), "in_day": bool(pre), "prior": prior,
                           "m": pre[0] if pre else None, "left": (pre[3] if pre else (1.0 if prior else None)), "m20": r.get("m20")})
            for d in src:
                for s_ in prep["uni"][d]:
                    r = byk.get((s_, d)) or {}
                    if not r.get("trades_ok") or r.get("R") is None or r["R"] >= RUN50 or r.get("split_day"):
                        continue
                    nr.append(bool(r.get("pre20_" + k) or prior_block(s_, d, k)))
            k1, n1 = sum(1 for x in rr if x["hit"]), len(rr)
            k2, n2 = sum(nr), len(nr)
            diff, ci = newcombe(k1, n1, k2, n2)
            lefts = [x["left"] for x in rr if x["hit"] and x["left"] is not None]
            t = {"run": [k1, n1], "non": [k2, n2], "diff": diff, "ci": ci, "left_med": statistics.median(lefts) if lefts else None,
                 "min_before_20_med": (statistics.median([x["m20"] - x["m"] for x in rr if x["in_day"] and x["m20"] is not None])
                                       if any(x["in_day"] and x["m20"] is not None for x in rr) else None),
                 "in_day": sum(1 for x in rr if x["in_day"]), "prior_only": sum(1 for x in rr if x["prior"]),
                 "floor_ok": n1 >= FLOOR_RUN, "fail_ok": res["fail_ok"]}
            t["verdict"] = verdict3(t)
            three[k] = t
            if mode:
                continue
            cats = {"بلوكٌ فقط": [], "إشعارٌ فقط": [], "كلاهما": [], "لا أحد": []}
            earlier, e_min, e_prior = 0, [], 0
            for x in rr:
                am = al_min.get((x["sym"], x["day"]))
                c = ("كلاهما" if (x["hit"] and am is not None) else "بلوكٌ فقط" if x["hit"] else "إشعارٌ فقط" if am is not None else "لا أحد")
                cats[c].append(f'{x["sym"]} {x["day"]}')
                if c == "كلاهما":
                    if x["prior"]:
                        earlier += 1
                        e_prior += 1
                    elif x["m"] is not None and x["m"] < am:
                        earlier += 1
                        e_min.append(am - x["m"])
            pre_rows = [r for r in src_rows if r.get("pre20_" + lab) and r.get("R") is not None and not r.get("split_day")]
            kb = sum(1 for r in pre_rows if r["R"] >= RUN100)
            nfb = sum(1 for r in pre_rows if r["R"] < RUN50)
            four[lab] = {"cats": {c: [len(v), v] for c, v in cats.items()}, "earlier": [earlier, len(cats["كلاهما"])],
                         "earlier_prior": e_prior, "earlier_min_med": statistics.median(e_min) if e_min else None,
                         "prec": [kb, len(pre_rows)], "prec_ci": wilson(kb, len(pre_rows)),
                         "false_per_run": (nfb / kb) if kb else None}
    al = []
    for (s_, d) in al_min:
        if d not in set(src) or s_ not in prep["uni"][d]:
            continue
        r = byk.get((s_, d)) or {}
        if r.get("R") is None or r.get("split_day"):
            continue
        al.append(r["R"])
    ka = sum(1 for R in al if R >= RUN100)
    fa = sum(1 for R in al if R < RUN50)
    res["oe_prec"] = {"prec": [ka, len(al)], "ci": wilson(ka, len(al)), "false_per_run": (fa / ka) if ka else None,
                      "lvs_ref": [143, 1028]}
    res["three"], res["four"] = three, four
    return res


def edgar_part(rows, prep, contact, get=None, sleep=None, cmap=None):
    """⑤ والملحق ⑥ ⟵ نتائجُ لكلّ حدّ."""
    import html as _html
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    sys.path.insert(0, ROOT)
    import edgar2_probe as E2
    get = get or (lambda url: _sec_get(url, contact))
    sleep = sleep or time.sleep
    subs, docs = {}, {}

    def sub_of(cik):
        if cik not in subs:
            sleep(SEC_SLEEP)
            subs[cik] = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
        return subs[cik]
    src_rows = [x for x in rows if x["src_day"] and x.get("trades_ok") and x.get("bars_ok")]
    out, sample = {}, []
    for lab in LABELS:
        blk = [x for x in src_rows if x.get("first_" + lab) and x.get("out_" + lab) and x.get("end5")]
        units, fails = [], 0
        for x in blk:
            cik = (cmap or {}).get(x["sym"]) or x.get("cik")
            j = sub_of(cik) if cik else None
            if not j:
                fails += 1
                continue
            rec = (j.get("filings") or {}).get("recent") or {}
            t0 = dt.datetime.fromtimestamp(x["ts_" + lab] / 1e9, dt.timezone.utc).astimezone(NY)
            t1 = dt.datetime.fromisoformat(x["end5"]).replace(hour=20, tzinfo=NY)
            hit, why = False, None
            for f, acc, ad, doc in zip(rec.get("form") or [], rec.get("acceptanceDateTime") or [],
                                        rec.get("accessionNumber") or [], rec.get("primaryDocument") or []):
                pa = E2.parse_acc(acc)
                if not pa:
                    continue
                t = E2.to_ny(pa, "B")
                if not (t0 <= t <= t1):
                    continue
                text = None
                if str(f).upper() == "8-K":
                    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{str(ad).replace('-', '')}/{doc}"
                    if url not in docs:
                        sleep(SEC_SLEEP)
                        raw = get(url)
                        docs[url] = _html.unescape(re.sub(r"<[^>]+>", " ", raw)) if isinstance(raw, str) else None
                    text = docs[url]
                h, why_ = offer_hit(f, text)
                if h:
                    hit, why = True, why_
                    if str(f).upper() == "8-K" and len(sample) < 20:
                        m = re.search(re.escape(why_), text or "", re.I)
                        sample.append(f"{x['sym']} {x['day']} 8-K «{(text or '')[max(0, m.start() - 80):m.end() + 80].strip() if m else ''}»")
                    break
            ret5 = (x["close5"] / x["first_" + lab][1] - 1.0) if x.get("close5") and x["first_" + lab][1] else None
            units.append({"sym": x["sym"], "hit": hit, "why": why, "out": x["out_" + lab], "ret5": ret5})
        r = {"n": len(blk), "fails": fails, "fail_ok": (fails / len(blk)) <= FAIL_MAX if blk else False}
        for g, flag in (("offer", True), ("none", False)):
            us = [u for u in units if u["hit"] == flag]
            r[g] = {"n": len(us), **{k: _rate([u["out"][j] for u in us]) for j, k in enumerate(OUTK)},
                    "ret5_med": statistics.median([u["ret5"] for u in us if u["ret5"] is not None])
                    if any(u["ret5"] is not None for u in us) else None}
        r["offer_share"] = (r["offer"]["n"] / len(units)) if units else None
        out[lab] = r
    return out, sample


def _sec_get(url, contact):
    import requests
    try:
        r = requests.get(url, headers={"User-Agent": contact, "Accept-Encoding": "gzip"}, timeout=30)
        if r.status_code != 200:
            return None
        return r.json() if "json" in (r.headers.get("Content-Type") or "") or url.endswith(".json") else r.text
    except Exception:                                            # noqa: BLE001
        return None


def predictions(A, B):
    p = {}
    try:
        p["TB1"] = A["one"]["a"]["median_day"] >= 300 and A["one"]["c"]["median_day"] < A["one"]["a"]["median_day"] / 3
        two = A["two"]["a"]
        same, mom = two["same_d20"][0], two["mom_d20"][0]
        p["TB2"] = same is not None and same > 0 and mom is not None and mom <= same / 2
        t = A["three"]["a"]
        p["TB3"] = t["run"][1] and t["run"][0] / t["run"][1] >= 0.60 and (t["left_med"] or 0) >= 0.70
        p["TB4"] = A["three"]["a"]["verdict"] == "يسبق" and A["three"]["c"]["verdict"] == "لا يفرّق"
        f = A["four"]["a"]
        pb = f["prec"][0] / f["prec"][1] if f["prec"][1] else None
        p["TB5"] = pb is not None and pb < 0.139 and f["earlier"][1] and f["earlier"][0] > f["earlier"][1] / 2
        e = A.get("five", {}).get("a") or {}
        p["TB6"] = (e.get("offer_share") is not None and e["offer_share"] < 0.15
                    and (e["offer"]["f50"][0] or 0) < (e["none"]["f50"][0] or 0))
        s6 = A["six"]["a"]
        p["TB9"] = s6["n"] and s6["cnt"]["up"] / s6["n"] < 0.55
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    if B:
        p["TB7"] = B.get("verdict7") == "لا فرق قابل للكشف"
        ga = B["res"]["a"]
        p["TB8"] = ga["n"] and ga["groups"]["G2"]["n"] / ga["n"] >= 0.30
    return p


def mode_assemble(nshards_a, nshards_b):
    import glob
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    LV = _lvs()
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not contact:
        log("⛔ SEC_CONTACT غيرُ مضبوط — لا تجميع (⑤ لا يُترك صامتًا · الملحق ⑦)")
        return 2
    out = {"run": os.environ.get("GITHUB_RUN_ID")}
    pa = os.path.join(OUT, "prep_a.json.gz")
    if os.path.exists(pa):
        prep = _jload(pa)
        U = json.load(open(UNIVERSE, encoding="utf-8"))
        prep["uni_n"] = {d: sorted((U["days"].get(d) or {}).get("N") or ()) for d in prep["sessions"]}
        rows, diag = [], {}
        fa = sorted(glob.glob(os.path.join(OUT, "a_*.json.gz")))
        for f in fa:
            j = _jload(f)
            rows.extend(j["rows"])
            diag.update(j.get("diag") or {})
        runners = json.load(open(RUNNERS, encoding="utf-8"))["rows"]
        A = part_a_results(rows, prep, runners, LV, U.get("alerts") or {}, NY)
        A["shards"] = [len(fa), nshards_a]
        A["excluded_syms"] = {s: d.get("ref") for s, d in diag.items() if d.get("excluded")}
        A["no_ref"] = sum(1 for d in diag.values() if d.get("ref") == "بلا مرجع")
        A["sym_errors"] = {s: d["error"] for s, d in diag.items() if d.get("error")}
        A["excl_conditions"] = prep["excl"]
        try:
            import Super_stock as S
            cmap = S.sec_cik_map() or {}
        except Exception:                                        # noqa: BLE001
            cmap = {}
        A["five"], A["five_sample"] = edgar_part(rows, prep, contact, cmap=cmap)
        out["A"] = A
    units = []
    fb = sorted(glob.glob(os.path.join(OUT, "b_*.json.gz")))
    cnt_b = {}
    for f in fb:
        j = _jload(f)
        units.extend(j["units"])
        for k, v in (j.get("counts") or {}).items():
            cnt_b[k] = cnt_b.get(k, 0) + v
    if units:
        res_b, meta_b = part_b_results(units)
        B = {"res": res_b, "meta": meta_b, "counts": cnt_b, "shards": [len(fb), nshards_b], "k4": meta_b["n_units"] == K4_ENTRIES}
        B["complete"] = shards_complete(len(fb), nshards_b)
        B["verdict7"] = verdict7({lab: res_b[lab] for lab in GOV_LABELS}) if (B["k4"] and B["complete"]) else "لا قياس"
        out["B"] = B
    if out.get("A"):
        out["A"]["complete"] = shards_complete(out["A"]["shards"][0], nshards_a)
        for lab in GOV_LABELS:
            out["A"]["three"][lab]["verdict"] = verdict3(out["A"]["three"][lab]) if out["A"]["complete"] else "لا قياس"
    for part in ("A", "B"):
        if out.get(part) and not out[part]["complete"]:
            log(f"⛔ جزءُ {part}: شرائحُ ناقصة {out[part]['shards'][0]} من {out[part]['shards'][1]} — الحكمُ «لا قياس» (TBK10)")
    out["preds"] = predictions(out.get("A") or {}, out.get("B"))
    for ln in report_lines(out):
        log(ln)
    print("TBLK_JSON " + json.dumps(out, ensure_ascii=False, default=str))
    return 0


def _pc(x, n=1):
    return "—" if x is None else f"{100 * x:.{n}f}%"


def report_lines(out):
    L = ["", "=" * 70, "🧱 T-BLOCK — النتيجة (العقد #812 · الملحق 1)", f"التشغيلة {out.get('run')}"]
    A, B = out.get("A"), out.get("B")
    if A:
        L.append(f"جزءُ أ: الكون {A['n_univ']} رمزًا-يومًا (أيّامُ المصدر) · مستبعَد {A['excluded']} · تعذّر الصفقات {A['trade_fail']} · "
                 f"شرائح {A['shards'][0]}/{A['shards'][1]} · صفقاتٌ مستبعدةٌ بالشروط {A['excl_trades']} من {A['all_trades']} · الفلوت {A['fsrc']}")
        for lab in LABELS:
            o = A["one"][lab]
            L.append(f"① ({lab}) وسيطُ البلوكات/يوم {o['median_day']} (N وحدَه {o['median_day_N']}) · المجموع {o['sum']} · "
                     f"رموزٌ-أيّام ببلوك {o['symdays_with']} ({_pc(o['share_symdays'])}) · {o['by_sess_src']}")
        for lab in LABELS:
            t = A["two"][lab]
            L.append(f"② ({lab}) n={t['n_block']} · " + " · ".join(
                f"{k} {_pc(t[k][0])} [نفسُه Δ {_pc(t['same_' + k][0])} {tuple(_pc(v) for v in t['same_' + k][1])} · زخم Δ "
                f"{_pc(t['mom_' + k][0])} {tuple(_pc(v) for v in t['mom_' + k][1])}]" for k in OUTK))
        for k, t in A["three"].items():
            L.append(f"③ ({k}) راكضون سبقهم بلوك {t['run'][0]}/{t['run'][1]} · غيرُ راكضين {t['non'][0]}/{t['non'][1]} · الفرق "
                     f"{_pc(t['diff'])} [{_pc(t['ci'][0])}، {_pc(t['ci'][1])}] · وسيطُ ما بقي {_pc(t['left_med'])} · في اليوم {t['in_day']} · "
                     f"سابقٌ فقط {t['prior_only']} · وسيطُ الدقائق قبل +20% {t['min_before_20_med']} ⟵ **{t['verdict']}**")
        for lab in LABELS:
            f = A["four"][lab]
            L.append(f"④ ({lab}) الفئات " + " · ".join(f"{c} {v[0]}" for c, v in f["cats"].items()) +
                     f" · أبكر {f['earlier'][0]}/{f['earlier'][1]} (سابقٌ {f['earlier_prior']} · وسيطُ الدقائق {f['earlier_min_med']}) · "
                     f"دقّةُ البلوك {f['prec'][0]}/{f['prec'][1]} {tuple(_pc(v) for v in f['prec_ci'])} · كاذبٌ/راكض {f['false_per_run']}")
        oe = A["oe_prec"]
        L.append(f"④ «هنا الدخول» على الكون نفسِه {oe['prec'][0]}/{oe['prec'][1]} {tuple(_pc(v) for v in oe['ci'])} · "
                 f"كاذبٌ/راكض {oe['false_per_run']} · المرجع LVS {oe['lvs_ref'][0]}/{oe['lvs_ref'][1]}")
        for lab in LABELS:
            e = A["five"][lab]
            L.append(f"⑤ ({lab}) بلوكات {e['n']} · تعذّر {e['fails']} · تبعه طرح {_pc(e['offer_share'])} · مع طرح {e['offer']['n']} "
                     f"(+50% خمسًا {_pc(e['offer']['f50'][0])} · عائدُ الخمس {_pc(e['offer']['ret5_med'])}) · بلا طرح {e['none']['n']} "
                     f"(+50% خمسًا {_pc(e['none']['f50'][0])} · {_pc(e['none']['ret5_med'])})" + ("" if e["fail_ok"] else " ⟵ «لا قياس»"))
        for s_ in A.get("five_sample") or []:
            L.append(f"   ⑤ عيّنة: {s_[:300]}")
        for lab in LABELS:
            s6 = A["six"][lab]
            L.append(f"⑥ ({lab}) n={s6['n']} · صعد {s6['cnt']['up']} · هبط {s6['cnt']['down']} · ثابت {s6['cnt']['flat']} · مقصوص {s6['cut']}")
    if B:
        m = B["meta"]
        L.append(f"جزءُ ب: الإدخالات {m['n_units']} (بوّابةُ K4 = {K4_ENTRIES}: {'✅' if B['k4'] else '❌'}) · مقيسة {m['ok']} · {m['why']} · منها مهلة {m.get('timeouts', 0)} · "
                 f"العدّادات {B['counts']} · شرائح {B['shards'][0]}/{B['shards'][1]}")
        for lab in LABELS:
            r = B["res"][lab]
            gs = " · ".join(f"{g} {r['groups'][g]['n']} {r['groups'][g]['by_year']} (20ج {_pc(r['groups'][g]['o20'][0] / r['groups'][g]['o20'][1] if r['groups'][g]['o20'][1] else None)})"
                            for g in ("G2", "G1", "G0", "Gx"))
            L.append(f"⑦ ({lab}) {gs} · G2−G0 مضبوطًا {_pc(r['est'])} [{_pc(r['ci'][0])}، {_pc(r['ci'][1])}] · لكلّ سنة "
                     f"{ {y: _pc(v) for y, v in r['per_year'].items()} } · خامّ {r['raw']} · G2−G1 {_pc(r['adj_g2g1'])} · بالعرض وحدَه "
                     f"{_pc(r['ask_only'][0])} · الأرضيّة {'✅' if r['floor_ok'] else '❌'}")
        L.append("⚖️ ⑦ لكلّ حدّ: " + " · ".join(f"({lab}) {verdict7({lab: B['res'][lab]})}" for lab in GOV_LABELS))
        L.append(f"⚖️ ⑦ الحاكم: **{B['verdict7']}**")
    if A:
        L.append(f"⚖️ ③ الحاكم: (أ) **{A['three']['a']['verdict']}** · (ج) **{A['three']['c']['verdict']}**")
    L.append(f"التنبّؤات: {out.get('preds')}")
    L.append("🔒 لا شيء يُشحَن · وما يعبر يُقترح شارةً بلا تنفيذ قبل قرار المالك.")
    return L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="check", choices=("check", "prep_a", "shard_a", "prep_b", "shard_b", "assemble"))
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد أو الملحق تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ والملحقُ مطابقان")
        return 0
    if a.mode == "assemble":
        return mode_assemble(int(os.environ.get("NSHARDS_A", "20")), int(os.environ.get("NSHARDS_B", "20")))
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    if a.mode == "prep_a":
        return mode_prep_a(key)
    if a.mode == "shard_a":
        return mode_shard_a(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", "20")))
    if a.mode == "prep_b":
        return mode_prep_b(key)
    return mode_shard_b(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", "20")))


if __name__ == "__main__":
    sys.exit(main())
