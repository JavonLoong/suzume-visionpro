// Spatial cloud volumes and a directional sky color field, with no source image.
function applyMovieNight30(T,nightScene,root,q){
  const rgb=c=>new T.Vector3(...c.map(v=>v/255)),linear=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);});
  const sky=nightScene.children.find(o=>o.name==='Night twilight sky');if(!sky)throw Error('Night sky missing');
  const colors=q.skyDisplayColors;
  sky.material=new T.ShaderMaterial({side:T.BackSide,depthWrite:false,uniforms:Object.fromEntries(Object.entries(colors).map(([k,c])=>[k,{value:rgb(c)}])),
    vertexShader:'varying vec3 direction30;void main(){direction30=vec3(position.x,-position.z,position.y);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader:`varying vec3 direction30;uniform vec3 leftHorizon,rightHorizon,leftLow,rightLow,zenith;
      void main(){vec3 v=normalize(direction30);float height=max(v.z,0.),east=smoothstep(-.11,.07,v.x);
      vec3 color=mix(mix(leftHorizon,rightHorizon,east),mix(leftLow,rightLow,east),smoothstep(.005,.085,height));
      color=mix(color,zenith,smoothstep(.13,.8,height));gl_FragColor=vec4(color,1.);}`});
  const fragment=`varying vec3 local30;uniform mat4 inverseModel30;uniform vec3 halfSize30,color30;uniform float seed30,density30,emission30,turbulence30;
    float field30(vec3 p){float shift=.24*sin(p.x*13.+seed30)+.10*sin(p.x*43.+p.y*.6+seed30*.8);float h=p.z-shift;
      float envelope=1.-length(vec3(p.x*.92,p.y*.9,h*1.25));
      float a=sin(p.x*45.+sin(h*3.+seed30)),b=sin(h*9.+p.y*.4+seed30);
      float c=sin(p.x*110.+h*15.+p.y*.7+seed30*3.),d=sin(h*21.-p.y*.6);
      float edge=max(max(abs(p.x),abs(p.y)),abs(p.z));float fade=1.-smoothstep(.82,1.,edge);
      return smoothstep(.06,.42,envelope+turbulence30*(.28*a*b+.12*c*d))*fade*density30;}
    vec3 display30(vec3 c){return mix(c*12.92,1.055*pow(max(c,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
    void main(){vec3 ro=(inverseModel30*vec4(cameraPosition,1.)).xyz,rd=normalize(local30-ro),inv=1./rd;
      vec3 aa=(-1.-ro)*inv,bb=(1.-ro)*inv,mn=min(aa,bb),mx=max(aa,bb);float entry=max(max(mn.x,mn.y),mn.z),end=min(min(mx.x,mx.y),mx.z);
      float begin=max(entry,0.);if(end<=begin)discard;float dt=(end-begin)/64.,worldStep=length(rd*halfSize30)*dt,alpha=0.;vec3 light=vec3(0.);
      for(int i=0;i<64;i++){vec3 p=ro+rd*(begin+(float(i)+.5)*dt);float sigma=field30(vec3(p.x,-p.z,p.y));float opacity=1.-exp(-sigma*worldStep);float weight=(1.-alpha)*opacity;light+=color30*emission30*weight;alpha+=weight;}
      if(alpha<.001)discard;gl_FragColor=vec4(display30(light/max(alpha,.001)),alpha);}`;
  q.clouds.forEach((row,i)=>{
    const ob=nightScene.children.find(o=>o.name==='Spatial twilight cloud volume '+i);if(!ob)throw Error('Night cloud missing: '+i);
    ob.position.set(row.center[0],row.center[2],-row.center[1]);ob.scale.set(row.halfSize[0],row.halfSize[2],row.halfSize[1]);ob.rotation.set(0,0,row.tilt);ob.updateMatrixWorld(true);
    ob.material=new T.ShaderMaterial({transparent:true,depthWrite:false,side:T.BackSide,uniforms:{inverseModel30:{value:ob.matrixWorld.clone().invert()},halfSize30:{value:ob.scale.clone()},color30:{value:new T.Vector3(...linear(q.cloudDisplayColors[row.tone]))},seed30:{value:row.seed},density30:{value:q.density},emission30:{value:q.emissionGain},turbulence30:{value:q.turbulence}},vertexShader:'varying vec3 local30;void main(){local30=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:fragment});
    ob.userData.movieCloud30=row;
  });
  root.nightEvidence30={revision:30,cloudVolumes:q.clouds.length,referenceImageUsedInSkyOrClouds:false,geometryType:'closed spatial volumes with analytic density and wind displacement',browserRuntimeVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
}
