    // Each world retains exactly one half-space of the same posed surface.
    // This is world-space clipping, so orbiting cannot reveal the other half.
    renderer.localClippingEnabled=true;
    const courtyardHalf=new T.Plane(),otherworldHalf=new T.Plane();
    const gatePoint=new T.Vector3(),gateNormal=new T.Vector3(),gateNormalMatrix=new T.Matrix3();
    function updateFigure(){
      portal.updateMatrixWorld(true);
      gatePoint.setFromMatrixPosition(portal.matrixWorld);
      gateNormal.set(0,0,1).applyMatrix3(gateNormalMatrix.getNormalMatrix(portal.matrixWorld)).normalize();
      courtyardHalf.setFromNormalAndCoplanarPoint(gateNormal,gatePoint);
      otherworldHalf.copy(courtyardHalf).negate();
    }
    updateFigure();
    function partitionMaterials(group,plane,label){
      const materials=new Map();
      group.traverse(o=>{if(!o.isMesh)return;
        function clone(original){
          if(!materials.has(original)){
            const m=original.clone();m.name=original.name+' — '+label;
            m.clippingPlanes=[plane];m.clipIntersection=false;m.clipShadows=true;
            materials.set(original,m);
          }
          return materials.get(original);
        }
        o.material=Array.isArray(o.material)?o.material.map(clone):clone(o.material);
      });
    }
    partitionMaterials(character,courtyardHalf,'courtyard half');
    partitionMaterials(nightCharacter,otherworldHalf,'otherworld half');
    root.portalPartitionEvidence=()=>{
      character.updateMatrixWorld(true);
      let courtyardVertices=0,otherworldVertices=0,crossingTriangles=0;
      const v=new T.Vector3();
      character.traverse(o=>{if(!o.isMesh)return;
        const p=o.geometry.attributes.position,idx=o.geometry.index,signs=new Int8Array(p.count);
        for(let i=0;i<p.count;i++){
          v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);
          signs[i]=courtyardHalf.distanceToPoint(v)>=0?1:-1;
          if(signs[i]>0)courtyardVertices++;else otherworldVertices++;
        }
        const count=idx?idx.count:p.count;
        for(let i=0;i<count;i+=3){const a=idx?idx.getX(i):i,b=idx?idx.getX(i+1):i+1,c=idx?idx.getX(i+2):i+2;if(signs[a]!==signs[b]||signs[a]!==signs[c])crossingTriangles++;}
      });
      return {method:'Complementary world-space half-planes at the portal aperture',courtyardPlane:[...courtyardHalf.normal.toArray(),courtyardHalf.constant],otherworldPlane:[...otherworldHalf.normal.toArray(),otherworldHalf.constant],courtyardVertices,otherworldVertices,crossingTriangles,localClippingEnabled:renderer.localClippingEnabled,shadowClipping:true};
    };
