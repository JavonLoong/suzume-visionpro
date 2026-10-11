from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-lower-facade-v50';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v50.json');review=read('visual-review-v50.json');b=read('browser-code-verification-v50.json');web=read('browser-http-verification-v50.json');spec=read('browser-lower-facade-v50.json');native=O/'Suzume_dual_scene_lower_facade_v50.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved'])
assert len(v['addedSolids'])==151 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedSolids'])
assert len(v['structuralOpeningProbes'])==36 and len(v['entranceFloorProbes'])==9
projection=read('lower-facade-projection-v50.json');assert projection['nativeSha256']==v['nativeSha256'] and projection['maximumAnchorErrorPixels']<1.5
images=read('packed-image-preservation-v50.json');assert images['nativeSha256']==v['nativeSha256'] and images['allPackedImageBytesPreserved']
fixtures=read('fixture-removal-verification-v50.json');assert fixtures['nativeSha256']==v['nativeSha256'] and fixtures['allSelectedComponentsFullyRemoved']
assert fixtures['groups']['bench']['components']==16 and fixtures['groups']['oldStair']['components']==7
assert all(b[k] for k in ['positionsNormalsUVsMatchNativeExactly','previousUnaffectedGeometryMaterialsAndIvyPreserved','allMaterialInstancesReused'])
assert b['previousFacadeBucketsReplaced']==14 and b['buckets']==17
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','detailReviewed','obliqueReviewed','obliqueDetailReviewed','boundaryDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v50.png','lower-facade-detail-v50.png','poster-oblique-v50.png','lower-facade-oblique-detail-v50.png','lower-facade-boundary-detail-v50.png']:
 assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':50,'nativeFile':'poster-lower-facade-v50/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'reconstructedOpeningUnits':6,'closedNewSolids':151,'oldBenchAndStairsRemoved':True,'entranceFloorClearanceVerified':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v50.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v50.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v50_poster_lower_facade';status['scene'].update({'currentNative':result['nativeFile'],'revision':50,'posterNativeCalibrationRevision':50,'posterNativeVerifiedV50':True,'posterLowerFacadeOpeningsReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-lower-facade-v50"><h2>入口与下层门窗重建 · v50（重建中）</h2>
<p>左侧入口、扇形窗、拱窗与三组大窗改为有厚度的门扇、窗框和真实墙体开口。入口地板已降低至门槛处，并重建较窄的台阶；清除了不符合海报位置的旧长椅和旧台阶。</p>
<p><a href="viewer/poster-v50.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-lower-facade-v50/Suzume_dual_scene_lower_facade_v50.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-lower-facade-v50/poster-front-v50.png" alt="门窗修正后的完整海报场景"><figcaption>入口与窗组的三维位置更贴近参照；整体尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-lower-facade-v50/lower-facade-comparison-v50.png" alt="下层门窗修正前后与参照对比"><img src="poster-lower-facade-v50/lower-facade-detail-v50.png" alt="入口和三组大窗"><img src="poster-lower-facade-v50/lower-facade-oblique-detail-v50.png" alt="门窗厚度及入口台阶的斜视图"><img src="poster-lower-facade-v50/lower-facade-boundary-detail-v50.png" alt="Boundary detail"><img src="poster-lower-facade-v50/poster-oblique-v50.png" alt="完整庭院侧向渲染"></details>
<p>151 个新增实体已检查封闭性、门窗净空及门槛与地板衔接。第三组大窗越过旧分段，已清理后方的旧墙。玻璃反射、细部破损、植物和隐藏结构仍需校准，浏览器实际显示待验证。</p>
<p><a href="poster-lower-facade-v50/verification-v50.json">模型检查</a> · <a href="poster-lower-facade-v50/visual-review-v50.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-lower-facade-v50">' in gallery:gallery=re.sub(r'<section id="poster-lower-facade-v50">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''入口与下层门窗重建 v50

完整模型：Suzume_dual_scene_lower_facade_v50.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

左侧六处入口/窗组有真实墙体开口、围边、窗格和玻璃实体。入口门扇包含下部面板、上部玻璃、格栅和门把手，扇形窗有曲线格栅。三组大窗之间由墙柱分隔，最后一组跨过旧分段后延长立面并清理旧墙。
入口内旧地板高于观测门槛，已降低并补齐墙脚；九处落地探测均落到新地板。36 处门窗采样确认没有旧构件遮挡。新增共 151 个封闭实体、22,612 个三角形。
旧长椅和旧楼梯完整构件被移除，新楼梯较窄并向入口右侧略偏移。人物和异世界数据、其余对象和既有贴图保持原有状态。

海报网页：http://127.0.0.1:8931/viewer/poster-v50.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查正面、局部和侧向原生渲染及网页几何。玻璃仍有固定参照色，细部破损、植被、隐藏结构及其他场景细节仍需校准。浏览器实际 GPU 显示待验证，整体尚未达到一比一。
''',encoding='utf-8');print('LOWER_FACADE_50_RELEASED',v['nativeSha256'])
