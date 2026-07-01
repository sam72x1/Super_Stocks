#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تنبيه تلقرام بملخّص تدقيق Cline الأسبوعي.

طبقة إشعار مستقلّة — **لا تمسّ جذور الفرز/الدخول/الوقف/الأهداف إطلاقًا**.
تُستدعى من `.github/workflows/cline_weekly_review.yml` بعد خطوة التدقيق
مباشرةً (قبل خطوة الـPR). تقرأ أحدث `reports/cline_weekly_*.md`، تستخرج
قسم «الملخّص التنفيذي»، وترسله لتلقرام عبر:
    TELEGRAM_BOT_TOKEN   — نفس توكن البوت.
    TELEGRAM_CHAT_ID     — يقبل عدّة معرّفات مفصولة بفاصلة (مثل البوت).
اختياري: CLINE_REPORT_PATH لتحديد مسار تقرير بعينه (للاختبار).

غير حرجة: تخرج بنجاح (0) دائمًا حتى لا تُفشل الـworkflow لو غاب التوكن
أو فشل الإرسال.
"""
import glob
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

REPO = "sam72x1/Super_Stocks"
PULLS_URL = f"https://github.com/{REPO}/pulls"
MAX_LEN = 3900  # حدّ تلغرام ~4096؛ نترك هامشًا للترويسة/الرابط.


def find_report():
    """أحدث تقرير Cline: تجاوز صريح ← تقرير اليوم ← أحدث موجود."""
    override = (os.environ.get("CLINE_REPORT_PATH") or "").strip()
    if override:
        return override if os.path.exists(override) else None
    today = f"reports/cline_weekly_{date.today().isoformat()}.md"
    if os.path.exists(today):
        return today
    files = sorted(glob.glob("reports/cline_weekly_*.md"))
    return files[-1] if files else None


def extract_summary(text):
    """يستخرج قسم «## ملخّص تنفيذي» حتى العنوان التالي (بديل: أول 1500 حرف)."""
    out, cap = [], False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("## ") and ("ملخّص" in s or "ملخص" in s):
            cap = True
            continue
        if cap and s.startswith("## "):
            break
        if cap:
            out.append(ln)
    # أزل الأسطر الفاصلة/الفارغة من الذيل (مثل «---» قبل العنوان التالي).
    while out and (not out[-1].strip() or set(out[-1].strip()) <= {"-"}):
        out.pop()
    summary = "\n".join(out).strip()
    return summary or text.strip()[:1500]


def build_message():
    header = f"🔬 مراجعة Cline الأسبوعية — {date.today().isoformat()}"
    path = find_report()
    if path:
        with open(path, encoding="utf-8") as f:
            summary = extract_summary(f.read())
    else:
        summary = "⚠️ لم يُعثر على تقرير هذا الأسبوع — راجع سجلّ GitHub Actions."
    msg = (
        f"{header}\n\n{summary}\n\n"
        "📄 التقرير الكامل على فرع cline/weekly-review — يُفتح لك PR للمراجعة.\n"
        f"🔗 {PULLS_URL}\n\n"
        "(مراجعة فقط — لا دمج للجذور بلا موافقتك)"
    )
    if len(msg) > MAX_LEN:
        msg = msg[:MAX_LEN] + "…"
    return msg


def send(token, chat_id, text):
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_raw = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_raw:
        print("لا توكن/معرّف تلقرام في البيئة — تخطّي الإرسال (غير حرج).")
        return
    msg = build_message()
    chats = [c.strip() for c in chat_raw.split(",") if c.strip()]
    ok = 0
    for chat in chats:
        try:
            status = send(token, chat, msg)
            print(f"أُرسل التنبيه لـ {chat}: HTTP {status}")
            ok += 1
        except Exception as exc:  # noqa: BLE001 — إشعار غير حرج
            print(f"فشل الإرسال لـ {chat}: {exc}")
    print(f"تم إرسال تنبيه Cline لـ {ok}/{len(chats)} وجهة.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — لا تُفشل الـworkflow أبدًا
        print(f"تحذير: فشل تنبيه تلقرام (غير حرج): {exc}")
    sys.exit(0)
