import glob, sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
_cache={}
def fonts(pattern):
    if pattern not in _cache:
        _cache[pattern]=[TTFont(f) for f in sorted(glob.glob(pattern))]
    return _cache[pattern]
def text_path(text, pattern, size, x, y, spacing=0):
    """return svg path d for text, baseline at y, starting at x"""
    out=[]; cx=x
    for ch in text:
        for f in fonts(pattern):
            cm=f.getBestCmap()
            if ord(ch) in cm:
                gs=f.getGlyphSet(); g=cm[ord(ch)]
                upm=f['head'].unitsPerEm; s=size/upm
                pen=SVGPathPen(gs, ntos=lambda v: f"{v:.1f}")
                gs[g].draw(TransformPen(pen,(s,0,0,-s,cx,y)))
                out.append(pen.getCommands())
                cx+=gs[g].width*s+spacing
                break
        else:
            raise SystemExit(f"missing {ch}")
    return " ".join(out), cx
