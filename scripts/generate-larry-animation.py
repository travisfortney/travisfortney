"""Render Larry's running loop for the profile README. Requires Pillow."""
import math
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FPS = 20
SPEED = 80
TURN_SECONDS = 0.4
RAMP_SECONDS = 0.25
CAT_SIZE = (72, 78)


def clean_sprite(sprite):
    """Remove detached specks while retaining the main figure's edge pixels."""
    alpha = sprite.getchannel("A")
    points = {(x, y) for y in range(sprite.height) for x in range(sprite.width)
              if alpha.getpixel((x, y)) > 16}
    components = []
    while points:
        seed = points.pop()
        stack, component = [seed], {seed}
        while stack:
            x, y = stack.pop()
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                adjacent = (x + dx, y + dy)
                if adjacent in points:
                    points.remove(adjacent)
                    component.add(adjacent)
                    stack.append(adjacent)
        components.append(component)
    keep = max(components, key=len)
    # Preserve the antialiased perimeter around the retained figure.
    mask = Image.new("L", sprite.size)
    for x, y in keep:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                px, py = x + dx, y + dy
                if 0 <= px < sprite.width and 0 <= py < sprite.height:
                    mask.putpixel((px, py), alpha.getpixel((px, py)))
    sprite.putalpha(mask)
    return sprite


def render(width, background, sprites, idle, index, travel):
    # Start halfway through the left turn so the loop closes on the same pose.
    t = (index / FPS - TURN_SECONDS / 2) % (2 * travel + 2 * TURN_SECONDS)
    distance = width - CAT_SIZE[0] - 32
    speed = distance / (travel - RAMP_SECONDS)
    def position(elapsed):
        if elapsed < RAMP_SECONDS:
            return speed * elapsed**2 / (2 * RAMP_SECONDS)
        if elapsed > travel - RAMP_SECONDS:
            return distance - speed * (travel - elapsed)**2 / (2 * RAMP_SECONDS)
        return speed * (elapsed - RAMP_SECONDS / 2)
    if t < travel:
        displacement = position(t)
        x, row = 16 + displacement, 0
    elif t < travel + TURN_SECONDS:
        x, row, displacement = width - CAT_SIZE[0] - 16, None, 0
    elif t < travel * 2 + TURN_SECONDS:
        elapsed = t - travel - TURN_SECONDS
        displacement = position(elapsed)
        x, row = width - CAT_SIZE[0] - 16 - displacement, 1
    else:
        x, row, displacement = 16, None, 0
    sprite = idle if row is None else sprites[row][math.floor(displacement / 6) % 8]
    # Match each frame's lowest foot to one baseline instead of floating.
    foot = sprite.getchannel("A").getbbox()[3]
    y = 216 - foot
    image = Image.new("RGBA", (width, 260))
    image.alpha_composite(sprite, (round(x), y))
    return image


def main():
    with Image.open(ASSETS / "larry-source" / "running.webp") as sheet:
        sprites = [[clean_sprite(sheet.crop((col*192, row*208, (col+1)*192, (row+1)*208))
                    .convert("RGBA").resize(CAT_SIZE, Image.Resampling.LANCZOS))
                    for col in range(8)] for row in range(2)]
    with Image.open(ASSETS / "larry-source" / "idle.webp") as sheet:
        idle = clean_sprite(sheet.crop((0, 0, 192, 208)).convert("RGBA")
                            .resize(CAT_SIZE, Image.Resampling.LANCZOS))
    for theme, background in (("light", "#ffffff"), ("dark", "#0d1117")):
        for layout, width in (("desktop", 960), ("mobile", 420)):
            travel = round(((width - CAT_SIZE[0] - 32) / SPEED + RAMP_SECONDS) * FPS) / FPS
            frame_count = round((2 * travel + 2 * TURN_SECONDS) * FPS)
            frames = [render(width, background, sprites, idle, i, travel)
                      for i in range(frame_count)]
            opaque = []
            for frame in frames:
                matte = Image.new("RGBA", frame.size, background)
                matte.alpha_composite(frame)
                opaque.append(matte.convert("RGB"))
            sample = Image.new("RGB", (width, 260 * 16), background)
            for i in range(16):
                sample.paste(opaque[round(i * (frame_count - 1) / 15)], (0, i*260))
            palette = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
            colors = palette.getpalette()
            colors[765:768] = [255, 0, 255]
            palette.putpalette(colors)
            indexed = []
            for frame, matte in zip(frames, opaque):
                image = matte.quantize(palette=palette, dither=Image.Dither.NONE)
                outside = frame.getchannel("A").point(lambda alpha: 255 if alpha == 0 else 0)
                image.paste(255, mask=outside)
                image.info["transparency"] = 255
                indexed.append(image)
            background_index = 255
            prefix = ASSETS / f"larry-running-{layout}-{theme}"
            indexed[0].save(prefix.with_suffix(".gif"), save_all=True,
                            append_images=indexed[1:], duration=50, loop=0,
                            disposal=2, optimize=False,
                            transparency=background_index, background=background_index)
            # Delta compression must reproduce every complete frame exactly.
            with Image.open(prefix.with_suffix(".gif")) as decoded:
                elapsed = 0
                for number in range(decoded.n_frames):
                    decoded.seek(number)
                    expected = Image.new("RGBA", decoded.size, background)
                    expected.alpha_composite(indexed[round(elapsed / (1000 / FPS))].convert("RGBA"))
                    actual = Image.new("RGBA", decoded.size, background)
                    actual.alpha_composite(decoded.convert("RGBA"))
                    if ImageChops.difference(actual.convert("RGB"), expected.convert("RGB")).getbbox():
                        raise ValueError(f"Frame mismatch in {prefix.name} at {elapsed} ms")
                    elapsed += decoded.info["duration"]
                if elapsed != frame_count * 1000 / FPS:
                    raise ValueError(f"Incorrect duration for {prefix.name}")
            still = Image.new("RGBA", (width, 260))
            still.alpha_composite(idle, ((width-CAT_SIZE[0])//2, 216-idle.getchannel("A").getbbox()[3]))
            still.save(prefix.with_suffix(".png"), optimize=True)
            print(prefix.with_suffix(".gif").name, prefix.with_suffix(".gif").stat().st_size)


if __name__ == "__main__":
    main()
