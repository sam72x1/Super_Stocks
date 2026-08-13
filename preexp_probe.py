#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬🕵️ `T-PREEXP-PROBE` — سلوكُ اليومين قبل الانفجار (`preexp_probe_prereg.md`).

**السؤال (§①، سؤالُ المالك نصًّا):** ماذا فعل المنفجرون في **الجلستين
‏[−2، −1]** قبل انفجارهم — على **الشموع اليومية** (ملحق §⑥) وعلى **الصفقات
الخام** (§②)؟ الزاويةُ الوحيدةُ غيرُ المفحوصة بعد خمس تجاربَ فشلت على نافذة
القاع وعلى صفقات ما قبل الإشارة.

🔒 **مِجَسٌّ تشخيصيٌّ لا تجربةَ حكم** — سقفُ نجاحه مثبَّتٌ سلفًا: **تقريرٌ
وصفيّ، صفرُ تغيير كودٍ أو عتبةٍ أو وزنِ ترتيب**. وأيُّ قاعدةٍ تُشتقّ منه ⇒
تسجيلٌ مسبقٌ جديد + اختبارٌ أماميّ + موافقةُ المالك.

**العيّنتان (§①):** (أ) كتالوجُ فيصل بمرساة `explosion_onset` **المصحَّحة
حصرًا** · (ب) **أسماكُنا الحيّة**: كلُّ صفٍّ في `wl["explosions"]` وسمُه
`base_reason == "مرشّح"` وغيرُ مشتبهِ تقسيم — تُقرأ من السجلّ **وقت التشغيل**
فتنمو ولا تُنتقى يدويًّا. **وشاهدُ الضبط لكلّ حدث:** نفسُ السهم في ‏[−12، −11]
(`case-crossover` — سابقةُ `E-PSEUDO`: تضبط الهويّةَ والفلوتَ والقطاعَ تلقائيًّا).

⚠️ **ويومُ الانفجار نفسُه مُستبعَدٌ من كلّ نافذة** (‏`timestamp.lt` عند فتح جلسة
المِرساة) ⇒ صفرُ تسريب (‏`PX1`).
🧩 **وإعادةُ استعمالٍ لا بناء:** كلُّ المقاييس **دوالُّ الإنتاج بأسمائها**
(`acc_components` · `_operator_blocks` · `uniform_prints` · `activity_features`)
— صفرُ منطقٍ مكرّر (‏`PX7`).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

EVENT_OFFSETS = (-2, -1)          # نافذةُ الحدث (§①)
CTRL_OFFSETS = (-12, -11)         # شاهدُ الضبط لنفس السهم (case-crossover)
MIN_PAIRS = 15                    # أرضيةُ الوصف لكلّ مجموعة (‏PX6)
TRADE_CAP = 60_000                # سقفُ صفقاتِ الجلسة — **يُطبَع دائمًا** (‏PX5)


def _log(msg: str) -> None:
    print(msg, flush=True)


def catalog_events() -> list:
    """المجموعة (أ) — كتالوجُ فيصل بمِرساة `explosion_onset` **المصحَّحة**.

    🔴 **ولا تُستعمل `explosion_index`** (المِرساةُ القديمة تقع **داخل** الانفجار
    ‏20/20 — عيبُ `P0` الموثَّق) — مقفولٌ نحويًّا `PX4`."""
    try:
        import catalog_envelope as CE                            # noqa: PLC0415
    except Exception as e:                                        # noqa: BLE001
        _log(f"⚠️ تعذّر استيراد الكتالوج ({e}) — المجموعة (أ) تُعلَن فارغة.")
        return []
    # 🔒 واستبعادُ المالك يُحترَم هنا أيضًا (‏`HTZ` مُخرَجٌ من الفارز بقراره ⇒
    #    لا يُقاس عليه) — نفسُ مصدرِ الحقيقة `EXCLUDED_BY_OWNER` لا قائمةٌ منّي.
    _skip = set(getattr(CE, "EXCLUDED_BY_OWNER", {}) or {})
    out = []
    for sym in getattr(CE, "CATALOG", []) or []:
        if str(sym).upper() in _skip:
            continue
        out.append({"symbol": str(sym).upper(), "group": "أ", "anchor": None})
    _log(f"📚 المجموعة (أ) كتالوج فيصل: {len(out)} رمزًا "
         f"(المِرساةُ تُحسب بـ`explosion_onset` عند الجلب)")
    return out


def live_events(path: str = "weekly_watchlist.json") -> list:
    """المجموعة (ب) — **أسماكُنا**: مرشّحٌ اجتاز الفارزَ عند قاعه ثم انفجر.

    تُقرأ من `wl["explosions"]` وقتَ التشغيل (تنمو مع كلّ منفجرٍ جديد) —
    `base_reason == "مرشّح"` **و**`suspect_split` غيرُ صادق."""
    try:
        wl = json.load(open(path, encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        _log(f"⚠️ تعذّرت قراءة {path} ({e}) — المجموعة (ب) تُعلَن فارغة.")
        return []
    out = []
    for e in (wl.get("explosions") or []):
        if e.get("base_reason") != "مرشّح" or e.get("suspect_split"):
            continue
        d = e.get("expl_date") or e.get("date")
        if not d:
            continue
        out.append({"symbol": str(e.get("symbol", "")).upper(), "group": "ب",
                    "anchor": str(d)[:10], "gain": e.get("gain")})
    _log(f"🐟 المجموعة (ب) أسماكُنا الحيّة: {len(out)} حدثًا "
         f"(‏`base_reason=مرشّح` وغيرُ مشتبهِ تقسيم)")
    return out


def _sessions_before(bars, anchor_iso: str, offsets) -> list:
    """جلساتُ التداول عند الإزاحات المطلوبة **قبل** المِرساة حصرًا.

    الإزاحاتُ **بالجلسات لا بالأيام** (‏عطلةٌ في المنتصف لا تُزيح النافذة) —
    ودائمًا `< anchor` فلا تدخل جلسةُ الانفجار (‏`PX1`)."""
    try:
        idx = [d for d in bars.index if str(d.date()) < anchor_iso]
    except Exception:                                             # noqa: BLE001
        return []
    out = []
    for off in offsets:                       # ‏−1 = آخرُ جلسةٍ قبل المِرساة
        k = len(idx) + off
        if 0 <= k < len(idx):
            out.append(idx[k])
    return out


def candle_layer(bars, sess_idx, crit=None) -> dict:
    """طبقةُ الشموع (ملحق §⑥) — **`activity_features` الإنتاجية بالاسم**
    (‏`PX7`) على شريحةٍ تنتهي عند جلسة النافذة حصرًا (صفرُ تسريب)."""
    import Super_stock as S                                      # noqa: PLC0415
    sl = bars.loc[:sess_idx]
    if len(sl) < 25:
        return {}
    a = S.activity_features(sl["High"].values, sl["Low"].values,
                            sl["Close"].values, sl["Volume"].values,
                            crit=crit, price=float(sl["Close"].iloc[-1]))
    try:                                       # فجوةُ الافتتاح عن إغلاق الأمس
        a["gap_pct"] = round((float(sl["Open"].iloc[-1])
                              / float(sl["Close"].iloc[-2]) - 1.0) * 100.0, 3)
    except Exception:                                             # noqa: BLE001
        a["gap_pct"] = None
    return a


def trades_layer(sym: str, sess_date: str) -> dict:
    """طبقةُ الصفقات (§②) — دوالُّ الإنتاج بأسمائها، ونهايةٌ **حصرية** عند فتح
    الجلسة التالية فلا تتسرّب صفقةٌ من بعدها.

    ⚠️ **تعذّرُ الجلب يُعَدّ ولا يُصنَّف** (‏`PX3`): عطبُ شبكةٍ ليس «هدوءًا»."""
    import Super_stock as S                                      # noqa: PLC0415
    nxt = (dt.date.fromisoformat(sess_date) + dt.timedelta(days=1)).isoformat()
    rows = S.polygon_base_trades(sym, days=1, end_date=nxt, cap=TRADE_CAP)
    if not rows:
        return {"fetch_ok": False}
    out = {"fetch_ok": True, "n_trades": len(rows),
           "truncated": len(rows) >= TRADE_CAP,
           "usd": round(sum((t.get("price") or 0) * (t.get("size") or 0)
                            for t in rows), 0)}
    try:
        acc = S.acc_components(rows) or {}
        out.update({k: acc.get(k) for k in
                    ("aggressive_buy_pct", "block_share_pct", "dark_share_pct")})
    except Exception:                                             # noqa: BLE001
        pass
    try:
        ob = S._operator_blocks(rows, S.CONFIG["OPERATOR_MIN_SHARES"]) or {}
        out.update({"buy_block_shares": ob.get("buy_block_shares"),
                    "bid_block_shares": ob.get("bid_block_shares")})
    except Exception:                                             # noqa: BLE001
        pass
    try:
        up = S.uniform_prints([(t.get("price"), t.get("size")) for t in rows])
        out.update({"uniform_size": (up or {}).get("uniform_size"),
                    "uniform_count": (up or {}).get("uniform_count")})
    except Exception:                                             # noqa: BLE001
        pass
    return out


def control_check() -> bool:
    """‏`PX2` شاهدُ ضبطٍ خارجيّ: يومُ `AAPL` واحد — عددُ صفقاتٍ معقول.
    **«الصفرُ عطبُ أداةٍ حتى يُنفى»** (درسُ PIT: صفرٌ موحَّدٌ كاد يدفن مشروعًا)."""
    d = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    r = trades_layer("AAPL", d)
    ok = bool(r.get("fetch_ok")) and int(r.get("n_trades") or 0) > 1000
    _log(f"🧪 PX2 شاهدُ الضبط AAPL@{d}: {r.get('n_trades')} صفقة ⇒ "
         + ("✅" if ok else "⛔ **عطبُ أداةٍ محتمَل — لا يُفسَّر أيُّ صفر**"))
    return ok


METRICS = ("vol_x", "range_x", "close_pos", "gap_pct", "n_trades", "usd",
           "aggressive_buy_pct", "block_share_pct", "dark_share_pct",
           "buy_block_shares", "bid_block_shares", "uniform_count")


def _median(xs):
    ys = sorted(v for v in xs if isinstance(v, (int, float)))
    if not ys:
        return None
    n = len(ys)
    return ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2.0


def _mean_of(win, key):
    """متوسطُ المقياس على جلستَي النافذة (‏[−2،−1] أو الشاهد)."""
    vals = [w.get(key) for w in (win or [])
            if isinstance(w.get(key), (int, float))]
    return (sum(vals) / len(vals)) if vals else None


def report_rows(rows) -> None:
    """§② **المقارنةُ المجمَّعة** — وسيطُ **الفرق الزوجيّ** (حدث − شاهد) لكلّ
    مقياسٍ ولكلّ مجموعة، **وعدُّ الإشارات الموجبة/السالبة**.

    🔴 **بلا اختباراتِ دلالةٍ حاكمة** (§②): وصفٌ لا حكم — والعيّنةُ مختارةٌ على
    النتيجة. والمقياسُ الذي **لا يكفي مقامُه** يُطبَع بمقامه لا بنسبةٍ عارية."""
    good = [r for r in rows if r.get("complete")]
    if not good:
        _log("⚠️ لا أزواجَ كاملة ⇒ لا وصف.")
        return
    for grp, label in (("أ", "كتالوج فيصل"), ("ب", "أسماكُنا الحيّة"),
                       (None, "المجموعتان معًا")):
        sub = [r for r in good if grp is None or r["group"] == grp]
        if not sub:
            continue
        _log(f"\n{'─' * 74}\n📊 {label} — أزواجٌ كاملة: {len(sub)}"
             + ("" if len(sub) >= MIN_PAIRS else
                f" ⚠️ **دون أرضية {MIN_PAIRS}: وصفٌ خامٌّ لا يُبنى عليه**")
             + f"\n{'─' * 74}")
        _log(f"{'المقياس':<20}{'وسيطُ الحدث':>13}{'وسيطُ الشاهد':>14}"
             f"{'وسيطُ الفرق':>13}{'موجب/سالب':>12}")
        for m in METRICS:
            ev = [_mean_of(r.get("حدث"), m) for r in sub]
            ct = [_mean_of(r.get("شاهد"), m) for r in sub]
            pairs = [(a, b) for a, b in zip(ev, ct)
                     if isinstance(a, (int, float)) and isinstance(b, (int, float))]
            if not pairs:
                _log(f"{m:<20}{'—':>13}{'—':>14}{'—':>13}{'مقامٌ صفر':>12}")
                continue
            d = [a - b for a, b in pairs]
            pos = sum(1 for x in d if x > 0)
            neg = sum(1 for x in d if x < 0)
            _log(f"{m:<20}{_median([a for a, _ in pairs]):>13.3f}"
                 f"{_median([b for _, b in pairs]):>14.3f}"
                 f"{_median(d):>13.3f}{f'{pos}/{neg}':>12}"
                 + (f"  (ن={len(pairs)})" if len(pairs) != len(sub) else ""))
    _log("\n⚠️ **قراءةٌ إلزامية:** «وسيطُ الفرق» وصفٌ لا دلالة — لا اختبارَ حاكمًا "
         "هنا بنصّ العقد · والعيّنةُ مختارةٌ على النتيجة ⇒ **توصيفٌ لا معدَّلُ "
         "إصابة** · وأيُّ نمطٍ لافتٍ **فرضيةٌ** لاختبارٍ أماميّ مسجَّل لا قاعدة.")


def main() -> int:
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        _log("⛔ `POLYGON_API_KEY` غائب ⇒ خروج 2 (لا مِجَسَّ بلا مصدر).")
        return 2
    _log(f"\n{'=' * 78}\n🔬🕵️ T-PREEXP-PROBE — سلوكُ اليومين قبل الانفجار"
         f"\n   نافذةُ الحدث {EVENT_OFFSETS} · شاهدُ الضبط {CTRL_OFFSETS} · "
         f"سقفُ الصفقات {TRADE_CAP:,}\n{'=' * 78}")
    if not control_check():
        _log("⛔ شاهدُ الضبط سقط ⇒ خروج 3 (لا رقمَ يُنشَر ولا يُفسَّر).")
        return 3
    import Super_stock as S                                      # noqa: PLC0415
    events = catalog_events() + live_events()
    only = (os.environ.get("PREEXP_ONLY") or "").strip().upper()
    if only:
        events = [e for e in events if e["symbol"] in only.split(",")]
        _log(f"↳ مقصورٌ على: {only}")
    rows, skipped, nofetch = [], 0, 0
    for ev in events:
        sym = ev["symbol"]
        try:
            hist = S.download_history([sym])
            bars = hist.get(sym)
        except Exception as e:                                    # noqa: BLE001
            _log(f"  ⚪️ {sym}: تعذّر التحميل ({e})")
            skipped += 1
            continue
        if bars is None or len(bars) < 60:
            skipped += 1
            continue
        anchor = ev.get("anchor")
        if not anchor:                        # المجموعة (أ): مِرساةٌ مصحَّحة
            try:
                import catalog_envelope as CE                     # noqa: PLC0415
                _hi = bars["High"].values.astype(float)
                _lo = bars["Low"].values.astype(float)
                _ix = CE.explosion_index(_hi, _lo)
                k = CE.explosion_onset(_lo, _ix) if _ix is not None else None
                anchor = str(bars.index[k].date()) if k is not None else None
            except Exception:                                     # noqa: BLE001
                anchor = None
        if not anchor:
            skipped += 1
            continue
        rec = {"symbol": sym, "group": ev["group"], "anchor": anchor,
               "gain": ev.get("gain")}
        ok_all = True
        for label, offs in (("حدث", EVENT_OFFSETS), ("شاهد", CTRL_OFFSETS)):
            agg = []
            for si in _sessions_before(bars, anchor, offs):
                d = str(si.date())
                c = candle_layer(bars, si)
                t = trades_layer(sym, d)
                if not t.get("fetch_ok"):
                    ok_all = False
                    nofetch += 1
                agg.append({"date": d, **c, **t})
            rec[label] = agg
            if len(agg) < len(offs):
                ok_all = False
        rec["complete"] = ok_all
        rows.append(rec)
        _log(f"  ✓ {sym} ({ev['group']}) مِرساة {anchor} — "
             f"{'كامل' if ok_all else '⚠️ ناقص (يُستبعَد من الوصف)'}")
    out = os.environ.get("PREEXP_CSV") or "preexp_probe_rows.jsonl"
    with open(out, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    good = [r for r in rows if r.get("complete")]
    report_rows(rows)                      # §② المقارنةُ المجمَّعة — لا تُدفَن
    _log(f"\n📊 أزواجٌ صالحة: {len(good)} من {len(rows)} "
         f"(‏تُخطّي {skipped} · تعذّرُ جلبٍ {nofetch} — يُعَدّ ولا يُصنَّف)")
    for g in ("أ", "ب"):
        n = sum(1 for r in good if r["group"] == g)
        _log(f"   المجموعة ({g}): {n}"
             + ("" if n >= MIN_PAIRS else
                f" ⚠️ **دون أرضية {MIN_PAIRS} ⇒ «لا تكفي وصفًا» وتُنشَر خامًا**"))
    _log(f"💾 الصفوفُ في {out} (تراكميّ · قابلٌ للاستئناف)")
    _log("\n⚠️ **تشخيصٌ لا حكم:** العيّنةُ مختارةٌ على النتيجة ⇒ توصيفٌ لا معدَّلُ "
         "إصابة · ولا تُشتقّ منه قاعدةٌ بلا تسجيلٍ مسبقٍ جديدٍ واختبارٍ أماميّ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
