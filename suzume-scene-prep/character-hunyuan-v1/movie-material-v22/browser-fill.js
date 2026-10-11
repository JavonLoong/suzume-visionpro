    // Native watts and this WebGL renderer's radiance are not interchangeable.
    // This is a provisional browser approximation, pending visual comparison.
    const movieFacadeLight22 = __MOVIE_FACADE_LIGHT_22__;
    T.RectAreaLightUniformsLib.init();
    const courtyardFill22 = new T.RectAreaLight(0xffffff,
      movieFacadeLight22.powerWatts / (Math.PI * 110), 11, 10);
    courtyardFill22.name = 'Soft courtyard fill on the movie facade v22';
    courtyardFill22.color.setRGB(...movieFacadeLight22.color);
    const [fx, fy, fz] = movieFacadeLight22.position;
    const [tx, ty, tz] = movieFacadeLight22.target;
    courtyardFill22.position.set(fx, fz, -fy);
    courtyardFill22.lookAt(tx, tz, -ty);
    scene.add(courtyardFill22);
    root.movieMaterialEvidence22 = {
      revision: 22, roofProjectionCorrected: true, localPlasterMaterial: true,
      browserLightUnitEquivalenceVerified: false, areaLightCastsShadows: false,
      browserRuntimeVerified: false, oneToOneComplete: false
    };
