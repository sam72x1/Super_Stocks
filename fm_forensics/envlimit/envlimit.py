"""🧺🎯 `T-ENV-LIMIT` — هل يتحوّل لمسُ صيّاد الغلاف إلى ربحٍ بأمر بيعٍ جاهز؟ (أمرُ المالك 2026-11-19 · وصفٌ · مرّةً واحدة)
العقد `T_ENV_LIMIT_prereg.md` مدموجٌ قبل أيّ رقم · قراءةٌ فقط · لا تلغرام · لا إنتاج.
الخروج: 0 صدر · 5 لا قياس (تغطية/تقسيمات) · 7 صدر من قبل · 11 العقدُ تغيّر."""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PREREG = os.path.join(HERE, "T_ENV_LIMIT_prereg.md")
PREREG_SHA = "94020768e146f194c877e7175b3c2b8a9c4afde71f1619af8c6f6f168243abe0"
RESULT = os.path.join(HERE, "T_ENV_LIMIT_RESULT.md")
LEDGER = os.path.join(ROOT, "hunter_ledger.jsonl")
RC_OK, RC_POP, RC_ONCE, RC_CONTRACT = 0, 5, 7, 11
ARMS = {"L50": 0.50, "L100": 1.00}       # §④ — لا ذراعَ ثالثة
FWD = 40                                  # §③ — جلسات
COST = 1.8                                # §③ — كلفةُ الجولة %
BOOT, SEED = 2000, "ENVL1"                # §⑤
MIN_E, MIN_C = 30, 20                     # §⑥ — كفايةٌ دنيا
COVER_MIN = 0.80                          # §⑧
HUNTERS = {"envelope": "e", "control": "c"}


def log(*a):
    print(*a, flush=True)


def contract_ok(path=None, sha=None) -> bool:
    try:
        return hashlib.sha256(open(path or PREREG, "rb").read()).hexdigest() == (sha or PREREG_SHA)
    except OSError:
        return False


def first_appearance(rows) -> dict:
    """§② ⟵ {"e": {رمز: جلسة}, "c": {رمز: جلسة}} — أقدمُ جلسةٍ لكلّ رمزٍ داخل كلّ ذراع."""
    out = {"e": {}, "c": {}}
    for r in rows or []:
        arm = HUNTERS.get(r.get("hunter"))
        sym, s = str(r.get("symbol") or "").upper(), str(r.get("session") or "")[:10]
        if not arm or not sym or len(s) != 10:
            continue
        if sym not in out[arm] or s < out[arm][sym]:
            out[arm][sym] = s
    return out


def window(session: str, cal: list):
    """جلساتُ السوق 1..40 بعد جلسة الرصد من التقويم المرجعيّ ⟵ قائمةٌ بـ40 تاريخًا أو None (النافذةُ لم تكتمل)."""
    after = [d for d in cal if d > session]
    return after[:FWD] if len(after) >= FWD else None


def trade(bars: dict, win: list, target: float, splits=(), session: str = "") -> dict:
    """§③ صفقةٌ واحدة. `bars` = {تاريخ: (افتتاح، أعلى، أدنى، إغلاق)} مسوّاة · `win` = الجلسات 1..40.
    ⟵ {"status": hit|time|delist|noentry|split, "ret": عائد% بعد الكلفة أو None, "exit": تاريخ}."""
    d1 = win[0]
    b1 = bars.get(d1)
    if not b1 or not b1[0] or b1[0] <= 0:
        return {"status": "noentry", "ret": None, "exit": None}
    entry = float(b1[0])
    tgt = entry * (1.0 + target)
    ex_day, status, px = None, None, None
    for d in win:
        b = bars.get(d)
        if b and b[1] is not None and float(b[1]) >= tgt:
            ex_day, status, px = d, "hit", tgt
            break
    if status is None:
        inwin = [d for d in win if d in bars]
        later = any(d > win[-1] for d in bars)
        if win[-1] in bars or later:
            ex_day = inwin[-1]
            status, px = "time", float(bars[ex_day][3])
        else:
            ex_day, status, px = inwin[-1], "delist", None
    if any((session or "") < s <= ex_day for s in (splits or ())):   # §③ التقسيمُ بعد جلسة الرصد وحتى يوم الخروج
        return {"status": "split", "ret": None, "exit": ex_day}
    if status == "delist":
        return {"status": "delist", "ret": -100.0, "exit": ex_day}
    return {"status": status, "ret": (px / entry - 1.0) * 100.0 - COST, "exit": ex_day}


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def boot(by_sess: dict, seed=SEED, B=BOOT):
    """§⑤ بوتستراب عنقوديٌّ بالجلسة. `by_sess` = {جلسة: {"e": [عوائد], "c": [عوائد]}}
    ⟵ {"e": (متوسّط، أدنى، أعلى)، "c": …، "d": …، "skipped": n}."""
    ss = sorted(by_sess)
    e_all = [x for s in ss for x in by_sess[s]["e"]]
    c_all = [x for s in ss for x in by_sess[s]["c"]]
    if not e_all or not c_all:
        return None
    rng = random.Random(seed)
    E, C, D, skipped = [], [], [], 0
    for _ in range(B):
        samp = [ss[rng.randrange(len(ss))] for _ in ss]
        e = [x for s in samp for x in by_sess[s]["e"]]
        c = [x for s in samp for x in by_sess[s]["c"]]
        if not e or not c:
            skipped += 1
            continue
        me, mc = _mean(e), _mean(c)
        E.append(me)
        C.append(mc)
        D.append(me - mc)

    def ci(v):
        v = sorted(v)
        if not v:
            return (None, None)
        return (v[int(0.025 * (len(v) - 1))], v[int(0.975 * (len(v) - 1))])
    me, mc = _mean(e_all), _mean(c_all)
    return {"e": (me,) + ci(E), "c": (mc,) + ci(C), "d": (me - mc,) + ci(D), "skipped": skipped}


def verdict(n_e: int, n_c: int, bt) -> str:
    """§⑥ — مكتوبٌ سلفًا."""
    if n_e < MIN_E or n_c < MIN_C or not bt or bt["e"][1] is None or bt["d"][1] is None:
        return "لا قياس"
    return "يتحوّل" if (bt["e"][1] > 0 and bt["d"][1] > 0) else "لا يتحوّل"


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def arm_stats(trades: list) -> dict:
    """`trades` = [{sym, session, status, ret}] لذراعٍ وجهةٍ واحدة (المحسوبةُ وحدَها: hit/time/delist)."""
    rs = [t["ret"] for t in trades]
    miss = [t["ret"] for t in trades if t["status"] != "hit"]
    return {"n": len(rs), "hit": sum(1 for t in trades if t["status"] == "hit"),
            "delist": sum(1 for t in trades if t["status"] == "delist"),
            "miss_median": _median(miss), "lt50": sum(1 for r in rs if r < -50.0),
            "worst": sorted(trades, key=lambda t: (t["ret"], t["sym"]))[:5]}


def _f(x, sign=True):
    if x is None:
        return "—"
    return f"{x:+.1f}%" if sign else f"{x:.1f}%"


def run() -> int:
    if not contract_ok():
        log(f"⛔ العقدُ تغيّر عن بصمته — خروج {RC_CONTRACT}")
        return RC_CONTRACT
    if os.path.exists(RESULT):
        log(f"⛔ صدر حكمُ T-ENV-LIMIT — مرّةً واحدة · خروج {RC_ONCE}")
        return RC_ONCE
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    import datetime as dt
    import Super_stock as S
    rows = [json.loads(ln) for ln in open(LEDGER, encoding="utf-8") if ln.strip()]
    fa = first_appearance(rows)
    log("# 🧺🎯 T-ENV-LIMIT — أمرُ بيعٍ جاهز على لمس صيّاد الغلاف (وصف · مرّةً واحدة)")
    log(f"- السجلّ {len(rows)} صفًّا · أوّلُ ظهور: الصيّاد {len(fa['e'])} رمزًا · الشاهد {len(fa['c'])} رمزًا")
    s0 = min(min(fa["e"].values()), min(fa["c"].values()))
    today = dt.date.today().isoformat()
    spy = S.polygon_daily_frame("SPY", s0, today)
    if spy is None or len(spy) < FWD:
        log(f"⛔ تعذّر التقويمُ المرجعيّ — خروج {RC_POP}")
        return RC_POP
    cal = [str(i)[:10] for i in spy.index]
    if cal and cal[-1] >= today:                                  # جلسةُ اليوم غيرُ مكتملة
        cal = cal[:-1]
    sp = S.polygon_splits_since(s0)
    if sp is None:
        log(f"⛔ تعذّر جلبُ التقسيمات — لا استبعادَ بلا قائمة · خروج {RC_POP}")
        return RC_POP
    log(f"- التقويمُ المرجعيّ {cal[0]} … {cal[-1]} ({len(cal)} جلسة) · رموزٌ لها تقسيمٌ منذ {s0}: {len(sp)}")
    need = {}
    for arm in ("e", "c"):
        for sym, s in fa[arm].items():
            w = window(s, cal)
            if w:
                need[(arm, sym)] = (s, w)
    elig = {a: sum(1 for k in need if k[0] == a) for a in ("e", "c")}
    log(f"- المؤهَّل (نافذتُه اكتملت): الصيّاد {elig['e']} · الشاهد {elig['c']}")
    bars_of = {}
    for sym in sorted({k[1] for k in need}):
        s_min = min(v[0] for k, v in need.items() if k[1] == sym)
        df = S.polygon_daily_frame(sym, s_min, today)
        if df is not None and len(df):
            bars_of[sym] = {str(i)[:10]: (float(o), float(h), float(lo), float(c))
                            for i, o, h, lo, c in zip(df.index, df["Open"], df["High"], df["Low"], df["Close"])}
    cov = {a: sum(1 for k in need if k[0] == a and k[1] in bars_of) for a in ("e", "c")}
    log(f"- شموعٌ مجلوبة: الصيّاد {cov['e']} من {elig['e']} · الشاهد {cov['c']} من {elig['c']}")
    if any(elig[a] == 0 or cov[a] / elig[a] < COVER_MIN for a in ("e", "c")):
        log(f"⚖️ «لا قياس» — تغطيةُ الشموع دون {int(COVER_MIN * 100)}% · خروج {RC_POP}")
        return RC_POP
    names = {"e": "الصيّاد", "c": "الشاهد"}
    for arm_name, tgt in ARMS.items():
        log("")
        log(f"## الذراع {arm_name} — هدف +{int(tgt * 100)}% · دخولٌ عند افتتاح اليوم التالي · بلا وقف · خروجٌ عند إغلاق الجلسة {FWD} · بعد كلفة {COST}%")
        per = {"e": [], "c": []}
        cnt = {"e": {}, "c": {}}
        by_sess = {}
        for (arm, sym), (s, w) in sorted(need.items()):
            if sym not in bars_of:
                cnt[arm]["بلا شموع"] = cnt[arm].get("بلا شموع", 0) + 1
                continue
            t = trade(bars_of[sym], w, tgt, splits=sp.get(sym) or (), session=s)
            cnt[arm][t["status"]] = cnt[arm].get(t["status"], 0) + 1
            if t["ret"] is None:
                continue
            per[arm].append({"sym": sym, "session": s, "status": t["status"], "ret": t["ret"]})
            by_sess.setdefault(s, {"e": [], "c": []})[arm].append(t["ret"])
        bt = boot(by_sess)
        for arm in ("e", "c"):
            st = arm_stats(per[arm])
            c = cnt[arm]
            log(f"### {names[arm]}")
            log(f"- محسوبة {st['n']} · لمس الهدف {st['hit']} ({_f(100.0 * st['hit'] / st['n'], False) if st['n'] else '—'}) · "
                f"خرج بالوقت {c.get('time', 0)} · مشطوب {st['delist']} · مستبعَدٌ بالتقسيم {c.get('split', 0)} · لا دخول {c.get('noentry', 0)} · بلا شموع {c.get('بلا شموع', 0)}")
            if bt:
                m, lo, hi = bt[arm]
                log(f"- **متوسّطُ العائد {_f(m)} [{_f(lo)} · {_f(hi)}]**")
            log(f"- وسيطُ عائد من لم يلمس {_f(st['miss_median'])} · خسر أكثر من 50%: {st['lt50']} ({_f(100.0 * st['lt50'] / st['n'], False) if st['n'] else '—'})")
            log("- أسوأ 5: " + (" · ".join(f"{t['sym']} {t['session']} {_f(t['ret'])} ({t['status']})" for t in st["worst"]) or "—"))
        if bt:
            m, lo, hi = bt["d"]
            log(f"- **الفرق (الصيّاد − الشاهد) {_f(m)} [{_f(lo)} · {_f(hi)}]** · جلساتُ الرصد {len(by_sess)} · إعاداتٌ مهمَلة {bt['skipped']} من {BOOT}")
        log(f"⚖️ ENVLIMIT {arm_name}: «{verdict(len(per['e']), len(per['c']), bt)}»")
    log("")
    log("لا شيء يُشحَن · لا تغييرَ على أيّ أداة.")
    return RC_OK


if __name__ == "__main__":
    sys.exit(run())
