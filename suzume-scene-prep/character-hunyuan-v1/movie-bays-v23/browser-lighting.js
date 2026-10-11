    // Native watts and these legacy WebGL light intensities use different units.
    // Treat this as a provisional preview until browser rendering is reviewed.
    const movieBaysLighting23=__MOVIE_BAYS_LIGHTING_23__;
    for(const spec of movieBaysLighting23.lights){
      let light;
      if(spec.type==='AREA'){
        light=new T.RectAreaLight(0xffffff,spec.powerWatts/(Math.PI*spec.dimensions[0]*spec.dimensions[1]),...spec.dimensions);
      }else{
        light=new T.SpotLight(0xffffff,spec.powerWatts/400,40,spec.angleRadians,spec.blend,2);
        light.castShadow=true;light.shadow.mapSize.set(1024,1024);light.shadow.camera.near=.5;light.shadow.camera.far=40;
        light.target.position.set(spec.target[0],spec.target[2],-spec.target[1]);scene.add(light.target);
      }
      light.name=spec.name;light.color.setRGB(...spec.color);
      light.position.set(spec.position[0],spec.position[2],-spec.position[1]);
      if(spec.type==='AREA')light.lookAt(spec.target[0],spec.target[2],-spec.target[1]);
      scene.add(light);
    }
