import SwiftUI

@main
struct VisionProPortalApp: App {
    @State private var session = PortalSession()
    var body: some Scene {
        WindowGroup { ContentView().environment(session) }
            .defaultSize(width: 620, height: 760)
        ImmersiveSpace(id: PortalSession.spaceID) { PortalImmersiveView().environment(session) }
            .immersionStyle(selection: .constant(.mixed), in: .mixed)
    }
}
