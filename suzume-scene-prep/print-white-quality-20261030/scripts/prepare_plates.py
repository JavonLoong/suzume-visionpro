import sys,json,math,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from fast_common import R,OLD,settings
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',N)
manifest=json.loads((OLD/'交付文件/零件清单.json').read_text(encoding='utf8'));rows={r['id']:r for r in manifest['parts']}
base=json.loads((R/'analysis/base_settings.json').read_text(encoding='utf8'))
MESH=R/'analysis/plate_meshes';MESH.mkdir(exist_ok=True)
def meta(p,k,v):ET.SubElement(p,'metadata',key=k,value=str(v))
def el(p,t,**a):return ET.SubElement(p,'{'+N+'}'+t,{k:str(v) for k,v in a.items()})
def geometry(row,long_x=False):
 q=np.load(OLD/'analysis/assembly_meshes'/(row['id']+'.npz'));m=np.array(row['assembly_to_print_matrix']);v=q['vertices']@m[:3,:3].T+m[:3,3]
 if long_x and np.ptp(v[:,1])>np.ptp(v[:,0]):v=v[:,[1,0,2]]*np.array([-1,1,1])
 v-=v.min(axis=0)
 return v,q['faces']
plates=[]
def write_plate(code,title,entries,height):
 model=ET.Element('{'+N+'}model',unit='millimeter',attrib={'{http://www.w3.org/XML/1998/namespace}lang':'zh-CN'})
 el(model,'metadata',name='Application').text='BambuStudio-02.01.01.52'
 el(model,'metadata',name='BambuStudio:3mfVersion').text='1'
 el(model,'metadata',name='Title').text=title
 resources=el(model,'resources');build=el(model,'build');cfg=ET.Element('config');plate=ET.Element('plate');assembly=ET.Element('assemble')
 meta(plate,'plater_id','1');meta(plate,'plater_name',title);meta(plate,'locked','false');meta(plate,'printer_model_id','BL-P001')
 items=[];vs=[];fs=[];face_groups=[];offset=0
 for j,(row,v,f,x,y) in enumerate(entries):
  mid=2*j+1;oid=mid+1;res=el(resources,'object',id=mid,type='model');mesh=el(res,'mesh');vv=el(mesh,'vertices');tt=el(mesh,'triangles')
  for p in v:el(vv,'vertex',x=format(p[0],'.17g'),y=format(p[1],'.17g'),z=format(p[2],'.17g'))
  for t in f:el(tt,'triangle',v1=int(t[0]),v2=int(t[1]),v3=int(t[2]))
  ob=el(resources,'object',id=oid,type='model');cs=el(ob,'components');el(cs,'component',objectid=mid)
  el(build,'item',objectid=oid,transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0',printable='1')
  co=ET.SubElement(cfg,'object',id=str(oid));meta(co,'name',row['id']);meta(co,'extruder','1')
  if row['id'].startswith(('K','T')):meta(co,'enable_support','0');meta(co,'brim_type','no_brim')
  part=ET.SubElement(co,'part',id=str(mid),subtype='normal_part');meta(part,'name',row['id']);meta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
  ET.SubElement(part,'mesh_stat',face_count=str(len(f)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
  ins=ET.SubElement(plate,'model_instance');meta(ins,'object_id',oid);meta(ins,'instance_id','0');meta(ins,'identify_id',oid)
  ET.SubElement(assembly,'assemble_item',object_id=str(oid),instance_id='0',transform='1 0 0 0 1 0 0 0 1 0 0 0',offset='0 0 0')
  placed=v+np.array([x,y,0]);assert placed[:,:2].min()>8 and placed[:,:2].max()<248 and not (placed[:,0].min()<18 and placed[:,1].min()<28),(code,row['id'],placed.min(axis=0),placed.max(axis=0))
  vs.append(placed);fs.append(f+offset);face_groups.append(np.full(len(f),j));offset+=len(v)
  items.append({'id':row['id'],'object_id':oid,'bounds_mm':[placed.min(axis=0).tolist(),placed.max(axis=0).tolist()]})
 cfg.append(plate);cfg.append(assembly)
 out=R/'交付文件/排盘工程'/(code+'.3mf')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/model_settings.config',ET.tostring(cfg,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/project_settings.config',json.dumps(settings(base,height,'small' if code.startswith('P01') else 'large'),ensure_ascii=False))
  z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/octet-stream"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 np.savez_compressed(MESH/(code+'.npz'),vertices=np.concatenate(vs),faces=np.concatenate(fs),face_groups=np.concatenate(face_groups))
 plates.append({'code':code,'title':title,'input':str(out),'layer_height':height,'items':items})
 print('PREPARED',code,len(entries),flush=True)

small=[]
def add(n,x,y):
 row=rows[n];v,f=geometry(row);small.append((row,v,f,x,y))
add('T01_先打印配合试块',40,40);add('D01_门框与台阶',92,40);add('D02_六格门扇',126,40)
for j,row in enumerate(r for r in rows.values() if '_附件' in r['id']):add(row['id'],40+18*j,90)
for j in range(8):add('K01_底盘拼接键',40+20*(j%4),120+14*(j//4))
for j in range(32):add('K02_模块定位销',40+8*(j%8),165+8*(j//8))
write_plate('P01_SMALL','白门、全部连接件、附件与试块',small,.16)
height=float(sys.argv[1]) if len(sys.argv)>1 else .28
for code,cn,plate_start in [('W','环形建筑',2),('S','钢架',6)]:
 for pair in range(4):
  entries=[];geoms=[]
  for i in [pair*2+1,pair*2+2]:
   row=rows[f'{code}{i:02d}_{cn}'];v,f=geometry(row,long_x=True);geoms.append((row,v,f))
  total=sum(np.ptp(v[:,1]) for _,v,_ in geoms)+20;y=(256-total)/2
  for row,v,f in geoms:
   entries.append((row,v,f,(256-np.ptp(v[:,0]))/2,y));y+=np.ptp(v[:,1])+20
  name=f'P{plate_start+pair:02d}_{code}{pair*2+1:02d}_{code}{pair*2+2:02d}'
  # This wall pair crashes the installed organic-support engine at 0.24 mm.
  # Its verified 0.20 mm support plan is retained; the other large plates use 0.24 mm.
  write_plate(name,f'{cn} {pair*2+1:02d} 与 {pair*2+2:02d}',entries,.20 if name=='P05_W07_W08' else .24)
from collections import Counter
actual=Counter(it['id'] for p in plates for it in p['items']);expected={r['id']:r['quantity'] for r in rows.values() if not r['id'].startswith('B')}
assert actual==expected,(actual,expected)
(R/'analysis/plates.json').write_text(json.dumps(plates,ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_PLATES_READY',len(plates),sum(actual.values()),flush=True)
