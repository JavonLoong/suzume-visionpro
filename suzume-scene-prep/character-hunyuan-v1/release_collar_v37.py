from pathlib import Path
import hashlib
import json
import re
import shutil

R = Path(__file__).parent
O = R / 'movie-collar-v37'
V = Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
read = lambda name: json.loads((O / name).read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
v = read('verification-v37.json')
b = read('browser-verification-v37.json')
a = read('integration-v37.json')
review = read('visual-review-v37.json')
native = O / 'Suzume_scene_movie_collar_v37.blend'
assert all(v[k] for k in [
    'freshReopenVerified', 'feetGripAndNonCollarGeometryPreserved',
    'faceAndPonytailPreservedExactly', 'clothUVSamplingVerified',
    'originalTexturePixelsPreserved', 'sharedSpatialMeshesAndMaterialsVerified',
    'dualQuaternionBodyAndHemPreserved', 'closedAndOpenVisibilityVerified',
    'neckAndChestSkinMaterialShared'])
assert v['collarTriangleFlips'] == v['collarDegenerateTriangles'] == v['closedHemBoundaryEdges'] == 0
assert v['hemSignedVolume'] > 0
assert all(b[k] for k in ['bodyBaseColorPixelsPreserved', 'collarUVExportVerified', 'inlineSyntaxVerified', 'rigidDoorAndDepthAwareNightPathsRetained'])
assert len(b['httpResourcesVerified']) == 7
assert review['accepted'] and not review['oneToOneComplete']
assert all(review[k] for k in ['sceneFrontReviewed', 'headFrontReviewed', 'headBackReviewed', 'headSideReviewed', 'headPortraitReviewed', 'collarDetailReviewed'])
assert sha(native) == v['nativeSha256']
for name in ['movie-front', 'head-front', 'head-back', 'head-side', 'head-portrait', 'collar-detail']:
    assert (O / (name + '-v37.png')).stat().st_mtime > native.stat().st_mtime
alias = V / 'suzume-full-scene.blend'
assert sha(alias) in [a['sourceSha256'], v['nativeSha256']], 'Primary scene changed externally; preserve it.'
shutil.copy2(native, alias)
assert sha(alias) == v['nativeSha256']

result = {
    'revision': 37,
    'nativeFile': 'movie-collar-v37/Suzume_scene_movie_collar_v37.blend',
    'nativeSha256': v['nativeSha256'],
    'primaryNativeAlias': str(alias),
    'currentNativeRevision': 37,
    'previousNativeRevisionPreserved': 36,
    'headSource': 'Mathematical v36 face and solid ponytail, with a locally reshaped lower neck; Hunyuan 3.1 body with repaired collar geometry and UV sampling. No new Hunyuan submission.',
    'collarRimRepaired': True,
    'feetGripAndNonCollarGeometryPreserved': True,
    'faceAndPonytailPreservedExactly': True,
    'sharedSpatialMeshesAndMaterialsVerified': True,
    'sixRendersReviewed': True,
    'characterTriangles': sum(v['partTriangles'].values()),
    'browserCandidate': 'viewer/candidate-v37.html',
    'browserRuntimeVerified': False,
    'browserDefaultRemainsRevision': 17,
    'oneToOneComplete': False,
    'remaining': review['remaining'],
}
(O / 'release-v37.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
status = json.loads((R / 'status.json').read_text(encoding='utf-8'))
status['status'] = 'native_v37_collar_and_neck_attachment_refinement'
status['scene'].update({
    'currentNative': result['nativeFile'], 'revision': 37,
    'headGeometryRevision': 37, 'faceGeometryRevision': 36,
    'headGeometrySource': result['headSource'],
    'headReconstruction': 'Mathematical head with official-reference frontal proportions and solid ponytail; lower neck reshaped into the repaired Hunyuan body collar. A neck/chest shading junction remains.',
    'nativePartitionVerifiedV37': True,
    'movieCalibrationCandidate': result['nativeFile'],
    'movieCalibrationCandidateRevision': 37,
    'movieCalibrationBrowserCandidate': 'http://127.0.0.1:8931/viewer/candidate-v37.html',
    'browserCandidateAsset': 'viewer/character-v37/suzume-posed-v37.gltf',
    'browserCandidateTriangles': result['characterTriangles'],
    'browserCandidateRuntimeVerified': False,
    'collarGeometryAndUVRepairVerified': True,
    'neckChestSkinMaterialShared': True,
    'oneToOneComplete': False,
})
status['next'] = review['remaining']
(R / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

section = '''<section id="movie-collar-v37"><h2>衣领修复与颈部连接 · v37（重建中）</h2>
<p>修平混元模型领口的锯齿，补上仅沿衣料边缘延伸的封闭卷边，调整局部贴图坐标和颈底形状。面部、马尾、脚部与握门姿势保留。</p>
<p><a href="movie-collar-v37/Suzume_scene_movie_collar_v37.blend">当前完整 Blender 场景</a> · <a href="viewer/candidate-v37.html">可旋转网页候选</a>（显示待实测） · <a href="viewer/character-v37/suzume-posed-v37.glb">当前人物 GLB</a></p>
<figure class="scene"><img style="max-width:650px" src="movie-collar-v37/head-portrait-v37.png" alt="当前独立三维头部与衣领"><figcaption>领口轮廓已修平；颈部与胸口仍有明暗接缝，人物神态和材质风格还未达到一比一。</figcaption></figure>
<details><summary>查看领口细节、完整场景与三视角</summary>
<img style="max-width:800px" src="movie-collar-v37/collar-detail-v37.png" alt="领口修复细节及仍可见的颈底接缝">
<img src="movie-collar-v37/movie-front-v37.png" alt="完整开门场景">
<img style="max-width:32%" src="movie-collar-v37/head-front-v37.png" alt="人物正面">
<img style="max-width:32%" src="movie-collar-v37/head-back-v37.png" alt="人物背面">
<img style="max-width:32%" src="movie-collar-v37/head-side-v37.png" alt="人物侧面"></details>
<p><a href="movie-collar-v37/verification-v37.json">模型与穿门分区检查</a> · <a href="movie-collar-v37/visual-review-v37.json">画面检查与待完成项</a> · <a href="viewer/candidate-v36.html">上一版对照</a></p></section>'''
gallery = (R / 'index.html').read_text(encoding='utf-8')
if '<section id="movie-collar-v37">' in gallery:
    gallery = re.sub(r'<section id="movie-collar-v37">.*?</section>', section, gallery, flags=re.S)
else:
    gallery = gallery.replace('</h1>', '</h1>' + section, 1)
(R / 'index.html').write_text(gallery, encoding='utf-8')
(O / '使用说明.txt').write_text('''衣领修复与颈部连接 v37

当前完整场景：Suzume_scene_movie_collar_v37.blend，第 72 帧为开门姿势。
主场景 suzume-full-scene.blend 已同步，v36 与更早文件保留。
身体来自混元 3.1，当前头部为独立数学几何；此轮没有新的混元生成。

修复范围：2976 个领口顶点、837 个局部 UV 顶点和 341 个颈底顶点。
新增 1.1 mm 半径的衣领卷边，为两端封口的 C 形实体，不经过前胸裸露皮肤。
229 个胸颈皮肤三角面改用与头部相同的肤色材质，日间与异世界各自匹配。
原始贴图像素不变。脸、马尾和领口范围之外的身体顶点完全保留。

重新打开原生文件检查通过：修改区无翻转或退化三角面，卷边无开放边；
日间/异世界共享网格与骨架，互补门平面裁切和开关门可见性保持。
人物导出共 548069 个三角面。GLTF 顶点及 UV 与原生模型误差小于百万分之一。

movie-front-v37.png：完整场景。head-front/back/side-v37.png：中性灯光三视角。
head-portrait-v37.png：正面近景。collar-detail-v37.png：衣领与颈底细节。
网页候选：http://127.0.0.1:8931/viewer/candidate-v37.html
人物 GLB：../viewer/character-v37/suzume-posed-v37.glb
网页资源、语法和模型导出已检查，实际浏览器 GPU 显示尚未验证；默认网页仍为 v17。

尚未达到一比一：颈底仍有明暗接缝；神态、侧脸、发型细节与材质风格、
门板近景相机、夜空与庭院水面，以及关门海报场景仍需校准。
''', encoding='utf-8')
print('COLLAR_37_RELEASED', result['nativeSha256'], flush=True)
