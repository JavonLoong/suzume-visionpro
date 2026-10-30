import json,zipfile,hashlib,re,xml.etree.ElementTree as ET,csv,io
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
from fast_common import R,OLD
O=R/'交付文件';plates=json.loads((R/'analysis/plates.json').read_text(encoding='utf8'));results=json.loads((R/'analysis/final-slice-results.json').read_text(encoding='utf8'))
bycode={Path(r['input']).stem:r for r in results}
printer=json.loads(Path('C:/Program Files/Bambu Studio/resources/profiles/BBL/machine/Bambu Lab X1 Carbon.json').read_text(encoding='utf8'))
assert printer['model_id']=='BL-P001'
validation=[]
for p in plates:
 path=Path(bycode[p['code']]['output'])
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  data={n:z.read(n) for n in z.namelist()}
 gc=data['Metadata/plate_1.gcode'];md5=hashlib.md5(gc).hexdigest();assert data['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
 cfg=json.loads(data['Metadata/project_settings.config'])
 assert cfg['printer_settings_id']=='Bambu Lab X1 Carbon 0.4 nozzle'
 assert cfg['filament_type']==['PLA'] and cfg['nozzle_diameter']==['0.4']
 assert cfg['curr_bed_type']=='Textured PEI Plate' and float(cfg['layer_height'])==p['layer_height']
 assert cfg['nozzle_temperature']==['220'] and cfg['textured_plate_temp']==['55']
 root=ET.fromstring(data['Metadata/slice_info.config']);plate=root.find('plate')
 meta={x.get('key'):x for x in plate.findall('metadata')}
 assert meta['outside'].get('value')=='false'
 objects=plate.findall('object');assert len(objects)==len(p['items'])
 assert all(x.get('skipped')=='false' for x in objects)
 expected=Counter(it['id'] for it in p['items']);assert expected==Counter(x.get('name') for x in objects)
 g=gc.decode('utf8');ids={int(x) for x in re.findall(r'^; OBJECT_ID: (\d+)',g,re.M)}
 assert {int(x.get('identify_id')) for x in objects}<=ids,(p['code'],'missing object toolpath')
 body=g.split('; EXECUTABLE_BLOCK_START',1)[1].split('; EXECUTABLE_BLOCK_END',1)[0]
 assert not any(('{' in ln.split(';')[0] or '}' in ln.split(';')[0]) for ln in body.splitlines())
 assert 'G29' in body and 'M73 P100' in body
 # The CLI leaves this display/compatibility field blank. Fill it from the installed official model profile.
 # G-code bytes, machine start/end code, and its checksum are deliberately preserved.
 meta['printer_model_id'].set('value',printer['model_id'])
 data['Metadata/slice_info.config']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 tmp=R/'analysis'/(p['code']+'_pack.tmp')
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for n,b in data.items():z.writestr(n,b)
 tmp.replace(path)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None and hashlib.md5(z.read('Metadata/plate_1.gcode')).hexdigest()==md5
 validation.append({'plate':p['code'],'object_count':len(objects),'all_objects_have_toolpaths':True,'outside':False,'gcode_md5':md5,'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'printer_model_id':printer['model_id'],'gcode_bytes':len(gc)})
 assert max([float(x) for x in re.findall(r'^; LINE_WIDTH: ([0-9.]+)',g,re.M)] or [0])<1.3
 print('VERIFIED_PRINT_FILE',p['code'],len(objects),flush=True)

def duration(seconds):return f'{seconds//3600}小时{seconds%3600//60:02d}分'
total=sum(r['seconds'] for r in results);grams=sum(r['grams'] for r in results)
with (O/'每盘耗时与耗材.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['打印文件','内容','零件数量','层高mm','预计耗时','预计耗材g'])
 for p in plates:
  r=bycode[p['code']];w.writerow(['WM2_'+p['code']+'.gcode.3mf',p['title'],len(p['items']),p['layer_height'],duration(r['seconds']),r['grams']])
 w.writerow(['合计','不含底盘',sum(len(p['items']) for p in plates),'',duration(total),round(grams,2)])
with (O/'逐件所在打印盘.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['零件编号','打印盘','本盘数量'])
 for p in plates:
  for n,q in Counter(it['id'] for it in p['items']).items():w.writerow([n,p['code'],q])
(O/'校验记录.json').write_text(json.dumps({'validation':validation,'slice_results':results},ensure_ascii=False,indent=2),encoding='utf8')

font_path='C:/Windows/Fonts/msyh.ttc';font=ImageFont.truetype(font_path,24);small=ImageFont.truetype(font_path,19);titlefont=ImageFont.truetype(font_path,34)
canvas=Image.new('RGB',(1500,1790),(237,243,246));draw=ImageDraw.Draw(canvas)
draw.text((32,20),'铃芽庭院｜白模修复版 · 9 盘',font=titlefont,fill=(20,50,63))
draw.text((32,70),f'X1 Carbon · 0.4 mm · PLA · 纹理 PEI 板   合计约 {duration(total)} / {grams:.0f} g',font=font,fill=(45,75,87))
for j,p in enumerate(plates):
 x=15+(j%3)*495;y=118+(j//3)*550;r=bycode[p['code']]
 pic=Image.open(O/'排盘图'/(p['code']+'.png')).convert('RGB').resize((475,475))
 canvas.paste(pic,(x,y));draw.text((x+8,y+477),p['code']+'  '+duration(r['seconds']),font=font,fill=(20,50,63))
 draw.text((x+8,y+513),f"{p['title']} · {r['grams']:.1f} g",font=small,fill=(55,85,92))
canvas.save(O/'九盘打印总览.jpg',quality=93)
geometry=json.loads((R/'analysis/final-geometry-checks.json').read_text(encoding='utf8'))
fit=json.loads((R/'analysis/final-fit-checks.json').read_text(encoding='utf8'))
assert len(geometry)==28 and all(x['watertight'] and x['normal_consistency'] and x['zero_area_faces']==0 for x in geometry)
(O/'模型与装配检查记录.json').write_text(json.dumps({'geometry':geometry,'fit':fit},ensure_ascii=False,indent=2),encoding='utf8')
first=bycode['P01_SMALL'];previous=97863
text=f'''铃芽庭院｜白模修复版 WM2
日期：2026-10-30

用本包的 WM2_ 文件替换上一版 P01～P09 加速文件。
本次不打印底盘。整体比例仍对应外径 400 mm，底盘、定位孔与连接销的规格保持兼容。
共 9 盘、28 类、66 个实体，全部已经完成切片。
预计总耗时：{duration(total)}；PLA：{grams:.2f} 克，含当前支撑、裙边与初始化估算。

使用方法
1. 解压本下载包，将“复制到SD卡”目录中的 9 个 WM2_*.gcode.3mf 复制到打印机 microSD 卡。
2. 保留完整扩展名，不要再解压这些 .gcode.3mf 文件。在打印机屏幕选择对应文件打印。
3. 先打印 WM2_P01_SMALL.gcode.3mf，约 {duration(first['seconds'])}、{first['grams']:.2f} 克。该盘已经包含白门、全部连接件、小附件和试块。
4. 确认销孔松紧和门轴能安装后，再打印 WM2_P02～WM2_P09。每盘仅需打印一次。
5. 门轴另备直径 1 mm 的金属丝，先取约 22 mm，再按实物修短。

固定打印配置
Bambu Lab X1 Carbon、0.4 mm 喷嘴、白色 PLA、纹理 PEI 板。
采用 Bambu PLA Basic 的温度和流量预设：喷嘴 220°C，热床 55°C。
如果实际机型、喷嘴、材料或板材不同，请打开“排盘工程”按实际配置重新切片。
切片器有 PLA 热床温度提示；55°C 是该纹理板预设值，按打印机提示保持散热。

本次修复
重建建筑和钢架的实体表面，清理极薄碎面与退化碎片，加固细杆。
5 件原来游离的小景物接到其下方的钢架底托，安装位置保持对应。
白门把手的相切接缝已修正；小建筑附件改为躺放，减少细长小件站立打印。
设计中的窗洞和拱门保留。模型表面封闭不等于把所有窗洞堵死。

白模效果与速度
大部分建筑和钢架：0.24 mm；P05 建筑盘：0.20 mm；白门和小件：0.16 mm。
大件 2 圈墙、8% 填充；小件 3 圈墙；保留必要的自动树状支撑。
外表面速度与加速度作了限制，减少白模表面的振纹；内部保持较快速度。
使用 Arachne 可变线宽处理细节，保留默认尺度的最小线宽限制，未设成 0。
两件大件合一盘，减少反复换盘和初始化；不使用运动或狂暴倍率。
上一版纯加速包预计 27小时11分。本版的实体加固和表面精度不同，以本包 CSV 的新耗时为准。

已完成的离线检查
28 类零件：封闭性、面朝向、正体积、零面积面、浮动碎片和实际导出 STL 的重新读取。
对自相交候选进行检查；斜切面上的共面候选另投影到平面检查，确认没有面片重叠，避免自动补面破坏外形。
32 个安装孔检查没有被加厚或修补堵住；建筑与钢架模块检查没有装配重叠。
修整模块底托的接触部位，预留约 0.2 mm 装配余量，清除裁切后脱落的薄碎边。
白门在 0、15、30、45、60、75、90 度开合位置检查无几何干涉。
9 盘全部重新切片，66 个实体都有实际打印路径，未超打印范围，G-code 校验值正确。
打印机标识字段补齐为官方 X1 Carbon 配置中的 BL-P001；没有改写生成的 G-code。

验证边界
尚未实际打印，未连接打印机或启动打印任务。
离线检查不能代替实际材料、首层粘附和支撑拆除效果；先用第一盘确认配合，再批量打印。
零件位置见随包的 Blender 总装，分盘数量和耗时见 CSV。

参考资料
Bambu Studio 官方源码：https://github.com/bambulab/BambuStudio/blob/v02.01.01.52/src/libslic3r/Format/bbs_3mf.cpp
X1 Carbon 官方规格：https://public-cdn.bambulab.com/store/bambulab-X1-carbon-tech-specs.pdf
模型厚度与打印设计：https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
'''
(O/'先读我_白模修复版打印说明.txt').write_text(text,encoding='utf-8-sig')
archive=Path('D:/虚拟C盘/铃芽庭院_白模修复版_X1C_不含底盘.zip');assert not archive.exists(),str(archive)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=2) as z:
 for p in O.rglob('*'):
  if p.is_file():z.write(p,Path('铃芽庭院_白模修复版_WM2')/p.relative_to(O))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
summary={'archive':str(archive),'size_mb':round(archive.stat().st_size/1024**2,2),'plates':len(plates),'objects':sum(len(p['items']) for p in plates),'seconds':total,'grams':round(grams,2),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(R/'analysis/delivery.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False),flush=True)

