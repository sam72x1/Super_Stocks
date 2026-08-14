#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🟣 `T-PURPLE` — مرساةُ الطلبات البنفسجية لمؤهَّلي الفارز الرئيسي (العقد:
`entry_purple_prereg.md` · مدفوعٌ **قبل** أيّ رقم · أمرُ المالك 2026-08-14).

**السؤال:** خطةُ الفارز ترسو على `pivot` (أدنى قاع النافذة) والسعرُ يصل
فوقها «بنسب جنونية» فلا تتعبأ (‏≈54% `no_fill`) — فهل إرساؤها على **المستوى
المُختبَر** (تعريف 🟣 «طلب/دخول» عند فيصل: «ضربها مرتين ولا كسرها ⇒ الدخول
فوقها») يرفع التسليمَ لكل إشارة؟

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** القبول `analyze_ticker`
الإنتاجي (المسار العادي حصرًا) · المستوى `tested_level` الإنتاجية · الخطة
`rebound_arms.mirror_plan` · الحسم `rebound_arms.resolve_episode` · قيدُ
السنة وقفزةُ `WAIT` كما في `rebound_arms.walk_symbol`.

**فحصُ البنية الحاكم:** حيث لا مستوى ⇒ الذراعان **بت-بت بالبناء** — أيُّ
تنافرٍ هناك عطبُ أداةٍ ⇒ خروج 3 ولا يُفسَّر رقم.
🔒 خارج مسار الفرز كليًّا (`Super_stock` لا يستورد هذا الملف — مقفول) · لا
`LOGIC_VERSION` · والحكم بمعايير §③ المسجّلة لا بعدها."""
from __future__ import annotations

import os
import sys


def _log(m):
    print(m, flush=True)


def walk_symbol_purple(sym, df, year=None):
    """يمشي رمزًا كلَّ جلسة: قبولُ المسار العادي ⇒ إشارةٌ بذراعين مقترنين.
    يرجع [{"i", "lv", "oc0", "st0", "oc1", "st1"}] — `lv` غائب ⇒ E1 ≡ E0."""
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    out = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return out
    n = len(df)
    i = RB.MIN_BARS
    while i < n:
        if year and yrs[i] != str(year):
            i += 1
            continue
        sl = df.iloc[:i + 1]
        S._REJECT_REASONS.pop(str(sym).upper(), None)
        try:
            r = S.analyze_ticker(sym, sl)
        except Exception:                                        # noqa: BLE001
            r = None
        if r:
            tr0 = [float(x) for x in (r.get("tranches") or r.get("entry") or [])]
            st0 = r.get("stop")
            st0 = float(st0[0] if isinstance(st0, (list, tuple)) else st0 or 0)
            if tr0 and st0 > 0:
                oc0 = RB.resolve_episode(hi, lo, i, tr0, st0)
                lv = None
                try:
                    t = S.tested_level(sl)
                    if t:
                        lv = float(t["level"])
                except Exception:                                # noqa: BLE001
                    lv = None
                if lv and lv > 0:
                    tr1, st1 = RB.mirror_plan(lv)
                    oc1 = RB.resolve_episode(hi, lo, i, tr1, st1)
                else:
                    tr1, st1, oc1 = tr0, st0, oc0     # بت-بت بالبناء (§②)
                out.append({"i": i, "lv": lv, "oc0": oc0, "st0": st0,
                            "oc1": oc1, "st1": st1})
            i += RB.WAIT
            continue
        i += 1
    return out


def report(rows, n_syms, year) -> int:
    """§③: الذراعان المقترنان + الأزواج المتنافرة + فحص البنية (خروج 3)."""
    import rebound_arms as RB                                    # noqa: PLC0415
    _log(f"\n🟣 T-PURPLE سنة {year} — رموزٌ مفحوصة {n_syms} · إشارات {len(rows)}")
    if not rows:
        _log("⛔ صفرُ إشارات — لا تشغيلةَ خضراءَ بصفر قياس (خروج 4).")
        return 4
    bad = [e for e in rows if not e["lv"] and e["oc0"] != e["oc1"]]
    if bad:
        _log(f"⛔ فحص البنية سقط: {len(bad)} صفًّا بلا مستوى واختلف ذراعاه "
             f"⇒ عطبُ أداةٍ (خروج 3) ولا يُفسَّر رقم.")
        return 3
    _log(f"  ✅ فحص البنية: حيث لا مستوى الذراعان بت-بت "
         f"({sum(1 for e in rows if not e['lv'])} صفًّا).")
    for name, key in (("E0-الإنتاج", "oc0"), ("E1-البنفسجي", "oc1")):
        eps = rows
        dec = [e for e in eps if e[key] in ("win", "loss")]
        k = sum(1 for e in dec if e[key] == "win")
        nf = sum(1 for e in eps if e[key] == "no_fill")
        op = sum(1 for e in eps if e[key] == "open")
        w = RB.wilson(k, len(dec)) if dec else (0.0, 0.0)
        _log(f"  {name:<12} إشارات={len(eps):<6} محسومة={len(dec):<5} "
             f"بلغ150={k:<4} شرطية={100.0 * k / len(dec) if dec else 0.0:6.2f}% "
             f"Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}] no_fill={nf} · open={op}")
        wp = RB.wilson(k, len(eps))
        _log(f"    ⤷ التسليم لكل إشارة = {100.0 * k / len(eps):6.2f}% "
             f"({k} من {len(eps)}) Wilson=[{100 * wp[0]:.2f},{100 * wp[1]:.2f}]")
    # الأزواج المتنافرة (McNemar) — المقياس الحاكم المقترن
    b = sum(1 for e in rows if e["oc1"] == "win" and e["oc0"] != "win")
    c = sum(1 for e in rows if e["oc0"] == "win" and e["oc1"] != "win")
    n = len(rows)
    diff = (b - c) / n
    se = ((b + c - (b - c) ** 2 / n) ** 0.5) / n if (b + c) else 0.0
    _log(f"  🔗 الأزواج المتنافرة: سلّمت E1 وحدها b={b} · سلّمت E0 وحدها c={c} "
         f"⇒ الفرق المقترن {100 * diff:+.2f} نقطة "
         f"[{100 * (diff - 1.96 * se):+.2f},{100 * (diff + 1.96 * se):+.2f}]")
    with_lv = sum(1 for e in rows if e["lv"])
    _log(f"  📎 إشارات لها مستوى مُختبَر: {with_lv} من {n} "
         f"({100.0 * with_lv / n:.1f}%) — الفرقُ كله يصنعه هذا الجزء بالبناء.")
    _log("  🧭 الحكمُ النهائي بمعايير §③ على السنوات الثلاث مجتمعةً — لا حكم بسنة.")
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🟣 T-PURPLE — مرساة الطلبات البنفسجية · سنة {year}"
         f"\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    probe = sorted(hist)[:5]
    for sym in probe:                       # فحص حتمية (عرف rebound_arms)
        df = hist[sym]
        if df is None or len(df) < RB.MIN_BARS + 10:
            continue
        sl = df.iloc[:RB.MIN_BARS + 10]
        a = S.analyze_ticker(sym, sl)
        b = S.analyze_ticker(sym, sl)
        if (a is None) != (b is None):
            _log(f"⛔ حتمية: نداءان متطابقان اختلفا على {sym} (خروج 5).")
            return 5
    rows, n_syms = [], 0
    yr = year if year and year != "?" else None
    if not yr:
        _log("⚠️ بلا سنةٍ محددة — المشي على كامل مدى اللقطة (يُعلَن).")
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        rows.extend(walk_symbol_purple(sym, df, year=yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · إشارات حتى الآن {len(rows)}")
    return report(rows, n_syms, year)


if __name__ == "__main__":
    sys.exit(main())
