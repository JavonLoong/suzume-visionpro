"""python export_onnx.py door_net.pt door_net.onnx  -- exports and checks onnxruntime against PyTorch."""
import sys, numpy as np, torch, onnxruntime as ort
from common import *
net = DoorNet(); net.load_state_dict(torch.load(sys.argv[1], map_location='cpu')); net.eval()
x = torch.rand(1, 1, IN_H, IN_W)
torch.onnx.export(net, x, sys.argv[2], opset_version=9, input_names=['image'], output_names=['maps'], dynamo=False)
sess = ort.InferenceSession(sys.argv[2], providers=['CPUExecutionProvider'])
d = np.abs(sess.run(None, {'image': x.numpy()})[0] - net(x).detach().numpy()).max()
import onnx
print('ops', sorted({n.op_type for n in onnx.load(sys.argv[2]).graph.node}), 'max diff', d)
assert d < 1e-4
print('EXPORT_PASS')
