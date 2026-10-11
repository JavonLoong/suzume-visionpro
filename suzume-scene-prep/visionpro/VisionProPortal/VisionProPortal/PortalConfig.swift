import Foundation
import Observation

/// 米，Y 向上，门槛中点为原点，朝 -Z 看入门后世界。
struct PortalConfig: Codable, Equatable {
    var height: Float = 2.1
    var x: Float = 0
    var y: Float = 0
    var z: Float = -2
    var yawDegrees: Float = 0
    var lightExponent: Float = 1
    var frameMode: FrameMode = .reference
    enum FrameMode: String, Codable, CaseIterable, Identifiable {
        case reference = "显示对齐门框"
        case occlusion = "门框仅作遮挡"
        case hidden = "隐藏虚拟门框"
        var id: String { rawValue }
    }
}

struct PortalAssetMetadata: Decodable {
    struct Aperture: Decodable { let width: Float; let height: Float }
    let aperture: Aperture
}

enum PortalAssetError: LocalizedError {
    case missing(String)
    case invalidMetadata
    var errorDescription: String? {
        switch self {
        case .missing(let name): return "缺少模型资源：\(name)。请检查 Xcode 的资源复制阶段。"
        case .invalidMetadata: return "模型尺寸清单无效，请重新导出 v56 资源。"
        }
    }
}

@MainActor @Observable
final class PortalSession {
    enum SpaceState { case closed, transitioning, open }
    static let spaceID = "suzumePortalSpace"
    var spaceState: SpaceState = .closed
    var config = PortalConfig()
    var status = "准备就绪。进入后，先对齐实体门的四个内角。"
    var assetError: String?
    func saveCalibration() {
        if let data = try? JSONEncoder().encode(config) {
            UserDefaults.standard.set(data, forKey: "SuzumePortalCalibrationV2")
            status = "参数已保存。下次进入仍需核对门框位置。"
        }
    }
    func restoreCalibration() {
        guard let data = UserDefaults.standard.data(forKey: "SuzumePortalCalibrationV2"),
              let saved = try? JSONDecoder().decode(PortalConfig.self, from: data) else { return }
        config = saved
        status = "已读取上次参数；它不是空间锚点，请重新核对位置。"
    }
}
