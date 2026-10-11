const fs=require('fs'),path=require('path'),vm=require('vm');
const R=__dirname,O=path.join(R,'movie-steel-v25'),T=require(path.join(R,'viewer/three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'steel-fit-v25.json'),'utf8'));
const materials={steel:new T.MeshStandardMaterial({color:0x766048,roughness:.8,metalness:.4}),edge:new T.MeshStandardMaterial({color:0x776349,roughness:.72,metalness:.45}),concrete:new T.MeshStandardMaterial({color:0x77766d,roughness:.95})};
for(const [name,color]of Object.entries({vine:0x536238,leaf0:0x58752b,leaf1:0x70953c,leaf2:0xa1b359}))materials[name]=new T.MeshStandardMaterial({color,roughness:.90});
for(const [name,m]of Object.entries(materials))m.name=name;
const c={T,scene:new T.Scene(),fit,materials};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(O,'build_steel.js'),'utf8')+'\nthis.group=buildMovieSteel25(T,scene,fit,materials);',c);
const meshes=[];c.group.traverse(o=>{if(!o.isMesh)return;const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);meshes.push({name:o.name,material:o.material.name,metadata:o.userData,positions:Array.from(g.attributes.position.array),normals:Array.from(g.attributes.normal.array),uv:g.attributes.uv?Array.from(g.attributes.uv.array):null});});
const result={revision:25,fit,meshes};fs.writeFileSync(path.join(O,'steel-geometry-v25.json'),JSON.stringify(result));console.log(JSON.stringify({parts:meshes.length,triangles:meshes.reduce((s,m)=>s+m.positions.length/9,0),columns:meshes.filter(m=>m.metadata.kind==='column').length,bows:meshes.filter(m=>m.metadata.kind==='observed-bow').length}));
