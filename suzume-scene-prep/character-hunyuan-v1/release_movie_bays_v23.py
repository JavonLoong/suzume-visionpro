"""Publish the reviewed full-scene comparison; retain earlier stable versions."""
from pathlib import Path
import json,re,subprocess,urllib.request,hashlib
R=Path(__file__).parent;O=R/'movie-bays-v23'
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
v=read('verification-v23.json');review=read('visual-review-v23.json');browser=read('browser-geometry-verification-v23.json')
assert v['freshReopenVerified'] and v['bodyHeadFootAndPortalPreserved'] and v['fourWallsWatertight']
assert v['rightBayV22GeometryPreserved'] and len(v['openings'])==6 and len(v['solidWindowSeparators'])==2
assert review['frontReviewed'] and review['obliqueReviewed'] and browser['nativeLowerWallGeometryMatches']
native=O/'Suzume_scene_movie_bays_v23.blend';images=[O/'movie-front-v23.png',O/'movie-left-oblique-v23.png']
assert all(f.stat().st_mtime>native.stat().st_mtime for f in images)
assert len({hashlib.sha256(f.read_bytes()).hexdigest() for f in images})==2
page=R/'viewer/candidate-v23.html'
for attrs,code in re.findall(r'<script([^>]*)>(.*?)</script>',page.read_text(encoding='utf-8'),re.S):
    if 'src=' in attrs or not code.strip():continue
    check=subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'],input=code,text=True,capture_output=True);assert check.returncode==0,check.stderr
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v23.html',timeout=10) as response:assert response.status==200 and response.read()==page.read_bytes()
result={'revision':23,'role':'movie solid facade comparison candidate','nativeFile':'movie-bays-v23/Suzume_scene_movie_bays_v23.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),
    'rebuiltBays':[12,13,14,15],'newParts':sum(v['newPartsByBay'].values()),'measuredWindowOpenings':6,
    'nativeFrontAndObliqueReviewed':True,'bodyHeadFootAndPortalVerified':True,'rightBayV22Preserved':True,
    'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v23.html',
    'browserGeometrySyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'browserLightingIsApproximate':True,
    'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v23.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
integration=read('integration-v23.json');integration['visualReviewPending']=False;integration['visualReview']='visual-review-v23.json';integration['lighting']='lighting-v23.json';(O/'integration-v23.json').write_text(json.dumps(integration,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v23_movie_solid_facade_comparison_candidate';status['scene']['movieCalibrationCandidate']=result['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=23;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v23.html';status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-bays-v23"><h2>电影窗组与实体立面 · v23（候选）</h2>
<p>四段建筑重新生成，共 669 个可编辑部件。左侧“两扇方窗加一扇拱窗”和右后方双窗按电影参照校准，窗间实墙、洞口厚度、房间、侧墙及屋顶均保留。左墙的冷色阴影和拱窗附近的暖光也已调整。</p>
<p><a href="movie-bays-v23/Suzume_scene_movie_bays_v23.blend">完整 Blender 对照场景</a> · <a href="viewer/candidate-v23.html">可旋转网页候选版</a>（交互和光照待复测） · <a href="movie-bays-v23/movie-left-oblique-v23.png">左侧窗组斜视近景</a></p>
<figure class="scene"><img src="movie-bays-v23/movie-front-v23.png" alt="重建左侧及门后窗组的完整电影对照场景"><figcaption>完整原生渲染。上层建筑、钢架、水面及人物细节仍需校准，尚未达到一比一。</figcaption></figure>
<p><a href="movie-material-v22/movie-front-v22.png">上一版同机位</a> · <a href="movie-bays-v23/verification-v23.json">窗洞、实墙和人物校验</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-bays-v23">' in gallery:gallery=re.sub(r'<section id="movie-bays-v23">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影窗组与实体立面 v23

Suzume_scene_movie_bays_v23.blend 包含完整昼景、门、人物和异世界，第 72 帧为开门。
Movie left and central bays — solid windows v23 集合内有四个建筑分组，共 669 个可编辑部件。
六个可见窗洞按电影参照拟合；方窗之间有实体墙，四段建筑都有完整房间、侧墙、屋顶及上层结构。
上层布局沿用原模型，并未在本版完成电影机位的校准。局部窗边误差不能当作整幅相似度。
原先位于左侧水边、与当前电影画面不符的推定长椅已移除。

混元独立头模、人物身体、脚部修正、互补穿门裁切和右侧 v22 建筑均经重新打开文件检查。
左墙补光为基于画面的推定值，不代表电影的实际灯光或建筑尺寸。
网页候选：http://127.0.0.1:8931/viewer/candidate-v23.html
网页通过几何、语法和本地资源检查，实际渲染与交互仍待复测。

movie-front-v23.png：完整开门机位。
movie-left-oblique-v23.png：四段建筑中的左侧窗组及上层结构斜视。
movie-front-geometry-v23.png：补光前的几何对照图。
本版尚未达到一比一。稳定原生版 v19、默认网页 v17 和此前候选版保留。
''',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
