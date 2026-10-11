// Execute the actual water builder and shader edits without claiming a GPU test.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-water-v29'),V='C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103';
const T=require(path.join(R,'viewer/three.min.js')),q=JSON.parse(fs.readFileSync(path.join(O,'water-spec-v29.json'),'utf8'));
const template=fs.readFileSync(path.join(V,'full-scene-template.html'),'utf8'),noise=template.match(/const noiseGLSL=`([^`]+)`/)[1];
const scene=new T.Scene(),source=JSON.parse(fs.readFileSync(path.join(O,'source-inspection-v29.json'),'utf8')),mats=new Map();
for(const row of source.objects.filter(x=>!x.name.startsWith('Live'))){
  const name=row.materials[0].name;if(!mats.has(name))mats.set(name,new T.MeshStandardMaterial());
  const ob=new T.Mesh(new T.BufferGeometry(),mats.get(name));ob.name=row.name;scene.add(ob);
}
const ctx={T,scene,root:{},noiseGLSL:noise,posterComposition:{door_scale_x:1},base:.14,q};vm.createContext(ctx);
const original=fs.readFileSync(path.join(V,'full-water-portal.js'),'utf8').replace('__WATER_PALETTE__',fs.readFileSync(path.join(V,'water-palette-v11.json'),'utf8'));
vm.runInContext(original+'\n'+fs.readFileSync(path.join(O,'browser-water.js'),'utf8')+'\napplyMovieWater29(T,scene,water,root,q,noiseGLSL);this.resultWater=water;',ctx);
const water=ctx.resultWater,u=water.material.uniforms,close=(a,b)=>assert(Math.abs(a-b)<1e-7);
q.fresnel.forEach((v,i)=>close(u.uFresnel.value.toArray()[i],v));close(u.uFresnelPower29.value,q.fresnelPower);close(u.uRippleScale29.value,q.rippleAmplitudeScale);close(u.uHazeDepth29.value,q.hazeOpticalDepth);close(u.uHazeStrength29.value,q.hazeStrength);close(u.uReflectionBlur29.value,q.reflectionRoughness*.04);
assert(water.material.fragmentShader.includes('pow(1.-viewCos,uFresnelPower29)'));assert(water.material.fragmentShader.includes('1.-exp(-uHazeDepth29/max(viewCos,.03))'));
assert(u.uReflection.value.isTexture&&u.uRefraction.value.isTexture);assert(!Object.keys(u).some(k=>/reference|image/i.test(k)));
let checked=0;for(const mat of mats.values()){
  const shader={uniforms:{},vertexShader:T.ShaderLib.standard.vertexShader,fragmentShader:T.ShaderLib.standard.fragmentShader};mat.onBeforeCompile(shader);
  assert(shader.vertexShader.includes('bedWorld29=(modelMatrix*vec4(transformed,1.)).xyz'));assert(shader.fragmentShader.includes('step(bedWorld29.y,.035)*step(.6,bedUp29)'));assert(shader.fragmentShader.includes('float bedHash29('));close(shader.uniforms.uAlgae29.value,q.algaeStrength);checked++;
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v29.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim()){new vm.Script(m[1]);scripts++;}
assert(html.includes('suzume-movie-view-v29'));assert(html.indexOf('const movieLightSpec27=')<html.indexOf('const waterSpec29='));assert(html.indexOf('const waterSpec29=')<html.indexOf('const characterAsset=await new Promise'));
const result={revision:29,actualWaterBuilderAndOpticsEditsExecuted:true,waterUniformParametersMatchNativeSpec:true,liveReflectionAndRefractionTexturesRetained:true,referenceImageUsedInWater:false,submergedMaterialShaderHooksChecked:checked,inlineScriptsParsed:scripts,browserRuntimeVerified:false,gpuShaderCompilationVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-verification-v29.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
