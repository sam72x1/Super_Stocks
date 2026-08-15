#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 T-METHOD-WINDOW — أذرعُ نافذة الحدث المؤسِّس وشرط RSI (العقد
`method_window_prereg.md` مدفوعٌ **قبل** أيّ رقم · أمرُ المالك «نفّذ الحزمة»).

🔒 **بحث/قياس — خارج الإنتاج تمامًا:** لا يستوردها `Super_stock.py` (مقفول)، ولا
تكتب حالة، ولا تمسّ بوّابةً ولا عتبة. تُعيد استعمال **دوالّ الإنتاج نفسها**
(`method_founding` · `method_sequence` · `falling_gap_candle` · `rsi`) فيستحيل أن
ينحرف المقيسُ عن المُشغَّل.

🔑 **تمريرةٌ واحدة والأذرعُ الأربعُ مشتقّةٌ منها** (العقد §④): لكلّ (رمز، جلسة)
يُنادى `method_founding` **مرّةً واحدة** بـ`dmin=0` ثم تُشتقّ العضويةُ من
`bars_since_peak` — فيستحيل **بنيويًّا** أن تختلف العيّنةُ أو الميزانية بين
الأذرع (القاعدة المستخرَجة من إفساد `T-CLIFF`).

⚠️ **والعتباتُ تُمرَّر صراحةً ولا تُقرأ من `CONFIG`** لنافذة الهبوط ولا لحدّ RSI
⇒ أرقامُ هذي التجربة **قابلةٌ لإعادة الإنتاج بت-بت بعد التطبيق**."""
from __future__ import annotations

import json
import os
import sys

STEP = 5                  # خطوةُ المشي بالجلسات (العقد §④ — واحدةٌ للأربع)
MIN_BARS = 60             # أرضيةُ الإنتاج (`scan_method_hunter`: `len(df) < 60`)
DMAX = 30                 # ثابتٌ في الأذرع الأربع ⇒ الشريحةُ متطابقة
RSI_MAX = 30.0            # «‏+ RSI تحت 30» — حدُّ الذراع، لا يُقرأ من CONFIG
RSI_MIN_BARS = 20         # أرضيةُ حسابِ RSI (تمييزُ المحسوب من المحشوّ)

# الأذرعُ الأربع: (الاسم، أدنى نافذة، هل يشترط RSI)
ARMS = (("A0", 20, False), ("A1", 10, False),
        ("A2", 20, True), ("A3", 10, True))
STAGES = ("price", "window_ok", "founding", "seq", "entry_zone",
          "gap_ok", "rsi_pass", "match")

CATALOG = frozenset("""AZI DSY EHGO ZCMD JZ SPRC JEM WORX NUWE ONCO KUST LABT
ELAB XHLD GWAV AUUD FRSX ENPH VMAR CUR NAMM MTVA TRUG MWC SVRE MBRX HTCR BNKK
CHSN PAVS HUBC WETO CAPR APVO CMTL KLXE""".split())


def _log(m):
    print(m, flush=True)


def arm_member(arm_dmin, arm_needs_rsi, bars_since_peak, rsi_ok, rsi_val) -> bool:
    """نقيّة: هل يقع الصفُّ داخل هذي الذراع؟ — **اشتقاقٌ لا إعادةُ حساب**.

    🔒 مقفولٌ بـ`MW1`: العضويةُ المشتقّة تطابق نداءً مباشرًا لـ`method_founding`
    بالـ`dmin` نفسه. و«تعذّرٌ ≠ مخالفة»: `rsi_ok=False` ⇒ **يمرّ**."""
    if bars_since_peak is None:
        return False
    if not (int(arm_dmin) <= int(bars_since_peak) <= DMAX):
        return False
    if arm_needs_rsi and rsi_ok and float(rsi_val) >= RSI_MAX:
        return False
    return True


def rsi_at(S, close):
    """نقيّة-الأثر: `(القيمة، هل هي محسوبة)` على الفريم اليوميّ.

    🔴 `rsi()` تنتهي بـ`fillna(50.0)` ⇒ المحشوُّ يُقرأ 50 و«تحت 30» كانت سترفضه
    ⇒ **تعذّرٌ = مخالفة** وهو نقيضُ قاعدتنا. ومسارُ الحشو الوحيد الممكن: سلسلةٌ
    قصيرة أو **بلا هبوطٍ واحد** داخل النافذة (`avg_loss`=0)."""
    try:
        if len(close) < RSI_MIN_BARS or not bool((close.diff().tail(42) < 0).any()):
            return (None, False)
        v = float(S.rsi(close).iloc[-1])
        return (v, v == v)                       # NaN ⇒ غيرُ محسوب
    except Exception:                                            # noqa: BLE001
        return (None, False)


def measure(S, hist) -> dict:
    """التمريرةُ الواحدة: تُرجع العدّادات لكلّ ذراع + التوزيع + الرموز."""
    cnt = {a[0]: {k: 0 for k in STAGES} for a in ARMS}
    cat = {a[0]: 0 for a in ARMS}
    syms_of = {a[0]: set() for a in ARMS}
    buckets = {"10-19": 0, "20-30": 0}
    pairs = 0
    price_floor = float(S.CONFIG["METHOD_MIN_PRICE"])
    for sym, df in (hist or {}).items():
        try:
            n = len(df)
        except Exception:                                        # noqa: BLE001
            continue
        # 🐞 كان الشرطُ `n < MIN_BARS + STEP` فيُسقط **كلَّ** رمزٍ طولُه 60-64 بارًا
        #    وهو داخلُ أرضية الإنتاج (60) ⇒ قصٌّ صامتٌ في المقام. كشفه قفلُ `MW2`.
        if n < MIN_BARS:
            continue
        in_cat = str(sym).upper() in CATALOG
        # 🔒 المشيُ **مُرسًى من الآخر**: أحدثُ جلسةٍ مقيسةٌ دائمًا مهما كان الطول
        #    (وإلّا سقطت الجلسةُ الأخيرة كلَّما لم يقبل الطولُ القسمةَ على الخطوة).
        #    والخطوةُ واحدةٌ للأذرع الأربع ⇒ المقارنةُ بينها بت-بت.
        for i in list(range(n, MIN_BARS - 1, -STEP))[::-1]:
            try:
                d = df.iloc[:i]
                pairs += 1
                price = float(d["Close"].values[-1])
                if price < price_floor:
                    continue
                for a in ARMS:
                    cnt[a[0]]["price"] += 1
                # ① نداءٌ **واحد** بنافذةٍ مفتوحةٍ من الأسفل ⇒ تُشتقّ الأذرعُ منه
                fnd = S.method_founding(d, dmin=0, dmax=DMAX)
                if not fnd:
                    continue
                b = int(fnd["bars_since_peak"])
                if 10 <= b <= 19:
                    buckets["10-19"] += 1
                elif 20 <= b <= DMAX:
                    buckets["20-30"] += 1
                for a in ARMS:
                    if int(a[1]) <= b <= DMAX:
                        cnt[a[0]]["window_ok"] += 1
                        cnt[a[0]]["founding"] += 1
                # ② التسلسل — بنداء الإنتاج حرفيًّا (النافذةُ من الحدث)
                ts = S.method_sequence(d, win=b + 2)
                if not (ts and ts.get("ok")):
                    continue
                bot = float(ts.get("bottom") or 0)
                if bot <= 0:
                    continue
                entry = bot * (1.0 + S.CONFIG["METHOD_ENTRY_PCT"] / 100.0)
                gap = S.falling_gap_candle(d, price=entry)
                t1 = float((gap or {}).get("head") or 0)
                rsi_val, rsi_ok = rsi_at(S, d["Close"].astype(float))
                for a in ARMS:
                    name, dmin, needs = a
                    if not (int(dmin) <= b <= DMAX):
                        continue
                    cnt[name]["seq"] += 1
                    if price > entry:
                        continue
                    cnt[name]["entry_zone"] += 1
                    if not t1 or t1 <= entry:
                        continue
                    cnt[name]["gap_ok"] += 1
                    if not arm_member(dmin, needs, b, rsi_ok, rsi_val):
                        continue
                    cnt[name]["rsi_pass"] += 1
                    cnt[name]["match"] += 1
                    syms_of[name].add(str(sym))
                    if in_cat:
                        cat[name] += 1
            except Exception:                                    # noqa: BLE001
                continue
    return {"cnt": cnt, "cat": cat, "buckets": buckets, "pairs": pairs,
            "syms": {k: sorted(v) for k, v in syms_of.items()}}


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 74}\n🔬 T-METHOD-WINDOW — لقطة {year}\n{'=' * 74}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 as-of {asof} · رموز {len(hist)} · خطوة {STEP} جلسات · "
         f"أرضية {MIN_BARS} بارًا")
    _log(f"⚙️ العتباتُ المُمرَّرة صراحةً (لا من CONFIG): dmax={DMAX} · "
         f"RSI<{RSI_MAX:.0f} · وأرضيةُ السعر من CONFIG="
         f"{float(S.CONFIG['METHOD_MIN_PRICE']):.2f}")
    res = measure(S, hist)
    cnt, buckets = res["cnt"], res["buckets"]
    if not res["pairs"]:
        _log("⛔ صفرُ أزواجٍ مقيسة (بصمة الـno-op) ⇒ خروج 4.")
        return 4
    _log(f"🩺 أزواجُ (رمز، جلسة) المقيسة: {res['pairs']:,}")
    _log(f"📊 توزيعُ `bars_since_peak`: سلّة 10-19 = {buckets['10-19']:,} · "
         f"سلّة 20-30 = {buckets['20-30']:,}")
    _log("\n" + "الذراع".ljust(6) + "".join(s.ljust(11) for s in STAGES))
    for name, _d, _r in ARMS:
        _log(name.ljust(6) + "".join(f"{cnt[name][s]:,}".ljust(11)
                                     for s in STAGES))
    # 🔒 بوّابةُ التداخل: A0 ⊆ A1 (وكذلك A2 ⊆ A3) — انكسارُها عطبُ أداةٍ لا نتيجة
    if not (set(res["syms"]["A0"]) <= set(res["syms"]["A1"])
            and set(res["syms"]["A2"]) <= set(res["syms"]["A3"])
            and cnt["A0"]["match"] <= cnt["A1"]["match"]
            and cnt["A2"]["match"] <= cnt["A3"]["match"]):
        _log("⛔ التداخلُ منكسر (‏A0 ⊄ A1) ⇒ عطبُ أداةٍ لا نتيجة ⇒ خروج 5.")
        return 5
    added = sorted(set(res["syms"]["A1"]) - set(res["syms"]["A0"]))
    cut = sorted(set(res["syms"]["A0"]) - set(res["syms"]["A2"]))
    _log(f"\n➕ يُدخلهم التوسيعُ (A1∖A0) [{len(added)}]: "
         + (" · ".join(added[:40]) or "—"))
    _log(f"➖ يُخرجهم شرطُ RSI (A0∖A2) [{len(cut)}]: "
         + (" · ".join(cut[:40]) or "—"))
    _log("\n🧬 شريحةُ الكتالوج (وصفيًّا لا حكمًا): "
         + " · ".join(f"{n}={res['cat'][n]}" for n, _d, _r in ARMS))
    # 🔒 بوّابةُ «المقياسُ لم يفرّق»: كلُّ الصفوف تمرّ أو صفرُها
    base = cnt["A0"]["gap_ok"]
    if base and cnt["A2"]["match"] in (0, base):
        _log(f"ℹ️ شرطُ RSI لم يفرّق على هذي اللقطة (‏{cnt['A2']['match']} من "
             f"{base}) ⇒ خروج 6 (يُطبَع بوصفه كذلك لا يُبتلَع).")
        _log("MW_JSON:" + json.dumps(
            {"year": year, "cnt": cnt, "buckets": buckets,
             "pairs": res["pairs"], "cat": res["cat"],
             "added": added, "cut": cut}, ensure_ascii=False))
        return 6
    _log("MW_JSON:" + json.dumps(
        {"year": year, "cnt": cnt, "buckets": buckets, "pairs": res["pairs"],
         "cat": res["cat"], "added": added, "cut": cut}, ensure_ascii=False))
    _log("\n⚠️ العقد §②: قمعٌ وكلفة — **لا عائد ولا حافّة** · والأعدادُ أرضيّةٌ "
         "(الفريمُ اليوميّ وحده) · والخطوةُ 5 جلسات.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
