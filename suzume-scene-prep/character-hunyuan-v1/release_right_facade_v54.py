from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-right-facade-v54';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();v=read('verification-v54.json');review=read('visual-review-v54.json');b=read('browser-code-verification-v54.json');web=read('browser-http-verification-v54.json');spec=read('browser-right-facade-v54.json');surface=read('surface-restoration-v54.json');native=O/'Suzume_dual_scene_right_facade_v54.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved','allPackedImageBytesPreserved'])
assert len(v['addedSolids'])==195 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedSolids']);assert sum(q['triangles'] for q in v['addedSolids'])==24900
assert len(v['changedOriginalMeshes'])==15 and len(v['structuralOpeningProbes'])==42 and len(v['entranceFloorProbes'])==9 and len(v['stairFoundationProbes'])==9;assert all(-.004<q['gapMeters']<0 for q in v['stairFoundationProbes'])
assert v['packedImageCount']==24 and v['preservedOriginalPackedImages']==23 and v['restoredAtlasSha256']==surface['atlasSha256']==sha(O/'right-facade-pigments-v54.png');assert surface['outsidePatchPixelsPreservedExactly'] and surface['restoredPixelsEqualColorGradedSourceExactly'] and surface['restoredPixels']==13175
assert all(b[k] for k in ['positionsNormalsAndUVsMatchNativeExactly','previousUnaffectedGeometryAndMaterialsPreserved','allIvyMatricesAndColorsPreservedExactly','existingMaterialInstancesReused','newRightPaintIsolated']) and b['previousBucketsReplaced']==15 and b['buckets']==18
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','detailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name,value in review['reviewedImageSha256'].items():assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==value
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':54,'nativeFile':'poster-right-facade-v54/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedReconstructedAssemblies':195,'rightOpeningUnits':7,'clearanceProbesVerified':42,'floorProbesVerified':9,'stairFoundationProbesVerified':9,'restoredVisibleSourcePixels':13175,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v54.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']};(O/'release-v54.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v54_poster_right_facade';status['scene'].update({'currentNative':result['nativeFile'],'revision':54,'posterNativeCalibrationRevision':54,'posterNativeVerifiedV54':True,'posterRightLowerFacadeReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-right-facade-v54"><h2>右侧门窗与立面重建 · v54（重建中）</h2>
<p>右侧三段立面已按参照重建：部分遮挡的拱门、窄拱窗、两扇并排长窗和三扇长窗。窗框、窗台、门楣、台阶和小风扇均为立体几何。</p>
<p><a href="viewer/poster-v54.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-right-facade-v54/Suzume_dual_scene_right_facade_v54.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-right-facade-v54/poster-front-v54.png" alt="右侧立面修正后的完整海报场景"><figcaption>七处门窗洞口已校准；整体仍在重建，尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-right-facade-v54/right-facade-comparison-v54.png" alt="右侧门窗修正前后对比"><img src="poster-right-facade-v54/right-facade-detail-v54.png" alt="右侧立面局部"><img src="poster-right-facade-v54/right-facade-oblique-detail-v54.png" alt="右侧立面近距离侧视图"><img src="poster-right-facade-v54/poster-oblique-v54.png" alt="完整庭院旋转视角"></details>
<p>195 组新增几何已检查封闭性，42 处洞口探测、入口地板和最低台阶支撑均通过检查。最右窗户的旧模糊带已恢复为可见参照细节。右侧上层拱廊、前景旧物、植物、磨损和隐藏结构仍需校准；浏览器实际显示待验证。</p>
<p><a href="poster-right-facade-v54/verification-v54.json">模型检查</a> · <a href="poster-right-facade-v54/visual-review-v54.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-right-facade-v54">' in gallery:gallery=re.sub(r'<section id="poster-right-facade-v54">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8');(O/'使用说明.txt').write_text('''右侧门窗与立面重建 v54

完整模型：Suzume_dual_scene_right_facade_v54.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

右侧三段立面包含七处独立洞口、窗框与窗台、门楣、入口门扇与台阶、小风扇和实体支撑，共 195 组封闭几何、24,900 个三角形。42 处洞口、9 处入口地板和 9 处最低台阶支撑已检查。
最右窗户的旧模糊带源于早期遮挡清理，此次在独立材质中恢复了 13,175 个可见参照像素。23 张原有打包图片保留，新增 1 张修正材质。
人物、独立头模、脚部间隙、门两侧分割和异世界沿用 v37。

海报网页：http://127.0.0.1:8931/viewer/poster-v54.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查原生正面、近景、侧面及等分辨率前后对比，网页几何和 HTTP 资源已验证。右侧上层拱廊、前景旧物、植物、玻璃反射、磨损及隐藏结构仍需校准，尚未达到一比一。浏览器实际 GPU 显示待验证。
''',encoding='utf-8');print('RIGHT_FACADE_54_RELEASED',v['nativeSha256'])
