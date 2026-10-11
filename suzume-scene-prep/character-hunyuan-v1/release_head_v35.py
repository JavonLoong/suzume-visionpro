from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).parent;O=R/'movie-head-v35';read=lambda n:json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v35.json');b=read('browser-verification-v35.json');a=read('integration-v35.json');fit=read('fit-v35.json');review=read('visual-review-v35.json');native=O/'Suzume_scene_movie_head_v35.blend'
assert v['freshReopenVerified'] and v['bodyFeetAndGripPreserved'] and v['sharedRigAndSpatialPartitionVerified']
assert len(v['closedPonytailParts'])==6 and all(p['boundaryEdges']==0 for p in v['closedPonytailParts'])
assert review['accepted'] and all(review[k] for k in ['sceneFrontReviewed','headFrontReviewed','headBackReviewed','headSideReviewed'])
assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256']
for n in ['movie-front-v35.png','head-front-v35.png','head-back-v35.png','head-side-v35.png']:assert (O/n).stat().st_mtime>native.stat().st_mtime
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');alias=V/'suzume-full-scene.blend'
assert hashlib.sha256(alias.read_bytes()).hexdigest() in [a['sourceSha256'],v['nativeSha256']],'Primary scene changed externally; preserve it.'
shutil.copy2(native,alias);assert hashlib.sha256(alias.read_bytes()).hexdigest()==v['nativeSha256']
result={'revision':35,'nativeFile':'movie-head-v35/Suzume_scene_movie_head_v35.blend','nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'currentNativeRevision':35,'previousNativeRevisionPreserved':34,'headSource':a['headSource'],'headPlacementAndPonytailShapeFitted':True,'independentClosedPonytailParts':6,'bodyFeetAndGripPreserved':True,'sharedSpatialHeadMeshVerified':True,'frontBackSideRenderedAndReviewed':True,'browserCandidate':'viewer/candidate-v35.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v35.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v35_head_proportion_and_solid_ponytail';status['scene'].update({'currentNative':result['nativeFile'],'revision':35,'headGeometryRevision':35,'headGeometrySource':a['headSource'],'headReconstruction':'Independent mathematical head with calibrated placement and a continuous overlapping ponytail core; Hunyuan body retained. The v35 envelope-only deformation trial was rejected.','nativePartitionVerifiedV35':True,'movieCalibrationCandidate':result['nativeFile'],'movieCalibrationCandidateRevision':35,'movieCalibrationBrowserCandidate':'http://127.0.0.1:8931/viewer/candidate-v35.html','browserCandidateAsset':'viewer/character-v35/suzume-posed-v35.gltf','moviePonytailWidthAndLengthVerified':True});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-head-v35"><h2>头部比例与马尾轮廓 · v35（重建中）</h2>
<p>按电影主机位下移头部、收窄后脑，马尾改为中段饱满、下端收尖的连续实体。背面、正面和侧面均经过原生渲染检查。</p>
<p><a href="movie-head-v35/Suzume_scene_movie_head_v35.blend">当前完整 Blender 场景</a> · <a href="viewer/candidate-v35.html">新版可旋转网页候选</a>（浏览器连接失败，显示待复测） · <a href="viewer/character-v35/suzume-posed-v35.glb">当前人物 GLB</a></p>
<figure class="scene"><img src="movie-head-v35/movie-front-v35.png" alt="头部校准后的完整门场景"><figcaption>身体、脚部、握门姿态和穿门分区保留。脸部神态、材质、庭院细节和关门场景仍需校准。</figcaption></figure>
<details><summary>查看头模三视角</summary><img style="max-width:32%" src="movie-head-v35/head-front-v35.png" alt="头模正面"><img style="max-width:32%" src="movie-head-v35/head-back-v35.png" alt="完整马尾背面"><img style="max-width:32%" src="movie-head-v35/head-side-v35.png" alt="实体发束侧面"><p>侧面与电影中不可见的部分仍为三维重建推定。</p></details>
<p><a href="movie-head-v35/verification-v35.json">几何与分区检查</a> · <a href="movie-head-v35/fit-v35.json">参考轮廓的采样约束</a> · <a href="viewer/candidate-v34.html">上一版对照</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-head-v35">' in gallery:gallery=re.sub(r'<section id="movie-head-v35">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text(f'''头部比例与马尾轮廓 v35

当前完整场景：Suzume_scene_movie_head_v35.blend，第 72 帧为开门姿势。
主场景 suzume-full-scene.blend 已同步；v34 和更早原生文件保留。
身体为混元 3.1 模型；当前独立头部和马尾为数学几何，此轮没有新的混元生成。
后脑按电影主机位校准位置和比例，颈部底部固定在原衣领处。
马尾使用一个连续的封闭主体、重叠发束和较短的左侧发梢，所有六部分均为有厚度的封闭网格。
早期直接拉宽旧发束会产生内部空洞，已经弃用；诊断图片保留在 rejected-envelope-warp。

电影原图 2552×1656 中的 17 个马尾高度采样，左右边界最大拟合残差约 {fit['maximumPonytailBoundaryResidualPixels']:.2f} 像素；人工参考标注自身约有 3 像素误差。这些局部约束不能证明整个人物或整个场景一比一。
当前后背方向 {a['backClothRays']} 条射线的最小衣服间隙约 {a['minimumBackClothRayGap']*100:.1f} 厘米；这不是所有方向的完整碰撞证明。
身体、脚部与右手所有顶点保持 v32 的结果。日间与异世界头部共享几何和骨架，仍以门平面作互补空间裁切。

movie-front-v35.png：完整场景。head-front/back/side-v35.png：中性光照三视角检查。
网页候选：http://127.0.0.1:8931/viewer/candidate-v35.html
人物 GLB：../viewer/character-v35/suzume-posed-v35.glb
导出含 12 个头部材质分区，共 544809 个三角面，与原生模型的顶点误差小于百万分之一米。
浏览器工具枚举超时，Chrome 入口返回不可用；当前只验证了网页资源、脚本语法和导出几何，未验证 GPU 实际显示。默认网页仍是 v17，新版本请用候选链接打开。

仍未达到一比一：面部身份和神态、后颈发际线、侧面深度、材质风格、夜空和庭院细节、关门海报场景仍待完善。
''',encoding='utf-8');print('HEAD_35_RELEASED',result['nativeSha256'],flush=True)
