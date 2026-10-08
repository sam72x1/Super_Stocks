"""Builds faisal_recovery/data/phase_a_inputs.json from measurements that cannot be recomputed in CI
(session transcript, uploads, scratch, GitHub API listings, Actions logs). Read-only on sources."""
import json, os, subprocess, collections, hashlib, datetime
REPO = '/home/user/Super_Stocks'
R = '/tmp/claude-0/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58/scratchpad/recovery'
SP = '/tmp/claude-0/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58/scratchpad/'
J = lambda p: json.load(open(p, encoding='utf-8'))
import sys as _s; _s.path.insert(0, REPO + '/faisal_method_v3')
import corpus_build as CB
def cbfp(path):
    f = CB.image_fingerprint(path)
    return {'dhash256': f['dhash256'], 'phash64': f['phash64']}
def rel_sp(p):
    if p is None: return None
    if p.startswith(SP): return 'scratchpad/' + p[len(SP):]
    if p.startswith(REPO + '/'): return p[len(REPO) + 1:]
    if '/uploads/' in p: return 'uploads/' + os.path.basename(p)
    return p
hr = J(R + '/h_repo.json'); ht = J(R + '/h_tr.json'); hs = J(R + '/h_scratch.json'); hu = J(R + '/h_up.json')
tr_by_sha = {v['sha256']: dict(v, **cbfp(p)) for p, v in ht.items()}
# seal-time re-extraction (tools/tr_extract.py → R/transcript2): the first pass must survive byte-for-byte in place
m1 = J(R + '/transcript_images_mapped.json')
CUTOFF = '2026-10-08T01:29:04Z'   # evidence cutoff = the artifact listing of the final runner probe (run 37713107882)
m_all = J(R + '/transcript2/_mapped.json')
m = [e for e in m_all if e['ts'][:19] + 'Z' <= CUTOFF]           # blocks after the cutoff are post-seal (none expected)
tmeta = J(R + '/transcript2/_meta.json')
_norm = lambda e: {k: v for k, v in e.items() if v is not None}
same = sum(1 for a, b in zip(m1, m) if _norm(a) == _norm(b))
assert same == len(m1) and len(m) >= len(m1), (same, len(m1), len(m))
for e in m:
    if e['sha256'] not in tr_by_sha:      # a block whose bytes were not in the first pass: fingerprint the re-extracted copy
        ext = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif'}[e['media']]
        q = R + '/transcript2/' + e['sha256'][:16] + '.' + ext
        from PIL import Image as _I
        _im = _I.open(q)
        tr_by_sha[e['sha256']] = dict(w=_im.size[0], h=_im.size[1], **cbfp(q))
blocks = []
for e in m:
    v = tr_by_sha[e['sha256']]
    blocks.append({'line': e['line'], 'ts': e['ts'], 'message_uuid': e['uuid'], 'role': e['role'], 'where': e['where'],
                   'tool': e.get('tool'), 'file_path': rel_sp(e.get('file_path')), 'sha256': e['sha256'], 'bytes': e['size'],
                   'media': e['media'], 'w': v['w'], 'h': v['h'], 'dhash256': v['dhash256'], 'phash64': v['phash64']})
# generator provenance for scratch groups (transcript line of the generating tool_use)
GEN = {'scratchpad/cid/': 8568, 'scratchpad/ex/pairs/': 10287, 'scratchpad/ex/nu/': 10423, 'scratchpad/pair_1880_2088.jpg': 11006,
       'scratchpad/rel/': 11118, 'scratchpad/rel2/': 11327, 'scratchpad/rel3/': 11408, 'scratchpad/check_1806_2049.jpg': 11545,
       'scratchpad/rel4/': 11819, 'scratchpad/rel5/': 12055, 'scratchpad/ex/kwm_top.jpg': 12739, 'scratchpad/ex/img0566.jpg': 12739}
SRC_OF = {'scratchpad/cid/': 'uploads/62cf5af8-image.jpg (corpus attachment)'}
scratch = {}
for p, v in sorted(hs.items()):
    rp = rel_sp(p)
    g = next((k for k in GEN if rp.startswith(k)), None)
    v = {k: v[k] for k in ('sha256', 'bytes', 'w', 'h')}
    v.update(cbfp(p))
    scratch[rp] = dict(v, generator_line=GEN.get(g) if g else None, derived_from=SRC_OF.get(g, 'faisal_images/ corpus files') if g else None)
# seal-time re-check of the scratchpad (outside recovery/) and of the uploads directory — by magic bytes, not by extension
_MAG = (b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"II*\x00", b"MM\x00*")
_files = _magic = 0
for _root, _dirs, _fs in os.walk(SP):
    if _root.startswith(SP + 'recovery'):
        continue
    for _f in _fs:
        _files += 1
        with open(os.path.join(_root, _f), 'rb') as _h:
            _hd = _h.read(12)
        _magic += any(_hd.startswith(m) for m in _MAG) or (_hd[:4] == b'RIFF' and _hd[8:12] == b'WEBP')
UPD = '/root/.claude/uploads'
_ups = [os.path.join(d, f) for d, _, fs in os.walk(UPD) for f in fs]
recheck_local = {'utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'scratch_files': _files, 'scratch_images_by_magic': _magic,
                 'uploads_files': len(_ups)}
assert _magic == len(hs) and len(_ups) == len(hu), (recheck_local, len(hs), len(hu))
_up_path, up = list(hu.items())[0]
uploads_current = [{'name': '62cf5af8-image.jpg', 'sha256': up['sha256'], 'bytes': up['bytes'], 'w': up['w'], 'h': up['h'], **cbfp(_up_path)}]
# git — seal-time re-measure on a full (unfiltered) mirror of every ref (remeasure/full.git)
RM = R + '/remeasure'
EXT = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.heic', '.heif')
mirror_refs = subprocess.run(['git', '-C', RM + '/full.git', 'for-each-ref', '--format=%(refname)'], capture_output=True, text=True).stdout.split()
otype = collections.Counter(); bbytes = 0
for ln in open(RM + '/full_objects.txt'):
    t_, _, sz = ln.split()
    otype[t_] += 1
    if t_ == 'blob':
        bbytes += int(sz)
scan = J(RM + '/blob_scan.json')
assert scan['blobs'] == otype['blob'] and scan['bytes'] == bbytes
img_magic = set(scan['magic'].get('jpeg', [])) | set(scan['magic'].get('png', [])) | set(scan['magic'].get('gif', [])) | set(scan['magic'].get('webp', []))
by_path = {}
for ln in open(RM + '/raw_all.txt', encoding='utf-8', errors='replace'):
    if not ln.startswith(':'):
        continue
    meta, path = ln.rstrip('\n').split('\t', 1)
    new = meta.split()[3]
    if set(new) != {'0'} and path.lower().endswith(EXT):
        by_path.setdefault(new, set()).add(path)
assert set(by_path) == img_magic, 'image blobs by magic != by path'
head_blobs = {l.split()[2] for l in subprocess.run(['git', '-C', RM + '/full.git', 'ls-tree', '-r', 'refs/heads/main'], capture_output=True, text=True).stdout.splitlines()}
old = []
for ln in open(R + '/old_path_blobs.txt', encoding='utf-8'):
    p, b = ln.split()
    blob = b.strip(',').split(',')[0]
    full = subprocess.run(['git', 'rev-parse', blob], cwd=REPO, capture_output=True, text=True).stdout.strip()
    data = subprocess.run(['git', 'cat-file', 'blob', full], cwd=REPO, capture_output=True).stdout
    sha = hashlib.sha256(data).hexdigest()
    head = [k for k, v in hr.items() if v['sha256'] == sha]
    old.append({'old_path': p, 'blob': full, 'sha256': sha, 'head_path': head[0] if head else None})
all_paths = {p for v in by_path.values() for p in v}
head_paths = {l.split('\t', 1)[1] for l in subprocess.run(['git', '-C', RM + '/full.git', 'ls-tree', '-r', 'refs/heads/main'], capture_output=True, text=True).stdout.splitlines()}
assert {o['old_path'] for o in old} == all_paths - head_paths, 'historical image paths changed'
git = {'mirror_refs_total': len(mirror_refs), 'branches': sum(1 for r in mirror_refs if r.startswith('refs/heads/')),
       'pull_heads': sum(1 for r in mirror_refs if r.startswith('refs/pull/') and r.endswith('/head')),
       'pull_merge_refs': sum(1 for r in mirror_refs if r.startswith('refs/pull/') and r.endswith('/merge')),
       'tags': sum(1 for r in mirror_refs if r.startswith('refs/tags/')),
       'objects_total': sum(otype.values()), 'commits': otype['commit'], 'trees': otype['tree'], 'blobs': otype['blob'],
       'blob_mb': round(bbytes / 1048576, 1), 'image_blobs_ever': len(img_magic), 'image_blobs_by_path': len(by_path),
       'magic_other': {k: len(v) for k, v in scan['magic'].items() if k not in ('jpeg', 'png', 'gif', 'webp')},
       'embedded_base64_image_blobs': len(scan['embedded']),
       'history_only_image_blobs': len(img_magic - head_blobs), 'image_paths_ever': len(all_paths), 'old_paths': old,
       'mirror_cloned_utc': datetime.datetime.utcfromtimestamp(os.path.getmtime(RM + '/full.git/HEAD')).strftime('%Y-%m-%dT%H:%M:%SZ'),
       'method': 'git clone --mirror (no filter) · git cat-file --batch-all-objects: magic bytes at offset 0 + base64 image '
                 'signatures inside every blob · git log --all -m --raw (paths)'}
# github text sources (pages listed 00:34Z + every PR/issue/comment created or updated since, fetched at seal time)
PAT = ['user-images.githubusercontent.com', 'github.com/user-attachments', 'private-user-images', '![', '<img']
def pages(prefix):
    out = []
    for f in sorted(os.listdir(R)):
        if f.startswith(prefix) and f.endswith('.json'):
            d = J(R + '/' + f); out += (d if isinstance(d, list) else d.get('items', []))
    return out
pulls = {x['number']: x for x in pages('pulls_') if 'number' in x}
pulls.update({x['number']: x for x in J(R + '/seal_pulls_recent.json')})
issues = {x['number']: x for x in pages('issues_') if 'number' in x}
icomments = {x['id']: x for x in pages('issues_comments_')}
icomments.update({x['id']: x for x in J(R + '/seal_issue_comments_recent.json')})
rcomments = {x['id']: x for x in pages('pulls_comments_')}
rcomments.update({x['id']: x for x in J(R + '/seal_review_comments_recent.json')})
rel = J(R + '/releases.json')
texts = [x.get('body') or '' for x in list(pulls.values()) + list(issues.values()) + list(icomments.values()) + list(rcomments.values()) + rel]
hits = sum(1 for t_ in texts if any(p_ in t_ for p_ in PAT))
gh = {'pulls': len(pulls), 'pull_review_comments': len(rcomments),
      'pure_issues': sum(1 for x in issues.values() if 'pull_request' not in x),
      'issue_comments': len(icomments), 'releases': len(rel), 'image_attachments_found': hits, 'patterns_searched': PAT,
      'refreshed_utc': datetime.datetime.utcfromtimestamp(os.path.getmtime(R + '/seal_pulls_recent.json')).strftime('%Y-%m-%dT%H:%M:%SZ')}
a2 = J(R + '/a2_keywords.json')
inputs = {
  'schema': 'phase_a_inputs/1', 'measured_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
  'main_commit_at_measure': subprocess.run(['git', 'rev-parse', 'origin/main'], cwd=REPO, capture_output=True, text=True).stdout.strip(),
  'git': git, 'github_text': gh,
  'transcript_current': {'file': 'session jsonl (this session, local)', 'first_ts': '2026-10-02T21:44:41.271Z', 'last_ts_at_measure': tmeta['last_ts'],
                         'lines_at_measure': tmeta['lines'], 'compaction_dropped_tokens': 146640486, 'image_blocks': len(blocks),
                         'recheck': {'first_pass_utc': '2026-10-08T00:41:40Z', 'first_pass_lines': 18215, 'first_pass_blocks': len(m1),
                                     'first_pass_blocks_identical': same, 'blocks_added_since': len(m) - len(m1),
                                     'cutoff_utc': CUTOFF, 'blocks_after_cutoff': len(m_all) - len(m),
                                     'note': 'a second context compaction (2026-10-08) left the local file intact'},
                         'unique_images': len({b['sha256'] for b in blocks}), 'blocks': blocks,
                         'human_messages': a2['human_msgs'], 'human_messages_with_image_blocks': a2['human_with_images'], 'a2_keyword_counts': a2['counts']},
  'uploads_current': uploads_current, 'scratch': scratch, 'local_recheck': recheck_local,
}
json.dump(inputs, open(REPO + '/faisal_recovery/data/phase_a_inputs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print('blocks', len(blocks), 'scratch', len(scratch), 'old', len(old), [o['head_path'] is None for o in old].count(True), gh, {k: v for k, v in git.items() if k not in ('old_paths', 'method')})
