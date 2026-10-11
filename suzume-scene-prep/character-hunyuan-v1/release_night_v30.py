"""Register the reviewed night candidate and preserve previous stable entry points."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-night-v30'
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v30.json');b=read('browser-verification-v30.json');review=read('visual-review-v30.json');appearance=read('night-appearance-v30.json')
assert v['freshReopenVerified'] and v['preservedDayMeshes']==2362 and v['characterHeadFeetAndPortalPreserved'] and v['cameraAndDayLightingPreserved']
assert v['closedSpatialCloudVolumes']==10 and not v['referenceImageUsedInSkyOrClouds']
assert b['cloudHelperExecuted'] and b['nativeAndBrowserTransformedCornersMatched']==80 and b['inlineScriptsParsed']>=1
assert review['frontReviewed'] and review['nightObliqueReviewed']
native=O/'Suzume_scene_movie_night_v30.blend';images=[O/'movie-front-v30.png',O/'night-oblique-v30.png'];assert all(p.stat().st_mtime>native.stat().st_mtime for p in images)
for name in ['viewer/candidate-v30.html','viewer/suzume-posed-v17.gltf','movie-surfaces-v28/reference-opening.jpg','movie-surfaces-v28/surface-validity-mask-v28.png']:
    with urllib.request.urlopen('http://127.0.0.1:8931/'+name,timeout=10) as response:assert response.status==200 and response.read()==(R/name).read_bytes()
result={'revision':30,'nativeFile':'movie-night-v30/Suzume_scene_movie_night_v30.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'nativeFrontAndNightObliqueReviewed':True,'cloudVolumeCount':10,'priorDayMeshesPreserved':2362,'bodyHeadFeetAndPortalPreserved':True,'waterRevisionPreserved':29,'referenceImageUsedInSkyOrClouds':False,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v30.html','browserTransformsMaterialsSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'nativeBrowserAppearanceEquivalenceVerified':False,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v30.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v30_movie_spatial_night_cloud_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=30;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v30.html';status['scene']['movieNightCloudsVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-night-v30"><h2>门内夜空与三维云层 · v30（候选）</h2>
<p>夜空改为深蓝紫色，十组云体重新调整位置、厚度和疏密。云层具有纵深，可从侧面观察；独立混元头模、脚部修正及穿门分区保留。</p>
<p><a href="movie-night-v30/Suzume_scene_movie_night_v30.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v30.html">可旋转网页候选版</a>（显示待复测） · <a href="movie-night-v30/night-oblique-v30.png">异世界斜视渲染</a></p>
<figure class="scene"><img src="movie-night-v30/movie-front-v30.png" alt="深蓝紫色夜空和空间云层的完整门场景"><figcaption>夜空与云体没有使用参照图片贴面。云形、夜景地平线、人物姿态以及另一幅关门场景仍有差距，未达到一比一。</figcaption></figure>
<p><a href="movie-night-v30/verification-v30.json">模型、人物和分区检查</a> · <a href="movie-night-v30/night-appearance-v30.json">局部色彩诊断（非整体相似度）</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-night-v30">' in gallery:gallery=re.sub(r'<section id="movie-night-v30">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门内夜空与三维云层 v30

Suzume_scene_movie_night_v30.blend：完整昼景、门、混元身体、独立混元头模及异世界。第 72 帧为开门姿态。
电影镜头下的夜空改为深蓝紫色；十组闭合云体通过三维密度场产生厚度、疏密和不规则云缘。
云层中心依据电影画面定位，纵深、背面轮廓与看不见的云体属于推定。天空及云体不含参照图片贴面。
独立 Night 场景曝光从 0 调整到 0.8，以匹配从门口观察时的曝光。

2362 个庭院网格、99 个未修改材质图、人物、头模、脚部位置和穿门互补裁切重新打开检查通过。
上一版水面、墙面、镜头与昼景灯光保留。穿门只显示对应空间中的身体部分。
movie-front-v30.png：完整正面。night-oblique-v30.png：另设机位的异世界斜视检查，不改动保存文件的参考镜头。

网页候选：http://127.0.0.1:8931/viewer/candidate-v30.html
已检查网页云体参数、坐标转换、脚本语法和本地资源。浏览器控制连接超时，GPU 显示和跨引擎外观一致性未验证。
尚未达到一比一：云形及低空雾、远处地平线、人物姿态与头发、细波光和铺石，以及关门海报场景仍需校准。
此前版本及默认入口保留。
''',encoding='utf-8')
print('NIGHT_30_RELEASED',result['nativeSha256'],flush=True)
