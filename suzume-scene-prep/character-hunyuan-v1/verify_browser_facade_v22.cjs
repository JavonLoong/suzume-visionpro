// Pure geometry/library checks; this does not launch or automate a browser.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const R = __dirname, O = path.join(R, 'movie-material-v22');
const T = require(path.join(R, 'viewer', 'three.min.js'));
const fit = JSON.parse(fs.readFileSync(path.join(R, 'movie-windows-v21', 'window-fit-v21.json'), 'utf8'));
const movie = JSON.parse(fs.readFileSync(path.join(R, 'movie-calibration-v20', 'courtyard-fit-v20.json'), 'utf8'));
const source = JSON.parse(fs.readFileSync(path.join(O, 'native-roof-geometry-v22.json'), 'utf8'));
const roles = ['sunWall','cornice','damp','roomMat','mullionMat','iron','ironEdge','windowMat'];
const materials = Object.fromEntries(roles.map(role => [role, new T.MeshStandardMaterial({color:0xffffff})]));
const context = {T, THREE:T, scene:new T.Scene(), materials, fit};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(R, 'viewer', 'RectAreaLightUniformsLib.js'), 'utf8'), context);
T.RectAreaLightUniformsLib.init();
assert(T.UniformsLib.LTC_FLOAT_1 && T.UniformsLib.LTC_FLOAT_2);
vm.runInContext(fs.readFileSync(path.join(R, 'movie-windows-v21', 'build_bay.js'), 'utf8') +
  fs.readFileSync(path.join(O, 'browser-facade.js'), 'utf8') +
  '\nthis.group=buildMovieBay21(T,scene,materials,fit);', context);
const group = context.group;
const wall = group.getObjectByName('Solid plaster wall with two through-openings');
const wallBefore = Array.from(wall.geometry.attributes.position.array);
vm.runInContext('refineMovieBay22(T,group,materials,fit);', context);
assert.deepStrictEqual(Array.from(wall.geometry.attributes.position.array), wallBefore);
assert.strictEqual(materials.sunWall.color.getHex(), 0xffffff);
assert.strictEqual(wall.material.color.getHex(), 0xf1eee6);
const p = movie.parameters, k = movie.depthScale, C = movie.depthScaleCenter;
const yaw = p.yaw, cy = Math.cos(yaw), sy = Math.sin(yaw), evidence = [];
for (const [name, expected] of Object.entries(source)) {
  const object = group.getObjectByName(name);
  const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
  geometry.applyMatrix4(object.matrixWorld);
  const a = geometry.attributes.position;
  assert.strictEqual(a.count, expected.length);
  let maxError = 0;
  for (let i=0; i<a.count; i++) {
    const x=a.getX(i), y=a.getY(i), z=a.getZ(i);
    const world = [
      C[0]+k*(cy*x-sy*z+p.translateX-C[0]),
      C[1]+k*(-sy*x-cy*z+p.translateY-C[1]),
      C[2]+k*(y*p.heightScale+p.heightOffset-C[2])
    ];
    for (let j=0;j<3;j++) maxError=Math.max(maxError,Math.abs(world[j]-expected[i][j]));
  }
  assert(maxError < .0001, `${name}: ${maxError}`);
  evidence.push({part:name, vertices:a.count, maximumNativeDifference:maxError});
}
const result = {revision:22, libraryRevision:T.REVISION, ltcTexturesInitialized:true,
  nativeRoofGeometryMatches:true, roof:evidence, wallGeometryPreserved:true,
  clonedPlasterDoesNotModifyOtherBays:true, browserRuntimeVerified:false};
fs.writeFileSync(path.join(O,'browser-geometry-verification-v22.json'), JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
