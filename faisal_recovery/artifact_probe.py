"""🔎 مِجَسُّ صور الـartifacts — PHASE A (FAISAL MASTER FORENSIC RECOVERY · A1/A3).

قراءةٌ فقط: يسرد كلَّ artifact حيٍّ في المستودع ⟵ ينزّل كلَّ واحدٍ إلى ملفٍّ مؤقّت ⟵ يفحص كلَّ مُدخَلٍ في الأرشيف
بتوقيعه (لا بامتداده) ⟵ لكلّ صورة: SHA256 والأبعاد وdHash/pHash ⟵ يقارنها بصور المستودع (SHA ثمّ أقربُ بصمة).
لا تلغرام · لا كتابةَ حالة · لا git · لا رفعَ artifact. المخرَجُ سطورٌ في السجلّ تبدأ بـ`APROBE` وكتلةُ JSON أخيرة.

لماذا على رنر: تنزيلُ الـartifact يُحوَّل إلى blob.core.windows.net والحاوية تحجبه (403 على CONNECT) ⟵ المصدرُ
«PARTIALLY_ACCESSIBLE» من الجلسة و«FULLY_ACCESSIBLE» من الرنر بـGITHUB_TOKEN (actions: read).
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

MAGIC = (
    (b"\xff\xd8\xff", "jpeg"), (b"\x89PNG\r\n\x1a\n", "png"), (b"GIF87a", "gif"), (b"GIF89a", "gif"),
    (b"BM", "bmp"), (b"II*\x00", "tiff"), (b"MM\x00*", "tiff"),
)


def sniff(head):
    """نوعُ الصورة من التوقيع أو None. نقيّة."""
    for sig, kind in MAGIC:
        if head.startswith(sig):
            return kind
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypavif"):
        return "heif"
    return None


def fingerprints(data):
    """(w, h, dhash64, phash64) أو Nones — Pillow/numpy من requirements.txt."""
    try:
        import numpy as np
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
        w, h = im.size
        g = im.convert("L")
        d = np.asarray(g.resize((9, 8), Image.LANCZOS), dtype=float)
        dh = (d[:, 1:] > d[:, :-1]).flatten()
        n = 32
        k = np.arange(n)[:, None]
        i = np.arange(n)[None, :]
        m = np.cos(np.pi * (2 * i + 1) * k / (2 * n))
        m[0] *= 1 / np.sqrt(2)
        m *= np.sqrt(2 / n)
        p = np.asarray(g.resize((n, n), Image.LANCZOS), dtype=float)
        low = (m @ p @ m.T)[:8, :8].flatten()
        ph = low > np.median(low[1:])
        hx = lambda bits: "%016x" % int("".join("1" if x else "0" for x in bits), 2)  # noqa: E731
        return w, h, hx(dh), hx(ph)
    except Exception:                                      # noqa: BLE001
        return None, None, None, None


def ham(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def repo_images(root="."):
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout.split("\n")
    rows = {}
    for p in out:
        if not p:
            continue
        q = os.path.join(root, p)
        try:
            with open(q, "rb") as f:
                b = f.read()
        except OSError:
            continue
        if sniff(b[:16]) is None:
            continue
        w, h, dh, ph = fingerprints(b)
        rows[hashlib.sha256(b).hexdigest()] = {"path": p, "w": w, "h": h, "dhash": dh, "phash": ph}
    return rows


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):                    # نلتقط العنوانَ ونطلبه بلا Authorization
        return None


def _api(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                               "Accept": "application/vnd.github+json",
                                               "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def list_artifacts(repo, token):
    arts, page = [], 1
    while True:
        d = _api(f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={page}", token)
        batch = d.get("artifacts", [])
        arts += batch
        if len(batch) < 100:
            return arts, d.get("total_count")
        page += 1


def download(url, token, dest):
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                               "Accept": "application/vnd.github+json"})
    try:
        opener.open(req, timeout=60)
        raise RuntimeError("no redirect")
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307, 308):
            raise
        loc = e.headers["Location"]
    with urllib.request.urlopen(urllib.request.Request(loc), timeout=600) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def scan_zip(path, repo_rows):
    """لكلّ مُدخَل: هل هو صورة؟ وإن كانت: في المستودع بالـSHA؟ وإلّا أقربُ صورةٍ فيه. نقيّة على الملفّ."""
    res = {"entries": 0, "images": 0, "in_repo": 0, "not_in_repo": [], "ext_image_not_magic": 0, "bad_zip": False}
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        res["bad_zip"] = True
        return res
    with z:
        for info in z.infolist():
            if info.is_dir():
                continue
            res["entries"] += 1
            with z.open(info) as f:
                head = f.read(16)
            kind = sniff(head)
            if kind is None:
                if info.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".tif", ".tiff")):
                    res["ext_image_not_magic"] += 1
                continue
            data = z.read(info)
            res["images"] += 1
            sha = hashlib.sha256(data).hexdigest()
            if sha in repo_rows:
                res["in_repo"] += 1
                continue
            w, h, dh, ph = fingerprints(data)
            near = None
            if dh and ph:
                best = min(((ham(dh, r["dhash"]) + 2 * ham(ph, r["phash"]), r["path"], ham(dh, r["dhash"]), ham(ph, r["phash"]))
                            for r in repo_rows.values() if r["dhash"]), default=None)
                if best:
                    near = {"path": best[1], "dhash_d": best[2], "phash_d": best[3]}
            res["not_in_repo"].append({"entry": info.filename, "kind": kind, "bytes": len(data), "sha256": sha,
                                       "w": w, "h": h, "dhash": dh, "phash": ph, "nearest": near})
    return res


def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    rows = repo_images(".")
    print(f"APROBE repo_images={len(rows)}", flush=True)
    arts, total = list_artifacts(repo, token)
    print(f"APROBE artifacts_listed={len(arts)} total_count={total}", flush=True)
    summary = {"repo_images": len(rows), "artifacts_listed": len(arts), "total_count": total,
               "expired": 0, "downloaded": 0, "failed": [], "per_artifact": [], "not_in_repo": []}
    tmpd = tempfile.mkdtemp()
    for a in sorted(arts, key=lambda x: x["id"]):
        if a.get("expired"):
            summary["expired"] += 1
            continue
        dest = os.path.join(tmpd, f"{a['id']}.zip")
        try:
            download(a["archive_download_url"], token, dest)
        except Exception as e:                              # noqa: BLE001
            summary["failed"].append({"id": a["id"], "name": a["name"], "err": f"{type(e).__name__}: {e}"[:200]})
            print(f"APROBE FAIL id={a['id']} name={a['name']} err={type(e).__name__}", flush=True)
            continue
        summary["downloaded"] += 1
        r = scan_zip(dest, rows)
        os.remove(dest)
        rec = {"id": a["id"], "name": a["name"], "created": a["created_at"], "run": (a.get("workflow_run") or {}).get("id"),
               "size": a["size_in_bytes"], "entries": r["entries"], "images": r["images"], "in_repo": r["in_repo"],
               "not_in_repo": len(r["not_in_repo"]), "ext_image_not_magic": r["ext_image_not_magic"], "bad_zip": r["bad_zip"]}
        summary["per_artifact"].append(rec)
        for x in r["not_in_repo"]:
            summary["not_in_repo"].append(dict(x, artifact_id=a["id"], artifact=a["name"], created=a["created_at"]))
        if r["images"] or r["bad_zip"]:
            print("APROBE ART " + json.dumps(rec, ensure_ascii=False), flush=True)
    imgs = sum(x["images"] for x in summary["per_artifact"])
    inr = sum(x["in_repo"] for x in summary["per_artifact"])
    uniq_new = sorted({x["sha256"] for x in summary["not_in_repo"]})
    summary["totals"] = {"image_entries": imgs, "in_repo": inr, "not_in_repo_entries": len(summary["not_in_repo"]),
                         "not_in_repo_unique_sha": len(uniq_new),
                         "artifacts_with_images": sum(1 for x in summary["per_artifact"] if x["images"])}
    for x in summary["not_in_repo"]:
        print("APROBE NEW " + json.dumps(x, ensure_ascii=False), flush=True)
    print("APROBE TOTALS " + json.dumps(summary["totals"], ensure_ascii=False), flush=True)
    print("APROBE FAILED " + json.dumps(summary["failed"], ensure_ascii=False), flush=True)
    print("APROBE_JSON_BEGIN")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_artifact"}, ensure_ascii=False))
    print("APROBE_JSON_END")
    return 0 if not summary["failed"] else 3


if __name__ == "__main__":
    sys.exit(main())
