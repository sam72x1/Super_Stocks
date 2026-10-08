"""Streams every blob of a full mirror and reports (a) image/PDF/archive magic at offset 0, (b) embedded base64 image
signatures inside text. Read-only. Usage: blob_scan.py <mirror.git> <out.json>"""
import subprocess, sys, json, re
G, OUT = sys.argv[1], sys.argv[2]
MAGIC = [(b"\xff\xd8\xff", "jpeg"), (b"\x89PNG\r\n\x1a\n", "png"), (b"GIF87a", "gif"), (b"GIF89a", "gif"), (b"BM", "bmp?"),
         (b"II*\x00", "tiff"), (b"MM\x00*", "tiff"), (b"%PDF", "pdf"), (b"PK\x03\x04", "zip"), (b"\x1f\x8b", "gzip")]
SIG = re.compile(rb"data:image/|iVBORw0KGgo|/9j/4AAQ|/9j/4QA|R0lGODlh|R0lGODdh|UklGR[A-Za-z0-9+/]{3}XRUJQ")
p = subprocess.Popen(["git", "-C", G, "cat-file", "--batch", "--batch-all-objects", "--unordered"], stdout=subprocess.PIPE)
f = p.stdout
res = {"blobs": 0, "bytes": 0, "magic": {}, "embedded": {}}
while True:
    hdr = f.readline()
    if not hdr:
        break
    oid, typ, size = hdr.split()
    size = int(size)
    data = f.read(size)
    f.read(1)
    if typ != b"blob":
        continue
    res["blobs"] += 1
    res["bytes"] += size
    head = data[:16]
    kind = None
    for sig, k in MAGIC:
        if head.startswith(sig):
            kind = k
            break
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        kind = "webp"
    if head[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypavif"):
        kind = "heif"
    if kind == "bmp?" and not (size > 26 and int.from_bytes(data[2:6], "little") == size):
        kind = None          # «BM» text prefix, not a bitmap header
    if kind:
        res["magic"].setdefault(kind, []).append(oid.decode())
    elif SIG.search(data):
        res["embedded"].setdefault(oid.decode(), [m.group(0).decode() for m in SIG.finditer(data)][:5])
p.wait()
json.dump(res, open(OUT, "w"), indent=0)
print("blobs", res["blobs"], "MB", round(res["bytes"] / 1048576, 1), {k: len(v) for k, v in res["magic"].items()}, "embedded", len(res["embedded"]))
