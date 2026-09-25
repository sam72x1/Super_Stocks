#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏱️🕵️ `T-ALERT-TIME` — «بعد كم يوم ينفجر؟» على تنبيهات «هنا الدخول» **الحقيقيّة وحدَها** (العقد `alert_timing_prereg.md`
— مدفوعٌ ومدموجٌ **قبل أيّ رقم**).

المجتمع: كلُّ مرساة `LIQ:*` في تاريخ git لـ`op_entry_state.json` منذ 2026-08-17 (`tierlink_probe.anchor_history` بالاسم) —
**لا صفوفَ باكتيست**. يومُ 0 بـ`prelink_probe.day0_of` بالاسم · الشموعُ اليوميّة `adjusted=true` بـ`prelink_probe.ticker_daily_adj`
بالاسم · RSI14 بـ`Super_stock.rsi` بالاسم على نافذة الحاكمة (الجلساتُ الستّون قبل يوم 0) · الفلوت/المتاح المؤرَّخان بـ
`opentry_link_probe.dated_values` بالاسم ويُفضَّل المتاحُ الأماميّ من `shadow_ready_ledger.jsonl` · والاحتمالُ التراكميّ
Kaplan-Meier مع المراقَبة (المتابعةُ الناقصة مُراقَبةٌ لا «لم ينفجر»).

⓪ `V-T1` قبل أيّ رقم: اتّفاقُ «+100% خلال 10» و«RSI أقلّ من 30» مع صفوف الحاكمة A (artifact `prelink-rows-36163255276`) ‏≥95%
   على ‏≥300 تنبيهٍ مشترك · و`V-T2` التغطيةُ ‏≥80% — وإلّا خروج 3 ولا يُطبع رقم.

**بُنيت لـ…** (قاعدةُ الحزمة): `day0_of`/`ticker_daily_adj`/`_selfcheck_readonly` بُنيت لـ`T-PRELINK` على المراسي نفسِها — مطابق ·
`dated_values`/`snapshot_before` بُنيت لـ`T-OPLINK` لقيم «≤ يوم المرساة» — مطابق · `anchor_history` بُنيت لقراءة المراسي من git — مطابق.

🔒 قراءةٌ فقط (`prelink_probe._selfcheck_readonly` بالاسم على مصدرها): لا تلغرام · لا كتابةَ حالة · لا `LOGIC_VERSION` · لا شيءَ يُشحَن.
الخروج: 0 قياس · 2 بلا مفتاح · 3 `V-T1`/`V-T2` ساقط أو صفوفُ الحاكمة غائبة · 4 صفرُ تنبيه · 5 ليست قراءةً فقط.
"""
import collections
import datetime as dt
import json
import os
import subprocess
import sys

import pandas as pd

import Super_stock as S                                              # rsi بالاسم
import prelink_probe as P                                            # day0_of · ticker_daily_adj · _selfcheck_readonly · ROWS_PREFIX
import opentry_link_probe as OPL                                     # _commits · snapshot_before · dated_values · SNAP_FILES · الحدود
from tierlink_probe import anchor_history                            # بالاسم
from link100_probe import year_days                                  # بالاسم
from kasih_scan import NY                                            # بالاسم

SINCE = os.environ.get("ALERT_SINCE") or "2026-08-17"
UNTIL = (os.environ.get("ALERT_UNTIL") or "").strip()                # فارغ = أمسُ نيويورك
ROWS_DIR = os.environ.get("PRELINK_ROWS_DIR") or "prelink_rows"
LEDGER = os.environ.get("SHADOW_LEDGER") or "shadow_ready_ledger.jsonl"
GOV_RUN = "36163255276"
HORIZON = 20                   # 🔒 §②-6: الجلساتُ 1-20 بعد يوم 0
KS = (1, 2, 3, 5, 10, 20)      # 🔒 §②-7
BACK = 60                      # 🔒 §②-3/5: نافذةُ الحاكمة `adj_window(back=60)`
MIN_RSI_BARS, MIN_LOW_BARS = 21, 20
MIN_N, MIN_EV = 20, 5          # 🔒 §③: أرضيّةُ الاحتمال · أرضيّةُ الوسيط
V_AGREE, V_MIN_SHARED, V_MIN_FOLLOW = 0.95, 300, 10                  # 🔒 §④
MIN_COVER = 0.80               # 🔒 §④ V-T2
FETCH_BACK_DAYS = 150          # §②-2: أيّامٌ تقويميّة قبل أوّل تنبيهٍ للرمز (‏≥60 جلسة)


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── التقويمُ والتنبيه ───────────────────────────
def calendar():
    """أيّامُ التداول 2022-2026 بالاسم (`year_days`) ⟵ (قائمة, فهرس) — الفهرسُ نفسُه في لوحة الحاكمة."""
    days = []
    for y in ("2022", "2023", "2024", "2025", "2026"):
        days += year_days(y)
    return days, {d: i for i, d in enumerate(days)}


def hhmm_of(a):
    """ساعةُ التنبيه بنيويورك من `anchor_ms` ⟵ «HH:MM» أو None."""
    try:
        return dt.datetime.fromtimestamp(int(a["anchor_ms"]) / 1000, tz=NY).strftime("%H:%M")
    except (KeyError, TypeError, ValueError, OSError, OverflowError):
        return None


def first_hit(fwd, close0, pct):
    """`fwd` = [(k, high أو None)] للجلسات 1..F بترتيبها ⟵ أوّلُ k فيه `(high ÷ close0 − 1) × 100 ≥ pct` — بصيغة الحاكمة حرفًا — أو None."""
    for k, h in fwd:
        if h is not None and (h / close0 - 1) * 100 >= pct:
            return k
    return None


def alert_row(a_day, sym, hhmm, bars, days, didx, last_i):
    """تنبيهٌ واحد ⟵ (صفّ, None) أو (None, سبب) — **نقيّة بلا شبكة**. `bars` = {تاريخ: (o, h, l, c, v)} مسوّاةٌ `adjusted=true`."""
    d0, _after = P.day0_of(a_day, hhmm, days, didx)
    if d0 is None or d0 not in didx:
        return None, "خارج التقويم"
    i0 = didx[d0]
    if i0 > last_i:
        return None, "أحدثُ من البيانات"
    b0 = bars.get(d0)
    if b0 is None or not b0[3] or b0[3] <= 0:
        return None, "بلا شمعة يوم 0"
    c0, l0 = float(b0[3]), float(b0[2])
    F = max(0, min(HORIZON, last_i - i0))
    pre = [bars[d] for d in days[max(0, i0 - BACK):i0] if d in bars]
    pre_c = [float(b[3]) for b in pre]
    pre_l = [float(b[2]) for b in pre]
    rsi14 = None
    if len(pre_c) >= MIN_RSI_BARS:
        rs = S.rsi(pd.Series(pre_c, dtype=float))
        rsi14 = float(rs.iloc[-1]) if len(rs) >= 15 else None
    new_low = (l0 <= min(pre_l)) if len(pre_l) >= MIN_LOW_BARS else None
    fwd = [(k, (float(bars[days[i0 + k]][1]) if days[i0 + k] in bars else None)) for k in range(1, F + 1)]
    hs = [h for _k, h in fwd if h is not None]
    mg = ((max(hs) / c0 - 1) * 100) if hs else (None if F == 0 else -100.0)
    return {"day": a_day, "sym": sym, "hhmm": hhmm, "day0": d0, "close0": c0, "F": F, "rsi14": rsi14,
            "new_low": new_low, "t50": first_hit(fwd, c0, 50.0), "t100": first_hit(fwd, c0, 100.0), "mg": mg}, None


# ─────────────────────────── الفلوت/المتاح المؤرَّخان ───────────────────────────
def dated_for_days(alert_days):
    """{يومُ التنبيه: {رمز: {float, avail, src}}} من لقطات git ‏≤ اليوم (`OPL._commits`/`snapshot_before`/`dated_values` بالاسم)."""
    commits = {f: OPL._commits(f) for f in OPL.SNAP_FILES}
    cache = {}

    def _load(h, f):
        if (h, f) not in cache:
            try:
                cache[(h, f)] = json.loads(subprocess.run(["git", "show", f"{h}:{f}"], capture_output=True, text=True).stdout)
            except Exception:                                        # noqa: BLE001
                cache[(h, f)] = None
        return cache[(h, f)]

    out = {}
    for day in sorted(set(alert_days)):
        snaps = {f: OPL.snapshot_before(commits[f], day, lambda h, f=f: _load(h, f)) for f in OPL.SNAP_FILES}
        out[day] = OPL.dated_values(day, snaps)
    return out


def load_shadow_ledger(path):
    """المتاحُ الأماميّ لكلّ (تاريخ، رمز) من دفتر `T-SHADOW` (R-03) ⟵ {} إن غاب الملفّ (لا «لا»)."""
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    k = (r.get("date"), r.get("symbol"))
                    if all(k) and r.get("avail") is not None:
                        out[k] = float(r["avail"])
                except (ValueError, TypeError, AttributeError):
                    continue
    except OSError:
        pass
    return out


def attach_dated(rows, dated, ledger):
    """يُلحق الفلوت/المتاح المؤرَّخين بكلّ صفّ — **والمتاحُ الأماميّ من الدفتر يُفضَّل** إن وُجد للتنبيه نفسِه (§②-4)."""
    for r in rows:
        dv = (dated.get(r["day"]) or {}).get(r["sym"]) or {}
        r["float"] = dv.get("float")
        r["avail"] = dv.get("avail")
        r["avail_src"] = "git" if r["avail"] is not None else None
        lv = ledger.get((r["day"], r["sym"]))
        if lv is not None:
            r["avail"], r["avail_src"] = lv, "ledger"
    return rows


def flags(r):
    """شروطُ المالك ⟵ True/False/None لكلّ شرط — **المجهولُ None لا «لا»** · والاقترانُ False إن سقط أيُّ شرطٍ معلوم."""
    rsi = None if r.get("rsi14") is None else r["rsi14"] < OPL.RSI_OWNER
    fl = None if r.get("float") is None else r["float"] < OPL.FLOAT_OWNER
    av = None if r.get("avail") is None else r["avail"] < OPL.AVAIL_OWNER

    def conj(*xs):
        if any(x is False for x in xs):
            return False
        if any(x is None for x in xs):
            return None
        return True
    return {"rsi": rsi, "float": fl, "avail": av, "pair": conj(fl, av), "triple": conj(rsi, fl, av), "new_low": r.get("new_low")}


GROUPS = (("الكلّ", lambda f: True),
          ("RSI أقلّ من 30", lambda f: f["rsi"] is True), ("RSI 30 فأكثر", lambda f: f["rsi"] is False),
          ("فلوت أقلّ من 4م", lambda f: f["float"] is True), ("فلوت 4م فأكثر", lambda f: f["float"] is False),
          ("متاح أقلّ من 20 ألفًا", lambda f: f["avail"] is True), ("متاح 20 ألفًا فأكثر", lambda f: f["avail"] is False),
          ("فلوت ∧ متاح", lambda f: f["pair"] is True),
          ("الثلاثةُ معًا", lambda f: f["triple"] is True),
          ("قاعٌ جديد", lambda f: f["new_low"] is True), ("ليس قاعًا جديدًا", lambda f: f["new_low"] is False))


# ─────────────────────────── القياس ───────────────────────────
def km(rows, key="t100"):
    """Kaplan-Meier على `key` مع المراقَبة ⟵ {n, events, curve: {j: P(j)} لـ1..20, P: لـ`KS`, at_risk: {j: n_j}} —
    **المتابَعون جلسةً فأكثر وحدَهم** · والمراقَبُ عند F تحت المراقبة للجلسات 1..F ثمّ يخرج."""
    obs = [(r[key], 1) if r.get(key) is not None else (r["F"], 0) for r in rows if r.get("F", 0) >= 1]
    surv, curve, at = 1.0, {}, {}
    for j in range(1, HORIZON + 1):
        n_j = sum(1 for t, _e in obs if t >= j)
        d = sum(1 for t, e in obs if e and t == j)
        if n_j:
            surv *= (1 - d / n_j)
        curve[j], at[j] = 1 - surv, n_j
    return {"n": len(obs), "events": sum(e for _t, e in obs), "curve": curve, "P": {j: curve[j] for j in KS}, "at_risk": at}


def event_stats(rows, key="t100"):
    """وسيطُ يوم الانفجار وربيعاه **بشرط الانفجار خلال 20 من منحنى KM نفسِه** (§②-7: الربيعُ q = أصغرُ j فيه
    `P(j) ≥ q × P(20)`) — لا وسيطًا خامًّا يتحيّز بالمراقَبة ⟵ dict أو None إن كانت الأحداثُ دون `MIN_EV`."""
    k = km(rows, key)
    p20 = k["curve"][HORIZON]
    if k["events"] < MIN_EV or p20 <= 0:
        return None

    def q_(q):
        return next(j for j in range(1, HORIZON + 1) if k["curve"][j] >= q * p20 - 1e-12)
    return {"n": k["events"], "median": q_(0.5), "q1": q_(0.25), "q3": q_(0.75)}


def group_measure(name, rows):
    """مجموعةٌ واحدة ⟵ {name, rows, n, syms, n0, km100, km50, ev100, ev50} — `km*` None دون `MIN_N` و`ev*` None دون `MIN_EV`."""
    fol = [r for r in rows if r["F"] >= 1]
    k100, k50 = km(fol, "t100"), km(fol, "t50")
    return {"name": name, "rows": rows, "n": len(fol), "syms": len({r["sym"] for r in rows}), "n0": len(rows) - len(fol),
            "km100": k100 if len(fol) >= MIN_N else None, "km50": k50 if len(fol) >= MIN_N else None,
            "ev100": event_stats(fol, "t100"), "ev50": event_stats(fol, "t50")}


def _pct(x):
    return f"{x * 100:.1f}%"


def _fmt_km(k):
    return (" · ".join(f"P({j}) {_pct(k['P'][j])}" for j in KS)
            + f" · متابَعون حتى 10: {k['at_risk'][10]} · حتى 20: {k['at_risk'][HORIZON]}")


def _fmt_ev(e):
    return "—" if not e else f"وسيطُ يوم الانفجار {e['median']:g} [ربيعاه {e['q1']:g}-{e['q3']:g}]"


def group_lines(g, histogram=False):
    """أسطرُ مجموعة: الاحتمالُ والوسيط إن بلغا أرضيّتيهما — **وإلّا «لا قياس» والتنبيهاتُ سردًا** (§③)."""
    out = [f"▶ {g['name']}: n={g['n']} (رموزٌ {g['syms']}) · بلا متابعةٍ بعد {g['n0']}"]
    fol = [r for r in g["rows"] if r["F"] >= 1]
    for lab, kk, ev in (("+100%", g["km100"], g["ev100"]), ("+50%", g["km50"], g["ev50"])):
        if kk:
            out.append(f"   {lab}: {_fmt_km(kk)} · أحداث {kk['events']} · {_fmt_ev(ev)}")
        else:
            out.append(f"   {lab}: «لا قياس» (n={g['n']} دون {MIN_N}) · {_fmt_ev(ev)}")
    if histogram:
        hc = collections.Counter(r["t100"] for r in fol if r.get("t100") is not None)
        out.append("   أيّامُ الانفجار +100% خامًّا (يتأثّر بالمراقَبة · وصفٌ لا حكم): "
                   + (" · ".join(f"ج{k} {hc[k]}" for k in sorted(hc)) or "لا شيء"))
    if not g["km100"]:
        for r in sorted(g["rows"], key=lambda r: (r["day"], r["sym"])):
            mg = "—" if r.get("mg") is None else f"{r['mg']:+.0f}%"
            rsi = "—" if r.get("rsi14") is None else f"{r['rsi14']:.1f}"
            fl = "—" if r.get("float") is None else f"{r['float'] / 1e6:.2f}م"
            av = "—" if r.get("avail") is None else f"{r['avail']:,.0f}"
            out.append(f"      • {r['sym']} {r['day']} (يومُ 0 {r['day0']}) · t50 {r.get('t50') or '—'} · t100 {r.get('t100') or '—'} · "
                       f"متابعة {r['F']} · أقصى صعودٍ {mg} · RSI {rsi} · فلوت {fl} · متاح {av}")
    return out


# ─────────────────────────── V-T1 · V-T2 ───────────────────────────
def load_gov_A(d):
    """صفوفُ الحاكمة A (artifact) ⟵ قائمة أو None إن غاب الملفّ."""
    path = os.path.join(d, f"{P.ROWS_PREFIX}A.jsonl")
    if not os.path.exists(path):
        return None
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def vt1(rows, gov):
    """⟵ (ok, أسطر): الاتّفاقُ مع الحاكمة A على التنبيهات المشتركة (يومُ 0 نفسُه · متابعةٌ ‏≥10 في الطرفين) (§④)."""
    mine = {(r["day"], r["sym"]): r for r in rows}
    sh_l = ag_l = sh_r = ag_r = 0
    for g in gov:
        m = mine.get((g.get("day"), g.get("sym")))
        gl = (g.get("o") or {}).get("late100_10")
        if m is None or m["day0"] != g.get("day0") or gl is None or m["F"] < V_MIN_FOLLOW:
            continue
        sh_l += 1
        ag_l += int(bool(gl) == (m["t100"] is not None and m["t100"] <= 10))
        gr = (g.get("raw") or {}).get("rsi14")
        if gr is not None and m["rsi14"] is not None:
            sh_r += 1
            ag_r += int((gr < OPL.RSI_OWNER) == (m["rsi14"] < OPL.RSI_OWNER))
    al = ag_l / sh_l if sh_l else 0.0
    ar = ag_r / sh_r if sh_r else 0.0
    ok = sh_l >= V_MIN_SHARED and sh_r >= V_MIN_SHARED and al >= V_AGREE and ar >= V_AGREE
    lines = [f"   «+100% خلال 10»: {ag_l}/{sh_l} = {al * 100:.1f}% (الحدّ {V_AGREE * 100:.0f}% على {V_MIN_SHARED} فأكثر)",
             f"   «RSI أقلّ من 30»: {ag_r}/{sh_r} = {ar * 100:.1f}%"]
    return ok, lines


# ─────────────────────────── التنبّؤات (§⑤) ───────────────────────────
def eval_predictions(gm, n_triple):
    """`gm` = {اسمُ المجموعة: قياسُها} ⟵ {AT-Pi: (✅/❌/⚪, شرح)}."""
    out = {"AT-P1": ("✅" if n_triple < 5 else "❌", f"الثلاثةُ معًا {n_triple} تنبيهًا")}
    e = gm["الكلّ"]["ev100"]
    out["AT-P2"] = ("⚪", "أحداثٌ دون 5") if not e else (("✅" if 3 <= e["median"] <= 8 else "❌"), f"الوسيط {e['median']:g}")
    a, b = gm["قاعٌ جديد"]["ev100"], gm["ليس قاعًا جديدًا"]["ev100"]
    out["AT-P3"] = ("⚪", "أحداثُ إحداهما دون 5") if not (a and b) else \
        (("✅" if abs(a["median"] - b["median"]) <= 1 else "❌"), f"{a['median']:g} مقابل {b['median']:g}")
    ka, kb = gm["RSI أقلّ من 30"]["km100"], gm["RSI 30 فأكثر"]["km100"]
    if not (ka and kb):
        out["AT-P4"] = ("⚪", "إحدى المجموعتين دون 20")
    else:
        pa, pb = ka["P"][10], kb["P"][10]
        ratio = (1.0 if pa == 0 else float("inf")) if pb == 0 else pa / pb
        out["AT-P4"] = (("✅" if 0.67 <= ratio <= 1.5 else "❌"), f"P(10) {_pct(pa)} مقابل {_pct(pb)} = {ratio:.2f}×")
    return out


# ─────────────────────────── الجلب ───────────────────────────
def fetch_bars(sym, d0, d1, key):
    """شموعُ الرمز `adjusted=true` ⟵ {تاريخ: (o, h, l, c, v)} (`ticker_daily_adj` بالاسم)."""
    return {d: (o, h, lo, c, v) for (d, o, h, lo, c, v) in (P.ticker_daily_adj(sym, d0, d1, key) or [])}


def main() -> int:                                                   # noqa: PLR0911, PLR0912, PLR0915
    src = open(__file__, encoding="utf-8").read()
    if not P._selfcheck_readonly(src):
        log("⛔ الحارسُ الذاتيّ: الأداةُ ليست قراءةً فقط — خروج 5")
        return 5
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    until = UNTIL or (dt.datetime.now(NY).date() - dt.timedelta(days=1)).isoformat()
    log(f"⏱️🕵️ T-ALERT-TIME «بعد كم يوم ينفجر؟» · تنبيهاتٌ حقيقيّة وحدَها منذ {SINCE} حتى {until} · الحاكمة {GOV_RUN}")
    anchors = {k: v for k, v in anchor_history(since=SINCE).items() if k[0] <= until}
    if not anchors:
        log("⛔ صفرُ تنبيهٍ في تاريخ git (بصمةُ no-op) — خروج 4")
        return 4
    gov = load_gov_A(ROWS_DIR)
    if gov is None:
        log(f"⛔ «لا قياس» — صفوفُ الحاكمة غائبة ({ROWS_DIR}) · خروج 3")
        return 3
    days, didx = calendar()
    first_day = collections.defaultdict(lambda: "9999")
    for (day, sym) in anchors:
        first_day[sym] = min(first_day[sym], day)
    syms = sorted(first_day)
    log(f"📥 تنبيهات {len(anchors)} على {len(syms)} رمزًا · الشموعُ اليوميّة adjusted=true لكلّ رمز")
    bars, fail = {}, 0
    for i, sym in enumerate(syms, 1):
        d0 = (dt.date.fromisoformat(first_day[sym]) - dt.timedelta(days=FETCH_BACK_DAYS)).isoformat()
        b = fetch_bars(sym, d0, until, key)
        if not b:
            fail += 1
        bars[sym] = b
        if i % 100 == 0:
            log(f"   … {i}/{len(syms)}")
    seen = [d for b in bars.values() for d in b if d <= until and d in didx]
    if not seen:
        log("⛔ «لا قياس» — صفرُ شمعةٍ مجلوبة · خروج 3")
        return 3
    last_day = max(seen)
    last_i = didx[last_day]
    rows, why = [], collections.Counter()
    for (day, sym) in sorted(anchors):
        hh = hhmm_of(anchors[(day, sym)])
        if hh is None:
            why["بلا ساعة"] += 1
            continue
        r, reason = alert_row(day, sym, hh, bars.get(sym) or {}, days, didx, last_i)
        if r is None:
            why[reason] += 1
            continue
        rows.append(r)
    denom = len(anchors) - why.get("أحدثُ من البيانات", 0)
    cover = len(rows) / denom if denom else 0.0
    log(f"🩺 V-T2 التغطية: قِيس {len(rows)} من {denom} = {cover * 100:.1f}% · آخرُ جلسةٍ في البيانات {last_day} · "
        f"رموزٌ تعذّر جلبُها {fail} · الأسباب {dict(why)}")
    if cover < MIN_COVER:
        log("⛔ V-T2 ساقط (التغطية دون 80%) — لا يُطبع رقم · خروج 3")
        return 3
    ok, lines = vt1(rows, gov)
    log(f"\n{'=' * 78}\n🔒 V-T1 — الاتّفاقُ مع صفوف الحاكمة A (قبل أيّ رقم)\n{'=' * 78}")
    for ln in lines:
        log(ln)
    if not ok:
        log("⛔ V-T1 ساقط — «لا قياس» ولا يُطبع رقم · خروج 3")
        return 3
    log("✅ V-T1 عابر")
    dated = dated_for_days([r["day"] for r in rows])
    ledger = load_shadow_ledger(LEDGER)
    attach_dated(rows, dated, ledger)
    fl_all = [flags(r) for r in rows]
    log(f"🧾 معلومٌ: RSI {sum(f['rsi'] is not None for f in fl_all)} · فلوت {sum(f['float'] is not None for f in fl_all)} · "
        f"متاح {sum(f['avail'] is not None for f in fl_all)} (من الدفتر الأماميّ {sum(1 for r in rows if r.get('avail_src') == 'ledger')}) · "
        f"قاعٌ جديد {sum(f['new_low'] is not None for f in fl_all)} · من {len(rows)}")
    gm = {}
    log(f"\n{'=' * 78}\n⏱️ المجموعات (§③) — Kaplan-Meier مع المراقَبة · يومُ 0 = أوّلُ إغلاقٍ نظاميّ عند التنبيه أو بعده\n{'=' * 78}")
    for name, pred in GROUPS:
        sub = [r for r, f in zip(rows, fl_all) if pred(f)]
        gm[name] = group_measure(name, sub)
        for ln in group_lines(gm[name], histogram=(name == "الكلّ")):
            log(ln)
    n_triple = sum(1 for f in fl_all if f["triple"] is True)
    pr = eval_predictions(gm, n_triple)
    log(f"\n{'=' * 78}\n🏁🏁 الخلاصة — «بعد كم يوم ينفجر؟» على التنبيهات الحقيقيّة وحدَها\n{'=' * 78}")
    for name in ("الكلّ", "RSI أقلّ من 30", "فلوت أقلّ من 4م", "متاح أقلّ من 20 ألفًا", "فلوت ∧ متاح", "الثلاثةُ معًا",
                 "قاعٌ جديد", "ليس قاعًا جديدًا"):
        g = gm[name]
        k = g["km100"]
        body = (f"+100% خلال 5 {_pct(k['P'][5])} · خلال 10 {_pct(k['P'][10])} · خلال 20 {_pct(k['P'][20])} "
                f"(متابَعون حتى 20: {k['at_risk'][HORIZON]}) · أحداث {k['events']} · {_fmt_ev(g['ev100'])}"
                if k else f"«لا قياس» (n={g['n']} دون {MIN_N})")
        log(f"   ▸ {name} (n={g['n']}): {body}")
    for kk, (st, why_) in pr.items():
        log(f"   🔮 {kk}: {st} ({why_})")
    g = gm["الكلّ"]
    tail = (f"الكلّ: وسيطُ يوم الانفجار +100% {g['ev100']['median']:g} جلسة" if g["ev100"] else "الكلّ: أحداثٌ دون 5")
    log(f"\n🏁 الثلاثةُ معًا: {'«لا قياس»' if gm['الثلاثةُ معًا']['km100'] is None else 'مقيس'} ({n_triple} تنبيهًا) · {tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
