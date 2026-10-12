from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
runtime={'DreamWorld.usdz','DoorFrame.usdz','DoorLeaf.usdz','Character.usdz','NightSky.png','AssetManifest.json'}
asset_report=json.loads((ROOT/'validation'/'asset_validation.json').read_text(encoding='utf-8'))
preview_report=json.loads((ROOT/'validation'/'preview_validation.json').read_text(encoding='utf-8'))
assert asset_report['sourceUnmodified'] and preview_report['pass']
assert not preview_report['requests'] and not preview_report['errors'] and not preview_report['consoleErrors']
files=[]
for file in (ROOT/'VisionProPortal').rglob('*'):
    if not file.is_file():continue
    if 'Resources' in file.parts and file.name not in runtime:continue
    if any(x in file.parts for x in ('DerivedData','BuildLogs','xcuserdata')):continue
    files.append(file)
files.extend(ROOT/name for name in ('README.md','技术方案.md','USDZ导出流程.md','续接记录.md','铃芽之旅_VisionPro适配_离线预览.html','cursor-original-source-20261011.zip'))
files.extend((ROOT/'tools').glob('*.py'))
files.extend((ROOT/'tools').glob('*.cjs'))
files.append(ROOT/'tools'/'portal_preview.html')
for name in ('asset_validation.json','preview_validation.json','export_manifest.json','character_export.json','hunyuan_character_selection.json','sky_clean_v2.json','portal-front.png','portal-side.png','world-full.png'):
    files.append(ROOT/'validation'/name)
for name,row in asset_report['assets'].items():
    path=ROOT/'VisionProPortal'/'VisionProPortal'/'Resources'/(name+'.usdz')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    assert not row['complianceErrors'] and not row['complianceFailedChecks']
report={'status':'content_and_source_adaptation_ready','swiftCompilation':'not_run_no_Mac','headsetValidation':'not_run_no_device',
 'offlinePreview':'pass','usdzCompliance':'pass','files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files))]}
index=ROOT/'交付清单.json';index.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');files.append(index)
dest=ROOT/'铃芽之旅_VisionPro适配_v57.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as zip:
    for path in sorted(set(files)):zip.write(path,Path('Suzume-VisionPro-v57')/path.relative_to(ROOT))
with zipfile.ZipFile(dest) as zip:
    assert zip.testzip() is None
    for name in ('DreamWorld.usdz','DoorFrame.usdz','DoorLeaf.usdz','Character.usdz'):
        data=zip.read('Suzume-VisionPro-v57/VisionProPortal/VisionProPortal/Resources/'+name)
        assert hashlib.sha256(data).hexdigest()==asset_report['assets'][Path(name).stem]['sha256']
print(json.dumps({'archive':str(dest),'bytes':dest.stat().st_size,'files':len(set(files)),'verified':True},ensure_ascii=False))
