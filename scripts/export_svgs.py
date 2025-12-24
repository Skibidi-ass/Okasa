"""Simple exporter: converts SVGs in /assets to PNG using CairoSVG if available.

Usage:
  python3 scripts/export_svgs.py

Produces: assets/okasa_front.png, etc.
"""
import os
from pathlib import Path

SVG_DIR = Path(__file__).resolve().parents[1] / 'assets'

svgs = list(SVG_DIR.glob('okasa_*.svg'))
if not svgs:
    print('No okasa SVGs found in', SVG_DIR)
    raise SystemExit(1)

try:
    import cairosvg
except Exception as e:
    print('CairoSVG not installed. To create PNG exports, install it with: pip install cairosvg')
    print('SVG files are available in', SVG_DIR)
    raise SystemExit(0)

for svg in svgs:
    # choose sizes: avatars get multiple smaller sizes, others default to 1200px
    if 'avatar' in svg.name:
        sizes = [512, 256, 128, 64]
    else:
        sizes = [1200]
    for s in sizes:
        out = svg.with_name(f"{svg.stem}_{s}.png")
        print(f'Converting {svg.name} -> {out.name} ({s}px) ...')
        try:
            cairosvg.svg2png(url=str(svg), write_to=str(out), output_width=s)
        except Exception as e:
            print('Failed to convert', svg.name, 'to', s, 'px:', e)
print('Done.')
