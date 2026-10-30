"""List, restore or verify the archived files in PROJECT_MANIFEST.json. Python 3.9+."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def destination(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not name.startswith('suzume-scene-prep/'):
        raise ValueError('Unsafe project path: ' + name)
    return path


def restore_archive(archive, rows):
    pending = []
    for row in rows:
        path = destination(row['path'])
        if path.exists():
            if not path.is_file() or sha256(path) != row['sha256']:
                raise RuntimeError('Existing file differs; keep or move it before restoring: ' + row['path'])
        else:
            pending.append(row)
    if not pending:
        return
    cache = ROOT / '.project-assets-cache'
    cache.mkdir(exist_ok=True)
    cached = cache / (archive['sha256'] + '.zip')
    if not cached.exists():
        temporary = cached.with_suffix('.download')
        print('Downloading', archive['url'], flush=True)
        with urllib.request.urlopen(archive['url'], timeout=120) as response, temporary.open('wb') as out:
            shutil.copyfileobj(response, out)
        if sha256(temporary) != archive['sha256']:
            raise RuntimeError('Download checksum mismatch: ' + archive['name'])
        temporary.replace(cached)
    if sha256(cached) != archive['sha256']:
        raise RuntimeError('Cached archive checksum mismatch: ' + str(cached))
    with zipfile.ZipFile(cached) as z:
        for row in pending:
            path = destination(row['path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation ensures that an existing local edit is never overwritten.
            with path.open('xb') as out, z.open(row['path']) as inp:
                shutil.copyfileobj(inp, out)
            if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
                raise RuntimeError('Restored file checksum mismatch: ' + row['path'])
    print('Restored', len(pending), 'files from', archive['name'], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('all', 'pico', 'visionpro', 'print'), default='all')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--restore', action='store_true', help='Download archives and restore missing files; never overwrite edits.')
    action.add_argument('--verify', action='store_true', help='Check local source files against this snapshot; do not download.')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'PROJECT_MANIFEST.json').read_text(encoding='utf-8'))
    prefixes = {'all': 'suzume-scene-prep/', 'pico': 'suzume-scene-prep/picounity/',
                'visionpro': 'suzume-scene-prep/visionpro/', 'print': 'suzume-scene-prep/print-'}
    rows = [r for r in manifest['files'] if r['path'].startswith(prefixes[args.scope])]
    if args.verify:
        failed = []
        for row in rows:
            path = destination(row['path'])
            if not path.is_file() or path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
                failed.append(row['path'])
        for name in failed:
            print('Missing or changed:', name)
        print(f'Checked {len(rows)} files; {len(failed)} missing or changed. SDK is checked by prepare_pico.py.')
        return 1 if failed else 0
    groups = {}
    for row in rows:
        if row['storage'] != 'git':
            groups.setdefault((row['releaseTag'], row['storage']), []).append(row)
    archives = {(a['releaseTag'], a['name']): a for a in manifest['archives']}
    for key, files in sorted(groups.items()):
        archive = archives[key]
        print(f"{key[0]}/{key[1]}: {len(files)} files; download {archive['bytes'] / 1024**2:.1f} MiB")
        if args.restore:
            restore_archive(archive, files)
    if not args.restore:
        print('Listing only. Add --restore to download and restore missing files.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
