#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️🔗 `T-OPLINK` — الرابطُ المشترك لأسهم تنبيه «هنا الدخول» عند لحظة المرساة.

**العقد:** `opentry_link_prereg.md` (مدفوعٌ قبل هذا الملفّ · أمرُ المالك 2026-09-25).

المجتمع: كلُّ مرساة `LIQ:*` من تاريخ git لـ`op_entry_state.json` (`tierlink_probe.anchor_history`
بالاسم) · المقياسُ الحاكم `exploded50` بالاسم من `tierlink_probe.measure` · الميزاتُ **قبل** يوم
المرساة من شموع Polygon اليوميّة (`adjusted=true` · ثابتةٌ تحت إعادة القياس) · الفلوت/المتاح من
**لقطات git المؤرَّخة ≤ يوم المرساة** وحدَها للحكم، وغيرُ المؤرَّخ وصفًا منفصلًا · عضويّةُ «الجاهز»
من لقطة `weekly_watchlist.json` يومَها · وبوّابةُ الرفض بـ`analyze_ticker` بالاسم على شموعٍ حتى `day−1`.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · والإنتاجُ لا يستورده. **ولا يُشحَن شيءٌ مهما كانت النتيجة.**

**رموزُ الخروج:** 0 صدر · 2 لا مفتاح · 3 تغطيةُ الجلب دون 80% · 4 صفرُ مرساة (بصمةُ no-op).
"""
import ast
import collections
import datetime as dt
import json
import os
import random
import statistics
import subprocess
import sys

import pandas as pd
import requests

from tierlink_probe import anchor_history, features, measure, daily_range, _bucket   # بالاسم
from tier_fwd_report import fetch_day, load_ledger                                 # بالاسم
from kasih_scan import NY, wilson                                                  # بالاسم
import Super_stock as S                                                            # rsi · spike_info · analyze_ticker · entry_status

SINCE = os.environ.get("OPLINK_SINCE", "2026-08-17")
UNTIL = os.environ.get("OPLINK_UNTIL", "")            # فارغ = أمسِ التشغيل (نيويورك)
SEED = int(os.environ.get("OPLINK_SEED", "20260925"))
MAX_ANCHORS = int(os.environ.get("OPLINK_MAX", "0"))  # 0 = الكلّ · >0 = جدوى
UNDATED_CAP = int(os.environ.get("OPLINK_UNDATED_CAP", "400"))
EXPL = 50.0
MIN_N, MIN_HALF, MIN_COVER, MIN_ROWS = 20, 10, 0.80, 100
API = "https://api.polygon.io"
FLOAT_OWNER, AVAIL_OWNER, RSI_OWNER = 4_000_000, 20_000, 30.0   # فرضيّاتُ المالك (العقد §④)
SNAP_FILES = ("weekly_watchlist.json", "company_cache.json", "hunter_watchlist.json")


def log(msg):
    print(msg, flush=True)


def _selfcheck_readonly() -> bool:
    """قراءةٌ فقط (كـ`TV6`/`WLK5`): صفرُ إرسالٍ وصفرُ كتابةِ حالةٍ — بالـAST على مصدرها."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                                # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    return False
    return True


# ───────────────────────── لقطاتُ git المؤرَّخة (العقد §④ · مؤرَّخٌ = تاريخ الكوميت ≤ يوم المرساة) ──
def _commits(path):
    out = subprocess.run(["git", "log", "--format=%h %ad", "--date=short", "--", path],
                         capture_output=True, text=True).stdout.splitlines()
    return [(l.split(" ", 1)[1], l.split(" ", 1)[0]) for l in out if l.strip()]   # (day, hash) الأحدثُ أوّلًا


def snapshot_before(commits, day, loader):
    """أحدثُ لقطةٍ بتاريخ **≤ يوم المرساة** — وإلّا None (لا لقطةَ لاحقة أبدًا · `V-O4`)."""
    for d, h in commits:
        if d <= day:
            return d, loader(h)
    return None, None


def dated_values(day, snaps):
    """`snaps` = {file: (snap_day, json)} ⟵ فلوت/متاح لكلّ رمز من أحدث لقطةٍ تحمل القيمة. يُرجع {sym: {float, avail, src}}."""
    out = {}
    order = sorted(((d, f, j) for f, (d, j) in snaps.items() if j is not None), reverse=True)
    for d, f, j in order:
        rows = []
        if f == "weekly_watchlist.json":
            rows = [(s.get("symbol"), s.get("float"), s.get("shares_available")) for s in (j.get("stocks") or [])]
        elif f == "company_cache.json":
            rows = [(k, (v or {}).get("float"), None) for k, v in j.items() if isinstance(v, dict)]
        elif f == "hunter_watchlist.json":
            rows = [(s.get("symbol"), s.get("float"), s.get("avail")) for s in (j.get("stocks") or [])]
        for sym, fl, av in rows:
            if not sym:
                continue
            o = out.setdefault(sym, {"float": None, "avail": None, "src": f"{f}@{d}"})
            if o["float"] is None and fl:
                o["float"] = float(fl)
            if o["avail"] is None and av is not None:
                o["avail"] = float(av)
    return out


def membership(day, wl):
    """عضويّةُ «الجاهز» يومَ المرساة: {sym: (member, ready)} من لقطة `weekly_watchlist` ≤ اليوم."""
    out = {}
    for s in (wl or {}).get("stocks") or []:
        if s.get("status", "active") != "active":
            continue
        try:
            ready = S.entry_status(s).get("status") == "ready_now"
        except Exception:                                            # noqa: BLE001
            ready = False
        out[s.get("symbol")] = (True, ready)
    return out


# ───────────────────────── الميزاتُ قبل يوم المرساة (العقد §④ · `V-O3`) ──────────────────────
def daily_frame(rows, day):
    """صفوفٌ يوميّة `(date, o, h, l, c, v)` ⟵ DataFrame **حتى `day−1` حصرًا** (لا شمعةَ يوم المرساة)."""
    rows = [r for r in rows if r[0] < day]
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["date", "Open", "High", "Low", "Close", "Volume"])
    df.index = pd.to_datetime(df.pop("date"))
    return df


def anchor_features(df, day, splits):
    """كلُّ ميزةٍ من `df` (حتى `day−1`) — نِسَبٌ ثابتةٌ تحت إعادة القياس. يُرجع القيمَ الخام والسلال."""
    if df is None or len(df) < 30:
        return None
    c = df["Close"].astype(float)
    rs = S.rsi(c)
    rsi14, rsi_min20 = float(rs.iloc[-1]), float(rs.tail(20).min())
    hi52 = float(df["High"].tail(252).max())
    drop52 = (1 - float(c.iloc[-1]) / hi52) * 100 if hi52 > 0 else None
    bw = S.CONFIG["BASE_WINDOW"]
    bh, bl = float(df["High"].tail(bw).max()), float(df["Low"].tail(bw).min())
    base_rng = (bh / bl - 1) * 100 if bl > 0 else None
    dvol20 = float((c * df["Volume"].astype(float)).tail(20).mean())
    try:
        spike, _n = S.spike_info(c.values.astype(float), exclude_last=bw)
    except Exception:                                                # noqa: BLE001
        spike = None
    last_rev = [d for (d, frm, to) in (splits or []) if d < day and frm > to]
    sd = (dt.date.fromisoformat(day) - dt.date.fromisoformat(max(last_rev))).days if last_rev else None
    raw = {"rsi14": rsi14, "rsi_min20": rsi_min20, "drop52": drop52, "base_rng": base_rng,
           "dvol20": dvol20, "spike": spike, "split_days": sd, "asof": str(df.index[-1].date())}
    b = {"rsi14": _bucket(rsi14, (30, 40, 55), ("<30", "30-40", "40-55", "≥55")),
         "rsi_min20": _bucket(rsi_min20, (27, 33), ("<27", "27-33", "≥33")),
         "drop52": _bucket(drop52, (50, 72, 90), ("<50%", "50-72", "72-90", "≥90")),
         "base_rng": _bucket(base_rng, (40, 120), ("<40%", "40-120", "≥120")),
         "dvol20": _bucket(dvol20, (15_000, 200_000), ("<15k$", "15-200k", "≥200k")),
         "spike": _bucket(spike, (60, 100), ("<60%", "60-100", "≥100")),
         "split_days": ("لا تقسيم" if sd is None else _bucket(sd, (31, 121), ("≤30", "31-120", ">120")))}
    return raw, b


def gate_of(sym, df):
    """بوّابةُ الرفض الأولى بـ`analyze_ticker` بالاسم على شموعٍ حتى `day−1` — أو «قُبل»."""
    if df is None or len(df) < S.CONFIG["MIN_BARS"]:
        return "بياناتٌ ناقصة"
    try:
        r = S.analyze_ticker(sym, df)
    except Exception as e:                                           # noqa: BLE001
        return f"⛔ {type(e).__name__}"
    return "قُبل" if r else (S._REJECT_REASONS.get(sym) or "؟")


def owner_flags(b, fl, av):
    """فرضيّاتُ المالك — `True`/`False`/`None` (مجهولٌ لا يُحتسب)."""
    return {"rsi<30": b["rsi14"] == "<30",
            "float<4م": None if fl is None else fl < FLOAT_OWNER,
            "avail<20k": None if av is None else av < AVAIL_OWNER}


def float_bucket(fl):
    return "؟" if fl is None else _bucket(fl, (FLOAT_OWNER, 20_000_000), ("<4م", "4-20م", "≥20م"))


def avail_bucket(av):
    return "؟" if av is None else _bucket(av, (AVAIL_OWNER, 40_000), ("<20k", "20-40k", "≥40k"))


# ───────────────────────── الحكم (العقد §⑤) ───────────────────────────────────
def judge(rows, feat, h2_from, label="exploded50", getf=None):
    """السلّةُ الأعلى مقابل مُكمِّلها: ‏≥2× · Wilson منفصلان · n≥20 · النصفان بنفس الاتّجاه (n≥10)."""
    getf = getf or (lambda r: r["f"].get(feat, "؟"))
    by = collections.defaultdict(list)
    for r in rows:
        v = getf(r)
        if v not in ("؟", None):
            by[v].append(r)
    table = {v: (len(rs), sum(1 for r in rs if r["o"][label]), wilson(sum(1 for r in rs if r["o"][label]), len(rs)))
             for v, rs in by.items()}
    elig = [(v, t) for v, t in table.items() if t[0] >= MIN_N]
    if not elig:
        return table, {"ok": False, "why": "لا حكم (كلُّ السلال دون 20)", "best": None}
    best_v, (bn, bk, (blo, bhi)) = max(elig, key=lambda x: x[1][1] / x[1][0])
    rest = [r for r in rows if getf(r) not in ("؟", None, best_v)]
    rn, rk = len(rest), sum(1 for r in rest if r["o"][label])
    if rn < MIN_N:
        return table, {"ok": False, "why": f"لا حكم (المُكمِّل {rn} دون 20)", "best": best_v}
    rlo, rhi = wilson(rk, rn)
    c1 = (bk / bn) >= 2 * (rk / rn) if rk else bk > 0
    c2 = blo > rhi
    h = {}
    for half, sel in (("H1", lambda r: r["date"] < h2_from), ("H2", lambda r: r["date"] >= h2_from)):
        hb = [r for r in rows if sel(r) and getf(r) == best_v]
        hr = [r for r in rows if sel(r) and getf(r) not in ("؟", None, best_v)]
        pb = sum(r["o"][label] for r in hb) / len(hb) if hb else None
        pr = sum(r["o"][label] for r in hr) / len(hr) if hr else None
        h[half] = (len(hb), pb, len(hr), pr)
    c4 = all(v[0] >= MIN_HALF and v[1] is not None and v[3] is not None and v[1] > v[3] for v in h.values())
    ok = c1 and c2 and c4
    return table, {"best": best_v, "best_rate": bk / bn * 100, "rest_rate": rk / rn * 100,
                   "ci_best": (blo, bhi), "ci_rest": (rlo, rhi), "n": (bn, rn), "c1": c1, "c2": c2,
                   "c3": True, "c4": c4, "halves": h, "ok": ok,
                   "why": "رابط" if ok else ("فصلٌ غيرُ متكرّر" if (c1 and c2) else "لا فصل")}


def fmt_table(table):
    return " · ".join(f"{v}: {k}/{n}={k / n * 100:.1f}% [{lo:.0f}·{hi:.0f}]"
                      for v, (n, k, (lo, hi)) in sorted(table.items(), key=lambda x: -x[1][1] / x[1][0]))


# ───────────────────────── الجلب ──────────────────────────────────────────────
def _get(url, params, key):
    try:
        r = requests.get(url, params=dict(params, apiKey=key), timeout=40)
        return r.json() if r.status_code == 200 else None
    except Exception:                                                # noqa: BLE001
        return None


def daily_bars(sym, d0, d1, key, adjusted="true"):
    js = _get(f"{API}/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}",
              {"adjusted": adjusted, "sort": "asc", "limit": "5000"}, key)
    out = []
    for b in (js or {}).get("results") or []:
        d = dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat()
        out.append((d, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b["v"])))
    return out


def splits_of(sym, key):
    js = _get(f"{API}/v3/reference/splits", {"ticker": sym, "limit": "100", "order": "asc"}, key)
    return [(s["execution_date"], float(s["split_from"]), float(s["split_to"]))
            for s in (js or {}).get("results") or [] if s.get("execution_date")]


def expl50_daily(rows, day):
    """المقياسُ اليوميّ المشترك (العقد §③-ب): أقصى `high` يومِ المرساة ÷ إغلاقُ الأمس − 1 ≥ 50%."""
    prev = [r for r in rows if r[0] < day]
    cur = [r for r in rows if r[0] == day]
    if not prev or not cur:
        return None
    return (cur[0][2] / prev[-1][4] - 1) * 100 >= EXPL


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    if not _selfcheck_readonly():
        log("⛔ الحارسُ الذاتيّ: الأداةُ ليست قراءةً فقط — خروج 5")
        return 5
    until = UNTIL or (dt.datetime.now(NY).date() - dt.timedelta(days=1)).isoformat()
    anchors = {k: v for k, v in anchor_history(since=SINCE).items() if k[0] <= until}
    if not anchors:
        log("⛔ صفرُ مرساةٍ في تاريخ git (بصمةُ no-op) — خروج 4")
        return 4
    keys = sorted(anchors)
    if MAX_ANCHORS:
        keys = keys[:MAX_ANCHORS]
        log(f"🧪 جدوى: أوّلُ {MAX_ANCHORS} مرساة فقط — لا يُفسَّر حكمٌ")
    log(f"🕵️🔗 T-OPLINK · مراسٍ {len(keys)} (منذ {SINCE} حتى {until}) · بذرة {SEED}")
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    commits = {f: _commits(f) for f in SNAP_FILES}
    cache_json = {}

    def _load(h, f):
        if (h, f) not in cache_json:
            try:
                cache_json[(h, f)] = json.loads(subprocess.run(["git", "show", f"{h}:{f}"],
                                                               capture_output=True, text=True).stdout)
            except Exception:                                        # noqa: BLE001
                cache_json[(h, f)] = None
        return cache_json[(h, f)]

    days = sorted({d for d, _ in keys})
    dated_by_day, member_by_day = {}, {}
    for day in days:
        snaps = {}
        for f in SNAP_FILES:
            sd, js = snapshot_before(commits[f], day, lambda h, f=f: _load(h, f))
            snaps[f] = (sd, js)
        dated_by_day[day] = dated_values(day, snaps)
        member_by_day[day] = membership(day, snaps["weekly_watchlist.json"][1])

    rows, fails, nobase, nofeat = [], 0, 0, 0
    minute_cache, daily_cache, split_cache = {}, {}, {}
    syms = sorted({s for _, s in keys})
    d0 = (dt.date.fromisoformat(days[0]) - dt.timedelta(days=800)).isoformat()
    for i, sym in enumerate(syms, 1):
        daily_cache[sym] = daily_bars(sym, d0, until, key, "true")
        split_cache[sym] = splits_of(sym, key)
        if i % 100 == 0:
            log(f"  … شموعٌ يوميّة {i}/{len(syms)}")
    for (day, sym) in keys:
        a = anchors[(day, sym)]
        bars = minute_cache.get((sym, day))
        if bars is None:
            bars = fetch_day(sym, day, key) or []
            minute_cache[(sym, day)] = bars
        if not bars:
            fails += 1
            continue
        dailies = daily_range(sym, day, key)               # adjusted=false (السعرُ الاسميّ · الأساس)
        b = ledger.get((day, sym))
        o = measure(a, b, bars, dailies)
        if o is None:
            nobase += 1
            continue
        f = features(a, b)
        pcs = [c for (d, _h, c) in (dailies or []) if d < day]
        if b is None and pcs and a.get("anchor_price"):
            f["gap"] = _bucket((a["anchor_price"] / pcs[-1] - 1) * 100, (10, 30), ("<10%", "10-30%", "≥30%"))
        df = daily_frame(daily_cache.get(sym) or [], day)
        af = anchor_features(df, day, split_cache.get(sym))
        if af is None:
            nofeat += 1
            raw, fb = {}, {k: "؟" for k in ("rsi14", "rsi_min20", "drop52", "base_rng", "dvol20", "spike", "split_days")}
        else:
            raw, fb = af
        f.update(fb)
        f["px_prev"] = _bucket(pcs[-1] if pcs else None, (1, 3, 10), ("<1$", "1-3$", "3-10$", ">10$"))
        dv = dated_by_day[day].get(sym) or {}
        f["float_d"], f["avail_d"] = float_bucket(dv.get("float")), avail_bucket(dv.get("avail"))
        mem, ready = member_by_day[day].get(sym, (False, False))
        f["member"], f["ready"] = ("عضو" if mem else "غير عضو"), ("جاهز" if ready else "لا")
        f["gate"] = "عضو" if mem else gate_of(sym, df)
        f["j1pre"] = "نعم" if (f.get("j1") == "J1" and f.get("tod") == "pre") else "لا"
        o["expl50_daily"] = expl50_daily([(d, None, h, None, c, None) for (d, h, c) in (dailies or [])], day)
        rows.append({"date": day, "symbol": sym, "f": f, "raw": raw, "dated": dv, "o": o})
    total = len(keys)
    cover = len(rows) / total
    log(f"🩺 V-O1 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} · بلا ميزات {nofeat} من {total} = {cover * 100:.1f}%")
    if cover < MIN_COVER:
        log("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم — خروج 3")
        return 3
    # V-O2 شاهدُ الهُويّة
    idn = [r for r in rows if "2026-08-18" <= r["date"] <= "2026-09-01"]
    k50 = sum(r["o"]["exploded50"] for r in idn)
    k100 = sum(r["o"]["exploded100"] for r in idn)
    log(f"🔒 V-O2 شاهدُ الهُويّة (08-18⟶09-01): exploded50 {k50}/{len(idn)} · exploded100 {k100} — المنشور 33/321 · 14 "
        f"{'✅' if (k50, k100) == (33, 14) else '⚠️ لا يطابق بت-بت — يُقرأ الفرقُ قبل الحكم'}")
    n = len(rows)
    for lab in ("exploded50", "exploded100"):
        k = sum(r["o"][lab] for r in rows)
        lo, hi = wilson(k, n)
        log(f"📊 الأساس {lab}: {k}/{n} = {k / n * 100:.1f}% [{lo:.0f}·{hi:.0f}]")
    med = statistics.median([r["raw"]["rsi14"] for r in rows if r["raw"].get("rsi14") is not None] or [float("nan")])
    log(f"📊 وسيطُ RSI14 عند المرساة: {med:.1f} · مؤرَّخُ الفلوت {sum(1 for r in rows if r['f']['float_d'] != '؟')} · "
        f"مؤرَّخُ المتاح {sum(1 for r in rows if r['f']['avail_d'] != '؟')} من {n}")
    h2_from = sorted(r["date"] for r in rows)[len(rows) // 2]
    log(f"⏱️ فاصلُ النصفين (وسيطُ التواريخ): {h2_from}")
    # ── الشاهد C (العقد §②-C · مقياسٌ يوميّ)
    random.seed(SEED)
    try:
        uni = sorted(set(S.get_universe()) - set(syms))
    except Exception:                                                # noqa: BLE001
        uni = []
    ctrl, ctrl_fail = [], 0
    if uni:
        per_day = collections.Counter(r["date"] for r in rows)
        for day, cnt in sorted(per_day.items()):
            for sym in random.sample(uni, min(cnt, len(uni))):
                dl = daily_range(sym, day, key)
                v = expl50_daily([(d, None, h, None, c, None) for (d, h, c) in (dl or [])], day)
                if v is None:
                    ctrl_fail += 1
                else:
                    ctrl.append(v)
    a_daily = [r["o"]["expl50_daily"] for r in rows if r["o"]["expl50_daily"] is not None]
    if ctrl and a_daily:
        pa, pc = sum(a_daily) / len(a_daily), sum(ctrl) / len(ctrl)
        log(f"🎲 V-O7/OP-P6 الشاهد C (n={len(ctrl)} · تعذّر {ctrl_fail}): expl50_daily مراسٍ {pa * 100:.1f}% مقابل شاهد {pc * 100:.1f}% "
            f"⇒ {(pa / pc if pc else float('inf')):.1f}× {'✅ ≥5×' if (pc == 0 or pa / pc >= 5) else '❌ دون 5×'}")
    else:
        log(f"🎲 الشاهد C: لم يُقَس (كون {len(uni)} · قِيس {len(ctrl)} · تعذّر {ctrl_fail})")
    # ── الميزات
    FEATS = ["rsi14", "rsi_min20", "float_d", "avail_d", "member", "gate", "drop52", "base_rng", "dvol20", "spike",
             "split_days", "px_prev", "gap", "tod", "j1", "j1pre"]
    log("\n" + "=" * 78 + "\n🔗 الميزاتُ على exploded50 (العقد §⑤)\n" + "=" * 78)
    links, verdicts = [], {}
    for feat in FEATS:
        table, v = judge(rows, feat, h2_from)
        verdicts[feat] = v
        log(f"\n▶ {feat}: {fmt_table(table)}")
        if v.get("best") is not None and "n" in v:
            log(f"   الأعلى «{v['best']}» {v['best_rate']:.1f}% مقابل {v['rest_rate']:.1f}% · n={v['n']} · "
                f"①{'✅' if v['c1'] else '❌'} ②{'✅' if v['c2'] else '❌'} ③✅ ④{'✅' if v['c4'] else '❌'} ⇒ {v['why']}")
            outside = [r for r in rows if r["f"]["j1pre"] != "نعم"]
            _t2, v2 = judge(outside, feat, h2_from)
            adds = bool(v2.get("c1") and v2.get("c2") and v2.get("best") == v["best"])
            v["adds"] = adds
            log(f"   ⑤ خارج J1∧pre (n={len(outside)}): {v2.get('why')} ⇒ {'يضيف ✅' if adds else 'لا يضيف ❌'}")
            if v["ok"] and adds and feat not in ("j1", "j1pre", "tod"):
                links.append(feat)
        else:
            log(f"   {v['why']}")
    # ── فرضيّاتُ المالك مجتمعةً
    log("\n" + "=" * 78 + "\n🧪 فرضيّاتُ المالك (مؤرَّخًا · مجهولٌ لا يُحتسب)\n" + "=" * 78)
    combos = {"rsi<30": ("rsi<30",), "float<4م": ("float<4م",), "avail<20k": ("avail<20k",),
              "rsi<30 ∧ float<4م": ("rsi<30", "float<4م"), "rsi<30 ∧ avail<20k": ("rsi<30", "avail<20k"),
              "float<4م ∧ avail<20k": ("float<4م", "avail<20k"), "الثلاثة معًا": ("rsi<30", "float<4م", "avail<20k")}
    combo_v = {}
    for name, ks in combos.items():
        def getf(r, ks=ks):
            fl = r["dated"].get("float") if r["dated"] else None
            av = r["dated"].get("avail") if r["dated"] else None
            fs = owner_flags(r["f"], fl, av)
            vals = [fs[k] for k in ks]
            return "؟" if any(v is None for v in vals) else ("نعم" if all(vals) else "لا")
        table, v = judge(rows, name, h2_from, getf=getf)
        combo_v[name] = v
        log(f"▶ {name}: {fmt_table(table)} ⇒ {v.get('why')}"
            + (f" (الأعلى «{v['best']}»)" if v.get("best") else ""))
    # ── SXTC (العقد §④ · OP-P5)
    log("\n" + "=" * 78 + "\n🎯 SXTC حالةً مسمّاة\n" + "=" * 78)
    for day in ("2026-09-04", "2026-09-11"):
        bars = daily_cache.get("SXTC") or daily_bars("SXTC", d0, until, key, "true")
        df = daily_frame(bars, day)
        af = anchor_features(df, day, split_cache.get("SXTC") or splits_of("SXTC", key))
        mem = member_by_day.get(day) or membership(day, snapshot_before(commits["weekly_watchlist.json"], day,
                                                                       lambda h: _load(h, "weekly_watchlist.json"))[1])
        m = mem.get("SXTC", (False, False))
        log(f"SXTC@{day}: عضو={m[0]} جاهز={m[1]} · بوّابة={gate_of('SXTC', df)} · "
            f"RSI14={af[0]['rsi14']:.1f} drop52={af[0]['drop52']:.0f}% base={af[0]['base_rng']:.0f}% "
            f"dvol20=${af[0]['dvol20']:,.0f} spike={af[0]['spike']}" if af else f"SXTC@{day}: بلا شموع كافية")
    # ── الحكم
    log("\n" + "=" * 78 + "\n🏁 الحكم (العقد §⑤)\n" + "=" * 78)
    v_member = verdicts.get("member", {})
    mem_share = sum(1 for r in rows if r["f"]["member"] == "عضو") / n * 100
    expl = [r for r in rows if r["o"]["exploded50"]]
    mem_expl = (sum(1 for r in expl if r["f"]["member"] == "عضو") / len(expl) * 100) if expl else float("nan")
    gates = collections.Counter(r["f"]["gate"] for r in rows if r["f"]["member"] != "عضو")
    log(f"📋 عضويّةُ «الجاهز» يومَ المرساة: {mem_share:.1f}% من المراسي · {mem_expl:.1f}% من المنفجرين · "
        f"بوّاباتُ رفض غير الأعضاء: {gates.most_common(6)}")
    if n < MIN_ROWS:
        branch = f"الفرعُ 3 «لا قياس» — المراسي المقيسة {n} دون 100"
    elif links:
        branch = f"الفرعُ 1 «رابطٌ مقيس» — {links}"
    else:
        dup = [f for f, v in verdicts.items() if v.get("ok") and not v.get("adds")]
        branch = "الفرعُ 2 «لا رابط»" + (f" — عابرٌ لكنه مكرِّرٌ لـJ1∧pre: {dup}" if dup else "")
    log(f"🏁 {branch}")
    rsi_v = verdicts.get("rsi14", {})
    log("🔮 التنبّؤات: "
        f"OP-P1 {'✅' if not (rsi_v.get('ok') and rsi_v.get('best') == '<30') else '❌'} · "
        f"OP-P2 {'✅' if (verdicts.get('float_d', {}).get('best') == '<4م' and not verdicts['float_d'].get('ok')) else '❌'} · "
        f"OP-P3 {'✅' if not verdicts.get('avail_d', {}).get('c4') else '❌'} · "
        f"OP-P4 {'✅' if (mem_share < 15 and (expl and mem_expl <= mem_share)) else '❌'} · "
        f"OP-P5/OP-P6 تُقرأ من الأسطر أعلاه")
    log("🔒 قراءةٌ فقط — لا يُشحَن شيءٌ مهما كانت النتيجة (العقد §⑧).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
