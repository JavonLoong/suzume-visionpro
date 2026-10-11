from pathlib import Path
import json,shutil,hashlib,zipfile,subprocess
R=Path(__file__).parent;H=R/'head-hunyuan-v1';W=R/'viewer'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
verification=read(H/'verification-v17.json');native=read(H/'native-integration-v17.json')
assert verification['freshReopenVerified'] and native['nativeRenderVerified']
assert native['oldHeadObjectsRemoved'] and native['pairedParts']==4
assert abs(native['minimumWorldHeight']-.2034619255)<1e-5
asset=read(W/'suzume-posed-v17.gltf')
triangles=sum(asset['accessors'][p['indices']]['count']//3 for m in asset['meshes'] for p in m['primitives'])
assert triangles==751541,triangles
assert any('COLOR_0' in p['attributes'] for m in asset['meshes'] for p in m['primitives'])
assert (R/'native-pose-front-v17.png').is_file() and (R/'native-pose-back-v17.png').is_file()
expanded=R/'Suzume_scene_Hunyuan_v17_expanded.blend'
if not expanded.exists():shutil.copy2(R/'Suzume_scene_Hunyuan_v17.blend',expanded)
shutil.copy2(R/'Suzume_scene_Hunyuan_v17_instances.blend',R/'Suzume_scene_Hunyuan_v17.blend')
shutil.copy2(R/'Suzume_scene_Hunyuan_v17.blend',V/'suzume-full-scene-hunyuan-v17.blend')
shutil.copy2(R/'Suzume_scene_Hunyuan_v17.blend',V/'suzume-full-scene.blend')
if not (W/'index-through-v16.html').exists():shutil.copy2(W/'index.html',W/'index-through-v16.html')
shutil.copy2(W/'candidate-v17.html',W/'index.html')

result=read(H/'public-generation-result-2.json');original=Path(result[0]['value'])
attempt=read(H/'public-generation-attempt-2.json');attempt['files']=[str(original)];write(H/'public-generation-attempt-2.json',attempt)
head=read(H/'status.json')
head.update({'stage':'independent_head_generated_and_integrated_v17','headModelSubmitted':True,
             'headModelGenerated':True,'headModelIntegrated':True,'hunyuanSubmissionsThisStage':2,
             'commercialWebsite31SubmissionsThisStage':0,'publicOfficial2mvSubmissions':2,
             'successfulHeadGenerations':1,'provider':'Tencent official Hunyuan3D-2mv Turbo public Space',
             'providerUrl':'https://huggingface.co/spaces/tencent/Hunyuan3D-2mv',
             'sourceMesh':'Suzume-head-Hunyuan2mv-original.glb','sourceMeshSha256':hashlib.sha256(original.read_bytes()).hexdigest(),
             'displayHead':'Suzume-head-candidate.glb','headEditableFile':'new-head-colored-candidate.blend',
             'characterEditableFile':'../Suzume_character_head_v17.blend','fullScene':'../Suzume_scene_Hunyuan_v17.blend',
             'cloudTextureAttempt':'First generation_all call failed with PyMeshLabException; the shape-only call completed and returned a real GLB.',
             'colorMethod':'Local four-view projected vertex colors and separately modeled left-only hairpins.',
             'browserBlocker':'The original site and browser-control connection remain unavailable. Generation was completed through Tencent official public Gradio API. Current web runtime has not been rechecked.',
             'attachmentGuide':'attachment-guide-v16.json','attachmentFile':'head-socket-v16.blend',
             'attachmentNote':'These are OLD-head preparation files. The integrated new head is in the v17 character and full scene.',
             'nativeVerification':'verification-v17.json','oneToOneComplete':False})
write(H/'status.json',head)
integration=read(H/'integration-v17.json')
for row in verification['newParts']:integration['partTriangles'][row['name']]=row['triangles']
integration['limitations']=['Head identity, hair geometry and color registration remain approximate.','Browser runtime could not be rechecked; native front/back renders and static browser assets passed.']
write(H/'integration-v17.json',integration)
status=read(R/'status.json');status.update({'revision':5,'date':'2026-10-10','status':'independent_head_integrated_v17_foot_fix_preserved'})
status['scene'].update({'currentNative':'Suzume_scene_Hunyuan_v17.blend','browserAsset':'viewer/suzume-posed-v17.gltf',
    'revision':17,'browserTriangles':triangles,'inlinePrototype':'Archived procedural v13 only. Current actual reconstructed character is the local v17 viewer.',
    'nativeAndBrowserPartitionVerified':False,'nativePartitionVerifiedV17':True,
    'browserValidation':'Syntax, local HTTP and GLTF assets checked. v17 browser runtime could not be exercised because browser control is unresponsive; v16 runtime verification remains on record.',
    'headReconstruction':'Independent four-view Hunyuan 2mv head generated, locally colored and installed in both worlds. 20-bone rig and v16 shoe clearance preserved.'})
status['next']=['Refine the independent head identity, hair and texture registration against film references','Recheck the v17 web viewer when browser control recovers','Refine sleeves, fingers and architectural reference alignment']
write(R/'status.json',status)
audit=read(V/'fidelity-audit.json')
audit.update({'current_stage':'independent_hunyuan_head_integrated_v17','goal_status':'active','one_to_one_complete':False,
              'latestNative':str(R/'Suzume_scene_Hunyuan_v17.blend'),'headReconstructionAudit':str(H/'status.json'),
              'latestProgress':'Official public multi-view API yielded a new head; local colors and physical hairpins applied; fitted to v16 rig, full native scene rendered from front/back, foot clearance unchanged.',
              'browserRuntimeV17Verified':False})
write(V/'fidelity-audit.json',audit)

(H/'使用说明.txt').write_text('独立头部重建：已生成并接入 v17\n\nfront / left / back / right.png 是根据电影参照生成的四视图，不是官方正交设定图。\n内置浏览器与 Chrome 控制连接未恢复，改用腾讯官方 Hunyuan3D-2mv 公开 API。带贴图接口报 PyMeshLabException；单独几何体接口成功，实际 GLB 已保留。\nSuzume-head-Hunyuan2mv-original.glb：云端原始几何体。\nSuzume-head-candidate.glb：清理、着色并增加实体发卡的独立头模。\nnew-head-colored-candidate.blend：独立头模可编辑源文件。\n../Suzume_character_head_v17.blend：接回 20 骨骼人物的版本。\n../Suzume_scene_Hunyuan_v17.blend：已保留脚部修复与庭院/异世界裁分的完整场景。\n\nhead-socket-preparation.blend 与 head-socket-v16.blend 只包含旧头的接合准备，不是新头模。\n脸型、发丝和多视图颜色映射仍有近似，尚未一比一。\n',encoding='utf-8')
(R/'使用说明.txt').write_text('铃芽之旅：混元人物与完整场景 v17\n\n本地预览：http://127.0.0.1:8931/viewer/\n若服务关闭，在本目录运行 python open_scene.py。拖动旋转，滚轮缩放，右键或 Shift 拖动平移。\n\nSuzume_scene_Hunyuan_v17.blend 是完整可编辑场景，第 1 帧关门，第 72 帧开门。Suzume_character_head_v17.blend 是人物与 20 骨骼。网页人物为静态姿态网格。\n身体保留此前混元 3D 3.1 模型、v16 的比例与脚部修复。新头部用专门四视图通过腾讯官方 Hunyuan3D-2mv 公开 API 生成，再清理、投射颜色、建立实体发卡并接合。\n未跨过门洞的表面留在庭院，跨过的表面只在异世界显示。新头与发卡使用同样的空间裁分和共享骨骼。\n完整场景已重新打开，并完成正面、背面原生渲染；鞋底最低高度仍为 0.2034619。草木保留原来数量、位置与颜色，改用共享实例降低内存。\n网页语法、HTTP 和模型文件检查通过；浏览器控制连接仍故障，v17 的网页交互还未复测。\n\n构建顺序：prepare_attachment_v16.py -> generate_public_head.py（已有生成记录，禁止无故重提）-> 网格清理与 paint_head.py -> integrate_head_v17.py -> integrate_native_head_v17.py -> render_native_v17_instances.py -> verify_head_v17.py -> build_viewer.py --candidate -> finalize_head_v17.py。\n尚未达到一比一：头部身份细节、发丝、贴图接缝、袖口和手指、建筑与夜景仍待精修。\n',encoding='utf-8')

gallery='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>铃芽 · 独立头部重建 v17</title><style>body{max-width:1200px;margin:auto;padding:28px;background:#172221;color:#f0eee8;font:16px/1.6 system-ui,sans-serif}h1,h2{font-weight:500}h1{font-size:26px}h2{font-size:20px;margin-top:32px}p{color:#b6c4bd}.views{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}figure{margin:0;background:#263330;border-radius:10px;overflow:hidden}img{width:100%;display:block}figcaption{text-align:center;padding:10px}a{color:#cfe1a0}.scene{max-width:820px}@media(max-width:700px){.views{grid-template-columns:repeat(2,minmax(0,1fr))}}</style><h1>铃芽 · 独立头部重建 v17</h1><p>头部已用专门四视图重新生成并接回人物。脚部间隙、可编辑骨骼与穿门空间分隔已保留。脸型、发丝和贴图细节仍在精修，尚未一比一。</p><p><a href="viewer/">打开可旋转场景</a> · <a href="Suzume_scene_Hunyuan_v17.blend">完整 Blender 场景</a> · <a href="Suzume_character_head_v17.blend">带骨骼人物</a> · <a href="head-hunyuan-v1/Suzume-head-candidate.glb">独立头模 GLB</a></p><div class="views">'''
for view,label in [('front','正面'),('left','左侧'),('back','背面'),('right','右侧')]:
    gallery+=f'<figure><img src="head-hunyuan-v1/new-head-color-{view}.png" alt="新头模{label}"><figcaption>新头模 · {label}</figcaption></figure>'
gallery+='</div><h2>完整场景原生渲染</h2><figure class="scene"><img src="native-pose-front-v17.png" alt="新头部已进入门后的异世界"><figcaption>新头部已接入，身体按门洞平面分隔</figcaption></figure><p><a href="native-pose-back-v17.png">查看庭院背面验证</a> · <a href="head-hunyuan-v1/status.json">头部生成与验收记录</a></p><h2>新头部的四视图输入</h2><div class="views">'
for view,label in [('front','正面'),('left','左侧'),('back','背面'),('right','右侧')]:
    gallery+=f'<figure><img src="head-hunyuan-v1/{view}.png" alt="头部{label}输入"><figcaption>{label}输入</figcaption></figure>'
gallery+='</div><p>输入图依据影片参照生成，不是官方正交设定图。身体来自混元 3D 3.1，新头部来自腾讯官方混元 2mv；头部颜色在本地映射，发卡是独立几何。<a href="head-hunyuan-v1/Suzume-head-multiview-inputs.zip">四视图和提示词</a> · <a href="head-hunyuan-v1/new-head-colored-candidate.blend">独立头模源文件</a> · <a href="Suzume_Hunyuan31_original.glb">原身体 GLB</a></p></html>'
(R/'index.html').write_text(gallery,encoding='utf-8')
with zipfile.ZipFile(H/'Suzume-head-multiview-inputs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['front.png','left.png','back.png','right.png','prompts.json','status.json','attachment-guide-v16.json','使用说明.txt']:
        archive.write(H/name,name)
write(H/'release-v17.json',{'revision':17,'native':str(R/'Suzume_scene_Hunyuan_v17.blend'),'nativeBytes':(R/'Suzume_scene_Hunyuan_v17.blend').stat().st_size,
                           'browserTriangles':triangles,'headIntegrated':True,'footClearancePreserved':True,'frontAndBackNativeRendered':True,
                           'browserStaticChecksPassed':True,'browserRuntimeVerified':False,'oneToOneComplete':False})
print('V17_RELEASED',triangles,(R/'Suzume_scene_Hunyuan_v17.blend').stat().st_size,flush=True)
