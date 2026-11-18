using System.Collections.Generic;
using UnityEngine;

// Collects door observations over a short time window, solves them together and reports a lock
// only once consecutive solutions agree. After the lock it keeps checking and reports a moved door.
public sealed class DoorPoseStabilizer
{
    public enum State { Searching, Sampling, Locked }
    public enum Event { None, Locked, Drifted }

    public bool assumeUpright = true;
    public int minimumObservations = 6, windowSize = 16, stableSolutions = 5, driftSolutions = 8;
    public float maximumAge = 4f, lostAfter = 1f, maximumRmsPixels = 1.5f;
    public float positionToleranceRatio = .04f, minimumPositionTolerance = .0015f, yawToleranceDegrees = 3f;

    public State CurrentState { get; private set; }
    public DoorPoseSolver.Solution Current { get; private set; }
    public DoorPoseSolver.Solution LockedSolution { get; private set; }
    public int ObservationCount => _window.Count;

    readonly List<DoorPoseSolver.Observation> _window = new List<DoorPoseSolver.Observation>();
    readonly List<DoorPoseSolver.Solution> _recent = new List<DoorPoseSolver.Solution>();
    float _lastSeen = float.NegativeInfinity;
    int _driftCount;

    public void Reset()
    {
        _window.Clear(); _recent.Clear(); _driftCount = 0; CurrentState = State.Searching;
    }

    public void MarkMissing(float time)
    {
        if (CurrentState == State.Sampling && time - _lastSeen > lostAfter) Reset();
    }

    public Event Add(DoorPoseSolver.Observation observation, float width, float height)
    {
        _lastSeen = observation.time;
        _window.Add(observation);
        _window.RemoveAll(o => observation.time - o.time > maximumAge);
        while (_window.Count > windowSize) _window.RemoveAt(0);
        if (CurrentState == State.Searching) CurrentState = State.Sampling;

        if (!DoorPoseSolver.SolveSingle(observation, width, height, out var solution)) return Event.None;
        if (assumeUpright)
        {
            var start = _recent.Count > 0 ? _recent[_recent.Count - 1] : solution;
            if (!DoorPoseSolver.SolveUpright(_window, width, height, start, out solution)) return Event.None;
        }
        else if (_window.Count > 1) solution = Average(width, height, solution);
        Current = solution;
        float tolerance = Mathf.Max(minimumPositionTolerance, height * positionToleranceRatio);

        if (CurrentState == State.Locked)
        {
            bool moved = solution.rmsPixels <= maximumRmsPixels && _window.Count >= minimumObservations
                && (Vector3.Distance(solution.position, LockedSolution.position) > tolerance * 2
                    || Mathf.Abs(Mathf.DeltaAngle(solution.yawDegrees, LockedSolution.yawDegrees)) > yawToleranceDegrees * 2);
            _driftCount = moved ? _driftCount + 1 : 0;
            if (_driftCount < driftSolutions) return Event.None;
            // Observations from before the move would drag the new estimate back to the old place.
            _window.RemoveRange(0, Mathf.Max(0, _window.Count - driftSolutions));
            _recent.Clear(); _driftCount = 0; CurrentState = State.Sampling;
            return Event.Drifted;
        }

        if (solution.rmsPixels > maximumRmsPixels) { _recent.Clear(); return Event.None; }
        _recent.Add(solution);
        while (_recent.Count > stableSolutions) _recent.RemoveAt(0);
        if (_window.Count < minimumObservations || _recent.Count < stableSolutions) return Event.None;
        foreach (var other in _recent)
            if (Vector3.Distance(other.position, solution.position) > tolerance
                || Mathf.Abs(Mathf.DeltaAngle(other.yawDegrees, solution.yawDegrees)) > yawToleranceDegrees) return Event.None;
        LockedSolution = solution; CurrentState = State.Locked; _driftCount = 0;
        return Event.Locked;
    }

    DoorPoseSolver.Solution Average(float width, float height, DoorPoseSolver.Solution latest)
    {
        Vector3 position = Vector3.zero, forward = Vector3.zero, up = Vector3.zero;
        float rms = 0; int count = 0;
        foreach (var o in _window)
        {
            if (!DoorPoseSolver.SolveSingle(o, width, height, out var s)) continue;
            position += s.position; forward += s.rotation * Vector3.forward; up += s.rotation * Vector3.up; rms += s.rmsPixels; count++;
        }
        if (count == 0 || forward.sqrMagnitude < 1e-6f) return latest;
        latest.position = position / count;
        latest.rotation = Quaternion.LookRotation(forward, up);
        latest.yawDegrees = latest.rotation.eulerAngles.y;
        latest.rmsPixels = rms / count;
        return latest;
    }
}
