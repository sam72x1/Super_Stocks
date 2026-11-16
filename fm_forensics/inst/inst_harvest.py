"""🏛️🗓️ حصّادُ «فلتر المؤسسات» الأسبوعيّ الصامت (أمرُ المالك 2026-11-16).

finviz بفلاتر `T-INST` نفسِها (ناسداك · نانو · دون 7$ · ملكيّةُ المؤسسات فوق 20% · تعاملاتُها فوق ‏+10%) كلَّ اثنين بعد الإغلاق
⟵ صفٌّ واحدٌ في سجلٍّ إلحاقيّ `data/inst_weekly.jsonl`: القائمةُ بتاريخها · لكلّ سهمٍ ملكيّتُه وتعاملاتُه وسعرُه وفلوتُه ·
وتقاطعُها مع «تحت المتابعة» (الجاهزيّةُ والنواقص) ومع قائمة البوت · والداخلون والخارجون عن آخر أسبوعٍ سليم.
🛡️ **الحارس:** صفرُ رمز · أو عددٌ لا يطابق المطبوع · أو أعمدةٌ غائبة · أو قيمٌ خارج الفلتر ⟵ صفُّ «عطل» بسببه لا لقطةٌ فارغة ·
والداخلون والخارجون يُحسبون دائمًا على آخر صفٍّ سليم.
🔒 قراءةٌ وجمعٌ فقط: لا تلغرام · لا كتابةَ حالة إنتاج · لا حكم — حتى حكم `T-INST` في 2026-12-15 (`T_INST_prereg.md`).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEDGER = os.path.join(HERE, "data", "inst_weekly.jsonl")
VIEW = 131                                   # عرضُ الملكيّة في finviz (الرموزُ والمطبوعُ والأعمدةُ في طلبٍ واحد)
COLS = ("Inst Own", "Inst Trans")
OWN_MIN, TRANS_MIN, TOL = 20.0, 10.0, 0.01   # حدّا الفلتر كما في `inst.FILTERS` · والتسامحُ تقريبُ finviz للعرض
DATA_RC = 7


def log(*a):
    print(*a, flush=True)


def _pct(s):
    m = re.search(r"-?\d+(?:\.\d+)?", str(s or "").replace(",", ""))
    return float(m.group()) if m else None


def week_of(day):
    """يومُ نيويورك (YYYY-MM-DD) ⟵ اثنينُ أسبوعه — مفتاحُ «صفٌّ سليمٌ واحد في الأسبوع»."""
    d = dt.date.fromisoformat(day)
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def guard(total, order, own):
    """⟵ سببُ العطل أو None: صفرُ رمز · بلا مطبوع · عددٌ لا يطابق · عمودٌ غائب · قيمةٌ خارج الفلتر (أعمدةٌ مزاحة)."""
    if not order:
        return "صفرُ رمز"
    if total is None:
        return "شكلُ الجدول: لا عددَ مطبوعًا"
    if total != len(order):
        return f"شكلُ الجدول: المطبوع {total} والمجلوب {len(order)}"
    miss = [s for s in order if any(c not in (own.get(s) or {}) for c in COLS)]
    if miss:
        return f"شكلُ الجدول: أعمدةٌ غائبة ({', '.join(COLS)}) في {len(miss)} من {len(order)}"
    bad = [s for s in order if (_pct(own[s].get("Inst Own")) is None or _pct(own[s]["Inst Own"]) < OWN_MIN - TOL
                                or _pct(own[s].get("Inst Trans")) is None or _pct(own[s]["Inst Trans"]) < TRANS_MIN - TOL)]
    if bad:
        return f"شكلُ الجدول: قيمٌ خارج الفلتر في {len(bad)} من {len(order)} ({', '.join(bad[:5])})"
    return None


def read_ledger(path=LEDGER):
    rows = []
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows


def last_ok(rows):
    return next((r for r in reversed(rows) if r.get("status") == "ok"), None)


def build_row(day, run, total, order, own, near_watch, watch_syms, prev):
    """صفٌّ سليم: القائمةُ بتاريخها ‏+ لكلّ سهم (الملكيّة · التعاملات · السعر · الفلوت · «تحت المتابعة» بجاهزيّته ونواقصه · القائمة)
    ‏+ الداخلون والخارجون عن `prev` (آخر صفٍّ سليم · وبلا سابقٍ None لا «كلُّهم داخلون»)."""
    per = {}
    for s in order:
        r, nw = own.get(s) or {}, near_watch.get(s)
        per[s] = {"inst_own": _pct(r.get("Inst Own")), "inst_trans": _pct(r.get("Inst Trans")), "price": _pct(r.get("Price")),
                  "float": r.get("Float"), "near_watch": nw is not None,
                  "readiness": (nw or {}).get("readiness"), "n_out": (nw or {}).get("n_out"), "in_list": s in watch_syms}
    ps = set(prev["tickers"]) if prev else None
    return {"status": "ok", "ny_date": day, "week_of": week_of(day), "run": run, "finviz_total": total, "n": len(order), "tickers": order,
            "rows": per, "near_watch_n": sum(1 for v in per.values() if v["near_watch"]),
            "ready_n": sum(1 for v in per.values() if v["near_watch"] and v["n_out"] == 0),
            "in_list_n": sum(1 for v in per.values() if v["in_list"]),
            "prev_week": prev["week_of"] if prev else None,
            "entered": sorted(set(order) - ps) if ps is not None else None,
            "exited": sorted(ps - set(order)) if ps is not None else None}


def fault_row(day, run, reason, total=None, n=0):
    return {"status": "fault", "ny_date": day, "week_of": week_of(day), "run": run, "reason": reason, "finviz_total": total, "n": n}


def should_write(rows, row):
    """صفٌّ سليمٌ واحد في الأسبوع: يُكتب ما لم يكن للأسبوع صفٌّ سليم · وصفُّ العطل يُكتب ولا يحجز الأسبوع."""
    return not any(r.get("status") == "ok" and r.get("week_of") == row["week_of"] for r in rows)


def append(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def ny_today(now=None):
    from zoneinfo import ZoneInfo
    return (now or dt.datetime.now(dt.timezone.utc)).astimezone(ZoneInfo("America/New_York")).date().isoformat()


def run(write, ledger=LEDGER, fetch=None, nw_path=None, wl_path=None, now=None):
    if fetch is None:
        sys.path.insert(0, HERE)
        import inst as I
        fetch = lambda: I.fetch_screen(VIEW)
    day, rid = ny_today(now), os.environ.get("GITHUB_RUN_ID")
    rows = read_ledger(ledger)
    got = fetch()
    if got is None:
        row = fault_row(day, rid, "تعذّر جلبُ finviz")
    else:
        total, order, own = got
        why = guard(total, order, own)
        if why:
            row = fault_row(day, rid, why, total, len(order))
        else:
            nw = json.load(open(nw_path or os.path.join(ROOT, "near_watch.json"), encoding="utf-8"))
            wl = json.load(open(wl_path or os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8"))
            row = build_row(day, rid, total, order, own, nw, {s.get("symbol") for s in wl.get("stocks") or []}, last_ok(rows))
    log("=" * 70)
    if row["status"] == "ok":
        log(f"🏛️🗓️ حصادُ فلتر المؤسسات · {day} (أسبوع {row['week_of']}) · {row['n']} سهمًا · في «تحت المتابعة» {row['near_watch_n']} "
            f"(صفرُ نواقص {row['ready_n']}) · في القائمة {row['in_list_n']}")
        log(f"   الداخلون عن أسبوع {row['prev_week']}: {row['entered']} · الخارجون: {row['exited']}")
        for s in row["tickers"]:
            v = row["rows"][s]
            log(f"   {s}: الملكيّة {v['inst_own']}% · التعاملات {v['inst_trans']}% · السعر {v['price']} · "
                + (f"تحت المتابعة · الجاهزيّة {v['readiness']} · النواقص {v['n_out']}" if v["near_watch"] else "خارج «تحت المتابعة»")
                + (" · في القائمة" if v["in_list"] else ""))
    else:
        log(f"⛔ عطل · {day} · {row['reason']} — يُكتب صفُّ عطلٍ لا لقطةٌ فارغة")
    if not write:
        log("🧪 تشغيلةٌ جافّة (write=0) — لا كتابة")
    elif should_write(rows, row):
        append(ledger, row)
        log(f"💾 أُلحق صفٌّ ({row['status']}) بـ{os.path.relpath(ledger, ROOT)}")
    else:
        log(f"⏭️ للأسبوع {row['week_of']} صفٌّ سليمٌ سلفًا — لا تكرار")
    print("INST_WEEKLY_JSON " + json.dumps(row, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if row["status"] == "ok" else DATA_RC


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", default=os.environ.get("INST_H_WRITE", "0"))
    a = ap.parse_args(argv)
    return run(a.write == "1")


if __name__ == "__main__":
    sys.exit(main())
