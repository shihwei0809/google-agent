# Geometry Diagrams

Use this reference when a teaching deck needs math diagrams.

## Planning Fields

For each geometry need, specify:

```yaml
geometry:
  id: slide_04_fig_01
  type: triangle
  purpose: show angle sum
  labels: [A, B, C]
  highlights:
    - angle: A
      color: primary
  canvas:
    width: 720
    height: 480
```

## Rendering Approach

- Prefer deterministic SVG or Python-generated diagrams over AI-generated math
  diagrams.
- Export diagrams as PNG or SVG, inspect them, then insert them into the deck.
- Keep labels large enough for projection.
- Use consistent colors with the slide palette.

## Supported Common Types

- triangle
- quadrilateral
- circle
- coordinate plane
- solid 3D sketch
- parallel lines cut by a transversal
- triangle centers
- similar triangles

For unsupported shapes, create a custom SVG/Python drawing with explicit
coordinates. Do not rely on image generation for precise geometric correctness.
