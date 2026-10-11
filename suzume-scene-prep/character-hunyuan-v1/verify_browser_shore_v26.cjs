// Compare independently reconstructed Three geometry with reopened native buffers.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-shore-v26'),T=require(path.join(R,'viewer/three.min.js'));
const read=n=>fs.readFileSync(path.join(O,n),'utf8'),fit=JSON.parse(read('shore-fit-v26.json')),expected=JSON.parse(read('native-shore-meshes-v26.json'));
const checks=[],shaderChecks=[];
const context={T,scene:new T.Scene(),root:{},bake:group=>{
  group.updateMatrixWorld(true);let count=0;
  group.traverse(o=>{
    if(!o.isMesh)return;count++;const name=o.name+' v26';assert(expected[name],name);
    const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);const a=g.attributes.position,world=new Float32Array(a.count*3);
    for(let i=0;i<a.count;i++){world[i*3]=a.getX(i);world[i*3+1]=-a.getZ(i);world[i*3+2]=a.getY(i);}
    const hash=crypto.createHash('sha256').update(Buffer.from(world.buffer)).digest('hex');assert.strictEqual(hash,expected[name].nativeFloat32Hash,name);checks.push({name,vertices:a.count});
  });return count;
}};
vm.createContext(context);vm.runInContext(read('build_shore.js')+'\n'+read('browser-shore.js').replace('__SHORE_FIT_26__',JSON.stringify(fit)),context);
assert.strictEqual(checks.length,Object.keys(expected).length);vm.runInContext('this.testMaterials26=shoreMaterials26;',context);
for(const [name,m]of Object.entries(context.testMaterials26)){
  const shader={vertexShader:T.ShaderLib.standard.vertexShader,fragmentShader:T.ShaderLib.standard.fragmentShader};m.onBeforeCompile(shader);
  assert(shader.vertexShader.includes('vShorePosition26=(modelMatrix*vec4(transformed,1.0)).xyz'));assert(shader.fragmentShader.includes('float patina26=shoreFbm26'));assert(!shader.fragmentShader.includes('undefined'));shaderChecks.push(name);
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v26.html'),'utf8');let scripts=0;
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(match[1].trim()){new vm.Script(match[1]);scripts++;}
assert(html.indexOf('const steelFit25=')<html.indexOf('const shoreFit26='));assert(html.includes('suzume-movie-view-v26'));
const result={revision:26,allNativeMeshPositionBuffersMatch:true,newParts:checks.length,triangles:checks.reduce((s,c)=>s+c.vertices/3,0),shaderMaterialsConstructed:shaderChecks,inlineScriptsParsed:scripts,browserRuntimeVerified:false,glslDriverCompilationVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-geometry-verification-v26.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
