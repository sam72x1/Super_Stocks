# -*- coding: utf-8 -*-
"""🤖🖐️ المرحلة 1 — عامل حصّاد التدفق الحيّ (يشغّله workflow دوريًّا بالسوق).

يراقب أسهم القائمة، وعند رصد **مسح لحظي** (Polygon minute + `_minute_sweep` على دعم السهم)
يسجّل **ميزات الامتصاص** (`operator_flow` + `polygon_flow`) + الحدث في `hand_flow_log.jsonl`
(النتيجة تُحسم لاحقًا). يبني البيانات المعنونة الحقيقية للوكيل (المرحلة 2). نفس فلسفة E2-A.

**🔴 فاشل-آمن مطلق:** بلا `POLYGON_API_KEY` أو `HAND_COLLECT!=1` = لا عمل · أي استثناء يُبتلَع ·
**خارج مسار الفرز/الإنتاج بالكامل** (لا يمسّ القائمة/التنبيهات/الجذور). التشغيل: `python hand_flow_collect.py`.
"""
import os
import sys

try:
    import Super_stock as bot
except ImportError:                    # pragma: no cover
    import super_stock as bot

from hand_flow_recorder import HandFlowRecorder, sweep_flow_features, LOG_PATH

SWEEP_NEAR_PCT = float(os.environ.get("HAND_NEAR_PCT", "8") or 8)   # قرب الدعم لفحص المسح
DEDUP_HOURS = float(os.environ.get("HAND_DEDUP_HOURS", "20") or 20)  # مرة/سهم/جلسة


def _forward_bars(sym, since_ts):
    """شموع يومية (high, low) بعد تاريخ الحدث — لحسم النتيجة (فاشل-آمن → [])."""
    try:
        hist = bot.download_history([sym])
        df = (hist or {}).get(sym)
        if df is None or len(df) == 0:
            return []
        import datetime as _dt
        since = _dt.date.fromtimestamp(float(since_ts))
        out = []
        for ts, row in df.iterrows():
            d = bot.pd.Timestamp(ts).date()
            if d > since:
                out.append((float(row["High"]), float(row["Low"])))
        return out
    except Exception:
        return []


def _already_today(recs, sym, now_ts):
    """دِدوب: هل سُجِّل مسح لهذا السهم خلال DEDUP_HOURS؟ (مرة/سهم/جلسة)."""
    for r in recs:
        if r.get("symbol") == sym:
            try:
                if (now_ts - float(r.get("ts") or 0)) <= DEDUP_HOURS * 3600:
                    return True
            except Exception:
                pass
    return False


def main():
    if os.environ.get("HAND_COLLECT", "").strip() != "1":
        bot.log("🖐️ حصّاد التدفق: HAND_COLLECT!=1 — لا عمل (فاشل-آمن).")
        return
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        bot.log("🖐️ حصّاد التدفق: لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return
    import time as _time
    rec = HandFlowRecorder()
    # ① حسم المعلّقات القديمة (نتائج نضجت)
    try:
        n = rec.resolve_pending(_forward_bars, target_pct=100.0, stop_pct=7.0, horizon=60)
        if n:
            bot.log(f"🖐️ حصّاد التدفق: حُسِمت {n} نتيجة معلّقة.")
    except Exception:
        pass
    # ② رصد المسوحات الحيّة على أسهم القائمة
    try:
        wl = bot.load_watchlist()
    except Exception:
        wl = {}
    active = [s for s in wl.get("stocks", []) if s.get("status") == "active"]
    if not active:
        bot.log("🖐️ حصّاد التدفق: القائمة فارغة.")
        return
    existing = rec.load()
    now = _time.time()
    logged = 0
    for s in active:
        try:
            sym = s.get("symbol")
            support = s.get("pivot")
            if not sym or not support or float(support) <= 0:
                continue
            if _already_today(existing, sym, now):
                continue
            bars = bot.polygon_minute_bars(sym, minutes=90)   # فاشل-آمن → None
            if not bars:
                continue
            # قرب الدعم فقط (يحمي الميزانية) — آخر سعر ضمن SWEEP_NEAR_PCT فوق الدعم
            last_close = float(bars[-1].get("c") or bars[-1].get("close") or 0)
            if last_close <= 0 or last_close > float(support) * (1 + SWEEP_NEAR_PCT / 100.0):
                continue
            if not bot._minute_sweep(bars, float(support)):
                continue
            # مسح مؤكَّد → التقط بصمة التدفق (الامتصاص عند القاع)
            of = bot.operator_flow(sym)                       # فاشل-آمن → None
            try:
                flow = bot.polygon_flow(sym)
            except Exception:
                flow = None
            feats = sweep_flow_features(of, flow)
            sweep_low = min(float(b.get("l") or b.get("low") or last_close) for b in bars)
            if rec.record_sweep(sym, round(float(support), 4), round(sweep_low, 4),
                                round(last_close, 4), feats, ts=now,
                                meta={"stop": s.get("stop"), "src": "live"}):
                logged += 1
        except Exception:
            continue
    bot.log(f"🖐️ حصّاد التدفق: سجّل {logged} مسحًا جديدًا · {rec.summary().splitlines()[0]}")
    # ③ حفظ السجل (git) ليتراكم عبر الجلسات
    try:
        bot.git_save([LOG_PATH])
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main() or 0)
