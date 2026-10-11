from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-rooftops-v45';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v45.json');review=read('visual-review-v45.json');b=read('browser-code-verification-v45.json');web=read('browser-http-verification-v45.json');spec=read('browser-rooftops-v45.json');geometry=read('rooftop-geometry-v45.json')
native=O/'Suzume_dual_scene_rooftops_v45.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==spec['nativeSha256']==b['nativeSha256']==review['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','retainedOriginalFacadeCoordinatesPreserved','roofSupportsVerified'])
assert len(v['addedAssemblies'])==4 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and len(q['roofSupportProbes'])>=8 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedAssemblies'])
assert all(p['roofTopZ']>=p['bottom'][2]-.015 for q in v['addedAssemblies'] for p in q['roofSupportProbes'])
assert all(q['pixelRMS']<.25 for q in geometry['fits'] if 'pixelRMS' in q)
assert all(b[k] for k in ['positionsNormalsUVsMatchNativeExportExactly','originalMaterialsReused','approximateNewMaterialsMatchSpec','unrelatedSceneObjectsPreserved'])
assert b['originalFacadeBucketsReplaced']==5 and b['otherFacadeAndSteelObjectsPreserved']==15
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','rooftopDetailReviewed','obliqueReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v45.png','rooftop-detail-v45.png','poster-oblique-v45.png']:
    assert (O/name).stat().st_mtime>native.stat().st_mtime
    assert sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':45,'nativeFile':'poster-rooftops-v45/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedRooftopAssemblies':4,'roofSupportProbes':sum(len(q['roofSupportProbes']) for q in v['addedAssemblies']),'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v45.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v45.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v45_poster_rooftop_equipment';status['scene'].update({'currentNative':result['nativeFile'],'revision':45,'posterNativeCalibrationRevision':45,'posterNativeVerifiedV45':True,'posterObservedRooftopEquipmentVerified':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-rooftops-v45"><h2>屋顶设备轮廓重建 · v45（重建中）</h2>
<p>重建左侧两座设备间和两只水箱，修正位置、顶边、扁顶盖、爬梯与管道。四组设备均为三维实体，屋面支撑已检查。</p>
<p><a href="viewer/poster-v45.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-rooftops-v45/poster-front-v45.png" alt="屋顶设备重建后的完整海报场景"><figcaption>设备轮廓更接近参照；栏杆、藤蔓、建筑门窗、人物与夜景仍在校准。</figcaption></figure>
<details><summary>参照对比、屋顶细节与侧向视角</summary><img src="poster-rooftops-v45/rooftop-comparison-v45.png" alt="官方参照与屋顶设备重建前后对比"><img src="poster-rooftops-v45/rooftop-detail-v45.png" alt="屋顶设备细节"><img src="poster-rooftops-v45/poster-oblique-v45.png" alt="庭院侧向渲染"></details>
<p>原生模型、网页几何与资源已检查；浏览器实际显示仍待验证。</p>
<p><a href="poster-rooftops-v45/verification-v45.json">模型检查</a> · <a href="poster-rooftops-v45/visual-review-v45.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-rooftops-v45">' in gallery:gallery=re.sub(r'<section id="poster-rooftops-v45">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''屋顶设备轮廓重建 v45

完整模型：Suzume_dual_scene_rooftops_v45.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

本版重建左侧两座设备间、中央水箱和画面左侧露出的水箱，并补入顶盖、爬梯与管道。原有庭院、钢架、水面、云层、人物和异世界保留。
设备间顶边与水箱顶盖位置依据参照拟合，背面、深度和隐蔽连接仍为推定。四组模型包含 74 个封闭部件，共 7,920 个三角形。36 个底部采样点确认落在原屋面上。
完整正面、局部和侧面渲染已核对。整体尚未达到一比一，栏杆密度、屋檐轮廓、藤蔓、门窗和人物神态等仍有偏差。

海报网页：http://127.0.0.1:8931/viewer/poster-v45.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
网页几何、法线、UV、材质参数和 HTTP 资源已检查。网页新材质仍为近似，实际 GPU 显示未验证。
''',encoding='utf-8')
print('ROOFTOPS_45_RELEASED',v['nativeSha256'],flush=True)
