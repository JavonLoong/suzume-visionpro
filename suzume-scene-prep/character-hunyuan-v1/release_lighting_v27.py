"""Publish a reviewed lighting candidate, keeping all prior scene variants."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-lighting-v27'
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v27.json');b=read('browser-verification-v27.json');review=read('visual-review-v27.json');comparison=read('appearance-comparison-v27.json')
assert v['freshReopenVerified'] and v['allDayMeshesUnchanged']==2362 and v['characterFeetHeadAndPortalPreserved'] and v['cameraUnchanged']
assert v['worldSpaceLightPositionsDirectionsPowersAndColorsVerified'] and v['separateCameraAndGlossySkyShaderVerified']
assert b['sunWorldPositionDirectionAndEnergyMatchNative'] and b['facadePowerAndColorsMatchNative'] and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed'] and 'movie-front-v27.png' in comparison['renders']
native=O/'Suzume_scene_movie_lighting_v27.blend';images=[O/'movie-front-v27.png',O/'movie-left-oblique-v27.png'];assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
page=R/'viewer/candidate-v27.html'
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v27.html',timeout=10) as response:assert response.status==200 and response.read()==page.read_bytes()
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/suzume-posed-v17.gltf',timeout=10) as response:assert response.status==200
result={'revision':27,'role':'Movie side sunlight, cool shadow and local facade fill comparison candidate','nativeFile':'movie-lighting-v27/Suzume_scene_movie_lighting_v27.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'nativeFrontAndObliqueReviewed':True,'previousDayMeshesUnchanged':2362,'bodyHeadFeetAndPortalPreserved':True,'cameraPreserved':True,'lightingTrialCount':4,'nativeSkyDisplaySeparatedFromWorldIllumination':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v27.html','browserLightParametersSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'browserSkyColorRetainsPreviousCalibration':True,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v27.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v27_movie_sunlight_and_local_fill_comparison_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=27;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v27.html';status['scene']['movieLightingVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-lighting-v27"><h2>电影日光、阴影与局部补光 · v27（候选）</h2>
<p>经过四组试渲染，调整了太阳方向、环境光和立面补光。左侧建筑恢复冷色阴影，右侧补光范围缩小；天空显示和环境照明分开校准。完整三维几何、人物与穿门分隔保留。</p>
<p><a href="movie-lighting-v27/Suzume_scene_movie_lighting_v27.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v27.html">可旋转网页候选版</a>（运行效果待复测） · <a href="movie-lighting-v27/movie-left-oblique-v27.png">同机位斜视</a></p>
<figure class="scene"><img src="movie-lighting-v27/movie-front-v27.png" alt="校准侧向日光、冷色阴影和局部补光后的原生渲染"><figcaption>原生渲染。岸台、水面、云层、材质绘制与人物仍有差距，未达到一比一。网页天空显示仍沿用此前校准，尚未完成跨引擎外观核对。</figcaption></figure>
<p><a href="movie-shore-v26/movie-front-v26.png">上一版正面</a> · <a href="movie-lighting-v27/appearance-comparison-v27.json">局部色彩诊断（非整体相似度）</a> · <a href="movie-lighting-v27/verification-v27.json">灯光与人物检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-lighting-v27">' in gallery:gallery=re.sub(r'<section id="movie-lighting-v27">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影日光与阴影 v27

Suzume_scene_movie_lighting_v27.blend：完整昼景、门、混元身体、独立头模与异世界。第 72 帧为开门。
本版根据电影参照进行了四组低分辨率试渲染，再检查完整尺寸的正面和斜视。
采用更偏侧面的日光方向、较弱环境光，以及范围缩小的右侧立面补光。
原生世界节点将天空显示与漫反射环境照明分开校准；反射天空权重单独设置。这是外观近似，并非制作现场的实测照明。

2362 个昼景网格和当前电影相机保持不变。人物、独立头模、脚部间隙、穿门分隔和开门照明驱动均在重新打开文件后检查。
movie-front-v27.png：正面原生渲染。
movie-left-oblique-v27.png：与前版相同机位的斜视。
trial-*.png：四组过程对照，不是最终渲染。
appearance-comparison-v27.json：手工选取的局部色彩区域，仅用于诊断照明，不是整体相似度或一比一验收。

网页：http://127.0.0.1:8931/viewer/candidate-v27.html
网页同步了太阳的世界坐标、方向、强度和立面补光参数；天空色彩保留此前网页校准，实际显示和旋转交互仍待复测。
岸台、水面、云层、材质绘制、人物细节与另一幅关门海报场景仍未完成一比一校准。
稳定原生 v19、默认网页 v17 和此前候选全部保留。
''',encoding='utf-8')
print('LIGHTING_27_RELEASED',result['nativeSha256'],flush=True)
