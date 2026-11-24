"""Build a flat, four-quadrant base compatible with the delivered WM2 parts."""
import hashlib, json, math, sys, zipfile
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
OLD = PROJECT / 'print-400mm-20261030'
QUALITY = PROJECT / 'print-white-quality-20261030'
sys.path.insert(0, str(OLD / '.deps'))
import manifold3d as mf

M = mf.Manifold
A = ROOT / 'analysis'
OUT = ROOT / 'STL'
A.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

def box(lo, hi):
    return M.cube(tuple(np.asarray(hi) - lo)).translate(tuple(lo))

def cyl(r, h, x=0, y=0, z=0, n=96):
    return M.cylinder(h, r, circular_segments=n).translate((x, y, z))

def mesh(body):
    q = body.to_mesh64()
    return trimesh.Trimesh(np.asarray(q.vert_properties)[:, :3], np.asarray(q.tri_verts), process=False)

def load_part(name):
    p = QUALITY / 'analysis/assembly_meshes' / (name + '.npz')
    d = np.load(p)
    body = M(mf.Mesh64(d['vertices'], d['faces'].astype('uint64')))
    assert body.status() == mf.Error.NoError, (name, body.status())
    return body

holes = []
for radius in (180, 134):
    for i in range(8):
        for offset in (-10, 10):
            angle = i * 45 + 22.5 + offset
            x, y = radius * np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))])
            holes.append({'radius': radius, 'module': i + 1, 'angle': angle, 'x': float(x), 'y': float(y)})
cuts = [cyl(1.7, 2.4, h['x'], h['y'], 2.8) for h in holes]
key_slots = []
for p in (60, 130, -60, -130):
    for lo, hi in (((-6.2, p - 3.2, 2.9), (6.2, p + 3.2, 5.2)), ((p - 3.2, -6.2, 2.9), (p + 3.2, 6.2, 5.2))):
        cuts.append(box(lo, hi))
        key_slots.append((lo, hi))
full = cyl(200, 5, n=2048) - M.batch_boolean(cuts, mf.OpType.Add)
quadrant = full.trim_by_plane((1, 0, 0), .1).trim_by_plane((0, 1, 0), .1)
assert quadrant.status() == mf.Error.NoError
quarters = [quadrant.rotate((0, 0, i * 90)) for i in range(4)]
assembled = M.batch_boolean(quarters, mf.OpType.Add)

checks = []
for i, body in enumerate(quarters, 1):
    t = mesh(body)
    assert t.is_watertight and t.is_winding_consistent and t.volume > 0
    assert len(t.split()) == 1
    np.savez_compressed(A / f'base{i}.npz', vertices=t.vertices, faces=t.faces)
    checks.append({'quadrant': i, 'watertight': True, 'components': 1, 'bounds_mm': t.bounds.tolist(), 'volume_mm3': float(t.volume)})

# All four quarters are geometrically identical; one STL is printed four times.
print_mesh = mesh(quadrant)
print_mesh.apply_translation(-print_mesh.bounds[0])
path = OUT / '底座.stl'
print_mesh.export(path, file_type='stl_ascii')
reloaded = trimesh.load(path, force='mesh')
assert reloaded.is_watertight and reloaded.is_winding_consistent
assert len(reloaded.split()) == 1
assert np.allclose(reloaded.extents, print_mesh.extents, atol=1e-6)
assert reloaded.extents[0] < 201 and reloaded.extents[1] < 201 and reloaded.extents[2] == 5
placed = print_mesh.copy()
placed.apply_translation([128 - placed.extents[0] / 2, 128 - placed.extents[1] / 2, 0])
np.savez_compressed(A / 'print_plate.npz', vertices=placed.vertices, faces=placed.faces)

manifest = json.loads((QUALITY / '交付文件/零件清单.json').read_text(encoding='utf8'))
parts = {}
fit_checks = []
for row in manifest['parts']:
    name = row['id']
    if name[0] not in 'WSD':
        continue
    body = load_part(name)
    parts[name] = body
    overlap = max(0.0, (body ^ assembled).volume())
    fit_checks.append({'part': name, 'base_interference_mm3': overlap})
    assert overlap < .01, (name, 'base collision', overlap)
    print('FIT', name, round(overlap, 6), flush=True)

for h in holes:
    name = f"{'W' if h['radius'] == 180 else 'S'}{h['module']:02d}_{'环形建筑' if h['radius'] == 180 else '钢架'}"
    # 3.8 mm pin bridges both mating sockets without bottoming out.
    pin = cyl(1.5, 3.8, h['x'], h['y'], 3.1, n=32)
    intrusion = max(0.0, (pin ^ (assembled + parts[name])).volume())
    assert intrusion < .001, (name, 'pin collision', intrusion)
    fit_checks.append({'socket': name, 'angle': h['angle'], 'pin_interference_mm3': intrusion})

for i, (lo, hi) in enumerate(key_slots):
    center = (np.array(lo) + hi) / 2
    size = (12, 6, 2) if abs(lo[0] + 6.2) < 1e-5 else (6, 12, 2)
    pos = (center[0] - size[0]/2, center[1] - size[1]/2, 2.9)
    key = M.cube(size).translate(pos)
    overlap = max(0.0, (key ^ assembled).volume())
    assert overlap < .001, ('key collision', i, overlap)
    fit_checks.append({'key': i + 1, 'interference_mm3': overlap})

report = {
    'design_date': '2026-11-13', 'diameter_mm': 400, 'thickness_mm': 5,
    'stl_file': str(path), 'stl_print_quantity': 4, 'identical_quadrants': True,
    'print_size_mm': reloaded.extents.tolist(), 'seam_gap_mm': .2,
    'mounting_holes': holes, 'socket_diameter_mm': 3.4, 'socket_depth_mm': 2.2,
    'socket_bottom_thickness_mm': 2.8, 'key_slot_bottom_thickness_mm': 2.9,
    'existing_keys_required': 8, 'existing_pins_required': 32,
    'keys_already_in': '第一组 第4盘', 'door_mount': '中心台阶底面薄涂胶固定，门扇铰链保持活动',
    'geometry_checks': checks, 'assembly_checks': fit_checks,
    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'source_manifest_sha256': hashlib.sha256((QUALITY / '交付文件/零件清单.json').read_bytes()).hexdigest(),
    'actual_print_test': False, 'water_tight_container': False,
    'notes': ['STL 是封闭实体，内部填充由切片设置决定。', '拼缝与可取出的拼接键不构成承重锁扣；拼合后粘接并从底部托住搬运。', '四块平底朝下打印，无悬空结构；旧版水底碎石细节未纳入本版。', '不装真实水，不预留未确认的电子元件。']
}
(A / 'geometry_and_fit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
archive = Path('D:/虚拟C盘/底座.zip')
if archive.exists():
    archive = ROOT / '底座.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(path, path.name)
with zipfile.ZipFile(archive) as z:
    assert z.namelist() == ['底座.stl'] and z.testzip() is None
    assert hashlib.sha256(z.read('底座.stl')).hexdigest() == report['sha256']
print('GEOMETRY_AND_FIT_PASS', len(fit_checks), 'checks', str(archive), flush=True)
