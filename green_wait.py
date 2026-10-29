"""⏳ «الانتظارُ الأخضر» — سطرٌ في التقرير اليوميّ القائم (أمرُ المالك 2026-10-29 «أضف سطر الانتظار الأخضر» · تقرير الجزء أ §أ1-د ③).

النمطُ المقيس: عملٌ جاهزٌ أو مأمورٌ به ينتظر وكلُّ الفحوص خضراء ولا سطرَ في أيّ مكانٍ يقول إنه ينتظر — PR #630 بقي 12.3 يومًا مفتوحًا ·
فكُّ تجميد الرادار 15 يومًا بين الأمر والدمج · ومُلتقِطُ H6 جمع صفرًا 12 يومًا. والحارسُ واحد، **عرضٌ فقط بلا تلغرام جديد**:
  (أ) PR مفتوحٌ أكثرَ من `PR_MAX_H` ساعة.
  (ب) workflow مجدولٌ **بلا تشغيلةٍ مجدولة** منذ ثالثِ آخرِ فتحةٍ كان يجب أن يشتعل فيها — والفتحاتُ تُعَدّ حتى «الآن − `GRACE_H`»
      وحدَها، لأن GitHub يؤخّر الكرون ساعاتٍ (مقيسٌ 300-420 دقيقة على كرونات المستودع 10-26…10-29) فالفتحةُ الأحدثُ ليست فائتةً بعد.
  وتشغيلةٌ تخطّت جوباتِها (التجميد بـ`if`) **تشغيلةٌ** — فالمُجمَّدُ عمدًا لا يُعَدّ منتظرًا.

قراءةٌ فقط (GitHub REST بـ`GITHUB_TOKEN` الجوب) · فاشلٌ-آمن مطلقًا: بلا رمزٍ أو بعطلٍ ⟵ لا سطر (والسببُ يُعاد للسجلّ) · لا يمسّ أيَّ قرار.
"""
import datetime as dt
import glob
import os

PR_MAX_H = 48              # أمرُ المالك بنصّه
MISSED_SLOTS = 3           # «ثلاث فتحاتٍ متتالية» بنصّ التقرير
GRACE_H = 8                # فوق أقصى تأخّرٍ مقيسٍ هذا الأسبوع (‏≈7 ساعات) — engineering
UTC = dt.timezone.utc


def _field(spec, lo, hi):
    """قيمُ حقلٍ واحدٍ من cron (`*` · `*/n` · `a-b` · `a-b/n` · `a,b`) ⟵ مجموعة · وأيُّ صيغةٍ لا تُفهم ⟵ ValueError."""
    out = set()
    for part in str(spec).split(","):
        step = 1
        if "/" in part:
            part, st = part.split("/", 1)
            step = int(st)
            if step <= 0:
                raise ValueError(spec)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = (int(x) for x in part.split("-", 1))
        else:
            a = b = int(part)
        if a < lo or b > hi or a > b:
            raise ValueError(spec)
        out.update(range(a, b + 1, step))
    return out


def parse_cron(expr):
    """cron خماسيّ (UTC كما يقرؤه GitHub) ⟵ (دقائق، ساعات، أيام الشهر، أشهر، أيام الأسبوع، يومٌ مقيَّد؟، أسبوعٌ مقيَّد؟)."""
    f = str(expr).split()
    if len(f) != 5:
        raise ValueError(expr)
    dow = {0 if d == 7 else d for d in _field(f[4], 0, 7)}
    return (_field(f[0], 0, 59), _field(f[1], 0, 23), _field(f[2], 1, 31), _field(f[3], 1, 12), dow,
            f[2] != "*", f[4] != "*")


def _fires(p, t):
    mi, hr, dom, mon, dow, dom_r, dow_r = p
    if t.minute not in mi or t.hour not in hr or t.month not in mon:
        return False
    d_ok, w_ok = t.day in dom, ((t.weekday() + 1) % 7) in dow
    if dom_r and dow_r:
        return d_ok or w_ok           # دلالةُ cron: حين يُقيَّد الاثنان يكفي أحدُهما
    return d_ok and w_ok


def last_slots(crons, before, n=MISSED_SLOTS, horizon_days=10):
    """آخرُ `n` فتحاتٍ (UTC) لأيٍّ من الكرونات عند `before` أو قبله — بحثٌ دقيقةً دقيقة إلى الوراء حتى `horizon_days`."""
    ps = [parse_cron(c) for c in crons]
    t = before.astimezone(UTC).replace(second=0, microsecond=0)
    stop = t - dt.timedelta(days=horizon_days)
    out = []
    while t > stop and len(out) < n:
        if any(_fires(p, t) for p in ps):
            out.append(t)
        t -= dt.timedelta(minutes=1)
    return out


def workflow_crons(root="."):
    """{اسمُ الملفّ: [crons]} للـworkflows المجدولة من `.github/workflows` في المستودع نفسِه."""
    import yaml
    out = {}
    for f in sorted(glob.glob(os.path.join(root, ".github", "workflows", "*.yml"))):
        try:
            w = yaml.safe_load(open(f, encoding="utf-8")) or {}
            on = w.get("on", w.get(True)) or {}
            sch = on.get("schedule") if isinstance(on, dict) else None
            crons = [str(c.get("cron")) for c in (sch or []) if isinstance(c, dict) and c.get("cron")]
        except Exception:                                       # noqa: BLE001
            continue
        if crons:
            out[os.path.basename(f)] = crons
    return out


def _ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(UTC)
    except Exception:                                           # noqa: BLE001
        return None


def stale_prs(prs, now, hours=PR_MAX_H):
    """[(رقم، عنوانٌ مختصر، ساعاتُ الفتح)] لكلّ PR مفتوحٍ أكثرَ من `hours` — الأقدمُ أوّلًا."""
    out = []
    for p in prs or []:
        c = _ts((p or {}).get("created_at"))
        if c is None or (p or {}).get("state", "open") != "open":
            continue
        age = (now - c).total_seconds() / 3600.0
        if age > hours:
            out.append((p.get("number"), str(p.get("title") or "")[:40], age))
    return sorted(out, key=lambda x: -x[2])


def stale_workflows(crons_by_wf, last_run_by_wf, now, n=MISSED_SLOTS, grace_h=GRACE_H):
    """[(workflow، ثالثُ آخرِ فتحة، آخرُ تشغيلةٍ مجدولة أو None)] لكلّ workflow بلا تشغيلةٍ مجدولةٍ منذ ثالثِ آخرِ فتحةٍ قبل «الآن − المهلة».
    workflow لم يُقرأ له شيء (غائبٌ عن `last_run_by_wf`) ⟵ لا حكم (لا يُعَدّ منتظرًا) — فالتعذّرُ لا يصنع إنذارًا."""
    out = []
    cut = now - dt.timedelta(hours=grace_h)
    for wf, crons in sorted((crons_by_wf or {}).items()):
        if wf not in (last_run_by_wf or {}):
            continue
        try:
            sl = last_slots(crons, cut, n)
        except Exception:                                       # noqa: BLE001
            continue
        if len(sl) < n:
            continue
        third = sl[-1]
        last = _ts(last_run_by_wf.get(wf)) if last_run_by_wf.get(wf) else None
        if last is None or last < third:
            out.append((wf, third, last))
    return out


def green_wait_line(prs_stale, wf_stale):
    """السطرُ المعروض — فارغٌ حين لا انتظار · بلا علامات مقارنة."""
    parts = []
    for num, title, age in prs_stale:
        parts.append(f"PR #{num} مفتوحٌ منذ {age / 24:.1f} يوم ({title})")
    for wf, third, last in wf_stale:
        parts.append(f"{wf} بلا تشغيلةٍ مجدولة منذ {third:%m-%d %H:%M} UTC"
                     + (f" (آخرُها {last:%m-%d %H:%M})" if last else " (ولا واحدة مسجّلة)"))
    if not parts:
        return ""
    return "⏳ <b>انتظارٌ أخضر</b> (عملٌ واقفٌ وكلُّ الفحوص خضراء): " + " · ".join(parts)


def fetch_github(repo, token, wfs, get=None):
    """(PRs المفتوحة، {workflow: created_at لآخر تشغيلةٍ مجدولة}) من GitHub REST — `get` يُحقَن للاختبار · العطلُ يرمي ليُعلَن."""
    if get is None:
        import requests

        def get(url, params=None):
            r = requests.get(url, params=params, timeout=15,
                             headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
            r.raise_for_status()
            return r.json()
    base = f"https://api.github.com/repos/{repo}"
    prs = get(f"{base}/pulls", {"state": "open", "per_page": 50}) or []
    last = {}
    for wf in wfs:
        try:
            runs = (get(f"{base}/actions/workflows/{wf}/runs", {"event": "schedule", "per_page": 1}) or {}).get("workflow_runs") or []
        except Exception:                                       # noqa: BLE001
            continue                                            # تعذّرٌ لهذا وحدَه ⟵ لا حكمَ عليه
        last[wf] = runs[0].get("created_at") if runs else None
    return prs, last


def green_wait_report(now=None, root=".", env=None, get=None):
    """(السطر، سببُ الغياب) — نقطةُ النداء من الفرز اليوميّ · فاشلٌ-آمن."""
    env = os.environ if env is None else env
    now = now or dt.datetime.now(UTC)
    token, repo = (env.get("GITHUB_TOKEN") or "").strip(), (env.get("GITHUB_REPOSITORY") or "").strip()
    if get is None and env.get("SUPER_STOCKS_TESTING") == "1":
        return "", "السويّة — لا شبكة"                          # كحارس `git_save`: تحت السويّة بلا حقنٍ لا نداء
    if get is None and (not token or not repo):
        return "", "لا رمز GitHub في البيئة"
    try:
        crons = workflow_crons(root)
        prs, last = fetch_github(repo, token, list(crons), get=get)
        return green_wait_line(stale_prs(prs, now), stale_workflows(crons, last, now)), ""
    except Exception as e:                                      # noqa: BLE001
        return "", f"{type(e).__name__}: {str(e)[:120]}"
