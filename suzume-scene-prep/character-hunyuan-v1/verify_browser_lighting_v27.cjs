// Numerical coordinate/power checks only; this does not exercise WebGL rendering.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-lighting-v27'),T=require(path.join(R,'viewer/three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'lighting-spec-v27.json'),'utf8')),audit=JSON.parse(fs.readFileSync(path.join(O,'integration-v27.json'),'utf8'));
const scene=new T.Scene(),sun=new T.DirectionalLight(0xffffff,3.2);scene.add(sun);scene.add(new T.HemisphereLight(0xffffff,0xffffff,.42));scene.add(new T.AmbientLight(0xffffff,.06));
for(const q of audit.lights.filter(q=>q.type!=='SUN')){const o=q.type==='AREA'?new T.RectAreaLight(0xffffff,1,...q.size):new T.SpotLight(0xffffff,1);o.name=q.name;scene.add(o);}
const context={T,scene,sun,root:{}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(O,'browser-lighting.js'),'utf8').replace('__LIGHTING_SPEC_27__',JSON.stringify(fit)),context);scene.updateMatrixWorld(true);
const eps=2e-5,close=(a,b)=>{assert.strictEqual(a.length,b.length);a.forEach((v,i)=>assert(Math.abs(v-b[i])<eps,[a,b]));};
const nativePosition=o=>[o.position.x,-o.position.z,o.position.y];const s=audit.lights.find(q=>q.type==='SUN');close(nativePosition(sun),s.worldPosition);assert(Math.abs(sun.intensity-s.power)<eps);
const expected=new T.Vector3(...s.worldPosition).normalize().negate();close(expected.toArray(),s.worldDirection);
for(const q of audit.lights.filter(q=>q.type!=='SUN')){
  const o=scene.children.find(o=>o.name===q.name);
  if(q.type==='AREA')assert(Math.abs(o.intensity*Math.PI*o.width*o.height-q.power)<eps);else assert(Math.abs(o.intensity*400-q.power)<eps);
  if(q.name==='Soft courtyard fill on the movie facade v22'){
    close(nativePosition(o),q.worldPosition);close([o.width,o.height],q.size);
    const dir=new T.Vector3(0,0,-1).applyQuaternion(o.quaternion);close([dir.x,-dir.z,dir.y],q.worldDirection);
  }
  if(q.type==='AREA')close(o.color.toArray(),q.color);
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v27.html'),'utf8');let scripts=0;
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(match[1].trim()){new vm.Script(match[1]);scripts++;}
assert(html.indexOf('const shoreFit26=')<html.indexOf('const movieLightSpec27='));assert(html.includes('suzume-movie-view-v27'));
const result={revision:27,sunWorldPositionDirectionAndEnergyMatchNative:true,facadePowerAndColorsMatchNative:true,rightFillPositionDirectionAndSizeMatchNative:true,inlineScriptsParsed:scripts,browserSkyColorRetainsPreviousCalibration:true,browserRuntimeVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-verification-v27.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
