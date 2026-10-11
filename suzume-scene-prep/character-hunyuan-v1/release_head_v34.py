from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).parent;O=R/'movie-head-v34';read=lambda n:json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v34.json');b=read('browser-verification-v34.json');a=read('integration-v34.json');review=read('visual-review-v34.json');native=O/'Suzume_scene_movie_head_v34.blend'
assert v['freshReopenVerified'] and v['bodyFeetAndGripPreserved'] and v['sharedRigAndSpatialPartitionVerified']
assert len(v['closedPonytailParts'])==6 and all(p['boundaryEdges']==0 for p in v['closedPonytailParts'])
assert review['sceneFrontReviewed'] and review['headFrontReviewed'] and review['headBackReviewed'] and review['headSideReviewed']
assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256']
for n in ['movie-front-v34.png','head-front-v34.png','head-back-v34.png','head-side-v34.png']:assert (O/n).stat().st_mtime>native.stat().st_mtime
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');alias=V/'suzume-full-scene.blend';previous=R/'Suzume_scene_Hunyuan_v19.blend'
oldhash=hashlib.sha256(previous.read_bytes()).hexdigest();assert hashlib.sha256(alias.read_bytes()).hexdigest() in [oldhash,v['nativeSha256']],'Primary scene changed externally; leave that file intact.'
shutil.copy2(native,alias);assert hashlib.sha256(alias.read_bytes()).hexdigest()==v['nativeSha256']
result={'revision':34,'nativeFile':'movie-head-v34/Suzume_scene_movie_head_v34.blend','nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'currentNativeRevision':34,'previousNativeRevisionPreserved':19,'headSource':a['headSource'],'independentClosedPonytailParts':6,'bodyFeetAndGripPreserved':True,'sharedSpatialHeadMeshVerified':True,'frontBackSideRenderedAndReviewed':True,'browserCandidate':'viewer/candidate-v34.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v34.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v34_independent_mathematical_head';status['scene'].update({'currentNative':result['nativeFile'],'revision':34,'headGeometryRevision':34,'headGeometrySource':a['headSource'],'headReconstruction':'Independent mathematical face, eyes, scalp, pins and six closed ponytail volumes; Hunyuan body retained. The fused Hunyuan tail deformation v33 was rejected.','nativePartitionVerifiedV34':True,'movieCalibrationCandidate':result['nativeFile'],'movieCalibrationCandidateRevision':34,'movieCalibrationBrowserCandidate':'http://127.0.0.1:8931/viewer/candidate-v34.html','browserCandidateAsset':'viewer/character-v34/suzume-posed-v34.gltf','moviePonytailLengthVerified':True});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-head-v34"><h2>独立头部与封闭发束 · v34（重建中）</h2>
<p>保留混元身体与握门姿态，头部改用独立可编辑的数学部件。马尾由六束封闭实体构成，长度与弧度可以调整，后颈不会随马尾拉伸。</p>
<p><a href="movie-head-v34/Suzume_scene_movie_head_v34.blend">当前完整 Blender 场景</a> · <a href="viewer/candidate-v34.html">可旋转网页候选</a>（显示待复测） · <a href="viewer/character-v34/suzume-posed-v34.glb">当前人物 GLB</a> · <a href="viewer/candidate-v32.html">混元头模对照</a></p>
<figure class="scene"><img src="movie-head-v34/movie-front-v34.png" alt="独立头部接入完整门场景"><figcaption>人物发梢按远景参照校准；脸部神态、发束轮廓、环境细节和关门场景仍未达到一比一。</figcaption></figure>
<details><summary>查看头模的正面、背面和侧面</summary><img style="max-width:32%" src="movie-head-v34/head-front-v34.png" alt="独立头模正面"><img style="max-width:32%" src="movie-head-v34/head-back-v34.png" alt="发束背面"><img style="max-width:32%" src="movie-head-v34/head-side-v34.png" alt="后颈和发束侧面"><p>中性灯光下的三维检查；侧面与隐藏部分仍为重建推定。</p></details>
<p><a href="movie-head-v34/verification-v34.json">封闭发束、双世界分区与导出检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-head-v34">' in gallery:gallery=re.sub(r'<section id="movie-head-v34">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text(f'''独立头部与实体发束 v34

当前原生文件：Suzume_scene_movie_head_v34.blend，第 72 帧为开门姿势。主场景 suzume-full-scene.blend 已同步至本版；旧版文件保留。
身体继续使用混元 3.1 重建，头部采用既有 v18 数学部件重新整合，马尾分为六束封闭实体，并按电影远景调整长度、弧度和发梢聚拢。此次没有新的混元提交。
v33 试验发现混元头模下段马尾与后颈存在融合连接，拉伸导致薄片；该试验未发布为当前模型。
马尾与皮肤、后颈和头皮没有共享顶点，改变发束不会拉扯这些部件。身体、脚部和右手的全部顶点与 v32 完全一致。
新的头部使用共享几何的日间/异世界副本和互补空间裁切。六束马尾均经过闭合边检查。
后背方向的 {a['backClothRays']} 条射线检查最小间隙约 {a['minimumBackClothRayGap']*100:.1f} 厘米；这不是所有方向的完整碰撞证明。

movie-front-v34.png：完整门场景；head-front/back/side-v34.png：中性灯光头部检查。
网页候选：http://127.0.0.1:8931/viewer/candidate-v34.html
人物 GLB：../viewer/character-v34/suzume-posed-v34.glb
导出包含 12 个头部材质分区，头部 135992 三角面，身体 408817 三角面。与原生顶点的误差小于百万分之一米。
网页资源和脚本已检查，实际浏览器显示尚未复测；默认网页 v17 保留，v32 提供原混元头模对照。

整体仍未达到一比一。面部身份、下颌和后脑轮廓、发梢形状、材质风格、宽视角夜空和关门海报等仍需校准。
近景相机试验保存在 movie-sky-v33，尚未接受，本轮没有修改夜空。
''',encoding='utf-8');print('HEAD_34_RELEASED',result['nativeSha256'],flush=True)
