"""Create side-by-side A/B comparison GIFs and PNGs for 24px previews.

Produces: assets/spritesheets/pixel/compare_ab/<anim>_24_ab.gif and <anim>_24_ab.png
"""
from PIL import Image, ImageSequence, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'assets' / 'spritesheets' / 'pixel' / 'compare_ab'
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANIMS = ['jump', 'kneel', 'wink']
DURATION = 80  # ms

for anim in ANIMS:
    path_a = ROOT / 'assets' / 'spritesheets' / 'pixel' / f'{anim}_24.gif'  # 10-color
    path_b = ROOT / 'assets' / 'spritesheets' / 'pixel' / 'compare_8color' / f'{anim}_24_8c.gif'  # 8-color
    if not path_a.exists() or not path_b.exists():
        print('Missing files for', anim)
        continue

    frames_a = [frame.copy().convert('RGBA') for frame in ImageSequence.Iterator(Image.open(path_a))]
    frames_b = [frame.copy().convert('RGBA') for frame in ImageSequence.Iterator(Image.open(path_b))]

    max_frames = max(len(frames_a), len(frames_b))
    # pad with last frame if different lengths
    while len(frames_a) < max_frames:
        frames_a.append(frames_a[-1].copy())
    while len(frames_b) < max_frames:
        frames_b.append(frames_b[-1].copy())

    composed_frames = []
    for fa, fb in zip(frames_a, frames_b):
        w = fa.width + fb.width
        h = max(fa.height, fb.height) + 18  # add space for labels
        comp = Image.new('RGBA', (w, h), (255,255,255,0))
        comp.paste(fa, (0, 18), fa)
        comp.paste(fb, (fa.width, 18), fb)
        draw = ImageDraw.Draw(comp)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        # labels
        draw.rectangle([0,0, fa.width, 18], fill=(15,23,42,200))
        draw.rectangle([fa.width,0, w,18], fill=(15,23,42,200))
        draw.text((6,2), '10-color', fill=(255,255,255,255), font=font)
        draw.text((fa.width+6,2), '8-color', fill=(255,255,255,255), font=font)
        composed_frames.append(comp)

    gif_out = OUT_DIR / f'{anim}_24_ab.gif'
    composed_frames[0].save(gif_out, save_all=True, append_images=composed_frames[1:], duration=DURATION, loop=0, disposal=2)
    # also write a static PNG of first frame
    png_out = OUT_DIR / f'{anim}_24_ab.png'
    composed_frames[0].save(png_out)
    print('Wrote', gif_out, 'and', png_out)

print('Done A/B compare.')