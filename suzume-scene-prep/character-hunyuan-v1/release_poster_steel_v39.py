from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-steel-v39';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v39.json');a=read('integration-v39.json');review=read('visual-review-v39.json');b=read('browser-code-verification-v39.json');roof=read('roof-contact-v39.json');web=read('browser-http-verification-v39.json')
native=O/'Suzume_dual_scene_steel_v39.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==a['nativeSha256']==roof['nativeSha256']
assert v['freshReopenVerified'] and v['movieStatePreservedExactly'] and v['allCheckedConnectionsIntersect'] and roof['outerRibPhysicallyIntersectsRoof']
assert len(v['closedMembers'])==16 and all(q['nonManifoldEdges']==0 for q in v['closedMembers'])
assert b['positionsNormalsUVVerifiedExactly'] and b['originalMaterialsPreserved'] and b['unrelatedSceneObjectsPreserved'] and b['triangles']==65964
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','steelDetailReviewed','obliqueReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v39.png','steel-detail-v39.png','poster-oblique-v39.png']:assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [a['sourceNativeSha256'],a['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==a['nativeSha256']
result={'revision':39,'nativeFile':'poster-steel-v39/'+native.name,'nativeSha256':a['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','addedClosedMembers':16,'checkedConnectedJoints':23,'outerRoofContactVerified':True,'movieRevision37Preserved':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v39.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserMaterialsApproximate':True,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v39.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v39_poster_observed_right_steelwork';status['scene'].update({'currentNative':result['nativeFile'],'revision':39,'posterNativeCalibrationRevision':39,'posterNativeVerifiedV39':True,'posterBrowserCandidate':result['posterBrowser'],'posterObservedRightSteelworkVerified':True,'posterOuterRibRoofContactVerified':True,'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-steel-v39"><h2>海报折梁、托架与立柱 · v39（重建中）</h2>
<p>补上右侧折断工字梁、弧形托架和细拉杆，重新校准两根立柱的弯曲轮廓。外侧钢架与屋面接合，内部连接均为有厚度的实体；电影场景保持 v37。</p>
<p><a href="viewer/poster-v39.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-steel-v39/Suzume_dual_scene_steel_v39.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-steel-v39/poster-front-v39.png" alt="按海报右侧钢架轮廓重建的完整三维场景"><figcaption>右侧主要钢架轮廓已有改进，截面角度、锈蚀与油漆、左侧钢架、水纹和远云仍需校准。</figcaption></figure>
<details><summary>查看钢架近景与侧向视角</summary><img style="max-width:750px" src="poster-steel-v39/steel-detail-v39.png" alt="实体工字梁、托架与连接细节"><img src="poster-steel-v39/poster-oblique-v39.png" alt="独立海报环境侧向检查"></details>
<p>网页几何与原生导出已核对；网页材质为近似实现，实际浏览器显示仍待验证。</p>
<p><a href="poster-steel-v39/verification-v39.json">模型检查</a> · <a href="poster-steel-v39/connections-v39.json">实体连接检查</a> · <a href="poster-steel-v39/projection-comparison-v39.json">立柱轮廓约束</a> · <a href="poster-steel-v39/visual-review-v39.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-steel-v39">' in gallery:gallery=re.sub(r'<section id="poster-steel-v39">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''海报钢架重建 v39

完整模型：Suzume_dual_scene_steel_v39.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。
海报场景名称沿用 v38，内部钢架已更新为 v39。电影人物、脚部修正和穿门分区保留。

以 2000×2824 海报测量右侧钢架中心线，重建 16 个封闭实体：两根主柱、横梁、折断梁、弧形托架、支撑和细拉杆，以及内侧基础。
端点处补充伸入主体的连接段，23 处检查确认两实体实际相交；外侧钢架与原有屋面的三角面接触已核对。
纵深从原有穹顶推定，并依据现有屋面约束修正；隐藏构造不是已知的原作工程尺寸。
清理原先对应的简化构件及右上多余残片。保留其他庭院几何和电影场景。

网页：http://127.0.0.1:8931/viewer/poster-v39.html
电影：http://127.0.0.1:8931/viewer/candidate-v37.html
网页钢架导出 65964 个三角面，坐标、法线与 UV 的加载检查通过；网页材质近似，实际 GPU 显示尚未验证。

尚未达到一比一：工字钢截面朝向、厚度与风化细节，左侧钢架、建筑和植物、海报水面与远云；电影人物神态、颈胸接缝、材质、近景机位与夜景仍需校准。
''',encoding='utf-8')
print('POSTER_39_RELEASED',a['nativeSha256'],flush=True)
