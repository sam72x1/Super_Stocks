# -*- coding: utf-8 -*-
"""
📦 FAISAL V3.1 — تفريغُ شموع حالات الصور (قراءةٌ فقط · لا تلغرام · لا حالةَ إنتاج).

لماذا: تنزيلُ الـartifact محجوبٌ من بيئة الجلسة (CONNECT 403 · عطلٌ مُثبَت 2026-10-02) وTradingView لا يُصلَ إليه منها ⟵
فالشموعُ التي تُحقَّق عليها الحالاتُ الذهبيّة (DXST · VEEE · RAYA · ATMV · EZRA) وأمثلةُ «غيرُ جاهز/انتظر» المستقلّة
تُجلب هنا على Actions وتُطبع في السجلّ مضغوطةً (V3OUT · gzip ثمّ base64) فتُحلَّل خارجه بلا إعادةِ جلب.

ما يُطبع لكلّ رمز:
  • محاولاتُ حلّ الرمز بالترتيب (خريطةُ الماسح ثمّ NASDAQ · NYSE · AMEX · OTC) وعددُ الشموع لكلّ محاولة — فلا يُقال
    «لا بيانات» عن رمزٍ لم يُجرَّب إلّا على بورصةٍ واحدة (عطلُ ATMV في V3).
  • اليوميّ (تسويةُ التقسيمات كما في الإنتاج) · و30 دقيقة **نظاميّة** و**ممتدّة** لرموز النافذة اللحظيّة وحدَها.
  • تغطيةُ الثلاثين دقيقة (أوّلُ شمعة · آخرُ شمعة · العدد) لكلّ رمزٍ ونوعِ جلسة = جوابُ §16 بالقياس لا بالظنّ.
والتواريخُ بتوقيت نيويورك (`TV.ny_time`) كما في الإنتاج.
"""
import base64
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

# الحالاتُ الذهبيّة ⟵ يوميّ ‏+ 30 دقيقة · وأمثلةُ «جاهز/غيرُ جاهز» المستقلّة ⟵ يوميّ وحدَه (تُقرأ بعد عقدٍ مكتوب)
GOLDEN = ["DXST", "VEEE", "RAYA", "ATMV", "EZRA"]
VALIDATION = ["LABT", "ZNB", "RUBI", "AMIX", "HCWB", "CUPR", "SPRC", "KWM", "PPCB", "NUWE", "SXTC", "NTCL", "ELPW",
              "CPOP", "DAIC", "WETO", "MSGY", "SNAL", "STKH", "DCOY", "BTOG", "YMT", "ONCO", "KUST", "ZCMD"]
EXCHANGES = ["NASDAQ", "NYSE", "AMEX", "OTC"]
DAILY_N = 1000
M30_N = 5000


def resolve(sym, chart, tmap=None):
    """يجرّب الرموزَ بالترتيب ويعيد (الرمزُ الكامل · الشموع · المحاولات) — أوّلُ رمزٍ بشموعٍ غيرِ فارغة يفوز."""
    cands = []
    if tmap and tmap.get(sym):
        cands.append(tmap[sym])
    for e in EXCHANGES:
        c = f"{e}:{sym}"
        if c not in cands:
            cands.append(c)
    tries = []
    for full in cands:
        b = chart.bars(full, "1D", n=DAILY_N)
        tries.append([full, None if b is None else len(b)])
        if b:
            return full, b, tries
    return None, None, tries


def _rows(bars, day=False):
    import tv_data as TV
    out = []
    for b in bars or []:
        t = TV.ny_time(b[0])
        out.append([str(t)[:10] if day else str(t)[:16]] + [None if x is None else round(float(x), 6) for x in b[1:6]])
    return out


def coverage(rows):
    return {"n": len(rows), "first": rows[0][0] if rows else None, "last": rows[-1][0] if rows else None}


def pack(obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")


def unpack(s):
    return json.loads(gzip.decompress(base64.b64decode(s)).decode("utf-8"))


def main(out_dir=None, golden=None, validation=None, chart=None, tmap=None):
    out_dir = out_dir or os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    golden = GOLDEN if golden is None else golden
    validation = VALIDATION if validation is None else validation
    if chart is None:
        import tv_data as TV
        chart = TV.Chart(timeout=30.0)
    if tmap is None:
        try:
            import Super_stock as S
            tmap = S._tv_ticker_map() or {}
        except Exception as e:                                     # noqa: BLE001 — خريطةٌ متعذّرة ⟵ البورصاتُ بالترتيب
            print(f"⚠️ خريطةُ الماسح تعذّرت ({type(e).__name__}) ⟵ تُجرَّب البورصاتُ بالترتيب")
            tmap = {}
    data, cov = {}, {}
    for sym in list(golden) + [s for s in validation if s not in golden]:
        full, daily, tries = resolve(sym, chart, tmap)
        rec = {"full": full, "tries": tries, "daily": _rows(daily, day=True)}
        cov[sym] = {"full": full, "tries": tries, "daily": coverage(rec["daily"])}
        if full and sym in golden:
            for key, ext in (("m30", False), ("m30x", True)):
                b = chart.bars(full, "30", n=M30_N, extended=ext)
                rec[key] = _rows(b)
                cov[sym][key] = coverage(rec[key]) if b is not None else {"n": None, "error": "bars ⟵ None"}
        data[sym] = rec
        print(f"── {sym}: {full or '⛔ لا رمزَ بشموع'} · محاولات {tries} · {json.dumps(cov[sym], ensure_ascii=False)}")
    try:
        import tv_data as TV
        calls = dict(getattr(TV, "CALLS", {}))
    except Exception:                                              # noqa: BLE001
        calls = {}
    res = {"tool": "case_dump V3.1", "golden": list(golden), "validation": list(validation), "coverage": cov,
           "tv_calls": calls, "b64gz": pack(data)}
    json.dump(res, open(os.path.join(out_dir, "case_dump.json"), "w", encoding="utf-8"), ensure_ascii=False)
    missing = [s for s in data if not data[s]["full"]]
    print(f"📦 رموزٌ بشموع {len(data) - len(missing)} من {len(data)} · بلا شموع: {missing or 'لا شيء'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
