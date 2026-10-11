// Optical controls on live scene reflection/refraction; no water reference image.
function applyMovieWater29(T,scene,water,root,q,noiseGLSL){
  const m=water.material,u=m.uniforms;
  u.uFresnel.value.set(...q.fresnel);u.uBedHaze.value=.10;
  const tint=q.reflectionTint.map(v=>Math.pow(v,1/2.2));for(const name of ['uTint0','uTint1','uTint2'])u[name].value.set(...tint);u.uWaterBias.value.set(0,0,0);
  u.uFresnelPower29={value:q.fresnelPower};u.uRippleScale29={value:q.rippleAmplitudeScale};u.uReflectionBlur29={value:q.reflectionRoughness*.04};
  u.uTransmissionTint29={value:new T.Vector3(...q.transmissionTint.map(v=>Math.pow(v,1/2.2)))};
  u.uHazeDepth29={value:q.hazeOpticalDepth||0};u.uHazeStrength29={value:q.hazeStrength||0};u.uHazeColor29={value:new T.Vector3(...(q.hazeColorDisplay||[0,0,0]).map(x=>x/255))};
  let code=m.fragmentShader;
  function replace(a,b){if(!code.includes(a))throw Error('Water v29 shader hook missing: '+a);code=code.replace(a,b);}
  replace('void main(){vec2 p=world.xz;float t=uTime;',`uniform float uFresnelPower29,uRippleScale29,uReflectionBlur29,uHazeDepth29,uHazeStrength29; uniform vec3 uHazeColor29,uTransmissionTint29;
    vec3 toWaterLinear29(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
    vec3 toWaterDisplay29(vec3 c){return mix(c*12.92,1.055*pow(max(c,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
    void main(){vec2 p=world.xz;float t=uTime;`);
  replace('vec2 slope=vec2(.32*a+.14*b,.20*b+.10*c);','vec2 slope=vec2(.32*a+.14*b,.20*b+.10*c)*uRippleScale29;');
  replace('pow(1.-viewCos,3.),.05,.97)','pow(1.-viewCos,uFresnelPower29),0.,.97)');
  replace('float blur=.0020+.0035*(1.-proximity);','float blur=uReflectionBlur29*(.8+.4*(1.-proximity));');
  replace('vec3 bed=texture2D(uRefraction,clamp(screen+slope*.0005,.001,.999)).rgb;','vec3 bed=texture2D(uRefraction,clamp(screen+slope*.0005,.001,.999)).rgb*uTransmissionTint29;');
  replace('gl_FragColor=vec4(color,1.);',`float haze29=uHazeStrength29*(1.-exp(-uHazeDepth29/max(viewCos,.03)));
    color=toWaterDisplay29(mix(toWaterLinear29(color),toWaterLinear29(uHazeColor29),haze29));
    gl_FragColor=vec4(color,1.);`);
  m.fragmentShader=code;m.needsUpdate=true;
  const seen=new Set();let bedMaterials=0;
  scene.traverse(o=>{
    if(!o.isMesh||!o.name.startsWith('Flooded polygon flagstones and broken slabs solid mesh')&&!o.name.startsWith('Movie courtyard continuous basin bed'))return;
    if(seen.has(o.material))return;seen.add(o.material);const mat=o.material;bedMaterials++;
    mat.onBeforeCompile=shader=>{
      shader.uniforms.uAlgae29={value:q.algaeStrength};
      shader.vertexShader='varying vec3 bedWorld29; varying float bedUp29;\n'+shader.vertexShader;
      shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nbedWorld29=(modelMatrix*vec4(transformed,1.)).xyz;bedUp29=normalize(mat3(modelMatrix)*objectNormal).y;');
      const noise=noiseGLSL.replace(/\bh\(/g,'bedHash29(').replace(/\bn\(/g,'bedNoise29(').replace(/\bfbm\(/g,'bedFbm29(');
      shader.fragmentShader='uniform float uAlgae29; varying vec3 bedWorld29; varying float bedUp29;\n'+noise+'\n'+shader.fragmentShader;
      shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
        float algae29=smoothstep(.34,.64,bedFbm29(bedWorld29.xz*.48))*bedNoise29(bedWorld29.xz*9.)*uAlgae29;
        algae29*=step(bedWorld29.y,.035)*step(.6,bedUp29);
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.025,.15,.06),algae29);`);
    };
    mat.customProgramCacheKey=()=> 'submerged-stone-algae-v29';mat.needsUpdate=true;
  });
  root.waterEvidence29={revision:29,referenceImageUsedInWater:false,liveReflectionAndRefraction:true,parameters:q,submergedBedMaterials:bedMaterials,geometryChanged:false,browserRuntimeVerified:false,oneToOneComplete:false,nativeBrowserAppearanceEquivalenceVerified:false};
}
