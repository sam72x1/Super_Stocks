# -*- coding: utf-8 -*-
"""
==========================================================
🔥📏 تحقّق رادار الانطلاق (Ignition Verify) — أداة مستقلة
==========================================================
يجيب سؤال المستخدم «هل فادنا الاشتراك فعلًا؟» بالأرقام (IGNITION_VERIFY_PLAN.md،
مسجَّل مسبقًا): لكل منفجر تاريخي، هل يشتعل الرادار على شموع يوم الانفجار، وأين في
الحركة (مكسب اليوم من الافتتاح عند الاشتعال)؟

المعيار المسجَّل: مفيد لو (الالتقاط ≥50% · وسيط الأبكرية ≤+20%).
التشغيل: IGNITION_VERIFY_YEAR=2025 python ignition_verify.py   (يلزم POLYGON_API_KEY)
**تحقّق/قياس فقط — لا يمسّ الفرز/الحالة/الرادار الحي.**
"""
import os
import time

import requests

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot

_CAP = 120                      # سقف المنفجرات المفحوصة (لا قصّ صامت — يُسجَّل)


def _day_minutes(sym, date_iso, key):
    """شموع دقيقة يوم تاريخي محدَّد من Polygon (فاشل-آمن → None)."""
    try:
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
               f"/range/1/minute/{date_iso}/{date_iso}"
               "?adjusted=true&sort=asc&limit=1000")
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"},
                         timeout=12)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v")} for b in res
                if b.get("c") is not None and b.get("v") is not None]
        return bars or None
    except Exception:
        return None


def _exploders(year):
    """المنفجرات التاريخية للسنة: (رمز، يوم الانفجار ISO، حاجز الكسر، افتتاح اليوم)."""
    symbols = bot.get_universe() or bot._default_backtest_symbols()
    dw = (f"{year}-01-01", f"{year}-12-31")
    bot.log(f"🔥📏 تحقّق: باكتيست {len(symbols)} رمز لسنة {year}…")
    hist = bot.download_history(symbols)
    need = bot.CONFIG["MIN_BARS"] + bot.CONFIG["BACKTEST_FORWARD_DAYS"]
    fwd = int(bot.CONFIG["BACKTEST_FORWARD_DAYS"])
    expl = bot.CONFIG["EXPLOSION_PCT"]
    out = []
    for sym, df in hist.items():
        if df is None or len(df) < need:
            continue
        try:
            dates = [str(d.date()) for d in df.index]
        except Exception:
            continue
        for t in bot.backtest_symbol(sym, df, date_window=dw):
            if not t.get("exploded") or str(t.get("date", ""))[:4] != str(year):
                continue
            try:
                i = dates.index(str(t["date"])) + 1        # أول بار أمامي
            except ValueError:
                continue
            fwd_df = df.iloc[i:i + fwd]
            if fwd_df.empty:
                continue
            off = bot._find_explosion_day(
                list(fwd_df["High"].values.astype(float)), float(t["entry"]), expl)
            if off is None:
                continue
            gpos = i + off                                 # موضع يوم الانفجار في df
            base = df.iloc[max(0, gpos - 5):gpos]          # ~5 جلسات قبله = القاعدة
            if base.empty:
                continue
            out.append({
                "symbol": sym,
                "day": dates[gpos] if gpos < len(dates) else str(fwd_df.index[off].date()),
                "break_level": round(float(base["High"].max()), 4),
                "open_px": round(float(df.iloc[gpos]["Open"]), 4)})
            if len(out) >= _CAP:
                bot.log(f"🔥📏 بلغ السقف {_CAP} منفجر — نتوقّف (مسجَّل، لا قصّ صامت).")
                return out
    return out


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def main():
    year = (os.environ.get("IGNITION_VERIFY_YEAR", "").strip()
            or os.environ.get("ACC_VERIFY_YEAR", "").strip())
    if not year.isdigit():
        bot.log("⚠️ ضع IGNITION_VERIFY_YEAR=2025 (سنة مكتملة).")
        return
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        bot.send_telegram("🔥📏 تحقّق الرادار: لا مفتاح POLYGON_API_KEY — يلزم دقائق "
                          f"Polygon التاريخية. أضِف السرّ وأعد التشغيل.\n\n{bot.FOOTER}")
        bot.log("⚠️ لا مفتاح Polygon.")
        return
    exps = _exploders(int(year))
    bot.log(f"🔥📏 {len(exps)} منفجر · جلب دقائق يوم الانفجار…")
    caught, gains = 0, []
    for j, e in enumerate(exps):
        mins = _day_minutes(e["symbol"], e["day"], key)
        if mins:
            fire = bot._ignition_first_fire(mins, e["break_level"], e["open_px"])
            if fire:
                caught += 1
                gains.append(fire["gain_pct"])
        if (j + 1) % 20 == 0:
            bot.log(f"🔥📏 {j + 1}/{len(exps)}")
        time.sleep(0.2)
    n = len(exps)
    rate = round(caught / n * 100.0) if n else 0
    med = _median(gains)
    useful = n >= 12 and rate >= 50 and med is not None and med <= 20
    lines = [f"🔥📏 <b>تحقّق رادار الانطلاق — سنة {year}</b>",
             f"منفجرات مفحوصة: <b>{n}</b>" + (f" (سقف {_CAP})" if n >= _CAP else "")]
    if n < 12:
        lines.append("عيّنة غير كافية (أقل من 12) — شغّل سنة كاملة.")
    else:
        lines.append(f"• الالتقاط: <b>{caught}/{n} = {rate}%</b> "
                     f"(المعيار: مفيد ≥50%)")
        lines.append(f"• الأبكرية (وسيط المكسب عند الاشتعال): "
                     f"<b>+{med:.0f}%</b> (المعيار: مفيد ≤+20%)"
                     if med is not None else "• الأبكرية: لا اشتعالات.")
        lines.append("")
        lines.append("✅ <b>حافة توقيت مفيدة بالدليل</b>" if useful else
                     "⚠️ <b>القيمة محدودة تاريخيًّا</b> — الحكم النهائي للسجلّ الحي")
    lines.append("")
    lines.append("ℹ️ تقريبيّ (دقائق حقيقية · حاجز مُقرَّب) · الإنذار الكاذب يُقاس حيًّا.")
    msg = "\n".join(lines)
    bot.log(msg)
    bot.send_telegram(msg + "\n\n" + bot.FOOTER)


if __name__ == "__main__":
    main()
