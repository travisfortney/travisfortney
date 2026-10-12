"""Generate a workbench check and Larry cameo from browser-rendered bases.

Requires Pillow. Run from the repository root:
    python3 scripts/generate-workbench-animation.py
The animation-source directory retains the browser-rendered SVG backgrounds
and the original Larry idle sprite used for the composition.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets'/'animation-source'
OUTPUT=ROOT/'assets'

def ease(v):
    v=max(0,min(1,v))
    return v*v*(3-2*v)

def point(x,y,mobile):
    theta=math.radians(-4)
    x,y=526+138+(x-138)*math.cos(theta)-(y-88)*math.sin(theta),86+88+(x-138)*math.sin(theta)+(y-88)*math.cos(theta)
    return ((x*.96-440,y*.96+174) if mobile else (x,y))

def frame(base, sprite, t, mobile):
    image=base.copy().convert('RGBA')
    scale=.96 if mobile else 1
    # Larry is occluded by the top edge of the keyboard window.
    reveal=ease((t-1.5)/.65)*(1-ease((t-3.35)/.65))
    if reveal>0:
        cat=sprite.resize((96,104),Image.Resampling.LANCZOS)
        x,y=824,145+(1-reveal)*95
        x,y=int(x*scale-(440 if mobile else 0)),int(y*scale+(174 if mobile else 0))
        if mobile: cat=cat.resize((92,100),Image.Resampling.LANCZOS)
        alpha=cat.getchannel('A')
        for px in range(cat.width):
            global_x=(x+px+(440 if mobile else 0))/scale
            edge=209+math.sin(math.radians(6))*(global_x-675)
            edge=edge*scale+(174 if mobile else 0)
            cutoff=max(0,min(cat.height,math.ceil(edge-y)))
            if cutoff<cat.height:
                ImageDraw.Draw(alpha).line((px,cutoff,px,cat.height),fill=0)
        cat.putalpha(alpha)
        image.alpha_composite(cat,(x,y))
    # Draw an antialiased check in the existing lavender utility tile.
    progress=ease((t-.4)/.75)
    if progress:
        overlay=Image.new('RGBA',(image.width*3,image.height*3))
        pts=[point(28,76,mobile),point(37,85,mobile),point(52,65,mobile)]
        lengths=[math.dist(pts[i],pts[i+1]) for i in range(2)]
        remaining=sum(lengths)*progress
        draw=ImageDraw.Draw(overlay)
        for i,length in enumerate(lengths):
            a,b=pts[i],pts[i+1]
            fraction=min(1,remaining/length)
            if fraction<=0: break
            end=(a[0]+(b[0]-a[0])*fraction,a[1]+(b[1]-a[1])*fraction)
            draw.line((a[0]*3,a[1]*3,end[0]*3,end[1]*3),fill='#293551',width=round(3.6*scale*3))
            remaining-=length
        image=Image.alpha_composite(image,overlay.resize(image.size,Image.Resampling.LANCZOS))
    return image

def main():
    source=Image.open(SOURCE/'larry-idle.gif')
    sprite=source.convert('RGBA')
    for mode in ('light','dark','mobile-light','mobile-dark'):
        mobile=mode.startswith('mobile')
        base=Image.open(SOURCE/f'base-{mode}.png').convert('RGBA')
        def gif_rgb(image):
            rgb=image.convert('RGB')
            # Reserve one unmistakable color for transparent rounded corners.
            transparent=image.getchannel('A').point(lambda a:255 if a<128 else 0)
            rgb.paste('#ff00ff',mask=transparent)
            return rgb
        palette=gif_rgb(frame(base,sprite,2.5,mobile)).quantize(colors=256,method=Image.Quantize.MEDIANCUT)
        colors=palette.getpalette()
        transparent_index=next(i for i in range(256) if colors[i*3:i*3+3]==[255,0,255])
        frames=[gif_rgb(frame(base,sprite,i/10,mobile)).quantize(palette=palette,dither=Image.Dither.NONE) for i in range(46)]
        duration=[100]*45+[5000]
        out=OUTPUT/f'workbench-animated-{mode}.gif'
        frames[0].save(out,save_all=True,append_images=frames[1:],duration=duration,loop=0,optimize=True,disposal=1,transparency=transparent_index)
        frame(base,sprite,2.5,mobile).save(OUTPUT/f'workbench-still-{mode}.png',optimize=True)
        print(out.name,out.stat().st_size,'bytes')
if __name__=='__main__': main()
