from pathlib import Path
import hashlib
import json
import re
import shutil

R = Path(__file__).parent
O = R / 'poster-right-arches-v55'
V = Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read = lambda n: json.loads((O / n).read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
v = read('verification-v55.json')
review = read('visual-review-v55.json')
b = read('browser-code-verification-v55.json')
web = read('browser-http-verification-v55.json')
spec = read('browser-right-arches-v55.json')
surface = read('surface-restoration-v55.json')
native = O / 'Suzume_dual_scene_right_arches_v55.blend'
alias = V / 'suzume-full-scene.blend'
assert sha(native) == v['nativeSha256'] == review['nativeSha256'] == b['nativeSha256'] == spec['nativeSha256']
assert all(v[k] for k in ['freshReopenVerified', 'movieStatePreservedExactly',
    'nightScenePreservedExactly', 'otherPosterObjectsMaterialsCameraLightingPreserved',
    'sharedNodeGroupsPreserved', 'unchangedOriginalFacePositionsAndUVsPreserved',
    'allExistingPackedImageBytesPreserved'])
assert len(v['addedSolids']) == 55
assert all(q['nonManifoldEdges'] == 0 and q['signedVolume'] > 0 and
           q['maximumVertexErrorMeters'] < 2e-6 for q in v['addedSolids'])
assert sum(q['triangles'] for q in v['addedSolids']) == 302028
assert len(v['changedOriginalMeshes']) == 9 and len(v['replacedPriorCornices']) == 2
assert len(v['structuralOpeningProbes']) == 17
assert len(v['lowerWallContacts']) == len(v['roofTransitionContacts']) == 9
assert all(abs(q['lowerWallTopZ'] - 4.44) < 2e-6 for q in v['lowerWallContacts'])
assert all(abs(q['originalRoofTopZ'] - 5.94) < 2e-6 for q in v['roofTransitionContacts'])
assert v['packedImageCount'] == 25 and v['preservedOriginalPackedImages'] == 24
assert v['restoredAtlasSha256'] == surface['atlasSha256'] == sha(O / 'right-arcade-pigments-v55.png')
assert surface['outsidePatchPixelsPreservedExactly'] and surface['restoredPixelsEqualColorGradedSourceExactly']
assert surface['foregroundBeamExclusionRetained'] and surface['restoredPixels'] == 4714
assert all(b[k] for k in ['positionsNormalsAndUVsMatchNativeExactly',
    'previousUnaffectedGeometryAndMaterialsPreserved', 'allIvyMatricesAndColorsPreservedExactly',
    'existingMaterialInstancesReused', 'newRightPaintIsolated'])
assert b['previousBucketsReplaced'] == 12 and b['buckets'] == 15 and b['triangles'] == 436961
assert len(web['resources']) == 38 and web['nativeDownloadAvailable']
assert review['acceptedAsIncrementalImprovement'] and not review['oneToOneComplete']
assert all(review[k] for k in ['frontReviewed', 'detailReviewed', 'obliqueReviewed',
    'obliqueDetailReviewed', 'referenceComparisonReviewed'])
for q in web['resources']:
    assert sha(R / q['path']) == q['sha256']
for name, value in review['reviewedImageSha256'].items():
    assert (O / name).stat().st_mtime > native.stat().st_mtime and sha(O / name) == value
assert sha(alias) in [v['sourceNativeSha256'], v['nativeSha256']], 'Primary model changed externally; preserve it.'
shutil.copy2(native, alias)
assert sha(alias) == v['nativeSha256']
result = {
    'revision': 55, 'nativeFile': 'poster-right-arches-v55/' + native.name,
    'nativeSha256': v['nativeSha256'], 'primaryNativeAlias': str(alias),
    'posterScene': 'Official poster courtyard v38', 'movieScene': 'Daytime circular hotel',
    'nightScene': 'Night meadow through the door', 'movieRevision37Preserved': True,
    'closedReconstructedAssemblies': 55, 'archUnits': 16, 'additionalGrayRecesses': 1,
    'clearanceProbesVerified': 17, 'lowerWallContactsVerified': 9,
    'roofContactsVerified': 9, 'restoredVisibleSourcePixels': 4714,
    'posterBrowser': 'http://127.0.0.1:8931/viewer/poster-v55.html',
    'movieBrowser': 'http://127.0.0.1:8931/viewer/candidate-v37.html',
    'browserRuntimeVerified': False, 'browserDefaultRemainsRevision': 17,
    'oneToOneComplete': False, 'remaining': review['remaining'],
}
(O / 'release-v55.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
status = json.loads((R / 'status.json').read_text(encoding='utf-8'))
status['status'] = 'native_v55_poster_right_arcade'
status['scene'].update({'currentNative': result['nativeFile'], 'revision': 55,
    'posterNativeCalibrationRevision': 55, 'posterNativeVerifiedV55': True,
    'posterRightUpperArcadeReconstructed': True, 'posterBrowserCandidate': result['posterBrowser'],
    'posterBrowserRuntimeVerified': False, 'oneToOneComplete': False})
status['next'] = review['remaining']
(R / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
section = '''<section id="poster-right-arches-v55"><h2>右侧拱廊与檐线重建 · v55（重建中）</h2>
<p>右侧上层现已重建十处大拱龛、五处小拱龛、一处尖拱及灰色壁龛。曲面墙体、凹入墙板、拱边和起伏檐线均有立体厚度，屋顶过渡段已接到原屋面。</p>
<p><a href="viewer/poster-v55.html">旋转查看最新海报场景</a> · <a href="viewer/candidate-v37.html">电影开门场景</a> · <a href="poster-right-arches-v55/Suzume_dual_scene_right_arches_v55.blend">下载双场景 Blender 模型</a></p>
<figure class="scene"><img style="max-width:560px" src="poster-right-arches-v55/poster-front-v55.png" alt="右侧拱廊修正后的完整海报场景"><figcaption>拱廊和屋顶轮廓已进一步校准；整体仍在重建，尚未达到一比一。</figcaption></figure>
<details><summary>参照对比、局部和旋转视角</summary><img src="poster-right-arches-v55/right-arches-comparison-v55.png" alt="右侧拱廊参照与修正前后对比"><img src="poster-right-arches-v55/right-arches-detail-v55.png" alt="右侧拱廊局部"><img src="poster-right-arches-v55/right-arches-oblique-detail-v55.png" alt="拱廊曲面墙体近距离侧视图"><img src="poster-right-arches-v55/poster-oblique-v55.png" alt="完整庭院旋转视角"></details>
<p>55 组新增几何已检查封闭性，17 处凹入空间及上下墙体、屋顶连接均通过检查。前景弯梁仍偏厚偏暗，植物、旧物、磨损和隐藏结构仍需校准；浏览器实际显示待验证。</p>
<p><a href="poster-right-arches-v55/verification-v55.json">模型检查</a> · <a href="poster-right-arches-v55/visual-review-v55.json">待完成项</a></p></section>'''
gallery = (R / 'index.html').read_text(encoding='utf-8')
if '<section id="poster-right-arches-v55">' in gallery:
    gallery = re.sub(r'<section id="poster-right-arches-v55">.*?</section>', section, gallery, flags=re.S)
else:
    gallery = gallery.replace('</h1>', '</h1>' + section, 1)
(R / 'index.html').write_text(gallery, encoding='utf-8')
(O / '使用说明.txt').write_text('''右侧拱廊与檐线重建 v55

完整模型：Suzume_dual_scene_right_arches_v55.blend。主文件 suzume-full-scene.blend 已同步。
Blender 场景：Official poster courtyard v38（第 1 帧海报）、Daytime circular hotel（第 72 帧电影）、Night meadow through the door（异世界）。

上层包含十处大拱龛、五处小拱龛、一处尖拱、灰色壁龛和残墙，配合有厚度的曲面墙体、起伏檐线及屋顶连接，共 55 组封闭几何、302,028 个三角形。17 处结构空间、9 处下层墙体连接和 9 处屋顶连接已检查。
最右拱顶和檐线的旧模糊区域在独立材质中恢复了 4,714 个可见参照像素；保留了前景弯梁遮挡区域。24 张原有打包图片保留，新增 1 张修正材质。
人物、独立头模、脚部间隙、门两侧分割和异世界沿用 v37。

海报网页：http://127.0.0.1:8931/viewer/poster-v55.html
电影网页：http://127.0.0.1:8931/viewer/candidate-v37.html

已检查原生正面、局部、侧面及等分辨率前后对比，网页几何和 HTTP 资源已验证。前景弯梁仍偏厚偏暗，植物、旧物、玻璃反射、磨损及隐藏结构仍需校准，尚未达到一比一。浏览器控制接口仍超时，实际 GPU 显示待验证。
''', encoding='utf-8')
print('RIGHT_ARCHES_55_RELEASED', v['nativeSha256'])
