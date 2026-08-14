#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️📐 `T-PRESS-BT` — باكتيست آلية الضغط على ثلاث سنوات (العقد:
`press_prereg.md §⑫` · مدفوعٌ **قبل** أيّ رقم · أمرُ المالك 2026-08-14).

**السؤال:** لو دخلنا كلَّ قراءة ضغطٍ بخطة النموذج، كم نسبةُ الربح والتوقّع؟

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** القراءة `press_radar.press_read`
(نفسُها التي التقطت WETO والكتالوج 29/29 بذراع w=40) · الخطة
`rebound_arms.mirror_plan` (دفعاتُ الإنتاج من المرساة والوقفُ تحتها — المرساة
هنا **قاعُ الضغط** بنصّ النموذج «قسم دفعاتك وخلها قريبة من الدعم») · الحسمُ
`rebound_arms.resolve_episode` (التعبئة من الجلسة **التالية** · الوقف أولًا
في الشمعة نفسها · الهدف ‏1.5×) · وقيدُ السنة كما في `rebound_arms.walk_symbol`
(منعُ العدّ المزدوج بين اللقطات).

**الذراعان مثبّتان من العقد — لا ثالث بعد الأرقام:** `P-V0` (قراءة الإنتاج) ·
`P-VA1` (نافذة القمة 40ج — الفائزة بالالتقاط في §⑪-ج).

🔒 خارج مسار الفرز كليًّا (`Super_stock` لا يستورد هذا الملف — مقفول) · لا
`LOGIC_VERSION` · والحكم بمعيار «إيجابية» المسجَّل في §⑫ لا بعده."""
from __future__ import annotations

import os
import sys

ARMS = (("P-V0", {}), ("P-VA1", {"w": 40}))

# 🗜️🧠 §⑬ `T-PRESS-BT-2`: بوّاباتُ الأذرع العشر — مثبّتة من التسجيل حرفيًّا،
# لا تُضاف حاديةَ عشرةَ بعد الأرقام. السبعُ الأولى على خطة الدفعات عند القاع،
# والثلاثُ الأخيرة على دخول «اول صعود اذا رجع وثبت تدخل» المؤجَّل.
GATES = (
    ("BASE", lambda e: True),
    ("HOLD3", lambda e: e["hold"] >= 3),
    ("RUN50", lambda e: e["runup"] >= 50.0),
    ("TESTED", lambda e: e["tested"]),
    ("DEEP50", lambda e: e["drop"] >= 50.0),
    ("HOLD3+RUN50", lambda e: e["hold"] >= 3 and e["runup"] >= 50.0),
    ("HOLD3+TESTED", lambda e: e["hold"] >= 3 and e["tested"]),
    ("RECLAIM", lambda e: True),
    ("RECLAIM+HOLD3", lambda e: e["hold"] >= 3),
    ("RECLAIM+RUN50", lambda e: e["runup"] >= 50.0),
)


def _log(m):
    print(m, flush=True)


def walk_symbol_press(sym, df, year=None):
    """يمشي رمزًا واحدًا لكلّ ذراعٍ على حدة ويرجع [(ذراع، فهرس، حسم، وقف)].

    قيدُ السنة إلزاميّ (عُرف `rebound_arms`): القبول لجلسات سنة القياس فقط،
    والحسم يمتدّ بذيل البيانات. بعد كل حلقةٍ قفزة `WAIT` (دِدوب زمنيّ —
    يقارب دِدوب الرادار الحيّ ولا يطابقه، مُعلَنٌ في §⑫)."""
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    out = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return out
    n = len(df)
    for arm, kw in ARMS:
        i = RB.MIN_BARS
        while i < n:
            if year and yrs[i] != str(year):
                i += 1
                continue
            r = PR.press_read(df.iloc[:i + 1], **kw)
            if r:
                tr, st = RB.mirror_plan(float(r["press_low"]))
                oc = RB.resolve_episode(hi, lo, i, tr, st)
                out.append((arm, i, oc, st))
                i += RB.WAIT
                continue
            i += 1
    return out


def resolve_reclaim(hi, lo, cl, i, press_low, wait=None):
    """نقيّة (§⑬): دخول فيصل المؤجَّل — «فريم دقيقه **اول صعود اذا رجع وثبت
    تدخل**» (منشور WETO الحرفيّ) رقميًّا بثوابت قائمة مسمّاة لا رقمَ جديدًا:
    ① أوّل يومٍ بعد الإطلاق إغلاقُه فوق قاع الضغط بـ`METHOD_BOUNCE_MIN_PCT`
    (‏«الصعود غالبا من 10 > 15٪» IMG_0486) ② ثم أوّل يومٍ يلمس قاعُه نطاقَ
    الضغط (`SPLIT_SWEEP_MAX_PCT`) **ويغلق عند القاع أو فوقه** («رجع وثبت» —
    تعريفُ «حافظ» المثبت في `stability_result`) ⇒ الدخول بإغلاقه · الوقف
    وقفُ `mirror_plan(القاع)` نفسُه · الهدف `TARGET_X`× الدخول · الحسم من
    اليوم التالي والوقفُ أولًا. ترجع (حسم، دخول، وقف)."""
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    try:
        w = int(wait if wait is not None else RB.WAIT)
        pl = float(press_low)
        bounce = pl * (1.0 + float(S.CONFIG.get("METHOD_BOUNCE_MIN_PCT", 10.0)) / 100.0)
        band = pl * (1.0 + float(S.CONFIG.get("SPLIT_SWEEP_MAX_PCT", 13.0)) / 100.0)
        stop = RB.mirror_plan(pl)[1]
        n = len(cl)
        end = min(i + 1 + w, n)
        j = None
        for t in range(i + 1, end):
            if float(cl[t]) >= bounce:
                j = t
                break
        if j is None:
            return ("no_entry", None, None)
        k = None
        for t in range(j + 1, end):
            if float(lo[t]) <= band and float(cl[t]) >= pl:
                k = t
                break
        if k is None:
            return ("no_entry", None, None)
        entry = float(cl[k])
        if entry <= stop:
            return ("no_entry", None, None)
        tgt = entry * float(RB.TARGET_X)
        for t in range(k + 1, n):
            if float(lo[t]) <= stop:
                return ("loss", entry, stop)
            if float(hi[t]) >= tgt:
                return ("win", entry, stop)
        return ("open", entry, stop)
    except Exception:                                            # noqa: BLE001
        return ("no_entry", None, None)


def walk_symbol_grid(sym, df, year=None):
    """مِشيةُ §⑬: نفسُ حلقات `P-VA1` **بالبناء** (نفس القراءة والخطة والحسم
    والقفزة) + حقولُ البوّابات من القراءة نفسها + حسمُ RECLAIM لكل حلقة —
    فكلُّ ذراعٍ مرشِّحٌ فرعيٌّ من نفس القائمة (ميزانية مطابقة)."""
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    recs = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        cl = df["Close"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return recs
    n = len(df)
    i = RB.MIN_BARS
    while i < n:
        if year and yrs[i] != str(year):
            i += 1
            continue
        r = PR.press_read(df.iloc[:i + 1], w=40)
        if r:
            pl = float(r["press_low"])
            tr, st = RB.mirror_plan(pl)
            oc = RB.resolve_episode(hi, lo, i, tr, st)
            rc_oc, rc_en, rc_st = resolve_reclaim(hi, lo, cl, i, pl)
            recs.append({"i": i, "hold": int(r.get("hold_sessions") or 0),
                         "runup": float(r.get("runup_pct") or 0.0),
                         "tested": bool(r.get("tested_level")),
                         "drop": float(r.get("drop_pct") or 0.0),
                         "oc": oc, "stop": st,
                         "rc_oc": rc_oc, "rc_entry": rc_en, "rc_stop": rc_st})
            i += RB.WAIT
            continue
        i += 1
    return recs


def grid_report(recs, base_check, year) -> int:
    """§⑬: جدول الأذرع العشر. `base_check` = (حلقات، محسومة، بلغ) لذراع
    `P-VA1` من مسار §⑫ في **نفس التشغيلة** — تطابقُ BASE معها **بت-بت** فحصُ
    تكاملٍ حاكم (اختلافٌ ⇒ خروج 3 ولا يُفسَّر رقم)."""
    import rebound_arms as RB                                    # noqa: PLC0415
    rw = r_win_value()
    _log(f"\n🧠 شبكة §⑬ — سنة {year} (الأذرعُ العشر المسجّلة · حلقات الأساس "
         f"{len(recs)}):")
    rc = 0
    for name, gate in GATES:
        sub = [e for e in recs if gate(e)]
        if name.startswith("RECLAIM"):
            dec = [e for e in sub if e["rc_oc"] in ("win", "loss")]
            k = sum(1 for e in dec if e["rc_oc"] == "win")
            rs = []
            for e in dec:
                if e["rc_oc"] == "win":
                    en, stp = float(e["rc_entry"]), float(e["rc_stop"])
                    rs.append((en * (float(RB.TARGET_X) - 1.0)) / (en - stp))
                else:
                    rs.append(-1.0)
            if rs:
                m = sum(rs) / len(rs)
                var = sum((x - m) ** 2 for x in rs) / max(len(rs) - 1, 1)
                se = (var / len(rs)) ** 0.5
                ci = f"[{m - 1.96 * se:+.3f},{m + 1.96 * se:+.3f}]"
            else:
                m, ci = 0.0, "[—]"
            ne = sum(1 for e in sub if e["rc_oc"] == "no_entry")
            _log(f"  {name:<14} حلقات={len(sub):<6} محسومة={len(dec):<5} "
                 f"بلغ150={k:<4} نسبة={100.0 * k / len(dec) if dec else 0.0:6.2f}% "
                 f"E={m:+.3f}R {ci} · no_entry={ne}")
        else:
            dec = [e for e in sub if e["oc"] in ("win", "loss")]
            k = sum(1 for e in dec if e["oc"] == "win")
            w = RB.wilson(k, len(dec)) if dec else (0.0, 0.0)
            p = k / len(dec) if dec else 0.0
            _log(f"  {name:<14} حلقات={len(sub):<6} محسومة={len(dec):<5} "
                 f"بلغ150={k:<4} نسبة={100.0 * p:6.2f}% "
                 f"Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}] "
                 f"E={p * (rw + 1.0) - 1.0:+.3f}R "
                 f"[{w[0] * (rw + 1.0) - 1.0:+.3f},{w[1] * (rw + 1.0) - 1.0:+.3f}]")
        if name == "BASE":
            got = (len(sub), len(dec), k)
            if got != tuple(base_check):
                _log(f"⛔ فحص تكامل BASE سقط: {got} مقابل P-VA1 {base_check} "
                     f"⇒ خروج 3 ولا يُفسَّر رقمٌ من الشبكة.")
                rc = 3
            else:
                _log(f"    ✅ فحص تكامل: BASE ≡ P-VA1 بت-بت {got}")
    return rc


def r_win_value():
    """نقيّة: ربحُ الصفقة الرابحة بوحدة المخاطرة — ثابتٌ بنسب خطة الإنتاج
    (الدفعات صعودًا من المرساة بخطوة `ENTRY_STEP_PCT` والوقف
    `STOP_BELOW_LOW_PCT` الأعمق تحتها والهدف ‏1.5× المتوسط) ⇒
    `R_win = 0.5×متوسط ÷ (متوسط − وقف)` ‏≈5.1R بأرقام اليوم."""
    import Super_stock as S                                      # noqa: PLC0415
    n_tr = int(S.CONFIG.get("ENTRY_TRANCHES", 3))
    step = float(S.CONFIG.get("ENTRY_STEP_PCT", 3.0)) / 100.0
    s = S.CONFIG.get("STOP_BELOW_LOW_PCT", (5, 7))
    s_hi = float(s[1] if isinstance(s, (list, tuple)) else s)
    avg_f = sum(1.0 + step * k for k in range(n_tr)) / max(n_tr, 1)
    risk = avg_f - (1.0 - s_hi / 100.0)
    return (0.5 * avg_f) / risk if risk > 0 else 0.0


def report(episodes, n_syms, year) -> int:
    import rebound_arms as RB                                    # noqa: PLC0415
    rw = r_win_value()
    _log(f"\n📊 T-PRESS-BT سنة {year} — رموزٌ مفحوصة {n_syms} · R_win={rw:.2f}")
    rc = 0
    for arm, _kw in ARMS:
        eps = [e for e in episodes if e[0] == arm]
        if not eps:
            _log(f"⛔ {arm}: صفرُ حلقات — لا تشغيلةَ خضراءَ بصفر قياس (خروج 4).")
            rc = 4
            continue
        dec = [e for e in eps if e[2] in ("win", "loss")]
        k = sum(1 for e in dec if e[2] == "win")
        nf = sum(1 for e in eps if e[2] == "no_fill")
        op = sum(1 for e in eps if e[2] == "open")
        w = RB.wilson(k, len(dec))
        p = k / len(dec) if dec else 0.0
        e_mid = p * (rw + 1.0) - 1.0
        e_lo = w[0] * (rw + 1.0) - 1.0
        e_hi = w[1] * (rw + 1.0) - 1.0
        _log(f"  {arm:<7} حلقات={len(eps):<6} محسومة={len(dec):<5} بلغ150={k:<4} "
             f"نسبة الربح={100.0 * p:6.2f}% Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}] "
             f"no_fill={nf} · open={op}")
        wp = RB.wilson(k, len(eps))
        _log(f"    ⤷ التسليم لكل حلقة = {100.0 * k / len(eps):6.2f}% ({k} من {len(eps)}) "
             f"Wilson=[{100 * wp[0]:.2f},{100 * wp[1]:.2f}]")
        _log(f"    ⤷ التوقّع لكل صفقة محسومة = {e_mid:+.3f}R "
             f"[{e_lo:+.3f},{e_hi:+.3f}] (الربح {rw:.2f}R · الخسارة −1R)")
    _log("  🧭 الحكمُ النهائيّ بمعيار §⑫ على السنوات الثلاث مجتمعةً — لا حكم بسنة.")
    return rc


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🗜️📐 T-PRESS-BT — باكتيست آلية الضغط (§⑫) · سنة {year}"
         f"\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)} · الذراعان {[a for a, _ in ARMS]}")
    episodes, n_syms = [], 0
    yr = year if year and year != "?" else None
    if not yr:
        _log("⚠️ بلا سنةٍ محددة — المشي على كامل مدى اللقطة (يُعلَن).")
    import rebound_arms as RB                                    # noqa: PLC0415
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        episodes.extend(walk_symbol_press(sym, df, year=yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات حتى الآن {len(episodes)}")
    rc = report(episodes, n_syms, year)
    # 🧠 §⑬: شبكة الأذرع العشر — BASE يُطابَق بـP-VA1 من نفس التشغيلة (تكامل)
    va1 = [e for e in episodes if e[0] == "P-VA1"]
    va1_dec = [e for e in va1 if e[2] in ("win", "loss")]
    base_check = (len(va1), len(va1_dec),
                  sum(1 for e in va1_dec if e[2] == "win"))
    grecs = []
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        grecs.extend(walk_symbol_grid(sym, df, year=yr))
    rc2 = grid_report(grecs, base_check, year)
    return rc or rc2


if __name__ == "__main__":
    sys.exit(main())
