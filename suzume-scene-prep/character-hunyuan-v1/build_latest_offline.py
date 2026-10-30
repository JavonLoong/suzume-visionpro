"""Retain the latest poster and movie views in one self-contained HTML file."""
import json
import build_offline_html as bundle

root = bundle.ROOT
resources = json.loads((root / 'poster-right-bow-v56/browser-http-verification-v56.json').read_text(encoding='utf-8'))['resources']
poster_assets = {r['path'] for r in resources}
# The last surface restoration added two textures after the old HTTP report.
poster_assets.update(['poster-right-bow-v56/right-facade-beam-mask-v56.png',
                     'poster-right-bow-v56/right-arcade-beam-mask-v56.png'])
scenes = [
    {'id': 'v56', 'label': 'v56 海报庭院', 'source': 'viewer/poster-v56.html', 'assets': sorted(poster_assets)},
    bundle.SCENES[2],  # v37 is the latest separate movie-door composition.
]
report = bundle.build('铃芽之旅_v56_最新双场景_离线.html', '铃芽之旅 · 最新双场景', scenes, [])
(bundle.OUT / '最新版打包清单.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('LATEST_OFFLINE_BUILT', report['file'], report['bytes'], report['assets'])
