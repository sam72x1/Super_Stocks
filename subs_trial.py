#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📣🧪 تجربةُ قناة المشتركين — عرضٌ فقط (أمرُ المالك 2026-11-19 «تجربة للقناة الآن»).

يشغّل أدواتِ الأسهم على آخر جلسةٍ مكتملة **بوضع التقاط**: كلُّ `send_telegram` يُلتقَط ولا يُرسَل (لا رقمَ محادثةِ المالك في بيئة التشغيل
أصلًا) · `git_save` معطَّلة والـworkflow قارئٌ (`contents: read`) ⟵ **لا ختمَ ولا صفَّ سجلٍّ يصل المستودع** (ما يُكتب على الرنر يزول معه) ·
ثمّ تُرسَل **نسخةُ القناة** (`subs_channel.sanitize` — بلا اسم فيصل) إلى `TELEGRAM_SUBS_CHAT_ID` وحدَه نشرًا مباشرًا وأوّلُ سطرٍ «تجربة».
لا يقرأ `subs_channel.ON` ولا يغيّره · يدويٌّ حصرًا · لا يمسّ أيَّ تشغيلٍ مجدول. `SUBS_TRIAL_DRY=1` ⟵ التقاطٌ وعدٌّ بلا إرسال.
"""
import os
import re
import sys
import traceback

FIRST_LINE = "تجربة"
NAME_RX = re.compile(r"فيصل|kisar", re.I)
# (المفتاح · الاسمُ المعروض · مفاتيحُ التشغيل القسريّ · المُشغِّل)
FORCE_ENV = ("HUNTER_FORCE", "SPLIT_FILTER_FORCE", "PRESS_RADAR_FORCE", "METHOD_FORCE", "DIGEST_FORCE")
TOOLS = (
    ("daily", "📋 الفرز اليوميّ (القائمة · الجاهزيّة · تحت المتابعة · اليد · رادار التقسيم · متابعة التنبيهات)"),
    ("split_hunter", "🪝 صيّاد التقسيم"),
    ("split_filter", "🧮 فلتر التقسيم"),
    ("press", "🗜️ رادار الضغط"),
    ("envelope", "📐 صيّاد الغلاف"),
    ("method", "🔬 صيّاد النهج العلمي (المطابق · المخفّف · بلا هدف فجوة)"),
    ("presession", "📒 ملخّص ما قبل الجلسة"),
)
SILENT = {"envelope": "صامتٌ بقرارٍ سابق — لا رسالةَ تلغرام له أصلًا (يكتب سجلَّه فقط)"}


def count_name(text):
    """🔒 نقيّة: كم مرّةً يرد اسمُ فيصل أو حسابُه في النصّ."""
    return len(NAME_RX.findall(text or ""))


def cut_hist(hist, cutoff):
    """🔒 نقيّة على المُدخَل: شموعُ كلّ رمزٍ حتى `cutoff` شاملًا (الجلسةُ الجارية لا تدخل) · والفارغُ يسقط · وغيرُ القاموس يُعاد كما هو."""
    if cutoff is None or not isinstance(hist, dict):
        return hist
    out = {}
    for sym, df in hist.items():
        try:
            keep = [getattr(ts, "date", lambda: ts)() <= cutoff for ts in df.index]
            d2 = df[keep]
            if len(d2):
                out[sym] = d2
        except Exception:                                        # noqa: BLE001
            out[sym] = df
    return out


def plan(captured, rcs):
    """🔒 نقيّة: ما يُرسَل للقناة من الملتقَط · ⟵ (قائمةُ (أداة، نصّ)، تقريرٌ لكلّ أداة).
    الأداةُ التي لها رسائلُ مسمّاةٌ للقناة (`subs_mirror`) تُرسَل منها هي وحدَها · وما لا نداءَ قناةٍ له (النهج العلمي) تُرسَل رسائلُه
    إن خرج 0 · والعطلُ (خروجٌ غيرُ صفر أو استثناء) لا يُرسَل ويُذكر سببُه."""
    out, rep = [], {}
    for key, _name in TOOLS:
        c = captured.get(key) or {"sent": [], "mirror": []}
        rc = rcs.get(key)
        r = {"sent": 0, "why": None, "name_hits": 0}
        if key in SILENT:
            r["why"] = SILENT[key]
        elif rc not in (0, None):
            r["why"] = f"لم تكتمل الأداة ({rc})"
        else:
            msgs = [t for _k, t in c["mirror"]] if c["mirror"] else ([] if key == "daily" else list(c["sent"]))
            if not msgs:
                r["why"] = "لم تُنتج رسالةً في هذا التشغيل"
            for t in msgs:
                r["name_hits"] += count_name(t)
                out.append((key, t))
            r["sent"] = len(msgs)
        rep[key] = r
    return out, rep


def _runner(key):
    if key == "daily":
        import Super_stock as S
        return S.main
    if key == "split_hunter":
        import split_hunter as M
        return M.run
    if key == "split_filter":
        import split_filter_hunter as M
        return M.run
    if key == "press":
        import press_radar as M
        return M.run
    if key == "method":
        import method_hunter as M
        return M.run
    if key == "presession":
        import presession_digest as M
        return M.main
    return None


def main():
    os.environ.pop("TELEGRAM_CHAT_ID", None)                     # 🔒 لا محادثةَ مالكٍ في هذا التشغيل مهما كانت البيئة
    os.environ.pop("TELEGRAM_OWNER_ID", None)
    os.environ["SCREENER_MODE"] = "FULL"
    os.environ["FORCE_RENEW"] = ""
    os.environ["RENEW_ON_CLOSE"] = "0"
    for k in FORCE_ENV:
        os.environ[k] = "1"
    import Super_stock as S
    import subs_channel as SC
    from split_hunter import session_gate
    S.TELEGRAM_CHAT = ""
    cutoff = session_gate()[1]
    S.log(f"📣🧪 تجربةُ القناة: آخرُ جلسةٍ مكتملة {cutoff} — التقاطٌ بلا إرسالٍ للمالك ولا حفظ")
    captured, cur = {}, [None]

    def _cap_send(text, on_admin=None):
        captured.setdefault(cur[0], {"sent": [], "mirror": []})["sent"].append(str(text or ""))
        return True

    def _cap_mirror(text, subs):
        if subs in SC.ACTIVE:
            captured.setdefault(cur[0], {"sent": [], "mirror": []})["mirror"].append((subs, str(text or "")))
        return "off"

    _dl = S.download_history
    S.send_telegram = _cap_send
    S.subs_mirror = _cap_mirror
    S.git_save = lambda *a, **k: True
    S.send_telegram_document = lambda *a, **k: True
    S.send_owner_document = lambda *a, **k: True
    S.download_history = lambda *a, **k: cut_hist(_dl(*a, **k), cutoff)
    rcs = {}
    for key, name in TOOLS:
        if key in SILENT:
            continue
        cur[0] = key
        S.log(f"━━━ 📣🧪 {name} ━━━")
        try:
            rc = _runner(key)()
            rcs[key] = 0 if rc in (None, 0) else rc
        except SystemExit as e:
            rcs[key] = 0 if e.code in (None, 0) else f"خروج {e.code}"
        except Exception as e:                                   # noqa: BLE001
            rcs[key] = f"{type(e).__name__}"
            traceback.print_exc()
    cur[0] = None
    todo, rep = plan(captured, rcs)
    dry = os.environ.get("SUBS_TRIAL_DRY", "").strip() == "1"
    first, parts_by = True, {}
    for key, text in todo:
        chunks = [c for c in (SC.sanitize(x) for x in S._chunk_message(text)) if c.strip()]
        if not chunks:
            continue
        if first:
            chunks[0] = FIRST_LINE + "\n\n" + chunks[0]
            first = False
        ok = True if dry else SC._send(chunks)
        d = parts_by.setdefault(key, {"parts": 0, "fail": 0})
        d["parts"] += len(chunks)
        d["fail"] += 0 if ok else 1
    S.log("━━━ 📣🧪 الحصيلة ━━━" + (" (جافّ — لا إرسال)" if dry else ""))
    total = 0
    for key, name in TOOLS:
        r, p = rep[key], parts_by.get(key, {"parts": 0, "fail": 0})
        c = captured.get(key) or {"sent": [], "mirror": []}
        total += p["parts"]
        S.log(f"{name}: رسائل {r['sent']} · أجزاءٌ مُرسَلة {p['parts']}"
              + (f" · ⚠️ تعذّر إرسالُ {p['fail']}" if p["fail"] else "")
              + f" · «فيصل/kisar» قبل الحذف {r['name_hits']} مرّة"
              + (f" · لم تُرسَل: {r['why']}" if r["why"] else "")
              + f" · (التُقط {len(c['sent'])} رسالةً إجمالًا)")
        if r["why"] and c["sent"]:
            S.log("   ↳ آخرُ ما قالته الأداة: " + SC.sanitize(SC._strip_tags(c["sent"][-1]))[:300].replace("\n", " ⏎ "))
        _mir = {t for _k, t in c["mirror"]}
        for t in c["sent"]:
            if c["mirror"] and t not in _mir:
                S.log("   ↳ خارج قائمة القناة (لم تُرسَل): " + SC._strip_tags(t).strip().split("\n")[0][:80])
    S.log(f"📣🧪 المجموع: {total} جزءًا إلى القناة · ولا شيء لمحادثة المالك · ولا حفظ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
