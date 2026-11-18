using System.Collections.Generic;
using UnityEngine;

// Pulls the four coarse corners onto the image's real jamb, lintel and threshold lines.
// Each side is located from many gradient samples, so the result is steadier than any single corner estimate.
public static class DoorEdgeRefiner
{
    static readonly int[,] Sides = { { 0, 2 }, { 1, 3 }, { 2, 3 }, { 0, 1 } }; // left, right, top, bottom

    // gray: one byte per pixel, row 0 at the top. Returns how many of the four sides were refined.
    public static int Refine(byte[] gray, int width, int height, Vector2[] corners, Vector2[] refined, float minimumContrast = 6f)
    {
        float doorWidth = (Vector2.Distance(corners[0], corners[1]) + Vector2.Distance(corners[2], corners[3])) * .5f;
        // Stay well inside the jamb's own width so the search cannot jump to the jamb's outer edge.
        float search = Mathf.Clamp(doorWidth * .06f, 1.5f, 6f);
        var point = new Vector2[4]; var direction = new Vector2[4];
        int count = 0;
        var samples = new List<Vector2>(); var signs = new List<float>();
        for (int side = 0; side < 4; side++)
        {
            Vector2 a = corners[Sides[side, 0]], b = corners[Sides[side, 1]];
            float length = Vector2.Distance(a, b);
            point[side] = a; direction[side] = length > 1e-3f ? (b - a) / length : Vector2.right;
            if (length < 8f) continue;
            Vector2 d = direction[side], normal = new Vector2(-d.y, d.x);
            int steps = Mathf.Clamp(Mathf.RoundToInt(length / 1.5f), 6, 40);
            samples.Clear(); signs.Clear();
            for (int i = 0; i < steps; i++)
            {
                Vector2 p = Vector2.Lerp(a, b, Mathf.Lerp(.18f, .82f, i / (steps - 1f)));
                float best = 0, bestOffset = 0, bestSign = 0;
                for (float s = -search; s <= search; s += .5f)
                {
                    float g = Gradient(gray, width, height, p + normal * s, normal);
                    if (Mathf.Abs(g) <= best) continue;
                    float before = Mathf.Abs(Gradient(gray, width, height, p + normal * (s - .5f), normal));
                    float after = Mathf.Abs(Gradient(gray, width, height, p + normal * (s + .5f), normal));
                    float denominator = before - 2 * Mathf.Abs(g) + after;
                    best = Mathf.Abs(g); bestSign = Mathf.Sign(g);
                    bestOffset = s + (denominator < -1e-3f ? Mathf.Clamp(.25f * (before - after) / denominator, -.25f, .25f) : 0);
                }
                if (best < minimumContrast) continue;
                samples.Add(p + normal * bestOffset); signs.Add(bestSign);
            }
            float sum = 0; foreach (float s in signs) sum += s;
            for (int i = samples.Count - 1; i >= 0; i--) if (signs[i] * sum < 0) samples.RemoveAt(i);
            int needed = Mathf.Max(4, steps / 2);
            if (samples.Count < needed || !FitLine(samples, out Vector2 centre, out Vector2 fitted)) continue;
            samples.RemoveAll(q => Mathf.Abs(Cross(q - centre, fitted)) > .75f);
            if (samples.Count < needed || !FitLine(samples, out centre, out fitted)) continue;
            if (Mathf.Abs(Vector2.Dot(fitted, d)) < .966f) continue; // more than 15 degrees off the coarse side
            point[side] = centre; direction[side] = fitted; count++;
        }
        int[,] corner = { { 0, 3 }, { 1, 3 }, { 0, 2 }, { 1, 2 } };
        for (int i = 0; i < 4; i++)
        {
            refined[i] = corners[i];
            if (Intersect(point[corner[i, 0]], direction[corner[i, 0]], point[corner[i, 1]], direction[corner[i, 1]], out Vector2 hit)
                && Vector2.Distance(hit, corners[i]) <= search * 1.5f) refined[i] = hit;
        }
        return count;
    }

    static float Gradient(byte[] gray, int width, int height, Vector2 p, Vector2 normal)
        => Sample(gray, width, height, p + normal) - Sample(gray, width, height, p - normal);

    static float Sample(byte[] gray, int width, int height, Vector2 p)
    {
        float x = Mathf.Clamp(p.x - .5f, 0, width - 1.001f), y = Mathf.Clamp(p.y - .5f, 0, height - 1.001f);
        int x0 = (int)x, y0 = (int)y; float fx = x - x0, fy = y - y0;
        int i = y0 * width + x0;
        return Mathf.Lerp(Mathf.Lerp(gray[i], gray[i + 1], fx), Mathf.Lerp(gray[i + width], gray[i + width + 1], fx), fy);
    }

    static bool FitLine(List<Vector2> points, out Vector2 centre, out Vector2 direction)
    {
        centre = Vector2.zero; direction = Vector2.right;
        foreach (var p in points) centre += p;
        centre /= points.Count;
        float xx = 0, xy = 0, yy = 0;
        foreach (var p in points) { Vector2 q = p - centre; xx += q.x * q.x; xy += q.x * q.y; yy += q.y * q.y; }
        if (xx + yy < 1e-6f) return false;
        float angle = .5f * Mathf.Atan2(2 * xy, xx - yy);
        direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
        return true;
    }
    static float Cross(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;
    static bool Intersect(Vector2 p, Vector2 d, Vector2 q, Vector2 e, out Vector2 hit)
    {
        hit = default;
        float denominator = Cross(d, e);
        if (Mathf.Abs(denominator) < 1e-4f) return false;
        hit = p + d * (Cross(q - p, e) / denominator);
        return true;
    }
}
