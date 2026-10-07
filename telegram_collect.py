# -*- coding: utf-8 -*-
"""
📥 مُجمِّع صور التلغرام — أداة مستقلة (لا تمسّ البوت ولا الفرز إطلاقًا).

**الفكرة (طلب المستخدم 2026-07-27):** «أبي أرفعها دفعة واحدة وتوصلك» بلا ضغط ملفات
وبلا موقع جديد. الحلّ: **بوت التلغرام الموجود أصلًا** — ترسل الصور للبوت من جوالك
(تحديد الكل ← إرسال = حركة واحدة)، ثم هذي الأداة تُشغَّل على GitHub Actions فتسحبها
عبر `getUpdates`/`getFile` وتحفظها في `faisal_images/` وتدفعها للمستودع، فأقرأها أنا.

**لماذا هنا لا عندي:** بيئتي تحجب `api.telegram.org`، والرنر لا يحجبه (البوت يرسل
منه يوميًّا) والسرّ `TELEGRAM_BOT_TOKEN` متاح هناك. فالتنزيل مكانه الصحيح الرنر.

**التشغيل:** workflow يدوي `telegram_collect.yml`.
**قراءة/تنزيل فقط · لا يطبع السرّ · فاشل-آمن · لا يمسّ أي منطق فرز.**
"""
import hashlib
import json
import os
import re
import time
import sys

import requests

API = "https://api.telegram.org"
REPORT = "telegram_collect_report.md"   # 🧾 تقرير كل سحبة (يُدفَع ليُقرأ)
OUT_DIR = "faisal_images"
STATE = "telegram_collect_state.json"
# 🧾 بياناتُ كلِّ رسالةٍ مسحوبة (‏2026-10-07 · دفعةُ الـ48 للتحقّق الأماميّ V4.1): إلحاقٌ فقط · سطرٌ لكلّ رسالة.
#    `getUpdates` يُقَرّ ثمّ يُحذَف عند تلغرام ⇒ تاريخُ الرسالة ومصدرُ إعادة التوجيه (القناة · تاريخُ المنشور الأصليّ)
#    والنصُّ المرفق **تضيع نهائيًّا** لو لم تُكتب هنا — وهي الطابعُ الزمنيّ الذي تشترطه الأهليّةُ الأماميّة.
#    🔒 بلا معرّف المحادثة ولا هويّة المرسِل ولا الاسمِ الأوّل لأيّ مستخدم (المستودعُ عامّ).
META = "telegram_collect_meta.jsonl"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")
PENDING_MAX = 500                                # سقف طابور الإعادة (صمّام أمان)
PENDING_TRIES = 6                                # محاولات قبل الاستسلام والإبلاغ


def _int_env(name, default):
    """يقرأ عددًا من البيئة بأمان: فراغ/غير رقمي/سالب ⇒ الافتراضي. نقيّة.

    (🔴 الخلل الذي أصلحته قبل أول تشغيل: الـworkflow يمرّر `max_files` **فارغًا**
    افتراضيًّا، فكان `int("")` يرمي `ValueError` **عند الاستيراد قبل `main()`** ⇒
    تشغيل فاشل بصفر صورة ⇒ «أرجع أرسل الصور». الآن مستحيل.)"""
    try:
        v = int(str(os.environ.get(name) or "").strip())
    except Exception:                                # noqa: BLE001
        return default
    return v if v > 0 else default


MAX_FILES = _int_env("TG_MAX_FILES", 600)


def _mask(s):
    """يخفي التوكن من أي نص قبل الطباعة (لا سرّ في السجل)."""
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    return str(s).replace(tok, "***") if tok else str(s)


TEXT_CAP = 4000                                  # سقفُ النصّ/التعليق المحفوظ لكلّ رسالة
# 🧊 FINAL PROTOCOL §⑥ (`faisal_method_v41/FINAL_PROTOCOL_prereg.md`): صفُّ الإصدار 2 يحمل `forward_type` صريحًا («none» حين لا توجيه —
#    فغيابُه في الصفوف الأقدم = مجهول لا «غيرُ مُعاد توجيهُه») والبصمةَ الإدراكيّة عند الجمع · وصفوفُ فجوة/نبضٍ لا تُخترع فيها رسالة.
META_V = 2
KEEP_NULL = ("dhash256", "phash64")              # تعذّرُ البصمة يُكتب null صريحًا لا يُحذف
RETENTION_HOURS = 24                             # تلغرام يحفظ التحديثَ غيرَ المسحوب ≈24 ساعة
HEARTBEAT_HOURS = 12                             # نبضٌ يُبقي آخرَ صفٍّ أحدثَ من نافذة الحفظ (كرون 4 ساعات ‏+ تأخّر GitHub ≈6)


def _iso(ts):
    """طابعُ يونكس ⇒ ISO بتوقيت UTC (`…Z`) · فارغٌ/غيرُ رقميٍّ/صفر ⇒ None. نقيّة."""
    try:
        v = int(ts)
    except Exception:                                # noqa: BLE001
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(v)) if v > 0 else None


def recipient_ids(raw=None):
    """كلُّ أرقام `TELEGRAM_CHAT_ID` بقواعد مُحلِّل البوت نفسِها (الفاصلة · المنقوطة · الفاصلة والمنقوطة
    العربيّتان «،» «؛» · السطر الجديد · المسافة) ⇒ قائمةُ نصوصٍ بترتيبها (الأوّلُ = المشرف). نقيّة حين يُمرَّر `raw`."""
    raw = os.environ.get("TELEGRAM_CHAT_ID", "") if raw is None else raw
    raw = str(raw or "")
    for sep in (";", "،", "؛", "\n", "\r", "\t", " "):
        raw = raw.replace(sep, ",")
    return [c.strip() for c in raw.split(",") if c.strip()]


def admin_id(raw=None):
    """المشرف = **أوّلُ** رقمٍ في `TELEGRAM_CHAT_ID` (`recipient_ids`) ⇒ نصٌّ أو None.
    نقيّة حين يُمرَّر `raw` · ومطابقتُها لمُحلِّل البوت مقفولةٌ في السويّة (لا تستورده: أداةٌ مستقلّة)."""
    ids = recipient_ids(raw)
    return ids[0] if ids else None


def forward_meta(msg):
    """🧾 مصدرُ إعادة التوجيه **بلا هويّةٍ شخصيّة** ⇒ dict أو None (رسالةٌ غيرُ مُعادٍ توجيهُها). نقيّة.

    يقرأ `forward_origin` (‏Bot API 7.0+: channel · chat · user · hidden_user) ثمّ الحقولَ القديمة
    (`forward_date` …) احتياطًا. **يُكتب:** النوع · تاريخُ المنشور الأصليّ (هو طابعُ قرار فيصل حين
    يُعاد توجيهُ منشوره) · عنوانُ القناة/المجموعة ومعرّفُها العامّ ونوعُها · رقمُ المنشور في القناة ·
    توقيعُ الكاتب · واسمُ المستخدم العامّ (@username). 🔒 **ولا يُكتب أبدًا:** المعرّفُ الرقميّ لأيّ
    مستخدمٍ أو محادثة · الاسمُ الأوّل والأخير · واسمُ صاحب الحساب المخفيّ (اختار الإخفاء ⇒ وسمٌ فقط)."""
    if not isinstance(msg, dict):
        return None
    o = msg.get("forward_origin")
    out = {}
    if isinstance(o, dict) and o.get("type"):
        t = str(o.get("type"))
        out["type"] = t
        out["date"] = _iso(o.get("date"))
        ch = o.get("chat") if t == "channel" else o.get("sender_chat") if t == "chat" else None
        su = o.get("sender_user") if t == "user" else None
        if t == "channel" and o.get("message_id"):
            out["origin_message_id"] = int(o.get("message_id"))
        hidden = t == "hidden_user"
    elif msg.get("forward_date"):                    # قبل Bot API 7.0
        out["type"] = "legacy"
        out["date"] = _iso(msg.get("forward_date"))
        ch, su = msg.get("forward_from_chat"), msg.get("forward_from")
        if msg.get("forward_from_message_id"):
            out["origin_message_id"] = int(msg.get("forward_from_message_id"))
        hidden = bool(msg.get("forward_sender_name"))
        o = {"author_signature": msg.get("forward_signature")}
    else:
        return None
    if isinstance(ch, dict):
        out["chat_title"] = ch.get("title")
        out["chat_username"] = ch.get("username")
        out["chat_type"] = ch.get("type")
    if isinstance(su, dict):
        out["user_username"] = su.get("username")
        out["user_is_bot"] = bool(su.get("is_bot"))
    if o.get("author_signature"):
        out["author_signature"] = str(o.get("author_signature"))
    if hidden:
        out["hidden"] = True
    if msg.get("is_automatic_forward"):
        out["automatic"] = True
    return {k: v for k, v in out.items() if v is not None}


def forward_public(fwd):
    """🧾 مصدرُ التوجيه **لأيّ مُرسِل** ⇒ dict أو None (2026-10-07 · دفعةُ الـ48: وُسمت كلُّها «من غير المشرف» فحُجب توجيهُها
    كلُّه وضاع تاريخُ المنشور الأصليّ — وهو لا يحمل هويّةَ أحد). نقيّة: من مُخرَج `forward_meta` تُبقي النوعَ وتاريخَ المنشور الأصليّ
    ووسمَ الإخفاء/الآليّ · وعنوانَ القناة ومعرّفَها ورقمَ منشورها وتوقيعَها **للقناة العامّة وحدَها** (لها @معرّف) · ولا اسمَ
    مستخدمٍ ولا عنوانَ مجموعةٍ ولا قناةٍ خاصّة."""
    if not isinstance(fwd, dict) or not fwd.get("type"):
        return None
    out = {k: fwd[k] for k in ("type", "date", "hidden", "automatic") if k in fwd}
    if fwd.get("chat_type") == "channel" and fwd.get("chat_username"):
        out.update({k: fwd[k] for k in ("chat_title", "chat_username", "chat_type", "origin_message_id", "author_signature")
                    if k in fwd})
    return out


def file_meta(msg, f):
    """🧾 بياناتُ **الملفّ الذي اختاره `pick_file` نفسُه** لا غيره ⇒ dict. نقيّة.
    المستند: المعرّفُ الثابت والحجمُ والنوعُ والاسمُ الأصليّ (الأبعادُ تُقاس من الملفّ المحفوظ) ·
    الصورة: المعرّفُ الثابت والعرضُ والارتفاعُ والحجم **للمقاس المختار** (يُطابَق بـ`file_id`)."""
    if not isinstance(msg, dict) or not isinstance(f, dict):
        return {}
    if f.get("kind") == "document":
        d = msg.get("document") if isinstance(msg.get("document"), dict) else {}
        got = {"file_unique_id": d.get("file_unique_id"), "file_size": d.get("file_size"),
               "mime": d.get("mime_type"), "orig_name": d.get("file_name")}
    else:
        p = next((p for p in (msg.get("photo") or [])
                  if isinstance(p, dict) and p.get("file_id") == f.get("file_id")), {})
        got = {"file_unique_id": p.get("file_unique_id"), "width": p.get("width"),
               "height": p.get("height"), "file_size": p.get("file_size")}
    return {k: v for k, v in got.items() if v is not None}


def msg_meta(u, msg, status, f=None, admin=None, **extra):
    """🧾 صفُّ بياناتٍ لرسالةٍ واحدة ⇒ dict جاهزٌ لسطر JSONL (نقيّةٌ عدا `collected_utc`).

    `admin` = معرّفُ المشرف · أو قائمةُ المستلمين كلِّهم (`recipient_ids` · الأوّلُ = المشرف) يُقارَن بمعرّف المحادثة **ولا
    يُكتب أيٌّ منهما** — يُكتب `from_admin` (صح · خطأ · None حين لا يُعرف المشرف) و`from_recipient` لغير المشرف (هل
    المُرسِلُ أحدُ مستلمي التقرير؟ — تشخيصٌ بلا هويّة). 🔒 **النصُّ والتعليقُ والروابطُ ومصدرُ التوجيه الكاملُ للمشرف وحده**
    (`redacted` لغيره): البوتُ نفسُه يُراسله مستلمو التقرير الآخرون، ورسالتُهم الخاصّة لا تُدفَع لمستودعٍ عامّ — **وغيرُ المشرف
    يُكتب له مصدرُ التوجيه بلا هويّة** (`forward_public`: النوعُ وتاريخُ المنشور الأصليّ وبياناتُ القناة العامّة وحدَها).
    والصفُّ يُكتب **قبل** أن يُقَرّ تحديثُه عند تلغرام (`_append_meta`)."""
    msg = msg if isinstance(msg, dict) else {}
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    cid = chat.get("id")
    ids = [str(x) for x in admin] if isinstance(admin, (list, tuple)) else ([str(admin)] if admin else [])
    from_admin = None if (not ids or cid is None) else (str(cid) == ids[0])
    fm = forward_meta(msg)
    row = {"meta_v": META_V, "forward_type": (fm or {}).get("type") or "none",
           "update_id": u.get("update_id") if isinstance(u, dict) else None,
           "message_id": msg.get("message_id"), "date": _iso(msg.get("date")),
           "media_group_id": msg.get("media_group_id"), "status": status,
           "from_admin": from_admin, "kind": (f or {}).get("kind"),
           "file": (file_meta(msg, f) or None) if f else None,
           "collected_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "run_id": os.environ.get("GITHUB_RUN_ID") or None}
    if from_admin:
        row["forward"] = fm
        if msg.get("caption"):
            row["caption"] = str(msg.get("caption"))[:TEXT_CAP]
        if msg.get("text"):
            row["text"] = str(msg.get("text"))[:TEXT_CAP]
        links = [e.get("url") for e in (list(msg.get("caption_entities") or [])
                                        + list(msg.get("entities") or []))
                 if isinstance(e, dict) and e.get("type") == "text_link" and e.get("url")]
        if links:
            row["links"] = links[:20]
    else:
        row["redacted"] = True
        row["forward"] = forward_public(fm)
        if from_admin is False:
            row["from_recipient"] = str(cid) in ids
    row.update(extra)
    return {k: v for k, v in row.items() if v is not None or k in KEEP_NULL}


def perceptual(path):
    """🧾 dHash256 · pHash64 للصورة المحفوظة **عند الجمع** بدوالّ V3 نفسِها (`faisal_method_v3/corpus_build.image_fingerprint`
    — مقارنةُ الاستلام بالمدوّنة بالبصمة نفسِها) ⇒ dict · وتعذّرُها ⇒ None مكتوبٌ صريحًا (لا حذف · §⑥)."""
    try:
        v3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faisal_method_v3")
        if v3 not in sys.path:
            sys.path.insert(0, v3)
        import corpus_build as CB                    # noqa: E402 — كسولٌ: numpy/Pillow من requirements
        fp = CB.image_fingerprint(path)
        return {"dhash256": fp["dhash256"], "phash64": fp["phash64"]}
    except Exception:                                # noqa: BLE001
        return {"dhash256": None, "phash64": None}


def _parse_iso(s):
    """«…Z» ⇒ ثوانٍ منذ الحقبة (UTC · `calendar.timegm`) أو None. نقيّة."""
    try:
        import calendar
        return calendar.timegm(time.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:                                # noqa: BLE001
        return None


def retention_gap(last_utc, now_utc, run_id=None):
    """🕳️ صفُّ فجوة حين مضى على آخر صفٍّ مكتوب أكثرُ من نافذة حفظ تلغرام ⇒ dict أو None. نقيّة.
    ما أُرسل للبوت خلالها **ربّما** حُذف عند تلغرام قبل سحبه — يُسجَّل المدى ولا تُخترع رسالة (§⑥)."""
    a, b = _parse_iso(last_utc), _parse_iso(now_utc)
    if a is None or b is None or b - a <= RETENTION_HOURS * 3600:
        return None
    return {"meta_v": META_V, "kind": "gap", "status": "gap", "gap": "RETENTION_WINDOW_EXCEEDED", "from_utc": last_utc,
            "to_utc": now_utc, "hours": round((b - a) / 3600.0, 1), "collected_utc": now_utc, "run_id": run_id}


def update_id_gaps(prev_uid, uids, now_utc, run_id=None):
    """🕳️ قفزاتُ رقم التحديث (`UPDATE_ID_GAP`) ⇒ صفوف. نقيّة. «محتمل» لا «فقدٌ مؤكَّد»: أنواعُ تحديثٍ غيرُ مطلوبة تستهلك أرقامًا ·
    ولا مرجعَ قبل أوّل تشغيل (`prev_uid` None)."""
    out = []
    for uid in uids:
        if prev_uid is not None and uid > prev_uid + 1:
            out.append({"meta_v": META_V, "kind": "gap", "status": "gap", "gap": "UPDATE_ID_GAP", "after_update_id": prev_uid,
                        "before_update_id": uid, "missing": uid - prev_uid - 1, "meaning": "POSSIBLE_LOSS_OR_FILTERED_UPDATE",
                        "collected_utc": now_utc, "run_id": run_id})
        prev_uid = uid if prev_uid is None else max(prev_uid, uid)
    return out


def heartbeat_due(last_utc, now_utc):
    """💓 نبضٌ حين يقدُم آخرُ صفٍّ أكثرَ من `HEARTBEAT_HOURS` (وبلا صفٍّ أصلًا ⇒ لا نبض). نقيّة."""
    a, b = _parse_iso(last_utc), _parse_iso(now_utc)
    return a is not None and b is not None and b - a > HEARTBEAT_HOURS * 3600


def last_row_utc(path=None, tail=1 << 16):
    """آخرُ `collected_utc` في ملفّ البيانات (الذيلُ وحدَه) ⇒ نصّ أو None (لا ملفّ · تعذّر)."""
    try:
        with open(path or META, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            fh.seek(max(0, n - tail))
            lines = fh.read().decode("utf-8", "replace").splitlines()
        for ln in reversed(lines):
            try:
                v = json.loads(ln).get("collected_utc")
            except Exception:                        # noqa: BLE001
                continue
            if v:
                return v
    except Exception:                                # noqa: BLE001
        return None
    return None


def meta_summary(rows):
    """🧾 ملخّصُ صفوف بيانات الرسائل لهذا التشغيل ⇒ أسطرٌ جاهزة (فارغةٌ بلا صفوف). نقيّة."""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if not rows:
        return []

    def _cnt(keys):
        c = {}
        for k in keys:
            c[k] = c.get(k, 0) + 1
        return c

    st = _cnt(str(r.get("status")) for r in rows)
    ad = _cnt(r.get("from_admin") for r in rows)
    rc = sum(1 for r in rows if r.get("from_recipient") is True)
    fw = [r["forward"] for r in rows if isinstance(r.get("forward"), dict)]
    ft = _cnt(str(x.get("type")) for x in fw)
    fd = sorted(x["date"] for x in fw if x.get("date"))
    md = sorted(r["date"] for r in rows if r.get("date"))
    groups = {r.get("media_group_id") for r in rows if r.get("media_group_id")}
    src = _cnt((x.get("chat_title") or (f"@{x['user_username']}" if x.get("user_username")
                                        else "حسابٌ مخفيّ" if x.get("hidden")
                                        else {"user": "مستخدم", "chat": "مجموعة", "channel": "قناةٌ خاصّة"}.get(x.get("type"), "؟")),
                x.get("chat_username")) for x in fw)
    out = [f"🧾 بياناتُ الرسائل: {len(rows)} صفًّا · "
           + " · ".join(f"{k} {v}" for k, v in sorted(st.items())),
           f"   من المشرف {ad.get(True, 0)} · من غيره {ad.get(False, 0)} (نصُّه محجوب"
           + (f" · منهم من مستلمي التقرير {rc} — المشرفُ أوّلُ رقمٍ في TELEGRAM_CHAT_ID" if rc else "") + ") · "
           f"غيرُ معروف {ad.get(None, 0)} · ألبومات {len(groups)}"]
    if md:
        out.append(f"   تاريخُ الإرسال للبوت: {md[0]} … {md[-1]}")
    out.append(f"   مُعاد توجيهُها {len(fw)}"
               + (" (" + " · ".join(f"{k} {v}" for k, v in sorted(ft.items())) + ")" if ft else "")
               + (f" · تاريخُ المنشور الأصليّ {fd[0]} … {fd[-1]}" if fd else ""))
    for (t, un), n in sorted(src.items(), key=lambda kv: (-kv[1], str(kv[0])))[:12]:
        out.append(f"   ↳ {t}" + (f" (@{un})" if un else "") + f" × {n}")
    cap = sum(1 for r in rows if r.get("caption"))
    if cap:
        out.append(f"   بتعليقٍ مرفق {cap}")
    return out


def _append_meta(rows):
    """يُلحق الصفوفَ بـ`META` **إلحاقًا لا إعادةَ كتابة** ثمّ يُفرغ القائمة ⇒ عددُ المكتوب ·
    و`-1` عند التعذّر (يُعلَن) — فيمتنع `main` عن إقرار صفحةٍ لم تُكتب بياناتُها."""
    if not rows:
        return 0
    try:
        with open(META, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as e:                           # noqa: BLE001
        print(f"⛔ تعذّر إلحاق بيانات الرسائل بـ{META}: {_mask(e)} — لا تُقَرّ هذه الصفحة")
        return -1
    n = len(rows)
    rows.clear()
    return n


def safe_name(name, fallback):
    """اسم ملف آمن يحفظ الرقم الأصلي (IMG_0153.jpeg يبقى كما هو). نقيّة."""
    base = os.path.basename(str(name or "")).strip()
    base = re.sub(r"[^A-Za-z0-9._\-؀-ۿ]", "_", base)
    if not base or not base.lower().endswith(IMG_EXT):
        base = f"{fallback}.jpg"
    return base[:120]


def pick_file(msg):
    """يستخرج من رسالة تلغرام أفضل ملف صورة: مستند صورة (يحفظ الجودة والاسم) أو
    أكبر مقاس من `photo` (مضغوط). يرجّع {file_id, name, kind} أو None. **نقيّة**."""
    if not isinstance(msg, dict):
        return None
    mid = msg.get("message_id") or 0
    doc = msg.get("document")
    if isinstance(doc, dict) and doc.get("file_id"):
        mime = str(doc.get("mime_type") or "")
        nm = str(doc.get("file_name") or "")
        if mime.startswith("image/") or nm.lower().endswith(IMG_EXT):
            return {"file_id": doc["file_id"],
                    "name": safe_name(nm, f"TG_{mid}"), "kind": "document"}
        return None
    ph = msg.get("photo")
    if isinstance(ph, list) and ph:
        big = max((p for p in ph if isinstance(p, dict) and p.get("file_id")),
                  key=lambda p: int(p.get("file_size") or 0), default=None)
        if big:
            return {"file_id": big["file_id"], "name": f"TG_{mid}.jpg",
                    "kind": "photo"}
    return None


def safe_offset(items, current=0):
    """🛡️ **العَقد الحاسم ضد «أرجع أرسل الصور»:** تلغرام يحذف التحديثات التي نُقِرّها
    بـ`offset`. فلا نُقِرّ إلا **البادئة الناجحة** — ونتوقّف عند **أول إخفاق** فيبقى
    محفوظًا عند تلغرام ويسحبه التشغيل التالي وحده. `items` = [(update_id, نجح؟)]
    بالترتيب. نقيّة · بلا شبكة.

    (الخلل الذي أصلحته: الكود السابق كان يرفع `offset` **قبل** التنزيل، فأي فشل شبكي
    يعني **صورة تُحذف من تلغرام ولا تُحفَظ عندنا** ⇒ إعادة إرسال الدفعة كلها.)"""
    off = int(current or 0)
    for uid, ok in items:
        if not ok:
            break
        off = max(off, int(uid) + 1)
    return off


def fetch_blob(tok, file_id, get=None, sleep=None):
    """ينزّل ملفًا بثلاث محاولات ويُصنّف الإخفاق ⇒ `(content, perm, why)`.

    **التصنيف هو جوهر ضمان «لا تعليق»:**
    - `perm=True` ⇒ إخفاق **دائم** لا يشفيه التكرار (تلغرام رفض · الملف انتهى ·
      حجم فوق 20 ميغا = حدّ بوتات تلغرام) ⇒ **يُقَرّ عند تلغرام ويُبلَّغ بالاسم**
      ليُعاد إرسال **تلك الصورة وحدها**، فلا يُحتجَز باقي الطابور.
    - `perm=False` ⇒ عابر (شبكة/5xx) ⇒ **لا يُقَرّ** ويُستأنَف بالتشغيل التالي.

    `get`/`sleep` قابلان للحقن (اختبار بلا شبكة). فاشلة-آمنة: لا ترمي أبدًا.

    (🔴 الخلل الثاني الذي أصلحته: الكود السابق كان يعدّ **كل** إخفاق عابرًا، فملف
    واحد منتهٍ = `offset` لا يتقدّم أبدًا ⇒ **كل تشغيل يتعطّل عند نفس التحديث**
    ⇒ الـ250 صورة الباقية لا تصل إطلاقًا.)"""
    get = get or (lambda url, **kw: requests.get(url, **kw))
    sleep = sleep if sleep is not None else time.sleep
    why = ""
    for attempt in range(3):
        try:
            fr = get(f"{API}/bot{tok}/getFile", timeout=60,
                     params={"file_id": file_id}).json()
            if not fr.get("ok"):
                d = str(fr.get("description") or "getFile رفض الطلب")
                # ⚠️ **إصلاح 2026-07-27:** كان **كل** `ok:false` يُصنَّف دائمًا —
                # لكن تلغرام يردّ بنفس الشكل على أخطاء **عابرة** تمامًا: 429
                # «Too Many Requests: retry after N» و5xx «Bad Gateway». ودفعةُ
                # 300+ صورة هي **بالضبط** ما يستدعي 429 ⇒ كانت الصور تُسقَط
                # نهائيًّا ويُقَرّ تحديثها = فقدٌ لا يُسترجَع إلا بإعادة إرسال.
                _code = int(fr.get("error_code") or 0)
                if _code == 429 or 500 <= _code < 600:
                    why = _mask(d)
                    if attempt < 2:
                        try:                      # احترم retry_after لو أرسله
                            _ra = float((fr.get("parameters") or {})
                                        .get("retry_after") or 0)
                        except Exception:         # noqa: BLE001
                            _ra = 0
                        try:
                            sleep(max(_ra, 1.5 * (attempt + 1)))
                        except Exception:         # noqa: BLE001
                            pass
                        continue
                    return None, False, why       # عابر ⇒ للطابور الدائم
                return None, True, _mask(d)       # ⛔ رفض تلغرام لا يشفيه التكرار
            fp = (fr.get("result") or {}).get("file_path")
            if not fp:
                return None, True, "بلا file_path (ملف منتهٍ)"
            resp = get(f"{API}/file/bot{tok}/{fp}", timeout=180)
            code = int(getattr(resp, "status_code", 0) or 0)
            if code == 200 and resp.content:
                return resp.content, False, ""
            why = f"HTTP {code}"
            if 400 <= code < 500 and attempt == 2:
                return None, True, why            # 4xx ثابت بعد ثلاث محاولات
        except Exception as e:                       # noqa: BLE001
            why = _mask(e)
        if attempt < 2:
            try:
                sleep(1.5 * (attempt + 1))
            except Exception:                        # noqa: BLE001
                pass
    return None, False, why or "تعذّر التنزيل"


def _store(body, name, shas, exts, matched=None, info=None):
    """يحفظ المحتوى باسم غير مُصادِم ⇒ `"saved"` أو `"dup"` (مكرّرة بالمحتوى).
    يحدّث `shas`/`exts` في المكان.

    🔍 **`matched` (قائمة اختيارية)**: عند التكرار يُلحَق بها `(الاسم، الملفّ المطابق)`
    — فبدل ادّعاء «93 مكرّرة» يصير بالإمكان **إثبات** أيّ ملفٍّ طابق أيًّا (سؤال المالك
    2026-07-28: «مب ملفات — صور خام»). يعمل مع `shas` قاموسًا (بصمة→اسم) أو مجموعةً.
    🧾 **`info` (قاموسٌ اختياريّ)**: يُملأ بـ`sha256` و`saved_name` (المحفوظ فعلًا بعد تفادي
    التصادم) أو `matched` — لصفّ بيانات الرسالة. وبدونه السلوكُ والإرجاعُ بت-بت."""
    digest = hashlib.sha256(body).hexdigest()
    if isinstance(info, dict):
        info["sha256"] = digest
    if digest in shas:
        _prev = shas.get(digest) if isinstance(shas, dict) else None
        if matched is not None:
            matched.append((name, _prev or "؟"))
        if isinstance(info, dict):
            info["matched"] = _prev or "؟"
        return "dup"
    path = os.path.join(OUT_DIR, name)
    n = 1
    while os.path.exists(path):                  # لا تدهس اسمًا موجودًا
        stem, ext = os.path.splitext(name)
        path = os.path.join(OUT_DIR, f"{stem}_{n}{ext}")
        n += 1
    with open(path, "wb") as fh:
        fh.write(body)
    if isinstance(shas, dict):
        shas[digest] = os.path.basename(path)
    else:
        shas.add(digest)
    e = os.path.splitext(path)[1].lower() or "?"
    exts[e] = exts.get(e, 0) + 1
    if isinstance(info, dict):
        info["saved_name"] = os.path.basename(path)
    return "saved"


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _existing_shas(d):
    """بصمة المحتوى ⇒ اسم الملف (قاموس، لا مجموعة) — ليُذكَر **الملفّ المطابق** عند
    الإبلاغ عن مكرّرة بدل رقم مجرَّد لا يُتحقَّق منه."""
    out = {}
    if not os.path.isdir(d):
        return out
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p) and f.lower().endswith(IMG_EXT):
            try:
                out[_sha(p)] = f
            except Exception:
                continue
    return out


def _saved_msg_ids(out_dir):
    """أرقام رسائل تلغرام المحفوظة فعلًا (من أسماء `TG_<id>.jpg`). فاشلة-آمنة → []."""
    try:
        return sorted(int(m.group(1)) for f in os.listdir(out_dir)
                      if (m := re.fullmatch(r"TG_(\d+)\.[A-Za-z0-9]+", f)))
    except Exception:                                # noqa: BLE001
        return []


def gap_report(ids, max_show: int = 12):
    """🔍 **تقرير الفجوات** — `message_id` في تلغرام متسلسل داخل المحادثة، فكل رقم
    غائب داخل المدى المحفوظ يعني **شيئًا لم يصلنا صورةً**: إمّا رسالة نصّية أو ردّ
    البوت (يستهلكان رقمًا أيضًا) وإمّا **صورة ضاعت فعلًا**.

    يجيب سؤال «هل وصل كل شي؟» **بدليل** بدل التخمين بفارق العدّ (المستخدم أرسل ~333
    ووصل 308 — والفارق وحده لا يميّز «ضاعت» من «رقم استهلكه نصّ»).

    دالّة نقيّة (تأخذ قائمة أرقام) · تُرجع أسطرًا جاهزة للطباعة أو [] لو لا فجوة."""
    ids = sorted(set(int(i) for i in (ids or [])))
    if len(ids) < 2:
        return []
    gaps = [(a + 1, b - 1) for a, b in zip(ids, ids[1:]) if b - a > 1]
    miss = sum(e - s + 1 for s, e in gaps)
    if not gaps:
        return [f"🔍 الترقيم متّصل {ids[0]}…{ids[-1]} بلا فجوة — لم يُفقَد شيء."]
        # (لا فجوة = يقين؛ ووجودها لا يعني الفقد حتمًا — انظر أدناه.)
    out = [f"🔍 الترقيم {ids[0]}…{ids[-1]} · **{miss} رقمًا غائبًا** في "
           f"{len(gaps)} فجوة (قد تكون رسائل نصّية أو ردود البوت — لا صورًا):"]
    out.append("   " + " · ".join(f"{s}" if s == e else f"{s}–{e}"
                                  for s, e in gaps[:max_show])
               + (f" … (+{len(gaps) - max_show})" if len(gaps) > max_show else ""))
    out.append("   ↳ للتأكّد من رقمٍ بعينه: مرّره لتلغرام بـ`forwardMessage` — "
               "إن رجع صورةً فهي ضائعة فعلًا، وإن رجع نصًّا فلا شيء فُقِد.")
    return out


def main():
    tok = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not tok:
        print("⚠️ لا TELEGRAM_BOT_TOKEN — لا عمل (فاشل-آمن).")
        return 0
    os.makedirs(OUT_DIR, exist_ok=True)
    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8")) or {}
        except Exception:
            state = {}
    offset = int(state.get("offset") or 0)
    seen_uid = set(state.get("seen_file_ids") or [])
    # 🛡️ طابور دائم بـ`file_id`: صور أخفق تنزيلها عابرًا. **`file_id` يبقى صالحًا
    # عند تلغرام بلا التحديث**، فلا نحتاج أبدًا للمقايضة بين «نعلّق الطابور» و«نفقد
    # الصورة» — نُقِرّ التحديث ونُعيد المحاولة من الطابور في التشغيلات التالية.
    pending = dict(state.get("pending") or {})
    shas = _existing_shas(OUT_DIR)
    saved, skipped, photos, docs, pages = 0, 0, 0, 0, 0
    failed, perm_failed, exts, deferred, got_ids = [], [], {}, [], []
    # 🧾 **أرقام الرسائل المحسوبة** (محفوظة أو مكرّرة أو مرفوضة نهائيًّا) — بدونها
    # كان تقرير الفجوات يعدّ **المكرّرة** فجوةً وهميّة فلا يُميَّز «مكرّر» من «ضائع»
    # (سؤال المالك 2026-07-28: «هل وصلت الـ100 كلها؟» لم يكن قابلًا للإثبات).
    acct = set(int(x) for x in (state.get("seen_msg_ids") or []))
    dropped, no_media = [], []   # 🔍 وسائط غير مقبولة · ورسائل بلا وسائط
    matched = []                 # 🔍 (اسم الواردة، الملفّ الذي طابقته)
    seen_skip = []               # 🔍 وصلت لكن `file_id` نُزِّل سابقًا
    # 🧾 بياناتُ الرسائل: `meta_rows` صفوفُ الصفحة الجارية (تُلحَق بـ`META` قبل طلب الصفحة
    #    التالية — فطلبُها يُقِرّ هذه عند تلغرام فيحذفها) · `meta_all` نسخةٌ للملخّص.
    adm = recipient_ids() or None              # الأوّلُ = المشرف · والباقون مستلمون (`from_recipient` بلا هويّة)
    meta_rows, meta_all, meta_n, meta_fail = [], [], 0, False

    def _mrow(row):
        meta_rows.append(row)
        meta_all.append(row)

    # 🕳️ §⑥: نافذةُ الحفظ (24 ساعة) منذ آخر صفٍّ مكتوب ⇒ صفُّ فجوةٍ بمداه — قبل أيّ سحب · وتعذّرُ كتابته لا يمنع السحب (يُعلَن)
    _now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _rid = os.environ.get("GITHUB_RUN_ID") or None
    _gap0 = retention_gap(last_row_utc(), _now, _rid)
    gaps = [_gap0] if _gap0 else []
    if _gap0 and _append_meta([dict(_gap0)]) < 0:
        print("⚠️ تعذّرت كتابةُ صفّ فجوة الحفظ — يُعلَن هنا فقط")
    prev_uid = (offset - 1) if offset > 0 else None

    if pending:                                      # الطابور أولًا قبل أي جديد
        print(f"🔁 إعادة محاولة {len(pending)} صورة مؤجَّلة من تشغيل سابق…")
        for fid, meta in list(pending.items()):
            nm = str((meta or {}).get("name") or f"TG_{fid[:8]}.jpg")
            _pm = {"message_id": (meta or {}).get("msg")}
            body, perm, why = fetch_blob(tok, fid)
            if body is not None:
                _inf = {}
                if _store(body, nm, shas, exts, matched, _inf) == "saved":
                    saved += 1
                    _inf.update(perceptual(os.path.join(OUT_DIR, _inf["saved_name"])))
                    _mrow(msg_meta(None, _pm, "saved_from_pending", None, adm, forward_type="UNKNOWN", **_inf))
                else:
                    skipped += 1
                    _mrow(msg_meta(None, _pm, "dup_from_pending", None, adm, forward_type="UNKNOWN", **_inf))
                seen_uid.add(fid)
                if (meta or {}).get("msg"):
                    acct.add(int(meta["msg"]))
                pending.pop(fid, None)
                continue
            tries = int((meta or {}).get("tries") or 1) + 1
            if perm or tries >= PENDING_TRIES:
                perm_failed.append(f"{nm} — {why} (بعد {tries} محاولات)")
                pending.pop(fid, None)
                _mrow(msg_meta(None, _pm, "perm_failed_from_pending", None, adm, forward_type="UNKNOWN", why=why))
            else:
                pending[fid] = {**(meta or {}), "name": nm, "tries": tries}
                deferred.append(nm)
                _mrow(msg_meta(None, _pm, "deferred_again", None, adm, forward_type="UNKNOWN", why=why))
        _w = _append_meta(meta_rows)
        meta_fail = _w < 0
        meta_n += max(_w, 0)

    while saved + skipped < MAX_FILES and pages < 40 and not meta_fail:
        pages += 1
        try:
            r = requests.get(f"{API}/bot{tok}/getUpdates", timeout=60,
                             params={"offset": offset, "limit": 100,
                                     "timeout": 0,
                                     "allowed_updates": '["message","channel_post"]'})
            data = r.json()
        except Exception as e:                       # noqa: BLE001
            print(f"⚠️ getUpdates: {_mask(e)}")
            break
        if not data.get("ok"):
            desc = _mask(data.get("description"))
            print(f"⚠️ تلغرام رفض الطلب: {desc}")
            if "webhook" in str(desc).lower():
                print("   ↳ السبب webhook مضبوط على البوت — يلزم حذفه مرة واحدة "
                      "(deleteWebhook) ليعمل getUpdates.")
            break
        ups = data.get("result") or []
        if not ups:
            break
        marks = []
        _ug = update_id_gaps(prev_uid, [int(x.get("update_id") or 0) for x in ups], _now, _rid)
        for _g in _ug:
            _mrow(_g)
        gaps += _ug
        prev_uid = max([prev_uid or 0] + [int(x.get("update_id") or 0) for x in ups])
        for u in ups:
            uid = int(u.get("update_id") or 0)
            msg = u.get("message") or u.get("channel_post") or {}
            f = pick_file(msg)
            if not f:
                # ⚠️ **تشخيص 2026-07-28:** «لا صورة ⇒ لا شيء يُفقَد» صحيحة **فقط** لو
                # كانت الرسالة نصًّا. أما وسائط بشكل لا نقبله (فيديو/ملصق/مستند بـmime
                # غريب) فتُقَرّ وتضيع **بلا أثر**. نُميّز الحالتين ونُبلّغ بالأرقام —
                # سؤال المالك «هل وصلت الـ100؟» يحتاج هذا التمييز بالذات.
                _media = next((k for k in ("document", "video", "animation",
                                           "sticker", "audio", "voice",
                                           "video_note")
                               if msg.get(k)), None)
                if _media:
                    dropped.append(f"{msg.get('message_id')}:{_media}")
                else:
                    no_media.append(int(msg.get("message_id") or 0))
                _mrow(msg_meta(u, msg, f"dropped:{_media}" if _media else "no_media",
                               None, adm))
                marks.append((uid, True))            # نصّ ⇒ لا شيء يُفقَد
                continue
            if f["file_id"] in seen_uid:
                # ⚠️ **إصلاح 2026-07-28:** هذا المسار كان **غير محسوب في أي عدّاد**
                # ولا يظهر بالتقرير إطلاقًا. فحين يعيد المالك إرسال صورٍ سبق تنزيلها،
                # يعطي تلغرام **نفس `file_id`** فتُتخطّى كلها هنا صامتةً ⇒ التقرير
                # يقول «0 عولج · 0 محفوظ · 0 مكرّر» بينما الحقيقة «كلها وصلت وكلها
                # عندنا سلفًا». وهذا بعينه ما أربكنا: 82 تحديثًا تقدّم بها الـoffset
                # بلا أي أثر في التقرير.
                seen_skip.append(int(msg.get("message_id") or 0))
                acct.add(int(msg.get("message_id") or 0))
                _mrow(msg_meta(u, msg, "seen", f, adm))
                marks.append((uid, True))            # نُزِّلت سابقًا
                continue
            body, perm, why = fetch_blob(tok, f["file_id"])
            if body is None:
                if perm:                             # تلغرام رفضه ⇒ يلزم إعادة إرساله
                    perm_failed.append(f"{f['name']} — {why} "
                                       f"(رسالة {msg.get('message_id')})")
                    seen_uid.add(f["file_id"])
                    acct.add(int(msg.get("message_id") or 0))
                    _mrow(msg_meta(u, msg, "perm_failed", f, adm, why=why))
                    marks.append((uid, True))
                elif len(pending) < PENDING_MAX:      # عابر ⇒ للطابور الدائم
                    pending[f["file_id"]] = {"name": f["name"],
                                             "msg": msg.get("message_id"),
                                             "tries": 1}
                    deferred.append(f["name"])
                    _mrow(msg_meta(u, msg, "deferred", f, adm, why=why))
                    marks.append((uid, True))         # آمن: `file_id` محفوظ عندنا
                else:                                 # صمّام: الطابور ممتلئ ⇒ لا نُقِرّ
                    failed.append(f"{f['name']} ({why})")
                    _mrow(msg_meta(u, msg, "failed", f, adm, why=why))
                    marks.append((uid, False))
                continue
            _inf = {}
            if _store(body, f["name"], shas, exts, matched, _inf) == "dup":
                skipped += 1                         # مكرّرة بالمحتوى ⇒ تُتخطّى
                seen_uid.add(f["file_id"])
                acct.add(int(msg.get("message_id") or 0))
                if _inf.get("matched") and _inf["matched"] != "؟":
                    _inf.update(perceptual(os.path.join(OUT_DIR, _inf["matched"])))
                _mrow(msg_meta(u, msg, "dup", f, adm, **_inf))
                marks.append((uid, True))
                continue
            _inf.update(perceptual(os.path.join(OUT_DIR, _inf["saved_name"])))
            _mrow(msg_meta(u, msg, "saved", f, adm, **_inf))
            seen_uid.add(f["file_id"])
            saved += 1
            got_ids.append(int(msg.get("message_id") or 0))
            acct.add(int(msg.get("message_id") or 0))
            docs += 1 if f["kind"] == "document" else 0
            photos += 1 if f["kind"] == "photo" else 0
            marks.append((uid, True))
        # 🔒 بياناتُ هذه الصفحة تُكتب **قبل** أن يُقَرّ أيُّ تحديثٍ منها: طلبُ الصفحة التالية
        #    بـ`offset` أعلى يحذفها عند تلغرام ⇒ إن تعذّرت الكتابةُ فلا تقدّمَ للإزاحة ولا طلبَ تالٍ.
        _w = _append_meta(meta_rows)
        if _w < 0:
            meta_fail = True
            break
        meta_n += _w
        new_off = safe_offset(marks, offset)
        if new_off == offset and failed:
            break            # أول تحديث نفسه فاشل ⇒ لا تقدّم، خلّه للتشغيل التالي
        offset = new_off
        if failed:
            break            # لا نتجاوز الإخفاق: التشغيل التالي يستأنف منه

    # 💓 §⑥: نبضٌ إن لم يُكتب صفٌّ منذ `HEARTBEAT_HOURS` — فيدلّ صمتٌ أطولُ من 24 ساعة بين الصفوف على تعطّل الجامع لا على هدوء البوت
    if not meta_fail and heartbeat_due(last_row_utc(), _now):
        _append_meta([{"meta_v": META_V, "kind": "heartbeat", "status": "heartbeat", "collected_utc": _now, "run_id": _rid}])
    state["offset"] = offset
    state["seen_file_ids"] = sorted(seen_uid)[-4000:]
    state["seen_msg_ids"] = sorted(x for x in acct if x)[-6000:]
    state["pending"] = pending
    state.pop("stalled", None)                       # حُلَّ بالطابور الدائم
    json.dump(state, open(STATE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    total = len([f for f in os.listdir(OUT_DIR)
                 if f.lower().endswith(IMG_EXT)]) if os.path.isdir(OUT_DIR) else 0
    print(f"📥 حُفِظت {saved} صورة جديدة · مكرّرة متخطّاة {skipped} "
          f"· (مستندات {docs} · صور مضغوطة {photos})")
    print(f"📁 مجموع الصور في {OUT_DIR}/ الآن: {total}")
    _ms = meta_summary(meta_all)
    for _ln in _ms:
        print(_ln)
    if meta_fail:
        print("⛔ **تعذّرت كتابةُ بيانات الرسائل** — لم تُقَرّ الصفحةُ المتعذّرة (يُعاد سحبُها "
              "بالتشغيل التالي ببياناتها). أعِد تشغيل الـworkflow.")
    # ⚠️ **إصلاح 2026-07-27:** بلوغ السقف كان يقطع السحب **صامتًا**، وبما أن المكرّرة
    # تُحسب ضمنه (`saved + skipped`) والصور الجديدة تأتي غالبًا **آخر** الدفعة، كان
    # القطع يقع عليها بالضبط — ثم يُطبع «لا جديد» فيُقرأ «وصل كل شي». الآن يُصرَّح.
    if saved + skipped >= MAX_FILES:
        print(f"⚠️ **بلغنا سقف هذا التشغيل ({MAX_FILES})** — قد تكون بقيت صور لم "
              "تُسحَب بعد. أعِد تشغيل الـworkflow (يستأنف من حيث وقف)، أو ارفع "
              "`max_files`. ⚠️ المكرّرة تُحسب ضمن السقف.")
    # 🔍 تقرير الفجوات على **كل** ما حُوسب (محفوظ ∪ مكرّر ∪ مرفوض) لا المحفوظ وحده —
    # وإلا عُدَّت المكرّرة فجوةً وهميّة (بعد إعادة إرسالٍ تُخطّى 47 صورة فتظهر «ناقصة»).
    if seen_skip:
        print(f"♻️ **وصلت {len(seen_skip)} صورة سبق تنزيلها بنفس `file_id`** "
              "— أي أنها **هي نفسها** الموجودة عندنا (تلغرام يعيد نفس "
              "المعرّف للملف نفسه). لا جديد ولا فقد.")
    if matched:
        print(f"🔁 **المكرّرة ({len(matched)}) وما طابقته** — بصمة SHA-256 على "
              "المحتوى، فالتطابق يعني **نفس الملف حرفيًّا**:")
        for _a, _b in matched[:25]:
            print(f"     {_a} = {_b}")
        if len(matched) > 25:
            print(f"     … (+{len(matched) - 25})")
    if dropped:
        print(f"⛔ **وسائط لم نقبلها ({len(dropped)}) — قد تكون صورًا "
              f"بشكل غير مدعوم:** " + " · ".join(dropped[:20]))
        print("   ↳ أعِد إرسالها **كصورة عادية أو ملف JPG/PNG**.")
    if no_media:
        print(f"ℹ️ رسائل بلا وسائط (نصّ/ردود) — لا شيء فُقِد: {len(no_media)}"
              + (f" · أرقامها: {no_media[:20]}" if len(no_media) <= 20 else ""))
    _gaps = gap_report(set(_saved_msg_ids(OUT_DIR)) | acct | set(no_media))
    for _ln in _gaps:
        print(_ln)
    # 🧾 **تقرير مكتوب** (إصلاح 2026-07-28): كل ما سبق يُطبَع في سجلّ Actions — وسجلّ
    # الوظيفة **لا يمكن قراءته آليًّا بالكامل** (الواجهة تقصّه من الذيل)، فبنيتُ تشخيصًا
    # لا أستطيع قراءته. الآن يُكتَب ملفًّا **يُدفَع مع الصور** فيُقرأ من المستودع مباشرةً.
    try:
        _R = [f"# 🧾 تقرير سحب صور التلغرام", "",
              f"- حُفِظت جديدة: **{saved}** · مكرّرة متخطّاة: **{skipped}**",
              f"- مجموع الصور الآن: **{total}**",
              f"- وصلت بمعرّف سبق تنزيله: **{len(seen_skip)}**",
              f"- عالق بالطابور: **{len(pending)}**",
              f"- بياناتُ الرسائل: **{meta_n}** صفًّا أُلحقت بـ`{META}`"
              + (" · ⛔ **تعذّرت كتابةُ صفحةٍ — لم تُقَرّ**" if meta_fail else ""),
              f"- 🕳️ فجواتٌ مسجَّلة: **{len(gaps)}**" + (" (" + " · ".join(sorted({str(g.get('gap')) for g in gaps})) + ")" if gaps else ""), ""]
        if _ms:
            _R += ["## 🧾 بياناتُ الرسائل (هذا التشغيل · بلا هويّةٍ شخصيّة)", "",
                   "```"] + _ms + ["```", ""]
        if seen_skip:
            _R += ["## ♻️ وصلت لكن `file_id` نُزِّل سابقًا (هي نفسها عندنا)", "",
                   f"العدد: **{len(seen_skip)}** · أرقام الرسائل: `{seen_skip[:60]}`",
                   "", "تلغرام يعيد **نفس المعرّف** للملف نفسه ⇒ إعادة إرسال "
                   "الصورة ذاتها تُتخطّى هنا. **لا جديد ولا فقد.**", ""]
        if matched:
            _R += ["## 🔁 المكرّرة وما طابقته (SHA-256 على المحتوى = نفس الملف حرفيًّا)",
                   "", "| الواردة | طابقت |", "|---|---|"]
            _R += [f"| {_a} | {_b} |" for _a, _b in matched]
            _R.append("")
        if dropped:
            _R += ["## ⛔ وسائط لم نقبلها (قد تكون صورًا بشكل غير مدعوم)", "",
                   "`" + "` · `".join(dropped) + "`", "",
                   "أعِد إرسالها **كصورة عادية أو ملف JPG/PNG**.", ""]
        if no_media:
            _R += ["## ℹ️ رسائل بلا وسائط (نصّ/ردود البوت) — لا شيء فُقِد", "",
                   f"العدد: **{len(no_media)}** · الأرقام: `{no_media}`", ""]
        if perm_failed:
            _R += ["## 🛑 رفضها تلغرام نهائيًّا", ""] + [f"- {_x}" for _x in perm_failed] + [""]
        if _gaps:
            _R += ["## 🔍 فجوات الترقيم", ""] + [f"- {_g}" for _g in _gaps] + [""]
        with open(REPORT, "w", encoding="utf-8") as _fh:
            _fh.write("\n".join(_R) + "\n")
        print(f"🧾 كُتب التقرير: {REPORT}")
    except Exception as _e:                                  # noqa: BLE001
        print(f"⚠️ تعذّر كتابة التقرير: {_mask(_e)}")
    if got_ids:
        # 🛡️ السجلّ نفسه وسيلة إنقاذ: `forwardMessage` بأرقام الرسائل يُرجع
        # `file_id` جديدًا لكل صورة، فلو ضاع الدفع تُستعاد بلا إعادة إرسال.
        print(f"🆔 أرقام الرسائل المحفوظة ({len(got_ids)}) من "
              f"{min(got_ids)} إلى {max(got_ids)}:")
        print("   " + ",".join(str(i) for i in got_ids))
    if exts:
        print("🧩 الامتدادات: " + " · ".join(f"{k} × {v}" for k, v in
                                            sorted(exts.items())))
        if any(k in (".heic", ".heif") for k in exts):
            print("⚠️ فيها HEIC — امتداد لا يُقرأ مباشرة، يلزم تحويله لـJPG.")
    if deferred:
        print(f"🔁 مؤجَّلة للتشغيل التالي {len(deferred)} (محفوظة بـfile_id، "
              f"**لا تُفقَد ولا تُعاد إرسالها**): " + " · ".join(deferred[:8]))
    if perm_failed:
        print(f"⛔ رفض تلغرام {len(perm_failed)} نهائيًّا: "
              + " · ".join(perm_failed[:10]))
        print("   ↳ **هذي وحدها** أعِد إرسالها ثم شغّل الـworkflow مرة أخرى.")
    if photos and not docs:
        print("ℹ️ كلها وصلت **صورًا مضغوطة**: تُقرأ عادةً، لكن الإرسال «كملف/Document» "
              "يحفظ حدّة النص لو صعبت قراءة صورة.")
    if failed:
        print(f"⛔ تعذّر تنزيل {len(failed)}: " + " · ".join(failed[:8]))
        print("   ↳ **لم تُقَرّ عند تلغرام** ⇒ أعِد تشغيل هذا الـworkflow وحده "
              "يستأنف منها — **لا تُعِد إرسال أي صورة**.")
    if saved == 0 and not failed and not deferred:
        print("ℹ️ لا جديد. تأكّد أنك أرسلت الصور للبوت **بعد** آخر تشغيل، وأن "
              "التحديثات لم تُستهلَك (تلغرام يحفظها ~24 ساعة).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
