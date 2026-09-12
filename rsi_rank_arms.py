#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📉🚦 `T-RSI-RANK` — **RSI مفتاحَ ترتيبٍ لا بوّابةَ رفض** (العقد
`rsi_rank_prereg.md` مدفوعٌ **ومدموجٌ في `main` قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال:** داخل المرشّحين المؤهَّلين وبميزانيّةٍ ثابتة — هل تقديمُ مَن `RSI`ه في
منطقة فيصل ‏[23, 27] يُسلّم منفجرين أكثر؟ **صفرُ مُقصًى وصفرُ مُسلَّمٍ يُفقَد.**

🔑 **البنيةُ تُغني عن نصف الحرّاس:** باكتيستٌ **واحدٌ لكلّ سنة** ⇒ مجموعةُ
المرشّحين **كائنٌ واحد** تُعاد عليها ستُّ إعاداتٍ بمُرتِّباتٍ مختلفة ⇒ الميزانيةُ
والمحورُ والكونُ والنافذةُ **متطابقةٌ بالبناء لا بالدعوى** (‏`V-K3`/`V-K4`).

🔒 **وما لا يُمَسّ:** `rank_key` في `Super_stock.py` (الحقنُ عبر `replay(ranker=)`)
· ولا `CONFIG` تُضبَط في أيّ موضع · ولا عتبةَ فرزٍ تتحرّك · ولا إرسال.

⚠️ **حدُّ صدقٍ في البوتستراب — يُعلَن قبل أيّ رقم:** الفاصلُ **عنقوديٌّ بالرمز**
كما ينصّ العقد، ويُعاد أخذُ **مساهمةِ كلّ رمزٍ المحقَّقة** في الفرق — **ولا تُعاد
آلةُ التخصيص داخل كلّ إعادة** (ذلك صحيحٌ نظريًّا ومستحيلٌ حسابيًّا: ‏5,000 × ستّ
أذرعٍ × ثلاث سنوات). ⇒ الفاصلُ يقيس تشتّتَ المساهمات لا اقترانَ الخانات.

⚠️ **وقراءةٌ مُعلَنةٌ لغموضٍ في العقد — قبل أيّ رقم:** `C-RAND` نصُّه «`rank_live`
بكاسرِ تعادلٍ عشوائيٍّ حتميّ»، و`rank_live` **ينتهي بـ`seq` فهو ترتيبٌ كلّيٌّ بلا
تعادل** ⇒ عشوائيٌّ **بعده** شاهدٌ ميّت يُطابق `K0` بت-بت. فالمنفَّذ: العشوائيُّ
يشغل **خانةَ كاسر التعادل نفسَها** (مكانَ `seq`) — وهو المعنى الوحيد الذي يجعله
شاهدًا. **ويُطبَع تطابقُه مع `K0` في كلّ سنة** فلو صار ميّتًا يُقرأ ولا يُخفى.
📌 **ومعه `D-RAND` — عشوائيٌّ كاملٌ وصفيٌّ لا يحكم** (‏`make_rank_random`)، لأن
تبريرَ العقد نفسِه يستند إلى `T-RANK-DENSE` وقياسُه كان على العشوائيّ الكامل.
**ولا يدخل `RK3` ولا أيَّ معيار** — يُطبَع ليُقرأ الغموضُ لا ليُحسَم به.

🔒 قراءةٌ/بحثٌ فقط · بلا كرون · والنتيجةُ حين تصدر في `rsi_rank_result.md`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import subprocess
import sys

import ceiling_arms as CA
# ── الاستيرادُ بالاسم = التجميدُ بالبناء (‏§⓪-ج من العقد) ──
from replay10 import (CAPACITY, candidates_from_trades, make_rank_random,
                      r_unit, rank_live, replay)

# ══════════ ثوابتُ العقد — تُطبَع في كلّ تقرير (‏`V-K8`) ══════════
BAND_LO, BAND_HI = 23.0, 27.0   # 🥇 حدّا فيصل حرفيًّا (ص65 · `TG_2043` · GWAV ص91)
D100 = 100.0                    # المقياسُ الحاكم `FWD` = مُسلَّمون بلغوا ‏+100%
FLOOR_FILLED = 100              # `engineering` — نفسُ أرضية `T-RSI40` فيُقارَن
BOOT, BOOT_SEED = 5000, 20260911
RAND_SEED = 20260911            # بذرةُ `C-RAND`/`D-RAND` — ثابتةٌ وتُطبَع
OUT_ROWS = "rsi_rank_rows.jsonl"
TRADES_TMPL = "rsi_rank_trades_{}.json"
# 📌 مرجعُ `V-K2` — **أرقامٌ منشورة** في `rsi40_result.md §②` لذراع الأساس `H0`
#    (نفسُ السعة ونفسُ `rank_live` ونفسُ اللقطات) ⇒ `K0` يجب أن يُعيدها.
PUBLISHED_K0_D100 = {"2023": 13, "2024": 9, "2025": 12}
# 📌 «السنواتُ الثلاث» بنصّ §④ — وهي **نفسُها** سنواتُ المرجع المنشور أعلاه.
GOV_YEARS = ("2023", "2024", "2025")
GOV_ARMS = ("K0", "K27", "C-DEPTH", "C-RAND")   # ما تقوم عليه المعايير
DESC_ARMS = ("KC", "KR", "D-RAND")              # وصفيٌّ لا يحكم


def _log(m):
    print(m, flush=True)


# ══════════ دوالُّ نقيّة — المُرتِّبات ══════════
def _env(c, key, default):
    """قراءةُ حقلٍ من `env_vals` لحظةَ الإشارة — **والغيابُ لا يُخمَّن**.

    🔴 و`NaN` **ليس** `None` (عيبٌ مقيسٌ عندنا أسقط بوّابةً **مفتوحة**) ⇒
    يُقارَن بنفسه صراحةً."""
    v = (c.payload.get("env_vals") or {}).get(key)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return default if v != v else v


def band_of(c) -> int:
    """‏0 = داخل منطقة فيصل ‏[23, 27] · ‏1 = خارجها **أو غائبة**.

    والغيابُ يُعامَل «خارج المنطقة» فينزل لآخر فئته — **نفسُ عُرف `rank_live`**
    مع `in_band` (لا يُدَّعى قربٌ بلا دليل)."""
    v = _env(c, "rsi_now", None)
    if v is None:
        return 1
    return 0 if BAND_LO <= v <= BAND_HI else 1


def k_base(c) -> tuple:
    """`K0` — مُرتِّبُ الإنتاج **بت-بت** (`replay10.rank_live` بلا زيادةٍ ولا نقص)."""
    return tuple(rank_live(c))


def k_band(c) -> tuple:
    """`K27` 🥇 — **ثنائيٌّ ثمّ `rank_live` حرفيًّا** (سابقةُ `T-PROX` التي شحنها
    المالك: «ثنائيٌّ لا مستمرّ، وترتيبٌ لا رفض») ⇒ **داخلَ كلّ فئةٍ الترتيبُ
    byte-identical** مع الإنتاج، ولا يُقصى أحد."""
    return (band_of(c),) + tuple(rank_live(c))


def k_inv(c) -> tuple:
    """`KR` **وصفيّة** — المنطقةُ **مقلوبة** (خارجها أوّلًا). شاهدُ اتّجاه: إن لم
    تكن أسوأَ من `K0` فالمفتاحُ صدفة (‏`P4`)."""
    return (1 - band_of(c),) + tuple(rank_live(c))


def k_cont(c) -> tuple:
    """`KC` **وصفيّة** — الأدنى `RSI` أوّلًا (رتيبٌ لا منطقة): أهي **المنطقةُ**
    أم «كلّما انخفض كان أفضل»؟ والغيابُ ينزل لآخر (‏999)."""
    return (_env(c, "rsi_now", 999.0),) + tuple(rank_live(c))


def c_depth(c) -> tuple:
    """`C-DEPTH` **ضبطٌ حاكم** — الأعمقُ هبوطًا أوّلًا بـ`drop_pct`، وهو **عمقٌ
    سعريٌّ خالٍ من RSI** ⇒ يعزل «مرجعَ فيصل» عن «العمق الخام».

    ⚠️ و`env_depth` **لا يصلح** هنا لأن `rsi_now` أحدُ معاييره (‏`CRITERIA`)
    فهو ملوَّثٌ بالمقيس — مُعلَنٌ في العقد §⓪-ج."""
    return (-_env(c, "drop_pct", -1.0),) + tuple(rank_live(c))


def make_c_rand(seed: int):
    """`C-RAND` **ضبطٌ حاكم** — `rank_live` وكاسرُ تعادلِه **عشوائيٌّ حتميّ**.

    🔑 والعشوائيُّ يشغل **خانةَ `seq`** لا ما بعدها: `rank_live` ينتهي بـ`seq`
    فهو ترتيبٌ كلّيٌّ **بلا تعادل**، وعشوائيٌّ بعده = شاهدٌ ميّتٌ يطابق `K0`.
    و`seq` يبقى **آخرًا** لكسر تصادم التجزئة ⇒ حتميّةٌ تامّة."""
    def _key(c) -> tuple:
        base = tuple(rank_live(c))
        h = hashlib.sha256(
            f"{seed}|tie|{c.session}|{c.symbol}".encode()).digest()
        return base[:-1] + (int.from_bytes(h[:8], "big"), base[-1])
    return _key


def rankers(seed: int = RAND_SEED) -> dict:
    """الستّةُ بترتيبِ جدولَي §② و§③ — **ولا سابعة تُضاف بعد رقم**."""
    return {"K0": k_base, "K27": k_band, "KC": k_cont, "KR": k_inv,
            "C-DEPTH": c_depth, "C-RAND": make_c_rand(seed),
            "D-RAND": make_rank_random(seed)}


# ══════════ القياس ══════════
def _hit100(p: dict) -> bool:
    """صفقةٌ مأخوذةٌ بلغت ‏+100% قبل الوقف — **نفسُ شرط `ceiling_arms._d(100)`**
    حرفًا بحرف (‏`mg_outcome` ليس `None` ولا `no_fill` · و`mg_pre_stop ≥ 100`)."""
    if (p or {}).get("mg_outcome") in (None, "no_fill"):
        return False
    try:
        return float(p.get("mg_pre_stop") or 0.0) >= D100
    except (TypeError, ValueError):
        return False


def _hit(p: dict, thr: float) -> bool:
    if (p or {}).get("mg_outcome") in (None, "no_fill"):
        return False
    try:
        return float(p.get("mg_pre_stop") or 0.0) >= thr
    except (TypeError, ValueError):
        return False


def measure(trades, expl: float, seed: int = RAND_SEED, only=None):
    """يقيس **كلَّ الأذرع على مجموعةِ مرشّحين واحدة** ⇒ الميزانيةُ والمحورُ
    والكونُ متطابقةٌ بالبناء. يُرجع `(نتائج, معلومات, مرشّحون)`.

    🔒 **و`only` ليست تحسينَ سرعة بل حاجزُ اطّلاع:** وضعُ الجدوى يمرّر
    `{"K0"}` ⇒ **لا ذراعَ أخرى تُحسَب أصلًا** فيستحيل أن يتسرّب `Δ` حاكمٌ
    من طباعةٍ سهوًا. «‏`K0` وحدَه» تصير **بنيةً لا وعدًا**."""
    dates = set()
    for t in trades:
        if t.get("date"):
            dates.add(str(t["date"]))
        if t.get("exit_date"):
            dates.add(str(t["exit_date"]))
    cands, idx, oc = candidates_from_trades(trades, extra_dates=sorted(dates))
    out = {}
    for name, fn in rankers(seed).items():
        if only is not None and name not in only:
            continue
        res = replay(cands, outcome_of=oc, ranker=fn, capacity=CAPACITY,
                     sessions=range(0, len(idx)))
        taken = res["taken"]
        nf = sum(1 for c in taken
                 if (c.payload or {}).get("mg_outcome") == "no_fill"
                 or (c.payload or {}).get("outcome") == "no_fill")
        rs = [v for v in (r_unit(c.payload) for c in taken) if v is not None]
        per_sym, hits = {}, []
        for c in taken:
            if _hit100(c.payload):
                per_sym[c.symbol] = per_sym.get(c.symbol, 0) + 1
                hits.append(f"{c.symbol}@{c.payload.get('date')}")
        out[name] = {
            "taken": len(taken), "no_fill": nf, "filled": len(taken) - nf,
            "d50": sum(1 for c in taken if _hit(c.payload, expl)),
            "d100": sum(1 for c in taken if _hit100(c.payload)),
            "rejected_cap": res["rejected_cap"],
            "per_trade": (round(sum(rs) / len(taken), 4) if taken else 0.0),
            "per_sym": per_sym, "hits": sorted(hits),
            "order": [c.symbol + "|" + str(c.payload.get("date")) for c in taken],
        }
    info = {"n_cands": len(cands), "axis": len(idx), "capacity": int(CAPACITY),
            "n_rows": len(trades)}
    return out, info, cands


def class_order_ok(cands, fn_band, fn_base) -> bool:
    """`V-K5` **سلوكيّ** — داخلَ كلّ فئةٍ من `K27` يطابق الترتيبُ `K0` بت-بت.

    يُبنى الترتيبان فعلًا ويُقارَن التسلسلُ المقصور على كلّ فئة — لا يُدَّعى
    من شكل الدالّة (قاعدةُ «سلوكيٌّ لا بنيويّ»)."""
    by_band = sorted(cands, key=fn_band)
    by_base = sorted(cands, key=fn_base)
    for b in (0, 1):
        a = [c.seq for c in by_band if band_of(c) == b]
        d = [c.seq for c in by_base if band_of(c) == b]
        if a != d:
            return False
    return True


def boot_delta(per_sym_a: dict, per_sym_b: dict,
               reps: int = BOOT, seed: int = BOOT_SEED) -> dict:
    """فاصلُ بوتستراب **عنقوديٌّ بالرمز** على فرق المساهمات المحقَّقة.

    ⚠️ **حدٌّ مُعلَن:** لا تُعاد آلةُ التخصيص داخل الإعادة (مستحيلٌ حسابيًّا)
    ⇒ يقيس تشتّتَ المساهمات لا اقترانَ الخانات."""
    keys = sorted(set(per_sym_a) | set(per_sym_b))
    if not keys:
        return {"delta": 0, "lo": 0.0, "hi": 0.0, "n_clusters": 0}
    d = [per_sym_a.get(k, 0) - per_sym_b.get(k, 0) for k in keys]
    n = len(d)
    rng = random.Random(seed)
    outs = []
    for _ in range(reps):
        outs.append(sum(d[rng.randrange(n)] for _ in range(n)))
    outs.sort()
    return {"delta": sum(d), "n_clusters": n,
            "lo": round(outs[int(0.025 * reps)], 2),
            "hi": round(outs[min(int(0.975 * reps), reps - 1)], 2)}


def _merge(per_year: dict, arm: str) -> dict:
    """تجميعُ مساهمات الرمز عبر السنوات — **الرمزُ عنقودٌ واحد** لا (سنة·رمز)."""
    agg = {}
    for y in per_year.values():
        for s, n in (y["arms"][arm]["per_sym"] or {}).items():
            agg[s] = agg.get(s, 0) + n
    return agg


def read_verdict(per_year: dict, boots: dict) -> dict:
    """قاعدةُ القراءة الثلاثيّة بحرف §④ — **دالّةٌ نقيّةٌ تُقفَل بجدول حقيقة**.

    🔴 وسقوطُ **سنةٍ واحدةٍ** على الأرضية **ليس «لا حكم» بل الفرعُ 2** — وهو
    بعينه ما وقع في `T-AHEXT-2` وما أصلحه `PGA10` في `T-PMGATE`."""
    # 🔒 الحكمُ على **السنوات الثلاث** وحدَها (§④) — وسنةٌ وصفيّةٌ زائدة، إن
    #    مرّت، **لا تدخل معيارًا حاكمًا** ولا تُنقذ ساقطًا.
    gov = {y: v for y, v in per_year.items() if y in GOV_YEARS}
    dropped = sorted(y for y in GOV_YEARS
                     if y not in gov or not gov[y]["floor_ok"])
    if len(dropped) >= 2:
        return {"branch": 3, "rk1": None, "rk2": None, "rk3": None,
                "rk3_degenerate": None, "dropped": dropped}
    ys = sorted(y for y in GOV_YEARS if y not in dropped)
    d1 = [gov[y]["delta"]["K27-K0"] for y in ys]
    d2 = [gov[y]["delta"]["K27-C-DEPTH"] for y in ys]
    d3 = [gov[y]["delta"]["K27-C-RAND"] for y in ys]
    # 🔴 `RK1`/`RK3` نصُّهما «**موجبٌ في السنوات الثلاث**» ⇒ سنةٌ ساقطةٌ على
    #    الأرضية **تُسقطهما بالتعريف** (لا يُقرأ لها رقم) ⇒ **الفرعُ 2** —
    #    وهو حرفُ الملاحظة الحمراء في §④. و`RK2` نصُّه «سنتين فأكثر» فيبقى
    #    قابلًا للاستيفاء بسنتين.
    full = not dropped
    rk1 = full and all(v > 0 for v in d1) and boots["K27-K0"]["lo"] > 0
    rk2 = (sum(1 for v in d2 if v > 0) >= 2
           and boots["K27-C-DEPTH"]["lo"] > 0)
    rk3 = full and all(v > 0 for v in d3)
    # 🔴 **شاهدٌ ميّت يُعلَن ولا يُطوى:** `rank_live` ينتهي بـ`seq` الفريد فهو
    #    ترتيبٌ كلّيٌّ **بلا تعادل** ⇒ إن لم تتعادل مكوّناتُه السابقة في أيّ
    #    سنةٍ مؤهَّلة صار `C-RAND` ≡ `K0` و**`RK3` إعادةُ صياغةٍ لإشارة `RK1`
    #    لا شاهدًا مستقلًّا**. الفرعُ يُحسَب **بحرف §④** (العقدُ مدموجٌ لا
    #    يُعدَّل)، والانحلالُ يُطبَع فلا يُقرأ دليلًا مستقلًّا — درسُ `C-MOM`.
    rk3_deg = bool(ys) and all(gov[y]["rand_dead"] for y in ys)
    return {"branch": 1 if (rk1 and rk2 and rk3) else 2,
            "rk1": rk1, "rk2": rk2, "rk3": rk3, "rk3_degenerate": rk3_deg,
            "dropped": dropped}


# ══════════ الحرّاس ══════════
def _git_sha(ref: str, path: str) -> str:
    try:
        p = subprocess.run(["git", "show", f"{ref}:{path}"],
                           capture_output=True, timeout=60)
        return hashlib.sha256(p.stdout).hexdigest()[:12] if p.returncode == 0 \
            else "?"
    except Exception:                                            # noqa: BLE001
        return "?"


def production_untouched() -> tuple:
    """`V-K1` — `Super_stock.py` **بت-بت** مع `origin/main`."""
    try:
        cur = hashlib.sha256(
            open("Super_stock.py", "rb").read()).hexdigest()[:12]
    except Exception:                                            # noqa: BLE001
        return False, "?", "?"
    base = _git_sha("origin/main", "Super_stock.py")
    return (base != "?" and cur == base), cur, base


def selfcheck_readonly() -> bool:
    """`V-K7`-ب — قراءةٌ فقط بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة، ولا يُفتَح
    للكتابة إلّا `OUT_ROWS` أو ملفُّ صفقاتِ السنة."""
    banned = {"send_telegram", "git_save", "save_watchlist",
              "save_op_entry_state", "record_new_alerts", "save_near_watch",
              "save_hunter_watch"}
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


BANNED_FWD = ("exit_date", "outcome", "mg_pre_stop", "mg_outcome", "r_unit",
              "hits", "d100")


def rankers_blind() -> bool:
    """`V-K7` — **صفرُ نظرٍ مستقبليّ**: مصادرُ المُرتِّبات لا تذكر حقلَ نتيجةٍ
    واحدًا. يُفحَص نصُّ كلّ دالّةٍ مُرتِّبة **بالـAST على الأسماء والسلاسل**."""
    import inspect                                               # noqa: PLC0415
    for fn in (band_of, k_base, k_band, k_inv, k_cont, c_depth, make_c_rand,
               _env):
        try:
            src = inspect.getsource(fn)
        except Exception:                                        # noqa: BLE001
            return False
        try:
            tree = ast.parse(src.lstrip())
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                if n.value in BANNED_FWD:
                    return False
            if isinstance(n, ast.Name) and n.id in BANNED_FWD:
                return False
            if isinstance(n, ast.Attribute) and n.attr in BANNED_FWD:
                return False
    return True


def _measure_year(year: str, frozen: str) -> dict:
    """يشغّل الباكتيست **في عمليةٍ ابنةٍ مستقلّة** لهذي السنة ويُرجع صفقاتها.

    🔒 والعزلُ مقصود: حالةُ `Super_stock` العامّة لا تُحمَل بين السنوات — وهو
    نفسُ سببِ الأبناء في `T-RSI40`/`T-CEILING`، مع فارقٍ جوهريّ: **هنا طفلٌ
    واحدٌ للسنة لا طفلٌ لكلّ ذراع**، لأن **لا ذراعَ تمسّ `CONFIG`.**"""
    env = {**dict(os.environ), **CA.child_env(),
           "BACKTEST_YEAR": year, "BT_FROZEN_PATH": frozen}
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child",
                        year], capture_output=True, text=True, env=env)
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    for ln in blob.splitlines():
        if not ln.startswith("RSIRANK_CHILD:"):
            _log(f"  [{year}] {ln}")
    rows = [x for x in blob.splitlines() if x.startswith("RSIRANK_CHILD:")]
    if p.returncode != 0 or not rows:
        return {}
    return json.loads(rows[-1].split("RSIRANK_CHILD:", 1)[1])


def run_child(year: str) -> int:
    import Super_stock as S                                      # noqa: PLC0415
    snap = CA.snapshot_id()
    _log(f"SNAP {year} as-of={snap['asof']} n_symbols={snap['n']}")
    trades = S.run_backtest() or []
    wf = [t for t in trades if t.get("exit_date")]
    _tp = TRADES_TMPL.format(year)
    with open(_tp, "w", encoding="utf-8") as fh:
        json.dump(wf, fh, ensure_ascii=False, default=str)
    meta = {"year": year, "snap": snap, "wf": len(wf), "path": _tp,
            "expl": float(S.CONFIG["EXPLOSION_PCT"]),
            # 🔒 برهانٌ لا زينة: عتباتُ RSI النافذة **لم تُمَسّ** بهذي التجربة.
            "rsi_now_hard": float(S.CONFIG["RSI_NOW_HARD"]),
            "rsi_max_now": float(S.CONFIG["RSI_MAX_NOW"])}
    meta.update(CA.rates(trades))
    print("RSIRANK_CHILD:" + json.dumps(meta, ensure_ascii=False))
    return 0


def main() -> int:                                               # noqa: PLR0911
    years = [x.strip() for x in
             str(os.environ.get("RSIRANK_YEARS", "")).split(",") if x.strip()]
    frozen = [x.strip() for x in
              str(os.environ.get("RSIRANK_FROZEN", "")).split(",") if x.strip()]
    dry = str(os.environ.get("RSIRANK_DRY", "")).strip() == "1"
    if not years or len(years) != len(frozen):
        _log("⛔ يلزم RSIRANK_YEARS و RSIRANK_FROZEN بالعدد نفسِه وبالترتيب نفسِه")
        return 2
    if any(y not in ("2023", "2024", "2025", "2026") for y in years):
        _log("⛔ سنةٌ غيرُ مسموحة")
        return 2
    if not dry and sorted(years) != sorted(GOV_YEARS):
        _log(f"⛔ الحكمُ يلزمه **السنواتُ الثلاث بعينها** {GOV_YEARS} (§④) — "
             f"والمُعطى {years}. لسنةٍ واحدة استعمل وضعَ الجدوى.")
        return 2
    if not selfcheck_readonly():
        _log("⛔ فحصُ «قراءةٌ فقط» سقط")
        return 3
    if not rankers_blind():
        _log("⛔ `V-K7` — مُرتِّبٌ يذكر حقلَ نتيجة")
        return 3

    _log(f"📌 المنطقة [{BAND_LO}, {BAND_HI}] من فيصل · الميزانية={int(CAPACITY)} "
         f"· الأرضية={FLOOR_FILLED} مُعبَّأة · `FWD` = مُسلَّمون ‏≥{D100:.0f}%")
    _log(f"📌 بوتستراب {BOOT} ببذرة {BOOT_SEED} · بذرةُ العشوائيّ {RAND_SEED} "
         f"(‏`V-K8`)")
    ok1, cur, base = production_untouched()
    _log(f"🔒 `V-K1` Super_stock.py {CA._mark(ok1)} (محلّي {cur} · main {base})")
    if not ok1:
        _log("⛔ `V-K1` سقط — الإنتاجُ ليس بت-بت مع main")
        return 3
    if dry:
        _log("🧪 **وضعُ الجدوى:** سنةٌ واحدة · **`K0` وحدَه تُحسَب** (‏`only`) "
             "⇒ **صفرُ `Δ` بنيويًّا لا وعدًا** — الجوابُ: هل تعبر الأرضيةُ وكم "
             "حجمُ `FWD` أصلًا؟ **ولا يُقرأ منه رقمٌ حاكم.**")

    per_year, meta_all, rows = {}, {}, []
    for y, fz in zip(years, frozen):
        _log("")
        _log(f"──── {y} (لقطة {fz}) ────")
        meta = _measure_year(y, fz)
        if not meta:
            _log(f"⛔ [{y}] الطفلُ سقط أو لم يُخرج صفقات")
            return 4
        if str(meta["snap"].get("asof", ""))[:4] != y:
            _log(f"⛔ [{y}] اللقطة as-of {meta['snap'].get('asof')} لا تطابق السنة")
            return 4
        meta_all[y] = meta
        with open(meta["path"], encoding="utf-8") as fh:
            trades = json.load(fh)
        # 🔒 **حاجزُ الاطّلاع:** في الجدوى تُحسَب `K0` **وحدَها** — لا ذراعَ
        #    أخرى تُبنى فيستحيل `Δ` بنيويًّا لا بالوعد.
        arms, info, cands = measure(trades, float(meta["expl"]),
                                    only=({"K0"} if dry else None))

        # ── `V-K2` مرجعُ الأساس المنشور ──
        pub = PUBLISHED_K0_D100.get(y)
        k0d = arms["K0"]["d100"]
        v2 = (pub is None) or (k0d == pub)
        _log(f"🔒 `V-K2` `K0` d100={k0d} · المنشور={pub} {CA._mark(v2)}"
             + ("" if v2 else "  ⚠️ **يُعلَن الفرقُ ولا يُطوى**"))
        # ── `V-K3`/`V-K4` بالبناء: مجموعةُ مرشّحين واحدة ──
        _log(f"🔒 `V-K3`/`V-K4` مرشّحون={info['n_cands']} · محور={info['axis']} "
             f"· سعة={info['capacity']} · صفوف={info['n_rows']} "
             f"(**كائنٌ واحدٌ لكلّ الأذرع**)")
        v5 = class_order_ok(cands, k_band, k_base)
        _log(f"🔒 `V-K5` `K27` داخلَ كلّ فئةٍ ≡ `K0` {CA._mark(v5)}")
        n_r = sum(1 for c in cands if _env(c, "rsi_now", None) is not None)
        cov = round(100.0 * n_r / max(1, len(cands)), 1)
        v6 = cov >= 90.0
        _log(f"🔒 `V-K6` تغطيةُ `rsi_now` {cov}% {CA._mark(v6)}")
        _log("🔒 `V-K7` مُرتِّبات عمياءُ عن النتيجة ✅ · `V-K8` الثوابتُ مطبوعة ✅")
        if not (v5 and v6):
            _log(f"⛔ [{y}] حارسٌ ساقط ⇒ لا يُقرأ رقمٌ من هذي السنة")
            return 5

        floor_ok = arms["K0"]["filled"] >= FLOOR_FILLED
        if dry:
            # ══ وضعُ الجدوى: **الأرضيةُ والحجمُ وحدَهما** ══
            # 🔒 صفرُ `Δ` · صفرُ ذراعٍ غيرِ `K0` · وصفرُ صفٍّ يحمل فرقًا.
            # 🩺 وشاهدُ الحياة يُقاس هنا **ترتيبًا لا تسليمًا**: مقارنةُ ترتيبَين
            #    نقيَّين على المرشّحين — **لا تمسّ نتيجةً ولا تعبئة**، واختلافُهما
            #    شرطٌ لازمٌ لحياة `C-RAND` لا كافٍ (يُقال كما هو).
            _dry_a = tuple(c.symbol for c in sorted(cands,
                                                    key=make_c_rand(RAND_SEED)))
            _dry_b = tuple(c.symbol for c in sorted(cands, key=k_base))
            _v = arms["K0"]
            _log(f"  K0       مأخوذ {_v['taken']:>4} · مُعبَّأ {_v['filled']:>4} · "
                 f"d50 {_v['d50']:>3} · **d100 {_v['d100']:>3}**")
            _log(f"  الأرضية (‏{FLOOR_FILLED} مُعبَّأة في `K0`) "
                 f"{CA._mark(floor_ok)}")
            _log("  🩺 `C-RAND` يفرّق عن `K0` **ترتيبًا**؟ "
                 + ("✅ نعم (شرطٌ لازمٌ لا كافٍ)" if _dry_a != _dry_b
                    else "🔴 **لا — شاهدٌ ميّتٌ على الترتيب**"))
            rows.append({"year": y, "info": info, "floor_ok": floor_ok,
                         "rsi_cov": cov, "dry": True,
                         "K0": {k: v for k, v in _v.items() if k != "order"},
                         "rand_order_differs": _dry_a != _dry_b})
            per_year[y] = {"arms": arms, "info": info, "floor_ok": floor_ok,
                           "rsi_cov": cov}
            break

        same = arms["C-RAND"]["order"] == arms["K0"]["order"]
        _log("🩺 شاهدُ الحياة: `C-RAND` ≡ `K0`؟ "
             + ("🔴 **نعم — شاهدٌ ميّت**" if same else "✅ لا (يفرّق)"))

        d = {f"K27-{a}": arms["K27"]["d100"] - arms[a]["d100"]
             for a in ("K0", "C-DEPTH", "C-RAND", "D-RAND")}
        per_year[y] = {"arms": arms, "info": info, "floor_ok": floor_ok,
                       "delta": d, "rand_dead": same, "rsi_cov": cov}
        for a in list(GOV_ARMS) + list(DESC_ARMS):
            v = arms[a]
            _log(f"  {a:<8} مأخوذ {v['taken']:>4} · مُعبَّأ {v['filled']:>4} · "
                 f"d50 {v['d50']:>3} · **d100 {v['d100']:>3}** · "
                 f"R/صفقة {v['per_trade']:+.4f}")
        _log(f"  Δ(d100) K27−K0={d['K27-K0']:+d} · K27−C-DEPTH="
             f"{d['K27-C-DEPTH']:+d} · K27−C-RAND={d['K27-C-RAND']:+d} · "
             f"[وصفيّ] K27−D-RAND={d['K27-D-RAND']:+d}")
        _log(f"  الأرضية (‏{FLOOR_FILLED} مُعبَّأة في `K0`) {CA._mark(floor_ok)}")
        rows.append({"year": y, "info": info, "floor_ok": floor_ok, "delta": d,
                     "rand_dead": same, "rsi_cov": cov,
                     "arms": {a: {k: v for k, v in arms[a].items()
                                  if k != "order"} for a in arms}})

    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    out = {"years": years, "dry": dry, "capacity": int(CAPACITY),
           "band": [BAND_LO, BAND_HI], "boot": BOOT, "boot_seed": BOOT_SEED,
           "rand_seed": RAND_SEED, "floor": FLOOR_FILLED,
           "per_year": {y: {"delta": v.get("delta"),
                            "floor_ok": v["floor_ok"],
                            "rand_dead": v.get("rand_dead"),
                            "d100": {a: v["arms"][a]["d100"] for a in v["arms"]},
                            "filled": {a: v["arms"][a]["filled"]
                                       for a in v["arms"]}}
                        for y, v in per_year.items()},
           "meta": meta_all}
    if dry:
        _log("")
        _log("🧪 وضعُ الجدوى: **لا حكمَ ولا فاصل** — الجوابُ عن الأرضية والحجم وحدَهما.")
        out["no_verdict"] = None
        print("RSIRANK_JSON " + json.dumps(out, ensure_ascii=False))
        return 0

    boots = {}
    for a in ("K0", "C-DEPTH", "C-RAND", "D-RAND"):
        boots[f"K27-{a}"] = boot_delta(_merge(per_year, "K27"),
                                       _merge(per_year, a))
    _log("")
    for k, b in boots.items():
        tag = "وصفيّ" if k.endswith("D-RAND") else "حاكم"
        _log(f"📐 [{tag}] {k}: Δ={b['delta']:+d} · فاصلٌ عنقوديٌّ بالرمز "
             f"[{b['lo']}, {b['hi']}] · عناقيد={b['n_clusters']}")
    out["boot"] = boots
    v = read_verdict(per_year, boots)
    out["verdict"] = v
    out["no_verdict"] = v["branch"] == 3
    _log("")
    _log(f"⚖️ **الحكم: الفرعُ {v['branch']}** · `RK1`={v['rk1']} · "
         f"`RK2`={v['rk2']} · `RK3`={v['rk3']}"
         + (f" · سنواتٌ ساقطةٌ على الأرضية: {v['dropped']}" if v["dropped"]
            else ""))
    if v.get("rk3_degenerate"):
        _log("🔴 **و`RK3` منحلّة:** `C-RAND` ≡ `K0` في كلّ سنةٍ مؤهَّلة "
             "(‏`rank_live` بلا تعادل) ⇒ **ليست شاهدًا مستقلًّا** بل إعادةُ "
             "صياغةٍ لإشارة `RK1` — والوصفيُّ `D-RAND` هو المقارنةُ التي "
             "أرادها تبريرُ العقد (`T-RANK-DENSE`).")
    print("RSIRANK_JSON " + json.dumps(out, ensure_ascii=False))
    return 9 if v["branch"] == 3 else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--child":
        sys.exit(run_child(sys.argv[2]))
    sys.exit(main())
