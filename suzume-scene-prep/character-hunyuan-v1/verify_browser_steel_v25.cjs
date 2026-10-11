// Pure Three.js geometry and shader-construction checks; no WebGL claim.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-steel-v25'),T=require(path.join(R,'viewer/three.min.js'));
const read=n=>fs.readFileSync(path.join(O,n),'utf8'),fit=JSON.parse(read('steel-fit-v25.json')),expected=JSON.parse(read('native-steel-meshes-v25.json'));
const scene=new T.Scene(),old=new T.Mesh(new T.BoxGeometry(1,1,1));old.name='Broken radial dome steelwork solid mesh';scene.add(old);
const checks=[],counts={},shaderChecks=[];
const context={T,scene,root:{},bake:group=>{
  group.updateMatrixWorld(true);let count=0;
  group.traverse(o=>{
    if(!o.isMesh)return;count++;
    const n=counts[o.name]||0;counts[o.name]=n+1;const name=o.name+' v25'+(n?'.'+String(n).padStart(3,'0'):'');assert(expected[name],name);
    const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);const a=g.attributes.position,world=new Float32Array(a.count*3);
    for(let i=0;i<a.count;i++){world[i*3]=a.getX(i);world[i*3+1]=-a.getZ(i);world[i*3+2]=a.getY(i);}
    const hash=crypto.createHash('sha256').update(Buffer.from(world.buffer)).digest('hex');assert.strictEqual(hash,expected[name].nativeFloat32Hash,name);checks.push({name,vertices:a.count});
  });return count;
}};
vm.createContext(context);vm.runInContext(read('build_steel.js')+'\n'+read('browser-steel.js').replace('__STEEL_FIT_25__',JSON.stringify(fit)),context);
assert.strictEqual(checks.length,732);assert.strictEqual(context.root.steelEvidence25.removedLegacyBatches,1);assert(!scene.children.includes(old));
vm.runInContext('this.testMaterials25=steelMaterials25;',context);
for(const [name,m]of Object.entries(context.testMaterials25)){
  if(!['steel','edge'].includes(name))continue;
  const shader={vertexShader:T.ShaderLib.standard.vertexShader,fragmentShader:T.ShaderLib.standard.fragmentShader};m.onBeforeCompile(shader);
  assert(shader.vertexShader.includes('vSteelPosition25=(modelMatrix*vec4(transformed,1.0)).xyz'));
  assert(shader.fragmentShader.includes('float oxide25=steelFbm25(vSteelPosition25*3.5)'));
  assert(!shader.fragmentShader.includes('undefined'));shaderChecks.push({material:name,worldSpaceCorrosionInjection:true});
  fs.writeFileSync(path.join(O,'webgl-'+name+'-vertex.glsl'),shader.vertexShader);fs.writeFileSync(path.join(O,'webgl-'+name+'-fragment.glsl'),shader.fragmentShader);
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v25.html'),'utf8');let scripts=0;
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(match[1].trim()){new vm.Script(match[1]);scripts++;}
assert(html.indexOf('const projectionSpec24=')<html.indexOf('const steelFit25='));assert(html.includes('suzume-movie-view-v25'));
const result={revision:25,allNativeMeshPositionBuffersMatch:true,newParts:checks.length,triangles:checks.reduce((s,c)=>s+c.vertices/3,0),shaderConstruction:shaderChecks,inlineScriptsParsed:scripts,browserRuntimeVerified:false,glslDriverCompilationVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-geometry-verification-v25.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
