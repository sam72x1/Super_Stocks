"""🚧 قياسُ «حدّ الانفجار 35» على العشرة (2026-10-29 · أمرُ المالك «قس حد الانفجار 35 على العشرة أولًا»).

التعريفاتُ كلُّها في `CHASE35_DEFS.md` (مدموجٌ قبل أيّ رقم) — هذي الأداةُ تطبّقها حرفيًّا:
  ③ `gain5` على الشمعة المرجعيّة `ref_bar` بصيغة `analyze_ticker` (إغلاقٌ ÷ إغلاقِ ما قبله بخمس جلسات − 1) ·
     «يرفضه 35» = فوق 35.0 · «يرفضه النافذ» = فوق 214.7287 · ومطابقةُ سعر الترشيح `entry_ref`.
  ④ القياسُ نفسُه على الإضافات الـ263 كلِّها (وصفٌ لا يحكم).

قراءةٌ فقط · بلا شبكة · لا تلغرام · لا تكتب إلّا في مجلّدها:
    python3 fm_forensics/chase35/chase35.py            ⟵ يبني `data/result.json` و`CHASE35_RESULT.md`
    python3 fm_forensics/chase35/chase35.py --check    ⟵ يعيد البناءَ في الذاكرة ويقارن بايتًا (خروج 1 عند الاختلاف)
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
INPUT = os.path.join(HERE, "data", "input.json")
RESULT_JSON = os.path.join(HERE, "data", "result.json")
RESULT_MD = os.path.join(HERE, "CHASE35_RESULT.md")
STORES = (                                                  # §③-2 بترتيبه
    "fm_forensics/anchor_age/data/anchor_bars.json.gz",
    "faisal_engine/data/rank/bars.json.gz",
    "faisal_engine/data/universe_bars.json.gz",
)
T35 = 35.0                                                  # الحدُّ المقيس (أمرُ المالك)
T_LIVE = 214.7286870417835                                  # النافذُ اليوم (مطبوعٌ في رأس كلّ تشغيلة)
MATCH_TOL = 0.02                                            # §③-5


def gain5_at(bars, ref_bar, added):
    """(الشمعةُ المستعملة، إغلاقُها، إغلاقُ ما قبلها بخمس، gain5، وسمُ المرجع) أو None — صيغةُ `analyze_ticker` حرفيًّا."""
    days = [b[0] for b in bars]
    tag = "ref_bar"
    if ref_bar and ref_bar in days:
        i = days.index(ref_bar)
    else:
        tag = "قبل يوم الإضافة"                            # §③-1 حين يغيب ref_bar أو لا شمعةَ له
        prior = [k for k, d in enumerate(days) if d < added]
        if not prior:
            return None
        i = prior[-1]
    if i < 5:
        return None
    c1, c6 = float(bars[i][4]), float(bars[i - 5][4])
    if not c6:
        return None
    return days[i], c1, c6, (c1 / c6 - 1.0) * 100.0, tag


def match_state(entry_ref, close, day, splits):
    """§③-5: مطابقةُ سعر الترشيح المخزَّن بإغلاق TradingView على الشمعة نفسِها."""
    if not entry_ref or not close:
        return "لا سعرَ ترشيح", None
    r = float(entry_ref) / float(close)
    if abs(r - 1.0) <= MATCH_TOL:
        return "مطابق", r
    if splits is None:
        return "غير مطابق (لا سجلَّ تقسيمات في الملفّ)", r
    f = 1.0
    for d, k in splits:
        if d > day:
            f *= float(k)
    if f != 1.0 and abs(r / f - 1.0) <= MATCH_TOL:
        return "مطابق بعد التقسيم", r
    return "غير مطابق", r


def load_stores(root=ROOT):
    out = []
    for rel in STORES:
        d = json.load(gzip.open(os.path.join(root, rel)))
        out.append((rel, d.get("daily") or {}, d.get("splits")))
    return out


def measure(add, stores):
    """صفُّ القياس لإضافةٍ واحدة — أوّلُ ملفٍّ فيه الشمعةُ المرجعيّة وخمسٌ قبلها (§③-2)."""
    sym, ref_bar, added = add["sym"], add.get("ref_bar"), add["added"]
    for rel, daily, splits in stores:
        bars = daily.get(sym)
        if not bars:
            continue
        g = gain5_at(bars, ref_bar, added)
        if g is None:
            continue
        day, c1, c6, g5, tag = g
        sp = None if splits is None else (splits.get(sym) or [])
        m, ratio = match_state(add.get("entry_ref"), c1, day, sp)
        return {"sym": sym, "added": added, "ref_bar": ref_bar, "bar": day, "bar_tag": tag,
                "close": round(c1, 6), "close_5": round(c6, 6), "gain5": round(g5, 4),
                "rej35": g5 > T35, "rej_live": g5 > T_LIVE,
                "entry_ref": add.get("entry_ref"), "ratio": None if ratio is None else round(ratio, 4),
                "match": m, "store": rel}
    return {"sym": sym, "added": added, "ref_bar": ref_bar, "bar": None, "gain5": None,
            "rej35": None, "rej_live": None, "match": "غير مقيس", "store": None}


def _dd(a, b):
    import datetime as _d
    return abs((_d.date.fromisoformat(a) - _d.date.fromisoformat(b)).days)


def context(row, stores, split_src):
    """§④ بعد الرقم (وصفٌ لا يحكم): ترتيبُ يوم الانفجار المسجَّل من الشمعة المرجعيّة · بُعدُ السعر عن أعلى إغلاقٍ في العشر قبلها ·
    أعلى إغلاقٍ في العشر بعدها · وهل «القفزة» في يوم تقسيمٍ عكسيّ (‏3 أيّامٍ تقويميّة فأقلّ · من سجلّ التقسيمات الوحيد المحفوظ)."""
    bar, sym = row.get("bar"), row["sym"]
    if not bar:
        return None
    for _rel, daily, _sp in stores:
        b = daily.get(sym)
        days = [q[0] for q in (b or [])]
        if bar not in days:
            continue
        i = days.index(bar)
        if i < 10 or i + 10 >= len(b):
            continue
        c = [float(q[4]) for q in b]
        ed = row["expl_date"]
        order = "بعد الشمعة" if ed > bar else ("يومَ الشمعة" if ed == bar else "قبل الشمعة")
        split_day = (row["kind"] == "قفزة"
                     and any(float(k) < 1.0 and _dd(d, ed) <= 3 for d, k in (split_src.get(sym) or [])))
        return {"order": order, "below_peak10": round((max(c[i - 10:i + 1]) / c[i] - 1.0) * 100.0, 1),
                "after10": round((max(c[i + 1:i + 11]) / c[i] - 1.0) * 100.0, 1), "split_day": split_day}
    return None


def build(inp, stores):
    ten_keys = [(t["sym"], t["added"]) for t in inp["ten"]]
    adds = {(a["sym"], a["added"]): a for a in inp["adds"]}
    ten = [dict(measure(adds[k], stores), **{k2: t[k2] for k2 in ("expl_date", "expl_gain", "kind", "sessions")})
           for k, t in zip(ten_keys, inp["ten"])]
    split_src = next((sp for _r, _d, sp in stores if sp is not None), {}) or {}
    for r in ten:
        r["ctx"] = context(r, stores, split_src)
    allrows = [measure(a, stores) for a in inp["adds"]]
    return {"ten": ten, "all": allrows}


def _n(x):
    return "—" if x is None else format(x, "g")


def _p(x, nd=1):
    return "—" if x is None else f"{x:+.{nd}f}%"


def render(res, inp):
    ten, allr = res["ten"], res["all"]
    n_meas = sum(1 for r in ten if r["gain5"] is not None)
    n35 = sum(1 for r in ten if r["rej35"])
    tenset = {(r["sym"], r["added"]) for r in ten}
    rej_all = [r for r in allr if r["rej35"]]
    rej_other = [r for r in rej_all if (r["sym"], r["added"]) not in tenset]
    unmeas_all = [r for r in allr if r["gain5"] is None]
    L = []
    L.append("# 🚧 «حدّ الانفجار 35» على العشرة — النتيجة (2026-10-29)")
    L.append("")
    L.append("**أيّ حدّ:** `RECENT_RISE_BLOCK_PCT` في `Super_stock.py` — قيمتُه النافذة اليوم **214.73** (المكتوبُ في الجدول 35.0 "
             "وتستبدله أرقامُ كاتالوج فيصل) · يرفض المرشّحَ الذي صعد أكثرَ منه في آخر 5 جلسات · "
             "**والعشرة:** LUNR · AEMD · INBS · SUGP · SUPX · PRHI · SSM · CELU · SMXT · SXTP — إضافاتٌ للقائمة منذ 08-01 "
             "سجّل البوتُ لكلٍّ منها «انفجارًا» يقع يومُه خلال 0-10 جلساتٍ قبل يوم الإضافة (تقريرُ الجزء أ · وانظر §③: "
             "التسميةُ أوسعُ من حقيقتها).")
    L.append("**لماذا كان 35 ثمّ تغيّر:** 35 رقمُ المشروع منذ بدايته (الفكرةُ «لا تلاحق» من فيصل والرقمُ نفسُه غيرُ مُتحقَّق) · "
             "وفي 2026-08-07/08 استبدلته «معايير فيصل وحدها» بحدّ كاتالوجه (8.16 ثمّ 214.73 حين صار الظرفُ «الحدّ الأدنى» P100 = "
             "أقصى صعودٍ رآه الكاتالوج) فتعطّلت البوّابةُ عمليًّا · وقاس `T-CHASE` (08-10) الرجوعَ إلى 35 «بلا ضرر» وبقي بلا قرار.")
    L.append("")
    L.append(f"## ① الجواب: كم من العشرة كان 35 سيرفضه؟ **{n35} من {n_meas}**"
             + ("" if n_meas == len(ten) else f" (وغيرُ مقيسٍ {len(ten) - n_meas})"))
    L.append("")
    L.append("| السهم | يومُ الإضافة | الانفجار (يومُه · نسبتُه · جلساتٌ قبل الإضافة) | الشمعةُ المرجعيّة | إغلاقُها | قبلها بخمس | صعودُ 5 جلسات | يرفضه 35؟ | مطابقةُ سعر الترشيح |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in ten:
        L.append(f"| {r['sym']} | {r['added']} | {r['expl_date']} · ‏{r['expl_gain']:g}% {r['kind']} · {r['sessions']} | "
                 f"{r.get('bar') or '—'}{'' if r.get('bar_tag') in (None, 'ref_bar') else ' (' + r['bar_tag'] + ')'} | "
                 f"{_n(r.get('close'))} | {_n(r.get('close_5'))} | "
                 f"{_p(r['gain5'])} | {'—' if r['rej35'] is None else ('نعم' if r['rej35'] else 'لا')} | "
                 f"{r['match']}{'' if r.get('ratio') is None else ' (' + format(r['ratio'], 'g') + ')'} |")
    live = [r["sym"] for r in ten if r["rej_live"]]
    L.append("")
    L.append("شاهدُ الاتّساق (التعريفات §③-4): الحدُّ النافذ 214.73 "
             + ("لا يرفض أيًّا من العشرة — كما يجب لأنها أُضيفت فعلًا." if not live else
                "**يرفض " + " · ".join(live) + " وقد أُضيفت فعلًا ⟵ عدمُ تطابقٍ في البيانات يُعلَن.**"))
    L.append("")
    L.append("## ② وصفٌ ثانويّ: الكلفةُ على باقي الإضافات (لا يحكم)")
    L.append("")
    L.append(f"من **{len(allr)}** إضافةً منذ 08-01 قِيس {len(allr) - len(unmeas_all)} · كان 35 سيرفض **{len(rej_all)}**: "
             f"منها {len(rej_all) - len(rej_other)} من العشرة و**{len(rej_other)}** من غيرها.")
    if rej_other:
        L.append("")
        L.append("| السهم | يومُ الإضافة | صعودُ 5 جلسات | مطابقة |")
        L.append("|---|---|---|---|")
        for r in sorted(rej_other, key=lambda x: (x["added"], x["sym"])):
            L.append(f"| {r['sym']} | {r['added']} | {_p(r['gain5'])} | {r['match']} |")
    if unmeas_all:
        L.append("")
        L.append("غيرُ مقيس (لا شموعَ كافية في الملفّات الثلاثة): " + " · ".join(f"{r['sym']} {r['added']}" for r in unmeas_all))
    L.append("")
    L.append("## ③ بعد الرقم — هل العشرةُ «مطاردةٌ بعد انفجار» أصلًا؟ (وصفٌ لا يغيّر التعريفَ ولا الجواب)")
    L.append("")
    L.append("«يومُ الانفجار» في سجلّ البوت (`scan_explosions`): للقفزة يومُ القفزة · **وللتجمّع يومُ بدء الصعود** "
             "(أوّلُ يومٍ بعد القاع · `_run_explosion`) لا قمّتُه ⟵ والصعودُ قد يستمرّ بعد الإضافة.")
    L.append("")
    L.append("| السهم | يومُ الانفجار المسجَّل من الشمعة المرجعيّة | قفزةٌ في يوم تقسيمٍ عكسيّ؟ | تحت أعلى إغلاقٍ في العشر قبلها | أعلى إغلاقٍ في العشر بعدها |")
    L.append("|---|---|---|---|---|")
    for r in ten:
        cx = r.get("ctx")
        if not cx:
            L.append(f"| {r['sym']} | — | — | — | — |")
            continue
        L.append(f"| {r['sym']} | {cx['order']} | {'نعم' if cx['split_day'] else 'لا'} | {cx['below_peak10']:g}% | {_p(cx['after10'])} |")
    _cx = [r["ctx"] for r in ten if r.get("ctx")]
    n_split = sum(1 for c in _cx if c["split_day"])
    n_after = sum(1 for c in _cx if c["order"] == "بعد الشمعة" and not c["split_day"])
    n_up20 = sum(1 for c in _cx if c["after10"] >= 20.0)
    L.append("")
    L.append(f"⟵ **{n_split}** «قفزةٌ» في يوم تقسيمٍ عكسيّ (ليست انفجارًا) · **{n_after}** بدأ صعودُها بعد شمعة الترشيح "
             f"(أُضيفت قبله) · و**{n_up20}** من {len(_cx)} علا إغلاقُها 20% فأكثر خلال عشر جلساتٍ بعد الإضافة. "
             "أعلى صعودِ خمسِ جلساتٍ بين الإضافات المقيسة كلِّها "
             + _p(max((r["gain5"] for r in allr if r["gain5"] is not None), default=None)) + ".")
    L.append("")
    L.append("## ④ حدودُ الصدق (مكتوبةٌ قبل الرقم في `CHASE35_DEFS.md §⑥` ‏+ ما ظهر بعده)")
    L.append("")
    L.append("1. البوتُ في أغسطس وسبتمبر قرأ ياهو والقياسُ على TradingView — ومطابقةُ سعر الترشيح تحرس يومَ الترشيح لا الشموعَ الخمس قبله.")
    L.append("2. السؤالُ «هل كان 35 سيمنع الإضافةَ يومَها» لا «هل كان سيُضاف لاحقًا» ولا ربحٌ أو خسارة (الكلفةُ على 3 سنوات قاسها `T-CHASE`).")
    L.append("3. رقمُ LUNR رُئي قبل كتابة التعريفات (إفصاحُ §⑥-3) — ولا معاملَ يُضبط عليه.")
    L.append("4. عشرةٌ في ثلاثة أشهر ⟵ وصفٌ لا معدّل.")
    L.append("5. **بعد الرقم:** «غير مطابق» سببُه في العشرة معروف — INBS وSUPX وSUGP أُضيفت **أثناء** جلسة 08-07 (13:38 و15:39 UTC) "
             "فسعرُ ترشيحها لحظيٌّ لا إغلاق، وSUGP قُسّم عكسيًّا 2026-10-07 (1 إلى 6) بعد الشمعة وسجلُّه في `universe_bars` لا في "
             "الملفّ الذي قِيس منه. والفرقُ لا يقترب من الحدّ: أعلى صعودٍ في العشرة "
             + _p(max((r["gain5"] for r in ten if r["gain5"] is not None), default=None)) + ".")
    L.append("6. **بعد الرقم:** §③ وصفٌ لم يُكتب قبل الرقم — «أعلى إغلاقٍ بعد الإضافة» إغلاقٌ لا تنفيذ، ولا ربحَ يُدَّعى.")
    L.append("")
    L.append(f"_المُدخَل `data/input.json` ({inp['provenance']}) · الشموع: " + " ⟵ ".join(f"`{s}`" for s in STORES)
             + " · `python3 fm_forensics/chase35/chase35.py --check` يعيد هذا الملفَّ بايتًا._")
    return "\n".join(L) + "\n"


def outputs(root=ROOT):
    inp = json.load(open(INPUT, encoding="utf-8"))
    res = build(inp, load_stores(root))
    return (json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", render(res, inp))


def main(argv):
    rj, md = outputs()
    if "--check" in argv:
        ok = (open(RESULT_JSON, encoding="utf-8").read() == rj and open(RESULT_MD, encoding="utf-8").read() == md)
        print("chase35 --check:", "OK" if ok else "⛔ مختلف")
        return 0 if ok else 1
    open(RESULT_JSON, "w", encoding="utf-8").write(rj)
    open(RESULT_MD, "w", encoding="utf-8").write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
