from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).parent;O=R/'poster-v38'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
a=read('integration-v38.json');v=read('verification-v38.json');b=read('browser-verification-v38.json');review=read('visual-review-v38.json');color=read('color-comparison-v38.json');restored=read('restoration-v38.json')
native=O/a['nativeFile'];alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==a['nativeSha256']
assert v['freshReopenVerified'] and v['movieGeometryTopologyMaterialsModifiersWorldAndCameraPreserved'] and v['independentSceneObjectsAndMaterials'] and v['packedSourceImagesVerified']
assert len(v['closedCloudMeshes'])==47 and all(q['nonManifoldEdges']==0 for q in v['closedCloudMeshes'])
assert review['acceptedAsIncrementalImprovement'] and all(review[k] for k in ['currentMovieEnvironmentAtPosterCameraReviewed','originalOfficialPosterReviewed','posterFrontFinalReviewed','posterObliqueReviewed'])
assert color['meanPatchColorError255']['posterV38']<color['meanPatchColorError255']['previousPosterNative']
assert len(b['httpResources'])==9 and b['inlineScriptsParsed']
assert not review['oneToOneComplete']
for name in ['poster-front-final-v38.png','poster-oblique-v38.png']:
    assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [restored['movieSourceSha256'],a['nativeSha256']], 'Primary scene changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==a['nativeSha256']
result={'revision':38,'nativeFile':'poster-v38/'+a['nativeFile'],'nativeSha256':a['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieGeometryRevision':37,'posterIndependentEnvironment':True,'movieStatePreservedExactly':True,'posterViewsRenderedAndReviewed':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v38.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','browserDefaultRemainsRevision':17,'browserRuntimeVerified':False,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v38.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'))
status['status']='native_v38_independent_poster_and_movie_environments'
status['scene'].update({'currentNative':result['nativeFile'],'revision':38,'dualReferenceScenesPreserved':True,'posterScene':result['posterScene'],'movieScene':result['movieScene'],'posterNativeVerifiedV38':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'posterNativeCalibrationRevision':38,'posterNativeColorConversionCalibrated':True,'movieCalibrationCandidate':'movie-collar-v37/Suzume_scene_movie_collar_v37.blend','movieCalibrationCandidateRevision':37,'oneToOneComplete':False})
status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-v38"><h2>关门海报与电影开门 · 独立双场景 v38（重建中）</h2>
<p>海报庭院与电影庭院分开保存，避免两幅参照的机位、建筑和钢架校准相互覆盖。海报原生渲染修正了天空、云层及已有表面颜色的显示转换；电影人物和穿门分区保持 v37。</p>
<p><a href="viewer/poster-v38.html">旋转查看关门海报</a> · <a href="viewer/candidate-v37.html">旋转查看电影开门</a>（两页显示均待实测） · <a href="poster-v38/Suzume_dual_scene_v38.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-v38/poster-front-final-v38.png" alt="独立海报场景的原生正面渲染"><figcaption>实体庭院与云层可自由绕看。右上折断工字梁、水纹、远云和建筑细节尚未达到一比一。</figcaption></figure>
<details><summary>查看侧向视角与修复前对照</summary><img src="poster-v38/poster-oblique-v38.png" alt="海报环境的侧向检查"><img style="max-width:350px" src="poster-v38/poster-current-before-v38.png" alt="修复前受到电影环境改动影响的海报视角"></details>
<p><a href="poster-v38/verification-v38.json">场景独立性与几何检查</a> · <a href="poster-v38/color-comparison-v38.json">八处天空与云层颜色检查</a> · <a href="poster-v38/visual-review-v38.json">画面检查与待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-v38">' in gallery:gallery=re.sub(r'<section id="poster-v38">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
before=color['meanPatchColorError255']['previousPosterNative'];after=color['meanPatchColorError255']['posterV38']
(O/'使用说明.txt').write_text(f'''海报与电影双场景 v38

完整模型：Suzume_dual_scene_v38.blend。主文件 suzume-full-scene.blend 已同步。
在 Blender 顶部场景选择器中切换：
1. Official poster courtyard v38：关门海报，第 1 帧，独立环境和机位。
2. Daytime circular hotel：电影开门，第 72 帧，保留 v37 人物与穿门效果。
3. Night meadow through the door：独立异世界。
鼠标中键旋转视角，滚轮缩放。两套完整庭院是分别校准的参照版本。

此次恢复海报对应的建筑和钢架布局，并校准原生渲染中已有表面颜色的显示转换。
47 个云体均为有体积的封闭网格。没有加入整幅画面的平面卡片。
电影场景 2360 个网格的几何、拓扑、材质、修改器、世界和相机检查保持一致。
所用图片均打包在模型里，原始图片像素未改动。

八处天空与云层颜色采样的平均通道误差从约 {before:.1f} 降到 {after:.1f}（0–255）。
这一数值只描述八处局部颜色，不能证明整幅画面或完整三维场景达到一比一。
五根钢架端点按原先手工标注核对，深度仍属重建推定。

海报网页：http://127.0.0.1:8931/viewer/poster-v38.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
网页脚本和本地资源已检查，实际浏览器 GPU 显示仍未验证；默认入口仍为 v17。

尚未达到一比一：海报右上折断工字梁、水面反射和波光、远云轮廓、建筑与植物细节；
电影人物神态、颈胸接缝、材质、近景机位和夜景仍待继续校准。
''',encoding='utf-8')
print('POSTER_38_RELEASED',a['nativeSha256'],flush=True)
