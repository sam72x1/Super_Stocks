# -*- coding: utf-8 -*-
"""📺 TradingView — مصدرُ البيانات بدل Polygon وياهو (أمرُ المالك 2026-09-29: «اشتراكي مخلص ولا راح اجدده حتى لو يتوقف
التحديث اللحظي المهم الاشعارات حقت الأدوات تكون مستمرة … و المهم تكون النتايج دقيقة يعني البيانات تاخذها من ترندق فيو مب ياهو»).

⚠️ **حدُّ صدقٍ مُعلَن (لا يُخفى):** TradingView **بلا واجهةٍ رسميّةٍ للبيانات**. هذا عميلٌ للنقطتين اللتين يستعملهما موقعُه
العامّ نفسُه **بلا تسجيل دخول**:
  ① الماسح `scanner.tradingview.com/america/scan` — لقطةُ حقولٍ لأسهم السوق كلِّها في طلبٍ واحد (RSI · الفلوت · الإغلاق …)
  ② مِقبسُ الشارت `wss://data.tradingview.com/socket.io/websocket` — شموعٌ تاريخيّة لرمز (يوميّ · ساعة · الجلسةُ الممتدّة)
وكلاهما **قد يتغيّر أو يُحجَب بلا إنذار** ⇒ كلُّ نداءٍ **فاشلٌ-آمن** (None) ويُعَدّ في `CALLS` · والمستدعي يُعلن التعذّر ولا يصمت.

🔒 **لا يكتب حالةً ولا يُرسل شيئًا** — جالبُ بياناتٍ فقط · والمِقبسُ يُستورَد كسولًا (`websocket-client`) فلا تحتاجه السويّة.
"""
import datetime as dt
import json
import queue
import random
import re
import string
import threading
import time
from zoneinfo import ZoneInfo

import requests

SCAN_URL = "https://scanner.tradingview.com/america/scan"
WS_URL = "wss://data.tradingview.com/socket.io/websocket"
ORIGIN = "https://www.tradingview.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TOKEN = "unauthorized_user_token"             # بلا تسجيل دخول (الموقعُ العامّ نفسُه)
EXCHANGES = ("NASDAQ", "NYSE", "AMEX")        # أسواقُ الأسهم الأمريكيّة في الماسح (كونُ البوت ناسداك · والباقي احتياطُ الرموز)
ERRORS = ("symbol_error", "series_error", "critical_error", "protocol_error")

NY = ZoneInfo("America/New_York")

CALLS = {"scan": 0, "scan_fail": 0, "bars": 0, "bars_fail": 0, "bars_empty": 0, "reconnect": 0}
_LOCK = threading.Lock()
_FRAME = re.compile(r"~m~\d+~m~")


def _count(k, n=1):
    with _LOCK:
        CALLS[k] = CALLS.get(k, 0) + n


# ── الإطار ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def frame(payload: str) -> str:
    """حمولةٌ ⟵ «~m~N~m~حمولة» (إطارُ المقبس)."""
    return "~m~%d~m~%s" % (len(payload), payload)


def msg(func: str, params: list) -> str:
    """رسالةُ بروتوكول الشارت {"m": الدالّة, "p": المعاملات} داخل إطارها."""
    return frame(json.dumps({"m": func, "p": params}, separators=(",", ":")))


def split_frames(raw: str) -> list:
    """«~m~N~m~حمولة» مكرّرًا ⟵ [حمولة…] — **بالفاصل لا بالطول** (طولُ الخادم بوحدات UTF-16 قد يخالف `len` في بايثون)."""
    return [p for p in _FRAME.split(raw or "") if p]


def decode(payload: str):
    """حمولةٌ ⟵ ("hb", نصّ) للنبض `~h~N` · ("msg", dict) للرسالة · (None, None) لغيرهما."""
    if payload.startswith("~h~"):
        return "hb", payload
    try:
        m = json.loads(payload)
    except ValueError:
        return None, None
    return ("msg", m) if isinstance(m, dict) else (None, None)


def bars_from(msgs: list, series: str = "s1") -> list:
    """رسائلُ `timescale_update`/`du` ⟵ [(ts, o, h, l, c, v)] مرتّبةً بالزمن بلا تكرار (الأحدثُ لنفس الطابع يغلب) ·
    والشمعةُ التالفة تُتخطّى لا تُخمَّن · والحجمُ الغائب صفر."""
    out = {}
    for m in msgs or []:
        if not isinstance(m, dict) or m.get("m") not in ("timescale_update", "du"):
            continue
        p = m.get("p") or []
        if len(p) < 2 or not isinstance(p[1], dict):
            continue
        ser = p[1].get(series)
        if not isinstance(ser, dict):
            continue
        for b in ser.get("s") or []:
            v = b.get("v") if isinstance(b, dict) else None
            if not isinstance(v, list) or len(v) < 5:
                continue
            try:
                ts = int(float(v[0]))
                o, h, lo, c = (float(x) for x in v[1:5])
                vol = float(v[5]) if len(v) > 5 and v[5] is not None else 0.0
            except (TypeError, ValueError):
                continue
            if min(o, h, lo, c) <= 0 or h < lo:
                continue
            out[ts] = (ts, o, h, lo, c, vol)
    return [out[k] for k in sorted(out)]


def _rand(n: int = 12) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


# ── مِقبسُ الشارت ────────────────────────────────────────────────────────────────────────────────────────────────────
class Chart:
    """مِقبسٌ واحدٌ لعدّة رموزٍ بالتتابع — جلسةُ شارتٍ لكلّ رمز تُحذف بعده · والنبضُ `~h~` يُردّ · وخطأُ الرمز ⟵ None له
    وحدَه · وسقوطُ المقبس ⟵ يُغلق ويُعاد فتحُه في النداء التالي. `connect` محقونٌ للاختبار (كائنٌ له send/recv/close)."""

    def __init__(self, url: str = WS_URL, timeout: float = 20.0, connect=None):
        self.url, self.timeout, self._connect = url, float(timeout), connect
        self.ws = None

    def open(self):
        if self.ws is None:
            if self._connect is not None:
                self.ws = self._connect()
            else:
                from websocket import create_connection          # كسولٌ: السويّةُ لا تحتاجه
                self.ws = create_connection(self.url, timeout=self.timeout,
                                            header=["Origin: " + ORIGIN, "User-Agent: " + UA])
            self.ws.send(msg("set_auth_token", [TOKEN]))
        return self.ws

    def close(self):
        try:
            if self.ws is not None:
                self.ws.close()
        except Exception:                                          # noqa: BLE001
            pass
        self.ws = None

    def bars(self, symbol: str, interval: str = "1D", n: int = 600, extended: bool = False,
             adjustment: str = "splits"):
        """شموعُ رمزٍ «EXCH:SYM» ⟵ [(ts, o, h, l, c, v)] (ts = بدايةُ الشمعة بثواني يونكس) · [] بلا شموع · None عند
        خطأ الرمز أو المقبس أو انقضاء المهلة (يُعَدّ `bars_fail`)."""
        _count("bars")
        cs = "cs_" + _rand()
        spec = json.dumps({"symbol": symbol, "adjustment": adjustment,
                           "session": "extended" if extended else "regular"}, separators=(",", ":"))
        got, status = [], None
        try:
            ws = self.open()
            ws.send(msg("chart_create_session", [cs, ""]))
            ws.send(msg("resolve_symbol", [cs, "symbol_1", "=" + spec]))
            ws.send(msg("create_series", [cs, "s1", "s1", "symbol_1", str(interval), int(n)]))
            t_end = time.time() + self.timeout
            while status is None and time.time() < t_end:
                raw = ws.recv()
                for pl in split_frames(raw):
                    kind, m = decode(pl)
                    if kind == "hb":
                        ws.send(frame(m))
                        continue
                    if kind != "msg":
                        continue
                    mp = m.get("p") or []
                    name = m.get("m")
                    if name in ("critical_error", "protocol_error"):
                        status = name
                        break
                    if not mp or mp[0] != cs:
                        continue                                   # رسالةُ جلسةٍ أخرى أو إشعارٌ عامّ
                    if name in ERRORS:
                        status = name
                        break
                    got.append(m)
                    if name == "series_completed":
                        status = "ok"
                        break
            try:
                ws.send(msg("chart_delete_session", [cs]))
            except Exception:                                      # noqa: BLE001
                self.close()
        except Exception:                                          # noqa: BLE001 — مقبسٌ ساقط ⟵ يُعاد في النداء التالي
            self.close()
            status = status or "socket"
        if status in ("critical_error", "protocol_error", "socket"):
            self.close()
        if status != "ok":
            _count("bars_fail")
            return None
        out = bars_from(got)
        if not out:
            _count("bars_empty")
        return out


def fetch_many(symbols, interval: str = "1D", n: int = 600, extended: bool = False, workers: int = 6,
               chart_factory=None, progress=None, pause: float = 0.0, gate=None) -> dict:
    """{رمز: شموع | None} لعدّة رموز على `workers` مقابس متوازية (كلُّ مقبسٍ يمرّ على نصيبه بالتتابع) · والرمزُ الذي فشل
    يُعاد **مرّةً واحدة** على مقبسٍ جديد (سقوطٌ عابر) · `chart_factory` محقونٌ للاختبار. الرموزُ بصيغة «EXCH:SYM».
    و`gate` (اختياريّ · قاطعُ دائرة) = كائنٌ له `skip()` قبل كلّ رمز (True ⟵ None بلا نداء) و`record(ok)` بعد نتيجته
    النهائيّة — فحين يُحجَب الموقعُ لا تُستنفَد المهلةُ على آلاف الرموز (درسُ Polygon 2026-09-29) · وبلا `gate` السلوكُ كما هو."""
    syms = list(dict.fromkeys(symbols or []))
    out = {}
    if not syms:
        return out
    q = queue.Queue()
    for s in syms:
        q.put(s)
    make = chart_factory or (lambda: Chart())
    done = [0]

    def work():
        ch = make()
        try:
            while True:
                try:
                    s = q.get_nowait()
                except queue.Empty:
                    return
                if gate is not None and gate.skip():
                    with _LOCK:
                        out[s] = None
                        done[0] += 1
                    continue
                r = ch.bars(s, interval=interval, n=n, extended=extended)
                if r is None:
                    ch.close()
                    _count("reconnect")
                    r = ch.bars(s, interval=interval, n=n, extended=extended)
                if gate is not None:
                    gate.record(r is not None)
                with _LOCK:
                    out[s] = r
                    done[0] += 1
                    k = done[0]
                if progress and k % 250 == 0:
                    progress(k, len(syms))
                if pause:
                    time.sleep(pause)
        finally:
            ch.close()

    ts = [threading.Thread(target=work, daemon=True) for _ in range(max(1, min(int(workers), len(syms))))]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


# ── الماسح ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def scan(columns, exchanges=EXCHANGES, extra_filters=None, post=None, timeout: float = 60.0, page: int = 5000):
    """الماسح ⟵ {«EXCH:SYM»: {عمود: قيمة}} لأسهم `exchanges` كلِّها (صفحاتٌ من `page`) · أو None عند التعذّر (فاشلٌ-آمن ·
    يُعَدّ `scan_fail`) — **لا نصفَ قائمة**: صفحةٌ تتعذّر ⟵ None للكلّ (درسُ `load_all_splits`: التغطيةُ لا تُعلَّم بصفحاتٍ
    ناقصة). `post` محقونٌ للاختبار (توقيعُ `requests.post`)."""
    cols = list(columns)
    post = post or requests.post
    flt = [{"left": "exchange", "operation": "in_range", "right": list(exchanges)}] + list(extra_filters or [])
    out, start, total = {}, 0, None
    while total is None or start < total:
        body = {"columns": cols, "filter": flt, "options": {"lang": "en"}, "markets": ["america"],
                "range": [start, start + int(page)], "sort": {"sortBy": "name", "sortOrder": "asc"},
                "symbols": {"query": {"types": []}, "tickers": []}}
        _count("scan")
        try:
            r = post(SCAN_URL, data=json.dumps(body), timeout=timeout,
                     headers={"Content-Type": "application/json", "Origin": ORIGIN, "Referer": ORIGIN + "/",
                              "User-Agent": UA})
            if getattr(r, "status_code", 0) != 200:
                _count("scan_fail")
                return None
            js = r.json()
        except Exception:                                          # noqa: BLE001
            _count("scan_fail")
            return None
        rows = js.get("data") if isinstance(js, dict) else None
        if not isinstance(rows, list):
            _count("scan_fail")
            return None
        total = int(js.get("totalCount") or 0)
        for row in rows:
            s, d = (row or {}).get("s"), (row or {}).get("d")
            if s and isinstance(d, list) and len(d) == len(cols):
                out[s] = dict(zip(cols, d))
        if not rows:
            break
        start += int(page)
    return out


def ticker_map(snap: dict) -> dict:
    """لقطةُ الماسح ⟵ {رمزٌ مجرّد: «EXCH:SYM»} — وعند تكرار الرمز في سوقين يغلب ناسداك (كونُ البوت) ثمّ الأوّلُ أبجديًّا."""
    best = {}
    for full in sorted(snap or {}):
        ex, _, sym = full.partition(":")
        if not sym:
            continue
        if sym not in best or (ex == "NASDAQ" and not best[sym].startswith("NASDAQ:")):
            best[sym] = full
    return best


def ny_time(ts: int) -> dt.datetime:
    """طابعُ شمعةٍ (ثواني يونكس) ⟵ وقتُ نيويورك."""
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).astimezone(NY)


def ny_day(ts: int) -> str:
    """طابعُ شمعةٍ (ثواني يونكس) ⟵ يومُ نيويورك «YYYY-MM-DD»."""
    return ny_time(ts).date().isoformat()
