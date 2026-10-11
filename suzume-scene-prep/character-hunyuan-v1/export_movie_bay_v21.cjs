const fs=require('fs'),path=require('path'),vm=require('vm');
const R=__dirname,O=path.join(R,'movie-windows-v21'),T=require(path.join(R,'viewer','three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'window-fit-v21.json'),'utf8'));
const specs={sunWall:[0xf2e6a6,.95,0,'stone'],cornice:[0xd7d4bd,.92,0,'stone'],damp:[0x708c83,1,0,'stone'],roomMat:[0x354947,1,0,'stone'],mullionMat:[0xa29c7e,.83,.12,'rust'],iron:[0x655448,.91,.3,'rust'],ironEdge:[0xa98962,.8,.28,'rust'],windowMat:[0x34576c,.59,.12,null,.65]};
const materials={};for(const [role,s]of Object.entries(specs)){materials[role]=new T.MeshStandardMaterial({color:s[0],roughness:s[1],metalness:s[2],opacity:s[4]||1,transparent:!!s[4]});materials[role].name=role;}
const context={T,scene:new T.Scene(),materials,fit};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(O,'build_bay.js'),'utf8')+'\nthis.group=buildMovieBay21(T,scene,materials,fit);',context);
const meshes=[];context.group.traverse(o=>{if(!o.isMesh)return;let g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);meshes.push({name:o.name,material:o.material.name,positions:Array.from(g.attributes.position.array),normals:Array.from(g.attributes.normal.array),uv:g.attributes.uv?Array.from(g.attributes.uv.array):null});});
const roleSpecs={};for(const [role,s] of Object.entries(specs))roleSpecs[role]={color:new T.Color(s[0]).convertSRGBToLinear().toArray(),roughness:s[1],metalness:s[2],texture:s[3],opacity:s[4]||1};
const result={revision:21,bayIndex:16,fit,materials:roleSpecs,meshes};fs.writeFileSync(path.join(O,'bay-geometry-v21.json'),JSON.stringify(result));console.log(JSON.stringify({meshes:meshes.length,vertices:meshes.reduce((s,m)=>s+m.positions.length/3,0),roof:fit.roofY}));
