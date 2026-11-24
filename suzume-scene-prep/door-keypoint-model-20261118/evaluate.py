"""Two-pass evaluation, the same procedure the headset runs.

python evaluate.py MODEL(.pt|.onnx) DATASET_DIR [--split val|all] [--scale S] [--dump FILE]
--scale S enlarges the image first (stands in for the headset's higher-resolution camera).
--dump writes per-image detections (pixels in the original image) for the Unity comparison.
"""
import sys, json, math
from pathlib import Path
import numpy as np, cv2, torch
from common import *

model, root = sys.argv[1], Path(sys.argv[2])
arg = lambda n, d: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
split, scale, dump = arg('--split', 'val'), float(arg('--scale', 1)), arg('--dump', None)
if model.endswith('.onnx'):
    import onnxruntime as ort
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
    run = lambda x: sess.run(None, {'image': x})[0][0]
else:
    net = DoorNet(); net.load_state_dict(torch.load(model, map_location='cpu')); net.eval().cuda()
    run = lambda x: net(torch.from_numpy(x).cuda()).detach().float().cpu().numpy()[0]

px, px1, t_err, r_err, rel = [], [], [], [], []
missed = false_pos = present = empty = 0
records = {}
with torch.no_grad():
    for p in sorted((root / 'labels').glob('*.json')):
        L = json.loads(p.read_text(encoding='utf8'))
        if split != 'all' and L['split'] != split:
            continue
        gray = imread_gray(root / L['image'])
        if scale != 1:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        kp = np.array(L['keypoints'])
        has = L.get('door_present', True)
        res = detect(run, gray)
        records[Path(L['image']).stem] = (res, kp)
        if not has:
            empty += 1; false_pos += res is not None
            continue
        if (kp[:, 2] == 0).any():
            continue            # partly outside the frame: the app does not use such frames
        present += 1
        if res is None:
            missed += 1; continue
        pts = res[0] / scale
        e = np.linalg.norm(pts - kp[:, :2], axis=1)
        px.append(e.max()); rel.append(e.max() / np.linalg.norm(kp[2, :2] - kp[0, :2]))
        one = detect(run, gray, passes=0)
        if one is not None:
            px1.append(np.linalg.norm(one[0] / scale - kp[:, :2], axis=1).max())
        w, h = L['opening_width_m'], L['opening_height_m']
        obj = np.array([[-w / 2, 0, 0], [w / 2, 0, 0], [-w / 2, h, 0], [w / 2, h, 0]], np.float64)
        ok, rvec, tvec = cv2.solvePnP(obj, pts, np.array(L['K']), None, flags=cv2.SOLVEPNP_IPPE)
        R = cv2.Rodrigues(rvec)[0]
        r_err.append(math.degrees(math.acos(max(-1, min(1, (np.trace(R.T @ np.array(L['R'])) - 1) / 2)))))
        t_err.append(float(np.linalg.norm(tvec.ravel() - L['t'])) * 1000)

q = lambda a: [round(float(np.percentile(a, v)), 3) for v in (50, 90, 99, 100)]
px = np.array(px)
print(json.dumps(dict(
    model=Path(model).name, dataset=root.name, split=split, scale=scale,
    doors=present, missed=missed, empty_images=empty, false_detections=int(false_pos),
    worst_corner_px_p50_p90_p99_max=q(px), first_pass_only_px=q(px1),
    worst_corner_over_door_height=q(rel), gross_errors_over_5px=int((px > 5).sum()),
    single_frame_position_mm=q(t_err), single_frame_rotation_deg=q(r_err)), ensure_ascii=False, indent=1))
if dump:
    # name python_found fully_labelled, 8 detected pixel values, 8 labelled pixel values
    lines = [str(root.resolve())]
    for name, (res, kp) in records.items():
        found = res is not None
        vals = (res[0] / scale).ravel() if found else np.zeros(8)
        lines.append(' '.join([name, str(int(found)), str(int((kp[:, 2] > 0).all()))]
                              + [f'{v:.3f}' for v in vals] + [f'{v:.3f}' for v in kp[:, :2].ravel()]))
    Path(dump).write_text('\n'.join(lines), encoding='utf8')
