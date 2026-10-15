using System.Collections.Generic;
using OneMoreDiner.ManagementUi;
using UnityEditor;
using UnityEngine;

namespace OneMoreDiner.ManagementUi.EditorTools
{
    /// <summary>Assemble and eyeball the management screens.</summary>
    public class ManagementUiWindow : EditorWindow
    {
        private UiLayoutFile _layout;
        private Vector2 _scroll;
        private bool _showResult = true;
        private string _status = "not run yet";
        private readonly List<string> _notes = new List<string>();
        private readonly List<string> _warnings = new List<string>();

        [MenuItem("Tools/ONE MORE DINER/UI V2/Screens", false, 10)]
        public static void Open()
        {
            var window = GetWindow<ManagementUiWindow>(false, "UI V2", true);
            window.minSize = new Vector2(420f, 320f);
            window.Show();
        }

        private void OnGUI()
        {
            if (_layout == null)
            {
                var load = new ManagementUiBuilder.Result();
                _layout = ManagementUiBuilder.LoadLayout(load);
                _warnings.AddRange(load.warnings);
            }

            EditorGUILayout.Space(4f);
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("1. Fix sprite import settings", GUILayout.Height(24f)))
                {
                    Run(result => ManagementUiBuilder.FixSpriteImportSettings(_layout, result));
                }
                if (GUILayout.Button("2. Assemble prefabs", GUILayout.Height(24f)))
                {
                    var result = ManagementUiBuilder.AssembleAll();
                    Apply(result);
                    GUIUtility.ExitGUI();
                }
                if (GUILayout.Button("Validate", GUILayout.Height(24f)))
                {
                    Run(result =>
                    {
                        ManagementUiBuilder.ResolveAssets(_layout, result);
                        return 0;
                    });
                }
            }
            EditorGUILayout.LabelField("status", _status);
            EditorGUILayout.LabelField("layout", ManagementUiBuilder.LayoutPath);
            EditorGUILayout.LabelField("prefabs", ManagementUiBuilder.PrefabFolder);

            if (_layout == null)
            {
                EditorGUILayout.HelpBox(_warnings.Count > 0 ? string.Join("\n", _warnings)
                    : "no layout loaded", MessageType.Error);
                return;
            }

            _showResult = EditorGUILayout.Foldout(_showResult, "log", true);
            if (_showResult)
            {
                using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
                {
                    foreach (var note in _notes)
                    {
                        EditorGUILayout.LabelField("• " + note, EditorStyles.miniLabel);
                    }
                    foreach (var warning in _warnings)
                    {
                        EditorGUILayout.LabelField("• " + warning, EditorStyles.miniLabel);
                    }
                    if (_notes.Count == 0 && _warnings.Count == 0)
                    {
                        EditorGUILayout.LabelField("clean", EditorStyles.miniLabel);
                    }
                }
            }

            EditorGUILayout.LabelField($"screens ({_layout.screens.Count})", EditorStyles.boldLabel);
            _scroll = EditorGUILayout.BeginScrollView(_scroll);
            foreach (var screen in _layout.screens)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    EditorGUILayout.LabelField(screen.id, GUILayout.Width(210f));
                    EditorGUILayout.LabelField($"{screen.elements.Count} items",
                        EditorStyles.miniLabel, GUILayout.Width(70f));
                    if (GUILayout.Button("Preview in scene", GUILayout.Width(130f)))
                    {
                        var result = new ManagementUiBuilder.Result();
                        var go = ManagementUiBuilder.PreviewInScene(screen, _layout, result);
                        Apply(result);
                        if (go != null)
                        {
                            Selection.activeGameObject = go;
                        }
                        SceneView.lastActiveSceneView?.FrameSelected();
                    }
                    if (GUILayout.Button("Select prefab", GUILayout.Width(110f)))
                    {
                        var path = $"{ManagementUiBuilder.PrefabFolder}/{screen.id}.prefab";
                        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                        if (prefab == null)
                        {
                            _warnings.Add($"no prefab yet: {path}");
                        }
                        else
                        {
                            Selection.activeObject = prefab;
                            EditorGUIUtility.PingObject(prefab);
                        }
                    }
                }
            }
            EditorGUILayout.EndScrollView();
        }

        private void Run(System.Func<ManagementUiBuilder.Result, int> action)
        {
            var result = new ManagementUiBuilder.Result();
            action(result);
            Apply(result);
        }

        private void Apply(ManagementUiBuilder.Result result)
        {
            _notes.Clear();
            _warnings.Clear();
            _notes.AddRange(result.notes);
            _warnings.AddRange(result.warnings);
            _status = $"{result.built} built, {result.notes.Count} note(s), "
                      + $"{result.warnings.Count} warning(s)" + (result.ok ? "" : "  [needs attention]");
        }
    }
}
