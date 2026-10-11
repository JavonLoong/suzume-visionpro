"""Publish a reviewed comparison candidate without replacing the stable scene."""
from pathlib import Path
import json, re, hashlib, subprocess, urllib.request
R = Path(__file__).parent
O = R / 'movie-material-v22'
def read(name):
    return json.loads((O/name).read_text(encoding='utf-8'))
v = read('verification-v22.json')
review = read('visual-review-v22.json')
browser = read('browser-geometry-verification-v22.json')
assert v['freshReopenVerified'] and v['bodyHeadHairpinWorldVerticesPreserved']
assert v['wallGeometryPreserved'] and v['wallWatertightAfterWelding']
assert review['frontReviewed'] and review['obliqueReviewed']
assert browser['nativeRoofGeometryMatches'] and browser['ltcTexturesInitialized']
native = O/'Suzume_scene_movie_material_v22.blend'
images = [O/'movie-front-v22.png', O/'movie-window-oblique-v22.png']
assert all(f.stat().st_mtime > native.stat().st_mtime for f in images)
assert len({hashlib.sha256(f.read_bytes()).hexdigest() for f in images}) == 2
page = R/'viewer'/'candidate-v22.html'
for attrs, code in re.findall(r'<script([^>]*)>(.*?)</script>', page.read_text(encoding='utf-8'), re.S):
    if 'src=' in attrs or not code.strip(): continue
    result = subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'], input=code,
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
for suffix in ['viewer/candidate-v22.html', 'viewer/RectAreaLightUniformsLib.js']:
    with urllib.request.urlopen('http://127.0.0.1:8931/'+suffix, timeout=10) as response:
        assert response.status == 200 and response.read() == (R/suffix).read_bytes()
release = {
    'revision':22, 'role':'movie facade material comparison candidate',
    'nativeFile':'movie-material-v22/Suzume_scene_movie_material_v22.blend',
    'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),
    'roofProjectionAndLocalPlasterCorrected':True,
    'originalBodyHeadFootAndPortalVerified':True,
    'nativeFrontAndObliqueReviewed':True, 'stableNativeRemainsRevision':19,
    'browserDefaultRemainsRevision':17, 'browserCandidate':'viewer/candidate-v22.html',
    'browserGeometryAndSyntaxAndHttpVerified':True, 'browserRuntimeVerified':False,
    'browserLightingIsUncalibratedApproximation':True,
    'oneToOneComplete':False, 'remaining':review['remaining'],
}
(O/'release-v22.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
integration = read('integration-v22.json')
integration['visualReviewPending'] = False
integration['visualReview'] = 'visual-review-v22.json'
integration['finalColorEvidence'] = 'final-color-comparison-v22.json'
(O/'integration-v22.json').write_text(json.dumps(integration,ensure_ascii=False,indent=2),encoding='utf-8')
status = json.loads((R/'status.json').read_text(encoding='utf-8'))
status['status'] = 'native_v22_movie_material_comparison_candidate'
status['scene']['movieCalibrationCandidate'] = release['nativeFile']
status['scene']['movieCalibrationCandidateRevision'] = 22
status['scene']['movieCalibrationBrowserCandidate'] = 'http://127.0.0.1:8931/viewer/candidate-v22.html'
status['scene']['movieMaterialCorrectionVerified'] = True
status['next'] = review['remaining']
(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section = '''<section id="movie-material-v22"><h2>电影墙面与光照校准 · v22（候选）</h2>
<p>缩减了右侧檐口的过深投影，单独校正这一段墙面的偏黄材质，并加入庭院补光。玻璃和窗棂已压暗，以保留亮墙与暗窗的对比。圆窗和方窗仍有真实洞口；混元独立头模、脚部修正和穿门分隔已重新校验。</p>
<p><a href="movie-material-v22/Suzume_scene_movie_material_v22.blend">完整 Blender 对照场景</a> · <a href="viewer/candidate-v22.html">可旋转网页候选版</a>（光照与交互待复测） · <a href="movie-material-v22/movie-window-oblique-v22.png">斜视窗洞近景</a></p>
<figure class="scene"><img src="movie-material-v22/movie-front-v22.png" alt="校正墙面材质与补光后的完整开门场景"><figcaption>右侧墙面已提亮并减轻偏绿；整幅场景尚未达到一比一，左侧建筑、水面和人物细节仍需校准。</figcaption></figure>
<p><a href="movie-windows-v21/movie-front-v21.png">上一版同机位渲染</a> · <a href="movie-material-v22/verification-v22.json">模型与裁切校验</a></p></section>'''
gallery = (R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-material-v22">' in gallery:
    gallery = re.sub(r'<section id="movie-material-v22">.*?</section>',section,gallery,flags=re.S)
else:
    gallery = gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影墙面与光照校准 v22

Suzume_scene_movie_material_v22.blend 包含昼景、门、人物和异世界。
第 72 帧为开门。右侧立面的 72 个几何部件仍在集合
Movie right facade — solid openings v21 中。

本版缩小了三段檐口或屋顶的凸出深度，单独校正右侧墙面和石材，
并用 Soft courtyard fill on the movie facade v22 面光源近似电影的漫射补光。
光源位置和建筑尺寸都是推定；不是官方尺寸或实测灯光。
人物身体、独立混元头模、发卡、脚部修正及互补空间裁切经重新打开文件校验。

movie-front-v22.png：完整开门机位。
movie-window-oblique-v22.png：窗洞和墙体的斜视近景。
color-trials-v22.json：三个手选墙面色块的试验，不能当作整幅图相似度。
网页候选：http://127.0.0.1:8931/viewer/candidate-v22.html
网页的几何、语法、资源请求已检查，运行和交互仍待复测。
网页面光源不支持投影，其亮度与 Blender 使用不同单位，未声称两者视觉等同。

此文件尚未达到一比一。稳定原生版 v19 与默认网页 v17 仍分别保留。
''',encoding='utf-8')
print(json.dumps(release,ensure_ascii=False,indent=2))
