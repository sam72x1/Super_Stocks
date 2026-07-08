# -*- coding: utf-8 -*-
"""
==========================================================
🔬 تجربة التحقق T-ACC (POLYGON_EDGE_PLAN §أ-4) — أداة مستقلة
==========================================================
تسأل السؤال الحاسم: **هل «التجميع الصامت» عند القاع يرتبط بالانفجار فعلًا؟**
(المؤشر الذي فشلت كل مؤشرات OHLCV في إيجاده — §0-ز).

المنهج (بلا تسريب، مسجَّل مسبقًا):
  1) يشغّل الباكتيست الموجود على سنة كاملة → إشارات (رمز · تاريخ · انفجر؟).
  2) لكل إشارة: يجلب صفقات Polygon **لنافذة القاع المنتهية يوم الإشارة حصريًا**
     (timestamp.lt = يوم الإشارة — صفقات قبلها فقط) → مكوّنات التجميع.
  3) يحكم لكل مكوّن (أثلاث) بمعيار مسجَّل مسبقًا (فرق انفجار 10+ نقاط + فاصلا
     Wilson منفصلان + يصمد بالسنتين) → يرسل الحكم لتلغرام + CSV تراكمي (استئناف).

التشغيل: ACC_VERIFY_YEAR=2025 python acc_verify.py   (يلزم POLYGON_API_KEY)
**تحقّق/تحليل فقط — لا يمسّ الفرز؛ منح الوزن قرارك بالأرقام لو ثبت الدليل.**
"""
import csv
import os
import time

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot

_FIELDS = ["symbol", "date", "outcome", "exploded",
           "aggressive_buy_pct", "block_share_pct", "dark_share_pct"]


def _load_done(path):
    """يقرأ الصفوف المحسوبة سابقًا (استئناف بعد انقطاع) → dict[key]=row."""
    done = {}
    if not os.path.exists(path):
        return done
    try:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                for k in ("aggressive_buy_pct", "block_share_pct",
                          "dark_share_pct"):
                    row[k] = int(row[k]) if row.get(k) not in ("", None) else None
                row["exploded"] = row.get("exploded") == "True"
                done[f"{row['symbol']}|{row['date']}"] = row
    except Exception as e:
        bot.log(f"⚠️ T-ACC: قراءة CSV: {e}")
    return done


def _append_csv(path, row):
    new = not os.path.exists(path)
    try:
        with open(path, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_FIELDS)
            if new:
                w.writeheader()
            w.writerow({k: row.get(k) for k in _FIELDS})
    except Exception as e:
        bot.log(f"⚠️ T-ACC: كتابة CSV: {e}")


def _year_signals(year):
    """إشارات الباكتيست للسنة (السوق الكامل بلا انحياز — نفس آلية run_backtest)."""
    symbols = bot.get_universe() or bot._default_backtest_symbols()
    dw = (f"{year}-01-01", f"{year}-12-31")
    bot.log(f"T-ACC: باكتيست {len(symbols)} رمز لسنة {year}…")
    hist = bot.download_history(symbols)
    need = bot.CONFIG["MIN_BARS"] + bot.CONFIG["BACKTEST_FORWARD_DAYS"]
    trades = []
    for sym, df in hist.items():
        if df is None or len(df) < need:
            continue
        for t in bot.backtest_symbol(sym, df, date_window=dw):
            if str(t.get("date", ""))[:4] == str(year):
                trades.append(t)
    return trades


def main():
    year = (os.environ.get("ACC_VERIFY_YEAR", "").strip()
            or os.environ.get("BACKTEST_YEAR", "").strip())
    if not year.isdigit():
        bot.log("⚠️ ضع ACC_VERIFY_YEAR=2025 (سنة مكتملة).")
        return
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        bot.send_telegram("🔬 T-ACC: لا مفتاح POLYGON_API_KEY — التجربة تحتاج "
                          "الصفقات التاريخية من Polygon. أضِف السرّ وأعد التشغيل."
                          f"\n\n{bot.FOOTER}")
        bot.log("⚠️ T-ACC: لا مفتاح Polygon.")
        return
    year = int(year)
    path = f"acc_verify_{year}.csv"
    done = _load_done(path)
    signals = _year_signals(year)
    bot.log(f"T-ACC: {len(signals)} إشارة · جلب التجميع من Polygon (بلا تسريب)…")
    rows = []
    for i, t in enumerate(signals):
        key = f"{t['symbol']}|{t['date']}"
        if key in done:
            rows.append(done[key])
            continue
        acc = None
        tr = bot.polygon_base_trades(t["symbol"], end_date=t["date"])
        if tr:
            acc = bot.acc_components(tr)
        row = {"symbol": t["symbol"], "date": str(t["date"]),
               "outcome": t.get("outcome"), "exploded": bool(t.get("exploded")),
               "aggressive_buy_pct": (acc or {}).get("aggressive_buy_pct"),
               "block_share_pct": (acc or {}).get("block_share_pct"),
               "dark_share_pct": (acc or {}).get("dark_share_pct")}
        rows.append(row)
        _append_csv(path, row)
        if (i + 1) % 10 == 0:
            bot.log(f"T-ACC: {i + 1}/{len(signals)}")
        time.sleep(0.25)                       # احترام حدّ Polygon
    report = "\n".join(bot.acc_verify_report(rows))
    bot.send_telegram(f"🔬 <b>تحقّق التجميع الصامت — سنة {year}</b>\n{report}"
                      f"\n\n{bot.FOOTER}")
    bot.log("✅ أُرسل حكم T-ACC.")


if __name__ == "__main__":
    main()
