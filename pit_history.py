# -*- coding: utf-8 -*-
"""🧭 pit_history — جالبُ تاريخ Polygon بمخرَجٍ مطابقٍ لإطار الباكتيست (مرحلة PIT ‏P2).

الغرض (‏`pit_prereg.md` §③-P2): مصدرُ أسعارٍ **يخدم المشطوبة** — yfinance لا يخدمها
وهي جوهرُ قياس انحياز البقاء. المخرَجُ إطارٌ بأعمدة `Open/High/Low/Close/Volume`
وفهرسِ تواريخ — **الشكلُ نفسُه** الذي يبنيه `_extract_into` من yfinance، فيقبله
`analyze_ticker`/`backtest_symbol` بلا سطرِ تكييفٍ واحد.

ويحوي **مِجَسَّ التغطية** الذي يفرضه التسجيل (‏§⑤): «تغطيةُ أسعار Polygon للمشطوبة
تُقاس ولا تُفترَض — عيّنةُ تحقّق ‏30 رمزًا مشطوبًا فأكثر». العيّنةُ **حتميّة**
(‏sha256 — نمط `control_panel` المعتمَد) فتُعاد بالضبط.

🔒 **عزلٌ تامّ:** لا يُستورَد في `Super_stock.py` ولا أيّ مسار إنتاجيّ · لا ملفَّ
حالة · فاشل-آمن بصوتٍ عالٍ. عتبةُ «تاريخٍ نافع» بارامترٌ هنا (افتراضُه 120 يطابق
`MIN_BARS` الإنتاجيّ **بالتوثيق لا بالاستيراد** — العزلُ مقدَّم، والقفلُ يحرس التطابق).

التشغيل (مِجَسّ التغطية):
    PIT_COVERAGE=1 PIT_UNIVERSE_FILE=pit_universe_2025-01-02.json \
    PIT_START=2024-01-01 PIT_END=2025-12-31 python3 pit_history.py
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

TIMEOUT = 20
RETRIES = 3
MIN_BARS_DEFAULT = 120     # ⇐ يطابق CONFIG["MIN_BARS"] الإنتاجيّ (مقفول باختبار)
SAMPLE_DEFAULT = 40        # ‏≥30 التي يفرضها التسجيل §⑤


def aggs_url(sym: str, start: str, end: str) -> str:
    """🔗 طلبُ الشموع اليومية — **`adjusted=true`** (نفسُ تسوية yfinance فتتطابق
    القراءتان؛ تشويهُ التقسيمات المعدَّلة حدُّ صدقٍ قائمٌ في المصدرين معًا)."""
    return (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/"
            f"{start}/{end}?adjusted=true&sort=asc&limit=50000")


def to_frame(results):
    """📐 نقيّة: نتائجُ Polygon ⟶ إطارٌ بشكل `_extract_into` **حرفيًّا**
    (‏`Open/High/Low/Close/Volume` · فهرسُ تواريخ · إسقاطُ صفوف Close الغائبة).
    فارغٌ/تالفٌ ⇒ None."""
    import pandas as pd
    rows = []
    for r in results or []:
        try:
            rows.append({
                "dt": pd.to_datetime(int(r["t"]), unit="ms").normalize(),
                "Open": float(r["o"]), "High": float(r["h"]),
                "Low": float(r["l"]), "Close": float(r["c"]),
                "Volume": float(r.get("v") or 0.0)})
        except (KeyError, TypeError, ValueError):
            continue
    if not rows:
        return None
    df = pd.DataFrame(rows).set_index("dt").sort_index()
    df.index.name = None
    df = df.dropna(subset=["Close"])
    return df[["Open", "High", "Low", "Close", "Volume"]] if len(df) else None


def _fetch(url: str, api_key: str):
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(
                url + "&apiKey=" + api_key,
                headers={"User-Agent": "pit-history/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:                                   # noqa: BLE001
            if attempt == RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def polygon_daily(sym: str, start: str, end: str, api_key: str, fetch=_fetch):
    """📥 شموعُ رمزٍ (يخدم المشطوبة). يرجّع `(df, تشخيص)` — **لا ابتلاعَ صامتًا**.

    🔴 درسُ أوّل تشغيلة (‏`31189086227`، ‏0/40 موحَّدة): النسخةُ الأولى كانت ترجع
    None لكل شيء فلا يُفرَّق «HTTP سليم بلا نتائج» عن «انهيار» عن «رفض» — خلافُ
    قاعدة «يسجّل ولا يصمت». الآن التشخيصُ يُسمّى: `ok` · `empty(status,count)` ·
    `HTTPError:code` · اسمُ الاستثناء."""
    try:
        blob = fetch(aggs_url(sym, start, end), api_key)
        df = to_frame((blob or {}).get("results"))
        if df is None:
            return None, (f"empty(status={ (blob or {}).get('status') }"
                          f",count={ (blob or {}).get('resultsCount') })")
        return df, "ok"
    except urllib.error.HTTPError as e:                          # noqa: BLE001
        return None, f"HTTPError:{e.code}"
    except Exception as e:                                       # noqa: BLE001
        return None, type(e).__name__


def pick_sample(symbols, n, salt="pit-coverage"):
    """🎲 نقيّة: عيّنةٌ **حتميّة** بـsha256 (نمط `control_panel`) — لا انتقاءَ يدٍ
    ولا `random` فتُعاد بالضبط في أيّ إعادة تشغيل."""
    ranked = sorted(symbols,
                    key=lambda s: hashlib.sha256(f"{salt}:{s}".encode()).hexdigest())
    return ranked[:max(0, int(n))]


CONTROL_DEFAULT = ("AAPL", "APVO", "SPRC")   # حيّةٌ ذاتُ تاريخٍ مؤكَّد (‏APVO مُثبَتة
                                             # ببروب NBBO 2026-07-30 على نفس المفتاح)


def coverage_probe(gone, api_key, start, end, sample_n=SAMPLE_DEFAULT,
                   min_bars=MIN_BARS_DEFAULT, fetch=_fetch, log=print,
                   control=CONTROL_DEFAULT):
    """🩺 المِجَسّ الذي يفرضه التسجيل §⑤: كم مشطوبًا له تاريخٌ نافع فعلًا؟

    🔒 **شاهدُ ضبطٍ إلزاميّ** (درسُ «المقياسُ نفسه يحتاج شاهد ضبط» + تشغيلة 0/40):
    رموزٌ حيّة تُقاس أوّلًا بنفس المسار — **صفرُها = عطلُ أداةٍ لا غيابُ بيانات**،
    ويُعلَن `tool_broken` فلا تُقرأ الأصفارُ اللاحقة «تغطيةً معدومة»."""
    ctrl = {}
    for sym in control:
        df, diag = polygon_daily(sym, start, end, api_key, fetch=fetch)
        ctrl[sym] = {"bars": 0 if df is None else len(df), "diag": diag}
        log(f"  🎛️ شاهد {sym}: {ctrl[sym]['bars']} شمعة ({diag})")
    tool_broken = all(c["bars"] == 0 for c in ctrl.values()) if ctrl else False
    if tool_broken:
        log("⛔ شاهدُ الضبط كلُّه صفر ⇒ **عطلُ أداةٍ/مفتاحٍ لا غيابُ بيانات** — "
            "الأصفارُ أدناه لا تُفسَّر تغطية.")
    sample = pick_sample(gone, sample_n)
    detail = {}
    for i, sym in enumerate(sample, 1):
        df, diag = polygon_daily(sym, start, end, api_key, fetch=fetch)
        n = 0 if df is None else len(df)
        detail[sym] = {"bars": n, "diag": diag,
                       "verdict": ("usable" if n >= min_bars
                                   else "short" if n > 0 else "none")}
        log(f"  {i}/{len(sample)} {sym}: {n} شمعة ⇒ {detail[sym]['verdict']} ({diag})")
    counts = {v: sum(1 for d in detail.values() if d["verdict"] == v)
              for v in ("usable", "short", "none")}
    total = len(detail) or 1
    return {"sample_n": len(detail), "min_bars": min_bars,
            "start": start, "end": end, **counts,
            "usable_pct": round(100.0 * counts["usable"] / total, 1),
            "tool_broken": tool_broken, "control": ctrl,
            "detail": detail}


def main():
    if os.environ.get("PIT_COVERAGE", "") != "1":
        print("⛔ الوضع الوحيد حاليًّا: PIT_COVERAGE=1 (المراحل التالية في pit_prereg.md)")
        return 2
    api_key = os.environ.get("POLYGON_API_KEY", "").strip()
    uni_file = os.environ.get("PIT_UNIVERSE_FILE", "").strip()
    start = os.environ.get("PIT_START", "").strip()
    end = os.environ.get("PIT_END", "").strip()
    if not (api_key and uni_file and start and end):
        print("⛔ يلزم: POLYGON_API_KEY · PIT_UNIVERSE_FILE · PIT_START · PIT_END")
        return 2
    try:
        blob = json.load(open(uni_file, encoding="utf-8"))
        gone = blob.get("gone") or []
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ تعذّرت قراءة ملفّ الكون: {type(e).__name__}: {e}")
        return 2
    if not gone:
        print("⛔ قائمة «غاب منذها» فارغة — لا شيء يُقاس")
        return 2
    sample_n = int(os.environ.get("PIT_SAMPLE", str(SAMPLE_DEFAULT)))
    print(f"🩺 مِجَسّ تغطية المشطوبة: عيّنة {sample_n} من {len(gone)} "
          f"(حتميّة sha256) · النافع = {MIN_BARS_DEFAULT} شمعة فأكثر")
    s = coverage_probe(gone, api_key, start, end, sample_n)
    print("")
    print(f"📊 نافع: {s['usable']} · قصير: {s['short']} · بلا تاريخ: {s['none']}"
          f" ⇒ التغطية {s['usable_pct']}%")
    print("🔏 PIT_COVERAGE_JSON " + json.dumps(
        {k: v for k, v in s.items() if k != "detail"}, ensure_ascii=False))
    if s.get("tool_broken"):
        print("⛔ خروجٌ غير صفريّ: شاهدُ الضبط صفر — أصلِح الأداة قبل تفسير أيّ رقم")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
