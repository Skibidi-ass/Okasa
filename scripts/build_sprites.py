"""Build sprite sheets from SVG frames in assets/sprites/.
Produces: assets/spritesheets/<animation>_sheet.png and <animation>_atlas.json
"""
from pathlib import Path
import cairosvg
from PIL import Image
import json

ROOT = Path(__file__).resolve().parents[1]
SPRITE_SVG_DIR = ROOT / 'assets' / 'sprites'
OUT_DIR = ROOT / 'assets' / 'spritesheets'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# gather frames grouped by animation prefix (okasa_jump_01.svg -> okasa_jump)
frames = {}
for svg in sorted(SPRITE_SVG_DIR.glob('okasa_*.svg')):
    name = svg.stem  # okasa_jump_01
    parts = name.rsplit('_', 1)
    anim = parts[0]  # okasa_jump
    frames.setdefault(anim, []).append(svg)

if not frames:
    print('No sprite SVGs found in', SPRITE_SVG_DIR)
    raise SystemExit(1)

for anim, svgs in frames.items():
    print('Building', anim, 'with', len(svgs), 'frames...')
    png_frames = []
    # convert each svg -> PNG (256px)
    for svg in svgs:
        out_png = svg.with_suffix('.png')
        try:
            cairosvg.svg2png(url=str(svg), write_to=str(out_png), output_width=256)
        except Exception as e:
            print('Failed to convert', svg, '->', e)
            continue
        png_frames.append(out_png)

    # open PNG frames and compute sheet size (horizontal layout)
    imgs = [Image.open(p) for p in png_frames]
    if not imgs:
        print('No images for', anim)
        continue
    w, h = imgs[0].size
    sheet_w = w * len(imgs)
    sheet_h = h
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (0,0,0,0))

    atlas = {'frames': {}, 'meta': {'sheet': f'{anim}_sheet.png', 'frame_w': w, 'frame_h': h, 'frame_count': len(imgs)}}

    for i, im in enumerate(imgs):
        sheet.paste(im, (i*w, 0))
        atlas['frames'][f'{anim}_{i}'] = {'x': i*w, 'y': 0, 'w': w, 'h': h}

    sheet_path = OUT_DIR / f'{anim}_sheet.png'
    atlas_path = OUT_DIR / f'{anim}_atlas.json'
    sheet.save(sheet_path)
    with open(atlas_path, 'w') as f:
        json.dump(atlas, f, indent=2)
    print('Wrote', sheet_path, 'and', atlas_path)

print('Done building sprite sheets.')