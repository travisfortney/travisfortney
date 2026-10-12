# Workbench animation source

The four base PNGs are browser renders of the matching workbench SVGs, with the utility tile's number removed to draw the animated check there.

Larry's original idle sprite is reused from [Larry David Desktop Pet](https://github.com/travisfortney/larry-david-desktop-pet/blob/main/qa/previews/idle.gif).

Regenerate the GIFs and reduced-motion stills with Pillow:

```sh
python3 scripts/generate-workbench-animation.py
```

Each GIF is a 9.5-second loop: the check draws, Larry peeks above the keyboard window and retreats, then the scene holds still. The header text and README body stay unchanged.
