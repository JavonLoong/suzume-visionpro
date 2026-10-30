"""Read-only cleanup planner. Deletion is performed separately in PowerShell."""
import collections, hashlib, json, re
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent
WORKSPACE = ROOT.parent
CHAR = ROOT / 'character-hunyuan-v1'
manifest = json.loads((AUDIT / 'remote-publication-manifest.json').read_text(encoding='utf-8'))
remote = {x['path']: x for x in manifest['files']}
tree = json.loads((AUDIT / 'remote-tree.json').read_text(encoding='utf-8'))
git_files = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
release = json.loads((AUDIT / 'remote-release.json').read_text(encoding='utf-8'))
assets = {a['name']: a for a in release['assets']}
for a in manifest['archives']:
    assert assets[a['name']]['digest'] == 'sha256:' + a['sha256']
    assert assets[a['name']]['size'] == a['bytes']

offline = json.loads((CHAR / '离线HTML/最新版打包清单.json').read_text(encoding='utf-8'))
test = json.loads((CHAR / '离线HTML/验证/铃芽之旅_v56_最新双场景_离线.html.json').read_text(encoding='utf-8'))
assert test['passed'] and not test['requests'] and not test['errors'] and not test['consoleErrors']
protected = {str((CHAR / p).resolve()).casefold() for p in offline['resources']}
# Required by the current v56 geometry verification script.
protected.update(str((CHAR / 'poster-railings-v46' / name).resolve()).casefold()
                 for name in ['original-ivy-matrices-v46.bin', 'original-ivy-colors-v46.bin'])
for dep in json.loads((AUDIT / 'blend-dependencies.json').read_text(encoding='utf-8')):
    protected.add(str(Path(dep['file']).resolve()).casefold())
    protected.update(str(Path(p).resolve()).casefold() for p in dep['externalPaths'])

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def backup(path, digest):
    key = path.relative_to(WORKSPACE).as_posix()
    row = remote.get(key)
    if not row or row['bytes'] != path.stat().st_size or row['sha256'] != digest:
        return None
    if row['storage'] == 'git':
        if key not in git_files:
            return None
        b = path.read_bytes()
        if hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() != git_files[key]['sha']:
            return None
        return f"https://github.com/JavonLoong/suzume-visionpro/blob/{tree['sha']}/{key}"
    return assets[row['storage']]['browser_download_url'] + '#entry=' + key

rows = []
skipped = []
for p in ROOT.rglob('*'):
    if not p.is_file() or p.is_symlink():
        continue
    rel = p.relative_to(ROOT)
    if rel.parts[0] in ['visionpro', AUDIT.name]:
        continue
    if str(p.resolve()).casefold() in protected:
        continue
    reason = None
    # Retain the latest scene folder, including source data and localisation tools.
    if 'poster-right-bow-v56' in rel.parts and p.suffix != '.blend1':
        continue
    if p.suffix == '.blend':
        reason = '旧版 Blender 场景（已由 v56 替代）'
    elif p.suffix == '.blend1':
        primary = p.with_suffix('.blend')
        if not primary.is_file() or p.stat().st_mtime > primary.stat().st_mtime:
            skipped.append({'path': str(p), 'reason': '自动备份比主文件新或主文件缺失'})
            continue
        primary_hash = sha(primary)
        evidence = backup(primary, primary_hash)
        if not evidence:
            skipped.append({'path': str(p), 'reason': '主文件未通过远端备份核对'})
            continue
        rows.append({'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': sha(p),
                     'reason': '早于已备份主文件的 Blender 自动保存副本',
                     'backup': None, 'supersededBy': str(primary), 'primaryBackup': evidence})
        continue
    elif rel.parts[0].startswith('reconstruction'):
        reason = '早期重建输出'
    elif '离线HTML' in rel.parts:
        if p.suffix == '.html' and p.name != offline['file']:
            reason = '旧版离线预览（已由验证通过的最新版双场景 HTML 替代）'
    elif len(rel.parts) >= 3 and rel.parts[1] == 'viewer':
        if rel.parts[2] == 'character-v37':
            continue  # latest movie character, includes a useful downloadable GLB
        if p.name in ['index.html', 'three.min.js', 'GLTFLoader.js', 'RectAreaLightUniformsLib.js']:
            continue
        reason = '旧版网页及其人物导出副本'
    elif len(rel.parts) >= 3 and re.match(r'(poster|movie|night)-.*v\d+$', rel.parts[1]):
        if p.suffix in {'.png', '.jpg', '.jpeg', '.bin', '.npz', '.npy', '.glb'}:
            reason = '旧版非运行依赖的渲染和中间几何输出'
        elif p.suffix == '.json' and p.stat().st_size > 1_000_000:
            reason = '旧版中间几何数据'
    if not reason:
        continue
    digest = sha(p)
    evidence = backup(p, digest)
    if not evidence:
        skipped.append({'path': str(p), 'reason': '本地内容未在远端清单中找到相同哈希，保留'})
        continue
    rows.append({'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': digest,
                 'reason': reason, 'backup': evidence})

for row in json.loads((AUDIT / 'verified-release-copies.json').read_text(encoding='utf-8')):
    # Keep the tiny recovery indexes; remove redundant upload archives/previews.
    if Path(row['path']).suffix in {'.zip', '.html'}:
        rows.append(row | {'reason': '已验证 GitHub Release SHA-256 的本地上传副本'})

# Explicit scope and immutability assertions before the plan can be executed.
assert len(rows) == len({r['path'].casefold() for r in rows})
for row in rows:
    p = Path(row['path'])
    assert p.is_relative_to(ROOT) or p.is_relative_to(WORKSPACE / 'suzume-visionpro-publishing/release-assets')
    assert str(p.resolve()).casefold() not in protected
    assert 'visionpro' not in p.relative_to(WORKSPACE).parts

stats = collections.defaultdict(lambda: {'files': 0, 'bytes': 0})
for row in rows:
    stats[row['reason']]['files'] += 1
    stats[row['reason']]['bytes'] += row['bytes']
preserve = []
for p in ROOT.rglob('*'):
    if p.is_file() and (str(p.resolve()).casefold() in protected or p.is_relative_to(ROOT / 'visionpro') or p.name == offline['file']):
        preserve.append({'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': sha(p)})
plan = {'remoteCommit': tree['sha'], 'release': release['html_url'], 'files': rows,
        'totalBytes': sum(x['bytes'] for x in rows), 'summary': stats, 'skipped': skipped,
        'protectedFiles': preserve, 'notes': ['No remote files will be changed.', 'Unpublished/latest files are retained.',
        'Automatic .blend1 backups are older than their remotely backed-up primary files; they are not individually archived.']}
(AUDIT / 'cleanup-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'files': len(rows), 'GiB': plan['totalBytes'] / 1024**3, 'summary': stats, 'skipped': skipped}, ensure_ascii=False, indent=2))
