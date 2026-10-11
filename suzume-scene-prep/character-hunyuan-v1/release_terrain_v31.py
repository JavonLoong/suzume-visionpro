"""Publish the inspected terrain candidate without promoting unverified browser output."""
from pathlib import Path
import json,hashlib,re,urllib.request
R=Path(__file__).parent;O=R/'movie-terrain-v31';read=lambda p:json.loads((O/p).read_text(encoding='utf-8'))
v=read('verification-v31.json');b=read('browser-verification-v31.json');review=read('visual-review-v31.json');native=O/'Suzume_scene_movie_terrain_v31.blend'
assert v['freshReopenVerified'] and v['bodyHeadFeetAndPortalPreserved'] and v['closedTerrainExtension'] and v['maximumAnnotatedSkylineErrorPixels']<3
assert v['nearGroundVerticesExactlyPreserved']==b['nearGroundVerticesPreserved'] and b['separateSourceAndDestinationTargetsVerified']
assert review['frontReviewed'] and review['wideNightReviewed']
for p in ['movie-front-v31.png','night-wide-v31.png']:assert (O/p).stat().st_mtime>native.stat().st_mtime
for p in ['viewer/candidate-v31.html','movie-terrain-v31/ground-world-v31.bin','movie-terrain-v31/extension-vertices-v31.bin','movie-terrain-v31/extension-indices-v31.bin']:
    with urllib.request.urlopen('http://127.0.0.1:8931/'+p,timeout=10) as response:assert response.status==200 and response.read()==(R/p).read_bytes()
result={'revision':31,'nativeFile':'movie-terrain-v31/Suzume_scene_movie_terrain_v31.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'nativeFrontAndWideNightReviewed':True,'nearGroundVerticesPreserved':v['nearGroundVerticesExactlyPreserved'],'preservedDayMeshes':v['preservedDayMeshes'],'bodyHeadFeetAndPortalPreserved':True,'continuousClosedTerrainExtension':True,'spatialMistVolumes':2,'maximumManuallyAnnotatedSkylineErrorPixels':v['maximumAnnotatedSkylineErrorPixels'],'skylineCheckScope':'Eight manually selected visible points at the calibrated movie camera only; not overall or all-angle similarity.','browserCandidate':'viewer/candidate-v31.html','browserRuntimeVerified':False,'nativeBrowserAppearanceEquivalenceVerified':False,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v31.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v31_movie_terrain_and_mist_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=31;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v31.html';status['scene']['movieDistantTerrainVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-terrain-v31"><h2>门内远景与空间薄雾 · v31（候选）</h2>
<p>按电影参照校准远处坡线，扩展成连续、有厚度的地形，并加入两层空间薄雾。人物附近与花草所在的地面保持原位置。</p>
<p><a href="movie-terrain-v31/Suzume_scene_movie_terrain_v31.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v31.html">可旋转网页候选</a>（显示待复测） · <a href="movie-terrain-v31/night-wide-v31.png">异世界宽视角</a></p>
<figure class="scene"><img src="movie-terrain-v31/movie-front-v31.png" alt="坡线和薄雾修正后的完整门场景"><figcaption>远景坡线按可见位置拟合，隐藏地形和雾的深度仍为推定。人物、草地细节、云形和另一幅关门场景尚未完成一比一。</figcaption></figure>
<p><a href="movie-terrain-v31/verification-v31.json">真实网格坡线、地面与人物检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-terrain-v31">' in gallery:gallery=re.sub(r'<section id="movie-terrain-v31">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门内远景地形与空间薄雾 v31

打开 Suzume_scene_movie_terrain_v31.blend，第 72 帧为开门姿态。场景保留完整庭院、门、混元身体、独立头模和穿门空间分区。
近处半径 85 米范围内的 5681 个地面顶点位置保持；远处坡面重新拟合，外侧扩展为封闭的连续地形，天空及云层沿用 v30。
原机位下，8 个手工标出的坡线点与实际网格投影相差不超过 1 像素。此检查仅覆盖这些可见点，不代表整体一比一。
两层薄雾采用有限三维密度场，保留真实遮挡；地形深度、背面和雾的分布仍属推定。

movie-front-v31.png：完整正面；night-wide-v31.png：异世界宽视角检查。
网页候选：http://127.0.0.1:8931/viewer/candidate-v31.html
网页地形数据与原生共用，雾使用深度纹理停止积分，避免覆盖前景人物。已检查几何、绘制路径与资源，GPU 和实际浏览器显示仍未验证。
整体尚未达到一比一。前序版本、稳定原生 v19、默认网页 v17 均保留。
''',encoding='utf-8');print('TERRAIN_31_RELEASED',result['nativeSha256'],flush=True)
