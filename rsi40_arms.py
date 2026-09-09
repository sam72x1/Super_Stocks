#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📉🚪 T-RSI40 — بوّابةُ «RSI الآن» (‏`rsi40_prereg.md`).

**السؤال (§①):** دليلُ فيصل يقول «مستحيل يصعد إذا RSI بمناطق 40» في خمسة مواضع،
وبوّابتُنا الصلبة النافذة **‏71.12** (من ظرف الكاتالوج) ⇒ كم يُكلّف شدُّها إلى
نصّه؟
**الأذرع (§③):** `H0` الأساس (‏71.1186…) · `H40` **الحاكمة** · `H50` · `H30`
**وصفيّة** — أربعٌ ولا خامسة، وفي **تشغيلةٍ واحدةٍ بميزانيةٍ ثابتة**.
**وشاهدُ الضبط `HC`** (‏§⑧-أ) **ليس ذراعًا**: عمليةٌ لا تضبط شيئًا، ويُشترَط
`H0 ≡ HC` بت-بت (‏`V-R0`).

🔒 **صفر مسٍّ بالإنتاج:** الوالدُ لا يستورد `Super_stock`؛ كلُّ ذراعٍ في **عملية
منفصلة** تضبط `CONFIG` **بعد** الاستيراد، و`Super_stock.py` **لا تُمَسّ بحرف**.

🔴🔴 **ولماذا «بعد الاستيراد» شرطٌ لا أسلوب (‏§⑦):** تمريرُ عَلَمٍ بالبيئة **ميّتٌ
بنيويًّا** — `_apply_backtest_overrides` (`Super_stock.py:860`) ثم
`apply_faisal_only` (`:1035`) تدهسه بـ`cfg.update(ov)`، و**`RSI_NOW_HARD` من
مفاتيح الظرف بالضبط** (`catalog_envelope.CRITERIA: rsi_now → RSI_NOW_HARD`)
⇒ أربعُ أذرعٍ متطابقةٍ بت-بت تُقرأ «لا فرق» وهي **غيابُ قياس**. و`V-R5` يطبع
القيمةَ النافذة فيستحيل أن تمرّ ذراعٌ ميّتة.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import ceiling_arms as CA          # §⑧-د: الميزانيةُ واحدةٌ **بالبناء** لا بالدعوى

# ⛔ ولا ذراعَ تُضاف بعد رؤية الأرقام (‏§③). الترتيبُ ترتيبُ جدول §③ حرفيًّا.
ARMS: dict[str, float] = {"H0": 71.1186192371257, "H40": 40.0,
                          "H50": 50.0, "H30": 30.0}
BASE_ARM = "H0"
CTRL_ARM = "HC"                 # §⑧-أ — شاهدُ ضبطٍ لا ذراع (لا يضبط شيئًا)
# الأرخى ⟶ الأشدّ — **للرصد الرتيب وحده** (‏`R-N`)، لا للحكم.
STRICT_ORDER = ["H0", "H50", "H40", "H30"]
GATE_KEY = "M10_RSI_فات_القطار"
FLOOR_FILLED = 100              # §④ الأرضية: ‏≥100 إشارةٍ مُعبَّأة في `H0`
_LAST_GATE: list = []


def trades_path(arm: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"rsi40_trades_{arm}.json")


def gate_hits(text: str) -> int:
    """عدّادُ جدار `M10` من **سطر التجميع المرقَّم وحده**.

    نفسُ مِرساة `ceiling_arms.gate_hits` وعيبُها المُصلَح: سطرُ كلّ رمزٍ
    (`باكتيست·أسباب AAA (…): KEY=5`) **بلا ترقيمٍ وبلا مسافاتٍ حول `=`**،
    فمميِّزُ التجميع `N. ` قبل المفتاح — ولا مِرساةَ `^` لأن سطرَ الإنتاج
    مسبوقٌ بختمِ وقت."""
    return sum(int(m.group(1)) for m in
               re.finditer(r"\d+\.\s*" + re.escape(GATE_KEY) + r"\s*=\s*(\d+)",
                           text or ""))


def run_child(arm: str) -> int:
    import Super_stock as S                                      # noqa: PLC0415
    live = float(S.CONFIG["RSI_NOW_HARD"])
    if arm != CTRL_ARM:
        S.CONFIG["RSI_NOW_HARD"] = float(ARMS[arm])       # **بعد** الاستيراد
    # §⑦/`V-R5`: القيمةُ **النافذة** تُطبع — لا القيمةُ المطلوبة.
    print(f"ARM_EFFECTIVE {arm} RSI_NOW_HARD={S.CONFIG['RSI_NOW_HARD']!r} "
          f"live={live!r}")
    snap = CA.snapshot_id()
    print(f"SNAP {arm} as-of={snap['asof']} n_symbols={snap['n']}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "hard": float(S.CONFIG["RSI_NOW_HARD"]), "live": live, "snap": snap,
           "expl": float(S.CONFIG["EXPLOSION_PCT"]),
           # 🔒 اللينةُ **لا تُمَسّ** (§③) — تُطبع برهانًا لا زينة.
           "soft": float(S.CONFIG["RSI_MAX_NOW"])}
    out.update(CA.rates(trades))
    wf = [t for t in trades if t.get("exit_date")]
    with open(trades_path(arm), "w", encoding="utf-8") as fh:
        json.dump(wf, fh, ensure_ascii=False, default=str)
    out["wf"] = len(wf)
    print("RSI40_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def portfolio_named(wf_by_arm: dict, expl: float) -> dict:
    """🏦 الحسمُ المحفظيُّ على محورِ جلساتٍ موحَّد — **ومعه الأسماء** (‏`RS2`).

    نسخةُ `ceiling_arms.portfolio` نفسِها (نفسُ `extra_dates` ونفسُ `rank_live`)
    مضافًا إليها **مجموعتا الأسماء** `set50`/`set100` — لأن `RS2` يشترط أن
    **تُسمّى** الكلفة: مَن خرج بالضبط، لا كم خرج."""
    import replay10 as RP                                        # noqa: PLC0415
    dates = set()
    for rows in wf_by_arm.values():
        for t in rows:
            if t.get("date"):
                dates.add(str(t["date"]))
            if t.get("exit_date"):
                dates.add(str(t["exit_date"]))
    out = {}
    for arm, rows in wf_by_arm.items():
        if not rows:
            out[arm] = {"taken": None, "d50": None, "d100": None,
                        "set50": [], "set100": []}
            continue
        cands, idx, oc = RP.candidates_from_trades(rows, extra_dates=sorted(dates))
        res = RP.replay(cands, outcome_of=oc, ranker=RP.rank_live,
                        sessions=range(0, len(idx)))
        taken = res["taken"]
        rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]

        def _names(thr, _tk=taken):
            got = []
            for c in _tk:
                p = c.payload or {}
                if p.get("mg_outcome") in (None, "no_fill"):
                    continue
                try:
                    if float(p.get("mg_pre_stop") or 0.0) >= thr:
                        got.append(f"{c.symbol}@{str(p.get('date'))[:10]}")
                except (TypeError, ValueError):
                    pass
            return sorted(set(got))
        s50, s100 = _names(expl), _names(100.0)
        nf = sum(1 for c in taken
                 if (c.payload or {}).get("mg_outcome") == "no_fill"
                 or (c.payload or {}).get("outcome") == "no_fill")
        out[arm] = {"taken": len(taken), "rejected_cap": res["rejected_cap"],
                    "d50": len(s50), "d100": len(s100), "axis": len(idx),
                    "set50": s50, "set100": s100, "taken_no_fill": nf,
                    "per_trade": (round(sum(rs) / len(taken), 4) if taken else 0.0)}
    return out


_CMP_KEYS = ("signals", "decided", "wins", "losses", "no_fill", "win_rate",
             "wf", "taken", "d50", "d100", "per_trade", "axis", "rejected_cap")


def validity(res: dict, hits: dict) -> tuple[bool, list, int]:
    """§④ + §⑧ — تُقرأ **قبل** أيّ تفسير. تُرجع (سليم، أسطر، رمزُ الخروج).

    التمييزُ نفسُه المقيسُ في `T-CEILING`: **البنيويُّ يُسقِط، وغيرُ البنيويّ
    يُعلَن ولا يُسقِط** — و`ℹ️` علامةٌ ثالثةٌ لأن علامتين لثلاث حالاتٍ تكذب."""
    lines, ok = [], True
    order = list(ARMS)

    # `V-R5` — القيمةُ النافذة = اسميُّ الذراع (وهو الحارسُ الذي أسقط آليةَ العَلَم).
    bad5 = [f"{a}: نافذ={res[a]['hard']!r} اسميّ={ARMS[a]!r}"
            for a in order if abs(res[a]["hard"] - ARMS[a]) > 1e-9]
    c5 = not bad5
    lines.append(("V-R5", c5, "القيمُ **النافذة** = الاسميّة (لا دهسَ ظرف): "
                  + " · ".join(f"{a}={res[a]['hard']:.4f}" for a in order)
                  + (f" ⇒ خرق: {' · '.join(bad5)}" if bad5 else ""), 4))

    # `V-R2` — الأذرعُ تتفرّق **عدديًّا** (وإلّا `no-op` = غيابُ قياس).
    sig = {a: res[a]["signals"] for a in order}
    c2 = len(set(sig.values())) > 1 and hits[BASE_ARM] >= 0 and hits["H30"] > 0
    lines.append(("V-R2", c2, "الأذرعُ تتفرّق عدديًّا والجدارُ فعّال: "
                  + " · ".join(f"{a}: إشارات={sig[a]} جدار={hits[a]}"
                               for a in order), 4))

    # `V-R3` — هويّةُ اللقطة واحدةٌ في الخمس (برهانُ الميزانية الثابتة).
    snaps = {a: (res[a].get("snap") or {}) for a in res}
    ids = {(s.get("asof"), s.get("n")) for s in snaps.values()}
    c3 = len(ids) == 1 and all(s.get("n") for s in snaps.values())
    lines.append(("V-R3", c3, "هويّةُ اللقطة واحدةٌ في الخمس: "
                  + " · ".join(f"{a}={snaps[a].get('asof')}/{snaps[a].get('n')}"
                               for a in sorted(snaps)), 4))

    # `V-R0` — شاهدُ الضبط: `H0 ≡ HC` بت-بت (§⑧-أ).
    ctrl = res.get(CTRL_ARM) or {}
    diff0 = [f"{k}: H0={res[BASE_ARM].get(k)!r} HC={ctrl.get(k)!r}"
             for k in _CMP_KEYS if res[BASE_ARM].get(k) != ctrl.get(k)]
    c0 = bool(ctrl) and not diff0 and abs(ctrl.get("hard", -1)
                                          - ctrl.get("live", -2)) <= 1e-12
    lines.append(("V-R0", c0, "شاهدُ الضبط: `H0` ≡ الإنتاجُ حرفيًّا (بت-بت)"
                  + (f" ⇒ خرق: {' · '.join(diff0[:4])}" if diff0 else ""), 3))

    # `V-R4` — لا عَلَمَ أصلًا: `Super_stock.py` بت-بت مقابل `origin/main` (§⑦).
    c4, why4 = _untouched()
    lines.append(("V-R4", c4, "لا عَلَمَ في الإنتاج — " + why4, 3))

    # `V-R1` ⟶ **رصدٌ يُعلَن ولا يُسقط** (‏§⑧-ب): `i += fwd` يجعل الأذرعَ
    #  **غيرَ متداخلة** فصفٌّ يدخل في الأشدّ سلوكٌ صحيحٌ لا عطب.
    for a in order:
        if a == BASE_ARM:
            continue
        b0, ba = set(res[BASE_ARM].get("keys") or []), set(res[a].get("keys") or [])
        lines.append((f"R-N/{a}", None,
                      f"تداخلٌ مع `H0` (رصدٌ لا بوّابة): خرج {len(b0 - ba)} · "
                      f"**دخل {len(ba - b0)}**"
                      + (f" ⇒ أمثلة: {' · '.join(sorted(ba - b0)[:3])}"
                         if (ba - b0) else ""), 0))
    mono = all(sig[STRICT_ORDER[i]] >= sig[STRICT_ORDER[i + 1]]
               for i in range(len(STRICT_ORDER) - 1))
    lines.append(("R-M", None,
                  ("رتابةُ الإشارات ✔" if mono else "🔎 **الإشاراتُ غيرُ رتيبة**")
                  + " (رصدٌ لا بوّابة): "
                  + " ≥ ".join(f"{a}={sig[a]}" for a in STRICT_ORDER), 0))

    codes = [_x for _t, _o, _w, _x in lines if _o is not None and not _o]
    ok = not codes
    # **‏4 يغلب 3**: «الأداةُ لم تقِس» أشدُّ من «المرجعُ لم يُطابق» — والرصدُ (`_x=0`)
    # لا يدخل أصلًا لأن `_o is None` يُقصيه.
    rc = 4 if 4 in codes else (max(codes) if codes else 0)
    return ok, lines, rc


def _untouched() -> tuple[bool, str]:
    """`V-R4` — **بصمةُ الملفّ كاملًا** مقابل `origin/main`، لا قراءةُ نيّة.

    وتعذّرُ القراءة (بلا ريموت) **يُعلَن ولا يُدَّعى نجاحًا**."""
    import hashlib                                               # noqa: PLC0415
    try:
        p = subprocess.run(["git", "show", "origin/main:Super_stock.py"],
                           capture_output=True, timeout=60,
                           cwd=os.path.dirname(os.path.abspath(__file__)))
        if p.returncode != 0 or not p.stdout:
            return False, "⛔ تعذّرت قراءةُ `origin/main` — لا يُدَّعى نجاح."
        base = hashlib.sha256(p.stdout).hexdigest()[:12]
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "Super_stock.py"), "rb") as fh:
            cur = hashlib.sha256(fh.read()).hexdigest()[:12]
        return (base == cur), f"بصمة origin/main={base} · الحاليّ={cur}"
    except Exception as e:                                        # noqa: BLE001
        return False, f"⛔ {type(e).__name__} — لا يُدَّعى نجاح."


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 78}\n📉🚪 T-RSI40 — بوّابةُ «RSI الآن» · السنة {year}"
          f"\n{'=' * 78}", flush=True)
    _fz = CA.frozen_missing()
    if _fz:
        print(f"⛔ لقطةُ PIT مفقودة ({_fz}) — لا تشغيلَ على كون اليوم.")
        return 4
    res, hits = {}, {}
    for arm in list(ARMS) + [CTRL_ARM]:
        tag = (f"سقف {ARMS[arm]:.4f}" if arm in ARMS else "شاهدُ ضبطٍ (بلا ضبط)")
        print(f"\n──── {arm} ({tag}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env={**dict(os.environ), **CA.child_env()})
        blob = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob)
        for ln in blob.splitlines():
            if not ln.startswith("RSI40_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob.splitlines() if x.startswith("RSI40_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("RSI40_JSON:", 1)[1])

    wf_by_arm = {}
    for arm in res:
        try:
            with open(trades_path(arm), encoding="utf-8") as fh:
                wf_by_arm[arm] = json.load(fh)
        except Exception as e:                                    # noqa: BLE001
            print(f"⛔ تعذّر قراءة صفقات {arm}: {e} — لا حكم.")
            return 2
    # مفاتيحُ التداخل (‏`R-N`) — من الصفقات نفسِها لا من الحسم.
    for arm, rows in wf_by_arm.items():
        res[arm]["keys"] = sorted({f"{t.get('symbol')}@{str(t.get('date'))[:10]}"
                                   for t in rows})
    port = portfolio_named(wf_by_arm, float(res[BASE_ARM].get("expl") or 50.0))
    for arm in res:
        res[arm].update(port.get(arm) or {})

    ok, lines, rc = validity(res, hits)
    globals()["_LAST_GATE"] = lines
    print("\n🚧 بوّابةُ الصلاحية (‏§④/§⑧ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why, _x in lines:
        print(f"  {tag} {CA._mark(good)} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return rc or 3

    base = res[BASE_ARM]
    # §④ الأرضية — تُقرأ بعد الصلاحية وقبل أيّ تفسير.
    filled = base["signals"] - base["no_fill"]
    print(f"\n📐 الأرضية: مُعبَّأةُ `H0` = {filled} (الحدّ {FLOOR_FILLED})")
    if filled < FLOOR_FILLED:
        print(f"⛔ **«لا حكم» لسنة {year}** — العيّنةُ دون الأرضية المسجَّلة.")
        return 5

    print(f"\n📊 النتيجة (سعة {CA._live_capacity()} · rank_live · السنة {year}):")
    for arm in ARMS:
        r = res[arm]
        print(f"  {arm:<4}: سقف={r['hard']:.4f} · إشارات={r['signals']:<5} · "
              f"محسومة={r['decided']:<5} · غير_مُعبّأة={r['no_fill']:<4} · "
              f"دقة={r['win_rate']}% ({r['wins']}✅/{r['losses']}🛑) · "
              f"مأخوذة={r['taken']:<4} (بلا تعبئة={r.get('taken_no_fill')}) · "
              f"**d100={r['d100']:<3}** · d50={r['d50']:<3} · "
              f"R/صفقة={r['per_trade']} · جدار={hits[arm]}")
    print("\n🧭 الفرق عن الأساس `H0` (الحاكمُ **d100**):")
    for arm in ARMS:
        if arm == BASE_ARM:
            continue
        r = res[arm]
        d100 = r["d100"] - base["d100"]
        cut = (100.0 * r["signals"] / base["signals"] - 100.0
               if base["signals"] else None)
        print(f"  {arm:<4}: d100 {d100:+d} · d50 {r['d50'] - base['d50']:+d} · "
              + (f"الإشارات {cut:+.2f}%" if cut is not None else "الإشارات —")
              + f" · R/صفقة {r['per_trade'] - base['per_trade']:+.3f}")

    # §④ `RS2` — **الكلفةُ تُسمّى لا تُجمَّل**.
    print("\n💸 `RS2` — مَن خرج بالضبط عند ‏+100% (الكلفةُ بأسمائها):")
    b100 = set(base.get("set100") or [])
    for arm in ARMS:
        if arm == BASE_ARM:
            continue
        a100 = set(res[arm].get("set100") or [])
        gone, came = sorted(b100 - a100), sorted(a100 - b100)
        print(f"  {arm:<4}: خرج {len(gone)}"
              + (f" ⟵ {' · '.join(gone)}" if gone else "")
              + f" · دخل {len(came)}"
              + (f" ⟵ {' · '.join(came)}" if came else ""))

    print("\n⚠️ **حدودُ §① قائمةٌ وتُقرأ مع الأرقام:** انحيازُ بقاءٍ (كونُ ناسداك "
          "اليوم) · بلا افتر · `M13`/`M14` لا تعملان في الباكتيست · "
          "و«يُقبَل مرشّحًا» ≠ «يصل المالك» · والمُرتِّبُ عند الصدفة بسعة 15 ⇒ "
          "**فروقٌ صغيرةٌ داخل الضجيج** · و**المُسلَّمون ليسوا ربحًا**.")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    _rc = run_parent()
    print(f"\n{'=' * 78}\n🏁 رمزُ الخروج: {_rc}"
          + ("  ✅ البوّابةُ عبرت" if _rc == 0
             else "  ⛔ **بوّابةُ الصلاحية سقطت**" if _rc == 3
             else "  ⛔ لقطةٌ مفقودة/سنةٌ لا تطابق" if _rc == 4
             else "  ⛔ **«لا حكم»** — دون الأرضية" if _rc == 5
             else "  ⛔ ذراعٌ سقطت (rc≠0) — لا حكم")
          + f"\n{'=' * 78}")
    for _t, _o, _w, _x in (_LAST_GATE or []):
        print(f"  {_t} {CA._mark(_o)} {_w}")
    sys.exit(_rc)
