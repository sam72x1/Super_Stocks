#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩸📏 T-SLIP — قياسُ الانزلاق الحقيقيّ على الوقف (العقد: `slip_prereg.md`).

**السؤال:** عند ضرب الوقف، بكم كنّا سنخرج **فعلًا**؟ وهل يصمد فارقُ «وقفه
قاعه» (‏`P1` مقابل `P0` = ‏+0.689R المنشور) بعد إدخال الانزلاق؟

🔴 **ولماذا يهمّ:** مخاطرةُ `P0` ‏0.10 من القاع ومخاطرةُ `P1` ‏0.03 ⇒
**الانزلاقُ نفسُه بالدولار يكلّف `P1` ‏3.3 أضعافَ ما يكلّف `P0`** بوحدة
المخاطرة ⇒ **الافتراضُ ليس محايدًا** (تصحيحٌ ذاتيٌّ منشورٌ في
`gold_entry_result.md §④`).

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** المِشيةُ والحلقاتُ والخطط من
`gold_entry_arms.walk_symbol_gold(..., with_plan=True)` · وفهرسُ شمعة الوقف
من `gold_entry_arms.stop_bar` (مرآةُ `resolve_episode`، لا تمسّها) · وشموعُ
الدقيقة من `event_exec.hist_minute_bars` (‏`adjusted=true` عمدًا ليطابق
اللقطة) وتوقيتُ نيويورك من `event_exec.NY`.

قراءةٌ/قياسٌ فقط · **صفرُ مسٍّ بالإنتاج** · لا `LOGIC_VERSION` · الإنتاجُ لا
يستورد هذا الملفّ.
"""
from __future__ import annotations

import json
import os
import sys
import time

# ═══ ثوابتُ العقد — مثبَّتةٌ قبل أيّ رقم ═══
QARMS = ("Q0", "Q1", "Q2", "Q3")      # §③: أربعةٌ ولا خامسة
PARMS = ("P0", "P1", "P2")            # §④: الأذرعُ المقيسة
GOV_Q, GOV_A, GOV_B = "Q2", "P1", "P0"   # المقياسُ الحاكم: E(P1)−E(P0) تحت Q2
SCALE_TOL = float(os.environ.get("SLIP_SCALE_TOL") or 0.02)   # §⑥ W2
COV_MIN = 90.0                        # §⑥ W3
SESS_OPEN, SESS_CLOSE = (9, 30), (16, 0)   # §② الجلسةُ النظاميّة وحدَها
MAX_FETCH = int(os.environ.get("SLIP_MAX_FETCH") or 40000)
WORKERS = int(os.environ.get("SLIP_WORKERS") or 6)
# 🔗 مِرساةُ التكامل `W0` — أرقامُ `gold_entry_result.md §①` المنشورة
PUB = {"2023": {"P0": (1660, 0.300), "P1": (1671, 1.153), "P2": (1642, 0.870)},
       "2024": {"P0": (1857, 0.103), "P1": (1862, 0.707), "P2": (1838, 0.453)},
       "2025": {"P0": (1854, 0.131), "P1": (1869, 0.759), "P2": (1842, 0.460)}}


def _log(m):
    print(m, flush=True)


# ═══════════════════ دوالُّ نقيّة (تُختبَر مباشرةً) ═══════════════════
def session_slice(bars, tz=None):
    """نقيّة: شموعُ **الجلسة النظاميّة وحدَها** (‏09:30-16:00 نيويورك) مرتَّبةً
    زمنيًّا. §② من العقد: الشمعةُ اليوميّة في اللقطة نظاميّةٌ حصرًا، فبحثٌ في
    البريماركت **يُطلق وقفًا لم ترَه الشمعةُ التي قرّرت الخسارة**."""
    if tz is None:
        import event_exec as EX                                  # noqa: PLC0415
        tz = EX.NY
    from datetime import datetime, timezone                      # noqa: PLC0415
    out = []
    for b in bars or []:
        try:
            t = float(b["t"])
            o, h, lo_, c = (float(b["o"]), float(b["h"]),
                            float(b["l"]), float(b["c"]))
        except (TypeError, ValueError, KeyError):
            continue
        if any(x != x or x <= 0 for x in (o, h, lo_, c)):   # ⚠️ NaN ليس None
            continue
        d = datetime.fromtimestamp(t / 1000.0, timezone.utc).astimezone(tz)
        hm = (d.hour, d.minute)
        if hm < SESS_OPEN or hm >= SESS_CLOSE:
            continue
        out.append({"t": t, "o": o, "h": h, "l": lo_, "c": c})
    out.sort(key=lambda x: x["t"])
    return out


def trigger_index(sess, stop):
    """نقيّة: فهرسُ **أوّل دقيقةٍ قاعُها يبلغ الوقف**. لا شيء ⇒ None."""
    try:
        st = float(stop)
    except (TypeError, ValueError):
        return None
    for k, b in enumerate(sess or []):
        if b["l"] <= st:
            return k
    return None


def fills(sess, stop):
    """نقيّة: أسعارُ التعبئة الأربعة (‏§③) لحدثِ وقفٍ واحد.

    `Q0` عند الوقف · `Q1` واعٍ بالفجوة · `Q2` **الحاكمة** (فجوة ‏+ إغلاقُ
    دقيقة الزناد) · `Q3` أسوأُ حال (قاعُ دقيقة الزناد).
    ‏`Q2c` **وصفيّةٌ لا تحكم**: `Q2` مقصوصةً عند الوقف — لأن أمرَ الوقف السوقيّ
    لا يُنفَّذ **أعلى** من مستواه عمليًّا، **والعقدُ سجّل `Q2` بلا قصّ فتُنشَر
    كما سُجِّلت** ومعها المقصوصة (نمطُ ملحق ① في `T-GOLD-ENTRY`).
    ترجع None إن تعذّر (لا جلسة / لا زناد)."""
    if not sess:
        return None
    try:
        st = float(stop)
    except (TypeError, ValueError):
        return None
    k = trigger_index(sess, st)
    if k is None:
        return None
    op = sess[0]["o"]
    gap = bool(op <= st)
    q1 = op if gap else st
    q2 = op if gap else sess[k]["c"]
    q3 = op if gap else sess[k]["l"]
    return {"Q0": st, "Q1": q1, "Q2": q2, "Q3": q3,
            "Q2c": min(q2, st), "gap": gap, "k": k,
            "sess_open": op, "sess_close": sess[-1]["c"],
            "sess_low": min(b["l"] for b in sess)}


def loss_r(avg, stop, fill):
    """نقيّة: خسارةٌ بوحدة مخاطرة الخطة —
    `−(المتوسّط − سعرُ التعبئة) ÷ (المتوسّط − الوقف)`.
    التعبئةُ عند الوقف ⇒ **‏−1.0 بالضبط** (فتُعيد `Q0` المنشورَ بت-بت).
    مخاطرةٌ غيرُ موجبة ⇒ ‏−1.0 (فاشلٌ-آمن، لا قسمةَ على صفر)."""
    try:
        a, s, f = float(avg), float(stop), float(fill)
    except (TypeError, ValueError):
        return -1.0
    risk = a - s
    if risk <= 0 or risk != risk:
        return -1.0
    return -(a - f) / risk


def scale_ok(sess_close, daily_close, tol=None):
    """نقيّة (‏`W2`): إغلاقُ الجلسة من الدقائق يطابق إغلاقَ اللقطة اليوميّ ضمن
    `tol`. تعذّرٌ ⇒ False (يُستبعَد ويُعَدّ — لا يُخمَّن ولا يُصحَّح)."""
    t = SCALE_TOL if tol is None else float(tol)
    try:
        a, b = float(sess_close), float(daily_close)
    except (TypeError, ValueError):
        return False
    if a <= 0 or b <= 0 or a != a or b != b:
        return False
    return abs(a - b) / b <= t


def _stats(xs):
    """وسيط · متوسّط · p90 — نقيّة، قائمةٌ فارغة ⇒ أصفار."""
    v = sorted(float(x) for x in xs if x == x)
    n = len(v)
    if not n:
        return {"n": 0, "med": 0.0, "avg": 0.0, "p90": 0.0}
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0
    return {"n": n, "med": med, "avg": sum(v) / n,
            "p90": v[min(n - 1, int(round(0.90 * (n - 1))))]}


def _paired(rs_a, rs_b):
    """فاصلُ 95% للفرق **المقترن** بين قائمتَي `R` (بنفس ترتيب الحلقات)."""
    ds = [a - b for a, b in zip(rs_a, rs_b)]
    m = len(ds)
    if m < 2:
        return None, None, m
    mean = sum(ds) / m
    var = sum((d - mean) ** 2 for d in ds) / (m - 1)
    se = (var / m) ** 0.5
    return mean - 1.96 * se, mean + 1.96 * se, m


# ═══════════════════ الجلب (فاشلٌ-آمن · مُعادُ الاستعمال بالاسم) ═══════════
def fetch_day(sym, iso, tries=3):
    """شموعُ دقيقةِ يومٍ واحد عبر `event_exec.hist_minute_bars` **بالاسم**، مع
    إعادةِ محاولةٍ محلّيّة (لا تُمَسّ `event_exec` — أرقامُها منشورة)."""
    import event_exec as EX                                      # noqa: PLC0415
    for a in range(tries):
        try:
            b = EX.hist_minute_bars(sym, iso, iso)
        except Exception:                                        # noqa: BLE001
            b = None
        if b:
            return b
        if a + 1 < tries:
            time.sleep(0.4 * (a + 1))
    return None


def main() -> int:                                               # noqa: C901
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    import gold_entry_arms as GE                                 # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    out_p = os.environ.get("SLIP_OUT") or "slip_events.jsonl"
    _log(f"\n{'=' * 78}\n🩸📏 T-SLIP — سنة {year}\n{'=' * 78}")
    _log(f"📐 أذرعُ التنفيذ: {' · '.join(QARMS)} · الأذرعُ المقيسة "
         f"{' · '.join(PARMS)} · الحاكم E({GOV_A})−E({GOV_B}) تحت {GOV_Q} · "
         f"الجلسة {SESS_OPEN[0]}:{SESS_OPEN[1]:02d}-{SESS_CLOSE[0]}:00 NY · "
         f"حارسُ المقياس {SCALE_TOL * 100:.1f}%")
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ اللقطةُ فارغة ⇒ خروج 2.")
        return 2
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")

    # ① المِشية — نفسُ محرّك `T-GOLD-ENTRY` بالاسم
    recs, n_syms = [], 0
    yr = year if year and year != "?" else None
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        recs.extend(GE.walk_symbol_gold(sym, df, year=yr, with_plan=True))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(recs)}")
    _log(f"🚶 حلقات {len(recs)} · رموزٌ مُشيت {n_syms}")
    if not recs:
        _log("⛔ صفرُ حلقات (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    # ② أحداثُ الوقف الفريدة (رمز، تاريخ)
    need, ev_n = {}, 0
    for e in recs:
        pl = e.get("plan") or {}
        for a in PARMS:
            p = pl.get(a) or {}
            if e[a][0] and e[a][1] == "loss" and p.get("date"):
                need.setdefault((e["sym"], p["date"]), None)
                ev_n += 1
    keys = sorted(need)
    _log(f"🩸 أحداثُ وقفٍ {ev_n} · أزواجٌ فريدة (رمز، تاريخ) {len(keys)}")
    if len(keys) > MAX_FETCH:
        _log(f"⚠️ قصٌّ مُعلَن: السقف {MAX_FETCH} ⇒ يُقصّ {len(keys) - MAX_FETCH}"
             f" زوجًا (‏`budget_cut`) — لا قصَّ صامت.")
        cut = set(keys[MAX_FETCH:])
        keys = keys[:MAX_FETCH]
    else:
        cut = set()

    # ③ الجلب المتوازي — النتيجةُ قاموسٌ فلا يعتمد الترتيب (حتميّ)
    import concurrent.futures as _cf                             # noqa: PLC0415
    t0 = time.time()
    done = 0
    with _cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_day, k[0], k[1]): k for k in keys}
        for f in _cf.as_completed(futs):
            need[futs[f]] = f.result()
            done += 1
            if done % 500 == 0:
                _log(f"  … جُلب {done}/{len(keys)} "
                     f"({time.time() - t0:.0f}ث)")
    _log(f"⬇️ اكتمل الجلب: {done} زوجًا في {time.time() - t0:.0f}ث")

    # ④ التعبئة لكلّ حدث + عدّاداتُ الاستبعاد المسمّاة (‏W3)
    why = {"no_minutes": 0, "scale_mismatch": 0, "no_trigger": 0,
           "budget_cut": 0}
    cache, rows = {}, []
    for e in recs:
        pl = e.get("plan") or {}
        for a in PARMS:
            p = pl.get(a) or {}
            if not (e[a][0] and e[a][1] == "loss" and p.get("date")):
                continue
            key = (e["sym"], p["date"])
            ck = (key, round(float(p["stop"]), 6))
            if ck in cache:
                fx = cache[ck]
            else:
                if key in cut:
                    fx = ("budget_cut", None)
                else:
                    bars = need.get(key)
                    sess = session_slice(bars) if bars else []
                    if not sess:
                        fx = ("no_minutes", None)
                    elif not scale_ok(sess[-1]["c"], p.get("dclose")):
                        fx = ("scale_mismatch", None)
                    else:
                        fl = fills(sess, p["stop"])
                        fx = (("no_trigger", None) if fl is None
                              else ("ok", fl))
                cache[ck] = fx
            st, fl = fx
            if st != "ok":
                why[st] += 1
                continue
            rows.append({"sym": e["sym"], "i": e["i"], "arm": a,
                         "date": p["date"], "avg": p["avg"],
                         "stop": p["stop"], "gap": fl["gap"],
                         **{q: fl[q] for q in QARMS}, "Q2c": fl["Q2c"],
                         "same_bar": bool(p.get("same_bar")),
                         "dopen": p.get("dopen"), "dlow": p.get("dlow")})
    meas = len(rows)
    cov = 100.0 * meas / max(ev_n, 1)
    _log(f"\n🩺 W3 التغطية: {meas} من {ev_n} = {cov:.1f}% · "
         f"مستبعَدون: " + " · ".join(f"{k}={v}" for k, v in sorted(why.items())))
    partial = cov < COV_MIN
    if partial:
        _log(f"⚠️ التغطيةُ دون {COV_MIN}% ⇒ **النتيجةُ جزئيّةٌ** ويُصرَّح بذلك.")

    fmap = {(r["sym"], r["i"], r["arm"]): r for r in rows}
    try:
        with open(out_p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        _log(f"💾 {out_p}: {len(rows)} صفًّا")
    except Exception as _e:                                      # noqa: BLE001
        _log(f"⚠️ تعذّر حفظُ الصفوف: {type(_e).__name__}")

    # ⑤ إعادةُ حساب `E` لكلّ (ذراعٍ مقيسة × ذراعِ تنفيذ)
    def r_of(e, a, q):
        el, oc, rw = e[a]
        if oc == "win":
            return rw
        r = fmap.get((e["sym"], e["i"], a))
        if r is None or q == "Q0":
            return -1.0
        return loss_r(r["avg"], r["stop"], r[q])

    dec = {a: [e for e in recs if e[a][0] and e[a][1] in ("win", "loss")]
           for a in PARMS}
    E = {a: {q: (sum(r_of(e, a, q) for e in dec[a]) / len(dec[a])
                 if dec[a] else None) for q in tuple(QARMS) + ("Q2c",)}
         for a in PARMS}

    # ⑥ `W0` بوّابةُ التكامل — بت-بت مع المنشور
    _log("\n🔗 W0 مِرساةُ التكامل (‏`Q0` يجب أن يعيد `gold_entry_result §①`):")
    bad = 0
    for a in PARMS:
        n_d = len(dec[a])
        e0 = E[a]["Q0"]
        exp = (PUB.get(year) or {}).get(a)
        tag = "—"
        if exp:
            ok = (n_d == exp[0] and e0 is not None
                  and abs(e0 - exp[1]) < 6e-4)   # المنشورُ مدوَّرٌ 3 خانات
                  # (‏6e-4 يسع التدوير · وأيُّ عطبٍ حقيقيٍّ يحرّك E أكثرَ بمراتب)
            tag = "✅ مطابق" if ok else "🔴 **تفرّق**"
            bad += 0 if ok else 1
        _log(f"  {a}: محسومة={n_d} · E(Q0)="
             f"{(f'{e0:+.3f}' if e0 is not None else '—')} · المنشور="
             f"{exp if exp else '—'} {tag}")
    if bad:
        _log("⛔ W0: تفرّقٌ عن المنشور ⇒ **عطبُ أداةٍ لا نتيجة** ⇒ خروج 3.")
        return 3

    # ⑦ `W1` حارسُ الـ`no-op`
    _log("\n🔎 W1 حارسُ الـ`no-op` (خسائرُ تغيّر سعرُ تعبئتها عن الوقف):")
    chg = {q: sum(1 for r in rows if abs(r[q] - r["stop"]) > 1e-9)
           for q in QARMS}
    for q in QARMS:
        _log(f"  {q}: {chg[q]} من {meas}")
    if chg.get(GOV_Q, 0) == 0:
        _log("⛔ W1: صفرُ تغيّرٍ في الذراع الحاكمة ⇒ `no-op` ⇒ خروج 4.")
        return 4

    # ⑧ توزيعُ الانزلاق
    _log("\n📉 توزيعُ الانزلاق (‏% من مستوى الوقف · موجبٌ = أسوأ):")
    for a in PARMS:
        rs = [r for r in rows if r["arm"] == a]
        if not rs:
            continue
        pct = [100.0 * (r["stop"] - r[GOV_Q]) / r["stop"] for r in rs]
        ru = [(-loss_r(r["avg"], r["stop"], r[GOV_Q])) - 1.0 for r in rs]
        sp, su = _stats(pct), _stats(ru)
        gp = sum(1 for r in rs if r["gap"])
        _log(f"  {a}: ن={sp['n']} · وسيط={sp['med']:+.2f}% "
             f"متوسّط={sp['avg']:+.2f}% p90={sp['p90']:+.2f}% ⟵⟶ "
             f"بوحدة المخاطرة: وسيط={su['med']:+.3f}R متوسّط={su['avg']:+.3f}R"
             f" p90={su['p90']:+.3f}R · فجوةٌ كاملة={gp} ({100.0*gp/len(rs):.1f}%)")

    # ⑨ جدولُ `E` والفارقُ الحاكم
    _log(f"\n📊 `E` لكلّ صفقةٍ محسومة (سنة {year}):")
    _log(f"{'الذراع':<6}" + "".join(f"{q:>10}" for q in QARMS) + f"{'Q2c*':>10}")
    for a in PARMS:
        _log(f"{a:<6}" + "".join(
            f"{(f'{E[a][q]:+.3f}' if E[a][q] is not None else '—'):>10}"
            for q in tuple(QARMS) + ("Q2c",)))
    _log("   * `Q2c` وصفيّةٌ لا تحكم (‏`Q2` مقصوصةً عند الوقف).")

    _log(f"\n🎯 الفارقُ {GOV_A}−{GOV_B} تحت كلّ ذراعِ تنفيذ:")
    for q in tuple(QARMS) + ("Q2c",):
        ea, eb = E[GOV_A][q], E[GOV_B][q]
        d = (ea - eb) if (ea is not None and eb is not None) else None
        _log(f"  {q}: {(f'{d:+.3f}R' if d is not None else '—')}")
    if any(E[a][q] is None for a in (GOV_A, GOV_B) for q in QARMS):
        _log("⛔ `E` غيرُ محسوبٍ لذراعٍ حاكمة (‏مقامٌ فارغ) ⇒ خروج 4.")
        return 4
    q0d = (E[GOV_A]["Q0"] - E[GOV_B]["Q0"])
    _log(f"  ↳ العامليّة: الفجوة (‏Q1−Q0) = "
         f"{(E[GOV_A]['Q1'] - E[GOV_B]['Q1']) - q0d:+.3f}R · "
         f"ما داخل الدقيقة (‏Q2−Q1) = "
         f"{(E[GOV_A]['Q2'] - E[GOV_B]['Q2']) - (E[GOV_A]['Q1'] - E[GOV_B]['Q1']):+.3f}R"
         f" · ذيلُ الدقيقة (‏Q3−Q2) = "
         f"{(E[GOV_A]['Q3'] - E[GOV_B]['Q3']) - (E[GOV_A]['Q2'] - E[GOV_B]['Q2']):+.3f}R")

    # ⑩ الفاصلُ المقترن للفارق الحاكم
    common = [e for e in recs
              if e[GOV_A][0] and e[GOV_B][0]
              and e[GOV_A][1] in ("win", "loss")
              and e[GOV_B][1] in ("win", "loss")]
    for q in ("Q0", GOV_Q):
        ra = [r_of(e, GOV_A, q) for e in common]
        rb = [r_of(e, GOV_B, q) for e in common]
        lo95, hi95, m = _paired(ra, rb)
        mean = (sum(ra) - sum(rb)) / m if m else 0.0
        _log(f"  فاصلُ 95% للفرق المقترن تحت {q}: "
             f"{(f'{mean:+.3f} [{lo95:+.3f},{hi95:+.3f}] ن={m}' if lo95 is not None else '—')}")

    # ⑪ الرفيقُ غيرُ المتحيّز: **المقيسُ فقط** (كلا الذراعين قابلٌ للقياس)
    sub = [e for e in common
           if all(e[a][1] == "win" or (e["sym"], e["i"], a) in fmap
                  for a in (GOV_A, GOV_B))]
    if sub:
        ra = [r_of(e, GOV_A, GOV_Q) for e in sub]
        rb = [r_of(e, GOV_B, GOV_Q) for e in sub]
        lo95, hi95, m = _paired(ra, rb)
        _log(f"\n🧪 الرفيقُ «المقيسُ فقط» (الحلقاتُ التي قِيس فيها الذراعان): "
             f"ن={len(sub)} · E({GOV_A})={sum(ra)/len(ra):+.3f} · "
             f"E({GOV_B})={sum(rb)/len(rb):+.3f} · الفارق="
             f"{(sum(ra)-sum(rb))/len(sub):+.3f}R"
             f"{f' [{lo95:+.3f},{hi95:+.3f}]' if lo95 is not None else ''}")
    # ⑫ «الوقفُ في شمعة الدخول نفسِها» — حالةٌ لم يعالجها العقد ⇒ **تُعَدّ
    #    وتُنشَر ومعها رفيقٌ يستبعدها**، ولا تُصحَّح بعد الأرقام.
    _sb_rows = [r for r in rows if r.get("same_bar")]
    _log(f"\n📌 «الوقفُ في شمعة الدخول نفسِها»: {len(_sb_rows)} من {meas}"
         f" ({100.0 * len(_sb_rows) / max(meas, 1):.1f}%) — عند الفجوة يُفترَض"
         f" فيها التعبئةُ عند الافتتاح **قبل** لحظةِ دخولنا فعليًّا ⇒ رفيقٌ"
         f" يستبعدها (وصفيٌّ لا يحكم):")
    fmap2 = {k: v for k, v in fmap.items() if not v.get("same_bar")}
    _sb_excl = [e for e in common
                if all(e[a][1] == "win" or (e["sym"], e["i"], a) in fmap2
                       for a in (GOV_A, GOV_B))]
    if _sb_excl:
        def _r2(e, a, q):
            el, oc, rw = e[a]
            if oc == "win":
                return rw
            r = fmap2.get((e["sym"], e["i"], a))
            if r is None or q == "Q0":
                return -1.0
            return loss_r(r["avg"], r["stop"], r[q])
        _ra = [_r2(e, GOV_A, GOV_Q) for e in _sb_excl]
        _rb = [_r2(e, GOV_B, GOV_Q) for e in _sb_excl]
        _lo, _hi, _m = _paired(_ra, _rb)
        _log(f"   ن={len(_sb_excl)} · E({GOV_A})={sum(_ra)/len(_ra):+.3f} · "
             f"E({GOV_B})={sum(_rb)/len(_rb):+.3f} · الفارق="
             f"{(sum(_ra)-sum(_rb))/len(_sb_excl):+.3f}R"
             f"{f' [{_lo:+.3f},{_hi:+.3f}]' if _lo is not None else ''}")
    _log("\n⚠️ شموعُ الدقيقة صفقاتٌ مجمَّعة والتعبئةُ الحقيقيّة على NBBO ·"
         " وبلا نمذجةِ طابورٍ أو تعبئةٍ جزئيّة ⇒ **أرضيّةُ ضررٍ لا سقفُه** ·"
         " وانزلاقُ الدخول والهدف خارجَ النطاق (‏§⑨ من العقد).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
