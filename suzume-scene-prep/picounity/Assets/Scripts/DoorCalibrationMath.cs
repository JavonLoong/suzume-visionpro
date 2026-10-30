using UnityEngine;

public static class DoorCalibrationMath
{
    public struct Placement
    {
        public Vector3 center;
        public Quaternion rotation;
        public float width, height;
    }
    // The four points are the opening's bottom-left, bottom-right, top-left, top-right.
    public static bool TryFit(Vector3[] p, Vector3 viewer, out Placement placement, out string error)
    {
        placement = default; error = "error_shape";
        if (p == null || p.Length < 4) return false;
        foreach (var v in p)
            if (float.IsNaN(v.x + v.y + v.z) || float.IsInfinity(v.x + v.y + v.z)) return false;
        Vector3 bottom = p[1] - p[0]; bottom.y = 0;
        float width = bottom.magnitude;
        if (width < .35f || width > 3f) { error = "error_width"; return false; }
        Vector3 right = bottom / width;
        Vector3 towardViewer = Vector3.Cross(-right, Vector3.up);
        Vector3 center = (p[0] + p[1]) * .5f;
        if (Vector3.Dot(towardViewer, viewer - center) < .05f) { error = "error_order"; return false; }
        float h1 = p[2].y - p[0].y, h2 = p[3].y - p[1].y;
        if (h1 < .5f || h2 < .5f || h1 > 3.5f || h2 > 3.5f) { error = "error_height"; return false; }
        if (Mathf.Abs(p[0].y - p[1].y) > .18f || Mathf.Abs(h1 - h2) > .2f) return false;
        foreach (int i in new[] { 2, 3 })
        {
            Vector3 edge = p[i] - p[i - 2]; edge.y = 0;
            if (edge.magnitude > .22f) return false;
        }
        placement = new Placement { center = center, rotation = Quaternion.LookRotation(towardViewer, Vector3.up), width = width, height = (h1 + h2) * .5f };
        error = null; return true;
    }
}
