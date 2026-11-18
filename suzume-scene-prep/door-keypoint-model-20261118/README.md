# 小门四角检测模型

这是 PICO v1.12 使用的门框四角模型和可复现实验代码。模型只用渲染图训练，尚未用实拍门验证。

## 文件

| 文件 | 用途 |
| --- | --- |
| `train.py`、`common.py` | 训练网络 |
| `evaluate.py` | 按 Unity 相同的两遍检测流程评估 |
| `export_onnx.py` | 从 PyTorch 权重导出并核对 ONNX |
| `run1/door_net.pt` | 最终 PyTorch 权重 |
| `run1/last.ckpt` | 可继续训练的检查点 |
| `door_net.onnx` | Unity 使用的最终模型 |
| `eval_*.txt` | 已保存的评估结果 |
| `unity_reference.txt` | Unity 与 Python 对照所需的逐图结果 |

模型输入是 `1×288×384` 灰度图，输出是 `72×96×12`：四张角点热图，加上每个角点的横向和纵向偏移。角点顺序固定为左下、右下、左上、右上。

## 常用命令

```powershell
python train.py ../door-keypoint-train-20261118 --out run1 --epochs 160 --batch 48
python evaluate.py run1/door_net.pt ../door-keypoint-dataset-20261118 --split all
python export_onnx.py run1/door_net.pt door_net.onnx
```

完整指标、Unity 对照和真机待测项见 [PICO v1.12 发布记录](../../docs/PICO-v1.12-door-vision.md)。
