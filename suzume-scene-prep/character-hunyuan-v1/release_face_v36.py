from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).parent;O=R/'movie-face-v36';read=lambda n:json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v36.json');b=read('browser-verification-v36.json');a=read('integration-v36.json');fit=read('fit-v36.json');review=read('visual-review-v36.json');native=O/'Suzume_scene_movie_face_v36.blend'
assert v['freshReopenVerified'] and v['bodyFeetAndGripPreserved'] and v['sharedRigAndSpatialPartitionVerified'] and v['v35PonytailPreservedExactly']
assert len(v['closedPonytailParts'])==6 and all(p['boundaryEdges']==0 for p in v['closedPonytailParts'])
assert review['accepted'] and all(review[k] for k in ['sceneFrontReviewed','headFrontReviewed','headBackReviewed','headSideReviewed','headPortraitReviewed'])
assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256']
for n in ['movie-front-v36.png','head-front-v36.png','head-back-v36.png','head-side-v36.png','head-portrait-v36.png']:assert (O/n).stat().st_mtime>native.stat().st_mtime
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');alias=V/'suzume-full-scene.blend'
assert hashlib.sha256(alias.read_bytes()).hexdigest() in [a['sourceSha256'],v['nativeSha256']],'Primary scene changed externally; preserve it.'
shutil.copy2(native,alias);assert hashlib.sha256(alias.read_bytes()).hexdigest()==v['nativeSha256']
result={'revision':36,'nativeFile':'movie-face-v36/Suzume_scene_movie_face_v36.blend','nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'currentNativeRevision':36,'previousNativeRevisionPreserved':35,'headSource':a['headSource'],'faceProportionsAndFrontalHairlineRefined':True,'v35PonytailPreservedExactly':True,'bodyFeetAndGripPreserved':True,'sharedSpatialHeadMeshVerified':True,'frontBackSideAndPortraitRenderedAndReviewed':True,'browserCandidate':'viewer/candidate-v36.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v36.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v36_official_reference_face_refinement';status['scene'].update({'currentNative':result['nativeFile'],'revision':36,'headGeometryRevision':36,'headGeometrySource':a['headSource'],'headReconstruction':'Mathematical face, eyes, raised nose, lower jaw and frontal hairline calibrated against the official character still; v35 solid ponytail and Hunyuan body retained.','nativePartitionVerifiedV36':True,'movieCalibrationCandidate':result['nativeFile'],'movieCalibrationCandidateRevision':36,'movieCalibrationBrowserCandidate':'http://127.0.0.1:8931/viewer/candidate-v36.html','browserCandidateAsset':'viewer/character-v36/suzume-posed-v36.gltf','officialFaceProportionsRefined':True});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-face-v36"><h2>五官比例与刘海 · v36（重建中）</h2>
<p>对照官方人物图收窄眼白、调整鼻子位置和下颌弧线，重新排列前额刘海，增加眼线与微张嘴部的几何细节。马尾、颈部底端、身体与穿门分区保留。</p>
<p><a href="movie-face-v36/Suzume_scene_movie_face_v36.blend">当前完整 Blender 场景</a> · <a href="viewer/candidate-v36.html">可旋转网页候选</a>（显示待实测） · <a href="viewer/character-v36/suzume-posed-v36.glb">当前人物 GLB</a></p>
<figure class="scene"><img style="max-width:650px" src="movie-face-v36/head-portrait-v36.png" alt="官方参照校准后的独立三维头部"><figcaption>正面比例有改进，但神态、鼻部深度、头发分束与材质风格仍未达到一比一。</figcaption></figure>
<details><summary>查看完整场景、背面与侧面</summary><img src="movie-face-v36/movie-front-v36.png" alt="完整门场景"><img style="max-width:48%" src="movie-face-v36/head-back-v36.png" alt="保留的马尾背面"><img style="max-width:48%" src="movie-face-v36/head-side-v36.png" alt="面部和头发侧面"><p>衣领仍有混元网格的锯齿边缘，尚需修复；侧面与不可见部位仍为重建推定。</p></details>
<p><a href="movie-face-v36/verification-v36.json">模型、材质与穿门分区检查</a> · <a href="movie-face-v36/fit-v36.json">局部五官比例约束</a> · <a href="viewer/candidate-v35.html">上一版对照</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-face-v36">' in gallery:gallery=re.sub(r'<section id="movie-face-v36">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text(f'''五官比例与刘海 v36

当前完整场景：Suzume_scene_movie_face_v36.blend，第 72 帧为开门姿势。
主场景 suzume-full-scene.blend 已同步，v35 与更早文件保留。
人物身体为混元 3.1 模型，当前头部为独立数学几何，此轮没有新的混元生成。
以官方 680×390 人物图的眼睛间距和眼线角度对齐正面比例，缩短下脸、调整下颌和鼻子、收窄并抬高眼白，增加上眼线厚度，重新排列前额刘海。
嘴部为贴合脸部的曲面浮雕，表现微张的深色开口与上方牙齿颜色；内部口腔和隐藏牙列尚未重建。
12 个手工脸缘采样的平均残差约 {fit['outlineMeanErrorInStudioPixels']:.1f} 像素，最大约 {fit['outlineMaxErrorInStudioPixels']:.1f} 像素，坐标属于 650×800 检查图。参照标注自身约有 3 像素误差，且相机姿态未完全匹配；这些局部采样不能证明整个人物一比一。

马尾和颈部底端的顶点保持 v35 结果；身体、脚部与握门姿态保持 v32 结果。
头部的日间/异世界版本共享几何与骨架，采用互补门平面裁切。六束马尾均保留闭合网格。
导出共 544809 个三角面，12 个头部材质分区。GLTF 与原生顶点误差小于百万分之一米。

head-portrait-v36.png：正面近景。head-front/back/side-v36.png：中性灯光三视角。movie-front-v36.png：完整场景。
网页候选：http://127.0.0.1:8931/viewer/candidate-v36.html
人物 GLB：../viewer/character-v36/suzume-posed-v36.glb
网页资源、脚本语法和模型已检查，实际浏览器显示未验证；默认网页仍为 v17。

尚未达到一比一：面部神态、鼻部深度与材质风格、衣领锯齿边缘、门板近景相机、夜空与庭院细节以及关门海报场景仍需校准。
''',encoding='utf-8');print('FACE_36_RELEASED',result['nativeSha256'],flush=True)
