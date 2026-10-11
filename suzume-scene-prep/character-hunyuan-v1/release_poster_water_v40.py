from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).parent;O=R/'poster-water-v40';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('verification-v40.json');a=read('integration-v40.json');review=read('visual-review-v40.json');b=read('browser-code-verification-v40.json');web=read('browser-http-verification-v40.json');measure=read('poster-front-v40-measurement.json');old=read('poster-front-v39-measurement.json')
native=O/'Suzume_dual_scene_water_v40.blend';alias=V/'suzume-full-scene.blend'
assert sha(native)==v['nativeSha256']==a['nativeSha256']
assert v['freshReopenVerified'] and v['movieStatePreservedExactly'] and v['posterGeometryMaterialsExceptWaterCameraAndLightingPreserved']
assert v['worldSpaceWaveAnimationVerified'] and v['liveReflectionAndRefraction'] and v['noReferenceImageInWater']
assert b['waterGeometryAndTransformUnchanged'] and b['liveRenderTargetsPreserved'] and b['allDeclaredShaderUniformsBound']
assert review['acceptedAsIncrementalImprovement'] and review['frontReviewed'] and review['obliqueReviewed'] and not review['oneToOneComplete']
assert measure['meanBandColorError255']<old['meanBandColorError255']
for q in web['resources']:assert sha(R/q['path'])==q['sha256']
for name in ['poster-front-v40.png','poster-oblique-v40.png']:assert (O/name).stat().st_mtime>native.stat().st_mtime
assert sha(alias) in [a['sourceNativeSha256'],a['nativeSha256']],'Primary model changed externally; preserve it.'
shutil.copy2(native,alias);assert sha(alias)==a['nativeSha256']
result={'revision':40,'nativeFile':'poster-water-v40/'+native.name,'nativeSha256':a['nativeSha256'],'primaryNativeAlias':str(alias),'posterScene':'Official poster courtyard v38','movieScene':'Daytime circular hotel','nightScene':'Night meadow through the door','movieRevision37Preserved':True,'posterBrowser':'http://127.0.0.1:8931/viewer/poster-v40.html','movieBrowser':'http://127.0.0.1:8931/viewer/candidate-v37.html','waterBandMeanColorErrorBefore':old['meanBandColorError255'],'waterBandMeanColorErrorAfter':measure['meanBandColorError255'],'metricScope':'Five fixed water bands; mean RGB differences only, not pixelwise likeness or full-scene fidelity.','browserRuntimeVerified':False,'browserWaterApproximate':True,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v40.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v40_poster_water_reflection_and_scattering';status['scene'].update({'currentNative':result['nativeFile'],'revision':40,'posterNativeCalibrationRevision':40,'posterNativeVerifiedV40':True,'posterWaterReflectionAndScatteringCalibrated':True,'posterBrowserCandidate':result['posterBrowser'],'posterBrowserRuntimeVerified':False,'oneToOneComplete':False});status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="poster-water-v40"><h2>海报水面与倒影 · v40（重建中）</h2>
<p>水面已调整为较柔和的青蓝色倒影，加入不规则波纹、浅水色散与断续波光。仍由完整场景产生实时反射和透射，可自由旋转；电影版人物与穿门分区保持 v37。</p>
<p><a href="viewer/poster-v40.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-water-v40/Suzume_dual_scene_water_v40.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-water-v40/poster-front-v40.png" alt="校准水面颜色和倒影后的完整三维海报场景"><figcaption>倒影对比和水色已改善；波光位置、石板轮廓、建筑与云层仍需继续对齐。</figcaption></figure>
<details><summary>水面对照与侧向视角</summary><img src="poster-water-v40/poster-front-v40-comparison.png" alt="官方海报水面与原生三维水面对照"><img src="poster-water-v40/poster-oblique-v40.png" alt="水面侧向检查"></details>
<p>网页版本使用近似水面着色，实际浏览器显示尚未验证。</p>
<p><a href="poster-water-v40/verification-v40.json">模型检查</a> · <a href="poster-water-v40/poster-front-v40-measurement.json">固定区域颜色测量</a> · <a href="poster-water-v40/visual-review-v40.json">待完成项</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="poster-water-v40">' in gallery:gallery=re.sub(r'<section id="poster-water-v40">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''海报水面校准 v40

完整模型：Suzume_dual_scene_water_v40.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。
海报名称沿用 v38，钢架为 v39，水面为 v40。电影人物、脚部净空和穿门分区保留。

本次只重建海报水材质；庭院几何、其他材质、机位和环境光保持原样。
水面使用实际场景的反射、IOR 1.333 的折射、不规则毫米级波纹、随视角变化的浅水颜色与断续波光。
水中没有海报贴图。唯一间接图像依赖是原有的颜色转换 LUT。
色散在表面近似实现，波光为程序化美术补充；并非完整体积水模拟或实测光学参数。

网页候选：http://127.0.0.1:8931/viewer/poster-v40.html
电影场景：http://127.0.0.1:8931/viewer/candidate-v37.html
网页脚本、绑定参数和资源下载已检查；浏览器控制超时，GPU 显示与原生外观一致性仍未验证。

仍未达到一比一：水底石板布局、波光位置与反射细节、远云轮廓、建筑植物、钢架截面和材质、人物神态与颈胸衔接、近景机位和夜景。
''',encoding='utf-8')
print('POSTER_WATER_40_RELEASED',a['nativeSha256'],flush=True)
