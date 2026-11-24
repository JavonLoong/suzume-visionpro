import pymeshlab as pm,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=[]
for p in (R/'STL').rglob('*.stl'):
    m=pm.MeshSet();m.load_new_mesh(str(p));m.compute_selection_by_self_intersections_per_face()
    count=m.current_mesh().selected_face_number();assert count==0,(p.name,count)
    rows.append({'file':str(p),'selected_faces':count});print(p.name,count)
assert len(rows)==9
(R/'analysis/self_intersection_check.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('NINE_SOLIDS_NO_SELF_INTERSECTIONS')
