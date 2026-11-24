# 11 月 20 日识别模型记录

当前 APK 使用原有 1.12.8 模型；补充训练的 200 / 400 / 600 步权重没有一致优于原模型，因此未替换部署模型。

`deployed_door_net_step100.pt` 保存当前部署模型对应的训练权重。应用实际加载 `../picounity/Assets/Resources/DoorNet/door_net.onnx`。

`finetune.py`、`evaluate.py` 和 `robust-evaluation.json` 是当时的补充训练和评估记录，脚本含本机数据路径。拍屏原始照片涉及现场环境，未公开；需自行提供对应数据并调整路径，不能仅凭本目录复现完整拍屏评估。旧合成训练数据仍可从之前 Release 取得。

54 个条件来自 3 张照片的相关变换，不是 54 张独立实拍，也不代表现场成功率。说明见 [本次测试报告](../../docs/pico-v1.13.0/01_测试报告.txt)。
