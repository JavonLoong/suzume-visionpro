from pathlib import Path
import hashlib
import json
import re
import shutil

R = Path(__file__).parent
O = R / 'poster-left-steel-v44'
V = Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read = lambda name: json.loads((O / name).read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
verification = read('verification-v44.json')
browser = read('browser-code-verification-v44.json')
web = read('browser-http-verification-v44.json')
spec = read('browser-steel-v44.json')
connections = read('connections-v44.json')
native = O / 'Suzume_dual_scene_left_steel_v44.blend'
alias = V / 'suzume-full-scene.blend'

# The front, detail/comparison, and oblique images were visually inspected.
review = {
    'revision': 44,
    'nativeSha256': verification['nativeSha256'],
    'frontReviewed': True,
    'leftSteelDetailReviewed': True,
    'obliqueReviewed': True,
    'referenceComparisonReviewed': True,
    'acceptedAsIncrementalImprovement': True,
    'observations': [
        'The final front restores the missing upper broken tie and curved brackets, lowers both long horizontal ties to their observed heights, and replaces three posts, two bowed broken beams, hanging rods and footings.',
        'The enlarged official-reference/before/after comparison shows improved centerline alignment. The outer column now has multiple folded edges and a corrected cut plane. Its pale edges and weathering remain less irregular than the illustration; the middle and back posts also remain too clean.',
        'The final oblique render shows the new members as solid depth-bearing geometry integrated into the circular courtyard. Physical overlap is independently verified at 27 intended joints. Hidden depths and cross sections are inferred from the scene, not measured from unseen official views.',
        'The detail image is an unmodified copy of the reviewed final trial rendered from the same native SHA. Full front and oblique views were rendered from that saved model afterward.',
        'Roof equipment, parapet and facade openings visibly differ from the reference. They were preserved in this revision and remain a major next priority.',
        'Movie character, feet, portal partition, night scene and shared node groups are unchanged from the preceding verified native model.',
        'Browser geometry, normals, UVs, material parameters and HTTP bytes pass their checks. A fresh Edge tab inventory attempt failed with nodeRepl.fetch request failed after 21.6 seconds. Actual browser/GPU rendering remains unverified.'
    ],
    'remaining': [
        'Align facade openings, rooftop equipment, parapet silhouette, ivy and shore debris. Inspect existing facade geometry before using it as an attachment target.',
        'Refine pale steel edges, corrosion, irregular damage and connection details; left columns remain smoother and cleaner than the reference.',
        'Refine lower-cloud ridge contours, pale gaps, hidden shapes and back lighting; some hidden banks remain too regular. Refine the five dominant clouds and other faint fragments.',
        'Align submerged poster stone outlines and major water glints; reduce angular straightness from oblique views and tune reflected facade detail.',
        'Continue movie character neck/chest blending, expression and material style, close-up camera and night-world detail.',
        'Verify both browser candidates in a functioning browser and reconcile approximate water and steel materials with native rendering.'
    ],
    'browserRuntimeVerified': False,
    'nativeBrowserAppearanceEquivalenceVerified': False,
    'oneToOneComplete': False
}
assert sha(native) == verification['nativeSha256'] == spec['nativeSha256'] == browser['nativeSha256']
assert all(verification[key] for key in [
    'freshReopenVerified', 'movieStatePreservedExactly', 'nightScenePreservedExactly',
    'otherPosterObjectsMaterialsCameraLightingPreserved', 'sharedNodeGroupsPreserved',
    'retainedOriginalSteelCoordinatesPreserved', 'allCheckedJointsOverlap'
])
assert len(verification['addedMembers']) == 20
assert all(member['nonManifoldEdges'] == 0 and member['signedVolume'] > 0
           and member['maximumVertexErrorMeters'] < 2e-6 for member in verification['addedMembers'])
assert len(connections['checks']) == verification['checkedPhysicalJoints'] == 27
assert all(check['verified'] for check in connections['checks'])
assert all(browser[key] for key in [
    'positionsNormalsUVsMatchNativeExportExactly', 'originalMaterialsReused',
    'approximateNewMaterialsMatchSpec', 'unrelatedSceneObjectsPreserved',
    'onlyCurrentSteelPayloadRequested'
])
assert browser['triangles'] == 89956 and browser['buckets'] == 12
for resource in web['resources']:
    assert sha(R / resource['path']) == resource['sha256'], resource['path']
images = ['poster-front-v44.png', 'left-steel-detail-v44.png', 'poster-oblique-v44.png']
for name in images:
    assert (O / name).stat().st_mtime > native.stat().st_mtime
review['reviewedImageSha256'] = {name: sha(O / name) for name in images}
(O / 'visual-review-v44.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
assert sha(alias) in [verification['sourceNativeSha256'], verification['nativeSha256']], 'Primary model changed externally; preserve it.'
shutil.copy2(native, alias)
assert sha(alias) == verification['nativeSha256']
result = {
    'revision': 44,
    'nativeFile': 'poster-left-steel-v44/' + native.name,
    'nativeSha256': verification['nativeSha256'],
    'primaryNativeAlias': str(alias),
    'posterScene': 'Official poster courtyard v38',
    'movieScene': 'Daytime circular hotel',
    'nightScene': 'Night meadow through the door',
    'movieRevision37Preserved': True,
    'addedClosedLeftSteelMembers': 20,
    'verifiedPhysicalJoints': 27,
    'posterBrowser': 'http://127.0.0.1:8931/viewer/poster-v44.html',
    'movieBrowser': 'http://127.0.0.1:8931/viewer/candidate-v37.html',
    'browserRuntimeVerified': False,
    'browserDefaultRemainsRevision': 17,
    'oneToOneComplete': False,
    'remaining': review['remaining']
}
(O / 'release-v44.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
status = json.loads((R / 'status.json').read_text(encoding='utf-8'))
status['status'] = 'native_v44_poster_left_steel'
status['scene'].update({
    'currentNative': result['nativeFile'], 'revision': 44,
    'posterNativeCalibrationRevision': 44, 'posterNativeVerifiedV44': True,
    'posterObservedLeftSteelworkVerified': True,
    'posterBrowserCandidate': result['posterBrowser'],
    'posterBrowserRuntimeVerified': False, 'oneToOneComplete': False
})
status['next'] = review['remaining']
(R / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
section = '''<section id="poster-left-steel-v44"><h2>左侧钢架与断梁重建 · v44（重建中）</h2>
<p>补回上方断梁、弧形支撑和悬垂杆，修正横梁高度、立柱截面与两段弯梁。新增 20 个实体部件，27 个接点已检查。</p>
<p><a href="viewer/poster-v44.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-left-steel-v44/Suzume_dual_scene_left_steel_v44.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-left-steel-v44/poster-front-v44.png" alt="左侧钢架重建后的完整海报场景"><figcaption>钢架位置和连接已有改善。建筑、屋顶设备、风化细节、人物和夜景仍在校准。</figcaption></figure>
<details><summary>局部参照对比与侧向视角</summary><img src="poster-left-steel-v44/left-steel-comparison-v44.png" alt="官方参照与钢架重建前后对比"><img src="poster-left-steel-v44/left-steel-detail-v44.png" alt="左侧钢架细节"><img src="poster-left-steel-v44/poster-oblique-v44.png" alt="完整庭院侧向渲染"></details>
<p>原生模型、网页几何与资源已检查；浏览器控制尚未恢复，实际网页显示仍待验证。</p>
<p><a href="poster-left-steel-v44/verification-v44.json">模型检查</a> · <a href="poster-left-steel-v44/connections-v44.json">接点检查</a> · <a href="poster-left-steel-v44/visual-review-v44.json">待完成项</a></p></section>'''
gallery = (R / 'index.html').read_text(encoding='utf-8')
if '<section id="poster-left-steel-v44">' in gallery:
    gallery = re.sub(r'<section id="poster-left-steel-v44">.*?</section>', section, gallery, flags=re.S)
else:
    gallery = gallery.replace('</h1>', '</h1>' + section, 1)
(R / 'index.html').write_text(gallery, encoding='utf-8')
(O / '使用说明.txt').write_text('''左侧钢架与断梁重建 v44

完整模型：Suzume_dual_scene_left_steel_v44.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

本版替换参照左侧范围内的旧钢架构件，补入 20 个封闭实体部件。原有右侧钢架、庭院、门、水面、云层和电影人物均保留。
27 个预期接点经过实体重叠检查。不可见纵深、截面和背面为数学推定，整体尚未达到一比一。
原生模型已重新打开检查，并检查正面、细节和侧向渲染。

海报网页：http://127.0.0.1:8931/viewer/poster-v44.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html
网页几何、法线、UV 和 HTTP 资源检查通过。网页钢材仍采用近似材质；浏览器实际 GPU 显示未验证。

后续优先校准建筑门窗、屋顶设备和女儿墙，再继续风化细节、水中石板、人物表情与颈胸衔接、异世界细节。
''', encoding='utf-8')
print('LEFT_STEEL_44_RELEASED', verification['nativeSha256'], flush=True)
