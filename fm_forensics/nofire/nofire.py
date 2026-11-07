#!/usr/bin/env python3
"""🔇 `T-NOFIRE` — «ليه ما أُطلق للـ52؟» (العقد `fm_forensics/nofire/NOFIRE_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode run` (رنر · Polygon · GitHub API · تاريخُ git كامل): لكلّ راكضٍ من الـ52 «لا أحد» (ولكلّ مُطلَقٍ من الـ143 بوّابةً للصدق) تُعاد
`liq_stage_events` بالاسم دقيقةً دقيقة أربعَ مرّات متداخلة (`F` · `F_U` الكون · `F_UA` ‏+العاملُ الحيّ · `P` ‏+بوّابةُ المضارب) ⟵ أوّلُ بوّابةٍ
تسقط (G1-G5) ⟵ والسببُ المسمّى بـ`liq_case_probe.why` ⟵ وتفصيلُ فجوة العامل ⟵ والدِّدوب ⟵ والتنبّؤات NF1-NF8 · ويطبع markdown و`NOFIRE_JSON`.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد أو ملفُّ المجتمع.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "NOFIRE_prereg.md")
CONTRACT_SHA = "28eb64f5aa0f7f1bcabe276451c3c7f8f15a0e76c30a1ac0a2b24a30735289e2"
POP = os.path.join(HERE, "data", "nofire_pop.json")
POP_SHA = "29be820e341901a165634be2635f82facd45afc508451f154d10d31c9b88eab1"
CONTRACT_RC = 9
NY = ZoneInfo("America/New_York")
WORKFLOW = "operator_entry.yml"
LIST_FILES = ("weekly_watchlist.json", "near_watch.json", "press_radar_state.json", "hunter_watchlist.json")
OP_STATE = "op_entry_state.json"
TC_FROM, TC_TO = "2026-09-10", "2026-11-04"                 # ⓪-K2 · يومُ الشحن 09-09 خارج (منتصفُ الجلسة)
OP_NY, END_NY = 4 * 60, 20 * 60
SWEEP_LAG_S = 6                                              # ② المسحُ بعد نهاية الدقيقة بست ثوانٍ
TRUTH_MIN, BARS_FAIL_MAX = 0.85, 0.10                        # ④
OP_CALLS_MAX = 40                                            # سقفُ نداءات بوّابة المضارب لراكضٍ واحد (يُعلَن إن بُلغ)
CRONS_UTC = ((6, 1), (8, 21), (11, 31), (13, 21), (17, 1), (18, 21), (0, 21), (2, 21), (4, 21), (22, 21))  # ⓪-K7
GATES = ("G1", "G2", "G3", "G4", "G5")
GATE_AR = {"G1": "لا زناد", "G2": "خارج الكون", "G3": "لا عامل (سقوطُ الكرون)", "G4": "بوّابةُ المضارب", "G5": "غيرُ مفسَّر (التغطية/البيانات)"}


def log(m=""):
    print(m, flush=True)


def _sha(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def contract_ok():
    return _sha(CONTRACT) == CONTRACT_SHA and _sha(POP) == POP_SHA


# ── دوالُّ نقيّة (مقفولةٌ في السويّة) ─────────────────────────────────────────────────────────────────────
def ny_ts(day, minute):
    d = dt.date.fromisoformat(day)
    return dt.datetime(d.year, d.month, d.day, minute // 60, minute % 60, tzinfo=NY).timestamp()


def ny_parts(t_ms):
    t = dt.datetime.fromtimestamp(int(t_ms) / 1000, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


def hm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}" if m is not None else "—"


def bar_dicts(rows, day):
    """`fetch_day` ⟵ قواميسُ `liq_stage_events` ليوم نيويورك `day` داخل [04:00، 20:00) مرتّبة."""
    out = []
    for b in rows or ():
        d, m = ny_parts(b[0])
        if d == day and OP_NY <= m < END_NY:
            out.append({"t": int(b[0]), "o": float(b[1]), "h": float(b[2]), "l": float(b[3]), "c": float(b[4]), "v": float(b[5])})
    out.sort(key=lambda x: x["t"])
    return out


def sweep_times(day):
    """② لحظةُ مسح كلّ دقيقة m ⟵ [(m، s_ms)] حيث s = نهايةُ الدقيقة ‏+6 ثوانٍ."""
    return [(m, int((ny_ts(day, m + 1) + SWEEP_LAG_S) * 1000)) for m in range(OP_NY, END_NY)]


def replay(bars, day, ok=None, tc=None, op=None, stage_fn=None, win_min=None):
    """② إعادةُ المسح دقيقةً دقيقة بالحالة المحمولة ⟵ {anchor_ms · at_ms · muted · op_calls · capped} (و`anchor_ms` None إن لم تُرسَ).
    `ok(s)` يقرّر هل يجري المسحُ عند s (العاملُ/الكون) · و`op(s)` بوّابةُ المضارب ⟵ True/False/None (None يمرّ كالحيّ)."""
    import Super_stock as bot
    fn = stage_fn or bot.liq_stage_events
    win = int(win_min if win_min is not None else bot.LIQ_WINDOW_MIN)
    import bisect
    ts = [b["t"] for b in bars]
    st, muted, calls = {}, 0, 0
    for _m, s in sweep_times(day):
        if ok is not None and not ok(s):
            continue
        w = bars[bisect.bisect_left(ts, s - win * 60_000):bisect.bisect_left(ts, s)]
        if not w:
            continue
        _tc = tc if (tc and not st.get("anchor_ms")) else None
        _ev, st2 = fn(w, st, now_ms=s, rearm=True, tc=_tc)
        if st2.get("anchor_ms") and not st.get("anchor_ms"):
            if op is not None:
                if calls >= OP_CALLS_MAX:
                    return {"anchor_ms": None, "at_ms": None, "muted": muted, "op_calls": calls, "capped": True}
                calls += 1
                r = op(s)
                if r is False:
                    muted += 1
                    st = {}                       # ⓪-K4: `seen.pop` ⟵ حالةٌ جديدة في المسح التالي
                    continue
            return {"anchor_ms": int(st2["anchor_ms"]), "at_ms": s, "muted": muted, "op_calls": calls, "capped": False}
        st = st2
    return {"anchor_ms": None, "at_ms": None, "muted": muted, "op_calls": calls, "capped": False}


def attribute(F, FU, FUA, P):
    """③ أوّلُ بوّابةٍ تسقط ⟵ G1…G5."""
    if not F.get("anchor_ms"):
        return "G1"
    if not FU.get("anchor_ms"):
        return "G2"
    if not FUA.get("anchor_ms"):
        return "G3"
    if not P.get("anchor_ms"):
        return "G4"
    return "G5"


def violent_index(bars, top_ms=None):
    """③ أعنفُ دقيقةٍ رفعةً (فتحًا ⟵ إغلاقًا) **قبل قمّة اليوم** (ومن الدقيقة الرابعة كي تُحسب النافذة) ⟵ فهرس أو None."""
    end = len(bars) if top_ms is None else next((i + 1 for i, b in enumerate(bars) if b["t"] == top_ms), len(bars))
    best, bi = None, None
    for i in range(3, end):
        b = bars[i]
        r = (b["c"] - b["o"]) / b["o"] if b["o"] > 0 else 0.0
        if best is None or r > best:
            best, bi = r, i
    return bi


def why_reasons(bars, i_viol, top_ms=None):
    """③ سببُ G1 عند أعنف دقيقة ⟵ (السبب، {سبب: عدد} على دقائق ما قبل القمّة · أوّلُ الجلسة؟) بـ`liq_case_probe` بالاسم."""
    import re
    import liq_case_probe as LCP
    if i_viol is None:
        return None, {}, False
    end = next((i + 1 for i, b in enumerate(bars) if b["t"] == top_ms), len(bars)) if top_ms else len(bars)
    dist = {}
    for i in range(3, end):
        r = re.sub(r"[-+]?\d[\d,.]*", "N", LCP.why(LCP.gate_trace(bars, i)).split("(")[0].split("$")[0].strip())
        dist[r] = dist.get(r, 0) + 1
    main = re.sub(r"[-+]?\d[\d,.]*", "N", LCP.why(LCP.gate_trace(bars, i_viol)).split("(")[0].split("$")[0].strip())
    return main, dist, i_viol <= 5


def intervals_fn(iv):
    """العاملُ حيٌّ عند s (ملّي) إن غطّتها فترةٌ من [(بدء، نهاية)] بالملّي."""
    iv = sorted(iv)
    return lambda s: any(a <= s <= b for a, b in iv)


def membership_fn(timeline):
    """الكونُ: [(ثانيةُ التغيّر، عضو؟)] تصاعديًّا ⟵ s (ملّي) ⟵ عضويّةُ آخر تغيّرٍ قبلها (لا شيءَ قبل الأوّل ⟵ خطأ)."""
    tl = sorted(timeline)

    def _f(s):
        cur = False
        for t, mem in tl:
            if t * 1000 <= s:
                cur = mem
            else:
                break
        return cur
    return _f


def parse_crons(yml_text):
    """كروناتُ `operator_entry.yml` (ساعة، دقيقة) UTC من نصّه (الأسطرُ غيرُ المعلَّقة)."""
    import re
    out = set()
    for ln in (yml_text or "").splitlines():
        if ln.lstrip().startswith("#"):
            continue
        m = re.search(r'cron:\s*"(\d+) ([\d,]+) \* \* [\d\-,]+"', ln)
        if m:
            for h in m.group(2).split(","):
                out.add((int(h), int(m.group(1))))
    return tuple(sorted(out))


def gap_detail(iv, at_ms, crons=None):
    """③ تفصيلُ G3: آخرُ نهايةٍ قبل `at_ms` وأوّلُ بدايةٍ بعدها (ملّي) · والكروناتُ المجدولة في الفجوة (النافذةُ يومَها · وإلّا K7)."""
    crons_set = set(crons if crons is not None else CRONS_UTC)
    before = max((b for a, b in iv if b <= at_ms), default=None)
    after = min((a for a, b in iv if a >= at_ms), default=None)
    lo = before if before is not None else at_ms - 6 * 3600 * 1000
    hi = after if after is not None else at_ms + 3600 * 1000
    crons = []
    t = dt.datetime.fromtimestamp(lo / 1000, dt.timezone.utc).replace(second=0, microsecond=0)
    end = dt.datetime.fromtimestamp(hi / 1000, dt.timezone.utc)
    while t <= end:
        if (t.hour, t.minute) in crons_set:
            crons.append(t.strftime("%H:%M"))
        t += dt.timedelta(minutes=1)
    return before, after, crons


def has_anchor(v, day):
    """③ الدِّدوب: حالةُ `LIQ:sym` تحمل مِرساةً (`anchor_ms` أو `rearm_prev.anchor_ms`) يومُها نيويوركيًّا `day` — والحالةُ بلا مِرساة ليست ددوبًا."""
    for a in (v or {}, (v or {}).get("rearm_prev") or {}):
        try:
            if ny_parts(int(a["anchor_ms"]))[0] == day:
                return True
        except (KeyError, TypeError, ValueError):
            continue
    return False


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def predictions(res):
    c = res["counts"]
    return {
        "NF1": bool(res.get("truth_ok")),
        "NF2": 26 <= c.get("G1", 0) <= 42,
        "NF3": 3 <= c.get("G3", 0) <= 13,
        "NF4": c.get("G2", 0) <= 5,
        "NF5": 2 <= c.get("G4", 0) <= 10,
        "NF6": res.get("dedup", 0) == 0,
        "NF7": c.get("G5", 0) <= 8,
        "NF8": (res.get("g1_top_reason") or "").startswith("قفزةُ حجمٍ"),
    }


def report_lines(res, rows, meta):
    L = ["# 🔇 `T-NOFIRE` — النتيجة (مولَّدةٌ بـ`nofire.py --mode run` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}` · تشغيلاتُ العامل المقروءة {meta.get('jobs')} في {meta.get('days')} يومًا", ""]
    tr = res.get("truth") or [0, 0]
    L.append(f"**بوّابةُ صدق الإعادة (§④):** `P` أرست مِرساةً لـ{tr[0]} من {tr[1]} مُطلَقًا = "
             f"{(tr[0] / tr[1] * 100 if tr[1] else 0):.1f}% ⟵ " + ("تُعتمد" if res.get("truth_ok") else "**لا قياس** (الجدولُ وصفٌ لا يُقرأ)"))
    L.append(f"**الشموع:** تعذّرت في {res.get('bars_fail')} من {res.get('bars_n')} · " + ("تُعتمد" if res.get("bars_ok") else "**لا قياس**"))
    if res.get("truth_dt_med") is not None:
        L.append(f"وصفًا: وسيطُ |مِرساة `P` − الإطلاق الحيّ| على المُطلَق لهم = {res['truth_dt_med']:.0f} دقيقة")
    L += ["", "## ① البوّابةُ لكلّ راكضٍ من الـ52 (أوّلُ بوّابةٍ تسقط)", "", "| البوّابة | العدد |", "|---|---|"]
    for g in GATES:
        L.append(f"| {g} {GATE_AR[g]} | {res['counts'].get(g, 0)} |")
    L.append(f"| — بلا شموع | {res['counts'].get('NA', 0)} |")
    L += ["", f"**سقوطُ الكرون (G3) مستقلًّا عن الكون (وصفًا · `F_A` بلا مِرساة و`F` مِرساة):** {res.get('g3_any', 0)} من 52",
          f"**الدِّدوب (مِرساةٌ بتاريخ اليوم في أيّ لقطة):** {res.get('dedup', 0)} · شاهدُ الضبط: وُجدت المِرساةُ عند "
          f"{(res.get('dedup_ctrl') or [0, 0])[0]} من {(res.get('dedup_ctrl') or [0, 0])[1]} مُطلَقًا · ومنها بحقل `sent` غيرِ فارغ "
          f"(أُرسل لها) {res.get('dedup_sent', 0)}: {' · '.join(res.get('dedup_names') or []) or '—'} · **توقيتُ الجلسة (مِرساةُ `F` خارج [04:00، 20:00)):** 0 بالبناء · "
          f"و«أوّلُ الجلسة» في G1: {res.get('g1_first', 0)}", ""]
    L += ["## ② G1 — لماذا لم يتحقّق الزناد؟", "", f"**السببُ عند أعنف دقيقةٍ قبل القمّة:**"]
    for r, n in sorted((res.get("g1_main") or {}).items(), key=lambda kv: -kv[1]):
        L.append(f"- {r}: {n}")
    L += ["", "**وصفًا — توزيعُ أوّل شرطٍ ساقطٍ على كلّ دقائق ما قبل القمّة (مجموعُ راكضي G1):**"]
    for r, n in sorted((res.get("g1_dist") or {}).items(), key=lambda kv: -kv[1])[:8]:
        L.append(f"- {r}: {n}")
    L += ["", "## ③ الأسماء", "", "| الرمز | اليوم | R | البوّابة | التفصيل |", "|---|---|---|---|---|"]
    for x in rows:
        L.append(f"| {x['sym']} | {x['day'][5:]} | +{x['R'] * 100:.0f}% | {x.get('gate', 'NA')} {GATE_AR.get(x.get('gate'), 'بلا شموع')} | {x.get('detail', '')} |")
    L += ["", "## ④ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, v in res["preds"].items():
        L.append(f"- `{k}` {'✅' if v else '❌'}")
    L += ["", "🔒 لا تغييرَ في أيّ أداة · الإعادةُ بقواعد اليوم على شموع Polygon المنشورة · وأيُّ علاجٍ عقدٌ آخر وقرارُ المالك."]
    return L


# ── الشبكة وgit (الرنر وحدَه) ───────────────────────────────────────────────────────────────────────────
def _gh(path, params=None):
    import requests
    tok, repo = os.environ.get("GITHUB_TOKEN", "").strip(), os.environ.get("GITHUB_REPOSITORY", "").strip()
    r = requests.get(f"https://api.github.com/repos/{repo}{path}", params=params or {}, timeout=30,
                     headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r


def _iso_ms(s):
    return int(dt.datetime.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)


def worker_jobs(days):
    """⓪-K7 فتراتُ تشغيلات `operator_entry.yml` (`run_started_at`…`updated_at` · ما عدا `skipped`) ⟵ {يوم: [(بدء، نهاية، id)]} بالملّي.
    بأسابيعَ متتالية (سقفُ البحث 1,000 تشغيلة للاستعلام) ومستوى التشغيلة لا الوظيفة (حصّةُ 1,000 نداء/ساعة)."""
    d0 = dt.date.fromisoformat(min(days)) - dt.timedelta(days=1)
    d1 = dt.date.fromisoformat(max(days)) + dt.timedelta(days=1)
    runs, seen = [], set()
    w0 = d0
    while w0 <= d1:
        w1 = min(d1, w0 + dt.timedelta(days=6))
        page = 1
        while True:
            js = _gh(f"/actions/workflows/{WORKFLOW}/runs",
                     {"created": f"{w0.isoformat()}..{w1.isoformat()}", "per_page": 100, "page": page}).json()
            rs = js.get("workflow_runs") or []
            for r in rs:
                if r.get("id") not in seen:
                    seen.add(r.get("id"))
                    runs.append(r)
            if len(rs) < 100:
                break
            page += 1
        w0 = w1 + dt.timedelta(days=1)
    out, n = {}, 0
    for r in runs:
        if r.get("status") != "completed" or r.get("conclusion") == "skipped":
            continue
        if not r.get("run_started_at") or not r.get("updated_at"):
            continue
        a, b = _iso_ms(r["run_started_at"]), _iso_ms(r["updated_at"])
        if b <= a:
            continue
        n += 1
        for dd in {ny_parts(a)[0], ny_parts(b)[0]}:
            out.setdefault(dd, []).append((a, b, r["id"]))
    return out, n, len(runs)


def _git(args):
    return subprocess.run(["git"] + args, capture_output=True, text=True, check=False).stdout


def file_commits(path):
    out = _git(["log", "--format=%ct %H", "--", path]).split()
    return sorted((int(out[i]), out[i + 1]) for i in range(0, len(out), 2))


_SHOW = {}


def show_json(h, path):
    k = (h, path)
    if k not in _SHOW:
        try:
            _SHOW[k] = json.loads(_git(["show", f"{h}:{path}"]) or "null")
        except Exception:                                            # noqa: BLE001
            _SHOW[k] = None
    return _SHOW[k]


def uni_timeline(sym, day, commits):
    """② عضويّةُ الرمز في `U(s)` عبر يوم نيويورك ⟵ [(ثانية، عضو؟)] من لقطات الملفّات الأربع."""
    import Super_stock as bot
    t0, t1 = ny_ts(day, OP_NY), ny_ts(day, END_NY)
    pts = sorted({t for f in LIST_FILES for t, _h in commits[f] if t0 < t < t1} | {t0})
    tl = []
    for t in pts:
        docs = []
        for f in LIST_FILES:
            h = None
            for ct, hh in commits[f]:
                if ct <= t:
                    h = hh
                else:
                    break
            docs.append(show_json(h, f) if h else None)
        wl, near, press, hunter = docs
        try:
            uni, _ = bot.live_watch_universe(wl or {}, near if isinstance(near, dict) else {}, press or {}, hunter or {},
                                             cap=10 ** 9, today_iso=day)
            mem = any(r.get("symbol") == sym for r in uni)
        except Exception:                                            # noqa: BLE001
            mem = False
        tl.append((t, mem))
    return tl


def day_states(day, keep=None):
    """③ كلُّ لقطات `op_entry_state.json` يومَ نيويورك `day` (حدودُ الإطار ISO بالـUTC) ⟵ قائمةُ قواميس — بقراءةٍ واحدة `git cat-file --batch`.
    🔧 و`keep` (مفاتيحُ `LIQ:sym` ليوم الراكضين) يُبقي من كلّ لقطةٍ هذه المفاتيحَ وحدَها (التشغيلةُ الأولى `42344390231` قُتلت بالذاكرة: 54,748 لقطةً كاملة)."""
    t0 = dt.datetime.fromtimestamp(ny_ts(day, 0), dt.timezone.utc)
    t1 = t0 + dt.timedelta(days=1)
    hs = _git(["log", f"--since={t0.strftime('%Y-%m-%dT%H:%M:%SZ')}", f"--until={t1.strftime('%Y-%m-%dT%H:%M:%SZ')}",
               "--format=%H", "--", OP_STATE]).split()
    if not hs:
        return []
    raw = subprocess.run(["git", "cat-file", "--batch"], input=("\n".join(f"{h}:{OP_STATE}" for h in hs) + "\n").encode(),
                         capture_output=True, check=False).stdout
    return parse_batch(raw, keep)


def parse_batch(raw, keep=None):
    """مُخرَجُ `git cat-file --batch` ⟵ قواميسُ JSON (المفقودُ والتالفُ يُتخطّى) · و`keep` يقصر كلَّ قاموسٍ على مفاتيحه."""
    out, i = [], 0
    while i < len(raw):
        j = raw.find(b"\n", i)
        if j < 0:
            break
        head = raw[i:j].split()
        i = j + 1
        if len(head) < 3 or head[1] != b"blob":
            continue
        n = int(head[2])
        try:
            d = json.loads(raw[i:i + n].decode("utf-8"))
            out.append({k: d[k] for k in keep if k in d} if (keep is not None and isinstance(d, dict)) else d)
        except ValueError:
            pass
        i += n + 1
    return out


def dedup_sent(sym, day, states):
    """③ وصفًا: هل حملت المِرساةُ الغائبة حقلَ `sent` غيرَ فارغ (أي أُرسل لها إشعار)؟"""
    for st in states or ():
        v = (st or {}).get(f"LIQ:{sym}")
        if isinstance(v, dict) and str(v.get("date") or "") == day and has_anchor(v, day) and v.get("sent"):
            return True
    return False


def dedup_kind(sym, day, states):
    """③ وصفًا لمن وُجدت له مِرساة: «بلا سعر» (حاضرةٌ في أحدث لقطةٍ لليوم و`anchor_price` فارغ — مقياسُ `first_anchor` يُسقطها) ·
    «غابت» (ليست في أحدث لقطة) · «حاضرة» · أو None. و`states` بترتيب `git log` (الأحدثُ أوّلًا)."""
    if not dedup_hit(sym, day, states):
        return None
    v = (states[0] or {}).get(f"LIQ:{sym}") if states else None
    if not (isinstance(v, dict) and str(v.get("date") or "") == day and has_anchor(v, day)):
        return "غابت"
    return "بلا سعر" if v.get("anchor_price") in (None, "", 0) else "حاضرة"


def dedup_hit(sym, day, states):
    """③ الدِّدوب: مِرساةٌ ليوم `day` في `LIQ:sym` بتاريخه في أيّ لقطةٍ من `states`."""
    for st in states or ():
        v = (st or {}).get(f"LIQ:{sym}")
        if isinstance(v, dict) and str(v.get("date") or "") == day and has_anchor(v, day):
            return True
    return False


def op_gate(sym, key):
    """② بوّابةُ المضارب تاريخيًّا: آخرُ 20,000 صفقة قبل s ⟵ `_operator_blocks` بالاسم ⟵ True/False/None."""
    import requests
    import Super_stock as bot

    def _f(s):
        try:
            r = requests.get(f"https://api.polygon.io/v3/trades/{sym.upper()}", timeout=30,
                             headers={"Authorization": f"Bearer {key}"},
                             params={"timestamp.lte": int(s) * 1_000_000, "order": "desc",
                                     "limit": int(bot.LIQ_OPERATOR_TRADES), "sort": "timestamp"})
            if r.status_code != 200:
                return None
            tr = (r.json() or {}).get("results") or []
            rows = [(t.get("price"), t.get("size")) for t in tr if t.get("price") and t.get("size")]
            rows.reverse()
            ob = bot._operator_blocks(rows, bot.CONFIG["OPERATOR_MIN_SHARES"])
            return None if ob is None else bool(ob.get("has_operator"))
        except Exception:                                            # noqa: BLE001
            return None
    return _f


def mode_run():
    from concurrent.futures import ThreadPoolExecutor
    import Super_stock as bot
    from tier_fwd_report import fetch_day
    from tierlink_probe import daily_range
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key or not os.environ.get("GITHUB_TOKEN"):
        log("⛔ لا مفتاح Polygon أو GITHUB_TOKEN — لا قياس.")
        return 3
    pop = json.load(open(POP, encoding="utf-8"))
    allrows = [dict(x, role="nobody") for x in pop["nobody"]] + [dict(x, role="fired") for x in pop["fired"]]
    days = sorted({x["day"] for x in allrows})
    jobs, n_jobs, n_runs = worker_jobs(days)
    log(f"🧰 تشغيلاتُ العامل: {n_jobs} من {n_runs} تشغيلة · أيّامٌ بوظائف {len(jobs)} من {len(days)}")
    commits = {f: file_commits(f) for f in LIST_FILES}
    yml_c = file_commits(f".github/workflows/{WORKFLOW}")

    def crons_on(day):
        h = None
        for ct, hh in yml_c:
            if ct <= ny_ts(day, 0):
                h = hh
            else:
                break
        return parse_crons(_git(["show", f"{h}:.github/workflows/{WORKFLOW}"])) if h else None

    def _fetch(x):
        return (x["sym"], x["day"]), fetch_day(x["sym"], x["day"], key), daily_range(x["sym"], x["day"], key)
    with ThreadPoolExecutor(8) as pool:
        got = {k: (b, d) for k, b, d in pool.map(_fetch, allrows)}

    def _one(x):
        k = (x["sym"], x["day"])
        raw, dly = got.get(k, (None, None))
        bars = bar_dicts(raw, x["day"])
        if len(bars) < 5:
            return dict(x, gate="NA", detail="بلا شموع")
        p0 = None
        for d, _h, c in sorted(dly or []):
            if d < x["day"] and c:
                p0 = c
        tc = ({"usd": bot.LIQ_TC_USD, "pct": bot.LIQ_TC_PCT, "prev_close": float(p0)}
              if (p0 and TC_FROM <= x["day"] <= TC_TO) else None)
        iv = [(a, b) for a, b, _i in jobs.get(x["day"], [])]
        alive = intervals_fn(iv)
        mem = membership_fn(uni_timeline(x["sym"], x["day"], commits))
        F = replay(bars, x["day"], None, tc)
        FU = replay(bars, x["day"], mem, tc) if F["anchor_ms"] else F
        FA = replay(bars, x["day"], alive, tc) if F["anchor_ms"] else F
        FUA = replay(bars, x["day"], lambda s: mem(s) and alive(s), tc) if FU["anchor_ms"] else FU
        P = replay(bars, x["day"], lambda s: mem(s) and alive(s), tc, op_gate(x["sym"], key)) if FUA["anchor_ms"] else FUA
        g = attribute(F, FU, FUA, P)
        out = dict(x, gate=g, F=F, FU=FU, FA=FA, FUA=FUA, P=P)
        top_ms = next((b["t"] for b in bars if ny_parts(b["t"])[1] == x.get("top_m")), None)
        if g == "G1":
            vi = violent_index(bars, top_ms)
            main, dist, first = why_reasons(bars, vi, top_ms)
            out.update(g1_main=main, g1_dist=dist, g1_first=first,
                       detail=f"أعنفُ دقيقة {hm(ny_parts(bars[vi]['t'])[1]) if vi is not None else '—'}: {main or '—'}"
                              + (" · أوّلُ الجلسة" if first else ""))
        elif g == "G3":
            at = FU["anchor_ms"]
            b4, af, crons = gap_detail(iv, at, crons_on(x["day"]))
            out["detail"] = (f"زنادٌ {hm(ny_parts(at)[1])} · آخرُ عاملٍ انتهى {hm(ny_parts(b4)[1]) if b4 else '—'}"
                             f" · التالي بدأ {hm(ny_parts(af)[1]) if af else '—'} · كروناتٌ مجدولةٌ في الفجوة: {', '.join(crons) or 'لا'}")
        elif g == "G2":
            out["detail"] = f"زنادٌ {hm(ny_parts(F['anchor_ms'])[1])} والرمزُ خارج الكون حينها"
        elif g == "G4":
            out["detail"] = f"زنادٌ {hm(ny_parts(FUA['anchor_ms'])[1])} · كُتم {P['muted']} مرّة" + (" · بلغ سقفَ النداءات" if P.get("capped") else "")
        else:
            out["detail"] = f"`P` أرست {hm(ny_parts(P['anchor_ms'])[1])} والحيُّ لا"
        out["dedup"] = dedup_hit(x["sym"], x["day"], states.get(x["day"]))
        out["dedup_sent"] = dedup_sent(x["sym"], x["day"], states.get(x["day"]))
        out["dedup_kind"] = dedup_kind(x["sym"], x["day"], states.get(x["day"]))
        return out

    keep_by = {}
    for x in allrows:
        keep_by.setdefault(x["day"], set()).add(f"LIQ:{x['sym']}")
    states = {d: day_states(d, keep_by.get(d, set())) for d in days}
    log(f"🗂️ لقطاتُ الحالة: {sum(len(v) for v in states.values())} في {len(days)} يومًا")
    with ThreadPoolExecutor(4) as pool:
        done = list(pool.map(_one, allrows))
    nob = [x for x in done if x["role"] == "nobody"]
    fired = [x for x in done if x["role"] == "fired"]
    counts = {}
    for x in nob:
        counts[x["gate"]] = counts.get(x["gate"], 0) + 1
    fired_ok = [x for x in fired if x.get("gate") != "NA"]
    truth = [sum(1 for x in fired_ok if (x.get("P") or {}).get("anchor_ms")), len(fired_ok)]
    dts = sorted(abs(ny_parts(x["P"]["anchor_ms"])[1] - x["fire_m"]) for x in fired_ok
                 if (x.get("P") or {}).get("anchor_ms") and x.get("fire_m") is not None)
    g1 = [x for x in nob if x["gate"] == "G1"]
    g1_main, g1_dist = {}, {}
    for x in g1:
        if x.get("g1_main"):
            g1_main[x["g1_main"]] = g1_main.get(x["g1_main"], 0) + 1
        for r, n in (x.get("g1_dist") or {}).items():
            g1_dist[r] = g1_dist.get(r, 0) + n
    bars_fail = sum(1 for x in done if x.get("gate") == "NA")
    res = {"counts": counts, "truth": truth, "truth_ok": bool(truth[1] and truth[0] / truth[1] >= TRUTH_MIN),
           "truth_dt_med": (dts[len(dts) // 2] if dts else None), "bars_fail": bars_fail, "bars_n": len(done),
           "bars_ok": bars_fail <= BARS_FAIL_MAX * len(done),
           "g3_any": sum(1 for x in nob if (x.get("F") or {}).get("anchor_ms") and not (x.get("FA") or {}).get("anchor_ms")),
           "dedup": sum(1 for x in nob if x.get("dedup")), "g1_first": sum(1 for x in g1 if x.get("g1_first")),
           "dedup_ctrl": [sum(1 for x in fired if x.get("dedup")), len(fired)],
           "dedup_sent": sum(1 for x in nob if x.get("dedup_sent")),
           "dedup_names": [f"{x['sym']} {x['day'][5:]} ({x.get('dedup_kind')})" for x in nob if x.get("dedup")],
           "g1_main": g1_main, "g1_dist": g1_dist,
           "g1_top_reason": (max(g1_main.items(), key=lambda kv: kv[1])[0] if g1_main else None)}
    res["preds"] = predictions(res)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"), "sha": _git(["rev-parse", "HEAD"]).strip(), "jobs": n_jobs, "days": len(days)}
    nob.sort(key=lambda x: (GATES.index(x["gate"]) if x["gate"] in GATES else 9, x["day"], x["sym"]))
    for ln in report_lines(res, nob, meta):
        print(ln)
    slim = [{k: x.get(k) for k in ("sym", "day", "R", "gate", "detail", "dedup", "dedup_sent", "dedup_kind")} for x in nob]
    print("NOFIRE_ROWS " + json.dumps(slim, ensure_ascii=False))
    print("NOFIRE_JSON " + json.dumps({"res": res, "meta": meta}, ensure_ascii=False, default=str))
    return 0


def mode_check():
    ok = contract_ok()
    log(f"🔒 بصمةُ العقد والمجتمع: {'✅' if ok else '⛔'}")
    return 0 if ok else CONTRACT_RC


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "run"), default="check")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد أو ملفّ المجتمع تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    return mode_check() if a.mode == "check" else mode_run()


if __name__ == "__main__":
    sys.exit(main())
