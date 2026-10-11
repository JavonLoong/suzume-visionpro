// Pure geometry math, also executed in Node for native/browser agreement.
function projectionGeometry24(spec){
  const p=spec.parameters,old=spec.oldEdges,edges=spec.newEdges,c=[p.courtyardX,p.courtyardY,0];
  function height(z,index){
    const raised=(index>=7&&index<=15)||(index>=18&&index<=26);
    const a=raised?[-.22,0,.73,.865,1.22,3.36,4.66,6.52]:[-.22,0,.73,.865,1.22,3.36,4.78];
    const b=raised?[-.22,0,1.33,1.47,p.windowSill,p.windowSill+2.14,p.arcadeBase,p.highRoof]:[-.22,0,1.33,1.47,p.windowSill,p.windowSill+2.14,p.lowRoof];
    let i=0;while(i<a.length-2&&z>=a[i+1])i++;
    return b[i]+(z-a[i])*(b[i+1]-b[i])/(a[i+1]-a[i]);
  }
  function source(v,architecture=true){
    const [x,y,z]=v,turn=Math.PI*2;let angle=((Math.atan2(x,y)-old[0])%turn+turn)%turn+old[0],i=0;
    while(i<31&&angle>=old[i+1])i++;
    const oa=(old[i]+old[i+1])/2,na=(edges[i]+edges[i+1])/2,oh=(old[i+1]-old[i])/2,nh=(edges[i+1]-edges[i])/2;
    const r=x*Math.sin(oa)+y*Math.cos(oa),front=23.5*Math.cos(oh)-r,nr=23.5*Math.cos(nh)-front;
    const u=(x*Math.cos(oa)-y*Math.sin(oa))*Math.tan(nh)/Math.tan(oh)*nr/Math.max(r,1e-6);
    let h=z;if(architecture){let t=Math.max(0,Math.min(1,(Math.hypot(x,y)-21.7)/.8));t=t*t*(3-2*t);h=z*(1-t)+height(z,i)*t;}
    return [nr*Math.sin(na)+u*Math.cos(na)+c[0],nr*Math.cos(na)-u*Math.sin(na)+c[1],h];
  }
  function newBay(v,index){return [v[0]+c[0],v[1]+c[1],height(v[2],index)];}
  return {source,newBay,height,center:c};
}
