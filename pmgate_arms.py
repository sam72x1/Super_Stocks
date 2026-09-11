#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅⏱️ `T-PMGATE` — بوّابةُ «فتحِ البري + 30 دقيقة» (العقد `pmgate_prereg.md`
مدفوعٌ **ومدموجٌ في `main` قبل هذا الملفّ** وقبل أيّ رقمٍ منه).

**الدعوى المقيسة:** للسهم الصاعد في الافتر — عند **‏04:30 نيويورك** (فتحُ
البريماركت ‏+ 30 دقيقة): هل تجاوز **قمّةَ الافتر**؟ فإن لم يتجاوزها فبقيّةُ
البري محدودة.

**ثلاثةُ دلاءٍ لا اثنان** (‏§① من العقد): `G-YES` تجاوز · `G-NO` لم يتجاوز
وقد تداول · **`G-NONE` لم يتداول بعدُ** — تُعلَن ولا تُطوى، ولها حساسيّةٌ ثانية.

🔑 **المقياسُ الحاكم `FWD` من سعرِ لحظة القرار لا من إغلاق الأمس:** `G-YES`
تجاوزت القمّةَ **بالتعريف** فتبدأ أعلى ميكانيكيًّا بمرجع الأمس، وهو بعينه
الاعتراضُ الذي أضعف `AX1` في `T-AHEXT-2` ⇒ حُصِّن هنا قبل أن يقع.

🔒 **التجميدُ بالبناء لا بالنسخ:** العتباتُ ودوالُّ القياس وآلةُ الطبقات
**تُستورَد بالاسم** من `ahext_arms` و`ahext2_arms` ⇒ لا تنحرف ولو أردتُ،
**وبذرةُ المعاينة تبقى كما هي** فالعيّنةُ هي عيّنةُ `T-AHEXT-2` بت-بت.

🔒 قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor

import Super_stock as S
# ── الاستيرادُ بالاسم = التجميدُ بالبناء (‏`V-P7` · §② من العقد) ──
from ahext_arms import (AH_MIN, COVER_MIN, GAP_MIN, PM_MIN, PRICE_HI, PRICE_LO,
                        classify_arm, et_ms, minutes_range, official_close,
                        screen_symbol, window_last_close, window_peak)
from ahext2_arms import (H_CAP, L_N, NEFF_MIN, SEED_TAG, THREADS, WSUM_TOL,
                         Z_N, plan_stratum, strata, w_pctile, w_rate)
# ⚠️ `measure` و`kish` **لا يُستورَدان هنا**: الأولى مرجعُ المطابقة في السويّة
#    (‏`V-P7` يستوردها بنفسه) والثانية يستعملها `w_rate` داخليًّا — واستيرادٌ
#    ميّتٌ «للتزيين» يُرضي قفلًا نصّيًّا ولا يُثبت وصلًا (الصنفُ ② المدوَّن).

# ── ثوابتُ هذي الأداة وحدَها (‏`V-P8` · تُطبَع في كلّ تقرير) ──
GATES = ("0415", "0430", "0445", "0500")   # `C-TIME` — والحاكمةُ وحدَها أدناه
GATE_MAIN = "0430"                          # «‏11 ونص» = فتحُ البري + 30 دقيقة
PM_OPEN = (4, 0)                            # فتحُ البريماركت بتوقيت نيويورك
PM_CLOSE = (9, 30)                          # جرسُ الافتتاح — حصرًا (‏`V-P2`)
AH_WIN = ((16, 0), (20, 0))                 # نافذةُ الافتر في `D-1`
BOOT = 5000                                 # إعاداتُ البوتستراب
BOOT_SEED = 20260911                        # بذرةٌ ثابتةٌ تُطبَع (لا عشوائيّةَ خفيّة)
OUT_ROWS = "pmgate_rows.jsonl"


def _log(m):
    print(m, flush=True)


# ══════════════════ دوالُّ نقيّة (تُقفَل سلوكيًّا) ══════════════════
def gate_key_ms(date_iso: str, key: str) -> int:
    """مفتاحُ بوّابةٍ `"HHMM"` ⟶ لحظةٌ **بتوقيت نيويورك** عبر `et_ms`.

    🔒 **ولا UTC مثبَّت هنا ولا في أيّ نافذة** — عطبٌ مقيسٌ عندنا مرّتين،
    والتحويلُ عبر `ZoneInfo` يتصيّف ويتشتّى آليًّا (‏`V-P2`)."""
    return et_ms(date_iso, int(key[:2]), int(key[2:]))


def bucket_of(ah_hi, hi_a, n_a: int) -> str:
    """الدلوُ عند لحظة القرار — **ثلاثةٌ لا اثنان** (‏§① من العقد).

    `G-NONE` ليست «تعذّرَ قياس» بل **حالةٌ حقيقيّة**: لم يتداول بعدُ عند تلك
    اللحظة ⇒ سعرُ القرار غيرُ معرَّف. وطيُّها صمتًا يُعيد انحيازَ `AX5`."""
    if n_a <= 0:
        return "G-NONE"
    if ah_hi is None or hi_a is None:
        return "G-NONE"
    return "G-YES" if float(hi_a) > float(ah_hi) else "G-NO"


def gate_measure(sym: str, prev_date: str, date: str,
                 fetch_close=None, fetch_bars=None, gates=GATES):
    """صفٌّ واحدٌ مقيس — **بجلبةٍ واحدةٍ تغطّي الجلستين** كما في `measure`.

    🔒 **`V-P7`:** الحقولُ الستّةُ الأولى (`prev_close` · `ah_rise` ·
    `ah_close_rise` · `ah_bars` · `pm_peak` · `n_bars`) **بصيغِ `measure`
    نفسِها حرفًا بحرف** ⇒ الأداةُ لم تنحرف عن الأصل، **والأصلُ لا يُمَسّ**.

    🔒 **`V-P2` صفرُ نظرٍ مستقبليّ:** كلُّ نافذةٍ `[frm, to)` حصرًا ⇒ شمعةُ
    الحدّ الأعلى خارجها · و`PM-a` و`PM-b` **لا تتقاطعان** عند البوّابة.

    🔒 **الجالبان محقونان** والقيمُ الافتراضيّةُ هي دوالُّ الشبكة نفسُها ⇒
    **مسارُ الإنتاج بت-بت والسويّةُ تختبر هذا المسارَ بعينه** (درسُ `AHX6`)."""
    pc = (fetch_close or official_close)(sym, prev_date)
    if not pc:
        return None
    ah_f = et_ms(prev_date, *AH_WIN[0])
    ah_t = et_ms(prev_date, *AH_WIN[1])
    pm_f = et_ms(date, *PM_OPEN)
    pm_t = et_ms(date, *PM_CLOSE)
    bars = (fetch_bars or minutes_range)(sym, ah_f, pm_t)
    if bars is None:
        return None

    ah_hi = window_peak(bars, ah_f, ah_t)
    ah_cl = window_last_close(bars, ah_f, ah_t)
    n_ah = sum(1 for b in bars if ah_f <= int(b["t"]) < ah_t)
    pm_hi = window_peak(bars, pm_f, pm_t)

    out = {"symbol": sym, "date": date, "prev_date": prev_date,
           "prev_close": round(pc, 4),
           "ah_rise": 0.0 if ah_hi is None else round(ah_hi / pc - 1.0, 4),
           "ah_close_rise": (None if ah_cl is None
                             else round(ah_cl / pc - 1.0, 4)),
           "ah_bars": n_ah,
           "pm_peak": None if pm_hi is None else round(pm_hi / pc - 1.0, 4),
           "n_bars": len(bars),
           "ah_hi": None if ah_hi is None else round(ah_hi, 4),
           "gates": {}}

    for k in gates:
        g = gate_key_ms(date, k)
        n_a = sum(1 for b in bars if pm_f <= int(b["t"]) < g)
        hi_a = window_peak(bars, pm_f, g)
        px = window_last_close(bars, pm_f, g)
        hi_b = window_peak(bars, g, pm_t)
        buck = bucket_of(ah_hi, hi_a, n_a)
        # `FWD` الحاكم: من **سعرِ لحظة القرار**. و`fwd_alt` للحساسيّة (§③-ب):
        # مرجعٌ بديلٌ = آخرُ إغلاقٍ في الافتر، يُبقي `G-NONE` بدل طيّها.
        px_alt = px if px is not None else ah_cl
        out["gates"][k] = {
            "n_a": n_a,
            "hi_a": None if hi_a is None else round(hi_a, 4),
            "px_gate": None if px is None else round(px, 4),
            "hi_b": None if hi_b is None else round(hi_b, 4),
            "bucket": buck,
            "fwd": (None if (hi_b is None or not px)
                    else round(hi_b / px - 1.0, 4)),
            "fwd_alt": (None if (hi_b is None or not px_alt)
                        else round(hi_b / px_alt - 1.0, 4)),
            "gate_ret": None if not px else round(px / pc - 1.0, 4)}
    return out


def clusters_of(rows, key: str, field: str = "fwd", thresh: float = PM_MIN):
    """يطوي الصفوفَ إلى **مجاميعَ لكلّ رمز** تكفي لإعادة حساب `Δ` بالضبط.

    🔑 وبها يصير البوتستراب **عنقوديًّا بالرمز** لا بالصفّ — والصفوفُ تتكرّر
    بالرمز فمعاملتُها مستقلّةً تُضيّق الفاصلَ كذبًا (نفسُ علّة ويلسون على
    العدد الموزون). والعنقدةُ **بالرمز عبر السنوات** فهي الأكثرُ تحفّظًا."""
    acc = {}
    for m in rows:
        g = m["gates"].get(key) or {}
        v, b = g.get(field), g.get("bucket")
        if v is None or b not in ("G-YES", "G-NO"):
            continue
        w = float(m["w"])
        a = acc.setdefault(m["symbol"], {"wy": 0.0, "hy": 0.0, "wn": 0.0,
                                         "hn": 0.0, "ny": 0, "nn": 0})
        hit = w if float(v) * 100.0 > float(thresh) else 0.0
        if b == "G-YES":
            a["wy"] += w
            a["hy"] += hit
            a["ny"] += 1
        else:
            a["wn"] += w
            a["hn"] += hit
            a["nn"] += 1
    return list(acc.values())


def delta_of(cl):
    """‏`Δ = hit(G-YES) − hit(G-NO)` بالنقاط — من مجاميع العناقيد وحدَها."""
    wy = sum(a["wy"] for a in cl)
    wn = sum(a["wn"] for a in cl)
    if wy <= 0 or wn <= 0:
        return None
    return (sum(a["hy"] for a in cl) / wy
            - sum(a["hn"] for a in cl) / wn) * 100.0


def boot_delta(cl, reps: int = BOOT, seed: int = BOOT_SEED):
    """فاصلُ بوتستراب **عنقوديٍّ بالرمز** لـ`Δ` — ببذرةٍ ثابتةٍ تُطبَع."""
    if not cl:
        return None
    rng = random.Random(seed)
    n, out = len(cl), []
    for _ in range(int(reps)):
        d = delta_of([cl[rng.randrange(n)] for _ in range(n)])
        if d is not None:
            out.append(d)
    if not out:
        return None
    out.sort()
    lo = out[int(0.025 * (len(out) - 1))]
    hi = out[int(0.975 * (len(out) - 1))]
    mean = sum(out) / len(out)
    var = sum((x - mean) ** 2 for x in out) / max(1, len(out) - 1)
    return {"lo": round(lo, 2), "hi": round(hi, 2),
            "se": round(var ** 0.5, 2), "reps": len(out)}


def _selfcheck_readonly() -> bool:
    """`V-P1` — قراءةٌ فقط بالـAST على مصدر هذي الأداة: صفرُ إرسالٍ وصفرُ
    كتابةِ حالة، والملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
    import ast as _a
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist",
              "save_op_entry_state", "record_new_alerts", "save_near_watch",
              "save_hunter_watch"}
    for n in _a.walk(_a.parse(src)):
        if isinstance(n, _a.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], _a.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, _a.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    if not (n.args and isinstance(n.args[0], _a.Name)
                            and n.args[0].id == "OUT_ROWS"):
                        return False
    return True


def _measure_year(hist, year: str, dry: bool):
    """يقيس سنةً واحدة ويُرجع (الصفوفُ الناجحة · الخطط · التغطية · حجمُ الكون)."""
    allrows = []
    for sym in sorted(hist):
        for c in screen_symbol(hist[sym], year):
            c["symbol"] = sym
            allrows.append(c)
    h, low, z = strata(allrows)
    if len(h) + len(low) + len(z) != len(allrows):
        return None, None, None, -1
    _log(f"🧱 [{year}] الكون {len(allrows)} صفًّا ⇒ H {len(h)} · "
         f"L {len(low)} · Z {len(z)}")

    spec = (("H", h, H_CAP),) if dry else (("H", h, H_CAP), ("L", low, L_N),
                                           ("Z", z, Z_N))
    plans = {}
    for name, rows, cap in spec:
        pick, w, N = plan_stratum(rows, cap)
        for r in pick:
            r["stratum"], r["w"], r["year"] = name, w, year
        plans[name] = {"pick": pick, "w": w, "N": N, "dropped": N - len(pick)}
        _log(f"   [{year}] {name}: N={N} · مُشغَّلٌ {len(pick)} · "
             f"**مُسقَطٌ {N - len(pick)}** · وزنٌ {w:.3f}")

    todo = [r for p in plans.values() for r in p["pick"]]
    _log(f"📡 [{year}] القياس: {len(todo)} صفًّا بـ{THREADS} خيوطٍ متوازية")

    def _one(r):
        m = gate_measure(r["symbol"], r["prev_date"], r["date"])
        if m is not None:
            m["stratum"], m["w"] = r["stratum"], r["w"]
            m["gap_pct"], m["year"] = r["gap_pct"], year
        return m

    done = []
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        for i, m in enumerate(ex.map(_one, todo)):
            if m is not None:
                done.append(m)
            if (i + 1) % 2000 == 0:
                _log(f"   … [{year}] {i + 1}/{len(todo)} · ناجحٌ {len(done)}")

    cov = {}
    for name, p in plans.items():
        got = sum(1 for m in done if m["stratum"] == name)
        cov[name] = round(got / len(p["pick"]) * 100.0, 1) if p["pick"] else 0.0
        _log(f"🔒 [{year}] `V-P6` تغطيةُ {name}: {got}/{len(p['pick'])} "
             f"= {cov[name]}%")
    return done, plans, cov, len(allrows)


# ══════════════════ التشغيل ══════════════════
def main() -> int:                                               # noqa: PLR0911
    years = [x.strip() for x in
             str(os.environ.get("PMGATE_YEARS", "")).split(",") if x.strip()]
    frozen = [x.strip() for x in
              str(os.environ.get("PMGATE_FROZEN", "")).split(",") if x.strip()]
    dry = str(os.environ.get("PMGATE_DRY", "")).strip() == "1"
    if not years or len(years) != len(frozen):
        _log("⛔ يلزم PMGATE_YEARS و PMGATE_FROZEN بالعدد نفسِه وبالترتيب نفسِه")
        return 2
    if any(y not in ("2023", "2024", "2025", "2026") for y in years):
        _log("⛔ سنةٌ غيرُ مسموحة")
        return 2
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        _log("⛔ يلزم POLYGON_API_KEY — ولا يُخمَّن رقمٌ بدونه")
        return 5
    if not _selfcheck_readonly():
        _log("⛔ `V-P1` فحصُ «قراءةٌ فقط» سقط")
        return 3

    _log(f"📌 مجمَّدٌ بالاستيراد: GAP_MIN={GAP_MIN} · PM_MIN={PM_MIN} · "
         f"AH_MIN={AH_MIN} · السعر [{PRICE_LO}, {PRICE_HI}]")
    _log(f"📌 الميزانيّة (‏`V-P8`): H_CAP={H_CAP} · L_N={L_N} · Z_N={Z_N} · "
         f"NEFF_MIN={NEFF_MIN} · خيوط={THREADS} · بذرةُ المعاينة={SEED_TAG}")
    _log(f"📌 البوّابات: {list(GATES)} · الحاكمةُ **{GATE_MAIN}** "
         f"(‏04:30 نيويورك) · بوتستراب {BOOT} ببذرة {BOOT_SEED}")
    if dry:
        _log("🧪 **وضعُ الجدوى:** الطبقةُ H وحدَها · **صفرُ `Δ` وصفرُ نسبةِ "
             "إصابة** — الجوابُ الوحيد: هل يبلغ `n_eff` أرضيّتَه؟")
        _log("⚠️ **وتشغيلُ هذا الوضع يُطلع على حصّة `G-NO` في الطبقة H** ⇒ "
             "`Q3` تصير **مُطَّلَعًا عليها جزئيًّا**، ويُعلَن ذلك في النتيجة.")

    # ── ① القياس، سنةً سنةً، بالميزانية نفسِها (‏`V-P8`) ──
    done, meta = [], {}
    for y, fz in zip(years, frozen):
        hist, _sp, asof = S.load_frozen_dataset(fz)
        if not hist:
            _log(f"⛔ [{y}] تعذّر تحميل اللقطة {fz}")
            return 2
        if str(asof or "")[:4] != y:
            _log(f"⛔ [{y}] اللقطة as-of {asof} لا تطابق سنةَ القياس")
            return 4
        _log(f"🔒 [{y}] اللقطة {fz} as-of {asof} ✅ · رموزُها {len(hist)}")
        d, plans, cov, uni = _measure_year(hist, y, dry)
        if uni < 0:
            _log(f"⛔ [{y}] `V-P5` الطبقاتُ لا تستوعب الغربال")
            return 6
        wsum = sum(p["N"] for p in plans.values())
        if not dry and abs(wsum - uni) > max(1, uni * WSUM_TOL):
            _log(f"⛔ [{y}] `V-P5` الأوزانُ لا تُغلق الكون: {wsum} ≠ {uni}")
            return 6
        if any(v < COVER_MIN for v in cov.values()):
            _log(f"⛔ [{y}] طبقةٌ دون {COVER_MIN}% ⇒ **لا حكم**")
            return 7
        for m in d:
            done.append(m)
        meta[y] = {"asof": str(asof), "universe": uni,
                   "strata": {n: {"N": plans[n]["N"], "run": len(plans[n]["pick"]),
                                  "dropped": plans[n]["dropped"],
                                  "w": round(plans[n]["w"], 4), "cover": cov[n]}
                              for n in plans}}

    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for m in sorted(done, key=lambda x: (x["year"], x["symbol"], x["date"])):
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    # ── ② المجتمع: صفوفُ `E-AH` وحدَها · **بلا أيّ شرطٍ على مُخرَج البري** ──
    # 🔴 وهذا عمدٌ منصوصٌ في العقد: اشتراطُ حركةٍ في البري **يشترط النتيجة
    #    نفسَها** فيُقصي الذائبين — وهم بعينهم مَن تتكلّم عنهم الدعوى.
    pop = [m for m in done if classify_arm(m["ah_rise"]) == "E-AH"]
    w_pop = sum(m["w"] for m in pop)
    _log("")
    _log(f"👥 المجتمع `E-AH`: {len(pop)} صفًّا خامًا (موزونٌ {w_pop:,.0f})")

    out = {"years": years, "meta": meta, "dry": dry,
           "pop_raw": len(pop), "pop_weighted": round(w_pop, 1),
           "seed_tag": SEED_TAG, "boot_seed": BOOT_SEED, "gates": {}}

    for k in GATES:
        bk = {b: [m for m in pop if m["gates"][k]["bucket"] == b]
              for b in ("G-YES", "G-NO", "G-NONE")}
        if sum(len(v) for v in bk.values()) != len(pop):
            _log(f"⛔ [{k}] الدلاءُ الثلاثةُ لا تستوعب المجتمع")
            return 6
        share = {b: (round(sum(m["w"] for m in bk[b]) / w_pop * 100.0, 1)
                     if w_pop else 0.0) for b in bk}
        rates, vals = {}, {}
        for b in ("G-YES", "G-NO"):
            v = [m["gates"][k]["fwd"] * 100.0 for m in bk[b]
                 if m["gates"][k]["fwd"] is not None]
            w = [m["w"] for m in bk[b] if m["gates"][k]["fwd"] is not None]
            vals[b] = (v, w)
            rates[b] = w_rate(v, w, PM_MIN)
        cl = clusters_of(pop, k)
        d = delta_of(cl)
        bo = boot_delta(cl) if not dry else None
        floor_ok = min(rates["G-YES"]["n_eff"], rates["G-NO"]["n_eff"]) >= NEFF_MIN
        g = {"share": share,
             "n_raw": {b: len(bk[b]) for b in bk},
             "n_eff": {b: rates[b]["n_eff"] for b in ("G-YES", "G-NO")},
             "floor_ok": floor_ok}
        if not dry:
            g.update({"hit": {b: rates[b] for b in ("G-YES", "G-NO")},
                      "delta": None if d is None else round(d, 2), "boot": bo,
                      "p90": {b: w_pctile(*vals[b], 90)
                              for b in ("G-YES", "G-NO")}})
        out["gates"][k] = g

        tag = "🥇 الحاكمة" if k == GATE_MAIN else "· `C-TIME` وصفيّة"
        _log(f"⏱️ [{k}] {tag} — خام {g['n_raw']} · حصص% {share} · "
             f"n_eff {g['n_eff']} · `V-P4` {'✅' if floor_ok else '⛔'}")
        if not dry:
            _log(f"    إصابةُ `FWD` فوق {PM_MIN}%: "
                 f"`G-YES` {rates['G-YES']['pct']}% · "
                 f"`G-NO` {rates['G-NO']['pct']}% ⇒ **Δ={d:+.2f} نقطة**"
                 + (f" · بوتستراب [{bo['lo']}, {bo['hi']}]" if bo else ""))

    if not dry:
        # ③-ب الحساسيّةُ المُعلَنة: `G-NONE` تُضَمّ إلى `G-NO` بمرجعٍ بديل.
        alt = clusters_of([m for m in pop], GATE_MAIN, field="fwd_alt")
        _log("")
        _log("🔎 §③-ب حساسيّة (‏`G-NONE` مضمومةٌ بمرجع إغلاق الافتر) — "
             "تُطبَع ولا تحكم")
        # `C-MOM` — بوّابةُ زخمٍ صرفٍ عند اللحظة نفسِها (وصفيّة).
        gr = sorted((m["gates"][GATE_MAIN]["gate_ret"], m) for m in pop
                    if m["gates"][GATE_MAIN]["gate_ret"] is not None)
        half = len(gr) // 2
        mom = {"top": [m for _, m in gr[half:]], "bot": [m for _, m in gr[:half]]}
        mrate = {}
        for b, rows in mom.items():
            v = [m["gates"][GATE_MAIN]["fwd"] * 100.0 for m in rows
                 if m["gates"][GATE_MAIN]["fwd"] is not None]
            w = [m["w"] for m in rows if m["gates"][GATE_MAIN]["fwd"] is not None]
            mrate[b] = w_rate(v, w, PM_MIN)
        md = round(mrate["top"]["pct"] - mrate["bot"]["pct"], 2)
        out["C_MOM"] = {"top": mrate["top"], "bot": mrate["bot"], "delta": md}
        out["sens_alt"] = {"delta": (None if delta_of(alt) is None
                                     else round(delta_of(alt), 2)),
                           "boot": boot_delta(alt)}
        _log(f"    §③-ب `Δ_alt` = {out['sens_alt']['delta']}")
        _log(f"🔬 `C-MOM` زخمٌ صرفٌ عند {GATE_MAIN}: أعلى نصفٍ "
             f"{mrate['top']['pct']}% · أدنى نصفٍ {mrate['bot']['pct']}% "
             f"⇒ Δ={md:+.2f} — **وصفيٌّ بنصّ العقد**")

    main_ok = out["gates"][GATE_MAIN]["floor_ok"]
    _log("")
    _log(f"🔒 `V-P4` حدُّ الدقّة {NEFF_MIN}/دلوٍ عند الحاكمة: "
         f"{'✅' if main_ok else '⛔ لا تدخل PG1/PG2'}")
    out["no_verdict"] = not main_ok
    print("PMGATE_JSON " + json.dumps(out, ensure_ascii=False))
    return 0 if main_ok else 9


if __name__ == "__main__":
    sys.exit(main())
