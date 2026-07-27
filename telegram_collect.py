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
OUT_DIR = "faisal_images"
STATE = "telegram_collect_state.json"
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


def _store(body, name, shas, exts):
    """يحفظ المحتوى باسم غير مُصادِم ⇒ `"saved"` أو `"dup"` (مكرّرة بالمحتوى).
    يحدّث `shas`/`exts` في المكان."""
    digest = hashlib.sha256(body).hexdigest()
    if digest in shas:
        return "dup"
    path = os.path.join(OUT_DIR, name)
    n = 1
    while os.path.exists(path):                  # لا تدهس اسمًا موجودًا
        stem, ext = os.path.splitext(name)
        path = os.path.join(OUT_DIR, f"{stem}_{n}{ext}")
        n += 1
    with open(path, "wb") as fh:
        fh.write(body)
    shas.add(digest)
    e = os.path.splitext(path)[1].lower() or "?"
    exts[e] = exts.get(e, 0) + 1
    return "saved"


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _existing_shas(d):
    out = set()
    if not os.path.isdir(d):
        return out
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p) and f.lower().endswith(IMG_EXT):
            try:
                out.add(_sha(p))
            except Exception:
                continue
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

    if pending:                                      # الطابور أولًا قبل أي جديد
        print(f"🔁 إعادة محاولة {len(pending)} صورة مؤجَّلة من تشغيل سابق…")
        for fid, meta in list(pending.items()):
            nm = str((meta or {}).get("name") or f"TG_{fid[:8]}.jpg")
            body, perm, why = fetch_blob(tok, fid)
            if body is not None:
                if _store(body, nm, shas, exts) == "saved":
                    saved += 1
                else:
                    skipped += 1
                seen_uid.add(fid)
                pending.pop(fid, None)
                continue
            tries = int((meta or {}).get("tries") or 1) + 1
            if perm or tries >= PENDING_TRIES:
                perm_failed.append(f"{nm} — {why} (بعد {tries} محاولات)")
                pending.pop(fid, None)
            else:
                pending[fid] = {**(meta or {}), "name": nm, "tries": tries}
                deferred.append(nm)

    while saved + skipped < MAX_FILES and pages < 40:
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
        for u in ups:
            uid = int(u.get("update_id") or 0)
            msg = u.get("message") or u.get("channel_post") or {}
            f = pick_file(msg)
            if not f:
                marks.append((uid, True))            # لا صورة ⇒ لا شيء يُفقَد
                continue
            if f["file_id"] in seen_uid:
                marks.append((uid, True))            # نُزِّلت سابقًا
                continue
            body, perm, why = fetch_blob(tok, f["file_id"])
            if body is None:
                if perm:                             # تلغرام رفضه ⇒ يلزم إعادة إرساله
                    perm_failed.append(f"{f['name']} — {why} "
                                       f"(رسالة {msg.get('message_id')})")
                    seen_uid.add(f["file_id"])
                    marks.append((uid, True))
                elif len(pending) < PENDING_MAX:      # عابر ⇒ للطابور الدائم
                    pending[f["file_id"]] = {"name": f["name"],
                                             "msg": msg.get("message_id"),
                                             "tries": 1}
                    deferred.append(f["name"])
                    marks.append((uid, True))         # آمن: `file_id` محفوظ عندنا
                else:                                 # صمّام: الطابور ممتلئ ⇒ لا نُقِرّ
                    failed.append(f"{f['name']} ({why})")
                    marks.append((uid, False))
                continue
            if _store(body, f["name"], shas, exts) == "dup":
                skipped += 1                         # مكرّرة بالمحتوى ⇒ تُتخطّى
                seen_uid.add(f["file_id"])
                marks.append((uid, True))
                continue
            seen_uid.add(f["file_id"])
            saved += 1
            got_ids.append(int(msg.get("message_id") or 0))
            docs += 1 if f["kind"] == "document" else 0
            photos += 1 if f["kind"] == "photo" else 0
            marks.append((uid, True))
        new_off = safe_offset(marks, offset)
        if new_off == offset and failed:
            break            # أول تحديث نفسه فاشل ⇒ لا تقدّم، خلّه للتشغيل التالي
        offset = new_off
        if failed:
            break            # لا نتجاوز الإخفاق: التشغيل التالي يستأنف منه

    state["offset"] = offset
    state["seen_file_ids"] = sorted(seen_uid)[-4000:]
    state["pending"] = pending
    state.pop("stalled", None)                       # حُلَّ بالطابور الدائم
    json.dump(state, open(STATE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    total = len([f for f in os.listdir(OUT_DIR)
                 if f.lower().endswith(IMG_EXT)]) if os.path.isdir(OUT_DIR) else 0
    print(f"📥 حُفِظت {saved} صورة جديدة · مكرّرة متخطّاة {skipped} "
          f"· (مستندات {docs} · صور مضغوطة {photos})")
    print(f"📁 مجموع الصور في {OUT_DIR}/ الآن: {total}")
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
