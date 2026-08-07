# -*- coding: utf-8 -*-
"""🧭 pit_universe — لقطةُ كونٍ point-in-time من Polygon (مرحلة PIT الأولى).

الغرض (‏`pit_prereg.md`): أوّلُ قياسٍ **صحيحِ الدلالة** لانحياز البقاء — كم اسمًا
كان حيًّا في يومٍ D وغاب من كون اليوم. الدلالةُ المعتمدة (درسُ المِجَسّ المسحوب):

    كونُ D = ‏/v3/reference/tickers?active=true&date=D   ← النشطون **في D نفسِه**
    «شُطب منذ D» = لقطة D ∖ لقطة اليوم                  ← فرقُ لقطتين، لا استعلامَ نفي

🔒 **عزلٌ تامّ:** لا يُستورَد في `Super_stock.py` ولا أيّ مسار إنتاجيّ · لا يكتب
ملفَّ حالة · فاشل-آمن بصوتٍ عالٍ (تعذُّرٌ ⇒ خروجٌ غير صفريّ مُعلَن، لا نتيجةٌ ناقصة
تُقرأ كاملة). التشغيل: `PIT_DATE=YYYY-MM-DD python3 pit_universe.py`
(اختياريًّا `PIT_EXCHANGE=XNAS` · `PIT_MAX_PAGES=60`).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://api.polygon.io/v3/reference/tickers"
TIMEOUT = 20
RETRIES = 3
PAGE_LIMIT = 1000          # أقصى ما يسمح به المنفذ لكل صفحة
MAX_PAGES_DEFAULT = 60     # ‏60 ألف صفّ سقفًا — أعلى بكثير من كون XNAS (~4-5 آلاف)


def build_url(date_str: str, exchange: str = "XNAS", limit: int = PAGE_LIMIT) -> str:
    """🔗 يبني طلبَ اللقطة — **`active=true` مع `date` حصرًا** (الدلالة الصحيحة).

    🔒 درسُ المِجَسّ المسحوب (‏2026-07-31): `active=false&date=D` تعني «مات قبل D»
    لا «شُطب خلال الفترة» — فاستعمالُها هنا **خطأٌ دلاليّ** يمنعه قفلُ اختبار."""
    q = {"market": "stocks", "exchange": exchange, "active": "true",
         "date": date_str, "limit": str(limit), "sort": "ticker"}
    return BASE + "?" + urllib.parse.urlencode(q)


def parse_page(blob: dict):
    """📄 نقيّة: تُرجع `(صفوف، next_url)` — الصفُّ `{ticker, type, name}` فقط
    (ما يلزم الفلترةَ اللاحقة، لا نقلَ حقولٍ لا تُستعمل)."""
    rows = []
    for r in (blob or {}).get("results") or []:
        t = (r or {}).get("ticker")
        if t:
            rows.append({"ticker": t, "type": r.get("type"),
                         "name": r.get("name")})
    return rows, (blob or {}).get("next_url")


def summarize(rows_then, rows_now):
    """📊 نقيّة: فرقُ اللقطتين — مقياسُ الانحياز الخام.

    ⚠️ حدُّ صدقٍ (يُطبَع مع الناتج): الغائبُ اليوم قد يكون اندماجًا/تغييرَ رمزٍ
    لا موتًا ⇒ الأعدادُ **سقفُ** الانحياز الخام لا صافي الوفيات."""
    then_syms = {r["ticker"] for r in rows_then}
    now_syms = {r["ticker"] for r in rows_now}
    gone = sorted(then_syms - now_syms)
    return {
        "n_then": len(then_syms),
        "n_now": len(now_syms),
        "n_gone": len(gone),
        "gone_pct": round(100.0 * len(gone) / len(then_syms), 1)
        if then_syms else None,
        "gone": gone,
    }


def _fetch(url: str, api_key: str):
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(
                url + ("&" if "?" in url else "?") + "apiKey=" + api_key,
                headers={"User-Agent": "pit-universe/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:                                   # noqa: BLE001
            if attempt == RETRIES - 1:
                raise
            print(f"⚠️ محاولة {attempt + 1} فشلت ({type(e).__name__}) — إعادة…")
            time.sleep(2 ** attempt)
    return None


def fetch_universe(date_str: str, api_key: str, exchange: str = "XNAS",
                   max_pages: int = MAX_PAGES_DEFAULT, fetch=_fetch):
    """📥 يلفّ الصفحات حتى النهاية. **قصٌّ بالسقف يُعلَن ولا يُصمَت** (قاعدة
    «لا قصّ صامت»): بلوغُ السقف مع `next_url` باقية ⇒ يرمي — لقطةٌ ناقصةٌ
    تُقرأ كاملةً أخطرُ من الفشل."""
    rows, url, pages = [], build_url(date_str, exchange), 0
    while url:
        if pages >= max_pages:
            raise RuntimeError(
                f"بلغ سقفَ الصفحات ({max_pages}) وما زالت صفحاتٌ باقية — "
                "لقطةٌ ناقصة تُرفَض، ارفع PIT_MAX_PAGES")
        blob = fetch(url, api_key)
        page_rows, url = parse_page(blob)
        rows.extend(page_rows)
        pages += 1
        print(f"  صفحة {pages}: ‏+{len(page_rows)} (المجموع {len(rows)})")
    return rows


def main():
    date_str = os.environ.get("PIT_DATE", "").strip()
    if not date_str:
        print("⛔ PIT_DATE مطلوب (YYYY-MM-DD)")
        return 2
    api_key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not api_key:
        print("⛔ POLYGON_API_KEY غائب")
        return 2
    exchange = os.environ.get("PIT_EXCHANGE", "XNAS").strip() or "XNAS"
    max_pages = int(os.environ.get("PIT_MAX_PAGES", str(MAX_PAGES_DEFAULT)))
    today = time.strftime("%Y-%m-%d")

    print(f"🧭 لقطة {exchange} كما في {date_str} …")
    rows_then = fetch_universe(date_str, api_key, exchange, max_pages)
    print(f"🧭 لقطة اليوم ({today}) …")
    rows_now = fetch_universe(today, api_key, exchange, max_pages)

    s = summarize(rows_then, rows_now)
    out = {"date": date_str, "today": today, "exchange": exchange,
           "summary": {k: v for k, v in s.items() if k != "gone"},
           "gone": s["gone"],
           "rows_then": rows_then,
           "caveat": ("الغائب اليوم قد يكون اندماجًا/تغيير رمز لا موتًا — "
                      "الأعداد سقفُ الانحياز الخام (pit_prereg.md §⑤)")}
    fn = f"pit_universe_{date_str}.json"
    with open(fn, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    print("")
    print(f"📊 حيٌّ في {date_str}: {s['n_then']} · حيٌّ اليوم: {s['n_now']}")
    print(f"📊 غاب منذها: {s['n_gone']} (‏{s['gone_pct']}% من لقطة {date_str})")
    print("⚠️ " + out["caveat"])
    print(f"💾 {fn}")
    # سطرُ ملخّصٍ آليّ للسجلّ (نمط ENVELOPE_P90_JSON — الـartifacts محجوبة عنّا)
    print("🔏 PIT_SUMMARY_JSON " + json.dumps(
        {"date": date_str, "today": today, "exchange": exchange,
         **{k: v for k, v in s.items() if k != "gone"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
