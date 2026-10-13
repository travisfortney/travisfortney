"""Render Larry's running loop for the profile README. Requires Pillow."""
import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FRAMES = 120
CAT_SIZE = (72, 78)


def render(width, background, sprites, index):
    phase = index / FRAMES
    right = phase < 0.5
    progress = phase * 2 if right else 2 - phase * 2
    x = round(progress * (width - CAT_SIZE[0]))
    y = round(135 + 45 * math.sin(2 * math.pi * phase))
    sprite = sprites[0 if right else 1][math.floor(index * 0.9) % 8]
    image = Image.new("RGBA", (width, 260), background)
    image.alpha_composite(sprite, (x, y))
    return image.convert("RGB")


def main():
    with Image.open(ASSETS / "larry-source" / "running.webp") as sheet:
        sprites = [[sheet.crop((col*192, row*208, (col+1)*192, (row+1)*208))
                    .convert("RGBA").resize(CAT_SIZE, Image.Resampling.LANCZOS)
                    for col in range(8)] for row in range(2)]
    for theme, background in (("light", "#ffffff"), ("dark", "#0d1117")):
        for layout, width in (("desktop", 960), ("mobile", 420)):
            frames = [render(width, background, sprites, i) for i in range(FRAMES)]
            sample = Image.new("RGB", (width, 260 * 16), background)
            for i in range(16):
                sample.paste(frames[i*7], (0, i*260))
            palette = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
            indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
            prefix = ASSETS / f"larry-running-{layout}-{theme}"
            indexed[0].save(prefix.with_suffix(".gif"), save_all=True,
                            append_images=indexed[1:], duration=100, loop=0,
                            disposal=2, optimize=False)
            frames[30].save(prefix.with_suffix(".png"), optimize=True)
            print(prefix.with_suffix(".gif").name, prefix.with_suffix(".gif").stat().st_size)


if __name__ == "__main__":
    main()
