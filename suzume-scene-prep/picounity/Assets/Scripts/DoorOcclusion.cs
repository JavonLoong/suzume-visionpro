using UnityEngine;

/// 虚拟门框 + 门扇（遮挡兜底）。
///
/// 为什么需要：MR 透视图层只是把真实画面垫在底层，虚拟内容默认会「浮」在真实物体之上，
/// 真实门扇/人体无法正确遮挡门后世界。先用与实体门框同尺寸的「虚拟门框 + 门扇」挡在门洞前，
/// 让虚拟门扇正常遮挡门后世界。之后再用 PICO 场景理解(Spatial Mesh)升级为真实遮挡。
public static class DoorOcclusion
{
    /// <summary>构建门框 + 门扇，返回容器（便于 PortalManager 统一打标记）。</summary>
    public static GameObject Build(Transform parent)
    {
        var door = new GameObject("DoorAssembly");
        door.transform.SetParent(parent, false);

        BuildFrame(door.transform);
        BuildLeaf(door.transform);
        return door;
    }

    static void BuildFrame(Transform parent)
    {
        var frame = new GameObject("DoorFrame");
        frame.transform.SetParent(parent, false);

        var mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.82f, 0.82f, 0.82f);

        float w = PortalConfig.DoorWidth;
        float h = PortalConfig.DoorHeight;
        float t = PortalConfig.DoorThickness;

        // 左右立柱
        foreach (float side in new[] { -1f, 1f })
        {
            var post = GameObject.CreatePrimitive(PrimitiveType.Cube);
            post.name = "Post";
            post.transform.SetParent(frame.transform, false);
            post.transform.localScale = new Vector3(t, h, t);
            post.transform.localPosition = new Vector3(side * (w / 2 + t / 2), h / 2, 0);
            post.GetComponent<MeshRenderer>().sharedMaterial = mat;
            post.GetComponent<Collider>().enabled = false;
        }
        // 上梁
        var header = GameObject.CreatePrimitive(PrimitiveType.Cube);
        header.name = "Header";
        header.transform.SetParent(frame.transform, false);
        header.transform.localScale = new Vector3(w + 2 * t, t, t);
        header.transform.localPosition = new Vector3(0, h + t / 2, 0);
        header.GetComponent<MeshRenderer>().sharedMaterial = mat;
        header.GetComponent<Collider>().enabled = false;
    }

    static void BuildLeaf(Transform parent)
    {
        var mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.78f, 0.78f, 0.78f);

        // 铰链放在左侧立柱处，门扇作为铰链的子物体向外偏移半个门宽，
        // 这样绕 Y 轴旋转铰链 = 真实的开门动作。
        var hinge = new GameObject("DoorHinge");
        hinge.transform.SetParent(parent, false);
        hinge.transform.localPosition = new Vector3(-PortalConfig.DoorWidth / 2f, 0f, 0f);

        var leaf = GameObject.CreatePrimitive(PrimitiveType.Cube);
        leaf.name = "DoorLeaf";
        leaf.transform.SetParent(hinge.transform, false);
        leaf.transform.localScale = new Vector3(
            PortalConfig.DoorWidth, PortalConfig.DoorHeight, PortalConfig.DoorThickness * 0.5f);
        // 相对铰链：向右移半个门宽、抬高半个门高
        leaf.transform.localPosition = new Vector3(
            PortalConfig.DoorWidth / 2f, PortalConfig.DoorHeight / 2f, 0f);
        leaf.GetComponent<MeshRenderer>().sharedMaterial = mat;
        leaf.GetComponent<Collider>().enabled = false;

        // 默认开门：门扇绕铰链转开，露出门洞才能看到门后世界。
        // 0 = 关闭（会挡住门后世界），-100 = 向内开约 100 度。
        hinge.transform.localRotation = Quaternion.Euler(0f, PortalConfig.DoorOpenAngle, 0f);
    }
}
