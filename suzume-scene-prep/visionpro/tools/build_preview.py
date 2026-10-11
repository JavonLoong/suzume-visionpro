from pathlib import Path
import gzip,base64
ROOT=Path(__file__).resolve().parents[1]
VIEWER=ROOT.parent/'character-hunyuan-v1'/'viewer'
html=(ROOT/'tools'/'portal_preview.html').read_text(encoding='utf-8')
libs='\n'.join('<script>'+ (VIEWER/name).read_text(encoding='utf-8').replace('</script','<\\/script')+'</script>' for name in ('three.min.js','GLTFLoader.js'))
assets=[]
for name,id in [('DreamWorld','worldAsset'),('DoorFrame','frameAsset')]:
    data=base64.b64encode(gzip.compress((ROOT/'preview-assets'/(name+'.glb')).read_bytes(),compresslevel=8,mtime=0)).decode()
    assets.append('<script type="application/octet-stream" id="'+id+'">'+data+'</script>')
html=html.replace('<!--LIBRARIES-->',libs).replace('<!--ASSETS-->','\n'.join(assets))
out=ROOT/'铃芽之旅_VisionPro适配_离线预览.html'
out.write_text(html,encoding='utf-8')
print(out.name, out.stat().st_size)
