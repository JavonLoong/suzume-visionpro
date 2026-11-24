"""Assemble the complete door-side print set from already verified source parts."""
import json,shutil,hashlib
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis';S=P/'print-door-detail-20261113';L=P/'print-linkage-trial-20261113'
for p in [A/'assembly',R/'STL',R/'交付']:p.mkdir(parents=True,exist_ok=True)
data=json.loads((S/'analysis/door_manifest.json').read_text(encoding='utf8'))
link=json.loads((L/'analysis/linkage_manifest.json').read_text(encoding='utf8'));new_parts={r['id']:r for r in link['parts']}
rows=[]
for row in data['parts']:
    row=row.copy();height=int(row['group'].replace('毫米',''));is_leaf=row['id'].endswith('门扇')
    source=new_parts[f'门扇{height}'] if is_leaf else row
    src=Path(source['stl_path'] if is_leaf else source['stl']);digest=source['sha256']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    dest=R/'STL'/row['group']/(row['id']+'.stl');dest.parent.mkdir(exist_ok=True);shutil.copy2(src,dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
    assembly=(L if is_leaf else S)/'analysis/assembly'/(row['id']+'.npz')
    shutil.copy2(assembly,A/'assembly'/assembly.name)
    mesh=trimesh.load(dest,force='mesh');assert mesh.is_volume and len(mesh.split())==1 and mesh.is_winding_consistent and np.all(mesh.area_faces>1e-12)
    row.update(stl=str(dest),sha256=digest,size_mm=mesh.extents.tolist(),source_stl=str(src));rows.append(row)
data.update(status='完整门侧打印包：精细白门、背面三档拉杆孔、对应插座板',parts=rows,linkage_source=str(L),
            linkage_checks=link['checks'],linkage_variants=link['variants'],servo_drive_finished=False,actual_print_test=False)
data['adapted'].append('已将背面三档拉杆耳合入完整门扇；原门框及插座接口沿用')
data['scope']='完成门侧几何与排盘；舵机、钢丝实际长度和支架不包含在本次交付'
(A/'door_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
for name in ['pack_doors.py','slice_doors.py','check_meshes.py']:shutil.copy2(S/'scripts'/name,R/'scripts'/name)
print('COMPLETE_DOOR_SET_ASSEMBLED',len(rows),flush=True)
