// Terrain coordinates are shared with Blender. Mist is integrated only to opaque depth.
function applyMovieTerrain31(T,nightScene,renderer,root,q,buffers){
 const ground=nightScene.children.find(o=>o.name==='Rolling meadow ground');if(!ground)throw Error('Night ground missing');
 const target=new Float32Array(buffers[0]),map=new Map();for(let i=0;i<target.length;i+=3)map.set(Math.round(target[i]*1000)+','+Math.round(target[i+1]*1000),target[i+2]);
 const pos=ground.geometry.attributes.position;let changed=0;
 for(let i=0;i<pos.count;i++){const x=pos.getX(i),y=-pos.getZ(i),key=Math.round(x*1000)+','+Math.round(y*1000);if(!map.has(key))throw Error('Ground coordinate mismatch');if(Math.hypot(x,y)>q.unchangedNearRadius){pos.setY(i,map.get(key));changed++;}}
 pos.needsUpdate=true;ground.geometry.computeVertexNormals();ground.geometry.computeBoundingSphere();
 const native=new Float32Array(buffers[1]),positions=new Float32Array(native.length),uv=new Float32Array(native.length/3*2);
 for(let i=0;i<native.length;i+=3){positions[i]=native[i];positions[i+1]=native[i+2];positions[i+2]=-native[i+1];uv[i/3*2]=(native[i]+200)/400;uv[i/3*2+1]=(native[i+1]+200)/400;}
 const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(positions,3));g.setAttribute('uv',new T.BufferAttribute(uv,2));g.setIndex(new T.BufferAttribute(new Uint32Array(buffers[2]),1));g.computeVertexNormals();g.computeBoundingSphere();
 const ext=new T.Mesh(g,ground.material);ext.name='Continuous distant meadow v31';nightScene.add(ext);
 const linear=rgb=>rgb.map(v=>{v/=255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);});
 const target31=new T.WebGLRenderTarget(1,1,{minFilter:T.LinearFilter,magFilter:T.LinearFilter,depthBuffer:true,stencilBuffer:false});target31.texture.encoding=T.sRGBEncoding;target31.depthTexture=new T.DepthTexture(1,1,T.UnsignedIntType);
 const uniforms={colorBuffer31:{value:target31.texture},depthBuffer31:{value:target31.depthTexture},inverseProjection31:{value:new T.Matrix4()},cameraWorld31:{value:new T.Matrix4()},fogLeft31:{value:new T.Vector3(...linear(q.fogLeftDisplay||q.fogColorDisplay))},fogRight31:{value:new T.Vector3(...linear(q.fogRightDisplay||q.fogColorDisplay))},fogX31:{value:new T.Vector2(...(q.fogLateralX||[-7,4]))},fogGain31:{value:new T.Vector2(...(q.fogLateralGain||[1,1]))},density31:{value:q.fogDensity},emission31:{value:q.fogEmissionGain}};
 q.fogVolumes.forEach((r,i)=>{uniforms['center'+i+'31']={value:new T.Vector3(...r.center)};uniforms['half'+i+'31']={value:new T.Vector3(...r.halfSize)};uniforms['seed'+i+'31']={value:r.seed};uniforms['weight'+i+'31']={value:r.weight};});
 const fragment=`varying vec2 uv31;uniform sampler2D colorBuffer31,depthBuffer31;uniform mat4 inverseProjection31,cameraWorld31;
 uniform vec3 fogLeft31,fogRight31,center031,center131,half031,half131;uniform vec2 fogX31,fogGain31;uniform float density31,emission31,seed031,seed131,weight031,weight131;
 vec3 decode31(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
 vec3 encode31(vec3 c){return mix(c*12.92,1.055*pow(max(c,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
 vec2 box31(vec3 ro,vec3 rd,vec3 center,vec3 halfSize){vec3 d=vec3(rd.x<0.?min(rd.x,-1e-7):max(rd.x,1e-7),rd.y<0.?min(rd.y,-1e-7):max(rd.y,1e-7),rd.z<0.?min(rd.z,-1e-7):max(rd.z,1e-7));vec3 a=(center-halfSize-ro)/d,b=(center+halfSize-ro)/d,mn=min(a,b),mx=max(a,b);return vec2(max(max(mn.x,mn.y),mn.z),min(min(mx.x,mx.y),mx.z));}
 float lateral31(float x){return smoothstep(fogX31.x,fogX31.y,x);}
 float field31(vec3 p,vec3 center,vec3 halfSize,float seed,float weight){vec3 local=(p-center)/halfSize;float edge=max(max(abs(local.x),abs(local.y)),abs(local.z));if(edge>=1.)return 0.;float height=center.z+.13*sin(p.x*.08+p.y*.10+seed),h=(p.z-height)/(halfSize.z*.38);float flow=.65+.35*sin(p.x*.17+p.y*.11+seed)*sin(p.x*.043-p.y*.07);return exp(-2.*h*h)*flow*(1.-smoothstep(.7,1.,edge))*density31*weight*mix(fogGain31.x,fogGain31.y,lateral31(p.x));}
 void main(){vec3 base=texture2D(colorBuffer31,uv31).rgb;float depth=texture2D(depthBuffer31,uv31).x;vec4 vp=inverseProjection31*vec4(uv31*2.-1.,depth*2.-1.,1.);vp/=vp.w;vec3 endWorld=(cameraWorld31*vp).xyz,origin=cameraWorld31[3].xyz;float stopDistance=length(endWorld-origin);vec3 direction=normalize(endWorld-origin),ro=vec3(origin.x,-origin.z,origin.y),rd=vec3(direction.x,-direction.z,direction.y);
 vec2 b0=box31(ro,rd,center031,half031),b1=box31(ro,rd,center131,half131);if(b0.y<b0.x)b0=vec2(1e6,-1e6);if(b1.y<b1.x)b1=vec2(1e6,-1e6);float begin=max(0.,min(b0.x,b1.x)),end=min(stopDistance,max(b0.y,b1.y));if(end<=begin){gl_FragColor=vec4(base,1.);return;}
 float dt=(end-begin)/96.,alpha=0.;vec3 radiance=vec3(0.);for(int i=0;i<96;i++){vec3 p=ro+rd*(begin+(float(i)+.5)*dt);float sigma=field31(p,center031,half031,seed031,weight031)+field31(p,center131,half131,seed131,weight131);float stepAlpha=1.-exp(-sigma*dt),w=(1.-alpha)*stepAlpha;radiance+=mix(fogLeft31,fogRight31,lateral31(p.x))*emission31*w;alpha+=w;}gl_FragColor=vec4(encode31(decode31(base)*(1.-alpha)+radiance),1.);}`;
 const mat=new T.ShaderMaterial({uniforms,depthTest:false,depthWrite:false,toneMapped:false,vertexShader:'varying vec2 uv31;void main(){uv31=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:fragment});
 const composite=new T.Scene();composite.add(new T.Mesh(new T.PlaneGeometry(2,2),mat));const screenCamera=new T.OrthographicCamera(-1,1,1,-1,0,1),size=new T.Vector2();
 root.terrainEvidence31={revision:31,groundVertices:pos.count,changedGroundVertices:changed,extensionTriangles:g.index.count/3,nearRadius:q.unchangedNearRadius,mistVolumes:2,depthClippedMist:true,browserRuntimeVerified:false,nativeBrowserAppearanceEquivalenceVerified:false,oneToOneComplete:false};
 function draw(camera){
   const destination=renderer.getRenderTarget();let width,height;if(destination){width=destination.width;height=destination.height;}else{renderer.getDrawingBufferSize(size);width=size.x;height=size.y;}
   if(target31.width!==width||target31.height!==height)target31.setSize(width,height);
   camera.updateMatrixWorld();uniforms.inverseProjection31.value.copy(camera.projectionMatrix).invert();uniforms.cameraWorld31.value.copy(camera.matrixWorld);
   renderer.setRenderTarget(target31);renderer.render(nightScene,camera);renderer.setRenderTarget(destination);renderer.render(composite,screenCamera);
 }
 draw.dispose=()=>{target31.dispose();mat.dispose();composite.children[0].geometry.dispose();};draw.inspection={target:target31,uniforms,material:mat,extension:ext};return draw;
}
