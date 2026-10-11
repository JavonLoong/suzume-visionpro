// Numerical Three.js verification; this does not assert browser rendering.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-projection-v24'),T=require(path.join(R,'viewer/three.min.js'));
const read=n=>fs.readFileSync(path.join(O,n),'utf8'),json=n=>JSON.parse(read(n));
const spec=json('projection-spec-v24.json'),fit=json('bay-fit-v24.json'),right=json('right-fit-v24.json'),native=json('native-lower-walls-v24.json');
const context={T,scene:new T.Scene(),root:{},stoneMap:null,rustMap:null,paintMap:null};
for(const [name,color]of Object.entries({brass:0xbda457,moss:0x536b35,sunWall:0xf2e6a6,cornice:0xd7d4bd,damp:0x708c83,roomMat:0x354947,mullionMat:0xa29c7e,iron:0x655448,ironEdge:0xa98962,windowMat:0x34576c}))context[name]=new T.MeshStandardMaterial({color});
const evidence=[];context.bake=group=>{
  group.updateMatrixWorld(true);let count=0;
  group.traverse(o=>{
    if(!o.isMesh)return;count++;
    if(o.userData.geometryRole23!=='lowerWall'&&!o.name.startsWith('Solid plaster wall'))return;
    let ancestor=o;while(ancestor&&!Number.isInteger(ancestor.userData.bayIndex23))ancestor=ancestor.parent;
    const index=ancestor?ancestor.userData.bayIndex23:16,g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);const a=g.attributes.position,expected=native[index];assert.strictEqual(a.count,expected.length);let error=0;
    for(let i=0;i<a.count;i++){const point=[a.getX(i),-a.getZ(i),a.getY(i)];for(let j=0;j<3;j++)error=Math.max(error,Math.abs(point[j]-expected[i][j]));}
    assert(error<.0001,'native/browser bay '+index+' error '+error);evidence.push({bay:index,vertices:a.count,maximumNativeDifference:error});
  });return count;
};
vm.createContext(context);
const apply=read('browser-apply.js').replace('__PROJECTION_SPEC_24__',JSON.stringify(spec)).replace('__BAY_FIT_24__',JSON.stringify(fit)).replace('__RIGHT_FIT_24__',JSON.stringify(right));
vm.runInContext(read('browser-geometry.js')+'\n'+read('build_bays.js')+'\n'+read('build_right.js')+'\n'+apply,context);
assert.strictEqual(evidence.length,5);assert.strictEqual(context.root.projectionEvidence24.newParts,789);
const p=spec.parameters,fov=2*Math.atan(18/p.lensMm)*180/Math.PI,cam=new T.PerspectiveCamera(fov,2552/1656,.05,700);
cam.position.set(p.cameraX,p.cameraZ,p.distance);cam.lookAt(p.cameraX,p.cameraZ-p.distance*Math.tan(p.pitch),0);cam.updateMatrixWorld(true);
let cameraError=0;for(const o of json('joint-fit-v24.json').observations){if(!o.world)continue;const v=new T.Vector3(o.world[0],o.world[2],-o.world[1]).project(cam);const uv=[(v.x*.5+.5)*2552,(.5-v.y*.5)*1656];cameraError=Math.max(cameraError,...uv.map((n,i)=>Math.abs(n-o.projected[i])));}
assert(cameraError<1e-6);
const html=fs.readFileSync(path.join(R,'viewer/candidate-v24.html'),'utf8');let scripts=0;for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){if(match[1].trim()){new vm.Script(match[1]);scripts++;}}
assert(html.includes('suzume-movie-view-v24'));assert(html.indexOf('const projectionSpec24=')<html.indexOf('const angle24='));assert(html.includes("canvas.getContext('webgl'"));
const result={revision:24,nativeFiveLowerWallsMatch:true,walls:evidence,newParts:789,cameraProjectionMaximumError:cameraError,inlineScriptsParsed:scripts,browserRuntimeVerified:false,browserFailure:'CUA tab binding timed out at Emulation.setFocusEmulationEnabled; no screenshot or interaction check available.'};
fs.writeFileSync(path.join(O,'browser-geometry-verification-v24.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
