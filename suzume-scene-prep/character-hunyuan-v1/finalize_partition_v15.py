from pathlib import Path
import json,shutil
R=Path(__file__).parent;V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=V/'suzume-full-scene-hunyuan-v15.blend'
for path in [R/'Suzume_scene_Hunyuan_v15.blend',V/'suzume-full-scene.blend']:shutil.copy2(source,path)
a=json.loads((R/'portal-partition-native-v15.json').read_text(encoding='utf-8'))
a['visualReview']='Native and browser front views retain the entered figure through the aperture; rear courtyard views remove the entered body and its courtyard reflection. Browser independent night view retains the entered body.'
a['renderChecks']=[json.loads((R/f'partition-check-{label}-v15.json').read_text(encoding='utf-8')) for label in ['front','back']]
a['goalOneToOneComplete']=False
(R/'portal-partition-native-v15.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
s=json.loads((R/'status.json').read_text(encoding='utf-8'));s['revision']=3;s['status']='portal_partition_verified'
s['scene'].update({'currentNative':'Suzume_scene_Hunyuan_v15.blend','revision':15,'spacePartition':'Complementary world-space half-planes at Three Z=-0.072 / Blender Y=0.072. Entered body belongs only to the night world.','nativeAndBrowserPartitionVerified':True,'nightViewIncludesEnteredCharacter':True,'oneToOneComplete':False})
(R/'status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'index.html';html=p.read_text(encoding='utf-8').replace('Suzume_scene_Hunyuan_v14.blend','Suzume_scene_Hunyuan_v15.blend')
html=html.replace('完成真实模型下载、贴图修复、骨骼绑定与场景接入。','完成真实模型下载、贴图修复、骨骼绑定与场景接入。v15 已按门洞平面划分庭院与异世界中的身体部分。')
p.write_text(html,encoding='utf-8')
p=R/'使用说明.txt';t=p.read_text(encoding='utf-8').replace('v14','v15').replace('Suzume_scene_Hunyuan_v14.blend','Suzume_scene_Hunyuan_v15.blend')
t+='\n穿门分隔：未跨过门洞平面的身体留在庭院；已跨过的表面只在异世界显示。绕到庭院背面不会看见已进入的身体，庭院阴影与倒影也使用同一裁分。\n网页会记住本地视角；骨骼源模型保留完整网格，场景材质负责分隔。\n构建顺序：rig_character.py -> integrate_scene.py --no-render -> export_posed_character.py -> partition_native_v15.py -> build_viewer.py。\n'
p.write_text(t,encoding='utf-8')
f=json.loads((V/'fidelity-audit.json').read_text(encoding='utf-8'))
f.update({'current_stage':'portal-character-partition-v15','native_model_copy':str(R/'Suzume_scene_Hunyuan_v15.blend'),'model_revision':'v15: Hunyuan character split into complementary courtyard and otherworld surface regions at the doorway; browser and native reflections and rear-view visibility verified. Character likeness and scene appearance still approximate.','portal_partition_audit':str(R/'portal-partition-native-v15.json'),'goal_status':'active','last_turn_classification':'substantial_progress','one_to_one_complete':False})
f['implemented_changes'].append('v15: entered character surface removed from courtyard and retained in otherworld; complementary world-space planes, material isolation and shadow/reflection partition; current orbit state preserved.')
(V/'fidelity-audit.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8')
print('V15_DELIVERY_UPDATED',source.stat().st_size)
