"""Trains the door-corner network.  python train.py TRAIN_DIR [EXTRA_DIR ...] --out OUT [--epochs N]"""
import json, math, sys, time, argparse
from pathlib import Path
import numpy as np, cv2, torch, torch.nn.functional as F
from torch.utils.data import Dataset
from concurrent.futures import ThreadPoolExecutor
from common import *

cv2.setNumThreads(0)


class Doors(Dataset):
    def __init__(self, roots, split, augment):
        self.items = []
        for root in roots:
            root = Path(root)
            for p in sorted((root / 'labels').glob('*.json')):
                L = json.loads(p.read_text(encoding='utf8'))
                if L['split'] == split:
                    self.items.append((str(root / L['image']), np.array(L['keypoints'], np.float64),
                                       bool(L.get('door_present', True))))
        self.augment = augment

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, kp, present = self.items[i]
        rng = np.random if self.augment else np.random.RandomState(i)
        gray = imread_gray(path)
        H, W = gray.shape
        base = W / IN_W
        xy = kp[:, :2]
        if present and rng.rand() < 0.55:
            lo, hi = xy.min(0), xy.max(0)
            size = max(hi[0] - lo[0], hi[1] - lo[1], 4.0)
            k = max(size / (rng.uniform(0.18, 0.8) * IN_H), 0.3)
            center = (lo + hi) / 2 + rng.uniform(-0.35, 0.35, 2) * size
            theta = math.radians(rng.uniform(-14, 14))
        else:
            k = base * (rng.uniform(0.55, 1.7) if present else math.exp(rng.uniform(math.log(0.2), math.log(1.5))))
            theta = math.radians(float(np.clip(rng.randn() * 5, -15, 15)))
            if present and rng.rand() < 0.85:
                # put the door centre at a random place inside the network input
                where = np.array([rng.uniform(0.1, 0.9) * IN_W, rng.uniform(0.1, 0.9) * IN_H])
                A0 = make_affine((0, 0), k, theta)
                center = xy.mean(0) - A0[:, :2] @ (where - np.array([IN_W / 2, IN_H / 2]))
            else:
                center = np.array([rng.uniform(0.2, 0.8) * W, rng.uniform(0.2, 0.8) * H])
        A = make_affine(center, k, theta)
        img = sample(pyramid(gray), A, level_bias=int(rng.rand() < 0.15)).astype(np.float32) / 255.0
        pts = to_input(A, xy)
        if self.augment:
            img = photometric(img, rng, pts if present else np.zeros((0, 2)))

        heat = np.zeros((4, OUT_H, OUT_W), np.float32)
        off = np.zeros((8, OUT_H, OUT_W), np.float32)
        mask = np.zeros((4, OUT_H, OUT_W), np.float32)
        if present:
            ys, xs = np.mgrid[0:OUT_H, 0:OUT_W]
            for j in range(4):
                gx, gy = pts[j] / STRIDE
                cx, cy = math.floor(gx), math.floor(gy)
                if not (0 <= cx < OUT_W and 0 <= cy < OUT_H):
                    continue
                y0, y1, x0, x1 = max(cy - 6, 0), min(cy + 7, OUT_H), max(cx - 6, 0), min(cx + 7, OUT_W)
                heat[j, y0:y1, x0:x1] = np.exp(-((xs[y0:y1, x0:x1] - cx) ** 2 + (ys[y0:y1, x0:x1] - cy) ** 2) / (2 * 1.2 ** 2))
                y0, y1, x0, x1 = max(cy - 1, 0), min(cy + 2, OUT_H), max(cx - 1, 0), min(cx + 2, OUT_W)
                off[2 * j, y0:y1, x0:x1] = gx - (xs[y0:y1, x0:x1] + 0.5)
                off[2 * j + 1, y0:y1, x0:x1] = gy - (ys[y0:y1, x0:x1] + 0.5)
                mask[j, y0:y1, x0:x1] = 0.5
                mask[j, cy, cx] = 1.0
        return torch.from_numpy(img[None]), torch.from_numpy(heat), torch.from_numpy(off), torch.from_numpy(mask), \
            torch.from_numpy(pts.astype(np.float32))


def photometric(img, rng, pts):
    h, w = img.shape
    probes = np.vstack([pts, pts.mean(0, keepdims=True)]).round().astype(int) if len(pts) else np.zeros((0, 2), int)
    probes = probes[(probes[:, 0] >= 0) & (probes[:, 0] < w) & (probes[:, 1] >= 0) & (probes[:, 1] < h)]

    def hides(draw):
        # a pasted shape may cover one corner (a finger does that) but not the door itself
        m = np.zeros((h, w), np.uint8); draw(m)
        return m[probes[:, 1], probes[:, 0]].sum() > 1
    if rng.rand() < 0.35:   # look-alike clutter: bright frames and bars
        for _ in range(rng.randint(1, 4)):
            c = (rng.uniform(0, w), rng.uniform(0, h)); s = (rng.uniform(6, 90), rng.uniform(6, 120))
            box = cv2.boxPoints((c, s, rng.uniform(-30, 30))).astype(np.int32)
            v = float(rng.uniform(0, 1))
            if rng.rand() < 0.5:
                cv2.polylines(img, [box], True, v, int(rng.randint(1, 6)), cv2.LINE_AA)
            elif not hides(lambda m: cv2.fillPoly(m, [box], 1)):
                layer = img.copy(); cv2.fillPoly(layer, [box], v, cv2.LINE_AA)
                a = rng.uniform(0.3, 1.0); img = img * (1 - a) + layer * a
    if rng.rand() < 0.25:   # blobs in front (fingers, controller)
        for _ in range(rng.randint(1, 3)):
            c = (int(rng.uniform(0, w)), int(rng.uniform(0, h)))
            axes, ang = (int(rng.uniform(5, 45)), int(rng.uniform(5, 45))), rng.uniform(0, 180)
            if not hides(lambda m: cv2.ellipse(m, c, axes, ang, 0, 360, 1, -1)):
                cv2.ellipse(img, c, axes, ang, 0, 360, float(rng.uniform(0, 1)), -1, cv2.LINE_AA)
    img = np.clip(img, 0, 1) ** rng.uniform(0.5, 2.0)
    c = np.array([[-0.5, 0.5], [-0.5, 0.5]], np.float32) * rng.uniform(-0.4, 0.4) \
        + np.array([[-0.5, -0.5], [0.5, 0.5]], np.float32) * rng.uniform(-0.4, 0.4) + 1
    img = img * cv2.resize(c, (w, h), interpolation=cv2.INTER_LINEAR)
    img = (img - 0.5) * rng.uniform(0.55, 1.5) + 0.5 + rng.uniform(-0.2, 0.2)
    if rng.rand() < 0.5:
        img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.3, 1.6))
    if rng.rand() < 0.7:
        noise = np.empty((h, w), np.float32); cv2.randn(noise, 0, rng.uniform(0.003, 0.04))
        img = img + noise
    img = np.clip(img, 0, 1)
    if rng.rand() < 0.3:
        ok, buf = cv2.imencode('.jpg', (img * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(rng.randint(25, 90))])
        img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
    return np.ascontiguousarray(img, np.float32)


def loss_fn(out, heat, off, mask):
    p = out[:, :4].float().clamp(1e-4, 1 - 1e-4)
    pos = (heat == 1).float()
    focal = -(pos * (1 - p) ** 2 * torch.log(p) + (1 - pos) * (1 - heat) ** 4 * p ** 2 * torch.log(1 - p))
    hl = focal.sum() / pos.sum().clamp(min=1)
    m = mask.repeat_interleave(2, 1)
    ol = (F.smooth_l1_loss(out[:, 4:].float(), off, reduction='none', beta=0.1) * m).sum() / m.sum().clamp(min=1)
    return hl + 4 * ol, hl, ol


class Loader:
    """Thread-based loader: worker processes each load CUDA DLLs and exhaust memory on a 16 GB machine."""

    def __init__(self, dataset, batch, train, threads):
        self.dataset, self.batch, self.train = dataset, batch, train
        self.pool = ThreadPoolExecutor(threads)

    def __len__(self):
        return len(self.dataset) // self.batch if self.train else math.ceil(len(self.dataset) / self.batch)

    def __iter__(self):
        order = np.random.permutation(len(self.dataset)) if self.train else np.arange(len(self.dataset))
        futures = [self.pool.submit(self.dataset.__getitem__, int(i)) for i in order[:len(self) * self.batch]]
        for b in range(len(self)):
            items = [f.result(timeout=300) for f in futures[b * self.batch:(b + 1) * self.batch]]
            yield [torch.stack(col) for col in zip(*items)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='+'); ap.add_argument('--out', required=True)
    ap.add_argument('--epochs', type=int, default=160); ap.add_argument('--batch', type=int, default=48)
    ap.add_argument('--workers', type=int, default=12); ap.add_argument('--lr', type=float, default=2e-3)
    ap.add_argument('--resume', action='store_true'); ap.add_argument('--init'); ap.add_argument('--start-epoch', type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    train = Loader(Doors(a.roots, 'train', True), a.batch, True, a.workers)
    val = Loader(Doors(a.roots, 'val', False), a.batch, False, a.workers)
    print('train', len(train.dataset), 'val', len(val.dataset), flush=True)
    dev = 'cuda'
    net = DoorNet().to(dev).to(memory_format=torch.channels_last)
    print('params', sum(p.numel() for p in net.parameters()), flush=True)
    opt = torch.optim.AdamW(net.parameters(), a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.epochs * len(train), pct_start=0.05)
    scaler = torch.amp.GradScaler()
    first = 0
    if a.resume and (out / 'last.ckpt').exists():
        ck = torch.load(out / 'last.ckpt', map_location=dev)
        net.load_state_dict(ck['net']); opt.load_state_dict(ck['opt']); sched.load_state_dict(ck['sched']); scaler.load_state_dict(ck['scaler'])
        first = ck['epoch'] + 1
    elif a.init:
        # weights only (no optimizer state was kept): continue the schedule from --start-epoch
        net.load_state_dict(torch.load(a.init, map_location=dev)); first = a.start_epoch
        for _ in range(first * len(train)):
            opt.step(); sched.step()
        opt.zero_grad(set_to_none=True)
    print('starting at epoch', first, flush=True)
    t0 = time.time()
    for ep in range(first, a.epochs):
        net.train(); tot = np.zeros(3); n = 0
        for img, heat, off, mask, _ in train:
            img, heat, off, mask = [t.to(dev, non_blocking=True) for t in (img, heat, off, mask)]
            with torch.autocast('cuda', dtype=torch.float16):
                o = net(img.contiguous(memory_format=torch.channels_last))
            l, hl, ol = loss_fn(o, heat, off, mask)
            opt.zero_grad(set_to_none=True)
            scaler.scale(l).backward(); scaler.step(opt); scaler.update(); sched.step()
            tot += [l.item(), hl.item(), ol.item()]; n += 1
        msg = f'ep {ep} loss {tot[0]/n:.4f} heat {tot[1]/n:.4f} off {tot[2]/n:.4f} t {time.time()-t0:.0f}s'
        if ep % 5 == 4 or ep == a.epochs - 1:
            net.eval(); errs = []; miss = 0; cnt = 0
            with torch.no_grad():
                for img, heat, off, mask, pts in val:
                    o = net(img.to(dev)).float().cpu().numpy()
                    for b in range(len(o)):
                        p, c = decode(o[b])
                        for j in range(4):
                            if heat[b, j].max() == 1:
                                cnt += 1
                                if c[j] < MIN_CONF: miss += 1
                                else: errs.append(float(np.linalg.norm(p[j] - pts[b, j].numpy())))
            e = np.array(errs)
            msg += f' | val px median {np.median(e):.3f} p90 {np.percentile(e,90):.3f} p99 {np.percentile(e,99):.3f} max {e.max():.1f} miss {miss}/{cnt}'
            torch.save(net.state_dict(), out / 'door_net.pt')
        torch.save(dict(net=net.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), scaler=scaler.state_dict(), epoch=ep), out / 'last.tmp')
        (out / 'last.tmp').replace(out / 'last.ckpt')
        print(msg, flush=True)
    print('TRAIN_DONE', flush=True)


if __name__ == '__main__':
    main()
