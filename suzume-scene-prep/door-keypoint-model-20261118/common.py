"""Shared pieces: network, image sampling, decoding and the two-pass inference used on the headset.

Pixel coordinates are continuous: pixel (i, j) covers [i, i+1) x [j, j+1), its centre is (i+0.5, j+0.5).
"""
import math
import numpy as np, cv2, torch, torch.nn as nn, torch.nn.functional as F

IN_W, IN_H, STRIDE = 384, 288, 4
OUT_W, OUT_H = IN_W // STRIDE, IN_H // STRIDE


def cbr(i, o, s=1):
    return nn.Sequential(nn.Conv2d(i, o, 3, s, 1, bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True))


class DoorNet(nn.Module):
    """Input 1x288x384 grey in [0,1]. Output 12x72x96: 4 corner heatmaps (after sigmoid) + 4 (dx, dy) offsets."""

    def __init__(self):
        super().__init__()
        self.s4 = nn.Sequential(cbr(1, 16, 2), cbr(16, 32, 2), cbr(32, 32), cbr(32, 32))
        self.s8 = nn.Sequential(cbr(32, 64, 2), cbr(64, 64), cbr(64, 64))
        self.s16 = nn.Sequential(cbr(64, 96, 2), cbr(96, 96), cbr(96, 96))
        self.s32 = nn.Sequential(cbr(96, 128, 2), cbr(128, 128), cbr(128, 128))
        self.u16 = cbr(128 + 96, 96)
        self.u8 = cbr(96 + 64, 64)
        self.u4 = nn.Sequential(cbr(64 + 32, 48), cbr(48, 48))
        self.heat = nn.Conv2d(48, 4, 1)
        self.off = nn.Conv2d(48, 8, 1)
        nn.init.constant_(self.heat.bias, -2.19)

    def features(self, x):
        a = self.s4(x); b = self.s8(a); c = self.s16(b); d = self.s32(c)
        up = lambda t: F.interpolate(t, scale_factor=2, mode='nearest')
        c = self.u16(torch.cat([up(d), c], 1))
        b = self.u8(torch.cat([up(c), b], 1))
        return self.u4(torch.cat([up(b), a], 1))

    def forward(self, x):
        f = self.features(x)
        return torch.cat([torch.sigmoid(self.heat(f)), self.off(f)], 1)


def imread_gray(path):
    return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_GRAYSCALE)


def pyramid(gray, levels=6):
    """2x2 box-filter pyramid (odd trailing row/column dropped, mean rounded), same as the C# side."""
    out = [gray]
    for _ in range(levels):
        g = out[-1]
        h, w = g.shape[0] // 2 * 2, g.shape[1] // 2 * 2
        if h < 2 or w < 2:
            break
        out.append(cv2.resize(g[:h, :w], (w // 2, h // 2), interpolation=cv2.INTER_AREA))  # rounded 2x2 mean
    return out


def make_affine(center, k, theta=0.0):
    """2x3 matrix taking network-input coordinates to source-image coordinates. k = source px per input px."""
    c, s = math.cos(theta) * k, math.sin(theta) * k
    A = np.array([[c, -s, 0], [s, c, 0]], np.float64)
    A[:, 2] = np.asarray(center) - A[:, :2] @ np.array([IN_W / 2, IN_H / 2])
    return A


def to_input(A, pts):
    return (np.asarray(pts, np.float64) - A[:, 2]) @ np.linalg.inv(A[:, :2]).T


def to_source(A, pts):
    return np.asarray(pts, np.float64) @ A[:, :2].T + A[:, 2]


def sample(pyr, A, level_bias=0):
    """Bilinear sample of the IN_W x IN_H network input, from the pyramid level matching the scale."""
    k = math.sqrt(abs(np.linalg.det(A[:, :2])))
    level = int(np.clip(math.floor(math.log2(max(k, 1e-6)) + 1e-9) + level_bias, 0, len(pyr) - 1))
    f = 1.0 / (1 << level)
    M = A * f
    M[:, 2] = (A[:, :2] @ np.array([0.5, 0.5]) + A[:, 2]) * f - 0.5
    return cv2.warpAffine(pyr[level], M, (IN_W, IN_H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_REPLICATE)


def decode(out):
    """out: 12xHxW numpy. Returns 4x2 input-pixel coordinates and 4 peak scores."""
    pts, conf = np.zeros((4, 2)), np.zeros(4)
    for i in range(4):
        idx = int(out[i].argmax())
        y, x = divmod(idx, OUT_W)
        conf[i] = out[i, y, x]
        pts[i] = ((x + 0.5 + out[4 + 2 * i, y, x]) * STRIDE, (y + 0.5 + out[5 + 2 * i, y, x]) * STRIDE)
    return pts, conf


FILL = 0.45          # second pass: door's larger extent / crop height
MIN_CONF = 0.3


def full_affine(w, h):
    return make_affine((w / 2, h / 2), max(w / IN_W, h / IN_H))


def crop_affine(pts):
    lo, hi = pts.min(0), pts.max(0)
    size = max(hi[0] - lo[0], hi[1] - lo[1], 4.0)
    return make_affine((lo + hi) / 2, size / (FILL * IN_H))


def detect(run, gray, passes=2):
    """run: function(1x1xHxW float32 array) -> 12xHxW array. Returns (source pixel corners 4x2, conf 4) or None."""
    pyr = pyramid(gray)
    A = full_affine(gray.shape[1], gray.shape[0])
    pts = conf = None
    for n in range(passes + 1):
        x = sample(pyr, A).astype(np.float32)[None, None] / 255.0
        p, conf = decode(run(x))
        if conf.min() < MIN_CONF:
            return None
        pts = to_source(A, p)
        if n == passes:
            break
        A = crop_affine(pts)
    return pts, conf
