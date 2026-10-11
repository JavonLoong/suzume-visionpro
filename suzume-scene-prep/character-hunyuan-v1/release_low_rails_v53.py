from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-low-rails-v53';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v53.json');review=read('visual-review-v53.json');b=read('browser-code-verification-v53.json');web=read('browser-http-verification-v53.json');spec=read('browser-low-rails-v53.json');native=O/'Suzume_dual_scene_low_rails_v53.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved','allPackedImageBytesPreserved','allExistingVegetationPreservedExactly'])
assert len(v['addedSolids'])==38 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 and q['vertexColorsPreserved'] for q in v['addedSolids'])
assert sum(q['triangles'] for q in v['addedSolids'])==5036 and sum(q['removedTriangles'] for q in v['changedOriginalMeshes'])==84 and v['packedImageCount']==23
assert len(v['groundContacts'])==9 and max(abs(q['gapMeters']-.001) for q in v['groundContacts'])<2e-5
assert len(v['pipeStrapContacts'])==3 and all(-.002<q['gapMeters']<.00002 for q in v['pipeStrapContacts'])
assert len(v['centerlineProjectionChecks'])==7 and max(q['maximumProjectionErrorPixels708'] for q in v['centerlineProjectionChecks'])<1e-4
assert all(b[k] for k in ['positionsNormalsUVsAndColorsMatchNativeExactly','previousUnaffectedGeometryAndMaterialsPreserved','allIvyMatricesAndColorsPreservedExactly','existingMaterialInstancesReused']) and b['previousBucketsReplaced']==2 and b['buckets']==5
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','detailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name,hash_value in review['reviewedImageSha256'].items():assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==hash_value
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':53,'nativeFile':'poster-low-rails-v53/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedReconstructedAssemblies':38,'removedUnmatchedBricks':7,'groundContactsVerified':9,'pipeStrapContactsVerified':3,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v53.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v53.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v53_poster_low_fixtures';status['scene'].update({'currentNative':result['nativeFile'],'revision':53,'posterNativeCalibrationRevision':53,'posterNativeVerifiedV53':True,'posterLowFrameAndPipeSupportsReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-low-rails-v53"><h2>残缺低框架与管道支架 · v53（重建中）</h2>
<p>左侧残缺低框架、弯曲金属边、破损短板及横管支架已补成三维实体。移除了浅岸前方七块不对应参照的凸起砖块。</p>
<p><a href="viewer/poster-v53.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-low-rails-v53/Suzume_dual_scene_low_rails_v53.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-low-rails-v53/poster-front-v53.png" alt="补入残缺低框架与支架后的海报场景"><figcaption>正面轮廓继续校准，完整场景可自由旋转；尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-low-rails-v53/low-rails-comparison-v53.png" alt="残缺低框架修正前后对比"><img src="poster-low-rails-v53/low-rails-detail-v53.png" alt="低框架与管道局部"><img src="poster-low-rails-v53/low-rails-oblique-detail-v53.png" alt="低框架支脚与管道支架的侧面"><img src="poster-low-rails-v53/poster-oblique-v53.png" alt="完整庭院侧向渲染"></details>
<p>38 组新增几何均已检查封闭性，9 处支脚落地和 3 处夹带贴管已核对。低框架的物件类别、隐藏连接和深度依照可见线索推定。湿痕、锈蚀、苔藓、植被和人物细节仍需校准；浏览器实际显示待验证。</p>
<p><a href="poster-low-rails-v53/verification-v53.json">模型检查</a> · <a href="poster-low-rails-v53/visual-review-v53.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-low-rails-v53">' in gallery:gallery=re.sub(r'<section id="poster-low-rails-v53">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''残缺低框架与管道支架 v53

完整模型：Suzume_dual_scene_low_rails_v53.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

新增 38 组封闭实体，包括左侧低框架、弯曲金属边、破损短板、支脚与横管夹带和支架，共 5,036 个三角形。七块不对应参照的旧砖块已移除。
九处支脚位置已与实际地面核对；三个夹带内壁接触原有横管。其余建筑、植物、材质和灯光保留。
人物、脚部间隙、独立头模、门两侧分割和异世界场景沿用 v37。

海报网页：http://127.0.0.1:8931/viewer/poster-v53.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查原生正面、局部和侧面渲染及网页几何数据。框架身份与隐藏结构依据可见线索推定；锈蚀、湿痕、苔藓、植物和建筑/人物细节仍在校准，整体尚未达到一比一。浏览器连接超时，实际 GPU 显示待验证。
''',encoding='utf-8');print('LOW_RAILS_53_RELEASED',v['nativeSha256'])
