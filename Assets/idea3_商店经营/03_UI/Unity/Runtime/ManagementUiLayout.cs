using System;
using System.Collections.Generic;
using UnityEngine;

namespace OneMoreDiner.ManagementUi
{
    /// <summary>Layout data exported from the design package by
    /// Unity/Source/export_layout_for_unity.py. Everything is expressed in
    /// reference pixels with the origin at the top left corner.</summary>
    [Serializable]
    public class UiLayoutFile
    {
        public int version;
        public string product;
        public string purpose;
        public int[] reference_resolution;
        public string origin;
        public string unit;
        public string asset_root;
        public List<UiPanelSpec> panels = new List<UiPanelSpec>();
        public List<UiIconSpec> icons = new List<UiIconSpec>();
        public List<UiBackgroundSpec> backgrounds = new List<UiBackgroundSpec>();
        public List<UiScreenSpec> screens = new List<UiScreenSpec>();
    }

    [Serializable]
    public class UiPanelSpec
    {
        public string id;
        public string path;
        public int[] size;
        public float radius;
        public string fill;
        public int[] border_LBRT;
        public int[] minimum_target_size;
    }

    [Serializable]
    public class UiIconSpec
    {
        public string id;
        public string path;
        public int[] size;
    }

    [Serializable]
    public class UiBackgroundSpec
    {
        public string id;
        public string path;
        public int[] size;
    }

    [Serializable]
    public class UiShadowSpec
    {
        public float dx;
        public float dy;
        public string color;
        public float alpha;
    }

    [Serializable]
    public class UiItemSpec
    {
        public string id;
        public string kind;          // rect, text, line, circle, glyph
        public int level;
        public float[] rect_px;      // x, y, width, height
        public string draw;          // panel, icon, solid, skip
        public string panel;
        public string icon;
        public string builtin;
        public string tint;
        public float alpha = 1f;
        public UiShadowSpec shadow;
        public float radius_design;
        public float radius_panel;
        public float border_scale = 1f;
        public string approx;

        public string text;
        public string anchor;        // start, middle, end
        public float anchor_x;
        public float baseline_px;
        public float size_px;
        public float weight;
        public float letter_spacing;
        public string color;

        public float X => rect_px != null && rect_px.Length > 0 ? rect_px[0] : 0f;
        public float Y => rect_px != null && rect_px.Length > 1 ? rect_px[1] : 0f;
        public float W => rect_px != null && rect_px.Length > 2 ? rect_px[2] : 1f;
        public float H => rect_px != null && rect_px.Length > 3 ? rect_px[3] : 1f;
    }

    [Serializable]
    public class UiScreenSpec
    {
        public string id;
        public string title;
        public string category;
        public float width = 1920f;
        public float height = 1080f;
        public string background;
        public string source_svg;
        public List<UiItemSpec> elements = new List<UiItemSpec>();
    }

    public static class UiColor
    {
        public static Color Parse(string hex, float alpha = 1f)
        {
            var color = new Color(1f, 1f, 1f, alpha);
            if (string.IsNullOrEmpty(hex))
            {
                return color;
            }
            var value = hex.Trim().TrimStart('#');
            if (value.Length == 3)
            {
                value = string.Concat(value[0], value[0], value[1], value[1], value[2], value[2]);
            }
            if (value.Length < 6 || !int.TryParse(value.Substring(0, 6),
                    System.Globalization.NumberStyles.HexNumber,
                    System.Globalization.CultureInfo.InvariantCulture, out var packed))
            {
                return color;
            }
            color.r = ((packed >> 16) & 0xFF) / 255f;
            color.g = ((packed >> 8) & 0xFF) / 255f;
            color.b = (packed & 0xFF) / 255f;
            color.a = alpha;
            return color;
        }

        /// <summary>Estimate of how wide a run of text is, used only to size the
        /// rect. Placement comes from the design anchor point, not from this.</summary>
        public static float EstimateWidth(string text, float sizePx)
        {
            var count = string.IsNullOrEmpty(text) ? 1 : text.Length;
            return Mathf.Max(sizePx * 0.62f * count, sizePx * 2f);
        }
    }
}
