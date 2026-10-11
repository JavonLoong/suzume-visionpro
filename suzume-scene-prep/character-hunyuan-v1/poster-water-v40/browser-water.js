// Live planar reflection/refraction with world-space waves. Native Cycles uses
// ray transport and AgX; this WebGL display-space approximation is a candidate.
function applyPosterWater40(T, water, root, q) {
  const m=water.material,u=m.uniforms;
  if(!u.uReflection||!u.uRefraction||!u.uTime||!u.uEye)throw Error('Poster water render targets missing');
  u.uFresnel.value.set(...q.fresnel);
  u.uReflectionTint40={value:new T.Vector3(...q.reflectionTint)};
  u.uTransmissionTint40={value:new T.Vector3(...q.transmissionTint)};
  u.uHazeFar40={value:new T.Vector3(...q.hazeColorDisplay.map(v=>v/255))};
  u.uHazeNear40={value:new T.Vector3(...q.hazeColorDisplayNear.map(v=>v/255))};
  u.uGlintColor40={value:new T.Vector3(...q.glintColorDisplay.map(v=>v/255))};
  u.uCosineRange40={value:new T.Vector2(...q.hazeCosineRange)};
  u.uGlintPatch40={value:new T.Vector2(...q.glintPatchScale)};u.uGlintCoverage40={value:new T.Vector2(...q.glintCoverage)};
  u.uWave040={value:new T.Vector4(...q.waves[0])};u.uWave140={value:new T.Vector4(...q.waves[1])};u.uWave240={value:new T.Vector4(...q.waves[2])};
  for(const [name,value] of Object.entries({uFresnelPower40:q.fresnelPower,uPhaseNoise40:q.phaseNoise,uBlur40:q.reflectionRoughness*.04,uHazeDepth40:q.hazeOpticalDepth,uHazeStrength40:q.hazeStrength,uGlintStrength40:q.glintStrength,uGlintFrequency40:q.glintFrequency,uGlintWarp40:q.glintWarp}))u[name]={value};
  m.fragmentShader=`
    uniform sampler2D uReflection,uRefraction;
    uniform float uTime,uFresnelPower40,uPhaseNoise40,uBlur40,uHazeDepth40,uHazeStrength40,uGlintStrength40,uGlintFrequency40,uGlintWarp40;
    uniform vec2 uFresnel,uCosineRange40,uGlintPatch40,uGlintCoverage40;
    uniform vec3 uEye,uReflectionTint40,uTransmissionTint40,uHazeFar40,uHazeNear40,uGlintColor40;
    uniform vec4 uWave040,uWave140,uWave240;
    varying vec4 reflection,projected; varying vec3 world;
    float hash40(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
    float noise40(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash40(i),hash40(i+vec2(1.,0.)),f.x),mix(hash40(i+vec2(0.,1.)),hash40(i+vec2(1.,1.)),f.x),f.y);}
    float patch40(vec2 p){return .65*noise40(p)+.35*noise40(p*2.03+vec2(9.2,4.7));}
    vec3 linear40(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
    vec3 display40(vec3 c){return mix(c*12.92,1.055*pow(max(c,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
    float wave40(vec2 p,vec4 w,float noisePhase){return sin(p.y*w.x+p.x*w.y+uTime*w.z+noisePhase)*w.w;}
    float height40(vec2 p){float n=patch40(p*.43);float phase=(n-.5)*uPhaseNoise40;return (wave40(p,uWave040,phase)+wave40(p,uWave140,phase)+wave40(p,uWave240,phase))*(.45+1.1*n);}
    void main(){
      vec2 p=world.xz;float e=.003;
      vec2 gradient=vec2(height40(p+vec2(e,0.))-height40(p-vec2(e,0.)),height40(p+vec2(0.,e))-height40(p-vec2(0.,e)))/(2.*e);
      vec3 normal=normalize(vec3(-gradient.x,1.,-gradient.y));vec3 eye=normalize(uEye-world);
      float viewCos=abs(dot(eye,normal));float fres=clamp(uFresnel.x+uFresnel.y*pow(1.-viewCos,uFresnelPower40),0.,1.);
      float proximity=1./max(1.,length(uEye-world)*.17);vec2 slope=gradient*20.;
      vec2 uv=reflection.xy/reflection.w+slope*vec2(.004,.022)*proximity;
      float blur=uBlur40*(.8+.4*(1.-proximity));
      vec3 reflected=linear40(texture2D(uReflection,clamp(uv,.001,.999)).rgb)*.4;
      reflected+=linear40(texture2D(uReflection,clamp(uv+vec2(0.,blur),.001,.999)).rgb)*.2;
      reflected+=linear40(texture2D(uReflection,clamp(uv-vec2(0.,blur),.001,.999)).rgb)*.2;
      reflected+=linear40(texture2D(uReflection,clamp(uv+vec2(blur*.4,0.),.001,.999)).rgb)*.1;
      reflected+=linear40(texture2D(uReflection,clamp(uv-vec2(blur*.4,0.),.001,.999)).rgb)*.1;
      vec2 screen=projected.xy/projected.w*.5+.5;
      vec3 bed=linear40(texture2D(uRefraction,clamp(screen+slope*.0005,.001,.999)).rgb)*uTransmissionTint40;
      vec3 color=mix(bed,reflected*uReflectionTint40,fres);
      float angle=clamp((viewCos-uCosineRange40.x)/(uCosineRange40.y-uCosineRange40.x),0.,1.);
      vec3 body=mix(linear40(uHazeFar40),linear40(uHazeNear40),angle);
      float haze=uHazeStrength40*(1.-exp(-uHazeDepth40/max(viewCos,.03)));
      color=mix(color,body,haze);
      float crest=pow(max(0.,sin(p.y*uGlintFrequency40+sin(p.x*.15)*.28+(patch40(p*.43)-.5)*uGlintWarp40+uTime*.22)),58.);
      float coverage=clamp((patch40(p*uGlintPatch40)-uGlintCoverage40.x)/(uGlintCoverage40.y-uGlintCoverage40.x),0.,1.);
      color=mix(color,linear40(uGlintColor40),crest*coverage*uGlintStrength40);
      gl_FragColor=vec4(display40(color),1.);
    }`;
  m.needsUpdate=true;
  root.posterWaterEvidence40={revision:40,parameters:q,referenceImageUsedInWater:false,liveReflectionAndRefraction:true,worldSpaceWaves:true,geometryChanged:false,browserRuntimeVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
}
