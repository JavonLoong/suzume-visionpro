using UnityEngine;

// A controller ray has direction but no measured depth. Search several distances along
// that world-space ray, reprojected through the current camera pose (including parallax).
public sealed class DoorSearchHint
{
    // Close targets move rapidly across camera pixels because the controller is below the eye.
    // Fill the former 25-45 cm gap and alternate two crop scales without searching the whole room.
    static readonly float[] Distances = { .30f, .25f, .35f, .20f, .40f, .45f, .60f, .75f, 1.25f, 2.2f, 4f, .12f, .18f };
    public static int SearchCycleLength => Distances.Length * 2;
    public Ray Ray { get; private set; }
    public bool Active { get; private set; }
    public int Revision { get; private set; }
    public bool HasFocus { get; private set; }
    Vector3 _focus;
    int _next;

    public bool Set(Ray ray)
    {
        if (!Finite(ray.origin) || !Finite(ray.direction) || ray.direction.sqrMagnitude < .5f) return false;
        Ray = new Ray(ray.origin, ray.direction.normalized); Active = true; HasFocus = false; _next = 0; Revision++;
        return true;
    }
    public void Clear() { Active = false; HasFocus = false; Revision++; }
    public void RestartScales() { HasFocus = false; _next = 0; Revision++; }
    public void Focus(Vector3 centre) { _focus = centre; HasFocus = true; }
    public void ClearFocus() { HasFocus = false; }

    public bool TryCrop(DoorCameraFrame frame, float doorHeight, out Rect crop)
    {
        crop = default;
        if (!Active || frame.width < 2 || frame.height < 2 || frame.fx <= 0 || frame.fy <= 0 || doorHeight <= 0) return false;
        Matrix4x4 worldToCamera = frame.cameraToWorld.inverse;
        for (int i = 0; i < (HasFocus ? 1 : SearchCycleLength); i++)
        {
            int slot = HasFocus ? 0 : _next++ % SearchCycleLength;
            float fill = HasFocus ? .45f : (slot % 2 == 0 ? .4f : .6f);
            Vector3 p = worldToCamera.MultiplyPoint3x4(HasFocus ? _focus : Ray.GetPoint(Distances[slot / 2]));
            if (!Finite(p) || p.z < .06f) continue;
            Vector2 centre = new Vector2(frame.cx + frame.fx * p.x / p.z, frame.cy - frame.fy * p.y / p.z);
            if (centre.x < 0 || centre.x >= frame.width || centre.y < 0 || centre.y >= frame.height) continue;
            // Covers imperfect pointing without shrinking a small door into the whole image.
            float h = Mathf.Max(72f, doorHeight * frame.fy / p.z / fill, 2f * frame.fy * Mathf.Tan(6f * Mathf.Deg2Rad));
            h = Mathf.Min(h, frame.height * .78f, frame.width * .75f * .78f);
            float w = h * (4f / 3f);
            centre.x = Mathf.Clamp(centre.x, w * .5f, frame.width - w * .5f);
            centre.y = Mathf.Clamp(centre.y, h * .5f, frame.height - h * .5f);
            crop = new Rect(centre.x - w * .5f, centre.y - h * .5f, w, h);
            return true;
        }
        return false;
    }

    // A confident rectangle elsewhere in the room must not override the user's target.
    public bool Accepts(Vector3 centre, float doorHeight)
    {
        if (!Active || !Finite(centre)) return false;
        Vector3 offset = centre - Ray.origin;
        float along = Vector3.Dot(offset, Ray.direction);
        if (along < .06f || along > 5f) return false;
        float radius = Mathf.Max(doorHeight * .6f, .015f) + along * Mathf.Tan(8f * Mathf.Deg2Rad);
        return (offset - along * Ray.direction).sqrMagnitude <= radius * radius;
    }

    static bool Finite(Vector3 v) => !float.IsNaN(v.x + v.y + v.z) && !float.IsInfinity(v.x + v.y + v.z);
}
