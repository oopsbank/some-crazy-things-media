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
pops=[]; flashes=[]; parts=[]; ghosts=[]; blasts=[]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill,**kw):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,**kw)
total=INTRO+len(F)+END; loser='b' if r['win']=='a' else 'a'
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; ending=t>=INTRO+len(F); live=INTRO<=t<INTRO+len(F)
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
            if k=='block': pops.append([px+random.uniform(-30,10),py-70,'BLOCK',BR,0,36]); continue
            col={'bite':TC,'bump':(255,255,255),'spray':GAS,'gas':GAS,'wave':WV,'bomb':BM}[k]
            pops.append([px+random.uniform(-30,30),py-70,f'-{dm}',col,0,38 if k=='gas' else (72 if k in('wave','bomb') else 52)])
        if fr['bite']: ghosts.append([ax,ay,0])
        for (ex,ey) in fr['booms']: blasts.append([ex,ey,0])
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    # stink clouds (under everything)
    if not ending:
        for (cx,cy,life) in fr['clouds']:
            al=int(70*min(1,life/30)*min(1,(CLOUD_T-life+1)/10))
            for k in range(5):
                ang=k/5*6.28+t*0.03+cx; ox,oy=math.cos(ang)*60,math.sin(ang)*60; rr=CLOUD_R-50
                ld.ellipse([cx+ox-rr,cy+oy-rr,cx+ox+rr,cy+oy+rr],fill=GAS+(al,))
    if not ending:
        for (wx,wy,wr) in fr['waves']:
            for k,(dr,al) in enumerate([(0,230),(-22,150),(-44,80)]):
                rr=wr+dr
                if rr>0: ld.ellipse([wx-rr,wy-rr,wx+rr,wy+rr],outline=WV+(al,),width=14-k*4)
        for (px,py) in fr['bombs']:
            ld.ellipse([px-20,py-20,px+20,py+20],fill=BM+(255,),outline=(255,255,255,255),width=4)
            ld.line([px+10,py-16,px+20,py-30],fill=(255,220,60,255),width=5)
    for e in blasts:
        e[2]+=1; k=e[2]; rr=BOMB_R*min(1,k/6); al=max(0,200-k*12)
        if al>0:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).ellipse([e[0]-rr,e[1]-rr,e[0]+rr,e[1]+rr],fill=BM+(al//2,),outline=GAS+(al,),width=10); lay.alpha_composite(ov)
    blasts[:]=[e for e in blasts if e[2]<18]
    for g in ghosts:
        g[2]+=1; a=max(0,140-g[2]*14)
        if a>0: ld.ellipse([g[0]-R,g[1]-R,g[0]+R,g[1]+R],outline=TC+(a,),width=4)
    ghosts[:]=[g for g in ghosts if g[2]<10]
    for (px,py,a) in fr['proj'] if not ending else []:
        ld.ellipse([px-12,py-12,px+12,py+12],fill=(200,230,70,235)); ld.ellipse([px-5,py-5,px+5,py+5],fill=(255,255,200,255))
    def draw_a():
        if fr['bite'] and not ending: ld.ellipse([ax-R-14,ay-R-14,ax+R+14,ay+R+14],fill=TC+(90,))
        if fr['gas'] and not fr['shell'] and not ending: ld.ellipse([ax-R-8,ay-R-8,ax+R+8,ay+R+8],outline=GAS+(255,),width=8)
        ld.ellipse([ax-R,ay-R,ax+R,ay+R],fill=(30,130,100),outline=(255,255,255),width=5)
        lay.alpha_composite(EA,(int(ax-43),int(ay-43)))
        if fr['shell'] and not ending:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).ellipse([ax-R-16,ay-R-16,ax+R+16,ay+R+16],fill=BR+(90,)); lay.alpha_composite(ov)
            ld.ellipse([ax-R-16,ay-R-16,ax+R+16,ay+R+16],outline=(240,200,140,255),width=7)
            for k in range(6):
                g=k/6*6.28+t*0.05; ld.line([ax+math.cos(g)*(R+2),ay+math.sin(g)*(R+2),ax+math.cos(g)*(R+16),ay+math.sin(g)*(R+16)],fill=(240,200,140,255),width=5)
    def draw_b():
        ld.ellipse([bx-R,by-R,bx+R,by+R],fill=(45,45,60),outline=(255,255,255),width=5)
        lay.alpha_composite(EB,(int(bx-43),int(by-43)))
    if ending:
        k=t-(INTRO+len(F))
        if k==0:
            lx,ly,col=(ax,ay,TC) if loser=='a' else (bx,by,SC)
            for _ in range(70):
                g=random.uniform(0,6.28); v=random.uniform(4,18); parts.append([lx,ly,math.cos(g)*v,math.sin(g)*v,col])
        draw_b() if loser=='a' else draw_a()
    else: draw_a(); draw_b()
    for fl in flashes:
        fl[4]+=1; c,fx,fy,col,k=fl
        if k<12: rr=R+k*12; ld.ellipse([fx-rr,fy-rr,fx+rr,fy+rr],outline=col+(max(0,255-k*20),),width=8)
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[2]*=.94; p[3]*=.94; ld.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill=p[4])
    for p in pops:
        p[4]+=1; a=max(0,255-p[4]*10); ld.text((p[0]-30,p[1]-p[4]*2),p[2],font=font(p[5]),fill=p[3]+(a,),stroke_width=3,stroke_fill=(0,0,0,a))
    pops[:]=[p for p in pops if p[4]<26]
    im.alpha_composite(lay); d=ImageDraw.Draw(im)
    cur=[f for f in flashes if f[4]<24]
    if cur and not ending:
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
            yy=y0+125+j*62; prog=1-max(fr['cd'][k],0)/CD[k] if live else (0 if t<INTRO else 1)
            ready=prog>.97
            d.rounded_rectangle([x0,yy,x0+330,yy+46],radius=12,outline=(255,215,60) if j==2 else (200,200,200),width=3)
            d.rounded_rectangle([x0+4,yy+4,x0+4+322*prog,yy+42],radius=10,fill=SKCOL[k] if not ready else (255,255,255))
            lab=NAMES[k].rstrip('!'); fl=font(28); w=d.textlength(lab,font=fl)
            d.text((x0+165-w/2,yy+7),lab,font=fl,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    if t<INTRO: ctext(d,W/2,780,'WHO WINS?',font(110),(255,255,255))
    if ending and t-(INTRO+len(F))>=12:
        txt=('TURTLE' if r['win']=='a' else 'SKUNK')+' WINS!'; ctext(d,W/2,1660,txt,font(96),TC if r['win']=='a' else SC)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=r['win']),open(OUT+'.json','w')); print('done',total)
