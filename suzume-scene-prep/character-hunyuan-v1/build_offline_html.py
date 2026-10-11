"""Lossless, portable HTML copies of the user's three existing scene viewers."""
import base64
import gzip
import hashlib
import html
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '离线HTML'
OUT.mkdir(exist_ok=True)
RUNTIME = (ROOT / 'offline_bundle_runtime.js').read_text(encoding='utf-8')

def gltf_files(name):
    path=ROOT/name
    doc=json.loads(path.read_text(encoding='utf-8'))
    return [name]+[(path.parent/x['uri']).relative_to(ROOT).as_posix()
                  for x in doc.get('buffers',[])+doc.get('images',[])
                  if x.get('uri') and not x['uri'].startswith('data:')]

character=gltf_files('viewer/character-v37/suzume-posed-v37.gltf')
shared=['viewer/three.min.js','viewer/GLTFLoader.js']+character
poster49=[x['path'] for x in json.loads((ROOT/'poster-arches-v49/browser-http-verification-v49.json').read_text())['resources']]
movie37=shared+['viewer/RectAreaLightUniformsLib.js','viewer/candidate-v37.html',
    'movie-surfaces-v28/reference-opening.jpg','movie-surfaces-v28/surface-validity-mask-v28.png',
    'movie-terrain-v31/ground-world-v31.bin','movie-terrain-v31/extension-vertices-v31.bin',
    'movie-terrain-v31/extension-indices-v31.bin']
SCENES=[
    {'id':'v49','label':'v49 主视觉','source':'viewer/poster-v49.html','assets':sorted(set(poster49))},
    {'id':'v38','label':'v38 海报庭院','source':'viewer/poster-v38.html','assets':sorted(set(shared+['viewer/poster-v38.html']))},
    {'id':'v37','label':'v37 电影开门','source':'viewer/candidate-v37.html','assets':sorted(set(movie37))},
]
RENDERS=[
    {'key':'poster-arches-v49/poster-front-v49.png','label':'v49 正面渲染','name':'铃芽之旅_v49_正面.png'},
    {'key':'poster-arches-v49/poster-oblique-v49.png','label':'v49 斜侧渲染','name':'铃芽之旅_v49_斜侧.png'},
]
MODEL={'key':'poster-v38/Suzume_dual_scene_v38.blend','name':'铃芽之旅_v38_双场景.blend'}

STYLE='''
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#111915;color:#e4e7e5;font:14px/1.55 system-ui,"Microsoft YaHei",sans-serif}.archive-header{padding:22px 26px 14px;border-bottom:1px solid #2b4035}.eyebrow{color:#b7c6b7;font-size:11px;letter-spacing:.18em}h1{font-size:24px;font-weight:500;margin:4px 0 8px}p{margin:4px 0;color:#a8b8ae}.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:15px}button{font:inherit;background:#23392d;color:#e3ece5;border:1px solid #476350;border-radius:8px;padding:8px 13px;cursor:pointer}button:hover{background:#36533e}button[aria-pressed=true]{background:#c2dbbc;color:#15271b;border-color:#c2dbbc}button:focus-visible{outline:2px solid #e2eed7;outline-offset:3px}button:disabled{opacity:.6;cursor:wait}.utility{margin-left:auto;display:flex;gap:8px}.status-row{display:flex;justify-content:space-between;gap:12px;padding:10px 26px;color:#a8b8ae;font-size:12px}#archive-stage{min-height:75vh;max-width:1600px;margin:auto;background:#111915}#archive-stage:fullscreen{overflow:auto}#scene-frame{width:100%;height:max(640px,calc(100vh - 230px));border:0;display:block}#archive-stage:fullscreen #scene-frame{height:100vh}.placeholder{min-height:70vh;display:grid;place-items:center;color:#b9cdbd}.gallery{display:flex;flex-wrap:wrap;gap:24px;padding:24px;justify-content:center}.gallery figure{margin:0;max-width:760px;flex:1 1 340px}.gallery img{width:100%;max-height:75vh;object-fit:contain;display:block;background:#0c120f;border-radius:10px}.gallery figcaption{margin:10px 0}.footnote{padding:18px 26px;text-align:center;color:#7f9989;font-size:12px}@media(max-width:680px){.archive-header{padding:16px}h1{font-size:20px}.utility{margin-left:0}button{padding:7px 10px}.status-row{padding:8px 16px}#scene-frame{height:max(640px,calc(100vh - 270px))}}
'''

payloads={}
def asset(key):
    if key in payloads:return payloads[key]
    path=ROOT/key
    data=path.read_bytes()
    packed=gzip.compress(data,compresslevel=6,mtime=0)
    use_gzip=len(packed)<len(data)*.98
    stored=packed if use_gzip else data
    mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    if path.suffix=='.gltf':mime='model/gltf+json'
    item={'gzip':use_gzip,'mime':mime,'bytes':len(data),'packedBytes':len(stored),
          'sha256':hashlib.sha256(data).hexdigest(),'encoded':base64.b64encode(stored).decode('ascii')}
    assert (gzip.decompress(stored) if use_gzip else stored)==data
    payloads[key]=item
    print('PACKED',key,len(data),'->',len(stored),flush=True)
    return item

def build(filename,title,scenes,renders,model=None,initial=None):
    keys=sorted(set([key for scene in scenes for key in scene['assets']]+[x['key'] for x in renders]+([model['key']] if model else [])))
    manifest={}
    for n,key in enumerate(keys):
        info=asset(key)
        manifest[key]={k:v for k,v in info.items() if k!='encoded'}|{'id':'embedded-'+str(n)}
    config={'scenes':scenes,'renders':renders,'model':model,'assets':manifest,'initial':initial or scenes[0]['id']}
    buttons=''.join('<button type="button" data-scene="'+s['id']+'" aria-pressed="false">'+s['label']+'</button>' for s in scenes)
    if renders:buttons+='<button type="button" data-scene="renders" aria-pressed="false">原始渲染图</button>'
    utility=('<button type="button" data-download-model>保存双场景 Blender 模型</button>' if model else '')+'<button type="button" data-fullscreen>全屏</button>'
    header=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' blob:; style-src 'unsafe-inline'; img-src data: blob:; connect-src blob: data:; frame-src 'self' about: blob:; font-src data:; worker-src blob:;"><title>{html.escape(title)}</title><style>{STYLE}</style></head><body><header class="archive-header"><div class="eyebrow">SUZUME · 离线收藏</div><h1>{html.escape(title)}</h1><p>双击此文件即可查看。模型与贴图已收录在文件内，可自由旋转、切换视角和开关门。</p><nav class="toolbar" aria-label="场景切换">{buttons}<div class="utility">{utility}</div></nav></header><div class="status-row"><span id="archive-status" role="status" aria-live="polite">准备载入…</span><span>无需启动服务器 · 可离线使用</span></div><main id="archive-stage"></main><footer class="footnote">保留所选版本的场景、材质与操作方式。部分隐藏结构仍为重建推测。</footer><script>window.OFFLINE_CONFIG={json.dumps(config,ensure_ascii=False,separators=(',',':'))};</script>'''
    target=OUT/filename
    if not scenes:
        header=header.replace('模型与贴图已收录在文件内，可自由旋转、切换视角和开关门。','原始分辨率渲染图已收录在文件内，可离线查看并保存原图。')
    with target.open('w',encoding='utf-8',newline='\n') as stream:
        stream.write(header)
        for key in keys:
            stream.write('<script type="application/octet-stream" id="'+manifest[key]['id']+'">')
            stream.write(payloads[key]['encoded']);stream.write('</script>\n')
        stream.write('<script>'+RUNTIME.replace('</script','<\\/script')+'</script></body></html>')
    return {'file':filename,'bytes':target.stat().st_size,'assets':len(keys),'scenes':[s['id'] for s in scenes],
            'includesNativeBlend':bool(model),'embeddedBytes':sum(x['bytes'] for x in manifest.values()),'resources':manifest}

reports=[]
reports.append(build('铃芽之旅_全部场景_离线珍藏.html','铃芽之旅 · 门的两侧',SCENES,RENDERS,MODEL))
for scene,filename in zip(SCENES,['铃芽之旅_v49_旋转场景.html','铃芽之旅_v38_海报庭院.html','铃芽之旅_v37_电影开门.html']):
    reports.append(build(filename,scene['label']+' · 铃芽之旅',[scene],RENDERS if scene['id']=='v49' else []))
reports.append(build('铃芽之旅_v49_原始渲染.html','铃芽之旅 · v49 原始渲染',[],RENDERS,initial='renders'))
(OUT/'打包清单.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
print('OFFLINE_HTML_BUILT',json.dumps([{k:v for k,v in x.items() if k!='resources'} for x in reports],ensure_ascii=False),flush=True)
