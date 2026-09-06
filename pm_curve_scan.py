# -*- coding: utf-8 -*-
"""🌅📈 `T-PM-CURVE` — منحنى الالتقاط/الكلفة للرادار الحيّ على **سنةٍ كاملة**
(العقد `presession_ceiling_prereg.md §④` — مدفوعٌ قبل أيّ رقم).

السؤال: كم يلتقط الرادارُ الحيُّ (‏`R1` = مرشِّحُ اللقطة + `liq_stage_events` الإنتاجيّة)
من منفجري البريماركت ‏+30/+50/+100% **قبل** بلوغهم الحدّ؟ وبكم رسالةٍ في الجلسة؟ وبأيّ
سعرٍ عن إغلاق الأمس؟ — ومعه **زناداتٌ تراكميّةٌ بلا قفزة حجم** (طبقةُ تسليمٍ موازيةٌ
تُقاس لا تُشحَن).

🔒 **أداةٌ مستقلّة**: تستورد دوالَّ `pm_radar_scan` **بالاسم** (‏`parse_pre` · `mover_t30`
· `candidate_index` · `replay_anchor`) فلا يُمَسّ ذلك الملفّ وأرقامُه المنشورة قابلةٌ
للإعادة بت-بت (سابقةُ `CAP15`) · بلا كون قوائم (لا `git` في سنةٍ كاملة) · وضعُ `legacy`
· قراءةٌ فقط: صفرُ إرسالٍ وصفرُ كتابةِ حالة · الإنتاجُ لا يستوردها.
🔒 **صفرُ رقمٍ مخترَع:** أرضياتُ الزنادات `LIQ_MIN_USD`/`IGNITION_USD_OPERATOR` ورفعاتُها
`LIQ_MIN_MOVE_PCT`/10%/20% كلُّها مُعادة (العقد §④).
"""
from __future__ import annotations

import gzip
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import datetime as dt                                            # noqa: E402

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import pm_radar_scan as PMR                                      # noqa: E402
import Super_stock as S                                          # noqa: E402

NY = KS.NY
DEFAULT_FROM, DEFAULT_TO = "2025-01-02", "2025-12-31"
LADDER = (30.0, 50.0, 100.0)          # ‏+30 faisal_verbatim · +50 · +100 رقمُ المالك
MOVER_USD = PMR.MOVER_USD             # أرضيةُ المتحرّك نفسُها (مُعادة)
USD_FLOOR = PMR.USD_FLOOR             # مرشِّحُ اللقطة = LIQ_MIN_USD
MOVE_PCT = float(S.LIQ_MIN_MOVE_PCT)  # 5%
# الزناداتُ التراكميّة (مثبَّتة — لا خامسة): (اسم · دولارٌ تراكميّ · رفعةٌ عن الأمس %)
TRIGS = (("T-A", USD_FLOOR, 10.0), ("T-B", MOVER_USD, 10.0),
         ("T-C", MOVER_USD, 20.0), ("T-D", USD_FLOOR, MOVE_PCT))
ARMS = ("R1",) + tuple(t[0] for t in TRIGS)
MIN_MOVERS = 100                      # أرضيةُ الحكم لكلّ سلّم (§④ V-K2)
COVERAGE_MIN = 95.0                   # V-K0: أيامُ الملفّات من أيام العمل
R1_CAP100_MIN = 60.0                  # C4
TRIG_CAP_MIN, TRIG_COST_MAX = 40.0, 3.0   # C5


def log(msg: str):
    print(msg, flush=True)


def trigger_ms(rows, prev_close, usd: float, pct: float):
    """أوّلُ دقيقةٍ مغلقةٍ يكون عندها **مجموعُ** سيولة البريماركت حتى نهايتها ‏≥ `usd`
    **و**إغلاقُها ‏≥ إغلاق الأمس × (1+pct/100). يُرجع `(ms, close)` أو `None`.
    بلا قفزة حجمٍ ولا رفعةِ دقيقة — الطبقةُ الموازية بعينها."""
    if not prev_close or prev_close <= 0:
        return None
    lvl = prev_close * (1.0 + pct / 100.0)
    cum = 0.0
    for b in rows:
        cum += b[4] * b[5]
        if cum >= usd and b[4] >= lvl:
            return (int(b[0]), float(b[4]))
    return None


def r1_anchor(rows):
    """مِرساةُ الإنتاج على مرشِّح اللقطة (‏`R1` في `T-PM-RADAR` خارج القوائم) —
    بدوالّ `pm_radar_scan` بالاسم. `(ms, price)` أو `None`."""
    i0 = PMR.candidate_index(rows, USD_FLOOR)
    if i0 is None:
        return None
    e = PMR.replay_anchor(rows, i0 + 1)
    if not e:
        return None
    return (int(e["anchor_ms"]), float(e.get("anchor_price") or e.get("price") or 0.0))


def day_rows(day, bars, prev_close):
    """صفوفُ يومٍ: لكلّ رمزٍ له إغلاقُ أمسٍ داخل النطاق — سلّمُ المتحرّكين والأذرع."""
    out = []
    for sym, rws in bars.items():
        pc = prev_close.get(sym)
        if pc is None or not (PMR.PRICE_LO <= pc <= PMR.PRICE_HI):
            continue
        lad = {str(int(p)): PMR.mover_t30(rws, pc, pct=p) for p in LADDER}
        arms = {"R1": r1_anchor(rws)}
        for nm, usd, pct in TRIGS:
            arms[nm] = trigger_ms(rws, pc, usd, pct)
        if not any(lad.values()) and not any(arms.values()):
            continue
        out.append({"day": day, "symbol": sym, "prev_close": pc,
                    "first_ret": round((rws[0][2] / pc - 1) * 100, 2) if rws else None,
                    "mover": lad, "arm": {k: (list(v) if v else None) for k, v in arms.items()},
                    "pre_usd": round(sum(b[4] * b[5] for b in rws))})
    return out


def chain_ok(rows) -> bool:
    """شاهدُ الضبط الداخليّ (‏§④ V-K1): بالبناء `T-A` ⇒ `T-D` أبكر أو في الدقيقة نفسِها
    (أرضيةٌ واحدةٌ ورفعةٌ أخفّ) · و`T-B` ⇒ `T-A` · و`T-C` ⇒ `T-B`. أيُّ خرقٍ عطبُ أداة."""
    for r in rows:
        a = r["arm"]
        for hi, lo in (("T-A", "T-D"), ("T-B", "T-A"), ("T-C", "T-B")):
            if a.get(hi) and (not a.get(lo) or a[lo][0] > a[hi][0]):
                return False
    return True


def summarize(rows, days) -> dict:
    """لكلّ سلّمٍ ولكلّ ذراع: الالتقاطُ قبل الحدّ · قبل +30% · الرسائل/جلسة · التأخّر · الإثمار."""
    res = {"n_days": len(days), "ladder": {}, "arms": {}}
    per_day = {a: {d: 0 for d in days} for a in ARMS}
    fruit = {a: [0, 0] for a in ARMS}
    for r in rows:
        t30 = r["mover"].get("30")
        for a in ARMS:
            v = r["arm"].get(a)
            if v:
                per_day[a][r["day"]] = per_day[a].get(r["day"], 0) + 1
                fruit[a][1] += 1
                fruit[a][0] += int(bool(t30) and v[0] < t30)
    for a in ARMS:
        msgs = sorted(per_day[a].values())
        res["arms"][a] = {"msgs_median": statistics.median(msgs) if msgs else 0,
                          "msgs_total": sum(msgs),
                          "fruit30_pct": (round(100.0 * fruit[a][0] / fruit[a][1], 1)
                                          if fruit[a][1] else None),
                          "fired": fruit[a][1]}
    for p in LADDER:
        key = str(int(p))
        mv = [r for r in rows if r["mover"].get(key)]
        cell = {"n": len(mv), "arms": {}}
        for a in ARMS:
            cap = [r for r in mv if r["arm"].get(a) and r["arm"][a][0] < r["mover"][key]]
            cap30 = [r for r in mv if r["arm"].get(a) and r["mover"].get("30")
                     and r["arm"][a][0] < r["mover"]["30"]]
            dl = [(r["arm"][a][1] / r["prev_close"] - 1) * 100 for r in cap
                  if r["prev_close"] and r["arm"][a][1]]
            cell["arms"][a] = {
                "captured": len(cap),
                "cap_pct": round(100.0 * len(cap) / len(mv), 1) if mv else None,
                "cap30_pct": round(100.0 * len(cap30) / len(mv), 1) if mv else None,
                "delay_median": round(statistics.median(dl), 1) if dl else None}
        res["ladder"][key] = cell
    return res


def verdict(res: dict) -> list:
    """C4/C5 بحرفهما (§④). تُرجع (اسم، ✅/🔴/⏸️، تفصيل)."""
    out = []
    c100 = res["ladder"].get("100") or {"n": 0, "arms": {}}
    if c100["n"] < MIN_MOVERS:
        return [("الأرضية", "⏸️", f"منفجرو +100%: {c100['n']} < {MIN_MOVERS} ⇒ لا حكم")]
    r1 = c100["arms"]["R1"]
    out.append(("C4 R1 يلتقط +100% قبل +100% ≥ 60%",
                "✅" if (r1["cap_pct"] or 0) >= R1_CAP100_MIN else "🔴", f"{r1['cap_pct']}%"))
    m1 = max(1.0, float(res["arms"]["R1"]["msgs_median"]))
    best = None
    for nm, _, _ in TRIGS:
        c = c100["arms"][nm]
        cost = res["arms"][nm]["msgs_median"] / m1
        ok = (c["cap30_pct"] or 0) >= TRIG_CAP_MIN and cost <= TRIG_COST_MAX
        if ok and (best is None or (c["cap30_pct"] or 0) > best[1]):
            best = (nm, c["cap30_pct"], cost)
    out.append(("C5 زنادٌ تراكميّ يلتقط +100% قبل +30% ≥ 40% بكلفةٍ ≤ 3× R1",
                "✅" if best else "🔴",
                (f"{best[0]} {best[1]}% ×{best[2]:.2f}" if best else "لا زناد")))
    return out


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        log("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    d_from = (os.environ.get("PMC_FROM") or DEFAULT_FROM).strip()
    d_to = (os.environ.get("PMC_TO") or DEFAULT_TO).strip()
    days = KS.weekdays(d_from, d_to)
    seed = KS.weekdays((dt.date.fromisoformat(d_from) - dt.timedelta(days=7)).isoformat(),
                       (dt.date.fromisoformat(d_from) - dt.timedelta(days=1)).isoformat())[-3:]
    log(f"🌅📈 T-PM-CURVE — {d_from} ⟶ {d_to} · {len(days)} يوم أسبوع · كون "
        f"[{PMR.PRICE_LO}, {PMR.PRICE_HI}]$ · R1: مرشِّح ${USD_FLOOR:,.0f} + liq_stage_events · "
        "زنادات: " + " · ".join(f"{n}=(${u:,.0f} ∧ +{p:g}%)" for n, u, p in TRIGS)
        + f" · سلّم {LADDER} بأرضية ${MOVER_USD:,.0f} · بلا كون قوائم · وضع legacy")
    prev_close: dict = {}
    rows_out, n_files, missing = [], 0, []
    fout = open("pm_curve_rows.jsonl", "w", encoding="utf-8")
    for di, day in enumerate(seed + days):
        seeding = di < len(seed)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                missing.append(day)
            continue
        dest = f"/tmp/pmc-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            if not seeding:
                missing.append(day)
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes, _dg = PMR.parse_pre(fh, prev_close, seeding, "legacy")
        except (OSError, KeyError, ValueError) as e:
            log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            if not seeding:
                missing.append(day)
            continue
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
        if seeding:
            prev_close.update(closes)
            log(f"🌱 بذرة إغلاق الأمس من {day}: {len(closes):,} رمزًا")
            continue
        n_files += 1
        rws = day_rows(day, bars, prev_close)
        for r in rws:
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")
        rows_out.extend(rws)
        n100 = sum(1 for r in rws if r["mover"].get("100"))
        log(f"📅 {day}: رموز {len(bars):,} · صفوف {len(rws)} · +30% "
            f"{sum(1 for r in rws if r['mover'].get('30'))} · +100% {n100} · R1 "
            f"{sum(1 for r in rws if r['arm'].get('R1'))}")
        prev_close.update(closes)
    fout.close()
    cov = 100.0 * n_files / len(days) if days else 0.0
    log(f"\n📦 ملفّات {n_files} من {len(days)} = {cov:.1f}% · مفقود {len(missing)}"
        + (": " + ", ".join(missing[:20]) if missing else "") + f" · صفوف {len(rows_out):,}")
    if n_files == 0 or not rows_out:
        log("⛔ صفرُ صفوف — عطبُ أداةٍ لا نتيجة (خروج 4)")
        return 4
    if cov < COVERAGE_MIN:
        log(f"⛔ V-K0 التغطية {cov:.1f}% < {COVERAGE_MIN}% ⇒ عطبُ أداةٍ لا نتيجة (خروج 3)")
        return 3
    if not chain_ok(rows_out):
        log("⛔ V-K1 سلسلةُ الزنادات مكسورة (T-C⇒T-B⇒T-A⇒T-D) ⇒ عطبُ أداةٍ (خروج 3)")
        return 3
    log("✅ V-K1 سلسلةُ الزنادات سليمة بالبناء")
    res = summarize(rows_out, days)
    log(f"\n📨 الرسائل لكلّ ذراع على {res['n_days']} جلسة: " + " · ".join(
        f"{a}: وسيط {v['msgs_median']} · مجموع {v['msgs_total']} · إثمار+30% {v['fruit30_pct']}%"
        for a, v in res["arms"].items()))
    for key, cell in res["ladder"].items():
        log(f"\n【متحرّكو +{key}% (سيولة ≥${MOVER_USD:,.0f})】 n={cell['n']}")
        log(f"   {'ذراع':<6}{'التقاط قبل الحدّ':>18}{'٪':>8}{'قبل +30%':>10}{'تأخّر وسيط٪':>14}")
        for a, v in cell["arms"].items():
            log(f"   {a:<6}{v['captured']:>18}{str(v['cap_pct']):>8}{str(v['cap30_pct']):>10}"
                f"{str(v['delay_median']):>14}")
    log("\n⚖️ الحكم (§④ — C4/C5 كما كُتبا):")
    for nm, mark, det in verdict(res):
        log(f"   {mark} {nm}: {det}")
    log("\n⚠️ حدود (مكتوبةٌ قبل الأرقام): لمسٌ لا تنفيذ · الكونُ فوق MIN_PRICE ومَن لا إغلاقَ "
        "أمسٍ باسمه خارج المقام (legacy) · لا ربحيّةَ تُقاس · والرادارُ يحتاج عاملًا حيًّا من "
        "04:00 · سقفُ النجاح اقتراحٌ للمالك — لا زنادَ يُشحَن ولا بوّابةَ تُمَسّ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
