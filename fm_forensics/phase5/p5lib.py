"""🔬 PHASE 5 — مكتبةُ البحث (قراءةٌ فقط · الإنتاجُ وV4 بلا تعديل): معلوماتٌ غيرُ شمعيّة × اختيارُ فيصل.
تعيد استعمالَ مكتبتَي المرحلتين 3 و4 بالاسم (التقويم · الشموع < T · الأهليّة) ولا تعرّف حدثًا جديدًا.
وحدةُ التحليل: الورقةُ × حلقةُ القرار (`DECISION_EPISODE_ID`) · والعنقدةُ على الورقة."""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.dirname(HERE)
P3 = os.path.join(FM, "phase3")
P4 = os.path.join(FM, "phase4")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, P4)
sys.path.insert(0, P3)
import p4lib as Q                        # noqa: E402
import p3lib as L                        # noqa: E402

S = L.S
ANCHORS = list(Q.ANCHORS)
EPISODE_GAP = 30                         # جلسات: وحداتُ فيصل المتباعدةُ أكثرَ منها = حلقةُ قرارٍ جديدة
REPO = os.path.dirname(FM)
SCRATCH = os.environ.get("P5_SCRATCH", os.path.join(HERE, "out"))


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, keys=None):
    """كتابةٌ باتّحاد المفاتيح (درسُ المرحلة 4: الصفُّ الأوّل لا يملك كلَّ الأعمدة)."""
    if keys is None:
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in keys})


def p4(name):
    return read_csv(os.path.join(P4, name))


def timeline_all():
    """سجلُّ المرحلة 3 كاملًا (306 ملاحظة) — بما فيها الطرفُ الثالث وMENTION/EXIT/UNKNOWN."""
    return read_csv(os.path.join(P3, "FAISAL_TIMELINE.csv"))


def faisal_units():
    """وحداتُ فيصل المؤرَّخة بصنفٍ من الأربعة (المرحلة 4 بالاسم)."""
    return Q.faisal_timeline()


def episodes(units=None):
    """حلقاتُ القرار: لكلّ ورقةٍ تُرتَّب الوحداتُ بالجلسة، وفجوةٌ > EPISODE_GAP جلسةً تفتح حلقةً جديدة.
    يعيد قائمةَ قواميس: ticker · episode_id · episode_no · start (أوّلُ جلسة) · units (قائمة) · first_state_class · tiers."""
    units = units if units is not None else faisal_units()
    by = {}
    for u in units:
        by.setdefault(u["ticker"], []).append(u)
    out = []
    for t, us in sorted(by.items()):
        us = sorted(us, key=lambda r: (r["session"], r["evidence_id"]))
        cur = None
        n = 0
        last_idx = None
        for u in us:
            ci = L.cal_index(u["session"])
            if cur is None or (ci is not None and last_idx is not None and ci - last_idx > EPISODE_GAP):
                n += 1
                cur = dict(ticker=t, episode_id=f"{t}_E{n}", episode_no=n, start=u["session"], units=[],
                           first_state_class=u["state"], first_evidence_class=u["evidence_class"], set=u["set"])
                out.append(cur)
            cur["units"].append(u)
            last_idx = ci if ci is not None else last_idx
        pass
    for e in out:
        e["end"] = max(u["session"] for u in e["units"])
        e["n_units"] = len(e["units"])
        e["states"] = sorted({u["state"] for u in e["units"]})
        e["highest_tier"] = max(e["states"], key=lambda s: ("WATCH", "FOCUS", "READY", "ENTRY").index(s))
        e["date_ambiguous"] = int(any(u["date_ambiguous"] for u in e["units"]))
    return out


def splits_yahoo():
    """تقسيماتُ ياهو من لقطة المرحلة 2 (`bars_2026-10-08.json.gz`) — تواريخُ تاريخيّةٌ بعتادٍ حاليّ (vintage = 2026-10-08)."""
    d = L.load()
    return d.get("splits") or {}


def ctb_log():
    """حصادُ المتاح/الرسوم المؤرَّخ (`ctb_log.jsonl`): لقطاتٌ يوميّةٌ من ChartExchange منذ 2026-07-30 — مصدرُ الاقتراض الوحيد بطابعٍ زمنيّ."""
    rows = []
    p = os.path.join(REPO, "ctb_log.jsonl")
    if not os.path.exists(p):
        return rows
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
    return rows


def scratch_json(name):
    p = os.path.join(SCRATCH, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def wilson(k, n, z=1.96):
    return Q.wilson(k, n, z)


def q(x, nd=3):
    return Q.q(x, nd)
