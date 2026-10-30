import json,zipfile,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'交付文件'
d=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
checks=json.loads((R/'analysis/final-geometry-checks.json').read_text(encoding='utf8'))
for c in checks:
 c.pop('self_intersection_scan_faces',None)
 cap=R/'analysis/cap_checks'/(c['id']+'.json')
 if cap.exists():
  report=json.loads(cap.read_text(encoding='utf8'))
  c['analytic_cut_raw_candidates']=report['scanner_candidates']
  c['analytic_cut_unclassified_candidates']=report['unclassified_candidates']
  c['projected_cut_planes_verified']=len(report['projected_cap_checks'])
 c['intersection_validation']='输入表面已修复并扫描；斜切面的共面候选已投影校验；装配接触裁切使用 Manifold 实体差集。'
d['project']='铃芽庭院 400 mm 白模修复版 WM2（不含底盘）'
d['source_history']={k:d.pop(k) for k in ['adaptation_notes','recovery_note'] if k in d}
d['export_validation']=checks
d['limits']=['400 mm 为底盘外径。本包不打印底盘；排除远景树林、天空、人物和虚拟异世界。',
 '保留实际窗洞和拱门；移除不可独立打印的薄碎片，实体表面已修复，钢架加固，接触处预留约 0.2 mm 装配余量。',
 '六格门保留独立门扇、门框和金属销轴结构；细小表面装饰适当简化。',
 '切片固定为 X1 Carbon、0.4 mm 喷嘴、白色 PLA、纹理 PEI 板。尚未试打，请先打印 P01 核对配合。',
 '9 盘均包含实际 G-code；没有连接打印机或启动打印任务。']
(R/'analysis/final-geometry-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
(O/'零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
p=O/'模型与装配检查记录.json';report=json.loads(p.read_text(encoding='utf8'));report['geometry']=checks
p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
delivery_path=R/'analysis/delivery.json';delivery=json.loads(delivery_path.read_text(encoding='utf8'));archive=Path(delivery['archive']);tmp=R/'analysis/final-delivery.tmp'
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=2) as z:
 for p in O.rglob('*'):
  if p.is_file() and not p.name.endswith('.blend1'):z.write(p,Path('铃芽庭院_白模修复版_WM2')/p.relative_to(O))
with zipfile.ZipFile(tmp) as z:
 assert z.testzip() is None
 assert len([n for n in z.namelist() if n.endswith('.gcode.3mf')])==9
tmp.replace(archive)
delivery.update(size_mb=round(archive.stat().st_size/1024**2,2),sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
delivery_path.write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(delivery,ensure_ascii=False))
