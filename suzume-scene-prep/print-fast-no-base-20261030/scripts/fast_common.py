import json,zipfile,xml.etree.ElementTree as ET,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
OLD=R.parent/'print-400mm-20261030'
INDEX={}
for p in Path('C:/Program Files/Bambu Studio/resources/profiles/BBL').rglob('*.json'):
 try:
  d=json.loads(p.read_text(encoding='utf-8-sig'))
  if d.get('name'):INDEX[d['name']]=d
 except Exception:pass
def profile(n):
 d=INDEX[n];r=profile(d['inherits']) if d.get('inherits') else {};r.update(d);return r
def settings(base,height,kind='large'):
 pn={.28:'0.28mm Extra Draft @BBL X1C',.24:'0.24mm Draft @BBL X1C',.16:'0.16mm Optimal @BBL X1C'}[height]
 c=base.copy();c.update(profile(pn))
 c.update({'print_settings_id':pn,'inherits_group':[pn,'','Bambu Lab X1 Carbon 0.4 nozzle'],
 'different_settings_to_system':['','',''],'filament_ids':['GFA00'],'print_compatible_printers':['Bambu Lab X1 Carbon 0.4 nozzle'],
 'layer_height':str(height),'wall_loops':'3' if kind=='small' else '2','sparse_infill_density':'8%',
 'sparse_infill_pattern':'adaptivecubic','top_shell_layers':'3','bottom_shell_layers':'3',
 'top_shell_thickness':'.72','bottom_shell_thickness':'.6','enable_support':'1','support_type':'tree(auto)',
 'support_threshold_angle':'30','support_on_build_plate_only':'0','support_base_pattern_spacing':'3',
 'support_interface_top_layers':'2','support_interface_bottom_layers':'1','support_top_z_distance':str(height),
 'support_bottom_z_distance':str(height),'brim_type':'outer_only','brim_width':'3','brim_object_gap':'.15',
 'enable_prime_tower':'0','print_sequence':'by layer','timelapse_type':'0','enable_overhang_speed':'1',
 'curr_bed_type':'Textured PEI Plate','textured_plate_temp':['55'],'textured_plate_temp_initial_layer':['55']})
 if kind=='small':c.update({'outer_wall_speed':['80'],'inner_wall_speed':['150'],'sparse_infill_density':'15%'})
 for k in ['name','type','from','inherits','setting_id','instantiation']:c.pop(k,None)
 return c
def patch(src,dst,height,kind='large'):
 with zipfile.ZipFile(src) as z:data={n:z.read(n) for n in z.namelist()}
 base=json.loads(data['Metadata/project_settings.config'])
 data['Metadata/project_settings.config']=json.dumps(settings(base,height,kind),ensure_ascii=False).encode('utf8')
 root=ET.fromstring(data['Metadata/model_settings.config'])
 for plate in root.findall('plate'):ET.SubElement(plate,'metadata',key='printer_model_id',value='BL-P001')
 data['Metadata/model_settings.config']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in data.items():z.writestr(n,b)
def slice_one(src,dst,orient=0):
 label=dst.stem;log=R/'analysis'/(label+'.log');err=R/'analysis'/(label+'.err')
 work=R/'analysis/work'/label;work.mkdir(parents=True,exist_ok=True)
 args=['C:/Program Files/Bambu Studio/bambu-studio.exe','--debug','2','--slice','0','--arrange','0','--orient',str(orient),'--mstpp','240','--export-3mf',dst.name,'--outputdir',str(work),str(src)]
 start=time.time()
 with log.open('w',encoding='utf8') as out,err.open('w',encoding='utf8') as ef:
  try:p=subprocess.run(args,stdout=out,stderr=ef,creationflags=subprocess.CREATE_NO_WINDOW,timeout=300);code=p.returncode
  except subprocess.TimeoutExpired:code=-1
 r={'input':str(src),'output':str(dst),'exit_code':code,'slicing_seconds':round(time.time()-start,1)}
 if code==0 and (work/dst.name).exists():
  shutil.copy2(work/dst.name,dst)
  with zipfile.ZipFile(dst) as z:
   root=ET.fromstring(z.read('Metadata/slice_info.config'));plate=root.find('plate')
   s={x.get('key'):x.get('value') for x in plate.findall('metadata')}
   r.update(seconds=int(s['prediction']),grams=float(s['weight']),outside=s['outside'],warnings=[x.attrib for x in plate.findall('warning')],gcode_files=[x for x in z.namelist() if x.endswith('.gcode')])
 (R/'analysis'/(label+'_result.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(r,ensure_ascii=False),flush=True)
 return r
