# -*- coding: utf-8 -*-
"""📺 جلبُ شموع TradingView لرموز اختبار الكون (`data/universe_manifest.json`) ⟵ `data/universe_bars.json.gz` — يعمل على رنر GitHub
(TradingView محجوبٌ من بيئة الجلسة). قراءةٌ فقط · لا تلغرام · لا حالةَ إنتاج. الشكلُ = شكلُ `fm_forensics/data/bars_*.json.gz`."""
import datetime as dt
import gzip
import json
import os
import sys

os.environ.setdefault("FAISAL_ONLY", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import Super_stock as S          # noqa: E402

START = os.environ.get("FE_START") or "2025-01-01"


def main():
    man = json.load(open(os.path.join(HERE, "data", "universe_manifest.json"), encoding="utf-8"))
    syms = list(man["symbols"])
    print(f"رموز: {len(syms)} · start={START}")
    frames, rep = S.tv_download(syms, START)
    print("📺", S._tv_bars_line(rep))
    out = {"meta": {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "start": START, "asked": len(syms), "got": len(frames),
                    "rep": {k: v for k, v in rep.items() if k != "gate"}, "source": "tradingview · regular session · adjustment=splits",
                    "manifest_dates": len(man["dates"])}, "daily": {}, "splits": {}}
    for s, df in frames.items():
        out["daily"][s] = [[i.strftime("%Y-%m-%d"), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume)] for i, r in df.iterrows()]
    t0 = dt.datetime.now(); budget = float(os.environ.get("FE_SPLIT_BUDGET_S") or 1500); n_ok = n_fail = 0
    for s in syms:
        if (dt.datetime.now() - t0).total_seconds() > budget:
            print(f"⏱️ ميزانيةُ التقسيمات انتهت عند {n_ok + n_fail} من {len(syms)} — الباقي مجهول (None)")
            break
        try:
            sp = S._fetch_splits_dq(s)
            if sp is None:
                out["splits"][s] = None; n_fail += 1
            elif isinstance(sp, list):
                out["splits"][s] = [[str(d)[:10], float(r)] for d, r in sp]; n_ok += 1
            else:
                out["splits"][s] = [[str(d)[:10], float(r)] for d, r in sp.items()]; n_ok += 1
        except Exception:                                         # noqa: BLE001
            out["splits"][s] = None; n_fail += 1
    print(f"🧾 تقسيمات: معلوم {n_ok} · مجهول {n_fail} · لم يُسأل {len(syms) - n_ok - n_fail}")
    path = os.path.join(HERE, "data", "universe_bars.json.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"💾 {path} · {os.path.getsize(path)} بايت · daily {len(out['daily'])}")


if __name__ == "__main__":
    main()
