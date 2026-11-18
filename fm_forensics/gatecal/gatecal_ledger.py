#!/usr/bin/env python3
"""📏 `T-GATECAL` — الأداتان 5 و6 من سجلّات البوت نفسِها (قراءةٌ فقط · بلا شبكة · لا تلغرام · لا إنتاج).

- `envelope`  (الملحق 5): صيّادُ الغلاف مقابل لوحة الشاهد — **وصفٌ فقط** (محورُ الظرف مُغلَق).
- `presession` (الملحق 6): أرضيّةُ القراءة المتطرّفة وأرضيّةُ قيمة التداول — منحنى شرطٍ واحد على حسم الأداة نفسِها.

    python fm_forensics/gatecal/gatecal_ledger.py count --tool envelope|presession
    python fm_forensics/gatecal/gatecal_ledger.py curve --tool envelope|presession

خروج 11 إن لم يطابق العقدُ أو الملحقُ بصمتَه · 5 إن خلا السجلّ.
"""
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import gatecal as G  # noqa: E402

SEED, BOOT = G.SEED, G.BOOT
RC_OK, RC_POP, RC_CONTRACT = 0, 5, 11
ADDENDA = {
    "envelope": ("T_GATECAL_A5_envelope.md", "832bad0f5040848b87dd3fe350d18860268297a0c98cb72034484da92a6fdbe2"),
    "presession": ("T_GATECAL_A6_presession.md", "f5a001a5d667f26170caed480f7f7d3d9ce8e050eb6cfa84635b7d52d51de3bd"),
}
HUNTER_LEDGER = os.path.join(ROOT, "hunter_ledger.jsonl")
PRE_LEDGER = os.path.join(ROOT, "presession_ledger.jsonl")
PRE_OUTCOMES = os.path.join(ROOT, "presession_outcomes.jsonl")
# الملحق 6 §② — الحاليُّ يُقرأ من الأداة الحيّة وقتَ النداء (`ps_current`) ويجب أن يكون في السلّم
PS_FLOOR_LADDER = [None, 0.50, 0.60, 0.69903, 0.80, 1.00]
PS_USD_LADDER = [100_000.0, 250_000.0, 500_000.0, 1_000_000.0]
PS_SUFF = {"loose_names": 100, "loose_hits": 30, "cur_hits": 20}


def log(m=""):
    print(m, flush=True)


def contract_ok(tool):
    try:
        f, sha = ADDENDA[tool]
        return G.sha_of(G.CONTRACT) == G.CONTRACT_SHA and G.sha_of(os.path.join(HERE, f)) == sha
    except (OSError, KeyError):
        return False


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except ValueError:
                        continue
    except OSError:
        pass
    return out


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# ══ الأداة 5 — صيّاد الغلاف (وصف) ═════════════════════════════════════════════════════════════════════
def env_rows(rows):
    """المحسومُ من الصيّاد والشاهد على الجلسات المشتركة وحدَها: {جلسة: {"e": [صفّ], "c": [صفّ]}}."""
    by = {}
    for r in rows or []:
        h = r.get("hunter")
        if h not in ("envelope", "control") or not (r.get("outcome") or {}).get("resolved"):
            continue
        by.setdefault(str(r.get("session"))[:10], {"e": [], "c": []})["e" if h == "envelope" else "c"].append(r)
    return {s: d for s, d in by.items() if d["e"] and d["c"]}


def _rate(rs, key):
    return sum(1 for r in rs if (r.get("outcome") or {}).get(key)) / len(rs) if rs else 0.0


def env_diff(common, key, seed=SEED, B=BOOT):
    """الفرقُ (الصيّاد − الشاهد) في معدّل `key` مجمَّعًا على الجلسات المشتركة · وفاصلُه ببوتستراب عنقوديٍّ بالجلسة."""
    ss = sorted(common)
    if not ss:
        return None

    def d(sample):
        e = [r for s in sample for r in common[s]["e"]]
        c = [r for s in sample for r in common[s]["c"]]
        return _rate(e, key) - _rate(c, key)
    rng = random.Random(seed)
    bs = sorted(d([ss[rng.randrange(len(ss))] for _ in ss]) for _ in range(B))
    return d(ss), bs[int(0.025 * B)], bs[min(B - 1, int(0.975 * B))]


def mode_envelope(curve):
    import hunter_ledger as LEDGER
    rows = read_jsonl(HUNTER_LEDGER)
    summ = LEDGER.summary([r for r in rows if r.get("hunter") in ("envelope", "control")])
    if not (summ.get("envelope") or {}).get("n"):
        log(f"⛔ لا صفوفَ لصيّاد الغلاف — خروج {RC_POP}")
        return RC_POP
    log("═══ 📏 T-GATECAL الأداة 5 — صيّاد الغلاف (وصفٌ فقط · محورُ الظرف مُغلَق) ═══")
    log(f"   {'':<10}{'مرصود':>8}{'محسوم':>8}{'hit50':>8}{'hit100':>8}")
    for name in ("envelope", "control"):
        d = summ.get(name) or {"n": 0, "resolved": 0, "hit50": 0, "hit100": 0, "gains": []}
        log(f"   {name:<10}{d['n']:>8}{d['resolved']:>8}{d['hit50']:>8}{d['hit100']:>8}")
    common = env_rows(rows)
    log(f"   جلساتٌ مشتركةٌ محسومة: {len(common)}")
    if not curve:
        log("   ⟵ العدُّ وحدَه (count) · والمعدّلاتُ والفرقُ في curve")
        return RC_OK
    for name in ("envelope", "control"):
        d = summ.get(name) or {}
        n = d.get("resolved", 0)
        for key in ("hit50", "hit100"):
            lo, hi = wilson(d.get(key, 0), n)
            log(f"   {name:<10}{key:<8}{(d.get(key, 0) / n * 100 if n else 0):6.1f}%  [{lo * 100:5.1f}% · {hi * 100:5.1f}%]")
        if d.get("gains"):
            log(f"   {name:<10}وسيطُ أعلى ربح {statistics.median(d['gains']):.1f}%")
    for key in ("hit50", "hit100"):
        r = env_diff(common, key)
        if r:
            log(f"   الفرقُ (الصيّاد − الشاهد) في {key} على المشتركة: {r[0] * 100:+.1f} نقطة [{r[1] * 100:+.1f} · {r[2] * 100:+.1f}]")
    e, c = summ.get("envelope") or {}, summ.get("control") or {}
    e_lo = wilson(e.get("hit100", 0), e.get("resolved", 0))[0]
    c_hi = wilson(c.get("hit100", 0), c.get("resolved", 0))[1]
    log(f"   التنبّؤ E1 (لا فصل): {'صدق' if e_lo <= c_hi else 'كذب'} (أدنى الصيّاد {e_lo * 100:.1f}% · أعلى الشاهد {c_hi * 100:.1f}%)")
    log("⚖️ «وصفٌ لا حكم» بنصّ الملحق 5 §③ — لا تغييرَ يُقترح على صيّاد الغلاف.")
    return RC_OK


# ══ الأداة 6 — أرضيّةُ ما قبل الجلسة ════════════════════════════════════════════════════════════════
def ps_current():
    import presession_feats as PF
    import presession_radar as PR
    return {"floor": PF.FLOOR_BY_SLOT.get("PM"), "usd": float(PR.MIN_DAY_USD), "cap": int(PR.PREFILTER_CAP), "topk": int(PF.TOPK)}


def ps_join(ledger, outcomes, drop=None):
    """صفوفُ الحسم مضمومًا إليها `usd_day` من سجلّ القرار بالمفتاح (يوم·جلسة·رمز) · والمستبعَدُ عند الحصّاد يُستبعد."""
    usd = {}
    for r in ledger or []:
        usd["{}|{}|{}".format(r.get("day"), r.get("sess"), str(r.get("sym") or "").upper())] = r.get("usd_day")
    out = []
    for o in outcomes or []:
        if o.get("sess") not in ("PM", "AH") or (drop and drop(o)):
            continue
        k = o.get("key") or "{}|{}|{}".format(o.get("day"), o.get("sess"), str(o.get("sym") or "").upper())
        out.append(dict(o, usd_day=usd.get(k)))
    return out


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if v != v else v


def ps_sent(r, floor=None, usd=None):
    """هل يُرسَل الصفُّ عند (أرضيّةِ قراءةٍ · أرضيّةِ قيمة)؟ — `in_top` ثمّ القيمةُ ≥ الأرضيّة (المعدومُ يسقط كما في `floor_ok`)."""
    if not r.get("in_top"):
        return False
    if floor is not None and r.get("sess") == "PM":
        v = _num(r.get("rank_val"))
        if v is None or v < floor:
            return False
    if usd is not None:
        u = _num(r.get("usd_day"))
        if u is None or u < usd:
            return False
    return True


def ps_point(rows, floor=None, usd=None):
    sel = [r for r in rows if ps_sent(r, floor, usd)]
    days = {r.get("day") for r in rows}
    hits = sum(int(r.get("hit") or 0) for r in sel)
    lo, hi = wilson(hits, len(sel))
    return {"names": len(sel), "days": len(days), "per_day": (len(sel) / len(days)) if days else 0.0, "hits": hits,
            "prec": (hits / len(sel)) if sel else 0.0, "lo": lo, "hi": hi, "full_hits": sum(int(r.get("full_hit") or 0) for r in sel)}


def ps_sufficient(loose, cur):
    return (loose["names"] >= PS_SUFF["loose_names"] and loose["hits"] >= PS_SUFF["loose_hits"] and cur["hits"] >= PS_SUFF["cur_hits"])


def ps_rank_buckets(rows, topk=10):
    b = {"top": 0, "mid": 0, "tail": 0}
    for r in rows:
        if int(r.get("hit") or 0):
            k = _num(r.get("rank"))
            b["top" if (k is not None and k <= topk) else "mid" if (k is not None and k <= 30) else "tail"] += 1
    return b


def _ps_line(lbl, p, cur=False, top_hits=None):
    cap = f" · التقط {p['hits']} من {top_hits}" if top_hits is not None else ""
    return (f"   {lbl:>10}{' ◀' if cur else '  '} أسماء {p['names']:>4} · {p['per_day']:4.1f}/يوم · إصابات {p['hits']:>3} · دقّة {p['prec'] * 100:5.1f}% "
            f"[{p['lo'] * 100:4.1f} · {p['hi'] * 100:4.1f}] · حتى الإغلاق {p['full_hits']}{cap}")


def mode_presession(curve):
    import presession_digest as PD
    cur = ps_current()
    if cur["floor"] not in PS_FLOOR_LADDER or cur["usd"] not in PS_USD_LADDER:
        log(f"⛔ الحاليُّ ({cur}) ليس في سلّم الملحق 6 — خروج {RC_CONTRACT}")
        return RC_CONTRACT
    rows = ps_join(read_jsonl(PRE_LEDGER), read_jsonl(PRE_OUTCOMES), drop=PD.tv_backfill)
    if not rows:
        log(f"⛔ لا صفوفَ محسومة — خروج {RC_POP}")
        return RC_POP
    log("═══ 📏 T-GATECAL الأداة 6 — أرضيّةُ ملخّص ما قبل الجلسة (سجلُّ البوت · الإصابةُ = +80% في نافذة الجلسة) ═══")
    verdicts = {}
    for sess in ("PM", "AH"):
        rs = [r for r in rows if r.get("sess") == sess]
        days = sorted({r.get("day") for r in rs})
        top = [r for r in rs if r.get("in_top")]
        log(f"【{sess}】 محسومٌ {len(rs)} في {len(days)} يومًا ({days[0] if days else '—'} … {days[-1] if days else '—'}) · داخل القائمة {len(top)} · "
            f"مُرسَلٌ فعلًا {sum(1 for r in rs if r.get('sent'))}")
        loose = ps_point(rs, None, None)
        now = ps_point(rs, cur["floor"] if sess == "PM" else None, cur["usd"])
        ok = ps_sufficient(loose, now)
        verdicts[sess] = ok
        log(f"   العدّ: الأرخى أسماء {loose['names']} إصابات {loose['hits']} · الحاليّ أسماء {now['names']} إصابات {now['hits']} "
            f"⟵ {'يكفي' if ok else '«وصف لا حكم» (دون 100 اسمًا · 30 إصابةً عند الأرخى · 20 عند الحاليّ)'}")
        if not curve:
            continue
        b = ps_rank_buckets(rs, cur["topk"])
        log(f"   توزيعُ الإصابات على الترتيب (وصف · السقف {cur['cap']}): داخل العشرة {b['top']} · 11-30 {b['mid']} · 31-{cur['cap']} {b['tail']}")
        if sess == "PM":
            log("   ── أرضيّةُ القراءة المتطرّفة (وأرضيّةُ القيمة عند الحاليّ) ──")
            for v in PS_FLOOR_LADDER:
                log(_ps_line("بلا" if v is None else f"{v:g}", ps_point(rs, v, cur["usd"]), v == cur["floor"], loose["hits"]))
        log("   ── أرضيّةُ قيمة تداول اليوم (تشديدٌ فقط · وأرضيّةُ القراءة عند الحاليّ) ──")
        for u in PS_USD_LADDER:
            log(_ps_line(f"{u / 1000:g} ألف", ps_point(rs, cur["floor"] if sess == "PM" else None, u), u == cur["usd"], loose["hits"]))
    if curve:
        pm = [r for r in rows if r.get("sess") == "PM"]
        now = ps_point(pm, cur["floor"], cur["usd"])
        hi = ps_point(pm, 0.80, cur["usd"])
        allhits = sum(int(r.get("hit") or 0) for r in pm)
        log(f"   التنبّؤ S1 (إصاباتُ PM عند الحاليّ دون 20): {'صدق' if now['hits'] < 20 else 'كذب'} ({now['hits']})")
        log(f"   التنبّؤ S2 (0.80 لا تفصل دقّتَها عن الحاليّ): {'صدق' if hi['lo'] <= now['hi'] else 'كذب'}")
        log(f"   التنبّؤ S3 (أغلبُ إصابات PM خارج المُرسَل): {'صدق' if now['hits'] * 2 < allhits else 'كذب'} ({now['hits']} من {allhits})")
    if any(verdicts.values()):
        log("⚖️ العدُّ يكفي في جلسةٍ ⟵ يتوقّف المسارُ قبل أيّ اقتراح: يلزمه الملحق 6-ب (ساقُ الربح · اختيارٌ ثمّ تأكيدٌ مرّة).")
    else:
        log("⚖️ «وصف لا حكم» في الجلستين — المنحنى وصفٌ ولا تغييرَ يُقترح.")
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else ""
    tool = argv[argv.index("--tool") + 1] if "--tool" in argv and argv.index("--tool") + 1 < len(argv) else ""
    if tool not in ADDENDA or mode not in ("count", "curve"):
        log("⛔ count | curve --tool " + " | ".join(ADDENDA))
        return 1
    if not contract_ok(tool):
        log(f"⛔ العقدُ أو ملحقُ الأداة لا يطابق بصمتَه — خروج {RC_CONTRACT} قبل أيّ قراءة")
        return RC_CONTRACT
    return (mode_envelope if tool == "envelope" else mode_presession)(mode == "curve")


if __name__ == "__main__":
    sys.exit(main())
