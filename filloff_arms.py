#!/usr/bin/env python3
"""🪜🩸 `T-FILLOFF` — أذرعُ «إزاحة التعبئة» (العقد `filloff_prereg.md`).

**السؤالُ الحاكم:** هل تُغيّر تكلفةُ التنفيذ المقيسة (`C-MED`, `S-MED`) حكمَ
`PR-SWEEP` على **المقام الذي حُكم عليه فعلًا** — «المُعبَّأة في الطرفين» بنصّ
توثيق `backtest_sweep_compare` — أم يصمد الرفض؟

🔒 **والمعيارُ لا يُعاد كتابتُه:** الدالّةُ الإنتاجيّة **تُنادى بالاسم** على صفوفٍ
أُعيدت كتابةُ عوائدها بـ`fcost_arms.ret_at`، وحكمُها هو الأوراكل. والتفكيكُ المحلّيُّ
يُعطي **مستوى الرِّجل** وحدَه، و`V-O2` يُلزمه موافقةَ الأوراكل في الأربع تقييمات ×
نقطتَي التكلفة — وإلّا خروجٌ **‏6**.

⚠️ **ومُعلَنٌ قبل أيّ رقم: §④ من العقد يسرد ستَّ رِجالٍ والمعيارُ الإنتاجيُّ سبعةُ
شروطٍ** — فيه `na ≥ 5` (أرضيةُ عيّنةِ المقام الزوجيّ). تُنفَّذ **السبعةُ كلُّها**
(الأوراكلُ هو الحاكم) وتُسمّى الأرضيةُ **الرِّجلَ ⓪** وتُطبَع. **وهي لا تُرخي `FO2`**
لأن التعبئةَ لا تتأثّر بالتكلفة ⇒ حالتُها متطابقةٌ في النقطتين بالبناء.

🔕 قراءةٌ/بحثٌ فقط · صفرُ مشيةِ باكتيست · صفرُ نداءٍ خارجيّ · صفرُ إسنادٍ إلى
`CONFIG` · ولا تُكتَب إلّا صفوفُ القياس (‏`filloff_rows.jsonl`).
"""
import ast
import hashlib
import json
import os
import statistics
import subprocess
import sys

# ══════════════════ ⓿ الثوابت — كلُّها من العقد ══════════════════
GOV_YEARS = ("2023", "2024", "2025")
TRADES_TMPL = "fcost_trades_{}.json"
LEGS_DEFAULT = "btcost_legs.jsonl"
OUT_ROWS = "filloff_rows.jsonl"

# 📌 المنشورُ في `btcost_result.md` — و`V-O3` يُلزم المستخرَجَ مطابقتَه
C_MED_PUB, S_MED_PUB = 1.8018, -0.4587
MED_TOL = 1e-4

# 📌 أرضيةُ المقام الزوجيّ (‏`V-O4`) — متحفّظةٌ بنصّ العقد
BOTH_YEAR, BOTH_POOL = 60, 250

# 🔒 الجذورُ الاثنا عشر ‏+ محرّكُ الحسم ‏+ **الأوراكل نفسُه** (‏`V-O6`)
ROOTS = ("rank_key", "select_top", "classify_tier", "analyze_ticker",
         "apply_short_gate", "apply_float_gate", "scan_market",
         "backtest_symbol", "scan_ignition", "scan_split_hunter",
         "entry_status", "build_interpretation", "_resolve_arm",
         "backtest_sweep_compare")

# 🔢 رموزُ الخروج — **متمايزةٌ عمدًا** فلا يُقرأ حارسٌ خللًا في السجلّ.
#    ‏2 مدخل · 3 فحصٌ ذاتيٌّ/جذور · 4 أرتيفكت · 5 `V-O1` · 6 `V-O2` ·
#    7 `V-O4` · **8 محجوزٌ للإغلاق** · **9 «لا حكم» (الفرعُ 3)**
RC_INPUT, RC_SELF, RC_ART = 2, 3, 4
RC_VO1, RC_VO2, RC_VO4, RC_NOVERDICT = 5, 6, 7, 9

# 🧩 أزواجُ (نتيجة، عائد) — التكلفةُ تُطبَّق على العائد وحدَه
RET_FIELDS = (("outcome", "ret_a"), ("outcome_b", "ret_b"),
              ("outcome_sweep", "ret_sweep_a"),
              ("outcome_sweep_b", "ret_sweep_b"))
# 🔒 الحقولُ التي يجب أن تبقى بت-بت (‏`V-O8`)
NONRET_FIELDS = ("outcome", "outcome_b", "outcome_sweep", "outcome_sweep_b",
                 "entry_model", "fill_reason_sweep", "date", "symbol")

# 🦵 أسماءُ الرِّجال — ⓪ أرضيةُ العيّنة (‏تُعلَن) ثمّ الستُّ من §④ بترتيبها
LEG_NAMES = ("L0_na", "L1_la", "L2_mb", "L3_cv_ge_av", "L4_cv_pos",
             "L5_fill", "L6_year")


def _log(msg: str) -> None:
    print(msg, flush=True)


def _num(v, nd: int = 4) -> str:
    """عرضٌ فاشلٌ-آمن: الغائبُ «—» ولا ينهار التنسيق (‏الصنفُ ①)."""
    return "—" if v is None else f"{v:+.{nd}f}"


# ══════════════════ ① دوالٌّ نقيّةٌ مقفولة ══════════════════
def rows_at(rows, c, s, ret_at):
    """صفوفٌ أُعيدت كتابةُ **عوائدها** عند `(c, s)` — والباقي بت-بت.

    `ret_at` يُحقَن (‏الإنتاجُ يمرّر `fcost_arms.ret_at` بالاسم) فالهُويّةُ هي
    هُويّةُ `T-FCOST` لا مثيلٌ لها. **وعند `(0,0)` تُرجِع `ret_at` المدخلَ بت-بت**
    فمُخرَجُ الأوراكل مطابقٌ حرفًا بحرف (‏`V-O1`).

    ⚠️ **ولا يُكتَب فوق عائدٍ نتيجتُه ليست `win`/`loss`** — يُترَك كما هو
    **ويُعدّ ويُعلَن** (‏`V-O8`): صفوفُ المحرّك قد تحمل «عالقة» بعائدٍ مقروء."""
    out, n_odd = [], 0
    for t in rows or []:
        u = dict(t)
        for okey, rkey in RET_FIELDS:
            r = t.get(rkey)
            if r is None:
                continue
            o = t.get(okey)
            if o in ("win", "loss"):
                u[rkey] = ret_at(float(r), o, c, s)
            else:
                n_odd += 1
        out.append(u)
    return out, n_odd


def nonret_signature(rows):
    """بصمةُ الحقول غيرِ العائدية — `V-O8` يشترط تطابقَها قبل/بعد الكتابة."""
    return [tuple(repr(t.get(k)) for k in NONRET_FIELDS) for t in rows or []]


def legs_of(rows, mean_lo95):
    """تفكيكٌ محلّيٌّ للرِّجال السبع — **مرآةُ الأوراكل لا بديلُه**.

    `mean_lo95` يُحقَن (`Super_stock._mean_lo95` بالاسم) فرِجلا `la`/`mb` حسابُ
    الإنتاج نفسُه. و`V-O2` يُلزم اتّفاقَ اقترانِ السبع مع حكمِ الأوراكل."""
    sw = [t for t in rows or [] if (t or {}).get("entry_model")
          == "sweep_confirmed"]
    if not sw:
        return None

    def bf(t):
        return t.get("ret_a") is not None

    def sf(t):
        return t.get("ret_sweep_a") is not None

    n_bf = sum(1 for t in sw if bf(t))
    n_sf = sum(1 for t in sw if sf(t))
    both = [t for t in sw if bf(t) and sf(t)]
    da = [t["ret_sweep_a"] - t["ret_a"] for t in both]
    db = [t["ret_sweep_b"] - t["ret_b"] for t in both
          if t.get("ret_b") is not None and t.get("ret_sweep_b") is not None]
    ma, la, na = mean_lo95(da)
    mb, _lb, _nb = mean_lo95(db)

    av_sum = cv_sum = 0.0
    av_n = cv_n = 0
    for t in sw:
        bo, so = t.get("outcome"), t.get("outcome_sweep")
        br = t["ret_a"] if bf(t) else 0.0
        sr = t["ret_sweep_a"] if sf(t) else 0.0
        d = sr - br
        if bo == "loss" and not sf(t):
            av_sum += d
            av_n += 1
        elif bo == "loss" and so == "win":
            cv_sum += d
            cv_n += 1

    by_year = {}
    for t in both:
        by_year.setdefault(str(t.get("date", ""))[:4], []).append(
            t["ret_sweep_a"] - t["ret_a"])
    yrs_ok = [y for y, v in by_year.items() if len(v) >= 3]
    year_pass = bool(yrs_ok) and all(sum(by_year[y]) > 0 for y in yrs_ok)

    legs = {
        "L0_na": na >= 5,
        "L1_la": la > 0,
        "L2_mb": mb > 0,
        "L3_cv_ge_av": cv_sum >= av_sum,
        "L4_cv_pos": cv_sum > 0,
        "L5_fill": bool(n_bf) and (n_sf / n_bf) >= 0.40,
        "L6_year": year_pass,
    }
    return {
        "legs": legs, "passed": all(legs.values()),
        "n_sig": len(sw), "n_bf": n_bf, "n_sf": n_sf, "n_both": len(both),
        "ma": ma, "la": la, "na": na, "mb": mb,
        "av_sum": av_sum, "av_n": av_n, "cv_sum": cv_sum, "cv_n": cv_n,
        "fill_ratio": (n_sf / n_bf) if n_bf else None,
        "by_year": {y: (sum(v) / len(v), len(v)) for y, v in by_year.items()},
    }


def failing(legs: dict) -> frozenset:
    """مجموعةُ الرِّجال الساقطة — موضوعُ `FO2`."""
    return frozenset(k for k in LEG_NAMES if not legs.get(k, True))


def verdict_of(lines) -> str:
    """حكمُ الأوراكل من نصِّه: `adopt` / `reject` / `none`.

    ⚠️ **ولا يُخمَّن:** الدالّةُ الإنتاجيّة تطبع «‏الحكم الأولي» بإحدى صيغتين،
    وغيابُهما معًا (أو حضورُهما) يُرجِع `none` فيسقط الحكمُ على `V-O2` لا يمرّ."""
    txt = "\n".join(lines or [])
    a, r = ("يتبنّى" in txt), ("يُرفض" in txt)
    if a and not r:
        return "adopt"
    if r and not a:
        return "reject"
    return "none"


def read_verdict(crit: dict) -> tuple:
    """الفروعُ الثلاثةُ بحرف §④ — دالّةٌ نقيّةٌ مقفولة.

    ① الثلاثةُ تعبر ⇒ الفرعُ 1 (‏«الحكمُ يصمد») · ② أيٌّ يسقط ⇒ الفرعُ 2
    (‏«الحكمُ يتزحزح») · ③ بوّابةُ صلاحيةٍ ساقطة ⇒ الفرعُ 3 («لا حكم»).

    🔑 **وترتيبُ الفحص: الصلاحيّةُ أوّلًا** — فبوّابةٌ ساقطةٌ لا تُقرأ حكمًا."""
    if not crit.get("gates_ok", False):
        return 3, "لا حكم — بوّابةُ صلاحيةٍ ساقطة"
    got = [k for k in ("FO1", "FO2", "FO3") if crit.get(k) is not None]
    if len(got) < 3:
        return 3, "لا حكم — معيارٌ لم يُحسَب"
    if all(crit[k] for k in ("FO1", "FO2", "FO3")):
        return 1, "الفرعُ 1 — الحكمُ يصمد أمام التكلفة المقيسة"
    bad = [k for k in ("FO1", "FO2", "FO3") if not crit[k]]
    return 2, "الفرعُ 2 — الحكمُ يتزحزح · الساقط: " + ", ".join(bad)


# ══════════════════ ② الفحصُ الذاتيّ (‏`V-O5`/`V-O6`/`V-O7`) ══════════════════
def _own_tree():
    return ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())


def no_fetch_ok() -> tuple:
    """`V-O5` — **بالـAST لا بالنصّ**: صفرُ مشيةٍ وصفرُ جلبٍ وصفرُ مفتاحِ مزوّد."""
    # ⚠️ **ولا يُحظَر الاسمُ العاري `get`** — فهو `dict.get` في كلّ سطرٍ هنا،
    #    وحظرُه يُسقط القفلَ على كودٍ سليم (الصنفُ ② بعينه، وقع فعلًا).
    #    الحظرُ على **الجالبات المسمّاة** وعلى **الوحدات**.
    banned_calls = {"run_backtest", "download_history", "polygon_minute_bars",
                    "polygon_prev_close", "polygon_flow", "polygon_nbbo",
                    "fetch_trades", "fetch_quotes", "urlopen"}
    banned_mods = {"requests", "yfinance", "urllib", "httpx", "http"}
    # 🐞 واسمُ المفتاح **يُركَّب وقت التشغيل** فلا يطابق القفلُ حرفيّتَه هو —
    #    وهذا وقع: كتابتُه كسلسلةٍ جعلت الفحصَ يسقط على نفسه (درسُ `pgrep`).
    key_needle = "POLY" + "GON"
    hits = []
    try:
        tree = _own_tree()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّر التحليل: {type(e).__name__}"
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if (a.name or "").split(".")[0] in banned_mods:
                    hits.append(f"import {a.name}")
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] in banned_mods:
                hits.append(f"from {n.module}")
        elif isinstance(n, ast.Call):
            nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            if nm in banned_calls:
                hits.append(f"call {nm}")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            if key_needle in n.value:
                hits.append("سلسلةُ مفتاحٍ")
    return (not hits), ("صفر" if not hits else " · ".join(sorted(set(hits))))


def no_config_write_ok() -> tuple:
    """`V-O7` — صفرُ إسنادٍ إلى `CONFIG` (‏ولا `update`) — سابقةُ `V-F9`/`RKA10`."""
    hits = []
    try:
        tree = _own_tree()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّر التحليل: {type(e).__name__}"
    for n in ast.walk(tree):
        tgts = []
        if isinstance(n, ast.Assign):
            tgts = list(n.targets)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            tgts = [n.target]
        for t in tgts:
            base = t
            while isinstance(base, (ast.Subscript, ast.Attribute)):
                base = base.value
            if getattr(base, "id", None) == "CONFIG":
                hits.append("إسناد")
        if isinstance(n, ast.Call):
            f = n.func
            if (getattr(f, "attr", None) in ("update", "setdefault", "pop")
                    and (getattr(f.value, "id", None) == "CONFIG"
                         or getattr(f.value, "attr", None) == "CONFIG")):
                hits.append(f"CONFIG.{f.attr}")
    return (not hits), ("صفر" if not hits else " · ".join(sorted(set(hits))))


def roots_identical() -> tuple:
    """`V-O6` — بصمةُ AST للجذور ‏+ محرّكِ الحسم ‏+ **الأوراكل** مقابل `origin/main`.

    ⚠️ تُقرأ على الرنر من `main` فالشجرةُ نظيفة — ولا يُبنى عليها قفلُ سويّةٍ
    سلوكيّ (درسُ `RSK3`)."""
    try:
        p = subprocess.run(["git", "show", "origin/main:Super_stock.py"],
                           capture_output=True, text=True)
        base = p.stdout or ""
        cur = open("Super_stock.py", encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّرت القراءة: {type(e).__name__}"
    if not base:
        return False, "تعذّر جلبُ origin/main"

    def fp(src):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return {}
        return {n.name: hashlib.sha256(ast.dump(n).encode()).hexdigest()[:12]
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name in ROOTS}

    a, b = fp(base), fp(cur)
    diff = [r for r in ROOTS if a.get(r) != b.get(r)]
    return (not diff), ("لا شيء" if not diff else "مختلفة: " + ", ".join(diff))


# ══════════════════ ③ المصدر ══════════════════
def load_trades(base_dir: str) -> tuple:
    """صفوفُ `fcost_trades_<سنة>.json` — ثلاثُ سنواتٍ أو خروجٌ بـ**‏4**."""
    per, missing = {}, []
    for y in GOV_YEARS:
        p = os.path.join(base_dir, TRADES_TMPL.format(y)) if base_dir \
            else TRADES_TMPL.format(y)
        try:
            rows = json.load(open(p, encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            missing.append(TRADES_TMPL.format(y))
            continue
        if not isinstance(rows, list) or not rows:
            missing.append(TRADES_TMPL.format(y) + " (فارغ)")
            continue
        per[y] = rows
    return per, missing


def medians_from_legs(path: str) -> tuple:
    """`C-MED`/`S-MED` **محسوبان من السيقان لا مكتوبَين بيدي** (سابقةُ §⑧)."""
    try:
        legs = [json.loads(x) for x in open(path, encoding="utf-8")
                if x.strip()]
    except Exception as e:                                       # noqa: BLE001
        return None, None, f"تعذّرت قراءةُ السيقان: {type(e).__name__}"
    cs = sorted(float(r["c"]) for r in legs if (r or {}).get("c") is not None)
    ss = sorted(float(r["s"]) for r in legs if (r or {}).get("s") is not None)
    if not cs or not ss:
        return None, None, "سيقانٌ بلا قياس"
    return statistics.median(cs), statistics.median(ss), f"{len(legs)} ساقًا"


# ══════════════════ ④ القياس ══════════════════
def evaluate(rows, c, s, ret_at, sweep_compare, mean_lo95) -> dict:
    """تقييمٌ واحد: الأوراكلُ ‏+ التفكيكُ المحلّيُّ على **الصفوف نفسِها**."""
    new, n_odd = rows_at(rows, c, s, ret_at)
    lines = sweep_compare(new)
    loc = legs_of(new, mean_lo95)
    return {"lines": lines, "verdict": verdict_of(lines), "local": loc,
            "n_odd": n_odd, "rows": new}


def main() -> int:
    dry = (os.environ.get("FILLOFF_DRY") or "").strip() == "1"
    base_dir = (os.environ.get("FILLOFF_TRADES_DIR") or "").strip()
    legs_path = (os.environ.get("FILLOFF_LEGS") or LEGS_DEFAULT).strip()

    _log("🪜🩸 `T-FILLOFF` — إزاحةُ التعبئة على المقام الزوجيّ"
         + ("  ‹وضعُ الجدوى›" if dry else ""))
    if dry:
        _log("   🧪 **الجدوى تجيب سؤالًا واحدًا: هل يعبر `V-O4`؟** — بلا `Δ` "
             "وبلا حكمٍ وبلا طبعِ حكمِ الأوراكل. ⚠️ **وتُطلِع على أعداد المقام "
             "الزوجيّ** (كمّيّةُ `V-O4` لا كمّيّةٌ حاكمة) — يُعلَن ولا يُطوى.")

    # ① الفحصُ الذاتيُّ قبل أيّ قراءة
    f_ok, f_why = no_fetch_ok()
    g_ok, g_why = no_config_write_ok()
    _log(f"   `V-O5` صفرُ مشيةٍ/جلب: {'✅' if f_ok else '🔴'} {f_why}")
    _log(f"   `V-O7` صفرُ إسنادِ `CONFIG`: {'✅' if g_ok else '🔴'} {g_why}")
    if not (f_ok and g_ok):
        return RC_SELF
    r_ok, r_why = roots_identical()
    _log(f"   `V-O6` الجذورُ والأوراكل: {'✅' if r_ok else '🔴'} {r_why}")
    if not r_ok:
        return RC_SELF

    # ② المصدر
    per, missing = load_trades(base_dir)
    if missing:
        _log(f"⛔ صفوفٌ ناقصة: {missing}")
        return RC_ART
    pool = [t for y in GOV_YEARS for t in per[y]]
    _log(f"   المصدر: " + " · ".join(f"{y}={len(per[y])}" for y in GOV_YEARS)
         + f" · المجمَّع={len(pool)}")

    c_raw, s_raw, med_why = medians_from_legs(legs_path)
    if c_raw is None:
        _log(f"⛔ {med_why}")
        return RC_ART
    ok3 = (abs(c_raw - C_MED_PUB) <= MED_TOL
           and abs(s_raw - S_MED_PUB) <= MED_TOL)
    _log(f"   `V-O3` القياسُ المستخرَج ({med_why}): `C-MED` = {c_raw:.4f}% · "
         f"`S-MED` = {s_raw:.4f}% — {'✅ يطابق المنشور' if ok3 else '🔴 يخالف'}")
    if not ok3:
        return RC_ART
    c_meas, s_meas = c_raw / 100.0, s_raw / 100.0

    import fcost_arms as FC                                      # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    ret_at, sweep, mlo = FC.ret_at, S.backtest_sweep_compare, S._mean_lo95

    # ③ `V-O1` — الهُويّةُ بت-بت عند (0,0) · و`V-O8` الحقولُ غيرُ العائدية
    raw_lines = sweep(pool)
    z = evaluate(pool, 0.0, 0.0, ret_at, sweep, mlo)
    same = (raw_lines == z["lines"])
    sig_ok = (nonret_signature(pool) == nonret_signature(z["rows"]))
    _log(f"   `V-O1` هُويّةُ (0,0) بت-بت: {'✅ مخالفات = 0' if same else '🔴'} "
         f"({len(raw_lines)} سطرًا)")
    _log(f"   `V-O8` الحقولُ غيرُ العائدية بت-بت: {'✅' if sig_ok else '🔴'} · "
         f"صفوفٌ بعائدٍ ونتيجةٍ ليست win/loss (لم تُكتَب): {z['n_odd']}")
    if not (same and sig_ok):
        return RC_VO1

    # ④ `V-O4` — أرضيةُ المقام الزوجيّ
    ev0 = {"pool": z}
    for y in GOV_YEARS:
        ev0[y] = evaluate(per[y], 0.0, 0.0, ret_at, sweep, mlo)
    booths = {k: (v["local"] or {}).get("n_both") for k, v in ev0.items()}
    _log("   `V-O4` المقامُ الزوجيّ: " + " · ".join(
        f"{k}={booths[k]}" for k in ("pool",) + GOV_YEARS))
    v4 = (isinstance(booths["pool"], int) and booths["pool"] >= BOTH_POOL
          and all(isinstance(booths[y], int) and booths[y] >= BOTH_YEAR
                  for y in GOV_YEARS))
    _log(f"      الحدُّ: سنةٌ ≥ {BOTH_YEAR} ومجمَّعٌ ≥ {BOTH_POOL} ⟶ "
         f"{'✅' if v4 else '🔴'}")
    if not v4:
        return RC_VO4
    if dry:
        _log("🧪 وضعُ الجدوى انتهى — `V-O4` عبر. **ولا رقمَ حاكمًا صدر** "
             "(لا `Δ` ولا حكمَ أوراكلٍ ولا رِجل).")
        _log("   ⚠️ ودرسُ `T-PMGATE`: **وضعُ الجدوى يُجيز ما يمرّ به وحدَه** — "
             "فلا يُقرأ إذنًا للمسار كلِّه.")
        return 0

    # ⑤ التقييماتُ الأربع × نقطتَي التكلفة
    ev1 = {k: evaluate(v, c_meas, s_meas, ret_at, sweep, mlo)
           for k, v in [("pool", pool)] + [(y, per[y]) for y in GOV_YEARS]}

    # `V-O2` — اقترانُ التفكيك المحلّيّ يوافق حكمَ الأوراكل في الثمانية
    mism = []
    for tag, ev in (("c0", ev0), ("cM", ev1)):
        for k, e in ev.items():
            loc = e["local"]
            exp = "adopt" if (loc and loc["passed"]) else "reject"
            if loc is None or e["verdict"] == "none" or e["verdict"] != exp:
                mism.append(f"{tag}:{k}({e['verdict']}≠{exp})")
    _log(f"   `V-O2` التفكيكُ يوافق الأوراكل (8 تقييمات): "
         f"{'✅' if not mism else '🔴 ' + ' · '.join(mism)}")
    if mism:
        return RC_VO2

    # ⑥ المعاييرُ الثلاثة
    v_pool0, v_poolM = ev0["pool"]["verdict"], ev1["pool"]["verdict"]
    fo1 = (v_pool0 == v_poolM)
    f0 = failing(ev0["pool"]["local"]["legs"])
    fM = failing(ev1["pool"]["local"]["legs"])
    fo2 = (f0 == fM)
    flips = []
    for k in ("pool",) + GOV_YEARS:
        a = ev0[k]["local"]["ma"]
        b = ev1[k]["local"]["ma"]
        if (a > 0) != (b > 0):
            flips.append(f"{k}({a:+.4f}⟶{b:+.4f})")
    fo3 = not flips

    _log("── النتائجُ الحاكمة (المجتمعُ المجمَّع) ──")
    _log(f"   حكمُ الأوراكل: عند (0,0) = **{v_pool0}** · عند القياس = "
         f"**{v_poolM}** ⟶ `FO1` {'✅' if fo1 else '🔴'}")
    _log(f"   الرِّجالُ الساقطة: (0,0) = {sorted(f0) or 'لا شيء'} · القياس = "
         f"{sorted(fM) or 'لا شيء'} ⟶ `FO2` {'✅' if fo2 else '🔴'}")
    _log(f"   إشارةُ `Δ_pair`: {'✅ لا انقلاب' if fo3 else '🔴 ' + ', '.join(flips)}"
         f" ⟶ `FO3` {'✅' if fo3 else '🔴'}")

    _log("── تفكيكٌ وصفيّ: `Δ_pair` ومكوّناتُ الرِّجال ──")
    rows_out = []
    for k in ("pool",) + GOV_YEARS:
        a, b = ev0[k]["local"], ev1[k]["local"]
        _log(f"  {k}: Δ_pair {_num(a['ma'])} ⟶ {_num(b['ma'])} · "
             f"سفليّ {_num(a['la'])} ⟶ {_num(b['la'])} · B {_num(a['mb'])} ⟶ "
             f"{_num(b['mb'])} · تحويل {a['cv_sum']:+.0f} ⟶ {b['cv_sum']:+.0f} "
             f"({a['cv_n']}) · تفادٍ {a['av_sum']:+.0f} ⟶ {b['av_sum']:+.0f} "
             f"({a['av_n']}) · تعبئة "
             f"{(a['fill_ratio'] or 0) * 100:.1f}% · زوجيّ {a['n_both']}")
        for tag, e in (("c0", a), ("cM", b)):
            rows_out.append({"scope": k, "point": tag, "ma": e["ma"],
                             "la": e["la"], "mb": e["mb"], "na": e["na"],
                             "cv_sum": e["cv_sum"], "av_sum": e["av_sum"],
                             "n_both": e["n_both"], "n_bf": e["n_bf"],
                             "n_sf": e["n_sf"],
                             "legs": {n: bool(e["legs"][n]) for n in LEG_NAMES},
                             "verdict": (ev0 if tag == "c0" else ev1)[k][
                                 "verdict"]})
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for r in rows_out:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    blob = open(OUT_ROWS, "rb").read()
    _log(f"   `V-O9` الحتميّة: {OUT_ROWS} = {len(blob)} بايت · "
         f"sha256 {hashlib.sha256(blob).hexdigest()[:16]}")

    crit = {"gates_ok": True, "FO1": fo1, "FO2": fo2, "FO3": fo3}
    branch, why = read_verdict(crit)
    _log(f"⚖️ **الحكم: {why}**")
    if branch == 1:
        _log("   ⇒ يُغلَق البندُ 2 من `PENDING_VERIFICATION.md` لـ`PR-SWEEP` "
             "بدليله · ويُرفَع بانرُ التقييد إلى «قِيس وصمد».")
    elif branch == 2:
        _log("   ⇒ **لا إغلاق** · تُنشَر النتيجةُ بحرفها وتُرفَع للمالك · "
             "**ولا تبنّيَ ولا تغييرَ إنتاجيّ تحت أيّ حال.**")
    return RC_NOVERDICT if branch == 3 else 0


if __name__ == "__main__":
    sys.exit(main())
