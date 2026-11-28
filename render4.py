import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim4 import simulate, AX0,AY0,AX1,AY1,R,CD,KR_WARN,KR_R,CRUSH_R
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
BASE={'a':emoji_base('🐙'),'b':emoji_base('🦀')}; EC={}
def emo(side,size):
    size=int(size)//2*2
    if (side,size) not in EC: EC[(side,size)]=BASE[side].resize((size,size),Image.LANCZOS)
    return EC[(side,size)]
OC=(245,120,210); CC=(255,125,70)
INK=(120,70,210); WH=(225,95,185); KR=(200,60,160); BUB=(130,215,255); GOLD=(255,195,60); RED=(255,70,70)
NAMES={'ink':'INK!','whip':'TENTACLE WHIP!','kraken':'KRAKEN!','bubbles':'BUBBLES!','claw':'CLAW DASH!','crush':'CRAB CRUSH!'}
SKCOL={'ink':INK,'whip':WH,'kraken':KR,'bubbles':BUB,'claw':CC,'crush':GOLD}
A_SK=('ink','whip','kraken'); B_SK=('bubbles','claw','crush')
INTRO=30; END=70
pops=[]; flashes=[]; parts=[]; ghosts=[]; blasts=[]; pinches=[]; whips=[]; tents=[]
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
            fx,fy=(ax,ay) if c in A_SK else (bx,by-hb)
            flashes.append([c,fx,fy,SKCOL[c],0])
            if c in ULTS: shake[0]=max(shake[0],26); flash[:]=[170,(255,255,255)]
        if fr['whip']: whips.append(list(fr['whip'])+[0,random.uniform(0,6.28)])
        for (tg,dm,k) in fr['hits']:
            px,py=(ax,ay) if tg=='a' else (bx,by)
            col={'ink':INK,'whip':WH,'kraken':KR,'bubble':BUB,'claw':CC,'crush':GOLD,'bump':(255,255,255)}[k]
            if k=='ink': burst(px,py,10,[INK,(60,30,110)],3,9)
            if k=='bubble': burst(px,py,8,[BUB,(255,255,255)],3,8)
            if k=='whip': shake[0]=max(shake[0],9); burst(px,py,14,[WH,(255,255,255)],5,13)
            if k=='claw': shake[0]=max(shake[0],10); pinches.append([px,py,0]); burst(px,py,16,[CC,(255,255,255)],5,14)
            if k=='kraken': flash[:]=[70,KR]; burst(px,py,30,[KR,WH,(255,255,255)],5,18)
            if k=='crush': flash[:]=[110,GOLD]
            pops.append([px+random.uniform(-30,30),py-70,f'-{dm}',col,0,72 if k in ULTS or k=='crush' else 52])
        for (ex,ey) in fr['erupt']:
            tents.append([ex,ey,0,random.uniform(-.4,.4)]); shake[0]=max(shake[0],12); burst(ex,ey,18,[(120,90,70),KR],4,12)
        if fr['landed']:
            lx,ly=fr['landed']; blasts.append([lx,ly,0]); shake[0]=max(shake[0],28)
            burst(lx,ly,60,[GOLD,CC,(255,255,255),(140,100,60)],5,24,(6,12))
        if fr['claw']: ghosts.append([bx,by,0])
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
        if a>0: ld.ellipse([g[0]-R,g[1]-R,g[0]+R,g[1]+R],outline=CC+(a,),width=4)
    ghosts[:]=[g for g in ghosts if g[2]<10]
    if not ending:
        for (px,py,a) in fr['inks']:
            ov,od=overlay()
            for q in range(6):
                tx,ty=px-math.cos(a)*q*10,py-math.sin(a)*q*10; rq=16-q*2
                od.ellipse([tx-rq,ty-rq,tx+rq,ty+rq],fill=INK+(220-q*35,))
            od.ellipse([px-17,py-17,px+17,py+17],fill=(70,35,130,255),outline=INK+(255,),width=4)
            od.ellipse([px-7,py-10,px,py-3],fill=(200,170,255,255)); lay.alpha_composite(ov)
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
        ld.ellipse([ax-R,ay-R,ax+R,ay+R],fill=(120,40,110),outline=(255,255,255),width=5)
        e=emo('a',86); lay.alpha_composite(e,(int(ax-43),int(ay-43)))
    def draw_b():
        sc=1+0.7*math.sin(math.pi*jmp[0]) if jmp and not ending else 1
        cy=by-hb; rr=R*sc
        if hb>0:
            ov,od=overlay(); sr=R*(1-0.4*hb/260); od.ellipse([bx-sr,by-sr*.45,bx+sr,by+sr*.45],fill=(0,0,0,160)); lay.alpha_composite(ov)
            ld.ellipse([bx-sr,by-sr*.45,bx+sr,by+sr*.45],outline=(255,255,255,90),width=3)
        if fr['claw'] and not ending:
            ang=math.atan2(ay-by,ax-bx)
            for k in range(7):
                off=(k-3)*16; L=90+((t*13+k*29)%70)
                sx0=bx-math.cos(ang)*(R+10)+math.cos(ang+1.57)*off; sy0=by-math.sin(ang)*(R+10)+math.sin(ang+1.57)*off
                ld.line([sx0,sy0,sx0-math.cos(ang)*L,sy0-math.sin(ang)*L],fill=(255,200,160,200),width=5)
            ov,od=overlay(); od.ellipse([bx-R-18,by-R-18,bx+R+18,by+R+18],fill=CC+(80,)); lay.alpha_composite(ov)
        if fr['inked'] and not ending:
            ld.ellipse([bx-R-8,cy-R-8,bx+R+8,cy+R+8],outline=INK+(255,),width=8)
            for q in range(3):
                dy_=(t*3+q*17)%40; ld.ellipse([bx-25+q*25-6,cy+R+dy_-6,bx-25+q*25+6,cy+R+dy_+8],fill=INK+(max(0,255-dy_*6),))
        ld.ellipse([bx-rr,cy-rr,bx+rr,cy+rr],fill=(140,45,30),outline=(255,255,255),width=5)
        e=emo('b',86*sc); lay.alpha_composite(e,(int(bx-e.width/2),int(cy-e.height/2)))
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
            d.rounded_rectangle([x0+4,yy+4,x0+4+322*prog,yy+42],radius=10,fill=SKCOL[k] if not ready else (255,255,255))
            lab=NAMES[k].rstrip('!'); fl=font(28); w=d.textlength(lab,font=fl)
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
json.dump(dict(ev=sorted(ev,key=lambda e:e[0]),intro=INTRO,n=N,end=END,win=r['win']),open(OUT+'.json','w')); print('done',total)
