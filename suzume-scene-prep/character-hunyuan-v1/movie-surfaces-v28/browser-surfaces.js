// Reference colors stay on physical triangles in world space while orbiting.
function createFilmSurfacePainter28(T,spec,source,mask){
  const P=spec.projection,C=new T.Vector3(P.cameraX,-P.distance,P.cameraZ),copies=new Map();
  const evidence={revision:28,selectedObjects:0,selectedTriangles:0,newSurfaceGeometryCount:0,fixedWorldProjection:true,browserRuntimeVerified:false,oneToOneComplete:false};
  const rgb0=new Set([0x708c83,0xe4e5e3,0xe1e4e6,0xb8c4bc,0xd7d4bd,0xa0bfd5]),rgb1=new Set([0xf1eee6,0xe9e5d7]);
  function paintMaterial(original){
    if(copies.has(original))return copies.get(original);
    const m=original.clone();m.name=original.name+' film pigments v28';
    m.onBeforeCompile=shader=>{
      shader.uniforms.filmSource28={value:source};shader.uniforms.filmMask28={value:mask};
      shader.uniforms.filmCamera28={value:C};shader.uniforms.filmLens28={value:new T.Vector3(Math.cos(P.pitch),Math.sin(P.pitch),1656*P.lensMm/36)};
      shader.vertexShader='attribute float filmEligible28;\nvarying vec3 filmWorld28;\nvarying float filmFace28;\n'+shader.vertexShader;
      shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nfilmWorld28=(modelMatrix*vec4(transformed,1.0)).xyz; filmFace28=filmEligible28;');
      shader.fragmentShader='uniform sampler2D filmSource28; uniform sampler2D filmMask28; uniform vec3 filmCamera28; uniform vec3 filmLens28; varying vec3 filmWorld28; varying float filmFace28;\n'+shader.fragmentShader;
      shader.fragmentShader=shader.fragmentShader.replace('#include <encodings_fragment>',`
        vec3 filmRel28=vec3(filmWorld28.x,-filmWorld28.z,filmWorld28.y)-filmCamera28;
        float filmDepth28=filmRel28.y*filmLens28.x-filmRel28.z*filmLens28.y;
        vec2 filmUV28=vec2(.5+filmLens28.z*filmRel28.x/(2552.0*filmDepth28),.5+filmLens28.z*(filmRel28.y*filmLens28.y+filmRel28.z*filmLens28.x)/(1656.0*filmDepth28));
        float filmInside28=step(0.0,filmUV28.x)*step(filmUV28.x,1.0)*step(0.0,filmUV28.y)*step(filmUV28.y,1.0)*step(0.0,filmDepth28);
        vec3 filmLinear28=sRGBToLinear(texture2D(filmSource28,filmUV28)).rgb;
        float filmMix28=texture2D(filmMask28,filmUV28).r*filmInside28*filmFace28;
        gl_FragColor.rgb=mix(gl_FragColor.rgb,filmLinear28,filmMix28);
        #include <encodings_fragment>`);
    };
    m.customProgramCacheKey=()=> 'fixed-film-surface-v28';copies.set(original,m);return m;
  }
  function decorate(o,index,groupIndex){
    const geo=o.geometry.index?o.geometry.toNonIndexed():o.geometry;
    const eligible=new Float32Array(geo.attributes.position.count);geo.setAttribute('filmEligible28',new T.BufferAttribute(eligible,1));o.geometry=geo;
    if(!(groupIndex?rgb1:rgb0).has(o.material.color.getHex()))return 0;
    const edges=spec.newEdges,[lo,hi]=edges.slice(index,index+2),angle=(lo+hi)/2,radial=[Math.sin(angle),Math.cos(angle)],radius=23.5*Math.cos((hi-lo)/2);
    const p=geo.attributes.position,a=new T.Vector3(),b=new T.Vector3(),c=new T.Vector3(),normal=new T.Vector3(),pos=new T.Vector3(),eye=new T.Vector3();let count=0;
    const native=(v,i)=>v.set(p.getX(i),-p.getZ(i),p.getY(i));
    for(let i=0;i<p.count;i+=3){
      native(a,i);native(b,i+1);native(c,i+2);pos.copy(a).add(b).add(c).multiplyScalar(1/3);normal.crossVectors(b.sub(a),c.sub(a)).normalize();
      const depth=radius-(pos.x-P.courtyardX)*radial[0]-(pos.y-P.courtyardY)*radial[1];eye.copy(C).sub(pos).normalize();
      if(depth>=spec.eligibleFrontDepth[0]&&depth<=spec.eligibleFrontDepth[1]&&pos.z>=spec.eligibleHeight[0]&&pos.z<=spec.eligibleHeight[1]&&normal.dot(eye)>=spec.facingMinimum){eligible.fill(1,i,i+3);count++;}
    }
    if(count){o.material=paintMaterial(o.material);evidence.selectedObjects++;evidence.selectedTriangles+=count;}
    return count;
  }
  return {decorate,evidence};
}
