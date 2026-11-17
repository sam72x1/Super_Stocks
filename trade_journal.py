#!/usr/bin/env python3
"""📒 دفترُ صفقات المالك (أمرُه 2026-11-16 · التعريفاتُ في `trade_journal_prereg.md` قبل أيّ صفقة).

يقرأ أوامرَ «صفقة:»/«خروج:» من **الخزنة المشفّرة** (`journal_vault.py` · صندوقُ الوارد الذي ملأه جامعُ التلغرام) ⟵ صفٌّ في الخزنة
نفسِها مع حالة السهم عند البوت **لحظةَ الرسالة** (نسخُ الملفّات عند آخر التزامٍ قبلها) ⟵ تقريرٌ **للمالك وحدَه** على تلغرام بعد كلّ
عشر صفقاتٍ مغلقة. 🔐 (أمرُ المالك 2026-11-17 ①-2) لا سعرَ ولا نصَّ ولا رمزَ في أيّ ملفٍّ عامّ ولا في سجلّ Actions · `TRADE_JOURNAL=0` ⟵
مطفأ. 🔒 لا يسحب من تلغرام ولا يمسّ إزاحةَ الجامع ولا أيَّ حالة إنتاج.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

REPORT_EVERY = 10
NY = ZoneInfo("America/New_York")
_DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩٫۰۱۲۳۴۵۶۷۸۹", "0123456789.0123456789")
_SEP = re.compile(r"\s*(?:·|\||،|—|–|\s-\s|\n)\s*")
_SYM = re.compile(r"^\$?([A-Za-z][A-Za-z.]{0,5})$")
_NUM = re.compile(r"\d+(?:\.\d+)?")


def log(m=""):
    print(m, flush=True)


# ── نقيّة ──────────────────────────────────────────────────────────────────────────────────────
def parse_cmd(text):
    """نصُّ رسالةٍ ⟵ {kind: entry|exit، sym، price، reason} · أو {kind: bad، why} لأمرٍ لا يُقرأ · أو None لغير الأوامر."""
    t = str(text or "").strip().translate(_DIG)
    m = re.match(r"^(صفقة|خروج)\s*[:：]\s*(.*)$", t, re.S)
    if not m:
        return None
    kind = "entry" if m.group(1) == "صفقة" else "exit"
    parts = [p.strip() for p in _SEP.split(m.group(2).strip()) if p.strip()]
    if len(parts) < 2 and parts:                                 # «صفقة: ABCD 1.25 سبب» بلا فاصل ⟵ المسافات
        w = parts[0].split()
        parts = w[:2] + ([" ".join(w[2:])] if len(w) > 2 else [])
    if len(parts) < 2:
        return {"kind": "bad", "why": "حقولٌ ناقصة", "text": t[:200]}
    sm = _SYM.match(parts[0].replace(" ", ""))
    nm = _NUM.search(parts[1].replace(",", "."))
    if not sm or not nm or float(nm.group()) <= 0:
        return {"kind": "bad", "why": "الرمزُ أو السعرُ لا يُقرأ", "text": t[:200]}
    out = {"kind": kind, "sym": sm.group(1).upper(), "price": float(nm.group())}
    if kind == "entry":
        out["reason"] = " · ".join(parts[2:])[:300]
    return out


def ny_day(iso):
    return dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(NY).date().isoformat()


def iso_ms(iso):
    return int(dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp() * 1000)


def new_commands(inbox, have):
    """صندوقُ وارد الخزنة [{message_id، date، text}] ⟵ أوامرُ جديدة (مفتاحُها `message_id`) بترتيب الوقت · وغيرُ الأمر لا يُقرأ."""
    out = []
    for r in inbox or ():
        if not isinstance(r, dict) or not r.get("text"):
            continue
        mid = r.get("message_id")
        if mid is None or int(mid) in have:
            continue
        c = parse_cmd(r["text"])
        if c is None:
            continue
        out.append({"id": int(mid), "date": r.get("date"), **c})
    return sorted(out, key=lambda x: (str(x.get("date") or ""), x["id"]))


def gold_of(ledger_lines, sym, day, upto_ms, gmin=3):
    """🥇 بقاعدة اليوم: كرتُ `M5` للسهم يومَه بـ`green` ‏≥ gmin أو `j1` قبل `upto_ms`."""
    for ln in ledger_lines:
        if sym not in ln or day not in ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if str(r.get("symbol") or "").upper() != sym or str(r.get("date") or "") != day:
            continue
        if r.get("price_ms") and int(r["price_ms"]) > upto_ms:
            continue
        g = r.get("green")
        if (isinstance(g, (int, float)) and g >= gmin) or r.get("j1") is True:
            return True
    return False


def bot_state(sym, day, ms, files, entry_status=None):
    """حالةُ السهم عند البوت من نسخ الملفّات `files` = {اسم: نصّ} (نقيّة) ⟵ dict."""
    def _j(name):
        try:
            return json.loads(files.get(name) or "null")
        except ValueError:
            return None
    st = {"list": False, "near": False, "ready": None, "readiness": None, "missing": [], "gold": False, "shadow": False, "x30": None}
    wl = _j("weekly_watchlist.json") or {}
    for s in (wl.get("stocks") or []) if isinstance(wl, dict) else []:
        if str(s.get("symbol") or "").upper() == sym and s.get("status") != "stopped":
            st["list"], st["readiness"] = True, s.get("readiness")
            st["missing"] = list(s.get("soft_fails") or [])[:8]
            if entry_status is not None:
                try:
                    st["ready"] = str((entry_status(s) or {}).get("label") or "") or None
                except Exception:                                # noqa: BLE001
                    st["ready"] = None
            break
    near = _j("near_watch.json") or {}
    row = near.get(sym) if isinstance(near, dict) else None
    if isinstance(row, dict):
        st["near"] = True
        if not st["list"]:
            st["readiness"] = row.get("readiness")
            st["missing"] = list(row.get("outside") or [])[:8]
    st["gold"] = gold_of((files.get("tier_fwd_ledger.jsonl") or "").splitlines(), sym, day, ms)
    stamp = _j("shadow_tg_stamp.json") or {}
    st["shadow"] = bool(isinstance(stamp, dict) and stamp.get("last_sent") == day and sym in (stamp.get("symbols") or []))
    oe = _j("op_entry_state.json") or {}
    xm = oe.get("XM:" + sym) if isinstance(oe, dict) else None
    if isinstance(xm, dict) and xm.get("date") == day:
        st["x30"] = {"px": xm.get("px"), "ms": xm.get("ms"), "before_you": bool(xm.get("ms") and int(xm["ms"]) <= ms)}
    return st


def pair(rows):
    """أوامرُ الدفتر ⟵ صفقاتٌ مغلقة: كلُّ خروجٍ يُغلق أقدمَ دخولٍ مفتوحٍ لرمزه (FIFO) ⟵ [(دخول، خروج)] بترتيب الإغلاق."""
    opened, closed = {}, []
    for r in sorted(rows, key=lambda x: (str(x.get("date") or ""), x["id"])):
        if r.get("kind") == "entry":
            opened.setdefault(r["sym"], []).append(r)
        elif r.get("kind") == "exit" and opened.get(r["sym"]):
            closed.append((opened[r["sym"]].pop(0), r))
    return closed


def outcome(entry, ex):
    """نتيجتُك وما كان البوت سيفعله (العقد §③): إشعارُ «تحرّك 30%» يومَ دخولك ⟵ دخلَ بسعره وخرجَ بخروجك · وإلّا لم يدخل."""
    you = ex["price"] / entry["price"] - 1.0
    x = (entry.get("state") or {}).get("x30")
    bot = (ex["price"] / float(x["px"]) - 1.0) if (x and x.get("px")) else None
    return you, bot


def _med(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def _p(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def report(closed, upto):
    """تقريرُ آخر عشر صفقاتٍ حتى `upto` (نقيّ) ⟵ نصّ."""
    chunk = closed[upto - REPORT_EVERY:upto]
    L = [f"📒 دفترُ صفقاتك — الصفقات {upto - REPORT_EVERY + 1}-{upto}"]
    you_all, pair_you, pair_bot, no_alert = [], [], [], 0
    for e, x in chunk:
        you, bot = outcome(e, x)
        st = e.get("state") or {}
        you_all.append(you)
        if bot is None:
            no_alert += 1
            b = "البوت لم ينبّه"
        else:
            pair_you.append(you)
            pair_bot.append(bot)
            b = f"البوت {_p(bot)}" + ("" if (st.get("x30") or {}).get("before_you") else " (نبّه بعدك)")
        flags = (" 🥇" if st.get("gold") else "") + (" 🌘" if st.get("shadow") else "")
        where = "القائمة" if st.get("list") else ("تحت المتابعة" if st.get("near") else "خارج البوت")
        L.append(f"${e['sym']} {ny_day(e['date'])[5:]}: أنت {_p(you)} · {b}{flags} · {where}"
                 + (f" · {st['ready']}" if st.get("ready") else ""))
    L.append(f"— أنت: وسيطك {_p(_med(you_all))} · رابحة {sum(1 for y in you_all if y > 0)} من {len(you_all)}")
    if pair_bot:
        L.append(f"— حيث نبّه البوت ({len(pair_bot)}): وسيطك {_p(_med(pair_you))} مقابل البوت {_p(_med(pair_bot))} على الصفقات نفسِها")
    L.append(f"— لم ينبّه البوت في {no_alert} · ⚠️ عشرُ صفقاتٍ وصفٌ لا حكم")
    return "\n".join(L)


# ── الرنر ─────────────────────────────────────────────────────────────────────────────────────
STATE_FILES = ("weekly_watchlist.json", "near_watch.json", "tier_fwd_ledger.jsonl", "shadow_tg_stamp.json", "op_entry_state.json")


def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout


def files_at(iso):
    """نسخُ ملفّات الحالة عند آخر التزامٍ قبل `iso` ⟵ ({اسم: نصّ}، صادقٌ؟) · وإلّا الحاليّة وصادقٌ = False (يُوسَم)."""
    h = _git("rev-list", "-1", f"--before={iso}", "HEAD").strip()
    out, exact = {}, bool(h)
    for f in STATE_FILES:
        txt = _git("show", f"{h}:{f}") if h else ""
        if not txt:
            exact = False
            try:
                txt = open(f, encoding="utf-8").read()
            except OSError:
                txt = ""
        out[f] = txt
    return out, exact


def send_owner(text, owner=None, token=None):
    """🔐 التقريرُ **للمالك وحدَه** (`TELEGRAM_OWNER_ID`) لا لمستلمي التقرير اليوميّ · بلا السرّ ⟵ False (يبقى معلَّقًا)."""
    owner = str(owner if owner is not None else os.environ.get("TELEGRAM_OWNER_ID", "")).strip()
    token = str(token if token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if not owner or not token:
        return False
    try:
        import requests
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": owner, "text": text, "disable_web_page_preview": "true"}, timeout=30)
        return r.status_code == 200 and bool((r.json() or {}).get("ok"))
    except Exception:                                            # noqa: BLE001
        return False


def main(vault_mod=None, send=None):
    JV = vault_mod
    if JV is None:
        import journal_vault as JV
    send = send or send_owner
    if not JV.enabled():
        log("📒 الدفتر مطفأ (`TRADE_JOURNAL=0` أو بلا مفتاح) — لا شيء")
        return 0
    v = JV.load()
    if v is None:
        log("⛔ 📒 الخزنةُ لم تُفكّ (المفتاحُ تغيّر؟) — لا كتابةَ فوقها")
        return 1
    led = v["ledger"]
    have = {int(r["id"]) for r in led if r.get("id") is not None}
    new = new_commands(v["inbox"], have)
    try:
        import Super_stock as bot
        es = bot.entry_status
    except Exception:                                            # noqa: BLE001
        es = None
    for c in new:
        if c["kind"] == "entry":
            fl, exact = files_at(c["date"])
            c["state"] = bot_state(c["sym"], ny_day(c["date"]), iso_ms(c["date"]), fl, es)
            c["state"]["exact"] = exact
        led.append(c)
    st = v["state"]
    closed = pair([r for r in led if r.get("kind") in ("entry", "exit")])
    done = int(st.get("reported") or 0)
    sent = 0
    while len(closed) >= done + REPORT_EVERY:
        if not send(report(closed, done + REPORT_EVERY)):        # 🔐 لا يُطبَع نصُّ التقرير في السجلّ العامّ
            log("⚠️ 📒 التقريرُ لم يُرسَل للمالك (بلا `TELEGRAM_OWNER_ID` أو رفضٌ) — يُعاد في التشغيل التالي")
            break
        done += REPORT_EVERY
        sent += 1
    st.update(reported=done, closed=len(closed), entries=sum(1 for r in led if r.get("kind") == "entry"))
    if not JV.save(v):
        log("⛔ 📒 حفظُ الخزنة تعذّر")
        return 1
    log(f"📒 الدفتر: أوامرُ جديدة {len(new)} · تقاريرُ أُرسلت الآن {sent}")   # أعدادٌ فقط — لا رمزَ ولا سعر
    return 0


if __name__ == "__main__":
    sys.exit(main())
