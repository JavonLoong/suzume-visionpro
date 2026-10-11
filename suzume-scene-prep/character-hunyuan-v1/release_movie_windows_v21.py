from pathlib import Path
import json,re,hashlib,subprocess,urllib.request
R=Path(__file__).parent;O=R/'movie-windows-v21';W=R/'viewer'
v=json.loads((O/'verification-v21.json').read_text(encoding='utf-8'));review=json.loads((O/'visual-review-v21.json').read_text(encoding='utf-8'))
assert v['freshReopenVerified'] and v['bodyHeadHairpinWorldVerticesPreserved'] and v['wallWatertightAfterWelding']
assert review['frontReviewed'] and review['obliqueReviewed']
native=O/'Suzume_scene_movie_windows_v21.blend';images=['movie-front-v21.png','movie-window-oblique-v21.png']
assert all((O/n).stat().st_mtime>native.stat().st_mtime for n in images)
assert len({hashlib.sha256((O/n).read_bytes()).hexdigest() for n in images})==2
page=W/'candidate-v21.html';html=page.read_text(encoding='utf-8')
for attr,code in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S):
    if 'src=' in attr or not code.strip():continue
    check=subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'],input=code,text=True,capture_output=True);assert check.returncode==0,check.stderr
with urllib.request.urlopen('http://127.0.0.1:8931/viewer/candidate-v21.html',timeout=10) as response:assert response.status==200 and response.read()==page.read_bytes()
release={'revision':21,'role':'movie facade comparison candidate','nativeFile':'movie-windows-v21/Suzume_scene_movie_windows_v21.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'rebuiltBay':16,'newEditableObjects':v['newObjects'],'actualRectangularAndCircularWallOpenings':True,'originalBodyHeadFootAndPortalVerified':True,'nativeFrontAndObliqueReviewed':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'browserCandidate':'viewer/candidate-v21.html','browserSyntaxAndHttpVerified':True,'browserRuntimeVerified':False,'oneToOneComplete':False,'remaining':review['remaining']}
(O/'release-v21.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
integration=json.loads((O/'integration-v21.json').read_text());integration['visualReviewPending']=False;integration['visualReview']='visual-review-v21.json';(O/'integration-v21.json').write_text(json.dumps(integration,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v21_movie_window_comparison_candidate'
status['scene']['movieCalibrationCandidate']=release['nativeFile'];status['scene']['movieCalibrationCandidateRevision']=21;status['scene']['movieCalibrationBrowserCandidate']='http://127.0.0.1:8931/viewer/candidate-v21.html';status['scene']['movieWindowGeometryVerified']=True;status['next']=review['remaining'];(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-windows-v21"><h2>电影右侧窗型重建 · v21（候选）</h2>
<p>右侧圆窗、方窗、檐口和管道按电影参照重建。两个窗洞穿透实体墙，窗沿、窗棂和后方房间均为可编辑几何。独立混元头模、脚部间隙和穿门分隔已校验保留。</p>
<p><a href="movie-windows-v21/Suzume_scene_movie_windows_v21.blend">完整 Blender 对照场景</a> · <a href="viewer/candidate-v21.html">可旋转网页候选版</a>（运行效果待复测） · <a href="movie-windows-v21/movie-window-oblique-v21.png">斜视窗洞近景</a></p>
<figure class="scene"><img src="movie-windows-v21/movie-front-v21.png" alt="重建圆窗和方窗后的完整电影对照场景"><figcaption>窗型和檐口位置已重建；墙面颜色、光照与整体尺度仍需校准，尚未达到一比一。</figcaption></figure>
<p><a href="viewer/candidate-v20.html">上一版立面对照</a> · <a href="movie-windows-v21/verification-v21.json">洞口、模型与人物校验</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-windows-v21">' in gallery:gallery=re.sub(r'<section id="movie-windows-v21">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''电影右侧窗型重建 v21

Suzume_scene_movie_windows_v21.blend 是包含昼景、门、人物和异世界的完整 Blender 对照场景。
新立面在集合 Movie right facade — solid openings v21 中，共 72 个可编辑部件。
墙体有真实圆形和矩形洞口；窗沿、放射窗棂、方窗格栅、檐口、屋顶、后方房间及管道均为几何。
第 72 帧为开门。人物身体、混元独立头模、脚部间隙和互补裁切经重新打开文件校验。

movie-front-v21.png：完整开门场景。
movie-window-oblique-v21.png：斜视近景，检查窗沿厚度与房间。
网页候选：http://127.0.0.1:8931/viewer/candidate-v21.html
网页已通过脚本语法及 HTTP 检查，运行和交互仍待复测。

这不是一比一验收完成版。新墙面偏绿，阴影与电影参照不同，其他立面与钢架仍需重建。
建筑尺寸沿用 v20 的推定值，不能据此当作官方建筑尺寸。
window-fit-v21.json 的误差只针对手工选取的窗边标记，不代表整幅相似度。
''',encoding='utf-8')
print(json.dumps(release,ensure_ascii=False,indent=2))
