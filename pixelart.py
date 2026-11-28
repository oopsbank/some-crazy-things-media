"""Pixel-art animal sprites (approved style "P1"): Noto Color Emoji -> 24 px, 14 colours, 1 px dark outline.
Scale up only with NEAREST so pixels stay crisp."""
from PIL import Image, ImageDraw, ImageFont
_EF=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
_CACHE={}
def pixel_sprite(ch,n=24,colors=14,outline=(20,10,25)):
    key=(ch,n,colors)
    if key in _CACHE: return _CACHE[key]
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=_EF,embedded_color=True)
    im=im.crop(im.getbbox()); im.thumbnail((n,n),Image.LANCZOS)
    c=Image.new('RGBA',(n+2,n+2),(0,0,0,0)); c.paste(im,((n+2-im.width)//2,(n+2-im.height)//2),im)
    a=c.getchannel('A').point(lambda v:255 if v>110 else 0)
    rgb=c.convert('RGB').quantize(colors,method=Image.Quantize.MEDIANCUT).convert('RGB')
    out=Image.new('RGBA',c.size,(0,0,0,0)); out.paste(rgb,(0,0),a)
    px=out.load(); al=a.load(); W,H=out.size
    for y in range(H):
        for x in range(W):
            if al[x,y]==0 and any(0<=x+dx<W and 0<=y+dy<H and al[x+dx,y+dy] for dx,dy in((1,0),(-1,0),(0,1),(0,-1))):
                px[x,y]=outline+(255,)
    _CACHE[key]=out; return out
def pixel_icon(ch,size):
    """Sprite scaled to `size` px with nearest-neighbour (crisp)."""
    s=pixel_sprite(ch); return s.resize((int(size),int(size)),Image.NEAREST)
