import Foundation
import RealityKit
import ImageIO

@MainActor
enum DreamWorldBuilder {
    static func resource(_ name: String, extension ext: String) throws -> URL {
        guard let url = Bundle.main.url(forResource: name, withExtension: ext) else {
            throw PortalAssetError.missing("\(name).\(ext)")
        }
        return url
    }
    static func metadata() throws -> PortalAssetMetadata {
        let url = try resource("AssetManifest", extension: "json")
        let result = try JSONDecoder().decode(PortalAssetMetadata.self, from: Data(contentsOf: url))
        guard result.aperture.width > 0, result.aperture.height > 0 else { throw PortalAssetError.invalidMetadata }
        return result
    }
    static func build() async throws -> Entity {
        let world = Entity()
        world.name = "DoorwayWorld"
        world.components.set(WorldComponent())
        let model = try await Entity(contentsOf: resource("DreamWorld", extension: "usdz"))
        world.addChild(model)
        // 天空只显示一次色彩，避免 USD 发光材质与环境光再次叠加。
        let skyTexture = try await TextureResource(named: "NightSky.png", in: .main)
        var skyMaterial = UnlitMaterial()
        skyMaterial.color = .init(texture: .init(skyTexture))
        skyMaterial.faceCulling = .none
        if let sky = model.findEntity(named: "DistantSky") {
            DoorOcclusion.replaceMaterials(in: sky, with: skyMaterial)
        }
        let skyURL = try resource("NightSky", extension: "png")
        guard let imageSource = CGImageSourceCreateWithURL(skyURL as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
            throw PortalAssetError.missing("NightSky.png（无法读取）")
        }
        let environment = try await EnvironmentResource(equirectangular: image, withName: "NightSkyIBL")
        world.components.set(ImageBasedLightComponent(source: .single(environment), intensityExponent: 1))
        model.components.set(ImageBasedLightReceiverComponent(imageBasedLight: world))
        return world
    }
}
