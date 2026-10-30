import bpy, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / 'character-hunyuan-v1' / 'poster-right-bow-v56'
results = []
pending = [folder / name for name in ['Suzume_dual_scene_right_bow_v56.blend', '铃芽之旅_v56_中文版.blend']]
visited = set()
while pending:
    file = pending.pop(0).resolve()
    if file in visited:
        continue
    visited.add(file)
    bpy.ops.wm.open_mainfile(filepath=str(file))
    paths = sorted(set(bpy.path.abspath(p) for p in bpy.utils.blend_paths(absolute=True, packed=False)))
    results.append({'file': str(file), 'scenes': [{'name': s.name, 'objects': len(s.objects)} for s in bpy.data.scenes], 'externalPaths': paths,
        'unpackedImages': [{'name': im.name, 'source': im.source, 'path': bpy.path.abspath(im.filepath)} for im in bpy.data.images if im.source == 'FILE' and not im.packed_file]})
    pending.extend(Path(p) for p in paths if Path(p).suffix == '.blend' and Path(p).is_file())
(Path(__file__).parent / 'blend-dependencies.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('LATEST_BLEND_DEPENDENCIES', json.dumps(results, ensure_ascii=False))
