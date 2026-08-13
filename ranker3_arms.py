#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚦🕵️ `T-RANKER3` — «الارتكاز الذي يجهّزه المضارب» مُرتِّبًا (`ranker3_prereg.md`).

**السؤال (§①):** `DFSC` رشّحه البوتُ بدرجة **85 (أعلى القائمة)** وانفجر **‏≥+106%**،
وترتيبُه يومَ 08-13 كان **‏#20 من 22**. فهل يرفع **السلوكُ القريب** (‏`act_score`)
و**تاريخُ الانفجارات** (`n_spikes`) المنفجرَ إلى الخانات الأولى؟

**خمسُ أذرعٍ ولا سادسة (§④):** `R-0` الأساس · `R-ACT` النشاطُ أوّلًا ·
**`R-ACT2` الحاكمة** (النطاقُ ثم النشاط) · `R-HIST` تاريخُ الانفجارات وحده ·
**`R-RAND` شاهدُ الضبط** (‏200 خلطة) — **بدونه لا معنى لأيّ تفوّق** (درسُ `T-RANKER2`).

**المقياسان (§⑤):** `d50` المُسلَّم داخل السعة · و**`d50@3`** داخل **أعلى ثلاث
خانات** — مسجَّلٌ لأنه سؤالُ المالك نصًّا («فيصل يدخل سهمين فقط») و**أشدُّ لا أسهل**.

🔒 **صفرُ مسٍّ بـ`rank_key`:** التسجيلُ افترض خطّافًا فيه، **والتنفيذُ أقلُّ تدخّلًا**
— `replay10` يقبل `ranker=` فتُبنى الأذرعُ مُرتِّباتٍ خارجيّة. المسُّ الوحيد
`backtest_symbol` خلف **علمٍ مطفأ** (`BT_ACTVALS`) بنفس سابقة `BT_ENVVALS`.
⚠️ **تجربةُ ترتيبٍ لا بوّابات:** `M1`-`M14` والدخولُ والوقفُ والأهداف **لا تُمَسّ**.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ARMS = ("R-0", "R-ACT", "R-ACT2", "R-HIST")
BASE_ARM = "R-0"
JUDGE_ARM = "R-ACT2"                  # §④: الحاكمة — لا تكسر عقد «الجاهز فقط»
RAND_SHUFFLES = 200                   # §④: شاهدُ الضبط
PUB_CAP = 15
# §⑦-V3 مِرساةُ التكامل: `R-0` = الإنتاج = ذراعُ `B120` في `base475_result.md §①`
# **عند سعة 15** (نفسُ مِرساة `T-STABILITY`).
INTEGRITY = {"2024": 25, "2025": 26, "2026": 15}
TOP_N = 3                             # §⑤: `d50@3` — «فيصل يدخل سهمين فقط»
_LAST_GATE: list = []


def _mark(v) -> str:
    """‏✅ عبَر · ⛔ يُسقط · **ℹ️ يُعلَن ولا يُسقط** — ثلاثُ حالاتٍ لا اثنتان
    (درسُ `T-STABILITY`: علامتان لثلاث حالاتٍ تكذب)."""
    return "ℹ️" if v is None else ("✅" if v else "⛔")


def child_env() -> dict:
    """أعلامُ الباكتيست — **بلا هذي لا يُحسَب `d50` ولا `R`** (‏`V4`؛ عيبٌ مقيس أسقط
    ثلاثَ تشغيلاتٍ لـ`T-CHASE` وطبع «‏+0» فقُرئ «لا فرق»). و`BT_ACTVALS` **هنا
    حصرًا** فالإنتاجُ لا يراه."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1", "BT_ENVVALS": "1",
            "BT_POTENTIAL": "1", "BT_ACTVALS": "1"}


def _d(taken, thr: float, top: int | None = None) -> int:
    """المنفجرون المُسلَّمون — `top` يقصر العدّ على **أعلى `top` خانات** (`d50@3`).
    ⚠️ `mg_outcome` غيرُ محسومٍ/`no_fill` **لا يُعدّ** (نفسُ عُرف `T-STABILITY`)."""
    n = 0
    for c in (taken[:top] if top else taken):
        p = c.payload
        if p.get("mg_outcome") in (None, "no_fill"):
            continue
        try:
            if float(p.get("mg_pre_stop") or 0.0) >= thr:
                n += 1
        except (TypeError, ValueError):
            pass
    return n


def _measure(trades, ranker) -> dict:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    wf = [t for t in trades if t.get("exit_date")]
    if not wf:
        return {}
    cands, idx, oc = RP.candidates_from_trades(wf)
    res = RP.replay(cands, outcome_of=oc, ranker=ranker,
                    sessions=range(0, len(idx)))
    taken = res["taken"]
    rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
    thr = float(S.CONFIG["EXPLOSION_PCT"])
    return {"taken": len(taken), "rejected_cap": res["rejected_cap"],
            "d50": _d(taken, thr), "d50_top": _d(taken, thr, TOP_N),
            "d100": _d(taken, 100.0),
            "per_trade": (round(sum(rs) / len(taken), 4) if taken else 0.0),
            "order": [c.payload.get("symbol") for c in taken[:12]]}


def run_child(arm: str) -> int:
    """يُشغّل الباكتيست **مرّةً واحدة** ثم يقيس كلَّ الأذرع على **نفس الصفقات**
    ⇒ الميزانيةُ ثابتةٌ **بالبناء** لا بالوعد (‏`V5` · درسُ `T-CLIFF`)."""
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR") or "?")
    out = {"year": year, "signals": len(trades)}
    # 🩺 تغطيةُ حقول النشاط — **كاشفُ الـno-op**: بلاها كلُّ الأذرع = الأساس
    wf = [t for t in trades if t.get("exit_date")]
    have = [t for t in wf if isinstance(t.get("act_vals"), dict)]
    out["wf"] = len(wf)
    out["act_cov"] = len(have)
    out["act_hist"] = {}
    for t in have:
        k = int((t["act_vals"] or {}).get("act_score") or 0)
        out["act_hist"][k] = out["act_hist"].get(k, 0) + 1
    out["spike_hist"] = {}
    for t in have:
        k = int((t["act_vals"] or {}).get("n_spikes") or 0)
        out["spike_hist"][min(k, 5)] = out["spike_hist"].get(min(k, 5), 0) + 1
    rankers = {"R-0": RP.rank_live, "R-ACT": RP.rank_act,
               "R-ACT2": RP.rank_act_band, "R-HIST": RP.rank_hist}
    out["arms"] = {a: _measure(trades, rankers[a]) for a in ARMS}
    # 🎲 شاهدُ الضبط — بذورٌ حتميّة (قابلةٌ لإعادة الإنتاج بالضبط)
    rnd = []
    for s in range(RAND_SHUFFLES):
        m = _measure(trades, RP.make_rank_random(s))
        if m:
            rnd.append((m["d50"], m["d50_top"]))
    out["rand"] = rnd
    print("R3_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def _pct(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    i = min(len(v) - 1, max(0, int(round(q / 100.0 * (len(v) - 1)))))
    return v[i]


def validity(res: dict) -> tuple[bool, list]:
    """§⑦ — تُقرأ **قبل** أيّ تفسير. `None` = يُعلَن ولا يُسقط."""
    lines, ok = [], True
    yrs = sorted(res)
    # V4 · المقياسُ الحاكم محسوبٌ لا غائب
    c4 = all(res[y]["arms"][a].get("d50") is not None for y in yrs for a in ARMS)
    lines.append(("V4", c4, "المقياسُ الحاكم محسوبٌ لا غائب: "
                  + " · ".join(f"{y}:{res[y]['arms'][BASE_ARM].get('d50')}"
                               for y in yrs)))
    # V2 · الأذرعُ متمايزةٌ فعلًا (كاشفُ الـno-op)
    diff = []
    for y in yrs:
        b = res[y]["arms"][BASE_ARM].get("order") or []
        for a in ARMS:
            if a == BASE_ARM:
                continue
            o = res[y]["arms"][a].get("order") or []
            if o != b:
                diff.append(f"{y}/{a}")
    c2 = len(diff) >= 2
    lines.append(("V2", c2, f"الأذرعُ تُنتج ترتيبًا مختلفًا فعلًا (لا `no-op`): "
                            f"{len(diff)} حالة — {diff[:6]}"))
    # V2ب · تغطيةُ حقول النشاط — بلاها كلُّ ذراعٍ = الأساس صامتًا
    cov = {y: (res[y]["act_cov"], res[y]["wf"]) for y in yrs}
    c2b = all(v[1] and v[0] / v[1] >= 0.90 for v in cov.values())
    lines.append(("V2ب", c2b, "تغطيةُ حقول النشاط ‏≥90% من المحسومة: "
                  + " · ".join(f"{y}:{v[0]}/{v[1]}" for y, v in cov.items())))
    # V2ج · المكوّناتُ حيّةٌ لا ثابتة (‏`A5` كان سيموت لو سبق `crit`)
    hist = {}
    for y in yrs:
        for k, v in (res[y].get("act_hist") or {}).items():
            hist[int(k)] = hist.get(int(k), 0) + v
    c2c = len([k for k, v in hist.items() if v]) >= 2
    lines.append(("V2ج", c2c, f"درجةُ النشاط **تتفاوت** (لا مكوّنَ ميّت): {hist}"))
    # V3 · فحصُ التكامل — يُعلَن ولا يُسقط
    bad = [f"{y}:{res[y]['arms'][BASE_ARM].get('d50')}≠{INTEGRITY[y]}"
           for y in yrs if y in INTEGRITY
           and res[y]["arms"][BASE_ARM].get("d50") != INTEGRITY[y]]
    lines.append(("V3", (None if bad else True),
                  ("فحصُ التكامل بت-بت (سعة 15) — `R-0` يعيد مِرساة `B120`"
                   if not bad else
                   f"🔴 **خرقٌ: {' · '.join(bad)} ⇒ مقامٌ جديد** — المقارنةُ "
                   "بالمنشور باطلةٌ والمقارنةُ بين الأذرع قائمة")))
    for _t, _o, _w in lines:
        if _o is not None:
            ok = ok and _o
    return ok, lines


def run_parent(years) -> int:
    print(f"\n{'=' * 78}\n🚦🕵️ T-RANKER3 — «هل يجهّزه المضارب؟» مُرتِّبًا · "
          f"السنوات {', '.join(years)}\n{'=' * 78}", flush=True)
    fz = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if fz and not os.path.exists(fz):
        print(f"⛔ **اللقطةُ المجمَّدة مفقودة**: {fz!r} ⇒ الباكتيست كان سيمضي على "
              "كون اليوم بمجتمعٍ آخر **بصمت** ⇒ توقّفٌ صريح (خروج 4).")
        return 4
    res = {}
    for y in years:
        print(f"\n──── السنة {y} ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child"],
                           capture_output=True, text=True,
                           env={**dict(os.environ), **child_env(),
                                "BACKTEST_YEAR": y})
        blob = (p.stdout or "") + "\n" + (p.stderr or "")
        rows = [x for x in blob.splitlines() if x.startswith("R3_JSON:")]
        for ln in blob.splitlines():
            if not ln.startswith("R3_JSON:"):
                print(f"  [{y}] {ln}")
        if p.returncode != 0 or not rows:
            print(f"⛔ السنة {y} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[y] = json.loads(rows[-1].split("R3_JSON:", 1)[1])

    ok, lines = validity(res)
    globals()["_LAST_GATE"] = lines
    print("\n🚧 بوّابةُ الصلاحية (‏§⑦ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why in lines:
        print(f"  {tag} {_mark(good)} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return 3

    yrs = sorted(res)
    print(f"\n📊 النتيجة (سعة {PUB_CAP} · `d50@{TOP_N}` = داخل أعلى {TOP_N} خانات):")
    for y in yrs:
        print(f"\n  ── {y} ── (إشارات {res[y]['signals']} · محسومة {res[y]['wf']} "
              f"· تغطيةُ النشاط {res[y]['act_cov']})")
        for a in ARMS:
            m = res[y]["arms"][a]
            mark = " 🥇" if a == JUDGE_ARM else ""
            print(f"    {a:7s} d50={m['d50']:<3} **d50@{TOP_N}={m['d50_top']:<2}** "
                  f"d100={m['d100']:<3} مأخوذة={m['taken']:<4} "
                  f"R/صفقة={m['per_trade']}{mark}")
        rd = res[y].get("rand") or []
        if rd:
            print(f"    {'R-RAND':7s} d50: وسيط={_pct([x[0] for x in rd], 50)} "
                  f"· p95={_pct([x[0] for x in rd], 95)} ‖ "
                  f"d50@{TOP_N}: وسيط={_pct([x[1] for x in rd], 50)} "
                  f"· p95={_pct([x[1] for x in rd], 95)}")

    print("\n🧭 الحرّاسُ الأربعة (‏§⑥ — بقراءتهم المسجَّلة قبل الأرقام):")
    j = {y: res[y]["arms"][JUDGE_ARM] for y in yrs}
    b = {y: res[y]["arms"][BASE_ARM] for y in yrs}
    dt = [j[y]["d50_top"] - b[y]["d50_top"] for y in yrs]
    ga = all(x >= 0 for x in dt)
    print(f"  (أ) {_mark(ga)} `d50@{TOP_N}` ‏≥ الأساس بلا انقلاب: "
          + " · ".join(f"{y}:{j[y]['d50_top']} مقابل {b[y]['d50_top']}"
                       for y in yrs) + f" ⇒ Δ={dt}")
    wins = 0
    for y in yrs:
        rd = [x[1] for x in (res[y].get("rand") or [])]
        p95 = _pct(rd, 95)
        if p95 is not None and j[y]["d50_top"] > p95:
            wins += 1
    gb = wins >= 2
    print(f"  (ب) {_mark(gb)} تتفوّق على العشوائيّ (فوق المئين 95) في "
          f"{wins} من {len(yrs)} — والحدُّ سنتان")
    nt = sum(j[y]["taken"] for y in yrs)
    nb = sum(b[y]["taken"] for y in yrs)
    rj = (sum(j[y]["per_trade"] * j[y]["taken"] for y in yrs) / nt) if nt else 0.0
    rb = (sum(b[y]["per_trade"] * b[y]["taken"] for y in yrs) / nb) if nb else 0.0
    gc = (rj - rb) >= -0.02
    print(f"  (ج) {_mark(gc)} `R`/صفقة مجمَّعًا: {rj:.4f} مقابل {rb:.4f} "
          f"⇒ Δ={rj - rb:+.4f} (الحدّ ‏≥ −0.02)")
    print("  (د) ℹ️ شاهدُ `DFSC` الحيّ — يُقاس بمِجَسٍّ منفصلٍ على اللقطة الحيّة")
    print(f"\n{'⚠️ ' * 3}\n**تجربةُ ترتيبٍ لا بوّابات (§⑨):** `M1`-`M14` والدخولُ "
          "والوقفُ والأهداف لم تُمَسّ · والعددُ صحيحٌ صغير ⇒ **‏±3 داخل الضجيج** · "
          "وأربعُ تجاربَ سابقةٍ في «سلوكٍ يميّز المنفجر» **فشلت** (`Q5`).")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(os.environ.get("BACKTEST_YEAR") or "?"))
    _ys = [y.strip() for y in
           (os.environ.get("R3_YEARS") or "2024,2025,2026").split(",") if y.strip()]
    _rc = run_parent(_ys)
    print(f"\n{'=' * 78}\n🏁 رمزُ الخروج: {_rc}"
          + ("  ✅ البوّابةُ عبرت" if _rc == 0
             else "  ⛔ **بوّابةُ الصلاحية سقطت**" if _rc == 3
             else "  ⛔ **لقطةٌ مفقودة**" if _rc == 4
             else "  ⛔ سنةٌ سقطت — لا حكم") + f"\n{'=' * 78}")
    for _t, _o, _w in (_LAST_GATE or []):
        print(f"  {_t} {_mark(_o)} {_w}")
    sys.exit(_rc)
