#!/usr/bin/env python3
"""📱 لقطاتُ تطبيق «مراقب استراتيجية فيصل» (دفعة `B4_20261107`) مقابل قيم البوت — قراءةٌ فقط (أمرُ المالك 2026-11-07 ①-ب/ج).

`--mode probe` (رنر): لكلّ رمزٍ في `APP_SYMS` (افتراضًا الأربعة): شموعُ `Super_stock.download_history` (ياهو هنا · والفرزُ اليوميّ على TradingView ⟵ الجدارُ يُطابَق بسجلّ `near_watch`) ⟵
`analyze_ticker` (مقبولٌ أم جدارُه بالاسم من `_REJECT_REASONS`) · `near_watch_measure` (قيمُ ظرف الكاتالوج والخارجُ عنه بحوافّ `envelope_p100.json`
الحيّة) · `tested_level` (المستوى واللمسات) · و`drop_pct`/`rr` مقابل حدّيهما ⟵ سطرٌ لكلّ رمز و`APP_JSON`.
🔒 لا تلغرام · لا حفظ حالة · لا تغيير في أيّ جذرٍ أو عتبة.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_SYMS = ("BRTX", "THH", "EHGO", "NEXR")
KEYS = ("drop_pct", "rr")


def edge_of(edges, name):
    """حدُّ معيارٍ من الحوافّ ⟵ (أرضية، سقف) لمعيار النطاق أو (None، حدّ) أو (حدّ، None)."""
    from catalog_envelope import CRITERIA
    for nm, side, _desc, _k in CRITERIA:
        if nm != name:
            continue
        e = (edges or {}).get(name)
        if e is None:
            return None
        if side == "both" and isinstance(e, (list, tuple)) and len(e) == 2:
            return (float(e[0]), float(e[1]))
        return (float(e), None) if side == "lo" else (None, float(e))
    return None


def probe_one(S, sym, df, edges):
    """صفُّ رمزٍ واحد — بلا شبكة (الشموعُ ممرَّرة)."""
    out = {"symbol": sym, "bars": 0 if df is None else int(len(df))}
    if df is None or len(df) == 0:
        return out
    S._CUR_SYM = sym
    S._REJECT_REASONS.pop(sym, None)
    r = S.analyze_ticker(sym, df)
    out["accepted"] = bool(r)
    out["wall"] = None if r else S._REJECT_REASONS.get(sym)
    tl = S.tested_level(df)
    out["tested_level"] = tl
    m = S.near_watch_measure(sym, df, edges)
    if m:
        vals, outside = m
        out["outside"] = outside
        out["vals"] = {k: vals.get(k) for k in KEYS}
        out["edges"] = {k: edge_of(edges, k) for k in KEYS}
        out["price"] = vals.get("price")
    return out


def main(argv=None):
    import Super_stock as S
    import envelope_scan as ES                     # 🔧 مصدرُ الحوافّ كالإنتاج (`Super_stock.py` · «تحت المتابعة») — كان `catalog_envelope.load_edges` ولا وجودَ لها
    syms = [s.strip().upper() for s in os.environ.get("APP_SYMS", ",".join(DEFAULT_SYMS)).split(",") if s.strip()]
    edges = ES.load_edges() or {}
    hist = S.download_history(syms)
    rows = [probe_one(S, s, (hist or {}).get(s), edges) for s in syms]
    for r in rows:
        print(f"📱 {r['symbol']}: شموع {r.get('bars')} · مقبول {r.get('accepted')} · الجدار {r.get('wall')} · المستوى المختبر {r.get('tested_level')} · "
              f"القيم {r.get('vals')} · الحدّان {r.get('edges')} · خارج الظرف {r.get('outside')}")
    print("APP_JSON " + json.dumps(rows, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
