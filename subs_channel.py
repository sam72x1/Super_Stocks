#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📣 قناةُ المشتركين — نسخةٌ مؤجَّلةٌ منظَّفة من رسائل الأدوات اليوميّة (أمرا المالك 2026-11-19 · عرضٌ وتوقيتٌ لا قياس).

**ما يذهب:** الرسائلُ المسمّاة في `ACTIVE` وحدَها (اسمٌ يُمرَّر من نقطة الإرسال · وما بلا اسمٍ لا يذهب أبدًا: الإكسل · الملفّات ·
«تحرّك 30%» · الظلّ · «شروطك الثلاثة» · دفترُ الصفقات · البطاقاتُ الحيّة · الأعطال · تقاريرُ القياس).
**كما هي إلّا اسم فيصل:** `sanitize` تستبدل عباراتِ الوسم («ظرف فيصل» ⟵ «الظرف» …) ثمّ تحذف كلَّ سطرٍ بقي فيه اسمُه أو حسابُه أو
مُعلِّمٌ من كلامه المنقول (الحرب · التصريف · «طاخ طيخ» · أمثلتُه بين قوسين) · ونسخةُ المالك لا تُمَسّ (التنظيفُ على نسخة القناة وحدَها).
**التوقيت:** موعدُ القناة `SEND_AT` بتوقيت الرياض (06:00 افتراضًا) — رسالةٌ جاهزةٌ قبله تُحفظ في صندوقٍ مشفّر (`subs_outbox/` ·
ملفٌّ لكلّ رسالة · لا تعارضَ بين الأدوات) ويُرسلها `flush` عند الموعد (مُطلِقُ الصباح يُطلق `subs_sender.yml` · وكروناتُه احتياطٌ) ·
ورسالةٌ جاهزةٌ بعده تُرسَل فورًا وأوّلُها سطرُ «⏰ تأخّر الإرسال» · وما بعد 21:00 الرياض فلصباح الغد.
**النشر:** `sendMessage` (منشورٌ مكتوب لا «محوّلة من») · HTML وإعادةٌ نصًّا صريحًا عند خطأ التنسيق · ولا رقمَ محادثةٍ في السجلّ.
↩️ **المفتاح:** `ON = False` ⟵ صفرُ عمل في كلّ أداة (نسخةُ المالك ومساراتُها بت-بت) · وغيابُ `TELEGRAM_SUBS_CHAT_ID` ⟵ لا إرسال.
🔒 لا عتبةَ ولا اختيارَ ولا جذرَ يُمَسّ · `SUB1`-`SUB9`.
"""
import datetime as dt
import hashlib
import os
import re
import sys
import time

import journal_vault as JV

ON = False                                  # ↩️ مطفأٌ حتى يوافق المالكُ على القائمة والعيّنات
ENV_CHAT = "TELEGRAM_SUBS_CHAT_ID"
SEND_AT = "06:00"                           # بتوقيت الرياض (UTC+3 ثابت) · أمرُ المالك 2026-11-19
EVENING_HOUR = 21                           # رسالةٌ بعد 21:00 الرياض ⟵ لموعد صباح الغد
GRACE_MIN = 10                              # إرسالُ الموعد بعده بأكثر من هذا ⟵ سطرُ «تأخّر الإرسال»
WAIT_MAX_MIN = 15                           # المُرسِلُ يُطلَق قبل الموعد ⟵ ينتظره ما دام في هذي الدقائق (`flush --wait`)
OUTBOX = "subs_outbox"
_SALT = "super-stocks|subs-outbox|v1|"
UTC = dt.timezone.utc
RIYADH = dt.timezone(dt.timedelta(hours=3))

# الاسم ⟵ وصفُه للمالك · بالترتيب الذي تُرسَل به رسائلُ الموعد الواحد
NAMES = {
    "daily_report": "📋 التقرير اليوميّ «قائمة الأسبوع» بأقسامه (الجاهز للدخول · شُطب اليوم · الارتداد الواصل · متابعة أسهم الصيّاد · 🏁 انفجر · 👀 تحت المتابعة · سطورُ التنبيه)",
    "hand": "🕵️ «أسهم فيها علامات يد» (من الفرز اليوميّ)",
    "split_radar": "🎯 «رادار أسهم التقسيم» (من الفرز اليوميّ)",
    "tracking": "📡 «متابعة التنبيهات السابقة» (هدفٌ تحقّق · وقفٌ ضُرب · انتهت)",
    "split_hunter": "🪝 «صيّاد أسهم التقسيم» (المطابق أو «لا يوجد»)",
    "split_filter": "🧮 «فلترة أسهم التقسيم» (المطابق أو «لا يوجد»)",
    "press": "🗜️ «رادار الضغط»",
    "presession": "📒 «حصاد قائمة ما قبل الجلسة»",
    "renewal_list": "🔄 «القائمة الأسبوعية الجديدة» (الجمعة)",
    "wrapup": "🧺 «حصاد الأسبوع» (الجمعة)",
    "fate": "🔄 «مصير أسهم الأسبوع الماضي» (الجمعة)",
    "weekly_report": "📊 «التقرير الأسبوعي» للأداء (الجمعة)",
}
ACTIVE = ("daily_report", "hand", "split_radar", "tracking", "split_hunter", "split_filter", "press", "presession")
NOT_SENT = ("🔬 «النهج العلمي» (ليس في قائمتك)", "📐 صيّاد الغلاف — صامتٌ بقرار: لا رسالةَ له أصلًا",
            "📣 «تحرّك 30%» · 🌘 الظلّ · 🔎📬 «شروطك الثلاثة» · 📎 الإكسل · 📒 دفترُ الصفقات · 🎯 البطاقاتُ الحيّة",
            "⛔ رسائلُ الأعطال وتأجيلُ التجديد وتقادمُه · 🔬 مساعدُ التطوير · 🕵️ تحديثُ اليد المسائيّ · كلُّ تقارير القياس")

# عباراتُ الوسم ⟵ صيغةٌ محايدة (الأطولُ أوّلًا · تُطبَّق قبل أيّ حذف)
LABELS = (
    ("(فيصل · ", "("), ("هدفُ فيصل الأوّل", "الهدفُ الأوّل"), ("هدفُ فيصل", "الهدف"), ("نطاق فيصل", "النطاق"),
    ("خطة فيصل النموذجية", "الخطة النموذجية"), ("خطّة فيصل النموذجيّة", "الخطّة النموذجيّة"),
    ("حركة فيصل المتوقّعة", "الحركة المتوقّعة"), ("حركة فيصل المتوقعة", "الحركة المتوقعة"),
    ("سعر انتظار فيصل", "سعر الانتظار"), ("منطقة انتظار فيصل", "منطقة الانتظار"),
    ("ظرفِ فيصل", "الظرف"), ("ظرف فيصل", "الظرف"), ("كتالوج فيصل", "الكتالوج"), ("كاتالوج فيصل", "الكاتالوج"),
    ("منهجية فيصل", "المنهجية"), ("منهجيّة فيصل", "المنهجيّة"), ("منهج فيصل", "المنهج"), ("مستويات فيصل", "المستويات"),
    ("وصفةُ فيصل", "الوصفة"), ("وصفة فيصل", "الوصفة"), ("حدّ فيصل", "الحدّ"), ("حد فيصل", "الحد"),
    ("زنادُ فيصل", "الزناد"), ("زناد فيصل", "الزناد"), ("نموذج فيصل", "النموذج"), ("نموذجُ فيصل", "النموذج"),
    ("أرقامُ فيصل", "الأرقام"), ("أرقام فيصل", "الأرقام"), ("معايير فيصل", "المعايير"), ("بوّابات فيصل", "البوّابات"),
    ("متوسطات فيصل", "المتوسطات"), ("بإعدادات فيصل", "بالإعدادات"), ("إعدادات فيصل", "الإعدادات"),
)
_NAME = re.compile(r"فيصل|kisar", re.I)
# كلامُه المنقول عن الشورت والحرب والتصريف ⟵ السطرُ كاملًا
_NOTE = re.compile(r"حرب|تصريف|يصرّف|يصرف|طاخ طيخ|ذخيرة هبوط|ارتفاع النسبة|ارتفعت النسبة")
# أمثلتُه بين قوسين ⟵ القوسُ يُحذف (رمزُ السهم المعروض في صفّه بلا قوسين أو بعلامة $ فلا يُمَسّ)
EXAMPLES = ("DSY", "ELAB", "XHLD", "LABT", "ZCMD", "EZRA", "JZ", "JEM", "YYAI", "NAMM", "ENPH", "VMAR", "SPPL", "CUR", "GDHG",
            "NUWE", "CUPR", "WORX", "TDIC", "CANF", "MTVA", "TRUG", "SMX", "LNAI")
_EX_PAREN = re.compile(r"\([^()]*\b(?:" + "|".join(EXAMPLES) + r")\b[^()]*\)")
_OPEN, _CLOSE = "(«", ")»"
_SEPS = (" · ", " — ")
LATE_LINE = "⏰ <b>تأخّر الإرسال</b> — موعدُ القناة {at} بتوقيت السعودية"


def log(m=""):
    print(f"[{dt.datetime.now(UTC).strftime('%H:%M:%S')}] {m}", flush=True)


def on():
    return bool(ON)


def parse_ids(raw):
    """مُحلِّلُ أرقام المحادثات (الفاصلةُ العربية والمنقوطة والسطرُ والمسافة) — مطابقٌ لـ`Super_stock._parse_chat_ids` (`SUB5`)."""
    raw = (raw or "").replace(";", ",").replace("،", ",").replace("؛", ",").replace("\n", ",") \
        .replace("\r", ",").replace("\t", ",").replace(" ", ",")
    out = []
    for c in raw.split(","):
        c = c.strip()
        if c and c not in out:
            out.append(c)
    return out


def targets(env=None):
    env = os.environ if env is None else env
    return parse_ids(env.get(ENV_CHAT, ""))


def bad(text):
    """🔒 هل يحمل النصُّ اسمَ فيصل أو حسابَه؟ (الحارسُ الأخير قبل أيّ إرسال)."""
    return bool(re.search(r"فيصل|kisar", text or "", re.I))


_QUOTED = re.compile(r"«|(?:فيصل|kisar)\s*:", re.I)


def _quoted(seg):
    """قوسٌ يحمل الاسم **مع** كلامٍ منقول («…» أو «فيصل:») ⟵ اقتباسٌ منسوبٌ له."""
    return bool(_NAME.search(seg) and _QUOTED.search(seg))


def _strip_name_parens(ln, pred=None):
    """يحذف كلَّ قوسٍ (‏«(…)» أو «‹«…»›») يحمل الاسم (أو يُرضي `pred`) — بعمقه (المتداخلُ يُحذف مع حاويه)."""
    pred = pred or (lambda seg: bool(_NAME.search(seg)))
    out, stack = [], []                    # stack: مواضعُ البدء في out
    for ch in ln:
        if ch in _OPEN:
            stack.append(len(out))
            out.append(ch)
        elif ch in _CLOSE and stack:
            st = stack.pop()
            out.append(ch)
            if pred("".join(out[st:])):
                del out[st:]
                while out and out[-1] == " ":
                    out.pop()
        else:
            out.append(ch)
    return "".join(out)


def _segments(ln):
    """يقسم السطر على « · » و« — » في العمق صفر وحدَه ⟵ [(فاصلٌ قبله، المقطع)]."""
    segs, cur, sep, depth, i = [], [], "", 0, 0
    while i < len(ln):
        ch = ln[i]
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE and depth:
            depth -= 1
        if depth == 0:
            hit = next((s for s in _SEPS if ln.startswith(s, i)), None)
            if hit:
                segs.append((sep, "".join(cur)))
                cur, sep = [], hit
                i += len(hit)
                continue
        cur.append(ch)
        i += 1
    segs.append((sep, "".join(cur)))
    return segs


def _balanced(ln):
    return all(ln.count(f"<{t}>") == ln.count(f"</{t}>") for t in ("b", "i", "u", "s", "code"))


def sanitize(text):
    """🔒 **نقيّة**: نسخةُ القناة. لكلّ سطر بالترتيب: ⓪ قوسٌ فيه اسمُه مع كلامٍ منقول («…» أو «فيصل:») يُحذف · ① عباراتُ الوسم محايدة · ② كلامُه عن الشورت/الحرب/التصريف ⟵ السطرُ
    كاملًا · ومثالُه بين قوسين ⟵ القوسُ · ③ كلُّ قوسٍ يحمل الاسم يُحذف · ④ كلُّ مقطعٍ (« · » أو « — ») يحمل الاسم يُحذف — وإن كان رأسَ السطر
    فالسطرُ كاملًا · ⑤ ما بقي فيه الاسم ⟵ السطرُ كاملًا (حارس) · ⑥ وسومُ HTML غيرُ المتوازنة بعد الحذف تُنزع من سطرها ·
    والأسطرُ الفارغة المتتالية تُطوى. نسخةُ المالك لا تمرّ من هنا."""
    out = []
    for ln in (text or "").split("\n"):
        orig = ln
        if _NAME.search(ln):                       # ⓪ الاقتباسُ المنسوبُ له بين قوسين يُحذف قبل أن تُحيّده عباراتُ الوسم
            ln = _strip_name_parens(ln, _quoted)
        for a, b in LABELS:
            ln = ln.replace(a, b)
        if _NOTE.search(ln):
            continue
        ln = re.sub(r" ?" + _EX_PAREN.pattern, "", ln)
        if _NAME.search(ln):
            ln = _strip_name_parens(ln)
        if _NAME.search(ln):
            segs = _segments(ln)
            if _NAME.search(segs[0][1]):
                continue
            ln = "".join(sep + seg for sep, seg in segs if not _NAME.search(seg))
        if _NAME.search(ln):
            continue
        if ln != orig and not _balanced(ln):
            ln = _strip_tags(ln)
        if not ln.strip() and out and not out[-1].strip():
            continue
        out.append(ln)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def _at(env=None):
    env = os.environ if env is None else env
    s = str(env.get("SUBS_SEND_AT") or SEND_AT).strip()
    h, m = (int(x) for x in s.split(":"))
    if not (0 <= h < EVENING_HOUR and 0 <= m < 60):
        raise ValueError(f"SUBS_SEND_AT {s} خارج 00:00-{EVENING_HOUR - 1}:59")
    return h, m


def due_for(now, env=None):
    """🔒 **نقيّة**: (لحظةُ الموعد UTC، متأخّرة؟) لرسالةٍ جاهزةٍ لحظةَ `now` — قبل موعد اليوم ⟵ موعدُ اليوم · بعده ⟵ متأخّرة (تُرسَل الآن) ·
    وبعد 21:00 الرياض ⟵ موعدُ الغد."""
    h, m = _at(env)
    r = now.astimezone(RIYADH)
    day = r.date() + dt.timedelta(days=1 if r.hour >= EVENING_HOUR else 0)
    due = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=RIYADH).astimezone(UTC)
    return due, now > due


def at_text(env=None):
    h, m = _at(env)
    return f"{h:02d}:{m:02d}"


def _pass(env=None):
    env = os.environ if env is None else env
    t = str(env.get("TELEGRAM_BOT_TOKEN") or "").strip()
    return hashlib.sha256((_SALT + t).encode()).hexdigest() if t else None


def _strip_tags(t):
    return re.sub(r"</?(?:b|i|u|s|code|pre|a)(?: [^>]*)?>", "", t or "")


def _send(chunks, env=None, post=None, late=False):
    """`sendMessage` لكلّ رقمٍ في السرّ · ⟵ True إن وصلت كلُّ الأجزاء لكلّ رقم · ولا رقمَ محادثةٍ في السجلّ."""
    env = os.environ if env is None else env
    ids, tok = targets(env), str(env.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not ids or not tok:
        return False
    if post is None:
        import requests
        post = requests.post
    parts = list(chunks)
    if late and parts:
        parts[0] = LATE_LINE.format(at=at_text(env)) + "\n\n" + parts[0]
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    ok = True
    for ch in parts:
        if bad(ch):                                 # الحارسُ الأخير — لا يُتوقَّع بالبناء
            log("⛔ قناة المشتركين: جزءٌ يحمل الاسم بعد التنظيف — رُفض")
            ok = False
            continue
        for cid in ids:
            try:
                r = post(url, json={"chat_id": cid, "text": ch, "parse_mode": "HTML",
                                    "disable_web_page_preview": True}, timeout=30)
                if r.status_code != 200 and "can't parse entities" in (r.text or ""):
                    r = post(url, json={"chat_id": cid, "text": _strip_tags(ch),
                                        "disable_web_page_preview": True}, timeout=30)
                if r.status_code != 200:
                    ok = False
                    log(f"⚠️ قناة المشتركين رفضت: HTTP {r.status_code}")
            except Exception as e:                  # noqa: BLE001
                ok = False
                log(f"⚠️ قناة المشتركين: {type(e).__name__}")
        time.sleep(1)
    return ok


def active(key, env=None):
    env = os.environ if env is None else env
    return on() and key in ACTIVE and bool(targets(env)) and bool(str(env.get("TELEGRAM_BOT_TOKEN") or "").strip())


def month_dirs(now):
    """🔒 **نقيّة**: مجلّدا الصندوق اللذان يُقرآن — شهرُ `now` (UTC) والشهرُ قبله (`subs_outbox/YYYY-MM` · مجلّدٌ لكلّ شهر ⟵ قائمةُ GitHub
    تبقى دون حدّ الألف ملفّ ولا يُحذف شيء)."""
    first = now.astimezone(UTC).replace(day=1)
    prev = (first - dt.timedelta(days=1))
    return [f"{OUTBOX}/{first.strftime('%Y-%m')}", f"{OUTBOX}/{prev.strftime('%Y-%m')}"]


def _item_path(key, due, chunks):
    h = hashlib.sha256((key + "\n".join(chunks)).encode()).hexdigest()[:10]
    order = list(NAMES).index(key) if key in NAMES else 99
    return os.path.join(OUTBOX, due.astimezone(UTC).strftime("%Y-%m"), f"{due.strftime('%Y%m%d%H%M')}_{order:02d}_{key}_{h}.vault")


def enqueue(key, chunks, now=None, env=None, post=None, saver=None):
    """رسالةٌ مسمّاة ⟵ تُنظَّف ⟵ قبل الموعد تُحفظ مشفّرةً في الصندوق · وبعده تُرسَل فورًا بسطر «تأخّر الإرسال».
    ⟵ «off» · «empty» · «queued» · «late_sent» · «late_queued» (تعذّر الإرسال فحُفظت ليُعيدها `flush`) · «nokey»."""
    env = os.environ if env is None else env
    if not active(key, env):
        return "off"
    now = now or dt.datetime.now(UTC)
    if isinstance(chunks, str):
        chunks = [chunks]
    clean = [c for c in (sanitize(x) for x in chunks) if c.strip()]
    if not clean:
        return "empty"
    due, late = due_for(now, env)
    if late:
        if _send(clean, env, post, late=True):
            log(f"📣 قناة المشتركين ⟵ {key}: أُرسلت متأخّرةً ({len(clean)} جزءًا)")
            return "late_sent"
        due = now
    pw = _pass(env)
    if pw is None:
        return "nokey"
    path = _item_path(key, due, clean)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = JV.encrypt({"key": key, "chunks": clean, "created": now.isoformat(), "due": due.isoformat()}, pw)
    if txt is None:
        return "nokey"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(txt)
    if saver is not None:
        try:
            saver([path])
        except Exception as e:                      # noqa: BLE001
            log(f"⚠️ قناة المشتركين: دفعُ الصندوق {type(e).__name__}")
    log(f"📣 قناة المشتركين ⟵ {key}: {'حُفظت لإعادة الإرسال' if late else 'حُفظت لموعد ' + due.strftime('%Y-%m-%d %H:%M UTC')}")
    return "late_queued" if late else "queued"


def unsent_names(names):
    """🔒 **نقيّة**: من أسماء ملفّات الصندوق ⟵ [(اسمُ الـvault، موعدُه UTC)] لما لم يُختم بـ`.sent` — بالترتيب (الموعد · ترتيبُ الأسماء).
    الموعدُ من بادئة الاسم (`YYYYmmddHHMM_`) فيقرؤه مُطلِقُ الصباح من قائمة main بلا فكّ تشفير."""
    names = set(names or [])
    out = []
    for n in sorted(names):
        if not n.endswith(".vault") or n[:-len(".vault")] + ".sent" in names:
            continue
        try:
            due = dt.datetime.strptime(n[:12], "%Y%m%d%H%M").replace(tzinfo=UTC)
        except ValueError:
            continue
        out.append((n, due))
    return out


def _unsent(now):
    out = []
    for d in month_dirs(now):
        if os.path.isdir(d):
            out += [(n, due, d) for n, due in unsent_names(os.listdir(d))]
    return sorted(out, key=lambda x: (x[1], x[0]))


def pending(env=None, now=None):
    """عناصرُ الصندوق التي حلّ موعدُها ولم تُختم «أُرسلت» — بالترتيب (الموعد · ترتيبُ الأسماء)."""
    pw = _pass(env)
    if pw is None:
        return []
    now = now or dt.datetime.now(UTC)
    out = []
    for n, due, d in _unsent(now):
        if due > now:
            continue
        p = os.path.join(d, n)
        v = JV.decrypt(open(p, encoding="utf-8").read(), pw)
        if not v:
            log(f"⚠️ قناة المشتركين: تعذّر فكُّ {n}")
            continue
        out.append((p, v))
    return out


def wait_due(now_fn=None, sleep=None):
    """المُرسِلُ يُطلَق قبل الموعد ببضع دقائق: أقربُ عنصرٍ لم يُرسَل موعدُه في `WAIT_MAX_MIN` القادمة ولا شيءَ حلّ قبله ⟵ ينام حتى الموعد."""
    now_fn = now_fn or (lambda: dt.datetime.now(UTC))
    sleep = sleep or time.sleep
    now = now_fn()
    dues = [d for _n, d, _dir in _unsent(now)]
    if not dues or min(dues) <= now:
        return 0.0
    wait = (min(dues) - now).total_seconds()
    if wait > WAIT_MAX_MIN * 60:
        return 0.0
    log(f"⏳ قناة المشتركين: انتظارُ الموعد {min(dues).strftime('%H:%M UTC')} ({wait:.0f} ث)")
    sleep(wait)
    return wait


def flush(now=None, env=None, post=None, saver=None):
    """موعدُ القناة: يُرسل ما حلّ موعدُه ويختم كلًّا بملفّ `.sent` (لا حذف) · بعد الموعد بأكثر من `GRACE_MIN` ⟵ بسطر «تأخّر الإرسال»."""
    env = os.environ if env is None else env
    if not on():
        log("↩️ قناة المشتركين مطفأة — لا إرسال")
        return 0
    if not targets(env):
        log("🔑 لا `TELEGRAM_SUBS_CHAT_ID` — لا إرسال")
        return 0
    now = now or dt.datetime.now(UTC)
    sent, marks = 0, []
    due_items = pending(env, now)
    n = len(due_items)
    for p, v in due_items:
        late = now > dt.datetime.fromisoformat(v["due"]) + dt.timedelta(minutes=GRACE_MIN)
        if _send(v.get("chunks") or [], env, post, late=late):
            mk = p[:-len(".vault")] + ".sent"
            with open(mk, "w", encoding="utf-8") as fh:
                fh.write(now.isoformat() + "\n")
            marks.append(mk)
            sent += 1
            log(f"📣 قناة المشتركين ⟵ {v.get('key')}: أُرسلت{' متأخّرة' if late else ''}")
    if marks and saver is not None:
        saver(marks)
    log(f"📣 قناة المشتركين: أُرسل {sent} من {n}" if n else "📣 قناة المشتركين: لا شيءَ حلّ موعدُه")
    return sent


def manifest():
    return (["📣 يذهب لقناة المشتركين:"] + ["  • " + NAMES[k] for k in ACTIVE]
            + ["⏸️ موسومٌ ولا يذهب (قرارُك):"] + ["  • " + v for k, v in NAMES.items() if k not in ACTIVE]
            + ["⛔ لا يذهب أبدًا:"] + ["  • " + x for x in NOT_SENT])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else ""
    if mode == "manifest":
        print("\n".join(manifest()))
        return 0
    if mode == "flush":
        if not on():
            log("↩️ قناة المشتركين مطفأة (`ON = False`) — لا إرسال")
            return 0
        if "--wait" in argv:
            wait_due()

        def _save(paths):
            import Super_stock as S                 # استيرادٌ كسول: لا يُحمَّل البوتُ إلّا حين يُختم شيء
            S.git_save(paths)
        flush(saver=_save)
        return 0
    print("flush [--wait] | manifest")
    return 1


if __name__ == "__main__":
    sys.exit(main())
