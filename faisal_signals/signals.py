"""🧾 سجلُّ إشارات فيصل (أمرُ المالك 2026-11-19 «سجل إشارات فيصل — تسجيل فقط»).

سجلٌّ إلحاقيّ `FAISAL_SIGNAL_LEDGER.jsonl`: كلُّ إشارةٍ ينقلها المالكُ من محادثته الخاصّة مع فيصل تُسجَّل
**بالرمز والتاريخ والسعر ونصّ القراءة وحدَها** (لا لقطات — المستودعُ عامّ).
- `kind = "retro"`  : ذُكرت بعد حركتها ⟵ **لا تدخل نسبةَ الإصابة أبدًا**.
- `kind = "forward"`: سُجّلت لحظةَ وصولها بسعرها ⟵ تُحسم بعد `RESOLVE_SESSIONS` جلسة وهي **وحدَها** في النسبة.
قراءةٌ فقط: لا إنتاج · لا تلغرام · لا عتبة. `python3 faisal_signals/signals.py --check` ⟵ خروج 0 أو أسبابُ الرفض.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "FAISAL_SIGNAL_LEDGER.jsonl")
RESOLVE_SESSIONS = 20
KINDS = ("retro", "forward")
BASE = ("id", "kind", "symbol", "recorded_utc", "reading", "source", "counts_in_hit_rate")
FORWARD = ("received_utc", "price_at_receipt", "resolve_after_sessions", "outcome")
RETRO = ("move_date", "prev_close", "reached", "bot_state")


def load(path=LEDGER):
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows


def problems(rows):
    """قائمةُ أسباب الرفض (فارغةٌ = سليم). الرجعيُّ لا يُحسب · والأماميُّ بلا طابع وصولٍ وسعرٍ مرفوض."""
    bad, seen = [], set()
    for i, r in enumerate(rows, 1):
        rid = r.get("id")
        for k in BASE:
            if k not in r:
                bad.append(f"السطر {i}: ينقصه `{k}`")
        if rid in seen:
            bad.append(f"السطر {i}: معرّفٌ مكرّر {rid}")
        seen.add(rid)
        kind = r.get("kind")
        if kind not in KINDS:
            bad.append(f"السطر {i}: نوعٌ مجهول {kind!r}")
            continue
        need = FORWARD if kind == "forward" else RETRO
        for k in need:
            if k not in r:
                bad.append(f"السطر {i}: ينقصه `{k}`")
        if kind == "retro" and r.get("counts_in_hit_rate") is not False:
            bad.append(f"السطر {i}: رجعيٌّ محسوبٌ في النسبة")
        if kind == "forward":
            if r.get("counts_in_hit_rate") is not True:
                bad.append(f"السطر {i}: أماميٌّ غيرُ محسوب")
            if not r.get("received_utc"):
                bad.append(f"السطر {i}: أماميٌّ بلا طابع وصول")
            px = r.get("price_at_receipt")
            if not (isinstance(px, (int, float)) and not isinstance(px, bool) and px > 0):
                bad.append(f"السطر {i}: أماميٌّ بلا سعر وصول")
            if r.get("resolve_after_sessions") != RESOLVE_SESSIONS:
                bad.append(f"السطر {i}: أفقُ الحسم ليس {RESOLVE_SESSIONS}")
        for k in ("image", "screenshot", "photo", "file"):
            if k in r:
                bad.append(f"السطر {i}: حقلُ لقطةٍ ممنوع `{k}`")
    return bad


def hit_rate(rows):
    """(إصابات، محسومة، معلّقة) — على الأماميّ المحسوم وحدَه · والرجعيُّ خارج العدّ بالبناء."""
    fw = [r for r in rows if r.get("kind") == "forward" and r.get("counts_in_hit_rate") is True]
    done = [r for r in fw if isinstance(r.get("outcome"), dict) and r["outcome"].get("hit") in (True, False)]
    return sum(1 for r in done if r["outcome"]["hit"]), len(done), len(fw) - len(done)


def main(argv):
    rows = load()
    bad = problems(rows)
    h, n, pend = hit_rate(rows)
    retro = sum(1 for r in rows if r.get("kind") == "retro")
    print(f"🧾 سجلُّ إشارات فيصل: {len(rows)} صفًّا · رجعيّ {retro} (خارج النسبة) · أماميّ محسوم {n} (إصابة {h}) · معلّق {pend}")
    for b in bad:
        print("❌", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
