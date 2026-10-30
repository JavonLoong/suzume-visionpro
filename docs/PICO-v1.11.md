# PICO v1.11 发布记录

版本：1.11（versionCode 12），包名：`com.suzume.portal`。
日期：2026-10-30，台北时间。

## 本次行为

- 保留山坡与平缓花海。浏览时 A 切换场景；选点时 A 只选择最终显示的场景，不打断定位。
- 启动时隐藏虚拟门和场景。瞄准左下角按右扳机记录第一条线，横移手柄后再次瞄准同一角。
- 连续显示两条前向射线的最近点、连接线、中点与距离，不要求两线相交，也没有 5 厘米通过门槛。第二次扳机记录中点。
- 顺序为左下、右下、左上、右上，八次选线后显示细线预览，再按一次右扳机确认显示虚拟门和场景。
- 手柄跟踪丢失时保留最近显示，禁止记录暂停的旧数据。严格平行时沿用上次深度并提示无法唯一确定远近。
- 完全移除旧诊断版的控制文件、定时隐藏画面和输入暂停入口。
- 在应用前台期间申请保持唤醒；离开前台释放请求，不修改头显全局休眠设置。
- 运行中休眠或失去焦点时保留已选角点与步骤，恢复后先松开按钮才能继续。强制结束应用后不承诺恢复未完成选点。

## 已完成验证

Unity 构建成功。ControllerTrialCheck、PortalRayTrialCheck、PassthroughTrialCheck、ContinuousRayTrialCheck、StablePlacementTrialCheck 均通过。

检查包含 2,001 个射线方向、连续预览与跟踪丢失、透明背景、1,800 次无按键更新、八次选线及最终确认；新增第二角点后暂停、暂停期间输入、按住按钮恢复、保留前两角并继续完成后两角的模拟。

ARM64 原生插件在 PICO 上完成连续 1,500 帧的画面层保留检查。

真机在 23:35:27 建立前台保亮请求，23:35:55 记录第四角，23:36:11 进入浏览状态。用户明确确认“能连续完成四个角，没有黑屏”。此前黑屏的系统日志显示佩戴检测在约 10–13 秒后触发休眠。约 90 秒的本次连续唤醒已超过此前中断时间；尚未进行长时间稳定性测试。

## 下载与对应源码

[APK](https://github.com/JavonLoong/suzume-visionpro/releases/download/complete-project-2026-10-30/SuzumePortal-PICO.apk) · [完整 Release](https://github.com/JavonLoong/suzume-visionpro/releases/tag/complete-project-2026-10-30) · [SHA-256](https://github.com/JavonLoong/suzume-visionpro/releases/download/complete-project-2026-10-30/SHA256SUMS.txt)

APK SHA-256：`7ab786a45d48dc3c0449c93aba9e81659d3001799ea17a1f2a31e64d4a98a091`。

此包与本次 Git 源码快照对应；固定 PICO SDK 提交与本地补丁由 `tools/prepare_pico.py` 恢复。完整源文件位置、大小和校验值见 `PROJECT_MANIFEST.json`。打印资料与 Vision Pro 的验收状态独立，不因本次归档而视为通过真机或最终打印验收。

参考资料：[PICO 官方 Enterprise API（AcquireWakeLock / ReleaseWakeLock）](https://sdk.picovr.com/docs/XRPlatformSDK/Unity/en/chapter_seven.html)。
