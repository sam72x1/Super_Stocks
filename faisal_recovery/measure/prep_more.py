"""Augments faisal_recovery/data/phase_a_inputs.json (repo non-corpus images · collector accounting · sessions) and writes
faisal_recovery/data/artifact_probe_result.json from the two probe runs' logs (values transcribed from APROBE lines)."""
import json, os, subprocess, hashlib, sys
REPO = '/home/user/Super_Stocks'
R = '/tmp/claude-0/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58/scratchpad/recovery'
sys.path.insert(0, REPO + '/faisal_method_v3')
import corpus_build as CB
P = REPO + '/faisal_recovery/data/phase_a_inputs.json'
inp = json.load(open(P, encoding='utf-8'))
git = lambda *a: subprocess.run(['git', *a], cwd=REPO, capture_output=True, text=True, check=True).stdout
# 1) repository images outside faisal_images/
other = []
for p in git('ls-files').split('\n'):
    if not p or p.startswith('faisal_images/') or not p.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        continue
    f = CB.image_fingerprint(os.path.join(REPO, p))
    sha = hashlib.sha256(open(os.path.join(REPO, p), 'rb').read()).hexdigest()
    if p.startswith('faisal_method_v3/v31/overlays/'):
        prov = 'V3.1 overlay render committed by faisal_method_v3 (tool chart from market data)'
    elif p.startswith('faisal_method_v4/overlays/'):
        prov = 'V4 overlay render committed by faisal_method_v4 (tool chart from market data)'
    elif p == 'operating_standard_v1.jpg':
        prov = 'owner image of the operating standard v1.0 (archived 2026-08-27; instructions, not market material)'
    else:
        prov = 'UNCLASSIFIED'
    other.append({'path': p, 'sha256': sha, 'w': f['width'], 'h': f['height'], 'dhash256': f['dhash256'], 'phash64': f['phash64'], 'provenance': prov})
assert not [o for o in other if o['provenance'] == 'UNCLASSIFIED'], [o['path'] for o in other if o['provenance'] == 'UNCLASSIFIED']
inp['repo_other_images'] = sorted(other, key=lambda o: o['path'])
# 2) collector accounting (state-history diff per collector commit + the run log / report that classifies it)
RUNS = [  # (state commit, run id, saved, dup_sha, seen_same_fid, perm_failed, evidence)
    ('a182c19ae', '30284432386', 308, 0, 0, 0, 'state diff: +308 file ids = +308 files'),
    ('2bf33dcde', '30328943359', 51, 47, 0, 0, 'job log 90179930019 «حُفِظت 51 · مكرّرة متخطّاة 47» · no ⛔ line · numbers not recorded'),
    ('b56f74134', '30329396971', 2, 93, 0, 0, 'job log 90181235164 «حُفِظت 2 · مكرّرة متخطّاة 93» · no ⛔ line'),
    ('05524b7ae', '30330117413', 1, 95, 0, 0, 'job log 90183286025 «حُفِظت 1 · مكرّرة متخطّاة 95» · 25 pairs printed + 70 · no ⛔ line'),
    ('36f472b4a', '30367399645', 9, 68, 0, 0, 'job log 90302093420: matched list 25 + 43 · no ⛔ line'),
    ('d3f07c567', '30370108316', 0, 0, 82, 0, 'telegram_collect_report.md @ d3f07c567 «وصلت بمعرّف سبق تنزيله: 82»'),
    ('f4039e67f', '35836473245', 32, 0, 0, 0, 'report @ f4039e67f'),
    ('64383f957', '35856019567', 17, 0, 0, 0, 'report @ 64383f957'),
    ('af79a3b89', '36778969767', 37, 2, 0, 0, 'report @ af79a3b89 (matched table)'),
    ('28d31b2bb', '36824129826', 17, 1, 0, 0, 'report @ 28d31b2bb (matched table)'),
    ('e939785e0', '36996073993', 11, 0, 0, 0, 'report @ e939785e0'),
    ('dad514a50', '37616553357', 46, 2, 0, 0, 'report @ dad514a50 (matched table) + telegram_collect_meta.jsonl rows'),
]
MATCHED = {2371: 'TG_2048', 2372: 'TG_2054', 2373: 'TG_2053', 2374: 'TG_2058', 2378: 'TG_2060', 2379: 'TG_2059', 2380: 'TG_2064',
           2381: 'TG_2063', 2382: 'TG_2062', 2383: 'TG_2067', 2384: 'TG_2066', 2385: 'TG_2065', 2386: 'TG_2070', 2387: 'TG_2069',
           2388: 'TG_2068', 2389: 'TG_2073', 2390: 'TG_2072', 2391: 'TG_2071', 2392: 'TG_2076', 2393: 'TG_2075', 2395: 'TG_2079',
           2396: 'TG_2078', 2397: 'TG_2077', 2398: 'TG_2082', 2399: 'TG_2081',
           2497: 'TG_1968', 2498: 'TG_1967', 2499: 'TG_1966', 2500: 'TG_1965', 2501: 'TG_1964', 2502: 'TG_1972', 2503: 'TG_1971',
           2504: 'TG_1970', 2505: 'TG_1975', 2506: 'TG_1974', 2507: 'TG_1973', 2508: 'TG_1977', 2509: 'TG_1976',
           57895: 'TG_50818', 57896: 'TG_50817', 57920: 'TG_50592', 58424: 'TG_58052', 58425: 'TG_58051'}
def tg_files(c):
    out = git('ls-tree', '--name-only', c, 'faisal_images/').split()
    return set(int(x.split('/')[-1][3:].split('.')[0]) for x in out if x.split('/')[-1].startswith('TG_') and x.split('/')[-1][3:].split('.')[0].isdigit())
commits = git('log', '--reverse', '--format=%h', '--', 'telegram_collect_state.json').split()
prev_m, prev_f, acc = set(), set(), []
runinfo = {r[0]: r for r in RUNS}
for c in commits:
    st = json.loads(git('show', f'{c}:telegram_collect_state.json'))
    m = set(int(x) for x in st.get('seen_msg_ids', []))
    f = tg_files(c)
    new = sorted((m - prev_m) - f) if prev_m or c != 'b0bca926b' else []
    if c == 'b0bca926b':        # back-fill commit: seen_msg_ids seeded from the 359 saved files only
        new = sorted((m - prev_m) - f)
        assert not new, new
    ts = git('log', '-1', '--format=%aI', c).strip()
    for msg in new:
        ri = runinfo[c]
        basis = ('same Telegram file id as an earlier saved message (collector «seen» path)' if ri[4] else
                 'collector SHA256 match on receipt (content identical to a saved corpus file)')
        acc.append({'msg': msg, 'state_commit': c, 'state_commit_utc': ts, 'run': ri[1],
                    'evidence': f'collector run {ri[1]} · {ri[6]}', 'basis': basis, 'matched': MATCHED.get(msg)})
    prev_m, prev_f = m, f
st_now = json.load(open(REPO + '/telegram_collect_state.json', encoding='utf-8'))
tg_now = tg_files('HEAD')
runs_total = 25          # every telegram_collect.yml run up to the evidence cutoff (API total_count at 01:41Z = 25 before the verification drain)
CUTOFF = '2026-10-08T01:29:04Z'   # evidence cutoff = the artifact listing of the final runner probe (run 37713107882)
VERIFY = json.load(open(R + '/cutoff_verification.json'))   # the collector run dispatched after the cutoff (bot queue proof)
inp['collector'] = {
    'runs_total': runs_total, 'run_failures': 0, 'saved_tg_files': len(tg_now), 'accounted_not_saved': len(acc),
    'dup_numbers_lost': 47, 'dup_lost_run': '30328943359', 'dup_lost_utc': '2026-07-28T04:32:17+00:00',
    'dup_lost_evidence': 'job log 90179930019 «مكرّرة متخطّاة 47» (numbers not recorded — commit b0bca926b explains)',
    'image_messages_total': len(tg_now) + len(acc) + 47, 'state_seen_msg_ids': len(st_now['seen_msg_ids']),
    'state_seen_file_ids': len(st_now['seen_file_ids']), 'pending_at_last_run': len(st_now.get('pending') or {}),
    'last_run_id': '37712531520', 'last_run_utc': '2026-10-08T01:21:39Z',
    'pre_seal_drain': {'run': '37712531520', 'utc': '2026-10-08T01:21:39Z', 'saved': 0, 'pending': 0, 'offset': st_now['offset'],
                       'offset_since': 'collector run 37616553357 (state commit dad514a50)'},
    'cutoff_verification': VERIFY,
    'runs': [{'run': r[1], 'state_commit': r[0], 'saved': r[2], 'dup_sha': r[3], 'seen_same_file_id': r[4], 'perm_failed': r[5], 'evidence': r[6]} for r in RUNS],
    'accounted_records': acc,
}
assert len(acc) == 343, len(acc)
assert set(st_now['seen_msg_ids']) >= {a['msg'] for a in acc}
# 3) sessions (metadata only; non-project titles withheld)
proj = [('session_01LBuXeYuQbmaEjVK9gwExgJ', 'SuperStock', '2026-06-21', '2026-06-23'), ('session_01CGxGCcG2D7Jfsna2FANqcc', 'Untitled session', '2026-06-21', '2026-06-22'),
        ('session_01NrobUVQrryf7xwVCDn7eAG', 'SuperStock2', '2026-06-21', '2026-06-23'), ('session_011pToVTt77eUANJWXi6FMvp', 'الارتكاز', '2026-06-23', '2026-09-06'),
        ('session_01KLd16AiYNzCDjAAT3d6sm9', 'المضاربة', '2026-06-23', '2026-08-05'), ('session_01UZMKjWjEFymBYQ6QjFKSFt', 'Bot modification idea', '2026-06-25', '2026-06-25'),
        ('session_01BEBReSRgih9ebMom6Upm5m', 'الجديد', '2026-06-25', '2026-08-05'), ('session_012dsDeXUZSyy4JYhiKQnntd', 'Untitled session', '2026-06-29', '2026-06-29'),
        ('session_018aioFVc46yPAR6KFZ69DTm', 'Super_StocksX Repairs', '2026-07-28', '2026-07-28'), ('session_01Xw8z2q8AUrDewbDTXM823S', 'Super_Stocks Deep Audit', '2026-07-28', '2026-07-29'),
        ('session_018TBM4ZyBAHuHrWxxRWaJYr', 'الارتكاز 2', '2026-09-05', '2026-09-09'), ('session_01SLEcBtTzC7yfFzWH1q1ZeY', 'this session', '2026-09-06', 'now')]
inp['sessions'] = {'project_related': len(proj) - 1, 'other': 4, 'this_session_counted_as': 'S14/S15',
                   'project_sessions': [{'id': a, 'title': b, 'created': c, 'updated': d} for a, b, c, d in proj if b != 'this session']}
json.dump(inp, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
# 4) probe result
loc = json.load(open(R + '/artifact_local_digests.json'))
def tree_manifest(c):
    lines = []
    for l in git('ls-tree', '-r', c, 'faisal_images/').splitlines():
        meta, path = l.split('\t', 1)
        data = subprocess.run(['git', 'cat-file', 'blob', meta.split()[2]], cwd=REPO, capture_output=True).stdout
        if data[:3] == b'\xff\xd8\xff' or data[:4] in (b'\x89PNG', b'GIF8') or data[:4] == b'RIFF':
            lines.append((path, hashlib.sha256(data).hexdigest()))
    return sorted(lines)
ART = [  # transcribed from APROBE ART lines of the final probe run 37713107882 (job 113103342736) — the first 11 are identical in runs 37709696440/37710659884
    (11144247490, 'faisal-images', '2026-10-01T06:20:05Z', '36824129826', 708, '52c45e05d514c03492daa37fa5335f9f57be0c082963a5588c67d4b425dcd48c'),
    (11147553730, 'faisal-images', '2026-10-01T08:05:46Z', '36834148239', 708, '52c45e05d514c03492daa37fa5335f9f57be0c082963a5588c67d4b425dcd48c'),
    (11222075486, 'faisal-images', '2026-10-02T10:33:44Z', '36996073993', 722, 'f92695ae67990a39069d3e1fdcac88bdc7232e3c617fcdbec72befd2d6f708e8'),
    (11224063931, 'faisal-v3-cases', '2026-10-02T11:41:34Z', '37002345242', 4, '764cfd0695aca1353fdd16cadbf2f64952adf01abc34debc8c0b2f44b222979f'),
    (11225486148, 'faisal-v3-cases', '2026-10-02T12:01:29Z', '37004211584', 4, '764cfd0695aca1353fdd16cadbf2f64952adf01abc34debc8c0b2f44b222979f'),
    (11236517398, 'faisal-images', '2026-10-02T15:45:39Z', '37029151586', 722, 'f92695ae67990a39069d3e1fdcac88bdc7232e3c617fcdbec72befd2d6f708e8'),
    (11452537419, 'faisal-images', '2026-10-07T00:13:08Z', '37550748477', 722, 'f92695ae67990a39069d3e1fdcac88bdc7232e3c617fcdbec72befd2d6f708e8'),
    (11474986552, 'faisal-images', '2026-10-07T10:11:38Z', '37605684975', 722, 'f92695ae67990a39069d3e1fdcac88bdc7232e3c617fcdbec72befd2d6f708e8'),
    (11480211284, 'faisal-images', '2026-10-07T11:49:24Z', '37616553357', 768, 'd298e84004b7ec3b1fe701eff5530c34c2739a627b5606b175ff3c3abde350ba'),
    (11497795532, 'faisal-images', '2026-10-07T16:30:26Z', '37652483700', 768, 'd298e84004b7ec3b1fe701eff5530c34c2739a627b5606b175ff3c3abde350ba'),
    (11514777420, 'faisal-images', '2026-10-07T22:16:20Z', '37695016642', 768, 'd298e84004b7ec3b1fe701eff5530c34c2739a627b5606b175ff3c3abde350ba'),
    (11522078996, 'faisal-images', '2026-10-08T01:22:18Z', '37712531520', 768, 'd298e84004b7ec3b1fe701eff5530c34c2739a627b5606b175ff3c3abde350ba'),
]
NEW = [  # APROBE NEW lines (identical in both runs)
    ('case_DXST.png', 13169, 'e71a9aae38a529371ff905bc9220b38cdcb4a145eb05eb52d4edfd63902ce18e', 'faisal_method_v3/v31/overlays/DXST_2026-06-15_daily.png', 0, 2),
    ('case_EZRA.png', 15397, '8e539e1670ea8803ae87d9094d022379d03afbb51ed2d684028d2ddb3079b5f5', 'faisal_method_v3/v31/overlays/RAYA_2026-08-21_daily.png', 10, 16),
    ('case_RAYA.png', 15799, '1412e18a92fec8eaaa28fa21a839422cecdbefdccfd2dde2240f1603e8448ea7', 'faisal_method_v3/v31/overlays/RAYA_2026-08-26_daily.png', 5, 2),
    ('case_VEEE.png', 14707, '6ef48bb1604fdcb704c6dc252d2f88e3cdc8bcdc582a289faa2cd40b0ec3e8fc', 'faisal_method_v3/v31/overlays/RAYA_2026-08-26_daily.png', 15, 18),
]
manifests, arts = {}, []
for aid, name, created, run, n, dig in ART:
    a = {'id': aid, 'name': name, 'created': created, 'run': run, 'images': n, 'manifest_digest': dig}
    if name == 'faisal-images':
        c = loc[run]['commit']
        a['tree_commit'] = c
        a['digest_match'] = loc[run]['digest'] == dig
        assert a['digest_match'], (aid, run)
        if dig not in manifests:
            tm = tree_manifest(c)
            assert hashlib.sha256('\n'.join(f'{p}\t{s}' for p, s in tm).encode()).hexdigest() == dig
            manifests[dig] = tm
    else:
        a['not_in_repo'] = [{'entry': e, 'bytes': b, 'sha256': s, 'w': 1100, 'h': 600, 'nearest': {'path': p, 'dhash_d': d1, 'phash_d': d2}}
                            for e, b, s, p, d1, d2 in NEW]
    arts.append(a)
_listed = [x for x in json.load(open(R + '/artifacts_all_seal.json')) if x['created_at'] <= CUTOFF]
assert len(_listed) == 925, len(_listed)          # = the probe's artifacts_listed / total_count at the cutoff
probe = {'schema': 'artifact_probe_result/2', 'runs': ['37709696440', '37710659884', '37713107882'],
         'jobs': ['113092446613', '113095575029', '113103342736'], 'final_run': '37713107882', 'listed_at_utc': CUTOFF,
         'probe_script': 'faisal_recovery/artifact_probe.py', 'artifacts_listed': 925, 'downloaded': 925, 'failed': 0, 'expired_listed': 0,
         'oldest_created': min(x['created_at'] for x in _listed), 'newest_created': max(x['created_at'] for x in _listed),
         'totals': {'image_entries': 7384, 'in_repo': 7376, 'not_in_repo_entries': 8, 'not_in_repo_unique_sha': 4, 'artifacts_with_images': 12},
         'artifacts_with_images': arts, 'tree_manifests': manifests}
assert sum(a['images'] for a in arts) == 7384
json.dump(probe, open(REPO + '/faisal_recovery/data/artifact_probe_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
print('other', len(other), 'acc', len(acc), 'collector total', inp['collector']['image_messages_total'], 'manifests', {k[:8]: len(v) for k, v in manifests.items()})
