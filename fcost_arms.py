#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩸⚙️ `T-FCOST` — تكلفةُ التنفيذ على **محرّك الباكتيست نفسِه** (العقد
`fcost_prereg.md` مدفوعٌ **ومدموجٌ في `main` قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال:** هل ينقلب حكمٌ محرّكيٌّ مقفول حين يُسعَّر التنفيذُ عند المستوى المقيس،
وعند أيّ تكلفةٍ ينقلب؟

🔑 **البنيةُ تُغني عن نصف الحرّاس:** التكلفةُ **لا تغيّر نتيجةَ أيّ صفقة**
(‏`outcome` مستقلٌّ عن `c` و`s`) بل حسابَ عائدها فقط ⇒ **مشيةٌ واحدةٌ لكلّ سنة**
تكفي الشبكةَ كلَّها، والمقارناتُ **داخليّةٌ على المشية نفسِها** فأثرُ الكون يُطرَح.

⚖️ **والهُويّةُ الجبريّة (‏§② من العقد) هي محورُ القراءة كلِّها:**
`ret(c) = k·r₀ + 100(k−1)` حيث `k = (1−c/2)/(1+c/2)` ⇒ الفرقُ على **المحسومة
وحدَها** يتقلّص بـ`k` ولا تنقلب إشارتُه أبدًا، **وينقلب** حين يُحتسَب غيرُ
المُعبَّأ صفرًا بإزاحةٍ `100(k−1)·(f_X − f_Y)` ⇒ **التكلفةُ تحابي الذراعَ التي
تتداول أقلّ**. **وعليه `FC3` هو المعيارُ ذو القيمة و`FC1` مرجَّحةُ العبور
بالجبر** — مُعلَنٌ في العقد §⑩-9 فلا يُقرأ عبورُها إنجازًا.

🔒 **وما لا يُمَسّ:** `_resolve_arm` و`backtest_symbol` والجذورُ الاثنا عشر ·
ولا `CONFIG` تُسنَد في أيّ موضعٍ من هذا الملفّ (الأعلامُ عبر بيئة الطفل حصرًا) ·
ولا قيمةُ `BT_SPREAD_PCT` الافتراضية تتحرّك · ولا إرسال.

⚠️ **وقراءتان مُعلَنتان لغموضٍ في العقد — قبل أيّ رقم:**
1. **`FC1`/`FC2` تُطبَّقان على قراءة كلّ زوجٍ المنشورة** (‏«المحسومة وحدَها» —
   وهي مقياسُ `backtest_2025_live_winrate.md` ومقياسُ `backtest_sweep_compare`
   الذي نُشر تحته حكمُ `T1b`)، **و`FC3` على القراءة (ب)** بنصّ العقد الصريح.
   والقراءةُ الأخرى **تُطبَع دائمًا** فلا يُخفى فرقُهما.
2. **`FC3` تُطبَّق على كلّ زوجٍ تفترق نسبةُ تعبئته فعلًا** لا على `PR-SWEEP`
   وحدَه — لأن العقد يقول «للأزواج المتفاوتة التعبئة»، **والافتراقُ يُقاس ولا
   يُفترَض** (ذراعا الوقف قد تتفاوتا في المحسومة وإن تساوت إشاراتُهما).

🔒 قراءةٌ/بحثٌ فقط · بلا كرون · والنتيجةُ حين تصدر في `fcost_result.md`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import statistics
import subprocess
import sys

# ══════════ ثوابتُ العقد — تُطبَع في كلّ تقرير ══════════
# §③ العائلةُ `S` (سبريدٌ متماثل ذهابًا وإيابًا) — سبعُ قيمٍ لا تتحرّك
CELLS_C = (0.0, 0.01, 0.0132, 0.0175, 0.02, 0.04, 0.08)
# §③ العائلةُ `L` (انزلاقٌ على الخاسر وحدَه) — أربعُ قيمٍ لا تتحرّك
CELLS_S = (0.0, 0.005, 0.01, 0.02)
C_MEAS_LO, C_MEAS_HI = 0.0132, 0.0175   # طرفا وسيط سبريد `T-SLIP-NBBO`
S_MEAS = 0.005                          # من عامليّة `T-SLIP` (‏−0.047R × ρ)
S_HI = 0.017                            # الحدُّ الأعلى (‏−0.157R × ρ) — وصفيّ
BREAKEVEN_MIN = 0.035                   # §⑤ `FC2` = ‏2× الطرفِ الأعلى المقيس
FLOOR_YEAR, FLOOR_TOTAL = 100, 350      # §⑤ أرضيةُ `V-F4` (سابقةُ `T-EXIT`)
GOV_YEARS = ("2023", "2024", "2025")    # §⑤ «السنوات الثلاث»
# §⑦ `V-F6` — المعاملُ المنشور في `T-SLIP` لذراع `P0`: ‏0.093R لكلّ 1%
COEF_LO, COEF_HI = 0.09, 0.11
# §⑦ `V-F2`/`V-F3` — **مجموعةُ الفحص مثبَّتةٌ سلفًا**: شهرٌ تقويميٌّ واحدٌ من
#    السوق الكامل (لا قائمةُ رموزٍ مُختارة قد تخرج فارغةً فيمرَّ الحارسُ خاويًا).
CHECK_YEAR, CHECK_MONTH = "2025", "6"
CHECK_MIN = 30                          # أقلُّ محسومةٍ تجعل الحارسَ ذا معنى
CHECK_C = 0.04                          # التكلفةُ التي يُصادَق عليها من المحرّك
CHECK_TOL = 0.05                        # نقطةٌ مئويّة على المتوسّط
# §⑦ `V-F3`-ب — بصمةُ `BT_CANDLE`: صفرُ تغيّرٍ عند ‏1% ⇒ الأداةُ لا تفعل شيئًا
NOOP_PROBE_C = 0.01

OUT_ROWS = "fcost_rows.jsonl"
TRADES_TMPL = "fcost_trades_{}.json"

# ⚙️ الأعلامُ المُلحِقة — **أسماءُ العقد §⑦ `V-F3` حرفيًّا ولا علمَ زائد**
FLAGS = {"BT_ENVVALS": "1", "BT_POTENTIAL": "1", "BT_SWEEP_ENTRY": "1"}

# 🔒 الجذورُ الاثنا عشر ‏+ محرّكُ الحسم — `V-F8`
ROOTS = ("rank_key", "select_top", "classify_tier", "analyze_ticker",
         "apply_short_gate", "apply_float_gate", "scan_market",
         "backtest_symbol", "scan_ignition", "scan_split_hunter",
         "entry_status", "build_interpretation", "_resolve_arm")

# 🔢 رموزُ الخروج — **متمايزةٌ عمدًا** فلا يُقرأ حارسٌ خللًا في السجلّ.
#    ‏2 مدخلٌ · 3 فحصٌ ذاتيٌّ/جذور · 4 طفلٌ/لقطة · 5 `V-F2` · 6 `V-F3` ·
#    7 `V-F5` · **8 محجوزٌ للإغلاق** · **9 «لا حكم» (الفرعُ 3)**
RC_INPUT, RC_SELF, RC_CHILD = 2, 3, 4
RC_VF2, RC_VF3, RC_VF5, RC_NOVERDICT = 5, 6, 7, 9

# 🧩 خريطةُ الأذرع ⟵ حقولِ المحرّك (‏§④) — **مصدرٌ واحدٌ لا خريطتان**
ARM_FIELDS = {
    "A":   ("outcome", "ret_a"),            # وقفُ الذيل — الإنتاج
    "B":   ("outcome_b", "ret_b"),          # وقفُ الإغلاق
    "LEG": ("outcome_legacy", "ret_legacy"),  # تفاؤلُ شمعة التعبئة (‏F-L1)
    "SW":  ("outcome_sweep", "ret_sweep_a"),  # ‏T1b دخولُ المسح-الاستعادة
}
# §④ الأزواجُ الثلاثة — (الاسم، الذراعُ المقابَلة، الأساس)
PAIRS = (("PR-STOP", "B", "A"), ("PR-LEGACY", "LEG", "A"),
         ("PR-SWEEP", "SW", "A"))


def _log(msg: str) -> None:
    print(msg, flush=True)


def _num(v, nd: int = 4) -> str:
    """عرضٌ فاشلٌ-آمن: الغائبُ «—» ولا ينهار التنسيق (‏الصنفُ ① في الأداة)."""
    return "—" if v is None else f"{v:+.{nd}f}" if nd >= 3 else f"{v:.{nd}f}"


# ══════════════════ ① الجبرُ — دوالٌّ نقيّةٌ مقفولة ══════════════════
def k_of(c: float) -> float:
    """معاملُ السبريد `k(c) = (1−c/2) ÷ (1+c/2)` — و`k(0) = 1.0` بالضبط."""
    return (1.0 - c / 2.0) / (1.0 + c / 2.0)


def ret_at(r0: float, outcome: str, c: float, s: float) -> float:
    """العائدُ بعد التكلفة: سبريدٌ على الجهتين ‏+ انزلاقٌ **على الخاسر وحدَه**.

    `ret = 100·[(1 + r₀/100)·f_s·k − 1]` حيث `f_s = 1−s` للخاسر و‏1 لغيره.
    🔒 **وعند `k = 1` و`f = 1` يُرجَع `r₀` نفسُه** — الضربُ في واحدٍ هُويّةٌ
    رياضيّة، وبها يصير `V-F1` **بت-بت** لا «ضمن تسامح» (‏دورةُ الفاصلة العائمة
    `((1+r/100)−1)·100` لا تُعيد `r` بالضبط)."""
    k = k_of(c)
    f = (1.0 - s) if outcome == "loss" else 1.0
    if k == 1.0 and f == 1.0:
        return float(r0)
    return ((1.0 + r0 / 100.0) * f * k - 1.0) * 100.0


def arm_view(rows: list, arm: str) -> list:
    """صفوفُ ذراعٍ بعينها: `(outcome, r₀)` للمحسومة فقط — و`None` تُسقَط."""
    okey, rkey = ARM_FIELDS[arm]
    out = []
    for t in rows or []:
        o = (t or {}).get(okey)
        r = (t or {}).get(rkey)
        if o in ("win", "loss") and r is not None:
            out.append((o, float(r)))
    return out


def e_resolved(view: list, c: float, s: float):
    """`E` = متوسّطُ العائد لكلّ صفقةٍ **محسومة** (مقياسُ التقرير المنشور)."""
    if not view:
        return None
    return sum(ret_at(r, o, c, s) for o, r in view) / float(len(view))


def e_zerofill(view: list, n_all: int, c: float, s: float):
    """قراءةُ (ب): المقامُ **كلُّ الإشارات** وغيرُ المحسوم صفرٌ — اتّفاقيةُ
    أذرع الدخول عندنا، وهي التي تُبقي إزاحةَ `100(k−1)·f`."""
    if not n_all:
        return None
    return sum(ret_at(r, o, c, s) for o, r in view) / float(n_all)


def fill_frac(view: list, n_all: int):
    return (len(view) / float(n_all)) if n_all else None


def offset_at(c: float, f_x: float, f_y: float) -> float:
    """إزاحةُ التعبئة `100(k−1)·(f_X − f_Y)` — سالبةٌ دائمًا للأكثر تعبئة."""
    return 100.0 * (k_of(c) - 1.0) * (f_x - f_y)


def breakeven_c(view_x: list, view_y: list, n_all: int, s: float,
                zerofill: bool, hi: float = 0.50, step: float = 0.001):
    """أصغرُ `c` تقلب **إشارةَ** الفرق — أو `None` إن لم يوجد ضمن `hi`.

    🔑 وعلى قراءة «المحسومة وحدَها» يستحيل الانقلابُ جبريًّا (اللازمُ ②) فتُرجَع
    `None` — **وهذا يُحسَب ولا يُفترَض**: الدالّةُ تمشي السلّمَ فعلًا."""
    def delta(c):
        if zerofill:
            a = e_zerofill(view_x, n_all, c, s)
            b = e_zerofill(view_y, n_all, c, s)
        else:
            a = e_resolved(view_x, c, s)
            b = e_resolved(view_y, c, s)
        return None if (a is None or b is None) else (a - b)

    d0 = delta(0.0)
    if d0 is None or d0 == 0.0:
        return None
    sign0 = 1.0 if d0 > 0 else -1.0
    c = step
    while c <= hi + 1e-12:
        d = delta(c)
        if d is not None and (1.0 if d > 0 else -1.0) != sign0:
            return round(c, 6)
        c += step
    return None


# ══════════════════ ② الحكم — يطبّق §⑥ بحرفه ══════════════════
def read_verdict(crit: dict, floor: dict) -> tuple:
    """الفروعُ الثلاثة بنصّ §⑥ — **الأرضيةُ أوّلًا** ثمّ المعاييرُ الثلاثة.

    `crit` = {"FC1": bool, "FC2": bool, "FC3": bool} ·
    `floor` = {"ok": bool, "why": str}."""
    lines = []
    if not floor.get("ok"):
        lines.append(f"⚖️ الفرعُ 3 — «لا حكم»: الأرضيةُ `V-F4` ساقطة ({floor.get('why')})")
        lines.append("   ويُكتب في ملفّ النتيجة **تاريخُ إعادة قراءةٍ صريح**.")
        return 3, lines
    ok = all(bool(crit.get(k)) for k in ("FC1", "FC2", "FC3"))
    if ok:
        lines.append("⚖️ الفرعُ 1 — الأحكامُ المحرّكيّةُ **تصمد** أمام تكلفة التنفيذ")
        lines.append("   ⇒ يُغلَق البندُ 2 من `PENDING_VERIFICATION.md` بدليله.")
        return 1, lines
    bad = [k for k in ("FC1", "FC2", "FC3") if not crit.get(k)]
    lines.append(f"⚖️ الفرعُ 2 — **لا إغلاق**: سقط {' و'.join('`' + b + '`' for b in bad)}")
    lines.append("   والزوجُ الساقطُ وحدَه يُوسَم ببانرِ تقييدٍ في ملفّ نتيجته.")
    return 2, lines


# ══════════════════ ③ حرّاسُ الصلاحية ══════════════════
def selfcheck_readonly() -> bool:
    """`V-F7`-ب — قراءةٌ فقط بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة، ولا يُفتَح
    للكتابة إلّا `OUT_ROWS` أو ملفُّ صفقاتٍ مؤقّت."""
    banned = {"send_telegram", "send_telegram_document", "git_save",
              "save_watchlist", "save_op_entry_state", "record_new_alerts",
              "save_near_watch", "save_hunter_watch"}
    allowed = {"OUT_ROWS", "_tp"}
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(ch in mode for ch in ("w", "a", "x", "+")):
                if not (n.args and isinstance(n.args[0], ast.Name)
                        and n.args[0].id in allowed):
                    return False
    return True


def no_config_assign() -> bool:
    """`V-F9` — **أشدُّ من القائمة البيضاء**: صفرُ إسنادٍ إلى `CONFIG` إطلاقًا.

    الأعلامُ تمرّ عبر **بيئة الطفل** فيقرؤها `_apply_backtest_overrides` في وضع
    `BACKTEST` حصرًا ⇒ الإنتاجُ محصَّنٌ بقفل `B1` القائم، ولا ذراعَ هنا تضبط
    إعدادًا في الذاكرة (‏وهو بعينه ما كان يفعله `T-RSI40`)."""
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        tgts = []
        if isinstance(n, ast.Assign):
            tgts = list(n.targets)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            tgts = [n.target]
        for t in tgts:
            if isinstance(t, ast.Subscript):
                base = t.value
                nm = getattr(base, "id", None) or getattr(base, "attr", None)
                if nm == "CONFIG":
                    return False
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Attribute) and f.attr in ("update", "setdefault")
                    and (getattr(f.value, "id", None)
                         or getattr(f.value, "attr", None)) == "CONFIG"):
                return False
    return True


def roots_identical() -> tuple:
    """`V-F8` — بصمةُ AST للجذور الاثني عشر ‏+ `_resolve_arm` مقابل `origin/main`.

    ⚠️ **وتُقرأ على الرنر من `main` فالشجرةُ نظيفة** — ولا يُبنى عليها قفلُ سويّةٍ
    سلوكيّ (درسُ `RSK3`: حارسٌ يفترض شجرةً نظيفةً يُحمّر البوّابةَ على كلّ تعديل)."""
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


# ══════════════════ ④ المشي — طفلٌ معزولٌ لكلّ قياس ══════════════════
def child_env(frozen: str, extra=None) -> dict:
    """بيئةُ الطفل: وضعُ الباكتيست ‏+ الأعلامُ المُلحِقة ‏+ اللقطة المجمَّدة.

    🔒🔴 **وتُجرَّد مفاتيحُ تلغرام بنيويًّا:** الطفلُ ينادي `run_backtest` وفيها
    إرسالٌ ووثائقُ CSV **بلا حارس** ⇒ لا يُتَّكل على غيابِ سرٍّ في workflow واحد."""
    env = {**dict(os.environ), **FLAGS, "BT_FROZEN_PATH": frozen}
    env.update(extra or {})
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_BOT_TOKEN_2",
              "TG_BOT_TOKEN", "TG_CHAT_ID"):
        env.pop(k, None)
    env["SCREENER_MODE"] = "BACKTEST"
    return env


def _run_child(tag: str, frozen: str, extra: dict) -> dict:
    env = child_env(frozen, extra)
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child",
                        tag], capture_output=True, text=True, env=env)
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    for ln in blob.splitlines():
        if not ln.startswith("FCOST_CHILD:"):
            _log(f"  [{tag}] {ln}")
    rows = [x for x in blob.splitlines() if x.startswith("FCOST_CHILD:")]
    if p.returncode != 0 or not rows:
        return {}
    return json.loads(rows[-1].split("FCOST_CHILD:", 1)[1])


def run_child(tag: str) -> int:
    """يُشغّل الباكتيست في عمليةٍ ابنة ويكتب صفقاتها — **بلا أيّ حسابِ تكلفة**."""
    import Super_stock as S                                      # noqa: PLC0415
    fz = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    snap = {"asof": None, "n": None}
    if fz:
        try:
            hist, _sp, asof = S.load_frozen_dataset(fz)
            snap = {"asof": (str(asof) if asof else None),
                    "n": (len(hist) if hist else 0)}
        except Exception as e:                                   # noqa: BLE001
            _log(f"⛔ لقطةٌ غيرُ مقروءة: {type(e).__name__}")
            return RC_CHILD
    _log(f"SNAP {tag} as-of={snap['asof']} n_symbols={snap['n']}")
    trades = S.run_backtest() or []
    _tp = TRADES_TMPL.format(tag)
    with open(_tp, "w", encoding="utf-8") as fh:
        json.dump(trades, fh, ensure_ascii=False, default=str)
    meta = {"tag": tag, "snap": snap, "n": len(trades), "path": _tp,
            # 🔒 برهانٌ لا زينة: قيمةُ السبريد النافذةُ داخل الطفل تُطبَع.
            "spread": float(S.CONFIG.get("BT_SPREAD_PCT") or 0.0),
            "sweep_on": bool(S.CONFIG.get("BT_SWEEP_ENTRY"))}
    print("FCOST_CHILD:" + json.dumps(meta, ensure_ascii=False))
    return 0


def _load(meta: dict) -> list:
    try:
        return json.load(open(meta["path"], encoding="utf-8"))
    except Exception:                                            # noqa: BLE001
        return []


def _key(t: dict) -> tuple:
    return (str((t or {}).get("symbol")), str((t or {}).get("date")))


# ══════════════════ ⑤ الحرّاسُ المقارنة ══════════════════
def check_noop(rows_off: list, rows_on: list) -> tuple:
    """`V-F3`-أ — الأعلامُ **مُلحِقةٌ لا مغيِّرة**: `outcome`/`ret_a` متطابقان."""
    a = {_key(t): (t.get("outcome"), t.get("ret_a")) for t in rows_off}
    b = {_key(t): (t.get("outcome"), t.get("ret_a")) for t in rows_on}
    if not a or not b:
        return False, "مجموعةٌ فارغة"
    if set(a) != set(b):
        return False, f"العضويةُ تفرّقت ({len(a)} مقابل {len(b)})"
    bad = [k for k in a if a[k] != b[k]]
    return (not bad), ("مطابق" if not bad else f"{len(bad)} صفًّا تفرّق")


def check_transform(rows_zero: list, rows_c: list, c: float) -> tuple:
    """`V-F2` — التحويلُ البعديُّ **مُصادَقٌ على المحرّك نفسِه** عند `c`."""
    z = {_key(t): t for t in rows_zero}
    got, exp = [], []
    for t in rows_c:
        k = _key(t)
        src = z.get(k)
        if src is None:
            continue
        o, r = t.get("outcome"), t.get("ret_a")
        o0, r0 = src.get("outcome"), src.get("ret_a")
        if o not in ("win", "loss") or o != o0 or r is None or r0 is None:
            continue
        got.append(float(r))
        exp.append(ret_at(float(r0), o0, c, 0.0))
    if len(got) < CHECK_MIN:
        return False, f"عيّنةٌ دون الحدّ ({len(got)} < {CHECK_MIN})", None
    d = abs(sum(got) / len(got) - sum(exp) / len(exp))
    return (d <= CHECK_TOL), f"n={len(got)} · فارقُ المتوسّط={d:.4f} نقطة", d


def rho_coef(rows: list):
    """`V-F6` — `ρ` وسيطًا والمعاملُ `0.01 ÷ ρ` (يُقارَن بـ‏0.093R المنشور)."""
    vals = []
    for t in rows or []:
        e, s = (t or {}).get("entry"), (t or {}).get("stop")
        try:
            e, s = float(e), float(s)
        except (TypeError, ValueError):
            continue
        if e > 0 and s > 0 and e > s:
            vals.append((e - s) / e)
    if not vals:
        return None, None
    med = statistics.median(vals)
    return med, (0.01 / med if med else None)


def changed_count(view: list, c: float) -> int:
    """`V-F3`-ب — كم صفقةً يتغيّر عائدُها عند `c` (بصمةُ `BT_CANDLE`)."""
    return sum(1 for o, r in view if ret_at(r, o, c, 0.0) != r)


# ══════════════════ ⑥ المسار الرئيس ══════════════════
def main() -> int:                                               # noqa: PLR0911
    years = [x.strip() for x in
             str(os.environ.get("FCOST_YEARS", "")).split(",") if x.strip()]
    frozen = [x.strip() for x in
              str(os.environ.get("FCOST_FROZEN", "")).split(",") if x.strip()]
    dry = str(os.environ.get("FCOST_DRY", "")).strip() == "1"
    if not years or len(years) != len(frozen):
        _log("⛔ يلزم FCOST_YEARS و FCOST_FROZEN بالعدد نفسِه وبالترتيب نفسِه")
        return RC_INPUT
    if any(y not in ("2023", "2024", "2025", "2026") for y in years):
        _log("⛔ سنةٌ غيرُ مسموحة")
        return RC_INPUT
    if not dry and sorted(years) != sorted(GOV_YEARS):
        _log(f"⛔ الحكمُ يشترط السنواتِ الثلاث {GOV_YEARS} بنصّ §⑤")
        return RC_INPUT

    _log("🩸⚙️ T-FCOST — تكلفةُ التنفيذ على محرّك الباكتيست")
    _log(f"   سلّمُ c={[round(x, 4) for x in CELLS_C]} · s={list(CELLS_S)}")
    _log(f"   الخليّةُ المقيسة: c*∈{{{C_MEAS_LO}, {C_MEAS_HI}}} · s*={S_MEAS}")
    _log(f"   الأرضية: {FLOOR_YEAR}/سنة · {FLOOR_TOTAL} مجمَّعًا · "
         f"تعادلُ `FC2` ≥ {BREAKEVEN_MIN}")
    if dry:
        _log("🧪 وضعُ الجدوى: **صفرُ Δ وصفرُ نقطةِ تعادلٍ وصفرُ حكم** — "
             "سؤالُه الوحيد: هل تعبر `V-F4`؟")
        _log("   ⚠️ ودرسُ `T-PMGATE`: وضعُ الجدوى يُجيز ما يمرّ به وحدَه.")

    if not selfcheck_readonly():
        _log("⛔ `V-F7`-ب: الأداةُ ليست قراءةً فقط")
        return RC_SELF
    if not no_config_assign():
        _log("⛔ `V-F9`: إسنادٌ إلى CONFIG داخل الأداة")
        return RC_SELF
    ok8, why8 = roots_identical()
    _log(f"🔒 `V-F8` الجذور: {why8}")
    if not ok8:
        return RC_SELF

    # ── المشيُ: طفلٌ لكلّ سنة (‏بلا أيّ تكلفة — التكلفةُ حسابٌ بعديّ) ──
    data, rows_all = {}, {}
    for y, fz in zip(years, frozen):
        _log(f"▶️ مشيُ {y} …")
        meta = _run_child(y, fz, {"BACKTEST_YEAR": y})
        if not meta:
            _log(f"⛔ سقط طفلُ {y}")
            return RC_CHILD
        rows = _load(meta)
        if not rows:
            _log(f"⛔ صفرُ صفقاتٍ في {y}")
            return RC_CHILD
        data[y], rows_all[y] = meta, rows
        _log(f"   {y}: إشارات={len(rows)} · لقطة as-of={meta['snap']['asof']} "
             f"· رموز={meta['snap']['n']} · سبريدُ الطفل={meta['spread']}")

    # ── الأرضيةُ `V-F4` ومستوى `PR-HEAD` ──
    views = {y: {a: arm_view(rows_all[y], a) for a in ARM_FIELDS} for y in years}
    floor_bad, tot = [], 0
    for y in years:
        for a in ARM_FIELDS:
            n = len(views[y][a])
            if a in ("A", "B", "LEG") and n < FLOOR_YEAR:
                floor_bad.append(f"{y}/{a}={n}")
        tot += len(views[y]["A"])
    if tot < FLOOR_TOTAL:
        floor_bad.append(f"مجمَّع A={tot}<{FLOOR_TOTAL}")
    floor = {"ok": not floor_bad, "why": ("مستوفاة" if not floor_bad
                                          else " · ".join(floor_bad))}
    _log(f"🚧 `V-F4` الأرضية: {floor['why']}")

    for y in years:
        n_all = len(rows_all[y])
        va = views[y]["A"]
        wins = sum(1 for o, _ in va if o == "win")
        wr = (100.0 * wins / len(va)) if va else None
        e0 = e_resolved(va, 0.0, 0.0)
        ff = fill_frac(va, n_all)
        rho, coef = rho_coef(rows_all[y])
        _log(f"📊 {y} `PR-HEAD`: إشارات={n_all} · محسومة={len(va)} · "
             f"نجاح={_num(wr, 1)}% · E_A(0,0)={_num(e0, 3)} نقطة · "
             f"تعبئة={_num(ff, 3)}")
        _log(f"   ρ وسيط={_num(rho, 4)} ⇒ معاملُ 1% = {_num(coef, 4)}R "
             f"(المنشور 0.093R) — `V-F6` "
             f"{'✅' if (coef and COEF_LO <= coef <= COEF_HI) else '⚠️ خارج النطاق'}")
        if not (coef and COEF_LO <= coef <= COEF_HI):
            _log("   ⚠️ المجتمعان مختلفان بالتصميم ⇒ تُقرأ النتيجةُ مقيَّدة "
                 "(تحذيرٌ لا خروج، بنصّ `V-F6`)")
        # حدُّ التقريب المنشور في §⑩-6
        if va:
            _log(f"   📐 حدُّ تقريبِ المحرّك على المتوسّط ≤ "
                 f"{0.029 / (len(va) ** 0.5):.4f} نقطة")

    if dry:
        _log("🧪 انتهى وضعُ الجدوى — لا Δ ولا تعادل ولا حكم.")
        return 0

    # ── `V-F3`-ب: الأداةُ تفعل شيئًا فعلًا ──
    ch = sum(changed_count(views[y]["A"], NOOP_PROBE_C) for y in years)
    _log(f"🧪 `V-F3`-ب: صفقاتٌ يتغيّر عائدُها عند {NOOP_PROBE_C:.0%} = {ch}")
    if ch == 0:
        _log("⛔ صفرُ تغيّرٍ ⇒ الأداةُ `no-op` (بصمةُ `BT_CANDLE`)")
        return RC_VF3

    # ── `V-F5`: النتيجةُ والعددُ لا يتحرّكان عبر الشبكة ──
    base = {y: (len(views[y]["A"]),
                sum(1 for o, _ in views[y]["A"] if o == "win"))
            for y in years}
    for c in CELLS_C:
        for s in CELLS_S:
            for y in years:
                v = [(o, ret_at(r, o, c, s)) for o, r in views[y]["A"]]
                if (len(v), sum(1 for o, _ in v if o == "win")) != base[y]:
                    _log("⛔ `V-F5`: النتيجةُ أو العددُ تحرّك بالتكلفة")
                    return RC_VF5
    _log("🔒 `V-F5`: النجاحُ والعددُ متطابقان في كلّ خلايا الشبكة ✅")

    # ── `V-F2`/`V-F3`-أ: مصادقةُ التحويل على المحرّك + حارسُ الـ`no-op` ──
    fz0 = frozen[years.index(CHECK_YEAR)] if CHECK_YEAR in years else frozen[0]
    cmn = {"BACKTEST_YEAR": CHECK_YEAR, "BACKTEST_MONTH": CHECK_MONTH}
    _log(f"▶️ حرّاسُ المصادقة على {CHECK_YEAR}-{CHECK_MONTH} …")
    m_on = _run_child("chk_on", fz0, cmn)
    m_off = _run_child("chk_off", fz0, {**cmn, **{k: "" for k in FLAGS}})
    m_c4 = _run_child("chk_c4", fz0, {**cmn, "BT_SPREAD_PCT": str(CHECK_C)})
    if not (m_on and m_off and m_c4):
        _log("⛔ سقط أحدُ أطفال المصادقة")
        return RC_CHILD
    r_on, r_off, r_c4 = _load(m_on), _load(m_off), _load(m_c4)
    ok3, why3 = check_noop(r_off, r_on)
    _log(f"🔒 `V-F3`-أ الأعلامُ مُلحِقةٌ لا مغيِّرة: {why3}")
    if not ok3:
        return RC_VF3
    ok2, why2, _d2 = check_transform(r_on, r_c4, CHECK_C)
    _log(f"🔒 `V-F2` التحويلُ مقابل المحرّك عند {CHECK_C:.0%}: {why2}")
    if not ok2:
        return RC_VF2

    # ── `V-F1`: الخليّةُ (0,0) = مُخرَجُ المحرّك بت-بت ──
    bad1 = 0
    for y in years:
        for o, r in views[y]["A"]:
            if ret_at(r, o, 0.0, 0.0) != r:
                bad1 += 1
    _log(f"🔒 `V-F1` الخليّةُ (0,0) بت-بت: مخالفات={bad1}")
    if bad1:
        return RC_SELF

    # ── الشبكةُ والأزواج ──
    out = open(OUT_ROWS, "w", encoding="utf-8")
    fc1, fc2, fc3 = True, True, True
    fc1_bad, fc2_bad, fc3_bad = [], [], []
    for name, x, y_arm in PAIRS:
        _log(f"── الزوج {name} ({x} − {y_arm}) ──")
        for yr in years:
            n_all = len(rows_all[yr])
            vx, vy = views[yr][x], views[yr][y_arm]
            fx, fy = fill_frac(vx, n_all), fill_frac(vy, n_all)
            if not vx or not vy:
                _log(f"  {yr}: ⛔ ذراعٌ بلا محسومة ({x}={len(vx)} · "
                     f"{y_arm}={len(vy)}) ⇒ الزوجُ يُتخطّى **مُعلَنًا** لهذي السنة")
                continue
            d0 = e_resolved(vx, 0.0, 0.0) - e_resolved(vy, 0.0, 0.0)
            z0 = (e_zerofill(vx, n_all, 0.0, 0.0)
                  - e_zerofill(vy, n_all, 0.0, 0.0))
            _log(f"  {yr}: Δ(أ المحسومة)={d0:+.4f} · Δ(ب صفرُ التعبئة)={z0:+.4f}"
                 f" · تعبئة {x}={fx:.3f} مقابل {y_arm}={fy:.3f}")
            # `FC1` — ثباتُ الإشارة داخل المدى المقيس (قراءةُ الزوج المنشورة)
            s0 = (1 if d0 > 0 else -1) if d0 else 0
            for c in [c for c in CELLS_C if c <= C_MEAS_HI + 1e-12]:
                for s in [s for s in CELLS_S if s <= S_MEAS + 1e-12]:
                    dd = e_resolved(vx, c, s) - e_resolved(vy, c, s)
                    sd = (1 if dd > 0 else -1) if dd else 0
                    if s0 and sd != s0:
                        fc1 = False
                        fc1_bad.append(f"{name}/{yr}/c={c}/s={s}")
                    zz = (e_zerofill(vx, n_all, c, s)
                          - e_zerofill(vy, n_all, c, s))
                    out.write(json.dumps(
                        {"pair": name, "year": yr, "c": c, "s": s,
                         "d_resolved": dd, "d_zerofill": zz,
                         "f_x": fx, "f_y": fy}, ensure_ascii=False) + "\n")
            # `FC2` — هامشُ التعادل عند `s*` (قراءةُ الزوج المنشورة)
            be = breakeven_c(vx, vy, n_all, S_MEAS, zerofill=False)
            be_b = breakeven_c(vx, vy, n_all, S_MEAS, zerofill=True)
            _log(f"      تعادلُ (أ) = {'لا تعادلَ منتهٍ' if be is None else f'{be:.4f}'}"
                 f" · تعادلُ (ب) = "
                 f"{'لا تعادلَ منتهٍ' if be_b is None else f'{be_b:.4f}'}")
            if be is not None and be < BREAKEVEN_MIN:
                fc2 = False
                fc2_bad.append(f"{name}/{yr}={be:.4f}")
            # `FC3` — سقفُ إزاحة التعبئة (قراءةُ (ب) بنصّ العقد)
            if fx is not None and fy is not None and abs(fx - fy) > 1e-12:
                off = abs(offset_at(C_MEAS_HI, fx, fy))
                _log(f"      `FC3` إزاحةٌ عند {C_MEAS_HI:.4f} = {off:.4f} "
                     f"مقابل |Δ(0) ب| = {abs(z0):.4f}")
                if not (off < abs(z0)):
                    fc3 = False
                    fc3_bad.append(f"{name}/{yr} off={off:.4f} ≥ |Δ|={abs(z0):.4f}")
            else:
                _log("      `FC3` لا ينطبق (نسبتا التعبئة متساويتان)")
    out.close()

    _log(f"🎯 `FC1` {'✅' if fc1 else '🔴 ' + ' · '.join(fc1_bad[:4])}")
    _log(f"🎯 `FC2` {'✅' if fc2 else '🔴 ' + ' · '.join(fc2_bad[:4])}")
    _log(f"🎯 `FC3` {'✅' if fc3 else '🔴 ' + ' · '.join(fc3_bad[:4])}")
    branch, lines = read_verdict({"FC1": fc1, "FC2": fc2, "FC3": fc3}, floor)
    for ln in lines:
        _log(ln)
    _log(f"📄 الصفوف: {OUT_ROWS}")
    return RC_NOVERDICT if branch == 3 else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--child":
        sys.exit(run_child(sys.argv[2]))
    sys.exit(main())
