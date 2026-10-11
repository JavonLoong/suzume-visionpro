from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-arches-v49';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v49.json');review=read('visual-review-v49.json');b=read('browser-code-verification-v49.json');web=read('browser-http-verification-v49.json');spec=read('browser-arches-v49.json');native=O/'Suzume_dual_scene_arches_v49.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved'])
assert len(v['addedSolids'])==68 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedSolids'])
assert len(v['structuralOpeningProbes'])==29 and len(v['infillSurroundContacts'])==29
assert all(q['intersectingTrianglePairs']>0 for q in v['infillSurroundContacts'])
assert len(v['upperWindowClearanceGrid'])==60 and all(q['clearDistanceMeters']==1 for q in v['upperWindowClearanceGrid'])
projection=read('arch-projection-comparison-v49.json');assert projection['nativeSha256']==v['nativeSha256'] and projection['maximumObservedAnchorErrorPixels']<1.5
images=read('packed-image-preservation-v49.json');assert images['nativeSha256']==v['nativeSha256'] and images['allPackedImageBytesPreserved']
assert all(b[k] for k in ['positionsNormalsUVsMatchNativeExactly','previousUnaffectedGeometryMaterialsAndIvyPreserved','allMaterialInstancesReused','previousPartitionBucketReplaced'])
assert b['previousFacadeBucketsReplaced']==6 and b['buckets']==10
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','archDetailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v49.png','arch-detail-v49.png','poster-oblique-v49.png','arch-oblique-detail-v49.png']:
 assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':49,'nativeFile':'poster-arches-v49/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'reconstructedArchUnits':29,'closedNewSolids':68,'upperWindowOldSillRemoved':True,'partitionRecessClearanceVerified':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v49.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v49.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v49_poster_arches';status['scene'].update({'currentNative':result['nativeFile'],'revision':49,'posterNativeCalibrationRevision':49,'posterNativeVerifiedV49':True,'posterArchedRecessesReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-arches-v49"><h2>尖拱与立面凹深重建 · v49（重建中）</h2>
<p>左侧大尖拱、细小凹槽及下方檐线重建为实体，共 29 处拱形单元。清除上层窗户下沿的旧窗台，并让局部室内隔墙退到凹槽后方。</p>
<p><a href="viewer/poster-v49.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-arches-v49/Suzume_dual_scene_arches_v49.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-arches-v49/poster-front-v49.png" alt="拱廊修正后的完整海报场景"><figcaption>拱形轮廓与参照更接近；被遮挡的结构、植物、人物和异世界仍在校准，整体尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、细节和旋转视角</summary><img src="poster-arches-v49/arch-comparison-v49.png" alt="拱形立面修正前后与参照对比"><img src="poster-arches-v49/arch-detail-v49.png" alt="尖拱与连续檐线"><img src="poster-arches-v49/arch-oblique-detail-v49.png" alt="拱形构件厚度和凹深"><img src="poster-arches-v49/poster-oblique-v49.png" alt="完整庭院侧向渲染"></details>
<p>已检查 68 个新实体的封闭性、凹槽净空、上层窗户遮挡及网页几何。灰色嵌板的结构和被梁遮挡的拱形仍属推断，浏览器实际显示待验证。</p>
<p><a href="poster-arches-v49/verification-v49.json">模型检查</a> · <a href="poster-arches-v49/visual-review-v49.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-arches-v49">' in gallery:gallery=re.sub(r'<section id="poster-arches-v49">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''尖拱与立面凹深重建 v49

完整模型：Suzume_dual_scene_arches_v49.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

29 处大尖拱与小凹槽有真实轮廓、围边和凹入嵌板。三段立面及下方檐线按参照重建；两道隔墙在凹槽后方退让，并保留下部与室内深处的分隔。新增共 68 个封闭实体。
移除了高窗下沿残留的旧窗台。60 个高窗采样位置向后方一米内没有旧墙或窗台遮挡，29 处拱形凹槽的中心净空和嵌板接合也通过检查。
保留的旧面坐标、UV、既有材质和贴图已核对，电影人物与异世界模型保持原有状态。

海报网页：http://127.0.0.1:8931/viewer/poster-v49.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

正面、局部、侧向渲染及网页几何、资源检查已完成。灰色嵌板性质、遮挡后的拱形与不可见结构仍为推断。浏览器实际 GPU 显示仍待验证，整体尚未达到一比一。
''',encoding='utf-8');print('ARCHES_49_RELEASED',v['nativeSha256'])
