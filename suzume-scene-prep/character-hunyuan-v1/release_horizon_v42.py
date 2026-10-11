from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-horizon-v42';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v42.json');a=read('integration-v42.json');review=read('visual-review-v42.json');b=read('browser-code-verification-v42.json');web=read('browser-http-verification-v42.json');metric=read('coverage-v42.json');color=read('color-comparison-v42.json');spec=read('browser-clouds-v42.json')
native=O/'Suzume_dual_scene_horizon_v42.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==a['nativeSha256']==spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','sharedNodeGroupsPreserved','otherPosterGeometryAndColorsMaterialsCameraLightingPreserved','waterRevision40Preserved','continuousPartSpansFormerGap'])
assert v['lowerCloudCount']==27 and all(q['nonManifoldEdges']==0 and q['signedLocalVolume']>0 and q['minimumLocalTriangleArea']>0 for q in v['clouds'])
assert all(b[k] for k in ['positionsNormalsColorsAndIndicesMatchExportExactly','worldTransformsVerified','originalMaterialsPreserved','mainCloudGeometriesUntouched','surroundingCloudGeometriesUntouched','onlyFinalCloudPayloadRequested'])
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','horizonDetailReviewed','obliqueReviewed']) and not review['oneToOneComplete']
assert metric['after']['sourceCloudRecall']>metric['before']['sourceCloudRecall']+.8
assert color['afterRGBMeanAbsoluteError255']<color['beforeRGBMeanAbsoluteError255']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v42.png','horizon-detail-v42.png','poster-oblique-v42.png']:assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [a['sourceNativeSha256'],a['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==a['nativeSha256']
result={'revision':42,'nativeFile':'poster-horizon-v42/'+native.name,'nativeSha256':a['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'posterWaterRevision40Preserved':True,'restoredContinuousHorizonBank':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v42.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','probeCloudCoverageBefore':metric['before']['sourceCloudRecall'],'probeCloudCoverageAfter':metric['after']['sourceCloudRecall'],'metricScope':metric['scope'],'browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v42.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v42_poster_continuous_central_horizon_bank';status['scene'].update({'currentNative':result['nativeFile'],'revision':42,'posterNativeCalibrationRevision':42,'posterNativeVerifiedV42':True,'posterCentralHorizonRecovered':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-horizon-v42"><h2>门上方低云补全 · v42（重建中）</h2>
<p>门上方被旧遮罩裁掉的云层已补成连续三维云体，连接两侧远云。海报庭院与电影开门场景可分别查看，人物、脚部和穿门分区保留。</p>
<p><a href="viewer/poster-v42.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-horizon-v42/Suzume_dual_scene_horizon_v42.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-horizon-v42/poster-front-v42.png" alt="补全中央低云后的三维海报场景"><figcaption>中央云层的缺口已连接。更低处的层云、建筑与钢架轮廓，以及人物神态仍需继续校准。</figcaption></figure>
<details><summary>低云细节、参照对比与侧向视角</summary><img src="poster-horizon-v42/horizon-detail-v42.png" alt="补全的低云实体"><img src="poster-horizon-v42/horizon-comparison-v42.png" alt="原图与补全前后对照"><img src="poster-horizon-v42/poster-oblique-v42.png" alt="完整场景的侧向检查"></details>
<p>网页资源与几何数据已检查，浏览器控制仍超时，实际显示尚未验证。</p>
<p><a href="poster-horizon-v42/verification-v42.json">模型检查</a> · <a href="poster-horizon-v42/coverage-v42.json">局部轮廓覆盖检查</a> · <a href="poster-horizon-v42/visual-review-v42.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-horizon-v42">' in gallery:gallery=re.sub(r'<section id="poster-horizon-v42">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门上方低云补全 v42

完整模型：Suzume_dual_scene_horizon_v42.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。
海报场景名称沿用 v38，钢架为 v39，水面为 v40。其余 26 组低云沿用 v41，原来被割成两组的中央云层重建为一组连续云体。

本次仅修复原分割遮罩在门上方错误裁掉的天空区域。合并的网格有 397,964 个三角形，由 7 个封闭部分组成，其中主云体跨过原来的中央缺口。纵深与遮挡后的形状由数学构造推定，不能视作原作工程数据。
云层使用固定顶点颜色和完整实体几何，可从任意方向查看。没有面向相机的云卡片。
电影场景、夜景、人物、脚部和门两侧的人体分区均保留。

海报网页：http://127.0.0.1:8931/viewer/poster-v42.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
网页几何、坐标变换和 HTTP 资源已核对。浏览器控制接口在打开页面时超时，实际 GPU 显示仍未验证。

仍未达到一比一：本次补回云层缺口，更低处的层云仍不足，云层颜色、左侧钢架、建筑、前景石板、人物神态与颈胸衔接、夜景仍需校准。
''',encoding='utf-8')
print('HORIZON_42_RELEASED',a['nativeSha256'],flush=True)
