const fs=require('fs'),path=require('path'),vm=require('vm');
const R=__dirname,O=path.join(R,'movie-projection-v24'),T=require(path.join(R,'viewer/three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'bay-fit-v24.json'),'utf8'));
const resources={stoneMap:null,rustMap:null,paintMap:null,brass:new T.MeshStandardMaterial({color:0xbda457,roughness:.46,metalness:.28}),moss:new T.MeshStandardMaterial({color:0x536b35,roughness:1})};
const context={T,scene:new T.Scene(),fit,resources};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(O,'build_bays.js'),'utf8')+'\nthis.group=buildMovieBays23(T,scene,fit,resources);',context);
const materials={},seen=new Map(),meshes=[];
context.group.traverse(o=>{
  if(!o.isMesh)return;
  let ancestor=o;while(ancestor&&!Number.isInteger(ancestor.userData.bayIndex23))ancestor=ancestor.parent;
  if(!ancestor)throw new Error('Mesh has no bay');
  if(!seen.has(o.material.uuid)){
    const m=o.material,key='material-'+seen.size;seen.set(m.uuid,key);
    materials[key]={color:m.color.clone().convertSRGBToLinear().toArray(),sourceHex:m.color.getHex(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,side:m.side};
  }
  const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);
  meshes.push({name:'Bay '+ancestor.userData.bayIndex23+' '+(o.name||'part '+meshes.length),bay:ancestor.userData.bayIndex23,role:o.userData.geometryRole23||null,material:seen.get(o.material.uuid),positions:Array.from(g.attributes.position.array),normals:Array.from(g.attributes.normal.array),uv:g.attributes.uv?Array.from(g.attributes.uv.array):null});
});
const result={revision:23,fit,materials,meshes};fs.writeFileSync(path.join(O,'bay-geometry-v24.json'),JSON.stringify(result));
console.log(JSON.stringify({objects:meshes.length,triangles:meshes.reduce((s,m)=>s+m.positions.length/9,0),materials:Object.keys(materials).length,lowerWalls:meshes.filter(m=>m.role==='lowerWall').map(m=>m.name)},null,2));
