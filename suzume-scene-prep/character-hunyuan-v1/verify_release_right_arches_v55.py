from pathlib import Path
import hashlib
import json
import requests

R = Path(__file__).parent
O = R / 'poster-right-arches-v55'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
release = json.loads((O / 'release-v55.json').read_text(encoding='utf-8'))
status = json.loads((R / 'status.json').read_text(encoding='utf-8'))
assert sha(R / release['nativeFile']) == sha(Path(release['primaryNativeAlias'])) == release['nativeSha256']
assert status['scene']['revision'] == 55 and status['scene']['currentNative'] == release['nativeFile']
assert not status['scene']['oneToOneComplete']
gallery = (R / 'index.html').read_text(encoding='utf-8')
assert gallery.index('id="poster-right-arches-v55"') < gallery.index('id="poster-right-facade-v54"')
checks = []
for name in ['index.html', 'status.json', 'viewer/poster-v55.html',
             'poster-right-arches-v55/poster-front-v55.png',
             'poster-right-arches-v55/right-arches-comparison-v55.png',
             'poster-right-arches-v55/release-v55.json']:
    r = requests.get('http://127.0.0.1:8931/' + name, timeout=30)
    r.raise_for_status()
    assert hashlib.sha256(r.content).hexdigest() == sha(R / name)
    checks.append(name)
result = {'revision': 55, 'nativeSha256': release['nativeSha256'],
    'primaryAliasMatches': True, 'statusAndGalleryPointToV55': True,
    'downloadAndPreviewResources': checks, 'browserDefaultRevision': 17,
    'browserRuntimeVerified': False, 'oneToOneComplete': False}
(O / 'release-verification-v55.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('RIGHT_ARCHES_55_RELEASE_VERIFIED', release['nativeSha256'])
