#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇 T-MINFLOOR — ذراعا «حدّ المالك المنصوص» (`minfloor_prereg.md`).

**السؤال (§①):** كم نسبةُ الدقة بحدّ المالك `P100` مقابل الكود السابق `P90`؟
**الذراعان (§②):** `A90` = `envelope_p90.json` · `A100` = `envelope_p100.json`
— يُختاران بـ`ENV_EDGES_FILE`، **ولا ذراعَ ثالثة**.

🔒 **عزلٌ تامّ:** كل ذراع في **عملية منفصلة** بيئتُها تُضبط قبل بدء بايثون
(درس بصمة الـno-op). **والوالد لا يستورد `Super_stock`** — الإنتاج داخل الطفل
حصرًا. بحث/قياس: صفر مسّ إنتاج (الفارز الحيّ يقرأ افتراضَه بلا هذا السائق).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ARMS = {"A90": "envelope_p90.json", "A100": "envelope_p100.json"}


def child_env(arm: str) -> dict:
    """بيئة الذراع — `ENV_EDGES_FILE` هو **الفرق الوحيد** بينهما."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
            "BT_ENVVALS": "1", "BT_POTENTIAL": "1",
            "ENV_EDGES_FILE": ARMS[arm]}


def rates(trades) -> dict:
    """نسبةُ الدقة بمقامها (§④-1) — **لا نسبةَ بلا مقام**."""
    w = sum(1 for t in trades if t.get("outcome") == "win")
    l = sum(1 for t in trades if t.get("outcome") == "loss")
    nf = sum(1 for t in trades if t.get("outcome") == "no_fill")
    dec = w + l
    return {"signals": len(trades), "decided": dec, "wins": w, "losses": l,
            "no_fill": nf,
            "win_rate": (round(100.0 * w / dec, 1) if dec else None)}


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import envelope_scan as EV                                   # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "edges_file": EV.EDGES_FILE,
           "edges_fp": EV.edges_fingerprint(EV.load_edges()),
           "min_price": S.CONFIG.get("MIN_PRICE"),
           "drop_floor": S.CONFIG.get("MIN_DROP_FLOOR")}
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
    print("MINFLOOR_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 72}\n🥇 T-MINFLOOR — حدُّ المالك P100 مقابل P90 · السنة {year}"
          f"\n{'=' * 72}")
    res = {}
    for arm in ("A90", "A100"):
        env = dict(os.environ)
        env.update(child_env(arm))
        print(f"\n──── الذراع {arm} ({ARMS[arm]}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env=env)
        blob = [x for x in ((p.stdout or "") + "\n" + (p.stderr or "")
                            ).splitlines() if x.startswith("MINFLOOR_JSON:")]
        for ln in ((p.stdout or "") + "\n" + (p.stderr or "")).splitlines():
            if not ln.startswith("MINFLOOR_JSON:"):
                print(f"  [{arm}] {ln}")
        if p.returncode != 0 or not blob:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(blob[-1].split("MINFLOOR_JSON:", 1)[1])

    a, b = res["A90"], res["A100"]
    print("\n🚧 بوّابةُ الصلاحية (كلُّ ذراعٍ قرأ ملفَّه فعلًا):")
    for t, r in (("A90", a), ("A100", b)):
        print(f"  {t}: {r['edges_file']} · بصمة {r['edges_fp']} · "
              f"سعر {r['min_price']:.2f} · أرضية هبوط {r['drop_floor']:.2f}")
    ok = (a["edges_file"] != b["edges_file"]
          and a["edges_fp"] != b["edges_fp"])
    print("  ⇒ " + ("✅ الذراعان مختلفتان فعلًا" if ok
                    else "⛔ نفسُ الملفّ/البصمة ⇒ no-op — لا تُفسَّر النتيجة"))
    if not ok:
        return 3

    print(f"\n📊 النتيجة (سعة {a.get('taken') is not None and 10} · rank_live):")
    for t, r in (("A90 ", a), ("A100", b)):
        wr = r["win_rate"]
        print(f"  {t}: إشارات={r['signals']} · محسومة={r['decided']} · "
              f"دقة={wr if wr is not None else '—'}% "
              f"({r['wins']}✅/{r['losses']}🛑) · مأخوذة={r.get('taken')} · "
              f"d50={r.get('d50')} (d100={r.get('d100')}) · "
              f"R/صفقة={r.get('per_trade')} · مرفوض بالسعة={r.get('rejected_cap')}")
    if a["win_rate"] is not None and b["win_rate"] is not None:
        print(f"\n🧭 الفرق (A100 − A90): الدقة {b['win_rate'] - a['win_rate']:+.1f} "
              f"نقطة · المنفجرون المُسلَّمون "
              f"{(b.get('d50') or 0) - (a.get('d50') or 0):+d} · الإشارات "
              f"×{(b['signals'] / a['signals']) if a['signals'] else 0:.1f}")
    print("\n⚠️ حدود الصدق (§⑦): انحياز بقاء · تشويه تقسيمات · بلا افتر · "
          "الكاتالوج اختيارٌ لاحقٌ للحدث · وP100 يلتقط كتالوجه بالبناء.")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    sys.exit(run_parent())
