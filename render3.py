import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim3 import simulate, AX0,AY0,AX1,AY1,R,CD,CLOUD_R,CLOUD_T,BOMB_R
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=simulate(SEED, record=True); F=r['frames']
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch,size):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True)
    return im.crop(im.getbbox()).resize((size,size),Image.LANCZOS)
EA,EB=emoji('🐢',86),emoji('🦨',86)
TC=(60,210,170); SC=(235,235,245); GAS=(190,220,60); BR=(170,110,50); WV=(70,170,255); BM=(150,60,200)
NAMES={'shell':'SHELL!','bite':'BITE!','spray':'SPRAY!','cloud':'STINK CLOUD!','wave':'TIDAL WAVE!','bomb':'TOXIC BOMB!'}
SKCOL={'shell':BR,'bite':TC,'spray':GAS,'cloud':GAS,'wave':WV,'bomb':BM}
INTRO=30; END=70
pops=[]; flashes=[]; parts=[]; ghosts=[]; blasts=[]; chomps=[]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill,**kw):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,**kw)
ULTS=('wave','bomb'); FREEZE=16
TL=[]; START=[]
for i,fr_ in enumerate(F):
    u=[c for c in fr_['casts'] if c in ULTS]
    if u: TL+=[(i,u[0],k) for k in range(FREEZE)]
    START.append(len(TL)); TL.append((i,None,0))
N=len(TL); total=INTRO+N+END; loser='b' if r['win']=='a' else 'a'
shake=[0.0]; flash=[0,(255,255,255)]; fxp=[]
def ult_caster(c,fr): return fr['a'][:2] if c=='wave' else fr['b'][:2]
for t in range(total):
    ti=min(max(t-INTRO,0),N-1); i,fz,fk=TL[ti]; fr=F[i]; ending=t>=INTRO+N; live=INTRO<=t<INTRO+N and fz is None; frozen=INTRO<=t<INTRO+N and fz is not None
    im=Image.new('RGBA',(W,H),(0,0,0,255)); d=ImageDraw.Draw(im)
    f1=font(64); P=[('TURTLE',TC),(' vs ',(230,230,230)),('SKUNK',SC)]
    tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
    for p,c in P: d.text((x,190),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
    d.rectangle([AX0-6,AY0-6,AX1+6,AY1+6],outline=(150,150,150),width=6)
    ax,ay,ahp=fr['a']; bx,by,bhp=fr['b']
    if live:
        for c in fr['casts']:
            fx,fy=(ax,ay) if c in('shell','bite','wave') else (bx,by)
            flashes.append([c,fx,fy,SKCOL[c],0])
        for (tg,dm,k) in fr['hits']:
            px,py=(ax,ay) if tg=='a' else (bx,by)
            if k=='block':
                if any(p[2]=='BLOCK' and p[4]<6 for p in pops): continue
                pops.append([px+random.uniform(-30,10),py-70,'BLOCK',(255,215,120),0,36])
                for _ in range(8):
                    g=random.uniform(0,6.28); v=random.uniform(6,12); fxp.append([px+math.cos(g)*(R+20),py+math.sin(g)*(R+20),math.cos(g)*v,math.sin(g)*v,(255,220,120),0,5])
                continue
            if k=='spray':
                for _ in range(7):
                    g=random.uniform(0,6.28); v=random.uniform(3,9); fxp.append([px+random.uniform(-25,25),py+random.uniform(-25,25),math.cos(g)*v,math.sin(g)*v,GAS,0,7])
            if k=='bite':
                shake[0]=max(shake[0],10); chomps.append([px,py,0])
                for _ in range(16):
                    g=random.uniform(0,6.28); v=random.uniform(5,14); fxp.append([px,py,math.cos(g)*v,math.sin(g)*v,random.choice([TC,(255,255,255)]),0,7])
            col={'bite':TC,'bump':(255,255,255),'spray':GAS,'gas':GAS,'wave':WV,'bomb':BM}[k]
            pops.append([px+random.uniform(-30,30),py-70,f'-{dm}',col,0,38 if k=='gas' else (72 if k in('wave','bomb') else 52)])
        if fr['bite']: ghosts.append([ax,ay,0])
        for (ex,ey) in fr['booms']:
            blasts.append([ex,ey,0]); shake[0]=max(shake[0],20); flash[:]=[110,BM]
            for _ in range(55):
                g=random.uniform(0,6.28); v=random.uniform(5,24); fxp.append([ex,ey,math.cos(g)*v,math.sin(g)*v,random.choice([BM,GAS,(255,220,60)]),0,random.randint(6,12)])
        for (tg,dm,k) in fr['hits']:
            if k=='wave':
                shake[0]=max(shake[0],20); flash[:]=[110,WV]
                for _ in range(45):
                    g=random.uniform(0,6.28); v=random.uniform(5,22); fxp.append([bx,by,math.cos(g)*v,math.sin(g)*v,random.choice([WV,(200,235,255),(255,255,255)]),0,random.randint(6,11)])
        for c in fr['casts']:
            if c in ULTS: shake[0]=max(shake[0],26); flash[:]=[170,(255,255,255)]
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    # stink clouds (under everything)
    if not ending:
        for (cx,cy,life) in fr['clouds']:
            al=int(70*min(1,life/30)*min(1,(CLOUD_T-life+1)/10))
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            for k in range(7):
                ang=k/7*6.28+t*0.025+cx; dist=55+12*math.sin(t*0.08+k); ox,oy=math.cos(ang)*dist,math.sin(ang)*dist
                rr=CLOUD_R-55+10*math.sin(t*0.1+k*1.7)
                od.ellipse([cx+ox-rr,cy+oy-rr,cx+ox+rr,cy+oy+rr],fill=((150,190,40) if k%2 else GAS)+(int(al*0.75),))
            rr=CLOUD_R-70; od.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],fill=(210,235,90,int(al*0.8)))
            lay.alpha_composite(ov)
            for k in range(3):
                ph=(t*2+k*37+int(cx))%70; sx0=cx-50+k*50; sy0=cy+30-ph
                pts=[(sx0+8*math.sin((sy0-yy)*0.15+k),yy) for yy in range(int(sy0),int(sy0)-40,-5)]
                ld.line(pts,fill=(120,150,30,max(0,220-ph*3)),width=5)
    if not ending:
        for (wx,wy,wr) in fr['waves']:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            od.ellipse([wx-wr,wy-wr,wx+wr,wy+wr],fill=WV+(45,))
            for k,(dr,al,wd) in enumerate([(0,255,26),(-34,170,16),(-70,100,10),(-110,50,6)]):
                rr=wr+dr
                if rr>0: od.ellipse([wx-rr,wy-rr,wx+rr,wy+rr],outline=(WV if k else (210,240,255))+(al,),width=wd)
            for k in range(24):
                g=k/24*6.28+wr*0.004; od.ellipse([wx+math.cos(g)*wr-9,wy+math.sin(g)*wr-9,wx+math.cos(g)*wr+9,wy+math.sin(g)*wr+9],fill=(230,245,255,230))
            lay.alpha_composite(ov)
        for (px,py) in fr['bombs']:
            ld.ellipse([px-30,py-30,px+30,py+30],fill=BM+(255,),outline=(255,255,255,255),width=5)
            ld.ellipse([px-10,py-10,px+10,py+10],fill=GAS+(255,))
            ld.line([px+16,py-24,px+28,py-44],fill=(255,220,60,255),width=6)
            for _ in range(3):
                g=random.uniform(0,6.28); fxp.append([px+28,py-44,math.cos(g)*4,math.sin(g)*4,(255,200,60),0,6])
    for e in blasts:
        e[2]+=1; k=e[2]; rr=BOMB_R*min(1,k/5); al=max(0,230-k*10)
        if al>0:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            od.ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=BM+(al//2,),outline=GAS+(al,),width=14)
            core=max(0,90-k*8); od.ellipse([e[0]-core,e[1]-core,e[0]+core,e[1]+core],fill=(255,240,180,al))
            sw=BOMB_R+k*22; od.ellipse([e[0]-sw,e[1]-sw,e[0]+sw,e[1]+sw],outline=(255,255,255,max(0,200-k*9)),width=6)
            lay.alpha_composite(ov)
    blasts[:]=[e for e in blasts if e[2]<24]
    for g in ghosts:
        g[2]+=1; a=max(0,140-g[2]*14)
        if a>0: ld.ellipse([g[0]-R,g[1]-R,g[0]+R,g[1]+R],outline=TC+(a,),width=4)
    ghosts[:]=[g for g in ghosts if g[2]<10]
    for (px,py,a) in fr['proj'] if not ending else []:
        for q in range(5):
            tx,ty=px-math.cos(a)*q*9,py-math.sin(a)*q*9; rq=12-q*2
            ld.ellipse([tx-rq,ty-rq,tx+rq,ty+rq],fill=(170,210,50,200-q*35))
        ld.ellipse([px-14,py-14,px+14,py+14],fill=(200,235,70,255)); ld.ellipse([px-6,py-8,px+3,py-1],fill=(255,255,220,255))
    if frozen:
        lay.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,170)))
    def draw_a():
        if fr['bite'] and not ending:
            ang=math.atan2(by-ay,bx-ax)
            for k in range(7):
                off=(k-3)*16; L=90+((t*13+k*29)%70)
                sx0=ax-math.cos(ang)*(R+10)+math.cos(ang+1.57)*off; sy0=ay-math.sin(ang)*(R+10)+math.sin(ang+1.57)*off
                ld.line([sx0,sy0,sx0-math.cos(ang)*L,sy0-math.sin(ang)*L],fill=(180,255,230,200),width=5)
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).ellipse([ax-R-18,ay-R-18,ax+R+18,ay+R+18],fill=TC+(80,)); lay.alpha_composite(ov)
        if fr['gas'] and not fr['shell'] and not ending: ld.ellipse([ax-R-8,ay-R-8,ax+R+8,ay+R+8],outline=GAS+(255,),width=8)
        ld.ellipse([ax-R,ay-R,ax+R,ay+R],fill=(30,130,100),outline=(255,255,255),width=5)
        lay.alpha_composite(EA,(int(ax-43),int(ay-43)))
        if fr['shell'] and not ending:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); SR_=R+20
            od.ellipse([ax-SR_,ay-SR_,ax+SR_,ay+SR_],fill=BR+(70,))
            for k in range(6):
                g=k/6*6.28+t*0.04; hx_,hy_=ax+math.cos(g)*(R+4),ay+math.sin(g)*(R+4)
                od.regular_polygon((hx_,hy_,20),6,rotation=math.degrees(g),fill=(200,140,60,200),outline=(255,225,160,255))
            od.ellipse([ax-SR_,ay-SR_,ax+SR_,ay+SR_],outline=(255,225,160,255),width=6)
            sh=(t*9)%360; od.arc([ax-SR_+6,ay-SR_+6,ax+SR_-6,ay+SR_-6],sh,sh+50,fill=(255,255,255,230),width=6)
            lay.alpha_composite(ov)
    def draw_b():
        ld.ellipse([bx-R,by-R,bx+R,by+R],fill=(45,45,60),outline=(255,255,255),width=5)
        lay.alpha_composite(EB,(int(bx-43),int(by-43)))
    if ending:
        k=t-(INTRO+N)
        if k==0:
            lx,ly,col=(ax,ay,TC) if loser=='a' else (bx,by,SC)
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
    for c in chomps:
        c[2]+=1; k=c[2]; gap=max(0,40-k*10); al=max(0,255-k*20); cx,cy=c[0],c[1]
        for sgn in (-1,1):
            yb=cy+sgn*(gap+6)
            ld.arc([cx-75,yb-60,cx+75,yb+60],200 if sgn<0 else 20,340 if sgn<0 else 160,fill=(255,255,255,al),width=10)
            for q in range(5):
                tx=cx-50+q*25; ty=yb+sgn*(-38) if False else yb-sgn*(-2)
                ld.polygon([(tx-9,yb-sgn*48),(tx+9,yb-sgn*48),(tx,yb-sgn*22)],fill=(255,255,255,al))
    chomps[:]=[c for c in chomps if c[2]<14]
    if frozen:
        cx,cy=ult_caster(fz,fr); col=SKCOL[fz]
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
        for k in range(18):
            g=k/18*6.28+fk*0.06; L=200+fk*28
            od.polygon([(cx+math.cos(g-.05)*(R+10),cy+math.sin(g-.05)*(R+10)),(cx+math.cos(g)*L,cy+math.sin(g)*L),(cx+math.cos(g+.05)*(R+10),cy+math.sin(g+.05)*(R+10))],fill=col+(150,))
        pr=R+20+(fk%6)*10; od.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],outline=(255,255,255,220),width=8)
        lay.alpha_composite(ov)
        (draw_a if fz=='wave' else draw_b)()
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
        col=TC if side==0 else SC; x0=140 if side==0 else 610; y0=1290
        ctext(d,x0+165,y0,f'HP {hp}',font(54),col)
        d.rounded_rectangle([x0,y0+70,x0+330,y0+100],radius=10,outline=col,width=3)
        d.rounded_rectangle([x0+4,y0+74,x0+4+322*hp/100,y0+96],radius=8,fill=col)
        sk=('shell','bite','wave') if side==0 else ('spray','cloud','bomb')
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
        txt=('TURTLE' if r['win']=='a' else 'SKUNK')+' WINS!'; ctext(d,W/2,1660,txt,font(96),TC if r['win']=='a' else SC)
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
