"""Pixel-art conversion pipeline for Okasa sprite frames.

- Takes PNG frames in `assets/sprites/` matching pattern `okasa_<anim>_NN.png`.
- Creates base pixel sizes (e.g., 32x32, 48x48), quantizes to limited palette, then upscales (nearest) to preserve blocky pixels.
- Writes outputs to `assets/sprites/pixel/<anim>/` and builds sprite sheets + GIF previews in `assets/spritesheets/pixel/`.

Usage:
  python3 scripts/pixelize_sprites.py
"""
from pathlib import Path
from PIL import Image, ImageOps
import re
import os

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / 'assets' / 'sprites'
PIXEL_DIR = ROOT / 'assets' / 'sprites' / 'pixel'
OUT_DIR = ROOT / 'assets' / 'spritesheets' / 'pixel'
PIXEL_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRAME_RE = re.compile(r'okasa_([a-z]+)_(\d+)\.png$')

# choose base sizes (small) and upscale factors
BASE_SIZES = [24, 32, 48]
UPSCALES = [3]
PALETTE_COLORS = 10

# GIF frame duration (milliseconds) used for preview GIFs
FRAME_DURATION_MS = 80

# custom Okasa palette (10 colors). Set USE_CUSTOM_PALETTE to True to enforce this palette.
USE_CUSTOM_PALETTE = True
CUSTOM_PALETTE = [
    '#0F172A',  # outfit near-black navy
    '#1E1B6B',  # hair indigo
    '#2EC4B6',  # hair teal
    '#FFD166',  # eye golden-amber
    '#FF6B6B',  # coral accent
    '#A0E7E5',  # talisman glow
    '#FFEFD5',  # skin
    '#2C3440',  # dark gray/depth
    '#FFFFFF',  # white/highlight
    '#000000',  # black/shadow
]

# helper: build a PIL palette image from hex color list for exact quantization
def make_palette_image(hex_colors):
    palette_img = Image.new('P', (16, 16))
    palette = []
    for h in hex_colors:
        h = h.lstrip('#')
        palette.extend([int(h[i:i+2], 16) for i in (0, 2, 4)])
    # pad to 256 colors (768 values)
    while len(palette) < 768:
        palette.extend([0, 0, 0])
    palette_img.putpalette(palette)
    return palette_img

PALETTE_IMAGE = make_palette_image(CUSTOM_PALETTE) if USE_CUSTOM_PALETTE else None

# gather frames grouped by animation
frames = {}
for p in sorted(SRC_DIR.glob('okasa_*.png')):
    m = FRAME_RE.search(p.name)
    if not m:
        continue
    anim = m.group(1)
    idx = int(m.group(2))
    frames.setdefault(anim, []).append((idx, p))

if not frames:
    print('No sprite frames found in', SRC_DIR)
    raise SystemExit(1)

for anim, entries in frames.items():
    entries.sort()
    print(f'Processing animation: {anim} ({len(entries)} frames)')
    # create output folder per animation
    anim_out = PIXEL_DIR / anim
    anim_out.mkdir(parents=True, exist_ok=True)
    # For each base size, create pixel frames
    for base in BASE_SIZES:
        pixel_frames = []
        for idx, path in entries:
            img = Image.open(path).convert('RGBA')
            # remove alpha to avoid semi-transparent edges during quantize
            bg = Image.new('RGBA', img.size, (0,0,0,0))
            bg.paste(img, (0,0), img)
            img = bg
            # downscale to base size
            small = img.resize((base, base), resample=Image.LANCZOS)
            # quantize to limited colors or use custom palette if enabled
            if USE_CUSTOM_PALETTE and PALETTE_IMAGE is not None:
                quant = small.convert('RGB').quantize(palette=PALETTE_IMAGE)
            else:
                quant = small.convert('RGB').quantize(colors=PALETTE_COLORS, method=Image.MEDIANCUT)
            quant_rgba = quant.convert('RGBA')
            frame_name = f'{anim}_{idx:02d}_{base}.png'
            out_path = anim_out / frame_name
            quant_rgba.save(out_path)
            pixel_frames.append(out_path)

            # upscale versions
            for scale in UPSCALES:
                up_sz = (base*scale, base*scale)
                up = quant_rgba.resize(up_sz, resample=Image.NEAREST)
                up_name = f'{anim}_{idx:02d}_{base}x{scale}.png'
                up_path = anim_out / up_name
                up.save(up_path)

        # build horizontal sprite sheet for base size and for each upscale
        if pixel_frames:
            # base sheet
            imgs = [Image.open(p).convert('RGBA') for p in pixel_frames]
            w, h = imgs[0].size
            sheet = Image.new('RGBA', (w * len(imgs), h), (0,0,0,0))
            atlas = {'frames': {}, 'meta': {'sheet': f'{anim}_{base}_sheet.png', 'frame_w': w, 'frame_h': h, 'frame_count': len(imgs)}}
            for i, im in enumerate(imgs):
                sheet.paste(im, (i*w, 0), im)
                atlas['frames'][f'{anim}_{i}'] = {'x': i*w, 'y': 0, 'w': w, 'h': h}
            sheet_path = OUT_DIR / f'{anim}_{base}_sheet.png'
            atlas_path = OUT_DIR / f'{anim}_{base}_atlas.json'
            sheet.save(sheet_path)
            import json
            with open(atlas_path, 'w') as f:
                json.dump(atlas, f, indent=2)
            print('Wrote', sheet_path, 'and', atlas_path)

            # upscaled sheets
            for scale in UPSCALES:
                up_imgs = [Image.open(p.with_name(p.stem + f'x{scale}.png')).convert('RGBA') for p in pixel_frames]
                w2, h2 = up_imgs[0].size
                sheet2 = Image.new('RGBA', (w2 * len(up_imgs), h2), (0,0,0,0))
                atlas2 = {'frames': {}, 'meta': {'sheet': f'{anim}_{base}x{scale}_sheet.png', 'frame_w': w2, 'frame_h': h2, 'frame_count': len(up_imgs)}}
                for i, im in enumerate(up_imgs):
                    sheet2.paste(im, (i*w2, 0), im)
                    atlas2['frames'][f'{anim}_{i}'] = {'x': i*w2, 'y': 0, 'w': w2, 'h': h2}
                sheet2_path = OUT_DIR / f'{anim}_{base}x{scale}_sheet.png'
                atlas2_path = OUT_DIR / f'{anim}_{base}x{scale}_atlas.json'
                sheet2.save(sheet2_path)
                with open(atlas2_path, 'w') as f:
                    json.dump(atlas2, f, indent=2)
                print('Wrote', sheet2_path, 'and', atlas2_path)

        # create animated GIF preview from base frames
        gif_frames = [Image.open(p).convert('RGBA') for p in pixel_frames]
        if gif_frames:
            gif_path = OUT_DIR / f'{anim}_{base}.gif'
            gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=FRAME_DURATION_MS, loop=0, disposal=2)
            print('Wrote GIF preview', gif_path)

# Optional: generate a comparison set using a reduced 8-color palette
GENERATE_8_COLOR_COMPARISON = True
CUSTOM_PALETTE_8 = [
    '#0F172A',  # outfit near-black navy
    '#1E1B6B',  # hair indigo
    '#2EC4B6',  # hair teal
    '#FFD166',  # eye golden-amber
    '#FF6B6B',  # coral accent
    '#A0E7E5',  # talisman glow
    '#FFEFD5',  # skin
    '#2C3440',  # dark gray/depth
]

if GENERATE_8_COLOR_COMPARISON:
    PALETTE_IMAGE_8 = make_palette_image(CUSTOM_PALETTE_8)
    COMPARE_OUT = OUT_DIR / 'compare_8color'
    COMPARE_OUT.mkdir(parents=True, exist_ok=True)
    print('Generating 8-color comparisons in', COMPARE_OUT)

    for anim, entries in frames.items():
        entries.sort()
        for base in BASE_SIZES:
            pixel_frames = []
            for idx, path in entries:
                img = Image.open(path).convert('RGBA')
                bg = Image.new('RGBA', img.size, (0,0,0,0))
                bg.paste(img, (0,0), img)
                img = bg
                small = img.resize((base, base), resample=Image.LANCZOS)
                quant = small.convert('RGB').quantize(palette=PALETTE_IMAGE_8)
                quant_rgba = quant.convert('RGBA')
                frame_name = f'{anim}_{idx:02d}_{base}_8c.png'
                out_path = PIXEL_DIR / anim / frame_name
                quant_rgba.save(out_path)
                pixel_frames.append(out_path)

                for scale in UPSCALES:
                    up_sz = (base*scale, base*scale)
                    up = quant_rgba.resize(up_sz, resample=Image.NEAREST)
                    up_name = f'{anim}_{idx:02d}_{base}x{scale}_8c.png'
                    up_path = PIXEL_DIR / anim / up_name
                    up.save(up_path)

            if pixel_frames:
                imgs = [Image.open(p).convert('RGBA') for p in pixel_frames]
                w, h = imgs[0].size
                sheet = Image.new('RGBA', (w * len(imgs), h), (0,0,0,0))
                atlas = {'frames': {}, 'meta': {'sheet': f'{anim}_{base}_8c_sheet.png', 'frame_w': w, 'frame_h': h, 'frame_count': len(imgs)}}
                for i, im in enumerate(imgs):
                    sheet.paste(im, (i*w, 0), im)
                    atlas['frames'][f'{anim}_{i}'] = {'x': i*w, 'y': 0, 'w': w, 'h': h}
                sheet_path = COMPARE_OUT / f'{anim}_{base}_8c_sheet.png'
                atlas_path = COMPARE_OUT / f'{anim}_{base}_8c_atlas.json'
                sheet.save(sheet_path)
                import json
                with open(atlas_path, 'w') as f:
                    json.dump(atlas, f, indent=2)
                print('Wrote', sheet_path, 'and', atlas_path)

                # build upscaled sheets using stored upscaled paths
                for scale in UPSCALES:
                    # gather upscaled frames for this scale
                    up_paths = [PIXEL_DIR / anim / f'{anim}_{int(p.name.split("_")[1]) :02d}_{base}x{scale}_8c.png' for p in pixel_frames]
                    # fallback: try to construct from names more robustly
                    up_paths = []
                    for p in pixel_frames:
                        # p.name example: 'jump_01_24_8c.png'
                        parts = p.name.split('_')  # ['jump','01','24','8c.png']
                        idx_str = parts[1]
                        up_name = f'{anim}_{idx_str}_{base}x{scale}_8c.png'
                        up_paths.append(PIXEL_DIR / anim / up_name)
                    up_imgs = [Image.open(pp).convert('RGBA') for pp in up_paths]
                    w2, h2 = up_imgs[0].size
                    sheet2 = Image.new('RGBA', (w2 * len(up_imgs), h2), (0,0,0,0))
                    atlas2 = {'frames': {}, 'meta': {'sheet': f'{anim}_{base}x{scale}_8c_sheet.png', 'frame_w': w2, 'frame_h': h2, 'frame_count': len(up_imgs)}}
                    for i, im in enumerate(up_imgs):
                        sheet2.paste(im, (i*w2, 0), im)
                        atlas2['frames'][f'{anim}_{i}'] = {'x': i*w2, 'y': 0, 'w': w2, 'h': h2}
                    sheet2_path = COMPARE_OUT / f'{anim}_{base}x{scale}_8c_sheet.png'
                    atlas2_path = COMPARE_OUT / f'{anim}_{base}x{scale}_8c_atlas.json'
                    sheet2.save(sheet2_path)
                    with open(atlas2_path, 'w') as f:
                        json.dump(atlas2, f, indent=2)
                    print('Wrote', sheet2_path, 'and', atlas2_path)

            gif_frames = [Image.open(p).convert('RGBA') for p in pixel_frames]
            if gif_frames:
                gif_path = COMPARE_OUT / f'{anim}_{base}_8c.gif'
                gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=FRAME_DURATION_MS, loop=0, disposal=2)
                print('Wrote GIF preview', gif_path)

print('Done pixelizing sprites.')
