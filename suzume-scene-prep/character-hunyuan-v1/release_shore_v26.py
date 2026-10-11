"""Publish only after native front and oblique image review."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-shore-v26'
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v26.json');b=read('browser-geometry-verification-v26.json');review=read('visual-review-v26.json')
assert v['freshReopenVerified'] and v['allNewMeshesClosed']==731 and v['allPreviousMeshesUnchanged']==1631
assert v['cameraAndLightsUnchanged'] and v['charactersFeetAndPortalPreserved'] and len(v['pipeBoreRayChecks'])==8
assert b['allNativeMeshPositionBuffersMatch'] and b['newParts']==731 and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed']
native=O/'Suzume_scene_movie_shore_v26.blend';images=[O/'movie-front-v26.png',O/'movie-left-oblique-v26.png']
assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
page=R/'viewer/candidate-v26.html'
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v26.html',timeout=10)as response:assert response.status==200 and response.read()==page.read_bytes()
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/suzume-posed-v17.gltf',timeout=10)as response:assert response.status==200
result={'revision':26,'role':'Movie sloped waterfront slabs and hollow pipework comparison candidate','nativeFile':'movie-shore-v26/Suzume_scene_movie_shore_v26.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'newParts':731,'triangles':b['triangles'],'allNewMeshesClosed':True,'pipeBoresCheckedAtBothEnds':4,'nativeFrontAndObliqueReviewed':True,'previousMeshesUnchanged':1631,'bodyHeadFeetAndPortalPreserved':True,'cameraAndLightsUnchangedFromV25':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v26.html','browserGeometrySyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v26.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v26_movie_shore_and_hollow_pipes_comparison_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=26;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v26.html';status['scene']['movieShoreGeometryVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-shore-v26"><h2>电影岸台与中空管道 · v26（候选）</h2>
<p>补上临水矮沿、倾斜断板和两层锈蚀管道。岸台沿整圈庭院延伸并留出南侧入口；管口有实体管壁和中空内腔，四条可见管路两端均已检查。</p>
<p><a href="movie-shore-v26/Suzume_scene_movie_shore_v26.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v26.html">可旋转网页候选版</a>（运行效果待复测） · <a href="movie-shore-v26/movie-left-oblique-v26.png">岸台与管道斜视</a></p>
<figure class="scene"><img src="movie-shore-v26/movie-front-v26.png" alt="重建临水岸台、断板和中空管道的原生场景渲染"><figcaption>原生渲染。保留人物、脚部间隙和穿门分隔；岸台高度与隐藏深度含推定，照明、水面和人物细节仍未达到一比一。</figcaption></figure>
<p><a href="movie-steel-v25/movie-front-v25.png">上一版正面</a> · <a href="movie-shore-v26/verification-v26.json">封闭性、管口与人物检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-shore-v26">' in gallery:gallery=re.sub(r'<section id="movie-shore-v26">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影岸台与中空管道 v26

Suzume_scene_movie_shore_v26.blend：完整昼景、门、混元身体、独立头模和异世界；第 72 帧为开门。
Movie waterfront v26 — sloped solid slabs and hollow pipes：新增岸台、断板、管道和连接件，共 731 个可编辑部件。
岸台沿院落延伸，并留出南侧入口；电影可见断板由手工描出的轮廓与推定高度生成，有厚度、坡面和凹凸边缘。
两层管道按当前镜头反投影到推定的半径 22.35 圆环，管壁有内外表面及端面环，断口不是实心封盖。
四条可见管路的两端分别用射线检查内腔和管壁；全部新增网格检查了封闭性和正体积。

这不等于官方尺寸复原：岸台高度、隐藏深度、后方管线和场景外观仍需继续校准。
相机与灯光沿用 v25；右侧照明偏亮、门内云层、水面反射、人物细节和关门海报场景仍有未完成部分。
其他 1631 个昼景网格、人物脚部间隙、独立头模、穿门分隔和开门照明均通过重新打开核验。

movie-front-v26.png：正面原生渲染。
movie-left-oblique-v26.png：与 v25 同机位的原生斜视渲染。
网页：http://127.0.0.1:8931/viewer/candidate-v26.html
网页新构件坐标、脚本和 HTTP 资源已检查；实际 WebGL 显示与交互仍待复测。
稳定原生 v19、默认网页 v17 和此前候选均保留；尚未达到一比一。
''',encoding='utf-8')
print('SHORE_26_RELEASED',result['nativeSha256'],result['newParts'],flush=True)
