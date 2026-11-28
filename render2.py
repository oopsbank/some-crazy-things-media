import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sim2 as S
from sim2 import N, CS, AX, AY, TOTAL, TARGET, TL
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=S.simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920; random.seed(3)
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch,s):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); im=im.crop(im.getbbox()); return im.resize((s,int(s*im.size[1]/im.size[0])),Image.LANCZOS)
NAME=['FIRE','WATER']; COL=[(235,80,35),(35,110,235)]; LIGHT=[(255,180,120),(150,200,255)]
ICON=[emoji('🔥',96),emoji('💧',86)]; BI=[emoji('🔥',30),emoji('💧',28)]
IT={'star':emoji('⭐',54),'bomb':emoji('💣',54),'bolt':emoji('⚡',54)}
SKN=['METEOR','TSUNAMI']; PICKTXT={'star':'+3 BALLS','bomb':'BOMB!','bolt':'SPEED!'}
pal=np.array(COL,dtype=np.float32)
def ctext(d,cx,y,t,fn,fill,sw=4):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
g=np.zeros((N,N),dtype=np.int64)
for i in range(N): g[:,i]=0 if i<N//2 else 1
flash=np.zeros((N,N),dtype=np.float32)
lines=Image.new('RGBA',(N*CS,N*CS),(0,0,0,0)); ld=ImageDraw.Draw(lines)
for k in range(N+1): ld.line([k*CS,0,k*CS,N*CS],fill=(0,0,0,40)); ld.line([0,k*CS,N*CS,k*CS],fill=(0,0,0,40))
bg=Image.new('RGBA',(W,H),(12,12,20,255))
grad=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(grad)
gd.rectangle([0,0,W//2,H],fill=COL[0]+(40,)); gd.rectangle([W//2,0,W,H],fill=COL[1]+(40,))
bg.alpha_composite(grad.filter(ImageFilter.GaussianBlur(120)))
END=100
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','17',OUT],stdin=subprocess.PIPE)
fx=[]; pops=[]; banner=[]; shake=0; total=len(F)+END; win=r['win']
for t in range(total):
    ending=t>=len(F); fi=min(t,len(F)-1); fr=F[fi]
    if not ending:
        for (i,j,o) in fr['conv']: g[j,i]=o; flash[j,i]=1.0
        shake=max(shake,fr['shake'])
        for e in EV.get(fi,[]):
            if e[1]=='cast': banner.append([f'{NAME[e[2]]}: {SKN[e[2]]}!',LIGHT[e[2]],0]); 
            if e[1]=='meteor': fx.append(['meteor',AX+e[2]*CS+CS/2,AY+e[3]*CS+CS/2,0])
            if e[1]=='wave': fx.append(['wave',0,AY+e[2]*CS+CS/2,0])
            if e[1]=='last': banner.append([f'{NAME[e[2]]}: LAST STAND!',(255,230,80),-10]); fx.append(['flash',0,0,0])
            if e[1]=='pick': pops.append([AX+e[4],AY+e[5]-40,PICKTXT[e[3]],LIGHT[e[2]],0]); fx.append(['ring',AX+e[4],AY+e[5],0,e[2]])
            if e[1]=='pick' and e[3]=='bomb': fx.append(['boom',AX+e[4],AY+e[5],0])
    rgb=pal[g]*(1-flash[...,None]*0.65)+255*flash[...,None]*0.65; flash*=0.8
    gim=Image.fromarray(rgb.astype(np.uint8),'RGB').resize((N*CS,N*CS),Image.NEAREST).convert('RGBA'); gim.alpha_composite(lines)
    lay=Image.new('RGBA',(N*CS,N*CS),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    if not ending:
        for (kind,x,y) in fr['items']:
            if kind:
                ic=IT[kind]; s=1+0.12*math.sin(t*.3); ic2=ic.resize((int(ic.size[0]*s),int(ic.size[1]*s)))
                ld.ellipse([x-34,y-34,x+34,y+34],fill=(255,255,255,90)); lay.alpha_composite(ic2,(int(x-ic2.size[0]/2),int(y-ic2.size[1]/2)))
        for (tm,x,y) in fr['balls']:
            rr=19; ld.ellipse([x-rr-3,y-rr-3,x+rr+3,y+rr+3],fill=(255,255,255,255)); ld.ellipse([x-rr,y-rr,x+rr,y+rr],fill=tuple(int(c*.7) for c in COL[tm])+(255,))
            if fr['boost'][tm]>0: ld.ellipse([x-rr-9,y-rr-9,x+rr+9,y+rr+9],outline=(255,240,90,200),width=4)
            ic=BI[tm]; lay.alpha_composite(ic,(int(x-ic.size[0]/2),int(y-ic.size[1]/2)))
    gim.alpha_composite(lay)
    im=bg.copy(); d=ImageDraw.Draw(im)
    ox=oy=0
    if shake>0: ox,oy=random.randint(-shake,shake),random.randint(-shake,shake); shake-=1
    gl=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(gl).rectangle([AX-8+ox,AY-8+oy,AX+N*CS+8+ox,AY+N*CS+8+oy],outline=(255,255,255,255),width=10)
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(9)))
    im.paste(gim,(AX+ox,AY+oy)); d=ImageDraw.Draw(im)
    d.rectangle([AX-4+ox,AY-4+oy,AX+N*CS+4+ox,AY+N*CS+4+oy],outline=(255,255,255),width=4)
    # effects over arena
    fl=Image.new('RGBA',(W,H),(0,0,0,0)); fd=ImageDraw.Draw(fl)
    for e in fx:
        e[3]+=1; k=e[3]
        if e[0]=='meteor':
            if k<8: y0=e[2]-(8-k)*60; fd.line([e[1]+(8-k)*30,y0-40,e[1]+(8-k)*30-30,y0+20],fill=(255,200,80,255),width=14)
            else: rr=(k-8)*12; fd.ellipse([e[1]-rr,e[2]-rr,e[1]+rr,e[2]+rr],outline=(255,140,30,max(0,255-(k-8)*30)),width=12)
        elif e[0]=='wave':
            x=AX+N*CS-k*60; fd.rectangle([x,e[2]-70,x+40,e[2]+70],fill=(180,220,255,max(0,220-k*12)))
        elif e[0]=='ring':
            rr=20+k*8; fd.ellipse([e[1]-rr,e[2]-rr,e[1]+rr,e[2]+rr],outline=LIGHT[e[4]]+(max(0,255-k*25),),width=6)
        elif e[0]=='boom':
            rr=20+k*16; fd.ellipse([e[1]-rr,e[2]-rr,e[1]+rr,e[2]+rr],fill=(255,230,150,max(0,200-k*20)))
        elif e[0]=='flash': fd.rectangle([0,0,W,H],fill=(255,255,255,max(0,180-k*30)))
    fx[:]=[e for e in fx if e[3]<20]
    im.alpha_composite(fl); d=ImageDraw.Draw(im)
    # header
    cnt=fr['cnt']; p0=cnt[0]*100/TOTAL; p1=100-p0
    im.alpha_composite(ICON[0],(70,70)); im.alpha_composite(ICON[1],(W-70-ICON[1].size[0],76))
    ld0=cnt[0]>=cnt[1]
    ctext(d,330,60,f'{p0:.0f}%',font(118 if ld0 else 96),LIGHT[0],6); ctext(d,W-330,60,f'{p1:.0f}%',font(118 if not ld0 else 96),LIGHT[1],6)
    ctext(d,W/2,96,'VS',font(48),(255,255,255),4)
    # tug bar with goal lines
    bx0,bx1,by=60,W-60,250; d.rounded_rectangle([bx0,by,bx1,by+60],radius=30,fill=COL[1])
    mid=bx0+(bx1-bx0)*cnt[0]/TOTAL; d.rounded_rectangle([bx0,by,max(mid,bx0+60),by+60],radius=30,fill=COL[0]); d.rectangle([mid-6,by-8,mid+6,by+68],fill=(255,255,255))
    for gx in (bx0+(bx1-bx0)*TARGET/TOTAL, bx0+(bx1-bx0)*(1-TARGET/TOTAL)):
        for yy in range(by-18,by+78,12): d.line([gx,yy,gx,yy+6],fill=(255,230,80),width=5)
    d.rounded_rectangle([bx0,by,bx1,by+60],radius=30,outline=(255,255,255),width=4)
    ctext(d,bx0+(bx1-bx0)*TARGET/TOTAL,by+76,'WIN',font(28),(255,230,80),3); ctext(d,bx0+(bx1-bx0)*(1-TARGET/TOTAL),by+76,'WIN',font(28),(255,230,80),3)
    # skill bars small
    for tm in (0,1):
        prog=1-max(fr['cd'][tm],0)/S.SK_CD[tm] if not ending else 0
        x0=60 if tm==0 else W/2+20; x1=W/2-20 if tm==0 else W-60
        d.rounded_rectangle([x0,390,x1,432],radius=12,outline=(200,200,210),width=3)
        if prog>.02: d.rounded_rectangle([x0+4,394,x0+4+(x1-x0-8)*prog,428],radius=10,fill=COL[tm] if prog<.97 else (255,255,255))
        ctext(d,(x0+x1)/2,395,SKN[tm],font(28),(255,255,255),3)
    # banners & pops
    for b in banner: b[2]+=1
    banner[:]=[b for b in banner if b[2]<24]
    if banner and not ending:
        b=banner[-1]; sc=1.3 if b[2]<4 else 1; ctext(d,W/2,AY+N*CS+30,b[0],font(int(60*sc)),b[1],6)
    for p in pops:
        p[4]+=1; ctext(d,p[0],p[1]-p[4]*2,p[2],font(46),p[3],5)
    pops[:]=[p for p in pops if p[4]<26]
    if not ending:
        secs=max(0,math.ceil((TL-fi)/30)); ctext(d,W/2,1600,f'{secs}s',font(64),(255,90,90) if secs<=5 else (200,200,210),4)
    if t<45:
        a=min(1,(45-t)/8)
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).rounded_rectangle([80,AY+340,W-80,AY+600],radius=30,fill=(0,0,0,int(215*a))); im.alpha_composite(ov); d=ImageDraw.Draw(im)
        if a>.1: ctext(d,W/2,AY+362,'REACH THE',font(80),(255,255,255),6); ctext(d,W/2,AY+460,'WIN LINE FIRST',font(80),(255,220,0),6)
    if ending and t-len(F)>=8:
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).rounded_rectangle([60,AY+330,W-60,AY+630],radius=30,fill=(0,0,0,225)); im.alpha_composite(ov); d=ImageDraw.Draw(im)
        im.alpha_composite(ICON[win],(int(W/2-ICON[win].size[0]/2),AY+345)); d=ImageDraw.Draw(im)
        ctext(d,W/2,AY+470,f'{NAME[win]} WINS!',font(110),LIGHT[win],6)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],n=len(F),end=END,win=win,conv=[len(f['conv']) for f in F]),open(OUT+'.json','w')); print('done',total)
