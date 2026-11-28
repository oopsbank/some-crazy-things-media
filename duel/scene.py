# Static desert arena with the two compact camps and big gates (from the approved mockup).
import sys, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; rng=np.random.default_rng(5)
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
def font(s): return ImageFont.truetype(B,int(s))
RED=(230,60,50); BLUE=(50,120,235); COL={0:RED,1:BLUE}
DARK={0:(140,30,25),1:(25,60,150)}; LIGHT={0:(255,130,110),1:(130,180,255)}
SS=4   # supersample factor for vector art
def ctext(d,cx,y,t,fn,fill,sw=4,sf=(0,0,0)):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=sf)
def paste(im,src,cx,cy): im.alpha_composite(src,(int(cx-src.size[0]/2),int(cy-src.size[1]/2)))

TOP_CAMP=(30,360); BOT_CAMP=(1290,1620)
def build_bg():
    global_rng_state=random.getstate(); random.seed(7)
    # ---- desert terrain ----
    TOPP=(0,200); FIELD=(200,1530); BOTP=(1530,1730)
    yy,xx=np.mgrid[0:H,0:W]
    n=rng.normal(0,1,(H//6+1,W//6+1)); n=np.kron(n,np.ones((6,6)))[:H,:W]
    base=np.zeros((H,W,3)); base[:]=(222,190,130)
    base+=n[...,None]*np.array([6,5,4])
    dune=np.sin(yy/38.0+np.sin(xx/140.0)*2.2)        # dune ripples
    base+=(dune[...,None]*np.array([10,9,7]))
    big=np.sin(xx/260.0+yy/310.0)*np.cos(yy/190.0)     # large dune shading
    base+=(big[...,None]*np.array([16,13,9]))
    im=Image.fromarray(np.clip(base,0,255).astype(np.uint8),'RGB').convert('RGBA'); d=ImageDraw.Draw(im)
    # ---- camps spanning the full width ----
    def camp(s,y0,y1,top):
        S=2; h=y1-y0; L=Image.new('RGBA',(W*S,h*S),(0,0,0,0)); g=ImageDraw.Draw(L)
        def R(x0,a,x1,b,**k): g.rectangle([x0*S,a*S,x1*S,b*S],**k)
        def RR(x0,a,x1,b,r,**k): g.rounded_rectangle([x0*S,a*S,x1*S,b*S],radius=r*S,**k)
        def E(cx,cy,r,**k): g.ellipse([(cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S],**k)
        PAD=90
        fy=h-34-PAD if top else 34+PAD   # front wall line (towards the enemy)
        by=10 if top else h-10          # back edge
        # compound ground
        RR(6,min(fy,by)-4,W-6,max(fy,by)+4,18,fill=(196,170,122,255),outline=(160,135,95,255),width=3*S)
        tint=Image.new('RGBA',L.size,COL[s]+(28,)); L.alpha_composite(Image.composite(tint,Image.new('RGBA',L.size,(0,0,0,0)),L.split()[3]))
        g=ImageDraw.Draw(L)
        # front wall: concrete barriers with two gates (where units leave)
        gates=[(380,700)]
        for x in range(14,W-14,40):
            if any(a-20<x<b for a,b in gates): continue
            RR(x,fy-10,x+36,fy+10,4,fill=(175,175,168,255),outline=(110,110,105,255),width=2*S)
        # back fence
        for x in range(14,W-14,24): R(x,by-2,x+14,by+2,fill=(120,105,80,255))
        # watchtowers at the corners
        for x in (40,W-40):
            cy=fy-(34 if top else -34)
            R(x-26,cy-26,x+26,cy+26,fill=(120,95,65,255),outline=(70,55,35,255),width=3*S); R(x-17,cy-17,x+17,cy+17,fill=DARK[s]+(255,))
        mid=(fy+by)/2
        # tents (team canvas with ridge)
        for x in (110,330,750,970):
            w2,h2=64,46; RR(x-w2/2+6,mid-h2/2+6,x+w2/2+6,mid+h2/2+6,6,fill=(0,0,0,60))
            RR(x-w2/2,mid-h2/2,x+w2/2,mid+h2/2,6,fill=COL[s]+(255,),outline=DARK[s]+(255,),width=3*S)
            g.line([(x-w2/2)*S,mid*S,(x+w2/2)*S,mid*S],fill=DARK[s]+(255,),width=4*S)
            R(x-w2/2,mid-h2/2,x,mid,fill=LIGHT[s]+(70,))
        # barracks
        for x in (220,860):
            w2,h2=110,62; R(x-w2/2+7,mid-h2/2+7,x+w2/2+7,mid+h2/2+7,fill=(0,0,0,60))
            R(x-w2/2,mid-h2/2,x+w2/2,mid+h2/2,fill=(150,140,120,255),outline=(90,85,70,255),width=3*S)
            for k in range(4): R(x-w2/2+6+k*28,mid-h2/2+6,x-w2/2+28+k*28,mid+h2/2-6,fill=(170,160,140,255))
            R(x-w2/2,mid-4,x+w2/2,mid+4,fill=DARK[s]+(255,))
        # fuel tanks + helipad
        for x in (450,630):
            for k in (-1,1):
                E(x,mid+k*22,18,fill=(200,200,190,255),outline=(120,120,110,255),width=2*S); E(x,mid+k*22,7,fill=(150,150,140,255))
        # command building in the middle with star
        w2,h2=130,84; R(540-w2/2+8,mid-h2/2+8,540+w2/2+8,mid+h2/2+8,fill=(0,0,0,70))
        RR(540-w2/2,mid-h2/2,540+w2/2,mid+h2/2,10,fill=(140,135,120,255),outline=(80,76,66,255),width=4*S)
        RR(540-w2/2+14,mid-h2/2+14,540+w2/2-14,mid+h2/2-14,8,fill=COL[s]+(255,),outline=DARK[s]+(255,),width=3*S)
        # ---- the big main gate (focal point) ----
        dr=1 if top else -1                       # direction towards the enemy
        gx0,gx1=380,700; gy=fy
        # forecourt slab sticking out of the wall
        R(gx0-90,min(gy,gy+dr*62),gx1+90,max(gy,gy+dr*62),fill=(165,160,150,255),outline=(110,106,98,255),width=3*S)
        for x in range(gx0-80,gx1+90,30): g.line([x*S,min(gy,gy+dr*62)*S,x*S,max(gy,gy+dr*62)*S],fill=(150,145,135,255),width=S)
        # doors: two heavy leaves in team colour with metal bands and rivets
        dy0,dy1=min(gy-dr*10,gy+dr*40),max(gy-dr*10,gy+dr*40)
        R(gx0,dy0,gx1,dy1,fill=DARK[s]+(255,))
        for k,(a,b) in enumerate(((gx0+4,540-3),(540+3,gx1-4))):
            R(a,dy0+4,b,dy1-4,fill=COL[s]+(255,),outline=DARK[s]+(255,),width=2*S)
            for x in range(int(a)+14,int(b),22): g.line([x*S,(dy0+5)*S,x*S,(dy1-5)*S],fill=DARK[s]+(140,),width=2*S)
            for yb in (dy0+9,dy1-9):
                R(a+2,yb-2,b-2,yb+2,fill=(70,70,75,255))
                for x in range(int(a)+8,int(b),18): E(x,yb,3,fill=(200,200,205,255))
        # two big gate towers with crenellations and team roofs
        for tx in (gx0-54,gx1+54):
            ty=gy+dr*14; t2=62
            R(tx-t2+6,ty-t2+6,tx+t2+6,ty+t2+6,fill=(0,0,0,80))
            R(tx-t2,ty-t2,tx+t2,ty+t2,fill=(150,140,120,255),outline=(85,78,65,255),width=4*S)
            for k in range(-t2+4,t2-8,16):
                R(tx+k,ty-t2-6,tx+k+9,ty-t2+2,fill=(135,125,105,255)); R(tx+k,ty+t2-2,tx+k+9,ty+t2+6,fill=(135,125,105,255))
                R(tx-t2-6,ty+k,tx-t2+2,ty+k+9,fill=(135,125,105,255)); R(tx+t2-2,ty+k,tx+t2+6,ty+k+9,fill=(135,125,105,255))
            RR(tx-40,ty-40,tx+40,ty+40,6,fill=COL[s]+(255,),outline=DARK[s]+(255,),width=3*S)
            g.line([(tx-40)*S,(ty-40)*S,(tx+40)*S,(ty+40)*S],fill=DARK[s]+(255,),width=2*S); g.line([(tx+40)*S,(ty-40)*S,(tx-40)*S,(ty+40)*S],fill=DARK[s]+(255,),width=2*S)
            E(tx,ty,12,fill=LIGHT[s]+(255,))
        im.alpha_composite(L.resize((W,h),Image.LANCZOS),(0,y0))
    camp(1,*TOP_CAMP,True); camp(0,*BOT_CAMP,False)
    random.setstate(global_rng_state)
    return im
