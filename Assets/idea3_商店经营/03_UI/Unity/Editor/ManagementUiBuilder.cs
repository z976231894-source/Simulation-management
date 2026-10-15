using System.Collections.Generic;
using System.IO;
using OneMoreDiner.ManagementUi;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace OneMoreDiner.ManagementUi.EditorTools
{
    /// <summary>Assembles the 18 designed screens into uGUI prefabs using only the
    /// art already shipped in 03_UI: 12 stretchable panels, 23 icons, 4 scene
    /// backgrounds and Unity's built-in UI sprites for flat fills and discs.</summary>
    public static class ManagementUiBuilder
    {
        public const string Root = "Assets/idea3_商店经营/03_UI";
        public const string LayoutPath = Root + "/Unity/Layout/ui_layout.json";
        public const string PrefabFolder = Root + "/Unity/Prefabs";
        public const string HostPrefabPath = PrefabFolder + "/UI_V2_ScreenHost.prefab";
        public const string PreviewHostName = "UI_V2_PreviewHost";

        public class Result
        {
            public readonly List<string> warnings = new List<string>();
            public readonly List<string> notes = new List<string>();
            public int built;
            public bool ok = true;
        }

        public static UiLayoutFile LoadLayout(Result result)
        {
            var full = Path.GetFullPath(LayoutPath);
            if (!File.Exists(full))
            {
                result.ok = false;
                result.warnings.Add($"layout file missing: {LayoutPath} "
                                    + "(run Unity/Source/export_layout_for_unity.py)");
                return null;
            }
            return JsonUtility.FromJson<UiLayoutFile>(File.ReadAllText(full));
        }

        // ---------------------------------------------------------------- sprites

        public static int FixSpriteImportSettings(UiLayoutFile layout, Result result)
        {
            var changed = 0;
            foreach (var panel in layout.panels)
            {
                changed += EnsureSprite($"{Root}/{panel.path}", panel.border_LBRT, 2048, result);
            }
            foreach (var icon in layout.icons)
            {
                changed += EnsureSprite($"{Root}/{icon.path}", null, 128, result);
            }
            foreach (var background in layout.backgrounds)
            {
                changed += EnsureSprite($"{Root}/{background.path}", null, 2048, result);
            }
            result.notes.Add($"sprite import settings updated on {changed} texture(s)");
            return changed;
        }

        private static int EnsureSprite(string assetPath, int[] border, int maxSize, Result result)
        {
            var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (importer == null)
            {
                result.warnings.Add($"not imported yet: {assetPath}");
                result.ok = false;
                return 0;
            }

            var dirty = false;
            if (importer.textureType != TextureImporterType.Sprite)
            {
                importer.textureType = TextureImporterType.Sprite;
                dirty = true;
            }
            if (importer.spriteImportMode != SpriteImportMode.Single)
            {
                importer.spriteImportMode = SpriteImportMode.Single;
                dirty = true;
            }
            if (!Mathf.Approximately(importer.spritePixelsPerUnit, 100f))
            {
                importer.spritePixelsPerUnit = 100f;
                dirty = true;
            }
            if (border != null && border.Length == 4)
            {
                var want = new Vector4(border[0], border[1], border[2], border[3]);
                if (importer.spriteBorder != want)
                {
                    importer.spriteBorder = want;
                    dirty = true;
                }
            }

            var settings = new TextureImporterSettings();
            importer.ReadTextureSettings(settings);
            if (settings.spriteMeshType != SpriteMeshType.FullRect)
            {
                settings.spriteMeshType = SpriteMeshType.FullRect;
                importer.SetTextureSettings(settings);
                dirty = true;
            }
            if (settings.spriteAlignment != (int)SpriteAlignment.Center)
            {
                settings.spriteAlignment = (int)SpriteAlignment.Center;
                importer.SetTextureSettings(settings);
                dirty = true;
            }

            if (!importer.alphaIsTransparency)
            {
                importer.alphaIsTransparency = true;
                dirty = true;
            }
            if (importer.mipmapEnabled)
            {
                importer.mipmapEnabled = false;
                dirty = true;
            }
            if (importer.filterMode != FilterMode.Bilinear)
            {
                importer.filterMode = FilterMode.Bilinear;
                dirty = true;
            }
            if (importer.wrapMode != TextureWrapMode.Clamp)
            {
                importer.wrapMode = TextureWrapMode.Clamp;
                dirty = true;
            }
            if (importer.textureCompression != TextureImporterCompression.Uncompressed)
            {
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                dirty = true;
            }
            if (importer.maxTextureSize != maxSize)
            {
                importer.maxTextureSize = maxSize;
                dirty = true;
            }

            if (!dirty)
            {
                return 0;
            }
            importer.SaveAndReimport();
            return 1;
        }

        public static ManagementUiAssembler.Assets ResolveAssets(UiLayoutFile layout, Result result)
        {
            var panels = new Dictionary<string, Sprite>();
            foreach (var panel in layout.panels)
            {
                panels[panel.id] = AssetDatabase.LoadAssetAtPath<Sprite>($"{Root}/{panel.path}");
            }
            var icons = new Dictionary<string, Sprite>();
            foreach (var icon in layout.icons)
            {
                icons[icon.id] = AssetDatabase.LoadAssetAtPath<Sprite>($"{Root}/{icon.path}");
            }
            var backgrounds = new Dictionary<string, Sprite>();
            foreach (var background in layout.backgrounds)
            {
                backgrounds[background.id] =
                    AssetDatabase.LoadAssetAtPath<Sprite>($"{Root}/{background.path}");
            }

            var assets = new ManagementUiAssembler.Assets
            {
                panel = id => id != null && panels.TryGetValue(id, out var sprite) ? sprite : null,
                icon = id => id != null && icons.TryGetValue(id, out var sprite) ? sprite : null,
                background = id => id != null && backgrounds.TryGetValue(id, out var sprite)
                    ? sprite : null,
                builtin = name => AssetDatabase.GetBuiltinExtraResource<Sprite>(
                    "UI/Skin/" + name + ".psd"),
            };

            assets.tmpFont = FindTmpFont();
            if (assets.tmpFont != null)
            {
                result.notes.Add($"text font: {assets.tmpFont.name}");
            }
            else
            {
                assets.legacyFont = FindBuiltinFont();
                result.notes.Add(assets.legacyFont != null
                    ? $"text font: built-in {assets.legacyFont.name} (no TMP font asset in the project)"
                    : "text font: none found, text will be skipped");
                if (assets.legacyFont == null)
                {
                    result.ok = false;
                }
            }
            return assets;
        }

        private static TMP_FontAsset FindTmpFont()
        {
            try
            {
                if (TMP_Settings.defaultFontAsset != null)
                {
                    return TMP_Settings.defaultFontAsset;
                }
            }
            catch
            {
                // TMP essentials are not imported in this project
            }
            foreach (var guid in AssetDatabase.FindAssets("t:TMP_FontAsset"))
            {
                var asset = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(
                    AssetDatabase.GUIDToAssetPath(guid));
                if (asset != null)
                {
                    return asset;
                }
            }
            return null;
        }

        private static Font FindBuiltinFont()
        {
            foreach (var name in new[] { "LegacyRuntime.ttf", "Arial.ttf" })
            {
                try
                {
                    var font = Resources.GetBuiltinResource<Font>(name);
                    if (font != null)
                    {
                        return font;
                    }
                }
                catch
                {
                    // try the next built-in name
                }
            }
            return null;
        }

        // ---------------------------------------------------------------- prefabs

        public static Result AssembleAll(bool fixImportSettings = true)
        {
            var result = new Result();
            var layout = LoadLayout(result);
            if (layout == null)
            {
                return result;
            }
            if (fixImportSettings)
            {
                FixSpriteImportSettings(layout, result);
            }
            var assets = ResolveAssets(layout, result);
            EnsureFolder(PrefabFolder);

            foreach (var screen in layout.screens)
            {
                var go = ManagementUiAssembler.Build(screen, assets, null, result.warnings);
                var path = $"{PrefabFolder}/{screen.id}.prefab";
                PrefabUtility.SaveAsPrefabAsset(go, path);
                Object.DestroyImmediate(go);
                result.built += 1;
            }
            BuildHostPrefab();
            result.notes.Add($"{result.built} screen prefabs + {Path.GetFileName(HostPrefabPath)} "
                             + $"written to {PrefabFolder}");
            AssetDatabase.SaveAssets();
            return result;
        }

        private static void BuildHostPrefab()
        {
            var host = new GameObject(Path.GetFileNameWithoutExtension(HostPrefabPath),
                typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster),
                typeof(ManagementUiHost));
            var canvas = host.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = host.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution =
                new Vector2(ManagementUiAssembler.ReferenceWidth,
                            ManagementUiAssembler.ReferenceHeight);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            PrefabUtility.SaveAsPrefabAsset(host, HostPrefabPath);
            Object.DestroyImmediate(host);
        }

        public static void EnsureFolder(string folder)
        {
            if (AssetDatabase.IsValidFolder(folder))
            {
                return;
            }
            var parent = Path.GetDirectoryName(folder)?.Replace('\\', '/');
            var leaf = Path.GetFileName(folder);
            if (!string.IsNullOrEmpty(parent) && !AssetDatabase.IsValidFolder(parent))
            {
                EnsureFolder(parent);
            }
            AssetDatabase.CreateFolder(parent, leaf);
        }

        // ---------------------------------------------------------------- scene

        public static GameObject PreviewInScene(UiScreenSpec screen, UiLayoutFile layout,
            Result result)
        {
            var assets = ResolveAssets(layout, result);
            var host = GameObject.Find(PreviewHostName);
            if (host == null)
            {
                host = new GameObject(PreviewHostName, typeof(Canvas), typeof(CanvasScaler),
                    typeof(GraphicRaycaster));
                var scaler = host.GetComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution =
                    new Vector2(ManagementUiAssembler.ReferenceWidth,
                                ManagementUiAssembler.ReferenceHeight);
                scaler.matchWidthOrHeight = 0.5f;
                Undo.RegisterCreatedObjectUndo(host, "Create UI V2 preview host");
            }
            for (var i = host.transform.childCount - 1; i >= 0; i--)
            {
                Object.DestroyImmediate(host.transform.GetChild(i).gameObject);
            }
            var go = ManagementUiAssembler.Build(screen, assets, host.transform, result.warnings);
            result.built = 1;
            result.notes.Add($"previewing {screen.id} in the open scene");
            return go;
        }
    }
}
