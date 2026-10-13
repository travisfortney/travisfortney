# Larry running frames

The two rows contain eight running-right and eight running-left frames, with
192 × 208 pixel cells. Artwork © 2026 Travis Fortney, reused from
[Larry David Desktop Pet](https://github.com/travisfortney/larry-david-desktop-pet).

`idle.webp` contains the original idle row for the brief turns and reduced-motion
stills. The renderer removes detached specks, aligns the feet, and uses 20 fps
output with consistent travel speed on desktop and mobile. The run eases into
each turn, and stride timing follows travel distance. GIFs and stills have
transparent backgrounds. Every decoded GIF frame is checked against its intended
image to catch trails or missing pixels.

Larry follows two curved diagonal paths through the space. The route is sampled
by distance to keep his speed and stride consistent while he moves up and down.

Regenerate the profile GIFs and reduced-motion stills with:

```sh
python3 scripts/generate-larry-animation.py
```
