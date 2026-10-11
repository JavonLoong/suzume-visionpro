"""Publish reviewed front/oblique renders and the complete steel candidate."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-steel-v25'
def read(n):return json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v25.json');b=read('browser-geometry-verification-v25.json');review=read('visual-review-v25.json');integration=read('integration-v25.json')
assert v['freshReopenVerified'] and v['charactersAndPortalPreserved'] and v['closedStructuralSections']==57
assert v['allOtherDayMeshesUnchanged']==899 and v['attachedIvyLeaves']==202
assert b['allNativeMeshPositionBuffersMatch'] and b['newParts']==732 and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['obliqueReviewed']
native=O/'Suzume_scene_movie_steel_v25.blend';images=[O/'movie-front-v25.png',O/'movie-left-oblique-v25.png'];assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in images})==2
page=R/'viewer/candidate-v25.html'
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v25.html',timeout=10) as response:assert response.status==200 and response.read()==page.read_bytes()
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/suzume-posed-v17.gltf',timeout=10) as response:assert response.status==200
result={'revision':25,'role':'Movie I-section steelwork and attached ivy comparison candidate','nativeFile':'movie-steel-v25/Suzume_scene_movie_steel_v25.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),
    'newParts':732,'closedStructuralSections':57,'columns':26,'attachedIvyLeaves':202,'nativeFrontAndObliqueReviewed':True,
    'bodyHeadFeetAndPortalPreserved':True,'otherDayMeshesUnchanged':899,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,
    'browserCandidate':'viewer/candidate-v25.html','browserGeometrySyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'glslDriverCompilationVerified':False,
    'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v25.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
integration['visualReviewPending']=False;integration['visualReview']='visual-review-v25.json';(O/'integration-v25.json').write_text(json.dumps(integration,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v25_movie_steel_and_attached_ivy_comparison_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=25;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v25.html';status['scene']['movieSteelGeometryVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-steel-v25"><h2>电影钢架与实体工字梁 · v25（候选）</h2>
<p>两根可见主柱、两段弯梁与左侧细拉杆按电影帧重新定位，原来横穿门后背景的错误梁已移除。整圈保留 26 根立柱，工字截面、底板和锚栓均为实体；新攀藤包含 202 片带茎与叶柄的叶片。</p>
<p><a href="movie-steel-v25/Suzume_scene_movie_steel_v25.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v25.html">可旋转网页候选版</a>（运行效果待复测） · <a href="movie-steel-v25/movie-left-oblique-v25.png">钢架与攀藤斜视</a></p>
<figure class="scene"><img src="movie-steel-v25/movie-front-v25.png" alt="实体工字形钢架和附着攀藤的完整三维场景"><figcaption>原生渲染。镜头、建筑、人物和穿门分隔保留；隐藏钢架仍为推定，水岸、云层和人物细节尚未达到一比一。</figcaption></figure>
<p><a href="movie-projection-v24/movie-front-v24.png">上一版正面</a> · <a href="movie-steel-v25/verification-v25.json">截面凹槽、封闭性和人物校验</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-steel-v25">' in gallery:gallery=re.sub(r'<section id="movie-steel-v25">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影钢架与实体工字梁 v25

Suzume_scene_movie_steel_v25.blend：完整昼景、门、人物和异世界。第 72 帧为开门。
Movie steelwork v25 — complete radial structure：整圈钢架和附着攀藤，共 732 个可编辑部件。
26 根立柱、断裂径向肋、两段电影可见弯梁、左侧细拉杆、底板和锚栓均为三维构件。
57 个结构截面已检查封闭性；主柱腹板、翼缘与凹槽用射线区分。202 片叶片带有茎和叶柄。

电影主柱和弯梁采用当前镜头下的手工标记，并反投影到推定的 20.8 单位钢架圆环。
柱顶、断口的隐藏部分和后方钢架不是已知官方尺寸，仍属推定。
锈蚀为三维位置驱动的程序材质，未使用旧的条纹图像。右侧补光按比例后移并扩大。
其余 899 个昼景网格、混元身体与独立头模、脚部间隙、穿门裁切和开门照明均通过重新打开检查。

movie-front-v25.png：正面原生渲染。
movie-left-oblique-v25.png：与 v24 相同机位的钢架斜视渲染。
movie-front-initial-v25.png 与 steel-diffuse-trial-*.png：过程对照，非最终交付渲染。
网页：http://127.0.0.1:8931/viewer/candidate-v25.html
网页全部新构件坐标、脚本、材质代码构造和 HTTP 资源已检查；实际 WebGL 编译、显示和交互仍待复测。

水岸台基、连续管道、门基砖石、云层、水面和人物细节仍需继续校准。尚未达到一比一。
稳定原生 v19、默认网页 v17、v24 及此前候选均保留。
''',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
