#!/usr/bin/env python3
"""🔐 خزنةُ دفتر صفقات المالك (أمرُه 2026-11-17 ①-2: «لا تكتب أسعاري ولا نصوص صفقاتي في أي ملف في الريبو العام … مشفّرًا بسرّ»).

ملفٌّ واحد `trade_journal.vault` = JSON مشفَّرٌ بـAES-256-CBC (‏`openssl enc -pbkdf2 -iter 200000 -md sha256 -salt -a -A`) يحمل:
`inbox` (أوامرُ «صفقة:»/«خروج:» بنصّها كما وصلت) · `ledger` (الصفوفُ المحلَّلة مع حالة البوت) · `state` (عدّاداتُ التقارير).
المفتاح: السرُّ `TRADE_JOURNAL_KEY` إن وُجد · وإلّا مشتقٌّ من `TELEGRAM_BOT_TOKEN` (SHA-256 بملحٍ ثابت) — **مساوٍ أمنيًّا للرسائل نفسِها**:
من يملك رمزَ البوت يقرأ رسائلَ البوت أصلًا · ⚠️ وتغييرُ رمز البوت يُعمي الخزنةَ القديمة (يُعلَن ولا يُدهَس: فكُّ تشفيرٍ فاشل ⟵ لا كتابة).
المفتاح `TRADE_JOURNAL=0` ⟵ الدفترُ مطفأ: لا التقاطَ ولا كتابة (والأوامرُ لا تُحفظ في أيّ مكان).
🔒 لا يطبع نصًّا ولا رمزًا ولا سعرًا في السجلّ (سجلُّ Actions عامٌّ أيضًا).
"""
import hashlib
import json
import os
import subprocess

VAULT = "trade_journal.vault"
_SALT = "super-stocks|trade-journal|v1|"


def _pass(env=None):
    env = os.environ if env is None else env
    k = str(env.get("TRADE_JOURNAL_KEY") or "").strip()
    if k:
        return k
    t = str(env.get("TELEGRAM_BOT_TOKEN") or "").strip()
    return hashlib.sha256((_SALT + t).encode()).hexdigest() if t else None


def enabled(env=None):
    env = os.environ if env is None else env
    return str(env.get("TRADE_JOURNAL", "1")).strip() != "0" and _pass(env) is not None


def _openssl(args, data, pw):
    e = dict(os.environ, TJV_PASS=pw)
    p = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-md", "sha256", "-a", "-A",
                        *args, "-pass", "env:TJV_PASS"], input=data, capture_output=True, env=e)
    return p.stdout if p.returncode == 0 else None


def encrypt(obj, pw):
    out = _openssl(["-salt"], json.dumps(obj, ensure_ascii=False, sort_keys=True).encode(), pw)
    return None if out is None else out.decode() + "\n"


def decrypt(txt, pw):
    out = _openssl(["-d"], (txt or "").strip().encode(), pw)
    if out is None:
        return None
    try:
        v = json.loads(out.decode())
    except ValueError:
        return None
    return v if isinstance(v, dict) else None


def empty():
    return {"v": 1, "inbox": [], "ledger": [], "state": {"reported": 0}}


def load(path=VAULT, env=None):
    """⟵ dict · ملفٌّ غائب ⟵ خزنةٌ فارغة · بلا مفتاح أو فكٌّ فاشل ⟵ None (لا يُكتب فوقها أبدًا)."""
    pw = _pass(env)
    if pw is None:
        return None
    if not os.path.exists(path):
        return empty()
    v = decrypt(open(path, encoding="utf-8").read(), pw)
    if v is None:
        return None
    for k, d in empty().items():
        v.setdefault(k, d)
    return v


def save(v, path=VAULT, env=None):
    pw = _pass(env)
    txt = None if pw is None else encrypt(v, pw)
    if txt is None:
        return False
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(txt)
    os.replace(tmp, path)
    return True


def add_inbox(item, path=VAULT, env=None):
    """أمرٌ واحد {message_id، date، text} ⟵ صندوقُ الوارد (لا تكرارَ بالمعرّف) · True إن حُفظ."""
    if not enabled(env):
        return False
    v = load(path, env)
    if v is None:
        return False
    if any(str(x.get("message_id")) == str(item.get("message_id")) for x in v["inbox"]):
        return True
    v["inbox"].append({k: item.get(k) for k in ("message_id", "date", "text")})
    return save(v, path, env)
