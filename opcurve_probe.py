#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️📈 `T-OPCURVE` — منحنى ما بعد مِرساة «هنا الدخول» (وصفيٌّ · يُنشَر جدولٌ ولا يُحكَم).

**العقد:** `opcurve_prereg.md` (مدفوعٌ ومدموجٌ `f3d6a5c6` قبل هذا الملفّ). أمرُ المالك
«سجل المنحنى» ثمّ «ابن الاداة» (‏2026-09-15/16).

المجتمع **ثلاثُ طبقاتٍ لا انتقاء** (العقد §②): (A) كلُّ مِرساةِ سيولةٍ حيّة من تاريخ git
لـ`op_entry_state.json` · (B) كروتُ `M5` في `tier_fwd_ledger.jsonl` · (C) وسمُ الزناد
`trig` بعد `SHIP_ISO` فقط.

🔒 **مقياسٌ واحدٌ لا اثنان:** `tierlink_probe.anchor_history`/`features`/`daily_range` ·
`tier_fwd_report.fetch_day`/`load_ledger` · `tier_days_report.true_e5` ·
`sym_day_probe.full_day_max`/`exit_point` · `kasih_scan.NY`/`wilson` ·
`btcost_arms.boot_ci_median`/`pctile` · `liq_trig_read.SHIP_ISO` — **بالاسم**؛ صفرُ
منطقِ حسمٍ مكرَّر. والأساسُ `e5` والنافذةُ `t0 = anchor_ms + 4 دقائق` هما عينُ ما أُنتجت
به أرقامُ `T-TIERLINK` (‏`V-C7`).

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · والإنتاجُ لا يستورده.
🔒 **لا يُحسَب «‏+10% قبل الوقف» مركَّبًا ولا `R` ولا تكلفة** (العقد §③) — حكمُ
`T-OPTRADE` يبقى غيرَ مُطَّلَعٍ عليه.

**رموزُ الخروج:** 0 صدر · 2 لا مفتاح (‏`V-C1`) · 3 تغطيةُ الجلب دون 80% (‏`V-C3` — لا
يُفسَّر رقم) · 4 صفرُ مِرساة (‏`V-C2` بصمةُ no-op) · **5 المستردُّ يخالف المخزون** (‏`V-C10` ·
الملحق §⑪-6 — ولا يُنشَر رقمٌ مستردّ).
"""
import collections
import datetime as dt
import os
import statistics as st
import sys

from tierlink_probe import anchor_history, features, daily_range        # بالاسم
from tier_fwd_report import fetch_day, load_ledger                       # بالاسم
from tier_days_report import true_e5                                     # بالاسم
from sym_day_probe import full_day_max, exit_point                       # بالاسم
from kasih_scan import NY, wilson                                        # بالاسم
from btcost_arms import boot_ci_median, pctile                           # بالاسم
from liq_trig_read import SHIP_ISO                                       # بالاسم

SINCE = os.environ.get("OPCURVE_SINCE", "2026-08-18")          # العقد §②
H2_FROM = os.environ.get("OPCURVE_H2_FROM", "2026-09-01")      # العقد §④ — النصفان
UNTIL = os.environ.get("OPCURVE_UNTIL", "").strip()            # §⑪-5 — فارغٌ = يومُ التشغيل (السلوكُ القائم)
HORIZONS = (5, 15, 30, 60)                                     # العقد §③ — بالدقائق الجداريّة
W_SET = (15, 30, 60, 120, 240)                                 # العقد §⑦ — قاعدةُ النافذة `W`
MIN_COVER = 0.80                                               # `V-C3`
MIN_HITS = 30                                                  # §⑦ — دون 30 ⇒ `EOD`
TRIG_SMALL = 20                                                # `V-C9` — سلّةُ زنادٍ «صغيرة»
CARD_OFFSET_MS = 4 * 60_000                                    # `t0` = بدايةُ شمعة الكرت (= `card_ms` في tierlink)
HIT_PCT = 10.0                                                 # هدفُ `T-TARGET10` المعتمَد
CI_METRICS = ("up_60", "close_reg", "pm_last")                 # §④ — ثلاثةُ أرقامٍ رئيسة فقط
MIN_RECON_MATCH = 0.99                                         # `V-C10` (§⑪-6) — دونه خروج 5
RECON_TOL_PCT = 0.1                                            # `V-C10` — «مطابقة» = فرقٌ نسبيٌّ لا يتجاوزه
TSV_COLS = ("date", "sym", "trig", "tod", "tier", "j1", "gap", "exploded50",
            "up5", "up15", "up30", "up60", "dn60", "up_ext", "t_peak", "dd_pre_peak",
            "t_hit10", "t_stop", "close_reg", "pm_last", "low_src", "gap_src")   # §⑪-8
BUCKETS = ("الكلّ", "trig", "tod", "tier", "j1", "gap", "pre∧gap≥30%", "exploded50")


def ship_ms(iso: str = SHIP_ISO) -> int:
    """`SHIP_ISO` (‏Z) ⟶ ملّي ثانية — قبله لا زنادَ موازيًا (‏`V-C9`)."""
    return int(dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


SHIP_MS = ship_ms()


def ny_hour(ms: int) -> float:
    t = dt.datetime.fromtimestamp(ms / 1000, tz=NY)
    return t.hour + t.minute / 60.0


# ───────────────────── الاسترداد (‏§⑪-3 · `V-C10` — نقيّة) ──────────────────────
def _first(*vals):
    """أوّلُ قيمةٍ **ليست `None`** — فحصٌ صريحٌ لا صدقٌ (‏`0.0` ليست غيابًا · §⑪-3-4)."""
    for v in vals:
        if v is not None:
            return v
    return None


def resolve_anchor(a: dict, b, bars):
    """سعرُ المِرساة وقاعُها — من المخزون، وإلّا **من شمعة المِرساة بتعريف الإنتاج حرفيًّا**.

    الإنتاجُ يكتبهما هكذا بعينه: `anchor_price = round(float(bar.c), 4)` ·
    `anchor_low = round(float(bar.l), 4)` ⇒ الاستردادُ **ليس مُقدِّرًا جديدًا** (§⑪-3).
    ويُعاد معهما فرقُ المستردّ عن المخزون حيث يتوفّران معًا (‏`V-C10`)، وهل غيّر
    **التقريبُ** قيمةَ المستردّ (‏§⑪-4: لو غيّرها فقد يتحرّك `e5` لصفٍّ لا سجلَّ له).
    """
    a_ms = int(a["anchor_ms"])
    bar = next((x for x in bars if x[0] == a_ms), None)
    src = b or {}
    raw_p = float(bar[4]) if bar else None
    raw_l = float(bar[3]) if bar else None
    rec_p = None if raw_p is None else round(raw_p, 4)
    rec_l = None if raw_l is None else round(raw_l, 4)
    st_p = _first(a.get("anchor_price"), src.get("anchor_price"))
    st_l = _first(a.get("anchor_low"), src.get("anchor_low"))

    def _d(stored, rec):
        if stored is None or rec is None:
            return None
        return abs(float(stored) - rec)

    return {"ap": _first(st_p, rec_p), "alow": _first(st_l, rec_l),
            "ap_src": "مخزون" if st_p is not None else ("شمعة" if rec_p is not None else "—"),
            "low_src": "مخزون" if st_l is not None else ("شمعة" if rec_l is not None else "—"),
            "d_price": _d(st_p, rec_p), "d_low": _d(st_l, rec_l),
            "ref_price": None if st_p is None else abs(float(st_p)),
            "ref_low": None if st_l is None else abs(float(st_l)),
            "round_moved": bool((rec_p is not None and rec_p != raw_p)
                                or (rec_l is not None and rec_l != raw_l))}


def recon_check(diffs):
    """‏`V-C10` (§⑪-6): (‏قُورن · طابق · نسبة · أكبرُ فرقٍ مطلق · أكبرُ فرقٍ نسبيّ ٪).

    «المطابقة» = فرقٌ **نسبيٌّ** لا يتجاوز `RECON_TOL_PCT`؛ وتُطبَع معها المطابقةُ
    **التامّة** (بعد تقريب الإنتاج) فلا يُخفي التسامحُ فرقًا حقيقيًّا."""
    pairs = [(d, ref) for d, ref in diffs if d is not None and ref]
    n = len(pairs)
    if not n:
        return {"n": 0, "ok": 0, "exact": 0, "rate": None, "max_abs": None, "max_rel": None}
    rels = [d / ref * 100.0 for d, ref in pairs]
    ok = sum(1 for r in rels if r <= RECON_TOL_PCT)
    return {"n": n, "ok": ok, "exact": sum(1 for d, _r in pairs if d <= 1e-9),
            "rate": ok / n, "max_abs": max(d for d, _r in pairs), "max_rel": max(rels)}


# ───────────────────────── المسار (العقد §③ — نقيّة) ────────────────────────────
def path_stats(bars, t0: int, e5: float, alow):
    """المقاييسُ كلُّها من الشموع نفسِها · النوافذُ **بالساعة الجداريّة** لا بعدّ الشموع.

    `bars` = `(t, o, h, l, c, v)` تصاعديًّا · `t0` بدايةُ شمعة الكرت · `e5` سعرُ الكرت ·
    `alow` قاعُ المِرساة (أو `None` ⇒ `t_stop` غيرُ معروف ويُعَدّ لا يُخمَّن)."""
    after = [b for b in bars if b[0] > t0]
    out = {}
    for h in HORIZONS:
        w = [b for b in after if b[0] <= t0 + h * 60_000]
        out[f"up_{h}"] = (max(b[2] for b in w) / e5 - 1.0) * 100.0 if w else None
        out[f"dn_{h}"] = (min(b[3] for b in w) / e5 - 1.0) * 100.0 if w else None
        out[f"ret_{h}"] = (w[-1][4] / e5 - 1.0) * 100.0 if w else None
    reg = [b for b in after if ny_hour(b[0]) < 16]
    out["up_reg"] = (max(b[2] for b in reg) / e5 - 1.0) * 100.0 if reg else None
    out["dn_reg"] = (min(b[3] for b in reg) / e5 - 1.0) * 100.0 if reg else None
    out["close_reg"] = (reg[-1][4] / e5 - 1.0) * 100.0 if reg else None
    best, at = full_day_max(bars, t0, e5)                       # = `mg_day` المنشور
    out["up_ext"] = best
    out["t_peak"] = (at - t0) / 60_000.0 if at is not None else None
    pre = [b for b in after if at is not None and b[0] <= at]
    out["dd_pre_peak"] = (min(b[3] for b in pre) / e5 - 1.0) * 100.0 if pre else None
    hit = next((b for b in after if b[2] >= e5 * (1.0 + HIT_PCT / 100.0)), None)
    out["t_hit10"] = (hit[0] - t0) / 60_000.0 if hit else None
    out["hit10_reg"] = bool(hit and ny_hour(hit[0]) < 16)
    if alow:
        _xc, xt = exit_point(bars, t0, alow)
        out["t_stop"] = (xt - t0) / 60_000.0 if xt is not None else None
        out["stop_reg"] = bool(xt is not None and ny_hour(xt) < 16)
        out["stop_known"] = True
    else:
        out["t_stop"], out["stop_reg"], out["stop_known"] = None, False, False
    out["exploded50"] = bool(best is not None and best >= 50.0)
    return out


def pm_stats(next_bars, e5: float):
    """بريماركتُ يوم التداول التالي (ساعةُ نيويورك دون 9.5) · `None` إن لم يُتداوَل (‏`V-C8`)."""
    pm = [b for b in (next_bars or []) if ny_hour(b[0]) < 9.5]
    if not pm:
        return None
    return {"pm_up": (max(b[2] for b in pm) / e5 - 1.0) * 100.0,
            "pm_dn": (min(b[3] for b in pm) / e5 - 1.0) * 100.0,
            "pm_last": (pm[-1][4] / e5 - 1.0) * 100.0,
            "pm_n": len(pm)}


def trig_bucket(a: dict, ship: int = SHIP_MS) -> str:
    """‏`R1` / `T-C` بعد الشحن فقط · وقبله «قبل الشحن» (لا يدخل سلّةَ الزناد)."""
    if int(a["anchor_ms"]) < ship:
        return "قبل الشحن"
    return "T-C" if a.get("trig") else "R1"


def buckets_of(f: dict, trig: str, exploded: bool) -> dict:
    """السلالُ المُغلَقة (العقد §④) — لا تُضاف سلّةٌ بعد الأرقام."""
    return {"الكلّ": "الكلّ", "trig": trig, "tod": f["tod"], "tier": f["tier"],
            "j1": f["j1"], "gap": f["gap"],
            "pre∧gap≥30%": "نعم" if (f["tod"] == "pre" and f["gap"] == "≥30%") else "لا",
            "exploded50": "نعم" if exploded else "لا"}


# ───────────────────────── الإحصاء (نقيّ · حتميّ) ───────────────────────────────
def _vals(rows, key, src="o"):
    return [r[src][key] for r in rows if r.get(src) and r[src].get(key) is not None]


def med3(rows, key, src="o"):
    """(‏n · الوسيط · p25 · p75) — الرُّبيعان برتبةٍ أقرب (`pctile` بالاسم)."""
    v = sorted(_vals(rows, key, src))
    if not v:
        return (0, None, None, None)
    return (len(v), st.median(v), pctile(v, 25), pctile(v, 75))


def share(rows, pred):
    """(‏k · n · % · Wilson) — نسبةٌ بفاصلها."""
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    if not n:
        return (0, 0, None, (None, None))
    return (k, n, k / n * 100.0, wilson(k, n))


def ci_median(rows, key, src="o"):
    """فاصلُ بوتستراب ‏95% عنقوديٌّ بالرمز (`boot_ci_median` بالاسم · بذرتُه ثابتة)."""
    groups = collections.defaultdict(list)
    for r in rows:
        if r.get(src) and r[src].get(key) is not None:
            groups[r["symbol"]].append(r[src][key])
    return boot_ci_median(dict(groups))


def window_rule(rows):
    """قاعدةُ النافذة `W` بحرف §⑦ — من الرُّبيع الأعلى لـ`t_hit10` بين مَن بلغ ‏+10% في النظاميّ."""
    hits = sorted(r["o"]["t_hit10"] for r in rows
                  if r["o"]["t_hit10"] is not None and r["o"]["hit10_reg"])
    n = len(hits)
    if n < MIN_HITS:
        return {"h": "EOD", "n": n, "p50": None, "p75": None, "p90": None,
                "why": f"‏{n} إصابةً دون {MIN_HITS} ⇒ `EOD`"}
    p50, p75, p90 = pctile(hits, 50), pctile(hits, 75), pctile(hits, 90)
    h = next((x for x in W_SET if x >= p75), "EOD")
    return {"h": h, "n": n, "p50": p50, "p75": p75, "p90": p90,
            "why": f"‏p75 = {p75:.0f} دقيقة ⇒ أصغرُ عنصرٍ في {list(W_SET)} فوقه"}


def night_rule(rows):
    """قاعدةُ الليل `O` بحرف §⑦ — في النصفين معًا بين مَن له بريماركتُ غد."""
    res = {}
    for half in ("H1", "H2"):
        sub = [r for r in rows if r["half"] == half and r.get("pm")
               and r["o"].get("close_reg") is not None]
        pm = [r["pm"]["pm_last"] for r in sub]
        cr = [r["o"]["close_reg"] for r in sub]
        if sub:
            mp, mc = st.median(pm), st.median(cr)
            res[half] = {"n": len(sub), "pm_last": mp, "close_reg": mc, "win": mp > mc}
        else:
            res[half] = {"n": 0, "pm_last": None, "close_reg": None, "win": None}
    arm = all(res[h]["win"] is True for h in ("H1", "H2"))
    return {"halves": res, "arm_P4": arm}


def predictions(rows, wres):
    """التنبّؤات `CP1`-`CP7` بحرف §⑥ — تُعاد (رمز · نصّ · صدق/None · تفصيل)."""
    out = []

    def _m(sub, key, src="o"):
        v = _vals(sub, key, src)
        return st.median(v) if v else None

    expl = [r for r in rows if r["o"]["exploded50"]]
    m1 = _m(expl, "t_peak")
    out.append(("CP1", "وسيطُ t_peak بين exploded50 ‏≤ 60 دقيقة",
                None if m1 is None else m1 <= 60, f"وسيط={m1} · n={len(expl)}"))
    m2 = _m(rows, "dn_60")
    out.append(("CP2", "وسيطُ dn_60 على الكلّ ‏≤ −5%",
                None if m2 is None else m2 <= -5.0, f"وسيط={m2}"))
    n = len(rows)
    by60 = sum(1 for r in rows if r["o"]["t_hit10"] is not None and r["o"]["t_hit10"] <= 60)
    byreg = sum(1 for r in rows if r["o"]["hit10_reg"])
    out.append(("CP3", "hit10_by_60 أكبرُ من (hit10_by_reg − hit10_by_60)",
                None if not n else by60 > (byreg - by60), f"by60={by60} · by_reg={byreg} · n={n}"))
    sub = [r for r in rows if r.get("pm") and r["o"].get("close_reg") is not None]
    m4p, m4c = _m(sub, "pm_last", "pm"), _m(sub, "close_reg")
    out.append(("CP4", "وسيطُ pm_last أدنى من وسيط close_reg (المجموعةُ نفسُها)",
                None if (m4p is None or m4c is None) else m4p < m4c,
                f"pm_last={m4p} · close_reg={m4c} · n={len(sub)}"))
    tc = [r for r in rows if r["trig"] == "T-C"]
    r1 = [r for r in rows if r["trig"] == "R1"]
    m5t, m5r = _m(tc, "up_60"), _m(r1, "up_60")
    out.append(("CP5", "وسيطُ up_60 لـT-C أدنى منه لـR1 (بعد الشحن)",
                None if (m5t is None or m5r is None) else m5t < m5r,
                f"T-C={m5t} (n={len(tc)}) · R1={m5r} (n={len(r1)})"))
    pre = [r for r in rows if r["f"]["tod"] == "pre"]
    reg = [r for r in rows if r["f"]["tod"] == "reg"]
    m6p, m6r = _m(pre, "up_reg"), _m(reg, "up_reg")
    out.append(("CP6", "وسيطُ up_reg لـpre أعلى منه لـreg",
                None if (m6p is None or m6r is None) else m6p > m6r,
                f"pre={m6p} (n={len(pre)}) · reg={m6r} (n={len(reg)})"))
    out.append(("CP7", "قاعدةُ W تُخرج h* = 60 أو 120",
                wres["h"] in (60, 120), f"h*={wres['h']}"))
    return out


# ───────────────────────── العرض ────────────────────────────────────────────────
def _f(x, w=6, d=1):
    return ("—".rjust(w)) if x is None else f"{x:+{w}.{d}f}"


def _fn(x, w=5, d=0):
    return ("—".rjust(w)) if x is None else f"{x:{w}.{d}f}"


def _q(rows, key, src="o"):
    n, m, lo, hi = med3(rows, key, src)
    return f"{_f(m)} [{_f(lo)}·{_f(hi)}] n={n:<3}"


def bucket_block(label, rows, with_ci=True):
    lines = [f"\n▶ {label}  (n={len(rows)} · H1 {sum(1 for r in rows if r['half']=='H1')} "
             f"· H2 {sum(1 for r in rows if r['half']=='H2')})"]
    lines.append("   الأفق     up وسيط [p25·p75]          dn وسيط [p25·p75]          ret وسيط [p25·p75]         hit10   stop")
    for h in HORIZONS:
        k_h, n_h, p_h, _ = share(rows, lambda r, h=h: r["o"]["t_hit10"] is not None and r["o"]["t_hit10"] <= h)
        sk = [r for r in rows if r["o"]["stop_known"]]
        k_s, n_s, p_s, _ = share(sk, lambda r, h=h: r["o"]["t_stop"] is not None and r["o"]["t_stop"] <= h)
        lines.append(f"   +{h:<3}د   {_q(rows, f'up_{h}')}  {_q(rows, f'dn_{h}')}  {_q(rows, f'ret_{h}')}  "
                     f"{_fn(p_h, 5, 1)}%  {_fn(p_s, 5, 1)}%")
    k_r, n_r, p_r, _ = share(rows, lambda r: r["o"]["hit10_reg"])
    sk = [r for r in rows if r["o"]["stop_known"]]
    k_sr, n_sr, p_sr, _ = share(sk, lambda r: r["o"]["stop_reg"])
    lines.append(f"   النظاميّ  {_q(rows, 'up_reg')}  {_q(rows, 'dn_reg')}  {_q(rows, 'close_reg')}  "
                 f"{_fn(p_r, 5, 1)}%  {_fn(p_sr, 5, 1)}%   (stop معروفٌ لـ{n_sr} من {len(rows)})")
    lines.append(f"   الممتدّ   up_ext {_q(rows, 'up_ext')} · t_peak(د) {_q(rows, 't_peak')} · "
                 f"dd_pre_peak {_q(rows, 'dd_pre_peak')}")
    pmr = [r for r in rows if r.get("pm")]
    lines.append(f"   بري الغد  pm_up {_q(pmr, 'pm_up', 'pm')} · pm_dn {_q(pmr, 'pm_dn', 'pm')} · "
                 f"pm_last {_q(pmr, 'pm_last', 'pm')} · بلا بري {len(rows) - len(pmr)}")
    for half in ("H1", "H2"):
        hr = [r for r in rows if r["half"] == half]
        hp = [r for r in hr if r.get("pm")]
        lines.append(f"   {half}       up_60 {_q(hr, 'up_60')} · close_reg {_q(hr, 'close_reg')} · "
                     f"pm_last {_q(hp, 'pm_last', 'pm')} · t_peak {_q(hr, 't_peak')}")
    k_e, n_e, p_e, (elo, ehi) = share(rows, lambda r: r["o"]["exploded50"])
    lines.append(f"   exploded50 {k_e}/{n_e} = {_fn(p_e, 5, 1)}% [{_fn(elo, 3, 0)}·{_fn(ehi, 3, 0)}]")
    if with_ci:
        cis = []
        for key in CI_METRICS:
            src = "pm" if key.startswith("pm_") else "o"
            lo, hi = ci_median(rows, key, src)
            cis.append(f"{key} [{_f(lo)}·{_f(hi)}]")
        lines.append("   CI95 عنقوديٌّ بالرمز للوسيط: " + " · ".join(cis))
    return "\n".join(lines)


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        print("⛔ لا POLYGON_API_KEY — خروج 2 (V-C1)")
        return 2
    anchors = anchor_history(SINCE)
    cut = 0
    if UNTIL:                                                   # §⑪-5 — تثبيتُ الكون
        before = len(anchors)
        anchors = {k: v for k, v in anchors.items() if k[0] <= UNTIL}
        cut = before - len(anchors)
    if not anchors:
        print("⛔ صفرُ مِرساةٍ في تاريخ git (بصمةُ no-op) — خروج 4 (V-C2)")
        return 4
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    win = f" · حتى {UNTIL} (قُصّ {cut})" if UNTIL else " · حتى يوم التشغيل"
    print(f"🕵️📈 T-OPCURVE · مراسٍ {len(anchors)} · سجلّ M5 {len(ledger)} · منذ {SINCE}{win} · "
          f"H2 من {H2_FROM} · الزنادُ بعد {SHIP_ISO}")
    rows, fails, nobase, pm_missing = [], 0, 0, 0
    pm_no_next, pm_no_bars = 0, 0                               # §⑪-7 — تفكيكٌ عرضيّ لا مقياس
    rec_low, rec_price, rec_gap, round_moved = [], 0, 0, 0      # §⑪-3/§⑪-4
    diffs_price, diffs_low = [], []                             # `V-C10`
    cache, dcache = {}, {}
    for (day, sym), a in sorted(anchors.items()):
        bars = cache.get((sym, day))
        if bars is None:
            bars = fetch_day(sym, day, key)
            cache[(sym, day)] = bars or []
        if not bars:
            fails += 1
            continue
        dailies = dcache.get((sym, day))
        if dailies is None:
            dailies = daily_range(sym, day, key) or []
            dcache[(sym, day)] = dailies
        b = ledger.get((day, sym))
        a_ms = int(a["anchor_ms"])
        ra = resolve_anchor(a, b, bars)                          # §⑪-3 — بتعريف الإنتاج
        ap = ra["ap"]
        diffs_price.append((ra["d_price"], ra["ref_price"]))
        diffs_low.append((ra["d_low"], ra["ref_low"]))
        if ra["low_src"] == "شمعة":
            rec_low.append(day)
        if ra["ap_src"] == "شمعة":
            rec_price += 1
        if ra["round_moved"]:
            round_moved += 1
        e5 = (b or {}).get("e5")
        if not e5:
            e5, _broke = true_e5(bars, a_ms, ap) if ap else (None, False)
        if not e5:
            nobase += 1
            continue
        t0 = a_ms + CARD_OFFSET_MS
        o = path_stats(bars, t0, e5, ra["alow"])
        nxt = next((d for (d, _h, _c) in dailies if d > day), None)
        pm = None
        if nxt:
            nb = cache.get((sym, nxt))
            if nb is None:
                nb = fetch_day(sym, nxt, key)
                cache[(sym, nxt)] = nb or []
            pm = pm_stats(nb, e5)
        if pm is None:
            pm_missing += 1
            if nxt is None:
                pm_no_next += 1
            else:
                pm_no_bars += 1
        f = features(a, b)
        gap_src = "سجلّ" if f["gap"] != "؟" else "—"
        if f["gap"] == "؟" and ap:
            # §⑪-3-3: الشرطُ على **النتيجة** لا على المصدر · والتعريفُ نفسُه
            # (‏`anchor_price ÷ إغلاق اليوم السابق − 1`) كما في `tierlink_probe.main`.
            pcs = [c for (d, _h, c) in dailies if d < day]
            if pcs:
                gap = (ap / pcs[-1] - 1) * 100
                f["gap"] = "<10%" if gap < 10 else ("10-30%" if gap < 30 else "≥30%")
                gap_src, rec_gap = "شموع", rec_gap + 1
        rows.append({"date": day, "symbol": sym, "half": "H1" if day < H2_FROM else "H2",
                     "trig": trig_bucket(a), "e5": e5, "f": f, "o": o, "pm": pm,
                     "low_src": ra["low_src"], "gap_src": gap_src,
                     "b": buckets_of(f, trig_bucket(a), o["exploded50"])})
    total = len(anchors)
    cover = len(rows) / total
    print(f"🩺 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} من {total} "
          f"= {cover*100:.1f}% · بلا بريماركتِ غد {pm_missing} ({pm_missing/max(1,len(rows))*100:.0f}%)"
          f" [لا يومَ تالٍ {pm_no_next} · يومٌ بلا شموعِ بري {pm_no_bars}]")
    unknown = sum(1 for r in rows if not r["o"]["stop_known"])
    days_lo = sorted(set(rec_low))
    print(f"🧩 الترميم (§⑪-3): قاعٌ مستردٌّ من الشمعة {len(rec_low)}"
          f"{' · أيامُه ' + days_lo[0] + ' ⟶ ' + days_lo[-1] + f' ({len(days_lo)} يومًا)' if days_lo else ''}"
          f" · سعرٌ مستردّ {rec_price} · فجوةٌ مستدرَكة {rec_gap} · وما زال بلا قاعٍ {unknown}"
          f" · قِيَمٌ غيّرها التقريبُ إلى أربع خانات **{round_moved}**")
    if cover < MIN_COVER:
        print("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم — خروج 3 (V-C3)")
        return 3
    # `V-C10` (§⑪-6) — المستردُّ يُقارَن بالمخزون حيث يتوفّران معًا
    cp, cl = recon_check(diffs_price), recon_check(diffs_low)
    for nm, c in (("السعر", cp), ("القاع", cl)):
        if c["n"]:
            print(f"🔎 V-C10 {nm}: قُورن {c['n']} · طابق {c['ok']} ({c['rate']*100:.2f}%) · "
                  f"مطابقةٌ تامّة {c['exact']} · أكبرُ فرقٍ {c['max_abs']:.6f} "
                  f"({c['max_rel']:.4f}% نسبيًّا · الحدُّ {RECON_TOL_PCT}%)")
        else:
            print(f"🔎 V-C10 {nm}: لا مقارنةَ ممكنة (صفرُ زوجٍ يجتمع فيه المخزونُ والشمعة)")
    bad = [nm for nm, c in (("السعر", cp), ("القاع", cl))
           if c["n"] and c["rate"] < MIN_RECON_MATCH]
    if bad:
        print(f"⛔ V-C10: المستردُّ يخالف المخزونَ حيث يُعرَف ({' · '.join(bad)}) ⇒ لا يُنشَر "
              f"رقمٌ مستردّ — خروج 5 (§⑪-6)")
        return 5
    n_tc = sum(1 for r in rows if r["trig"] == "T-C")
    n_r1 = sum(1 for r in rows if r["trig"] == "R1")
    n_pre = sum(1 for r in rows if r["trig"] == "قبل الشحن")
    small = " — **صغيرة** (دون 20)" if min(n_tc, n_r1) < TRIG_SMALL else ""
    print(f"🚦 سلّةُ الزناد بعد الشحن: R1 {n_r1} · T-C {n_tc}{small} · قبل الشحن {n_pre} (V-C9)")
    # ── الجداول
    print("\n" + "=" * 100 + "\n📈 المسارُ بالسلال (العقد §③×§④) — كلُّ رقمٍ ٪ من e5 · النوافذُ بالساعة الجداريّة\n" + "=" * 100)
    for bk in BUCKETS:
        vals = sorted({r["b"][bk] for r in rows})
        for v in vals:
            sub = [r for r in rows if r["b"][bk] == v]
            print(bucket_block(f"{bk} = {v}" if bk != "الكلّ" else "الكلّ", sub))
    # ── القاعدتان (§⑦)
    wres = window_rule(rows)
    print("\n" + "=" * 100 + "\n🪟 قاعدةُ النافذة `W` (§⑦)\n" + "=" * 100)
    print(f"   إصاباتُ +10% في النظاميّ n={wres['n']} · p50={_fn(wres['p50'],4,0)} · "
          f"p75={_fn(wres['p75'],4,0)} · p90={_fn(wres['p90'],4,0)} دقيقة ⇒ **h* = {wres['h']}** ({wres['why']})")
    ores = night_rule(rows)
    print("\n🌙 قاعدةُ الليل `O` (§⑦):")
    for half in ("H1", "H2"):
        hh = ores["halves"][half]
        print(f"   {half}: n={hh['n']} · وسيط pm_last {_f(hh['pm_last'])} مقابل close_reg {_f(hh['close_reg'])} "
              f"⇒ {'الليلُ أعلى' if hh['win'] else ('الليلُ أدنى' if hh['win'] is False else '—')}")
    print(f"   ⇒ ذراعُ `P4` (حملٌ إلى بريماركت الغد · وصفيّة) في عقد T-OPTRADE: "
          f"{'**نعم**' if ores['arm_P4'] else '**لا**'}")
    # ── التنبّؤات (§⑥)
    print("\n" + "=" * 100 + "\n🔮 التنبّؤات (§⑥ — كُتبت قبل الأرقام)\n" + "=" * 100)
    for cid, text, ok, detail in predictions(rows, wres):
        mark = "✅ مؤكَّد" if ok else ("🔴 مكذَّب" if ok is False else "— لا يُقاس")
        print(f"   {cid} {text}: {mark} · {detail}")
    # ── الصفوف كاملةً (لا قصّ)
    print("\n📋 الصفوف (تاريخ · رمز · زناد · وقت · فئة · J1 · فجوة · انفجر · up5 · up15 · up30 · up60 · dn60 · "
          "up_ext · t_peak · dd_pre · t_hit10 · t_stop · close_reg · pm_last):")
    for r in sorted(rows, key=lambda r: (r["date"], r["symbol"])):
        f, o, pm = r["f"], r["o"], r.get("pm") or {}
        print(f"   {r['date'][5:]} {r['symbol']:<6} {r['trig']:<9} {f['tod']:<5} {f['tier']:<6} {f['j1']:<3} "
              f"{f['gap']:<7} {'نعم' if o['exploded50'] else 'لا ':<3} {_f(o['up_5'])} {_f(o['up_15'])} "
              f"{_f(o['up_30'])} {_f(o['up_60'])} {_f(o['dn_60'])} {_f(o['up_ext'])} {_fn(o['t_peak'],5,0)} "
              f"{_f(o['dd_pre_peak'])} {_fn(o['t_hit10'],5,0)} {_fn(o['t_stop'],5,0)} {_f(o['close_reg'])} "
              f"{_f(pm.get('pm_last'))}")
    # ── كتلةُ الاستخراج (§⑪-8) — نسخةٌ آليّةٌ لا إعادةَ بناءٍ بتقطيع نصّ
    def _t(x):
        return "" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))

    print("\n⟦TSV⟧")
    print("\t".join(TSV_COLS))
    for r in sorted(rows, key=lambda r: (r["date"], r["symbol"])):
        f, o, pm = r["f"], r["o"], r.get("pm") or {}
        print("\t".join(_t(v) for v in (
            r["date"], r["symbol"], r["trig"], f["tod"], f["tier"], f["j1"], f["gap"],
            "نعم" if o["exploded50"] else "لا", o["up_5"], o["up_15"], o["up_30"], o["up_60"],
            o["dn_60"], o["up_ext"], o["t_peak"], o["dd_pre_peak"], o["t_hit10"], o["t_stop"],
            o["close_reg"], pm.get("pm_last"), r["low_src"], r["gap_src"])))
    print("⟦/TSV⟧")
    print("\n⚠️ حدودُ صدق (§⑧): لمسٌ لا تنفيذ · ≈4 أسابيعَ وكلُّ ميزةٍ تتحلّل بين النصفين · المجتمعُ ما صمد في آخر "
          "لقطةِ يومه لا كلُّ ما رسا · e5 قد يغيب فيُعَدّ · سلّةُ الزناد ≈4-5 جلسات · exploded50 سلّةُ نتيجةٍ "
          "تصف ولا تختار · بريماركتُ الغد رقيقُ السيولة · لا تكلفةَ ولا R · وصفيٌّ بنصّ العقد — لا حكم."
          "\n   §⑪: القاعُ والسعرُ المستردّان **بتعريف الإنتاج** لا بمُقدِّرٍ جديد (ومُثبَتان "
          "على المخزون بـ`V-C10`) · و`tier`/`j1` تبقى «؟» ولا تُخمَّن (استردادُها يلزمه إعادةُ "
          "تشغيل `liq_stage_events` = مُقدِّرٌ آخر) · وسلّةُ الفجوة المستدرَكة مصدرُها في العمود.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
