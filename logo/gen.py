from glyph import text_path
M='/tmp/fs/x_fontsource-shippori-mincho*/package/files/*-800-normal.woff2'
M7='/tmp/fs/x_fontsource-shippori-mincho*/package/files/*-700-normal.woff2'
G="#1E5B3A"; GOLD="#C9A227"; W="#FFFFFF"
def symbol(g=G, acc=GOLD, pane=W, ox=0, oy=0, s=1.0):
    # shield with house-roof top; 4-pane window; accent pane
    shield="M100 6 L186 52 L186 116 C186 158 146 184 100 198 C54 184 14 158 14 116 L14 52 Z"
    x0,y0,p,gap=59,76,38,6
    panes=[(x0,y0,pane),(x0+p+gap,y0,acc),(x0,y0+p+gap,pane),(x0+p+gap,y0+p+gap,pane)]
    r=''.join(f'<rect x="{x}" y="{y}" width="{p}" height="{p}" rx="3" fill="{c}"/>' for x,y,c in panes)
    # roof line inside (宀 echo)
    roof=f'<path d="M100 28 L168 64" fill="none" stroke="{pane}" stroke-width="0"/>'
    return (f'<g transform="translate({ox},{oy}) scale({s})"><path d="{shield}" fill="{g}"/>'
            f'<path d="M42 62 L100 30 L158 62" fill="none" stroke="{pane}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>{r}</g>')
def txt(t,pat,size,x,y,fill,sp=0):
    d,e=text_path(t,pat,size,x,y,sp); return f'<path d="{d}" fill="{fill}"/>',e
def svg(w,h,body,bg=None):
    b=f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{b}{body}</svg>'
TAG="補償つき防犯フィルムという安心"
def horizontal(tag=True,g=G,acc=GOLD,pane=W,fg=None,bg=None,bandtxt=W):
    fg=fg or g; pad=30; S=1.3; sw=200*S
    tx=pad+sw+36; W_=420
    body=symbol(g,acc,pane,pad,pad,S)
    a,_=txt("窓守屋",M,140,tx,pad+122,fg)
    hs=84; sp=(W_-4*hs)/3
    b,_=txt("まもりや",M7,hs,tx,pad+122+hs+22,fg,sp)
    body+=a+b
    total=pad+sw+36+W_+pad; h=pad*2+sw
    if tag:
        by=h-pad+20; bw=total-2*pad; bh=66
        ts=bw/16*0.92; d,e=text_path(TAG,M7,ts,0,0)
        off=pad+(bw-e)/2
        d,e=text_path(TAG,M7,ts,off,by+bh/2+ts*0.34)
        body+=f'<rect x="{pad}" y="{by}" width="{bw}" height="{bh}" rx="8" fill="{fg}"/><path d="{d}" fill="{bandtxt}"/>'
        h=by+bh+pad
    return svg(total,h,body,bg),total,h
def vertical(tag=True,g=G,acc=GOLD,pane=W,fg=None,bg=None,bandtxt=W):
    fg=fg or g; pad=30; W_=450; total=W_+pad*2
    sw=220
    body=symbol(g,acc,pane,(total-sw)/2,pad,1.1)
    y=pad+sw+150
    a,_=txt("窓守屋",M,150,pad,y,fg)
    hs=84; sp=(W_-4*hs)/3
    b,_=txt("まもりや",M7,hs,pad,y+hs+24,fg,sp)
    body+=a+b; h=y+hs+24+pad
    if tag:
        by=h-pad+26; bh=56; ts=W_/16*0.92
        d,e=text_path(TAG,M7,ts,0,0); off=pad+(W_-e)/2
        d,e=text_path(TAG,M7,ts,off,by+bh/2+ts*0.34)
        body+=f'<rect x="{pad}" y="{by}" width="{W_}" height="{bh}" rx="8" fill="{fg}"/><path d="{d}" fill="{bandtxt}"/>'
        h=by+bh+pad
    return svg(total,h,body,bg),total,h
import os
o='/home/user/insta-autopost/logo'; os.makedirs(o,exist_ok=True)
files={
 'mamoriya_horizontal.svg':horizontal(True,bg=W)[0],
 'mamoriya_horizontal_notag.svg':horizontal(False,bg=W)[0],
 'mamoriya_vertical.svg':vertical(True,bg=W)[0],
 'mamoriya_vertical_notag.svg':vertical(False,bg=W)[0],
 'mamoriya_mono.svg':horizontal(True,acc="#FFFFFF",bg=W)[0],
 'mamoriya_reverse.svg':horizontal(True,g=W,acc=GOLD,pane=G,fg=W,bg=G,bandtxt=G)[0],
 'mamoriya_symbol.svg':svg(220,220,symbol(G,GOLD,W,10,10,1.0),W),
}
for k,v in files.items(): open(f'{o}/{k}','w').write(v)
print(list(files))
