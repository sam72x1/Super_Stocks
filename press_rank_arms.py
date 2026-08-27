#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️🥇 `T-PRESS-RANK` — «مَن الثمانيةُ الذين يصلونك؟» أذرعُ ترتيبِ كروت رادار الضغط.

**العقد:** `press_rank_prereg.md` مدفوعٌ **قبل أيّ سطرِ كودِ أداة** (‏وملحقُه §⑨
مدفوعٌ **قبل أيّ رقم**). أمرُ المالك: «قس عدد الصفقات **شتغل على قناة الضغط**».

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** القراءةُ `press_radar.press_read`
(‏`ALERT_W`) · الصحوةُ `press_radar.wake_read` · الترتيبُ `press_radar.alert_rank`
· الدِدوبُ `press_radar.should_alert` · السقفُ `press_radar.ALERT_CAP` · الجاهزيّةُ
`press_radar.READY_HOLD` · الخطّةُ `rebound_arms.mirror_plan` · الحسمُ
`rebound_arms.resolve_episode` · و`R` من `press_backtest.r_win_value` ·
وبوّابةُ التكامل `press_wake_arms.walk_symbol_wake` **بالاسم** (مِشيةُ §⑬).

🔒 **قراءةٌ فقط:** لا تُعدّل ملفًّا ولا ترسل شيئًا ولا يستوردها الإنتاج ·
`Super_stock.py` و`press_radar.py` و`rebound_arms.py` و`press_wake_arms.py`
byte-identical · لا `LOGIC_VERSION`.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys

# ───────────────────────── ثوابتُ العقد (§③/§④/§⑤) ─────────────────────────
ARM_NAMES = ("A0", "A1", "A2", "A3")
N_SEEDS = 200                       # §③ شاهدُ الصدفة
BOOT_N = 10_000                     # §④-2
BOOT_SEED = 54321                   # §④-2 — نفسُ بذرة T-RANK-DENSE
FLOOR_SESSIONS = 40                 # §④-4
FLOOR_CARDS = 150                   # §④-4
COVERAGE_MIN = 95.0                 # §⑤ PV3
PV1_MEDIAN_MIN = 3.0                # §⑤ PV1
# §⑤ PV0 — محسومةُ HOLD3 المنشورة سنةً بسنة (‏1660+1857+1854 = 5371)
PV0_RESOLVED = {"2023": 1660, "2024": 1857, "2025": 1854}


def _log(m):
    print(m, flush=True)


def r_of(oc, rw):
    """`R` للكرت بصيغة §⑯ حرفيًّا: فائزةٌ +r_win · خاسرةٌ −1 · وغيرُهما صفرٌ
    **لكنها تستهلك كرتًا** (نظيرُ `r_unit` في `replay10`)."""
    if oc == "win":
        return float(rw)
    if oc == "loss":
        return -1.0
    return 0.0


# ───────────────────────────── المِشيةُ الكثيفة ─────────────────────────────

def ready_rows(sym, df, year):
    """كلُّ (جلسة، رمز) جاهزٍ في السنة — **بخطوة 1 وبلا قفزة `WAIT`**.

    ⚖️ §⑨-1/⑨-2: `plan` و`prev_q` **غائبان بنيويًّا** (ذاكرةُ البِركة لا وجود
    لها تاريخيًّا · و`prev_qualified` مقيسٌ ‏≈8.6 ساعة/سنة) ⇒ يُمرَّران `None`
    **للأذرع الأربع بالتساوي** فالمفتاحان الأوّلان في `alert_rank` خاملان."""
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    out = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        days = [str(d)[:10] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return out
    n = len(df)
    for i in range(RB.MIN_BARS, n):
        if year and days[i][:4] != str(year):
            continue
        sl = df.iloc[:i + 1]
        r = PR.press_read(sl, w=PR.ALERT_W)
        if not r:
            continue
        if int(r.get("hold_sessions") or 0) < PR.READY_HOLD:
            continue                       # «🟢 جاهز» = تعريفُ الإنتاج حرفيًّا
        try:
            w = PR.wake_read(sl)           # بلا افتر — أرضيّةٌ مُعلَنة (§⑧-2)
        except Exception:                                        # noqa: BLE001
            w = {}
        tr, st = RB.mirror_plan(float(r["press_low"]))
        oc = RB.resolve_episode(hi, lo, i, tr, st)
        out.append({"session": days[i], "symbol": str(sym), "read": r,
                    "plan": None, "prev_q": None,
                    "wake": w or {}, "oc": oc,
                    "swept": bool(r.get("swept_hold"))})
    return out


# ────────────────────────────── الأذرعُ الأربع ──────────────────────────────

def order_a0(rows):
    """**`A0` المرجع** — ترتيبُ الإنتاج حرفيًّا: `alert_rank` ثم تجزئةٌ ثابتة
    تضع المستيقظَ أوّلًا (‏`press_radar.run` سطرَي `rows.sort` و`_card_rows`)."""
    import press_radar as PR                                     # noqa: PLC0415
    xs = sorted(rows, key=PR.alert_rank)
    aw = [r for r in xs if (r.get("wake") or {}).get("awake")]
    qu = [r for r in xs if not (r.get("wake") or {}).get("awake")]
    return aw + qu


def order_a1(rows):
    """**`A1` الحاكمة** — 🩸 المكنوسُ بعد حفظٍ أوّلًا **ثم ترتيبُ `A0` حرفيًّا**.
    مفتاحُها `swept_hold` من `press_read` نفسِها — **صفرُ عتبةٍ جديدة**."""
    base = order_a0(rows)
    return ([r for r in base if r.get("swept")]
            + [r for r in base if not r.get("swept")])


def order_a2(rows, rng):
    """**`A2`** شاهدُ الصدفة — ترتيبٌ عشوائيٌّ داخل متنافسي الجلسة نفسِها."""
    xs = list(rows)
    rng.shuffle(xs)
    return xs


def order_a3(rows):
    """**`A3`** فيفو — الأقدمُ جاهزيّةً أوّلًا (‏`hold_sessions` الأكبرُ أقدمُ)،
    والرمزُ فاصلُ تعادلٍ حتميّ."""
    return sorted(rows, key=lambda r: (
        -int((r.get("read") or {}).get("hold_sessions") or 0), r["symbol"]))


# ─────────────────────────── التسليمُ تحت السقف والدِدوب ───────────────────────────

def deliver(by_sess, sessions, order_fn, rw):
    """يمشي الجلساتِ بالترتيب: دِدوبٌ **ثم** ترتيبٌ **ثم** سقف — كترتيب الإنتاج.

    ⚖️ §⑨-3: لكلّ ذراعٍ **ذاكرةُ دِدوبٍ خاصّة** (الأذرعُ تُسلّم رموزًا مختلفة
    فذاكرةٌ مشتركة كانت ستجعل ذراعًا تكتم أخرى) — مُعلَنٌ في الملحق."""
    import press_radar as PR                                     # noqa: PLC0415
    mem, per_sess, cards = {}, {}, []
    n_bind = 0
    for s in sessions:
        pool = by_sess.get(s, [])
        cand = [r for r in pool if PR.should_alert(mem.get(r["symbol"], {}), s)]
        if len(cand) > PR.ALERT_CAP:
            n_bind += 1
        picked = order_fn(cand)[:PR.ALERT_CAP]
        tot = 0.0
        for r in picked:
            mem[r["symbol"]] = {"last_alert": s}
            tot += r_of(r["oc"], rw)
            cards.append({"s": s, "sym": r["symbol"], "oc": r["oc"]})
        per_sess[s] = tot
    return {"per_sess": per_sess, "cards": cards, "bind": n_bind}


def dedupe_violations(cards):
    """`PV4`: صفرُ رمزٍ يُسلَّم مرّتين داخل `REALERT_DAYS`."""
    import press_radar as PR                                     # noqa: PLC0415
    last, bad = {}, 0
    for c in cards:
        prev = last.get(c["sym"])
        if prev is not None:
            gap = PR._days_between(prev, c["s"])
            if gap is not None and gap < PR.REALERT_DAYS:
                bad += 1
        last[c["sym"]] = c["s"]
    return bad


def boot_ci(diffs, n=BOOT_N, seed=BOOT_SEED, level=0.95):
    """بوتستراب **عنقودُه الجلسة** — تُعاد معاينةُ الجلسات بالإحلال."""
    if not diffs:
        return {"lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(seed)
    m = len(diffs)
    out = [sum(diffs[rng.randrange(m)] for _ in range(m)) / m for _ in range(n)]
    out.sort()
    a = (1.0 - level) / 2.0
    q = lambda p: out[min(max(int(round(p * (len(out) - 1))), 0), len(out) - 1)]
    return {"lo": q(a), "hi": q(1.0 - a), "n": m}


# ──────────────────────────────── التقرير ────────────────────────────────

def report(rows, n_syms, n_seen, year) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    rw = PB.r_win_value()
    _log(f"\n{'—' * 74}\n📊 T-PRESS-RANK سنة {year} — رموزٌ مفحوصة {n_syms} · "
         f"صفوفٌ جاهزة {len(rows)} · R_win={rw:.2f}")

    # `PV3` تغطية
    cov = 100.0 * n_syms / max(n_seen, 1)
    _log(f"   🩺 `PV3` التغطية {cov:.1f}% ({n_syms} من {n_seen}) · "
         f"مفقودٌ {n_seen - n_syms}")
    if cov < COVERAGE_MIN:
        _log(f"   ⛔ `PV3` دون {COVERAGE_MIN}% ⇒ خروج 3.")
        return 3
    if not rows:
        _log("   ⛔ صفرُ صفٍّ جاهز (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    by_sess = {}
    for r in rows:
        by_sess.setdefault(r["session"], []).append(r)
    sessions = sorted(by_sess)
    if len(sessions) < FLOOR_SESSIONS:
        _log(f"   ⛔ الأرضية: الجلسات {len(sessions)} دون {FLOOR_SESSIONS} "
             "⇒ لا حكم (خروج 4).")
        return 4

    # `PV1` وسيطُ الجاهزين لكلّ جلسة
    per_n = [len(by_sess[s]) for s in sessions]
    med = statistics.median(per_n)
    _log(f"   📐 `PV1` وسيطُ الجاهزين/جلسة = {med:.1f} "
         f"(المدى {min(per_n)}-{max(per_n)})")
    if med < PV1_MEDIAN_MIN:
        _log(f"   ⛔ `PV1` دون {PV1_MEDIAN_MIN} ⇒ السقفُ لا يبنّد فلا سؤال "
             "(خروج 4).")
        return 4

    res = {}
    for name in ("A0", "A1", "A3"):
        fn = {"A0": order_a0, "A1": order_a1, "A3": order_a3}[name]
        res[name] = deliver(by_sess, sessions, fn, rw)
    draws, last_a2 = [], None
    for sd in range(N_SEEDS):
        rng = random.Random(sd)
        d = deliver(by_sess, sessions, lambda xs, _r=rng: order_a2(xs, _r), rw)
        draws.append(sum(d["per_sess"].values()) / len(sessions))
        last_a2 = d
    draws.sort()
    p95 = draws[min(max(int(round(0.95 * (len(draws) - 1))), 0), len(draws) - 1)]
    a2_med = statistics.median(draws)

    # `PV2` تفرّقُ الأذرع
    set0 = {(c["s"], c["sym"]) for c in res["A0"]["cards"]}
    set1 = {(c["s"], c["sym"]) for c in res["A1"]["cards"]}
    only1 = len(set1 - set0)
    _log(f"   📐 `PV2` كروتٌ تُسلّمها `A1` ولا تُسلّمها `A0`: {only1}")
    if only1 == 0:
        _log("   ⛔ `PV2` `A1` لم تتفرّق عن `A0` إطلاقًا ⇒ `no-op` (خروج 4).")
        return 4

    # `PV4` الدِدوب
    bad = {k: dedupe_violations(v["cards"]) for k, v in res.items()}
    bad["A2"] = dedupe_violations((last_a2 or {}).get("cards") or [])
    _log("   📐 `PV4` خرقُ الدِدوب لكلّ ذراع: "
         + " · ".join(f"{k}={v}" for k, v in bad.items()))
    if any(v for v in bad.values()):
        _log("   ⛔ `PV4` الدِدوبُ غيرُ نافذ ⇒ خروج 3.")
        return 3

    _log("   ┌─ الأذرع (المقياسُ الحاكم: صافي R المُسلَّم لكلّ جلسة) ────────")
    for name in ("A0", "A1", "A3"):
        v = res[name]
        n_cards = len(v["cards"])
        dec = [c for c in v["cards"] if c["oc"] in ("win", "loss")]
        k = sum(1 for c in dec if c["oc"] == "win")
        wl, wh = (0.0, 0.0)
        try:
            import rebound_arms as RB                            # noqa: PLC0415
            wl, wh = RB.wilson(k, len(dec)) if dec else (0.0, 0.0)
        except Exception:                                        # noqa: BLE001
            pass
        _log(f"   │ {name}: {sum(v['per_sess'].values()) / len(sessions):+.4f}"
             f" · كروت {n_cards} · محسومة {len(dec)} · بلغ الهدف "
             f"{(100.0 * k / len(dec) if dec else 0.0):5.2f}% "
             f"[{100 * wl:.1f},{100 * wh:.1f}] · بنّد السقف {v['bind']} جلسة")
    _log(f"   │ A2 العشوائيّ: وسيط {a2_med:+.4f} · مئين 95 {p95:+.4f} "
         f"(‏{N_SEEDS} بذرة)")
    _log("   └───────────────────────────────────────────────────────────")

    n_cards0 = len(res["A0"]["cards"])
    if n_cards0 < FLOOR_CARDS:
        _log(f"   ⛔ الأرضية: كروتُ `A0` {n_cards0} دون {FLOOR_CARDS} "
             "⇒ لا حكم (خروج 4).")
        return 4

    d1 = (sum(res["A1"]["per_sess"].values())
          - sum(res["A0"]["per_sess"].values())) / len(sessions)
    d3 = (sum(res["A3"]["per_sess"].values())
          - sum(res["A0"]["per_sess"].values())) / len(sessions)
    ci = boot_ci([res["A1"]["per_sess"][s] - res["A0"]["per_sess"][s]
                  for s in sessions])
    _log(f"   📐 A1−A0 = {d1:+.4f} [{ci['lo']:+.4f},{ci['hi']:+.4f}] · "
         f"A3−A0 = {d3:+.4f} · A1 فوق مئين95؟ "
         f"{'نعم' if sum(res['A1']['per_sess'].values()) / len(sessions) > p95 else 'لا'}")
    swept_n = sum(1 for r in rows if r.get("swept"))
    _log(f"   🩸 حصّةُ المكنوس بعد حفظٍ من الجاهزين: "
         f"{100.0 * swept_n / len(rows):.1f}% ({swept_n} من {len(rows)})")

    _log("DIFFS " + json.dumps(
        {"year": year,
         "d": [round(res["A1"]["per_sess"][s] - res["A0"]["per_sess"][s], 6)
               for s in sessions]}, ensure_ascii=False))
    _log("PRANK " + json.dumps(
        {"year": year, "sessions": len(sessions), "ready": len(rows),
         "median_ready": med, "bind": res["A0"]["bind"],
         "swept_pct": round(100.0 * swept_n / len(rows), 1),
         "r_win": round(rw, 4), "p95": round(p95, 4),
         "a2_med": round(a2_med, 4), "only1": only1,
         "arms": {k: {"net": round(sum(v["per_sess"].values())
                                   / len(sessions), 4),
                      "cards": len(v["cards"]),
                      "dec": sum(1 for c in v["cards"]
                                 if c["oc"] in ("win", "loss")),
                      "win": sum(1 for c in v["cards"] if c["oc"] == "win")}
                  for k, v in res.items()},
         "d1": round(d1, 4), "d3": round(d3, 4),
         "ci": {"lo": round(ci["lo"], 4), "hi": round(ci["hi"], 4)}},
        ensure_ascii=False))
    return 0


# ─────────────────────────── `PV0` بوّابةُ التكامل ───────────────────────────

def pv0_gate(hist, year) -> tuple:
    """يُعيد مِشيةَ §⑬ **بالاسم** (`press_wake_arms.walk_symbol_wake`) ويقارن
    محسومةَ `HOLD3` بالمنشور سنةً بسنة. يرجّع (نجح، محسومة، فائزة)."""
    import press_radar as PR                                     # noqa: PLC0415
    import press_wake_arms as PW                                 # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    recs = []
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        recs.extend(PW.walk_symbol_wake(sym, df, year=year))
    h3 = [e for e in recs if int(e.get("hold") or 0) >= PR.READY_HOLD]
    dec = [e for e in h3 if e["oc"] in ("win", "loss")]
    k = sum(1 for e in dec if e["oc"] == "win")
    exp = PV0_RESOLVED.get(str(year))
    ok = exp is not None and len(dec) == exp
    return ok, len(dec), k


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🗜️🥇 T-PRESS-RANK — سنة {year}\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    yr = year if year and year != "?" else None

    ok, dec, k = pv0_gate(hist, yr)
    _log(f"   {'✅' if ok else '⛔'} `PV0` HOLD3 محسومة={dec} · فائزة={k} "
         f"(المنشور {PV0_RESOLVED.get(str(year), '؟')})")
    if not ok:
        _log("   ⛔ `PV0` تفرّقٌ عن أرقام §⑬ المنشورة ⇒ عطبُ أداةٍ لا نتيجة "
             "(خروج 3).")
        return 3

    rows, n_syms, n_seen = [], 0, 0
    for sym, df in hist.items():
        n_seen += 1
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        rows.extend(ready_rows(sym, df, yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · صفوفٌ جاهزة {len(rows)}")
    return report(rows, n_syms, n_seen, year)


if __name__ == "__main__":
    sys.exit(main())
