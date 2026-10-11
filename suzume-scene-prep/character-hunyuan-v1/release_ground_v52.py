from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-ground-v52';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v52.json');review=read('visual-review-v52.json');b=read('browser-code-verification-v52.json');web=read('browser-http-verification-v52.json');spec=read('browser-ground-v52.json');supports=read('column-support-verification-v52.json');native=O/'Suzume_dual_scene_ground_v52.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']==supports['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved','allPackedImageBytesPreserved','unmodifiedVegetationPreservedExactly'])
assert len(v['addedSolids'])==56 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 and q['vertexColorsPreserved'] for q in v['addedSolids'])
assert sum(q['triangles'] for q in v['addedSolids'])==10982 and sum(q['removedTriangles'] for q in v['changedOriginalMeshes'])==666 and v['packedImageCount']==23
assert len(v['replantedStems'])==13 and all(q['allOtherVerticesTopologyAndColorsPreserved'] and q['leafBladesOrGrassTipsPreserved'] for q in v['replantedStems'])
assert len(v['rootGroundProbes'])==13 and max(abs(q['gapMeters']) for q in v['rootGroundProbes'])<.006
assert len(v['grassBladeGroundProbes'])==126 and max(abs(q['gapMeters']) for q in v['grassBladeGroundProbes'])<.006
assert len(v['chairSupportContacts'])==4 and max(abs(q['gapMeters']) for q in v['chairSupportContacts'])<2e-5
assert supports['threeColumnBasesSupported'] and supports['lowestStairTreadSupported']
assert all(b[k] for k in ['positionsNormalsUVsAndColorsMatchNativeExactly','previousUnaffectedGeometryAndMaterialsPreserved','allIvyMatricesAndColorsPreservedExactly','existingMaterialInstancesReused']) and b['previousBucketsReplaced']==12 and b['buckets']==13
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','detailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name,hash_value in review['reviewedImageSha256'].items():assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==hash_value
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':52,'nativeFile':'poster-ground-v52/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedReconstructedAssemblies':56,'removedOldPlinthAndSlabComponents':15,'lowerPlantStemsReplanted':13,'grassBasesGrounded':126,'columnChairAndStairSupportsVerified':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v52.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v52.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v52_poster_ground';status['scene'].update({'currentNative':result['nativeFile'],'revision':52,'posterNativeCalibrationRevision':52,'posterNativeVerifiedV52':True,'posterShallowBankAndStonesReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-ground-v52"><h2>浅岸与碎石重建 · v52（重建中）</h2>
<p>左侧水边的高直条和大方石已替换为浅积土、不规则岸沿与碎石。草茎下端接入地表，钢柱、残椅和最低一级台阶都有实体支撑。</p>
<p><a href="viewer/poster-v52.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-ground-v52/Suzume_dual_scene_ground_v52.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-ground-v52/poster-front-v52.png" alt="浅岸与碎石修正后的完整海报场景"><figcaption>水边轮廓更贴近参照；整体尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-ground-v52/ground-comparison-v52.png" alt="浅岸与碎石修正前后对比"><img src="poster-ground-v52/ground-detail-v52.png" alt="水边局部"><img src="poster-ground-v52/ground-oblique-detail-v52.png" alt="岸面与支撑结构的侧面"><img src="poster-ground-v52/poster-oblique-v52.png" alt="完整庭院侧向渲染"></details>
<p>56 组重建几何已检查封闭性；13 组植物的下部茎段和 126 根草叶底部已接到地表，叶片与草尖保留。人物和异世界场景保持原有状态。低栏杆、零碎旧物、湿痕与苔藓等细节仍需校准；隐藏深度由参照推断，浏览器实际显示待验证。</p>
<p><a href="poster-ground-v52/verification-v52.json">模型检查</a> · <a href="poster-ground-v52/visual-review-v52.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-ground-v52">' in gallery:gallery=re.sub(r'<section id="poster-ground-v52">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''浅岸与碎石重建 v52

完整模型：Suzume_dual_scene_ground_v52.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

三个过高的旧基座及其外沿顶板、九块不对应参照的凸起方石已移除。重建了浅积土、六块主要石头、破碎支撑石和台阶基础，共 56 组封闭几何、10,982 个三角形。
13 组植物下端重新接入地表，保留叶片、草尖、拓扑与颜色。126 处草叶底部及三根钢柱、四处椅脚、最低台阶支撑均已检查。建筑内部的后方地板保留原高度。
人物、脚部间隙、独立头模、门两侧分割和异世界场景沿用 v37，不在此次修改范围内。

海报网页：http://127.0.0.1:8931/viewer/poster-v52.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查正面、局部和侧面原生渲染及网页几何数据。岸面湿痕、碎石裂纹、苔藓、低栏杆、残留旧物和其他建筑/人物细节仍需校准，整体尚未达到一比一。浏览器实际 GPU 显示仍待验证。
''',encoding='utf-8');print('GROUND_52_RELEASED',v['nativeSha256'])
