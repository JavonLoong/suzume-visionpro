import json,zipfile,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'交付文件';C=R/'analysis/slice_checks'
d=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
reports=[]
names={'sample':'白门与连接件试装盘','B02':'B02 底盘','W02':'W02 建筑','W03':'W03 建筑','S05':'S05 最高钢架'}
for key,label in names.items():
 r=json.loads((C/(key+'_result.json')).read_text(encoding='utf8'));assert r['exit_code']==0 and r['gcode_files']
 plate=ET.parse(C/(key+'_slice_info.xml')).getroot().find('plate')
 stats={n.get('key'):n.get('value') for n in plate.findall('metadata')}
 assert stats['outside']=='false'
 r.update(label=label,estimated_seconds=int(stats['prediction']),estimated_grams=float(stats['weight']),outside_print_volume=False,warnings=[n.attrib for n in plate.findall('warning')])
 reports.append(r)
lines=['切片检查摘要','检查日期：2026-10-30','软件：本机 Bambu Studio 02.01.01.52，X1 Carbon 0.4 mm 喷嘴，PLA，纹理 PEI 板。',
 '工程中记录的是暂定参数；打印前换成你们实际的线材和板材。','',
 '32 类 STL 已逐件检查：尺寸单位为毫米、封闭性通过、面朝向一致、体积为正、落在打印底面。',
 '4 块底盘均为约 199.9×199.9 mm；最大钢架高约 115.5 mm。',
 '白门 0、15、30、45、60、75、90 度开合采样均无几何重叠。','',
 '以下 5 个打印盘实际完成离线切片，程序返回码均为 0，均产生 G-code，均未超出打印范围：']
for r in reports:
 t=r['estimated_seconds'];lines.append(f"{r['label']}：约 {t//3600}小时{t%3600//60}分钟，{r['estimated_grams']:.2f}克 PLA（含当前支撑和初始化耗材估算）。")
lines += ['',
 '切片中的提示：',
 '5 盘均有 bed_temperature_too_high_than_filament 提示。当前继承的 PLA/纹理板预设存在热床温度高于该耗材软化阈值的提醒；打印前使用实际耗材预设，并按拓竹提示保持散热。',
 '树状支撑步骤的日志还出现 Not precalculated Placeable areas requested, critical: 0；切片仍正常结束并输出刀路。支撑能否好拆仍要靠实物小样确认。',
 '',
 '检查范围：已抽查试装盘、1块最大底盘、2块复杂建筑、1块最高钢架；其余零件未逐一切片。',
 '未进行实物打印，未连接打印机。真实孔位松紧、细杆强度、装配平整度与支撑拆除效果仍待试装。',
 '交付的是可重新切片的 3MF 工程与 STL，不附自动开印用 G-code；切片证据留在本任务 analysis/slice_checks 目录。']
(O/'切片检查摘要.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
(O/'切片检查记录.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
# Remove only the superseded Blender backup from the delivery, retaining it locally.
for src in O.glob('*.blend1'):
 dst=R/'analysis/withdrawn'/src.name;dst.parent.mkdir(exist_ok=True,parents=True)
 assert src.resolve().is_relative_to(R.resolve()) and dst.resolve().is_relative_to(R.resolve())
 shutil.move(src,dst)
archive=Path('D:/虚拟C盘/铃芽庭院_400mm_X1C_分件首版.zip')
if archive.exists():
 archive=Path('D:/虚拟C盘/铃芽庭院_400mm_X1C_分件首版_20261030.zip')
assert not archive.exists(),str(archive)
files=[p for p in O.rglob('*') if p.is_file()]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in files:z.write(p,Path('铃芽庭院_400mm_X1C')/p.relative_to(O))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None and len(z.namelist())==len(files)
result={'archive':str(archive),'size_mb':round(archive.stat().st_size/1024**2,2),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'file_count':len(files),'part_types':len(d['parts']),'slice_checks':len(reports)}
(R/'analysis/delivery-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False),flush=True)
