using UnityEngine;

// Physical size of the printed door's clear opening. The pose solver needs it in metres, so it is
// selectable at run time instead of being fixed to one print. Presets come from the print files.
public static class DoorPhysicalSize
{
    public struct Preset { public string name; public float width, height; }
    const string Key = "SuzumePortal.DoorSize.V1";
    public const int CustomIndex = 3;
    public static readonly Preset[] Presets =
    {
        new Preset { name = "50mm", width = .0193f, height = .0463f },
        new Preset { name = "60mm", width = .0230f, height = .0558f },
        new Preset { name = "70mm", width = .0270f, height = .0654f },
    };
    [System.Serializable] class Saved { public int index = 1; public float width, height; }
    static Saved _saved;

    static Saved State
    {
        get
        {
            if (_saved != null) return _saved;
            _saved = new Saved();
            string json = PlayerPrefs.GetString(Key, "");
            if (!string.IsNullOrEmpty(json)) JsonUtility.FromJsonOverwrite(json, _saved);
            if (_saved.index < 0 || _saved.index > CustomIndex || (_saved.index == CustomIndex && !Valid(_saved.width, _saved.height))) _saved.index = 1;
            return _saved;
        }
    }
    public static int Index => State.index;
    public static string Name => State.index == CustomIndex ? "custom" : Presets[State.index].name;
    public static float Width => State.index == CustomIndex ? State.width : Presets[State.index].width;
    public static float Height => State.index == CustomIndex ? State.height : Presets[State.index].height;

    public static void Select(int index)
    {
        if (index < 0 || index >= Presets.Length) return;
        State.index = index; Save();
    }
    // Next preset; a custom size is kept in the cycle once one has been set.
    public static void Cycle()
    {
        int count = Valid(State.width, State.height) ? CustomIndex + 1 : Presets.Length;
        State.index = (State.index + 1) % count; Save();
    }
    public static bool SetCustom(float width, float height)
    {
        if (!Valid(width, height)) return false;
        State.width = width; State.height = height; State.index = CustomIndex; Save();
        return true;
    }
    static bool Valid(float width, float height) => width >= .005f && width <= 3f && height >= .01f && height <= 3.5f;
    static void Save() { PlayerPrefs.SetString(Key, JsonUtility.ToJson(State)); PlayerPrefs.Save(); }
}
