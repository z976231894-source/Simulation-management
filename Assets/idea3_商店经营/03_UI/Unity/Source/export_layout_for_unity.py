#!/usr/bin/env python3
"""Turn the design package into an assembly spec for Unity.

Reads only what the package already ships:

    ../../manifest.json          panel + icon list, colours, resolutions
    ../../svg/*.svg              the 18 screens, authoritative layout
    ../../assets/panels/*.svg    the 12 stretchable pieces
    ../../assets/icons/*.svg     the 23 icons
    ../../backgrounds/*.png      the 4 scene backgrounds

Writes:

    ../Layout/ui_layout.json     every screen as a flat list of draw items

Nothing is generated: each item points at an existing asset (one of the 12
panels, one of the 23 icons, a background, or a Unity built-in UI sprite).
Rounded rects pick the panel whose corner radius and border are closest to the
design, and carry a tint so the fill colour still matches exactly.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UI = HERE.parents[1]                      # .../03_UI
OUT = HERE.parent / "Layout" / "ui_layout.json"

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"

# corner radius + border colour of each shipped panel piece, read from
# assets/panels/*.svg (fill, stroke, radius)
PANELS = {
    "panel_paper": {"fill": "#FFF9ED", "stroke": "#D7DAC8", "radius": 24},
    "panel_forest": {"fill": "#183E34", "stroke": None, "radius": 24},
    "panel_soft": {"fill": "#E9EADB", "stroke": None, "radius": 24},
    "ticket_paper": {"fill": "#FFF9ED", "stroke": "#D7DAC8", "radius": 8},
    "button_primary": {"fill": "#183E34", "stroke": None, "radius": 12},
    "button_secondary": {"fill": "#FFF9ED", "stroke": "#183E34", "radius": 12},
    "button_danger": {"fill": "#CC775F", "stroke": None, "radius": 12},
    "button_disabled": {"fill": "#E9EADB", "stroke": None, "radius": 12},
    "chip_mint": {"fill": "#BDD6C4", "stroke": None, "radius": 18},
    "chip_coral": {"fill": "#CC775F", "stroke": None, "radius": 18},
    "keycap": {"fill": "#F7F1E4", "stroke": "#D7DAC8", "radius": 6},
    "progress_track": {"fill": "#D7DAC8", "stroke": None, "radius": 8},
}

ELEMENT_RE = re.compile(r"<(image|rect|text|line|circle|g)\b([^>]*?)(?:/>|>(.*?)</\1>)", re.S)
SHAPE_RE = re.compile(r"<(path|circle|rect|line)\b([^>]*?)/>", re.S)


def attrs(raw: str) -> dict:
    return dict(re.findall(r'([\w:.-]+)\s*=\s*"([^"]*)"', raw))


def num(value, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def px(value):
    if value is None:
        return None
    return int(value) if abs(value - round(value)) < 1e-6 else round(value, 2)


def rgb(value: str):
    value = (value or "").lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        return None
    try:
        return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None


def tint_for(target: str, base: str) -> str:
    """Per channel multiplier that turns the panel's own fill into the design colour."""
    want, have = rgb(target), rgb(base)
    if want is None or have is None:
        return "#FFFFFF"
    channels = []
    for a, b in zip(want, have):
        channels.append(1.0 if b <= 1e-4 else max(0.0, min(1.0, a / b)))
    return "#" + "".join(f"{round(c * 255):02X}" for c in channels)


def same_color(a: str, b: str) -> bool:
    ra, rb = rgb(a), rgb(b)
    return ra is not None and rb is not None and max(abs(x - y) for x, y in zip(ra, rb)) < 0.02


def tint_possible(target: str, base: str) -> bool:
    """A multiply tint can only darken, so a brighter target cannot be reached."""
    want, have = rgb(target), rgb(base)
    if want is None or have is None:
        return True
    return not any(a > b + 0.004 for a, b in zip(want, have))


def pick_panel(fill, stroke):
    """Panel piece to slice, chosen on colour and border only.

    The corner radius is corrected at draw time through the Image's
    pixelsPerUnitMultiplier (see border_scale below), so the piece no longer has
    to match the design radius. A tint multiplies and can only darken, so the
    amount that cannot be reached (a brighter target than the piece carries)
    is what gets penalised."""
    want_stroke = bool(stroke)
    scored = []
    want = rgb(fill) or (1.0, 1.0, 1.0)
    for name, panel in PANELS.items():
        if bool(panel["stroke"]) != want_stroke:
            continue
        have = rgb(panel["fill"]) or (0.0, 0.0, 0.0)
        shortfall = sum(max(0.0, a - b) for a, b in zip(want, have))
        distance = sum(abs(a - b) for a, b in zip(want, have))
        scored.append((round(shortfall, 4), round(distance, 4),
                       abs(panel["radius"] - 24.0), name))
    if not scored:
        scored = [(9.99, 9.99, 0.0, name) for name in PANELS]
    scored.sort()
    return scored[0][3]


def border_scale(radius_design, panel_radius):
    """Factor for Image.pixelsPerUnitMultiplier that turns the piece's own corner
    radius into the radius the design asked for: drawn border = (radius + 3) / scale."""
    if not radius_design or radius_design <= 0:
        return 1.0
    return round(min(4.0, max(0.4, (panel_radius + 3.0) / (radius_design + 3.0))), 4)


def parse_defs(raw: str):
    gradients, patterns, filters = {}, {}, {}
    block = re.search(r"<defs>(.*?)</defs>", raw, re.S)
    if not block:
        return gradients, patterns, filters
    body = block.group(1)
    for head, inner in re.findall(r"<linearGradient\b([^>]*)>(.*?)</linearGradient>", body, re.S):
        stops = []
        for stop in re.findall(r"<stop\b([^>]*)/?>", inner):
            values = attrs(stop)
            stops.append({"color": values.get("stop-color"),
                          "opacity": num(values.get("stop-opacity"), 1.0)})
        gradients[attrs(head).get("id")] = stops
    for head, inner in re.findall(r"<pattern\b([^>]*)>(.*?)</pattern>", body, re.S):
        patterns[attrs(head).get("id")] = inner.strip()
    for head, inner in re.findall(r"<filter\b([^>]*)>(.*?)</filter>", body, re.S):
        shadow = re.search(r"<feDropShadow\b([^>]*)/?>", inner)
        if not shadow:
            continue
        values = attrs(shadow.group(1))
        filters[attrs(head).get("id")] = {
            "dx": num(values.get("dx")), "dy": num(values.get("dy")),
            "color": values.get("flood-color", "#000000"),
            "alpha": num(values.get("flood-opacity"), 0.2),
        }
    return gradients, patterns, filters


def first_color_in(markup: str):
    match = re.search(r'fill="(#[0-9A-Fa-f]{3,6})"', markup or "")
    return match.group(1) if match else None


def icon_tables():
    by_paths, by_shape = {}, {}
    for path in sorted((UI / "assets" / "icons").glob("*.svg")):
        raw = path.read_text(encoding="utf-8")
        paths = tuple(re.findall(r'<path d="([^"]+)"', raw))
        if paths:
            by_paths[paths] = path.stem
        circles = re.findall(r'<circle\b([^>]*)/>', raw)
        if circles:
            key = tuple(sorted(
                (round(num(attrs(c).get("cx")), 2), round(num(attrs(c).get("cy")), 2),
                 round(num(attrs(c).get("r")), 2)) for c in circles))
            by_shape[key] = path.stem
    return by_paths, by_shape


def background_table():
    sha = hashlib.sha1
    return {sha((UI / "backgrounds" / name.name).read_bytes()).hexdigest(): name.stem
            for name in (UI / "backgrounds").glob("*.png")}


def parse_screen(svg_path: Path, icons, shapes, backgrounds):
    raw = svg_path.read_text(encoding="utf-8")
    gradients, patterns, filters = parse_defs(raw)
    body = raw[raw.find("</defs>") + 7:] if "</defs>" in raw else raw
    body = body[: body.rfind("</svg>")] if "</svg>" in body else body

    items, report = [], {"border_scaled": 0, "tint_clamped": 0,
                         "skipped": [], "approximated": []}
    background = None
    used = {}

    def unique(base):
        count = used.get(base, 0)
        used[base] = count + 1
        return base if count == 0 else f"{base}_{count + 1}"

    for order, match in enumerate(ELEMENT_RE.finditer(body)):
        tag, head, inner = match.group(1), match.group(2), match.group(3) or ""
        props = attrs(head)

        if tag == "image":
            payload = props.get("href", "").split(",", 1)[-1]
            digest = hashlib.sha1(base64.b64decode(payload)).hexdigest()
            background = backgrounds.get(digest)
            if not background:
                report["skipped"].append("background image does not match backgrounds/*.png")
            continue

        if tag == "rect":
            x, y = num(props.get("x")), num(props.get("y"))
            w, h = num(props.get("width")), num(props.get("height"))
            radius = num(props.get("rx")) if props.get("rx") else None
            if radius is not None and radius <= 0:
                radius = None          # rx="0" is a square rect, not a nine-slice piece
            fill, stroke = props.get("fill"), props.get("stroke")
            reference = re.fullmatch(r"url\(#([\w-]+)\)", (fill or "").strip())
            name = reference.group(1) if reference else None
            opacity = num(props.get("opacity"), 1.0)
            item = {"id": unique(f"rect_{order}"), "kind": "rect", "level": order,
                    "rect_px": [px(x), px(y), px(w), px(h)], "alpha": px(opacity)}

            if name in gradients:
                stops = gradients[name] or []
                color = stops[0]["color"] if stops else "#000000"
                mean = sum(stop["opacity"] for stop in stops) / len(stops) if stops else 1.0
                item.update({"draw": "solid", "builtin": "Background",
                             "tint": color, "alpha": px(mean * opacity),
                             "approx": f"gradient {name} drawn as a flat wash"})
                report["approximated"].append(f"{item['id']} gradient {name}")
            elif name in patterns:
                color = first_color_in(patterns[name]) or "#FFFFFF"
                item.update({"draw": "solid", "builtin": "Background",
                             "tint": color, "alpha": px(opacity),
                             "approx": f"pattern {name} drawn as a flat band"})
                report["approximated"].append(f"{item['id']} pattern {name}")
            elif radius is not None and fill:
                panel = pick_panel(fill, stroke)
                item.update({"draw": "panel", "panel": panel, "tint": tint_for(fill, PANELS[panel]["fill"])})
                item["radius_design"] = px(radius)
                item["radius_panel"] = PANELS[panel]["radius"]
                item["border_scale"] = border_scale(radius, PANELS[panel]["radius"])
                if abs(item["border_scale"] - 1.0) > 0.01:
                    report["border_scaled"] += 1
                if not tint_possible(fill, PANELS[panel]["fill"]):
                    report["tint_clamped"] += 1
            elif fill:
                item.update({"draw": "solid", "builtin": "Background", "tint": fill})
            else:
                item.update({"draw": "skip"})
                report["skipped"].append(f"{item['id']} rect without fill")

            if props.get("filter") == "url(#shadow)":
                item["shadow"] = filters.get("shadow", {"dx": 0, "dy": 10,
                                                        "color": "#0E2E24", "alpha": 0.2})
            items.append(item)
            continue

        if tag == "text":
            size = num(props.get("font-size"), 16)
            items.append({
                "id": unique("text_" + re.sub(r"[^0-9A-Za-z]+", "_", html.unescape(inner))[:24].lower()),
                "kind": "text", "level": order,
                "text": html.unescape(inner).strip(),
                "anchor": props.get("text-anchor", "start"),
                "anchor_x": px(num(props.get("x"))),
                "baseline_px": px(num(props.get("y"))),
                "size_px": px(size),
                "weight": px(num(props.get("font-weight"), 400)),
                "letter_spacing": px(num(props.get("letter-spacing"), 0)),
                "color": props.get("fill"),
                "color_px": None,
            })
            continue

        if tag == "line":
            x1, y1 = num(props.get("x1")), num(props.get("y1"))
            x2, y2 = num(props.get("x2")), num(props.get("y2"))
            thickness = max(1.0, num(props.get("stroke-width"), 1))
            items.append({
                "id": unique(f"line_{order}"), "kind": "line", "level": order,
                "rect_px": [px(min(x1, x2)), px(min(y1, y2) - thickness / 2),
                            px(abs(x2 - x1) or thickness), px(abs(y2 - y1) or thickness)],
                "draw": "solid", "builtin": "Background",
                "tint": props.get("stroke"), "alpha": 1,
            })
            continue

        if tag == "circle":
            cx, cy, r = num(props.get("cx")), num(props.get("cy")), num(props.get("r"))
            fill, stroke = props.get("fill"), props.get("stroke")
            size = 2 * r
            item = {"id": unique(f"circle_{order}"), "kind": "circle", "level": order,
                    "rect_px": [px(cx - r), px(cy - r), px(size), px(size)]}
            if fill and fill != "none":
                item.update({"draw": "solid", "builtin": "Knob", "tint": fill, "alpha": 1,
                             "approx": "outline drawn as a filled disc" if stroke else None})
                if stroke:
                    report["approximated"].append(f"{item['id']} circle outline")
            else:
                item.update({"draw": "skip"})
                report["skipped"].append(f"{item['id']} outline only circle")
            items.append(item)
            continue

        paths = re.findall(r'<path d="([^"]+)"', inner)
        icon = icons.get(tuple(paths))
        if not icon:
            circles = re.findall(r'<circle\b([^>]*)/>', inner)
            if circles:
                key = tuple(sorted(
                    (round(num(attrs(c).get("cx")), 2), round(num(attrs(c).get("cy")), 2),
                     round(num(attrs(c).get("r")), 2)) for c in circles))
                icon = shapes.get(key)
        if not icon:
            icon = "onions"
            report["approximated"].append(f"glyph at level {order} drawn with the onions icon")
        bounds = shape_bounds(inner, props.get("transform"))
        items.append({
            "id": unique("glyph_" + icon), "kind": "glyph", "level": order,
            "rect_px": bounds, "draw": "icon", "icon": icon,
            "tint": props.get("stroke") or "#183E34", "alpha": 1,
        })

    return items, background, report


def shape_bounds(inner, transform):
    tx = ty = 0.0
    scale = 1.0
    if transform:
        move = re.search(r"translate\(\s*(" + NUM + r")[ ,]+(" + NUM + r")?\s*\)", transform)
        if move:
            tx, ty = float(move.group(1)), float(move.group(2) or 0)
        zoom = re.search(r"scale\(\s*(" + NUM + r")", transform)
        if zoom:
            scale = float(zoom.group(1))
    boxes = []
    for head in re.findall(r'<circle\b([^>]*)/>', inner):
        p = attrs(head)
        cx, cy, r = num(p.get("cx")), num(p.get("cy")), num(p.get("r"))
        boxes.append((cx - r, cy - r, 2 * r, 2 * r))
    for head in re.findall(r'<rect\b([^>]*)/>', inner):
        p = attrs(head)
        boxes.append((num(p.get("x")), num(p.get("y")), num(p.get("width")), num(p.get("height"))))
    for path in re.findall(r'<path d="([^"]+)"', inner):
        numbers = [float(v) for v in re.findall(NUM, path)]
        if len(numbers) >= 2:
            xs, ys = numbers[0::2], numbers[1::2]
            boxes.append((min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))
    if not boxes:
        return None
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[0] + b[2] for b in boxes)
    bottom = max(b[1] + b[3] for b in boxes)
    return [px(tx + left * scale), px(ty + top * scale),
            px((right - left) * scale), px((bottom - top) * scale)]


def png_size(path: Path):
    header = path.read_bytes()[16:24]
    return int.from_bytes(header[0:4], "big"), int.from_bytes(header[4:8], "big")


def main() -> int:
    manifest = json.loads((UI / "manifest.json").read_text(encoding="utf-8"))
    icons, shapes = icon_tables()
    backgrounds = background_table()

    panels = []
    for name, info in PANELS.items():
        png = UI / "assets" / "panels" / f"{name}.png"
        nine = next((a for a in manifest["assets"] if a["id"] == name), None) or {}
        inset = nine.get("nine_slice", {}).get("left", int(info["radius"]) + 3)
        panels.append({
            "id": name,
            "path": f"assets/panels/{name}.png",
            "size": list(png_size(png)),
            "radius": info["radius"],
            "fill": info["fill"],
            "border_LBRT": [inset, inset, inset, inset],
            "minimum_target_size": [inset * 2 + 1, inset * 2 + 1],
        })

    icon_assets = []
    for asset in manifest["assets"]:
        if asset["type"] != "icon":
            continue
        icon_assets.append({"id": asset["id"], "path": f"assets/icons/{asset['id']}.png",
                            "size": list(png_size(UI / "assets" / "icons" / f"{asset['id']}.png"))})

    background_assets = []
    for name in sorted(name.stem for name in (UI / "backgrounds").glob("*.png")):
        background_assets.append({"id": name, "path": f"backgrounds/{name}.png",
                                  "size": list(png_size(UI / "backgrounds" / f"{name}.png"))})

    screens, totals = [], {"elements": 0, "border_scaled": 0, "tint_clamped": 0,
                           "skipped": 0, "approximated": 0, "text": 0}
    for screen in manifest["screens"]:
        items, background, report = parse_screen(
            UI / screen["svg"], icons, shapes, backgrounds)
        screens.append({
            "id": screen["id"], "title": screen.get("title"),
            "category": screen.get("category"),
            "width": screen.get("width", 1920), "height": screen.get("height", 1080),
            "background": background,
            "source_svg": screen["svg"],
            "elements": items,
            "report": report,
        })
        totals["elements"] += len(items)
        totals["text"] += sum(1 for i in items if i["kind"] == "text")
        totals["border_scaled"] += report["border_scaled"]
        totals["tint_clamped"] += report["tint_clamped"]
        totals["skipped"] += len(report["skipped"])
        totals["approximated"] += len(report["approximated"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "version": 1,
        "product": manifest["product"],
        "purpose": "Assembled from the assets shipped in this package; no new art",
        "reference_resolution": manifest["resolution"],
        "origin": "top-left",
        "unit": "pixels at reference resolution",
        "asset_root": "Assets/idea3_商店经营/03_UI",
        "palette": manifest["colors"],
        "builtin_sprites": {
            "Background": "UI/Skin/Background.psd (flat white, used for solid fills)",
            "Knob": "UI/Skin/Knob.psd (white disc, used for filled circles)",
        },
        "panels": panels,
        "icons": icon_assets,
        "backgrounds": background_assets,
        "screens": screens,
        "totals": totals,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(totals, indent=2, ensure_ascii=False))
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
