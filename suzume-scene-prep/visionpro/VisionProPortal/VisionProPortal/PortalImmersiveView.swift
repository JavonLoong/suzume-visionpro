import SwiftUI
import RealityKit

struct PortalImmersiveView: View {
    @Environment(PortalSession.self) private var session
    @State private var portalSystem = PortalSystem()
    var body: some View {
        RealityView { content in
            session.assetError = nil
            session.status = "正在载入 v56 门框与花海……"
            do {
                try await portalSystem.setup()
                portalSystem.update(session.config)
                content.add(portalSystem.root)
                session.status = "花海已载入。移动头部，核对四个门角和空间视差。"
            } catch is CancellationError {
                // 加载时退出不显示资源错误。
            } catch {
                session.assetError = error.localizedDescription
                session.status = "载入失败。退出后可重试。"
            }
        } update: { _ in
            portalSystem.update(session.config)
        }
        .onAppear { session.spaceState = .open }
        .onDisappear {
            portalSystem.teardown()
            session.spaceState = .closed
        }
    }
}
