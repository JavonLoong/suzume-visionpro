using System;
using System.Collections;
using System.Threading.Tasks;
using Unity.Barracuda;
using UnityEngine;

// Door-corner network (door-keypoint-model-20261118/common.py is the reference implementation).
// Input 1x288x384 grey in [0,1]; output 72x96x12: four corner heatmaps and four (dx, dy) cell offsets.
// A frame is searched whole first, then re-read from a crop around the door so the corners are
// measured at close to the camera's own resolution.
public sealed class BarracudaDoorDetector : IDoorKeypointDetector, IDoorGuidedDetector, IDisposable
{
    public const int InputWidth = 384, InputHeight = 288, Stride = 4;
    const int OutputWidth = InputWidth / Stride, OutputHeight = InputHeight / Stride, Channels = 12;
    const float Fill = .45f; // door's larger extent / crop height in the close-up passes
    public float minimumConfidence = .3f, trackSeconds = 1f;

    readonly IWorker _worker;
    readonly float[] _input = new float[InputWidth * InputHeight];
    readonly Vector2[] _previous = new Vector2[4];
    float _previousTime = float.NegativeInfinity;
    byte[][] _levels = new byte[8][];
    readonly int[] _levelWidth = new int[8], _levelHeight = new int[8];
    int _levelCount;

    public int LastPasses { get; private set; }
    public double MaximumSliceMilliseconds { get; private set; }
    public bool IsRunning { get; private set; }
    public double SamplingMilliseconds { get; private set; }
    public string SlowestStage { get; private set; }
    int _generation;
    public Rect LastSearchRegion { get; private set; }

    public static BarracudaDoorDetector Create(WorkerFactory.Type? type = null)
    {
        var asset = Resources.Load<NNModel>("DoorNet/door_net");
        if (asset == null) { Debug.LogWarning("[DoorDetector] Resources/DoorNet/door_net is missing"); return null; }
        // Android Vulkan results must match recorded-frame CPU results before enabling GPU inference.
        var chosen = type ?? (Application.platform == RuntimePlatform.Android ? WorkerFactory.Type.CSharpBurst
            : (SystemInfo.supportsComputeShaders ? WorkerFactory.Type.ComputePrecompiled : WorkerFactory.Type.CSharpBurst));
        try { return new BarracudaDoorDetector(ModelLoader.Load(asset), chosen); }
        catch (Exception e) { Debug.LogWarning("[DoorDetector] cannot start: " + e.Message); return null; }
    }

    BarracudaDoorDetector(Model model, WorkerFactory.Type type)
    {
        _worker = WorkerFactory.CreateWorker(type, model);
        Debug.Log("[DoorDetector] worker " + type);
    }

    public void Reset() { _previousTime = float.NegativeInfinity; _generation++; }
    public void Dispose() { _worker?.Dispose(); }

    // 2x3 map from network-input coordinates to frame coordinates; scale = frame pixels per input pixel.
    struct Map
    {
        public float scale, x, y;
        public Vector2 ToFrame(Vector2 p) => new Vector2(p.x * scale + x, p.y * scale + y);
        public static Map Around(Vector2 centre, float scale) => new Map
        { scale = scale, x = centre.x - scale * InputWidth * .5f, y = centre.y - scale * InputHeight * .5f };
        public static Map Whole(int width, int height) =>
            Around(new Vector2(width * .5f, height * .5f), Mathf.Max(width / (float)InputWidth, height / (float)InputHeight));
        public static Map Crop(Vector2[] p)
        {
            Vector2 lo = p[0], hi = p[0];
            for (int i = 1; i < 4; i++) { lo = Vector2.Min(lo, p[i]); hi = Vector2.Max(hi, p[i]); }
            float size = Mathf.Max(Mathf.Max(hi.x - lo.x, hi.y - lo.y), 4f);
            return Around((lo + hi) * .5f, size / (Fill * InputHeight));
        }
    }

    public bool TryDetect(DoorCameraFrame frame, Vector2[] pixels, float[] confidence)
    {
        _levels[0] = frame.gray; _levelWidth[0] = frame.width; _levelHeight[0] = frame.height; _levelCount = 1;
        LastPasses = 0;
        bool tracking = frame.time - _previousTime >= 0 && frame.time - _previousTime < trackSeconds;
        Map map = tracking ? Map.Crop(_previous) : Map.Whole(frame.width, frame.height);
        // New search: whole frame, close-up, close-up re-centred. Tracking: the first close-up comes from the last result.
        int runs = tracking ? 2 : 3;
        for (int n = 0; n < runs; n++)
        {
            if (!Run(map, pixels, confidence)) { Reset(); return false; }
            if (n < runs - 1) map = Map.Crop(pixels);
        }
        Array.Copy(pixels, _previous, 4); _previousTime = frame.time;
        return true;
    }

    public bool TryDetectGuided(DoorCameraFrame frame, Rect searchRegion, Vector2[] pixels, float[] confidence)
    {
        LastPasses = 0;
        if (searchRegion.width < 2 || searchRegion.height < 2) return false;
        _levels[0] = frame.gray; _levelWidth[0] = frame.width; _levelHeight[0] = frame.height; _levelCount = 1;
        LastSearchRegion = searchRegion;
        Vector2 previousCentre = (_previous[0] + _previous[1] + _previous[2] + _previous[3]) * .25f;
        bool tracking = frame.time >= _previousTime && frame.time - _previousTime < trackSeconds && searchRegion.Contains(previousCentre);
        Map seed = Map.Around(searchRegion.center, Mathf.Max(searchRegion.width / InputWidth, searchRegion.height / InputHeight));
        Map map = tracking ? Map.Crop(_previous) : seed;
        if (!Run(map, pixels, confidence))
        {
            Reset();
            if (!tracking || !Run(seed, pixels, confidence)) return false;
        }
        Vector2 centre = (pixels[0] + pixels[1] + pixels[2] + pixels[3]) * .25f;
        if (!searchRegion.Contains(centre)) { Reset(); return false; }
        // Re-read this local candidate at the camera's resolution; never fall back to the whole frame.
        if (!Run(Map.Crop(pixels), pixels, confidence)) { Reset(); return false; }
        centre = (pixels[0] + pixels[1] + pixels[2] + pixels[3]) * .25f;
        if (!searchRegion.Contains(centre)) { Reset(); return false; }
        Array.Copy(pixels, _previous, 4); _previousTime = frame.time;
        return true;
    }

    // One in-flight inference. Yield between layer batches and wait for worker jobs without
    // blocking the XR render loop. Reset invalidates results but lets scheduled jobs drain safely.
    public IEnumerator DetectGuidedAsync(DoorCameraFrame frame, Rect region, Vector2[] pixels,
        float[] confidence, Action<bool> completed, Func<bool> valid = null)
    {
        if (IsRunning) throw new InvalidOperationException("Detector already running");
        IsRunning = true;
        int generation = _generation;
        bool Current() => generation == _generation && (valid == null || valid());
        try
        {
            LastPasses = 0; MaximumSliceMilliseconds = 0; SamplingMilliseconds = 0; SlowestStage = "none";
            if (region.width < 2 || region.height < 2 || !Current()) { completed(false); yield break; }
            _levels[0] = frame.gray; _levelWidth[0] = frame.width; _levelHeight[0] = frame.height; _levelCount = 1;
            LastSearchRegion = region;
            Vector2 previousCentre = (_previous[0] + _previous[1] + _previous[2] + _previous[3]) * .25f;
            bool tracking = frame.time >= _previousTime && frame.time - _previousTime < trackSeconds && region.Contains(previousCentre);
            Map seed = Map.Around(region.center, Mathf.Max(region.width / InputWidth, region.height / InputHeight));
            bool found = false;
            yield return RunAsync(tracking ? Map.Crop(_previous) : seed, pixels, confidence, x => found = x);
            if (!Current()) { completed(false); yield break; }
            if (!found && tracking)
            {
                _previousTime = float.NegativeInfinity;
                yield return RunAsync(seed, pixels, confidence, x => found = x);
                if (!Current()) { completed(false); yield break; }
            }
            if (!found || !region.Contains((pixels[0]+pixels[1]+pixels[2]+pixels[3])*.25f))
            { _previousTime = float.NegativeInfinity; completed(false); yield break; }
            yield return RunAsync(Map.Crop(pixels), pixels, confidence, x => found = x);
            if (!Current()) { completed(false); yield break; }
            found &= region.Contains((pixels[0]+pixels[1]+pixels[2]+pixels[3])*.25f);
            if (found) { Array.Copy(pixels, _previous, 4); _previousTime = frame.time; }
            else _previousTime = float.NegativeInfinity;
            completed(found);
        }
        finally { IsRunning = false; }
    }

    void RecordSlice(System.Diagnostics.Stopwatch timer, string stage)
    {
        if (timer.Elapsed.TotalMilliseconds <= MaximumSliceMilliseconds) return;
        MaximumSliceMilliseconds = timer.Elapsed.TotalMilliseconds; SlowestStage = stage;
    }

    IEnumerator RunAsync(Map map, Vector2[] pixels, float[] confidence, Action<bool> completed)
    {
        // Sampling and box-filter pyramids only touch this detector's owned arrays and numeric
        // values; no Unity objects or worker calls cross threads. The frame is held by the caller.
        var prepare = Task.Run(() => {
            var t = System.Diagnostics.Stopwatch.StartNew(); Sample(map); return t.Elapsed.TotalMilliseconds;
        });
        while (!prepare.IsCompleted) yield return null;
        if (prepare.IsFaulted) throw prepare.Exception;
        SamplingMilliseconds += prepare.Result; LastPasses++;
        var slice = System.Diagnostics.Stopwatch.StartNew();
        using (var input = new Tensor(1, InputHeight, InputWidth, 1, _input))
        {
            RecordSlice(slice, "input");
            var schedule = _worker.StartManualSchedule(input);
            bool more = true; int layer = 0;
            while (more)
            {
                slice.Restart(); int first = layer;
                do { more = schedule.MoveNext(); layer++; }
                while (more && slice.Elapsed.TotalMilliseconds < 1.5);
                Unity.Jobs.JobHandle.ScheduleBatchedJobs();
                RecordSlice(slice, "schedule " + first + "-" + layer);
                if (more) yield return null;
            }
            slice.Restart(); var output = _worker.PeekOutput(); RecordSlice(slice, "peek");
            while (true)
            {
                slice.Restart(); bool ready = output.PrepareCacheForAccess(blocking:false); RecordSlice(slice, "readback");
                if (ready) break;
                yield return null;
            }
            slice.Restart();
            bool found = Decode(map, output.ToReadOnlyArray(), pixels, confidence);
            RecordSlice(slice, "decode");
            completed(found);
        }
    }

    bool Run(Map map, Vector2[] pixels, float[] confidence)
    {
        Sample(map);
        LastPasses++;
        using (var input = new Tensor(1, InputHeight, InputWidth, 1, _input))
        {
            _worker.Execute(input);
            var output = _worker.PeekOutput();
            float[] maps = output.ToReadOnlyArray(); // NHWC
            return Decode(map, maps, pixels, confidence);
        }
    }

    bool Decode(Map map, float[] maps, Vector2[] pixels, float[] confidence)
    {
            bool found = true;
            for (int k = 0; k < 4; k++)
            {
                int best = 0; float peak = float.NegativeInfinity;
                for (int cell = 0, at = k; cell < OutputWidth * OutputHeight; cell++, at += Channels)
                    if (maps[at] > peak) { peak = maps[at]; best = cell; }
                int x = best % OutputWidth, y = best / OutputWidth, offset = best * Channels + 4 + 2 * k;
                confidence[k] = peak;
                pixels[k] = map.ToFrame(new Vector2((x + .5f + maps[offset]) * Stride, (y + .5f + maps[offset + 1]) * Stride));
                found &= peak >= minimumConfidence;
            }
            return found;
    }

    // Bilinear read from the half-resolution level that matches the scale (2x2 means, so large reductions do not alias).
    void Sample(Map map)
    {
        int level = Mathf.Clamp(Mathf.FloorToInt(Mathf.Log(Mathf.Max(map.scale, 1e-6f), 2f) + 1e-6f), 0, _levels.Length - 1);
        level = EnsureLevel(level);
        byte[] source = _levels[level]; int width = _levelWidth[level], height = _levelHeight[level];
        float f = 1f / (1 << level), step = map.scale * f;
        float x0 = (map.x + map.scale * .5f) * f - .5f, y0 = (map.y + map.scale * .5f) * f - .5f;
        const float normalise = 1f / 255f;
        for (int j = 0; j < InputHeight; j++)
        {
            float sy = Mathf.Clamp(y0 + j * step, 0, height - 1);
            int ya = (int)sy, yb = Math.Min(ya + 1, height - 1); float ty = sy - ya;
            int rowA = ya * width, rowB = yb * width, target = j * InputWidth;
            for (int i = 0; i < InputWidth; i++)
            {
                float sx = Mathf.Clamp(x0 + i * step, 0, width - 1);
                int xa = (int)sx, xb = Math.Min(xa + 1, width - 1); float tx = sx - xa;
                float top = source[rowA + xa] + (source[rowA + xb] - source[rowA + xa]) * tx;
                float bottom = source[rowB + xa] + (source[rowB + xb] - source[rowB + xa]) * tx;
                _input[target + i] = (top + (bottom - top) * ty) * normalise;
            }
        }
    }

    int EnsureLevel(int wanted)
    {
        while (_levelCount <= wanted)
        {
            int from = _levelCount - 1, sw = _levelWidth[from], w = sw / 2, h = _levelHeight[from] / 2;
            if (w < 1 || h < 1) return from;
            byte[] source = _levels[from], target = _levels[_levelCount];
            if (target == null || target.Length != w * h) target = _levels[_levelCount] = new byte[w * h];
            for (int y = 0; y < h; y++)
            {
                int a = 2 * y * sw, b = a + sw, o = y * w;
                for (int x = 0; x < w; x++, a += 2, b += 2)
                    target[o + x] = (byte)((source[a] + source[a + 1] + source[b] + source[b + 1] + 2) >> 2);
            }
            _levelWidth[_levelCount] = w; _levelHeight[_levelCount] = h; _levelCount++;
        }
        return wanted;
    }
}
