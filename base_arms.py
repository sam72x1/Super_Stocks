#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧱 T-BASE — ذراعا «سقف عرض القاعدة M4» (`base_prereg.md`).

**السؤال (§①):** هل إرجاعُ `BASE_RANGE_MAX_PCT` من 23,684.63 (‏P100)
إلى **‏40** (حكمُ `M4-LADDER` الموثّق) **يُكلّف** شيئًا مقيسًا؟
**الذراعان (§③):** `B23685` = 23684.63 · `B40` = 40.0 — **ولا ثالثة**.

🔒 **صفر مسٍّ بالإنتاج:** الوالدُ لا يستورد `Super_stock`، وكلُّ ذراعٍ في **عملية
منفصلة** تضبط `CONFIG` **بعد** الاستيراد (‏`faisal_only_overrides` يُطبَّق وقتَه)
فتُطبَع القيمةُ النافذة ⇒ يستحيل الـ`no-op` الصامت. الفارزُ الحيّ لا يمرّ من هنا.

⚠️ **تجربةُ كلفةٍ لا حافّة** (‏§⑦): الاعتمادُ يلزمه **عدمُ تدهور** لا تحسّنًا.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ARMS = {"B23685": 23684.631623040408, "B40": 40.0}
GATE_KEY = "M4_base_واسعة"          # عدّادُ البوّابة في توزيع رفض الإنتاج


def child_env(arm: str) -> dict:
    """🔴 **بيئةُ الطفل — عيبٌ مقيس أُصلح (2026-08-08).**

    كتبتُ السائقَ أوّلًا **بلا** هذي الدالّة (تمريرُ `os.environ` كما هو) فلم
    تُرفَع أعلامُ الباكتيست ⇒ `exit_date` لا يُلحَق و`mg_pre_stop` لا يُحسَب ⇒
    `wf` فارغة ⇒ **`d50`/`R`/`taken` كلُّها `None`** — والمقياسُ الحاكم غائب،
    والتشغيلةُ **خضراء**، وسطرُ الفرق طبع «‏d50 +0» فيُقرأ «لا فرق» وحقيقتُه
    «**لم يُقَس**». وهي بصمةُ الـ`no-op` بصيغةٍ جديدة: لا علمٌ ميّت بل **مقياسٌ
    غائبٌ يُطبَع صفرًا**. ولذلك أُضيفت البوّابة ④ أدناه.

    ⚠️ **ولا يُبدَّل أيُّ علمٍ هنا بين الذراعين** — الفرقُ الوحيد سقفُ البوّابة."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
            "BT_ENVVALS": "1", "BT_POTENTIAL": "1"}


def rates(trades) -> dict:
    """نسبةُ الدقة بمقامها (‏§⑥-3) — **لا نسبةَ بلا مقام**."""
    w = sum(1 for t in trades if t.get("outcome") == "win")
    ls = sum(1 for t in trades if t.get("outcome") == "loss")
    nf = sum(1 for t in trades if t.get("outcome") == "no_fill")
    dec = w + ls
    return {"signals": len(trades), "decided": dec, "wins": w, "losses": ls,
            "no_fill": nf,
            "win_rate": (round(100.0 * w / dec, 1) if dec else None)}


def gate_hits(text: str) -> int:
    """يقرأ عدّادَ البوّابة من **توزيع رفض الإنتاج نفسِه** (‏§⑤-2).

    السطرُ من `reject_distribution_lines`: «‏   1. M4_base_واسعة = 9017 (31%)».
    غيابُ المفتاح ⇒ 0 (‏= لم تُشتعل ولا مرّة، وهو بعينه ما نتوقّعه في B23685)."""
    n = 0
    for m in re.finditer(re.escape(GATE_KEY) + r"[^=\n]*=\s*(\d+)", text or ""):
        n += int(m.group(1))
    return n


def probe(syms: str = None) -> int:
    """🔬 مِجَسٌّ تشخيصيّ **خارج الحكم** (‏`base_prereg.md` §⑧ — مُعلَنٌ سلفًا).

    يجيب سؤال المالك الحرفيّ «هل كان 40 سيرفض LGHL؟»: يجلب الرمزَ حيًّا، يطبع
    `base_range` **المقيس** من نافذة الإنتاج نفسِها، ويشغّل `_diagnose_symbol`
    **الإنتاجيّة** بكلا السقفين. **لا يدخل أيَّ مقياسٍ من §⑥.**"""
    import Super_stock as S                                      # noqa: PLC0415
    names = [x.strip().upper() for x in
             (syms or os.environ.get("BASE_PROBE_SYMS") or "LGHL").split(",")
             if x.strip()]
    if not names:
        return 0
    print(f"\n{'─' * 74}\n🔬 مِجَسٌّ تشخيصيّ (خارج الحكم · §⑧): {' · '.join(names)}"
          f"\n{'─' * 74}", flush=True)
    try:
        hist = S.download_history(names)
    except Exception as e:                                       # noqa: BLE001
        print(f"  ⛔ تعذّر التحميل ({e}) — المِجَسّ تشخيصٌ فلا يُسقط التجربة.")
        return 0
    bw = int(S.CONFIG["BASE_WINDOW"])
    for sym in names:
        df = hist.get(sym)
        if df is None or len(df) < bw:
            print(f"  ⚪️ {sym}: لا بيانات كافية ({0 if df is None else len(df)}).")
            continue
        hi = float(df["High"].tail(bw).max())
        lo = float(df["Low"].tail(bw).min())
        rng = (hi / lo - 1.0) * 100.0 if lo > 0 else float("nan")
        print(f"  📏 {sym}: نافذة {bw} جلسة — أعلى ${hi:.4f} · أدنى ${lo:.4f} ⇒ "
              f"**عرض القاعدة {rng:.1f}%** (آخر شمعة {df.index[-1].date()})")
        for arm, cap in ARMS.items():
            verdict = "❌ يُرفَض M4_base_واسعة" if rng > cap else "✅ يمرّ M4"
            print(f"     {arm} (سقف {cap:,.2f}): {verdict}")
        for arm, cap in ARMS.items():
            print(f"  ── تشخيصُ الإنتاج بسقف {arm} ──")
            _old = S.CONFIG["BASE_RANGE_MAX_PCT"]
            try:
                S.CONFIG["BASE_RANGE_MAX_PCT"] = float(cap)
                S._diagnose_symbol(sym, df)
            except Exception as e:                               # noqa: BLE001
                print(f"     ⚠️ تعذّر التشخيص: {e}")
            finally:
                S.CONFIG["BASE_RANGE_MAX_PCT"] = _old
    return 0


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    # 🔴 **بعد** الاستيراد حصرًا: `faisal_only_overrides` يُطبَّق وقت الاستيراد،
    #    فالضبطُ هنا هو النافذُ فعلًا — ويُطبَع إثباتًا (‏§⑤-1).
    S.CONFIG["BASE_RANGE_MAX_PCT"] = float(ARMS[arm])
    print(f"ARM_EFFECTIVE {arm} BASE_RANGE_MAX_PCT="
          f"{S.CONFIG['BASE_RANGE_MAX_PCT']!r}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "base_pct": S.CONFIG["BASE_RANGE_MAX_PCT"]}
    out.update(rates(trades))
    wf = [t for t in trades if t.get("exit_date")]
    if wf:
        cands, idx, oc = RP.candidates_from_trades(wf)
        res = RP.replay(cands, outcome_of=oc, ranker=RP.rank_live,
                        sessions=range(0, len(idx)))
        taken = res["taken"]
        rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
        expl = float(S.CONFIG["EXPLOSION_PCT"])

        def _d(thr):
            n = 0
            for c in taken:
                p = c.payload
                if p.get("mg_outcome") in (None, "no_fill"):
                    continue
                try:
                    if float(p.get("mg_pre_stop") or 0.0) >= thr:
                        n += 1
                except (TypeError, ValueError):
                    pass
            return n
        out.update({"taken": len(taken), "rejected_cap": res["rejected_cap"],
                    "d50": _d(expl), "d100": _d(100.0),
                    "per_trade": (round(sum(rs) / len(taken), 4)
                                  if taken else 0.0)})
    print("BASE_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 74}\n🧱 T-BASE — سقفُ عرض القاعدة: 40 مقابل 23,684.63 · "
          f"السنة {year}\n{'=' * 74}", flush=True)
    res, hits, eff = {}, {}, {}
    for arm in ("B23685", "B40"):
        print(f"\n──── الذراع {arm} (‏{ARMS[arm]}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env={**dict(os.environ), **child_env(arm)})
        blob_all = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob_all)
        for ln in blob_all.splitlines():
            if ln.startswith("ARM_EFFECTIVE"):
                eff[arm] = ln.split("=", 1)[1].strip()
            if not ln.startswith("BASE_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob_all.splitlines() if x.startswith("BASE_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("BASE_JSON:", 1)[1])

    armA, armB = "B23685", "B40"
    a, b = res["B23685"], res["B40"]
    print("\n🚧 بوّابةُ الصلاحية (‏§⑤ — تُقرأ قبل أيّ تفسير):")
    print(f"  ① القيمةُ النافذة: B23685={eff.get('B23685')} · B40={eff.get('B40')}")
    print(f"  ② عدّادُ «{GATE_KEY}»: B23685={hits['B23685']} · B40={hits['B40']}")
    print(f"  ④ المقياسُ الحاكم: {armA}.d50={a.get('d50')} · "
          f"{armB}.d50={b.get('d50')} (‏None = لم يُقَس)")
    print(f"  ③ الإشارات: B23685={a['signals']} · B40={b['signals']}")
    ok1 = abs(a["base_pct"] - b["base_pct"]) > 1e-9
    ok2 = hits["B40"] > 0
    ok3 = b["signals"] < a["signals"]
    # ④ 🔴 **المقياسُ الحاكم حاضرٌ فعلًا** (أُضيفت بعد تشغيلةٍ باطلة): غيابُ
    #    `taken`/`d50` يعني أن مسار `replay10` لم يعمل ⇒ لا يجوز طبعُ فرقٍ منها.
    ok4 = all(r.get("taken") is not None and r.get("d50") is not None
              for r in (a, b))
    for tag, ok, why in (("①", ok1, "القيمتان مختلفتان فعلًا"),
                         ("②", ok2, "البوّابةُ اشتعلت في B40"),
                         ("③", ok3, "الإشاراتُ نقصت"),
                         ("④", ok4, "المقياسُ الحاكم (‏d50/مأخوذة) محسوبٌ لا غائب")):
        print(f"     {tag} {'✅' if ok else '⛔'} {why}")
    if not (ok1 and ok2 and ok3 and ok4):
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ التجربة no-op — لا تُفسَّر نتيجتها.**")
        return 3

    print("\n📊 النتيجة (سعة 10 · rank_live):")
    for t, r in (("B23685", a), ("B40   ", b)):
        wr = r["win_rate"]
        print(f"  {t}: إشارات={r['signals']} · محسومة={r['decided']} · "
              f"دقة={wr if wr is not None else '—'}% "
              f"({r['wins']}✅/{r['losses']}🛑) · مأخوذة={r.get('taken')} · "
              f"d50={r.get('d50')} (d100={r.get('d100')}) · "
              f"R/صفقة={r.get('per_trade')} · مرفوض بالسعة={r.get('rejected_cap')}")
    # ⚠️ **الأجزاءُ تُبنى قائمةً لا سلسلةَ `+` بشرطٍ في ذيلها**: كتبتُها أوّلًا
    #    `… + X if a["signals"] else ""` فكان الشرطُ يحكم **السلسلةَ كلَّها** لا
    #    الطرفَ الأخير — يعمل بالمصادفة ويكسر صامتًا عند أوّل تعديل. كلُّ طرفٍ
    #    الآن محروسٌ بمقامه على حدة (ولا قسمةَ على صفر).
    d50a, d50b = (a.get("d50") or 0), (b.get("d50") or 0)
    rta, rtb = (a.get("per_trade") or 0.0), (b.get("per_trade") or 0.0)
    parts = [f"d50 {d50b - d50a:+d}"
             + (f" ({100.0 * (d50b - d50a) / d50a:+.1f}%)" if d50a else
                " (مقامُ B23685 صفر — لا نسبة)")]
    parts.append(f"R/صفقة {rtb - rta:+.3f}")
    if a["win_rate"] is not None and b["win_rate"] is not None:
        parts.append(f"الدقة {b['win_rate'] - a['win_rate']:+.1f} نقطة")
    if a["signals"]:
        parts.append(f"الإشارات {100.0 * b['signals'] / a['signals'] - 100:+.1f}%")
    print("\n🧭 الفرق (B40 − B23685): " + " · ".join(parts))
    print(f"  💰 كلفةُ الحماية المقيسة: {hits['B40']} رفضةَ «{GATE_KEY}» في B40 "
          f"مقابل {hits['B23685']} في B23685.")
    print("\n⚠️ **تجربةُ كلفةٍ لا حافّة (‏§⑦):** «لم يُكلّف» ليست «ربّح» · والحكمُ "
          "المجمَّع يلزمه السنواتُ الثلاث · وحدودُ §⑩ قائمة (انحياز بقاء · تشويه "
          "تقسيمات · بلا افتر · والباكتيستُ أعمى عن ثمن الملاحقة والوسم الكاذب).")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    if "--probe" in sys.argv:            # 🔬 المِجَسّ وحده (تشخيصٌ خارج الحكم)
        sys.exit(probe())
    _rc = run_parent()
    try:                                 # المِجَسّ **بعد** الحكم فلا يؤثّر عليه
        probe()
    except Exception as _e:                                      # noqa: BLE001
        print(f"⚠️ المِجَسّ التشخيصيّ: {_e} — ولا يمسّ الحكم.")
    sys.exit(_rc)
