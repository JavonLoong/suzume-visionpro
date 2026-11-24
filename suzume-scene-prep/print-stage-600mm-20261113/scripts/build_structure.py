"""600 mm stage prototype, source-derived sockets and replaceable servo-door modules.

All dimensions are mm. Deck datum z=0..8; original WM2 feet remain at z=5.
Servo dimensions are deliberately not asserted: the hanging carrier has adjustment slots.
"""
import hashlib, json, math, sys, time, zipfile
from pathlib import Path
import numpy as np
import trimesh

R = Path(__file__).resolve().parents[1]
P = R.parent
Q = P / 'print-white-quality-20261030'
sys.path.insert(0, str(P / 'print-400mm-20261030/.deps'))
import manifold3d as mf
M, C, OP = mf.Manifold, mf.CrossSection, mf.OpType
A, OUT = R / 'analysis', R / 'STL'
for p in (A, OUT, A / 'assembly'):
    p.mkdir(parents=True, exist_ok=True)
records, checks = [], []

def cube(lo, hi):
    return M.cube(tuple(np.asarray(hi) - lo)).translate(tuple(lo))

def cyl(r, h, x=0, y=0, z=0, n=64):
    return M.cylinder(h, r, circular_segments=n).translate((x, y, z))

def union(parts):
    return M.batch_boolean(parts, OP.Add)

def hexagon(af, h, x=0, y=0, z=0):
    return cyl(af / math.sqrt(3), h, x, y, z, n=6)

def capsule(a, b, radius, z, h):
    cs = C.batch_hull([C.circle(radius, 32).translate(a), C.circle(radius, 32).translate(b)])
    return cs.extrude(h).translate((0, 0, z))

def screw_cut(x, y, bottom=-10, top=8, head=True, head_seat=None):
    body = cyl(1.7, top - bottom + .2, x, y, bottom)
    seat = top-2 if head_seat is None else head_seat
    return body + cyl(3.2, top-seat+.2, x, y, seat) if head else body

def nut_cut(x, y, z, depth=2.7):
    return hexagon(5.9, depth, x, y, z)

def to_mesh(m):
    data = m.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:, :3], np.asarray(data.tri_verts), process=False)

def load(name):
    d = np.load(Q / 'analysis/assembly_meshes' / (name + '.npz'))
    m = M(mf.Mesh64(d['vertices'], d['faces'].astype('uint64')))
    assert m.status() == mf.Error.NoError, name
    return m

def check_zero(label, body, tolerance=.005):
    volume = max(0., body.volume())
    checks.append({'check': label, 'interference_mm3': volume, 'allowed_mm3': tolerance})
    assert volume < tolerance, (label, volume)

def check_against(label, body, obstacles, tolerance=.005):
    lo=np.array(body.bounding_box()[:3]);hi=np.array(body.bounding_box()[3:]);volume=0.
    for other in obstacles:
        b=np.array(other.bounding_box())
        if np.all(hi>b[:3]) and np.all(b[3:]>lo):volume+=max(0.,(body^other).volume())
    checks.append({'check':label,'interference_mm3':volume,'allowed_mm3':tolerance})
    assert volume<tolerance,(label,volume)

def emit(name, body, group, quantity=1, rotate=(0,0,0), components=1, note=''):
    body = body.simplify(.002)
    assert body.status() == mf.Error.NoError and not body.is_empty(), (name, body.status())
    m = to_mesh(body)
    assert m.is_watertight and m.is_winding_consistent and m.volume > 0, name
    assert len(body.decompose()) == components, (name, len(body.decompose()))
    np.savez_compressed(A / 'assembly' / (name+'.npz'), vertices=m.vertices, faces=m.faces)
    posed = to_mesh(body.rotate(rotate))
    shift = -posed.bounds[0]
    posed.apply_translation(shift)
    assert max(posed.extents[:2]) < 239 and posed.extents[2] < 245, (name, posed.extents)
    folder = OUT / group
    folder.mkdir(exist_ok=True)
    path = folder / (name+'.stl')
    posed.export(path, file_type='stl_ascii')
    loaded = trimesh.load(path, force='mesh')
    if not loaded.is_watertight:
        original_volume = loaded.volume
        loaded.update_faces(loaded.nondegenerate_faces(height=1e-12))
        loaded.update_faces(loaded.unique_faces())
        loaded.remove_unreferenced_vertices()
        assert abs(loaded.volume-original_volume) < .001, name
        assert loaded.is_watertight and loaded.is_winding_consistent, name
        loaded.export(path, file_type='stl_ascii')
        loaded = trimesh.load(path, force='mesh')
    assert loaded.is_watertight and loaded.is_winding_consistent, name
    assert len(loaded.split()) == components, name
    row = {'id': name, 'group': group, 'quantity': quantity, 'print_size_mm': posed.extents.tolist(),
           'volume_mm3': float(m.volume), 'faces': len(m.faces), 'components': components,
           'rotation_degrees': list(rotate), 'print_translation': shift.tolist(), 'note': note,
           'stl_path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    records.append(row)
    np.savez_compressed(A / (name+'_print.npz'), vertices=posed.vertices, faces=posed.faces)
    print('PART', name, np.round(posed.extents, 2).tolist(), 'x', quantity, flush=True)
    return row

source_manifest = json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))
parts = {r['id']: load(r['id']) for r in source_manifest['parts'] if r['id'][0] in 'WS'}
print('SOURCE_PARTS_LOADED', len(parts), flush=True)
socket_profiles, cuts, socket_data = {}, [], []
foot_slab = cube((-210,-210,5), (210,210,8.001))
for name, body in parts.items():
    if '_附件' in name:
        continue
    projection = C((body ^ foot_slab).project().to_polygons(), mf.FillRule.Positive)
    socket_profiles[name] = projection
    snug = projection.offset(.25)
    cuts += [snug.extrude(3.2).translate((0,0,5)), projection.offset(.55).extrude(.65).translate((0,0,7.4))]
    socket_data.append({'part': name, 'depth_mm': 3, 'clearance_per_side_mm': .25, 'entry_relief_per_side_mm': .55, 'profile_area_mm2': snug.area()})
    print('SOCKET', name, round(snug.area(),1), flush=True)

# Keep all 32 existing module locating pins as an optional secondary locator.
pin_points = []
for radius in (180,134):
    for i in range(8):
        for off in (-10,10):
            angle = math.radians(i*45+22.5+off)
            x,y = radius*np.array([math.cos(angle),math.sin(angle)])
            cuts.append(cyl(1.7,2.4,x,y,2.8))
            pin_points.append((float(x),float(y)))

CY, FY, CLEAR = 20., 35., .25
outer_points = [(-88,-53),(88,-53),(88,45),(80,53),(-88,53)]
inner_points = [(-73,-38),(73,-38),(73,30),(65,38),(-73,38)]
outer = C([outer_points], mf.FillRule.Positive)
inner = C([inner_points], mf.FillRule.Positive)
outer_at = outer.translate((0,CY))
inner_at = inner.translate((0,CY))
cuts += [outer_at.offset(CLEAR).extrude(4.3).translate((0,0,4)),
         inner_at.offset(CLEAR).extrude(8.4).translate((0,0,-.2)),
         outer_at.offset(.55).extrude(.6).translate((0,0,7.5))]
cassette_bolts = [(x,y+CY) for x in (-80,80) for y in (-45,45)]
cuts += [screw_cut(x,y,head=False) for x,y in cassette_bolts]

# Nine deck panels: a 3 x 3 grid, 0.30 mm assembly gaps.
bridge_points = []
for x in (-100,100):
    for y in (-210,0,210):
        bridge_points.append((x,y,0))
for y in (-100,100):
    for x in (-210,0,210):
        bridge_points.append((x,y,90))
bridge_holes = []
for x,y,angle in bridge_points:
    for d in (-17,17):
        dx,dy = (d,0) if angle==0 else (0,d)
        bridge_holes.append((x+dx,y+dy))
cuts += [screw_cut(x,y,head_seat=3 if math.hypot(x,y)<205 else 6) for x,y in bridge_holes]
post_centers = [(x,y) for x in (-100,100) for y in (-100,100)]
post_holes = [(x+dx,y+dy) for x,y in post_centers for dx in (-10,10) for dy in (-10,10)]
cuts += [screw_cut(x,y,head_seat=3) for x,y in post_holes]
skirt_holes = []
for i in range(8):
    for angle in (i*45+10,i*45+35):
        a=math.radians(angle)
        skirt_holes.append((294*math.cos(a),294*math.sin(a)))
cuts += [screw_cut(x,y) for x,y in skirt_holes]
deck = cyl(300,8,n=1536) - union(cuts)
tiles = []
for row in range(3):
    for col in range(3):
        x0,x1=-300+200*col,-100+200*col
        y0,y1=-300+200*row,-100+200*row
        lo=(x0+(.15 if col else 0),y0+(.15 if row else 0),-.1)
        hi=(x1-(.15 if col<2 else 0),y1-(.15 if row<2 else 0),8.1)
        tile=deck ^ cube(lo,hi)
        tiles.append(tile)
        emit(f'底板{row+1}{col+1}',tile,'底座结构')
deck_assembled=union(tiles)
for name,body in parts.items():
    check_zero(name+'落座',body ^ deck_assembled)
    if name in socket_profiles:
        for lift in (1,2,4):
            check_zero(name+f'插入过程_{lift}',body.translate((0,0,lift)) ^ deck_assembled)
for i,(x,y) in enumerate(bridge_holes+post_holes+skirt_holes):
    seat=3 if math.hypot(x,y)<205 else 6
    head=cyl(2.85,1.65,x,y,seat)
    check_against(f'M3低圆头{i+1}与底板和旧部件',head,[deck_assembled]+list(parts.values()))

# Removable skirts carry the outer perimeter; their inner top slope is 45 degrees.
skirt = cyl(299,80,z=-80,n=1536) - (
    cyl(296,68,z=-80,n=1536) + M.cylinder(12,296,284,circular_segments=1536).translate((0,0,-12)))
skirt = skirt.trim_by_plane((0,1,0),.15).trim_by_plane((math.sin(math.pi/4),-math.cos(math.pi/4),0),.15)
for angle in (10,35):
    a=math.radians(angle); x,y=294*math.cos(a),294*math.sin(a)
    skirt = skirt - screw_cut(x,y,-7,0,False) - nut_cut(x,y,-5.2,2.8)
emit('围边_打印7件',skirt,'底座结构',quantity=7,rotate=(0,0,67.5))
wire_skirt=skirt - cube((275,99,-80.2),(305,115,-64))
emit('出线围边_打印1件',wire_skirt,'底座结构',rotate=(0,0,67.5),note='16 mm 宽底部出线缺口；底部保持可检修')

# The four central posts also join the four adjacent deck corners.
post=cube((-22,-22,-5),(22,22,0)) + (cyl(12,75,z=-80)-cyl(9,75.1,z=-80.1))
for x in (-10,10):
    for y in (-10,10):
        post=post-screw_cut(x,y,-9,0,False)-nut_cut(x,y,-5,2.8)
emit('中央支脚_打印4件',post,'底座结构',4,rotate=(180,0,0))
bridge=cube((-26,-10,-5),(26,10,0))
for x in (-17,17):
    bridge=bridge-screw_cut(x,0,-5.2,.1,False)-nut_cut(x,0,-5.1,2.8)
emit('接缝压条_打印12件',bridge,'底座结构',12,rotate=(180,0,0))

# The door sits on a separate thrust washer, independently of the drive shaft.
# Splitting the washer avoids an unsupported flange when printing the shaft.
shaft=hexagon(8,16,z=-24)+cyl(4.5,16,z=-8)+hexagon(8,20,z=8)
emit('门轴_打印1件',shaft,'门通用件',note='试制轴；9 mm 圆轴段、8 mm 对边六角端。先试转再接舵机。')
thrust_washer=cyl(7,2,z=8)-cyl(4.8,2.2,z=7.9)
emit('门轴承托垫圈',thrust_washer,'门通用件',note='垫在门扇下轴套与固定门框之间，门重传到门框，不压舵机。')
coupler=cube((-27,-16,-29.5),(27,16,-25.5))+cyl(9,16,z=-25.5)
coupler=coupler-hexagon(8.4,16.2,z=-25.6)-cyl(3.2,4.2,z=-29.6)
for sign in (-1,1):
    coupler=coupler-capsule((sign*9,0),(sign*22,0),1.7,-29.6,4.3)
emit('舵盘接头',coupler,'门通用件',note='夹持原配舵盘；不打印舵机花键。舵盘孔距与厚度需实物确认。')
clamp=cube((-27,-16,-35.5),(27,16,-32.5))-cyl(7,3.3,z=-35.6)
for sign in (-1,1):
    clamp=clamp-capsule((sign*9,0),(sign*22,0),1.7,-35.6,3.4)
emit('舵盘夹片',clamp,'门通用件',note='夹片间距由螺丝和垫片适配原配舵盘；图中 3 mm 仅为占位。')

# Adjustable suspended carrier: two crossbars slide along Y, servo mounting
# screws slide along X. Four separate hangers adjust carrier height.
carrier=cube((-72,-50,0),(72,50,4))-cube((-62,-40,-.1),(62,40,4.1))
for x in (-67,67):
    carrier=carrier-capsule((x,-42),(x,42),1.7,-.1,4.2)
    for y in (-44,44):
        tab=cube((x-4,y-6,4),(x+4,y+6,16))
        bore=cyl(1.7,12,z=-6).rotate((0,90,0)).translate((x,y,10))
        carrier=carrier+(tab-bore)
emit('舵机升降托架',carrier,'门通用件',note='安装高度与输出轴位置待现有舵机试装；不是某个型号的专用底座。')
bar=cube((-72,-6,0),(72,6,4))-capsule((-57,0),(57,0),1.7,-.1,4.3)
for x in (-67,67):
    bar=bar-cyl(1.7,4.4,x,0,-.2)
emit('舵机滑动横梁_打印2件',bar,'门通用件',2)
hanger=cube((0,-7,-66),(4,7,0))+cube((-10,-7,0),(4,7,4))
# Slot axis is horizontal through the vertical wall; use a transformed capsule.
slot=capsule((0,-56),(0,-12),1.7,-1,6).rotate((90,0,90))
# Explicit hull of two X-oriented cylinders avoids transform convention ambiguity.
slot=M.batch_hull([cyl(1.7,6,z=-1).rotate((0,90,0)).translate((0,0,z)) for z in (-56,-12)])
hanger=hanger-slot-cyl(1.7,4.4,-5,0,-.1)
emit('升降吊耳_打印4件',hanger,'门通用件',4,rotate=(0,90,0))

door_variants=[]
for label,W,H in [('主门',50,82),('小门',40,62),('大门',60,102)]:
    ax=W/2-5
    plate=outer.extrude(4).translate((0,CY,4))+inner.extrude(4).translate((0,CY,0))
    # Shaft opening; mounting feet and hanger attachments.
    plate=plate-cyl(4.8,8.3,ax,FY,-.1)
    for x in (-(W/2+5),W/2+5):
        plate=plate-cube((x-5.25,FY-6.25,3),(x+5.25,FY+6.25,8.2))
        plate=plate-cyl(1.7,3.3,x,FY,-.1)-cyl(3.2,2,x,FY,-.1)
    for x,y in cassette_bolts:
        plate=plate-screw_cut(x,y,0,8,True)
    for x in (-70,70):
        for y in (-44,44):
            plate=plate-screw_cut(x,y+CY,3.8,8,True)
    emit(label+'插座板',plate,label,note='外轮廓统一 176×106 mm，缺角防反插；嵌入后用四颗 M3 螺丝锁紧。')
    check_zero(label+'插座与台面',plate ^ deck_assembled)

    frame=cube((-W/2-10,-6,0),(W/2+10,6,H+18))-cube((-W/2,-6.1,8),(W/2,6.1,H+8))
    frame=frame-cyl(8,H,ax,0,8)-cyl(4.8,8.3,ax,0,-.1)-cyl(2.2,10.3,ax,0,H+7.9)
    # Capture an M4 nut in the lintel: a 20 mm screw is a fixed upper pivot,
    # while the door rotates around its 4.4 mm clearance bore.
    frame=frame-hexagon(7.4,3.5,ax,0,H+12.3)-cube((ax-4.2,-6.1,H+12.3),(ax+4.2,0,H+15.8))
    for x in (-(W/2+5),W/2+5):
        frame=frame+cube((x-5,-6,-5),(x+5,6,0))
        frame=frame-cyl(1.7,13.3,x,0,-5.1)-nut_cut(x,0,3.1,2.7)
        frame=frame-cube((x-3,-6.1,3.1),(x+3,0,5.8))
    frame=frame.translate((0,FY,8))
    emit(label+'门框',frame,label,rotate=(-90,0,0),note='门洞宽高为 '+str(W)+'×'+str(H)+' mm；门框横梁装 M4 螺母，M4×20 螺钉作固定上轴，门扇绕螺钉转动。')
    check_zero(label+'门框与插座',frame ^ plate)
    check_against(label+'门框与庭院',frame,list(parts.values()))

    leaf=cube((-W/2+1.2,-1.6,11),(W/2-1,5.6,H+5))
    # Six recessed front panels; keep the rear printing face flat.
    span=H-14
    for xa,xb in [(-W/2+5,-2),(2,W/2-5)]:
        for za,zb in [(15,15+.23*span),(18+.23*span,15+.75*span),(18+.75*span,H+1)]:
            if xb>xa and zb>za:
                leaf=leaf-cube((xa,-1.7,za),(xb,-.9,zb))
    bottom_hub=(cyl(7,18,ax,0,10)-hexagon(8.4,18.2,ax,0,9.9)) ^ cube((-300,-20,-100),(300,5.6,300))
    top_hub=cyl(5,12,ax,0,H-6)-cyl(2.2,12.3,ax,0,H-6.1)
    leaf=(leaf+bottom_hub+top_hub)-hexagon(8.4,18.2,ax,0,9.9)-cyl(2.2,12.3,ax,0,H-6.1)
    leaf=leaf.translate((0,FY,8))
    emit(label+'门扇',leaf,label,rotate=(-90,0,0))
    world_shaft=shaft.translate((ax,FY,8))
    upper_pin=cyl(2,20,ax,FY,H+6)
    check_zero(label+'M4上轴与门框门扇',upper_pin ^ (frame+leaf))
    check_zero(label+'门轴与门扇',world_shaft ^ leaf)
    check_zero(label+'门轴与固定座',world_shaft ^ (frame+plate))
    washer_world=thrust_washer.translate((ax,FY,8))
    check_zero(label+'承托垫圈与门轴门框',washer_world ^ (world_shaft+frame))
    bearing_area=(washer_world.slice(16.001) ^ frame.slice(15.999)).area()
    checks.append({'check':label+'承托垫圈接触面积','area_mm2':bearing_area})
    assert bearing_area>40,(label,bearing_area)
    world_coupler=coupler.translate((ax,FY,8))
    check_zero(label+'接头与插座',world_coupler ^ plate)
    check_zero(label+'接头与门轴',world_coupler ^ world_shaft)
    obstacles=list(parts.values())+[frame,plate,deck_assembled]
    for angle in range(0,106,3):
        rotated=leaf.translate((-ax,-FY,-8)).rotate((0,0,angle)).translate((ax,FY,8))
        check_against(label+f'开门{angle}度',rotated,obstacles)
    # A padded swept envelope checks between the sampled angles, against scenery.
    profile=leaf.project()
    sweeps=[profile.translate((-ax,-FY)).rotate(a).translate((ax,FY)) for a in np.arange(0,105.01,1)]
    sweep=C.batch_boolean(sweeps,OP.Add).offset(1).extrude(H+12).translate((0,0,17))
    check_against(label+'连续扫掠余量与庭院',sweep,list(parts.values()))
    np.savez_compressed(A/(label+'_sweep.npz'),vertices=to_mesh(sweep).vertices,faces=to_mesh(sweep).faces)
    door_variants.append({'label':label,'opening_width_mm':W,'opening_height_mm':H,'pivot_xy':[ax,FY],
                          'shaft_frame_datum_z':8,'tested_opening_degrees':[0,105],'cassette_outer_mm':[176,106],
                          'view_angle_degrees_at_500mm':[math.degrees(2*math.atan(W/1000)),math.degrees(2*math.atan(H/1000))]})
    print('DOOR_SWEEP_PASSED',label,flush=True)

manifest={'date':'2026-11-13','stage_diameter_mm':600,'courtyard_diameter_mm':400,'radial_border_mm':100,
          'deck_thickness_mm':8,'underclearance_mm':80,'total_height_mm':88,
          'slot_depth_mm':3,'nominal_slot_clearance_per_side_mm':.25,
          'source_sha256':hashlib.sha256((Q/'交付文件/零件清单.json').read_bytes()).hexdigest(),
          'stage_choice':'60厘米圆形；结构样机，未做实体试配，不承诺零间隙或通用舵机即插即用。',
          'servo_model':None,'servo_horn_verified':False,'actual_print_test':False,'electronics_implemented':False,
          'parts':records,'sockets':socket_data,'door_variants':door_variants,'geometry_checks':checks,
          'positions':{'bridge_points':bridge_points,'post_centers':post_centers,'skirt_holes':skirt_holes,'cassette_bolts':cassette_bolts},
          'pending':['用小试块确认槽口余量','核实现有舵机尺寸、原配舵盘孔距和厚度','打印单扇门并手动转动后再接舵机','控制角度、供电及远距离线材由后续电子联调确定']}
(A/'structure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('STRUCTURE_GEOMETRY_PASS',len(records),'unique files',len(checks),'checks',flush=True)
