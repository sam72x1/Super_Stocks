"""Re-extracts every base64 image block of this session's transcript (line · role · ts · uuid · sha256 · size · media ·
where · tool · file_path) and writes the decoded bytes to OUTDIR/<sha16>.<ext>. Read-only on the transcript."""
import json, hashlib, base64, os, sys
T = '/root/.claude/projects/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58.jsonl'
OUT = sys.argv[1]
tool_of = {}          # tool_use_id -> (name, file_path)
res = []
last_ts, nlines = None, 0
with open(T, encoding='utf-8') as f:
    for ln, l in enumerate(f, 0):        # 0-based line numbers — the convention of the first pass (S14 IMAGE_IDs)
        nlines = ln + 1
        try:
            d = json.loads(l)
        except Exception:
            continue
        last_ts = d.get('timestamp') or last_ts
        msg = d.get('message') or {}
        content = msg.get('content')
        if not isinstance(content, list):
            continue
        for i, c in enumerate(content):
            if not isinstance(c, dict):
                continue
            if c.get('type') == 'tool_use':
                inp = c.get('input') or {}
                tool_of[c.get('id')] = (c.get('name'), inp.get('file_path'))
            def emit(img, where, tool=None, fp=None):
                src = img.get('source') or {}
                if src.get('type') != 'base64':
                    return
                b = base64.b64decode(src.get('data') or '')
                sha = hashlib.sha256(b).hexdigest()
                ext = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif'}.get(src.get('media_type'), 'bin')
                p = os.path.join(OUT, sha[:16] + '.' + ext)
                if not os.path.exists(p):
                    open(p, 'wb').write(b)
                e = {'line': ln, 'role': msg.get('role'), 'ts': d.get('timestamp'), 'uuid': d.get('uuid'), 'sha256': sha,
                     'size': len(b), 'media': src.get('media_type'), 'where': where}
                if tool is not None or fp is not None:
                    e['tool'] = tool; e['file_path'] = fp
                res.append(e)
            if c.get('type') == 'image':
                emit(c, f'/content[{i}]')
            elif c.get('type') == 'tool_result' and isinstance(c.get('content'), list):
                name, fp = tool_of.get(c.get('tool_use_id'), (None, None))
                for j, cc in enumerate(c['content']):
                    if isinstance(cc, dict) and cc.get('type') == 'image':
                        emit(cc, f'/content[{i}]/content[{j}]', name, fp)
json.dump(res, open(os.path.join(OUT, '_mapped.json'), 'w'), ensure_ascii=False, indent=0)
json.dump({'lines': nlines, 'last_ts': last_ts}, open(os.path.join(OUT, '_meta.json'), 'w'))
print('blocks', len(res), 'unique', len({e['sha256'] for e in res}))
