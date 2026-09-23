# -*- coding: utf-8 -*-
"""📰 مِجَسّ «شمعة الخبر» (R-01 · دفعة 2026-09-23) — **مؤقّت · قراءةٌ فقط · يُحذف بعد قراءة مُخرَجه**.

يجيب قبل دمج السطر عن ثلاثة أسئلة (حزمةُ `faisal_batches/2026-09-23/` · `U-04`):
  ① **CETX** (فيصل `TG_50828`: «شمعة الخبر 3 > 2.70 =E مقاومه»): أيُّ إيداعِ 8-K ببند 2.02
     وقع قرب Ⓔ (منتصف أغسطس تقريبًا)؟ وما OHLCV شمعتَي `lag` 0 و1؟ وهل 2.70-3.00
     رأسٌ وقاع أم جسم (افتتاحٌ وإغلاق)؟
  ② **SNAL** شاهدٌ ثانٍ (Ⓔ في شارت فيصل `TG_20260905_05` نحو 4.9-5.0 في أغسطس).
  ③ **التغطية:** كم سهمًا من القائمة الحيّة له إيداعٌ ببند 2.02 داخل نافذة
     `PROXY_LOOKBACK_DAYS`؟ وكيف يبدو السطرُ عليها فعلًا؟
لا تلغرام · لا Polygon · لا كتابة حالة. يلزمه `SEC_CONTACT` (هويّةُ الوكيل لدى SEC فقط).
"""
import datetime as dt
import json
import time

import requests

import Super_stock as S

TARGETS = ("CETX", "SNAL")
FAISAL = {"CETX": (2.70, 3.00)}        # نصُّ فيصل «3 > 2.70»
LOOK_DAYS = 400                        # للشاهدين: أربعةُ أرباعٍ تقريبًا


def filings_202(sym, days):
    """[(filingDate, acceptanceDateTime, form, items)] لكلّ 8-K/8-K/A ببند 2.02 خلال `days`."""
    cik = S.sec_cik_map().get(sym.upper())
    if not cik:
        return None, "no_cik"
    r = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
                     headers=S.SEC_UA, timeout=40)
    r.raise_for_status()
    rec = ((r.json().get("filings") or {}).get("recent")) or {}
    cut = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    out = []
    for i, form in enumerate(rec.get("form", []) or []):
        fd = (rec.get("filingDate") or [""])[i] if i < len(rec.get("filingDate") or []) else ""
        if fd < cut:
            break
        items = (rec.get("items") or [""])[i] if i < len(rec.get("items") or []) else ""
        acc = ((rec.get("acceptanceDateTime") or [""])[i]
               if i < len(rec.get("acceptanceDateTime") or []) else "")
        if str(form).startswith("8-K") and "2.02" in [x.strip() for x in str(items).split(",")]:
            out.append((fd, acc, form, items))
    return out, "ok"


def bars_around(df, date):
    """شمعتا `lag` 0 و1 حول يوم الإيداع (كما تختارهما `news_candle_level`)."""
    import numpy as np
    import pandas as pd
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    idx = idx.normalize()
    pos = int(np.searchsorted(idx.values, pd.Timestamp(date).to_datetime64(), side="left"))
    rows = []
    for p in (pos - 1, pos, pos + 1, pos + 2):
        if 0 <= p < len(df):
            b = df.iloc[p]
            rows.append({"lag": p - pos, "date": str(idx[p].date()),
                         "o": round(float(b["Open"]), 4), "h": round(float(b["High"]), 4),
                         "l": round(float(b["Low"]), 4), "c": round(float(b["Close"]), 4),
                         "v": int(float(b["Volume"]))})
    return rows


def main():
    print(f"🔑 SEC_UA مضبوط: {'نعم' if 'contact@example.com' not in S.SEC_UA['User-Agent'] else 'لا — الافتراضيّ الوهميّ'}")
    hist = S.download_history(list(TARGETS), start_override="2025-06-01")
    for sym in TARGETS:
        print(f"\n════════ {sym} ════════")
        try:
            fl, st = filings_202(sym, LOOK_DAYS)
        except Exception as e:                                   # noqa: BLE001
            print(f"⛔ SEC: {type(e).__name__}: {e}")
            continue
        print(f"حالة SEC: {st} · إيداعاتُ 2.02 خلال {LOOK_DAYS} يومًا: {len(fl or [])}")
        df = hist.get(sym)
        print(f"الإطار: {0 if df is None else len(df)} شمعة · آخرُ إغلاق "
              f"{'—' if df is None or not len(df) else round(float(df['Close'].iloc[-1]), 4)}")
        for fd, acc, form, items in (fl or []):
            print(f"\n  📄 {form} · filingDate={fd} · acceptanceDateTime={acc} · items={items}")
            if df is None or not len(df):
                continue
            for row in bars_around(df, fd):
                print("     ", json.dumps(row, ensure_ascii=False))
            nc = S.news_candle_level(df, fd)
            print("     ⟵ السطر:", S.news_candle_line(nc) or "—", "| lag =", (nc or {}).get("lag"))
            if sym in FAISAL and nc:
                lo, hi = FAISAL[sym]
                body = (min(nc["open"], nc["close"]), max(nc["open"], nc["close"]))
                print(f"     ⟵ مقابل فيصل {lo}-{hi}: الرأس/القاع = {nc['low']}-{nc['high']} · "
                      f"الجسم = {round(body[0], 4)}-{round(body[1], 4)}")
        time.sleep(0.3)

    # ③ التغطية على القائمة الحيّة
    wl = json.load(open("weekly_watchlist.json", encoding="utf-8"))
    act = sorted({s["symbol"] for s in wl.get("stocks", []) if s.get("status") == "active"})
    win = int(S.CONFIG["PROXY_LOOKBACK_DAYS"])
    print(f"\n════════ التغطية: {len(act)} سهمًا نشطًا · نافذة {win} يومًا ════════")
    hh = S.download_history(act) if act else {}
    got, fails = [], 0
    for sym in act:
        try:
            fl, st = filings_202(sym, win)
        except Exception as e:                                   # noqa: BLE001
            fails += 1
            print(f"  ⛔ {sym}: {type(e).__name__}")
            continue
        fl8 = [f for f in (fl or []) if f[2] == "8-K"]          # الأصليّ فقط كما في الإنتاج
        if fl8:
            nc = S.news_candle_level(hh.get(sym), fl8[0][0])
            got.append(sym)
            print(f"  ✅ {sym}: {fl8[0][0]} ⟵ {S.news_candle_line(nc) or '— (لا شمعة)'}")
        time.sleep(0.15)
    print(f"\nالحصيلة: {len(got)} من {len(act)} لها 8-K ببند 2.02 داخل النافذة · إخفاقاتُ SEC = {fails}")


if __name__ == "__main__":
    main()
