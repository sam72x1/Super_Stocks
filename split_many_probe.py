# -*- coding: utf-8 -*-
"""🔁 مِجَسّ R-02 المؤقّت (دفعة 2026-09-23 · §14 البند 3) — **قراءةٌ فقط · يُحذف قبل الدمج**.

يُجيب بالبيانات الحقيقيّة (سلسلة تقسيمات ياهو على رنر Actions):
  ① توزيعُ `split_count_all` على مجتمعَين حقيقيَّين من المستودع: قائمةُ متابعة الصيّاد
     (`hunter_watchlist.json`) وسجلُّ حصاده (`hunter_ledger.jsonl`) — بميزانيّة وقتٍ **مُعلَنة**
     (لا قصٌّ صامت: يُطبع كم قيس من كم).
  ② شاهدان: رمزٌ بأربعةٍ فأكثر ⇒ السطرُ **يظهر** · ورمزٌ بثلاثةٍ بالضبط ⇒ **لا يظهر** —
     عبر **المسارين الإنتاجيَّين نفسَيهما**: تنبيهُ الصيّاد (كاشُ التشغيلة `_SPLITS_MEMO` كما
     يملؤه `scan_split_hunter`) · وفحصُ اليد (`hand_check.hand_check` يُعيد النصّ ولا يُرسله).
لا تلغرام · لا كتابةُ حالة (الرنر يُرمى) · لا Polygon (بلا سرّ) · لا كرون.
"""
import datetime as dt
import json
import os
import time

import Super_stock as S

T0 = time.time()
BUDGET_S = float(os.environ.get("PROBE_BUDGET_S", "540"))
TODAY = dt.date.today()


def _syms_of(obj):
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("symbol", "sym", "ticker") and isinstance(v, str):
                out.add(v.upper())
            else:
                out |= _syms_of(v)
    elif isinstance(obj, list):
        for x in obj:
            out |= _syms_of(x)
    return out


def _load():
    hw = set()
    try:
        hw = _syms_of(json.load(open("hunter_watchlist.json", encoding="utf-8")))
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ hunter_watchlist.json: {type(e).__name__}")
    led = set()
    try:
        for ln in open("hunter_ledger.jsonl", encoding="utf-8"):
            try:
                led |= _syms_of(json.loads(ln))
            except Exception:                                    # noqa: BLE001
                continue
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ hunter_ledger.jsonl: {type(e).__name__}")
    return sorted(hw), sorted(led - hw)


def _ser(sp):
    try:
        return [(str(ts)[:10], round(float(v), 6)) for ts, v in zip(sp.index, sp.values)]
    except Exception:                                            # noqa: BLE001
        return None


def main():
    hw, led = _load()
    print(f"🔁 R-02 مِجَسّ · اليوم {TODAY} · قائمةُ الصيّاد {len(hw)} · سجلُّ الحصاد {len(led)} · "
          f"ميزانيّة {BUDGET_S:.0f}ث · SPLIT_MANY_COUNT={S.CONFIG['SPLIT_MANY_COUNT']}")
    rows, fails, skipped = [], [], []
    for grp, lst in (("قائمة", hw), ("سجلّ", led)):
        for sym in lst:
            if time.time() - T0 > BUDGET_S:
                skipped.append(sym)
                continue
            sp = S._fetch_splits(sym)                  # المسارُ الإنتاجيّ نفسُه (يملأ الكاش)
            if sp is None:
                fails.append(sym)
                continue
            rows.append((grp, sym, S.split_count_all(sp, TODAY),
                         S._split_frequency(sp, TODAY), _ser(sp)))
    n_all = len(rows)
    dist = {}
    for _, _, n, _, _ in rows:
        dist[n] = dist.get(n, 0) + 1
    many = [r for r in rows if r[2] > S.CONFIG["SPLIT_MANY_COUNT"]]
    three = [r for r in rows if r[2] == S.CONFIG["SPLIT_MANY_COUNT"]]
    print(f"📊 قيس {n_all} · تعذّر الجلب {len(fails)} · **لم يُقَس لانتهاء الميزانيّة {len(skipped)}**")
    print("📊 توزيعُ العدد (التاريخ كلُّه):", dict(sorted(dist.items())))
    print(f"📊 فوق {S.CONFIG['SPLIT_MANY_COUNT']} ⇒ سطر: {len(many)} من {n_all}"
          f" ({(100.0 * len(many) / n_all) if n_all else 0:.1f}%) · ثلاثةٌ بالضبط: {len(three)}")
    for grp, sym, n, f1y, ser in sorted(many, key=lambda r: -r[2])[:25]:
        print(f"   🔁 {grp} {sym}: كلّ={n} · سنة={f1y} · {ser}")
    for grp, sym, n, f1y, ser in three[:10]:
        print(f"   3️⃣ {grp} {sym}: كلّ={n} · سنة={f1y} · {ser}")
    if fails:
        print("⛔ تعذّر:", " · ".join(fails[:40]))
    # ② الشاهدان عبر المسارين الإنتاجيَّين
    wit = []
    if many:
        wit.append(sorted(many, key=lambda r: -r[2])[0][1])
    if three:
        wit.append(three[0][1])
    for sym in wit:
        n = S.split_count_all(S._SPLITS_MEMO.get(sym), TODAY)
        ma20 = None
        try:
            h = S.download_history([sym]) or {}
            df = h.get(sym)
            ma20 = round(S.ema(df["Close"], 20), 4) if df is not None else None
            px = float(df["Close"].iloc[-1]) if df is not None else None
        except Exception as e:                                   # noqa: BLE001
            px = None
            print(f"⛔ {sym} إطار: {type(e).__name__}")
        row = {"symbol": sym, "price": px or 1.0, "half": 1.0, "ref": 2.0, "float": 9e5,
               "avail": None, "borrow_fee": None, "ema20": ma20 or 0.0, "ema30": 0.0,
               "ema50": 0.0, "split_date": str(TODAY), "freq": 0, "plan": {},
               "bottom_test": None, "split_ma": None}
        try:
            msg = S.build_split_hunter_alert([row], today=TODAY,
                                             fetch_hist=lambda s: {})   # الإطارُ لا يلزم السطر
            got = [ln.strip() for ln in msg.splitlines() if "🔁 مقسّم" in ln]
        except Exception as e:                                   # noqa: BLE001
            got = [f"⛔ {type(e).__name__}: {e}"]
        print(f"🪝 تنبيهُ الصيّاد · {sym} (كلّ={n} · متوسّط20={ma20}): {got or '— لا سطر'}")
        try:
            import hand_check as HC
            txt, err = HC.hand_check(sym)
            hc = [ln.strip() for ln in str(txt or "").splitlines() if "🔁 مقسّم" in ln]
            print(f"🕵️ فحصُ اليد · {sym}: {hc or '— لا سطر'}" + (f" · خطأ={err}" if err else ""))
        except Exception as e:                                   # noqa: BLE001
            print(f"⛔ فحصُ اليد {sym}: {type(e).__name__}: {e}")
    print(f"⏱️ {time.time() - T0:.0f}ث")


if __name__ == "__main__":
    main()
