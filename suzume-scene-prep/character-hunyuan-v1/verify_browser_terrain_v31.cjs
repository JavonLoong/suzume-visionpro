// Execute actual geometry edits and depth-composite scheduling without a GPU claim.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-terrain-v31'),T=require(path.join(R,'viewer/three.min.js')),q=JSON.parse(fs.readFileSync(path.join(O,'terrain-spec-v31.json'),'utf8'));
const bytes=name=>{const b=fs.readFileSync(path.join(O,name));return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);};
const original=new Float32Array(bytes('original-world-check-v31.bin')),positions=new Float32Array(original.length);for(let i=0;i<original.length;i+=3){positions[i]=original[i];positions[i+1]=original[i+2];positions[i+2]=-original[i+1];}
const ground=new T.Mesh(new T.BufferGeometry().setAttribute('position',new T.BufferAttribute(positions,3)),new T.MeshLambertMaterial());ground.name='Rolling meadow ground';const nightScene=new T.Scene();nightScene.add(ground);
const destination=new T.WebGLRenderTarget(700,900),calls=[];let active=destination;const renderer={getRenderTarget:()=>active,setRenderTarget:t=>{active=t;},getDrawingBufferSize:v=>v.set(1280,720),render:(s,c)=>calls.push({scene:s,target:active,camera:c})};
const root={},buffers=['ground-world-v31.bin','extension-vertices-v31.bin','extension-indices-v31.bin'].map(bytes),ctx={T,nightScene,renderer,root,q,buffers};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(O,'browser-terrain.js'),'utf8')+'\nthis.draw=applyMovieTerrain31(T,nightScene,renderer,root,q,buffers);',ctx);
const actual=ground.geometry.attributes.position.array,target=new Float32Array(buffers[0]);let near=0,changed=0;for(let i=0;i<original.length;i+=3){
 if(Math.hypot(original[i],original[i+1])<=q.unchangedNearRadius){assert(actual[i]===original[i]&&actual[i+1]===original[i+2]&&actual[i+2]===-original[i+1]);near++;}
 else{assert(Math.abs(actual[i+1]-target[i+2])<1e-5);changed++;}
}
const ext=ctx.draw.inspection.extension,native=new Float32Array(buffers[1]),p=ext.geometry.attributes.position.array;for(let i=0;i<p.length;i+=3){assert(p[i]===native[i]&&p[i+1]===native[i+2]&&p[i+2]===-native[i+1]);}
assert(ext.geometry.index.count/3===q.geometryCounts.extensionTriangles);assert(ctx.draw.inspection.target.depthTexture.isDepthTexture);assert(ctx.draw.inspection.target.depthTexture.type===T.UnsignedIntType);
const camera=new T.PerspectiveCamera(45,700/900,.05,900);camera.position.set(.15,2.88,11.73);camera.lookAt(0,1.9,0);ctx.draw(camera);
assert(calls.length===2&&calls[0].scene===nightScene);assert(calls[0].target===ctx.draw.inspection.target&&calls[1].target===destination);assert(active===destination);assert(calls[1].target!==ctx.draw.inspection.uniforms.colorBuffer31.value&&calls[1].target!==ctx.draw.inspection.target);
active=null;ctx.draw(camera);assert(ctx.draw.inspection.target.width===1280&&ctx.draw.inspection.target.height===720);assert(active===null);
const html=fs.readFileSync(path.join(R,'viewer/candidate-v31.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim()){new vm.Script(m[1]);scripts++;}
assert(html.includes('renderNight31(reflectionCam)'));assert((html.match(/renderNight31\(camera\)/g)||[]).length===2);assert(html.includes('renderNight31.dispose()'));
const result={revision:31,actualGeometryAndRenderHelperExecuted:true,nearGroundVerticesPreserved:near,changedGroundVertices:changed,nativeExtensionVerticesMatched:p.length/3,nativeExtensionTriangles:ext.geometry.index.count/3,depthTextureAttached:true,separateSourceAndDestinationTargetsVerified:true,portalReflectionAndStandaloneRenderPathsHooked:true,resizeAndDestinationRestorationVerified:true,inlineScriptsParsed:scripts,browserRuntimeVerified:false,gpuShaderCompilationVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
ctx.draw.dispose();fs.writeFileSync(path.join(O,'browser-verification-v31.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
