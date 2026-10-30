// Unity API stub —— 仅用于本地编译验证，不是真实 Unity 库。
// 提供脚本用到的 UnityEngine 类型的最小签名，让代码能真正编译，
// 从而发现 API 误用 / 逻辑错误（而非仅语法）。
#pragma warning disable CS0108, CS0169, CS0649, CS0067
using System;

namespace UnityEngine
{
    public class Object
    {
        public string name;
        public static T Instantiate<T>(T original) where T : Object => original;
    }

    public class GameObject : Object
    {
        public Transform transform { get; set; } = new Transform();
        public GameObject() { }
        public GameObject(string name) { this.name = name; }
        public static GameObject CreatePrimitive(PrimitiveType type)
        {
            var g = new GameObject();
            g.transform = new Transform();
            g._renderer = new MeshRenderer();
            g._collider = new Collider();
            return g;
        }
        internal MeshRenderer _renderer;
        internal Collider _collider;
        public T GetComponent<T>() where T : class, new()
        {
            if (typeof(T) == typeof(MeshRenderer)) return (T)(object)_renderer;
            if (typeof(T) == typeof(Collider)) return (T)(object)_collider;
            return new T();
        }
        public T[] GetComponentsInChildren<T>(bool includeInactive) where T : class
        {
            return new T[0];
        }
        public T AddComponent<T>() where T : class, new() => new T();
    }

    public class Component : Object
    {
        public GameObject gameObject { get; set; }
        public Transform transform => gameObject != null ? gameObject.transform : null;
        public T GetComponent<T>() where T : class, new() => gameObject != null ? gameObject.GetComponent<T>() : new T();
    }

    public class Behaviour : Component { }
    public class MonoBehaviour : Behaviour { }

    public class Transform : Component
    {
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 localScale = Vector3.one;
        public Vector3 localPosition;
        public Quaternion localRotation;
        public Transform parent;
        public void SetParent(Transform p, bool worldPositionStays) { parent = p; }
    }

    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
        public static Vector3 one => new Vector3(1, 1, 1);
        public static Vector3 zero => new Vector3(0, 0, 0);
        public static Vector3 operator *(Vector3 a, float d) => new Vector3(a.x * d, a.y * d, a.z * d);
    }

    public struct Quaternion
    {
        public static Quaternion identity => new Quaternion();
        public static Quaternion Euler(float x, float y, float z) => new Quaternion();
    }

    public struct Color
    {
        public float r, g, b, a;
        public Color(float r, float g, float b) { this.r = r; this.g = g; this.b = b; a = 1; }
        public Color(float r, float g, float b, float a) { this.r = r; this.g = g; this.b = b; this.a = a; }
        public static Color white => new Color(1, 1, 1, 1);
        public static Color magenta => new Color(1, 0, 1, 1);
        public static Color cyan => new Color(0, 1, 1, 1);
    }

    public enum PrimitiveType { Sphere, Capsule, Cylinder, Cube, Plane, Quad }

    public class Material : Object
    {
        public Material(Shader shader) { }
        public Color color;
        public int renderQueue;
        public void SetFloat(string name, float value) { }
        public void SetInt(string name, int value) { }
        public void EnableKeyword(string keyword) { }
        public void DisableKeyword(string keyword) { }
    }

    public class Shader : Object
    {
        public static Shader Find(string name) => new Shader();
    }

    public class MeshRenderer : Component
    {
        public Material sharedMaterial { get; set; }
        public Material[] sharedMaterials { get; set; }
    }

    public class Collider : Component
    {
        public bool enabled = true;
    }

    public enum LightType { Spot, Directional, Point, Area }

    public class Light : Behaviour
    {
        public LightType type;
        public Color color;
        public float intensity;
    }

    public static class Random
    {
        public static float Range(float min, float max) => min;
        public static int Range(int min, int max) => min;
    }

    public static class Debug
    {
        public static void Log(object message) { }
        public static void LogWarning(object message) { }
    }

    public class HeaderAttribute : Attribute
    {
        public HeaderAttribute(string header) { }
    }

    public class TooltipAttribute : Attribute
    {
        public TooltipAttribute(string tooltip) { }
    }
}

namespace UnityEngine.Rendering
{
    public enum BlendMode { Zero, One, DstColor, SrcColor, OneMinusDstColor, SrcAlpha, OneMinusSrcAlpha, DstAlpha, OneMinusDstAlpha }
}
