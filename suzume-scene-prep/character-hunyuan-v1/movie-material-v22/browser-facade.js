// Apply the native facade correction before its meshes are baked to world space.
function refineMovieBay22(T, group, materials, fit) {
  const plaster = materials.sunWall.clone();
  plaster.name = 'Movie pale plaster v22';
  plaster.color.setHex(0xf1eee6);
  const trim = materials.cornice.clone();
  trim.name = 'Movie warm stone trim v22';
  trim.color.setHex(0xe9e5d7);
  const glazing = materials.windowMat.clone();
  glazing.name = 'Movie shaded glazing v22';
  glazing.color.setHex(0x213040);
  const frame = materials.mullionMat.clone();
  frame.name = 'Movie aged window frame v22';
  frame.color.setHex(0x777562);
  group.traverse(o => {
    if (!o.isMesh) return;
    if (o.material === materials.sunWall) o.material = plaster;
    else if (o.material === materials.cornice) o.material = trim;
    else if (o.material === materials.windowMat) o.material = glazing;
    else if (o.material === materials.mullionMat) o.material = frame;
    if (o.name === 'Upper cornice') {
      o.scale.z = .30 / .70;
      o.position.z = .025;
    } else if (o.name === 'Upper wall shadow course') {
      o.scale.z = .20 / .55;
      o.position.z = .025;
    } else if (o.name === 'Roof slab') {
      const p = o.geometry.attributes.position;
      // The slab's shape is in XY before its rotation to the horizontal plane.
      for (let i = 0; i < p.count; i++) {
        const oldFront = p.getY(i);
        const front = -4.595 + (oldFront + 4.595) * (4.595 + .12) / (4.595 + .355);
        p.setXY(i, p.getX(i) * (fit.chordRadius - front) / (fit.chordRadius - oldFront), front);
      }
      p.needsUpdate = true;
      o.geometry.computeVertexNormals();
      o.geometry.computeBoundingBox();
      o.geometry.computeBoundingSphere();
    }
  });
  group.updateMatrixWorld(true);
}
