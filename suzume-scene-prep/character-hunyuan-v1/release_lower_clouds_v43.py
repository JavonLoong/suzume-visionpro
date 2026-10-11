from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v43.json');review=read('visual-review-v43.json');b=read('browser-code-verification-v43.json');web=read('browser-http-verification-v43.json');metric=read('final-comparison-v43.json');spec=read('browser-clouds-v43.json');geometry=read('lower-cloud-geometry-v43.json')
native=O/'Suzume_dual_scene_lower_clouds_v43.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==spec['nativeSha256']==b['nativeSha256']==review['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','allExistingPosterObjectsAndMaterialsPreserved','sharedNodeGroupsPreserved'])
assert len(v['addedClosedClouds'])==3 and all(q['nonManifoldEdges']==0 and q['signedLocalVolume']>0 and q['minimumTriangleArea']>0 for q in v['addedClosedClouds'])
assert all(q['parts']==1 and q['maximumEllipsoidDepthRadiusMeters']>8 for q in geometry['clouds'])
assert all(b[k] for k in ['positionsNormalsColorsAndIndicesMatchExportExactly','worldTransformsVerified','existingCloudObjectsGeometriesMatricesPreserved','originalMaterialReused'])
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','lowerSkyDetailReviewed','obliqueReviewed']) and not review['oneToOneComplete']
assert not metric['trial'] and metric['afterRGBMeanAbsoluteError255']<metric['beforeRGBMeanAbsoluteError255']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v43.png','lower-sky-detail-v43.png','poster-oblique-v43.png']:assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':43,'nativeFile':'poster-lower-clouds-v43/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'existingPosterGeometryPreserved':True,'addedClosedCloudBanks':3,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v43.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','lowerSkyColorErrorBefore255':metric['beforeRGBMeanAbsoluteError255'],'lowerSkyColorErrorAfter255':metric['afterRGBMeanAbsoluteError255'],'metricScope':metric['maskScope'],'browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v43.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v43_poster_lower_cloud_strata';status['scene'].update({'currentNative':result['nativeFile'],'revision':43,'posterNativeCalibrationRevision':43,'posterNativeVerifiedV43':True,'posterLowerCloudStrataRebuilt':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-lower-clouds-v43"><h2>地平线层云重建 · v43（重建中）</h2>
<p>门后补入三层原分割遗漏的灰蓝色云体，恢复靠近地平线的层次。云体封闭且具有纵深，完整庭院可自由旋转。</p>
<p><a href="viewer/poster-v43.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-lower-clouds-v43/Suzume_dual_scene_lower_clouds_v43.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-lower-clouds-v43/poster-front-v43.png" alt="补入灰蓝色低云后的完整海报场景"><figcaption>低空的明暗层次已有改善。云层局部轮廓、左侧钢架、建筑、人物和夜景仍在校准。</figcaption></figure>
<details><summary>层云细节、参照对比与侧向视角</summary><img src="poster-lower-clouds-v43/lower-sky-detail-v43.png" alt="地平线实体云层细节"><img src="poster-lower-clouds-v43/final-comparison-v43.png" alt="官方参照与重建前后对比"><img src="poster-lower-clouds-v43/poster-oblique-v43.png" alt="完整庭院侧向渲染"></details>
<p>原生模型、网页几何与资源已检查；浏览器控制仍未恢复，实际网页显示尚未验证。</p>
<p><a href="poster-lower-clouds-v43/verification-v43.json">模型检查</a> · <a href="poster-lower-clouds-v43/final-comparison-v43.json">局部颜色比较</a> · <a href="poster-lower-clouds-v43/visual-review-v43.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-lower-clouds-v43">' in gallery:gallery=re.sub(r'<section id="poster-lower-clouds-v43">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''地平线层云重建 v43

完整模型：Suzume_dual_scene_lower_clouds_v43.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

在 v42 的基础上新增三组封闭云体，补回旧分割遗漏的灰蓝色低云。原有庭院、门、水面、钢架、云层与电影人物均保留。
每组云是一个封闭的实体。纵深约 282、312、345 米，截面前后厚度随云团变化；隐蔽部分和背面由数学方法推定。
表面为固定顶点颜色。门、藤蔓、钢架和屋顶区域排除后才取样参照颜色，不使用朝向相机的云卡片。

海报网页：http://127.0.0.1:8931/viewer/poster-v43.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
几何和资源已通过检查，浏览器实际 GPU 显示仍未验证。大体积云网格增加了模型和网页资源大小。

整体尚未达到一比一。低云局部形状仍偏平顺；左侧钢架、建筑轮廓、屋顶设备、石板、人物神态和颈胸衔接、异世界仍需继续校准。
''',encoding='utf-8')
print('LOWER_CLOUD_43_RELEASED',v['nativeSha256'],flush=True)
