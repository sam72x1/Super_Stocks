"""🔬 PHASE 2 — إعادةُ تشغيل بوّابات الهُويّة (`analyze_ticker` الإنتاجيّة بلا تعديل) على شموع المِجَسّ في عوالمَ معزولة:
A      الإنتاج: شموعُ TradingView المسوّاة بالتقسيم (كما يراها البوت) · كلُّ شيءٍ كما هو.
B_PSH  استمراريّةٌ تاريخيّة فقط: مرجعُ M2 = قمّةُ ما بعد آخر تقسيمٍ عكسيّ (علمُ الباكتيست القائم `BT_SPLIT_REF_M2` + `_BT_SPLITS_CTX`) · الشموعُ نفسُها.
B_M4   استمراريّةٌ فقط: مدى القاعدة واعٍ بالتقسيم داخل النافذة (`BT_SPLIT_AWARE_M4`) · مع B_PSH.
B_RAW  استمراريّةٌ فقط: أسعارٌ خامٌّ غيرُ مسوّاة (إعادةُ ضرب الشموع قبل كلّ تقسيمٍ بنسبته) · لا علم.
B_CUT  استمراريّةٌ فقط: التاريخُ يبدأ من آخر تقسيمٍ عكسيّ (سهمٌ «جديد») · لا علم.
ID     هُويّةٌ فقط: الشموعُ نفسُها تحت رمزٍ آخر (X_<sym>) · لا تقسيمات · لا علم ⟵ يجب أن يطابق A بت-بت.
بلا نظرٍ للأمام: شموعُ ≤ (يوم السجلّ − 1) كما يرى الفرزُ الصباحيّ. قراءةٌ فقط · لا إنتاج · لا تلغرام · لا حالة."""
import csv, gzip, json, os, sys, io, contextlib, datetime as dt
os.environ.setdefault("FAISAL_ONLY", "1")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
import pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import Super_stock as S
ANCHORS = ["DKI", "SXTC", "HUBC", "CRE"]


def load():
    p = sorted(f for f in os.listdir(os.path.join(ROOT, "fm_forensics", "data")) if f.startswith("bars_"))[-1]
    return json.load(gzip.open(os.path.join(ROOT, "fm_forensics", "data", p), "rt"))


def frame(rows):
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]); df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def raw_rows(rows, splits):
    """إلغاءُ التسوية: كلُّ شمعةٍ قبل تقسيمٍ (نسبة r) تُضرب بـ r (العكسيّ 1:80 ⟵ r=0.0125 يُصغّر الأسعار ويُكبّر الحجم)."""
    out = []
    for d, o, h, l, c, v in rows:
        f = 1.0
        for sd, r in (splits or []):
            if r and d < sd:
                f *= float(r)
        out.append([d, o * f, h * f, l * f, c * f, v / f if f else v])
    return out


def inputs(df):
    """القيمُ نفسُها التي تقرؤها M1–M5 (نسخةٌ حسابيّة للتسجيل · لا تغيّر القرار)."""
    c = df["Close"].values; price = float(c[-1]); hi52 = float(df["High"].tail(252).max())
    drop = (1.0 - price / hi52) * 100.0 if hi52 > 0 else None
    bs, _ = S.spike_info(c, exclude_last=S.CONFIG["BASE_WINDOW"])
    bw = S.CONFIG["BASE_WINDOW"]; bh = float(df["High"].tail(bw).max()); bl = float(df["Low"].tail(bw).min())
    rng = (bh / bl - 1.0) * 100.0 if bl > 0 else None
    dv = float((df["Close"] * df["Volume"]).tail(20).mean())
    return dict(price=round(price, 4), hi52=round(hi52, 4), drop=round(drop, 2) if drop is not None else None,
                spike=round(float(bs), 1), base_range=round(rng, 1) if rng is not None else None, dollar_vol=round(dv, 0), bars=len(df))


def run_one(sym, df, world, splits):
    S._REJECT_REASONS.pop(sym, None)
    for k in ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M4"):
        S.CONFIG[k] = 0
    S._BT_SPLITS_CTX = None
    if world in ("B_PSH", "B_M4"):
        S.CONFIG["BT_SPLIT_REF_M2"] = 1; S._BT_SPLITS_CTX = [(pd.Timestamp(d), float(r)) for d, r in (splits or [])]
        if world == "B_M4":
            S.CONFIG["BT_SPLIT_AWARE_M4"] = 1
    if len(df) < S.CONFIG["MIN_BARS"]:
        return "TOO_FEW_BARS", None
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            r = S.analyze_ticker(sym, df)
        except Exception as e:                                    # noqa: BLE001
            return "ERROR:" + type(e).__name__, None
    if r:
        return "PASS", dict(score=r.get("score"), soft_fails=len(r.get("soft_fails") or []), tier=r.get("tier"))
    return S._REJECT_REASONS.get(sym, "REJECT_?"), None


def main(argv):
    data = load(); dates = [d["date"] for d in json.load(open(os.path.join(ROOT, "reject_log.json")))]
    syms = sorted(data["daily"]); only = set(argv[1].split(",")) if len(argv) > 1 else None
    out = []
    for sym in syms:
        if only and sym not in only:
            continue
        rows = data["daily"][sym]; sp = [(d, float(r)) for d, r in (data.get("splits") or {}).get(sym) or []]
        rsp = [(d, r) for d, r in sp if r < 1.0]
        for day in dates:
            asof_rows = [r for r in rows if r[0] < day]
            if not asof_rows:
                continue
            asof = asof_rows[-1][0]
            in_win = [d for d, r in rsp if asof_rows[max(0, len(asof_rows) - 252)][0] <= d <= asof]
            worlds = {"A": frame(asof_rows), "ID": frame(asof_rows), "B_PSH": frame(asof_rows), "B_M4": frame(asof_rows),
                      "B_RAW": frame(raw_rows(asof_rows, sp)),
                      "B_CUT": frame([r for r in asof_rows if not rsp or r[0] >= max(d for d, _ in rsp)]) if rsp else None}
            for w, df in worlds.items():
                if df is None or len(df) == 0:
                    continue
                res, extra = run_one("X_" + sym if w == "ID" else sym, df, w, sp if w in ("B_PSH", "B_M4") else None)
                row = dict(symbol=sym, log_date=day, asof=asof, world=w, result=res, rsplits_in_252=len(in_win),
                           last_rsplit=(max(d for d, _ in rsp) if rsp else ""), **inputs(df) if len(df) else {})
                if extra:
                    row.update(extra)
                out.append(row)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    path = os.path.join(HERE, "out", "replay_%s.csv" % ("anchors" if only else "all"))
    keys = ["symbol", "log_date", "asof", "world", "result", "rsplits_in_252", "last_rsplit", "price", "hi52", "drop", "spike", "base_range", "dollar_vol", "bars", "score", "soft_fails", "tier"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); [w.writerow(r) for r in out]
    print(path, len(out))


if __name__ == "__main__":
    main(sys.argv)
