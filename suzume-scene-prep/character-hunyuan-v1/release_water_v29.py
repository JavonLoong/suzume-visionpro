"""Register the visually reviewed shallow-water candidate and its limitations."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-water-v29'
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v29.json');b=read('browser-verification-v29.json');review=read('visual-review-v29.json');appearance=read('water-appearance-v29.json')
assert v['freshReopenVerified'] and v['allDayMeshGeometryAndTopologyPreserved']==2362 and v['characterHeadFeetAndPortalPreserved'] and v['cameraAndLightingPreserved']
assert v['liveReflectionAndRefractionNodesVerified'] and v['shallowShadowTransmissionAndScatterVerified'] and not v['referenceImageUsedInWater']
assert b['actualWaterBuilderAndOpticsEditsExecuted'] and b['waterUniformParametersMatchNativeSpec'] and b['liveReflectionAndRefractionTexturesRetained'] and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed'] and 'movie-front-v29.png' in appearance['renders']
native=O/'Suzume_scene_movie_water_v29.blend';images=[O/'movie-front-v29.png',O/'movie-left-oblique-v29.png'];assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
for file in ['viewer/candidate-v29.html','viewer/suzume-posed-v17.gltf','movie-surfaces-v28/reference-opening.jpg','movie-surfaces-v28/surface-validity-mask-v28.png']:
    with urllib.request.urlopen('http://127.0.0.1:8931/'+file,timeout=10) as response:assert response.status==200 and response.read()==(R/file).read_bytes()
result={'revision':29,'role':'Live shallow-water reflection, clear paving and world-space submerged algae','nativeFile':'movie-water-v29/Suzume_scene_movie_water_v29.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'nativeFrontAndObliqueReviewed':True,'waterTrialCount':6,'previousDayMeshesUnchanged':2362,'bodyHeadFeetAndPortalPreserved':True,'cameraAndLightingPreserved':True,'liveReflectionAndRefraction':True,'referenceImageUsedInWater':False,'submergedStoneMaterialsRefined':v['submergedAlgaeMaterialCount'],'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v29.html','browserShaderEditsParametersSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'nativeBrowserAppearanceEquivalenceVerified':False,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v29.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v29_movie_shallow_water_and_paving_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=29;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v29.html';status['scene']['movieWaterVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-water-v29"><h2>电影浅水与水底 · v29（候选）</h2>
<p>经过六组试渲染，调整水面的反射与透射、波纹、散射色和水下受光；石板轮廓重新显现，水底加入附着于实体石面的藻类色斑。倒影仍来自场景中的真实建筑。</p>
<p><a href="movie-water-v29/Suzume_scene_movie_water_v29.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v29.html">可旋转网页候选版</a>（显示待复测） · <a href="movie-water-v29/movie-left-oblique-v29.png">斜视渲染</a></p>
<figure class="scene"><img src="movie-water-v29/movie-front-v29.png" alt="浅水倒影与可见水底的原生渲染"><figcaption>水面使用场景反射与折射，没有贴入参照图片。散射和反射比例属于画面风格近似；波光亮点、铺石细节、夜云和人物仍有差距，未达到一比一。</figcaption></figure>
<p><a href="movie-surfaces-v28/movie-front-v28.png">上一版正面</a> · <a href="movie-water-v29/water-appearance-v29.json">局部水色诊断（非整体相似度）</a> · <a href="movie-water-v29/verification-v29.json">水面与人物检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-water-v29">' in gallery:gallery=re.sub(r'<section id="movie-water-v29">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影浅水与水底 v29

Suzume_scene_movie_water_v29.blend：完整昼景、门、混元身体、独立头模与异世界；第 72 帧为开门。
水面保留真实场景的反射和折射，没有使用参照图片作水面贴图。
按六组试渲染调整反射比例、粗糙度和波纹，并加入近似的浅水散射色及日光透射。
原有实体石板保持，藻类色斑固定在水下石板的上表面；7 个水底材质被调整。
这些参数用于接近电影绘制的外观，属于艺术近似，不是实测光学常数或完整体积水模拟。

2362 个昼景网格的顶点和拓扑保持，原镜头、灯光、墙面校准、人物、头模、脚部间隙和穿门分隔重新打开后检查通过。
movie-front-v29.png：完整正面渲染。movie-left-oblique-v29.png：同机位斜视渲染。
trial-*.png：六组过程对照，其中两组只渲染下方水面区域，上方黑色区域没有参与渲染。
water-appearance-v29.json：手工选取的水面区域色彩和对比度，仅用于诊断，不是整体相似度。

网页候选：http://127.0.0.1:8931/viewer/candidate-v29.html
网页的水面程序、参数与资源已检查；浏览器运行、GPU 着色器编译和跨引擎外观一致性仍未验证。
波光亮点、石板轮廓与色彩、夜云、人物和另一幅关门海报场景仍未完成一比一校准。
稳定原生 v19、默认网页 v17 和此前候选全部保留。
''',encoding='utf-8')
print('WATER_29_RELEASED',result['nativeSha256'],flush=True)
