from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-foreground-v51';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v51.json');review=read('visual-review-v51.json');b=read('browser-code-verification-v51.json');web=read('browser-http-verification-v51.json');spec=read('browser-foreground-v51.json');native=O/'Suzume_dual_scene_foreground_v51.blend';alias=V/'suzume-full-scene.blend';contact=read('foreground-contact-audit-v51.json')
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']==contact['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved','allPackedImageBytesPreserved'])
assert len(v['addedSolids'])==32 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 and q['vertexColorsPreserved'] for q in v['addedSolids'])
assert v['packedImageCount']==23 and contact['oldPropTrianglesRemoved']==706 and contact['newLeaves']==2108 and contact['newGrassBlades']==126
assert v['ivy']['removedCount']==256 and v['ivy']['remainingCount']==4187 and v['ivy']['retainedPointsAndAttributesPreservedExactly']
assert len(contact['chairLegSupportContacts'])==2 and all(0<=q['contactOverlapMeters']<.01 for q in contact['chairLegSupportContacts'])
assert all(b[k] for k in ['positionsNormalsUVsAndColorsMatchNativeExactly','previousUnaffectedGeometryAndMaterialsPreserved','retainedIvyMatricesAndColorsPreservedExactly','ivySharedResourcesNotDisposed','existingMaterialInstancesReused'])
assert b['previousFacadeBucketsReplaced']==6 and b['buckets']==9 and b['ivyRemovedCount']==256
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','detailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name,hash_value in review['reviewedImageSha256'].items():assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==hash_value
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':51,'nativeFile':'poster-foreground-v51/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedNewAssemblies':32,'newLeaves':2108,'newGrassBlades':126,'largeLeavesRemoved':256,'oldBoxPropsAndPipeRemoved':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v51.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v51.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v51_poster_foreground';status['scene'].update({'currentNative':result['nativeFile'],'revision':51,'posterNativeCalibrationRevision':51,'posterNativeVerifiedV51':True,'posterForegroundPlantsAndPropsReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-foreground-v51"><h2>门前植物与旧物重建 · v51（重建中）</h2>
<p>门前过大的叶片替换为细枝小叶，箱形杂物按可见轮廓重建为残椅，并重建较低的空心管道及弯管。新增植物和旧物都有完整立体结构。</p>
<p><a href="viewer/poster-v51.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-foreground-v51/Suzume_dual_scene_foreground_v51.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-foreground-v51/poster-front-v51.png" alt="门前植物与旧物重建后的完整海报场景"><figcaption>植物和旧物轮廓更贴近参照；整体尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-foreground-v51/foreground-comparison-v51.png" alt="植物与旧物修正前后对比"><img src="poster-foreground-v51/foreground-detail-v51.png" alt="门前植物与管道局部"><img src="poster-foreground-v51/foreground-oblique-detail-v51.png" alt="残椅和枝叶的立体侧面"><img src="poster-foreground-v51/poster-oblique-v51.png" alt="完整庭院侧向渲染"></details>
<p>新增 2,108 片小叶与 126 根草叶，清除了局部 256 片大叶；其余植被与人物、异世界场景保持原有状态。残椅的物体类型和隐藏结构由局部参照推断。地面碎石、植物分布和表面磨损仍需校准，浏览器实际显示待验证。</p>
<p><a href="poster-foreground-v51/verification-v51.json">模型检查</a> · <a href="poster-foreground-v51/visual-review-v51.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-foreground-v51">' in gallery:gallery=re.sub(r'<section id="poster-foreground-v51">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门前植物与旧物重建 v51

完整模型：Suzume_dual_scene_foreground_v51.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

新增较细的枝叶、草叶、攀附藤蔓、残椅与较低的空心管道和回弯。新增 32 个封闭实体组，包含 2,108 片小叶与 126 根草叶。移除了局部 256 片粗大叶子和旧箱形杂物/旧管道的 706 个三角形，其余 4,187 片原有叶子的变换、颜色保持一致。
人物、脚部间隙、独立头模、门两侧分割和异世界场景沿用 v37，不在此次修改范围内。

海报网页：http://127.0.0.1:8931/viewer/poster-v51.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查正面、局部和侧面原生渲染及网页几何数据。地面条带和碎石、植物精确分布/颜色、旧物破损及隐藏结构仍需校准，整体尚未达到一比一。浏览器实际 GPU 显示仍待验证。
''',encoding='utf-8');print('FOREGROUND_51_RELEASED',v['nativeSha256'])
