import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageChops
from sim5 import simulate, AX0,AY0,AX1,AY1,R,CD,DIG_R,WHIRL_R,TIMBER_WARN,TIMBER_W,TIMBER_FALL
from pixelart import pixel_sprite
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=simulate(SEED, record=True); F=r['frames']
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
BASE={'a':pixel_sprite('\U0001FA8F'),'b':pixel_sprite('\U0001FA93')}; EC={}
def emo(side,size,rot=0):
    size=int(size)//2*2; rot=int(rot)%360//15*15
    k=(side,size,rot)
    if k not in EC:
        im=BASE[side].resize((size,size),Image.NEAREST)
        EC[k]=im.rotate(rot,resample=Image.NEAREST,expand=False) if rot else im
    return EC[k]
SC_=(150,195,230); XC=(240,85,60)
DIRT=(150,100,55); DIRT2=(205,160,100); WIND=(140,215,255); LEAF=(70,180,80); TRUNK=(120,75,35); RED=(255,60,60)
NAMES={'dig':'DIG!','bury':'BURY!','whirl':'WHIRLWIND!','timber':'TIMBER!'}
SKCOL={'dig':DIRT2,'bury':DIRT,'whirl':WIND,'timber':LEAF}
A_SK=('dig','bury'); B_SK=('whirl','timber'); ULTS=('bury','timber'); FREEZE=16
INTRO=30; END=70
pops=[]; flashes=[]; parts=[]; blasts=[]; fxp=[]; logs=[]; holes=[]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill,**kw):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,**kw)
ARENA=Image.new('L',(1080,1920),0); ImageDraw.Draw(ARENA).rectangle([AX0,AY0,AX1,AY1],fill=255)
def put(lay,ov):   # composite an effect layer clipped to the arena
    ov.putalpha(ImageChops.multiply(ov.getchannel('A'),ARENA)); lay.alpha_composite(ov)
def overlay(): ov=Image.new('RGBA',(W,H),(0,0,0,0)); return ov,ImageDraw.Draw(ov)
def burst(x,y,n,cols,vmin,vmax,life=(6,11)):
    for _ in range(n):
        g=random.uniform(0,6.28); v=random.uniform(vmin,vmax); fxp.append([x,y,math.cos(g)*v,math.sin(g)*v,random.choice(cols),0,random.randint(*life)])
def hpbar(ld,cx,cy,hp,col,t,rr=None):
    rr=rr or R; w=150; hp=max(hp,0); y=cy+rr+14
    if y+22>AY1-2: y=cy-rr-36
    c=col if hp>=25 else ((255,60,60) if (t//4)%2 else (255,150,150))
    ld.rounded_rectangle([cx-w/2-5,y-5,cx+w/2+5,y+23],radius=10,fill=(0,0,0,220),outline=(255,255,255,240),width=3)
    if hp>0: ld.rounded_rectangle([cx-w/2,y,cx-w/2+max(10,w*hp/100),y+18],radius=7,fill=c+(255,))
def band(od,seg,w,fill):
    x0,y0,x1,y1=seg; L=math.hypot(x1-x0,y1-y0) or 1; nx,ny=-(y1-y0)/L*w/2,(x1-x0)/L*w/2
    od.polygon([(x0+nx,y0+ny),(x1+nx,y1+ny),(x1-nx,y1-ny),(x0-nx,y0-ny)],fill=fill)
TL=[]; START=[]
for i,fr_ in enumerate(F):
    u=[c for c in fr_['casts'] if c in ULTS]
    if u: TL+=[(i,u[0],k) for k in range(FREEZE)]
    START.append(len(TL)); TL.append((i,None,0))
N=len(TL); total=INTRO+N+END; loser='b' if r['win']=='a' else 'a'
shake=[0.0]; flash=[0,(255,255,255)]
for t in range(total):
    ti=min(max(t-INTRO,0),N-1); i,fz,fk=TL[ti]; fr=F[i]; ending=t>=INTRO+N; live=INTRO<=t<INTRO+N and fz is None; frozen=INTRO<=t<INTRO+N and fz is not None
    im=Image.new('RGBA',(W,H),(0,0,0,255)); d=ImageDraw.Draw(im)
    f1=font(64); P=[('SHOVEL',SC_),(' vs ',(230,230,230)),('AXE',XC)]
    tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
    for p,c in P: d.text((x,190),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
    d.rectangle([AX0-6,AY0-6,AX1+6,AY1+6],outline=(150,150,150),width=6)
    ax,ay,ahp=fr['a']; bx,by,bhp=fr['b']
    if live:
        for c in fr['casts']:
            fx,fy=(ax,ay) if c in A_SK else (bx,by)
            flashes.append([c,fx,fy,SKCOL[c],0])
            if c in ULTS: shake[0]=max(shake[0],26); flash[:]=[170,(255,255,255)]
        for (tg,dm,k) in fr['hits']:
            px,py=(ax,ay) if tg=='a' else (bx,by)
            col={'dig':DIRT2,'bury':DIRT2,'whirl':WIND,'timber':LEAF,'bump':(255,255,255)}[k]
            if k=='whirl': burst(px,py,6,[WIND,(255,255,255)],3,9)
            if k=='timber': flash[:]=[110,LEAF]
            pops.append([px+random.uniform(-30,30),py-70,f'-{dm}',col,0,72 if k=='timber' else (40 if k=='bury' else 52)])
        if fr['popup']:
            px,py=fr['popup']; blasts.append([px,py,0]); shake[0]=max(shake[0],14); burst(px,py,40,[DIRT,DIRT2,(255,230,170)],5,20)
        if fr['dig']: burst(ax+random.uniform(-20,20),ay+R*.5,3,[DIRT,DIRT2],4,10,(5,9))
        if fr['tele']:
            ox,oy,nx_,ny_=fr['tele']; holes.append([ox,oy,0]); burst(ox,oy,14,[DIRT,(60,40,20)],3,8)
        if fr['clodhit']:
            hx,hy=fr['clodhit']; shake[0]=max(shake[0],16); flash[:]=[90,DIRT]; burst(hx,hy,45,[DIRT,DIRT2,(90,60,30)],5,18)
            pops.append([hx-60,hy-120,'BURIED!',DIRT2,0,58])
        for seg in fr['crash']:
            logs.append([seg,0]); shake[0]=max(shake[0],30)
            x0,y0,x1,y1=seg
            for q in range(14):
                u=q/13; burst(x0+(x1-x0)*u,y0+(y1-y0)*u,4,[LEAF,(40,120,50),TRUNK,(255,255,255)],4,14)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    if not ending:
        # dig target zone
        if fr['zone']:
            zx,zy,u=fr['zone']; ov,od=overlay(); rr=DIG_R
            od.ellipse([zx-rr,zy-rr,zx+rr,zy+rr],fill=RED+(int(35+85*u),))
            put(lay,ov)
            pr=rr*(1.5-0.5*u); ld.ellipse([zx-pr,zy-pr,zx+pr,zy+pr],outline=RED+(255,),width=7)
            ld.ellipse([zx-rr,zy-rr,zx+rr,zy+rr],outline=(255,255,255,160 if (t//3)%2 else 60),width=3)
            ld.line([zx-40,zy,zx+40,zy],fill=(255,255,255,220),width=5); ld.line([zx,zy-40,zx,zy+40],fill=(255,255,255,220),width=5)
            g2=emo('a',64).copy(); g2.putalpha(g2.getchannel('A').point(lambda v:v*int(60+120*u)//255)); lay.alpha_composite(g2,(int(zx-32),int(zy-32)))
        # timber: a tree grows in each corner; red band shows where it will fall
        for (seg,tt,ang) in fr['trees']:
            if tt<TIMBER_WARN:
                u=tt/TIMBER_WARN; ov,od=overlay(); band(od,seg,TIMBER_W,RED+(int(40+90*u),)); put(lay,ov)
                if (t//3)%2: band(ld,seg,6,(255,255,255,200))
                x0,y0,x1,y1=seg; mx,my=x0+(x1-x0)*.6,y0+(y1-y0)*.6
                ld.text((mx-12,my-30),'!',font=font(60),fill=(255,255,255,255),stroke_width=4,stroke_fill=RED+(255,))
                th=20+60*u; fr_=14+34*u; ov,od=overlay()
                od.ellipse([x0-30,y0-10,x0+30,y0+14],fill=(90,60,30,230))
                od.rectangle([x0-8-5*u,y0-th,x0+8+5*u,y0],fill=TRUNK+(255,))
                for q,(ox,oy) in enumerate([(0,-1.0),(-.6,-.7),(.6,-.7)]):
                    cx,cy=x0+ox*fr_*.8,y0-th+oy*fr_*.6; rq=fr_*(1 if q==0 else .75)
                    od.ellipse([cx-rq,cy-rq,cx+rq,cy+rq],fill=(LEAF if q==0 else (50,150,60))+(255,),outline=(30,90,40,255),width=3)
                lay.alpha_composite(ov)
    for e in blasts:   # dig pop-up dirt blast
        e[2]+=1; k=e[2]; rr=DIG_R*min(1,k/4); al=max(0,220-k*12)
        if al>0:
            ov,od=overlay(); od.ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=DIRT2+(al//3,),outline=DIRT2+(al,),width=12)
            for q in range(9):
                g=q/9*6.28+e[1]; od.polygon([(e[0]+math.cos(g-.15)*30,e[1]+math.sin(g-.15)*30),(e[0]+math.cos(g)*rr,e[1]+math.sin(g)*rr),(e[0]+math.cos(g+.15)*30,e[1]+math.sin(g+.15)*30)],fill=DIRT+(al,))
            put(lay,ov)
    blasts[:]=[e for e in blasts if e[2]<20]
    for e in holes:
        e[2]+=1; al=max(0,230-e[2]*10)
        if al>0:
            ov,od=overlay(); od.ellipse([e[0]-R,e[1]-R*.5,e[0]+R,e[1]+R*.5],fill=(30,20,10,al),outline=DIRT2+(al,),width=5); put(lay,ov)
    holes[:]=[e for e in holes if e[2]<24]
    # fallen trees
    for lg in logs:
        lg[1]+=1; k=lg[1]; al=255 if k<14 else max(0,255-(k-14)*30)
        if al>0:
            seg=lg[0]; x0,y0,x1,y1=seg; fall=min(1,k/3)
            ov,od=overlay(); band(od,seg,TIMBER_W*fall,(0,0,0,int(al*.4)))
            band(od,seg,34,TRUNK+(al,))
            for q in range(10):
                u=0.45+q*0.06; cx,cy=x0+(x1-x0)*u,y0+(y1-y0)*u; rr=46+((q*37)%3)*8
                od.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],fill=(LEAF if q%2 else (50,150,60))+(al,))
            put(lay,ov)
    logs[:]=[lg for lg in logs if lg[1]<24]
    if not ending:
        for (cx,cy,s) in fr['clods']:
            ov,od=overlay()
            for q in range(5):
                rq=20-q*3; od.ellipse([cx-rq,cy-rq,cx+rq,cy+rq],fill=DIRT+(150-q*28,))
            od.ellipse([cx-24,cy-24,cx+24,cy+24],fill=DIRT+(255,),outline=(90,60,30,255),width=4)
            for q in range(3):
                g=q*2.1+s*0.3; od.ellipse([cx+math.cos(g)*10-6,cy+math.sin(g)*10-6,cx+math.cos(g)*10+6,cy+math.sin(g)*10+6],fill=DIRT2+(255,))
            lay.alpha_composite(ov)
    if frozen:
        lay.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,170)))
    def draw_a():
        digging=fr['dig'] and not ending
        ld.ellipse([ax-R,ay-R,ax+R,ay+R],fill=(25,45,60),outline=(255,255,255),width=5)
        e=emo('a',104,(30*math.sin(t*0.9)) if digging else 0); lay.alpha_composite(e,(int(ax-52),int(ay-52+(8*abs(math.sin(t*0.9)) if digging else 0))))
        if digging:
            ov,od=overlay(); od.pieslice([ax-R-10,ay+R*.25,ax+R+10,ay+R*1.5],180,360,fill=(115,78,40,255),outline=DIRT2+(255,),width=4); lay.alpha_composite(ov)
        hpbar(ld,ax,ay,0 if (ending and loser=='a') else ahp,SC_,t)
    def draw_b():
        spin=fr['whirl'] and not ending
        if spin:
            ov,od=overlay(); rr=WHIRL_R+R*.3
            od.ellipse([bx-rr,by-rr,bx+rr,by+rr],fill=WIND+(35,))
            for q in range(3):
                a0=(t*40+q*120)%360; od.arc([bx-rr,by-rr,bx+rr,by+rr],a0,a0+70,fill=WIND+(230,),width=10)
                r2=rr*0.7; a1=(-t*55+q*120)%360; od.arc([bx-r2,by-r2,bx+r2,by+r2],a1,a1+60,fill=(255,255,255,180),width=6)
            lay.alpha_composite(ov)
        ld.ellipse([bx-R,by-R,bx+R,by+R],fill=(65,22,18),outline=(255,255,255),width=5)
        e=emo('b',104,(t*45) if spin else 0); lay.alpha_composite(e,(int(bx-52),int(by-52)))
        if fr['buried'] and not ending:
            ov,od=overlay(); k=fr['buried']
            od.pieslice([bx-R-14,by-R*.2,bx+R+14,by+R*1.9],180,360,fill=(115,78,40,255),outline=DIRT2+(255,),width=5)
            od.rectangle([bx-R-14,by+R*.85,bx+R+14,by+R+8],fill=(115,78,40,255))
            for q in range(5):
                gx=bx-R+q*R*.5; od.ellipse([gx-9,by+R*.35-(q%2)*14-9,gx+9,by+R*.35-(q%2)*14+9],fill=DIRT2+(255,))
            lay.alpha_composite(ov)
        hpbar(ld,bx,by,0 if (ending and loser=='b') else bhp,XC,t)
    if ending:
        k=t-(INTRO+N)
        if k==0:
            lx,ly,col=(ax,ay,SC_) if loser=='a' else (bx,by,XC)
            for _ in range(70):
                g=random.uniform(0,6.28); v=random.uniform(4,18); parts.append([lx,ly,math.cos(g)*v,math.sin(g)*v,col])
        draw_b() if loser=='a' else draw_a()
    else: draw_a(); draw_b()
    for fl in flashes:
        fl[4]+=1; c,fx,fy,col,k=fl
        if k<12: rr=R+k*12; ld.ellipse([fx-rr,fy-rr,fx+rr,fy+rr],outline=col+(max(0,255-k*20),),width=8)
    for p in fxp:
        p[0]+=p[2]; p[1]+=p[3]; p[2]*=.93; p[3]*=.93; p[3]+=.4; p[5]+=1; sz=max(2,p[6]-p[5]//3)
        ld.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[4]+(max(0,255-p[5]*9),))
    fxp[:]=[p for p in fxp if p[5]<28]
    if frozen:
        cx,cy=(ax,ay) if fz=='bury' else (bx,by); col=SKCOL[fz]
        ov,od=overlay()
        for k in range(18):
            g=k/18*6.28+fk*0.06; L=200+fk*28
            od.polygon([(cx+math.cos(g-.05)*(R+10),cy+math.sin(g-.05)*(R+10)),(cx+math.cos(g)*L,cy+math.sin(g)*L),(cx+math.cos(g+.05)*(R+10),cy+math.sin(g+.05)*(R+10))],fill=col+(150,))
        pr=R+20+(fk%6)*10; od.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],outline=(255,255,255,220),width=8)
        lay.alpha_composite(ov)
        (draw_a if fz=='bury' else draw_b)()
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[2]*=.94; p[3]*=.94; ld.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill=p[4])
    for p in pops:
        p[4]+=1; a=max(0,255-p[4]*10); ld.text((p[0]-30,p[1]-p[4]*2),p[2],font=font(p[5]),fill=p[3]+(a,),stroke_width=3,stroke_fill=(0,0,0,a))
    pops[:]=[p for p in pops if p[4]<26]
    im.alpha_composite(lay); d=ImageDraw.Draw(im)
    if frozen:
        col=SKCOL[fz]; sz=int(150-min(fk,6)*7)
        ctext(d,W/2,268,'ULTIMATE',font(48),(255,215,60),stroke_width=4,stroke_fill=(0,0,0))
        ctext(d,W/2,312-(sz-110)//2,NAMES[fz],font(sz-30),col,stroke_width=7,stroke_fill=(0,0,0))
    cur=[f for f in flashes if f[4]<24]
    if cur and not ending and not frozen:
        c=cur[-1]; ctext(d,W/2,AY0-90,NAMES[c[0]],font(64),c[3])
    flashes[:]=cur
    for side in (0,1):
        hp=max(ahp if side==0 else bhp,0)
        if ending and ((side==0 and loser=='a') or (side==1 and loser=='b')): hp=0
        col=SC_ if side==0 else XC; x0=140 if side==0 else 610; y0=1290
        ctext(d,x0+165,y0,f'HP {hp}',font(54),col)
        d.rounded_rectangle([x0,y0+70,x0+330,y0+100],radius=10,outline=col,width=3)
        d.rounded_rectangle([x0+4,y0+74,x0+4+322*hp/100,y0+96],radius=8,fill=col)
        sk=A_SK if side==0 else B_SK
        for j,k in enumerate(sk):
            ult=k in ULTS; yy=y0+125+j*62; prog=1-max(fr['cd'][k],0)/CD[k] if (live or frozen) else (0 if t<INTRO else 1)
            ready=prog>.97
            if ult and ready and not ending and t>=INTRO:
                gw=int(4+3*math.sin(t*0.4)); d.rounded_rectangle([x0-gw-2,yy-gw-2,x0+330+gw+2,yy+46+gw+2],radius=16,outline=(255,215,60),width=gw)
            d.rounded_rectangle([x0,yy,x0+330,yy+46],radius=12,outline=(255,215,60) if ult else (200,200,200),width=3)
            d.rounded_rectangle([x0+4,yy+4,x0+4+322*prog,yy+42],radius=10,fill=SKCOL[k] if not ready else (255,255,255))
            lab=NAMES[k].rstrip('!'); fl=font(28); w=d.textlength(lab,font=fl)
            d.text((x0+165-w/2,yy+7),lab,font=fl,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    if t<INTRO: ctext(d,W/2,780,'WHO WINS?',font(110),(255,255,255))
    if ending and t-(INTRO+N)>=12:
        txt=('SHOVEL' if r['win']=='a' else 'AXE')+' WINS!'; ctext(d,W/2,1620,txt,font(96),SC_ if r['win']=='a' else XC)
    if flash[0]>0:
        im.alpha_composite(Image.new('RGBA',(W,H),flash[1]+(int(flash[0]),))); flash[0]=max(0,flash[0]-28)
    out=im.convert('RGB')
    if shake[0]>0.5:
        dx,dy=int(random.uniform(-1,1)*shake[0]),int(random.uniform(-1,1)*shake[0])
        sh=Image.new('RGB',(W,H)); sh.paste(out,(dx,dy)); out=sh; shake[0]*=0.82
    proc.stdin.write(out.tobytes())
proc.stdin.close(); proc.wait()
ev=[(START[e[0]],)+tuple(e[1:]) for e in r['ev']]
ev+=[(START[e[0]]-FREEZE,'ultcharge') for e in r['ev'] if e[1]=='cast' and e[2] in ULTS]
json.dump(dict(ev=sorted(ev,key=lambda e:e[0]),intro=INTRO,n=N,end=END,win=r['win'],whp=max(r['ah'],r['bh'])),open(OUT+'.json','w')); print('done',total)
