import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sim
from sim import N, CS, AX, AY
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=sim.simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920; random.seed(2)
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'; FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch,s):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); im=im.crop(im.getbbox()); return im.resize((s,int(s*im.size[1]/im.size[0])),Image.LANCZOS)
EM=['🔥','💧','🌿','⚡']; NAME=['FIRE','WATER','LEAF','BOLT']; SK=['EXPLOSION','SPLIT','GROW','BOLT']
COL=[(230,75,40),(40,115,230),(45,175,75),(235,190,20)]; LIGHT=[(255,190,150),(160,200,255),(170,240,180),(255,245,160)]
ICON=[emoji(e,58) for e in EM]; BALLI=[emoji(e,34) for e in EM]; BALLS=[emoji(e,24) for e in EM]
pal=np.array(COL,dtype=np.float32); lpal=np.array(LIGHT,dtype=np.float32)
def ctext(d,cx,y,t,fn,fill,sw=4):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
END=95; TL=1200
g=np.zeros((N,N),dtype=np.int64)   # g[y,x]
for i in range(N):
    for j in range(N): g[j,i]=(0 if i<N//2 else 1) if j<N//2 else (2 if i<N//2 else 3)
flash=np.zeros((N,N),dtype=np.float32)
lines=Image.new('RGBA',(N*CS,N*CS),(0,0,0,0)); ld=ImageDraw.Draw(lines)
for k in range(N+1): ld.line([k*CS,0,k*CS,N*CS],fill=(0,0,0,45)); ld.line([0,k*CS,N*CS,k*CS],fill=(0,0,0,45))
bg=Image.new('RGBA',(W,H),(14,14,24,255)); d=ImageDraw.Draw(bg)
ctext(d,W/2,24,'TERRITORY WAR',font(64),(255,255,255),5)
glow=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(glow).rectangle([AX-8,AY-8,AX+N*CS+8,AY+N*CS+8],outline=(255,255,255,255),width=8)
bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
ImageDraw.Draw(bg).rectangle([AX-5,AY-5,AX+N*CS+5,AY+N*CS+5],outline=(255,255,255),width=4)
CARD=[(40,112),(560,112),(40,262),(560,262)]; CW,CH=480,140
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','17',OUT],stdin=subprocess.PIPE)
fx=[]; banner=[]; total=len(F)+END; win=r['win']; final=F[-1]['cnt']
srt=sorted(final,reverse=True); margin=srt[0]-srt[1]
for t in range(total):
    ending=t>=len(F); fi=min(t,len(F)-1); fr=F[fi]
    if not ending:
        for (i,j,o) in fr['conv']: g[j,i]=o; flash[j,i]=1.0
        for e in EV.get(fi,[]):
            if e[1]=='cast':
                tm=e[2]; banner.append([tm,0]); fx.append([tm,AX+e[3],AY+e[4],0,None])
            if e[1]=='boltline': fx[-1][4]=e[4]
    # grid image
    rgb=pal[g]*(1-flash[...,None]*0.7)+lpal[g]*0+np.array([255,255,255],dtype=np.float32)*flash[...,None]*0.7
    flash*=0.82
    gim=Image.fromarray(rgb.astype(np.uint8),'RGB').resize((N*CS,N*CS),Image.NEAREST).convert('RGBA'); gim.alpha_composite(lines)
    im=bg.copy(); im.paste(gim,(AX,AY)); d=ImageDraw.Draw(im)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    # skill fx
    for e in fx:
        tm,x0,y0,k,ang=e; e[3]+=1
        if tm==0: rr=20+k*14; ld.ellipse([x0-rr,y0-rr,x0+rr,y0+rr],outline=(255,140,40,max(0,255-k*22)),width=12)
        elif tm==1: rr=20+k*8; ld.ellipse([x0-rr,y0-rr,x0+rr,y0+rr],outline=(120,190,255,max(0,255-k*22)),width=8)
        elif tm==2:
            for q in range(6): a=q*1.05+k*.2; rr=30+k*10; ld.ellipse([x0+math.cos(a)*rr-6,y0+math.sin(a)*rr-6,x0+math.cos(a)*rr+6,y0+math.sin(a)*rr+6],fill=(140,255,150,max(0,255-k*22)))
        elif ang is not None and k<10:
            pts=[(x0,y0)]
            for s in range(1,13):
                L=s*50; pts.append((x0+math.cos(ang)*L+random.uniform(-14,14),y0+math.sin(ang)*L+random.uniform(-14,14)))
            ld.line(pts,fill=(255,255,180,240-k*20),width=10); ld.line(pts,fill=(255,255,255,255-k*20),width=4)
    fx[:]=[e for e in fx if e[3]<12]
    im.alpha_composite(lay); d=ImageDraw.Draw(im)
    if not ending:
        for (tm,x,y,life) in fr['balls']:
            X,Y=AX+x,AY+y; rr=23 if life<0 else 16
            d.ellipse([X-rr-3,Y-rr-3,X+rr+3,Y+rr+3],fill=(255,255,255)); d.ellipse([X-rr,Y-rr,X+rr,Y+rr],fill=tuple(int(c*.75) for c in COL[tm]))
            ic=BALLI[tm] if life<0 else BALLS[tm]; im.alpha_composite(ic,(int(X-ic.size[0]/2),int(Y-ic.size[1]/2)))
    # cards
    cnt=fr['cnt']; lead=max(range(4),key=lambda q:cnt[q])
    for tm in range(4):
        x0,y0=CARD[tm]; alive=fr['alive'][tm]
        bc=COL[tm] if alive else (70,70,70)
        d.rounded_rectangle([x0,y0,x0+CW,y0+CH],radius=18,fill=(28,28,40),outline=bc,width=5 if (tm==lead or (ending and tm==win)) else 3)
        im.alpha_composite(ICON[tm],(x0+14,y0+12))
        d.text((x0+84,y0+12),NAME[tm],font=font(40),fill=bc)
        pct=cnt[tm]*100/(N*N); ptxt=f'{pct:.1f}%' if alive else 'OUT'
        fn=font(56); w=d.textlength(ptxt,font=fn); d.text((x0+CW-18-w,y0+6),ptxt,font=fn,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
        prog=1-max(fr['cd'][tm],0)/sim.CD[sim.TEAMS[tm]] if not ending else 0
        bx0,by0=x0+18,y0+84
        d.rounded_rectangle([bx0,by0,x0+CW-18,by0+38],radius=10,outline=(200,200,210),width=3)
        if prog>0.02: d.rounded_rectangle([bx0+4,by0+4,bx0+4+(CW-44)*prog,by0+34],radius=8,fill=COL[tm] if prog<0.97 else (255,255,255))
        fl=font(26); w=d.textlength(SK[tm],font=fl); d.text((x0+CW/2-w/2,by0+5),SK[tm],font=fl,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    # banner
    cur=[b for b in banner if b[1]<22]
    for b in banner: b[1]+=1
    banner[:]=cur
    if cur and not ending:
        tm=cur[-1][0]; ctext(d,W/2,AY+N*CS+22,f'{NAME[tm]}: {SK[tm]}!',font(56),LIGHT[tm],5)
    # timer + share bar
    secs=max(0,math.ceil((TL-fi)/30)) if not ending else 0
    tc=(255,80,80) if secs<=5 and not ending else (255,255,255)
    if not ending: ctext(d,W/2,1530,f'{secs}',font(120 if secs>5 else 140),tc,6)
    x=60
    for tm in range(4):
        w=(W-120)*cnt[tm]/(N*N); d.rectangle([x,1700,x+w,1750],fill=COL[tm]); x+=w
    d.rectangle([60,1700,W-60,1750],outline=(255,255,255),width=3)
    if t<45:
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).rounded_rectangle([80,AY+360,W-80,AY+600],radius=30,fill=(0,0,0,int(215*min(1,(45-t)/8)))); im.alpha_composite(ov); d=ImageDraw.Draw(im)
        a=min(1,(45-t)/8)
        if a>.1: ctext(d,W/2,AY+380,'MOST LAND',font(96),(255,255,255),6); ctext(d,W/2,AY+495,'AFTER 40s WINS',font(66),(255,215,0),5)
    if ending and t-len(F)>=10:
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ov).rounded_rectangle([60,AY+330,W-60,AY+630],radius=30,fill=(0,0,0,225)); im.alpha_composite(ov); d=ImageDraw.Draw(im)
        im.alpha_composite(ICON[win].resize((110,110)),(int(W/2-55),AY+345)); d=ImageDraw.Draw(im)
        ctext(d,W/2,AY+460,f'{NAME[win]} WINS!',font(104),LIGHT[win],6)
        if margin<=5: ctext(d,W/2,AY+575,f'BY {margin} TILE{"S" if margin>1 else ""}!',font(48),(255,255,255),4)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],n=len(F),end=END,win=win,conv=[len(f['conv']) for f in F]),open(OUT+'.json','w')); print('done',total,margin)
