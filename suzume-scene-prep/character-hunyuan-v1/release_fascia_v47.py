from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-fascia-v47';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v47.json');review=read('visual-review-v47.json');b=read('browser-code-verification-v47.json');web=read('browser-http-verification-v47.json');spec=read('browser-fascia-v47.json');comparison=read('fascia-comparison-v47.json')
native=O/'Suzume_dual_scene_fascia_v47.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==spec['nativeSha256']==b['nativeSha256']==review['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','allOriginalPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved'])
assert len(v['addedAssemblies'])==4 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 and q['slabIntersectingTrianglePairs']>0 for q in v['addedAssemblies'])
assert len(v['adjacentBayJoints'])==3 and all(p['intersectingTrianglePairs']>0 for p in v['adjacentBayJoints'])
assert all(b[k] for k in ['positionsNormalsMaterialAssignmentsMatchNativeExactly','previousSceneAndIvyPreserved','newMaterialParametersMatchNativeSpec'])
assert b['closedSolids']==4 and b['triangles']==128
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','fasciaDetailReviewed','obliqueReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
assert comparison['afterRGBDistance']<comparison['beforeRGBDistance']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v47.png','fascia-detail-v47.png','poster-oblique-v47.png']:
    assert (O/name).stat().st_mtime>native.stat().st_mtime
    assert sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':47,'nativeFile':'poster-fascia-v47/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'closedFasciaSections':4,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v47.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v47.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v47_poster_fascia';status['scene'].update({'currentNative':result['nativeFile'],'revision':47,'posterNativeCalibrationRevision':47,'posterNativeVerifiedV47':True,'posterObservedLeftFasciaReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-fascia-v47"><h2>左侧檐口剖面校准 · v47（重建中）</h2>
<p>左侧顶板前缘补入四段实体檐口与滴水边，校正此前过黑的横带，并保留原屋顶支撑结构。</p>
<p><a href="viewer/poster-v47.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-fascia-v47/Suzume_dual_scene_fascia_v47.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-fascia-v47/poster-front-v47.png" alt="檐口修正后的完整海报场景"><figcaption>已修正左侧檐口黑带；门窗、植物、人物及异世界细节仍在校准，整体尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和侧向视角</summary><img src="poster-fascia-v47/fascia-comparison-v47.png" alt="檐口修正前后与参照的对比"><img src="poster-fascia-v47/fascia-detail-v47.png" alt="左侧檐口细节"><img src="poster-fascia-v47/poster-oblique-v47.png" alt="完整庭院侧向渲染"></details>
<p>已检查实体闭合、顶板接合和网页几何数据；浏览器实际显示仍待验证。</p>
<p><a href="poster-fascia-v47/verification-v47.json">模型检查</a> · <a href="poster-fascia-v47/visual-review-v47.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-fascia-v47">' in gallery:gallery=re.sub(r'<section id="poster-fascia-v47">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''左侧檐口剖面校准 v47

完整模型：Suzume_dual_scene_fascia_v47.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

左侧四个开间补入封闭的檐口剖面，包含立面、斜面与下部滴水边，共 128 个三角形。所有分段均与原顶板相交，三个相邻接点已检查。原屋顶、栏杆、设备和植物保留。
主视图、局部与侧向渲染已核对。网页几何使用原生模型坐标、法线与材质分配，但网页环境光和表面风化仍有近似；实际浏览器 GPU 显示未验证。

海报网页：http://127.0.0.1:8931/viewer/poster-v47.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

整体仍未达到一比一。建筑门窗与立面层次、植物分布、风化、云水细节、人物表情与颈部衔接及异世界继续校准。
''',encoding='utf-8')
print('FASCIA_47_RELEASED',v['nativeSha256'])
