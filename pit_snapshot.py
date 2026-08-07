# -*- coding: utf-8 -*-
"""🧭 pit_snapshot — لقطةُ أسعارٍ point-in-time كاملة من Polygon (مرحلة PIT ‏P3-أ).

الغرض (‏`pit_prereg.md` §③): بناءُ لقطةٍ **بنفس صيغة** `save_frozen_dataset`
حرفيًّا (‏`{hist, splits, asof, history_days}` · gzip-pickle-4 · مانفست SHA-256)
لكن كونُها **كونُ يومٍ ماضٍ الشامل** (‏من لقطة `pit_universe`، بمن شُطب لاحقًا) —
فيستهلكها `backtest.yml` القائم **بلا تعديل حرفٍ** عبر artifact باسم
`frozen-dataset` وملفّ `frozen_backtest.pkl.gz`.

⚠️ **حدود صدقٍ مطبوعة مع كلّ مُخرَج:**
- Polygon `adjusted=true` يسوّي **التقسيمات** · وyfinance `auto_adjust` يسوّي
  التقسيمات **والتوزيعات** — الفرقُ شبه معدومٍ في فئتنا (مغمورةٌ بلا توزيعات)
  لكنه يُسمّى ولا يُخفى.
- فلترُ النوع يحاكي فلترَ كون الفارز (أسهمٌ عادية: `CS`/`ADRC`؛ تُستبعد
  ETF/وارنت/وحدة/ممتازة/حقوق) — والمُستبعَد **يُعدّ ويُعلَن** لا يُطوى.

🔒 عزلٌ تامّ: لا يُستورَد في `Super_stock.py` ولا أيّ مسار إنتاجيّ · التطابقُ مع
صيغة الإنتاج مضمونٌ **بقفلٍ سلوكيّ** (تُبنى لقطةٌ مصغّرة وتُقرأ عبر
`load_frozen_dataset` الإنتاجيّة نفسِها في السويّة).

التشغيل:
    PIT_UNIVERSE_FILE=pit_universe_2025-01-02.json PIT_START=2022-10-01 \
    PIT_END=2026-03-31 python3 pit_snapshot.py
"""
import gzip
import hashlib
import json
import os
import pickle
import sys
import time

from pit_history import polygon_daily, _fetch as _net_fetch

MIN_BARS = 120                 # ⇐ يطابق CONFIG["MIN_BARS"] (بالتوثيق لا بالاستيراد)
COMMON_TYPES = {"CS", "ADRC"}  # أسهمٌ عادية (يحاكي فلتر get_universe)
SPLITS_URL = "https://api.polygon.io/v3/reference/splits"
SLEEP = 0.05                   # ‏~4800 نداء ⇒ لطفٌ بالمنفذ بلا إبطاءٍ مؤثّر


def split_series(rows):
    """📐 نقيّة: صفوفُ `/v3/reference/splits` ⟶ ‏{رمز: Series بنسبة yfinance}.

    النسبة = `split_to / split_from` (عكسيّ 1-مقابل-20 ⇒ 0.05) — **نفسُ اصطلاح**
    عمود `Stock Splits` الذي يخزّنه `run_freeze`، فتقرؤه بوّاباتُ الوهميات
    و`_split_scale_factor` بلا ترجمة."""
    import pandas as pd
    acc = {}
    for r in rows or []:
        try:
            t = r["ticker"]
            frm, to = float(r["split_from"]), float(r["split_to"])
            d = pd.to_datetime(r["execution_date"])
            if frm > 0 and to > 0:
                acc.setdefault(t, []).append((d, to / frm))
        except (KeyError, TypeError, ValueError):
            continue
    out = {}
    for t, pairs in acc.items():
        pairs.sort()
        out[t] = pd.Series([v for _, v in pairs], index=[d for d, _ in pairs])
    return out


def fetch_all_splits(start, end, api_key, fetch=_net_fetch, max_pages=200):
    """📥 مسحةٌ واحدة مرقّمة لكل تقسيمات السوق في النافذة (لا نداءَ لكلّ رمز)."""
    rows, pages = [], 0
    url = (f"{SPLITS_URL}?execution_date.gte={start}&execution_date.lte={end}"
           f"&limit=1000&sort=execution_date")
    while url:
        if pages >= max_pages:
            raise RuntimeError(f"splits: بلغ سقف الصفحات ({max_pages}) وبقيّةٌ باقية")
        blob = fetch(url, api_key) or {}
        rows.extend(blob.get("results") or [])
        url = blob.get("next_url")
        pages += 1
    return rows


def save_snapshot(hist, splits, asof, history_days, path):
    """💾 **نفسُ صيغة `save_frozen_dataset` حرفيًّا** (المفاتيح الأربعة · بروتوكول 4
    · مانفست SHA-256) — التطابقُ محروسٌ بقفلٍ سلوكيّ يقرأ عبر اللودر الإنتاجيّ."""
    payload = {"hist": hist, "splits": splits, "asof": asof,
               "history_days": history_days}
    blob = pickle.dumps(payload, protocol=4)
    with gzip.open(path, "wb") as fh:
        fh.write(blob)
    sha = hashlib.sha256(blob).hexdigest()
    manifest = {"asof": asof, "n_symbols": len(hist), "sha256": sha,
                "history_days": history_days, "path": path}
    with open(path + ".manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def main():
    api_key = os.environ.get("POLYGON_API_KEY", "").strip()
    uni_file = os.environ.get("PIT_UNIVERSE_FILE", "").strip()
    start = os.environ.get("PIT_START", "").strip()
    end = os.environ.get("PIT_END", "").strip()
    out = os.environ.get("PIT_OUT", "frozen_backtest.pkl.gz").strip()
    if not (api_key and uni_file and start and end):
        print("⛔ يلزم: POLYGON_API_KEY · PIT_UNIVERSE_FILE · PIT_START · PIT_END")
        return 2
    blob = json.load(open(uni_file, encoding="utf-8"))
    rows = blob.get("rows_then") or []
    date_then = blob.get("date")
    if not rows:
        print("⛔ لقطة الكون بلا صفوف")
        return 2

    syms = [r["ticker"] for r in rows if (r.get("type") or "CS") in COMMON_TYPES]
    skipped_type = len(rows) - len(syms)
    print(f"🧭 لقطة PIT: كون {date_then} = {len(rows)} · أسهمٌ عادية {len(syms)}"
          f" · مُستبعَدٌ بالنوع {skipped_type} (ETF/وارنت/وحدة…)")

    # 🎛️ شاهدُ ضبطٍ قبل أيّ لفّة (درسُ 0/40): حيٌّ صفريٌّ = عطلُ أداةٍ فنقف فورًا.
    _c, _cd = polygon_daily("AAPL", start, end, api_key)
    if _c is None or not len(_c):
        print(f"⛔ شاهدُ الضبط AAPL صفر ({_cd}) — عطلُ أداةٍ/بيئة، لا لقطةَ تُبنى")
        return 3

    hist, diag_counts = {}, {}
    short_n = 0
    t0 = time.time()
    for i, sym in enumerate(syms, 1):
        df, diag = polygon_daily(sym, start, end, api_key)
        key = diag.split("(")[0].split(":")[0]
        diag_counts[key] = diag_counts.get(key, 0) + 1
        if df is not None and len(df) >= MIN_BARS:
            hist[sym] = df
        elif df is not None:
            short_n += 1
        if i % 250 == 0:
            print(f"  {i}/{len(syms)} · صالح {len(hist)} · "
                  f"{(time.time() - t0) / 60:.1f}د")
        time.sleep(SLEEP)

    print("🧭 تقسيمات النافذة (مسحة واحدة)…")
    try:
        sp_rows = fetch_all_splits(start, end, api_key)
        splits = {t: s for t, s in split_series(sp_rows).items() if t in hist}
        print(f"  تقسيمات السوق بالنافذة: {len(sp_rows)} صفًّا · "
              f"لرموز اللقطة: {len(splits)}")
    except Exception as e:                                       # noqa: BLE001
        # لقطةٌ بلا splits أسوأ من الفشل (بوّابة الوهميات تُعطَّل بصمت) ⇒ نقف.
        print(f"⛔ تعذّر جلب التقسيمات: {type(e).__name__}: {e}")
        return 3

    import datetime as _dt
    hd = (_dt.date.fromisoformat(end) - _dt.date.fromisoformat(start)).days
    man = save_snapshot(hist, splits, asof=date_then, history_days=hd, path=out)
    print("")
    print(f"💾 {out} · رموز {man['n_symbols']} · بتقسيمات {len(splits)} · "
          f"SHA {man['sha256'][:12]}")
    print(f"📊 تشخيص الجلب: {diag_counts} · قصير (تحت {MIN_BARS}): {short_n}")
    print("⚠️ حدُّ صدق: Polygon يسوّي التقسيمات لا التوزيعات (yfinance يسوّي "
          "الاثنين) — الفرقُ شبه معدومٍ في فئتنا ويُسمّى هنا.")
    print("🔏 PIT_SNAPSHOT_JSON " + json.dumps(
        {"asof": date_then, "start": start, "end": end,
         "universe_total": len(rows), "common": len(syms),
         "skipped_type": skipped_type, "usable": man["n_symbols"],
         "short": short_n, "with_splits": len(splits),
         "sha256": man["sha256"][:16], "diag": diag_counts},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
