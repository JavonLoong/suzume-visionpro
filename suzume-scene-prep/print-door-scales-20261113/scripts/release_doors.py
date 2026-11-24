import json,hashlib,zipfile
from pathlib import Path
import trimesh
R=Path(__file__).resolve().parents[1];A=R/'analysis';D=R/'交付';D.mkdir(exist_ok=True)
data=json.loads((A/'door_manifest.json').read_text(encoding='utf8'));packed=json.loads((A/'packed_manifest.json').read_text(encoding='utf8'));results=json.loads((A/'slicing_checks.json').read_text(encoding='utf8'));byid={c['id']:c for c in results}
archives=[]
for group,name in [('单档','白门'),('同盘','三档')]:
    rows=[p for p in packed if p['group']==group];out=D/(name+'.zip');assert not out.exists(),out
    for row in rows:
        p=Path(row['stl_path']);c=byid[row['id']];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']==c['stl_sha256']
        assert c['exit_code']==0 and c['outside']=='false' and c['md5_valid']
        mesh=trimesh.load(p,force='mesh');assert mesh.is_volume and mesh.is_winding_consistent and len(mesh.split())==row['components']
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for row in rows:z.write(row['stl_path'],Path(row['stl_path']).name)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None and all(n.endswith('.stl') and '/' not in n for n in z.namelist())
        for row in rows:assert hashlib.sha256(z.read(Path(row['stl_path']).name)).hexdigest()==row['sha256']
    archives.append({'name':name,'archive':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'stl_count':len(rows),'parts':sum(r['components'] for r in rows)})
    print('RELEASE',json.dumps(archives[-1],ensure_ascii=False),flush=True)
b=Path(data['base_project']);previous=json.loads((b/'analysis/release_checks.json').read_text(encoding='utf8'));basezip=Path('D:/虚拟C盘/底座.zip')
assert hashlib.sha256(basezip.read_bytes()).hexdigest()==previous['archives'][0]['sha256']
report={'status':'三档白门静态试配版','baseline_height_mm':40,'linear_factors':[1.25,1.5,1.75],'archives':archives,'base_unchanged':{'path':str(basezip),'sha256':previous['archives'][0]['sha256']},'native_slicing':results,'physical_fit_test':False,'servo_drive_finished':False}
(A/'release_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
lines=[]
for v in data['door_variants']:
    result=byid[f"白门_{v['factor']:g}倍"]
    lines.append(f"{v['factor']:g} 倍：门框含台阶高 {v['outer_height_mm']} mm；门框外宽 {v['outer_frame_width_mm']:.2f} mm；门洞 {v['opening_width_mm']:.2f} × {v['opening_height_mm']:.2f} mm。约 {round(result['seconds']/60)} 分钟，{result['grams']:.2f} 克。插座板 {v['cassette_dots']} 个凹点。")
all_result=byid['三档同盘']
note='''三档白门 · 2026-11-13

以当前 40 mm 高的门为 1 倍，分别制作 1.25、1.5、1.75 倍。
长、宽、厚度等比例放大；轴孔、装配间隙与公共底座接口按实际配合尺寸单独处理。
'''+ '\n'.join(lines)+f'''

两种打印方式，二选一，不必重复打印：
1. D:/虚拟C盘/白门.zip：只有 3 个 STL。按倍率选一个文件，里面是该尺寸的门框、门扇、插座板，各 1 件。
2. D:/虚拟C盘/三档.zip：只有 三档同盘.stl。一次打印三种尺寸，总共 9 件；约 {round(all_result['seconds']/60)} 分钟，{all_result['grams']:.2f} 克。
同盘文件从左往右为 1.25、1.5、1.75 倍。每列前面是插座板，中间是门框，后面是平放门扇。

所有插座板外部接口都是 64×44 mm，沿用相同缺角定位舌与 M2 螺钉孔。
可直接替换现有 50 cm 底座的插座板，底板、庭院凹槽、脚垫、接缝条不用重新打印。
每一档的门框和插座板需成套使用。门轴位置随门宽变化，不代表舵机可以无需调整就互换。
原来 40 mm 门在旧版工程保留，不再放进当前白门包。
三档台阶都嵌入插座板 1.2 mm，露出底板的高度分别是 48.8、58.8、68.8 mm。

门轴：2 mm 金属杆，孔统一 2.4 mm，贯通插座板底部。不要在切片软件里继续整体缩放。
已先填回原模型的细轴孔，再缩放外形、重开孔，避免 1.5/1.75 倍时轴孔跟着变松。
4 处铰链都检查了孔边有连续实体、金属杆不碰模型。
每隔 1° 检查一次，0～105° 范围未发现门扇与门框、插座板、底板及现有庭院部件的交叠。
全部 STL 是封闭实体，重读后法向一致，无零面积面；三种单档与三档同盘共 4 盘均已完成本机切片。

切片设置：X1 Carbon / 0.4 mm 喷嘴 / 白色 PLA / 纹理 PEI / 0.16 mm 层高。
3 圈墙、15% gyroid 填充、普通自动支撑、支撑上下间距 0.16 mm、3 mm 边裙。
STL 按毫米、100% 尺寸导入并保留排布；STL 不携带切片参数，需要按上面设置重新切片。
切片器仍有 PLA 与 55℃ 热床相关的 bed_temperature_too_high_than_filament 提示；未出现打印范围越界。
以上时间与材料是切片器估算。实物孔径、松紧、表面效果尚未试打，不保证无需修整就严丝合缝。
仍是静态开合样机；舵机支架、传动连接和电动开门未完成。

三档同尺度对比：{R/'三档尺寸对比.png'}
1.25 倍整体：{R/'1.25倍整体.png'}
1.5 倍整体：{R/'1.5倍整体.png'}
1.75 倍整体：{R/'1.75倍整体.png'}
Blender 工程：{R/'三档白门.blend'}（默认显示 1.5 倍；另外两档保存在 50毫米、70毫米集合内）
'''
(R/'三档门说明.txt').write_text(note,encoding='utf-8-sig')
print('THREE_DOORS_RELEASE_PASS',flush=True)
