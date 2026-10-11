// Numerical mesh/material checks; no claim of browser or GPU rendering validation.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-surfaces-v28'),P24=path.join(R,'movie-projection-v24'),T=require(path.join(R,'viewer/three.min.js'));
const read=(p)=>JSON.parse(fs.readFileSync(p,'utf8'));
const spec=read(path.join(O,'surface-spec-v28.json')),projection=read(path.join(P24,'projection-spec-v24.json')),audit=read(path.join(O,'integration-v28.json'));
spec.newEdges=projection.newEdges;
const scene=new T.Scene(),ctx={T,spec,projection,scene};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(P24,'browser-geometry.js'),'utf8')+'\n'+fs.readFileSync(path.join(O,'browser-surfaces.js'),'utf8')+'\nthis.math=projectionGeometry24(projection);this.painter=createFilmSurfacePainter28(T,spec,new T.Texture(),new T.Texture());',ctx);
const html=fs.readFileSync(path.join(R,'viewer/candidate-v28.html'),'utf8');
const bake=html.slice(html.indexOf('function bake(group){'),html.indexOf('const skyCoefficients='));vm.runInContext(bake,ctx);
const counts={},expected={},roles={sunWall:0xf1eee6,cornice:0xe9e5d7,damp:0x708c83,roomMat:0x354947,mullionMat:0x777562,iron:0x655448,ironEdge:0xa98962,windowMat:0x213040};
for(const row of audit.selectedObjects)expected[row.bay]=(expected[row.bay]||0)+row.polygons.length;
let materialChecks=0;
for(const [gi,file] of ['bay-geometry-v24.json','right-geometry-v24.json'].entries()){
  const D=read(path.join(P24,file)),mats={},group=new T.Group();scene.add(group);
  for(const rec of D.meshes){
    const index=rec.bay===undefined?16:rec.bay;
    if(!mats[rec.material])mats[rec.material]=new T.MeshStandardMaterial({color:gi?roles[rec.material]:D.materials[rec.material].sourceHex});
    const g=new T.BufferGeometry(),position=Float32Array.from(rec.positions);
    for(let i=0;i<position.length;i+=3){const v=ctx.math.newBay([position[i],-position[i+2],position[i+1]],index);position[i]=v[0];position[i+1]=v[2];position[i+2]=-v[1];}
    g.setAttribute('position',new T.BufferAttribute(position,3));g.computeVertexNormals();if(rec.uv)g.setAttribute('uv',new T.Float32BufferAttribute(rec.uv,2));
    const o=new T.Mesh(g,mats[rec.material]);group.add(o);const count=ctx.painter.decorate(o,index,gi);counts[index]=(counts[index]||0)+count;
    if(count&&materialChecks===0){
      const shader={uniforms:{},vertexShader:T.ShaderLib.standard.vertexShader,fragmentShader:T.ShaderLib.standard.fragmentShader};o.material.onBeforeCompile(shader);
      assert(shader.vertexShader.includes('filmWorld28=(modelMatrix*vec4(transformed,1.0)).xyz'));
      assert(shader.fragmentShader.indexOf('gl_FragColor.rgb=mix')<shader.fragmentShader.indexOf('#include <encodings_fragment>'));
      assert(shader.fragmentShader.indexOf('#include <tonemapping_fragment>')<shader.fragmentShader.indexOf('gl_FragColor.rgb=mix'));
      assert.strictEqual(shader.uniforms.filmCamera28.value.y,-spec.projection.distance);materialChecks++;
    }
  }
  ctx.bake(group);
}
assert.deepStrictEqual(counts,expected);assert.strictEqual(ctx.painter.evidence.selectedTriangles,audit.selectedPolygonCount);
let attrTotal=0;scene.traverse(o=>{if(o.isMesh&&o.geometry.attributes.filmEligible28){const a=o.geometry.attributes.filmEligible28.array;for(const v of a)attrTotal+=v;}});
assert.strictEqual(attrTotal/3,audit.selectedPolygonCount);
let scripts=0;for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim()){new vm.Script(m[1]);scripts++;}
assert(html.indexOf('const filmPainter28=')<html.indexOf('const groups24='));assert(html.includes('filmPainter28.decorate(o,index,gi)'));assert(html.includes('suzume-movie-view-v28'));
const result={revision:28,selectedNativeAndBrowserTrianglesMatch:true,selectedTriangles:audit.selectedPolygonCount,trianglesByBay:counts,eligibilityAttributePreservedAfterActualBake:true,shaderInsertionAndFixedCameraUniformsChecked:true,inlineScriptsParsed:scripts,browserRuntimeVerified:false,oneToOneComplete:false};
fs.writeFileSync(path.join(O,'browser-verification-v28.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
