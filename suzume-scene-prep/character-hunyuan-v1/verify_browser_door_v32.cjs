const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-door-v32'),T=require(path.join(R,'viewer/three.min.js'));
const ctx={T};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(O,'browser-door.js'),'utf8'),ctx);
const frame=new T.Group();frame.scale.x=-.8805754780769348;
const leaf=new T.Group();leaf.position.set(-.804,.24,.055);frame.add(leaf);
const g=new T.BoxGeometry(1.6,3.4,.095);g.translate(.8,1.7,0);const mesh=new T.Mesh(g);leaf.add(mesh);frame.updateMatrixWorld(true);
const before=[];for(let i=0;i<g.attributes.position.count;i++)before.push(new T.Vector3().fromBufferAttribute(g.attributes.position,i).applyMatrix4(mesh.matrixWorld));
ctx.makeDoorLeafRigid32(T,leaf);const compensation=leaf.parent;ctx.makeDoorLeafRigid32(T,leaf);assert(leaf.parent===compensation);
let closedDelta=0;for(let i=0;i<before.length;i++){const p=new T.Vector3().fromBufferAttribute(g.attributes.position,i).applyMatrix4(mesh.matrixWorld);closedDelta=Math.max(closedDelta,p.distanceTo(before[i]));}assert(closedDelta<1e-12);
const sweep=[];for(const a of [0,.2421875,.775,1.3078125,1.55]){leaf.rotation.y=a;frame.updateMatrixWorld(true);const origin=new T.Vector3().applyMatrix4(leaf.matrixWorld),width=new T.Vector3(1.6,0,0).applyMatrix4(leaf.matrixWorld).distanceTo(origin),thickness=new T.Vector3(0,0,.095).applyMatrix4(leaf.matrixWorld).distanceTo(origin);assert(Math.abs(width-1.408920764923096)<1e-9);assert(Math.abs(thickness-.095)<1e-9);sweep.push({angle:a,width,thickness});}
const audit=JSON.parse(fs.readFileSync(path.join(O,'integration-v32.json'),'utf8'));const knob=new T.Vector3(1.5625,1.626,.18).applyMatrix4(leaf.matrixWorld),native=[knob.x,-knob.z,knob.y];assert(Math.hypot(...native.map((x,i)=>x-audit.newKnobWorld[i]))<1e-6);
const html=fs.readFileSync(path.join(R,'viewer/candidate-v32.html'),'utf8');for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim())new vm.Script(m[1]);
assert(html.includes('makeDoorLeafRigid32(T,hinge);makeDoorLeafRigid32(T,nightHinge);'));assert(html.includes("load('character-v32/suzume-posed-v32.gltf'"));assert(html.includes('renderNight31(reflectionCam)'));
const result={revision:32,actualHelperExecuted:true,closedVertexMaximumDifference:closedDelta,sweep,nativeBrowserKnobMatches:true,bothSpatialDoorCopiesHooked:true,newCharacterAssetHooked:true,inlineSyntaxValid:true,browserRuntimeVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-verification-v32.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
