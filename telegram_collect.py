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
import sys

import requests

API = "https://api.telegram.org"
OUT_DIR = "faisal_images"
STATE = "telegram_collect_state.json"
MAX_FILES = int(os.environ.get("TG_MAX_FILES", "600"))
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")


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
    shas = _existing_shas(OUT_DIR)
    saved, skipped, photos, docs, pages = 0, 0, 0, 0, 0

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
        for u in ups:
            offset = max(offset, int(u.get("update_id") or 0) + 1)
            msg = u.get("message") or u.get("channel_post") or {}
            f = pick_file(msg)
            if not f or f["file_id"] in seen_uid:
                continue
            try:
                fr = requests.get(f"{API}/bot{tok}/getFile", timeout=60,
                                  params={"file_id": f["file_id"]}).json()
                fp = ((fr.get("result") or {}).get("file_path")) if fr.get("ok") else None
                if not fp:
                    continue
                blob = requests.get(f"{API}/file/bot{tok}/{fp}", timeout=120)
                if blob.status_code != 200 or not blob.content:
                    continue
            except Exception as e:                   # noqa: BLE001
                print(f"⚠️ تنزيل {f['name']}: {_mask(e)}")
                continue
            digest = hashlib.sha256(blob.content).hexdigest()
            if digest in shas:                       # مكرّرة بالمحتوى ⇒ تُتخطّى
                skipped += 1
                seen_uid.add(f["file_id"])
                continue
            path = os.path.join(OUT_DIR, f["name"])
            n = 1
            while os.path.exists(path):              # لا تدهس اسمًا موجودًا
                stem, ext = os.path.splitext(f["name"])
                path = os.path.join(OUT_DIR, f"{stem}_{n}{ext}")
                n += 1
            with open(path, "wb") as fh:
                fh.write(blob.content)
            shas.add(digest)
            seen_uid.add(f["file_id"])
            saved += 1
            docs += 1 if f["kind"] == "document" else 0
            photos += 1 if f["kind"] == "photo" else 0

    state["offset"] = offset
    state["seen_file_ids"] = sorted(seen_uid)[-4000:]
    json.dump(state, open(STATE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"📥 حُفِظت {saved} صورة جديدة · مكرّرة متخطّاة {skipped} "
          f"· (مستندات {docs} · صور مضغوطة {photos})")
    if photos and not docs:
        print("ℹ️ كلها وصلت **صورًا مضغوطة**: تُقرأ عادةً، لكن الإرسال «كملف/Document» "
              "يحفظ حدّة النص لو صعبت قراءة صورة.")
    if saved == 0:
        print("ℹ️ لا جديد. تأكّد أنك أرسلت الصور للبوت **بعد** آخر تشغيل، وأن "
              "التحديثات لم تُستهلَك (تلغرام يحفظها ~24 ساعة).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
