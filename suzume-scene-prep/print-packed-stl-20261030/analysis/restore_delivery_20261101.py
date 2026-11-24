from pathlib import Path
import json,zipfile,hashlib,re,xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1];A=R/'analysis'
target=Path('D:/虚拟C盘');archive=target/'第一组.zip';print_dir=target/'第一组_直接打印'
rows=json.loads((A/'export-checks.json').read_text(encoding='utf8'))
slice_results=json.loads((A/'slicing-checks.json').read_text(encoding='utf8'))
assert len(rows)==4 and sum(r['components'] for r in rows)==66
assert all(r['watertight'] and r['normal_consistency'] for r in rows)
assert len(slice_results)==4 and all(r['exit_code']==0 and r['outside']=='false' for r in slice_results)
assert not archive.exists(), '目标压缩包已存在，停止覆盖未知文件'
tmp=A/'第一组_恢复中.zip'
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for row in rows:
        data=(R/'STL'/row['filename']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256'], row['filename']
        z.writestr(row['filename'],data)
with zipfile.ZipFile(tmp) as z:
    assert z.namelist()==[f'第{i}盘.stl' for i in range(1,5)]
    for row in rows:assert hashlib.sha256(z.read(row['filename'])).hexdigest()==row['sha256']
tmp.replace(archive)
print('RESTORED_STL_ARCHIVE',str(archive),flush=True)

machine=json.loads(Path('C:/Program Files/Bambu Studio/resources/profiles/BBL/machine/Bambu Lab X1 Carbon.json').read_text(encoding='utf8'))
assert machine['model_id']=='BL-P001'
print_dir.mkdir(exist_ok=True)
checks=[]
for i in range(1,5):
    src=A/f'Plate{i}.gcode.3mf';dst=print_dir/f'{i}.gcode.3mf'
    assert not dst.exists(), '目标打印文件已存在，停止覆盖未知文件'
    with zipfile.ZipFile(src) as z:
        assert z.testzip() is None
        entries={n:z.read(n) for n in z.namelist()}
    gc=entries['Metadata/plate_1.gcode'];md5=hashlib.md5(gc).hexdigest()
    assert entries['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
    cfg=json.loads(entries['Metadata/project_settings.config'])
    assert cfg['printer_settings_id']=='Bambu Lab X1 Carbon 0.4 nozzle'
    assert cfg['nozzle_diameter']==['0.4'] and cfg['filament_type']==['PLA']
    assert cfg['curr_bed_type']=='Textured PEI Plate'
    assert cfg['nozzle_temperature']==['220'] and cfg['textured_plate_temp']==['55']
    assert cfg['enable_support']=='1' and cfg['support_type']=='tree(auto)'
    assert float(cfg['layer_height'])==(.16 if i==4 else .2)
    root=ET.fromstring(entries['Metadata/slice_info.config']);plate=root.find('plate');meta={x.get('key'):x for x in plate.findall('metadata')}
    assert meta['outside'].get('value')=='false' and meta['support_used'].get('value')=='true'
    objects=plate.findall('object');assert len(objects)==1 and objects[0].get('skipped')=='false'
    assert objects[0].get('name')==f'Plate{i}'
    g=gc.decode('utf8');body=g.split('; EXECUTABLE_BLOCK_START',1)[1].split('; EXECUTABLE_BLOCK_END',1)[0]
    assert not any('{' in line.split(';')[0] or '}' in line.split(';')[0] for line in body.splitlines())
    assert 'G29' in body and 'M73 P100' in body and re.search(r'^; OBJECT_ID: 2\b',body,re.M)
    assert max(float(x) for x in re.findall(r'^; LINE_WIDTH: ([0-9.]+)',g,re.M))<1.3
    # Fill only the printer identification metadata omitted by the CLI.
    # Keep the generated machine instructions and their checksum byte-for-byte.
    meta['printer_model_id'].set('value',machine['model_id'])
    entries['Metadata/slice_info.config']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    work=A/f'direct_print_{i}.tmp'
    with zipfile.ZipFile(work,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for name,data in entries.items():z.writestr(name,data)
    with zipfile.ZipFile(work) as z:
        assert z.testzip() is None
        assert hashlib.md5(z.read('Metadata/plate_1.gcode')).hexdigest()==md5
        assert z.read('Metadata/plate_1.gcode')==gc
    work.replace(dst)
    checks.append({'plate':i,'path':str(dst),'printer':'Bambu Lab X1 Carbon','nozzle_mm':.4,'material':'PLA','plate_type':'Textured PEI Plate','nozzle_C':220,'bed_C':55,'layer_height_mm':float(cfg['layer_height']),'estimated_seconds':int(meta['prediction'].get('value')),'estimated_grams':float(meta['weight'].get('value')),'support_used':True,'outside':False,'gcode_md5':md5,'file_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'warnings':[x.attrib for x in plate.findall('warning')]})
    print('VERIFIED_DIRECT_PRINT',i,md5,flush=True)
report={'date':'2026-11-01','stl_archive':str(archive),'stl_count':4,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'direct_print_directory':str(print_dir),'direct_print_files':checks,'actual_print_test':False,'printer_job_started':False}
(A/'restored_delivery_20261101.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':str(archive),'print_directory':str(print_dir),'plates':4,'estimated_hours':round(sum(x['estimated_seconds'] for x in checks)/3600,2),'estimated_grams':sum(x['estimated_grams'] for x in checks)},ensure_ascii=False),flush=True)
