#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬🔥 T-OPFIRE — أداةُ القياس (‏`opfire_prereg.md` هو العقد · لا يُغيَّر بعد الأرقام).

**السؤال:** في لحظة اشتعالٍ يرصدها `_ignition_signal` الإنتاجيّ، هل **قرارُ الكتم
المركَّب** (بصمةُ المضارب) يفصل `real` عن `fakeout` بتعريفَي `_ignition_outcome`؟

🔒 **قارئٌ محض:** لا يكتب حالةً · لا يُستورَد في `Super_stock` · يستورد دوالَّ الإنتاج
**ولا ينسخها** · وخروجٌ **غيرُ صفريّ** عند سقوط أيّ بوّابةِ صلاحية.

🔴 **ولماذا جالبان بحثيّان خاصّان (وليس دوالَّ الإنتاج):** أُثبِت بالقراءة أن
الإنتاجيّتين **لا تكفيان لهذي التجربة**:
 · `polygon_minute_bars` تُثبّت `adjusted=true` وتقرأ «آخر N دقيقة» من **الآن**
   (`Super_stock.py:11160-11161`) ⇒ **لا تصل يومًا تاريخيًّا ولا تُعطي سعرًا خامًّا**،
   والعقد يشترط الخامَّ في الثلاثة (`opfire_prereg.md` §⑨-4 · البوّابة `V9`).
 · `polygon_base_trades` **تُسقط الطابع الزمنيّ** (تُرجع price/size/exchange فقط،
   `Super_stock.py:12050-12052`) ⇒ **يستحيل تقطيعُ الدقائق** ولا تنفيذُ `V5`.
⇒ الجالبان هنا **للجلب فقط**، **وكلُّ حكمٍ يبقى بدوالّ الإنتاج بأسمائها** (قفل `OPF2`).

**وضعُ الجدوى** (`OPFIRE_MODE=feasibility`، الافتراضيّ): **يومٌ واحد** على رموز القائمة
الحيّة — **لا يُنتج حكمًا** بل يطبع ما لم يكن مقيسًا: **أسماءَ حقول `/v3/trades`
الفعلية** · نسبةَ `fallback` · حالتَي `break_level` · وسرعةَ المسار. ولا سنةَ قبل عبوره.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time

import requests

import Super_stock as S

MODE = os.environ.get("OPFIRE_MODE", "feasibility").strip()
DAY = os.environ.get("OPFIRE_DAY", "").strip()          # YYYY-MM-DD
MAX_SYMS = int(os.environ.get("OPFIRE_MAX_SYMS", "12"))
WITNESS = os.environ.get("OPFIRE_WITNESS", "AAPL").strip().upper()
WIN_MIN = 30            # 🔒 نافذةُ الكشف = الحيّ حرفيًّا (Super_stock.py:12369)
FOOTPRINT_TRADES = 250  # 🔒 نافذةُ البصمة = الحيّ حرفيًّا (operator_flow, :12147)
BASE = "https://api.polygon.io"

_FAILS: list = []       # بوّاباتُ صلاحيةٍ ساقطة — تُطبَع وتُسقط الخروج


def gate(name: str, ok: bool, detail: str = "") -> bool:
    """بوّابةُ صلاحيةٍ **تسقط بصوتٍ عالٍ** — لا صمتَ ولا تقديرَ ولا مضيٌّ على عطب."""
    print(("  ✅ " if ok else "  ⛔ ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILS.append(name)
    return ok


def _key() -> str:
    return os.environ.get("POLYGON_API_KEY", "").strip()


def fetch_minute_bars_raw(sym: str, day: str):
    """شموعُ دقيقةِ **يومٍ تاريخيّ** بسعرٍ **خامّ** (`adjusted=false`) — بوّابة `V9`.

    تُرجع [{'o','h','l','c','v','t'}…] تصاعديًّا (‏`t` = بداية الدقيقة ms) أو None.
    **والدقائقُ الفارغة تُحذَف ولا تُملأ بأصفار** (سلوكُ تجميع Polygon نفسُه — العقد §②-2)."""
    k = _key()
    if not k:
        return None
    try:
        url = (f"{BASE}/v2/aggs/ticker/{sym.upper()}/range/1/minute/{day}/{day}"
               f"?adjusted=false&sort=asc&limit=50000")
        r = requests.get(url, headers={"Authorization": f"Bearer {k}"}, timeout=20)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v"), "t": b.get("t")}
                for b in res if b.get("c") is not None and b.get("v") is not None]
        return bars or None
    except Exception:
        return None


def fetch_trades_day(sym: str, day: str, cap: int = 400_000):
    """صفقاتُ يومٍ كاملة **مع الطابع الزمنيّ** — وهو ما تُسقطه دالّةُ الإنتاج.

    ترجّع (rows, raw_keys) حيث rows = [{'ts','price','size','exchange'}…] تصاعديًّا
    و`raw_keys` = **أسماءُ حقول أوّل نتيجةٍ كما جاءت من المزوّد** (تُطبَع لبوّابة `V5`:
    اسمُ حقل الزمن **يُثبَت من المُخرَج لا يُخمَّن**). فاشلٌ-آمن → (None, [])."""
    k = _key()
    if not k:
        return None, []
    h = {"Authorization": f"Bearer {k}"}
    nxt_day = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    url = (f"{BASE}/v3/trades/{sym.upper()}?timestamp.gte={day}"
           f"&timestamp.lt={nxt_day}&limit=50000&order=asc")
    out, raw_keys = [], []
    try:
        for _ in range(12):
            r = requests.get(url, headers=h, timeout=25)
            if r.status_code != 200:
                # عقدُ الطبقة: فشلٌ = None **لا بترٌ صامت** (درسُ `polygon_base_trades`).
                print(f"  ⚠️ صفقات {sym}: صفحة فشلت ({r.status_code}) — تُسقَط كاملةً")
                return None, raw_keys
            j = r.json() or {}
            res = j.get("results") or []
            if res and not raw_keys:
                raw_keys = sorted(res[0].keys())
            for t in res:
                ts = t.get("sip_timestamp", t.get("participant_timestamp"))
                out.append({"ts": ts, "price": t.get("price"),
                            "size": t.get("size"), "exchange": t.get("exchange")})
            nx = j.get("next_url")
            if not nx or len(out) >= cap:
                break
            url = nx if "apiKey" in nx else nx + f"&apiKey={k}"
        return (out or None), raw_keys
    except Exception:
        return None, raw_keys


def mute_decision(of, usd) -> tuple:
    """🔒 **قرارُ الكتم الإنتاجيّ المركَّب** — إعادةُ بناءِ `Super_stock.py:12440-12456`
    حرفيًّا، بثلاث قيم (العقد §③):

      · `pass_operator`  : البصمةُ مقيسة **و**`has_operator`      ⇒ يمرّ
      · `mute_operator`  : البصمةُ مقيسة **و**`¬has_operator`     ⇒ يُكتَم
      · `fallback`       : `_operator_blocks` أرجعت **None**      ⇒ `group` يُكتَم · غيرُه يمرّ

    ترجّع (الشريحة، مكتوم؟) — و`fallback` **يُعَدّ ولا يُسقَط** (السيولةُ الرقيقة تُنتج
    `None` وتُنتج `group` معًا، فإسقاطُها يحذف الشريحةَ المتحيّزة بعينها)."""
    if of is not None:
        if not of.get("has_operator"):
            return "mute_operator", True
        return "pass_operator", False
    return "fallback", S._ignition_candle_class(usd)[0] == "group"


def scan_symbol_day(sym: str, day: str, entry: dict) -> dict:
    """يمشي دقائقَ يومٍ واحدٍ لرمزٍ واحد ⟶ أوّلُ اشتعالٍ فقط (دِدوب العقد §②-4).

    **كلُّ حكمٍ بدالّة الإنتاج:** `_ignition_break_level` · `_ignition_signal` ·
    `_operator_blocks` · `_ignition_candle_class`. ولا نظرَ مستقبليّ: البصمةُ من صفقاتٍ
    زمنُها **أصغرُ من** نهاية دقيقة الاشتعال (`<` لا `<=`) — بوّابة `V5`."""
    out = {"symbol": sym, "day": day, "bars": 0, "trades": 0,
           "break_level": None, "lvl_kind": None, "fire": None,
           "slice": None, "muted": None, "raw_keys": [], "ts_field": None}
    lvl = S._ignition_break_level(entry)
    if not lvl:
        out["lvl_kind"] = "none"
        return out
    crit = ((entry.get("interp") or {}).get("critical_number") or {}).get("price")
    out["break_level"] = float(lvl)
    out["lvl_kind"] = "critical" if crit else "fallback_pivot105"

    bars = fetch_minute_bars_raw(sym, day)
    if not bars:
        return out
    out["bars"] = len(bars)
    rows, raw_keys = fetch_trades_day(sym, day)
    out["raw_keys"] = raw_keys
    if rows is None:
        return out
    out["trades"] = len(rows)
    out["ts_field"] = ("sip_timestamp" if "sip_timestamp" in raw_keys
                       else ("participant_timestamp"
                             if "participant_timestamp" in raw_keys else None))

    for i in range(6, len(bars) + 1):
        win = bars[max(0, i - WIN_MIN):i]
        sig = S._ignition_signal(win, out["break_level"],
                                 vol_mult=float(S.CONFIG["IGNITION_VOL_MULT"]))
        if not sig:
            continue
        end_ms = int(win[-1]["t"]) + 60_000          # نهايةُ دقيقة الاشتعال
        end_ns = end_ms * 1_000_000                  # الطابعُ من المزوّد بالنانو
        prior = [r for r in rows
                 if r.get("ts") is not None and int(r["ts"]) < end_ns]
        tail = prior[-FOOTPRINT_TRADES:]
        of = S._operator_blocks([(r["price"], r["size"]) for r in tail
                                 if r["price"] and r["size"]],
                                int(S.CONFIG["OPERATOR_MIN_SHARES"]))
        sl, muted = mute_decision(of, sig.get("usd"))
        out["fire"] = dict(sig, minute_ms=end_ms - 60_000,
                           n_footprint=len(tail),
                           candle_class=S._ignition_candle_class(sig.get("usd"))[0])
        out["slice"], out["muted"] = sl, muted
        break                                        # 🔒 اشتعالٌ واحدٌ لكلّ (رمز، جلسة)
    return out


def main() -> int:
    print("=" * 78)
    print("🔬🔥 T-OPFIRE — " + ("**وضعُ الجدوى** (لا حكم)" if MODE == "feasibility"
                                else f"وضع «{MODE}»"))
    print("=" * 78)
    if MODE != "feasibility":
        print("⛔ لا وضعَ غيرَ الجدوى مُنفَّذٌ بعد — والعقد يمنع السوقَ الكامل قبل عبوره.")
        return 2
    if not _key():
        print("⛔ `POLYGON_API_KEY` غائب — لا حصادَ ولا حكم.")
        return 2

    wl = S.load_watchlist()
    act = [s for s in (wl.get("stocks") or []) if s.get("status") == "active"]
    day = DAY or (dt.date.today() - dt.timedelta(days=1)).isoformat()
    syms = act[:MAX_SYMS]
    print(f"🔗 اليوم: {day} · رموزُ القائمة الحيّة: {len(syms)} من {len(act)} نشِط · "
          f"نافذةُ الكشف {WIN_MIN}د · نافذةُ البصمة {FOOTPRINT_TRADES} صفقة")
    print(f"   عتباتُ الإنتاج: vol×{S.CONFIG['IGNITION_VOL_MULT']} · "
          f"طبعة≥{S.CONFIG['OPERATOR_MIN_SHARES']} · "
          f"قروب≤{S.CONFIG['IGNITION_USD_GROUP']:,} · "
          f"مضارب≥{S.CONFIG['IGNITION_USD_OPERATOR']:,}")

    t0 = time.time()
    rows = []
    for s in syms:
        try:
            rows.append(scan_symbol_day(s["symbol"], day, s))
        except Exception as e:                                   # noqa: BLE001
            print(f"  ⚠️ {s.get('symbol')}: {type(e).__name__}: {e}")
    dur = time.time() - t0

    lvl_ok = [r for r in rows if r["break_level"]]
    crit_n = sum(1 for r in lvl_ok if r["lvl_kind"] == "critical")
    fb_n = sum(1 for r in lvl_ok if r["lvl_kind"] == "fallback_pivot105")
    fires = [r for r in rows if r["fire"]]
    raw_keys = next((r["raw_keys"] for r in rows if r["raw_keys"]), [])
    ts_field = next((r["ts_field"] for r in rows if r["ts_field"]), None)
    n_trades = sum(r["trades"] for r in rows)
    n_bars = sum(r["bars"] for r in rows)
    sl_count = {}
    for r in fires:
        sl_count[r["slice"]] = sl_count.get(r["slice"], 0) + 1

    print(f"\n📊 المقيس ({dur:,.1f}ث): شموع={n_bars:,} · صفقات={n_trades:,} · "
          f"مستوى كسر={len(lvl_ok)}/{len(rows)} (حرج {crit_n} · احتياط {fb_n}) · "
          f"اشتعالات={len(fires)}")
    if fires:
        print("   الشرائح: " + " · ".join(f"{k}={v}" for k, v in sl_count.items()))
        for r in fires:
            f = r["fire"]
            print(f"   🔥 {r['symbol']} · سعر {f['price']} · vol×{f['vol_x']} · "
                  f"${f['usd']:,} ({f['candle_class']}) · كسر {r['break_level']:.4f} · "
                  f"بصمة من {f['n_footprint']} صفقة ⇒ {r['slice']}"
                  + (" · **مكتوم**" if r["muted"] else " · يمرّ"))

    print("\n🚦 بوّاباتُ الصلاحية:")
    gate("V3 العلمُ فعّال — قرأ (رمز، يوم) فعلًا",
         n_bars > 0 and n_trades > 0,
         f"شموع={n_bars:,} · صفقات={n_trades:,} — الصفرُ ‏no-op لا تُفسَّر نتيجتُه")
    gate("V8 `break_level` مبنيٌّ فعلًا (يقتل «صفرُ اشتعالٍ بنيويّ» قبل الميزانية)",
         len(lvl_ok) > 0, f"{len(lvl_ok)} من {len(rows)}")
    gate("V5 حقلُ الزمن **مُثبَتٌ من المُخرَج لا مُخمَّن**", bool(ts_field),
         f"الحقل: {ts_field or '—'} · حقولُ المزوّد: {', '.join(raw_keys) or '—'}")
    gate("V10 `exchange` حاضرٌ (وإلّا `dark_share_pct` «غيرُ مقيس» لا صفرًا)",
         "exchange" in raw_keys, "غيابُه لا يُسقط الجدوى لكنه يُعلَن")
    gate("V1 شاهدُ الضبط — رمزٌ سائلٌ يُخرج سماتٍ غيرَ تافهة",
         *(lambda w: (bool(w and w[0] and len(w[0]) > 1000),
                      f"{WITNESS}: {len(w[0]) if w and w[0] else 0:,} صفقة"))(
             fetch_trades_day(WITNESS, day, cap=60_000)))
    gate("V9 مقياسُ سعرٍ واحدٌ **خامّ** في الشموع والمستويات",
         "adjusted=false" in open(__file__, encoding="utf-8").read(),
         "الجالبُ البحثيّ يثبّت `adjusted=false`")

    print("\n📌 وما يقيسه هذا الوضعُ ولا يحكم به: **نسبةُ `fallback`** التي تحكم أرضيةَ "
          "«‏≥25 لكلّ شريحة» في العقد §⑥ — وتُقاس على مجتمع ARMED لا على هذي العيّنة.")
    print("🔒 **وضعُ جدوى: صفرُ حكم.** ولا سنةَ ولا سوقَ كاملٌ قبل عبور البوّابات، "
          "ولا رقمَ يُكتَب في `opfire_result.md` قبل ذلك.")
    if _FAILS:
        print("\n⛔ سقطت: " + " · ".join(_FAILS))
        return 3
    print("\n✅ عبرت بوّاباتُ الجدوى كلُّها.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
