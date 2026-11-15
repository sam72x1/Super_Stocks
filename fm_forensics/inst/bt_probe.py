"""T-INST-BT ⓪ مِجَسُّ توفّر (قبل العقد · لا رقمَ نتيجة): روابطُ مجموعات 13F في SEC وأعمدتُها · ملفّاتُ الإخفاق في التسليم (FTD: CUSIP↔رمز) ·
وحقلُ الأسهم القائمة من Polygon بتاريخ. لا يحسب ملكيّةً ولا مطابقةً ولا عائدًا."""
import io, json, os, re, sys, time, zipfile
import requests

UA = {"User-Agent": (os.environ.get("SEC_CONTACT") or "").strip() or "research probe"}
PAGES = ["https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets", "https://www.sec.gov/dera/data/form-13f-data-sets"]
FTD = ["https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data", "https://www.sec.gov/data/foiadocsfailsdatahtm"]


def get(u, **k):
    for i in range(3):
        try:
            r = requests.get(u, headers=UA, timeout=60, **k)
            if r.status_code == 200:
                return r
            print("  ", u, r.status_code)
        except Exception as e:                                   # noqa: BLE001
            print("  ", u, type(e).__name__)
        time.sleep(2 + 3 * i)
    return None


def links(pages, pat):
    for p in pages:
        r = get(p)
        if r is None:
            continue
        ls = sorted(set(re.findall(r'href="([^"]*' + pat + r'[^"]*)"', r.text)))
        print(f"📄 {p}: {len(ls)} رابطًا")
        if ls:
            return ["https://www.sec.gov" + x if x.startswith("/") else x for x in ls]
    return []


def main():
    z = links(PAGES, r"\.zip")
    for u in z:
        print("   ", u)
    if z:
        u = z[-1] if "2026" not in z[0] else z[0]
        cand = [x for x in z if "2026" in x] or z
        u = sorted(cand)[-1]
        r = get(u)
        if r is not None:
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            print(f"📦 {u} · {len(r.content)/1e6:.1f}MB · {zf.namelist()}")
            for n in zf.namelist():
                if n.lower().endswith(".tsv"):
                    with zf.open(n) as f:
                        head = f.readline().decode("utf-8", "replace").strip()
                        cnt = sum(1 for _ in f)
                    print(f"   {n}: {cnt} صفًّا · الأعمدة: {head[:400]}")
    f = links(FTD, r"cnsfails")
    print(f"📄 FTD: {len(f)} ملفًّا · أوّلها {f[:2]} · آخرها {f[-2:]}")
    if f:
        r = get(sorted(f)[-1])
        if r is not None:
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            txt = zf.read(zf.namelist()[0]).decode("latin-1")
            rows = [l.split("|") for l in txt.splitlines()[1:] if "|" in l]
            syms = {x[2] for x in rows if len(x) > 3}
            print(f"   {zf.namelist()[0]}: رأس {txt.splitlines()[0][:200]} · صفوف {len(rows)} · رموز {len(syms)}")
            nw = set(json.load(open("near_watch.json", encoding="utf-8")))
            print(f"   تغطيةُ «تحت المتابعة» ({len(nw)}) في هذا الملفّ الواحد: {len(nw & syms)}")
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    for s, d in (("ASTI", "2025-08-14"), ("FEMY", "2024-11-14")):
        r = requests.get(f"https://api.polygon.io/v3/reference/tickers/{s}", params={"date": d, "apiKey": key}, timeout=30)
        j = r.json().get("results", {}) if r.status_code == 200 else {}
        print(f"🏢 Polygon {s}@{d}: {r.status_code} · مفاتيح الأسهم: {[k for k in j if 'share' in k]} · cusip؟ {'cusip' in j}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
