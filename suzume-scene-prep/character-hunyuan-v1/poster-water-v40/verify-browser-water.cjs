// Executes material setup with real Three.js objects and checks the built page.
// This does not create a browser, WebGL context or claim GPU shader validation.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js'));
const q=JSON.parse(fs.readFileSync(path.join(__dirname,'water-spec-v40.json')));
const reflection=new T.Texture(),refraction=new T.Texture();
const mat=new T.ShaderMaterial({uniforms:{uReflection:{value:reflection},uRefraction:{value:refraction},uTime:{value:2.4},uEye:{value:new T.Vector3(0,2,5)},uMatrix:{value:new T.Matrix4()},uFresnel:{value:new T.Vector2()}}});
const water=new T.Mesh(new T.CircleGeometry(29,128),mat);water.rotation.x=-Math.PI/2;water.position.y=.05;
const geometry=water.geometry,position=water.position.clone(),matrix=water.matrix.clone(),evidence={};
const context=vm.createContext({Error,Object});vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-water.js'),'utf8'),context);
context.applyPosterWater40(T,water,evidence,q);
assert.strictEqual(water.geometry,geometry);assert(water.position.equals(position));assert(water.matrix.equals(matrix));assert.strictEqual(water.material,mat);
assert.strictEqual(mat.uniforms.uReflection.value,reflection);assert.strictEqual(mat.uniforms.uRefraction.value,refraction);assert.equal(mat.uniforms.uTime.value,2.4);
const declarations=[...mat.fragmentShader.matchAll(/uniform\s+\w+\s+([^;]+);/g)].flatMap(m=>m[1].split(',').map(x=>x.trim()));
assert(declarations.length>15);for(const name of declarations)assert(mat.uniforms[name]&&mat.uniforms[name].value!==undefined,'Unbound GLSL uniform '+name);
const html=fs.readFileSync(path.join(root,'viewer/poster-v40.html'),'utf8');let parsed=0;
for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)){if(m[2].trim()){new vm.Script(m[2]);parsed++;}}
assert(html.includes("let state={open:false,motion:false,azimuth:posterComposition.azimuth"));assert(html.includes('suzume-poster-view-v40'));assert(html.includes('await applyPosterSteel39(T,scene,root)'));assert(html.includes('applyPosterWater40(T,water,root,posterWaterSpec40)'));assert(!html.includes('applyMovieWater29'));assert(!html.includes('applyMovieTerrain31'));assert(!html.includes('__WATER_PALETTE__'));
assert(html.indexOf('applyPosterWater40(T,water,root,posterWaterSpec40)')<html.indexOf('const characterAsset=await new Promise'));
const report={revision:40,threeRevision:T.REVISION,inlineScriptsParsed:parsed,waterGeometryAndTransformUnchanged:true,liveRenderTargetsPreserved:true,animationUniformPreserved:true,allDeclaredShaderUniformsBound:true,shaderUniforms:declarations,posterClosedDefaultAndIsolatedStorage:true,previousSteelAndCurrentCharacterRetained:true,scope:'Node material setup, uniform binding and JavaScript parsing. Does not verify GLSL compilation, WebGL rendering or visual equivalence.',browserRuntimeVerified:false};
fs.writeFileSync(path.join(__dirname,'browser-code-verification-v40.json'),JSON.stringify(report,null,2));console.log('POSTER_WATER_40_BROWSER_CODE_CHECKED',declarations.length,'uniforms');
