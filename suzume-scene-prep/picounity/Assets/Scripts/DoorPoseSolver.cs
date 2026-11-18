using System;
using System.Collections.Generic;
using UnityEngine;

// Door pose from the four inner corners of the opening and the door's known physical size.
// Corner order everywhere: bottom-left, bottom-right, top-left, top-right as seen by the viewer.
// Pixels use a top-left origin with v pointing down. The returned pose matches DoorCalibrationMath:
// position = bottom centre of the opening, rotation = LookRotation(towards viewer, up).
public static class DoorPoseSolver
{
    public struct Observation
    {
        public Matrix4x4 cameraToWorld; // Unity camera axes: x right, y up, z forward
        public float fx, fy, cx, cy, time;
        public Vector2 bottomLeft, bottomRight, topLeft, topRight;
        public Vector2 Pixel(int i) => i == 0 ? bottomLeft : i == 1 ? bottomRight : i == 2 ? topLeft : topRight;
        public void SetPixels(Vector2[] p) { bottomLeft = p[0]; bottomRight = p[1]; topLeft = p[2]; topRight = p[3]; }
    }
    public struct Solution
    {
        public Vector3 position;
        public Quaternion rotation;
        public float yawDegrees, rmsPixels;
    }

    const double HuberPixels = 2.0;

    // Full six-degree-of-freedom pose from one image.
    public static bool SolveSingle(Observation o, float width, float height, out Solution solution)
    {
        solution = default;
        if (width <= 0 || height <= 0 || o.fx <= 0 || o.fy <= 0) return false;
        double[] objX = { -width * .5, width * .5, -width * .5, width * .5 }, objY = { 0, 0, height, height };
        var a = new double[8, 9];
        for (int i = 0; i < 4; i++)
        {
            Vector2 p = o.Pixel(i);
            double x = (p.x - o.cx) / o.fx, y = (p.y - o.cy) / o.fy, X = objX[i], Y = objY[i];
            int r = i * 2;
            a[r, 0] = X; a[r, 1] = Y; a[r, 2] = 1; a[r, 6] = -x * X; a[r, 7] = -x * Y; a[r, 8] = x;
            a[r + 1, 3] = X; a[r + 1, 4] = Y; a[r + 1, 5] = 1; a[r + 1, 6] = -y * X; a[r + 1, 7] = -y * Y; a[r + 1, 8] = y;
        }
        var h = new double[8];
        if (!SolveLinear(a, 8, h)) return false;
        double[] c1 = { h[0], h[3], h[6] }, c2 = { h[1], h[4], h[7] }, t = { h[2], h[5], 1 };
        double scale = 2.0 / (Norm(c1) + Norm(c2));
        if (double.IsNaN(scale) || double.IsInfinity(scale)) return false;
        for (int i = 0; i < 3; i++) t[i] *= scale;
        double[] r1 = Normalized(c1);
        double d = Dot(c2, r1);
        double[] r2 = Normalized(new[] { c2[0] - d * r1[0], c2[1] - d * r1[1], c2[2] - d * r1[2] });
        double[] r3 = Cross(r1, r2);
        double[] rotation = { r1[0], r2[0], r3[0], r1[1], r2[1], r3[1], r1[2], r2[2], r3[2] }; // row-major

        double best = Refine(o, objX, objY, ref rotation, ref t);
        // A small planar target has a second, mirrored minimum; test it rather than trust the first.
        double[] view = Normalized(new[] { -t[0], -t[1], -t[2] });
        double[] normal = { rotation[2], rotation[5], rotation[8] };
        double[] axis = Cross(normal, view);
        double sin = Norm(axis), cos = Dot(normal, view);
        if (sin > 1e-4)
        {
            double angle = 2 * Math.Atan2(sin, cos);
            double[] flipped = Multiply(Rodrigues(new[] { axis[0] / sin * angle, axis[1] / sin * angle, axis[2] / sin * angle }), rotation);
            double[] flippedT = (double[])t.Clone();
            double other = Refine(o, objX, objY, ref flipped, ref flippedT);
            bool ambiguous = other < best * 1.5 + 0.02 && best < other * 1.5 + 0.02;
            if (other < best && !ambiguous || ambiguous && UpAlignment(o, flipped) > UpAlignment(o, rotation))
            { rotation = flipped; t = flippedT; best = other; }
        }
        if (t[2] <= 0) return false;
        Vector3 toViewer = o.cameraToWorld.MultiplyVector(new Vector3((float)rotation[2], -(float)rotation[5], (float)rotation[8]));
        Vector3 up = o.cameraToWorld.MultiplyVector(new Vector3((float)rotation[1], -(float)rotation[4], (float)rotation[7]));
        solution.position = o.cameraToWorld.MultiplyPoint3x4(new Vector3((float)t[0], -(float)t[1], (float)t[2]));
        solution.rotation = Quaternion.LookRotation(toViewer, up);
        solution.yawDegrees = solution.rotation.eulerAngles.y;
        solution.rmsPixels = (float)Math.Sqrt(best / 8);
        return !float.IsNaN(solution.position.x + solution.position.y + solution.position.z);
    }

    // Position and yaw of a door that stands upright (its vertical is world up), from any number of views.
    // Views taken from different head positions triangulate the depth that one small image cannot give.
    public static bool SolveUpright(IList<Observation> observations, float width, float height, Solution initial, out Solution solution)
    {
        solution = default;
        int n = observations.Count;
        if (n == 0) return false;
        var worldToCamera = new Matrix4x4[n];
        Vector3 cameraCentre = Vector3.zero;
        for (int i = 0; i < n; i++)
        {
            worldToCamera[i] = observations[i].cameraToWorld.inverse;
            cameraCentre += (Vector3)observations[i].cameraToWorld.GetColumn(3) / n;
        }
        Func<double[], bool, double[]> residual = (x, robust) =>
        {
            var r = new double[n * 8];
            double c = Math.Cos(x[3]), s = Math.Sin(x[3]);
            for (int k = 0; k < 4; k++)
            {
                // Viewer's left is the portal's +X.
                double side = (k % 2 == 0 ? 1 : -1) * width * .5;
                var world = new Vector3((float)(x[0] + side * c), (float)(x[1] + (k >= 2 ? height : 0)), (float)(x[2] - side * s));
                for (int i = 0; i < n; i++)
                {
                    Observation o = observations[i];
                    Vector3 p = worldToCamera[i].MultiplyPoint3x4(world);
                    double z = Math.Max(p.z, 1e-4);
                    Vector2 pixel = o.Pixel(k);
                    double du = o.fx * p.x / z + o.cx - pixel.x, dv = o.cy - o.fy * p.y / z - pixel.y;
                    r[(i * 4 + k) * 2] = robust ? Huber(du) : du;
                    r[(i * 4 + k) * 2 + 1] = robust ? Huber(dv) : dv;
                }
            }
            return r;
        };
        double yaw = initial.yawDegrees * Math.PI / 180;
        double[] first = { initial.position.x, initial.position.y, initial.position.z, yaw };
        double cost = Minimize(x => residual(x, true), first);
        // The same mirrored minimum appears as a yaw reflected about the viewing direction.
        Vector3 toCamera = cameraCentre - new Vector3((float)first[0], (float)first[1], (float)first[2]);
        double viewYaw = Math.Atan2(toCamera.x, toCamera.z);
        double[] second = { first[0], first[1], first[2], 2 * viewYaw - first[3] };
        double secondCost = Minimize(x => residual(x, true), second);
        double[] best = secondCost < cost ? second : first;
        double[] raw = residual(best, false);
        double sum = 0;
        foreach (double v in raw) sum += v * v;
        solution.position = new Vector3((float)best[0], (float)best[1], (float)best[2]);
        solution.yawDegrees = Mathf.Repeat((float)(best[3] * 180 / Math.PI), 360f);
        solution.rotation = Quaternion.Euler(0, solution.yawDegrees, 0);
        solution.rmsPixels = (float)Math.Sqrt(sum / raw.Length);
        Vector3 p0 = solution.position;
        return !float.IsNaN(p0.x + p0.y + p0.z + solution.rmsPixels) && Vector3.Dot(solution.rotation * Vector3.forward, cameraCentre - p0) > 0;
    }

    static double Huber(double r)
    {
        double q = r / HuberPixels;
        return Math.Sign(r) * HuberPixels * Math.Sqrt(2 * (Math.Sqrt(1 + q * q) - 1));
    }
    static double UpAlignment(Observation o, double[] rotation)
        => o.cameraToWorld.MultiplyVector(new Vector3((float)rotation[1], -(float)rotation[4], (float)rotation[7])).normalized.y;

    static double Refine(Observation o, double[] objX, double[] objY, ref double[] rotation, ref double[] t)
    {
        double[] r0 = rotation;
        Func<double[], double[]> residual = x =>
        {
            double[] r = Multiply(Rodrigues(x), r0);
            var e = new double[8];
            for (int i = 0; i < 4; i++)
            {
                double cx = r[0] * objX[i] + r[1] * objY[i] + x[3], cy = r[3] * objX[i] + r[4] * objY[i] + x[4];
                double cz = Math.Max(r[6] * objX[i] + r[7] * objY[i] + x[5], 1e-6);
                Vector2 p = o.Pixel(i);
                e[i * 2] = o.fx * cx / cz + o.cx - p.x;
                e[i * 2 + 1] = o.fy * cy / cz + o.cy - p.y;
            }
            return e;
        };
        double[] parameters = { 0, 0, 0, t[0], t[1], t[2] };
        double cost = Minimize(residual, parameters);
        rotation = Multiply(Rodrigues(parameters), r0);
        t = new[] { parameters[3], parameters[4], parameters[5] };
        return cost;
    }

    // Levenberg-Marquardt with a numeric Jacobian; x is updated in place, the return value is the squared error.
    static double Minimize(Func<double[], double[]> residual, double[] x, int iterations = 40)
    {
        int n = x.Length;
        double[] r = residual(x);
        double cost = SquaredNorm(r), damping = 1e-3;
        int m = r.Length;
        var jacobian = new double[m, n];
        for (int iteration = 0; iteration < iterations; iteration++)
        {
            for (int j = 0; j < n; j++)
            {
                double keep = x[j], step = 1e-6 * Math.Max(1, Math.Abs(keep));
                x[j] = keep + step; double[] plus = residual(x);
                x[j] = keep - step; double[] minus = residual(x);
                x[j] = keep;
                for (int i = 0; i < m; i++) jacobian[i, j] = (plus[i] - minus[i]) / (2 * step);
            }
            var normal = new double[n, n + 1];
            bool improved = false;
            for (int attempt = 0; attempt < 8 && !improved; attempt++)
            {
                for (int a = 0; a < n; a++)
                {
                    for (int b = 0; b < n; b++)
                    {
                        double sum = 0;
                        for (int i = 0; i < m; i++) sum += jacobian[i, a] * jacobian[i, b];
                        normal[a, b] = sum;
                    }
                    normal[a, a] *= 1 + damping; normal[a, a] += 1e-12;
                    double g = 0;
                    for (int i = 0; i < m; i++) g += jacobian[i, a] * r[i];
                    normal[a, n] = -g;
                }
                var delta = new double[n];
                if (!SolveLinear(normal, n, delta)) { damping *= 10; continue; }
                var candidate = new double[n];
                for (int j = 0; j < n; j++) candidate[j] = x[j] + delta[j];
                double[] next = residual(candidate);
                double nextCost = SquaredNorm(next);
                if (nextCost < cost)
                {
                    improved = true;
                    bool converged = cost - nextCost < 1e-12 * (1 + cost);
                    Array.Copy(candidate, x, n); r = next; cost = nextCost; damping = Math.Max(damping * .3, 1e-9);
                    if (converged) return cost;
                }
                else damping *= 10;
            }
            if (!improved) break;
        }
        return cost;
    }

    // Gaussian elimination with partial pivoting on an augmented n x (n+1) matrix (modified in place).
    static bool SolveLinear(double[,] a, int n, double[] x)
    {
        for (int column = 0; column < n; column++)
        {
            int pivot = column;
            for (int row = column + 1; row < n; row++) if (Math.Abs(a[row, column]) > Math.Abs(a[pivot, column])) pivot = row;
            if (Math.Abs(a[pivot, column]) < 1e-14) return false;
            if (pivot != column) for (int k = column; k <= n; k++) { double swap = a[column, k]; a[column, k] = a[pivot, k]; a[pivot, k] = swap; }
            for (int row = column + 1; row < n; row++)
            {
                double f = a[row, column] / a[column, column];
                if (f == 0) continue;
                for (int k = column; k <= n; k++) a[row, k] -= f * a[column, k];
            }
        }
        for (int row = n - 1; row >= 0; row--)
        {
            double sum = a[row, n];
            for (int k = row + 1; k < n; k++) sum -= a[row, k] * x[k];
            x[row] = sum / a[row, row];
        }
        return true;
    }
    static double[] Rodrigues(double[] w)
    {
        double angle = Math.Sqrt(w[0] * w[0] + w[1] * w[1] + w[2] * w[2]);
        if (angle < 1e-12) return new double[] { 1, 0, 0, 0, 1, 0, 0, 0, 1 };
        double x = w[0] / angle, y = w[1] / angle, z = w[2] / angle, c = Math.Cos(angle), s = Math.Sin(angle), k = 1 - c;
        return new[] { c + x * x * k, x * y * k - z * s, x * z * k + y * s, y * x * k + z * s, c + y * y * k, y * z * k - x * s, z * x * k - y * s, z * y * k + x * s, c + z * z * k };
    }
    static double[] Multiply(double[] a, double[] b)
    {
        var c = new double[9];
        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) c[i * 3 + j] = a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j];
        return c;
    }
    static double SquaredNorm(double[] v) { double s = 0; foreach (double e in v) s += e * e; return s; }
    static double Dot(double[] a, double[] b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    static double Norm(double[] a) => Math.Sqrt(Dot(a, a));
    static double[] Normalized(double[] a) { double n = Norm(a); return new[] { a[0] / n, a[1] / n, a[2] / n }; }
    static double[] Cross(double[] a, double[] b) => new[] { a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0] };
}
