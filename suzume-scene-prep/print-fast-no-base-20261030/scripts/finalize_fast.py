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
 path=O/'复制到SD卡'/(p['code']+'.gcode.3mf')
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
 print('VERIFIED_PRINT_FILE',p['code'],len(objects),flush=True)

def duration(seconds):return f'{seconds//3600}小时{seconds%3600//60:02d}分'
total=sum(r['seconds'] for r in results);grams=sum(r['grams'] for r in results)
with (O/'每盘耗时与耗材.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['打印文件','内容','零件数量','层高mm','预计耗时','预计耗材g'])
 for p in plates:
  r=bycode[p['code']];w.writerow([p['code']+'.gcode.3mf',p['title'],len(p['items']),p['layer_height'],duration(r['seconds']),r['grams']])
 w.writerow(['合计','不含底盘',sum(len(p['items']) for p in plates),'',duration(total),round(grams,2)])
with (O/'逐件所在打印盘.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['零件编号','打印盘','本盘数量'])
 for p in plates:
  for n,q in Counter(it['id'] for it in p['items']).items():w.writerow([n,p['code'],q])
(O/'校验记录.json').write_text(json.dumps({'validation':validation,'slice_results':results},ensure_ascii=False,indent=2),encoding='utf8')

font_path='C:/Windows/Fonts/msyh.ttc';font=ImageFont.truetype(font_path,24);small=ImageFont.truetype(font_path,19);titlefont=ImageFont.truetype(font_path,34)
canvas=Image.new('RGB',(1500,1790),(237,243,246));draw=ImageDraw.Draw(canvas)
draw.text((32,20),'铃芽庭院｜除底盘外 9 盘打印总览',font=titlefont,fill=(20,50,63))
draw.text((32,70),f'X1 Carbon · 0.4 mm · PLA · 纹理 PEI 板   合计约 {duration(total)} / {grams:.0f} g',font=font,fill=(45,75,87))
for j,p in enumerate(plates):
 x=15+(j%3)*495;y=118+(j//3)*550;r=bycode[p['code']]
 pic=Image.open(O/'排盘图'/(p['code']+'.png')).convert('RGB').resize((475,475))
 canvas.paste(pic,(x,y));draw.text((x+8,y+477),p['code']+'  '+duration(r['seconds']),font=font,fill=(20,50,63))
 draw.text((x+8,y+513),f"{p['title']} · {r['grams']:.1f} g",font=small,fill=(55,85,92))
canvas.save(O/'九盘打印总览.jpg',quality=93)

lines=['铃芽庭院：除底盘外，X1 Carbon 加速切片包','日期：2026-10-30','',
 f'共 9 盘、28 类零件、66 个实体。预计合计 {duration(total)}，PLA {grams:.2f} 克，已计入当前支撑、裙边和打印机初始化估算。',
 '包含：8 段建筑、8 段钢架、门框和门扇、7 个建筑附件、8 个连接键、32 个定位销、1 个配合试块。',
 '不包含：4 块底盘。模型比例仍为总直径 400 mm。','',
 '打印配置必须相符',
 '打印机：Bambu Lab X1 Carbon。喷嘴：0.4 mm。单色 PLA，按 Bambu PLA Basic 预设切片。打印板：纹理 PEI。',
 '喷嘴打印温度 220°C、热床 55°C。若实验室使用其他机器、喷嘴、材料或板材，请用“排盘工程”重新切片，不要直接打印这些固定刀路。',
 '线材选用能匹配 Bambu PLA Basic 预设的 PLA；品牌、流量差异需要以你们的小样结果为准。','',
 '怎么直接打印',
 '1. 解压下载包，把“复制到SD卡”目录里的 9 个 .gcode.3mf 文件复制到打印机 microSD 卡。保留完整扩展名，不要把这些文件再解压。',
 '2. 装好对应的 PLA 和纹理 PEI 板，在打印机屏幕选择卡内文件开始打印。这里不需要再次切片。',
 '3. 先打印 P01_SMALL。它包含全部白门、小附件、连接件和试块，预计 35 分钟、约 7.1 克。确认销孔与门轴能装，再打印 P02～P09。',
 '4. P02～P05 是建筑，P06～P09 是钢架。每盘只需打印一次；孔销和连接键已经放够数量。',
 '5. 去支撑后按旧版总装文件的编号装配。白门另备直径 1 mm 的金属丝作门轴，约 22 mm 起步并按实物修短。','',
 '这次怎样缩短时间',
 '建筑和钢架改为 0.28 mm 层高、2 圈墙、8% 填充，采用本机拓竹官方 Extra Draft 预设的速度；保留自动树状支撑和 3 mm 裙边。',
 '白门、小附件、定位销保留 0.16 mm 层高和 3 圈墙。连接件单独关闭支撑、裙边，方便取件。',
 '不改变模型尺寸，不使用运动/狂暴倍率，不改写打印机的运动或热保护参数。',
 '同一 W02 建筑样件：旧版 8小时40分 → 新版单件 2小时45分，约少 68%。',
 '同一 S05 钢架样件：旧版 3小时19分 → 新版单件 1小时21分，约少 59%。',
 '这两组是同一零件的实际切片对比，不代表整套旧版总耗时；整套新版时间以每盘 CSV 为准。',
 '取舍：大件层纹会更明显；按需要打磨、底漆、上色。微小掉漆纹理不会像 0.12 mm 版那样细。','',
 '检查结果与范围',
 '9 盘均实际完成离线切片；每盘都有真实 G-code、有效 MD5、原生缩略图和打印信息。',
 '全部 66 个实体都在切片记录与实际对象刀路中，未超打印范围。未包含底盘，也没有漏掉附件。',
 '修正了命令行导出遗漏的打印机标识字段：BL-P001，来自本机官方 X1 Carbon 型号配置。G-code 内容和其 MD5 保持原样。',
 '切片器提示 PLA 热床温度高于配置中的软化阈值；55°C 为该纹理板预设值，打印时按机器提示保持散热。',
 '尚未实际打印。孔的松紧、薄杆强度和支撑拆除效果仍以 P01 小样及第一盘大件实物为准。',
 '没有连接打印机或启动任何打印任务。','',
 '资料',
 '本机配置：C:/Program Files/Bambu Studio/resources/profiles/BBL/',
 'Bambu Studio 官方源码（切片文件结构）：https://github.com/bambulab/BambuStudio/blob/v02.01.01.52/src/libslic3r/Format/bbs_3mf.cpp',
 'X1 Carbon 官方规格：https://public-cdn.bambulab.com/store/bambulab-X1-carbon-tech-specs.pdf']
(O/'先读我_直接打印说明.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
archive=Path('D:/虚拟C盘/铃芽庭院_不含底盘_X1C_已切片加速版.zip');assert not archive.exists(),str(archive)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=2) as z:
 for p in O.rglob('*'):
  if p.is_file():z.write(p,Path('铃芽庭院_已切片加速版')/p.relative_to(O))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
summary={'archive':str(archive),'size_mb':round(archive.stat().st_size/1024**2,2),'plates':len(plates),'objects':sum(len(p['items']) for p in plates),'seconds':total,'grams':round(grams,2),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(R/'analysis/delivery.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False),flush=True)
