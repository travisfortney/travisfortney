"""Render Larry's running loop for the profile README. Requires Pillow."""
import math
from bisect import bisect_right
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FPS = 25
SPEED = 100
RAMP_SECONDS = 0.25
CAT_SIZE = (108, 117)
STRIDE_DISTANCE = 9


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


def make_route(width):
    """Two gently curved diagonal runs, sampled by distance for even pacing."""
    distance = width - CAT_SIZE[0] - 32
    routes = []
    for returning in (False, True):
        points, lengths = [], [0.0]
        for step in range(201):
            progress = step / 200
            bend = 20 * math.sin(math.pi * progress)
            if returning:
                point = (16 + distance * (1 - progress), 132 + 104 * progress - bend)
            else:
                point = (16 + distance * progress, 236 - 104 * progress + bend)
            if points:
                lengths.append(lengths[-1] + math.dist(points[-1], point))
            points.append(point)
        routes.append((points, lengths))
    return routes


def route_point(route, distance):
    points, lengths = route
    distance = max(0, min(lengths[-1], distance))
    segment = min(len(points) - 2, max(0, bisect_right(lengths, distance) - 1))
    fraction = (distance - lengths[segment]) / (lengths[segment + 1] - lengths[segment])
    start, end = points[segment], points[segment + 1]
    return (start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction)


def compose(width, sprite, point, foot=None):
    x, baseline = point
    foot = sprite.getchannel("A").getbbox()[3] if foot is None else foot
    image = Image.new("RGBA", (width, 260))
    image.alpha_composite(sprite, (round(x), round(baseline) - foot))
    return image


def choreography(width, sprites, behaviors, routes):
    """Run, investigate the room, blink, run back, and finish with a small hop."""
    frames = []
    idle = behaviors["idle"][0]

    def hold(sprite, point, seconds, foot=None):
        image = compose(width, sprite, point, foot)
        frames.extend([image] * round(seconds * FPS))

    def run(route, row, start, end):
        distance = end - start
        travel = round((distance / SPEED + RAMP_SECONDS) * FPS) / FPS
        speed = distance / (travel - RAMP_SECONDS)
        for i in range(round(travel * FPS)):
            elapsed = i / FPS
            if elapsed < RAMP_SECONDS:
                displacement = speed * elapsed**2 / (2 * RAMP_SECONDS)
            elif elapsed > travel - RAMP_SECONDS:
                displacement = distance - speed * (travel - elapsed)**2 / (2 * RAMP_SECONDS)
            else:
                displacement = speed * (elapsed - RAMP_SECONDS / 2)
            position = start + displacement
            sprite = sprites[row][math.floor(position / STRIDE_DISTANCE) % 8]
            frames.append(compose(width, sprite, route_point(route, position)))

    left, right = routes[0][0][0], routes[0][0][-1]
    distance = routes[0][1][-1]
    stop = distance * 0.46
    perch = route_point(routes[0], stop)
    hold(idle, left, 0.6)
    run(routes[0], 0, 0, stop)
    hold(idle, perch, 0.4)
    # Follow adjacent direction poses smoothly, lingering on interesting views.
    for direction in [4, 3, 2, 1, 0, 15, 14, 13, 12, 13, 14, 15, 0, 1, 2, 3, 4]:
        hold(behaviors["look"][direction], perch, 0.4 if direction in (0, 4, 12) else 0.15)
    hold(idle, perch, 0.4)
    run(routes[0], 0, stop, distance)
    # A short blink at the far end keeps the turnaround quiet.
    for column in [0, 1, 2, 3, 4, 5, 0]:
        hold(behaviors["idle"][column], right, 0.15)
    run(routes[1], 1, 0, routes[1][1][-1])
    hold(idle, left, 0.4)
    for column in [0, 1, 2, 3, 2, 1, 0]:
        hold(behaviors["wave"][column], left, 0.15)
    hold(idle, left, 0.35)
    # Preserve the atlas's hop height, interpolating its takeoff and landing.
    jump_foot = behaviors["jump"][0].getchannel("A").getbbox()[3]
    jump_height = jump_foot - behaviors["jump"][2].getchannel("A").getbbox()[3]
    for i in range(round(0.88 * FPS)):
        elapsed = i / FPS
        column = min(4, int(elapsed / 0.18))
        sprite = behaviors["jump"][column]
        airborne = max(0, min(1, (elapsed - 0.12) / 0.6))
        lift = jump_height * math.sin(math.pi * airborne)**2
        frames.append(compose(width, sprite, (left[0], left[1] - lift)))
    hold(idle, left, 0.6)
    return frames


def main():
    with Image.open(ASSETS / "larry-source" / "polished-atlas.png") as sheet:
        def row_frames(row, count):
            return [clean_sprite(sheet.crop((round(col*sheet.width/8), round(row*sheet.height/11),
                                             round((col+1)*sheet.width/8), round((row+1)*sheet.height/11)))
                                 .convert("RGBA").resize(CAT_SIZE, Image.Resampling.LANCZOS))
                    for col in range(count)]
        sprites = [row_frames(1, 8), row_frames(2, 8)]
        behaviors = {"idle": row_frames(0, 6), "wave": row_frames(3, 4),
                     "jump": row_frames(4, 5), "look": row_frames(9, 8) + row_frames(10, 8)}
        idle = behaviors["idle"][0]
    for theme, background in (("light", "#ffffff"), ("dark", "#0d1117")):
        # Train one palette on every pose, shared across desktop and mobile.
        poses = sprites[0] + sprites[1] + [pose for state in behaviors.values() for pose in state]
        sample = Image.new("RGBA", (CAT_SIZE[0]*8, CAT_SIZE[1]*math.ceil(len(poses)/8)), background)
        for i, pose in enumerate(poses):
            sample.alpha_composite(pose, ((i % 8)*CAT_SIZE[0], (i // 8)*CAT_SIZE[1]))
        palette = sample.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        colors = palette.getpalette()
        colors[765:768] = [255, 0, 255]
        palette.putpalette(colors)
        for layout, width in (("desktop", 960), ("mobile", 420)):
            routes = make_route(width)
            frames = choreography(width, sprites, behaviors, routes)
            frame_count = len(frames)
            for number, frame in enumerate(frames):
                bounds = frame.getchannel("A").getbbox()
                if not bounds or not (0 < bounds[0] < bounds[2] < width
                                      and 0 < bounds[1] < bounds[3] < frame.height):
                    raise ValueError(f"Clipped or empty frame at {layout} frame {number}")
            opaque = []
            for frame in frames:
                matte = Image.new("RGBA", frame.size, background)
                matte.alpha_composite(frame)
                opaque.append(matte.convert("RGB"))
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
                            append_images=indexed[1:], duration=1000 // FPS, loop=0,
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
