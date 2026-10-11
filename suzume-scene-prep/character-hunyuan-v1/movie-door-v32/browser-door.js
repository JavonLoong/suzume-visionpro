// Counteract the frame's X scale before rotating, then apply width in leaf space.
// Both portal copies keep the same hinge variables used by the existing animation.
function makeDoorLeafRigid32(T,leaf){
  if(leaf.userData.rigidLeafRevision===32)return leaf.parent;
  const frame=leaf.parent,scale=Math.abs(frame.scale.x);
  if(!Number.isFinite(scale)||scale<1e-6)throw Error('Invalid door width');
  const compensation=new T.Group();compensation.name='Rigid hinge compensation v32';
  compensation.scale.x=1/scale;frame.add(compensation);compensation.add(leaf);
  leaf.position.x*=scale;leaf.scale.x*=scale;leaf.userData.rigidLeafRevision=32;
  frame.updateMatrixWorld(true);return compensation;
}
