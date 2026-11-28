import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim import *
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch,s):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); im=im.crop(im.getbbox()); return im.resize((s,int(s*im.size[1]/im.size[0])),Image.LANCZOS)
ICON=[emoji('🍓',70),emoji('🫐',70)]; SPONGE=emoji('🧽',46)
LIQ=[(225,35,75),(70,80,225)]; LIQ2=[(255,120,150),(140,160,255)]; NAME=['STRAWBERRY','BLUEBERRY']
TC={1:(80,80,90),2:(60,140,220),3:(60,180,120),5:(170,90,220),10:(255,190,0)}
INTRO=40; END=90
def ctext(d,cx,y,t,fn,fill,sw=4):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
bg=Image.new('RGBA',(W,H),(10,10,18,255)); d=ImageDraw.Draw(bg)
f1=font(58); P=[('STRAWBERRY',LIQ2[0]),(' vs ',(230,230,230)),('BLUEBERRY',LIQ2[1])]
tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
for p,c in P: d.text((x,170),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
bg.alpha_composite(ICON[0],(int(W/2-tw/2-10),70)); bg.alpha_composite(ICON[1],(int(W/2+tw/2-60),70))
for s in (0,1):
    ox=LX[s]; d.rectangle([ox-4,TOP-14,ox+LW+4,GLASS_TOP-40],outline=(110,110,125),width=4)
    for (px,py,pr) in PEGS:
        px=mirror(px,s)+ox; d.ellipse([px-pr,py-pr,px+pr,py+pr],fill=(200,200,215))
    tx0,tx1,ty=TRAP
    if s==1: tx0,tx1=LW-tx1,LW-tx0
    d.rounded_rectangle([ox+tx0,ty-10,ox+tx1,ty+14],radius=10,fill=(235,200,60))
    for xx in range(int(ox+tx0)+12,int(ox+tx1)-10,40): d.ellipse([xx-5,ty-3,xx+5,ty+7],fill=(190,150,30))
    bg.alpha_composite(SPONGE,(int(ox+(tx0+tx1)/2-23),int(ty-52)))
def glass_poly(cx): return [(cx-glass_x(GLASS_TOP),GLASS_TOP),(cx+glass_x(GLASS_TOP),GLASS_TOP),(cx+glass_x(GLASS_BOT),GLASS_BOT),(cx-glass_x(GLASS_BOT),GLASS_BOT)]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
pops=[]; spill=[]
total=INTRO+len(F)+END; win=r['win']
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; live=INTRO<=t<INTRO+len(F); ending=t>=INTRO+len(F); fi=max(t-INTRO,0) if not ending else len(F)-1
    im=bg.copy(); d=ImageDraw.Draw(im)
    for s in (0,1):
        ox=LX[s]
        # conveyor tiles
        base=-(fi*CONV)%PERIOD - PERIOD
        while base<LW:
            acc=0
            for m,w in TILES:
                a0,a1=base+acc,base+acc+w; acc+=w
                x0,x1=(a0,a1) if s==0 else (LW-a1,LW-a0)
                x0c,x1c=max(x0,0),min(x1,LW)
                if x1c-x0c>2:
                    d.rectangle([ox+x0c+1,GATE_Y-20,ox+x1c-1,GATE_Y+20],fill=TC[m])
                    if x1c-x0c>=w-4: ctext(d,ox+(x0c+x1c)/2,GATE_Y-17,f'x{m}',font(26 if m<10 else 24),(255,255,255),2)
            base+=PERIOD
        bx,by,bl=BAR; a=fr['ang'] if s==0 else -fr['ang']
        d.line([ox+bx-math.cos(a)*bl,by-math.sin(a)*bl,ox+bx+math.cos(a)*bl,by+math.sin(a)*bl],fill=(255,255,255),width=12); d.ellipse([ox+bx-10,by-10,ox+bx+10,by+10],fill=(255,210,0))
        for (x,y) in fr['ds'][s]:
            if y>GLASS_TOP-90:
                lim=glass_x(max(y,GLASS_TOP))-PR-6; k=min(1,(y-(GLASS_TOP-90))/60); x=LW/2+max(-lim,min(lim,x-LW/2))*k+(x-LW/2)*(1-k) if abs(x-LW/2)>lim else x
            X=ox+x; d.ellipse([X-PR,y-PR,X+PR,y+PR],fill=LIQ[s]); d.ellipse([X-5,y-6,X+1,y],fill=LIQ2[s])
        # glass
        cx=ox+LW/2; lv=min(fr['lvl'][s],CAP)/CAP; surf=GLASS_BOT-(GLASS_BOT-GLASS_TOP)*lv
        if lv>0:
            pts=[]
            for k in range(41):
                hx=-glass_x(surf)+2*glass_x(surf)*k/40; pts.append((cx+hx,surf+math.sin(k*.5+t*.3)*4))
            pts+= [(cx+glass_x(GLASS_BOT),GLASS_BOT),(cx-glass_x(GLASS_BOT),GLASS_BOT)]
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(lay).polygon(pts,fill=LIQ[s]+(235,)); im.alpha_composite(lay); d=ImageDraw.Draw(im)
            for k in range(6):
                bx_=cx+((k*73+t*3)%300)-150; by_=GLASS_BOT-((k*131+t*4)%int(max(GLASS_BOT-surf,1)))
                if abs(bx_-cx)<glass_x(by_)-10: d.ellipse([bx_-4,by_-4,bx_+4,by_+4],outline=LIQ2[s],width=2)
        gp=glass_poly(cx); d.line(gp+[gp[0]],fill=(220,230,240),width=7)
        d.line([gp[3][0]+20,GLASS_BOT-20,gp[0][0]+25,GLASS_TOP+30],fill=(255,255,255,90),width=6)
        for xx in range(int(cx-glass_x(GLASS_TOP)+10),int(cx+glass_x(GLASS_TOP)-10),30): d.line([xx,GLASS_TOP+6,xx+15,GLASS_TOP+6],fill=(255,255,255),width=4)
        ctext(d,cx+glass_x(GLASS_TOP)-30,GLASS_TOP-36,'FULL',font(26),(255,255,255),2)
        pct=int(lv*100); ctext(d,cx,GLASS_BOT-230,f'{pct}%',font(84 if pct<100 else 96),(255,255,255),6)
    if live:
        for e in EV.get(fi,[]):
            if e[1]=='mult' and e[3]>=5 and not any(p[6]==e[2] and p[4]<10 for p in pops): pops.append([LX[e[2]]+min(max(e[4],60),LW-60),GATE_Y-60,f'x{e[3]}!',TC[e[3]],0,50 if e[3]<10 else 66,e[2]])
    if ending:
        k=t-(INTRO+len(F)); cx=LX[win]+LW/2
        if k<55:
            for side in (-1,1):
                for _ in range(3): spill.append([cx+side*glass_x(GLASS_TOP),GLASS_TOP-4,side*random.uniform(2,6),random.uniform(-6,-1),0])
        if k<6:
            for _ in range(10): spill.append([cx+random.uniform(-180,180),GLASS_TOP,random.uniform(-5,5),random.uniform(-14,-6),0])
    for p in spill:
        p[0]+=p[2]; p[1]+=p[3]; p[3]+=0.6; p[4]+=1; d.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill=LIQ[win] if win is not None else (255,255,255))
    spill[:]=[p for p in spill if p[1]<H+20]
    for p in pops:
        p[4]+=1; ctext(d,p[0],p[1]-p[4]*2,p[2],font(p[5]),p[3],4)
    pops[:]=[p for p in pops if p[4]<24]
    if t<INTRO:
        d.rectangle([0,960,W,1120],fill=(0,0,0)); ctext(d,W/2,975,'FIRST TO OVERFLOW',font(76),(255,255,255)); ctext(d,W/2,1060,'WINS',font(48),(255,220,0))
    if ending and t-(INTRO+len(F))>=14:
        d.rectangle([0,960,W,1100],fill=(0,0,0)); ctext(d,W/2,975,f'{NAME[win]} WINS!',font(96),LIQ2[win],5)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=win,cap=CAP),open(OUT+'.json','w')); print('done',total)
