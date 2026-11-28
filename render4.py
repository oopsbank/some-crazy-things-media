import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim4 import simulate, AX0,AY0,AX1,AY1,R,CD,KR_WARN,KR_R,CRUSH_R,BURROW_R,MINE_ARM
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=simulate(SEED, record=True); F=r['frames']
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji_base(ch):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True)
    return im.crop(im.getbbox())
from pixelart import pixel_sprite
BASE={'a':pixel_sprite('🐙'),'b':pixel_sprite('🦀')}; EC={}
def emo(side,size):
    size=int(size)//2*2
    if (side,size) not in EC: EC[(side,size)]=BASE[side].resize((size,size),Image.NEAREST)
    return EC[(side,size)]
OC=(245,120,210); CC=(255,125,70)
INK=(120,70,210); WH=(225,95,185); KR=(200,60,160); BUB=(130,215,255); GOLD=(255,195,60); RED=(255,70,70)
MN=(170,100,255); TEAL=(110,255,210); PRL=(255,235,225); SAND=(215,170,100)
NAMES={'ink':'INK!','mine':'INK MINE!','blink':'CAMO BLINK!','whip':'TENTACLE WHIP!','kraken':'KRAKEN!',
       'bubbles':'BUBBLES!','pearl':'PEARL!','burrow':'BURROW!','boomer':'CLAW BOOMERANG!','crush':'CRAB CRUSH!'}
SKCOL={'ink':INK,'mine':MN,'blink':TEAL,'whip':WH,'kraken':KR,'bubbles':BUB,'pearl':PRL,'burrow':SAND,'boomer':CC,'crush':GOLD}
A_MOVES=('ink','mine','blink','whip','kraken')
A_SK=('s1a','whip','kraken'); B_SK=('s1b','boomer','crush')
INTRO=30; END=70
pops=[]; flashes=[]; parts=[]; ghosts=[]; blasts=[]; pinches=[]; whips=[]; tents=[]; afters=[]; inkbooms=[]; dirt=[]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill,**kw):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,**kw)
def overlay(): ov=Image.new('RGBA',(W,H),(0,0,0,0)); return ov,ImageDraw.Draw(ov)
def burst(x,y,n,cols,vmin,vmax,life=(6,11)):
    for _ in range(n):
        g=random.uniform(0,6.28); v=random.uniform(vmin,vmax); fxp.append([x,y,math.cos(g)*v,math.sin(g)*v,random.choice(cols),0,random.randint(*life)])
ULTS=('kraken','crush'); FREEZE=16
TL=[]; START=[]
for i,fr_ in enumerate(F):
    u=[c for c in fr_['casts'] if c in ULTS]
    if u: TL+=[(i,u[0],k) for k in range(FREEZE)]
    START.append(len(TL)); TL.append((i,None,0))
N=len(TL); total=INTRO+N+END; loser='b' if r['win']=='a' else 'a'
shake=[0.0]; flash=[0,(255,255,255)]; fxp=[]
def tentacle(ld,x1,y1,x2,y2,phase,w0=24,w1=7,col=WH,al=255,suck=True):
    L=math.hypot(x2-x1,y2-y1) or 1; nx,ny=-(y2-y1)/L,(x2-x1)/L; n=18
    pts=[]
    for k in range(n+1):
        u=k/n; off=math.sin(u*math.pi*2+phase)*min(60,L*.15)*math.sin(u*math.pi)
        pts.append((x1+(x2-x1)*u+nx*off,y1+(y2-y1)*u+ny*off,w0+(w1-w0)*u))
    for (px,py,w) in pts: ld.ellipse([px-w,py-w,px+w,py+w],fill=col+(al,))
    if suck:
        for k,(px,py,w) in enumerate(pts[1:-1]):
            if k%2==0: s=max(3,w*.35); ld.ellipse([px+nx*w*.3-s,py+ny*w*.3-s,px+nx*w*.3+s,py+ny*w*.3+s],fill=(255,210,235,al))
def hpbar(ld,cx,cy,hp,col,t,rr=None):
    rr=rr or R; w=150; hp=max(hp,0); y=cy+rr+14
    if y+22>AY1-2: y=cy-rr-36
    c=col if hp>=25 else ((255,60,60) if (t//4)%2 else (255,150,150))
    ld.rounded_rectangle([cx-w/2-5,y-5,cx+w/2+5,y+23],radius=10,fill=(0,0,0,220),outline=(255,255,255,240),width=3)
    if hp>0: ld.rounded_rectangle([cx-w/2,y,cx-w/2+max(10,w*hp/100),y+18],radius=7,fill=c+(255,))
for t in range(total):
    ti=min(max(t-INTRO,0),N-1); i,fz,fk=TL[ti]; fr=F[i]; ending=t>=INTRO+N; live=INTRO<=t<INTRO+N and fz is None; frozen=INTRO<=t<INTRO+N and fz is not None
    im=Image.new('RGBA',(W,H),(0,0,0,255)); d=ImageDraw.Draw(im)
    f1=font(64); P=[('OCTOPUS',OC),(' vs ',(230,230,230)),('CRAB',CC)]
    tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
    for p,c in P: d.text((x,190),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
    d.rectangle([AX0-6,AY0-6,AX1+6,AY1+6],outline=(150,150,150),width=6)
    ax,ay,ahp=fr['a']; bx,by,bhp=fr['b']; jmp=fr['jump']
    hb=260*math.sin(math.pi*jmp[0]) if jmp and not ending else 0   # crab height in the air
    if live:
        for c in fr['casts']:
            fx,fy=(ax,ay) if c in A_MOVES else (bx,by-hb)
            flashes.append([c,fx,fy,SKCOL[c],0])
            if c in ULTS: shake[0]=max(shake[0],26); flash[:]=[170,(255,255,255)]
        if fr['whip']: whips.append(list(fr['whip'])+[0,random.uniform(0,6.28)])
        for (tg,dm,k) in fr['hits']:
            px,py=(ax,ay) if tg=='a' else (bx,by)
            col={'ink':INK,'mine':MN,'blink':TEAL,'whip':WH,'kraken':KR,'bubble':BUB,'pearl':PRL,'burrow':SAND,'boomer':CC,'crush':GOLD,'bump':(255,255,255)}[k]
            if k=='blink': shake[0]=max(shake[0],9); burst(px,py,18,[TEAL,(255,255,255)],5,13)
            if k=='pearl': shake[0]=max(shake[0],7); burst(px,py,14,[PRL,(255,200,220)],4,12)
            if k=='boomer': pinches.append([px,py,0]); burst(px,py,10,[CC,(255,255,255)],4,11)
            if k=='burrow': flash[:]=[60,SAND]
            if k=='ink': burst(px,py,10,[INK,(60,30,110)],3,9)
            if k=='bubble': burst(px,py,8,[BUB,(255,255,255)],3,8)
            if k=='whip': shake[0]=max(shake[0],9); burst(px,py,14,[WH,(255,255,255)],5,13)
            if k=='kraken': flash[:]=[70,KR]; burst(px,py,30,[KR,WH,(255,255,255)],5,18)
            if k=='crush': flash[:]=[110,GOLD]
            pops.append([px+random.uniform(-30,30),py-70,f'-{dm}',col,0,72 if k in ULTS or k=='crush' else 52])
        for (ex,ey) in fr['erupt']:
            tents.append([ex,ey,0,random.uniform(-.4,.4)]); shake[0]=max(shake[0],12); burst(ex,ey,18,[(120,90,70),KR],4,12)
        if fr['landed']:
            lx,ly=fr['landed']; blasts.append([lx,ly,0]); shake[0]=max(shake[0],28)
            burst(lx,ly,60,[GOLD,CC,(255,255,255),(140,100,60)],5,24,(6,12))
        if fr['blink']:
            ox,oy,nx_,ny_=fr['blink']; afters.append([ox,oy,nx_,ny_,0]); burst(ox,oy,16,[TEAL,(200,255,240)],3,9); burst(nx_,ny_,16,[TEAL,(255,255,255)],3,9)
        for (mx,my) in fr['minebooms']:
            inkbooms.append([mx,my,0]); shake[0]=max(shake[0],12); burst(mx,my,30,[INK,MN,(40,20,70)],5,18)
        if fr['popup']:
            px,py=fr['popup']; dirt.append([px,py,0]); shake[0]=max(shake[0],14); burst(px,py,40,[SAND,(150,110,60),(255,230,170)],5,20)
        if fr['burrow'] and t%2==0: burst(bx+random.uniform(-30,30),by+random.uniform(-20,20),2,[SAND,(150,110,60)],2,5,(4,7))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    if not ending:
        # kraken warnings
        for (kx,ky,kt) in fr['krak']:
            if kt<=KR_WARN:
                u=kt/KR_WARN; ov,od=overlay(); rr=KR_R
                od.ellipse([kx-rr,ky-rr,kx+rr,ky+rr],fill=RED+(int(40+70*u),))
                lay.alpha_composite(ov)
                pr=rr*(1.6-0.6*u); ld.ellipse([kx-pr,ky-pr,kx+pr,ky+pr],outline=RED+(255,),width=6)
                ld.line([kx-30,ky,kx+30,ky],fill=(255,255,255,200),width=4); ld.line([kx,ky-30,kx,ky+30],fill=(255,255,255,200),width=4)
        # crush target marker
        if jmp:
            u,tx,ty=jmp; ov,od=overlay(); rr=CRUSH_R
            od.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],fill=GOLD+(int(25+60*u),)); lay.alpha_composite(ov)
            pr=rr*(1.3-0.3*u); ld.ellipse([tx-pr,ty-pr,tx+pr,ty+pr],outline=GOLD+(255,),width=7)
            ld.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],outline=(255,255,255,140),width=3)
    for e in blasts:
        e[2]+=1; k=e[2]; rr=CRUSH_R*min(1,k/4); al=max(0,230-k*10)
        if al>0:
            ov,od=overlay()
            od.ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=GOLD+(al//3,),outline=GOLD+(al,),width=16)
            for q in range(10):
                g=q/10*6.28+e[0]; L=rr*0.9
                od.line([e[0]+math.cos(g)*30,e[1]+math.sin(g)*30,e[0]+math.cos(g)*L,e[1]+math.sin(g)*L],fill=(120,80,40,al),width=6)
            sw=CRUSH_R+k*24; od.ellipse([e[0]-sw,e[1]-sw,e[0]+sw,e[1]+sw],outline=(255,255,255,max(0,200-k*9)),width=7)
            lay.alpha_composite(ov)
    blasts[:]=[e for e in blasts if e[2]<24]
    # kraken tentacles erupting
    for tn in tents:
        tn[2]+=1; k=tn[2]; up=min(1,k/4)*(1 if k<10 else max(0,1-(k-10)/6)); al=255 if k<10 else max(0,255-(k-10)*40)
        if up>0:
            ov,od=overlay(); x0,y0=tn[0],tn[1]+30
            od.ellipse([x0-70,y0-22,x0+70,y0+22],fill=(70,40,30,al))
            tentacle(od,x0,y0,x0+math.sin(tn[3])*120*up,y0-240*up,k*0.5+tn[3]*5,w0=34,w1=8,col=KR,al=al)
            lay.alpha_composite(ov)
    tents[:]=[tn for tn in tents if tn[2]<16]
    for g in ghosts:
        g[2]+=1; a=max(0,140-g[2]*14)
        if a>0:
            rr=26 if len(g)>3 else R
            ld.ellipse([g[0]-rr,g[1]-rr,g[0]+rr,g[1]+rr],outline=CC+(a,),width=4)
    for e in afters:   # blink afterimage + dotted trail
        e[4]+=1; k=e[4]; al=max(0,200-k*18)
        if al>0:
            ov,od=overlay(); od.ellipse([e[0]-R,e[1]-R,e[0]+R,e[1]+R],fill=TEAL+(al//3,),outline=TEAL+(al,),width=4)
            for q in range(12):
                u=q/11; od.ellipse([e[0]+(e[2]-e[0])*u-5,e[1]+(e[3]-e[1])*u-5,e[0]+(e[2]-e[0])*u+5,e[1]+(e[3]-e[1])*u+5],fill=TEAL+(al,))
            g2=emo('a',104).copy(); g2.putalpha(g2.getchannel('A').point(lambda v:v*al//400)); ov.alpha_composite(g2,(int(e[0]-52),int(e[1]-52)))
            lay.alpha_composite(ov)
    afters[:]=[e for e in afters if e[4]<12]
    for e in inkbooms:
        e[2]+=1; k=e[2]; rr=40+k*14; al=max(0,230-k*16)
        if al>0:
            ov,od=overlay(); od.ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=(50,25,90,al//2),outline=MN+(al,),width=10)
            for q in range(7):
                g=q/7*6.28+e[0]; L=rr*1.1; od.ellipse([e[0]+math.cos(g)*L-12,e[1]+math.sin(g)*L-12,e[0]+math.cos(g)*L+12,e[1]+math.sin(g)*L+12],fill=INK+(al,))
            lay.alpha_composite(ov)
    inkbooms[:]=[e for e in inkbooms if e[2]<16]
    for e in dirt:
        e[2]+=1; k=e[2]; rr=BURROW_R*min(1,k/4); al=max(0,220-k*12)
        if al>0:
            ov,od=overlay(); od.ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=SAND+(al//3,),outline=SAND+(al,),width=12)
            for q in range(9):
                g=q/9*6.28+e[1]; od.polygon([(e[0]+math.cos(g-.15)*30,e[1]+math.sin(g-.15)*30),(e[0]+math.cos(g)*rr,e[1]+math.sin(g)*rr),(e[0]+math.cos(g+.15)*30,e[1]+math.sin(g+.15)*30)],fill=(150,110,60,al))
            lay.alpha_composite(ov)
    dirt[:]=[e for e in dirt if e[2]<20]
    ghosts[:]=[g for g in ghosts if g[2]<10]
    if not ending:
        for (px,py,a) in fr['inks']:
            ov,od=overlay()
            for q in range(6):
                tx,ty=px-math.cos(a)*q*10,py-math.sin(a)*q*10; rq=16-q*2
                od.ellipse([tx-rq,ty-rq,tx+rq,ty+rq],fill=INK+(220-q*35,))
            od.ellipse([px-17,py-17,px+17,py+17],fill=(70,35,130,255),outline=INK+(255,),width=4)
            od.ellipse([px-7,py-10,px,py-3],fill=(200,170,255,255)); lay.alpha_composite(ov)
        for (mx,my,mt) in fr['mines']:
            armed=mt>MINE_ARM; ov,od=overlay()
            for q in range(8):
                g=q/8*6.28+mt*0.03; od.line([mx+math.cos(g)*16,my+math.sin(g)*16,mx+math.cos(g)*30,my+math.sin(g)*30],fill=MN+(255,),width=6)
            od.ellipse([mx-22,my-22,mx+22,my+22],fill=(60,30,110,255),outline=MN+(255,),width=4)
            lc=(255,60,60) if armed and (t//5)%2 else (120,60,60); od.ellipse([mx-7,my-7,mx+7,my+7],fill=lc+(255,))
            if armed: od.ellipse([mx-40,my-40,mx+40,my+40],outline=MN+(70,),width=3)
            lay.alpha_composite(ov)
        for (px,py,vx,vy) in fr['pearls']:
            m=math.hypot(vx,vy) or 1; ov,od=overlay()
            for q in range(6):
                tx,ty=px-vx/m*q*11,py-vy/m*q*11; rq=15-q*2
                od.ellipse([tx-rq,ty-rq,tx+rq,ty+rq],fill=(255,210,230,170-q*28))
            od.ellipse([px-17,py-17,px+17,py+17],fill=PRL+(255,),outline=(255,190,215,255),width=3)
            od.ellipse([px-9,py-11,px-1,py-3],fill=(255,255,255,255)); lay.alpha_composite(ov)
        for (px,py,rot,back) in fr['booms']:
            ov,od=overlay()
            for q in range(2):
                g=rot+q*math.pi; cx_,cy_=px+math.cos(g)*14,py+math.sin(g)*14
                od.pieslice([cx_-30,cy_-30,cx_+30,cy_+30],math.degrees(g)+20,math.degrees(g)+160,fill=CC+(255,),outline=(255,230,210,255),width=3)
            od.ellipse([px-10,py-10,px+10,py+10],fill=(150,50,30,255))
            lay.alpha_composite(ov)
            ghosts.append([px,py,4,'boom'])
        for (px,py) in fr['bubs']:
            wob=3*math.sin(t*0.5+px*0.05); rq=17+wob
            ov,od=overlay(); od.ellipse([px-rq,py-rq,px+rq,py+rq],fill=BUB+(60,),outline=BUB+(255,),width=4)
            od.ellipse([px-9,py-11,px-2,py-4],fill=(255,255,255,240)); lay.alpha_composite(ov)
    # whips
    for w in whips:
        x1,y1,x2,y2,hit,k,ph=w; w[5]+=1
        if k<9:
            ext=min(1,(k+1)/3); al=255 if k<5 else 255-(k-5)*55
            ov,od=overlay(); tentacle(od,x1,y1,x1+(x2-x1)*ext,y1+(y2-y1)*ext,ph+k*0.6,col=WH,al=al); lay.alpha_composite(ov)
    whips[:]=[w for w in whips if w[5]<9]
    if frozen:
        lay.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,170)))
    def draw_a():
        ld.ellipse([ax-R,ay-R,ax+R,ay+R],fill=(60,22,58),outline=(255,255,255),width=5)
        e=emo('a',104); lay.alpha_composite(e,(int(ax-52),int(ay-52)))
        hpbar(ld,ax,ay,0 if (ending and loser=='a') else ahp,OC,t)
    def draw_b():
        sc=1+0.7*math.sin(math.pi*jmp[0]) if jmp and not ending else 1
        cy=by-hb; rr=R*sc
        if hb>0:
            ov,od=overlay(); sr=R*(1-0.4*hb/260); od.ellipse([bx-sr,by-sr*.45,bx+sr,by+sr*.45],fill=(0,0,0,160)); lay.alpha_composite(ov)
            ld.ellipse([bx-sr,by-sr*.45,bx+sr,by+sr*.45],outline=(255,255,255,90),width=3)
        if fr['burrow'] and not ending:
            ov,od=overlay(); od.ellipse([bx-R-6,by-R*.55,bx+R+6,by+R*.55],fill=(120,85,45,255),outline=SAND+(255,),width=5)
            for q in range(4):
                g=q*1.4+t*0.3; od.line([bx+math.cos(g)*20,by+math.sin(g)*10,bx+math.cos(g)*50,by+math.sin(g)*22],fill=(60,40,20,255),width=4)
            lay.alpha_composite(ov)
            e=emo('b',52); lay.alpha_composite(e,(int(bx-26),int(by-R*.55-28)))
            hpbar(ld,bx,by,bhp,CC,t); return
        if fr['inked'] and not ending:
            ld.ellipse([bx-R-8,cy-R-8,bx+R+8,cy+R+8],outline=INK+(255,),width=8)
            for q in range(3):
                dy_=(t*3+q*17)%40; ld.ellipse([bx-25+q*25-6,cy+R+dy_-6,bx-25+q*25+6,cy+R+dy_+8],fill=INK+(max(0,255-dy_*6),))
        ld.ellipse([bx-rr,cy-rr,bx+rr,cy+rr],fill=(55,22,18),outline=(255,255,255),width=5)
        e=emo('b',104*sc); lay.alpha_composite(e,(int(bx-e.width/2),int(cy-e.height/2)))
        hpbar(ld,bx,cy,0 if (ending and loser=='b') else bhp,CC,t,rr)
    if ending:
        k=t-(INTRO+N)
        if k==0:
            lx,ly,col=(ax,ay,OC) if loser=='a' else (bx,by,CC)
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
    for c in pinches:   # two claw arcs snapping shut
        c[2]+=1; k=c[2]; gap=max(0,50-k*12); al=max(0,255-k*20); cx,cy=c[0],c[1]
        ld.arc([cx-80-gap,cy-80,cx+80-gap,cy+80],100,260,fill=CC+(al,),width=16)
        ld.arc([cx-80+gap,cy-80,cx+80+gap,cy+80],-80,80,fill=CC+(al,),width=16)
    pinches[:]=[c for c in pinches if c[2]<14]
    if frozen:
        cx,cy=(ax,ay) if fz=='kraken' else (bx,by); col=SKCOL[fz]
        ov,od=overlay()
        for k in range(18):
            g=k/18*6.28+fk*0.06; L=200+fk*28
            od.polygon([(cx+math.cos(g-.05)*(R+10),cy+math.sin(g-.05)*(R+10)),(cx+math.cos(g)*L,cy+math.sin(g)*L),(cx+math.cos(g+.05)*(R+10),cy+math.sin(g+.05)*(R+10))],fill=col+(150,))
        pr=R+20+(fk%6)*10; od.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],outline=(255,255,255,220),width=8)
        lay.alpha_composite(ov)
        (draw_a if fz=='kraken' else draw_b)()
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
        col=OC if side==0 else CC; x0=140 if side==0 else 610; y0=1290
        ctext(d,x0+165,y0,f'HP {hp}',font(54),col)
        d.rounded_rectangle([x0,y0+70,x0+330,y0+100],radius=10,outline=col,width=3)
        d.rounded_rectangle([x0+4,y0+74,x0+4+322*hp/100,y0+96],radius=8,fill=col)
        sk=A_SK if side==0 else B_SK
        for j,k in enumerate(sk):
            yy=y0+125+j*62; prog=1-max(fr['cd'][k],0)/CD[k] if (live or frozen) else (0 if t<INTRO else 1)
            ready=prog>.97
            if j==2 and ready and not ending and t>=INTRO:
                gw=int(4+3*math.sin(t*0.4)); d.rounded_rectangle([x0-gw-2,yy-gw-2,x0+330+gw+2,yy+46+gw+2],radius=16,outline=(255,215,60),width=gw)
            d.rounded_rectangle([x0,yy,x0+330,yy+46],radius=12,outline=(255,215,60) if j==2 else (200,200,200),width=3)
            mk=fr['n1a'] if k=='s1a' else (fr['n1b'] if k=='s1b' else k)
            d.rounded_rectangle([x0+4,yy+4,x0+4+322*prog,yy+42],radius=10,fill=SKCOL[mk] if not ready else (255,255,255))
            lab=NAMES[mk].rstrip('!').replace('CLAW BOOMERANG','BOOMERANG'); fl=font(28); w=d.textlength(lab,font=fl)
            d.text((x0+165-w/2,yy+7),lab,font=fl,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    if t<INTRO: ctext(d,W/2,780,'WHO WINS?',font(110),(255,255,255))
    if ending and t-(INTRO+N)>=12:
        txt=('OCTOPUS' if r['win']=='a' else 'CRAB')+' WINS!'; ctext(d,W/2,1660,txt,font(96),OC if r['win']=='a' else CC)
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
