// Pure Three.js model comparison; no browser automation or runtime claim.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=__dirname,O=path.join(R,'movie-bays-v23'),T=require(path.join(R,'viewer/three.min.js'));
const fit=JSON.parse(fs.readFileSync(path.join(O,'bay-fit-v23.json'),'utf8'));
const movie=JSON.parse(fs.readFileSync(path.join(R,'movie-calibration-v20/courtyard-fit-v20.json'),'utf8'));
const native=JSON.parse(fs.readFileSync(path.join(O,'native-lower-walls-v23.json'),'utf8'));
const resources={stoneMap:null,rustMap:null,paintMap:null,brass:new T.MeshStandardMaterial({color:0xbda457}),moss:new T.MeshStandardMaterial({color:0x536b35})};
const context={T,scene:new T.Scene(),fit,resources};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(O,'build_bays.js'),'utf8')+'\nthis.group=buildMovieBays23(T,scene,fit,resources);',context);
const p=movie.parameters,k=movie.depthScale,C=movie.depthScaleCenter,cy=Math.cos(p.yaw),sy=Math.sin(p.yaw);
const top=C[2]+k*(.89*p.heightScale+p.heightOffset-C[2]);
const walls=[];context.group.traverse(o=>{if(o.userData.geometryRole23==='lowerWall')walls.push(o);});
assert.strictEqual(walls.length,4);
const evidence=[];
for(const wall of walls){
  const index=wall.parent.userData.bayIndex23,expected=native[index],b=fit.bays.find(b=>b.index===index);
  const geometry=wall.geometry.index?wall.geometry.toNonIndexed():wall.geometry.clone();geometry.applyMatrix4(wall.matrixWorld);
  const a=geometry.attributes.position;assert.strictEqual(a.count,expected.length);let maxError=0;
  for(let i=0;i<a.count;i++){
    const x=a.getX(i),y=a.getY(i),z=a.getZ(i);
    const height=y>=.89?C[2]+k*(y*p.heightScale+p.heightOffset-C[2]):-.22+(y+.22)*(top+.22)/1.11;
    const world=[C[0]+k*(cy*x-sy*z+p.translateX-C[0]),C[1]+k*(-sy*x-cy*z+p.translateY-C[1]),height];
    for(let j=0;j<3;j++)maxError=Math.max(maxError,Math.abs(world[j]-expected[i][j]));
  }
  assert(maxError<.0001);
  const rayChecks=[];
  for(const q of b.openings){
    const point=new T.Vector3(q.x,q.bottom+q.height*.4,3).applyMatrix4(wall.matrixWorld);
    const normal=new T.Vector3(0,0,-1).transformDirection(wall.matrixWorld);
    const hits=new T.Raycaster(point,normal,0,10).intersectObject(wall,false);assert.strictEqual(hits.length,0);
    rayChecks.push(q.name);
  }
  evidence.push({bay:index,vertices:a.count,maximumNativeDifference:maxError,actualWindowOpenings:rayChecks});
}
const html=fs.readFileSync(path.join(R,'viewer/candidate-v23.html'),'utf8');
assert(html.indexOf('const movieBayFit23=')<html.indexOf('const movieWindowFit21='));
assert(html.includes("o.name.startsWith('Movie rebuilt left and central bays v23 solid mesh')"));
const result={revision:23,nativeLowerWallGeometryMatches:true,properReplacementOrder:true,independentPrefixProtectsRightBay:true,walls:evidence,browserRuntimeVerified:false};
fs.writeFileSync(path.join(O,'browser-geometry-verification-v23.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
