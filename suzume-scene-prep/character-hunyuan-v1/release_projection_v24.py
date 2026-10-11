"""Publish only after fresh checks and both native renders are reviewed."""
from pathlib import Path
import json,re,hashlib,urllib.request
R=Path(__file__).parent;O=R/'movie-projection-v24'
def read(n):return json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v24.json');b=read('browser-geometry-verification-v24.json');review=read('visual-review-v24.json');f=read('joint-fit-v24.json')
assert v['freshReopenVerified'] and v['bodyHeadFeetAndPortalGeometryPreserved'] and v['fiveWallsWatertight'] and len(v['eightOpenings'])==8
assert b['nativeFiveLowerWallsMatch'] and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed']
native=O/'Suzume_scene_movie_projection_v24.blend';images=[O/'movie-front-v24.png',O/'movie-left-oblique-v24.png']
assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
page=R/'viewer/candidate-v24.html'
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v24.html',timeout=10) as response:assert response.status==200 and response.read()==page.read_bytes()
for name in ['three.min.js','GLTFLoader.js','RectAreaLightUniformsLib.js','suzume-posed-v17.gltf']:
    with urllib.request.urlopen('http://127.0.0.1:8931/viewer/'+name,timeout=10) as response:assert response.status==200
result={'revision':24,'role':'Complete movie camera and courtyard comparison candidate','nativeFile':'movie-projection-v24/Suzume_scene_movie_projection_v24.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),
    'lensMm':f['parameters']['lensMm'],'courtyardRadius':23.5,'newParts':789,'solidWindowOpenings':8,'nativeFrontAndObliqueReviewed':True,
    'bodyHeadFeetAndPortalVerified':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,
    'browserCandidate':'viewer/candidate-v24.html','browserGeometrySyntaxAndHttpVerified':True,'browserRuntimeVerified':False,
    'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v24.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
integration=read('integration-v24.json');integration['visualReviewPending']=False;integration['visualReview']='visual-review-v24.json';(O/'integration-v24.json').write_text(json.dumps(integration,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v24_camera_and_courtyard_comparison_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=24;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v24.html';status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-projection-v24"><h2>镜头与完整庭院联合校准 · v24（候选）</h2>
<p>按门框、人物、窗顶、拱廊和水线重新拟合镜头。当前镜头约 87 mm，庭院恢复到源模型的 23.5 单位半径；整圈开间与连续楼层同步调整。五段建筑、八个真实窗洞、后方房间和侧墙均可旋转查看。</p>
<p><a href="movie-projection-v24/Suzume_scene_movie_projection_v24.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v24.html">可旋转网页候选版</a>（运行效果待复测） · <a href="movie-projection-v24/movie-left-oblique-v24.png">斜视渲染</a></p>
<figure class="scene"><img src="movie-projection-v24/movie-front-v24.png" alt="镜头和完整庭院联合校准后的原生三维渲染"><figcaption>混元独立头模、脚部间隙和穿门分隔已保留并校验。钢架、门内云层、水面和人物细节仍有明显差异，尚未达到一比一。</figcaption></figure>
<p><a href="movie-bays-v23/movie-front-v23.png">上一版正面渲染</a> · <a href="movie-projection-v24/verification-v24.json">实体窗洞、人物与穿门校验</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-projection-v24">' in gallery:gallery=re.sub(r'<section id="movie-projection-v24">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''镜头与完整庭院联合校准 v24

Suzume_scene_movie_projection_v24.blend：完整昼景、门、混元人物与异世界。第 72 帧为开门。
Movie courtyard projection v24 — complete solid rooms 集合：五段重建建筑，共 789 个可编辑部件。
八个真实窗洞均已射线检查，五面墙焊接后均保持封闭实体。整圈建筑的相邻径向边界连续。
人物身体、独立混元头模、发卡、脚部修正与互补空间裁切的几何指纹和材质设置均通过复核。

约 87 mm 镜头、23.5 单位庭院半径是从手工图像标记推定的重建参数，不代表官方制作数据。
此前将背景放大三倍的处理在本候选中已取消。前景脚和门槛保持原三维位置。
异世界远处山丘和云层按当前电影镜头重排；门口 12 单位以内的地形与人物保持不变。

movie-front-v24.png：正面原生渲染。
movie-left-oblique-v24.png：完整房间与窗组斜视渲染。
网页候选：http://127.0.0.1:8931/viewer/candidate-v24.html
网页通过几何、镜头投影、语法和本地 HTTP 检查；浏览器控制连接仍超时，实际交互未复核。

仍待修正：钢架位置和形状、连续管道、门基与铺石、水面、昼夜云层、藤叶贴合，以及人物脸型、发丝与手臂姿态。
本版尚未达到一比一。稳定原生 v19、默认网页 v17 和此前候选全部保留。
''',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
