import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sim2 as S
from sim2 import LW,LX,TOP,PR,GLASS_TOP,GLASS_BOT,CAP,TILES,PERIOD,CONV,GATE_Y,TRAP,PEGS,BAR,mirror,glass_x
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=S.simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920; random.seed(4)
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch,s):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); im=im.crop(im.getbbox()); return im.resize((s,int(s*im.size[1]/im.size[0])),Image.LANCZOS)
FRUIT=[emoji('🍓',120),emoji('🫐',120)]; SPONGE=emoji('🧽',54); CROWN=emoji('👑',80)
LIQ=[(230,30,80),(60,80,235)]; LIQD=[(120,0,35),(20,25,120)]; LIQ2=[(255,140,170),(150,170,255)]; NEON=[(255,70,120),(80,140,255)]
NAME=['STRAWBERRY','BLUEBERRY']
TC={1:(70,70,85),2:(40,130,230),3:(30,180,110),5:(160,70,230),10:(255,180,0)}
END=100; INTRO_OVL=48
def ctext(d,cx,y,t,fn,fill,sw=4,sf=(0,0,0)):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=sf)
def sphere(rad,col,hi):
    n=rad*4; im=Image.new('RGBA',(n,n),(0,0,0,0)); d=ImageDraw.Draw(im)
    for k in range(rad*2,0,-1):
        t=k/(rad*2); c=tuple(int(col[i]*(0.55+0.45*(1-t))+hi[i]*0.0) for i in range(3))
        d.ellipse([n/2-k,n/2-k,n/2+k,n/2+k],fill=c+(255,))
    d.ellipse([n/2-rad*0.9,n/2-rad*1.1,n/2-rad*0.1,n/2-rad*0.4],fill=hi+(200,))
    return im.resize((rad*2,rad*2),Image.LANCZOS)
DROP=[sphere(PR,LIQ[s],(255,255,255)) for s in (0,1)]
PEG=sphere(10,(190,195,215),(255,255,255))
# ---------- static background ----------
bg=Image.new('RGBA',(W,H)); px=bg.load()
top=(26,14,46); bot=(8,20,40)
grad=Image.new('RGBA',(1,H))
for y in range(H): t=y/H; grad.putpixel((0,y),tuple(int(top[i]*(1-t)+bot[i]*t) for i in range(3))+(255,))
bg=grad.resize((W,H))
bok=Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(bok)
for _ in range(26):
    x,y,rr=random.uniform(0,W),random.uniform(0,H),random.uniform(20,70); c=random.choice([NEON[0],NEON[1],(255,220,120)])
    bd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=c+(28,))
bg.alpha_composite(bok.filter(ImageFilter.GaussianBlur(18)))
glow=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
for s in (0,1):
    ox=LX[s]; gd.rounded_rectangle([ox-6,TOP-40,ox+LW+6,GLASS_TOP-36],radius=28,outline=NEON[s]+(255,),width=10)
bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
d=ImageDraw.Draw(bg)
for s in (0,1):
    ox=LX[s]; pan=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(pan).rounded_rectangle([ox-6,TOP-40,ox+LW+6,GLASS_TOP-36],radius=28,fill=(255,255,255,14)); bg.alpha_composite(pan); d=ImageDraw.Draw(bg)
    d.rounded_rectangle([ox-6,TOP-40,ox+LW+6,GLASS_TOP-36],radius=28,outline=NEON[s]+(255,),width=4)
    for (pxx,py,pr) in PEGS: bg.alpha_composite(PEG,(int(mirror(pxx,s)+ox-10),int(py-10)))
    tx0,tx1,ty=TRAP
    if s==1: tx0,tx1=LW-tx1,LW-tx0
    for k in range(3): bg.alpha_composite(SPONGE,(int(ox+tx0+(tx1-tx0)*(k+.5)/3-27),int(ty-18)))
f1=font(60); P=[('STRAWBERRY',LIQ2[0]),(' vs ',(235,235,235)),('BLUEBERRY',LIQ2[1])]
tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
for p,c in P: d.text((x,70),p,font=f1,fill=c,stroke_width=4,stroke_fill=(0,0,0)); x+=d.textlength(p,font=f1)
# glass liquid gradient textures
GH=GLASS_BOT-GLASS_TOP
LTEX=[]
for s in (0,1):
    g=Image.new('RGBA',(1,GH))
    for y in range(GH): t=y/GH; g.putpixel((0,y),tuple(int(LIQ[s][i]*(1-t)+LIQD[s][i]*t) for i in range(3))+(240,))
    LTEX.append(g.resize((420,GH)))
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','17',OUT],stdin=subprocess.PIPE)
pops=[]; spill=[]; ripples=[]; pegflash={}; sparks=[]
total=len(F)+END; win=r['win']; lose=1-win
for t in range(total):
    ending=t>=len(F); fi=min(t,len(F)-1); fr=F[fi]
    im=bg.copy(); d=ImageDraw.Draw(im)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    if not ending:
        for (s,pxx,py) in fr['hp']: pegflash[(s,pxx,py)]=6
    for k,v in list(pegflash.items()):
        s,pxx,py=k; X=LX[s]+pxx; a=int(40*v)
        ld.ellipse([X-16,py-16,X+16,py+16],fill=NEON[s]+(a,)); pegflash[k]=v-1
        if v<=1: del pegflash[k]
    for s in (0,1):
        ox=LX[s]
        # fruit squeezing
        sc=1+0.07*math.sin(t*0.8+s); fimg=FRUIT[s].resize((int(120*sc),int(FRUIT[s].size[1]*sc)))
        im.alpha_composite(fimg,(int(ox+LW/2-fimg.size[0]/2),int(TOP-40-fimg.size[1]*0.75)))
        # conveyor
        base=-(fi*CONV)%PERIOD-PERIOD
        while base<LW:
            acc=0
            for m,w in TILES:
                a0,a1=base+acc,base+acc+w; acc+=w
                x0,x1=(a0,a1) if s==0 else (LW-a1,LW-a0)
                x0c,x1c=max(x0,0),min(x1,LW)
                if x1c-x0c>12:
                    c=TC[m]; d.rounded_rectangle([ox+x0c+2,GATE_Y-22,ox+x1c-2,GATE_Y+22],radius=8,fill=c)
                    d.rounded_rectangle([ox+x0c+5,GATE_Y-19,ox+x1c-5,GATE_Y-8],radius=5,fill=tuple(min(255,v+60) for v in c))
                    if x1c-x0c>=w-6: ctext(d,ox+(x0c+x1c)/2,GATE_Y-16,f'x{m}',font(26),(255,255,255),3)
                    if m==10 and random.random()<.5: sparks.append([ox+random.uniform(x0c,x1c),GATE_Y+random.uniform(-20,20),0])
            base+=PERIOD
        bx,by,bl=BAR; a=fr['ang'] if s==0 else -fr['ang']
        p0=(ox+bx-math.cos(a)*bl,by-math.sin(a)*bl); p1=(ox+bx+math.cos(a)*bl,by+math.sin(a)*bl)
        ld.line([p0,p1],fill=NEON[s]+(90,),width=26); d.line([p0,p1],fill=(250,250,255),width=12)
        for p in (p0,p1): d.ellipse([p[0]-6,p[1]-6,p[0]+6,p[1]+6],fill=(250,250,255))
        d.ellipse([ox+bx-11,by-11,ox+bx+11,by+11],fill=(255,210,0))
    im.alpha_composite(lay); d=ImageDraw.Draw(im)
    # drops
    for s in (0,1):
        ox=LX[s]
        for (x,y,vx,vy) in fr['ds'][s]:
            if y>GLASS_TOP-90:
                lim=glass_x(max(y,GLASS_TOP))-PR-6
                if abs(x-LW/2)>lim: k=min(1,(y-(GLASS_TOP-90))/60); x=LW/2+max(-lim,min(lim,x-LW/2))*k+(x-LW/2)*(1-k)
            X=ox+x
            d.line([X,y,X-vx*1.6,y-vy*1.6],fill=LIQ[s],width=int(PR*1.4))
            im.alpha_composite(DROP[s],(int(X-PR),int(y-PR)))
    # glasses
    lead=0 if fr['lvl'][0]>fr['lvl'][1] else (1 if fr['lvl'][1]>fr['lvl'][0] else None)
    for s in (0,1):
        ox=LX[s]; cx=ox+LW/2; lv=min(fr['lvl'][s],CAP)/CAP; surf=GLASS_BOT-GH*lv
        if not ending:
            for e in EV.get(fi,[]):
                if e[1]=='drop' and e[2]==s and random.random()<.5: ripples.append([s,ox+min(max(e[3],LW/2-150),LW/2+150),0])
        if lv>0:
            pts=[(cx-glass_x(surf)+2*glass_x(surf)*k/40, surf+math.sin(k*.5+t*.35)*4) for k in range(41)]
            pts+=[(cx+glass_x(GLASS_BOT),GLASS_BOT),(cx-glass_x(GLASS_BOT),GLASS_BOT)]
            mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).polygon(pts,fill=255)
            tex=Image.new('RGBA',(W,H),(0,0,0,0)); tex.paste(LTEX[s],(int(cx-210),GLASS_TOP))
            im.paste(tex,(0,0),Image.composite(tex.getchannel('A'),Image.new('L',(W,H),0),mask))
            d=ImageDraw.Draw(im)
            # foam
            for k in range(18):
                fx=cx-glass_x(surf)+12+(2*glass_x(surf)-24)*k/17; fy=surf+math.sin(k*.5+t*.35)*4
                rr=7+3*math.sin(k*1.7+t*.2); d.ellipse([fx-rr,fy-rr,fx+rr,fy+rr],fill=LIQ2[s])
            for k in range(10):
                bx_=cx+((k*73+t*3)%300)-150; by_=GLASS_BOT-((k*131+t*5)%int(max(GLASS_BOT-surf,1)))
                if abs(bx_-cx)<glass_x(by_)-12 and by_>surf+12: d.ellipse([bx_-4,by_-4,bx_+4,by_+4],outline=LIQ2[s],width=2)
        for rp in ripples:
            if rp[0]==s:
                rp[2]+=1; rw=8+rp[2]*4; d.ellipse([rp[1]-rw,surf-rw*.3,rp[1]+rw,surf+rw*.3],outline=(255,255,255),width=2)
        # glass body
        danger=lv>=0.9 and not ending
        gc=(255,60,60) if danger and (t//4)%2==0 else (225,235,245)
        gp=[(cx-glass_x(GLASS_TOP),GLASS_TOP),(cx+glass_x(GLASS_TOP),GLASS_TOP),(cx+glass_x(GLASS_BOT),GLASS_BOT),(cx-glass_x(GLASS_BOT),GLASS_BOT)]
        d.line(gp+[gp[0]],fill=gc,width=8,joint='curve')
        d.ellipse([gp[0][0]-6,GLASS_TOP-10,gp[1][0]+6,GLASS_TOP+10],outline=gc,width=4)
        d.line([gp[3][0]+22,GLASS_BOT-30,gp[0][0]+28,GLASS_TOP+40],fill=(255,255,255),width=7)
        d.line([gp[3][0]+40,GLASS_BOT-50,gp[0][0]+44,GLASS_TOP+120],fill=(255,255,255),width=3)
        for xx in range(int(cx-glass_x(GLASS_TOP)+14),int(cx+glass_x(GLASS_TOP)-14),30): d.line([xx,GLASS_TOP+16,xx+15,GLASS_TOP+16],fill=(255,255,255),width=4)
        pct=int(lv*100); ctext(d,cx,GLASS_BOT-250,f'{pct}%',font(90),(255,255,255),7)
        if lead==s and not ending:
            im.alpha_composite(CROWN,(int(cx-40),int(GLASS_TOP-120+math.sin(t*.3)*6)))
        if ending and s==win: im.alpha_composite(CROWN.resize((120,int(CROWN.size[1]*1.5))),(int(cx-60),int(GLASS_TOP-170)))
    ripples[:]=[rp for rp in ripples if rp[2]<12]
    d=ImageDraw.Draw(im)
    for sp in sparks:
        sp[2]+=1; a=6-sp[2]; d.line([sp[0]-a,sp[1],sp[0]+a,sp[1]],fill=(255,255,220),width=2); d.line([sp[0],sp[1]-a,sp[0],sp[1]+a],fill=(255,255,220),width=2)
    sparks[:]=[sp for sp in sparks if sp[2]<6]
    if not ending:
        for e in EV.get(fi,[]):
            if e[1]=='mult' and e[3]>=5 and not any(p[6]==e[2] and p[4]<10 for p in pops):
                pops.append([LX[e[2]]+min(max(e[4],70),LW-70),GATE_Y-64,f'x{e[3]}!',TC[e[3]],0,54 if e[3]<10 else 72,e[2]])
    if ending:
        k=t-len(F); cx=LX[win]+LW/2
        if k<70:
            for side in (-1,1):
                for _ in range(3): spill.append([cx+side*glass_x(GLASS_TOP),GLASS_TOP-4,side*random.uniform(2,6),random.uniform(-6,-1),0,LIQ[win]])
        if k<8:
            for _ in range(16): spill.append([cx+random.uniform(-180,180),GLASS_TOP,random.uniform(-7,7),random.uniform(-20,-8),0,random.choice([LIQ[win],LIQ2[win],(255,255,255)])])
    for p in spill:
        p[0]+=p[2]; p[1]+=p[3]; p[3]+=0.6; p[4]+=1; rr=9 if p[5]!=(255,255,255) else 6; d.ellipse([p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr],fill=p[5])
    spill[:]=[p for p in spill if p[1]<H+20]
    for p in pops:
        p[4]+=1; sc=1+max(0,(4-p[4]))*0.12; ctext(d,p[0],p[1]-p[4]*2,p[2],font(int(p[5]*sc)),p[3],5)
    pops[:]=[p for p in pops if p[4]<24]
    if t<INTRO_OVL:
        a=1 if t<INTRO_OVL-8 else (INTRO_OVL-t)/8
        if a>0.05:
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); od.rounded_rectangle([60,960,W-60,1130],radius=30,fill=(0,0,0,int(210*a)))
            im.alpha_composite(ov); d=ImageDraw.Draw(im)
            ctext(d,W/2,975,'FIRST TO OVERFLOW',font(74),(255,255,255),5); ctext(d,W/2,1062,'WINS',font(50),(255,215,0),4)
    if ending and t-len(F)>=12:
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); od.rounded_rectangle([50,930,W-50,1140],radius=30,fill=(0,0,0,215)); im.alpha_composite(ov); d=ImageDraw.Draw(im)
        ctext(d,W/2,945,f'{NAME[win]} WINS!',font(92),LIQ2[win],6)
        l=r['lvl']; ctext(d,W/2,1060,f'{min(l[0],CAP)*100//CAP}%  vs  {min(l[1],CAP)*100//CAP}%',font(52),(255,255,255),4)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=0,n=len(F),end=END,win=win,cap=CAP),open(OUT+'.json','w')); print('done',total)
