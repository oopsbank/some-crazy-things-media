# Crisp vector art for the two big blobs, plus pixel masks used by the sim for touch tests.
import math
import numpy as np
from PIL import Image, ImageDraw
AR=1.3          # height/width of both big shapes (same for fairness)
def tear(m, n=900, wob=0.0, wobk=5, lean=0.0):
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        y=-math.cos(t); f=(1-y)/2          # f=1 at the tip, 0 at the bottom
        x=math.sin(t)*abs(math.sin(t/2))**m
        x*=1+wob*math.sin(wobk*t)*f
        x+=lean*f*f
        pts.append((x,y))
    mx=max(abs(p[0]) for p in pts)
    return [(x/mx,y) for x,y in pts]
def grad(w,h,top,bot):
    g=np.linspace(0,1,h)[:,None,None]; a=np.array(top)[None,None,:]*(1-g)+np.array(bot)[None,None,:]*g
    return Image.fromarray(np.repeat(a,w,axis=1).astype(np.uint8),'RGB')
def layer(img,pts,box,top,bot):
    x0,y0,x1,y1=box; w,h=x1-x0,y1-y0
    poly=[(x0+(x+1)/2*w,y0+(y+1)/2*h) for x,y in pts]
    m=Image.new('L',img.size,0); ImageDraw.Draw(m).polygon(poly,fill=255)
    img.paste(grad(img.size[0],img.size[1],top,bot),(0,0),m)
def water(M):
    Hh=int(M*AR); img=Image.new('RGBA',(M,Hh),(0,0,0,0)); base=Image.new('RGB',(M,Hh))
    pts=tear(1.6)
    m=Image.new('L',(M,Hh),0); ImageDraw.Draw(m).polygon([((x+1)/2*M,(y+1)/2*Hh) for x,y in pts],fill=255)
    rim=int(M*0.035)
    layer(base,pts,(0,0,M,Hh),(40,110,220),(20,60,170))
    layer(base,pts,(rim,rim*1.6,M-rim,Hh-rim),(120,205,255),(40,130,235))
    d=ImageDraw.Draw(base)
    d.ellipse([M*0.20,Hh*0.45,M*0.32,Hh*0.70],fill=(200,235,255))
    img.paste(base,(0,0),m); return img
def fire(M):
    Hh=int(M*AR); img=Image.new('RGBA',(M,Hh),(0,0,0,0)); base=Image.new('RGB',(M,Hh))
    outer=tear(0.85,wob=0.20,wobk=6,lean=0.10)
    m=Image.new('L',(M,Hh),0); ImageDraw.Draw(m).polygon([((x+1)/2*M,(y+1)/2*Hh) for x,y in outer],fill=255)
    rim=int(M*0.03)
    layer(base,outer,(0,0,M,Hh),(170,20,10),(200,40,10))
    layer(base,outer,(rim,rim*1.6,M-rim,Hh-rim),(235,50,25),(255,110,20))
    mid=tear(1.0,wob=0.14,wobk=5,lean=-0.08)
    layer(base,mid,(M*0.16,Hh*0.30,M*0.84,Hh-rim*2),(255,120,20),(255,175,40))
    inn=tear(1.3,wob=0.08,wobk=4,lean=0.05)
    layer(base,inn,(M*0.30,Hh*0.56,M*0.70,Hh-rim*3),(255,215,60),(255,245,190))
    img.paste(base,(0,0),m); return img
def radial(M,cx,cy,r,inner,outer):
    yy,xx=np.mgrid[0:M,0:M]; t=np.clip(np.sqrt((xx-cx)**2+(yy-cy)**2)/r,0,1)[...,None]
    return Image.fromarray((np.array(inner)*(1-t)+np.array(outer)*t).astype(np.uint8),'RGB')
def sun(M):
    img=Image.new('RGBA',(M,M),(0,0,0,0)); c=M/2
    m=Image.new('L',(M,M),0); md=ImageDraw.Draw(m)
    n=12
    for i in range(n):   # rays
        a=2*math.pi*i/n; w=math.pi/n*0.55
        md.polygon([(c+math.cos(a-w)*M*0.34,c+math.sin(a-w)*M*0.34),(c+math.cos(a)*M*0.5,c+math.sin(a)*M*0.5),(c+math.cos(a+w)*M*0.34,c+math.sin(a+w)*M*0.34)],fill=255)
    img.paste(radial(M,c,c,M*0.5,(255,235,80),(255,150,20)),(0,0),m)
    r=M*0.40; m2=Image.new('L',(M,M),0); ImageDraw.Draw(m2).ellipse([c-r,c-r,c+r,c+r],fill=255)
    img.paste(radial(M,c,c,r,(255,140,10),(230,90,0)),(0,0),m2)
    r2=r*0.92; m3=Image.new('L',(M,M),0); ImageDraw.Draw(m3).ellipse([c-r2,c-r2,c+r2,c+r2],fill=255)
    img.paste(radial(M,c-r*0.25,c-r*0.3,r*1.6,(255,250,170),(255,175,30)),(0,0),m3)
    return img
def moon(M):
    img=Image.new('RGBA',(M,M),(0,0,0,0)); c=M/2; r=M*0.47
    m=Image.new('L',(M,M),0); ImageDraw.Draw(m).ellipse([c-r,c-r,c+r,c+r],fill=255)
    img.paste(radial(M,c,c,r,(110,80,200),(70,40,150)),(0,0),m)          # rim
    r2=r*0.93; m2=Image.new('L',(M,M),0); ImageDraw.Draw(m2).ellipse([c-r2,c-r2,c+r2,c+r2],fill=255)
    img.paste(radial(M,c-r*0.3,c-r*0.3,r*1.7,(245,240,255),(170,150,235)),(0,0),m2)
    # crescent shadow on the right side
    m3=Image.new('L',(M,M),0); ImageDraw.Draw(m3).ellipse([c-r2+r*0.55,c-r2-r*0.1,c+r2+r*0.55,c+r2-r*0.1],fill=150)
    m3=Image.fromarray(np.minimum(np.array(m3),np.array(m2)))
    img.paste(Image.new('RGB',(M,M),(90,70,170)),(0,0),m3)
    d=ImageDraw.Draw(img)
    for (fx,fy,fr) in ((-0.35,-0.15,0.13),(-0.05,0.35,0.10),(-0.45,0.30,0.07),(0.05,-0.40,0.08),(-0.15,0.05,0.06)):
        x,y,rr=c+fx*r,c+fy*r,fr*r; d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=(190,175,235,255),outline=(150,130,215,255),width=max(2,int(M*0.006)))
    return img
THEMES={'fire':(fire,water,1.3),'sun':(sun,moon,1.0)}
ART=[fire,water]
_cache={}
def set_theme(name):
    global AR,ART
    a,b,AR=THEMES[name]; ART=[a,b]; _cache.clear(); _mask.clear()
def masters():
    if 'm' not in _cache:
        out=[]
        for fn in ART:
            big=fn(1600) if fn in (fire,water) else fn(1400); mips=[big]
            while mips[-1].size[0]>120: mips.append(mips[-1].resize((mips[-1].size[0]//2,mips[-1].size[1]//2),Image.LANCZOS))
            out.append(mips)
        _cache['m']=out
    return _cache['m']
def sprite(s,width):
    mips=masters()[s]; src=mips[0]
    for im in mips:
        if im.size[0]>=width: src=im
    w=max(int(width),2); h=max(int(width*AR),2)
    return src.resize((w,h),Image.LANCZOS if w<src.size[0] else Image.BICUBIC)
_mask={}
def mask(s):
    if s not in _mask:
        im=ART[s](400); _mask[s]=np.array(im.split()[3])>40
    return _mask[s]
