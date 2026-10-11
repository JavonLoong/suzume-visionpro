"""Publish an explicitly labeled comparison without replacing the stable scene."""
from pathlib import Path
import json,re,subprocess,urllib.request,hashlib
R=Path(__file__).parent;O=R/'movie-calibration-v20';W=R/'viewer'
verification=json.loads((O/'verification-v20.json').read_text(encoding='utf-8'))
review=json.loads((O/'visual-review-v20.json').read_text(encoding='utf-8'))
assert verification['freshReopenVerified'] and verification['characterWorldVerticesExactlyPreserved']
assert review['frontReviewed'] and review['overviewReviewed'] and review['sideReviewed']
native=O/'Suzume_scene_movie_candidate_v20.blend'
for name in ['movie-front-candidate-v20.png','movie-overview-v20.png','movie-side-v20.png']:
    assert (O/name).stat().st_mtime>native.stat().st_mtime
assert len({hashlib.sha256((O/name).read_bytes()).digest() for name in ['movie-front-candidate-v20.png','movie-overview-v20.png','movie-side-v20.png']})==3
verification['allAngleImagesReviewed']=True
verification['oneToOneComplete']=False
verification['reviewScope']='Front, oblique overview and left-side snapshots; not exhaustive orbit or fidelity approval.'
(O/'verification-v20.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
html=(W/'candidate-v20.html').read_text(encoding='utf-8')
for attrs,script in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S):
    if 'src=' in attrs or not script.strip():continue
    p=subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'],input=script,text=True,capture_output=True);assert p.returncode==0,p.stderr
assert 'root.movieCourtyardEvidence=' in html and 'localClippingEnabled=true' in html
assert 'radius:190,target:[16,8,39]' in html
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v20.html',timeout=10) as response:
    assert response.status==200 and response.read()==(W/'candidate-v20.html').read_bytes()
release={'revision':20,'role':'movie-opening comparison candidate','nativeFile':'movie-calibration-v20/Suzume_scene_movie_candidate_v20.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v20.html','browserSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'browserBlocker':'CUA inventory timed out after 20 seconds during this iteration.','nativeFrontSideOverviewReviewed':True,'characterFootCorrectionAndPortalPartitionPreserved':True,'geometryScaleInferred':True,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v20.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'))
status['scene']['movieCalibrationCandidate']='movie-calibration-v20/Suzume_scene_movie_candidate_v20.blend'
status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v20.html'
status['scene']['movieCalibrationCandidateRevision']=20
status['scene']['movieCalibrationNativeVerified']=True
status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-courtyard-v20"><h2>电影镜头立面校准 · v20（候选）</h2>
<p>按开门画面的窗边、立柱和水面位置调整完整环形建筑。独立混元头模、脚部间隙和穿门分隔保留。建筑尺寸仍为推定，台基、窗型与原画仍有差距，尚未达到一比一。</p>
<p><a href="movie-calibration-v20/Suzume_scene_movie_candidate_v20.blend">完整 Blender 对照场景</a> · <a href="viewer/candidate-v20.html">可旋转网页对照版</a>（网页运行待复测） · <a href="Suzume_scene_Hunyuan_v19.blend">保留的 v19 场景</a></p>
<figure class="scene"><img src="movie-calibration-v20/movie-front-candidate-v20.png" alt="电影开门镜头立面校准候选"><figcaption>立面校准候选；建筑整体距离和尺寸仍需进一步确定。</figcaption></figure>
<p><a href="movie-calibration-v20/movie-overview-v20.png">完整环形建筑俯视检查</a> · <a href="movie-calibration-v20/movie-side-v20.png">门侧面检查</a> · <a href="movie-calibration-v20/verification-v20.json">模型校验记录</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-courtyard-v20">' in gallery:gallery=re.sub(r'<section id="movie-courtyard-v20">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影镜头立面校准候选 v20

Suzume_scene_movie_candidate_v20.blend 是可编辑、可自由旋转的完整三维对照场景。
时间轴第 72 帧为开门；第 1 帧为关门。人物使用 v17 独立混元头模，身体和脚部几何没有修改。
该文件保留昼景与异世界两套场景，并继续按门平面切分人物。
movie-front-candidate-v20.png、movie-side-v20.png、movie-overview-v20.png 是保存后重新打开并渲染的检查图。

网页对照版：http://127.0.0.1:8931/viewer/candidate-v20.html
网页只验证了脚本语法和本地服务；浏览器连接超时，尚未完成运行时与交互检查。
原网页和 v19 原生文件继续保留。

尺寸说明：动画截图不能唯一确定空间深度。建筑半径暂设 70.5 个场景单位；这是拟合推定值，不是官方尺寸。
13 个立面标记的误差只反映这些手工标记，不能作为整幅相似度。
水面交线仍有约 39–52 个原图像素偏差；窗型、台基、钢架、光照与人物神态仍有差距。
当前没有通过一比一验收。
''',encoding='utf-8')
print(json.dumps(release,ensure_ascii=False,indent=2))
