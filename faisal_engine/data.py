# -*- coding: utf-8 -*-
"""مِقبسُ البيانات المجمَّدة للمحرّك — قراءةٌ فقط (الشموعُ والتقسيمات من `fm_forensics/data/bars_2026-10-08.json.gz` ·
وإيداعاتُ SEC من `fm_forensics/data/sec_2026-10-08.json.gz`). كلُّ سياقٍ يُعاد **مؤرَّخًا** والغائبُ None = UNKNOWN."""
import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BARS = os.path.join(ROOT, "fm_forensics", "data", "bars_2026-10-08.json.gz")
SEC = os.path.join(ROOT, "fm_forensics", "data", "sec_2026-10-08.json.gz")
_B = _S = None


def _bars():
    global _B
    if _B is None:
        _B = json.load(gzip.open(BARS, "rt", encoding="utf-8"))
    return _B


def _sec():
    global _S
    if _S is None:
        _S = json.load(gzip.open(SEC, "rt", encoding="utf-8"))
    return _S


def symbols():
    return sorted(_bars()["daily"])


def bars(sym):
    """[[date,o,h,l,c,v], …] أو [] — مسوّاةٌ بالتقسيم (TradingView · adjustment=splits)."""
    return list(_bars()["daily"].get(sym) or [])


def splits(sym):
    """[(date, ratio)] من ملفّ الشموع (ياهو) — [] إن لم يُسجَّل شيء؛ None إن كان الرمزُ خارج الملفّ أصلًا."""
    sp = _bars()["splits"]
    if sym not in sp:
        return None
    return [(d, r) for d, r in sp[sym]]


def sec_filings(sym):
    """[{form, filingDate}] مؤرَّخة أو None إن لم يكن للرمز سجلٌّ في SEC (status != ok)."""
    rec = _sec()["symbols"].get(sym)
    if not rec or rec.get("status") != "ok":
        return None
    return [{"form": f.get("form"), "filingDate": f.get("filingDate")} for f in rec.get("filings", [])]


def context(sym, asof):
    """السياقُ المؤرَّخ: الطرحُ من إيداعات SEC بتاريخ ≤ asof (يُطبَّق داخل المحرّك) · التقسيماتُ مؤرَّخة · الفلوتُ والمتاحُ
    والقروباتُ والضغطُ UNKNOWN تاريخيًّا (المرحلة 5: لا عتادَ مؤرَّخًا قبل سجلّات البوت)."""
    return {"splits": splits(sym), "sec_filings": sec_filings(sym), "float_shares": None, "short_available": None,
            "groups": None, "operator_press": None,
            "sources": {"bars": _bars()["meta"].get("source"), "bars_utc": _bars()["meta"].get("utc"),
                        "sec_retrieved_utc": _sec()["meta"].get("retrieved_utc"), "float": "UNKNOWN (no dated source)",
                        "short_available": "UNKNOWN (no dated source)", "groups": "UNKNOWN", "operator_press": "UNKNOWN (daily bars)"}}
