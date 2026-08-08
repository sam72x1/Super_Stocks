#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚧 T-CHASE — ذراعا «سقف منع الملاحقة» (`chase_prereg.md`).

**السؤال (§①):** هل إرجاعُ `RECENT_RISE_BLOCK_PCT` من 214.73 (‏P100 = أقصى نافذة)
إلى **‏35** (رقمُ المالك الموثّق، D11) **يُكلّف** شيئًا مقيسًا؟
**الذراعان (§②):** `G214` = 214.7286870417835 · `G35` = 35.0 — **ولا ثالثة**.

🔒 **صفر مسٍّ بالإنتاج:** الوالدُ لا يستورد `Super_stock`، وكلُّ ذراعٍ في **عملية
منفصلة** تضبط `CONFIG` **بعد** الاستيراد (‏`faisal_only_overrides` يُطبَّق وقتَه)
فتُطبَع القيمةُ النافذة ⇒ يستحيل الـ`no-op` الصامت. الفارزُ الحيّ لا يمرّ من هنا.

⚠️ **تجربةُ كلفةٍ لا حافّة** (‏§⑥): الاعتمادُ يلزمه **عدمُ تدهور** لا تحسّنًا.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ARMS = {"G214": 214.7286870417835, "G35": 35.0}
GATE_KEY = "M4_انفجر_فعلاً"          # عدّادُ البوّابة في توزيع رفض الإنتاج


def rates(trades) -> dict:
    """نسبةُ الدقة بمقامها (‏§⑤-3) — **لا نسبةَ بلا مقام**."""
    w = sum(1 for t in trades if t.get("outcome") == "win")
    ls = sum(1 for t in trades if t.get("outcome") == "loss")
    nf = sum(1 for t in trades if t.get("outcome") == "no_fill")
    dec = w + ls
    return {"signals": len(trades), "decided": dec, "wins": w, "losses": ls,
            "no_fill": nf,
            "win_rate": (round(100.0 * w / dec, 1) if dec else None)}


def gate_hits(text: str) -> int:
    """يقرأ عدّادَ البوّابة من **توزيع رفض الإنتاج نفسِه** (‏§④-2).

    السطرُ من `reject_distribution_lines`: «‏   3. M4_انفجر_فعلاً = 128 (4.1%)».
    غيابُ المفتاح ⇒ 0 (‏= لم تُشتعل ولا مرّة، وهو بعينه ما نتوقّعه في G214)."""
    n = 0
    for m in re.finditer(re.escape(GATE_KEY) + r"[^=\n]*=\s*(\d+)", text or ""):
        n += int(m.group(1))
    return n


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    # 🔴 **بعد** الاستيراد حصرًا: `faisal_only_overrides` يُطبَّق وقت الاستيراد،
    #    فالضبطُ هنا هو النافذُ فعلًا — ويُطبَع إثباتًا (‏§④-1).
    S.CONFIG["RECENT_RISE_BLOCK_PCT"] = float(ARMS[arm])
    print(f"ARM_EFFECTIVE {arm} RECENT_RISE_BLOCK_PCT="
          f"{S.CONFIG['RECENT_RISE_BLOCK_PCT']!r}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "chase_pct": S.CONFIG["RECENT_RISE_BLOCK_PCT"]}
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
    print("CHASE_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 74}\n🚧 T-CHASE — سقفُ منع الملاحقة: 35 مقابل 214.73 · "
          f"السنة {year}\n{'=' * 74}", flush=True)
    res, hits, eff = {}, {}, {}
    for arm in ("G214", "G35"):
        print(f"\n──── الذراع {arm} (‏{ARMS[arm]}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env=dict(os.environ))
        blob_all = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob_all)
        for ln in blob_all.splitlines():
            if ln.startswith("ARM_EFFECTIVE"):
                eff[arm] = ln.split("=", 1)[1].strip()
            if not ln.startswith("CHASE_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob_all.splitlines() if x.startswith("CHASE_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("CHASE_JSON:", 1)[1])

    a, b = res["G214"], res["G35"]
    print("\n🚧 بوّابةُ الصلاحية (‏§④ — تُقرأ قبل أيّ تفسير):")
    print(f"  ① القيمةُ النافذة: G214={eff.get('G214')} · G35={eff.get('G35')}")
    print(f"  ② عدّادُ «{GATE_KEY}»: G214={hits['G214']} · G35={hits['G35']}")
    print(f"  ③ الإشارات: G214={a['signals']} · G35={b['signals']}")
    ok1 = abs(a["chase_pct"] - b["chase_pct"]) > 1e-9
    ok2 = hits["G35"] > 0
    ok3 = b["signals"] < a["signals"]
    for tag, ok, why in (("①", ok1, "القيمتان مختلفتان فعلًا"),
                         ("②", ok2, "البوّابةُ اشتعلت في G35"),
                         ("③", ok3, "الإشاراتُ نقصت")):
        print(f"     {tag} {'✅' if ok else '⛔'} {why}")
    if not (ok1 and ok2 and ok3):
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ التجربة no-op — لا تُفسَّر نتيجتها.**")
        return 3

    print("\n📊 النتيجة (سعة 10 · rank_live):")
    for t, r in (("G214", a), ("G35 ", b)):
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
                " (مقامُ G214 صفر — لا نسبة)")]
    parts.append(f"R/صفقة {rtb - rta:+.3f}")
    if a["win_rate"] is not None and b["win_rate"] is not None:
        parts.append(f"الدقة {b['win_rate'] - a['win_rate']:+.1f} نقطة")
    if a["signals"]:
        parts.append(f"الإشارات {100.0 * b['signals'] / a['signals'] - 100:+.1f}%")
    print("\n🧭 الفرق (G35 − G214): " + " · ".join(parts))
    print(f"  💰 كلفةُ الحماية المقيسة: {hits['G35']} رفضةَ «{GATE_KEY}» في G35 "
          f"مقابل {hits['G214']} في G214.")
    print("\n⚠️ **تجربةُ كلفةٍ لا حافّة (‏§⑥):** «لم يُكلّف» ليست «ربّح» · والحكمُ "
          "المجمَّع يلزمه السنواتُ الثلاث · وحدودُ §⑧ قائمة (انحياز بقاء · تشويه "
          "تقسيمات · بلا افتر · والباكتيستُ أعمى عن ثمن الملاحقة بنيويًّا).")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    sys.exit(run_parent())
