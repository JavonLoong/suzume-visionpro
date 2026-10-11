from pathlib import Path
import json,re,hashlib
R=Path(__file__).parent;O=R/'movie-door-v32';read=lambda n:json.loads((O/n).read_text(encoding='utf-8'))
v=read('verification-v32.json');b=read('browser-verification-v32.json');asset=read('character-asset-verification-v32.json');native=O/'Suzume_scene_movie_door_v32.blend'
assert v['reopened'] and v['dimensionsInvariantAtFiveAngles'] and v['dayNightDoorMatricesMatch'] and b['nativeBrowserKnobMatches']
assert asset['maximumExportToNativeDistance']==0 and asset['maximumNativeToExportDistance']==0
for n in ['movie-front-v32.png','door-hand-inspection-v32.png']:assert (O/n).stat().st_mtime>native.stat().st_mtime
remaining=['Refine character identity, hair silhouette and individual finger contact; current Hunyuan head is approximate.','Fit the close movie camera again using reviewed panel correspondences; the previous v32 camera trials are not accepted.','Restore wider off-axis sunset colors and the visible star arrangement while preserving the narrow front sky.','Refine cloud outlines, meadow flowers, haze, paving and water glints.','Finish the separate closed-door poster scene and inspect the full model from additional angles.','Verify the web candidate in an actual connected browser; the control session still times out.']
review={'revision':32,'frontReviewed':True,'contactStudioReviewed':True,'observations':['Open-door front rendering retains the character and portal composition.','Neutral contact view shows the right hand around the handle and a continuous bent elbow.','Hair shape, facial likeness and individual finger separation remain approximate.'],'studioImageScope':'Unclipped character and real door geometry under neutral inspection lighting; not a final otherworld rendering.','remaining':remaining,'oneToOneComplete':False}
(O/'visual-review-v32.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
result={'revision':32,'nativeFile':'movie-door-v32/Suzume_scene_movie_door_v32.blend','nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'rigidDoorVerified':True,'grippingArmRetargeted':True,'feetMinimumClearanceMeters':{k:x['minimumClearance'] for k,x in v['feet'].items()},'independentHeadPreserved':True,'portalGeometryAndMaterialPartitionVerified':True,'browserCandidate':'viewer/candidate-v32.html','browserRuntimeVerified':False,'browserFailure':'cua.getTab(3,browser=2) timed out after 20 seconds; kernel reset.','frontAndContactRendersReviewed':True,'stableNativeRemainsRevision':19,'browserDefaultRemainsRevision':17,'oneToOneComplete':False,'remaining':remaining}
(O/'release-v32.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
status=json.loads((R/'status.json').read_text(encoding='utf-8'));status['status']='native_v32_rigid_door_and_right_grip_candidate';status['scene'].update({'movieCalibrationCandidate':result['nativeFile'],'movieCalibrationCandidateRevision':32,'movieCalibrationBrowserCandidate':'http://127.0.0.1:8931/viewer/candidate-v32.html','movieRigidDoorVerified':True,'movieGripRetargeted':True});status['next']=remaining;(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
section='''<section id="movie-door-v32"><h2>固定门板尺寸与握门姿态 · v32（候选）</h2>
<p>修正了门框横向缩放导致门板打开时变宽的问题，并重新定位右臂和握门手。脚部、独立混元头模和门两侧的空间分区保留。</p>
<p><a href="movie-door-v32/Suzume_scene_movie_door_v32.blend">完整 Blender 场景</a> · <a href="viewer/candidate-v32.html">可旋转网页候选</a>（显示待复测） · <a href="viewer/character-v32/suzume-posed-v32.glb">当前人物 GLB</a></p>
<figure class="scene"><img src="movie-door-v32/movie-front-v32.png" alt="门板尺寸与握门姿态修正后的完整场景"><figcaption>门板开合时宽约 1.409 米、厚 9.5 厘米；脚部与门槛保留约 9 毫米间隙。人物造型、夜空及关门场景仍未达到一比一。</figcaption></figure>
<details><summary>查看握门手的独立检查图</summary><img style="max-width:100%" src="movie-door-v32/door-hand-inspection-v32.png" alt="中性灯光下的右臂与门把手贴合检查"><p>这是完整人物和实体门板的中性灯光检查图，不是异世界最终画面。</p></details>
<p><a href="movie-door-v32/verification-v32.json">重新打开后的原生检查</a> · <a href="movie-door-v32/character-asset-verification-v32.json">导出模型与原生几何对比</a></p></section>'''
gallery=(R/'index.html').read_text(encoding='utf-8')
if '<section id="movie-door-v32">' in gallery:gallery=re.sub(r'<section id="movie-door-v32">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('</h1>','</h1>'+section,1)
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''门板刚性旋转与右手修正 v32

完整三维文件：Suzume_scene_movie_door_v32.blend，第 72 帧为开门姿态。
关闭到打开的五个采样角度下，门板宽约 1.409 米、厚 9.5 厘米；不再随旋转伸缩。关闭时 14 个门板网格的最大顶点变化约 0.00000012 米。
右臂按实际门把手位置重新求解，握门手保留原姿态并随门把移动。人物是静态开门姿势，不是完整走路或抓握动画。
脚部与非右臂顶点完全保留；两脚与现有支撑碰撞体最小间隙约 9 毫米。头模为此前完成的独立混元 2mv 四视图重建，此轮未重复生成或消费额度。
门的两侧继续使用互补空间裁切，已跨过门面的身体仅属于异世界。

movie-front-v32.png：真实完整场景正面渲染。
door-hand-inspection-v32.png：完整人物与门的中性灯光检查，用于观察手部接触；不是最终异世界效果。
网页候选：http://127.0.0.1:8931/viewer/candidate-v32.html
网页的实际修正函数、模型顶点和资源已检查，但浏览器连接仍超时，GPU 显示与交互未复测。

人物脸部、发束、手指、宽视角夜空与关门海报仍未完成一比一。movie-sky-v32 下的近景机位拟合是未接受的试验，不作为成品机位。
默认网页 v17 与稳定原生 v19 保留。
''',encoding='utf-8')
print('DOOR_32_RELEASED',result['nativeSha256'],flush=True)
