# -*- coding: utf-8 -*-
"""🗓️🔎 «أسهمُ البوت هذا الأسبوع وشروطي الثلاثة» — كم سهمًا في قائمة البوت طابق (فلوت أقلّ من 4م · RSI أقلّ من 30 ·
«الشورت» أقلّ من 20 ألفًا · وفوق الدولار)، وهل انفجر منها شيءٌ هذا الأسبوع؟

أمرُ المالك (2026-09-25): «ابيك تقيس لي كم عدد أسهم الارتكاز المراقبة من البوت هذا الاسبوع و اللي تطابق هذي الشروط الثلاثة
فلوت تحت 4 مليون و rsi تحت 30 و الشورت تحت 20 الف و استثن اسهم السنتات … وهل فيه شي انفجر منها هذا الأسبوع ولا لا ركز زين».

**قراءةٌ فقط** · لا تلغرام · لا كتابةَ حالة · لا تغييرَ على الفرز · **والتعريفاتُ مثبَّتةٌ هنا قبل أيّ رقم RSI:**

① **المجتمع** = كلُّ سهمٍ نشطٍ في `weekly_watchlist.json` داخل **أحدثِ لقطةٍ على main قبل افتتاح** كلّ جلسةٍ من جلسات الأسبوع
   (09:30 نيويورك · بوقت الالتزام `%cI` = متى صار على main) — أي ما كان البوتُ يراقبه داخلًا إلى الجلسة · والاتّحادُ = «المراقَبة».
② **الشروط** لكلّ (سهم، جلسة d) بما كان معلومًا **قبل** d: RSI14 (`Super_stock.rsi` بالاسم) على إغلاقات Polygon اليوميّة
   `adjusted=true` حتى **إغلاق الجلسة السابقة c** (‏21 إغلاقًا على الأقلّ وإلّا مجهول) · والسعرُ = إغلاقُ c **الخامّ** (`adjusted=false`:
   تقسيمٌ لاحق لا يرفع سهمَ سنتاتٍ فوق الدولار) · والفلوتُ و«الشورت» = `float` و`shares_available` (المتاحُ من ChartExchange — سطرُ
   «شورت» في الكرت) **من لقطة d نفسِها** · والحدودُ بالاسم: `RSI_OWNER` · `FLOAT_OWNER` · `AVAIL_OWNER` (`opentry_link_probe`) و`PX_MIN`
   (`prelink_px`) · **والمجهولُ مجهولٌ لا «لا»**.
③ **الانفجار** = أقصى `high` (adjusted) من الجلسة d حتى آخر جلسةٍ منتهيةٍ في الأسبوع ÷ إغلاق c − 1 ⟵ +50% و+100% (والرقمُ يُطبع) —
   **ولو خرج السهمُ من القائمة بعدها** (السؤال: هل انفجر هذا الأسبوع؟).
④ **حارسا الصدق قبل الأرقام:** `V-W1` RSI المحسوب عند `ref_bar` يطابق `rsi` المخزَّن (ضمن نقطتين) لـ80% فأكثر من ترشيحات الأسبوع
   (5 فأكثر) وإلّا خروج 3 · `V-W2` شموعٌ لـ90% فأكثر من الرموز وإلّا خروج 3.
⑤ **بديلٌ يُطبع ولا يَحكم:** «الشورت» = حجمُ FINRA اليوميّ (`short`) أقلّ من 20 ألفًا.
⑥ **مجتمعٌ ثانٍ يُطبع ولا يَحكم — قائمةُ الارتداد** (`pullback` من اللقطة نفسِها · كلُّ حالاتها · خارجَ اتّحاد القائمة الرئيسيّة):
   «المتاح» لا يُخزَّن لها ⇒ **الاقترانُ مجهولٌ بالبناء** ⟵ تُطبع الثلاثةُ المعلومة (RSI · فلوت · دولار) وأقصى الصعود ·
   ولا تدخل سطرَ الحكم ولا `V-W2` · **وحالةُ المتابعة** (`cont_status`: ترشيحُ الأسبوع · مستمرّ · خرج من النموذج) تُطبع ولا تُصفّي.
⑦ **ملحقٌ مؤرَّخ 2026-09-25 — بعد التشغيلة الأولى `36194240914` وقبل أيّ رقمِ مطابقةٍ أو انفجار:** خرجت 3 بـ`V-W1` ‏17/22 =
   ‏77.3% · والساقطون الخمسة **كلُّهم شمعتُهم 09-18 ودخلوا main أثناء جلسة 09-18 نفسِها** (تشغيلتا فرزٍ يدويّتان 15:10-15:26 و
   18:50-19:02 UTC) ⇒ RSI البوت عليهم محسوبٌ على **شمعةٍ لم تكتمل** فلا يُقارَن بإغلاقٍ نهائيّ — عيبٌ في **مجموعة المقارنة** لا في
   الحساب. ⇒ `V-W1` يستبعد كلَّ ترشيحٍ **دخل main قبل إغلاق جلسة شمعته** (`ref_bar`) بمعيارٍ **زمنيٍّ لا بقيم RSI** (وقتُ الالتزام ·
   والإغلاقُ من التقويم بالاسم `session_info`) — ويُستبعد به ناجحون أيضًا · **والعتبةُ لا تُمَسّ** (نقطتان · 80% على 5) · **والنسبةُ لو
   دخلوا تُطبع** · **والشروطُ لا تقرأ RSI البوت أصلًا** (Polygon وحدَه) ⇒ لا أثرَ لهم على الحكم. ووقتُ الالتزام لا يسبق الحسابَ أبدًا ⇒
   الاستبعادُ لا يطال ترشيحًا حُسب بعد الإغلاق.
⑧ **ملحقٌ مؤرَّخ 2026-09-25 (ليلًا) — «الجلسة الممتدّة» بعد مسكة المالك «GCTK … محقق فوق 140٪ هذا الأسبوع»:** ③ يقيس **الجلسة
   النظاميّة وحدَها** (يوميُّ Polygon) وحدُّه كان مكتوبًا في حدود الصدق **لا في العنوان** ⇒ «لا سهمَ من الـ51 بلغ +50%» صحّ للنظاميّة
   وكذب على سؤال المالك: GCTK بلغ **5.46 في أفتر 09-23** (16:45 نيويورك · مِجَسّ الملفّات المجمَّعة `36201669055`) وأعلى نظاميّته 3.25.
   ⇒ **عمودٌ ثانٍ يُطبع بجانب ③ ولا يستبدله** (③ ونتائجُه المنشورة بت-بت):
   · **النافذة** `[start, end)`: `start` = الأحدثُ من **04:00 نيويورك يومَ أوّل جلسةٍ مراقَبة** ومن **أوّل ظهورٍ للسهم نشطًا على main**
     في الأسبوع (بوقت الالتزام · نشطٌ في آخر لقطةٍ قبل 04:00 أوّلِ جلسات الأسبوع ⇒ 04:00 نفسُها) — **فلا يُحتسب صعودٌ قبل أن تُرى
     القائمة** · و`end` = **20:00 نيويورك آخرَ جلسةٍ منتهية** أو لحظةُ التشغيل إن سبقتها (ويُطبع الحدّ).
   · **القمّة** = أقصى `high` لشموع دقيقة Polygon `adjusted=true` (البريماركت والأفتر ضمنًا) **بدأت داخل النافذة** ÷ إغلاق c نفسِه
     في ③ − 1 ⟵ +50/+100 · ويُطبع وقتُها وجلستُها (بري قبل 09:30 · نظاميّ حتى إغلاق التقويم · أفتر بعده).
   · **حارسان قبل الرقم:** `V-W3` شموعُ دقيقةٍ لـ90% فأكثر من الرموز · `V-W4` القمّةُ الممتدّة لا تقلّ عن النظاميّة بأكثر من نقطتين
     لـ90% فأكثر ممّن لهما القيمتان (النافذةُ الممتدّة تحوي جلساتِ ③ النظاميّة كلَّها بالبناء ⇒ النقصُ عطبُ جلب) — وسقوطُ أيٍّ منهما
     ⇒ العمودُ «لا حكم» **ولا يمسّ ③ ولا رمزَ الخروج**.
   · **وسطرُ الحكم الأخير يحمل العمودين معًا** (درسُ الخطأ: حدُّ الصدق الذي يغيّر الجواب مكانُه العنوانُ لا الحاشية).
   · **والرقمُ الممتدُّ الوحيد المعلومُ قبل هذا السطر = GCTK** — وبقيّةُ المجتمع لم تُقَس ممتدّةً قبله.

الخروج: 0 قياس · 2 بلا مفتاح · 3 حارسٌ ساقط · 4 لا لقطة/لا رمز · 5 ليست قراءةً فقط.
"""
import collections
import datetime as dt
import json
import os
import subprocess
import sys

import pandas as pd

import Super_stock as S                                              # rsi بالاسم
import market_calendar as MC                                         # إغلاقُ الجلسة بالاسم (⑦)
import opentry_link_probe as OPL                                     # حدودُ المالك بالاسم
import prelink_probe as P                                            # ticker_daily_adj · _get · API · _selfcheck_readonly
import prelink_px as PX                                              # PX_MIN بالاسم («فوق الدولار»)
from kasih_scan import NY
from link100_probe import year_days

WL_FILE = "weekly_watchlist.json"
WEEK = (os.environ.get("WATCH_WEEK") or "").strip()                  # اثنينُ الأسبوع YYYY-MM-DD · فارغ ⇒ أحدثُ أسبوع
HIST_DAYS = 400                  # engineering — أيّامٌ تقويميّة قبل الأسبوع ليتقارب RSI (Wilder) كحساب البوت
MIN_RSI_BARS = 21                # كـ`T-PRELINK`/`T-ALERT-TIME`
RSI_TOL, V_AGREE, V_MIN_N = 2.0, 0.80, 5                            # 🔒 V-W1
MIN_BAR_COVER = 0.90                                                 # 🔒 V-W2
EXPLODE = (50.0, 100.0)
CLOSED_AFTER = (16, 30)          # الجلسةُ «منتهية» بعد 16:30 نيويورك (هامشُ الشمعة اليوميّة) · الجاريةُ لا تُحتسب
EXT_FROM, EXT_TO = (4, 0), (20, 0)   # ⑧ البريماركت 04:00 ⟶ نهايةُ الأفتر 20:00 نيويورك (نافذةُ دقائق Polygon الممتدّة)
EXT_TOL = 2.0                    # ⑧ 🔒 V-W4 — نقطتان: الممتدّةُ لا تقلّ عن النظاميّة بأكثر منهما (engineering)
MIN_MIN_COVER = MIN_EXT_AGREE = 0.90                                 # ⑧ 🔒 V-W3 · V-W4
UTC = dt.timezone.utc


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── التقويم ───────────────────────────
def calendar(year):
    """أيّامُ التداول للسنة وسابقتِها بالاسم (`year_days`) مرتّبة."""
    return sorted(set(year_days(str(int(year) - 1)) + year_days(str(year))))


def prev_day(cal, d):
    xs = [x for x in cal if x < d]
    return xs[-1] if xs else None


def last_closed_day(cal, now_ny):
    """آخرُ جلسةٍ انتهت (بعد 16:30 نيويورك) — **الجاريةُ لا تُحتسب**."""
    today = now_ny.date().isoformat()
    done = (now_ny.hour, now_ny.minute) >= CLOSED_AFTER
    past = [d for d in cal if d < today or (d == today and done)]
    return past[-1] if past else None


def monday_of(d):
    x = dt.date.fromisoformat(d)
    return (x - dt.timedelta(days=x.weekday())).isoformat()


def week_days(cal, monday, last_day):
    """جلساتُ أسبوع `monday` (الاثنين-الجمعة) من التقويم — حتى آخر جلسةٍ منتهية."""
    fri = (dt.date.fromisoformat(monday) + dt.timedelta(days=4)).isoformat()
    return [d for d in cal if monday <= d <= fri and d <= last_day]


def open_utc(day):
    y, m, d = map(int, day.split("-"))
    return dt.datetime(y, m, d, 9, 30, tzinfo=NY).astimezone(UTC)


def close_utc(day):
    """إغلاقُ الجلسة النظاميّة ليوم `day` بـUTC — **من التقويم بالاسم** (`session_info`: ‏16:00 أو إغلاقٌ مبكّر) (⑦)."""
    mins = (MC.session_info(day) or {}).get("close_ny_min") or 16 * 60
    y, m, d = map(int, day.split("-"))
    return dt.datetime(y, m, d, mins // 60, mins % 60, tzinfo=NY).astimezone(UTC)


# ─────────────────────────── لقطاتُ القائمة ───────────────────────────
def wl_commits(path=WL_FILE):
    """[(وقتُ الالتزام UTC, hash)] من الأقدم — بوقت الالتزام (`%cI`) لا التأليف: متى صارت اللقطةُ على main."""
    out = subprocess.run(["git", "log", "--format=%H %cI", "--", path], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            rows.append((dt.datetime.fromisoformat(parts[1]).astimezone(UTC), parts[0]))
    return sorted(rows)


def snapshot_before(commits, cut):
    """أحدثُ التزامٍ **قبل** `cut` تمامًا (الالتزامُ عند 09:30:00 نفسِها بعدَه) ⟵ (t, h) أو None."""
    best = None
    for t, h in commits:
        if t < cut:
            best = (t, h)
        else:
            break
    return best


def load_snapshot(h, path=WL_FILE):
    try:
        return json.loads(subprocess.run(["git", "show", f"{h}:{path}"], capture_output=True, text=True).stdout)
    except ValueError:
        return None


def active_entries(js):
    """{رمز: مدخل} للنشط وحدَه."""
    return {s["symbol"]: s for s in ((js or {}).get("stocks") or [])
            if s.get("symbol") and s.get("status", "active") == "active"}


def pullback_entries(js):
    """{رمز: مدخل} لقائمة الارتداد كلِّها (مراقَبةٌ ومُطلَقة) — مجتمعٌ ثانٍ يُطبع ولا يَحكم (⑥)."""
    return {p["symbol"]: p for p in ((js or {}).get("pullback") or []) if p.get("symbol")}


CONT = {None: "ترشيحُ الأسبوع", "renewed": "أعاد التأهّل", "continues": "مستمرّ", "exited": "خرج من النموذج"}


def cont_label(e):
    """حالةُ المتابعة بالعربيّة (`cont_status`) — عرضٌ فقط."""
    return CONT.get((e or {}).get("cont_status"), str((e or {}).get("cont_status")))


# ─────────────────────────── الشروط والانفجار ───────────────────────────
def _num(x):
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


def flags(rsi, px, fl, av):
    """(RSI أقلّ من 30 · فلوت أقلّ من 4م · «شورت» أقلّ من 20 ألفًا · سعر 1$ فأكثر) — **المجهولُ None لا «لا»** · والحدودُ
    بالاسم وحصريّة (30 و4م و20 ألفًا ليست «أقلّ»)."""
    return (None if rsi is None else rsi < OPL.RSI_OWNER,
            None if fl is None else fl < OPL.FLOAT_OWNER,
            None if av is None else av < OPL.AVAIL_OWNER,
            None if px is None else px >= PX.PX_MIN)


def conj(xs):
    """الاقتران: «لا» متى سقط شرطٌ معلوم ولو جُهل غيرُه · ثمّ «مجهول» · ثمّ «نعم»."""
    if any(x is False for x in xs):
        return False
    if any(x is None for x in xs):
        return None
    return True


def rsi_at(adj, c):
    """RSI14 عند إغلاق `c` على إغلاقات adjusted **حتى c ضمنًا** ⟵ None إن قلّت عن `MIN_RSI_BARS`."""
    closes = [row[4] for row in adj if row[0] <= c]
    if len(closes) < MIN_RSI_BARS:
        return None
    return float(S.rsi(pd.Series(closes)).iloc[-1])


def close_at(rows, c):
    """إغلاقُ آخرِ شمعةٍ في `rows` تاريخُها c أو قبله ⟵ None."""
    xs = [row for row in rows if row[0] <= c]
    return xs[-1][4] if xs else None


def max_rise(adj, c, d_from, d_to):
    """أقصى `high` (adjusted) في [d_from, d_to] ÷ إغلاق c (adjusted) − 1 بالمئة ⟵ (pct, day) أو (None, None)."""
    c0 = close_at(adj, c)
    win = [row for row in adj if d_from <= row[0] <= d_to]
    if not c0 or c0 <= 0 or not win:
        return None, None
    best = max(win, key=lambda r: r[2])
    return (best[2] / c0 - 1.0) * 100.0, best[0]


def ext_bounds(d1, seen, last_day, now_utc):
    """⑧ النافذةُ الممتدّة `[start, end)` بـUTC: `start` = الأحدثُ من 04:00 نيويورك يومَ `d1` (أوّلِ جلسةٍ مراقَبة) ومن `seen`
    (أوّلِ ظهورٍ للسهم نشطًا على main · None ⟵ 04:00 نفسُها) — فلا يُحتسب صعودٌ قبل أن تُرى القائمة · و`end` = الأسبقُ من 20:00
    نيويورك يومَ `last_day` ومن `now_utc`."""
    y, m, d = map(int, d1.split("-"))
    t0 = dt.datetime(y, m, d, *EXT_FROM, tzinfo=NY).astimezone(UTC)
    y, m, d = map(int, last_day.split("-"))
    t1 = dt.datetime(y, m, d, *EXT_TO, tzinfo=NY).astimezone(UTC)
    return (t0 if seen is None else max(t0, seen)), min(t1, now_utc)


def max_rise_ext(mins, c0, start, end):
    """⑧ أقصى `high` لدقيقةٍ **بدأت** في `[start, end)` ÷ `c0` − 1 بالمئة ⟵ (pct, ms) أو (None, None) · و`mins` = [(ms, high)]."""
    if not c0 or c0 <= 0:
        return None, None
    lo, hi = start.timestamp() * 1000.0, end.timestamp() * 1000.0
    win = [b for b in mins if lo <= b[0] < hi]
    if not win:
        return None, None
    best = max(win, key=lambda b: b[1])
    return (best[1] / c0 - 1.0) * 100.0, best[0]


def sess_label(ms):
    """⑧ جلسةُ الدقيقة: «بري» قبل 09:30 نيويورك · «نظاميّ» حتى إغلاق التقويم (يعرف الإغلاقَ المبكّر) · «أفتر» بعده."""
    t = dt.datetime.fromtimestamp(ms / 1000.0, tz=UTC)
    day = t.astimezone(NY).date().isoformat()
    if t < open_utc(day):
        return "بري"
    return "نظاميّ" if t < close_utc(day) else "أفتر"


def vw4(pairs, tol=EXT_TOL):
    """⑧ `V-W4`: من [(رمز, نظاميّ%, ممتدّ%)] ⟵ (نسبةُ مَن لا تقلّ ممتدّتُه عن نظاميّته بأكثر من `tol` نقطة, n, الشاذّون) —
    النافذةُ الممتدّة تحوي جلساتِ ③ كلَّها بالبناء ⇒ النقصُ عطبُ جلب."""
    xs = [(s, r, e) for s, r, e in pairs if r is not None and e is not None]
    bad = [(s, r, e) for s, r, e in xs if e < r - tol]
    n = len(xs)
    return ((n - len(bad)) / n if n else 0.0), n, bad


def first_seen_map(commits, d1_by_sym, week_lo, pick=None, load=None):
    """⑧ {رمز: بدءُ ظهوره **المتّصل** نشطًا على main حتى لقطة ما قبل افتتاح `d1`} — يُرجَع من تلك اللقطة إلى الوراء ما دام
    نشطًا في كلّ التزام · فإن بلغ ما قبل `week_lo` ⟵ `week_lo` نفسُها · والغائبُ عن لقطة `d1` ⟵ غائبٌ عن القاموس. `pick` =
    مُستخرِجُ المجموعة (`active_entries` للرئيسيّة · `pullback_entries` للارتداد) · و`commits` مرتّبةٌ صعودًا."""
    pick = pick or active_entries
    load = load or load_snapshot
    cache = {}

    def act(h):
        if h not in cache:
            cache[h] = set(pick(load(h) or {}))
        return cache[h]
    out = {}
    for s, d in d1_by_sym.items():
        cut = open_utc(d)
        idx = max((i for i, (t, _h) in enumerate(commits) if t < cut), default=None)
        if idx is None or s not in act(commits[idx][1]):
            continue
        j = idx
        while j > 0 and commits[j][0] >= week_lo and s in act(commits[j - 1][1]):
            j -= 1
        out[s] = week_lo if commits[j][0] < week_lo else commits[j][0]
    return out


def partial_nominations(commits, first_entry, since, load=None):
    """{رمز: وقتُ دخوله main} لترشيحات الأسبوع (`added` من `since`) التي **ظهرت على main قبل إغلاق جلسة شمعتها** (`ref_bar`)
    بـ(`added`, `ref_bar`) نفسيهما ⇒ RSI البوت عليها محسوبٌ على شمعةٍ لم تكتمل (⑦). يُمسح ما بين منتصف ليل يوم الشمعة (نيويورك)
    وإغلاقها وحدَه · والتزاماتُ `commits` مرتّبةٌ صعودًا."""
    load = load or load_snapshot
    cache, out = {}, {}
    for sym, e in sorted(first_entry.items()):
        rb, ad = str(e.get("ref_bar") or "")[:10], str(e.get("added") or "")[:10]
        if not rb or ad < since:
            continue
        lo = dt.datetime(*map(int, rb.split("-")), tzinfo=NY).astimezone(UTC)
        cl = close_utc(rb)
        for t, h in commits:
            if t < lo:
                continue
            if t >= cl:
                break
            if h not in cache:
                cache[h] = load(h) or {}
            x = active_entries(cache[h]).get(sym)
            if x and str(x.get("ref_bar") or "")[:10] == rb and str(x.get("added") or "")[:10] == ad:
                out[sym] = t
                break
    return out


def vw1(first_entry, adj_by_sym, since, exclude=()):
    """`V-W1`: RSI المحسوب عند `ref_bar` مقابل `rsi` المخزَّن لترشيحات الأسبوع (`added` من `since`) ⟵ (نسبة, n, صفوف) ·
    و`exclude` = المُرشَّحون قبل إغلاق جلسة شمعتهم (⑦) خارج المقارنة."""
    rows = []
    for sym, e in sorted(first_entry.items()):
        rb, st = str(e.get("ref_bar") or "")[:10], _num(e.get("rsi"))
        if not rb or st is None or str(e.get("added") or "")[:10] < since or sym in exclude:
            continue
        mine = rsi_at(adj_by_sym.get(sym) or [], rb)
        if mine is None:
            continue
        rows.append((sym, rb, st, mine, abs(mine - st) <= RSI_TOL))
    n = len(rows)
    return (sum(1 for r in rows if r[4]) / n if n else 0.0), n, rows


# ─────────────────────────── الجلب ───────────────────────────
def fetch_raw(sym, d0, d1, key):
    """شموعٌ يوميّة **خامّة** (`adjusted=false`) لسعر «فوق الدولار» يومَها — بـ`_get` بالاسم (إعادةُ المحاولة)."""
    js = P._get(f"{P.API}/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}",
                {"adjusted": "false", "sort": "asc", "limit": "5000"}, key)
    out = []
    for b in (js or {}).get("results") or []:
        d = dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat()
        out.append((d, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0)))
    return out


def fetch_bars(sym, d0, d1, key):
    """(adjusted, خامّ) لكلّ رمز — adjusted بـ`ticker_daily_adj` بالاسم."""
    return P.ticker_daily_adj(sym, d0, d1, key), fetch_raw(sym, d0, d1, key)


def fetch_minutes(sym, d0, d1, key):
    """⑧ شموعُ دقيقة Polygon `adjusted=true` بين يومين (**البريماركت والأفتر ضمنًا** · 04:00-20:00 نيويورك) ⟵ [(ms, high)] —
    بـ`_get` بالاسم (إعادةُ المحاولة) · والشمعةُ التالفة تُتخطّى لا تُخمَّن."""
    js = P._get(f"{P.API}/v2/aggs/ticker/{sym}/range/1/minute/{d0}/{d1}",
                {"adjusted": "true", "sort": "asc", "limit": "50000"}, key)
    out = []
    for b in (js or {}).get("results") or []:
        try:
            out.append((int(b["t"]), float(b["h"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ─────────────────────────── الرئيسيّ ───────────────────────────
def _fmt(x, f="{:,.0f}"):
    return "—" if x is None else f.format(x)


def _mark(x):
    return "؟" if x is None else ("✓" if x else "✗")


def _when(ms):
    """⑧ «MM-DD HH:MM جلسة» بتوقيت نيويورك."""
    return f"{dt.datetime.fromtimestamp(ms / 1000.0, tz=NY):%m-%d %H:%M} {sess_label(ms)}"


def _ext_txt(x, ok, lead=" · ممتدًّا "):
    """⑧ ذيلُ السطر الممتدّ — فارغٌ إن سقط حارسا ⑧ أو لا قيمة (لا يُخمَّن رقم)."""
    if not ok or not x or x[0] is None:
        return ""
    return f"{lead}{x[0]:+.1f}% ({_when(x[1])})"


def main(now=None) -> int:                                           # noqa: PLR0911, PLR0912, PLR0915
    if not P._selfcheck_readonly(open(__file__, encoding="utf-8").read()):
        log("⛔ ليست قراءةً فقط")
        return 5
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا POLYGON_API_KEY")
        return 2
    now = now or dt.datetime.now(tz=NY)                              # يُحقَن في الأقفال · الحيُّ ساعةُ نيويورك
    cal = calendar(now.year)
    last_day = last_closed_day(cal, now)
    monday = WEEK or monday_of(last_day)
    days = week_days(cal, monday, last_day)
    commits = wl_commits()
    lists, pb_by = {}, {}
    for d in days:
        sb = snapshot_before(commits, open_utc(d))
        if not sb:
            continue
        js = load_snapshot(sb[1])
        if js is None:
            continue
        lists[d] = (sb[0], sb[1], active_entries(js))
        pb_by[d] = pullback_entries(js)
    if not lists:
        log(f"⛔ لا لقطةَ قبل أيّ جلسة في أسبوع {monday}")
        return 4
    wdays = sorted(lists)
    log(f"🗓️🔎 أسهمُ البوت أسبوعَ {wdays[0]} ⟶ {wdays[-1]} ({len(wdays)} جلسات منتهية) · الشروط: RSI أقلّ من {OPL.RSI_OWNER:g} · "
        f"فلوت أقلّ من {OPL.FLOAT_OWNER:,} · «شورت» (المتاح) أقلّ من {OPL.AVAIL_OWNER:,} · سعر ${PX.PX_MIN:.2f} فأكثر")
    for d in wdays:
        t, h, ents = lists[d]
        log(f"   📋 {d}: لقطةُ {t.astimezone(NY):%m-%d %H:%M} نيويورك ({h[:9]}) · نشطٌ {len(ents)}")
    union = sorted({s for d in wdays for s in lists[d][2]})
    first_entry = {}
    for d in wdays:
        for s, e in lists[d][2].items():
            first_entry.setdefault(s, e)
    if not union:
        log("⛔ صفرُ رمز")
        return 4
    log(f"👥 المراقَبة هذا الأسبوع (اتّحادُ القوائم قبل الافتتاح): {len(union)} رمزًا")
    last_entry = {}
    for d in wdays:
        for s, e in lists[d][2].items():
            last_entry[s] = e
    cc = collections.Counter(cont_label(last_entry[s]) for s in union)
    log("   حالةُ المتابعة (آخرُ لقطةٍ للرمز): " + " · ".join(f"{k} {v}" for k, v in sorted(cc.items(), key=lambda kv: -kv[1])))

    d0 = (dt.date.fromisoformat(wdays[0]) - dt.timedelta(days=HIST_DAYS)).isoformat()
    adj_by, raw_by = {}, {}
    for i, s in enumerate(union, 1):
        adj_by[s], raw_by[s] = fetch_bars(s, d0, wdays[-1], key)
        if i % 20 == 0:
            log(f"   … {i}/{len(union)}")
    covered = [s for s in union if adj_by.get(s)]
    cover = len(covered) / len(union)
    log(f"🩺 V-W2 الشموع: {len(covered)} من {len(union)} = {cover * 100:.1f}% (الحدّ {MIN_BAR_COVER * 100:.0f}%) · "
        f"بلا شموع: {', '.join(s for s in union if not adj_by.get(s)) or 'لا أحد'}")
    if cover < MIN_BAR_COVER:
        log("⛔ V-W2 ساقط — لا رقم")
        return 3
    since = prev_day(cal, wdays[0]) or wdays[0]
    part = partial_nominations(commits, first_entry, since)
    agree, n1, rows1 = vw1(first_entry, adj_by, since, exclude=part)
    log(f"🔒 V-W1 RSI عند `ref_bar` مقابل المخزَّن (ترشيحاتٌ من {since}): {sum(1 for r in rows1 if r[4])}/{n1} = {agree * 100:.1f}% "
        f"ضمن {RSI_TOL:g} نقطة (الحدّ {V_AGREE * 100:.0f}% على {V_MIN_N} فأكثر)")
    for r in rows1:
        log(f"      {r[0]:6} ref {r[1]} · مخزَّن {r[2]:.1f} · محسوب {r[3]:.1f} {'✓' if r[4] else '✗'}")
    if part:
        agree_all, n_all, rows_all = vw1(first_entry, adj_by, since)
        log(f"   ⑦ خارج المقارنة {len(part)} مُرشَّحًا دخلوا main **قبل إغلاق جلسة شمعتهم** (RSI البوت على شمعةٍ لم تكتمل) · "
            f"ولو دخلوا: {sum(1 for r in rows_all if r[4])}/{n_all} = {agree_all * 100:.1f}%")
        for sym, t in sorted(part.items()):
            e = first_entry[sym]
            log(f"      {sym:6} ref {str(e.get('ref_bar'))[:10]} · دخل main {t.astimezone(NY):%m-%d %H:%M} نيويورك "
                f"(الإغلاق {close_utc(str(e.get('ref_bar'))[:10]).astimezone(NY):%H:%M}) · مخزَّن {_fmt(_num(e.get('rsi')), '{:.1f}')}")
    if n1 >= V_MIN_N and agree < V_AGREE:
        log("⛔ V-W1 ساقط — RSI المحسوب لا يطابق RSI البوت ⇒ لا رقم")
        return 3
    if n1 < V_MIN_N:
        log(f"⚠️ V-W1 «لا يُحكم» (n={n1} دون {V_MIN_N}) — يُكمَل بلا تأكيد هُويّة RSI")

    # ── لكلّ (سهم، جلسة) ──
    per = collections.defaultdict(dict)
    for d in wdays:
        c = prev_day(cal, d)
        for s, e in lists[d][2].items():
            rsi = rsi_at(adj_by.get(s) or [], c)
            px = close_at(raw_by.get(s) or [], c)
            fl, av, fin = _num(e.get("float")), _num(e.get("shares_available")), _num(e.get("short"))
            f = flags(rsi, px, fl, av)
            alt = conj((f[0], f[1], None if fin is None else fin < OPL.AVAIL_OWNER, f[3]))
            per[s][d] = {"c": c, "rsi": rsi, "px": px, "float": fl, "avail": av, "finra": fin,
                         "f": f, "m": conj(f), "alt": alt}

    # ── ⑧ الجلسةُ الممتدّة — عمودٌ ثانٍ بجانب ③ لا بديلٌ عنه · وحارساه قبل أيّ رقمٍ ممتدّ ──
    now_utc = now.astimezone(UTC)
    week_lo = ext_bounds(wdays[0], None, wdays[-1], now_utc)[0]
    d1_by = {s: sorted(per[s])[0] for s in union}
    seen = first_seen_map(commits, d1_by, week_lo)
    reg, ext, mins_by = {}, {}, {}
    for s in union:
        c1 = per[s][d1_by[s]]["c"]
        reg[s] = max_rise(adj_by.get(s) or [], c1, d1_by[s], wdays[-1])
        mins_by[s] = fetch_minutes(s, wdays[0], wdays[-1], key)
        st, en = ext_bounds(d1_by[s], seen.get(s), wdays[-1], now_utc)
        ext[s] = max_rise_ext(mins_by[s], close_at(adj_by.get(s) or [], c1), st, en)
    ext_end = ext_bounds(wdays[-1], None, wdays[-1], now_utc)[1]
    n_min = sum(1 for s in union if mins_by.get(s))
    mcov = n_min / len(union)
    agree4, n4, bad4 = vw4([(s, reg[s][0], ext[s][0]) for s in union])
    ext_ok = mcov >= MIN_MIN_COVER and n4 > 0 and agree4 >= MIN_EXT_AGREE
    log(f"🌙 ⑧ الجلسةُ الممتدّة (البري والأفتر · عمودٌ ثانٍ لا يمسّ ③): من 04:00 نيويورك يومَ أوّل جلسةٍ مراقَبة أو أوّلِ ظهورٍ "
        f"على main (الأحدث) حتى {ext_end.astimezone(NY):%m-%d %H:%M} نيويورك")
    log(f"🩺 V-W3 شموعُ الدقيقة: {n_min} من {len(union)} = {mcov * 100:.1f}% (الحدّ {MIN_MIN_COVER * 100:.0f}%) · بلا شموع: "
        f"{', '.join(s for s in union if not mins_by.get(s)) or 'لا أحد'}")
    log(f"🔒 V-W4 الممتدّةُ لا تقلّ عن النظاميّة بأكثر من {EXT_TOL:g} نقطة: {n4 - len(bad4)}/{n4} = {agree4 * 100:.1f}% "
        f"(الحدّ {MIN_EXT_AGREE * 100:.0f}%)"
        + (" · الشاذّون: " + ", ".join(f"{b[0]} {b[1]:+.1f}/{b[2]:+.1f}" for b in bad4) if bad4 else ""))
    if not ext_ok:
        log("⚠️ ⑧ العمودُ الممتدّ «لا حكم» (V-W3/V-W4) — ③ قائمٌ كما هو ولا يتغيّر رمزُ الخروج")

    log("")
    log("=" * 78)
    log("📅 لكلّ جلسة: القائمةُ داخلًا إليها · المطابقون (الأربعة معًا) · المجهول")
    log("=" * 78)
    for d in wdays:
        rs = [per[s][d] for s in lists[d][2]]
        log(f"   {d}: القائمة {len(rs)} · يطابق {sum(1 for r in rs if r['m'] is True)} · مجهول {sum(1 for r in rs if r['m'] is None)} · "
            f"(RSI أقلّ من 30: {sum(1 for r in rs if r['f'][0])} · فلوت: {sum(1 for r in rs if r['f'][1])} · "
            f"متاح: {sum(1 for r in rs if r['f'][2])} · فوق الدولار: {sum(1 for r in rs if r['f'][3])})")

    log("")
    log("=" * 78)
    log("🧾 كلُّ سهمٍ مراقَب: [RSI · فلوت · متاح · دولار] عند إغلاق ما قبل كلّ جلسة · وأقصى صعودٍ هذا الأسبوع")
    log("=" * 78)
    matched, unknown, contrast = [], [], []
    for s in union:
        ds = sorted(per[s])
        d1 = ds[0]
        mr, mday = max_rise(adj_by.get(s) or [], per[s][d1]["c"], d1, wdays[-1])
        contrast.append((s, mr, mday, d1))
        cells = []
        for d in ds:
            r = per[s][d]
            cells.append(f"{d[5:]} RSI {_fmt(r['rsi'], '{:.1f}')} {''.join(_mark(x) for x in r['f'])}")
        mt = [d for d in ds if per[s][d]["m"] is True]
        tag = "🎯" if mt else ("❔" if any(per[s][d]["m"] is None for d in ds) else "  ")
        log(f" {tag} {s:6} {' | '.join(cells)} · أقصى صعودٍ {_fmt(mr, '{:+.1f}%')}"
            f"{'' if mday is None else ' (' + mday[5:] + ')'}{_ext_txt(ext.get(s), ext_ok)}")
        if mt:
            dm = mt[0]
            r = per[s][dm]
            mr2, md2 = max_rise(adj_by.get(s) or [], r["c"], dm, wdays[-1])
            st2, en2 = ext_bounds(dm, seen.get(s), wdays[-1], now_utc)
            xm = max_rise_ext(mins_by.get(s) or [], close_at(adj_by.get(s) or [], r["c"]), st2, en2)
            matched.append((s, dm, r, mr2, md2, len(mt), xm))
        elif any(per[s][d]["m"] is None for d in ds):
            unknown.append(s)

    log("")
    log("=" * 78)
    log("🎯 المطابقون (الأربعة معًا في جلسةٍ على الأقلّ) — وما جرى بعد أوّل مطابقة")
    log("=" * 78)
    for s, dm, r, mr2, md2, k, xm in matched:
        ex = " · ".join(f"+{int(t)}%: {'نعم' if (mr2 or -1e9) >= t else 'لا'}" for t in EXPLODE)
        log(f"   🎯 {s}: أوّلُ مطابقةٍ داخلًا إلى {dm} (إغلاق {r['c']}) · RSI {_fmt(r['rsi'], '{:.1f}')} · فلوت {_fmt(r['float'])} · "
            f"متاح {_fmt(r['avail'])} · سعر ${_fmt(r['px'], '{:.2f}')} · جلساتُ المطابقة {k} · أقصى صعودٍ بعدها "
            f"{_fmt(mr2, '{:+.1f}%')}{'' if md2 is None else ' (' + md2 + ')'} · {ex} · حالتُه: {cont_label(last_entry[s])}"
            f"{_ext_txt(xm, ext_ok, ' · وشاملًا البري والأفتر ')}")
    if not matched:
        log("   لا أحد")
    if unknown:
        log(f"   ❔ مجهولٌ (شرطٌ غيرُ معلوم ولا شرطَ ساقط): {', '.join(unknown)}")

    log("")
    log("=" * 78)
    log("💥 المقارنة: كلُّ مراقَبٍ بلغ +50% هذا الأسبوع (من إغلاق ما قبل أوّل جلسةٍ مراقَبة)")
    log("=" * 78)
    mset = {m[0] for m in matched}
    boom = sorted([c for c in contrast if c[1] is not None and c[1] >= EXPLODE[0]], key=lambda c: -c[1])
    for s, mr, mday, d1 in boom:
        log(f"   {'🎯' if s in mset else '  '} {s}: {mr:+.1f}% ({mday}) · مراقَبٌ من {d1}")
    if not boom:
        log("   لا أحد")
    log("")
    log("=" * 78)
    log("💥⑧ شاملًا البري والأفتر: كلُّ مراقَبٍ بلغ +50% هذا الأسبوع (من إغلاق ما قبل أوّل جلسةٍ مراقَبة · منذ ظهوره على main)")
    log("=" * 78)
    eboom = sorted((s for s in union if ext_ok and ext[s][0] is not None and ext[s][0] >= EXPLODE[0]),
                   key=lambda s: -ext[s][0])
    for s in eboom:
        log(f"   {'🎯' if s in mset else '  '} {s}: {ext[s][0]:+.1f}% ({_when(ext[s][1])}) · النظاميّة {_fmt(reg[s][0], '{:+.1f}%')} · "
            f"مراقَبٌ من {d1_by[s]}" + ("" if seen.get(s) is None else f" · ظهر على main {seen[s].astimezone(NY):%m-%d %H:%M}"))
    if not ext_ok:
        log("   لا حكم (V-W3/V-W4)")
    elif not eboom:
        log("   لا أحد")
    alt = sorted({s for s in union for d in per[s] if per[s][d]["alt"] is True})
    log(f"🔁 البديل «الشورت» = حجمُ FINRA اليوميّ أقلّ من {OPL.AVAIL_OWNER:,} (يُطبع ولا يَحكم): يطابق {len(alt)}"
        f"{' — ' + ', '.join(alt) if alt else ''} · ومجهولُ FINRA في "
        f"{sum(1 for s in union if all(per[s][d]['finra'] is None for d in per[s]))} رمزًا")
    last = wdays[-1]
    now_m = []
    for s, e in lists[last][2].items():
        f = flags(rsi_at(adj_by.get(s) or [], last), close_at(raw_by.get(s) or [], last),
                  _num(e.get("float")), _num(e.get("shares_available")))
        if conj(f) is True:
            now_m.append(s)
    log(f"🔭 عند إغلاق {last} (قائمةُ آخر جلسة · للأسبوع القادم قبل التجديد): يطابق {len(now_m)}"
        f"{' — ' + ', '.join(sorted(now_m)) if now_m else ''}")

    # ── ⑥ قائمةُ الارتداد — تُطبع ولا تَحكم ──
    pb_union = sorted({s for d in wdays for s in pb_by.get(d, {})} - set(union))
    log("")
    log("=" * 78)
    log(f"🔁 قائمةُ الارتداد (مستقلّة · تُطبع ولا تَحكم · «المتاح» لا يُخزَّن لها ⇒ الاقترانُ مجهولٌ بالبناء): {len(pb_union)} رمزًا")
    log("=" * 78)
    pb_three, pb_boom, pb_dead, pb_ext = [], [], [], []
    pb_seen = first_seen_map(commits, {s: min(d for d in wdays if s in pb_by.get(d, {})) for s in pb_union}, week_lo,
                             pick=pullback_entries)
    for s in pb_union:
        adj, raw = fetch_bars(s, d0, wdays[-1], key)
        if not adj:
            pb_dead.append(s)
            continue
        ds = sorted(d for d in wdays if s in pb_by.get(d, {}))
        cells, hit = [], []
        for d in ds:
            c = prev_day(cal, d)
            f = flags(rsi_at(adj, c), close_at(raw or [], c), _num(pb_by[d][s].get("float")), None)
            cells.append(f"{d[5:]} RSI {_fmt(rsi_at(adj, c), '{:.1f}')} {_mark(f[0])}{_mark(f[1])}{_mark(f[3])}")
            if f[0] and f[1] and f[3]:
                hit.append((d, c))
        mr, mday = max_rise(adj, prev_day(cal, ds[0]), ds[0], wdays[-1])
        st = pb_by[ds[-1]][s].get("status") or "—"
        pst, pen = ext_bounds(ds[0], pb_seen.get(s), wdays[-1], now_utc)
        px_ = max_rise_ext(fetch_minutes(s, wdays[0], wdays[-1], key), close_at(adj, prev_day(cal, ds[0])), pst, pen)
        if ext_ok and px_[0] is not None:
            pb_ext.append((s, px_[0]))
        log(f"   {'🎯' if hit else '  '} {s:6} [{st}] {' | '.join(cells)} · فلوت {_fmt(_num(pb_by[ds[-1]][s].get('float')))} · "
            f"أقصى صعودٍ {_fmt(mr, '{:+.1f}%')}{'' if mday is None else ' (' + mday[5:] + ')'}{_ext_txt(px_, ext_ok)}")
        if hit:
            mr3, _md3 = max_rise(adj, hit[0][1], hit[0][0], wdays[-1])
            pb_three.append((s, mr3))
        if mr is not None and mr >= EXPLODE[0]:
            pb_boom.append((s, mr))
    if pb_dead:
        log(f"   بلا شموع: {', '.join(pb_dead)}")
    t50 = sum(1 for _s, m in pb_three if m is not None and m >= EXPLODE[0])
    t100 = sum(1 for _s, m in pb_three if m is not None and m >= EXPLODE[1])
    log(f"🔁 الارتداد: {len(pb_union)} رمزًا · تستوفي الثلاثةَ المعلومة (RSI · فلوت · دولار) في جلسةٍ: {len(pb_three)}"
        f"{' (' + ', '.join(s for s, _m in pb_three) + ')' if pb_three else ''} · بلغ منها +50%: {t50} · +100%: {t100} · "
        f"وبلغ +50% من القائمة كلِّها: {len(pb_boom)}{' (' + ', '.join(s for s, _m in pb_boom) + ')' if pb_boom else ''} · "
        f"والمتاحُ مجهولٌ فلا تُحسب مطابقة")
    pe50 = [s for s, m in sorted(pb_ext, key=lambda x: -x[1]) if m >= EXPLODE[0]]
    pe100 = [s for s, m in sorted(pb_ext, key=lambda x: -x[1]) if m >= EXPLODE[1]]
    log("🔁⑧ الارتداد شاملًا البري والأفتر: " + ("لا حكم (V-W3/V-W4)" if not ext_ok else
        f"بلغ +50%: {len(pe50)}{' (' + ', '.join(pe50) + ')' if pe50 else ''} · +100%: {len(pe100)}"
        f"{' (' + ', '.join(pe100) + ')' if pe100 else ''}"))

    n50 = sum(1 for m in matched if m[3] is not None and m[3] >= EXPLODE[0])
    n100 = sum(1 for m in matched if m[3] is not None and m[3] >= EXPLODE[1])
    e50 = sum(1 for m in matched if m[6][0] is not None and m[6][0] >= EXPLODE[0])
    e100 = sum(1 for m in matched if m[6][0] is not None and m[6][0] >= EXPLODE[1])
    all_r = sum(1 for s in union if reg[s][0] is not None and reg[s][0] >= EXPLODE[0])
    log("")
    # ⑧ سطرُ الحكم يحمل العمودين: حدُّ الصدق الذي يغيّر الجوابَ مكانُه العنوانُ لا الحاشية
    log(f"🏁 المراقَبة هذا الأسبوع {len(union)} · تطابق الثلاثة وفوق الدولار {len(matched)} · انفجر منها +50%: {n50} · +100%: {n100} "
        f"(النظاميّة) · وشاملًا البري والأفتر: " + (f"+50%: {e50} · +100%: {e100}" if ext_ok else "لا حكم")
        + f" · ومن المراقَبة كلِّها بلغ +50%: نظاميًّا {all_r} · شاملًا البري والأفتر "
        + ((f"{len(eboom)}" + (f" ({', '.join(eboom)})" if eboom else "")) if ext_ok else "لا حكم"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
