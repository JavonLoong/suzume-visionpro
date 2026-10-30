using UnityEngine;
using UnityEditor;

/// <summary>
/// 自动配置铃芽之旅 FBX 模型与烘焙贴图的导入设置：
/// 1. 开启 32 位索引（UInt32），保证 26 万顶点的花海网格与 18 万顶点的草叶网格完整导入不截断。
/// 2. FlowerPalette.png 使用 Point（最近邻）采样、无压缩、无 Mipmap，确保每朵花精确取到调色板像素。
/// 3. 法线贴图自动设为 NormalMap。
/// </summary>
public class SuzumeAssetPostprocessor : AssetPostprocessor
{
    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith("Assets/Models/") && !assetPath.StartsWith("Assets/Resources/Worlds/")) return;
        var importer = (ModelImporter)assetImporter;
        importer.indexFormat = ModelImporterIndexFormat.UInt32;
        importer.isReadable = true;
        importer.importAnimation = false;
        importer.importCameras = false;
        importer.importLights = false;
    }

    void OnPreprocessTexture()
    {
        if (assetPath.StartsWith("Assets/Resources/ControllerGuide/"))
        {
            var guide = (TextureImporter)assetImporter;
            guide.textureType = TextureImporterType.Default;
            guide.alphaIsTransparency = true;
            guide.textureCompression = TextureImporterCompression.Uncompressed;
            guide.mipmapEnabled = true;
            guide.npotScale = TextureImporterNPOTScale.None;
            guide.wrapMode = TextureWrapMode.Clamp;
            guide.filterMode = FilterMode.Trilinear;
            guide.maxTextureSize = 2048;
            return;
        }
        if (!assetPath.StartsWith("Assets/Textures/") && !assetPath.StartsWith("Assets/Resources/Textures/")) return;
        var importer = (TextureImporter)assetImporter;

        if (assetPath.Contains("FlowerPalette"))
        {
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = false;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.sRGBTexture = true;
            importer.wrapMode = TextureWrapMode.Clamp;
        }
        else if (assetPath.Contains("NightSky"))
        {
            importer.maxTextureSize = 2048;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            importer.sRGBTexture = true;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.filterMode = FilterMode.Bilinear;
        }
        else if (assetPath.Contains("normal"))
        {
            importer.textureType = TextureImporterType.NormalMap;
            importer.maxTextureSize = 2048;
        }
        else if (assetPath.Contains("metallic") || assetPath.Contains("roughness"))
        {
            importer.sRGBTexture = false;
            importer.maxTextureSize = 2048;
        }
        else
        {
            importer.maxTextureSize = 2048;
            importer.sRGBTexture = true;
        }
    }
}
