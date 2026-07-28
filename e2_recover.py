#!/usr/bin/env python3
"""🔬♻️ استرجاع جلسات E2 الضائعة من artifacts التشغيلات السابقة.

**الخلفية (عطل حقيقي، 2026-07-28):** خطوة الدفع في `ignition.yml` كانت **عارية بلا
rebase**، والجلسة تمتدّ ~4.5 ساعة فيتحرّك `main` أثناءها ⇒ `! [rejected] (fetch first)`
⇒ **ملخّص كل جلسة يضيع** رغم نجاح المقطعين والدمج. جلسة واحدة فقط (2026-07-24) نجح
دفعها من عشر. البيانات نفسها **لم تضع**: كل تشغيلة ترفع `ign-assembled-<run_id>`
(احتفاظ 90 يومًا) قبل الدفع. هذه الأداة تُعيدها إلى الريبو.

الاستعمال (داخل workflow بعد `gh run download`):
    python3 e2_recover.py <مجلّد التنزيلات>

**استرجاع/دمج فقط:** لا يمسّ الرادار ولا الفرز ولا أي جذر، ولا يخترع بيانات — ينسخ ما
رُفِع وقتها حرفيًّا. عند تعارض تاريخين من تشغيلتين تفوز **الأكثر دورات مكتملة** (حتميّ)
ويُطبَع التعارض صراحةً.
"""
import glob
import json
import os
import shutil
import sys

INDEX = "ignition_e2_session_index.json"
ROOT = "e2_measurement"
IDX_KEYS = ("n_delivered", "n_emitted", "n_raw_candidates", "n_symbols", "termination")


def _read_json(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def _session_dirs(download_root):
    """كل مجلّدات الجلسات داخل التنزيلات — بأي عمق (لا نفترض شكل الأرشيف)."""
    pats = (os.path.join(download_root, "**", ROOT, "session_*"),
            os.path.join(download_root, "**", "session_*"))
    out = {}
    for pat in pats:
        for d in glob.glob(pat, recursive=True):
            if os.path.isdir(d) and os.path.basename(d).startswith("session_"):
                out.setdefault(os.path.realpath(d), os.path.basename(d)[len("session_"):])
    return out


def _summary_of(sdir):
    """ملخّص الجلسة: من summary.json داخلها، وإلا من ignition_e2_summary.json المجاور."""
    s = _read_json(os.path.join(sdir, "summary.json"))
    if s:
        return s
    up = os.path.dirname(os.path.dirname(sdir))       # …/<run>/  (فوق e2_measurement)
    return _read_json(os.path.join(up, "ignition_e2_summary.json"))


def recover(download_root, repo_root="."):
    idx_path = os.path.join(repo_root, INDEX)
    idx = _read_json(idx_path)
    before = set(idx)
    best, conflicts, no_summary = {}, [], []
    for sdir, date in sorted(_session_dirs(download_root).items()):
        summ = _summary_of(sdir)
        if not summ or summ.get("session_date") not in (None, date):
            # ملخّص غائب أو لتاريخ آخر ⇒ لا نخمّن
            if not summ:
                no_summary.append((date, sdir))
                continue
        loops = int(summ.get("loops_completed") or 0)
        prev = best.get(date)
        if prev and prev[0] != loops:
            conflicts.append((date, prev[0], loops))
        if not prev or loops > prev[0]:
            best[date] = (loops, sdir, summ)

    copied, merged = [], []
    for date, (loops, sdir, summ) in sorted(best.items()):
        dst = os.path.join(repo_root, ROOT, "session_%s" % date)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(sdir, dst)
            copied.append(date)
        entry = {k: summ.get(k) for k in IDX_KEYS if summ.get(k) is not None}
        if date not in idx:
            merged.append(date)
        idx[date] = {**idx.get(date, {}), **entry}

    with open(idx_path, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(idx.items())), fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("♻️ استرجاع جلسات E2")
    print("   كانت بالفهرس: %d ⇒ صارت: %d (جديدة: %d)"
          % (len(before), len(idx), len(merged)))
    print("   جلسات جديدة: " + (", ".join(merged) or "لا شيء"))
    print("   مجلّدات خام نُسخت: " + (", ".join(copied) or "لا شيء"))
    if conflicts:
        print("   ⚠️ تعارض تاريخ من تشغيلتين (فازت الأكثر دورات): "
              + " · ".join("%s (%d مقابل %d)" % c for c in conflicts))
    if no_summary:
        print("   ⚠️ بلا ملخّص (تُخطَّت، لا تخمين): "
              + ", ".join(d for d, _ in no_summary))
    # صدق العدّ: الفهرس لا يُثبت الاكتمال — المدقّق الصارم وحده يفعل.
    normal = [d for d, v in idx.items() if v.get("termination") == "normal"]
    print("   🧮 بالفهرس %d جلسة · منها %d بإنهاء طبيعي." % (len(idx), len(normal)))
    print("   ⚠️ الفهرس عدّاد لا شهادة اكتمال — شغّل "
          "`ignition_e2_analyze.py e2_measurement --strict` للحكم.")
    return {"index": len(idx), "new": merged, "copied": copied,
            "conflicts": conflicts, "no_summary": [d for d, _ in no_summary]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("الاستعمال: e2_recover.py <مجلّد تنزيلات artifacts>")
    recover(sys.argv[1])
