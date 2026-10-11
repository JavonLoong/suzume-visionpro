from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-clouds-v41';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v41.json');a=read('integration-v41.json');review=read('visual-review-v41.json');b=read('browser-code-verification-v41.json');web=read('browser-http-verification-v41.json');metric=read('silhouette-comparison-v41.json');spec=read('browser-clouds-v41.json')
native=O/'Suzume_dual_scene_clouds_v41.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==a['nativeSha256']==spec['nativeSha256']
assert v['freshReopenVerified'] and v['movieStatePreservedExactly'] and v['otherPosterGeometryAndColorsMaterialsCameraLightingPreserved'] and v['waterRevision40Preserved']
assert v['changedCloudCount']==28 and all(q['nonManifoldEdges']==0 and q['signedLocalVolume']>0 and q['minimumLocalTriangleArea']>0 for q in v['clouds'])
assert b['positionsNormalsColorsAndIndicesMatchExportExactly'] and b['worldTransformsVerified'] and b['originalMaterialsPreserved'] and b['mainCloudGeometriesUntouched']
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','cloudDetailReviewed','obliqueReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v41.png','cloud-detail-v41.png','poster-oblique-v41.png']:assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [a['sourceNativeSha256'],a['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==a['nativeSha256']
result={'revision':41,'nativeFile':'poster-clouds-v41/'+native.name,'nativeSha256':a['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'posterWaterRevision40Preserved':True,'closedCloudsRebuilt':28,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v41.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','weightedMaskIoUBefore':metric['weightedOldIoU'],'weightedMaskIoUAfter':metric['weightedNewIoU'],'metricScope':metric['scope'],'browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v41.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v41_poster_dense_closed_distant_clouds';status['scene'].update({'currentNative':result['nativeFile'],'revision':41,'posterNativeCalibrationRevision':41,'posterNativeVerifiedV41':True,'posterDistantCloudGeometryRefined':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-clouds-v41"><h2>海报远云轮廓与细节 · v41（重建中）</h2>
<p>28 组远云重建为更细密的封闭云体，补回小云团起伏并修正表面颜色。水面、钢架和完整庭院保留，电影版人物与穿门分区保持 v37。</p>
<p><a href="viewer/poster-v41.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-clouds-v41/Suzume_dual_scene_clouds_v41.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-clouds-v41/poster-front-v41.png" alt="远云细化后的完整三维海报场景"><figcaption>远云折面已有改善；中央低云的缺失区域、钢架遮挡后的云形，以及建筑与人物仍需继续校准。</figcaption></figure>
<details><summary>云层细节、参照对比与侧向视角</summary><img src="poster-clouds-v41/cloud-detail-v41.png" alt="远云封闭实体细节"><img src="poster-clouds-v41/poster-front-v41-cloud-comparison.png" alt="原海报与三维远云对照"><img src="poster-clouds-v41/poster-oblique-v41.png" alt="三维云层侧向检查"></details>
<p>网页模型数据与资源已核对，实际浏览器显示尚未验证。</p>
<p><a href="poster-clouds-v41/verification-v41.json">模型检查</a> · <a href="poster-clouds-v41/silhouette-comparison-v41.json">轮廓遮罩比较</a> · <a href="poster-clouds-v41/visual-review-v41.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-clouds-v41">' in gallery:gallery=re.sub(r'<section id="poster-clouds-v41">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''海报远云细化 v41

完整模型：Suzume_dual_scene_clouds_v41.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。
海报名称沿用 v38，钢架为 v39、水面为 v40、28 组远云为 v41。电影人物、脚部净空和穿门分区保留。

本次重新构建下方 28 组云体，网格封闭且有体积，可从各方向查看。纵深依据轮廓内切椭球推定，不是已知的原作工程数据。
表面使用固定顶点颜色，以官方海报颜色为主。钢架遮挡区域的颜色做连续延拓，背面颜色为推定；没有面向相机的云卡片。
云体采用密网格，因此模型和网页资源比上一版更大。

网页候选：http://127.0.0.1:8931/viewer/poster-v41.html
电影场景：http://127.0.0.1:8931/viewer/candidate-v37.html
网页几何、坐标变换和资源已检查；实际 GPU 显示与渲染引擎间的外观一致性尚未验证。

仍未达到一比一：中央低云曾被旧遮罩裁掉，需要补回；钢架遮挡后的云形和背面、五朵主云的细节、左侧钢架、建筑、水底石板、人物神态与颈胸衔接、夜景仍需校准。
''',encoding='utf-8')
print('CLOUD_41_RELEASED',a['nativeSha256'],flush=True)
