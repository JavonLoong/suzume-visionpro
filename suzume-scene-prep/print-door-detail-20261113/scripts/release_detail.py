"""Publish only verified STL geometry; keep printing notes outside ZIP archives."""
import json,hashlib,zipfile
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];A=R/'analysis';D=R/'交付';D.mkdir(exist_ok=True)
data=json.loads((A/'door_manifest.json').read_text(encoding='utf8'))
packed=json.loads((A/'packed_manifest.json').read_text(encoding='utf8'))
results=json.loads((A/'slicing_checks.json').read_text(encoding='utf8'));byid={c['id']:c for c in results}
intersections=json.loads((A/'self_intersection_check.json').read_text(encoding='utf8'))
assert len(intersections)==9 and all(x['selected_faces']==0 for x in intersections)
assert len(data['door_variants'])==3 and len(data['parts'])==9
motion=[c for c in data['checks'] if '开门' in c['check']]
assert len(motion)==318 and max(c['interference_mm3'] for c in motion)<.003
archives=[]
for group,name in [('单档','白门'),('同盘','三档')]:
    rows=[p for p in packed if p['group']==group];out=D/(name+'.zip');assert not out.exists(),out
    for row in rows:
        p=Path(row['stl_path']);c=byid[row['id']]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']==c['stl_sha256']
        assert c['exit_code']==0 and c['outside']=='false' and c['md5_valid'] and c['layer_height_mm']==.12
        mesh=trimesh.load(p,force='mesh')
        assert mesh.is_volume and mesh.is_winding_consistent and len(mesh.split())==row['components'] and np.all(mesh.area_faces>1e-12)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for row in rows:z.write(row['stl_path'],Path(row['stl_path']).name)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None and all(n.endswith('.stl') and '/' not in n for n in z.namelist())
        for row in rows:assert hashlib.sha256(z.read(Path(row['stl_path']).name)).hexdigest()==row['sha256']
    archives.append({'name':name,'archive':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'stl_count':len(rows),'parts':sum(r['components'] for r in rows)})
    print('RELEASE',json.dumps(archives[-1],ensure_ascii=False),flush=True)
basezip=Path('D:/虚拟C盘/底座.zip');basehash=hashlib.sha256(basezip.read_bytes()).hexdigest()
assert basehash=='e98dcc5b71dae350caa7175b47d577df9ee09761bc2520b56ed05155c56a6114'
report={'status':'软件原门细节版，静态试配','archives':archives,'base_unchanged':{'path':str(basezip),'sha256':basehash},'native_slicing':results,'self_intersections':intersections,'motion_checks':len(motion),'physical_fit_test':False,'servo_drive_finished':False}
(A/'release_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
lines=[]
for v in data['door_variants']:
    result=byid[f"白门_{v['factor']:g}倍"]
    lines.append(f"{v['factor']:g} 倍：门框含台阶高 {v['outer_height_mm']} mm；门框外宽 {v['outer_frame_width_mm']:.2f} mm。含对应插座板，约 {round(result['seconds']/60)} 分钟、{result['grams']:.2f} 克。插座板有 {v['cassette_dots']} 个凹点。")
all_result=byid['三档同盘']
note='''软件原门细节版 · 2026-11-13

依据当前 Unity 程序实际加载的 DoorFrame.fbx 和 DoorLeaf.fbx 重制。
保留原门的六格比例、凸起门板、细边线、层叠门楣、长锁板、圆把手和正面小合页。
软件贴面背后补为实体；1.6 mm 门板芯、细把手背部加强；2 mm 金属轴用的功能合页藏在背面。
把手与锁板保留源造型，向门内平移 1.5 mm，避免原软件中的穿模导致门框出现难看的缺口。
原贴面磨损在裸露门板区域转为浅刻纹。STL 不携带白漆、锈色、贴图，彩图外观需要后续涂装。
门框内侧按门扇运动路径让位，避免虚拟模型中原本存在的重叠。

'''+ '\n'.join(lines)+f'''

两种包二选一，避免重复打印：
1. D:/虚拟C盘/白门.zip：只有三种尺寸各自的 STL；选一个文件即含该尺寸门框、门扇和插座板各一件。
2. D:/虚拟C盘/三档.zip：只有 三档同盘.stl；一次打印三档共九件，约 {round(all_result['seconds']/60)} 分钟、{all_result['grams']:.2f} 克。
同盘文件从左到右依次 50、60、70 mm；每列前方插座板，中间门框，后方平放门扇。

通用插座外形 64×44 mm、下方缺角定位舌和 M2 孔位保持不变，沿用现有 50 cm 底座。
底座、庭院插槽、脚垫、接缝条不用因为换门重新制作。
每档门框与对应插座板成套安装；不同尺寸的门轴位置不同。
门框台阶嵌入插座板 1.2 mm，不能在切片软件里继续整体缩放。
轴孔 2.4 mm，适配另备的 2 mm 金属杆；孔贯通插座板。
装配顺序：去除支撑和边裙、清理轴孔、门框放入对应浅槽、对齐背部合页、穿入金属杆。
插座板再嵌入底座，沿用 M2 螺钉。实物孔径和插槽松紧仍需试打确认。

本机验证设置：X1 Carbon / 0.4 mm 喷嘴 / PLA / 纹理 PEI / 0.12 mm 层高。
三圈墙、15% gyroid 填充、普通自动支撑、支撑上下间距 0.12 mm、3 mm 边裙。
STL 按毫米、100% 导入，保留文件中的排布；STL 不保存机器参数，需要按以上设置重新切片。
精细门板朝上平放；门框竖放并启用支撑。拆支撑时保护把手和细边线。
切片器仍记录 PLA 与 55℃ 热床的 bed_temperature_too_high_than_filament 提示，未出现范围越界。
时间与材料均为切片器估计，未进行实际打印。

检查：九个零件重读后均为单一封闭实体，面方向一致，无零面积三角形、无自交。
每 1° 检查一次，0～105° 范围未发现门扇与门框、插座、底板及已有庭院部件相撞。
四种排盘均完成本机切片，G-code 校验码通过。对应切片工程仅保留在 analysis/slice_projects 供核查，不混入 STL 包。
这仍是静态开合样机，舵机支架、驱动联轴器、电动开门尚未完成。

细节预览：{R/'白门细节近景.png'}
同尺度三档：{R/'三档尺寸对比.png'}
Blender 工程：{R/'三档白门.blend'}
'''
(R/'打印说明.txt').write_text(note,encoding='utf-8-sig')
print('DETAILED_RELEASE_PASS',flush=True)
