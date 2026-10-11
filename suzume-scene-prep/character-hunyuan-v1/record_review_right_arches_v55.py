from pathlib import Path
import hashlib
import json
import sys

assert '--reviewed' in sys.argv, 'Inspect all five current renders before recording review.'
R = Path(__file__).parent
O = R / 'poster-right-arches-v55'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
v = read(O / 'verification-v55.json')
prior = read(R / 'poster-right-facade-v54/visual-review-v54.json')
native = O / 'Suzume_dual_scene_right_arches_v55.blend'
assert sha(native) == v['nativeSha256']
names = ['poster-front-v55.png', 'right-arches-detail-v55.png',
         'poster-oblique-v55.png', 'right-arches-oblique-detail-v55.png',
         'right-arches-comparison-v55.png']
for name in names:
    assert (O / name).stat().st_mtime > native.stat().st_mtime
remaining = [
    'Reconstruct materials in previously occluded regions for rotated views. The close oblique still exposes blurred foreground-post/beam exclusion patches, and the boundary into the unmodified neighboring bay is visibly approximate.',
    'Refine right arcade glazing/grilles, gray backing, chipped cap edges and concealed room depth. Ten large caps follow measured reference boundaries; partially occluded bases, infill and hidden construction remain inferred.',
    'Correct the right foreground curved steel beam: it remains visibly too thick and dark against the reference. Refine its profile, pale edges, corrosion and irregular damage.',
    *[q for q in prior['remaining'] if not q.startswith('Rebuild the right upper arcade')],
]
review = {
    'revision': 55, 'nativeSha256': v['nativeSha256'],
    'frontReviewed': True, 'detailReviewed': True,
    'obliqueReviewed': True, 'obliqueDetailReviewed': True,
    'referenceComparisonReviewed': True,
    'acceptedAsIncrementalImprovement': True,
    'observations': [
        'The right upper storey now uses a continuous curved wall with ten large arches, five small arched recesses, one pointed arch and a broad gray recess with a broken masonry stub. This replaces the generic black arch openings. Each modeled surround, bead, infill and wall has depth; no camera-facing cards were introduced.',
        'Large arch caps were fitted to visible dark boundaries in the reference. The lower cornice and crown use varying-height profiles rather than uniform horizontal strips. A roof transition joins the new crown to the existing roof at Z=5.94 m. Foreground-beam-occluded bases and unobserved sections are inferred.',
        'Fifty-five closed solid assemblies contain 302028 triangles. The saved/reopened geometry has positive signed volume, no non-manifold edges and maximum vertex error below 2 micrometers. Seventeen probes verify structural recess clearance, nine verify contact with the lower walls and nine verify the rear roof transition.',
        'Nine original mesh buckets were trimmed at explicit replacement volumes. Their unaffected triangle positions and UVs remain unchanged. Two prior v54 flat cornices were replaced; all other v54 right facade assemblies remain preserved.',
        'An isolated texture restores 4714 visible source pixels (4712 changed pixel values) around the rightmost caps and cornice that an old vertical-post exclusion mask had blurred. The true foreground-beam exclusion is retained and every pixel outside the patch is unchanged.',
        'The full front, cropped detail, close oblique, full opposite-side oblique and equal-resolution reference/before/after comparison were inspected. The new arcade is an incremental geometric improvement; the oversized dark foreground beam, coarse ivy, foreground equipment and broader material differences remain visible.',
        'Movie and night scenes, shared node groups, unaffected poster objects, camera, lighting and materials are preserved. All 24 previously packed images retain their exact bytes; the corrected arcade atlas adds one packed image.',
        'The actual Three.js construction chain through v55 was executed in Node. Twelve prior geometry buckets are replaced by fifteen native-exported buckets containing 436961 triangles. Positions, normals and UVs match the native data; untouched geometry/materials and ivy matrices/colors are preserved. All 38 HTTP resources match local bytes.',
        'Browser/GPU display remains unverified. The v55 control inventory attempt via cua.getState timed out after 20 seconds and reset its kernel. Node construction and HTTP checks do not establish browser appearance equivalence.',
    ],
    'remaining': remaining, 'browserRuntimeVerified': False,
    'nativeBrowserAppearanceEquivalenceVerified': False,
    'oneToOneComplete': False,
    'reviewedImageSha256': {name: sha(O / name) for name in names},
}
(O / 'visual-review-v55.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
print('RIGHT_ARCHES_55_REVIEW_RECORDED', v['nativeSha256'])
