from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape


WIDTH = 1600
HEIGHT = 2400


def t(x: int, y: int, content: str, size: int = 32, weight: int = 400, fill: str = "#eef4ff", anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI, Microsoft JhengHei, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(content)}</text>'
    )


def render_card(card: dict) -> list[str]:
    x = int(card["x"])
    y = int(card["y"])
    w = int(card["w"])
    h = int(card["h"])
    accent = card.get("accent", "#60a5fa")
    lines = card.get("lines", [])
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="#132042" stroke="#28406f" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="10" height="{h}" rx="5" fill="{accent}"/>',
        t(x + 28, y + 48, str(card["title"]), 30, 700),
    ]
    line_y = y + 92
    for line in lines:
        parts.append(t(x + 40, line_y, f"• {line}", 24, 400, "#d7e3ff"))
        line_y += 42
    return parts


def render_bars(chart: dict) -> list[str]:
    x = int(chart.get("x", 100))
    y = int(chart.get("y", 280))
    w = int(chart.get("w", 1400))
    items = chart["items"]
    max_value = max(item["value"] for item in items)
    parts = [t(x, y, chart["title"], 28, 700, "#bcd0ff")]
    row_y = y + 48
    for item in items:
        label = str(item["label"])
        value = float(item["value"])
        right_text = str(item.get("text", value))
        bar_w = int((value / max_value) * (w - 360))
        parts.append(t(x, row_y, label, 24, 500))
        parts.append(f'<rect x="{x + 360}" y="{row_y - 22}" width="{w - 360}" height="24" rx="12" fill="#21335f"/>')
        parts.append(f'<rect x="{x + 360}" y="{row_y - 22}" width="{bar_w}" height="24" rx="12" fill="#60a5fa"/>')
        parts.append(t(x + w - 10, row_y, right_text, 22, 700, "#f8fbff", "end"))
        row_y += 54
    return parts


def build_svg(spec: dict) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0b1020"/>',
        '<rect x="40" y="40" width="1520" height="2320" rx="32" fill="#111936" stroke="#24325c" stroke-width="2"/>',
        t(100, 130, spec["title"], 56, 800),
        t(100, 180, spec.get("subtitle", ""), 26, 400, "#b9c8ed"),
    ]
    if "bar_chart" in spec:
        parts.extend(render_bars(spec["bar_chart"]))
    for card in spec.get("cards", []):
        parts.extend(render_card(card))
    parts.append(t(100, HEIGHT - 70, spec.get("footer", ""), 20, 400, "#90a2cc"))
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an SVG infographic from a JSON spec.")
    parser.add_argument("spec", help="Path to the JSON spec.")
    parser.add_argument("--output", required=True, help="Output SVG path.")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    output_path = Path(args.output).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    svg = build_svg(spec)
    output_path.write_text(svg, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
