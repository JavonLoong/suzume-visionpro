    const movieLightSpec27=__LIGHTING_SPEC_27__;
    const lightPoint27=p=>new T.Vector3(p[0],p[2],-p[1]);
    sun.position.copy(lightPoint27(movieLightSpec27.sunWorldPosition));sun.target.position.set(0,0,0);sun.intensity=movieLightSpec27.sunEnergy;
    for(const o of scene.children){
      if(o.isHemisphereLight)o.intensity=.42*movieLightSpec27.worldStrength/.7;
      if(o.isAmbientLight)o.intensity=.06*movieLightSpec27.worldStrength/.7;
    }
    const rightLight27=scene.children.find(o=>o.name==='Soft courtyard fill on the movie facade v22');
    rightLight27.position.copy(lightPoint27(movieLightSpec27.rightPosition));rightLight27.width=movieLightSpec27.rightSize[0];rightLight27.height=movieLightSpec27.rightSize[1];rightLight27.intensity=movieLightSpec27.rightFill/(Math.PI*rightLight27.width*rightLight27.height);rightLight27.color.setRGB(1,.92,.82);rightLight27.lookAt(lightPoint27(movieLightSpec27.rightTarget));
    const leftLight27=scene.children.find(o=>o.name==='Cool courtyard fill on the left facade v23');
    leftLight27.intensity=movieLightSpec27.leftFill/(Math.PI*leftLight27.width*leftLight27.height);leftLight27.color.setRGB(...movieLightSpec27.leftColor);
    const archLight27=scene.children.find(o=>o.name==='Localized sunlight around the arched window v23');archLight27.intensity=movieLightSpec27.archSpot/400;
    root.lightingEvidence27={revision:27,source:'Four native lighting trials followed by full front and oblique review',sunWorldSpaceMatched:true,localFacadeFill:true,browserSkyColorRetainsPreviousCalibration:true,browserRuntimeVerified:false,oneToOneComplete:false};
