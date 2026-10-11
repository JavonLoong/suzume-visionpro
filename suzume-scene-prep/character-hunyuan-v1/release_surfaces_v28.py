"""Register the reviewed surface candidate without replacing stable defaults."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-surfaces-v28'
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v28.json');b=read('browser-verification-v28.json');review=read('visual-review-v28.json')
assert v['freshReopenVerified'] and v['allDayMeshGeometryAndTopologyUnchanged']==2362 and v['characterHeadFeetAndPortalPreserved']
assert v['cameraAndLightsPreserved'] and v['sourceImagePackedUnmodified'] and v['signedColorLutPackedAndReopened'] and v['newSurfaceGeometryCount']==0
assert b['selectedNativeAndBrowserTrianglesMatch'] and b['eligibilityAttributePreservedAfterActualBake'] and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed']
native=O/'Suzume_scene_movie_surfaces_v28.blend';images=[O/'movie-front-v28.png',O/'movie-left-oblique-v28.png'];assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
files=['viewer/candidate-v28.html','movie-surfaces-v28/reference-opening.jpg','movie-surfaces-v28/surface-validity-mask-v28.png','viewer/suzume-posed-v17.gltf']
for file in files:
    with urllib.request.urlopen('http://127.0.0.1:8931/'+file,timeout=10) as response:assert response.status==200 and response.read()==(R/file).read_bytes()
result={'revision':28,'role':'Fixed reference colors on existing physical plaster and stone faces','nativeFile':'movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'nativeFrontAndObliqueReviewed':True,'previousDayMeshesUnchanged':2362,'bodyHeadFeetAndPortalPreserved':True,'cameraAndLightingPreserved':True,'selectedPhysicalObjects':v['selectedPhysicalObjects'],'selectedPolygons':v['selectedPolygons'],'newSurfaceGeometryCount':0,'referenceShadingRetained':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v28.html','browserFaceSelectionSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'browserRuntimeAttempt':'Existing IAB candidate tab connection timed out; no screenshot or interaction verification obtained.','oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v28.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v28_movie_physical_wall_surface_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=28;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v28.html';status['scene']['movieSurfaceProjectionVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-surfaces-v28"><h2>电影墙面色彩与污迹 · v28（候选）</h2>
<p>将参照色彩固定到真实墙面和石材表面，保留窗洞、后方房间与原有几何。前景门、人物、钢柱、弯梁及鲜绿叶片从映射中排除。</p>
<p><a href="movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v28.html">可旋转网页候选版</a>（显示待复测） · <a href="movie-surfaces-v28/movie-left-oblique-v28.png">斜视渲染</a></p>
<figure class="scene"><img src="movie-surfaces-v28/movie-front-v28.png" alt="固定墙面色彩与污迹后的原生渲染"><figcaption>原生渲染。参照中的光影保留在表面颜色里，不代表实测材质。水面、夜云、人物及遮挡区域仍有差距，未达到一比一。</figcaption></figure>
<p><a href="movie-lighting-v27/movie-front-v27.png">上一版正面</a> · <a href="movie-surfaces-v28/verification-v28.json">几何、材质与穿门检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-surfaces-v28">' in gallery:gallery=re.sub(r'<section id="movie-surfaces-v28">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影实体墙面色彩 v28

Suzume_scene_movie_surfaces_v28.blend：完整昼景、门、混元身体、独立头模与异世界；第 72 帧为开门。
164 个现有物体的 14678 个正面多边形使用固定的世界坐标参照映射。没有增加平面或替换几何。
窗洞、窗后房间、石材厚度、侧面与背面均保留。门、人物、钢柱、弯梁与鲜绿叶片从参照映射中排除。
参照图未经修改并打包进 Blender；色彩通过保留有符号浮点数的逆 AgX 查找表校准。
参照原有光影被保留在表面色彩里，这不是实测反照率材质。被遮挡和未观察到的部分继续使用原材质，仍有接缝和明暗差异。

2362 个昼景网格的顶点与拓扑重新打开后检查不变。人物、头模、脚部间隙、穿门分区和开门照明驱动保持。
movie-front-v28.png：正面渲染。movie-left-oblique-v28.png：斜视渲染，检查表面色彩固定在建筑上。
网页候选：http://127.0.0.1:8931/viewer/candidate-v28.html
网页的选面、脚本和资源已检查；实际 WebGL 显示及旋转尚未验证，浏览器连接仍超时。
水面、夜云、人物细节、遮挡部分与关门海报场景仍未完成一比一校准。
稳定原生 v19、默认网页 v17 和此前候选保留。
''',encoding='utf-8')
print('SURFACES_28_RELEASED',result['nativeSha256'],flush=True)
