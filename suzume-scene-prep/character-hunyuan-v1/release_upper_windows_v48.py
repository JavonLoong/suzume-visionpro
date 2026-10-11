from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-upper-windows-v48';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda n:json.loads((O/n).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v48.json');review=read('visual-review-v48.json');b=read('browser-code-verification-v48.json');web=read('browser-http-verification-v48.json');spec=read('browser-upper-windows-v48.json');contacts=read('glazing-contact-verification-v48.json');native=O/'Suzume_dual_scene_upper_windows_v48.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==review['nativeSha256']==b['nativeSha256']==spec['nativeSha256']==contacts['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified','movieStatePreservedExactly','nightScenePreservedExactly','otherPosterObjectsMaterialsCameraLightingPreserved','sharedNodeGroupsPreserved','unchangedOriginalFacePositionsAndUVsPreserved','sourceResolutionAtlasPacked'])
assert len(v['addedSolids'])==33 and all(q['nonManifoldEdges']==0 and q['signedVolume']>0 and q['maximumVertexErrorMeters']<2e-6 for q in v['addedSolids'])
assert len(v['structuralOpeningProbes'])==5 and all(q['clearDistanceMeters']==1 for q in v['structuralOpeningProbes'])
assert contacts['allFivePaneSolidsSupportedByAtLeastThreeFrameMembers'] and len(contacts['panes'])==5
assert read('window-projection-comparison-v48.json')['maximumPixelError']<1.5
cleanup=read('native-atlas-cleanup-verification-v48.json');assert cleanup['nativeSha256']==v['nativeSha256'] and cleanup['packedCleanAtlasMatchesVerifiedPixels'] and cleanup['originalFacadePixelsOutsideMaskPreservedExactly']
assert all(b[k] for k in ['positionsNormalsUVsMatchNativeExactly','previousUnaffectedGeometryMaterialsAndIvyPreserved','unmodifiedOriginalMaterialInstancesReused','isolatedSourceResolutionAtlasLoaded'])
assert b['previousFacadeBucketsReplaced']==7 and b['buckets']==11
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['frontReviewed','windowDetailReviewed','obliqueReviewed','obliqueDetailReviewed','referenceComparisonReviewed']) and not review['oneToOneComplete']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v48.png','upper-window-detail-v48.png','poster-oblique-v48.png','upper-window-oblique-detail-v48.png']:
 assert (O/name).stat().st_mtime>native.stat().st_mtime and sha(O/name)==review['reviewedImageSha256'][name]
assert sha(alias) in [v['sourceNativeSha256'],v['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==v['nativeSha256']
result={'revision':48,'nativeFile':'poster-upper-windows-v48/'+native.name,'nativeSha256':v['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'observedUpperWindows':4,'closedNewSolids':33,'solidGlazingPieces':5,'structuralOpeningsVerified':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v48.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserRuntimeVerified':False,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v48.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v48_poster_upper_windows';status['scene'].update({'currentNative':result['nativeFile'],'revision':48,'posterNativeCalibrationRevision':48,'posterNativeVerifiedV48':True,'posterObservedUpperWindowOpeningsReconstructed':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-upper-windows-v48"><h2>左侧高窗实体重建 · v48（重建中）</h2>
<p>四处可见高窗已按参照重建墙体开口、窗框和玻璃厚度；跨越旧房间边界的窗洞已清理隔墙遮挡。新建部分共 33 个封闭实体，并剔除了两条贴在旧墙面纹理上的前景杆影。</p>
<p><a href="viewer/poster-v48.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-upper-windows-v48/Suzume_dual_scene_upper_windows_v48.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-upper-windows-v48/poster-front-v48.png" alt="高窗修正后的完整海报场景"><figcaption>高窗几何与参照图案的位置更一致；拱窗、植物、人物和异世界仍在校准，整体尚未达到一比一。</figcaption></figure>
<details><summary>高窗对比、局部和侧向视角</summary><img src="poster-upper-windows-v48/upper-window-comparison-v48.png" alt="高窗实体修正前后与参照的对比"><img src="poster-upper-windows-v48/upper-window-detail-v48.png" alt="左侧立面细节"><img src="poster-upper-windows-v48/upper-window-oblique-detail-v48.png" alt="高窗厚度与墙角的近距离斜视图"><img src="poster-upper-windows-v48/poster-oblique-v48.png" alt="完整庭院侧向渲染"></details>
<p>已检查窗洞后方净空、玻璃与窗框接合及网页几何。玻璃反射的视角变化仍属近似，浏览器实际显示待验证。</p>
<p><a href="poster-upper-windows-v48/verification-v48.json">模型检查</a> · <a href="poster-upper-windows-v48/visual-review-v48.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-upper-windows-v48">' in gallery:gallery=re.sub(r'<section id="poster-upper-windows-v48">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''左侧高窗实体重建 v48

完整模型：Suzume_dual_scene_upper_windows_v48.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

四处可见高窗改为真实墙体开口与封闭窗框、玻璃实体。跨分段的窗有两块连续玻璃，全组共五块玻璃实体；每块均与至少三个窗框构件接合。两道旧房间隔墙在这一层退让，窗洞后方一米范围已确认没有旧墙堵塞。
两段上层墙体、四段室内隔墙、窗框及玻璃共 33 个封闭实体、10,208 个三角形。保留的旧面坐标和 UV 已核对，电影人物与异世界模型保持原有状态。
新建部分使用原始分辨率的固定 UV 表面纹理，追加剔除两条原遮罩漏掉的前景细杆。保留的旧立面纹理仅修改这两条杆影覆盖的 707 个像素，其他像素逐字节保留。纹理遮挡区域、不可见结构和随视角变化的玻璃反射仍为近似。

海报网页：http://127.0.0.1:8931/viewer/poster-v48.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

正面、局部、侧向渲染及网页几何、资源检查已完成。浏览器实际 GPU 显示仍待验证，整体尚未达到一比一。
''',encoding='utf-8');print('UPPER_WINDOWS_48_RELEASED',v['nativeSha256'])
