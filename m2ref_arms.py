#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧭 T-M2REF — ذراعا «مرجع الهبوط الواعي بالتقسيم» (علاج C1 · `m2ref_prereg.md`).

**السؤال المسجَّل (§①):** هل استبدال مرجع M2 (قمة 52أ المعدَّلة) بقمة ما بعد آخر
تقسيم عكسي يرفع المنفجرين المُسلَّمين لخانات السعة دون فتح ضجيج أو هدم العائد؟
**+ سؤال الآلية:** كم رمزًا يحجبه السقف زورًا بالمرجع المعدَّل؟ (فئة C1 تُقاس
لأول مرة على السوق الكامل — TDIC الحالة الحيّة الأولى.)

**الذراعان (§③ — ولا ثالثة):** `R0` الإنتاج كما هو · `R1` نفسه + `BT_SPLIT_REF_M2=1`.
🔒 **عزل تامّ:** كل ذراع في **عملية منفصلة** بيئتُها تُضبط قبل بدء بايثون —
درس بصمة الـno-op (`BT_CANDLE`): الضبط بعد الاستيراد يصل متأخّرًا والعلم يخمل.

⚠️ **الوالد لا يستورد `Super_stock` إطلاقًا** (قفل M2R6): كل استيرادات الإنتاج
داخل مسار الطفل حصرًا — فالوالد لا يلمس CONFIG ولا يفبرك حالة مشتركة بين الذراعين.

🔒 بحث/قياس — صفر مسّ إنتاج (العلم مطفأ افتراضيًّا). النتائج تُطبَع للسجلّ
(تنزيل الـartifacts محجوب بسياسة الشبكة).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# ── §⑤-V1: أرقام إعادة الإنتاج المسجَّلة (K-LIVE في T-RANKER2 ≡ S-LIVE في T-SLOT
#    بت-بت — d50 بسعة 10 ومُرتِّب rank_live على لقطات PIT الثلاث). R0 يجب أن
#    يعيدها **بت-بت** وإلا فلا حكم (بوّابة صلاحية حاكمة، نمط C10 في T-CAP).
VALID_D50 = {"2024": 22, "2025": 14, "2026": 6}

# ── §③: بيئة كل ذراع — **دالّة نقيّة** (قفل M2R1: عزل الذراعين).
#    `BT_ENVVALS` إلزامي (rank_live يقرأ in_band) · `BT_POTENTIAL` إلزامي
#    (d50 يقرأ mg_pre_stop) · `BT_REPLAY10` إلزامي (exit_date لتحرير الخانات).
ARM_EXTRA = {"R0": {}, "R1": {"BT_SPLIT_REF_M2": "1"}}


def child_env(arm: str) -> dict:
    """بيئة الطفل للذراع — R0 **بلا** `BT_SPLIT_REF_M2` وR1 به حصرًا."""
    env = {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
           "BT_ENVVALS": "1", "BT_POTENTIAL": "1"}
    env.update(ARM_EXTRA.get(arm, {}))
    return env


# ── §⑤-V2: سطر «العلم فعّال» — يلتقط النشط (N>0) والخامل (0) معًا.
FLAG_RE = re.compile(r"قرأ لقطة splits لـ(\d+) رمز")
M2CAP_RE = re.compile(r"M2_هبوط_فوق_97 = (\d+)")


def flag_syms(out: str):
    """كم رمزًا قرأ لقطة splits (None = السطر غائب كليًّا)."""
    m = FLAG_RE.search(out or "")
    return int(m.group(1)) if m else None


def m2cap_wall(out: str):
    """حجم جدار `M2_هبوط_فوق_97` من توزيع الرفض المطبوع (None = غائب)."""
    m = M2CAP_RE.search(out or "")
    return int(m.group(1)) if m else None


def v1_check(year: str, d50_r0):
    """بوّابة V1: هل أعاد R0 الرقم المسجَّل بت-بت؟ ('pass'/'fail'/'no_ref')."""
    ref = VALID_D50.get(str(year).strip())
    if ref is None:
        return "no_ref"
    return "pass" if d50_r0 == ref else "fail"


# ── §⑤-3: مسح الآلية — نقيّ، `psh_fn` محقونة للاختبار (بلا استيراد إنتاج).
#    تقسيم المحجوبين bالسقف: opened داخل النطاق · shifted_low تحت الأرضية
#    (نمط EHGO) · still_blocked فوق السقف بالمرجع الواعي · no_ref لا مرجع له
#    (يرتدّ للمعدَّل = يبقى محجوبًا — يُفصل عن still_blocked للشفافية).
def mech_scan(hist: dict, splits_map: dict, cap: float, floor: float,
              psh_fn) -> dict:
    out = {"universe": 0, "blocked_adj": 0, "opened": 0, "shifted_low": 0,
           "still_blocked": 0, "no_ref": 0, "opened_syms": []}
    for sym, df in (hist or {}).items():
        try:
            if df is None or not len(df):
                continue
            high = df["High"]
            price = float(df["Close"].iloc[-1])
            hi52 = float(high.tail(252).max())
            if not (price > 0 and hi52 > 0):
                continue
            out["universe"] += 1
            drop_adj = (1.0 - price / hi52) * 100.0
            if drop_adj <= cap:
                continue
            out["blocked_adj"] += 1
            psh = psh_fn(high.tail(252), (splits_map or {}).get(sym),
                         df.index[-1])
            if not psh or psh <= 0:
                out["no_ref"] += 1
                continue
            d2 = (1.0 - price / float(psh)) * 100.0
            if d2 > cap:
                out["still_blocked"] += 1
            elif d2 < floor:
                out["shifted_low"] += 1
            else:
                out["opened"] += 1
                if len(out["opened_syms"]) < 40:
                    out["opened_syms"].append(sym)
        except Exception:
            continue
    return out


def anchor_row(sym: str, hist: dict, splits_map: dict, cap: float,
               floor: float, psh_fn) -> dict:
    """§⑤-V3: مِرساة شفافية — الغياب يُعلَن لا يُتخطّى بصمت."""
    df = (hist or {}).get(sym)
    if df is None or not len(df):
        return {"symbol": sym, "present": False}
    try:
        high = df["High"]
        price = float(df["Close"].iloc[-1])
        hi52 = float(high.tail(252).max())
        sp = (splits_map or {}).get(sym)
        last_rs = None
        try:
            it = sp.items() if hasattr(sp, "items") else (sp or [])
            rs = [d for d, r in it if r and 0 < float(r) < 1.0]
            last_rs = str(max(rs))[:10] if rs else None
        except Exception:
            last_rs = None
        psh = psh_fn(high.tail(252), sp, df.index[-1])
        drop_adj = (1.0 - price / hi52) * 100.0 if hi52 > 0 else None
        drop_ref = ((1.0 - price / float(psh)) * 100.0
                    if psh and psh > 0 else None)
        verdict = None
        if drop_ref is not None:
            verdict = ("داخل النطاق" if floor <= drop_ref <= cap else
                       ("تحت الأرضية" if drop_ref < floor else "فوق السقف"))
        return {"symbol": sym, "present": True, "price": round(price, 2),
                "hi52_adj": round(hi52, 2),
                "drop_adj": round(drop_adj, 1) if drop_adj is not None else None,
                "last_rsplit": last_rs,
                "psh": round(float(psh), 2) if psh else None,
                "drop_ref": round(drop_ref, 1) if drop_ref is not None else None,
                "band_verdict": verdict}
    except Exception as e:                                       # noqa: BLE001
        return {"symbol": sym, "present": True, "error": type(e).__name__}


def _delivered(taken, thr: float) -> int:
    """المنفجرون المُسلَّمون (§⑤-1) — نفس تعريف T-RANKER2 حرفيًّا."""
    n = 0
    for c in taken:
        t = c.payload
        if t.get("mg_outcome") in (None, "no_fill"):
            continue
        try:
            if float(t.get("mg_pre_stop") or 0.0) >= thr:
                n += 1
        except (TypeError, ValueError):
            continue
    return n


def run_child(arm: str) -> int:
    """جسم الذراع — يعمل في عملية مستقلة بيئتُها مضبوطة قبل بدء بايثون."""
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    trades = S.run_backtest() or []
    with_fields = [t for t in trades if t.get("exit_date")]
    with_band = [t for t in with_fields
                 if isinstance(t.get("env_vals"), dict)
                 and "in_band" in t["env_vals"]]
    with_mg = [t for t in with_fields if t.get("mg_outcome") is not None]
    payload = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
               "n_trades": len(trades), "with_fields": len(with_fields),
               "with_band": len(with_band), "with_mg": len(with_mg)}
    if with_fields:
        cands, idx, outcome_of = RP.candidates_from_trades(with_fields)
        res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.rank_live,
                        sessions=range(0, len(idx)))
        taken = res["taken"]
        rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
        expl = float(S.CONFIG["EXPLOSION_PCT"])
        payload.update({
            "capacity": RP.CAPACITY, "sessions": len(idx),
            "taken": len(taken), "rejected_cap": res["rejected_cap"],
            "d50": _delivered(taken, expl), "d100": _delivered(taken, 100.0),
            "total_r": round(sum(rs), 4),
            "per_trade": round(sum(rs) / len(taken), 6) if taken else 0.0,
            "signals_syms": sorted({t["symbol"] for t in with_fields}),
        })
    if arm == "R1":
        # مسح الآلية + المِرساتان (§⑤-3/V3) — من نفس اللقطة المجمّدة
        fp = os.environ.get("BT_FROZEN_PATH", "").strip()
        if fp and os.path.exists(fp):
            hist, smap, _asof = S.load_frozen_dataset(fp)
            cap = float(S.CONFIG["MAX_DROP_PCT"])
            floor = float(S.CONFIG["MIN_DROP_FLOOR"])
            payload["mech"] = mech_scan(hist, smap, cap, floor,
                                        S._post_split_high)
            payload["anchors"] = [
                anchor_row(s, hist, smap, cap, floor, S._post_split_high)
                for s in ("TDIC", "NUWE")]
        else:
            payload["mech"] = None      # يُعلَن — لا يُتخطّى بصمت (V3)
            payload["anchors"] = None
    print("M2REF_JSON: " + json.dumps(payload, ensure_ascii=False))
    return 0


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 72}\n🧭 T-M2REF — مرجع الهبوط الواعي بالتقسيم · السنة {year}"
          f"\n{'=' * 72}")
    results, logs = {}, {}
    for arm in ("R0", "R1"):
        env = dict(os.environ)
        env.update(child_env(arm))
        print(f"\n──── تشغيل الذراع {arm} (عملية معزولة) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm],
                           capture_output=True, text=True, env=env)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        logs[arm] = out
        for ln in out.splitlines():
            if not ln.startswith("M2REF_JSON:"):
                print(f"  [{arm}] {ln}")
        tail = [ln for ln in out.splitlines() if ln.startswith("M2REF_JSON:")]
        if p.returncode != 0 or not tail:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) أو بلا JSON — لا حكم.")
            return 2
        results[arm] = json.loads(tail[-1].split("M2REF_JSON:", 1)[1])

    r0, r1 = results["R0"], results["R1"]

    # ── بوّابات الصلاحية (§⑤-4) — قبل قراءة أي مقارنة ──
    print("\n🚧 بوّابات الصلاحية:")
    v1 = v1_check(year, r0.get("d50"))
    print(f"  V1 إعادة إنتاج R0 بت-بت: d50={r0.get('d50')} مقابل "
          f"{VALID_D50.get(year, '—')} ⇒ "
          + {"pass": "✅", "fail": "⛔ سقطت — لا حكم",
             "no_ref": "⚠️ سنة بلا مرجع مسجَّل"}[v1])
    n_flag = flag_syms(logs["R1"])
    print(f"  V2 «العلم فعّال» في R1: قرأ لقطة splits لـ{n_flag} رمزًا ⇒ "
          + ("✅" if (n_flag or 0) > 0 else "⛔ خامل ⇒ no-op — لا حكم"))
    n_flag0 = flag_syms(logs["R0"])
    print(f"      (وR0 بلا العلم: سطر «العلم فعّال» {'غائب ✅' if n_flag0 is None else f'حاضر بقيمة {n_flag0} ⛔ عزل مكسور'})")
    anchors = r1.get("anchors")
    print("  V3 المِرساتان (شفافية — من اللقطة مباشرة):")
    if anchors:
        for a in anchors:
            if not a.get("present"):
                print(f"    {a['symbol']}: ⚠️ غائب من اللقطة (يُعلَن)")
            elif a.get("error"):
                print(f"    {a['symbol']}: ⚠️ خطأ {a['error']}")
            else:
                print(f"    {a['symbol']}: سعر ${a['price']} · قمة معدَّلة "
                      f"${a['hi52_adj']} (هبوط {a['drop_adj']}%) · آخر تقسيم "
                      f"عكسي {a['last_rsplit'] or '—'} · مرجع واعٍ "
                      f"{('$' + str(a['psh'])) if a['psh'] else '—'} ⇒ هبوط "
                      f"{a['drop_ref'] if a['drop_ref'] is not None else '—'}% "
                      f"({a['band_verdict'] or '—'})")
    else:
        print("    ⚠️ بلا لقطة ⇒ لا مِرساة (يُعلَن)")
    gates_ok = (v1 == "pass") and (n_flag or 0) > 0 and (n_flag0 is None)
    if not gates_ok:
        print("\n⛔ بوّابة صلاحية ساقطة ⇒ **لا تُفسَّر المقارنة** — تُصلَح "
              "الأداة وتُعاد التشغيلة.")

    # ── الآلية (§⑤-3) ──
    mech = r1.get("mech")
    if mech:
        print(f"\n🔬 الآلية (لقطة {year} عند آخر شمعة · {mech['universe']} رمزًا):")
        print(f"  محجوب بالسقف بالمرجع المعدَّل: {mech['blocked_adj']}")
        print(f"    ⤷ ينفتح داخل النطاق بالمرجع الواعي: {mech['opened']} "
              f"({', '.join(mech['opened_syms'][:12])}"
              f"{'…' if len(mech['opened_syms']) > 12 else ''})")
        print(f"    ⤷ ينتقل تحت الأرضية (نمط EHGO): {mech['shifted_low']}")
        print(f"    ⤷ يبقى فوق السقف بالمرجع الواعي: {mech['still_blocked']}")
        print(f"    ⤷ بلا مرجع واعٍ (يبقى على المعدَّل): {mech['no_ref']}")

    # ── المقارنة (§⑤-1/2) ──
    print(f"\n📊 الذراعان (سعة {r0.get('capacity')} · rank_live · بلا free_of):")
    for tag, r in (("R0", r0), ("R1", r1)):
        print(f"  {tag}: إشارات={r.get('with_fields')} · مأخوذة={r.get('taken')}"
              f" · d50={r.get('d50')} (d100={r.get('d100')}) · "
              f"R/صفقة={r.get('per_trade', 0):+.4f} · "
              f"إجمالي R={r.get('total_r', 0):+.1f} · "
              f"مرفوض بالسعة={r.get('rejected_cap')}")
    s0 = set(r0.get("signals_syms") or [])
    s1 = set(r1.get("signals_syms") or [])
    added, removed = sorted(s1 - s0), sorted(s0 - s1)
    print(f"  رموز جديدة في R1: {len(added)}"
          + (f" ({', '.join(added[:15])}{'…' if len(added) > 15 else ''})"
             if added else ""))
    print(f"  رموز فقدها R1: {len(removed)}"
          + (f" ({', '.join(removed[:15])}{'…' if len(removed) > 15 else ''})"
             if removed else ""))
    w0, w1 = m2cap_wall(logs["R0"]), m2cap_wall(logs["R1"])
    print(f"  جدار M2_هبوط_فوق_97: R0={w0 if w0 is not None else '—'} · "
          f"R1={w1 if w1 is not None else '—'}")

    d = (r1.get("d50") or 0) - (r0.get("d50") or 0)
    dr = (r1.get("per_trade") or 0.0) - (r0.get("per_trade") or 0.0)
    print("\n🧭 قراءات §⑥ لهذي السنة (الحكم يلزمه اللقطات الثلاث):")
    print(f"  d50: R1−R0 = {d:+d} · حارس العائد R1−R0 = {dr:+.4f}R/صفقة "
          f"(الحدّ −0.05)")
    print("\n⚠️ حدود الصدق كما سُجِّلت (§⑦): 2026 جزئية · أعداد صغيرة "
          "(ثبات الاتجاه لا p-values) · المرجع الواعي رهن اكتمال سجلّ تقسيمات "
          "اللقطة (V3 الكاشف) · «انفتاح» الرمز لا يعني ربحيّته — d50 هو الحكم.")
    return 0 if gates_ok else 3


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    sys.exit(run_parent())
