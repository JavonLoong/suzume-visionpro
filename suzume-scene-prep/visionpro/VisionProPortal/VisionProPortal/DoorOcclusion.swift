import RealityKit

@MainActor
enum DoorOcclusion {
    /// 只作用于预先建好的门框。不能识别现实中的门扇或经过的人。
    static func replaceMaterials(in entity: Entity, with material: any Material) {
        if var model = entity.components[ModelComponent.self] {
            model.materials = model.materials.map { _ in material }
            entity.components.set(model)
        }
        for child in entity.children { replaceMaterials(in: child, with: material) }
    }
}
