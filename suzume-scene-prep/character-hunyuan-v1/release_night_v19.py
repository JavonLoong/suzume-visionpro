"""Publish the verified native lighting improvement, retaining earlier models."""
from pathlib import Path
import json,re,subprocess,shutil,urllib.request,hashlib
R=Path(__file__).parent;O=R/'night-calibration-v19';W=R/'viewer'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
verification=json.loads((O/'verification-v19.json').read_text(encoding='utf-8'))
assert verification['freshReopenVerified'] and verification['allCharacterWorldVerticesExactlyPreserved']
light=json.loads((O/'lighting-v19.json').read_text(encoding='utf-8'));assert light['powerWatts']==15
assert (O/'portal-light-candidate.png').stat().st_mtime>(R/'Suzume_scene_Hunyuan_v19.blend').stat().st_mtime
html=(W/'candidate-v19.html').read_text(encoding='utf-8')
for attrs,script in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S):
    if 'src=' in attrs or not script.strip():continue
    check=subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'],input=script,text=True,capture_output=True)
    assert check.returncode==0,check.stderr
assert "doorwayDaylight.intensity=.48" in html and "localClippingEnabled=true" in html
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v19.html',timeout=10) as response:
    assert response.status==200
    assert hashlib.sha256(response.read()).digest()==hashlib.sha256((W/'candidate-v19.html').read_bytes()).digest()
shutil.copy2(O/'portal-light-candidate.png',R/'native-pose-front-v19.png')
shutil.copy2(R/'Suzume_scene_Hunyuan_v19.blend',V/'suzume-full-scene-hunyuan-v19.blend')
shutil.copy2(R/'Suzume_scene_Hunyuan_v19.blend',V/'suzume-full-scene.blend')
release={'revision':19,'nativeScene':'Suzume_scene_Hunyuan_v19.blend','headGeometryRevision':17,
         'change':'Warm courtyard illumination admitted through the open door, fitted against reference color regions',
         'nativeRenderVerified':True,'nativeRender':'native-pose-front-v19.png','allCharacterWorldVerticesPreserved':True,
         'footClearanceAndPortalPartitionPreserved':True,'doorLightClosesCorrectly':True,
         'browserCandidate':'viewer/candidate-v19.html','browserRuntimeVerified':False,
         'browserDefaultRemainsRevision':17,'oneToOneComplete':False,
         'remaining':['Architectural scale and reference camera perspective differ markedly.','Head likeness and hair silhouette remain approximate.','Sky/cloud structure and flower density need closer matching.','Browser interaction cannot yet be exercised because control keeps timing out.']}
(O/'release-v19.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'))
status['status']='native_v19_doorway_light_calibrated';status['scene']['currentNative']='Suzume_scene_Hunyuan_v19.blend'
status['scene']['revision']=19;status['scene']['headGeometryRevision']=17
status['scene']['nativeLightingVerifiedV19']=True
status['scene']['browserLightingCandidate']='http://127.0.0.1:8931/viewer/candidate-v19.html'
status['scene']['nativeAndBrowserPartitionVerified']=False
status['scene']['browserDefaultRevision']=17
status['next']=release['remaining']
(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
gallery=(R/'index.html').read_text(encoding='utf-8')
gallery=gallery.replace('<title>铃芽 · 独立头部重建 v17</title>','<title>铃芽之旅 · 三维场景与模型</title>').replace('<h1>铃芽 · 独立头部重建 v17</h1>','<h1>铃芽之旅 · 三维场景与模型</h1>')
section='''<section id="night-light-v19"><h2>门内光照校准 · v19</h2>
<p>门口透入的日光会照亮迈入异世界的人物和近处花草，关门时同步关闭。人物、头模和脚部几何均保持不变。当前仍未达到一比一。</p>
<p><a href="Suzume_scene_Hunyuan_v19.blend">最新完整 Blender 场景</a> · <a href="viewer/candidate-v19.html">可旋转光照对比版</a>（网页效果待复测） · <a href="night-calibration-v19/light-color-comparison.json">局部颜色对照</a></p>
<figure class="scene"><img src="native-pose-front-v19.png" alt="门内光照校准后的完整原生场景"><figcaption>门内校服、裙子与花草保留夜景中的颜色层次</figcaption></figure>
<p><a href="native-pose-front-v17.png">查看调整前</a> · <a href="night-calibration-v19/verification-v19.json">模型和开关门验证</a></p></section>'''
if '<section id="night-light-v19">' in gallery:gallery=re.sub(r'<section id="night-light-v19">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门内光照校准 v19

最新原生文件：上一级 Suzume_scene_Hunyuan_v19.blend。
时间轴 1 帧为关门，72 帧为开门；门口日光随开度变化。
这是基于 v17 混元独立头模的光照调整，未改动身体、头模、脚部和裁切平面。
完整原生渲染：上一级 native-pose-front-v19.png。
网页对比： http://127.0.0.1:8931/viewer/candidate-v19.html
网页采用局部聚光灯近似，浏览器连接仍超时，尚未完成运行时和视觉复测。

light-color-comparison.json 只比较校服、裙子、头发三个区域的中位 RGB。
它不是整体相似度，也不能证明一比一。建筑透视、云层、花草密度和人物神态仍需调整。
''',encoding='utf-8')
print(json.dumps(release,ensure_ascii=False,indent=2))
