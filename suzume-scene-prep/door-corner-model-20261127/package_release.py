from pathlib import Path
import json,hashlib,shutil,subprocess,zipfile

root=Path(__file__).resolve().parent
project=Path('D:/suzume-picounity')
mirror=Path('D:/虚拟C盘/JavonLoongSkill/suzume-visionpro-public/suzume-scene-prep/picounity')
release=Path('D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/PICO安装包/实体门联调_1.13.5_四角局部精定位_20261127')
log=(root/'release-build.log').read_text(encoding='utf-8',errors='replace')
assert 'APK 已生成:' in log and '[DoorCornerReleaseCheck] local model, pipeline and aperture checks passed' in log
assert 'error CS' not in log and 'Shader error' not in log
candidate=json.loads((root/'模型核验.json').read_text(encoding='utf-8'))
assert hashlib.sha256((project/'Assets/Resources/DoorNet/door_corner.onnx').read_bytes()).hexdigest()==candidate['sha256']
assert hashlib.sha256((project/'Assets/Editor/CornerRefinementTrial/door_corner.onnx').read_bytes()).hexdigest()==candidate['sha256']
assert json.loads((root/'final_stress_6000.json').read_text(encoding='utf-8'))['passes_no_regression_gate']
apk=project/'Builds/SuzumePortal-PICO-PhysicalDoor-v1.13.5.apk'
android=Path('D:/Unity/Editors/2022.3.62f3/Editor/Data/PlaybackEngines/AndroidPlayer')
badging=subprocess.run([str(android/'SDK/build-tools/34.0.0/aapt.exe'),'dump','badging',str(apk)],check=True,capture_output=True,text=True,encoding='utf-8').stdout
assert "package: name='com.suzume.portal.bletrial' versionCode='27' versionName='1.13.5'" in badging
signature=subprocess.run([str(android/'OpenJDK/bin/java.exe'),'-jar',str(android/'SDK/build-tools/34.0.0/lib/apksigner.jar'),'verify','--verbose',str(apk)],check=True,capture_output=True,text=True).stdout
candidate['apk_integrated']=True
candidate['integration_version']='1.13.5'
candidate['integration_apk_sha256']=hashlib.sha256(apk.read_bytes()).hexdigest()
candidate['unity_fixture_agreement']='86/86'
(root/'模型核验.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
release.mkdir(exist_ok=True);proof=release/'验证记录';proof.mkdir(exist_ok=True)
shutil.copy2(apk,release/apk.name)
for name in ['模型核验.json','unity-refiner-check.txt','final_stress_6000.json','config.json','continue_config.json','geometric_config.json']:
 shutil.copy2(root/name,proof/name)
shutil.copy2('D:/suzume-aperture-fit-20261125/aperture-check.txt',proof/'aperture-check.txt')
(proof/'apk-badging.txt').write_text(badging,encoding='utf-8');(proof/'apk-signature.txt').write_text(signature,encoding='utf-8')
(proof/'regression-summary.txt').write_text('\n'.join(line for line in log.splitlines() if line.startswith('[') and ('PASS' in line or 'checks passed' in line))+'\n',encoding='utf-8')
readme='''铃芽之旅 · 实体门联调 1.13.5（2026-11-27）
阶段测试包；整体目标仍在进行中，不能称为已完成实物精准识别和展示验收。
包名 com.suzume.portal.bletrial，版本 1.13.5 / 27。覆盖“实体门联调”，不覆盖 11.18 主应用。
本次电脑没有检测到 PICO，没有安装到头显，也没有操作实体门。

本轮实质改进
继续用原模型找门，新增一个只有 23427 个参数的局部模型，重新看四个内角。
四个角的置信分数都达到 0.5，移动量都不超过 max(1.5 像素，预测门宽的 8%)，且四边形有效，才整组采用修正。
只要一个角不可靠，就保留原来四个角，避免拼接出不一致的形状。
局部模型已接入实际识别到空间计算的流程；用户冻结、微调、确认和保存方式保持不变。
局部计算分段执行；切换目标、取消、结果过期或销毁组件后不得发布旧结果。
保留上一版相机姿态配对修复，以及此前的门洞裁切、四角微调和主控适配。

训练和指标（开发诊断，不是独立实物准确率）
局部模型训练 6000 步。训练批次包含开门渲染图、一般渲染图、旧屏幕实拍和 AI 图，最后加入旋转、倾斜和拉伸变化。
严格标准：四个角中的最大误差不超过门洞宽度的 1%。
AI 同源诊断：0/45 → 11/45；最大角点误差中位数约 6.41 → 4.93 像素；误差占门宽中位数 3.80% → 2.82%。
合成图：6/309 → 22/309；原有粗位置通过数保持 274/309。
旧屏幕图 6 项、原实拍参考 5 项的粗位置通过数保持；严格标准仍是 0，没有改善。
46 项原负样本没有新增误报。局部模型本身不创建新检测，只处理原模型已找到的门。
117 项同源变化检查包含缩小、偏移、旋转、明暗、模糊、压缩、二维透视和遮挡；各组粗位置通过数未下降。
中间实验曾在侧视和旧案例上退步；本包使用通过最终检查的 step6000、四角联合 0.5 阈值，并非早期的宽松实验方案。

Unity 与运行流程检查
86 项参考计算：采用/拒绝判断全部一致；坐标最大差约 0.000183 像素。
实际 DoorAutoLocator 流程已验证：修正角点进入空间计算；取消时不发布结果。
未使用就释放、重复释放、处理中释放、异步取消、再次使用等情况通过。
电脑 CPU Burst 推理中位数约 29.44 毫秒；一项异步样本总耗时约 52.57 毫秒，最长主线程片段约 0.57 毫秒。
上述时间是电脑数据，不能当作头显速度或帧率。
控制器、四角调整、保存/取消和六角度裁切回归通过。裁切检查排除了 2 像素栅格边缘。
APK 包名、版本和签名通过核验。

仍需完成
真实门洞的双眼贴边、头动时对齐与漂移、头显帧率/识别延迟、跨次启动锚点恢复、实体机构主控连接及开闭到位回执。
新增 AI 图片来自同一参考，不能代替独立的真实门洞样本。手工标注存在边缘不确定性。
不要把 0.1/0.5 毫米的微调步长当成实测精度。

操作
右扳机引导识别，再按右扳机冻结；右摇杆按下进入微调。
A/X 选择整体或角；左摇杆左右/前后，右摇杆上下；Y 切步长；右扳机保存，B 取消。
Browse 展示状态且主控查询确认可用后：右 A 开门、右 B 复位；Tune 中保持选角/取消功能。

记录位置
完整训练与实验：D:/suzume-integration-20261127/corner-refinement
源码已同步本机 Git 工作区，未提交或推送 GitHub。
'''
(release/'00_阶段结果与操作说明.txt').write_text(readme,encoding='utf-8-sig')
changes=['Assets/Scripts/DoorAutoLocator.cs','Assets/Scripts/DoorCornerRefiner.cs','Assets/Scripts/DoorCornerRefiner.cs.meta',
 'Assets/Editor/BuildPicoApk.cs','Assets/Editor/DoorCornerRefinerCheck.cs','Assets/Editor/DoorCornerRefinerCheck.cs.meta',
 'Assets/Editor/DoorCornerReleaseCheck.cs','Assets/Editor/DoorCornerReleaseCheck.cs.meta',
 'Assets/Resources/DoorNet/door_corner.onnx','Assets/Resources/DoorNet/door_corner.onnx.meta']
def equal(a,b):
 if a.read_bytes()==b.read_bytes():return True
 try:return a.read_text(encoding='utf-8')==b.read_text(encoding='utf-8')
 except UnicodeDecodeError:return False
for name in changes:
 source=project/name;target=mirror/name;before=root/'before'/source.name
 assert source.is_file(),name
 assert not target.exists() or equal(source,target) or (before.exists() and equal(before,target)),f'Unrelated change: {target}'
for name in changes:
 source=project/name;target=mirror/name;target.parent.mkdir(exist_ok=True,parents=True)
 if source.suffix=='.cs':source.write_text(source.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
 shutil.copy2(source,target)
settings=mirror/'ProjectSettings/ProjectSettings.asset';s=settings.read_text(encoding='utf-8').replace('bundleVersion: 1.13.4','bundleVersion: 1.13.5').replace('AndroidBundleVersionCode: 26','AndroidBundleVersionCode: 27');settings.write_text(s,encoding='utf-8',newline='\n')
with zipfile.ZipFile(release/'本轮源码与模型.zip','w',zipfile.ZIP_DEFLATED) as out:
 for name in changes:out.write(project/name,name)
 out.write(settings,'ProjectSettings/ProjectSettings.asset')
 for script in root.glob('*.py'):out.write(script,'训练实验/'+script.name)
 out.write(root/'step6000.pt','训练实验/step6000.pt')
manifest={'goal_status':'active','goal_complete':False,'version':'1.13.5','version_code':27,
 'apk_bytes':apk.stat().st_size,'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
 'global_model_sha256':hashlib.sha256((project/'Assets/Resources/DoorNet/door_net.onnx').read_bytes()).hexdigest(),
 'local_model_sha256':candidate['sha256'],'local_training_steps':6000,'local_model_integrated':True,
 'headset_installed':False,'headset_tested':False,'physical_controller_tested':False,'real_corner_precision_verified':False,
 'github_pushed':False,'source_files':changes}
(release/'阶段核验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(release);print(json.dumps(manifest,ensure_ascii=False))
