import Foundation
import RealityKit
import simd

@MainActor
final class PortalSystem {
    let root = Entity()
    private var world: Entity?
    private var referenceFrame: Entity?
    private var occludingFrame: Entity?
    private var metadata: PortalAssetMetadata?
    private var disposed = false
    func setup() async throws {
        let dimensions = try DreamWorldBuilder.metadata()
        let target = try await DreamWorldBuilder.build()
        let frame = try await Entity(contentsOf: DreamWorldBuilder.resource("DoorFrame", extension: "usdz"))
        try Task.checkCancellation()
        guard !disposed else { throw CancellationError() }
        let portal = Entity()
        portal.name = "DoorwayAperture"
        let w = dimensions.aperture.width / 2
        let h = dimensions.aperture.height
        // 网格原点在门槛；与 USDZ 原点一致。
        var descriptor = MeshDescriptor(name: "DoorwayOpening")
        descriptor.positions = .init([[-w, 0, 0], [w, 0, 0], [w, h, 0], [-w, h, 0]])
        descriptor.normals = .init(Array(repeating: SIMD3<Float>(0, 0, 1), count: 4))
        descriptor.textureCoordinates = .init([[0, 0], [1, 0], [1, 1], [0, 1]])
        descriptor.primitives = .triangles([0, 1, 2, 0, 2, 3])
        let mesh = try MeshResource.generate(from: [descriptor])
        portal.components.set(ModelComponent(mesh: mesh, materials: [PortalMaterial()]))
        var component = PortalComponent(target: target)
        component.clippingMode = .plane(.positiveZ)
        portal.components.set(component)
        let occlusion = frame.clone(recursive: true)
        DoorOcclusion.replaceMaterials(in: occlusion, with: OcclusionMaterial())
        root.name = "SuzumeDoorwayRoot"
        // target 也必须在场景树内，WorldComponent 负责限制可见范围。
        root.addChild(target)
        root.addChild(portal)
        root.addChild(frame)
        root.addChild(occlusion)
        metadata = dimensions
        world = target
        referenceFrame = frame
        occludingFrame = occlusion
    }
    func update(_ config: PortalConfig) {
        guard let metadata else { return }
        root.position = [config.x, config.y, config.z]
        root.orientation = simd_quatf(angle: config.yawDegrees * .pi / 180, axis: [0, 1, 0])
        root.scale = .init(repeating: config.height / metadata.aperture.height)
        referenceFrame?.isEnabled = config.frameMode == .reference
        occludingFrame?.isEnabled = config.frameMode == .occlusion
        if let world, var light = world.components[ImageBasedLightComponent.self] {
            light.intensityExponent = config.lightExponent
            world.components.set(light)
        }
    }
    func teardown() {
        disposed = true
        root.removeFromParent()
        root.children.removeAll()
        world = nil
        referenceFrame = nil
        occludingFrame = nil
    }
}
