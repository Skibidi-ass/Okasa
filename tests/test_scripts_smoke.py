import subprocess
import shutil
import json
from pathlib import Path
from PIL import Image
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_png(path: Path, color=(255, 0, 0, 255)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (64, 64), color)
    img.save(path)


def _make_svg(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # very small valid SVG
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#00FF00"/></svg>'
    path.write_text(svg)


def test_build_and_pixelize_smoke(tmp_path: Path):
    # copy scripts to temp dir so script-relative ROOT resolves to tmp dir
    scripts_src = REPO_ROOT / 'scripts'
    scripts_dst = tmp_path / 'scripts'
    shutil.copytree(scripts_src, scripts_dst)

    assets_sprites = tmp_path / 'assets' / 'sprites'
    assets_sprites.mkdir(parents=True, exist_ok=True)

    # create two simple SVG frames and two simple PNG frames (pixelize uses PNGs)
    _make_svg(assets_sprites / 'okasa_jump_01.svg')
    _make_svg(assets_sprites / 'okasa_jump_02.svg')

    _make_png(assets_sprites / 'okasa_jump_01.png')
    _make_png(assets_sprites / 'okasa_jump_02.png')

    # If cairosvg is available, run build_sprites.py which converts SVG->PNG and builds a sheet
    try:
        import cairosvg  # type: ignore
        has_cairosvg = True
    except Exception:
        has_cairosvg = False

    if has_cairosvg:
        subprocess.run(["python3", "scripts/build_sprites.py"], cwd=tmp_path, check=True)

        sheet = tmp_path / 'assets' / 'spritesheets' / 'okasa_jump_sheet.png'
        atlas = tmp_path / 'assets' / 'spritesheets' / 'okasa_jump_atlas.json'
        assert sheet.exists(), f"Expected sheet at {sheet}"
        assert atlas.exists(), f"Expected atlas at {atlas}"

        with atlas.open() as f:
            data = json.load(f)
        assert data['meta']['frame_count'] == 2
        assert len(data['frames']) == 2

    else:
        pytest.skip("cairosvg not installed; skipping build_sprites part")

    # always run pixelize_sprites.py (works from PNG inputs)
    subprocess.run(["python3", "scripts/pixelize_sprites.py"], cwd=tmp_path, check=True)

    pixel_sheet = tmp_path / 'assets' / 'spritesheets' / 'pixel' / 'jump_32_sheet.png'
    pixel_atlas = tmp_path / 'assets' / 'spritesheets' / 'pixel' / 'jump_32_atlas.json'
    assert pixel_sheet.exists(), f"Expected pixel sheet at {pixel_sheet}"
    assert pixel_atlas.exists(), f"Expected pixel atlas at {pixel_atlas}"

    with pixel_atlas.open() as f:
        pdata = json.load(f)
    assert pdata['meta']['frame_count'] == 2
    assert len(pdata['frames']) == 2
