from pathlib import Path
R=Path(__file__).parent;O=R/'poster-right-bow-v56'
source=(R/'poster-right-arches-v55/verify-browser-right-arches.cjs').read_text()
prefix=source.split(' const targets=new Map(),mats=new Map();')[0]
prefix=prefix.replace('browser-right-arches-v55.json','browser-right-bow-v56.json').replace('right-arches-v55.bin','right-bow-v56.bin')
prefix=prefix.replace("'poster-right-arches-v55/browser-right-arches.js']","'poster-right-arches-v55/browser-right-arches.js','poster-right-bow-v56/browser-right-bow.js']")
body=r'''
 await sandbox.applyPosterRightArches55(T,scene,evidence);
 const targets=new Map(),mats=new Map();let disposed=0;
 for(const q of spec.targets){const ob=scene.getObjectByName(q.name);assert(ob);targets.set(q.key,ob);mats.set(q.key,ob.material);ob.geometry.addEventListener('dispose',()=>disposed++);}
 const surfaceUpdates=new Map(spec.surfaceUpdates.map(q=>[q.browserTarget,q]));assert.equal(surfaceUpdates.size,2);
 const untouched=[];scene.traverse(ob=>{if(ob!==scene&&!Array.from(targets.values()).includes(ob))untouched.push([ob,ob.parent,ob.geometry,ob.material,ob.matrix.clone()]);});
 const currentIvy=scene.getObjectByName(ivy.name),ivyMatrices=currentIvy.instanceMatrix.array.slice(),ivyColors=currentIvy.instanceColor.array.slice();
 await sandbox.applyPosterRightBow56(T,scene,evidence);assert.equal(disposed,2);for(const ob of targets.values())assert.strictEqual(ob.parent,null);
 for(const [ob,parent,geometry,material,matrix] of untouched){assert.strictEqual(ob.parent,parent);assert.strictEqual(ob.geometry,geometry);assert(ob.matrix.equals(matrix));if(surfaceUpdates.has(ob.name)){const q=surfaceUpdates.get(ob.name);assert.notStrictEqual(ob.material,material);assert.equal(ob.material.type,material.type);assert.equal(ob.material.map.userData.sourceURL,'../poster-right-bow-v56/'+q.newAtlas);assert.equal(ob.material.map.encoding,T.sRGBEncoding);assert.equal(ob.material.toneMapped,material.toneMapped);assert.equal(ob.material.fog,material.fog);}else assert.strictEqual(ob.material,material);}
 assert.strictEqual(scene.getObjectByName(ivy.name),currentIvy);assert.deepStrictEqual(currentIvy.instanceMatrix.array,ivyMatrices);assert.deepStrictEqual(currentIvy.instanceColor.array,ivyColors);
 const group=scene.getObjectByName('Poster measured right bow v56');assert.equal(group.children.length,3);let triangles=0;
 for(const q of spec.buckets){
  const ob=group.getObjectByName('Poster right bow '+q.key+' v56');assert(ob.castShadow&&ob.receiveShadow);assert(ob.matrix.equals(new T.Matrix4()));
  for(const [name,offset,width] of [['position',0,3],['normal',3,3],['uv',6,2]]){const a=ob.geometry.attributes[name].array;assert.equal(a.length,q.vertexCount*width);for(let i=0;i<q.vertexCount;i++)for(let j=0;j<width;j++)assert.equal(a[i*width+j],raw.readFloatLE(q.byteOffset+(i*8+offset+j)*4));}
  if(q.reuseTargetMaterial)assert.strictEqual(ob.material,mats.get(q.reuseTargetMaterial));else{assert(ob.material.isMeshBasicMaterial);assert.equal(ob.material.toneMapped,false);assert.equal(ob.material.fog,false);assert.equal(ob.material.map.userData.sourceURL,'../poster-right-bow-v56/right-bow-paint-v56.png');assert.equal(ob.material.map.encoding,T.sRGBEncoding);assert.equal(ob.material.map.wrapS,T.ClampToEdgeWrapping);assert.equal(ob.material.map.wrapT,T.ClampToEdgeWrapping);}
  triangles+=q.vertexCount/3;
 }
 const html=fs.readFileSync(path.join(root,'viewer/poster-v56.html'),'utf8');let scripts=0;for(const q of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(q[2].trim()){new vm.Script(q[2]);scripts++;}
 const calls=['applyPosterSteel44','applyPosterRailings46','applyPosterFascia47','applyPosterUpperWindows48','applyPosterArches49','applyPosterLowerFacade50','applyPosterForeground51','applyPosterGround52','applyPosterLowRails53','applyPosterRightFacade54','applyPosterRightArches55','applyPosterRightBow56'].map(s=>'await '+s+'(T,scene,root);');
 for(let i=0;i<calls.length;i++){assert(html.includes(calls[i]));if(i)assert(html.indexOf(calls[i])>html.indexOf(calls[i-1]));}assert(html.includes('suzume-poster-view-v56'));assert.equal(triangles,spec.triangles);assert.equal(triangles,36240);
 const report={revision:56,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,triangles,buckets:spec.buckets.length,previousBucketsReplaced:spec.targets.length,positionsNormalsAndUVsMatchNativeExactly:true,previousUnaffectedGeometryAndMaterialsPreserved:true,allIvyMatricesAndColorsPreservedExactly:true,existingSteelMaterialInstancesReused:true,newBeamPaintIsolated:true,surfaceTexturesReplacedWithoutGeometryChanges:true,browserRuntimeVerified:false,browserMaterialsApproximate:true,scope:'Actual Three.js construction and chained v44, v46-v56 data loading in Node. Two facade textures explicitly restored, other materials preserved. PNG bytes checked with a texture-loader shim; no browser/GPU rendering.'};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v56.json'),JSON.stringify(report,null,2));console.log('RIGHT_BOW_56_BROWSER_DATA_VERIFIED',triangles);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
(O/'verify-browser-right-bow.cjs').write_text(prefix+body,encoding='utf-8')
print('RIGHT_BOW_56_BROWSER_CHECK_PREPARED')
