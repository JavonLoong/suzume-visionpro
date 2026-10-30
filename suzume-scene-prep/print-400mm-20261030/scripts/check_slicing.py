import subprocess,sys,json,time,zipfile,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'交付文件';C=R/'analysis/slice_checks';C.mkdir(exist_ok=True)
exe='C:/Program Files/Bambu Studio/bambu-studio.exe'
for name in sys.argv[1:]:
 path=O/'00_先试装_白门与连接件_X1C.3mf' if name=='sample' else min((O/'拓竹X1C工程_逐件').glob(name+'*.3mf'),key=lambda p:len(p.name))
 start=time.time();args=[exe,'--debug','2','--slice','0','--arrange','0','--orient','0','--mstpp','180','--export-3mf',name+'_sliced.3mf','--outputdir',str(C),str(path)]
 with (C/(name+'.log')).open('w',encoding='utf8') as out,(C/(name+'.err')).open('w',encoding='utf8') as err:
  try:p=subprocess.run(args,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,timeout=240);code=p.returncode
  except subprocess.TimeoutExpired:code=-1
 rec={'part':name,'input':str(path),'exit_code':code,'seconds':round(time.time()-start,1),'sliced_file_exists':(C/(name+'_sliced.3mf')).exists()}
 if rec['sliced_file_exists']:
  with zipfile.ZipFile(C/(name+'_sliced.3mf')) as z:
   rec['gcode_files']=[f for f in z.namelist() if f.endswith('.gcode')]
   if 'Metadata/slice_info.config' in z.namelist():
    s=z.read('Metadata/slice_info.config').decode('utf8');(C/(name+'_slice_info.xml')).write_text(s,encoding='utf8')
 (C/(name+'_result.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(rec,ensure_ascii=False),flush=True)
