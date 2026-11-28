import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import sim, shapes
from sim import ROWS, LANES, CARW, CX, BOT, TOPWIN, rad, box, SPLIT_ROW
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=sim.simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920
random.seed(SEED)
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    sz=int(sz)
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); return im.crop(im.getbbox())
def eyes(im):
    im=im.copy(); d=ImageDraw.Draw(im); w,h=im.size; cy=h*0.62
    for ex in (w*0.36,w*0.64):
        d.ellipse([ex-w*.11,cy-h*.11,ex+w*.11,cy+h*.11],fill='white'); d.ellipse([ex-w*.05,cy-h*.02,ex+w*.05,cy+h*.09],fill='black')
    return im
BIG0=[emoji('🔥'),emoji('💧')]
SMALL=[eyes(BIG0[0]).resize((54,58),Image.LANCZOS),eyes(BIG0[1]).resize((50,58),Image.LANCZOS)]
CARS=[emoji(c) for c in '🚗🚕🚙🚌🚓']
def carimg(k,d):
    im=CARS[k%len(CARS)]; im=im.resize((CARW,int(CARW*im.size[1]/im.size[0])),Image.LANCZOS)
    return ImageOps.mirror(im) if d>0 else im
CI={(k,d):carimg(k,d) for k in range(5) for d in (-1,1)}
OR=(255,140,40); BL=(70,170,255); NAME=['FIRE','WATER']; COL=[OR,BL]
TC={1:(110,110,125),2:(50,130,230),3:(40,175,110),5:(160,80,230),20:(235,60,60),100:(255,190,0)}
INTRO=45; END=80

def paste(dst,src,x,y):
    x,y=int(x),int(y); sw,sh=src.size
    x0,y0=max(x,0),max(y,0); x1,y1=min(x+sw,W),min(y+sh,H)
    if x1<=x0 or y1<=y0: return
    dst.alpha_composite(src.crop((x0-x,y0-y,x1-x,y1-y)) if (x0,y0,x1,y1)!=(x,y,x+sw,y+sh) else src,(x0,y0))
def ctext(d,cx,y,t,fn,fill,sw=4,sf=(0,0,0)):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=sf)
def glow(col,n=256):
    yy,xx=np.mgrid[-1:1:n*1j,-1:1:n*1j]; rr=np.sqrt(xx**2+yy**2)
    a=np.clip(1-rr,0,1)**2*170
    arr=np.zeros((n,n,4),np.uint8); arr[...,0],arr[...,1],arr[...,2]=col; arr[...,3]=a.astype(np.uint8)
    return Image.fromarray(arr,'RGBA')
GLOW=[glow(OR),glow(BL)]
SHADOW=Image.new('RGBA',(80,24),(0,0,0,0)); ImageDraw.Draw(SHADOW).ellipse([0,0,79,23],fill=(0,0,0,90)); SHADOW=SHADOW.filter(ImageFilter.GaussianBlur(3))
CSHADOW=Image.new('RGBA',(CARW+20,34),(0,0,0,0)); ImageDraw.Draw(CSHADOW).ellipse([0,0,CARW+19,33],fill=(0,0,0,110)); CSHADOW=CSHADOW.filter(ImageFilter.GaussianBlur(5))

# ---------- static background ----------
rng=np.random.default_rng(3)
def tex(h,base,amp):
    a=np.clip(np.array(base)[None,None,:]+rng.normal(0,amp,(h,W,1)),0,255).astype(np.uint8); return Image.fromarray(a,'RGB').convert('RGBA')
bg=Image.new('RGBA',(W,H),(0,0,0,255))
hud=np.zeros((190,W,3)); hud[:]=np.linspace(8,26,190)[:,None,None]; bg.paste(Image.fromarray(hud.astype(np.uint8),'RGB'),(0,0))
for row in range(10):
    y=ROWS[row]; top=y-40
    if row in LANES: bg.paste(tex(80,(48,49,56),6),(0,top))
    elif row in (0,8): bg.paste(tex(80,(160,158,150),5),(0,top))
    else: bg.paste(tex(80,(56,130,62),9),(0,top))
d=ImageDraw.Draw(bg)
for row in (0,8):
    for x in range(0,W,90): d.line([x,ROWS[row]-40,x,ROWS[row]+40],fill=(135,133,126),width=2)
for row in (3,4,5):
    for _ in range(140):
        x=rng.uniform(0,W); y=rng.uniform(ROWS[row]-38,ROWS[row]+38); d.line([x,y,x+rng.uniform(-3,3),y-rng.uniform(5,11)],fill=(80,165,80),width=2)
d.rectangle([0,ROWS[SPLIT_ROW]-3,W,ROWS[SPLIT_ROW]+3],fill=(255,230,120))
for a,b in ((1,2),(6,7)):
    y=ROWS[a]+40
    for x in range(0,W,90): d.rounded_rectangle([x,y-4,x+50,y+4],radius=3,fill=(235,235,230))
    for yy in (ROWS[a]-40,ROWS[b]+36): d.rectangle([0,yy,W,yy+4],fill=(250,205,0))
for x in range(0,W,40):
    for yy in (0,1):
        d.rectangle([x,ROWS[9]-40+yy*40,x+40,ROWS[9]+yy*40],fill=(240,240,240) if (x//40+yy)%2 else (22,22,22))
ar=np.zeros((H-990,W,3)); g=np.linspace(0,1,H-990)[:,None]
ar[...,0]=14+10*g; ar[...,1]=22+18*g; ar[...,2]=30+22*g
bg.paste(Image.fromarray(ar.astype(np.uint8),'RGB'),(0,990))
for x in range(0,W,60): d.line([x,990,x,H],fill=(32,46,58),width=1)
for y in range(990,H,60): d.line([0,y,W,y],fill=(32,46,58),width=1)
d.rectangle([0,986,W,994],fill=(10,10,14))
f1=font(66); P=[('FIRE',OR),(' vs ',(230,230,230)),('WATER',BL)]
tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
for p,c in P: d.text((x,28),p,font=f1,fill=c,stroke_width=3,stroke_fill=(0,0,0)); x+=d.textlength(p,font=f1)

proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
pops=[]; parts=[]; rings=[]
total=INTRO+len(F)+END; win=r['win']; lose=1-win
BADGE={}
def badge(m):
    if m not in BADGE:
        fn=font(26); t=f'x{m}'; tw=int(ImageDraw.Draw(Image.new('RGBA',(1,1))).textlength(t,font=fn))
        im=Image.new('RGBA',(tw+22,36),(0,0,0,0)); dd=ImageDraw.Draw(im)
        dd.rounded_rectangle([1,1,tw+20,34],radius=12,fill=TC[m]+(255,),outline=(255,255,255),width=2)
        dd.text((11,2),t,font=fn,fill=(255,255,255),stroke_width=2,stroke_fill=(0,0,0)); BADGE[m]=im
    return BADGE[m]
def ease(x): x=min(max(x,0),1); return x*x*(3-2*x)
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; live=INTRO<=t<INTRO+len(F); ending=t>=INTRO+len(F); fidx=t-INTRO; k=t-(INTRO+len(F))
    im=bg.copy(); d=ImageDraw.Draw(im)
    for l,(dd_,sp) in LANES.items():
        for j,cx in enumerate(fr['cars'][l]):
            ci=CI[((l+j)%5,dd_)]
            paste(im,CSHADOW,cx-CARW/2-10,ROWS[l]+ci.size[1]/2-22)
            paste(im,ci,cx-CARW/2,ROWS[l]-ci.size[1]/2)
    if live:
        for e in EV.get(fidx,[]):
            if e[1]=='splat':
                s,x0,y0,v=e[2],e[3],e[4],e[5]
                for _ in range(16):
                    a=random.uniform(0,6.28); vv=random.uniform(2,9)
                    parts.append([x0,y0,math.cos(a)*vv,math.sin(a)*vv-(3 if s==0 else 0),(120,120,120) if s==0 else BL,0,'puff' if s==0 else 'drop'])
                pops.append([x0,y0-50,f'-{v}',(255,80,80),0,44 if v<1000 else 60])
            if e[1]=='spawn':
                pops.append([e[4],ROWS[SPLIT_ROW]-60,'+2',COL[e[2]],0,52])
                rings.append([e[4],ROWS[SPLIT_ROW],0,COL[e[2]]])
            if e[1]=='fizzle':
                for _ in range(10): parts.append([e[4],e[5],random.uniform(-2,2),random.uniform(-6,-2),(230,230,230),0,'steam'])
                pops.append([e[4],e[5]-50,f'-{e[3]}',(200,200,200),0,40])
            if e[1]=='eat':
                if e[3]>=250: pops.append([e[4],e[5]-50,f'+{e[3]}',COL[e[2]],0,50 if e[3]<1000 else 66])
                rings.append([e[4],e[5],0,COL[e[2]]])
            if e[1]=='feed':
                bx_,by_,bw_,bh_=box(e[2],fr['big'][e[2]]); pops.append([min(max(CX[e[2]],90),W-90),min(max(by_+bh_*0.35,240),H-200),f'+{e[3]}',COL[e[2]],0,50 if e[3]<1000 else 70])
    order=(0,1) if fr['big'][0]>fr['big'][1] else (1,0)   # bigger behind, smaller in front
    labels=[]
    for s in order:
        v=fr['big'][s]; rr=rad(v)
        if ending:
            if s==lose:
                rr*=max(0,1-k/20)
                if k<20:
                    for _ in range(6): parts.append([CX[s]+random.uniform(-rr,rr),BOT-random.uniform(0,2*rr*shapes.AR),random.uniform(-1,1),random.uniform(-7,-3),(230,230,230),0,'steam'])
            else: rr=rr+(1500-rr)*ease((k-4)/30)
        if rr<4: continue
        w2=2*rr; h2=w2*shapes.AR; top=BOT-h2
        gs=int(max(w2,h2)*1.5); paste(im,GLOW[s].resize((gs,gs),Image.BILINEAR),CX[s]-gs/2,BOT-h2/2-gs/2)
        if top<H and CX[s]-rr<W:
            # only resize the visible part when the sprite is huge
            spr=shapes.sprite(s,w2) if w2<2600 else shapes.sprite(s,2600).resize((int(w2),int(h2)),Image.BILINEAR)
            paste(im,spr,CX[s]-rr,top)
        if not ending: labels.append((s,v,rr,top,h2))
    for (s,v,rr,top,h2) in labels:
        fn=font(max(46,min(110,rr*0.3))); txt=str(int(v)); tw_=d.textlength(txt,font=fn)
        lx=min(max(CX[s],tw_/2+20),W-tw_/2-20); ly=min(max(BOT-h2*0.32,250),H-fn.size-40)
        ctext(d,lx,ly,txt,fn,(255,255,255),6,tuple(int(c*0.35) for c in COL[s]))
    for (s,x0,row,hop,v,m) in fr['ch'] if not ending else []:
        p=(8-hop)/8 if hop>0 else 0; yy=ROWS[row]+80*p-math.sin(math.pi*p)*26
        sc=1+0.12*math.log10(m) if m>1 else 1
        img=SMALL[s] if sc==1 else SMALL[s].resize((int(SMALL[s].size[0]*sc),int(SMALL[s].size[1]*sc)))
        paste(im,SHADOW.resize((int(50*sc),14)),x0-25*sc,ROWS[row]+80*p+18)
        paste(im,img,x0-img.size[0]/2,yy-img.size[1]/2)
        bd=badge(m); paste(im,bd,x0-bd.size[0]/2,yy-img.size[1]/2-38)
    for (s,x0,y0,v,kk) in fr['fly'] if not ending else []:
        ty=BOT-rad(fr['big'][s])*shapes.AR; p=kk/14; bx=x0+(CX[s]-x0)*p; by=y0+(ty-y0)*p-math.sin(math.pi*p)*120
        paste(im,SMALL[s],bx-27,by-29)
    for rg in rings:
        rg[2]+=1; rr=10+rg[2]*5; a=max(0,220-rg[2]*16)
        d.ellipse([rg[0]-rr,rg[1]-rr*0.6,rg[0]+rr,rg[1]+rr*0.6],outline=rg[3]+(a,),width=5)
    rings[:]=[rg for rg in rings if rg[2]<14]
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[5]+=1
        if p[6]=='drop': p[3]+=0.6
        sz=9 if p[6]=='drop' else 7+p[5]*0.5; a=max(0,230-p[5]*10)
        d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[4]+(a,))
    parts[:]=[p for p in parts if p[5]<22]
    for p in pops:
        p[4]+=1; ctext(d,p[0],p[1]-p[4]*2,p[2],font(p[5]),p[3],4)
    pops[:]=[p for p in pops if p[4]<26]
    if not ending:
        for x in range(0,W,40): d.line([x,TOPWIN,x+22,TOPWIN],fill=(255,255,255),width=4)
    b0,b1=fr['big']; frac=b0/(b0+b1) if b0+b1>0 else .5
    if ending: frac=frac+((1.0 if win==0 else 0.0)-frac)*ease(k/20)
    bx0,bx1,by0,by1=60,W-60,118,160; mid=bx0+(bx1-bx0)*frac
    d.rounded_rectangle([bx0-4,by0-4,bx1+4,by1+4],radius=24,fill=(0,0,0))
    if mid>bx0+2: d.rounded_rectangle([bx0,by0,mid,by1],radius=20,fill=OR)
    if mid<bx1-2: d.rounded_rectangle([mid,by0,bx1,by1],radius=20,fill=BL)
    d.rectangle([mid-3,by0-8,mid+3,by1+8],fill=(255,255,255))
    fn=font(30); d.text((bx0+14,by0+3),str(int(b0)),font=fn,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    tt=str(int(b1)); d.text((bx1-14-d.textlength(tt,font=fn),by0+3),tt,font=fn,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    if t<INTRO:
        d.rounded_rectangle([60,1130,W-60,1330],radius=30,fill=(0,0,0,210)); ctext(d,W/2,1150,'FIRST TO FILL',font(70),(255,255,255)); ctext(d,W/2,1240,'THE SCREEN WINS',font(66),(255,220,0))
    if ending and k>=18:
        sc=1+0.25*max(0,1-(k-18)/8)
        ctext(d,W/2,860,f'{NAME[win]} WINS!',font(120*sc),(255,255,255),10,tuple(int(c*0.45) for c in COL[win]))
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=win),open(OUT+'.json','w')); print('done',total)
