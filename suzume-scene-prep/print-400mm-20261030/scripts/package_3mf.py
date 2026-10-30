import json,sys,copy,math,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];O=R/'交付文件';A=R/'analysis'/'assembly_meshes';D=O/'拓竹X1C工程_逐件';D.mkdir(exist_ok=True)
manifest=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',N)
def e(p,t,**a):return ET.SubElement(p,'{'+N+'}'+t,{k:str(v) for k,v in a.items()})
def metadata(p,k,v):ET.SubElement(p,'metadata',key=k,value=str(v))
index={}
for p in Path('C:/Program Files/Bambu Studio/resources/profiles/BBL').rglob('*.json'):
 try:
  d=json.loads(p.read_text(encoding='utf-8-sig'))
  if d.get('name'):index[d['name']]=d
 except Exception:pass
def profile(n):
 d=index[n];r=profile(d['inherits']) if d.get('inherits') else {};r.update(d);return r
def settings(category):
 process='0.20mm Standard @BBL X1C' if category=='底盘' else '0.12mm High Quality @BBL X1C'
 r={};r.update(profile('Bambu Lab X1 Carbon 0.4 nozzle'));r.update(profile(process));r.update(profile('Bambu PLA Basic @BBL X1C'))
 r.update({'printer_settings_id':'Bambu Lab X1 Carbon 0.4 nozzle','printer_model':'Bambu Lab X1 Carbon','printer_variant':'0.4','print_settings_id':process,'filament_settings_id':['Bambu PLA Basic @BBL X1C'],'filament_type':['PLA'],'filament_colour':['#E4E1D5'],'default_filament_colour':[''],'curr_bed_type':'Textured PEI Plate','wall_loops':'3','top_shell_layers':'5','bottom_shell_layers':'4','sparse_infill_density':'12%','sparse_infill_pattern':'gyroid','enable_support':'0' if category in ['底盘','连接件','试装件'] else '1','support_type':'tree(auto)','support_threshold_angle':'30','support_on_build_plate_only':'0','brim_type':'no_brim' if category in ['连接件','试装件'] else 'outer_only','brim_width':'3','brim_object_gap':'.15','enable_prime_tower':'0','print_sequence':'by layer','filament_is_support':['0'],'required_nozzle_HRC':['3'],'inherits_group':[process,'','Bambu Lab X1 Carbon 0.4 nozzle'],'filament_ids':['GFA00'],'different_settings_to_system':['','',''],'print_compatible_printers':['Bambu Lab X1 Carbon 0.4 nozzle'],'flush_volumes_matrix':['0'],'flush_volumes_vector':['140','140']})
 for k in ['name','type','from','inherits','setting_id','instantiation']:r.pop(k,None)
 return r
def write3mf(path,entries,category):
 model=ET.Element('{'+N+'}model',unit='millimeter',attrib={'{http://www.w3.org/XML/1998/namespace}lang':'zh-CN'})
 e(model,'metadata',name='Application').text='BambuStudio-02.01.01.52'
 e(model,'metadata',name='BambuStudio:3mfVersion').text='1'
 e(model,'metadata',name='Title').text=path.stem
 resources=e(model,'resources');build=e(model,'build');cfg=ET.Element('config');plate=ET.SubElement(cfg,'plate')
 metadata(plate,'plater_id','1');metadata(plate,'plater_name',path.stem);metadata(plate,'locked','false')
 ass=ET.SubElement(cfg,'assemble')
 for j,(row,x,y) in enumerate(entries):
  d=np.load(A/(row['id']+'.npz'));v=d['vertices'];f=d['faces'];xf=np.array(row['assembly_to_print_matrix']);v=v@xf[:3,:3].T+xf[:3,3]
  mid=j*2+1;oid=mid+1
  meshob=e(resources,'object',id=mid,type='model');mesh=e(meshob,'mesh');vv=e(mesh,'vertices');tt=e(mesh,'triangles')
  for p in v:e(vv,'vertex',x=format(p[0],'.17g'),y=format(p[1],'.17g'),z=format(p[2],'.17g'))
  for t in f:e(tt,'triangle',v1=int(t[0]),v2=int(t[1]),v3=int(t[2]))
  ob=e(resources,'object',id=oid,type='model');com=e(ob,'components');e(com,'component',objectid=mid)
  e(build,'item',objectid=oid,transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0',printable='1')
  co=ET.SubElement(cfg,'object',id=str(oid));metadata(co,'name',row['id']);metadata(co,'extruder','1')
  part=ET.SubElement(co,'part',id=str(mid),subtype='normal_part');metadata(part,'name',row['id']);metadata(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1');ET.SubElement(part,'mesh_stat',face_count=str(len(f)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
  inst=ET.SubElement(plate,'model_instance');metadata(inst,'object_id',oid);metadata(inst,'instance_id','0');metadata(inst,'identify_id',oid)
  ET.SubElement(ass,'assemble_item',object_id=str(oid),instance_id='0',transform='1 0 0 0 1 0 0 0 1 0 0 0',offset='0 0 0')
 cfg.remove(plate);cfg.remove(ass);cfg.append(plate);cfg.append(ass)
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/model_settings.config',ET.tostring(cfg,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/project_settings.config',json.dumps(settings(category),ensure_ascii=False))
  z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/octet-stream"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
for row in manifest['parts']:
 if len(sys.argv)>1 and row['id'] not in sys.argv[1:]:continue
 w,h,z=row['size_mm'];write3mf(D/(row['id']+'.3mf'),[(row,128-w/2,128-h/2)],row['category'])
 print('3MF',row['id'],flush=True)
byid={r['id']:r for r in manifest['parts']}
sample=[(byid['T01_先打印配合试块'],60,80),(byid['K01_底盘拼接键'],105,80),(byid['K02_模块定位销'],125,80),(byid['D01_门框与台阶'],60,110),(byid['D02_六格门扇'],88,110)]
write3mf(O/'00_先试装_白门与连接件_X1C.3mf',sample,'白门')
keys=[(byid['K01_底盘拼接键'],55+(i%4)*20,60+(i//4)*12) for i in range(8)]
keys += [(byid['K02_模块定位销'],55+(i%8)*8,100+(i//8)*8) for i in range(32)]
write3mf(O/'01_全套定位键与销_X1C.3mf',keys,'连接件')
print('PACKAGED',len(manifest['parts'])+2,flush=True)
