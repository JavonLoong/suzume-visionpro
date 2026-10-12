"""Run with Blender's Python, which bundles OpenUSD. Validate packages, then round-trip to GLB."""
from pathlib import Path
import bpy,json,hashlib,zipfile,struct
from pxr import Usd,UsdGeom,UsdShade,UsdUtils
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'VisionProPortal'/'VisionProPortal'/'Resources'
OUT=ROOT/'validation'
PREVIEW=ROOT/'preview-assets';PREVIEW.mkdir(exist_ok=True)
manifest=json.loads((RES/'AssetManifest.json').read_text(encoding='utf-8'))
report={'assets':{},'xcodeCompiled':False,'headsetTested':False,'sourceUnmodified':False}
report['sourceUnmodified']=hashlib.sha256(Path(manifest['source']).read_bytes()).hexdigest()==manifest['sourceSHA256']
assert report['sourceUnmodified']
for name in ('DreamWorld','DoorFrame','DoorLeaf','Character'):
    path=RES/(name+'.usdz')
    stage=Usd.Stage.Open(str(path));assert stage
    assert str(UsdGeom.GetStageUpAxis(stage))=='Y'
    assert abs(UsdGeom.GetStageMetersPerUnit(stage)-1)<1e-6
    meshes=[];images=[]
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_])
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            m=UsdGeom.Mesh(prim);points=m.GetPointsAttr().Get();counts=m.GetFaceVertexCountsAttr().Get()
            assert len(points)>0 and len(counts)>0
            box=cache.ComputeWorldBound(prim).ComputeAlignedRange()
            meshes.append({'path':str(prim.GetPath()),'vertices':len(points),'triangles':sum(n-2 for n in counts),'bounds':[list(box.GetMin()),list(box.GetMax())]})
        for attr in prim.GetAttributes():
            if str(attr.GetTypeName())=='asset':
                value=attr.Get()
                if value and value.path:
                    assert value.resolvedPath, (prim.GetPath(),value)
                    images.append(value.path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        with path.open('rb') as stream:
            for item in z.infolist():
                assert item.compress_type==zipfile.ZIP_STORED
                stream.seek(item.header_offset+26)
                n,x=struct.unpack('<HH',stream.read(4))
                assert (item.header_offset+30+n+x)%64==0
    check=UsdUtils.ComplianceChecker(arkit=True,rootPackageOnly=False,skipARKitRootLayerCheck=False)
    check.CheckCompliance(str(path))
    errors=list(check.GetErrors());failed=list(check.GetFailedChecks());warnings=list(check.GetWarnings())
    row={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'upAxis':'Y','metersPerUnit':1,
         'triangles':sum(m['triangles'] for m in meshes),'meshes':meshes,'textures':images,
         'complianceErrors':errors,'complianceFailedChecks':failed,'complianceWarnings':warnings}
    report['assets'][name]=row
    if name=='DreamWorld':
        ground=next(m for m in meshes if '/NearMeadow/' in m['path'])
        lo,hi=ground['bounds']
        assert hi[1]-lo[1]<20 and hi[2]-lo[2]>100, 'Ground must be horizontal in the exported Y-up coordinates'
    if name=='Character':
        lo=[min(m['bounds'][0][axis] for m in meshes) for axis in range(3)]
        hi=[max(m['bounds'][1][axis] for m in meshes) for axis in range(3)]
        height=hi[1]-lo[1]
        assert 1.60 <= height <= 1.64, f'Character height must be 1.62 m, got {height}'
        assert row['triangles'] < 100000, f'Character budget exceeded: {row["triangles"]}'
    print('USD_VALIDATED',name,'triangles',row['triangles'],'failed',len(failed),'errors',len(errors),flush=True)
    if errors or failed: print(json.dumps({'errors':errors,'failed':failed},ensure_ascii=True),flush=True)
    assert not errors and not failed,(name,errors,failed)
    # Import the delivered USDZ, not Blender's pre-export scene, for the desktop preview.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=str(path))
    bpy.ops.export_scene.gltf(filepath=str(PREVIEW/(name+'.glb')),export_format='GLB',export_animations=False,export_yup=True)
(OUT/'asset_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ALL_ASSETS_VALID',flush=True)
