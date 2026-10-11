const fs=require('fs'),path=require('path'),vm=require('vm');
const R=__dirname,O=path.join(R,'movie-shore-v26'),T=require(path.join(R,'viewer/three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'shore-fit-v26.json'),'utf8'));
const colors={concrete:0xa3af9c,bank:0x75877c,curb:0xa4b19d,rust:0x795342,rustDark:0x43362d};
const materials=Object.fromEntries(Object.entries(colors).map(([name,color])=>{const m=new T.MeshStandardMaterial({color,roughness:.96,metalness:name.startsWith('rust')?.12:0});m.name=name;return[name,m];}));
const c={T,scene:new T.Scene(),fit,materials};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(O,'build_shore.js'),'utf8')+'\nthis.group=buildMovieShore26(T,scene,fit,materials);',c);
const meshes=[];c.group.traverse(o=>{if(!o.isMesh)return;const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);meshes.push({name:o.name,material:o.material.name,metadata:o.userData,positions:Array.from(g.attributes.position.array),normals:Array.from(g.attributes.normal.array)});});
fs.writeFileSync(path.join(O,'shore-geometry-v26.json'),JSON.stringify({revision:26,fit,meshes}));console.log(JSON.stringify({parts:meshes.length,triangles:meshes.reduce((s,m)=>s+m.positions.length/9,0)}));
