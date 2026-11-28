import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sim, scene
from sim import R_DOT, NAMES, HP0
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=sim.simulate(SEED,record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920; random.seed(SEED)
RED=(230,60,50); BLUE=(50,120,235); COL=[RED,BLUE]; DARK=[(140,30,25),(25,60,150)]; LIGHT=[(255,150,120),(150,200,255)]
WARN=(255,40,40); NAME=['RED','BLUE']
FINAL=['INFERNO APOCALYPSE',"HEAVEN'S WRATH"]
FB='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(s):
    s=int(s)
    if s not in FC: FC[s]=ImageFont.truetype(FB,s)
    return FC[s]
def ctext(d,cx,y,t,fn,fill,sw=4,sf=(0,0,0)):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=sf)
def paste(dst,src,x,y):
    x,y=int(x),int(y); sw,sh=src.size; x0,y0=max(x,0),max(y,0); x1,y1=min(x+sw,W),min(y+sh,H)
    if x1<=x0 or y1<=y0: return
    dst.alpha_composite(src.crop((x0-x,y0-y,x1-x,y1-y)) if (x0,y0,x1,y1)!=(x,y,x+sw,y+sh) else src,(x0,y0))
def pc(dst,src,cx,cy): paste(dst,src,cx-src.size[0]/2,cy-src.size[1]/2)
# ---------- cached sprites ----------
GL={}
def glow(col,size,alpha=200,power=2.0):
    size=max(8,int(size)//8*8); key=(col,size,alpha,power)
    if key not in GL:
        yy,xx=np.mgrid[-1:1:size*1j,-1:1:size*1j]; a=np.clip(1-np.sqrt(xx**2+yy**2),0,1)**power*alpha
        arr=np.zeros((size,size,4),np.uint8); arr[...,0],arr[...,1],arr[...,2]=col; arr[...,3]=a.astype(np.uint8)
        GL[key]=Image.fromarray(arr,'RGBA')
    return GL[key]
GA={}
def G(im,cx,cy,col,size,alpha=200,power=2.0):
    # additive light: brightens what is underneath instead of painting over it
    g=glow(col,size,alpha,power); key=(col,g.size[0],alpha,power)
    if key not in GA: GA[key]=(np.asarray(g)[...,3:4].astype(np.float32)/255*np.array(col,np.float32)).astype(np.int16)
    A=GA[key]; sw=A.shape[1]; x,y=int(cx-sw/2),int(cy-sw/2)
    x0,y0,x1,y1=max(x,0),max(y,0),min(x+sw,W),min(y+sw,H)
    if x1<=x0 or y1<=y0: return
    reg=np.asarray(im.crop((x0,y0,x1,y1))).astype(np.int16)
    reg[...,:3]+=A[y0-y:y1-y,x0-x:x1-x]; im.paste(Image.fromarray(np.clip(reg,0,255).astype(np.uint8),'RGBA'),(x0,y0))
def dot(col,r=R_DOT,alpha=255):
    S=4; w=int(r*2+6); L=Image.new('RGBA',(w*S,w*S),(0,0,0,0)); g=ImageDraw.Draw(L); c=w*S/2; R=r*S
    g.ellipse([c-R,c-R,c+R,c+R],fill=col+(alpha,),outline=(0,0,0,alpha),width=int(R*0.2))
    return L.resize((w,w),Image.LANCZOS)
DOT=[dot(RED),dot(BLUE)]; DOTW=dot((255,255,255)); GHOST=[[dot(c,alpha=a) for a in (40,70,100,130,160)] for c in (RED,BLUE)]
SHADOW=Image.new('RGBA',(40,14),(0,0,0,0)); ImageDraw.Draw(SHADOW).ellipse([0,0,39,13],fill=(0,0,0,80)); SHADOW=SHADOW.filter(ImageFilter.GaussianBlur(2))
yy_,xx_=np.mgrid[0:H,0:W]
# ---------- background, camps, ruins ----------
BG=scene.build_bg()
CAMP_Y={1:(30,312),0:(1338,1622)}           # whole camp area (incl. gate forecourt) per side
GATE={1:(540,265),0:(540,1385)}
HPY={1:318,0:1306}
def ruin(img,s):
    y0,y1=CAMP_Y[s]; reg=np.array(img.crop((0,y0,W,y1))).astype(float)
    rng=np.random.default_rng(11+s)
    n=rng.normal(0,1,((y1-y0)//10+1,W//10+1)); n=np.kron(n,np.ones((10,10)))[:y1-y0,:W]
    reg[...,:3]=reg[...,:3]*0.33+np.array([40,28,20])*0.25+n[...,None]*8
    out=img.copy(); out.paste(Image.fromarray(np.clip(reg,0,255).astype(np.uint8),'RGBA'),(0,y0)); d=ImageDraw.Draw(out)
    for _ in range(70):   # rubble
        x=rng.uniform(10,W-10); y=rng.uniform(y0+10,y1-10); rr=rng.uniform(5,16)
        pts=[(x+math.cos(a)*rr*rng.uniform(.6,1.2),y+math.sin(a)*rr*rng.uniform(.6,1.2)) for a in np.linspace(0,6.28,6,endpoint=False)]
        d.polygon(pts,fill=tuple(int(v) for v in rng.integers(60,110,3)),outline=(25,22,20))
    for _ in range(14):   # cracks
        x=rng.uniform(40,W-40); y=rng.uniform(y0+20,y1-20); pts=[(x,y)]
        for k in range(6): x+=rng.uniform(-30,30); y+=rng.uniform(-14,14); pts.append((x,y))
        d.line(pts,fill=(20,16,14),width=3)
    for _ in range(9):    # scorch
        x=rng.uniform(60,W-60); y=rng.uniform(y0+30,y1-30); pc(out,glow((10,8,6),rng.uniform(140,260),210,1.2),x,y)
    return out
FIRES={s:[(random.uniform(40,W-40),random.uniform(CAMP_Y[s][0]+30,CAMP_Y[s][1]-30)) for _ in range(16)] for s in (0,1)}
win=r['win']; lose=1-win; ENDF=r['endf']
RUIN=ruin(BG,lose)
HATCH=(((xx_+yy_)//12)%2).astype(np.uint8)
# ---------- telegraph drawing ----------
def zbbox(z):
    k=z['k']
    if k=='c': return z['x']-z['r'],z['y']-z['r'],z['x']+z['r'],z['y']+z['r']
    if k=='l': w=z['w']/2; return min(z['x0'],z['x1'])-w,min(z['y0'],z['y1'])-w,max(z['x0'],z['x1'])+w,max(z['y0'],z['y1'])+w
    if k=='cone': return z['x']-z['r'],z['y']-z['r'],z['x']+z['r'],z['y']+z['r']
    if k=='m':
        bs=[zbbox(s) for s in z['subs']]; return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)
    if k=='rect': return z['x0'],z['y0'],z['x1'],z['y1']
def zdraw(g,z,ox,oy,prog=1.0,fill=255):
    k=z['k']
    if k=='c':
        rr=z['r']*prog; g.ellipse([z['x']-rr-ox,z['y']-rr-oy,z['x']+rr-ox,z['y']+rr-oy],fill=fill)
    elif k=='l':
        a=math.atan2(z['y1']-z['y0'],z['x1']-z['x0']); nx,ny=-math.sin(a)*z['w']/2,math.cos(a)*z['w']/2
        x1=z['x0']+(z['x1']-z['x0'])*prog; y1=z['y0']+(z['y1']-z['y0'])*prog
        g.polygon([(z['x0']+nx-ox,z['y0']+ny-oy),(x1+nx-ox,y1+ny-oy),(x1-nx-ox,y1-ny-oy),(z['x0']-nx-ox,z['y0']-ny-oy)],fill=fill)
    elif k=='cone':
        rr=z['r']*prog; a0,a1=math.degrees(z['a']-z['h']),math.degrees(z['a']+z['h'])
        g.pieslice([z['x']-rr-ox,z['y']-rr-oy,z['x']+rr-ox,z['y']+rr-oy],a0,a1,fill=fill)
    elif k=='m':
        for s in z['subs']: zdraw(g,s,ox,oy,prog,fill)
    elif k=='rect':
        g.rectangle([z['x0']-ox,z['y0']-oy,z['x1']-ox,z['y1']-oy],fill=fill)
def dashed(d,pts,col,width=4,dash=16,gap=10,closed=True,phase=0):
    n=len(pts); rng_=range(n if closed else n-1)
    for i in rng_:
        (x0,y0),(x1,y1)=pts[i],pts[(i+1)%n]; L=math.hypot(x1-x0,y1-y0) or 1; t=-phase%(dash+gap)-(dash+gap)
        while t<L:
            a=max(t,0)/L; b=min(t+dash,L)/L
            if b>a: d.line([x0+(x1-x0)*a,y0+(y1-y0)*a,x0+(x1-x0)*b,y0+(y1-y0)*b],fill=col,width=width)
            t+=dash+gap
def zoutline(d,z,col,width,phase):
    k=z['k']
    if k=='c':
        n=max(12,int(2*math.pi*z['r']/26)); pts=[(z['x']+math.cos(2*math.pi*i/n)*z['r'],z['y']+math.sin(2*math.pi*i/n)*z['r']) for i in range(n)]
        for i in range(n):
            if (i+phase//6)%2==0: d.line([pts[i],pts[(i+1)%n]],fill=col,width=width)
    elif k=='l':
        a=math.atan2(z['y1']-z['y0'],z['x1']-z['x0']); nx,ny=-math.sin(a)*z['w']/2,math.cos(a)*z['w']/2
        dashed(d,[(z['x0']+nx,z['y0']+ny),(z['x1']+nx,z['y1']+ny),(z['x1']-nx,z['y1']-ny),(z['x0']-nx,z['y0']-ny)],col,width,phase=phase)
    elif k=='cone':
        a0,a1=z['a']-z['h'],z['a']+z['h']; pts=[(z['x'],z['y'])]+[(z['x']+math.cos(a0+(a1-a0)*i/10)*z['r'],z['y']+math.sin(a0+(a1-a0)*i/10)*z['r']) for i in range(11)]
        dashed(d,pts,col,width,phase=phase)
    elif k=='m':
        for s in z['subs']: zoutline(d,s,col,width,phase)
    elif k=='rect':
        dashed(d,[(z['x0'],z['y0']),(z['x1'],z['y0']),(z['x1'],z['y1']),(z['x0'],z['y1'])],col,width,phase=phase)
def telegraph(im,z,prog,t,big=False):
    x0,y0,x1,y1=[int(v) for v in zbbox(z)]; x0,y0=max(x0-4,0),max(y0-4,0); x1,y1=min(x1+4,W),min(y1+4,H)
    if x1<=x0 or y1<=y0: return
    m=Image.new('L',(x1-x0,y1-y0),0); zdraw(ImageDraw.Draw(m),z,x0,y0)
    pm=Image.new('L',(x1-x0,y1-y0),0); zdraw(ImageDraw.Draw(pm),z,x0,y0,max(prog,0.001))
    M=np.array(m)>0; P=np.array(pm)>0; hz=((xx_[y0:y1,x0:x1]+yy_[y0:y1,x0:x1]+t*2)//12)%2
    pulse=0.5+0.5*math.sin(t*0.5) if big else 0
    a=M*(50+hz*40+pulse*25)+P*80
    arr=np.zeros((y1-y0,x1-x0,4),np.uint8); arr[...,0],arr[...,1],arr[...,2]=WARN; arr[...,3]=np.clip(a,0,255).astype(np.uint8)
    im.alpha_composite(Image.fromarray(arr,'RGBA'),(x0,y0))
    d=ImageDraw.Draw(im); zoutline(d,z,(255,60,60) if not big else (255,int(120+100*pulse),80),5 if not big else 7,t*2)
# ---------- state ----------
parts=[]; fx=[]; pops=[]; decals=[]; banners=[]; shake=[0.0]; flash=[0.0]; dark=[0.0]
def P(x,y,vx,vy,life,col,size,grav=0.0,kind='dot'): parts.append([x,y,vx,vy,0,life,col,size,grav,kind])
def burst(x,y,n,cols,sp=(2,9),life=(12,24),size=(4,9),grav=0.0,up=0.0):
    for _ in range(n):
        a=random.uniform(0,6.283); v=random.uniform(*sp)
        P(x,y,math.cos(a)*v,math.sin(a)*v-up,random.randint(*life),random.choice(cols),random.uniform(*size),grav)
def bolt(d,x0,y0,x1,y1,col,width,seg=10,jit=40):
    pts=[(x0,y0)]
    for k in range(1,seg):
        p=k/seg; pts.append((x0+(x1-x0)*p+random.uniform(-jit,jit),y0+(y1-y0)*p+random.uniform(-jit*0.3,jit*0.3)))
    pts.append((x1,y1)); d.line(pts,fill=col,width=width,joint='curve'); return pts
FX_SND=[]   # extra sound cues created by the scripted finale
hist={0:[],1:[]}
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
END=240; total=len(F)+END
ruined=False
for t in range(total):
    i=min(t,len(F)-1); fr=F[i]; live=t<len(F); k=t-len(F)   # k>=0: finale
    im=(RUIN if ruined else BG).copy(); d=ImageDraw.Draw(im)
    # decals (scorch marks)
    for dc in decals:
        dc[3]+=1; a=int(max(0,200-dc[3]*1.2))
        if a>0: pc(im,glow((25,18,12),dc[2]*2,a,1.3),dc[0],dc[1])
    decals[:]=[dc for dc in decals if dc[3]<170]
    # fires on the ruins
    if ruined:
        for (x,y) in FIRES[lose]:
            fl=0.75+0.25*math.sin(t*0.9+x)
            G(im,x,y,(255,120,20),110*fl,170); G(im,x,y-6,(255,220,90),45*fl,230)
            if random.random()<0.5: P(x+random.uniform(-10,10),y,random.uniform(-.5,.5),random.uniform(-3,-1.5),random.randint(16,30),random.choice([(255,150,40),(255,200,80),(90,85,80)]),random.uniform(5,10))
            if random.random()<0.25: P(x,y-20,random.uniform(-.4,.4),random.uniform(-2,-1),40,(70,66,62),random.uniform(10,16),kind='smoke')
    # telegraphs
    for (sk,o,z,pg) in (fr['tele'] if live else []):
        telegraph(im,z,pg,t,big=sk in ('METEOR','THUNDER'))
        if sk in ('METEOR','THUNDER') and z['k'] in ('c','m'):
            cz=z if z['k']=='c' else z['subs'][0]
            ctext(d:=ImageDraw.Draw(im),cz['x'],cz['y']-cz['r']-50,'!',font(46),(255,255,255),6,WARN)
        # falling meteor in the last part of its telegraph
        if sk=='METEOR' and pg>0.6:
            q=(pg-0.6)/0.4; sx,sy=z['x']+340,z['y']-760; mx,my=sx+(z['x']-sx)*q,sy+(z['y']-sy)*q
            for j in range(7):
                tq=max(0,q-j*0.05); tx,ty=sx+(z['x']-sx)*tq,sy+(z['y']-sy)*tq
                G(im,tx,ty,(255,110,20),110-j*10,170-j*18)
            G(im,mx,my,(255,200,80),120,230); d=ImageDraw.Draw(im); d.ellipse([mx-17,my-17,mx+17,my+17],fill=(85,45,25),outline=(255,150,40),width=4); G(im,mx,my,(255,200,90),70,200)
            if random.random()<0.8: P(mx,my,random.uniform(-2,2),random.uniform(-3,1),14,random.choice([(255,160,40),(255,90,20),(120,110,100)]),random.uniform(6,11))
    d=ImageDraw.Draw(im)
    # events of this frame
    if live:
        for e in EV.get(t,[]):
            kd=e[1]
            if kd=='cast' and t>=ENDF: continue
            if kd=='cast':
                s,sk,nm=e[2],e[3],e[4]
                if sk==2:
                    banners.append([nm,s,0,48]); shake[0]=max(shake[0],4)
                else: pops.append([fr['f'][s][0],fr['f'][s][1]-60,nm,COL[s],0,24,(255,255,255)])
            elif kd=='slash':
                fx.append(dict(k='slash',x=e[3],y=e[4],a=e[5],t=0)); burst(e[3]+math.cos(e[5])*90,e[4]+math.sin(e[5])*90,14,[(255,255,255),(255,120,90)],(3,9))
            elif kd=='charge': fx.append(dict(k='chargeflash',x=e[3],y=e[4],t=0))
            elif kd=='charge_end':
                fx.append(dict(k='ring',x=e[3],y=e[4],t=0,col=(255,120,60),r=110,life=12)); burst(e[3],e[4],22,[(255,160,40),(255,80,30),(200,190,170)],(3,10)); shake[0]=max(shake[0],7)
            elif kd=='meteor':
                x,y=e[3],e[4]; fx.append(dict(k='boom',x=x,y=y,t=0,size=360,col=(255,120,30))); fx.append(dict(k='ring',x=x,y=y,t=0,col=(255,200,120),r=175,life=16))
                burst(x,y,34,[(255,170,50),(255,90,20),(255,230,140),(110,100,90)],(3,13),(14,30),(5,11),0.25); decals.append([x,y,90,0]); shake[0]=max(shake[0],11)
            elif kd=='shards': G(im,e[3],e[4],(150,220,255),160,220)
            elif kd=='shard_hit': burst(e[3],e[4],16,[(200,240,255),(255,255,255),(120,190,255)],(3,9),(8,16),(3,7))
            elif kd=='shock':
                x,y=e[3],e[4]; fx.append(dict(k='shock',x=x,y=y,t=0)); burst(x,y,26,[(180,230,255),(255,255,255),(90,160,255)],(4,12)); shake[0]=max(shake[0],8)
            elif kd=='thunder':
                x,y=e[3],e[4]; fx.append(dict(k='thunder',x=x,y=y,t=0)); flash[0]=max(flash[0],0.55); shake[0]=max(shake[0],16); decals.append([x,y,150,0])
                burst(x,y,50,[(200,235,255),(255,255,255),(80,150,255)],(4,16),(16,34),(4,10))
            elif kd=='hit':
                v,dm,x,y,src=e[2],e[3],e[4],e[5],e[6]; big=src in ('METEOR','THUNDER','CHARGE')
                pops.append([x,y-34,f'-{dm}',(255,255,255),0,66 if big else 44,COL[v]]); burst(x,y,12,[COL[v],(255,255,255)],(2,7))
            elif kd=='miss': pops.append([e[3],e[4]-40,'DODGE',(255,255,255),0,30,(40,40,40)])
            elif kd=='dash':
                fx.append(dict(k='dash',x=e[3],y=e[4],a=e[5],t=0,s=e[2])); burst(e[3],e[4],8,[(210,190,150),(235,220,190)],(1,3),(10,18),(5,9))
            elif kd=='ko':
                x,y=e[3],e[4]; fx.append(dict(k='boom',x=x,y=y,t=0,size=420,col=COL[e[2]])); fx.append(dict(k='ring',x=x,y=y,t=0,col=(255,255,255),r=220,life=18))
                burst(x,y,70,[COL[e[2]],(255,255,255),LIGHT[e[2]]],(3,16),(18,40),(5,12)); shake[0]=max(shake[0],18); flash[0]=max(flash[0],0.5)
    # ---------- finale: skill 4 destroys the enemy base ----------
    if k>=0:
        wx,wy=F[-1]['f'][win][0],F[-1]['f'][win][1]
        gx,gy=GATE[lose]; y0c,y1c=CAMP_Y[lose]
        if k==5: pops.append([W/2,860,'K.O.',(255,255,255),-12,150,(0,0,0)])
        if k==40: banners.append(['FINAL SKILL: '+FINAL[win],win,0,60]); FX_SND.append((t,'final_cast'))
        if 40<=k<120:   # winner charges up
            q=min(1,(k-40)/40); G(im,wx,wy,COL[win],160+220*q,200); G(im,wx,wy,(255,255,255),60+80*q,220)
            if random.random()<0.9:
                a=random.uniform(0,6.28); rr=random.uniform(80,180); P(wx+math.cos(a)*rr,wy+math.sin(a)*rr,-math.cos(a)*5,-math.sin(a)*5,16,random.choice([COL[win],LIGHT[win],(255,255,255)]),random.uniform(4,8))
        if 60<=k<110:   # huge warning over the whole enemy camp
            telegraph(im,dict(k='rect',x0=4,y0=y0c,x1=W-4,y1=y1c),(k-60)/50,t,big=True); d=ImageDraw.Draw(im)
            for x in (180,540,900): ctext(d,x,(y0c+y1c)/2-40,'!',font(80),(255,255,255),8,WARN)
            if k==60: FX_SND.append((t,'alarm'))
        if win==0:      # INFERNO APOCALYPSE: a giant meteor crashes into the blue camp
            if 96<=k<112:
                q=(k-96)/16; sx,sy=-300,-500; mx,my=sx+(gx-sx)*q,sy+(gy-sy)*q
                for j in range(10):
                    tq=max(0,q-j*0.045); G(im,sx+(gx-sx)*tq,sy+(gy-sy)*tq,(255,100,20),330-j*22,190-j*14)
                G(im,mx,my,(255,210,90),360,240); d=ImageDraw.Draw(im); d.ellipse([mx-58,my-58,mx+58,my+58],fill=(85,45,25),outline=(255,150,40),width=8); d.ellipse([mx-30,my-40,mx+6,my-4],fill=(130,70,35)); G(im,mx,my,(255,200,90),200,200)
                for _ in range(6): P(mx,my,random.uniform(-6,6),random.uniform(-6,6),20,random.choice([(255,160,40),(255,90,20),(90,80,70)]),random.uniform(8,16))
                if k==96: FX_SND.append((t,'meteor_fall'))
            if k==112:
                FX_SND.append((t,'mega_boom')); flash[0]=1.0; shake[0]=34; ruined=True
                fx.append(dict(k='boom',x=gx,y=gy,t=0,size=1500,col=(255,120,20),life=40)); fx.append(dict(k='ring',x=gx,y=gy,t=0,col=(255,220,150),r=900,life=30))
                for xx in range(60,W,120): fx.append(dict(k='boom',x=xx,y=random.uniform(y0c+40,y1c-40),t=-random.randint(0,18),size=420,col=(255,140,30),life=26))
                burst(gx,gy,220,[(255,170,50),(255,90,20),(255,230,140),(110,100,90),(60,55,50)],(4,26),(20,50),(6,16),0.3)
        else:           # HEAVEN'S WRATH: lightning storm + a giant pillar on the red camp
            if 80<=k<140: dark[0]=max(dark[0],min(0.55,(k-80)/30))
            if 100<=k<128:
                for _ in range(3):
                    tx=random.uniform(30,W-30); ty=random.uniform(y0c+20,y1c-20)
                    bolt(d,tx+random.uniform(-200,200),0,tx,ty,(120,180,255),14,14,50); bolt(d,tx+random.uniform(-200,200),0,tx,ty,(255,255,255),5,14,50)
                    G(im,tx,ty,(150,200,255),260,230); d=ImageDraw.Draw(im); burst(tx,ty,6,[(200,235,255),(255,255,255)],(3,10))
                flash[0]=max(flash[0],0.2); shake[0]=max(shake[0],10)
                if k%4==0: FX_SND.append((t,'thunder'))
            if 128<=k<150:
                q=1-(k-128)/22; w=int(260*q+30)
                lay=Image.new('RGBA',(w*2,H),(0,0,0,0)); ImageDraw.Draw(lay).rectangle([w//2,0,w*3//2,gy],fill=(150,210,255,int(200*q)))
                paste(im,lay.filter(ImageFilter.GaussianBlur(20)),gx-w,0); d=ImageDraw.Draw(im); d.rectangle([gx-w//4,0,gx+w//4,gy],fill=(255,255,255))
                G(im,gx,gy,(150,210,255),700*q+200,240)
            if k==128:
                FX_SND.append((t,'mega_boom')); flash[0]=1.0; shake[0]=34; ruined=True
                fx.append(dict(k='boom',x=gx,y=gy,t=0,size=1500,col=(110,170,255),life=40)); fx.append(dict(k='ring',x=gx,y=gy,t=0,col=(220,240,255),r=900,life=30))
                for xx in range(60,W,120): fx.append(dict(k='boom',x=xx,y=random.uniform(y0c+40,y1c-40),t=-random.randint(0,18),size=420,col=(255,140,30),life=26))
                burst(gx,gy,220,[(200,235,255),(255,255,255),(80,150,255),(255,150,40),(90,85,80)],(4,26),(20,50),(6,16),0.3)
    # ---------- effects ----------
    d=ImageDraw.Draw(im)
    for e in fx:
        e['t']+=1; tt=e['t']
        if tt<=0: continue
        if e['k']=='slash':
            q=min(1,tt/5); a0=e['a']-math.radians(60); a1=a0+math.radians(120)*q; fade=max(0,1-(tt-5)/6)
            for rad_,col,wid in ((150,(255,120,90),26),(150,(255,240,230),9)):
                pts=[(e['x']+math.cos(a0+(a1-a0)*j/14)*rad_,e['y']+math.sin(a0+(a1-a0)*j/14)*rad_) for j in range(15)]
                if fade>0: d.line(pts,fill=col,width=max(1,int(wid*fade)),joint='curve')
            G(im,e['x']+math.cos(e['a'])*100,e['y']+math.sin(e['a'])*100,(255,150,120),260,int(150*fade)); d=ImageDraw.Draw(im)
            e['done']=tt>11
        elif e['k']=='chargeflash':
            G(im,e['x'],e['y'],(255,150,60),220,int(220*max(0,1-tt/8))); e['done']=tt>8
        elif e['k']=='ring':
            life=e['life']; q=tt/life; rr=e['r']*(0.2+0.8*q**0.6); a=int(255*(1-q))
            lay=Image.new('RGBA',(int(rr*2+20),int(rr*2+20)),(0,0,0,0)); ImageDraw.Draw(lay).ellipse([10,10,rr*2+10,rr*2+10],outline=e['col']+(a,),width=max(2,int(14*(1-q))))
            pc(im,lay,e['x'],e['y']); d=ImageDraw.Draw(im); e['done']=tt>=life
        elif e['k']=='boom':
            life=e.get('life',18); q=tt/life; s=e['size']*(0.4+0.6*min(1,q*2.5))
            G(im,e['x'],e['y'],e['col'],s,int(240*(1-q)),1.5); G(im,e['x'],e['y'],(255,240,200),s*0.45,int(255*(1-q)**1.5),1.5); d=ImageDraw.Draw(im)
            e['done']=tt>=life
        elif e['k']=='shock':
            q=tt/14; rr=150*min(1,q*1.6)
            G(im,e['x'],e['y'],(120,190,255),rr*2.6,int(200*(1-q))); d=ImageDraw.Draw(im)
            d.ellipse([e['x']-rr,e['y']-rr,e['x']+rr,e['y']+rr],outline=(220,240,255),width=max(2,int(10*(1-q))))
            if tt<10:
                for j in range(6):
                    a=random.uniform(0,6.28); bolt(d,e['x'],e['y'],e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,(170,220,255),5,6,18); bolt(d,e['x'],e['y'],e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,(255,255,255),2,6,18)
            e['done']=tt>=14
        elif e['k']=='thunder':
            q=tt/20
            if tt<12:
                targets=[(e['x'],e['y'])]+[(e['x']+random.uniform(-180,180),e['y']+random.uniform(-180,180)) for _ in range(2)]+[(random.uniform(60,1020),e['y']) for _ in range(2)]+[(e['x'],random.uniform(380,1300)) for _ in range(2)]
                for (tx,ty) in targets:
                    sx=tx+random.uniform(-150,150); bolt(d,sx,0,tx,ty,(110,170,255),16,16,45); bolt(d,sx,0,tx,ty,(255,255,255),5,16,45)
                    G(im,tx,ty,(150,200,255),200,220); d=ImageDraw.Draw(im)
            G(im,e['x'],e['y'],(120,180,255),620,int(220*(1-q))); d=ImageDraw.Draw(im)
            e['done']=tt>=20
        elif e['k']=='dash':
            q=tt/7; a=e['a']
            for off in (-14,0,14):
                nx,ny=-math.sin(a)*off,math.cos(a)*off
                d.line([e['x']+nx,e['y']+ny,e['x']+nx+math.cos(a)*120*q,e['y']+ny+math.sin(a)*120*q],fill=(255,255,255),width=max(1,int(4*(1-q))))
            e['done']=tt>=7
    fx[:]=[e for e in fx if not e.get('done')]
    # ---------- fighters ----------
    if live or k<4:
        for s in (0,1):
            x,y,hp,st,fl,cds,aura=fr['f'][s]
            if hp<=0 and not live: continue
            if hp<=0 and t>ENDF: continue
            hist[s].append((x,y,st)); hist[s]=hist[s][-8:]
            for j,(hx,hy,hs) in enumerate(hist[s][:-1]):
                if hs in ('dash','charge'): pc(im,GHOST[s][min(4,j*5//8)],hx,hy)
            if st=='charge':
                for _ in range(4): P(x+random.uniform(-8,8),y+random.uniform(-8,8),random.uniform(-1.5,1.5),random.uniform(-1.5,1.5),14,random.choice([(255,160,40),(255,80,20),(255,220,120)]),random.uniform(6,12))
                G(im,x,y,(255,120,40),120,200)
            if aura>0:
                G(im,x,y,COL[s],200+40*math.sin(t*0.6),210)
                for _ in range(2): P(x+random.uniform(-30,30),y+random.uniform(-10,20),0,random.uniform(-4,-2),18,random.choice([COL[s],LIGHT[s],(255,255,255)]),random.uniform(3,6))
            pc(im,SHADOW,x+3,y+R_DOT+2); pc(im,DOTW if fl>0 and fl%2==0 else DOT[s],x,y)
            d=ImageDraw.Draw(im)
            d.rounded_rectangle([x-26,y-34,x+26,y-27],radius=3,fill=(0,0,0)); d.rounded_rectangle([x-25,y-33,x-25+50*hp/HP0,y-28],radius=2,fill=COL[s])
    else:
        x,y=F[-1]['f'][win][0],F[-1]['f'][win][1]; pc(im,SHADOW,x+3,y+R_DOT+2); pc(im,DOT[win],x,y)
    # ---------- particles ----------
    d=ImageDraw.Draw(im)
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[3]+=p[8]; p[4]+=1
        q=p[4]/p[5]
        if p[9]=='smoke':
            sz=p[7]*(1+q); d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[6])
        else:
            sz=p[7]*(1-q)
            if sz>0.5: d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[6])
    parts[:]=[p for p in parts if p[4]<p[5]]
    # ---------- HP bars at the gates (compact) ----------
    if live or k<60:
        for s in (0,1):
            hp=fr['f'][s][2]; cx,yb=540,HPY[s]; w=120
            d.rounded_rectangle([cx-w,yb,cx+w,yb+24],radius=12,fill=(0,0,0),outline=(255,255,255),width=2)
            if hp>0: d.rounded_rectangle([cx-w+4,yb+4,cx-w+4+(2*w-8)*hp/HP0,yb+20],radius=8,fill=COL[s])
            ctext(d,cx,yb-1,f'{int(hp)}',font(21),(255,255,255),3)
    # ---------- popups / banners / texts ----------
    for p in pops:
        p[4]+=1; yy=p[1]-max(0,p[4])*1.6; sc=1+0.4*max(0,1-p[4]/5) if p[4]>=0 else 1.5
        if p[4]>=-6: ctext(d,p[0],yy,p[2],font(p[5]*sc),p[3],5,p[6])
    pops[:]=[p for p in pops if p[4]<30]
    for b in banners:
        b[2]+=1; q=b[2]; L=b[3]; s=b[1]
        slide=min(1,q/6); out=max(0,(q-(L-8))/8); x_off=(1-slide)*W*(-1 if s==0 else 1)+out*W*(1 if s==0 else -1)
        by=900; lay=Image.new('RGBA',(W,150),(0,0,0,0)); g=ImageDraw.Draw(lay)
        g.polygon([(0,20),(W,0),(W,130),(0,150)],fill=(10,10,14,225)); g.polygon([(0,20),(W,0),(W,10),(0,30)],fill=COL[s]+(255,)); g.polygon([(0,140),(W,120),(W,130),(0,150)],fill=COL[s]+(255,))
        fn=font(70 if len(b[0])<14 else (58 if len(b[0])<22 else 46)); tw=g.textlength(b[0],font=fn)
        g.text(((W-tw)/2,40),b[0],font=fn,fill=(255,255,255),stroke_width=5,stroke_fill=COL[s])
        paste(im,lay,x_off,by-75); d=ImageDraw.Draw(im)
    banners[:]=[b for b in banners if b[2]<b[3]]
    if t<sim.INTRO+15:
        if t<sim.INTRO-10:
            ctext(d,W/2,780,'RED',font(130),RED,8); ctext(d,W/2,915,'VS',font(80),(255,255,255),6); ctext(d,W/2,1000,'BLUE',font(130),BLUE,8)
        elif t>=sim.INTRO-8:
            sc=1+0.6*max(0,1-(t-sim.INTRO+8)/6); ctext(d,W/2,880,'FIGHT!',font(140*sc),(255,230,80),9)
            if t==sim.INTRO-8: FX_SND.append((t,'fight'))
    if k>=150:
        q=min(1,(k-150)/8); ctext(d,W/2,820,f'{NAME[win]} WINS!',font(130*(2-q)),(255,255,255),10,DARK[win])
        if k>=158: ctext(d,W/2,975,'BASE DESTROYED',font(58),(255,220,80),6)
        if k==150: FX_SND.append((t,'win'))
    # ---------- camera: darken, shake, flash ----------
    out=im.convert('RGB')
    if dark[0]>0.01:
        out=Image.blend(out,Image.new('RGB',(W,H),(5,8,25)),dark[0]); dark[0]*=0.9 if k<0 or k>=140 else 1.0
    if shake[0]>0.5:
        dx,dy=int(random.uniform(-1,1)*shake[0]),int(random.uniform(-1,1)*shake[0])
        sh=Image.new('RGB',(W,H)); sh.paste(out,(dx,dy)); out=sh; shake[0]*=0.86
    if flash[0]>0.02:
        out=Image.blend(out,Image.new('RGB',(W,H),(255,255,255)),min(1,flash[0])); flash[0]*=0.72
    proc.stdin.write(out.tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],n=len(F),end=END,win=win,extra=FX_SND),open(OUT+'.json','w')); print('done',total)
