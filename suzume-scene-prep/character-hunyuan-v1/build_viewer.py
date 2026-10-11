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
    const characterAsset=await new Promise((resolve,reject)=>new T.GLTFLoader().load('suzume-posed-v17.gltf',resolve,undefined,reject));
    const character=characterAsset.scene;character.name='Suzume Hunyuan posed character';
    let figureTriangles=0;
    character.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;figureTriangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;}});
    scene.add(character);
    const nightCharacter=character.clone(true);nightCharacter.name='Suzume Hunyuan beyond portal';nightScene.add(nightCharacter);
    __PORTAL_CHARACTER_PARTITION__
    root.figureEvidence={source:'Hunyuan 3D 3.1 body and independent Hunyuan 2mv four-view head',revision:17,triangles:figureTriangles,independentHead:true,pose:'v16 foot clearance and editable 20-bone rig preserved; independent head with neck blending',oneToOneComplete:false};
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
s=s.replace('<option value="night">门后草地</option>','<option value="night">门后草地</option><option value="head">人物近景</option>')
s=s.replace("if(name==='aerial')", "if(name==='head')Object.assign(state,{open:true,azimuth:Math.PI,elevation:0,radius:1.45,target:[-.15,2.89,-.78]});if(name==='aerial')")
s=s.replace("state.view==='night'", "(state.view==='night'||state.view==='head')")
s=s.replace("'aerial','night'", "'aerial','night','head'")
header='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>铃芽之旅 · 完整三维场景</title>
<style>
:root{--foreground:#e4e7e5;--background:#111915;--muted:#22372f}*{box-sizing:border-box}body{margin:0;background:#111915;font:14px/1.6 system-ui,"Microsoft YaHei",sans-serif;color:#e4e7e5}main{max-width:1440px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:20px}h1{font-size:24px;font-weight:500;letter-spacing:.1em;margin:0}p{color:#a9b6af;margin:4px 0}a{color:#b6d4c2}button,select{font:inherit;color:#e5ece7;background:#263b30;border:1px solid #506959;border-radius:8px;padding:9px 15px}button{cursor:pointer}button:hover{background:#375444}button:focus-visible,select:focus-visible{outline:2px solid #c5dfac;outline-offset:3px}.full-controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px}.form-label{display:flex;gap:10px;align-items:center}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
#suzume-full-scene .full-stage{width:min(100%,540px);border-radius:12px}#suzume-full-scene .full-stage.landscape{width:100%;max-height:78vh}footer{text-align:center;color:#8fa496;font-size:12px;margin-top:16px}@media(max-width:650px){main{padding:14px}header{align-items:start;flex-direction:column;gap:5px}h1{font-size:21px}}
</style><main><header><div><h1>铃芽之旅 · 门的两侧</h1><p>拖动旋转 · 滚轮缩放 · 右键或 Shift 拖动平移</p></div><p>混元人物 / 独立头部重建 · v17</p></header>'''
footer='<footer>可旋转的完整几何场景。头部已独立重建，脚部间隙和穿门空间分隔已保留；脸型、发丝与贴图细节仍在校准。<br><a href="../index.html">人物四视图与文件</a> · <a href="suzume-posed-v17.glb" download>下载场景姿态人物 GLB</a></footer></main></html>'
if '--movie-projection' in sys.argv or '--movie-steel' in sys.argv:
 from projection_geometry_v24 import O as P24,P,new_edges,old_edges
 import math,numpy as np
 spec={'parameters':P,'oldEdges':old_edges.tolist(),'newEdges':new_edges.tolist(),'rotationAngle':float(np.mean(new_edges[13:18]-old_edges[13:18]))}
 (P24/'projection-spec-v24.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
 code=(P24/'browser-geometry.js').read_text(encoding='utf-8')+'\n'+(P24/'build_bays.js').read_text(encoding='utf-8')+'\n'+(P24/'build_right.js').read_text(encoding='utf-8')+'\n'+(P24/'browser-apply.js').read_text(encoding='utf-8')
 for marker,value in [('__PROJECTION_SPEC_24__',json.dumps(spec)),('__BAY_FIT_24__',(P24/'bay-fit-v24.json').read_text(encoding='utf-8')),('__RIGHT_FIT_24__',(P24/'right-fit-v24.json').read_text(encoding='utf-8'))]:code=code.replace(marker,value)
 hook='const staticParts=[hotel,dome,floorGroup,rubble].map(bake).reduce((a,b)=>a+b,0);'
 assert hook in s;s=s.replace(hook,hook+'\n'+code)
 lights=json.loads((P24/'integration-v24.json').read_text(encoding='utf-8'))['lights']
 if '--movie-steel' in sys.argv:
  for light in lights:
   if light['name']=='Soft courtyard fill on the movie facade v22':
    light['position']=[t+2.5*(p-t) for p,t in zip(light['position'],light['target'])];light['dimensions']=[v*2.5 for v in light['dimensions']];light['powerWatts']*=6.25
 environment=(P24/'browser-environment.js').read_text(encoding='utf-8').replace('__LIGHTS_24__',json.dumps(lights))
 doorlight=(R/'night-calibration-v19/browser-door-light.js').read_text(encoding='utf-8')
 s=s.replace('const characterAsset=await new Promise',environment+'\n'+doorlight+'\n    const characterAsset=await new Promise')
 s=s.replace('hinge.rotation.y=angle;', 'hinge.rotation.y=angle;doorwayDaylight.intensity=.48*Math.max(0,Math.min(1,angle/1.55));')
 fov=math.degrees(2*math.atan(18/P['lensMm']));distance=P['distance']/math.cos(P['pitch']);target=[P['cameraX'],P['cameraZ']-P['distance']*math.tan(P['pitch']),0]
 close=f"azimuth:0,elevation:{P['pitch']},radius:{distance},target:{json.dumps(target)}"
 s=s.replace('azimuth:0,elevation:.01,radius:4.04,target:[.18,1.94,0]',close)
 s=s.replace('new T.PerspectiveCamera(62,',f'new T.PerspectiveCamera({fov},')
 # Reference close view uses the fitted lens; other presets retain a usable
 # wide field of view for interactive navigation and head inspection.
 s=s.replace('function updateCamera(){',f"function updateCamera(){{camera.fov=state.view==='close'?{fov}:62;camera.updateProjectionMatrix();")
 s=s.replace("if(name==='aerial')Object.assign(state,{azimuth:.45,elevation:1.18,radius:52,target:[0,1.5,0]});",f"if(name==='aerial')Object.assign(state,{{azimuth:.45,elevation:.8,radius:68,target:[{P['courtyardX']},3,{-P['courtyardY']}]}});")
 s=s.replace('suzume-local-view','suzume-movie-view-v24')
 s=s.replace('<script src="GLTFLoader.js"></script>','<script src="GLTFLoader.js"></script>\n<script src="RectAreaLightUniformsLib.js"></script>')
 header=header.replace('混元人物 / 独立头部重建 · v17','镜头与完整庭院联合校准 · v24')
 footer='<footer>镜头、整圈庭院和楼层高度已联合校准；人物头模、脚部修正与穿门分隔保留。当前仍是复刻对照版，尚未达到一比一；网页运行效果待复测。<br><a href="candidate-v23.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v24.html'
 if '--movie-steel' in sys.argv:
  S25=R/'movie-steel-v25'
  steel=(S25/'build_steel.js').read_text(encoding='utf-8')+'\n'+(S25/'browser-steel.js').read_text(encoding='utf-8').replace('__STEEL_FIT_25__',(S25/'steel-fit-v25.json').read_text(encoding='utf-8'))
  s=s.replace('const characterAsset=await new Promise',steel+'\n    const characterAsset=await new Promise')
  s=s.replace('suzume-movie-view-v24','suzume-movie-view-v25')
  header=header.replace('镜头与完整庭院联合校准 · v24','电影钢架与实体工字梁重建 · v25')
  footer='<footer>主柱、可见弯梁与细拉杆按电影参照重建；钢架采用实体工字截面，环形结构、底板和锚栓可自由查看。隐藏结构仍为推定，尚未达到一比一；网页运行效果待复测。<br><a href="candidate-v24.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
  output=out/'candidate-v25.html'
elif any(mode in sys.argv for mode in ['--night-light','--movie','--movie-windows','--movie-material','--movie-bays']):
 s=s.replace('const characterAsset=await new Promise', (R/'night-calibration-v19'/'browser-door-light.js').read_text(encoding='utf-8')+'\n    const characterAsset=await new Promise')
 s=s.replace('hinge.rotation.y=angle;', 'hinge.rotation.y=angle;doorwayDaylight.intensity=.48*Math.max(0,Math.min(1,angle/1.55));')
 header=header.replace('混元人物 / 独立头部重建 · v17','混元人物 / 门内光照校准 · v19')
 footer='<footer>门内光照校准版：开门时，日光进入异世界并照亮迈入的人物和近处花草。原生场景已渲染，网页光照待复测。<br><a href="index.html">返回原场景</a> · <a href="../index.html">对比渲染与模型文件</a></footer></main></html>'
 output=out/'candidate-v19.html'
 if any(mode in sys.argv for mode in ['--movie','--movie-windows','--movie-material','--movie-bays']):
  movie_code=(R/'movie-calibration-v20'/'browser-courtyard.js').read_text(encoding='utf-8').replace('__MOVIE_COURTYARD_FIT__',(R/'movie-calibration-v20'/'courtyard-fit-v20.json').read_text(encoding='utf-8'))
  s=s.replace('const characterAsset=await new Promise',movie_code+'\n    const characterAsset=await new Promise')
  s=s.replace('clamp(state.radius,3.5,80)','clamp(state.radius,3.5,260)')
  s=s.replace("if(name==='aerial')Object.assign(state,{azimuth:.45,elevation:1.18,radius:52,target:[0,1.5,0]});", "if(name==='aerial')Object.assign(state,{azimuth:.6,elevation:.7,radius:190,target:[16,8,39]});")
  s=s.replace("localStorage.getItem('suzume-local-view')","localStorage.getItem('suzume-movie-view-v20')").replace("localStorage.setItem('suzume-local-view'","localStorage.setItem('suzume-movie-view-v20'")
  header=header.replace('混元人物 / 门内光照校准 · v19','电影立面校准 / 对照场景 · v20')
  footer='<footer>电影镜头对照版：建筑距离、窗边与立柱位置已重新校准，完整环形结构可自由旋转。建筑尺寸仍为推定，当前未达到一比一；网页效果待复测。<br><a href="index.html">原场景</a> · <a href="../index.html">对比渲染与完整模型</a></footer></main></html>'
  output=out/'candidate-v20.html'
  if any(mode in sys.argv for mode in ['--movie-windows','--movie-material','--movie-bays']):
   W21=R/'movie-windows-v21'
   replace_code=(W21/'build_bay.js').read_text(encoding='utf-8')+'\n'+(W21/'browser-replace-bay.js').read_text(encoding='utf-8').replace('__MOVIE_WINDOW_FIT_21__',(W21/'window-fit-v21.json').read_text(encoding='utf-8'))
   if '--movie-material' in sys.argv or '--movie-bays' in sys.argv:
    F22=R/'movie-material-v22'
    replace_code=(F22/'browser-facade.js').read_text(encoding='utf-8')+'\n'+replace_code
    bay_hook="newMovieBay21.name='Circular ruined hotel with exterior entrance';"
    assert bay_hook in replace_code
    replace_code=replace_code.replace(bay_hook,"refineMovieBay22(T,newMovieBay21,{sunWall,cornice,windowMat,mullionMat},movieWindowFit21);\n    "+bay_hook)
   if '--movie-bays' in sys.argv:
    B23=R/'movie-bays-v23'
    bays_code=(B23/'build_bays.js').read_text(encoding='utf-8')+'\n'+(B23/'browser-replace-bays.js').read_text(encoding='utf-8').replace('__MOVIE_BAY_FIT_23__',(B23/'bay-fit-v23.json').read_text(encoding='utf-8'))
    replace_code=bays_code+'\n'+replace_code
    old="if(o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))movieMesh(o,'hotel');"
    new="if(o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh')||o.name.startsWith('Movie rebuilt left and central bays v23 solid mesh'))movieMesh(o,'hotel');"
    assert old in s;s=s.replace(old,new)
   hook='const staticParts=[hotel,dome,floorGroup,rubble].map(bake).reduce((a,b)=>a+b,0);'
   assert hook in s;s=s.replace(hook,hook+'\n'+replace_code)
   header=header.replace('电影立面校准 / 对照场景 · v20','电影圆窗与立面重建 · v21')
   footer='<footer>电影窗型对照版：右侧圆窗、方窗、墙体和檐口已按参照重建，洞口和后方房间均为三维结构。当前未达到一比一；网页效果待复测。<br><a href="candidate-v20.html">上一版立面对照</a> · <a href="../index.html">原生渲染与模型文件</a></footer></main></html>'
   output=out/'candidate-v21.html'
   if '--movie-material' in sys.argv or '--movie-bays' in sys.argv:
    light=json.loads((F22/'integration-v22.json').read_text(encoding='utf-8'))['fillLight']
    fill=(F22/'browser-fill.js').read_text(encoding='utf-8').replace('__MOVIE_FACADE_LIGHT_22__',json.dumps(light))
    s=s.replace('const characterAsset=await new Promise',fill+'\n    const characterAsset=await new Promise')
    s=s.replace('<script src="GLTFLoader.js"></script>','<script src="GLTFLoader.js"></script>\n<script src="RectAreaLightUniformsLib.js"></script>')
    s=s.replace('suzume-movie-view-v20','suzume-movie-view-v22')
    header=header.replace('电影圆窗与立面重建 · v21','电影墙面与光照校准 · v22')
    footer='<footer>右侧墙面已修正檐口投影、材质和补光。完整模型可旋转，窗洞和房间均为实体结构；网页光照仍待复测，尚未达到一比一。<br><a href="candidate-v21.html">上一版窗型对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
    output=out/'candidate-v22.html'
    if '--movie-bays' in sys.argv:
     bays_lighting=(B23/'browser-lighting.js').read_text(encoding='utf-8').replace('__MOVIE_BAYS_LIGHTING_23__',(B23/'lighting-v23.json').read_text(encoding='utf-8'))
     s=s.replace('const characterAsset=await new Promise',bays_lighting+'\n    const characterAsset=await new Promise')
     header=header.replace('电影墙面与光照校准 · v22','电影窗组与实体立面重建 · v23')
     footer='<footer>四段建筑已重新生成，六个可见窗洞按电影参照校准；房间、侧墙和屋顶保持完整。上层建筑及整体比例仍需校准，尚未达到一比一；网页交互待复测。<br><a href="candidate-v22.html">上一版立面对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
     s=s.replace('suzume-movie-view-v22','suzume-movie-view-v23')
     output=out/'candidate-v23.html'
elif '--clean-head' in sys.argv:
 s=s.replace('suzume-posed-v17.gltf','suzume-posed-v18.gltf')
 s=s.replace("source:'Hunyuan 3D 3.1 body and independent Hunyuan 2mv four-view head',revision:17", "source:'Hunyuan 3D 3.1 body and reference-driven mathematical head candidate',revision:18")
 s=s.replace('independent head with neck blending','mathematical head with neck blending')
 header=header.replace('混元人物 / 独立头部重建 · v17','混元身体 / 几何头部对比 · v18')
 footer='<footer>几何头部对比版：脸部、眼睛、发束与发卡可独立编辑；人物神态仍在校准。<br><a href="index.html">返回混元头模版本</a> · <a href="../index.html">四视图与对比文件</a> · <a href="suzume-posed-v18.glb" download>下载当前人物 GLB</a></footer></main></html>'
 output=out/'candidate-v18.html'
else:
 footer=footer.replace('人物四视图与文件</a>', '人物四视图与文件</a> · <a href="candidate-v18.html">几何头部对比版</a>')
 output=out/('candidate-v17.html' if '--candidate' in sys.argv else 'index.html')
if '--movie-shore' in sys.argv:
 assert '--movie-steel' in sys.argv,'Shore reconstruction extends the complete steel candidate.'
 S26=R/'movie-shore-v26'
 shore=(S26/'build_shore.js').read_text(encoding='utf-8')+'\n'+(S26/'browser-shore.js').read_text(encoding='utf-8').replace('__SHORE_FIT_26__',(S26/'shore-fit-v26.json').read_text(encoding='utf-8'))
 s=s.replace('const characterAsset=await new Promise',shore+'\n    const characterAsset=await new Promise')
 s=s.replace('suzume-movie-view-v25','suzume-movie-view-v26')
 header=header.replace('电影钢架与实体工字梁重建 · v25','电影岸台与管道重建 · v26')
 footer='<footer>岸台采用带厚度的倾斜断板，管道有实体管壁与中空断口；完整庭院、人物与穿门分隔保留。场景尺寸仍含推定，尚未达到一比一；网页运行效果待复测。<br><a href="candidate-v25.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v26.html'
if '--movie-lighting' in sys.argv:
 assert '--movie-shore' in sys.argv,'Lighting calibration extends the complete shore candidate.'
 L27=R/'movie-lighting-v27'
 lighting=(L27/'browser-lighting.js').read_text(encoding='utf-8').replace('__LIGHTING_SPEC_27__',(L27/'lighting-spec-v27.json').read_text(encoding='utf-8'))
 s=s.replace('const characterAsset=await new Promise',lighting+'\n    const characterAsset=await new Promise')
 s=s.replace('suzume-movie-view-v26','suzume-movie-view-v27')
 header=header.replace('电影岸台与管道重建 · v26','电影日光与阴影校准 · v27')
 footer='<footer>侧向日光、阴影区和右侧补光重新校准；岸台、管道、人物和穿门分隔保留。尚未达到一比一，网页光照、天空色彩和旋转交互待复测。<br><a href="candidate-v26.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v27.html'
if '--movie-surfaces' in sys.argv:
 assert '--movie-lighting' in sys.argv,'Surface calibration extends the reviewed lighting candidate.'
 S28=R/'movie-surfaces-v28'
 surface_spec=json.loads((S28/'surface-spec-v28.json').read_text(encoding='utf-8'));surface_spec['newEdges']=new_edges.tolist()
 surface_code=(S28/'browser-surfaces.js').read_text(encoding='utf-8')+'\nconst surfaceSpec28='+json.dumps(surface_spec)+';\n'
 surface_code+='''const loadSurface28=url=>new Promise((resolve,reject)=>new T.TextureLoader().load(url,t=>{t.encoding=T.LinearEncoding;t.minFilter=T.LinearFilter;t.magFilter=T.LinearFilter;t.generateMipmaps=false;resolve(t);},undefined,reject));
    const [filmSource28,filmMask28]=await Promise.all([loadSurface28('../movie-surfaces-v28/reference-opening.jpg'),loadSurface28('../movie-surfaces-v28/surface-validity-mask-v28.png')]);
    const filmPainter28=createFilmSurfacePainter28(T,surfaceSpec28,filmSource28,filmMask28);root.surfaceEvidence28=filmPainter28.evidence;
'''
 hook='const projectionSpec24='
 assert hook in s;s=s.replace(hook,surface_code+'\n'+hook,1)
 hook='o.matrixAutoUpdate=false;o.matrix.copy(o.parent.matrixWorld).invert();'
 assert hook in s;s=s.replace(hook,hook+'filmPainter28.decorate(o,index,gi);',1)
 hook="for(const [mat,gs] of batches){const g=new T.BufferGeometry();for(const name of ['position','normal','uv']){const size=name==='uv'?2:3,"
 replacement="for(const [mat,gs] of batches){const g=new T.BufferGeometry();const names=['position','normal','uv'];if(gs.some(q=>q.attributes.filmEligible28)){names.push('filmEligible28');for(const q of gs)if(!q.attributes.filmEligible28)q.setAttribute('filmEligible28',new T.Float32BufferAttribute(new Float32Array(q.attributes.position.count),1));}for(const name of names){const size=name==='filmEligible28'?1:name==='uv'?2:3,"
 assert hook in s;s=s.replace(hook,replacement,1)
 s=s.replace('suzume-movie-view-v27','suzume-movie-view-v28')
 header=header.replace('电影日光与阴影校准 · v27','电影墙面色彩与污迹校准 · v28')
 footer='<footer>参照色彩固定在真实墙面与石材上，保留完整窗洞、房间和自由旋转视角。前景遮挡区域继续使用原材质；整体仍未达到一比一，网页显示待复测。<br><a href="candidate-v27.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v28.html'
if '--movie-water' in sys.argv:
 assert '--movie-surfaces' in sys.argv,'Water refinement extends the physical wall surface candidate.'
 W29=R/'movie-water-v29'
 water_code=(W29/'browser-water.js').read_text(encoding='utf-8')+'\nconst waterSpec29='+(W29/'water-spec-v29.json').read_text(encoding='utf-8')+';\napplyMovieWater29(T,scene,water,root,waterSpec29,noiseGLSL);\n'
 s=s.replace('const characterAsset=await new Promise',water_code+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-movie-view-v28','suzume-movie-view-v29')
 header=header.replace('电影墙面色彩与污迹校准 · v28','电影浅水与水底校准 · v29')
 footer='<footer>浅水反射、透射与水底石板重新校准，保留真实场景倒影和完整三维几何。细波光、夜云与人物仍需修整；网页显示和跨引擎色彩待复测，尚未达到一比一。<br><a href="candidate-v28.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v29.html'
if '--movie-night' in sys.argv:
 assert '--movie-water' in sys.argv,'Night reconstruction extends the reviewed shallow-water candidate.'
 N30=R/'movie-night-v30'
 night_code=(N30/'browser-night.js').read_text(encoding='utf-8')+'\nconst nightSpec30='+(N30/'night-spec-v30.json').read_text(encoding='utf-8')+';\napplyMovieNight30(T,nightScene,root,nightSpec30);\n'
 s=s.replace('const characterAsset=await new Promise',night_code+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-movie-view-v29','suzume-movie-view-v30')
 header=header.replace('电影浅水与水底校准 · v29','电影夜空与空间云层校准 · v30')
 footer='<footer>门内夜空与三维云层重新建模，保留独立头模、脚部修正和跨门分区。云体背面及纵深由参照推定，整体仍未达到一比一；网页显示待复测。<br><a href="candidate-v29.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v30.html'
if '--movie-terrain' in sys.argv:
 assert '--movie-night' in sys.argv,'Terrain reconstruction extends the spatial night candidate.'
 F31=R/'movie-terrain-v31'
 terrain_code=(F31/'browser-terrain.js').read_text(encoding='utf-8')+'\nconst terrainSpec31='+(F31/'terrain-spec-v31.json').read_text(encoding='utf-8')+';\n'
 terrain_code+="const terrainBuffers31=await Promise.all(['ground-world-v31.bin','extension-vertices-v31.bin','extension-indices-v31.bin'].map(async name=>{const response=await fetch('../movie-terrain-v31/'+name);if(!response.ok)throw Error('Terrain resource unavailable');return response.arrayBuffer();}));\nconst renderNight31=applyMovieTerrain31(T,nightScene,renderer,root,terrainSpec31,terrainBuffers31);\n"
 s=s.replace('const characterAsset=await new Promise',terrain_code+'\n    const characterAsset=await new Promise',1)
 assert s.count('renderer.render(nightScene,camera)')==3 # One in helper, two original render paths.
 # Replace original call sites only; the helper must keep its base-scene render.
 s=s.replace('renderer.setRenderTarget(null);renderer.render(nightScene,camera);','renderer.setRenderTarget(null);renderNight31(camera);')
 s=s.replace('renderer.setRenderTarget(portalTarget);renderer.render(nightScene,camera);','renderer.setRenderTarget(portalTarget);renderNight31(camera);')
 s=s.replace('renderer.setRenderTarget(portalReflectionTarget);renderer.render(nightScene,reflectionCam);','renderer.setRenderTarget(portalReflectionTarget);renderNight31(reflectionCam);')
 s=s.replace('if(!root.isConnected){renderer.dispose();','if(!root.isConnected){renderNight31.dispose();renderer.dispose();')
 s=s.replace('suzume-movie-view-v30','suzume-movie-view-v31')
 header=header.replace('电影夜空与空间云层校准 · v30','电影远景地形与薄雾校准 · v31')
 footer='<footer>远景坡线按参照重建，并补充连续地形与空间薄雾；近处花草、人物和穿门分区保留。远景深度及隐藏部分仍为推定，整体尚未达到一比一；网页显示待复测。<br><a href="candidate-v30.html">上一版对照</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v31.html'
if '--movie-door' in sys.argv:
 assert '--movie-terrain' in sys.argv,'Rigid door extends the reviewed terrain candidate.'
 D32=R/'movie-door-v32'
 door_code=(D32/'browser-door.js').read_text(encoding='utf-8')+'\nmakeDoorLeafRigid32(T,hinge);makeDoorLeafRigid32(T,nightHinge);\nroot.doorRigEvidence32={rigid:true,revision:32,handRetargeted:true};\n'
 s=s.replace('const characterAsset=await new Promise',door_code+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-posed-v17.gltf','character-v32/suzume-posed-v32.gltf')
 s=s.replace('suzume-movie-view-v31','suzume-movie-view-v32')
 s=s.replace("pose:'v16 foot clearance and editable 20-bone rig preserved; independent head with neck blending'","pose:'v32 rigid door and retargeted right grip; v16 feet and independent v17 head preserved'")
 header=header.replace('电影远景地形与薄雾校准 · v31','刚性门板与握门姿态修正 · v32')
 footer='<footer>门板开合时保持固定尺寸，右手随门把手重新定位；独立头模、脚部间隙和穿门分区保留。手指与人物造型仍需细化，尚未达到一比一；网页显示待复测。<br><a href="candidate-v31.html">上一版对照</a> · <a href="character-v32/suzume-posed-v32.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v32.html'
if '--movie-hair' in sys.argv:
 assert '--movie-door' in sys.argv,'Ponytail refinement extends the rigid door and retargeted grip.'
 s=s.replace('character-v32/suzume-posed-v32.gltf','character-v33/suzume-posed-v33.gltf')
 s=s.replace('suzume-movie-view-v32','suzume-movie-view-v33')
 s=s.replace('v32 rigid door and retargeted right grip; v16 feet and independent v17 head preserved','v33 extended Hunyuan ponytail; v32 rigid door and grip; v16 feet preserved')
 header=header.replace('刚性门板与握门姿态修正 · v32','混元马尾长度与空间位置校准 · v33')
 footer='<footer>马尾沿现有三维发束延长，并根据上衣背面调整间隙；脸部、发卡、脚部和握门姿态保留。整体仍未达到一比一，网页显示待复测。<br><a href="candidate-v32.html">上一版对照</a> · <a href="character-v33/suzume-posed-v33.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v33.html'
if '--movie-head' in sys.argv:
 assert '--movie-door' in sys.argv and '--movie-hair' not in sys.argv,'Independent head uses the v32 body; the fused v33 trial is rejected.'
 s=s.replace('character-v32/suzume-posed-v32.gltf','character-v34/suzume-posed-v34.gltf')
 s=s.replace('suzume-movie-view-v32','suzume-movie-view-v34')
 s=s.replace("source:'Hunyuan 3D 3.1 body and independent Hunyuan 2mv four-view head',revision:17","source:'Hunyuan 3D 3.1 body and reference-driven mathematical head with independent closed ponytail locks',revision:34")
 s=s.replace('v32 rigid door and retargeted right grip; v16 feet and independent v17 head preserved','v34 mathematical head and six closed ponytail locks; v32 rigid door, grip and feet preserved')
 header=header.replace('刚性门板与握门姿态修正 · v32','独立头部与实体发束重建 · v34')
 footer='<footer>身体沿用混元模型，头部采用独立可编辑的几何部件，马尾由六束封闭实体组成。脚部、握门姿态和穿门分区保留；整体仍未达到一比一，网页显示待复测。<br><a href="candidate-v32.html">混元头模对照</a> · <a href="character-v34/suzume-posed-v34.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v34.html'
if '--movie-head-shape' in sys.argv:
 assert '--movie-head' in sys.argv,'Head silhouette refinement extends the independent mathematical head.'
 s=s.replace('character-v34/suzume-posed-v34.gltf','character-v35/suzume-posed-v35.gltf')
 s=s.replace('suzume-movie-view-v34','suzume-movie-view-v35')
 s=s.replace("source:'Hunyuan 3D 3.1 body and reference-driven mathematical head with independent closed ponytail locks',revision:34","source:'Hunyuan 3D 3.1 body and mathematical head; calibrated placement and overlapping solid ponytail volumes',revision:35")
 s=s.replace('v34 mathematical head and six closed ponytail locks; v32 rigid door, grip and feet preserved','v35 head placement and ponytail silhouette; v32 rigid door, grip and feet preserved')
 header=header.replace('独立头部与实体发束重建 · v34','头部比例与马尾轮廓校准 · v35')
 footer='<footer>头部位置、后脑宽度和马尾轮廓已按电影主机位校准。完整几何仍可自由旋转，进入门后的部分使用异世界分区。面部神态、材质与环境仍在重建，网页显示待复测。<br><a href="candidate-v34.html">上一版对照</a> · <a href="character-v35/suzume-posed-v35.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v35.html'
if '--movie-face' in sys.argv:
 assert '--movie-head-shape' in sys.argv,'Facial refinement retains the calibrated v35 head and ponytail.'
 s=s.replace('character-v35/suzume-posed-v35.gltf','character-v36/suzume-posed-v36.gltf')
 s=s.replace('suzume-movie-view-v35','suzume-movie-view-v36')
 s=s.replace("source:'Hunyuan 3D 3.1 body and mathematical head; calibrated placement and overlapping solid ponytail volumes',revision:35","source:'Hunyuan 3D 3.1 body and mathematical head; official-reference face proportions and solid ponytail',revision:36")
 s=s.replace('v35 head placement and ponytail silhouette; v32 rigid door, grip and feet preserved','v36 face proportions, eyes, nose and frontal hairline; v35 ponytail and v32 body preserved')
 header=header.replace('头部比例与马尾轮廓校准 · v35','五官比例与刘海校准 · v36')
 footer='<footer>按官方人物图调整五官比例、下颌和前额刘海，头部仍为完整三维几何。马尾、脚部、握门姿态和穿门分区保留；神态、材质与环境尚未达到一比一，网页显示待复测。<br><a href="candidate-v35.html">上一版对照</a> · <a href="character-v36/suzume-posed-v36.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v36.html'
if '--movie-collar' in sys.argv:
 assert '--movie-face' in sys.argv,'Collar repair retains the official-reference face refinement.'
 s=s.replace('character-v36/suzume-posed-v36.gltf','character-v37/suzume-posed-v37.gltf')
 s=s.replace('suzume-movie-view-v36','suzume-movie-view-v37')
 s=s.replace("source:'Hunyuan 3D 3.1 body and mathematical head; official-reference face proportions and solid ponytail',revision:36","source:'Hunyuan body with repaired collar and mathematical head with blended neck attachment; official-reference face and solid ponytail',revision:37")
 s=s.replace('v36 face proportions, eyes, nose and frontal hairline; v35 ponytail and v32 body preserved','v37 smooth collar, clean fabric edge and blended neck attachment; v36 face and v32 feet/grip retained')
 header=header.replace('五官比例与刘海校准 · v36','领口与头颈衔接修复 · v37')
 footer='<footer>领口切边已重建为平顺曲线，布料部分带实体包边，并修正肤色残留与颈部底端衔接。五官、马尾、脚部和握门姿态保留；整体尚未达到一比一，网页显示待实测。<br><a href="candidate-v36.html">上一版对照</a> · <a href="character-v37/suzume-posed-v37.glb" download>下载当前人物</a> · <a href="../index.html">原生渲染与完整模型</a></footer></main></html>'
 output=out/'candidate-v37.html'
if '--poster' in sys.argv:
 assert not any(arg.startswith('--movie') for arg in sys.argv), 'Poster and movie environment variants must remain independent.'
 initial="let state={open:true,motion:false,azimuth:0,elevation:.01,radius:4.04,target:[.18,1.94,0],view:'close'};"
 assert initial in s
 s=s.replace(initial,"let state={open:false,motion:false,azimuth:posterComposition.azimuth,elevation:posterComposition.elevation,radius:posterComposition.radius,target:[...posterComposition.target],view:'poster'};")
 s=s.replace('suzume-local-view','suzume-poster-view-v38')
 s=s.replace('suzume-posed-v17.gltf','character-v37/suzume-posed-v37.gltf')
 rigid=(R/'movie-door-v32/browser-door.js').read_text(encoding='utf-8')+'\nmakeDoorLeafRigid32(T,hinge);makeDoorLeafRigid32(T,nightHinge);\n'
 s=s.replace('const characterAsset=await new Promise',rigid+'\n    const characterAsset=await new Promise',1)
 s=s.replace("source:'Hunyuan 3D 3.1 body and independent Hunyuan 2mv four-view head',revision:17", "source:'Hunyuan 3.1 body with repaired collar and independent mathematical head',revision:37")
 s=s.replace("pose:'v16 foot clearance and editable 20-bone rig preserved; independent head with neck blending'", "pose:'v37 collar and head; v32 rigid door and grip; corrected feet retained'")
 header=header.replace('铃芽之旅 · 门的两侧','铃芽之旅 · 关门海报').replace('混元人物 / 独立头部重建 · v17','独立海报环境 · v38')
 footer='<footer>按关门海报重建的可旋转庭院。电影开门场景单独保留，几何纵深与隐藏细节仍在校准。<br><a href="candidate-v37.html">查看电影开门场景</a> · <a href="../poster-v38/Suzume_dual_scene_v38.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v38.html'
if '--poster-steel' in sys.argv:
 assert '--poster' in sys.argv,'Observed poster steel uses the independent poster environment.'
 steel=(R/'poster-steel-v39/browser-steel.js').read_text(encoding='utf-8')+'\nawait applyPosterSteel39(T,scene,root);\n'
 s=s.replace('const characterAsset=await new Promise',steel+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-poster-view-v38','suzume-poster-view-v39')
 header=header.replace('独立海报环境 · v38','海报折梁与立柱重建 · v39')
 footer='<footer>右侧折断钢梁、弧形托架、细拉杆和立柱已按海报轮廓重建。完整庭院可自由旋转，深度、锈蚀、水纹与建筑细节仍在校准。<br><a href="poster-v38.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-steel-v39/Suzume_dual_scene_steel_v39.blend">下载双场景 Blender 模型</a> · <a href="../index.html">重建记录</a></footer></main></html>'
 output=out/'poster-v39.html'
if '--poster-water' in sys.argv:
 assert '--poster-steel' in sys.argv and '--poster' in sys.argv,'Water v40 extends the independent poster steel scene.'
 water40=(R/'poster-water-v40/browser-water.js').read_text(encoding='utf-8')+'\nconst posterWaterSpec40='+(R/'poster-water-v40/water-spec-v40.json').read_text(encoding='utf-8')+';\napplyPosterWater40(T,water,root,posterWaterSpec40);\n'
 s=s.replace('const characterAsset=await new Promise',water40+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-poster-view-v39','suzume-poster-view-v40')
 header=header.replace('海报折梁与立柱重建 · v39','海报水面与倒影校准 · v40')
 footer='<footer>水面使用实时场景倒影、浅水透射与不规则波纹。三维结构可自由旋转，原作波光、建筑细节与远云仍在校准。<br><a href="poster-v39.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-water-v40/Suzume_dual_scene_water_v40.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v40.html'
if '--poster-clouds' in sys.argv:
 assert '--poster-water' in sys.argv and '--poster-steel' in sys.argv and '--poster' in sys.argv,'Cloud v41 extends the reviewed independent poster environment.'
 clouds41=(R/'poster-clouds-v41/browser-clouds.js').read_text(encoding='utf-8')+'\nawait applyPosterClouds41(T,scene,root,cloudGeometries);\n'
 s=s.replace('const characterAsset=await new Promise',clouds41+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-poster-view-v40','suzume-poster-view-v41')
 header=header.replace('海报水面与倒影校准 · v40','海报远云轮廓与细节重建 · v41')
 footer='<footer>远云已按海报轮廓重建为完整云体，细化起伏与表面颜色。庭院可自由旋转，遮挡后的云形、建筑和人物细节仍在校准。<br><a href="poster-v40.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-clouds-v41/Suzume_dual_scene_clouds_v41.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v41.html'
if '--poster-horizon' in sys.argv:
 assert '--poster-clouds' in sys.argv,'The continuous bank extends the v41 closed cloud set.'
 previous='await applyPosterClouds41(T,scene,root,cloudGeometries);'
 assert s.count(previous)==1
 horizon42=(R/'poster-horizon-v42/browser-clouds.js').read_text(encoding='utf-8')+'\nawait applyPosterHorizon42(T,scene,root,cloudGeometries);'
 s=s.replace(previous,horizon42)
 s=s.replace('suzume-poster-view-v41','suzume-poster-view-v42')
 header=header.replace('海报远云轮廓与细节重建 · v41','门上方低云补全 · v42')
 footer='<footer>门上方被旧遮罩裁掉的低云已补为连续云体，可自由旋转查看。更低处的云层、建筑和人物细节仍在校准。<br><a href="poster-v41.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-horizon-v42/Suzume_dual_scene_horizon_v42.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v42.html'
if '--poster-lower-clouds' in sys.argv:
 assert '--poster-horizon' in sys.argv,'The lower strata extend the v42 cloud set.'
 lower43=(R/'poster-lower-clouds-v43/browser-clouds.js').read_text(encoding='utf-8')+'\nawait applyPosterLowerClouds43(T,scene,root,cloudGeometries);\n'
 s=s.replace('const characterAsset=await new Promise',lower43+'\n    const characterAsset=await new Promise',1)
 s=s.replace('suzume-poster-view-v42','suzume-poster-view-v43')
 header=header.replace('门上方低云补全 · v42','地平线层云重建 · v43')
 footer='<footer>门后补入三层灰蓝色实体云层，恢复地平线附近的明暗层次。完整庭院可自由旋转，隐藏形状、建筑和人物细节仍在校准。<br><a href="poster-v42.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-lower-clouds-v43/Suzume_dual_scene_lower_clouds_v43.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v43.html'
if '--poster-left-steel' in sys.argv:
 assert '--poster-lower-clouds' in sys.argv,'Left steel extends the latest independent poster scene.'
 previous='await applyPosterSteel39(T,scene,root);'
 assert s.count(previous)==1
 steel44=(R/'poster-left-steel-v44/browser-steel.js').read_text(encoding='utf-8')+'\nawait applyPosterSteel44(T,scene,root);'
 s=s.replace(previous,steel44).replace('suzume-poster-view-v43','suzume-poster-view-v44')
 header=header.replace('地平线层云重建 · v43','左侧钢架与断梁重建 · v44')
 footer='<footer>左侧立柱、断梁、弧形支架与吊杆已重建，并校正横梁高度。庭院可自由旋转，漆面、建筑和人物细节仍在校准。<br><a href="poster-v43.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-left-steel-v44/Suzume_dual_scene_left_steel_v44.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v44.html'
if '--poster-rooftops' in sys.argv:
 assert '--poster-left-steel' in sys.argv,'Rooftops extend the latest independent poster scene.'
 previous='await applyPosterSteel44(T,scene,root);'
 assert s.count(previous)==1
 rooftops45=(R/'poster-rooftops-v45/browser-rooftops.js').read_text(encoding='utf-8')+'\nawait applyPosterRooftops45(T,scene,root);'
 s=s.replace(previous,previous+'\n'+rooftops45).replace('suzume-poster-view-v44','suzume-poster-view-v45')
 header=header.replace('左侧钢架与断梁重建 · v44','屋顶设备轮廓重建 · v45')
 footer='<footer>左侧设备间、水箱、爬梯和管道已按参照重建。完整庭院可自由旋转，建筑门窗、风化和人物细节仍在校准。<br><a href="poster-v44.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v45.html'
if '--poster-railings' in sys.argv:
 assert '--poster-rooftops' in sys.argv,'Railings extend the latest independent poster scene.'
 previous='await applyPosterRooftops45(T,scene,root);'
 assert s.count(previous)==1
 rails46=(R/'poster-railings-v46/browser-railings.js').read_text(encoding='utf-8')+'\nawait applyPosterRailings46(T,scene,root);'
 s=s.replace(previous,rails46).replace('suzume-poster-view-v45','suzume-poster-view-v46')
 header=header.replace('屋顶设备轮廓重建 · v45','栏杆密度与藤蔓校准 · v46')
 footer='<footer>左侧栏杆的密度和上沿已重建，屋顶叶片缩小，原生模型的藤蔓颜色传递已修复。完整庭院可自由旋转，建筑与人物细节仍在校准。<br><a href="poster-v45.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-railings-v46/Suzume_dual_scene_railings_v46.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v46.html'
if '--poster-fascia' in sys.argv:
 assert '--poster-railings' in sys.argv,'Fascia extends the latest independent poster scene.'
 previous='await applyPosterRailings46(T,scene,root);'
 assert s.count(previous)==1
 fascia47=(R/'poster-fascia-v47/browser-fascia.js').read_text(encoding='utf-8')+'\nawait applyPosterFascia47(T,scene,root);'
 s=s.replace(previous,previous+'\n'+fascia47).replace('suzume-poster-view-v46','suzume-poster-view-v47')
 header=header.replace('栏杆密度与藤蔓校准 · v46','左侧檐口剖面校准 · v47')
 footer='<footer>左侧顶板边缘补入有厚度的灰蓝色檐口与滴水边。完整庭院可自由旋转，建筑与人物细节仍在校准。<br><a href="poster-v46.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-fascia-v47/Suzume_dual_scene_fascia_v47.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v47.html'
if '--poster-upper-windows' in sys.argv:
 assert '--poster-fascia' in sys.argv,'Upper windows extend the latest independent poster scene.'
 previous='await applyPosterFascia47(T,scene,root);'
 assert s.count(previous)==1
 windows48=(R/'poster-upper-windows-v48/browser-upper-windows.js').read_text(encoding='utf-8')+'\nawait applyPosterUpperWindows48(T,scene,root);'
 s=s.replace(previous,previous+'\n'+windows48).replace('suzume-poster-view-v47','suzume-poster-view-v48')
 header=header.replace('左侧檐口剖面校准 · v47','左侧高窗实体重建 · v48')
 footer='<footer>左侧高窗已重建真实开口、窗框和玻璃厚度，并清理窗后的旧隔墙。完整庭院可自由旋转，细节仍在校准。<br><a href="poster-v47.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-upper-windows-v48/Suzume_dual_scene_upper_windows_v48.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v48.html'
if '--poster-arches' in sys.argv:
 assert '--poster-upper-windows' in sys.argv,'Arches extend the latest independent poster scene.'
 previous='await applyPosterUpperWindows48(T,scene,root);'
 assert s.count(previous)==1
 arches49=(R/'poster-arches-v49/browser-arches.js').read_text(encoding='utf-8')+'\nawait applyPosterArches49(T,scene,root);'
 s=s.replace(previous,previous+'\n'+arches49).replace('suzume-poster-view-v48','suzume-poster-view-v49')
 header=header.replace('左侧高窗实体重建 · v48','尖拱与立面凹深重建 · v49')
 footer='<footer>左侧尖拱、小拱及下方檐线已重建为实体，清理高窗下沿的旧窗台遮挡。完整庭院可自由旋转，隐藏结构和细节仍在校准。<br><a href="poster-v48.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-arches-v49/Suzume_dual_scene_arches_v49.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v49.html'
if '--poster-lower-facade' in sys.argv:
 assert '--poster-arches' in sys.argv,'Lower facade extends the latest independent poster scene.'
 previous='await applyPosterArches49(T,scene,root);'
 assert s.count(previous)==1
 lower50=(R/'poster-lower-facade-v50/browser-lower-facade.js').read_text(encoding='utf-8')+'\nawait applyPosterLowerFacade50(T,scene,root);'
 s=s.replace(previous,previous+'\n'+lower50).replace('suzume-poster-view-v49','suzume-poster-view-v50')
 header=header.replace('尖拱与立面凹深重建 · v49','入口与下层门窗重建 · v50')
 footer='<footer>左侧入口、扇形窗、三组大窗和台阶已重建为实体，入口内地板与门槛衔接。完整庭院可自由旋转，隐藏结构和细节仍在校准。<br><a href="poster-v49.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-lower-facade-v50/Suzume_dual_scene_lower_facade_v50.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v50.html'
if '--poster-foreground' in sys.argv:
 assert '--poster-lower-facade' in sys.argv,'Foreground extends the latest independent poster scene.'
 previous='await applyPosterLowerFacade50(T,scene,root);'
 assert s.count(previous)==1
 foreground51=(R/'poster-foreground-v51/browser-foreground.js').read_text(encoding='utf-8')+'\nawait applyPosterForeground51(T,scene,root);'
 s=s.replace(previous,previous+'\n'+foreground51).replace('suzume-poster-view-v50','suzume-poster-view-v51')
 header=header.replace('入口与下层门窗重建 · v50','门前植物与旧物重建 · v51')
 footer='<footer>门前植物改为细枝小叶，补入残椅与弯管的立体结构。完整庭院可自由旋转，植物分布、表面磨损和隐藏结构仍在校准。<br><a href="poster-v50.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-foreground-v51/Suzume_dual_scene_foreground_v51.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v51.html'
if '--poster-ground' in sys.argv:
 assert '--poster-foreground' in sys.argv,'Ground extends the latest independent poster scene.'
 previous='await applyPosterForeground51(T,scene,root);'
 assert s.count(previous)==1
 ground52=(R/'poster-ground-v52/browser-ground.js').read_text(encoding='utf-8')+'\nawait applyPosterGround52(T,scene,root);'
 s=s.replace(previous,previous+'\n'+ground52).replace('suzume-poster-view-v51','suzume-poster-view-v52')
 header=header.replace('门前植物与旧物重建 · v51','浅岸与碎石重建 · v52')
 footer='<footer>左侧水边改为浅积土和不规则碎石，保留门前植物、残椅与完整庭院。可自由旋转查看，磨损、植被和未见结构仍在校准。<br><a href="poster-v51.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-ground-v52/Suzume_dual_scene_ground_v52.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v52.html'
if '--poster-low-rails' in sys.argv:
 assert '--poster-ground' in sys.argv,'Low fixtures extend the latest independent poster scene.'
 previous='await applyPosterGround52(T,scene,root);'
 assert s.count(previous)==1
 fixtures53=(R/'poster-low-rails-v53/browser-low-rails.js').read_text(encoding='utf-8')+'\nawait applyPosterLowRails53(T,scene,root);'
 s=s.replace(previous,previous+'\n'+fixtures53).replace('suzume-poster-view-v52','suzume-poster-view-v53')
 header=header.replace('浅岸与碎石重建 · v52','残缺低框架与管道支架 · v53')
 footer='<footer>左侧低框架和管道支架已补成实体，可自由旋转查看。磨损、植物和隐藏结构仍在校准。<br><a href="poster-v52.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-low-rails-v53/Suzume_dual_scene_low_rails_v53.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v53.html'
if '--poster-right-facade' in sys.argv:
 assert '--poster-low-rails' in sys.argv,'Right facade extends the latest independent poster scene.'
 previous='await applyPosterLowRails53(T,scene,root);'
 assert s.count(previous)==1
 right54=(R/'poster-right-facade-v54/browser-right-facade.js').read_text(encoding='utf-8')+'\nawait applyPosterRightFacade54(T,scene,root);'
 s=s.replace(previous,previous+'\n'+right54).replace('suzume-poster-view-v53','suzume-poster-view-v54')
 header=header.replace('残缺低框架与管道支架 · v53','右侧门窗与立面重建 · v54')
 footer='<footer>右侧拱门、窄拱窗、两扇与三扇长窗已按参照重建，可自由旋转查看。磨损、植物和隐藏结构仍在校准。<br><a href="poster-v53.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-right-facade-v54/Suzume_dual_scene_right_facade_v54.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v54.html'
if '--poster-right-arches' in sys.argv:
 assert '--poster-right-facade' in sys.argv,'Right arcade extends the latest independent poster scene.'
 previous='await applyPosterRightFacade54(T,scene,root);'
 assert s.count(previous)==1
 arches55=(R/'poster-right-arches-v55/browser-right-arches.js').read_text(encoding='utf-8')+'\nawait applyPosterRightArches55(T,scene,root);'
 s=s.replace(previous,previous+'\n'+arches55).replace('suzume-poster-view-v54','suzume-poster-view-v55')
 header=header.replace('右侧门窗与立面重建 · v54','右侧拱廊与檐线重建 · v55')
 footer='<footer>右侧大拱、小拱龛、尖拱和弯曲檐线已按参照重建，可自由旋转查看。隐藏结构、植物与表面磨损仍在校准。<br><a href="poster-v54.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-right-arches-v55/Suzume_dual_scene_right_arches_v55.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v55.html'
if '--poster-right-bow' in sys.argv:
 assert '--poster-right-arches' in sys.argv,'Right bow extends the latest independent poster scene.'
 previous='await applyPosterRightArches55(T,scene,root);'
 assert s.count(previous)==1
 bow56=(R/'poster-right-bow-v56/browser-right-bow.js').read_text(encoding='utf-8')+'\nawait applyPosterRightBow56(T,scene,root);'
 s=s.replace(previous,previous+'\n'+bow56).replace('suzume-poster-view-v55','suzume-poster-view-v56')
 header=header.replace('右侧拱廊与檐线重建 · v55','右侧弯梁轮廓与漆面校准 · v56')
 footer='<footer>右侧弯梁已按参照收薄截面并校准轮廓与漆面，可自由旋转查看。植物、遮挡区域材质和隐藏结构仍在校准。<br><a href="poster-v55.html">上一版海报</a> · <a href="candidate-v37.html">电影开门场景</a> · <a href="../poster-right-bow-v56/Suzume_dual_scene_right_bow_v56.blend">下载双场景 Blender 模型</a> · <a href="../index.html">渲染与重建记录</a></footer></main></html>'
 output=out/'poster-v56.html'
output.write_text(header+s+footer,encoding='utf-8')
for name,url in [('three.min.js','https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'),('GLTFLoader.js','https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js')]:
 if not (out/name).exists():
  response=requests.get(url,timeout=30);response.raise_for_status();(out/name).write_bytes(response.content)
print('LOCAL_VIEWER_BUILT',str(output),len(output.read_bytes()))
