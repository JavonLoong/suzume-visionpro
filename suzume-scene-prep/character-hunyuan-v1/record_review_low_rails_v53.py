from pathlib import Path
import json,hashlib,sys
assert '--reviewed' in sys.argv,'Inspect the five current rendered images before recording review.'
R=Path(__file__).parent;O=R/'poster-low-rails-v53';v=json.loads((O/'verification-v53.json').read_text());prior=json.loads((R/'poster-ground-v52/visual-review-v52.json').read_text());native=O/'Suzume_dual_scene_low_rails_v53.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(native)==v['nativeSha256']
names=['poster-front-v53.png','low-rails-detail-v53.png','poster-oblique-v53.png','low-rails-oblique-detail-v53.png','low-rails-comparison-v53.png']
for name in names:assert (O/name).stat().st_mtime>native.stat().st_mtime
remaining=[
 'Refine the broken low frame paint, corrosion, short board damage and concealed connections. Its identity is ambiguous in the single reference, and its depth and rear structure remain inferred.',
 *prior['remaining'][1:3],
 'Refine chair frame/seat wear, pipe corrosion and bends, strap weathering and nearby fragments. The chair interpretation and concealed construction remain inferred from one partly occluded view.',
 *prior['remaining'][4:]]
review={'revision':53,'nativeSha256':v['nativeSha256'],'frontReviewed':True,'detailReviewed':True,'obliqueReviewed':True,'obliqueDetailReviewed':True,'referenceComparisonReviewed':True,'acceptedAsIncrementalImprovement':True,'observations':[
 'Seven original brick boxes, 84 triangles in two debris meshes, were removed from the waterline in front of the new shallow bank. Every retained original face position and UV survives the saved/reopened file unchanged. The central door debris and all unselected bricks remain.',
 'The left low frame has seven traced rail/edge paths, four short solid boards and six ground-bearing legs with shoes. The entry horizontals were identified as stair edges and are not duplicated with an invented railing. The visible screen-space paths are matched, but furniture identity, rear connections and depth remain inferred.',
 'An initial depth estimate put some left support feet beyond the sediment bank. Their depths were revised while retaining the observed projection. All six frame feet and three pipe-support feet are now verified against actual native ground surfaces with a 1 mm center gap and slightly embedded shoe bottoms.',
 'Three exposed curved straps, flat uprights, foot shoes and bolts were added to the old horizontal pipe. An initial strap bore left a 19 mm radial gap. The bore was corrected to 154 mm against the 155 mm pipe radius; native surface probes confirm approximately 1 mm overlap. Existing pipe and collars are unchanged.',
 'The final detail and reference comparison remove the conspicuous brown stubs and add slender frame silhouettes and pipe support accents. The side view confirms volumetric fixtures and the grounded support arrangement. Overall texture, paint wear, vegetation, water and neighboring facade discrepancies remain visible.',
 '38 closed solids contain 5036 new triangles. Saved/reopened coordinates, vertex colors, manifold edges and positive volumes are verified. Movie and night scenes, all existing vegetation, shared node groups, unaffected poster geometry/materials/camera/lighting and all 23 packed images are preserved.',
 'The actual Three.js construction chain from v44 and v46 through v53 ran in Node. Five exported geometry buckets replace two original debris buckets and add the new fixtures. Native positions, normals, UVs and colors match exactly, and unaffected objects, reusable materials and all surviving original ivy matrices/colors remain unchanged. All 32 required HTTP resources match local bytes.',
 'A fresh browser inventory attempt timed out after 20 seconds in v53. Node construction, HTTP delivery and native renders are verified; browser/GPU appearance and interaction remain unverified.'
 ],'remaining':remaining,'browserRuntimeVerified':False,'nativeBrowserAppearanceEquivalenceVerified':False,'oneToOneComplete':False,'reviewedImageSha256':{name:sha(O/name) for name in names}}
(O/'visual-review-v53.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8');print('LOW_RAILS_53_REVIEW_RECORDED',v['nativeSha256'])
