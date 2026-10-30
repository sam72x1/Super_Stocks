# -*- coding: utf-8 -*-
"""🧮🔬 `T-SPLITGATES` — قياسُ بوّابتَي «فلترة أسهم التقسيم» (العقد `SPLIT_GATES_prereg.md` · مدموجٌ قبل أيّ رقم).

البوّابتان (لا تُمَسّان — قياسٌ فقط):
    G1 «صعد X% أوّل التقسيم (الحدّ 20%)»  = `_split_setup_probe(...)["didnt_rise"]` بـ`SPLIT_ROSE_MAX_PCT`
    G2 «لم يكتمل ثبات الدعم الثاني»       = `method_sequence(df, win=FAISAL_BOTTOM_LOOKBACK)["ok"]`

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا `LOGIC_VERSION` · ولا يُشحَن منه شيء.
كلُّ شرطٍ يُحسب **بالدوالّ الإنتاجيّة بالاسم** (`_split_setup_probe` · `method_sequence` · `descending_ladder` ·
`split_filter_stop` · `group_pump_scar`) وبترتيب `scan_split_filter` نفسِه — لا نسخة.

الأوضاع (`SG_MODE`):
    units         بناءُ قائمة الوحدات المؤرَّخة من ملفّات المستودع (بلا شبكة) ⟵ data/units.json
    units_eval    ② على الوحدات (Polygon: شموعٌ مسوّاة ‏+ تقسيمات) ⟵ سطرٌ لكلّ وحدة ‏+ RESULT_JSON
    pop_prep      ③④ التقسيماتُ العكسيّة 2022-08 … 2025-12 على أسهم ناسداك (لقطاتٌ شهريّة PIT) ⟵ out/prep.json.gz
    pop_shard     ③④ شريحةُ رموز (SHARD · NSHARDS) ⟵ out/shard_NN.json.gz
    pop_assemble  ③④ الحصصُ والفواصل والضبطُ والحكم ⟵ RESULT_JSON
    guards        حرّاسٌ اصطناعيّة بلا شبكة (SG1…)
"""
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "SPLIT_GATES_prereg.md")
UNITS = os.path.join(HERE, "data", "units.json")
OUT = os.path.join(HERE, "out")
SEED = 20261030
CONTRACT_SHA = "bd8d13b9cd0580304a642176f65422b77ef27fc29565a4495030a12f54d41ac0"   # بصمةُ العقد (SGA1)
UNITS_SHA = "019cadf67aa00d974727589108ad5c70f8576e3d734c63ae14e7fb3bb869280c"      # بصمةُ قائمة الوحدات (SGA2)
WIN = 20                                   # «خلال 20 جلسة» (أمرُ المالك)
BOOT_B = 2000
X_FROM, X_TO = "2023-01-03", "2025-12-31"  # ③④ ثلاثُ سنوات (يومُ الفحص X)
SPLITS_FROM = "2022-08-01"                 # نافذةُ الحدث 120 يومًا قبل أوّل X
BARS_FROM, BARS_TO = "2022-01-03", "2026-02-27"
UNIT_BARS_FROM = "2024-06-03"
MIN_GROUP = 30                             # §⑦ أرضيّةُ كلّ مجموعة (إدخالات)
MIN_TICKERS = 15                           # §⑦ أرضيّةُ الرموز في كلّ مجموعة
COVERAGE_FLOOR = 0.85                      # §⑦ تغطيةُ الشموع
REPRO_TOL_PTS = 2.0                        # §⑥ إعادةُ إنتاج دفعة 10-28
REPRO_MIN = 8                              # من 10
WITNESS_G2_MIN = 3                         # من 4
MOM_BINS = 5                               # §⑤ خُمُسيّاتُ الزخم
TICKER_RE = re.compile(r"^[A-Z]{1,5}$")

# §③-ج دفعةُ 10-28 = قائمةُ «قريبٌ من الشرط» في سجلّ `split_filter.yml` (تشغيلات 10-28 · 10-29 · 10-30) بقيمتها المسجَّلة.
#   (الرمز، يومُ التشغيل D، النسبةُ المسجَّلة، رقمُ التشغيلة) — D التالي لجلسة البيانات.
BATCH_1028 = [
    ("FBGL", "2026-10-28", 23, "40643179983"), ("CYCU", "2026-10-28", 26, "40643179983"),
    ("ELPW", "2026-10-28", 21, "40643179983"), ("SNAL", "2026-10-28", 98, "40643179983"),
    ("YMAT", "2026-10-28", 106, "40643179983"), ("HAO", "2026-10-29", 54, "40829630420"),
    ("BYAH", "2026-10-28", 46, "40643179983"), ("CGTL", "2026-10-28", 42, "40643179983"),
    ("GLE", "2026-10-28", 20, "40643179983"), ("CIIT", "2026-10-28", 28, "40643179983"),
]
# ④ شهودُ البوّابة الثانية بالاسم (أمرُ المالك) من السجلّ نفسِه.
WITNESS_G2 = [("MDCX", "2026-10-30", "41014435536"), ("BDAI", "2026-10-28", "40643179983"),
              ("ELAB", "2026-10-28", "40643179983"), ("UCAR", "2026-10-28", "40643179983")]
INTAKE_BATCHES = ("B4_20261008", "B36_20261027", "B22_20261028")
H6_CASES = {("BKYI", "2026-10-22"), ("CYCU", "2026-10-23"), ("ICMB", "2026-10-24"), ("ANPA", "2026-10-14")}


def log(*a):
    print(*a, flush=True)


def contract_sha():
    with open(CONTRACT, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ── الوحدات (بلا شبكة) ────────────────────────────────────────────────────────────────────────────────
def build_units(root=ROOT):
    """§③ قائمةُ الوحدات المؤرَّخة — حتميّة من ملفّات المستودع. الوحدةُ = (رمز، يوم D، مصدر).
    المدوّنة: صفوفُ `MASTER_CORPUS_INVENTORY` بكاتبٍ فيصل وتاريخٍ بدقّة اليوم ورمزٍ صالح ·
    الاستلامُ الأماميّ: صورُ فيصل في الدفعات الثلاث (B22 بعد تصحيحه الإلحاقيّ وإقرار المالك بكاتب الـ22) ·
    دفعةُ 10-28 وشهودُ G2 بالاسم."""
    units = {}

    def _add(sym, d, src, img, extra=None):
        if not (sym and TICKER_RE.match(sym) and d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)):
            return False
        k = f"{sym}_{d}"
        u = units.setdefault(k, {"unit": k, "sym": sym, "D": d, "sources": [], "images": []})
        if src not in u["sources"]:
            u["sources"].append(src)
        if img and img not in u["images"]:
            u["images"].append(img)
        for kk, vv in (extra or {}).items():
            u[kk] = vv
        return True

    inv = json.load(open(os.path.join(root, "faisal_method_v41", "corpus_audit", "MASTER_CORPUS_INVENTORY.json"),
                         encoding="utf-8"))["rows"]
    skipped = {"undated_or_partial": 0, "bad_ticker": 0}
    for r in inv:
        if not (r.get("FAISAL_DECISION") or {}).get("is_faisal"):
            continue
        d = str(r.get("DATE") or "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            skipped["undated_or_partial"] += 1
            continue
        for t in r.get("TICKER") or []:
            if not _add(str(t), d, "corpus", r.get("UNIT_ID")):
                skipped["bad_ticker"] += 1
    for b in INTAKE_BATCHES:
        base = os.path.join(root, "faisal_method_v41", "final_protocol", "intake", b)
        ann = json.load(open(os.path.join(base, "annotations.json"), encoding="utf-8"))["images"]
        if b == "B22_20261028":                                  # التصحيحُ الإلحاقيّ ‏+ إقرارُ المالك بكاتب الـ22 كلِّها
            corr = json.load(open(os.path.join(base, "CORRECTION_01.json"), encoding="utf-8"))
            ann = {k: {**v, **(corr.get("images") or {}).get(k, {}), "faisal_author": True} for k, v in ann.items()}
        for img, a in sorted(ann.items()):
            if not a.get("faisal_author"):
                continue
            d = a.get("decision_date")
            if not d and "2026-10-27" in str(a.get("date_evidence") or ""):
                d = "2026-10-27"                                 # يومُ نيويورك الظاهر في لقطات الألبوم (INFERRED)
            sym = a.get("symbol")
            if not d:
                skipped["undated_or_partial"] += 1
                continue
            _add(sym, d, f"intake:{b}", img, {"h6": True} if (sym, d) in H6_CASES else None)
    for sym, d, pct, run in BATCH_1028:
        _add(sym, d, "batch1028", f"run:{run}", {"logged_rose_pct": pct})
    for sym, d, run in WITNESS_G2:
        _add(sym, d, "witness_g2", f"run:{run}", {"logged_g2": True})
    out = sorted(units.values(), key=lambda u: (u["D"], u["sym"]))
    return {"units": out, "skipped": skipped, "n": len(out),
            "by_source": {s: sum(1 for u in out if s in u["sources"]) for s in
                          ("corpus", "intake:B4_20261008", "intake:B36_20261027", "intake:B22_20261028",
                           "batch1028", "witness_g2")},
            "h6": sorted(u["unit"] for u in out if u.get("h6"))}


def units_sha(blob):
    return hashlib.sha256(json.dumps(blob, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


# ── نقيّة: الشرطُ بالدوالّ الإنتاجيّة ───────────────────────────────────────────────────────────────────
def rows_df(rows):
    import pandas as pd
    idx = pd.DatetimeIndex([pd.Timestamp(x[0]) for x in rows])
    return pd.DataFrame({"Open": [x[1] for x in rows], "High": [x[2] for x in rows], "Low": [x[3] for x in rows],
                         "Close": [x[4] for x in rows], "Volume": [x[5] for x in rows]}, index=idx)


_RB = []


def _rb():
    """`fm_forensics/rebuild/rebuild.py` يُحمَّل مرّةً واحدة (لا إضافةَ لمسار البحث في كلّ نداء)."""
    if not _RB:
        p = os.path.join(ROOT, "fm_forensics", "rebuild")
        if p not in sys.path:
            sys.path.insert(0, p)
        import rebuild as RB
        _RB.append(RB)
    return _RB[0]


def asof_view(rows, splits, day):
    """صفوفٌ قبل `day` على مقياس الجلسة السابقة له (`rebuild.asof_scale` بالاسم) ‏+ التقسيماتُ المنفّذة قبله."""
    RB = _rb()
    v = RB.asof_scale(rows, splits, day)
    return v, [(d, r) for d, r in (splits or []) if d < day]


def eval_conditions(S, df, splits, today):
    """§② شروطُ `scan_split_filter` المحسوبة من الشموع — كلٌّ مستقلًّا (لا يتوقّف عند أوّل سقوط) وبالدوالّ الإنتاجيّة.
    `today` = تاريخُ آخر شمعة (dt.date). الحقول: price_ok · applicable · near_bottom · rose_raw · g1_pass · seq_ok ·
    entry_ok (None إن لم يكتمل التسلسل) · group · ret20."""
    C = S.CONFIG
    ev = {"price": None, "price_ok": False, "applicable": False, "near_bottom": False, "rose_raw": None,
          "g1_pass": None, "seq_ok": False, "bounce_pct": None, "entry_ok": None, "group": None, "ret20": None,
          "event_date": None}
    if df is None or len(df) < 40:
        ev["short"] = True
        return ev
    price = float(df["Close"].values[-1])
    ev["price"] = price
    ev["price_ok"] = C["SPLIT_RADAR_PRICE_MIN"] <= price <= C["SPLIT_RADAR_PRICE_MAX"]
    c = df["Close"].values
    if len(c) > 20 and c[-21] > 0:
        ev["ret20"] = float(c[-1] / c[-21] - 1.0)
    probe = S._split_setup_probe(df, splits, today)
    if probe:
        ev["applicable"] = True
        ev["near_bottom"] = bool(probe.get("near_bottom"))
        fv = probe.get("first_val")
        ref = probe.get("ref")
        ev["event_date"] = probe.get("event_date")
        ev["rose_pct"] = probe.get("rose_pct")
        ev["g1_pass"] = bool(probe.get("didnt_rise"))
        ev["rose_raw"] = probe.get("rose_pct")
        ev["ref"], ev["first_val"] = ref, fv
    seq = S.method_sequence(df, win=int(C["FAISAL_BOTTOM_LOOKBACK"]))
    ev["seq_ok"] = bool(seq and seq.get("ok"))
    if seq:
        ev["bounce_pct"] = seq.get("bounce_pct")
    if ev["seq_ok"]:
        bot = float(seq["bottom"])
        step = float(C["FAISAL_LADDER_STEP"])
        entries = S.descending_ladder(bot + step, step=-step)
        stop, _k = S.split_filter_stop(df, seq)
        ev["entry_ok"] = bool(entries) and stop is not None and price <= max(entries)
    try:
        ev["group"] = bool(S.group_pump_scar(df))
    except Exception:                                             # noqa: BLE001
        ev["group"] = None
    return ev


ORDER = ("price", "setup", "G1", "G2", "entry", "group")


def first_fail(ev):
    """ترتيبُ `scan_split_filter` نفسُه ⟵ أوّلُ شرطٍ يسقط (ما يطبعه السجلّ «قريبٌ من الشرط»)."""
    if not ev.get("price_ok"):
        return "price"
    if not (ev.get("applicable") and ev.get("near_bottom")):
        return "setup"
    if not ev.get("g1_pass"):
        return "G1"
    if not ev.get("seq_ok"):
        return "G2"
    if not ev.get("entry_ok"):
        return "entry"
    if ev.get("group"):
        return "group"
    return None


def sole(ev, gate):
    """§② «ترفضها البوّابةُ وحدَها»: البوّابةُ تسقط وكلُّ شرطٍ آخرَ محسوبٍ من الشموع يمرّ.
    G1: price · setup · G2 · entry · بلا قروب.  G2: price · setup · G1 · بلا قروب (entry غيرُ معرَّفٍ بلا تسلسل)."""
    base = ev.get("price_ok") and ev.get("applicable") and ev.get("near_bottom") and ev.get("group") is False
    if gate == "G1":
        return bool(base and ev.get("g1_pass") is False and ev.get("seq_ok") and ev.get("entry_ok"))
    if gate == "G2":
        return bool(base and ev.get("g1_pass") is True and not ev.get("seq_ok"))
    raise ValueError(gate)


def in_pop(ev, gate):
    """§④ مجتمعُ «وصل بقيّة الشروط» لكلّ بوّابة (البوّابةُ نفسُها حرّة)."""
    base = ev.get("price_ok") and ev.get("applicable") and ev.get("near_bottom") and ev.get("group") is False
    if gate == "G1":
        return bool(base and ev.get("seq_ok") and ev.get("entry_ok") and ev.get("g1_pass") is not None)
    if gate == "G2":
        return bool(base and ev.get("g1_pass") is True)
    raise ValueError(gate)


def rejected(ev, gate):
    return (ev.get("g1_pass") is False) if gate == "G1" else (not ev.get("seq_ok"))


# ── نقيّة: الإحصاء ─────────────────────────────────────────────────────────────────────────────────────
def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def mom_cuts(vals, k=MOM_BINS):
    """§⑤ حدودُ الخُمُسيّات من قيم الزخم وحدَها (بلا نتيجة)."""
    v = sorted(x for x in vals if x is not None)
    if len(v) < k:
        return []
    return [v[int(len(v) * i / k)] for i in range(1, k)]


def mom_bin(x, cuts):
    if x is None:
        return None
    b = 0
    for c in cuts:
        if x >= c:
            b += 1
    return b


def delta_raw(items):
    """items = [(rej bool, exploded bool, ticker, stratum)] ⟵ p(rej) − p(pass)."""
    r = [e for rj, e, *_ in items if rj]
    p = [e for rj, e, *_ in items if not rj]
    if not r or not p:
        return None
    return sum(r) / len(r) - sum(p) / len(p)


def delta_strat(items):
    """فرقٌ مُطبَّقٌ بأوزان كوكران-مانتل-هانزل على طبقات الزخم (الطبقةُ بلا مجموعةٍ تُسقط وتُعَدّ)."""
    strata = {}
    for rj, e, _t, s in items:
        if s is None:
            continue
        strata.setdefault(s, [[], []])[0 if rj else 1].append(e)
    num = den = 0.0
    for a, b in strata.values():
        if not a or not b:
            continue
        w = len(a) * len(b) / (len(a) + len(b))
        num += w * (sum(a) / len(a) - sum(b) / len(b))
        den += w
    return num / den if den else None


def cluster_boot(items, fn, b=BOOT_B, seed=SEED):
    """فاصلُ 95% بإعادة سحب الرموز (العنقود = الرمز)."""
    by = {}
    for it in items:
        by.setdefault(it[2], []).append(it)
    keys = sorted(by)
    if len(keys) < 2:
        return (None, None)
    rnd = random.Random(seed)
    vals = []
    for _ in range(b):
        smp = []
        for _k in range(len(keys)):
            smp.extend(by[keys[rnd.randrange(len(keys))]])
        v = fn(smp)
        if v is not None:
            vals.append(v)
    if len(vals) < b * 0.9:
        return (None, None)
    vals.sort()
    return (round(vals[int(0.025 * len(vals))], 4), round(vals[int(0.975 * len(vals)) - 1], 4))


def verdict(raw, raw_ci, st, st_ci, years, floors_ok, repro_ok):
    """§⑧ الحكمُ بالأضعف: «تُسقط أفضل» · «تحمي» · «لا فرق قابل للكشف» · «لا قياس»."""
    if not (floors_ok and repro_ok):
        return "لا قياس"
    if None in (raw, st) or None in (raw_ci or (None,)) or None in (st_ci or (None,)):
        return "لا قياس"
    ys = [y for y in years if y is not None]
    pos = sum(1 for y in ys if y > 0)
    neg = sum(1 for y in ys if y < 0)
    if raw_ci[0] > 0 and st_ci[0] > 0 and pos >= 2:
        return "تُسقط أفضل"
    if raw_ci[1] < 0 and st_ci[1] < 0 and neg >= 2:
        return "تحمي"
    return "لا فرق قابل للكشف"


# ── الشبكة ───────────────────────────────────────────────────────────────────────────────────────────
def _bars(sym, a, b, key):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import pit_history as PH
    df, why = PH.polygon_daily(sym, a, b, key)
    if df is None:
        return [], why
    return [(i.date().isoformat(), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume))
            for i, r in df.iterrows()], why


def _splits_all(a, b, key):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import pit_snapshot as PS
    by = {}
    for r in PS.fetch_all_splits(a, b, key):
        try:
            by.setdefault(r["ticker"], []).append([r["execution_date"], float(r["split_to"]) / float(r["split_from"])])
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    for v in by.values():
        v.sort()
    return by


def _S():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "1")
    import Super_stock as S
    return S


def _contract_ok():
    """يرفض 9 ما لم يطابق العقدُ وقائمةُ الوحدات بصمتَيهما المثبّتتين (العقدُ قبل الرقم · والقائمةُ مجمَّدة)."""
    try:
        blob = json.load(open(UNITS, encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return contract_sha() == CONTRACT_SHA and units_sha(blob) == UNITS_SHA


def _today(rows):
    return dt.date.fromisoformat(rows[-1][0]) if rows else None


def mode_units_eval(key, units=None, fetch_bars=None, splits_by=None):
    S = _S()
    units = units or json.load(open(UNITS, encoding="utf-8"))["units"]
    syms = sorted({u["sym"] for u in units})
    if splits_by is None:
        splits_by = _splits_all(UNIT_BARS_FROM, dt.date.today().isoformat(), key)
    bars, diag = {}, {}
    for s in syms:
        rows, why = (fetch_bars(s) if fetch_bars else _bars(s, UNIT_BARS_FROM, dt.date.today().isoformat(), key))
        bars[s] = rows
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
    out = []
    for u in units:
        rows, sp = bars.get(u["sym"]) or [], splits_by.get(u["sym"], [])
        rec = {"unit": u["unit"], "sym": u["sym"], "D": u["D"], "sources": u["sources"]}
        for tag, day in (("prim", u["D"]), ("sens", (dt.date.fromisoformat(u["D"]) + dt.timedelta(1)).isoformat())):
            v, spv = asof_view(rows, sp, day)
            if len(v) < 40:
                rec[tag] = {"nodata": True, "bars": len(v)}
                continue
            ev = eval_conditions(S, rows_df(v), spv, _today(v))
            rec[tag] = {"asof": v[-1][0], "price": round(ev["price"], 4), "applicable": ev["applicable"],
                        "near_bottom": ev["near_bottom"], "rose_pct": ev.get("rose_pct"), "g1_pass": ev["g1_pass"],
                        "seq_ok": ev["seq_ok"], "bounce_pct": ev["bounce_pct"], "entry_ok": ev["entry_ok"],
                        "group": ev["group"], "first_fail": first_fail(ev), "sole_G1": sole(ev, "G1"),
                        "sole_G2": sole(ev, "G2"), "event_date": ev["event_date"]}
        if "logged_rose_pct" in u:
            rec["logged_rose_pct"] = u["logged_rose_pct"]
        if u.get("logged_g2"):
            rec["logged_g2"] = True
        out.append(rec)
    res = {"mode": "units_eval", "contract_sha": contract_sha(), "n_units": len(units), "symbols": len(syms),
           "bars_diag": diag, "units": out, "summary": units_summary(out)}
    return res


def units_summary(out):
    """§⑥ ملخّصُ ② وبوّابةُ إعادة الإنتاج."""
    sm = {}
    for tag in ("prim", "sens"):
        rows = [r.get(tag) or {} for r in out]
        ok = [x for x in rows if not x.get("nodata")]
        sm[tag] = {"evaluated": len(ok), "nodata": len(rows) - len(ok),
                   "applicable": sum(1 for x in ok if x.get("applicable")),
                   "g1_says_reject": sum(1 for x in ok if x.get("g1_pass") is False),
                   "g2_says_reject_in_setup": sum(1 for x in ok if x.get("applicable") and x.get("near_bottom")
                                                  and not x.get("seq_ok")),
                   "first_fail": {k: sum(1 for x in ok if x.get("first_fail") == k) for k in ORDER},
                   "passes_all": sum(1 for x in ok if x.get("first_fail") is None),
                   "sole_G1": sum(1 for x in ok if x.get("sole_G1")),
                   "sole_G2": sum(1 for x in ok if x.get("sole_G2"))}
    rep = [r for r in out if "logged_rose_pct" in r]
    hit = 0
    for r in rep:                                   # الإنتاجُ رفضها كلَّها بـG1 ⟵ النسبةُ ضمن نقطتين والرفضُ نفسُه
        p = (r.get("prim") or {}).get("rose_pct")
        if (p is not None and abs(p - r["logged_rose_pct"]) <= REPRO_TOL_PTS
                and (r.get("prim") or {}).get("g1_pass") is False):
            hit += 1
    wit = [r for r in out if r.get("logged_g2")]
    whit = sum(1 for r in wit if (r.get("prim") or {}).get("seq_ok") is False)
    sm["repro_g1"] = {"hit": hit, "of": len(rep), "ok": hit >= REPRO_MIN}
    sm["witness_g2"] = {"hit": whit, "of": len(wit), "ok": whit >= WITNESS_G2_MIN}
    return sm


def mode_pop_prep(key):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import market_calendar as MC
    import pit_universe as PU
    RB = _rb()
    months = [(2022, m) for m in range(8, 13)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
    snaps, union = {}, set()
    for d in RB._first_sessions(months, MC):
        rows = PU.fetch_universe(d, key)
        keep = sorted(r["ticker"] for r in rows if r.get("type") in ("CS", "ADRC"))
        snaps[d[:7]] = keep
        union |= set(keep)
        log(f"prep snapshot {d}: CS/ADRC {len(keep)}")
    allsp = _splits_all(SPLITS_FROM, dt.date.today().isoformat(), key)
    rev_t = {}
    for t, sp in allsp.items():
        rv = [d for d, r in sp if r < 1.0 and SPLITS_FROM <= d <= X_TO and t in set(snaps.get(d[:7], []))]
        if rv:
            rev_t[t] = rv
    prep = {"snapshots_n": {k: len(v) for k, v in snaps.items()}, "reverse_tickers": sorted(rev_t),
            "reverse_events": sum(len(v) for v in rev_t.values()),
            "splits": {t: allsp[t] for t in rev_t}}
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, "prep.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(prep, fh)
    log(f"prep: union {len(union)} · reverse-split tickers {len(rev_t)} · events {prep['reverse_events']}")
    return {"mode": "pop_prep", "union": len(union), "reverse_tickers": len(rev_t),
            "reverse_events": prep["reverse_events"]}


def symbol_rows(S, sym, rows, splits, lookback_days=None):
    """③④ لكلّ جلسة X في [X_FROM، X_TO] تقع بعد تقسيمٍ عكسيٍّ بأقلَّ من نافذة الحدث: الشروطُ على منظور X والنتيجة."""
    RB = _rb()
    lb = int(lookback_days or S.CONFIG["SPLIT_LOOKBACK_DAYS"])
    revs = [dt.date.fromisoformat(d) for d, r in splits if r < 1.0]
    out = []
    dates = [x[0] for x in rows]
    for i, x in enumerate(rows):
        X = x[0]
        if X < X_FROM or X > X_TO or i + 1 >= len(rows):
            continue
        xd = dt.date.fromisoformat(X)
        if not any(0 <= (xd - d).days <= lb for d in revs):
            continue
        D = rows[i + 1][0]                                         # يومُ القرار = الجلسةُ التالية
        v, spv = asof_view(rows, splits, D)
        if len(v) < 40 or v[-1][0] != X:
            continue
        ev = eval_conditions(S, rows_df(v[-400:]), spv, xd)
        exp = RB.exploded(rows, D, float(S.CONFIG["EXPLOSION_PCT"]), WIN)
        out.append({"X": X, "D": D, "in1": in_pop(ev, "G1"), "in2": in_pop(ev, "G2"), "rej1": rejected(ev, "G1"),
                    "rej2": rejected(ev, "G2"), "rose": ev.get("rose_pct"), "ret20": ev.get("ret20"),
                    "exp": exp, "ff": first_fail(ev)})
    return out, dates


def mode_pop_shard(key, shard, nshards, fetch_bars=None, prep=None):
    S = _S()
    if prep is None:
        with gzip.open(os.path.join(OUT, "prep.json.gz"), "rt", encoding="utf-8") as fh:
            prep = json.load(fh)
    syms = prep["reverse_tickers"][shard::nshards]
    res, diag = {}, {}
    t0 = time.time()
    for n, s in enumerate(syms):
        rows, why = (fetch_bars(s) if fetch_bars else _bars(s, BARS_FROM, BARS_TO, key))
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        if not rows:
            continue
        try:
            rr, dates = symbol_rows(S, s, rows, prep["splits"].get(s, []))
        except Exception as e:                                    # noqa: BLE001
            diag[f"err:{type(e).__name__}"] = diag.get(f"err:{type(e).__name__}", 0) + 1
            continue
        res[s] = {"rows": rr, "dates": dates}
        if n % 20 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s")
    out = {"shard": shard, "symbols": len(syms), "bars_diag": diag, "res": res}
    if fetch_bars is None:
        os.makedirs(OUT, exist_ok=True)
        with gzip.open(os.path.join(OUT, f"shard_{shard:02d}.json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(out, fh)
    return out


def gate_stats(res, gate):
    """§⑤ الإدخالاتُ الجديدة لكلّ رمز ثمّ الحصص والفواصل والضبط والسنوات."""
    RB = _rb()
    key_in, key_rej = ("in1", "rej1") if gate == "G1" else ("in2", "rej2")
    ents = []
    for s, blob in sorted(res.items()):
        rr = {r["X"]: r for r in blob["rows"]}
        fire = [x for x, r in rr.items() if r[key_in]]
        for X in RB.new_entries(fire, blob["dates"], win=WIN):
            r = rr[X]
            if r["exp"] is None:
                continue
            ents.append({"sym": s, "X": X, "rej": bool(r[key_rej]), "exp": bool(r["exp"]), "ret20": r["ret20"],
                         "rose": r.get("rose")})
    cuts = mom_cuts([e["ret20"] for e in ents])
    items = [(e["rej"], e["exp"], e["sym"], mom_bin(e["ret20"], cuts)) for e in ents]
    rj = [e for e in ents if e["rej"]]
    ps = [e for e in ents if not e["rej"]]
    raw = delta_raw(items)
    st = delta_strat(items)
    raw_ci = cluster_boot(items, delta_raw)
    st_ci = cluster_boot(items, delta_strat)
    years = {}
    for y in ("2023", "2024", "2025"):
        yi = [it for it, e in zip(items, ents) if e["X"][:4] == y]
        years[y] = {"n_rej": sum(1 for it in yi if it[0]), "n_pass": sum(1 for it in yi if not it[0]),
                    "delta": None if delta_raw(yi) is None else round(delta_raw(yi), 4)}
    # ضبطُ الزخم الصرف C-MOM (وصفيّ): يُقصي بالعدد نفسِه أعلى الزخم
    k = len(rj)
    srt = sorted([e for e in ents if e["ret20"] is not None], key=lambda e: -e["ret20"])
    cmom = srt[:k]
    floors = (len(rj) >= MIN_GROUP and len(ps) >= MIN_GROUP and len({e["sym"] for e in rj}) >= MIN_TICKERS
              and len({e["sym"] for e in ps}) >= MIN_TICKERS)
    se = None
    if raw_ci[0] is not None:
        se = (raw_ci[1] - raw_ci[0]) / (2 * 1.96)
    return {"gate": gate, "entries": len(ents), "tickers": len({e["sym"] for e in ents}),
            "rej": {"n": len(rj), "tickers": len({e["sym"] for e in rj}), "exp": sum(e["exp"] for e in rj),
                    "share": round(sum(e["exp"] for e in rj) / len(rj), 4) if rj else None,
                    "wilson": wilson(sum(e["exp"] for e in rj), len(rj))},
            "pass": {"n": len(ps), "tickers": len({e["sym"] for e in ps}), "exp": sum(e["exp"] for e in ps),
                     "share": round(sum(e["exp"] for e in ps) / len(ps), 4) if ps else None,
                     "wilson": wilson(sum(e["exp"] for e in ps), len(ps))},
            "delta_raw": None if raw is None else round(raw, 4), "delta_raw_ci": raw_ci,
            "delta_strat": None if st is None else round(st, 4), "delta_strat_ci": st_ci,
            "mom_cuts": [round(c, 4) for c in cuts], "years": years,
            "cmom": {"n": len(cmom), "exp": sum(e["exp"] for e in cmom),
                     "share": round(sum(e["exp"] for e in cmom) / len(cmom), 4) if cmom else None},
            "mde80": None if se is None else round(2.8 * se, 4), "floors_ok": floors}


def mode_pop_assemble(shards=None, units_result=None):
    if shards is None:
        shards = []
        for f in sorted(os.listdir(OUT)):
            if f.startswith("shard_") and f.endswith(".json.gz"):
                with gzip.open(os.path.join(OUT, f), "rt", encoding="utf-8") as fh:
                    shards.append(json.load(fh))
    res, diag, nsym = {}, {}, 0
    for sh in shards:
        res.update(sh["res"])
        nsym += sh["symbols"]
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
    cov = (diag.get("ok", 0) / nsym) if nsym else 0.0
    repro_ok = bool(((units_result or {}).get("summary") or {}).get("repro_g1", {}).get("ok"))
    wit_ok = bool(((units_result or {}).get("summary") or {}).get("witness_g2", {}).get("ok"))
    out = {"mode": "pop_assemble", "contract_sha": contract_sha(), "symbols": nsym, "bars_diag": diag,
           "coverage": round(cov, 4), "coverage_ok": cov >= COVERAGE_FLOOR, "repro_g1_ok": repro_ok,
           "witness_g2_ok": wit_ok}
    for gate, rep in (("G1", repro_ok), ("G2", wit_ok)):
        gs = gate_stats(res, gate)
        gs["verdict"] = verdict(gs["delta_raw"], gs["delta_raw_ci"], gs["delta_strat"], gs["delta_strat_ci"],
                                [v["delta"] for v in gs["years"].values()], gs["floors_ok"] and out["coverage_ok"],
                                rep)
        out[gate] = gs
    return out


# ── الحرّاس الاصطناعيّة (بلا شبكة) ──────────────────────────────────────────────────────────────────────
def guards():
    S = _S()
    ok = []

    def chk(name, cond):
        ok.append((name, bool(cond)))
        log(("✅" if cond else "❌"), name)

    # SG1 الوحداتُ حتميّة
    a, b = build_units(), build_units()
    chk("SG1 build_units حتميّة", units_sha(a) == units_sha(b) and a["n"] > 0)
    # SG2 first_fail بترتيب الإنتاج
    base = {"price_ok": True, "applicable": True, "near_bottom": True, "g1_pass": True, "seq_ok": True,
            "entry_ok": True, "group": False}
    chk("SG2 first_fail ترتيبُ الإنتاج", first_fail(base) is None
        and first_fail(dict(base, g1_pass=False, seq_ok=False)) == "G1"
        and first_fail(dict(base, seq_ok=False)) == "G2" and first_fail(dict(base, price_ok=False, g1_pass=False)) == "price")
    # SG3 sole يفرّق «وحدَها»
    chk("SG3 sole: G1 وحدَها لا مع G2", sole(dict(base, g1_pass=False), "G1")
        and not sole(dict(base, g1_pass=False, seq_ok=False), "G1")
        and sole(dict(base, seq_ok=False, entry_ok=None), "G2") and not sole(dict(base, seq_ok=False, group=True), "G2"))
    # SG4 in_pop يحرّر البوّابة نفسَها ويشترط الباقي
    chk("SG4 in_pop", in_pop(dict(base, g1_pass=False), "G1") and not in_pop(dict(base, g1_pass=False, seq_ok=False), "G1")
        and in_pop(dict(base, seq_ok=False, entry_ok=None), "G2") and not in_pop(dict(base, g1_pass=False), "G2"))
    # SG5 الفرقُ المطبَّق يزيل أثرَ الزخم المصطنع: داخل كلّ طبقةٍ الحصّتان متساويتان والمرفوضون في الطبقات العليا
    items = []
    for st in range(5):
        for grp, n in ((True, 5 * (st + 1)), (False, 5 * (5 - st))):
            k = st * n // 5                                        # حصّةُ الانفجار st×20% في المجموعتين
            for j in range(n):
                items.append((grp, j < k, f"T{st}{int(grp)}{j}", st))
    _ds = delta_strat(items)
    chk("SG5 الخامُ موجبٌ والمطبَّقُ صفر", (delta_raw(items) or 0) > 0.15 and _ds is not None and abs(_ds) < 1e-9)
    # SG6 الحكمُ بالأضعف
    chk("SG6 verdict", verdict(0.2, (0.05, 0.3), 0.15, (0.01, 0.3), [0.1, 0.2, -0.1], True, True) == "تُسقط أفضل"
        and verdict(0.2, (0.05, 0.3), 0.15, (-0.01, 0.3), [0.1, 0.2, 0.1], True, True) == "لا فرق قابل للكشف"
        and verdict(0.2, (0.05, 0.3), 0.15, (0.01, 0.3), [0.1, -0.2, -0.1], True, True) == "لا فرق قابل للكشف"
        and verdict(-0.2, (-0.3, -0.05), -0.15, (-0.3, -0.01), [-0.1, -0.2, 0.1], True, True) == "تحمي"
        and verdict(0.2, (0.05, 0.3), 0.15, (0.01, 0.3), [0.1, 0.2, 0.1], True, False) == "لا قياس")
    # SG7 الشروطُ بالدوالّ الإنتاجيّة: مقسّمٌ صعد 50% يُرفض بـG1 وآخرُ لم يصعد يمرّ
    import pandas as pd
    def _mk(rise):
        days = pd.bdate_range("2025-01-02", periods=130)
        px, rows = 10.0, []
        for i, d in enumerate(days):
            if i < 60:
                c = 10.0 - i * 0.05
            elif i == 60:
                c = 4.0                                            # يومُ التقسيم (مسوّى)
            elif i < 64:
                c = 4.0 * (1 + rise * (i - 60) / 3)
            else:
                c = max(2.2, 4.0 * (1 + rise) - (i - 63) * 0.12)
            rows.append((d.date().isoformat(), c, c * 1.01, c * 0.99, c, 1e5))
        return rows, [(days[60].date().isoformat(), 0.1)]
    r1, sp1 = _mk(0.5)
    r0, sp0 = _mk(0.05)
    e1 = eval_conditions(S, rows_df(r1), sp1, dt.date.fromisoformat(r1[-1][0]))
    e0 = eval_conditions(S, rows_df(r0), sp0, dt.date.fromisoformat(r0[-1][0]))
    chk("SG7 G1 من `_split_setup_probe` بالاسم", e1["applicable"] and e1["g1_pass"] is False and (e1["rose_pct"] or 0) > 20
        and e0["applicable"] and e0["g1_pass"] is True)
    # SG8 asof_view لا ينظر للأمام
    v, spv = asof_view(r1, sp1, r1[100][0])
    chk("SG8 asof_view قبل D حصرًا", v[-1][0] == r1[99][0] and all(d < r1[100][0] for d, _ in spv))
    bad = [n for n, c in ok if not c]
    log(f"guards: {len(ok) - len(bad)}/{len(ok)}")
    return 0 if not bad else 1


def main():
    mode = os.environ.get("SG_MODE", "guards")
    key = os.environ.get("POLYGON_API_KEY", "")
    if mode == "guards":
        return guards()
    if mode == "units":
        blob = build_units()
        os.makedirs(os.path.dirname(UNITS), exist_ok=True)
        with open(UNITS, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, ensure_ascii=False, indent=1, sort_keys=True)
        log(f"units: {blob['n']} · {blob['by_source']} · sha {units_sha(blob)}")
        return 0
    if not _contract_ok():
        log("⛔ العقدُ أو قائمةُ الوحدات لا يطابقان بصمتَيهما — لا رقمَ قبل العقد")
        return 9
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    if mode == "units_eval":
        res = mode_units_eval(key)
        for r in res["units"]:
            p = r.get("prim") or {}
            log(f"UNIT {r['unit']} {'/'.join(r['sources'])} · asof {p.get('asof')} · ff {p.get('first_fail')} · "
                f"rose {p.get('rose_pct')} · seq {p.get('seq_ok')} · soleG1 {p.get('sole_G1')} · soleG2 {p.get('sole_G2')}")
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "units_eval.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        log("RESULT_JSON " + json.dumps(res, ensure_ascii=False, separators=(",", ":")))
        return 0
    if mode == "pop_prep":
        log("PREP_JSON " + json.dumps(mode_pop_prep(key), ensure_ascii=False))
        return 0
    if mode == "pop_shard":
        r = mode_pop_shard(key, int(os.environ["SHARD"]), int(os.environ["NSHARDS"]))
        log(f"shard done: {r['symbols']} · {r['bars_diag']}")
        return 0
    if mode == "pop_assemble":
        ur = None
        p = os.path.join(OUT, "units_eval.json")
        if os.path.exists(p):
            ur = json.load(open(p, encoding="utf-8"))
        res = mode_pop_assemble(units_result=ur)
        log("RESULT_JSON " + json.dumps(res, ensure_ascii=False, separators=(",", ":")))
        return 0
    log(f"⛔ وضعٌ مجهول: {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
