import sys, numpy as np, cv2, torch
from train import Doors
from common import *
ds = Doors([sys.argv[1]], 'train', True)
np.random.seed(1)
tiles=[]
for i in range(0, 24):
    img, heat, off, mask, pts = ds[i*7]
    im = cv2.cvtColor((img[0].numpy()*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    im = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    # decode from the target tensors: must land on the labelled corner
    tgt = np.concatenate([heat.numpy(), off.numpy()])
    p, c = decode(tgt)
    for j in range(4):
        if c[j] == 1:
            assert np.linalg.norm(p[j]-pts[j].numpy()) < 1e-3, (p[j], pts[j])
            q = (int(pts[j][0]*2*16), int(pts[j][1]*2*16))
            cv2.circle(im, q, 6*16, [(0,255,255),(255,255,0),(0,255,0),(180,105,255)][j], 1, cv2.LINE_AA, 4)
    tiles.append(im)
rows=[np.hstack(tiles[r*4:r*4+4]) for r in range(6)]
cv2.imencode('.jpg', np.vstack(rows))[1].tofile(sys.argv[2])
print('OK')
