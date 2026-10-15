using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace OneMoreDiner.ManagementUi
{
    /// <summary>Builds one screen as a uGUI hierarchy from the exported layout.
    /// Every draw item uses an asset that already exists in the package: one of
    /// the 12 panels, one of the 23 icons, a background, or a Unity built-in UI
    /// sprite. Nothing is generated.</summary>
    public static class ManagementUiAssembler
    {
        public const float ReferenceWidth = 1920f;
        public const float ReferenceHeight = 1080f;

        /// <summary>Where sprites and the text font come from. The editor fills
        /// these with AssetDatabase lookups; a runtime caller can pass anything.</summary>
        public class Assets
        {
            public Func<string, Sprite> panel = _ => null;
            public Func<string, Sprite> icon = _ => null;
            public Func<string, Sprite> background = _ => null;
            public Func<string, Sprite> builtin = _ => null;
            public TMP_FontAsset tmpFont;
            public Font legacyFont;
        }

        public static GameObject Build(UiScreenSpec screen, Assets assets, Transform parent,
            List<string> warnings = null)
        {
            warnings = warnings ?? new List<string>();
            var root = new GameObject(screen.id, typeof(RectTransform));
            var rootRect = root.GetComponent<RectTransform>();
            if (parent != null)
            {
                rootRect.SetParent(parent, false);
            }
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.pivot = new Vector2(0.5f, 0.5f);
            rootRect.anchoredPosition = Vector2.zero;
            rootRect.sizeDelta = new Vector2(screen.width, screen.height);

            if (!string.IsNullOrEmpty(screen.background))
            {
                var sprite = assets.background(screen.background);
                if (sprite == null)
                {
                    warnings.Add($"{screen.id}: background '{screen.background}' not found");
                }
                else
                {
                    var go = new GameObject("background", typeof(RectTransform), typeof(Image));
                    var rect = go.GetComponent<RectTransform>();
                    rect.SetParent(rootRect, false);
                    rect.anchorMin = Vector2.zero;
                    rect.anchorMax = Vector2.one;
                    rect.pivot = new Vector2(0.5f, 0.5f);
                    rect.anchoredPosition = Vector2.zero;
                    rect.sizeDelta = Vector2.zero;
                    var image = go.GetComponent<Image>();
                    image.sprite = sprite;
                    image.type = Image.Type.Simple;
                    image.preserveAspect = false;
                    image.raycastTarget = false;
                }
            }

            var items = new List<UiItemSpec>(screen.elements);
            items.Sort((a, b) => a.level.CompareTo(b.level));
            foreach (var item in items)
            {
                BuildItem(rootRect, item, assets, warnings);
            }
            return root;
        }

        private static void BuildItem(RectTransform parent, UiItemSpec item, Assets assets,
            List<string> warnings)
        {
            if (item.kind == "text")
            {
                BuildText(parent, item, assets, warnings);
                return;
            }
            if (item.draw == "skip")
            {
                warnings.Add($"{parent.name}/{item.id}: {item.kind} cannot be drawn from the "
                             + "shipped assets" + (string.IsNullOrEmpty(item.approx) ? "" : $" ({item.approx})"));
                return;
            }

            var go = new GameObject(item.id, typeof(RectTransform));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = new Vector2(item.X, -item.Y);
            rect.sizeDelta = new Vector2(Mathf.Max(1f, item.W), Mathf.Max(1f, item.H));

            Sprite sprite = null;
            var sliced = false;
            switch (item.draw)
            {
                case "panel":
                    sprite = assets.panel(item.panel);
                    sliced = sprite != null && sprite.border != Vector4.zero;
                    if (sprite == null)
                    {
                        warnings.Add($"{parent.name}/{item.id}: panel '{item.panel}' not found");
                    }
                    break;
                case "icon":
                    sprite = assets.icon(item.icon);
                    if (sprite == null)
                    {
                        warnings.Add($"{parent.name}/{item.id}: icon '{item.icon}' not found");
                    }
                    break;
                default:
                    sprite = assets.builtin(item.builtin);
                    break;
            }

            var image = go.AddComponent<Image>();
            image.sprite = sprite;
            image.type = sliced ? Image.Type.Sliced : Image.Type.Simple;
            image.preserveAspect = false;
            image.raycastTarget = false;
            image.color = UiColor.Parse(item.tint, Mathf.Clamp01(item.alpha));
            if (sliced && item.border_scale > 0.01f
                && Mathf.Abs(item.border_scale - 1f) > 0.01f)
            {
                // scales the nine-slice border so the piece draws the corner radius
                // the design asked for, without needing a new piece per radius
                image.pixelsPerUnitMultiplier = item.border_scale;
            }

            if (item.shadow != null)
            {
                var shadow = go.AddComponent<Shadow>();
                shadow.effectColor = UiColor.Parse(item.shadow.color, Mathf.Clamp01(item.shadow.alpha));
                shadow.effectDistance = new Vector2(item.shadow.dx, -item.shadow.dy);
                shadow.useGraphicAlpha = true;
            }
        }

        private static void BuildText(RectTransform parent, UiItemSpec item, Assets assets,
            List<string> warnings)
        {
            var go = new GameObject(item.id, typeof(RectTransform));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = rect.anchorMax = new Vector2(0f, 1f);

            var size = Mathf.Max(1f, item.size_px);
            var bold = item.weight >= 600f;
            var ascent = AscentEm(assets, size) * size;
            var top = item.baseline_px - ascent;
            var width = UiColor.EstimateWidth(item.text, size) * 2f + 100f;
            var height = Mathf.Max(size * 1.5f, 8f);

            var pivotX = 0f;
            switch (item.anchor)
            {
                case "middle":
                    pivotX = 0.5f;
                    break;
                case "end":
                    pivotX = 1f;
                    break;
            }
            rect.pivot = new Vector2(pivotX, 1f);
            rect.anchoredPosition = new Vector2(item.anchor_x, -top);
            rect.sizeDelta = new Vector2(width, height);

            var color = UiColor.Parse(item.color);
            if (assets.tmpFont != null)
            {
                var text = go.AddComponent<TextMeshProUGUI>();
                text.font = assets.tmpFont;
                text.fontSize = size;
                text.fontStyle = bold ? FontStyles.Bold : FontStyles.Normal;
                text.color = color;
                text.text = item.text;
                text.alignment = item.anchor == "middle" ? TextAlignmentOptions.Top
                    : item.anchor == "end" ? TextAlignmentOptions.TopRight : TextAlignmentOptions.TopLeft;
                text.overflowMode = TextOverflowModes.Overflow;
                text.raycastTarget = false;
                if (Mathf.Abs(item.letter_spacing) > 0.01f)
                {
                    // design tracking is in px at the design size; TMP expects 1/100 em
                    text.characterSpacing = item.letter_spacing / size * 100f;
                }
            }
            else if (assets.legacyFont != null)
            {
                var text = go.AddComponent<Text>();
                text.font = assets.legacyFont;
                text.fontSize = Mathf.RoundToInt(size);
                text.fontStyle = bold ? FontStyle.Bold : FontStyle.Normal;
                text.color = color;
                text.text = item.text;
                text.alignment = item.anchor == "middle" ? TextAnchor.UpperCenter
                    : item.anchor == "end" ? TextAnchor.UpperRight : TextAnchor.UpperLeft;
                text.horizontalOverflow = HorizontalWrapMode.Overflow;
                text.verticalOverflow = VerticalWrapMode.Overflow;
                text.raycastTarget = false;
                if (Mathf.Abs(item.letter_spacing) > 0.01f)
                {
                    warnings.Add($"{item.id}: letter spacing {item.letter_spacing}px needs a font "
                                 + "asset that supports tracking");
                }
            }
            else
            {
                warnings.Add($"{item.id}: no font available, text skipped");
                UnityEngine.Object.DestroyImmediate(go);
            }
        }

        private static float AscentEm(Assets assets, float sizePx)
        {
            try
            {
                if (assets.tmpFont != null)
                {
                    var face = assets.tmpFont.faceInfo;
                    if (face.pointSize > 0)
                    {
                        return Mathf.Clamp(face.ascentLine / face.pointSize, 0.5f, 1.2f);
                    }
                }
                else if (assets.legacyFont != null && assets.legacyFont.fontSize > 0)
                {
                    return Mathf.Clamp(assets.legacyFont.ascent / (float)assets.legacyFont.fontSize,
                        0.5f, 1.2f);
                }
            }
            catch (Exception)
            {
                // fall through to the design's own estimate
            }
            return 0.8f;
        }
    }
}
