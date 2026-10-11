"""Standalone local viewer; large original model stays outside the inline widget."""
from pathlib import Path
import json,sys,requests
R=Path(__file__).parent;out=R/'viewer';out.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
sys.path.insert(0,str(V));from pack_cloud_payloads import pack_records
s=(V/'full-scene-template.html').read_text(encoding='utf-8')
mapping=[('__HOTEL_GEOMETRY__','round-hotel.js'),('__DOOR_GEOMETRY__','door-solid-geometry.js'),('__NIGHT_WORLD__','night-world.js'),('__WATER_AND_PORTAL__','full-water-portal.js'),('__CLOUD_SOLIDS__','cloud-reference-volumes.json'),('__POSTER_COMPOSITION__','poster-composition-v7.json'),('__DOME_CALIBRATION__','dome-calibration-v7.json'),('__SKY_PALETTE__','sky-palette-v7.json'),('__DOME_ARCH_CALIBRATION__','dome-arch-calibration-v8.json'),('__FACADE_SURFACE__','facade-pigments-v9.js'),('__FACADE_PIGMENTS__','facade-pigments-v9.json'),('__DISTANT_CLOUDS__','distant-cloud-volumes-v9.json'),('__DOOR_PANEL_CALIBRATION__','door-panel-calibration-v10.json'),('__DOOR_CHIPS__','door-chips-v10.json'),('__DOOR_SURFACE__','door-pigments-v10.js'),('__DOOR_PIGMENTS__','door-pigments-v10.json'),('__WATER_PALETTE__','water-palette-v11.json')]
for marker,file in mapping:
 value=(V/file).read_text(encoding='utf-8')
 if marker in ['__CLOUD_SOLIDS__','__DISTANT_CLOUDS__']:value=pack_records(json.loads(value))
 s=s.replace(marker,value)
character="""
    loading.textContent='正在载入混元人物与完整三维场景…';
    const characterAsset=await new Promise((resolve,reject)=>new T.GLTFLoader().load('suzume-posed-v16.gltf',resolve,undefined,reject));
    const character=characterAsset.scene;character.name='Suzume Hunyuan posed character';
    let figureTriangles=0;
    character.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;figureTriangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;}});
    scene.add(character);
    const nightCharacter=character.clone(true);nightCharacter.name='Suzume Hunyuan beyond portal';nightScene.add(nightCharacter);
    __PORTAL_CHARACTER_PARTITION__
    root.figureEvidence={source:'Actual Hunyuan 3D 3.1 four-view generation',revision:16,triangles:figureTriangles,pose:'Film-landmark calibration; editable 20-bone rig and proportion shape key are in Blender',oneToOneComplete:false};
"""
s=s.replace('__CHARACTER_GEOMETRY__',character.replace('__PORTAL_CHARACTER_PARTITION__',(R/'portal-character-partition.js').read_text(encoding='utf-8')))
s=s.replace("new T.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'})","new T.WebGLRenderer({canvas,context:canvas.getContext('webgl',{antialias:true,alpha:false,powerPreference:'high-performance'}),antialias:true,alpha:false,powerPreference:'high-performance'})")
s=s.replace('<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>','<script src="three.min.js"></script>\n<script src="GLTFLoader.js"></script>')
s=s.replace("let state={open:false,motion:!reduced,azimuth:posterComposition.azimuth,elevation:posterComposition.elevation,radius:posterComposition.radius,target:[...posterComposition.target],view:'poster'};","let state={open:true,motion:false,azimuth:0,elevation:.01,radius:4.04,target:[.18,1.94,0],view:'close'};")
s=s.replace("character.visible=state.open;nightCharacter.visible=state.view!=='night'&&state.open;","character.visible=state.open&&angle>1.50;nightCharacter.visible=character.visible;")
s=s.replace("restore(window.openai&&window.openai.widgetState);","restore(window.openai&&window.openai.widgetState);try{if(!location.search.includes('inspection=1'))restore({privateContent:JSON.parse(localStorage.getItem('suzume-local-view')||'null')});}catch(e){}")
s=s.replace("const save=()=>{if(window.openai", "const save=()=>{try{if(!location.search.includes('inspection=1'))localStorage.setItem('suzume-local-view',JSON.stringify({scene:'suzume-full-3d',revision:7,...state}));}catch(e){}if(window.openai")
s=s.replace("complete procedural figure","Hunyuan reconstructed figure")
s=s.replace('<option value="back">背面</option>','<option value="left">左侧</option><option value="right">右侧</option><option value="back">背面</option>')
s=s.replace("if(name==='aerial')","if(name==='left')Object.assign(state,{azimuth:-Math.PI/2,elevation:.07,radius:5.5,target:[0,1.7,-.4]});if(name==='right')Object.assign(state,{azimuth:Math.PI/2,elevation:.07,radius:5.5,target:[0,1.7,-.4]});if(name==='aerial')")
s=s.replace("'close','back','aerial'","'close','left','right','back','aerial'")
header='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>铃芽之旅 · 完整三维场景</title>
<style>
:root{--foreground:#e4e7e5;--background:#111915;--muted:#22372f}*{box-sizing:border-box}body{margin:0;background:#111915;font:14px/1.6 system-ui,"Microsoft YaHei",sans-serif;color:#e4e7e5}main{max-width:1440px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:20px}h1{font-size:24px;font-weight:500;letter-spacing:.1em;margin:0}p{color:#a9b6af;margin:4px 0}a{color:#b6d4c2}button,select{font:inherit;color:#e5ece7;background:#263b30;border:1px solid #506959;border-radius:8px;padding:9px 15px}button{cursor:pointer}button:hover{background:#375444}button:focus-visible,select:focus-visible{outline:2px solid #c5dfac;outline-offset:3px}.full-controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px}.form-label{display:flex;gap:10px;align-items:center}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
#suzume-full-scene .full-stage{width:min(100%,540px);border-radius:12px}#suzume-full-scene .full-stage.landscape{width:100%;max-height:78vh}footer{text-align:center;color:#8fa496;font-size:12px;margin-top:16px}@media(max-width:650px){main{padding:14px}header{align-items:start;flex-direction:column;gap:5px}h1{font-size:21px}}
</style><main><header><div><h1>铃芽之旅 · 门的两侧</h1><p>拖动旋转 · 滚轮缩放 · 右键或 Shift 拖动平移</p></div><p>混元人物 / 比例与步态校准 · v16</p></header>'''
footer='<footer>可旋转的完整几何场景。人物为混元 3D 重建，穿门空间分隔已保留，造型与握门细节仍在校准。<br><a href="../index.html">人物四视图与文件</a> · <a href="suzume-posed-v16.glb" download>下载场景姿态人物 GLB</a></footer></main></html>'
output=out/('candidate-v16.html' if '--candidate' in sys.argv else 'index.html')
output.write_text(header+s+footer,encoding='utf-8')
for name,url in [('three.min.js','https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'),('GLTFLoader.js','https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js')]:
 if not (out/name).exists():
  response=requests.get(url,timeout=30);response.raise_for_status();(out/name).write_bytes(response.content)
print('LOCAL_VIEWER_BUILT',str(output),len(output.read_bytes()))
