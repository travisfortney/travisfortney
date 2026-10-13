# Larry running frames

The two rows contain eight running-right and eight running-left frames, with
192 × 208 pixel cells. Artwork © 2026 Travis Fortney, reused from
[Larry David Desktop Pet](https://github.com/travisfortney/larry-david-desktop-pet).

`idle.webp` contains the original idle row for the brief turns and reduced-motion
stills. The renderer removes detached specks, aligns the feet, and uses 25 fps
output with consistent travel speed on desktop and mobile. The run eases into
each turn, and stride timing follows travel distance. GIFs and stills have
transparent backgrounds. Every decoded GIF frame is checked against its intended
image to catch trails or missing pixels.

Larry is rendered at 108 × 117 pixels and follows two curved diagonal paths
through the space. The route is sampled by distance to keep his speed and stride
consistent while he moves up and down.

`behaviors.webp` is the original full spritesheet from the same package. It adds
the planted 16-direction look-around poses, idle blink, wave, and five-frame hop.
Larry pauses partway through his run to look around, blinks at the far end, then
runs back, waves, and hops. The hop keeps its original height with eased takeoff
and landing.
Every frame is checked for clipping as well as faithful GIF decoding.

`polished-atlas.png` is a rendering refinement of the original atlas with closer
fur tones and consistent lighting across the poses. It keeps the 8 × 11 layout.
The renderer reads this sheet, removes detached edge residue, and uses one
palette per theme trained on every pose and shared across desktop and mobile.
The original strips and full atlas are retained as the source artwork.

Regenerate the profile GIFs and reduced-motion stills with:

```sh
python3 scripts/generate-larry-animation.py
```
