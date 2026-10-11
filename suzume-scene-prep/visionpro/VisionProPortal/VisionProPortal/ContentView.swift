import SwiftUI

struct ContentView: View {
    @Environment(PortalSession.self) private var session
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace
    var body: some View {
        @Bindable var session = session
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("铃芽之旅 · 梦幻门").font(.largeTitle)
                Text("透过实体门，望见星空下的花海。").foregroundStyle(.secondary)
                Button(session.spaceState == .open ? "退出梦幻门" : "进入梦幻门") {
                    Task { await toggleSpace() }
                }.disabled(session.spaceState == .transitioning)
                Text(session.status).font(.callout)
                if let error = session.assetError { Text(error).foregroundStyle(.red) }
                Divider()
                Text("对齐实体门").font(.title2)
                Text("先显示门框，将四个内角重合；净高变化时，宽度和花海按原比例缩放。")
                    .font(.callout).foregroundStyle(.secondary)
                adjustment("门洞净高", value: $session.config.height, range: 0.5...3.5, step: 0.01, unit: "米")
                adjustment("左右", value: $session.config.x, range: -5...5, step: 0.01, unit: "米")
                adjustment("门槛高度", value: $session.config.y, range: -1...2, step: 0.01, unit: "米")
                adjustment("前后", value: $session.config.z, range: -8...1, step: 0.01, unit: "米")
                adjustment("朝向", value: $session.config.yawDegrees, range: -180...180, step: 0.5, unit: "度")
                adjustment("花海亮度", value: $session.config.lightExponent, range: -2...4, step: 0.1, unit: "档")
                Picker("虚拟门框", selection: $session.config.frameMode) {
                    ForEach(PortalConfig.FrameMode.allCases) { mode in Text(mode.rawValue).tag(mode) }
                }
                HStack {
                    Button("保存参数") { session.saveCalibration() }
                    Button("读取参数") { session.restoreCalibration() }
                    Button("重置") { session.config = PortalConfig() }
                }
                Text("手动对齐版本：每次进入都要核对位置。实体门扇和行人的自动遮挡尚待接入与实机验证。")
                    .font(.footnote).foregroundStyle(.secondary)
            }.padding(28)
        }
    }
    private func adjustment(_ name: String, value: Binding<Float>, range: ClosedRange<Float>, step: Float, unit: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(name)
                Spacer()
                Text("\(value.wrappedValue, specifier: "%.2f") \(unit)").monospacedDigit()
            }
            Slider(value: value, in: range, step: step)
        }
    }
    @MainActor
    private func toggleSpace() async {
        if session.spaceState == .open {
            session.spaceState = .transitioning
            await dismissImmersiveSpace()
            session.spaceState = .closed
        } else if session.spaceState == .closed {
            session.spaceState = .transitioning
            switch await openImmersiveSpace(id: PortalSession.spaceID) {
            case .opened: session.spaceState = .open
            case .userCancelled:
                session.spaceState = .closed
                session.status = "已取消进入。"
            case .error:
                session.spaceState = .closed
                session.status = "系统未能打开沉浸空间，请稍后重试。"
            @unknown default:
                session.spaceState = .closed
                session.status = "未能进入沉浸空间。"
            }
        }
    }
}
