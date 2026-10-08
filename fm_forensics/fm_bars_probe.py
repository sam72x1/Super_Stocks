"""🔎📺 FM-PROBE — جلبُ شموع TradingView لتحليلٍ جنائيٍّ قراءةً فقط (مهمّة «FABLE 5 FORENSIC MASTER MISSION» 2026-10-08).

يأخذ الشموع اليوميّة (الجلسة النظاميّة · مسوّاةً بالتقسيم · شكلُ `download_history` حرفًا عبر `Super_stock.tv_download`)
لمجموعةٍ من الرموز، وشموعَ الساعة الممتدّة لرموز المرساة الأربعة (`tv_hour_fetcher`)، ويكتبها مضغوطةً في
`fm_forensics/data/`. **لا تلغرام · لا حالةَ إنتاج · لا جذور.** الرموزُ من ملفّات الحالة في المستودع وحدَها (لا تُغرَس بالاسم إلّا
المراساةُ الأربعة بوصفها رموزَ تحقيقٍ لا منطقَ إنتاج)."""
import gzip
import json
import os
import sys
import datetime as dt

os.environ.setdefault("FAISAL_ONLY", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Super_stock as S          # noqa: E402

ANCHORS = ["DKI", "SXTC", "HUBC", "CRE"]
START = os.environ.get("FM_START") or "2025-01-01"


def symbols():
    syms = set(ANCHORS)
    try:
        wl = json.load(open("weekly_watchlist.json"))
        for e in wl.get("explosions") or []:
            if (e.get("gain") or 0) >= 100:
                syms.add(e["symbol"])
        for s in wl.get("stocks") or []:
            syms.add(s["symbol"])
        for s in wl.get("pullback") or []:
            syms.add(s.get("symbol"))
    except Exception as e:                                        # noqa: BLE001
        print("⚠️ weekly_watchlist:", e)
    try:
        extra = os.environ.get("FM_EXTRA_SYMS_FILE")
        if extra and os.path.exists(extra):
            syms.update(x.strip().upper() for x in open(extra).read().split() if x.strip())
    except Exception as e:                                        # noqa: BLE001
        print("⚠️ extra:", e)
    try:
        d = json.load(open("faisal_method_v4/results/cases_v4.json"))
        for c in (d.get("cases") if isinstance(d, dict) else d) or []:
            for t in c.get("tickers") or []:
                t = str(t).strip().upper().rstrip("?")
                if t.isalpha():
                    syms.add(t)
    except Exception as e:                                        # noqa: BLE001
        print("⚠️ cases_v4:", e)
    syms.discard(None)
    return sorted(s for s in syms if s)


def main():
    syms = symbols()
    print(f"رموز: {len(syms)} · start={START}")
    frames, rep = S.tv_download(syms, START)
    print("📺", S._tv_bars_line(rep))
    out = {"meta": {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "start": START,
                    "asked": len(syms), "got": len(frames), "rep": {k: v for k, v in rep.items() if k != "gate"},
                    "source": "tradingview · regular session · adjustment=splits"},
           "daily": {}, "hourly": {}}
    for s, df in frames.items():
        out["daily"][s] = [[i.strftime("%Y-%m-%d"), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume)]
                           for i, r in df.iterrows()]
    try:
        hf = S.tv_hour_fetcher(ANCHORS)
        for s in ANCHORS:
            h = hf(s, "2025-01-01", "2030-01-01")
            out["hourly"][s] = h
            print(f"⏱️ {s}: شموع ساعة {len(h) if h is not None else None}")
    except Exception as e:                                        # noqa: BLE001
        print("⚠️ hourly:", type(e).__name__, e)
    os.makedirs("fm_forensics/data", exist_ok=True)
    path = f"fm_forensics/data/bars_{dt.date.today().isoformat()}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"💾 {path} · {os.path.getsize(path)} بايت · daily {len(out['daily'])} · hourly {len(out['hourly'])}")
    for s in ANCHORS:
        b = out["daily"].get(s)
        print(s, (len(b), b[0][0], b[-1]) if b else "— تعذّر")


if __name__ == "__main__":
    main()
