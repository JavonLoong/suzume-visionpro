// Execute cloud transforms and material construction; this is not a GPU/browser test.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-night-v30'),T=require(path.join(R,'viewer/three.min.js'));
const q=JSON.parse(fs.readFileSync(path.join(O,'night-spec-v30.json'),'utf8'));
const a=JSON.parse(fs.readFileSync(path.join(O,'integration-v30.json'),'utf8'));
const nightScene=new T.Scene(),sky=new T.Mesh(new T.SphereGeometry(540,40,20),new T.ShaderMaterial());sky.name='Night twilight sky';nightScene.add(sky);
for(let i=0;i<10;i++){const ob=new T.Mesh(new T.BoxGeometry(2,2,2),new T.ShaderMaterial());ob.name='Spatial twilight cloud volume '+i;nightScene.add(ob);}
const ctx={T,nightScene,root:{},q};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(O,'browser-night.js'),'utf8')+'\napplyMovieNight30(T,nightScene,root,q);',ctx);
let cornersChecked=0;
const coord=(p)=>[p.x,-p.z,p.y],close=(x,y)=>assert(Math.abs(x-y)<1e-4);
for(let i=0;i<10;i++){
 const ob=nightScene.children.find(o=>o.name==='Spatial twilight cloud volume '+i),native=a.cloudMeshes[ob.name],M=native.matrix;
 const expected=[];for(const x of [-1,1])for(const y of [-1,1])for(const z of [-1,1])expected.push(M.slice(0,3).map(r=>r[0]*x+r[1]*y+r[2]*z+r[3]));
 for(const x of [-1,1])for(const y of [-1,1])for(const z of [-1,1]){const actual=coord(new T.Vector3(x,y,z).applyMatrix4(ob.matrixWorld));assert(expected.some(p=>Math.hypot(...p.map((v,k)=>v-actual[k]))<1e-4));cornersChecked++;}
 const u=ob.material.uniforms;close(u.density30.value,q.density);close(u.emission30.value,q.emissionGain);close(u.turbulence30.value,q.turbulence);
 const identity=ob.matrixWorld.clone().multiply(u.inverseModel30.value);identity.elements.forEach((v,k)=>close(v,k%5===0?1:0));
 assert(ob.material.side===T.BackSide&&ob.material.transparent&&!ob.material.depthWrite);assert(ob.material.fragmentShader.includes('max(entry,0.)'));assert(ob.material.fragmentShader.includes('vec3(p.x,-p.z,p.y)'));
 assert(!Object.values(u).some(x=>x.value&&x.value.isTexture));
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v30.html'),'utf8');let parsed=0;for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim()){new vm.Script(m[1]);parsed++;}
assert(html.indexOf('const waterSpec29=')<html.indexOf('const nightSpec30='));assert(html.indexOf('const nightSpec30=')<html.indexOf('const characterAsset=await new Promise'));assert(html.includes('suzume-movie-view-v30'));
const result={revision:30,cloudHelperExecuted:true,closedBoxVolumes:10,nativeAndBrowserTransformedCornersMatched:cornersChecked,materialParametersMatchSpec:true,rayMarchHandlesInsideAndOutsideOrigins:true,referenceImagesUsedInClouds:false,inlineScriptsParsed:parsed,browserRuntimeVerified:false,gpuCompilationVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-verification-v30.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
