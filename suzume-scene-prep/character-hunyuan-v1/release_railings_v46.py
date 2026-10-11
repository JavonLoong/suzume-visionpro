from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-railings-v46';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v46.json');review=read('visual-review-v46.json');b=read('browser-code-verification-v46.json');web=read('browser-http-verification-v46.json');spec=read('browser-railings-v46.json');ivy=read('ivy-scale-v46.json')
native=O/'Suzume_dual_scene_railings_v46.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==spec['nativeSha256']==b['nativeSha256']==review['nativeSha256']==ivy['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','retainedOriginalFacadeCoordinatesPreserved'])
assert len(v['addedAssemblies'])==4 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedAssemblies'])
assert len(v['roofSupportProbes'])==267 and all(p['roofTopZ']>=p['bottom'][2] for p in v['roofSupportProbes'])
assert len(v['adjacentBayJoints'])==3 and all(p['intersectingTrianglePairs']>0 for p in v['adjacentBayJoints'])
assert v['ivyRepair']['resizedLeftRoofLeaves']==len(ivy['edits'])==352 and v['ivyRepair']['realizedColorsNonzero'] and v['ivyRepair']['nodeGroupIsolatedFromMovie']
assert all(b[k] for k in ['positionsNormalsUVsMatchNativeExportExactly','originalMaterialsReused','approximateNewMaterialsMatchSpec','unrelatedSceneObjectsPreserved','ivySourceMatchesOriginalSceneExport','otherIvyMatricesAndAllColorsPreservedExactly'])
assert b['originalFacadeBucketsReplaced']==6 and b['otherFacadeAndSteelObjectsPreserved']==14 and b['ivyChangedMatricesMatchNative']==352
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','railingDetailReviewed','obliqueReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v46.png','railing-detail-v46.png','poster-oblique-v46.png']:
    assert (O/name).stat().st_mtime>native.stat().st_mtime
    assert sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':46,'nativeFile':'poster-railings-v46/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedRailAssemblies':4,'uprights':267,'resizedLeftRoofLeaves':352,'nativeIvyColorsRestored':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v46.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v46.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v46_poster_railings_and_ivy';status['scene'].update({'currentNative':result['nativeFile'],'revision':46,'posterNativeCalibrationRevision':46,'posterNativeVerifiedV46':True,'posterObservedRailingDensityVerified':True,'posterIvyColorRealizationFixed':True,'posterLeftRoofLeafSizingAdjusted':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-railings-v46"><h2>栏杆密度与藤蔓校准 · v46（重建中）</h2>
<p>按参照重建左侧四段栏杆，增加竖杆密度并下调上沿。修复原生模型叶片发黑的问题，缩小左侧屋顶的 352 片叶子。</p>
<p><a href="viewer/poster-v46.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-railings-v46/Suzume_dual_scene_railings_v46.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-railings-v46/poster-front-v46.png" alt="栏杆与藤蔓修正后的完整海报场景"><figcaption>栏杆的高度、密度和叶片尺寸已有改善；檐口、建筑门窗、植物分布、人物和夜景仍在校准。</figcaption></figure>
<details><summary>参照对比、局部和侧向视角</summary><img src="poster-railings-v46/railing-comparison-v46.png" alt="栏杆与藤蔓重建前后对比"><img src="poster-railings-v46/railing-detail-v46.png" alt="左侧屋顶细节"><img src="poster-railings-v46/poster-oblique-v46.png" alt="完整庭院侧向渲染"></details>
<p>原生模型、网页几何、叶片变换和资源已检查；浏览器实际显示仍待验证。</p>
<p><a href="poster-railings-v46/verification-v46.json">模型检查</a> · <a href="poster-railings-v46/visual-review-v46.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-railings-v46">' in gallery:gallery=re.sub(r'<section id="poster-railings-v46">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''栏杆密度与藤蔓校准 v46

完整模型：Suzume_dual_scene_railings_v46.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

左侧四段栏杆改为 267 根竖杆，上沿按参照重建，下沿仍落在原屋面和檐口上。栏杆共 400 个封闭部件、4,800 个三角形。全部竖杆的底部支撑和三个分段接点已检查。
原生藤蔓此前禁用了实例实现节点，叶片材质无法取得颜色。现仅为这组叶片建立独立节点组并恢复颜色传递，共 44,430 个叶片顶点。其他森林和夜景实例的设置保留。
左侧屋顶 352 片叶子缩小至原来的 32%，其余叶片位置、尺度和所有颜色数据保留。网页使用原始场景的实例矩阵校验后应用同样的尺寸修正。

海报网页：http://127.0.0.1:8931/viewer/poster-v46.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
完整正面、局部与侧面已核对，网页数据已检查，实际 GPU 显示仍未验证。网页栏杆、钢架和水面材质与原生模型尚有近似。

整体尚未达到一比一。檐口与立面层次、门窗几何、藤蔓分布、风化、云水细节、人物神态与颈部衔接、异世界仍需继续校准。
''',encoding='utf-8')
print('RAILINGS_46_RELEASED',v['nativeSha256'],flush=True)
