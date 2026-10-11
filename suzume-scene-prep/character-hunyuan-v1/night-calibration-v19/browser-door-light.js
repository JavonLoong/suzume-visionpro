    // Warm courtyard illumination entering the open aperture. This is a local
    // source in the otherworld, so its falloff follows the entered character.
    const doorwayDaylight=new T.SpotLight(0xffedde,0,11,1.15,.30,2);
    doorwayDaylight.name='Daylight admitted through the doorway';
    doorwayDaylight.position.set(0,1.78,.18);
    doorwayDaylight.target.position.set(0,1.78,-3.2);
    doorwayDaylight.castShadow=true;
    doorwayDaylight.shadow.mapSize.set(1024,1024);
    doorwayDaylight.shadow.bias=-.0002;
    doorwayDaylight.shadow.normalBias=.015;
    nightScene.add(doorwayDaylight,doorwayDaylight.target);
    root.doorwayLightEvidence={revision:19,type:'Localized spotlight approximation of admitted courtyard light',
      followsDoorOpening:true,affectsOtherworldOnly:true,browserVisuallyVerified:false};
