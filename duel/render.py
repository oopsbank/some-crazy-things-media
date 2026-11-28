import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sim, scene
from sim import R_DOT, HP0
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=sim.simulate(SEED,record=True); F=r['frames']; NF=len(F); EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
SETS=r['sets']
W,H=1080,1920; random.seed(SEED)
RED=(230,60,50); BLUE=(50,120,235); COL=[RED,BLUE]; DARK=[(140,30,25),(25,60,150)]; LIGHT=[(255,150,120),(150,200,255)]
WARNC=[(255,40,40),(30,110,255)]; WEDGE=[(255,60,60),(70,150,255)]; WPULSE=[(255,200,80),(170,220,255)]; NAME=['RED','BLUE']
EL={'fire':((255,120,30),(255,225,130),(120,35,10)),'ice':((110,200,255),(235,250,255),(40,90,170)),
    'lightning':((120,170,255),(255,255,255),(50,70,200)),'poison':((120,220,50),(225,255,160),(40,90,20)),
    'void':((170,70,255),(240,205,255),(55,15,105)),'light':((255,215,80),(255,255,235),(210,150,30)),
    'steel':((215,222,235),(255,255,255),(110,115,130))}
FB='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(s):
    s=max(8,int(s))
    if s not in FC: FC[s]=ImageFont.truetype(FB,s)
    return FC[s]
def ctext(d,cx,y,t,fn,fill,sw=4,sf=(0,0,0)):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=sf)
def paste(dst,src,x,y):
    x,y=int(x),int(y); sw,sh=src.size; x0,y0=max(x,0),max(y,0); x1,y1=min(x+sw,W),min(y+sh,H)
    if x1<=x0 or y1<=y0: return
    dst.alpha_composite(src.crop((x0-x,y0-y,x1-x,y1-y)) if (x0,y0,x1,y1)!=(x,y,x+sw,y+sh) else src,(x0,y0))
def pc(dst,src,cx,cy): paste(dst,src,cx-src.size[0]/2,cy-src.size[1]/2)
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
    alpha=int(max(0,min(255,alpha)))
    if alpha<3 or size<8: return
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
CAMP_Y={1:(30,312),0:(1338,1622)}; GATE={1:(540,265),0:(540,1385)}; HPY={1:318,0:1306}
def ruin(img,s):
    y0,y1=CAMP_Y[s]; reg=np.array(img.crop((0,y0,W,y1))).astype(float)
    rng=np.random.default_rng(11+s)
    n=rng.normal(0,1,((y1-y0)//10+1,W//10+1)); n=np.kron(n,np.ones((10,10)))[:y1-y0,:W]
    reg[...,:3]=reg[...,:3]*0.33+np.array([40,28,20])*0.25+n[...,None]*8
    out=img.copy(); out.paste(Image.fromarray(np.clip(reg,0,255).astype(np.uint8),'RGBA'),(0,y0)); d=ImageDraw.Draw(out)
    for _ in range(70):
        x=rng.uniform(10,W-10); y=rng.uniform(y0+10,y1-10); rr=rng.uniform(5,16)
        pts=[(x+math.cos(a)*rr*rng.uniform(.6,1.2),y+math.sin(a)*rr*rng.uniform(.6,1.2)) for a in np.linspace(0,6.28,6,endpoint=False)]
        d.polygon(pts,fill=tuple(int(v) for v in rng.integers(60,110,3)),outline=(25,22,20))
    for _ in range(14):
        x=rng.uniform(40,W-40); y=rng.uniform(y0+20,y1-20); pts=[(x,y)]
        for k in range(6): x+=rng.uniform(-30,30); y+=rng.uniform(-14,14); pts.append((x,y))
        d.line(pts,fill=(20,16,14),width=3)
    for _ in range(9):
        x=rng.uniform(60,W-60); y=rng.uniform(y0+30,y1-30); pc(out,glow((10,8,6),rng.uniform(140,260),210,1.2),x,y)
    return out
FIRES={s:[(random.uniform(40,W-40),random.uniform(CAMP_Y[s][0]+30,CAMP_Y[s][1]-30)) for _ in range(16)] for s in (0,1)}
win=r['win']; lose=1-win; ENDF=r['endf']
RUIN=ruin(BG,lose)
FEL=sim.ULT[SETS[win][2]]['el']; FNAME=sim.FINAL[FEL]; FSTYLE='meteor' if FEL in ('fire','ice','poison','steel') else 'pillar'
FC1,FC2,FC3=EL[FEL]
DASHEL=[next((sim.NORMAL[n]['el'] for n in SETS[s][:2] if sim.NORMAL[n]['t']=='dash'),'steel') for s in (0,1)]
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
    elif k=='rect': g.rectangle([z['x0']-ox,z['y0']-oy,z['x1']-ox,z['y1']-oy],fill=fill)
def dashed(d,pts,col,width=4,dash=16,gap=10,closed=True,phase=0):
    n=len(pts)
    for i in range(n if closed else n-1):
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
            if (i+int(phase)//6)%2==0: d.line([pts[i],pts[(i+1)%n]],fill=col,width=width)
    elif k=='l':
        a=math.atan2(z['y1']-z['y0'],z['x1']-z['x0']); nx,ny=-math.sin(a)*z['w']/2,math.cos(a)*z['w']/2
        dashed(d,[(z['x0']+nx,z['y0']+ny),(z['x1']+nx,z['y1']+ny),(z['x1']-nx,z['y1']-ny),(z['x0']-nx,z['y0']-ny)],col,width,phase=phase)
    elif k=='cone':
        a0,a1=z['a']-z['h'],z['a']+z['h']; pts=[(z['x'],z['y'])]+[(z['x']+math.cos(a0+(a1-a0)*i/10)*z['r'],z['y']+math.sin(a0+(a1-a0)*i/10)*z['r']) for i in range(11)]
        dashed(d,pts,col,width,phase=phase)
    elif k=='m':
        for s in z['subs']: zoutline(d,s,col,width,phase)
    elif k=='rect': dashed(d,[(z['x0'],z['y0']),(z['x1'],z['y0']),(z['x1'],z['y1']),(z['x0'],z['y1'])],col,width,phase=phase)
def telegraph(im,z,prog,t,big=False,o=0):
    x0,y0,x1,y1=[int(v) for v in zbbox(z)]; x0,y0=max(x0-4,0),max(y0-4,0); x1,y1=min(x1+4,W),min(y1+4,H)
    if x1<=x0 or y1<=y0: return
    m=Image.new('L',(x1-x0,y1-y0),0); zdraw(ImageDraw.Draw(m),z,x0,y0)
    pm=Image.new('L',(x1-x0,y1-y0),0); zdraw(ImageDraw.Draw(pm),z,x0,y0,max(prog,0.001))
    M=np.array(m)>0; P_=np.array(pm)>0; hz=((xx_[y0:y1,x0:x1]+yy_[y0:y1,x0:x1]+int(t*2))//12)%2
    pulse=0.5+0.5*math.sin(t*0.5) if big else 0
    a=M*(50+hz*40+pulse*25)+P_*80
    arr=np.zeros((y1-y0,x1-x0,4),np.uint8); arr[...,0],arr[...,1],arr[...,2]=WARNC[o]; arr[...,3]=np.clip(a,0,255).astype(np.uint8)
    im.alpha_composite(Image.fromarray(arr,'RGBA'),(x0,y0))
    d=ImageDraw.Draw(im); ec=WEDGE[o]; pc_=WPULSE[o]
    zoutline(d,z,ec if not big else tuple(int(ec[j]+(pc_[j]-ec[j])*pulse) for j in range(3)),5 if not big else 7,t*2)
# ---------- world state ----------
parts=[]; fx=[]; pops=[]; decals=[]; banners=[]; shake=[0.0]; flash=[0.0]; dark=[0.0]; pools=[]; G_list=[]
def P(x,y,vx,vy,life,col,size,grav=0.0,kind='dot'): parts.append([x,y,vx,vy,0.0,life,col,size,grav,kind])
def burst(x,y,n,cols,sp=(2,9),life=(12,24),size=(4,9),grav=0.0,up=0.0):
    for _ in range(n):
        a=random.uniform(0,6.283); v=random.uniform(*sp)
        P(x,y,math.cos(a)*v,math.sin(a)*v-up,random.randint(*life),random.choice(cols),random.uniform(*size),grav)
def bolt(d,x0,y0,x1,y1,col,width,seg=10,jit=40):
    pts=[(x0,y0)]
    for k in range(1,seg):
        p=k/seg; pts.append((x0+(x1-x0)*p+random.uniform(-jit,jit),y0+(y1-y0)*p+random.uniform(-jit*0.3,jit*0.3)))
    pts.append((x1,y1)); d.line(pts,fill=col,width=width,joint='curve')
def lerp(a,b,q): return a+(b-a)*q
def falling(im,x,y,q,el,size=1.0,frm=(340,-760)):
    c1,c2,c3=EL[el]; sx,sy=x+frm[0],y+frm[1]; mx,my=sx+(x-sx)*q,sy+(y-sy)*q
    for j in range(7):
        tq=max(0,q-j*0.05); G(im,sx+(x-sx)*tq,sy+(y-sy)*tq,c1,(110-j*10)*size,170-j*20)
    G(im,mx,my,c2,120*size,230); d=ImageDraw.Draw(im); rr=17*size
    if el=='ice': d.polygon([(mx,my-rr*1.8),(mx+rr*0.8,my),(mx,my+rr*1.2),(mx-rr*0.8,my)],fill=(220,245,255),outline=c3)
    elif el=='light': d.ellipse([mx-rr,my-rr,mx+rr,my+rr],fill=(255,255,240),outline=c1,width=3)
    elif el=='poison': d.ellipse([mx-rr,my-rr,mx+rr,my+rr],fill=c1,outline=c3,width=4)
    else: d.ellipse([mx-rr,my-rr,mx+rr,my+rr],fill=(85,45,25),outline=c1,width=4)
    if random.random()<0.8: P(mx,my,random.uniform(-2,2),random.uniform(-3,1),14,random.choice([c1,c2,(120,110,100)]),random.uniform(6,11)*size)
def impact(x,y,el,size=1.0,sh=10):
    c1,c2,c3=EL[el]
    fx.append(dict(k='boom',x=x,y=y,t=0,size=340*size,col=c1)); fx.append(dict(k='ring',x=x,y=y,t=0,col=c2,r=170*size,life=16))
    burst(x,y,int(30*size),[c1,c2,c3,(110,100,90)],(3,13),(14,30),(5,11),0.25); shake[0]=max(shake[0],sh)
    if el=='poison': pools.append([x,y,110*size,0])
    else: decals.append([x,y,90*size,0])
    if el=='lightning': fx.append(dict(k='spark',x=x,y=y,t=0,r=150*size))
    if el=='ice': fx.append(dict(k='spikes',x=x,y=y,t=0,r=120*size))
FX_SND=[]; hist={0:[],1:[]}; ruined=False
def world_event(i):
    # fired exactly once when world time crosses frame i
    global ruined
    if i<NF:
        fr=F[i]
        for e in EV.get(i,[]):
            kd=e[1]
            if kd=='cast':
                if i>=ENDF: continue
                s,slot,nm,el=e[2],e[3],e[4],e[5]
                if slot==2: banners.append([nm,s,0,46,el]); shake[0]=max(shake[0],4)
                else: pops.append([fr['f'][s][0],fr['f'][s][1]-62,nm,COL[s],0,24,(255,255,255)])
            elif kd=='res':
                o,nm,typ,el,z,ex=e[2],e[3],e[4],e[5],e[6],e[7]; c1,c2,c3=EL[el]
                if typ=='cone':
                    fx.append(dict(k='slash',x=z['x'],y=z['y'],a=z['a'],h=z['h'],r=z['r'],el=el,t=0))
                    for _ in range(int(z['r']*z['h']*0.25)):
                        a=z['a']+random.uniform(-z['h'],z['h']); v=random.uniform(4,z['r']/7)
                        P(z['x'],z['y'],math.cos(a)*v,math.sin(a)*v,random.randint(8,14),random.choice([c1,c2]),random.uniform(4,9))
                elif typ=='dash': G_list.append((z['x0'],z['y0'],c1,200,220))
                elif typ in ('circle','rain','ring'): impact(z['x'],z['y'],el,z['r']/110,8 if typ=='circle' else 11)
                elif typ=='nova': fx.append(dict(k='nova',x=z['x'],y=z['y'],r=z['r'],el=el,t=0)); shake[0]=max(shake[0],7)
                elif typ=='fan': G_list.append((ex['x'],ex['y'],c2,160,220))
                elif typ in ('beam','grid'): fx.append(dict(k='beam',z=z,el=el,t=0)); shake[0]=max(shake[0],8 if typ=='beam' else 10)
                elif typ=='cross':
                    fx.append(dict(k='thunder',x=ex['x'],y=ex['y'],t=0,el=el)); flash[0]=max(flash[0],0.55); shake[0]=max(shake[0],16); decals.append([ex['x'],ex['y'],150,0])
                    burst(ex['x'],ex['y'],50,[c1,c2,c3],(4,16),(16,34),(4,10))
                elif typ=='hole':
                    fx.append(dict(k='boom',x=z['x'],y=z['y'],t=0,size=700,col=c1,life=22)); fx.append(dict(k='ring',x=z['x'],y=z['y'],t=0,col=c2,r=320,life=20))
                    burst(z['x'],z['y'],60,[c1,c2,c3,(20,10,30)],(4,18),(16,34),(5,12)); flash[0]=max(flash[0],0.45); shake[0]=max(shake[0],16)
            elif kd=='dash_end':
                c1,c2,c3=EL[e[5]]; fx.append(dict(k='ring',x=e[3],y=e[4],t=0,col=c2,r=110,life=12)); burst(e[3],e[4],22,[c1,c2,(200,190,170)],(3,10)); shake[0]=max(shake[0],7)
            elif kd=='proj_hit':
                c1,c2,c3=EL[e[5]]; burst(e[3],e[4],16,[c1,c2,(255,255,255)],(3,9),(8,16),(3,7))
            elif kd=='hit':
                v,dm,x,y,nm,big=e[2],e[3],e[4],e[5],e[6],e[7]
                pops.append([x,y-34,f'-{dm}',(255,255,255),0,66 if big else 44,COL[v]]); burst(x,y,12,[COL[v],(255,255,255)],(2,7))
            elif kd=='miss': pops.append([e[3],e[4]-40,'DODGE',(255,255,255),0,30,(40,40,40)])
            elif kd=='dash': fx.append(dict(k='dash',x=e[3],y=e[4],a=e[5],t=0)); burst(e[3],e[4],8,[(210,190,150),(235,220,190)],(1,3),(10,18),(5,9))
            elif kd=='ko':
                x,y=e[3],e[4]; fx.append(dict(k='boom',x=x,y=y,t=0,size=420,col=COL[e[2]])); fx.append(dict(k='ring',x=x,y=y,t=0,col=(255,255,255),r=220,life=18))
                burst(x,y,70,[COL[e[2]],(255,255,255),LIGHT[e[2]]],(3,16),(18,40),(5,12)); shake[0]=max(shake[0],18); flash[0]=max(flash[0],0.5)
                banners.append(['K.O.',e[2],0,40,None])
    else:
        k=i-NF; gx,gy=GATE[lose]; y0c,y1c=CAMP_Y[lose]
        if k==30: banners.append(['FINAL SKILL: '+FNAME,win,0,60,FEL]); FX_SND.append((i,'final_cast'))
        if k==60: FX_SND.append((i,'alarm'))
        hitk=112 if FSTYLE=='meteor' else 128
        if FSTYLE=='meteor' and k==96: FX_SND.append((i,'meteor_fall'))
        if FSTYLE=='pillar' and 100<=k<128 and k%4==0: FX_SND.append((i,'thunder'))
        if k==hitk:
            FX_SND.append((i,'mega_boom')); flash[0]=1.0; shake[0]=34; ruined=True
            fx.append(dict(k='boom',x=gx,y=gy,t=0,size=1500,col=FC1,life=40)); fx.append(dict(k='ring',x=gx,y=gy,t=0,col=FC2,r=900,life=30))
            for xx in range(60,W,120): fx.append(dict(k='boom',x=xx,y=random.uniform(y0c+40,y1c-40),t=-random.randint(0,18),size=420,col=(255,140,30),life=26))
            burst(gx,gy,220,[FC1,FC2,FC3,(255,150,40),(90,85,80)],(4,26),(20,50),(6,16),0.3)
        if k==150: FX_SND.append((i,'win'))
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
END=240; TOTAL_W=NF+END
Tw=0.0; speed=1.0; done_idx=-1; VT=[]; vf=0
while Tw<TOTAL_W-1:
    # ---- advance world time; slow motion while an announcement is on screen ----
    target=0.15 if banners else 1.0
    speed+=(target-speed)*0.35; dt=speed
    Tw=min(Tw+dt,TOTAL_W-1); VT.append(Tw)
    while done_idx<int(Tw): done_idx+=1; world_event(done_idx)
    i=min(int(Tw),NF-1); q=Tw-int(Tw); fr=F[i]; fr2=F[min(i+1,NF-1)]; live=Tw<NF; kf=Tw-NF; t=Tw
    im=(RUIN if ruined else BG).copy()
    if dark[0]>0.01: im=Image.blend(im,Image.new('RGBA',(W,H),(5,8,25,255)),dark[0])
    d=ImageDraw.Draw(im)
    for dc in decals:
        dc[3]+=dt; a=int(max(0,200-dc[3]*1.2))
        if a>0: pc(im,glow((25,18,12),dc[2]*2,a,1.3),dc[0],dc[1])
    decals[:]=[dc for dc in decals if dc[3]<170]
    for pl in pools:     # lingering poison puddles
        pl[3]+=dt; a=max(0,1-pl[3]/90)
        G(im,pl[0],pl[1],(90,200,40),pl[2]*2,int(150*a),1.2)
        if random.random()<0.4*a*dt: P(pl[0]+random.uniform(-pl[2],pl[2])*0.6,pl[1]+random.uniform(-pl[2],pl[2])*0.4,0,-1,14,(170,255,110),random.uniform(3,6))
    pools[:]=[p for p in pools if p[3]<90]
    if ruined:
        for (x,y) in FIRES[lose]:
            fl=0.75+0.25*math.sin(t*0.9+x)
            G(im,x,y,(255,120,20),110*fl,170); G(im,x,y-6,(255,220,90),45*fl,230)
            if random.random()<0.5*dt: P(x+random.uniform(-10,10),y,random.uniform(-.5,.5),random.uniform(-3,-1.5),random.randint(16,30),random.choice([(255,150,40),(255,200,80),(90,85,80)]),random.uniform(5,10))
            if random.random()<0.25*dt: P(x,y-20,random.uniform(-.4,.4),random.uniform(-2,-1),40,(70,66,62),random.uniform(10,16),kind='smoke')
    for (x,y,c,s_,a) in G_list: G(im,x,y,c,s_,a)
    G_list.clear()
    # ---- telegraphs (progress interpolated between world frames) ----
    nxt={id(tt[2]):tt[3] for tt in fr2['tele']}
    for (nm,o,z,pg,typ,el) in (fr['tele'] if live else []):
        pg2=nxt.get(id(z),1.0); pgi=lerp(pg,pg2,q) if pg2>=pg else pg
        big=typ in ('rain','cross','ring','grid','hole')
        telegraph(im,z,pgi,t,big=big,o=o)
        if big and z['k'] in ('c','m'):
            cz=z if z['k']=='c' else z['subs'][0]
            ctext(ImageDraw.Draw(im),cz['x'],cz['y']-cz['r']-50,'!',font(46),(255,255,255),6,WARNC[o])
        if typ in ('rain','ring') and pgi>0.6: falling(im,z['x'],z['y'],(pgi-0.6)/0.4,el,1.0 if typ=='rain' else 0.9,(340,-760) if typ=='rain' else (0,-900))
        if typ=='hole':   # swirling vortex while the black hole charges
            c1,c2,c3=EL[el]; G(im,z['x'],z['y'],c1,z['r']*1.6*pgi+60,200); dd=ImageDraw.Draw(im); rr=30+40*pgi
            dd.ellipse([z['x']-rr,z['y']-rr,z['x']+rr,z['y']+rr],fill=(10,0,20),outline=c2,width=4)
            for _ in range(int(4*dt)+1):
                a=random.uniform(0,6.28); R=z['r']*random.uniform(0.6,1.2); px,py=z['x']+math.cos(a)*R,z['y']+math.sin(a)*R
                P(px,py,(-math.cos(a)*0.06-math.sin(a)*0.05)*R,(-math.sin(a)*0.06+math.cos(a)*0.05)*R,12,random.choice([c1,c2,(40,10,70)]),random.uniform(3,7))
    d=ImageDraw.Draw(im)
    # ---- finale (continuous drawing) ----
    if kf>=0:
        wx,wy=F[-1]['f'][win][0],F[-1]['f'][win][1]; gx,gy=GATE[lose]; y0c,y1c=CAMP_Y[lose]
        if 30<=kf<120:
            qq=min(1,(kf-30)/40); G(im,wx,wy,COL[win],160+220*qq,200); G(im,wx,wy,FC2,60+80*qq,220)
            if random.random()<0.9*dt:
                a=random.uniform(0,6.28); rr=random.uniform(80,180); P(wx+math.cos(a)*rr,wy+math.sin(a)*rr,-math.cos(a)*5,-math.sin(a)*5,16,random.choice([COL[win],FC1,FC2]),random.uniform(4,8))
        if 60<=kf<110:
            telegraph(im,dict(k='rect',x0=4,y0=y0c,x1=W-4,y1=y1c),(kf-60)/50,t,big=True,o=win); d=ImageDraw.Draw(im)
            for x in (180,540,900): ctext(d,x,(y0c+y1c)/2-40,'!',font(80),(255,255,255),8,WARNC[win])
        if FSTYLE=='meteor' and 96<=kf<112:
            qq=(kf-96)/16; sx,sy=-300,(-500 if gy<900 else 300); mx,my=sx+(gx-sx)*qq,sy+(gy-sy)*qq
            for j in range(10):
                tq=max(0,qq-j*0.045); G(im,sx+(gx-sx)*tq,sy+(gy-sy)*tq,FC1,330-j*22,190-j*14)
            G(im,mx,my,FC2,360,240); d=ImageDraw.Draw(im)
            if FEL=='ice': d.polygon([(mx,my-110),(mx+52,my),(mx,my+70),(mx-52,my)],fill=(220,245,255),outline=FC3,width=6)
            else: d.ellipse([mx-58,my-58,mx+58,my+58],fill=(85,45,25) if FEL!='poison' else FC1,outline=FC1,width=8)
            for _ in range(int(6*dt)+1): P(mx,my,random.uniform(-6,6),random.uniform(-6,6),20,random.choice([FC1,FC2,(90,80,70)]),random.uniform(8,16))
        if FSTYLE=='pillar':
            if 80<=kf<140: dark[0]=max(dark[0],min(0.55,(kf-80)/30))
            if 100<=kf<128:
                for _ in range(3):
                    tx=random.uniform(30,W-30); ty=random.uniform(y0c+20,y1c-20)
                    bolt(d,tx+random.uniform(-200,200),0,tx,ty,FC1,14,14,50); bolt(d,tx+random.uniform(-200,200),0,tx,ty,FC2,5,14,50)
                    G(im,tx,ty,FC1,260,230); d=ImageDraw.Draw(im); burst(tx,ty,6,[FC1,FC2],(3,10))
                flash[0]=max(flash[0],0.2); shake[0]=max(shake[0],10)
            if 128<=kf<150:
                qq=1-(kf-128)/22; w=int(260*qq+30)
                lay=Image.new('RGBA',(w*2,H),(0,0,0,0)); ImageDraw.Draw(lay).rectangle([w//2,0,w*3//2,gy],fill=FC1+(int(200*qq),))
                paste(im,lay.filter(ImageFilter.GaussianBlur(20)),gx-w,0); d=ImageDraw.Draw(im); d.rectangle([gx-w//4,0,gx+w//4,gy],fill=FC2)
                G(im,gx,gy,FC1,700*qq+200,240)
    # ---- effects ----
    d=ImageDraw.Draw(im)
    for e in fx:
        e['t']+=dt; tt=e['t']
        if tt<=0: continue
        if e['k']=='slash':
            c1,c2,c3=EL[e['el']]; qq=min(1,tt/5); a0=e['a']-e['h']*1.1; a1=a0+e['h']*2.2*qq; fade=max(0,1-(tt-5)/6); R=e['r']*0.82
            for col,wid in ((c1,26),(c2,9)):
                pts=[(e['x']+math.cos(a0+(a1-a0)*j/14)*R,e['y']+math.sin(a0+(a1-a0)*j/14)*R) for j in range(15)]
                if fade>0: d.line(pts,fill=col,width=max(1,int(wid*fade)),joint='curve')
            G(im,e['x']+math.cos(e['a'])*R*0.6,e['y']+math.sin(e['a'])*R*0.6,c1,e['r']*1.5,int(170*fade)); d=ImageDraw.Draw(im)
            e['done']=tt>11
        elif e['k']=='ring':
            life=e['life']; qq=tt/life; rr=e['r']*(0.2+0.8*qq**0.6); a=int(255*max(0,1-qq))
            lay=Image.new('RGBA',(int(rr*2+20),int(rr*2+20)),(0,0,0,0)); ImageDraw.Draw(lay).ellipse([10,10,rr*2+10,rr*2+10],outline=e['col']+(a,),width=max(2,int(14*max(0,1-qq))))
            pc(im,lay,e['x'],e['y']); d=ImageDraw.Draw(im); e['done']=tt>=life
        elif e['k']=='boom':
            life=e.get('life',18); qq=min(1,tt/life); s_=e['size']*(0.4+0.6*min(1,qq*2.5))
            G(im,e['x'],e['y'],e['col'],s_,int(240*(1-qq)),1.5); G(im,e['x'],e['y'],(255,240,200),s_*0.45,int(255*(1-qq)**1.5),1.5); d=ImageDraw.Draw(im)
            e['done']=tt>=life
        elif e['k']=='spark':
            if tt<10:
                for j in range(5):
                    a=random.uniform(0,6.28); rr=e['r']*random.uniform(.5,1)
                    bolt(d,e['x'],e['y'],e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,(170,210,255),5,6,18); bolt(d,e['x'],e['y'],e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,(255,255,255),2,6,18)
            e['done']=tt>=10
        elif e['k']=='spikes':
            qq=min(1,tt/4); fade=max(0,1-(tt-8)/8)
            if fade>0:
                for j in range(10):
                    a=2*math.pi*j/10+0.3; L=e['r']*qq*(0.7+0.3*(j%2)); bx,by=e['x']+math.cos(a)*L,e['y']+math.sin(a)*L
                    nx,ny=-math.sin(a)*12,math.cos(a)*12
                    d.polygon([(e['x']+nx,e['y']+ny),(bx,by),(e['x']-nx,e['y']-ny)],fill=(225,245,255),outline=(90,160,230))
            e['done']=tt>=16
        elif e['k']=='nova':
            c1,c2,c3=EL[e['el']]; qq=min(1,tt/10); rr=e['r']*qq; fade=max(0,1-(tt-6)/10)
            G(im,e['x'],e['y'],c1,rr*2.4,int(190*fade)); d=ImageDraw.Draw(im)
            d.ellipse([e['x']-rr,e['y']-rr,e['x']+rr,e['y']+rr],outline=c2,width=max(2,int(16*fade)))
            if tt<10:
                for j in range(int(8*dt)+1):
                    a=random.uniform(0,6.28); P(e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,math.cos(a)*3,math.sin(a)*3,12,random.choice([c1,c2]),random.uniform(4,8))
                if e['el']=='lightning':
                    for j in range(4):
                        a=random.uniform(0,6.28); bolt(d,e['x'],e['y'],e['x']+math.cos(a)*rr,e['y']+math.sin(a)*rr,(255,255,255),3,6,16)
            e['done']=tt>=16
        elif e['k']=='beam':
            z=e['z']; c1,c2,c3=EL[e['el']]; fade=max(0,1-tt/12); wd=z['w']*(0.6+0.6*fade)
            if fade>0:
                n=int(math.hypot(z['x1']-z['x0'],z['y1']-z['y0'])/70)+1
                for j in range(n+1):
                    G(im,lerp(z['x0'],z['x1'],j/n),lerp(z['y0'],z['y1'],j/n),c1,wd*3,int(170*fade))
                d=ImageDraw.Draw(im); d.line([z['x0'],z['y0'],z['x1'],z['y1']],fill=c1,width=max(2,int(wd))); d.line([z['x0'],z['y0'],z['x1'],z['y1']],fill=c2,width=max(1,int(wd*0.4)))
                for _ in range(int(5*dt)+1):
                    qq=random.random(); P(lerp(z['x0'],z['x1'],qq),lerp(z['y0'],z['y1'],qq),random.uniform(-3,3),random.uniform(-3,3),12,random.choice([c1,c2]),random.uniform(4,8))
            e['done']=tt>=12
        elif e['k']=='thunder':
            qq=tt/20; c1,c2,c3=EL[e['el']]
            if tt<12:
                targets=[(e['x'],e['y'])]+[(e['x']+random.uniform(-180,180),e['y']+random.uniform(-180,180)) for _ in range(2)]+[(random.uniform(60,1020),e['y']) for _ in range(2)]+[(e['x'],random.uniform(380,1300)) for _ in range(2)]
                for (tx,ty) in targets:
                    sx=tx+random.uniform(-150,150); bolt(d,sx,0,tx,ty,c1,16,16,45); bolt(d,sx,0,tx,ty,c2,5,16,45)
                    G(im,tx,ty,c1,200,220); d=ImageDraw.Draw(im)
            G(im,e['x'],e['y'],c1,620,int(220*max(0,1-qq))); d=ImageDraw.Draw(im)
            e['done']=tt>=20
        elif e['k']=='dash':
            qq=min(1,tt/7); a=e['a']
            for off in (-14,0,14):
                nx,ny=-math.sin(a)*off,math.cos(a)*off
                d.line([e['x']+nx,e['y']+ny,e['x']+nx+math.cos(a)*120*qq,e['y']+ny+math.sin(a)*120*qq],fill=(255,255,255),width=max(1,int(4*(1-qq))))
            e['done']=tt>=7
    fx[:]=[e for e in fx if not e.get('done')]
    # ---- projectiles ----
    for (px,py,a,el,sz,o) in (fr['proj'] if live else []):
        c1,c2,c3=EL[el]; px+=math.cos(a)*27*q; py+=math.sin(a)*27*q
        for j in range(4): G(im,px-math.cos(a)*j*14,py-math.sin(a)*j*14,c1,sz*5-j*8,190-j*40)
        d=ImageDraw.Draw(im)
        if el=='ice': d.polygon([(px+math.cos(a)*sz*1.8,py+math.sin(a)*sz*1.8),(px-math.sin(a)*sz*0.6,py+math.cos(a)*sz*0.6),(px-math.cos(a)*sz,py-math.sin(a)*sz),(px+math.sin(a)*sz*0.6,py-math.cos(a)*sz*0.6)],fill=(225,245,255),outline=c3)
        else: d.ellipse([px-sz*0.7,py-sz*0.7,px+sz*0.7,py+sz*0.7],fill=c2,outline=c1,width=3)
        if random.random()<0.6*dt: P(px,py,random.uniform(-1,1),random.uniform(-1,1),10,random.choice([c1,c2]),sz*0.5)
    # ---- fighters ----
    if live or kf<4:
        for s in (0,1):
            x,y,hp,st,fl,aura=fr['f'][s]; x,y=lerp(x,fr2['f'][s][0],q),lerp(y,fr2['f'][s][1],q)
            if hp<=0 and Tw>=ENDF: continue
            hist[s].append((x,y,st)); hist[s]=hist[s][-8:]
            for j,(hx,hy,hs) in enumerate(hist[s][:-1]):
                if hs in ('dash','charge'): pc(im,GHOST[s][min(4,j*5//8)],hx,hy)
            if st=='charge':
                c1,c2,c3=EL[DASHEL[s]]
                for _ in range(int(4*dt)+1): P(x+random.uniform(-8,8),y+random.uniform(-8,8),random.uniform(-1.5,1.5),random.uniform(-1.5,1.5),14,random.choice([c1,c2]),random.uniform(6,12))
                G(im,x,y,c1,120,200)
            if aura>0:
                ue=EL[sim.ULT[SETS[s][2]]['el']]
                G(im,x,y,ue[0],200+40*math.sin(t*0.6),210)
                if random.random()<dt: P(x+random.uniform(-30,30),y+random.uniform(-10,20),0,random.uniform(-4,-2),18,random.choice([COL[s],ue[0],ue[1]]),random.uniform(3,6))
            pc(im,SHADOW,x+3,y+R_DOT+2); pc(im,DOTW if fl>0 and fl%2==0 else DOT[s],x,y)
            d=ImageDraw.Draw(im)
            d.rounded_rectangle([x-26,y-34,x+26,y-27],radius=3,fill=(0,0,0)); d.rounded_rectangle([x-25,y-33,x-25+50*hp/HP0,y-28],radius=2,fill=COL[s])
    else:
        x,y=F[-1]['f'][win][0],F[-1]['f'][win][1]; pc(im,SHADOW,x+3,y+R_DOT+2); pc(im,DOT[win],x,y)
    # ---- particles ----
    d=ImageDraw.Draw(im)
    for p in parts:
        p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[3]+=p[8]*dt; p[4]+=dt
        qq=p[4]/p[5]
        if p[9]=='smoke':
            sz=p[7]*(1+qq); d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[6])
        else:
            sz=p[7]*(1-qq)
            if sz>0.5: d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[6])
    parts[:]=[p for p in parts if p[4]<p[5]]
    # ---- HP bars at the gates ----
    if live or kf<60:
        for s in (0,1):
            hp=fr['f'][s][2]; cx,yb=540,HPY[s]; w=120
            d.rounded_rectangle([cx-w,yb,cx+w,yb+24],radius=12,fill=(0,0,0),outline=(255,255,255),width=2)
            if hp>0: d.rounded_rectangle([cx-w+4,yb+4,cx-w+4+(2*w-8)*hp/HP0,yb+20],radius=8,fill=COL[s])
            ctext(d,cx,yb-1,f'{int(hp)}',font(21),(255,255,255),3)
    # ---- damage popups (world time) ----
    for p in pops:
        p[4]+=dt; yy=p[1]-max(0,p[4])*1.6; sc=1+0.4*max(0,1-p[4]/5) if p[4]>=0 else 1.5
        if p[4]>=-6: ctext(d,p[0],yy,p[2],font(p[5]*sc),p[3],5,p[6])
    pops[:]=[p for p in pops if p[4]<30]
    # ---- announcements (real time; the world is slowed while they show) ----
    for b in banners:
        b[2]+=1; qb=b[2]; L=b[3]; s=b[1]
        if b[0]=='K.O.':
            sc=1+0.8*max(0,1-qb/6)
            if qb<L: ctext(d,W/2,780,'K.O.',font(190*sc),(255,255,255),12,(0,0,0))
            continue
        slide=min(1,qb/6); out=max(0,(qb-(L-8))/8); x_off=(1-slide)*W*(-1 if s==0 else 1)+out*W*(1 if s==0 else -1)
        lay=Image.new('RGBA',(W,150),(0,0,0,0)); g=ImageDraw.Draw(lay); ec=EL[b[4]][0] if b[4] else COL[s]
        g.polygon([(0,20),(W,0),(W,130),(0,150)],fill=(10,10,14,225)); g.polygon([(0,20),(W,0),(W,10),(0,30)],fill=COL[s]+(255,)); g.polygon([(0,140),(W,120),(W,130),(0,150)],fill=ec+(255,))
        fn=font(70 if len(b[0])<14 else (56 if len(b[0])<22 else (44 if len(b[0])<30 else 38))); tw=g.textlength(b[0],font=fn)
        g.text(((W-tw)/2,40),b[0],font=fn,fill=(255,255,255),stroke_width=5,stroke_fill=COL[s])
        paste(im,lay,x_off,825); d=ImageDraw.Draw(im)
    banners[:]=[b for b in banners if b[2]<b[3]]
    if Tw<sim.INTRO+15:
        if Tw<sim.INTRO-10:
            ctext(d,W/2,780,'RED',font(130),RED,8); ctext(d,W/2,915,'VS',font(80),(255,255,255),6); ctext(d,W/2,1000,'BLUE',font(130),BLUE,8)
        elif Tw>=sim.INTRO-8:
            sc=1+0.6*max(0,1-(Tw-sim.INTRO+8)/6); ctext(d,W/2,880,'FIGHT!',font(140*sc),(255,230,80),9)
            if not any(x[1]=='fight' for x in FX_SND): FX_SND.append((Tw,'fight'))
    if kf>=150:
        qq=min(1,(kf-150)/8); ctext(d,W/2,820,f'{NAME[win]} WINS!',font(130*(2-qq)),(255,255,255),10,DARK[win])
        if kf>=158: ctext(d,W/2,975,'BASE DESTROYED',font(58),(255,220,80),6)
    out=im.convert('RGB')
    if dark[0]>0.01 and (kf<0 or kf>=140): dark[0]*=0.93**dt
    if shake[0]>0.5:
        dx,dy=int(random.uniform(-1,1)*shake[0]),int(random.uniform(-1,1)*shake[0])
        sh=Image.new('RGB',(W,H)); sh.paste(out,(dx,dy)); out=sh; shake[0]*=0.86**max(dt,0.3)
    if flash[0]>0.02:
        out=Image.blend(out,Image.new('RGB',(W,H),(255,255,255)),min(1,flash[0])); flash[0]*=0.72**max(dt,0.3)
    proc.stdin.write(out.tobytes()); vf+=1
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],n=NF,end=END,win=win,extra=FX_SND,vt=VT,sets=SETS),open(OUT+'.json','w')); print('done',vf,'frames',SETS)
