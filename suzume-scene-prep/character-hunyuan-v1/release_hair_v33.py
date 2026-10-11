from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).parent;O=R/'movie-hair-v33';read=lambda n:json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v33.json');b=read('browser-verification-v33.json');a=read('integration-v33.json');review=read('visual-review-v33.json');native=O/'Suzume_scene_movie_hair_v33.blend'
assert v['freshReopenVerified'] and v['bodyFeetGripAndPinsExactlyPreserved'] and v['pairedSpatialPartitionVerified'] and v['headTopologyPreserved']
assert review['frontReviewed'] and review['backReviewed'] and review['sideReviewed'] and review['acceptedContinuousCurve']
assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256']
for n in ['movie-front-v33.png','hair-back-v33.png','hair-side-v33.png']:assert (O/n).stat().st_mtime>native.stat().st_mtime
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');alias=V/'suzume-full-scene.blend';previous=R/'Suzume_scene_Hunyuan_v19.blend'
oldhash=hashlib.sha256(previous.read_bytes()).hexdigest();alias_hash=hashlib.sha256(alias.read_bytes()).hexdigest();assert alias_hash in [oldhash,v['nativeSha256']],'Primary scene changed externally; leave that file intact.'
shutil.copy2(native,alias);assert hashlib.sha256(alias.read_bytes()).hexdigest()==v['nativeSha256']
result={'revision':33,'nativeFile':'movie-hair-v33/Suzume_scene_movie_hair_v33.blend','nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'currentNativeRevision':33,'previousNativeRevisionPreserved':19,'ponytailLengthAndContinuousDepthCurveUpdated':True,'bodyFeetGripAndPinsExactlyPreserved':True,'faceAndFrontScalpVerticesPreserved':True,'sharedSpatialHeadMeshVerified':True,'frontBackSideRenderedAndReviewed':True,'browserCandidate':'viewer/candidate-v33.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v33.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v33_hunyuan_ponytail_refinement';status['scene'].update({'currentNative':result['nativeFile'],'revision':33,'headGeometryRevision':33,'headGenerationRevision':17,'movieCalibrationCandidate':result['nativeFile'],'movieCalibrationCandidateRevision':33,'movieCalibrationBrowserCandidate':'http://127.0.0.1:8931/viewer/candidate-v33.html','moviePonytailLengthVerified':True});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-hair-v33"><h2>电影马尾长度与空间曲线 · v33（候选）</h2>
<p>马尾沿原有混元网格延长到参照中的上背部位置，并用连续曲线避开上衣；脸部、发卡、身体、脚部和握门姿态保留。</p>
<p><a href="movie-hair-v33/Suzume_scene_movie_hair_v33.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v33.html">可旋转网页候选</a>（显示待复测） · <a href="viewer/character-v33/suzume-posed-v33.glb">当前人物 GLB</a></p>
<figure class="scene"><img src="movie-hair-v33/movie-front-v33.png" alt="马尾轮廓调整后的完整门场景"><figcaption>发梢按远景参照位置校准；隐藏部分的发束曲线为三维推定，整体仍未达到一比一。</figcaption></figure>
<details><summary>查看马尾的背面和侧面</summary><img style="max-width:48%" src="movie-hair-v33/hair-back-v33.png" alt="完整人物的背面发束检查"><img style="max-width:48%" src="movie-hair-v33/hair-side-v33.png" alt="发束与衣服间隙的侧面检查"><p>中性灯光下的完整三维检查图；保留真实发束厚度，不是最终异世界光照。</p></details>
<p><a href="movie-hair-v33/verification-v33.json">原生几何与导出检查</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-hair-v33">' in gallery:gallery=re.sub(r'<section id="movie-hair-v33">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text(f'''电影马尾轮廓校准 v33

完整场景：Suzume_scene_movie_hair_v33.blend，第 72 帧为开门姿势。
在现有独立混元头模上局部延长马尾，保留原网格拓扑、顶点颜色和骨骼。正面脸部、前侧头皮、发卡、身体、脚部和右手位置均保留。
马尾沿连续三次曲线向后弯出，避开上衣。{a['shirtRayClearanceSamples']} 个下段发束顶点对应的背面射线检查保留至少约 {a['minimumHairToBackClothGap']*100:.1f} 厘米间隙；这不是所有方向的完整碰撞证明。
原机位的发梢对齐手工标出的参照像素，单点吻合不代表整体一比一。马尾侧面和深度是合理推定。

movie-front-v33.png：完整场景原生渲染。
hair-back-v33.png / hair-side-v33.png：背面与侧面的中性灯光检查。
trial-local-clearance 目录保留了第一轮弯折过急的试验，最终场景已改用连续曲线。
网页候选：http://127.0.0.1:8931/viewer/candidate-v33.html
人物导出和原生顶点误差小于 0.000001 米。网页脚本与资源通过检查，实际浏览器显示仍未复测。

独立头模的发丝表面、皮肤颜色接缝和面部特征仍需细化。近景相机拟合尚未接受，夜空本轮未修改，关门海报场景尚未完成一比一。
当前原生场景已更新至 v33；v19 旧文件保留，默认网页仍为 v17。
''',encoding='utf-8');print('HAIR_33_RELEASED',result['nativeSha256'],flush=True)
