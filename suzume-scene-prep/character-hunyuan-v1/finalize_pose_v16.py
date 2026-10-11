from pathlib import Path
import json,shutil
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
a=json.loads((R/'pose-calibration-v16.json').read_text())
verify=json.loads((R/'verification-front-v16.json').read_text())
browser=json.loads((R/'browser-evidence-v16.json').read_text())
assert verify['partition']['courtyard']==a['partition']['courtyard']
assert browser['figure']['revision']==16 and browser['contextLost']==False
assert all(v['minimumClearance']>.006 for v in a['footCollision'].values())
source=V/'suzume-full-scene-hunyuan-v16.blend'
for target in [R/'Suzume_scene_Hunyuan_v16.blend',V/'suzume-full-scene.blend']:shutil.copy2(source,target)
a['visualReview']='Studio front/back/side and complete browser front/side/rear inspected. Final native front reopened/rendered after foot collision correction. Feet clear foundation and portal threshold; body partition retained.'
a['limitations']+=['Foot screen positions remain offset because solid threshold clearance takes precedence; door and foundation/reference alignment still require calibration','User requested independent head reconstruction; in progress, current head remains Hunyuan whole-body generation']
(R/'pose-calibration-v16.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
s=json.loads((R/'status.json').read_text(encoding='utf-8'));s['revision']=4;s['status']='foot_collision_fixed_head_reconstruction_in_progress'
s['scene'].update({'currentNative':'Suzume_scene_Hunyuan_v16.blend','revision':16,'browserAsset':'viewer/suzume-posed-v16.gltf','inlinePrototype':'Archived procedural v13 only. Current actual Hunyuan model is the local v16 viewer.','poseAudit':'pose-calibration-v16.json','footClearanceVerified':True,'headReconstruction':'Independent head multi-view preparation in progress','oneToOneComplete':False})
s['next']=['Reconstruct the head independently from film-aligned four views and attach to the existing rig','Refine sleeve and individual finger deformation','Calibrate doorway/foundation and hotel silhouette against both film references']
(R/'status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'index.html';html=p.read_text(encoding='utf-8').replace('Suzume_scene_Hunyuan_v15.blend','Suzume_scene_Hunyuan_v16.blend').replace('v15 已按门洞平面划分庭院与异世界中的身体部分。','v16 已校准人物比例与步态，修复鞋底与石台、门槛穿模，并保留穿门空间分隔。头部正在独立重建。');p.write_text(html,encoding='utf-8')
p=R/'使用说明.txt';t=p.read_text(encoding='utf-8').replace('v15','v16')
t=t[:t.index('构建顺序：')]+'当前构建：以 v15 场景为基准，measure_pose_v16.py / measure_surface_uv.py 提取量测，fit_pose_v16.py 拟合骨骼、比例与脚部碰撞，export_pose_v16.py 输出浏览器网格，build_viewer.py 构建网页。\n\n脚部修复：对两只鞋的 28114 个鞋与踝部顶点核验三层石台与门洞下缘净空。原片机位的脚点仍有误差，未把二维对齐作为允许穿模的理由。\n头部独立重建进行中；当前 v16 仍使用此前整个人物生成的头部。\n'
p.write_text(t,encoding='utf-8')
f=json.loads((V/'fidelity-audit.json').read_text(encoding='utf-8'))
f.update({'current_stage':'pose-and-foot-collision-v16-head-reconstruction-started','native_model_copy':str(R/'Suzume_scene_Hunyuan_v16.blend'),'model_revision':'v16: film-space pose and proportions, back-cloth skinning repair, explicit shoe/foundation/threshold clearance. Independent head reconstruction requested and started.','pose_calibration_audit':str(R/'pose-calibration-v16.json'),'goal_status':'active','last_turn_classification':'substantial_progress','one_to_one_complete':False})
entry='v16: adjusted film landmarks and lower-body proportions; repaired 385 back-cloth vertices incorrectly attached to hair; enforced nonpenetrating shoe/threshold placement while retaining complementary portal materials.'
if entry not in f['implemented_changes']:f['implemented_changes'].append(entry)
(V/'fidelity-audit.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8')
print('V16_DELIVERY_SAVED',source.stat().st_size)
