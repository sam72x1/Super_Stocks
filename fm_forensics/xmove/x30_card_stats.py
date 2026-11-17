"""📊📣 «مثل هذا الإشعار» لرسالة «تحرّك 30%» — أمرُ المالك 2026-11-17 (استثناءٌ صريح · **عرضٌ لا قياس**):
«انقل سطر «📊 مثل هذا الإشعار» إلى رسالة «تحرّك 30%»، بنفس صيغته، محسوبًا على إشعارات «تحرّك 30%» من بيانات T-XMOVE — ومن سعر
الإشعار لا من إغلاق الأمس. خلف مفتاح.»

المادّة: سجلّاتُ `T-XMOVE` بحرفها (أجزاءُ التشغيلة `43916334799` · `xmove.py --mode chunk`) ⟵ كلُّ إطلاقٍ `X30` غيرِ يومِ تقسيم في يومٍ من
`GOLD_FROM` فصاعدًا (أوّلُ صفوف السجلّ · فيصير العاديُّ و🥇 مصنَّفَين على الأيّام نفسِها) ⟵ شموعُ دقيقة اليوم (`tier_fwd_report.fetch_day` ·
كما في T-XMOVE) ⟵ النتيجةُ بدالّة `opsig.outcome` **بالاسم** من **سعر الإشعار** (إغلاقُ دقيقة الإطلاق = السعرُ في الرسالة) على الشموع التي تبدأ
**بعد** دقيقة الإطلاق ⟵ الأرقامُ الأربعة بدالّة `opsig.card_stats` بالاسم (وسيطُ أعلى ربح · ‏+20% · الكارثيّ · الوسيطُ بوقف −10%).
🥇 = للسهم صفٌّ قويٌّ في السجلّ (قاعدةُ `xmove.gold_map` بالاسم) **دقيقتُه لا تتأخّر عن دقيقة الإطلاق** (كما يَسِمه العاملُ الحيّ `upto_ms`).
الأوضاع: `run --dir <مجلّدُ الأجزاء>` (يلزم POLYGON_API_KEY) ⟵ `x30_card_outcomes.jsonl` و`x30_card_stats.json` · و`stats` بلا شبكة يعيد الأرقام
من الملفّ الأوّل. لا تلغرام · لا حالةَ إنتاج · لا حكمَ ولا عتبة.
"""
import glob
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
OUTCOMES = os.path.join(ROOT, "x30_card_outcomes.jsonl")
STATS = os.path.join(ROOT, "x30_card_stats.json")
SRC_RUN = 43916334799
KEY = "X30"
MIN_MS = 60_000
DEFS = ("الدخولُ سعرُ الإشعار (إغلاقُ دقيقة الإطلاق) · أعلى ربح = أعلى قمّةٍ بعد دقيقة الإطلاق بقيّةَ اليوم · +20% من أعلى ربح · "
        "كارثيّ = قاعٌ 20% تحت الدخول خلال 30 دقيقة · بوقف −10% = الخروجُ عند −10% إن لُمس وإلّا آخرُ شمعة · "
        "🥇 = صفٌّ قويٌّ في السجلّ لا يتأخّر عن الإطلاق · بلا أيّام التقسيم")


def log(m=""):
    print(m, flush=True)


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _xm():
    return _load("xmove_x30cs", "fm_forensics/xmove/xmove.py")


def _op():
    return _load("opsig_x30cs", "fm_forensics/opsig/opsig.py")


def fires_of(recs, gold_from, key=KEY):
    """(نقيّة) إطلاقاتُ `key` غيرُ يومِ التقسيم في أيّامٍ من `gold_from` فصاعدًا ⟵ [{d، sym، m، px، gold}] مرتّبة ·
    و`gold` = لـ(اليوم، الرمز) دقيقةُ 🥇 لا تتأخّر عن دقيقة الإطلاق."""
    out = []
    for r in recs or ():
        f = (r.get("fires") or {}).get(key)
        if not f or r.get("split") or str(r.get("d") or "") < gold_from:
            continue
        try:
            m, px = int(f[0]), float(f[1])
        except (TypeError, ValueError, IndexError):
            continue
        g = (r.get("fires") or {}).get("gold")
        gold = bool(g) and g[0] is not None and int(g[0]) <= m
        out.append({"d": str(r["d"]), "sym": str(r["sym"]).upper(), "m": m, "px": px, "gold": gold})
    return sorted(out, key=lambda x: (x["d"], x["sym"]))


def outcome_at(bars, day, m, px, ny_parts, outcome):
    """(نقيّة) ⟵ (النتيجة، إغلاقُ شمعة الإطلاق) · النتيجةُ `outcome` من **سعر الإشعار** على الشموع التي تبدأ بعد دقيقة الإطلاق ·
    None إن غابت شمعةُ الإطلاق (لا تُخترَع دقيقة)."""
    fb = next((b for b in bars or () if ny_parts(b[0]) == (day, int(m))), None)
    if fb is None or not px or px <= 0:
        return None, None
    return outcome(bars, int(fb[0]) + MIN_MS, float(px)), float(fb[4])


def publish(st, n_fires, asof, src_run=SRC_RUN):
    keep = ("n", "maxg_med", "p20", "cat", "s10_med")
    return {"asof": asof, "source": f"T-XMOVE (التشغيلة {src_run}) · إطلاقاتُ «تحرّك 30%» {n_fires} · من سعر الإشعار",
            "normal": {k: (st.get("normal") or {}).get(k) for k in keep},
            "gold": {k: (st.get("gold") or {}).get(k) for k in keep}, "defs": DEFS}


def stats_of(rows, card_stats):
    ok = [r for r in rows if r.get("out")]
    return {"normal": card_stats([r for r in ok if not r.get("gold")]), "gold": card_stats([r for r in ok if r.get("gold")])}


def _write_stats(rows, asof):
    OP = _op()
    st = stats_of(rows, OP.card_stats)
    pub = publish(st, sum(1 for r in rows if r.get("out")), asof)
    with open(STATS, "w", encoding="utf-8") as fh:
        json.dump(pub, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    log(f"📊 {pub['source']}")
    for k in ("normal", "gold"):
        log(f"   {k}: {pub[k]}")
    return pub


def mode_run(d_in, key):
    from concurrent.futures import ThreadPoolExecutor
    from tier_fwd_report import fetch_day
    XM, OP = _xm(), _op()
    paths = sorted(glob.glob(os.path.join(d_in, "**", "xmove_part_*.json"), recursive=True))
    recs = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            recs.extend(json.load(fh).get("recs") or [])
    fires = fires_of(recs, XM.GOLD_FROM)
    days = sorted({f["d"] for f in fires})
    log(f"📊 الأجزاء {len(paths)} · السجلّات {len(recs)} · إطلاقاتُ X30 (بلا تقسيم · من {XM.GOLD_FROM}) {len(fires)} · "
        f"🥇 {sum(1 for f in fires if f['gold'])} · أيّام {len(days)} ({days[0] if days else '—'} ⟵ {days[-1] if days else '—'})")
    if len(paths) != 6:
        log("⛔ الأجزاءُ ليست ستّة — لا كتابة")
        return 2

    def _one(f):
        try:
            res, c = outcome_at(fetch_day(f["sym"], f["d"], key), f["d"], f["m"], f["px"], XM.ny_parts, OP.outcome)
        except Exception as e:                                   # noqa: BLE001
            return dict(f, err=type(e).__name__)
        if res is None:
            return dict(f, skip="nobar")
        return dict(f, out=res, c_fire=c)
    with ThreadPoolExecutor(XM.WORKERS) as pool:
        rows = list(pool.map(_one, fires))
    mism = sum(1 for r in rows if r.get("out") and abs(r["c_fire"] / r["px"] - 1) > 0.001)
    log(f"📥 بنتيجة {sum(1 for r in rows if r.get('out'))} · بلا شمعة إطلاق {sum(1 for r in rows if r.get('skip'))} · "
        f"خطأ {sum(1 for r in rows if r.get('err'))} · إغلاقُ الشمعة ≠ سعرِ T-XMOVE {mism}")
    with open(OUTCOMES, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if _write_stats(rows, days[-1] if days else "") else 1


def mode_stats():
    rows = []
    with open(OUTCOMES, encoding="utf-8") as fh:
        for ln in fh:
            if ln.strip():
                rows.append(json.loads(ln))
    _write_stats(rows, max((r["d"] for r in rows), default=""))
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else "stats"
    if mode == "run":
        key = (os.environ.get("POLYGON_API_KEY") or "").strip()
        if not key:
            log("⛔ بلا مفتاح Polygon — لا حساب")
            return 3
        return mode_run(argv[argv.index("--dir") + 1] if "--dir" in argv else "x30_in", key)
    return mode_stats()


if __name__ == "__main__":
    sys.exit(main())
