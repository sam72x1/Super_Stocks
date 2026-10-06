"""🩺 مِجَسٌّ مؤقّت (2026-10-06): صيغةُ صفحة اقتراض ChartExchange بعد عطل `parse:empty` (حصّاد 37430703426:
26 من 26 · الصفحةُ ‏≈117 ألف محرف ومرساةُ `name="ctbtoday"` غائبة). يطبع بنيةَ الصفحة ولا يكتب شيئًا · يُحذف بعد القراءة."""
import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Super_stock as S  # noqa: E402

SHARD = int(os.environ.get("CTB_SHARD", "0"))
SYMS = [["GWAV", "LABT"], ["KMRK", "AAPL"], ["TRAW", "GEOS"]][SHARD % 3]


def strip(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))


def ctx(s, pat, w=170, k=6, flags=re.I):
    out = []
    for m in re.finditer(pat, s, flags):
        out.append(s[max(0, m.start() - w):m.end() + w])
        if len(out) >= k:
            break
    return out


for sym in SYMS:
    url = f"https://chartexchange.com/symbol/nasdaq-{sym.lower()}/borrow-fee/"
    print("=" * 100)
    try:
        r = requests.get(url, headers=S.BROWSER_UA, timeout=15)
    except Exception as e:  # noqa: BLE001
        print(sym, "EXC", type(e).__name__, e)
        continue
    t = r.text or ""
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    print(f"{sym} status={r.status_code} len={len(t)} title={title.group(1).strip() if title else None!r} final_url={r.url}")
    print("parse_old:", S._parse_ce_borrow(t), "| 'ctbtoday' in page:", "ctbtoday" in t, "| 'ctb' count:", t.lower().count("ctb"))
    txt = strip(t)
    print("stripped_len:", len(txt))
    for pat in [r"As of", r"shares available", r"available", r"fee of", r"Borrow Fee", r"Interactive", r"IBKR", r"Rebate"]:
        for c in ctx(txt, pat, k=4):
            print(f"  [{pat}] …{c}…")
    i = t.lower().find("available")
    if i >= 0:
        print("RAW@available:", repr(t[max(0, i - 900):i + 600]))
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)", t, re.I)
    print("script_src:", srcs[:30])
    apis = sorted(set(re.findall(r"[\"'](/api/[^\"'\s]+|https?://[^\"'\s]*(?:api|ajax|json)[^\"'\s]*)[\"']", t, re.I)))
    print("api_like:", apis[:40])
    for sc in re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", t, re.S | re.I):
        if re.search(r"borrow|ctb|available|fee", sc, re.I):
            for c in ctx(sc, r"borrow|ctb|available|fee", w=250, k=3):
                print("  [inline-script] …", repr(c), "…")
    datas = re.findall(r"(data-[a-z0-9_-]+)=[\"']([^\"']{20,400})", t, re.I)
    print("data_attrs:", [(a, v[:160]) for a, v in datas if re.search(r"borrow|ctb|fee|avail|\{", v, re.I)][:20])
    for tb in re.findall(r"<table.*?</table>", t, re.S | re.I)[:3]:
        print("TABLE:", strip(tb)[:900])
    print("TEXT_HEAD:", txt[:1500])
