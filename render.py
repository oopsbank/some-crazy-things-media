import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps
import sim
from sim import ROWS, LANES, CARW, TILES, PERIOD, CONV, CX, CY, rad
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=sim.simulate(SEED, record=True); F=r['frames']; EV={}
for e in r['ev']: EV.setdefault(e[0],[]).append(e)
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True); return im.crop(im.getbbox())
def eyes(im):
    im=im.copy(); d=ImageDraw.Draw(im); w,h=im.size; cy=h*0.62
    for ex in (w*0.36,w*0.64):
        d.ellipse([ex-w*.11,cy-h*.11,ex+w*.11,cy+h*.11],fill='white'); d.ellipse([ex-w*.05,cy-h*.02,ex+w*.05,cy+h*.09],fill='black')
    return im
EF,EW=eyes(emoji('🔥')),eyes(emoji('💧'))
SMALL=[EF.resize((54,58),Image.LANCZOS),EW.resize((50,58),Image.LANCZOS)]
CARS=[emoji(c) for c in '🚗🚕🚙🚌🚓']
def carimg(k,d):
    im=CARS[k%len(CARS)]; im=im.resize((CARW,int(CARW*im.size[1]/im.size[0])),Image.LANCZOS)
    return ImageOps.mirror(im) if d>0 else im
CI={(k,d):carimg(k,d) for k in range(5) for d in (-1,1)}
OR=(255,140,40); BL=(70,170,255); NAME=['FIRE','WATER']; COL=[OR,BL]
TC={1:(90,90,100),2:(60,140,220),3:(60,180,120),5:(170,90,220),20:(230,70,70),100:(255,200,0)}
INTRO=45; END=80
def ctext(d,cx,y,t,fn,fill,sw=4):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
bg=Image.new('RGBA',(W,H),(30,90,45,255)); d=ImageDraw.Draw(bg)
d.rectangle([0,0,W,180],fill=(12,12,18))
for row in range(10):
    y=ROWS[row]; top=y-40
    if row in LANES: d.rectangle([0,top,W,top+80],fill=(45,45,52))
    elif row==4: pass
    else: d.rectangle([0,top,W,top+80],fill=(150,150,140) if row in (0,3,5,8) else (40,110,55))
for a,b in ((1,2),(6,7)):
    y=ROWS[a]+40
    for x in range(0,W,80): d.rectangle([x,y-3,x+44,y+3],fill=(240,240,240))
    d.rectangle([0,ROWS[a]-42,W,ROWS[a]-38],fill=(250,210,0)); d.rectangle([0,ROWS[b]+38,W,ROWS[b]+42],fill=(250,210,0))
d.rectangle([0,ROWS[9]-40,W,ROWS[9]+40],fill=(235,235,235))
for x in range(0,W,40):
    for yy in (0,1):
        if (x//40+yy)%2==0: d.rectangle([x,ROWS[9]-40+yy*40,x+40,ROWS[9]+yy*40],fill=(20,20,20))
d.rectangle([0,990,W,H],fill=(20,60,30)); d.line([W/2,1000,W/2,H],fill=(60,100,70),width=4)
f1=font(70); P=[('FIRE',OR),(' vs ',(230,230,230)),('WATER',BL)]
tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
for p,c in P: d.text((x,55),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
pops=[]; parts=[]
total=INTRO+len(F)+END; win=r['win']; lose=1-win
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; live=INTRO<=t<INTRO+len(F); ending=t>=INTRO+len(F); fidx=t-INTRO
    im=bg.copy(); d=ImageDraw.Draw(im)
    # conveyor
    y=ROWS[4]; off=(max(fidx,0)*CONV)%PERIOD; x=-off
    while x<W:
        for m,w in TILES:
            d.rectangle([x+2,y-38,x+w-2,y+38],fill=TC[m]); ctext(d,x+w/2,y-22,f'x{m}',font(34 if m<100 else 22),(255,255,255),3); x+=w
        d.rectangle([x,y-38,x+40,y+38],fill=(25,25,30)); x+=40
    for l,(dd,sp) in LANES.items():
        for k,cx in enumerate(fr['cars'][l]):
            ci=CI[(int(abs(cx*7+l*13)//997)%5 if False else (l+k)%5,dd)]
            im.alpha_composite(ci,(int(cx-CARW/2),int(ROWS[l]-ci.size[1]/2)))
    if live:
        for e in EV.get(fidx,[]):
            if e[1]=='splat':
                s,x0,y0,v=e[2],e[3],e[4],e[5]
                for _ in range(14):
                    a=random.uniform(0,6.28); vv=random.uniform(2,9)
                    parts.append([x0,y0,math.cos(a)*vv,math.sin(a)*vv-(3 if s==0 else 0),(120,120,120) if s==0 else BL,0,'puff' if s==0 else 'drop'])
                if v>=5: pops.append([x0,y0-50,f'-{v}',(255,80,80),0,46])
            if e[1]=='mult' and e[3]>=3:
                pops.append([e[4],ROWS[4]-60,f'x{e[3]}!',TC[e[3]] if e[3]!=1 else (255,255,255),0,58 if e[3]>=20 else 44])
            if e[1]=='feed' and e[3]>=5:
                pops.append([CX[e[2]],CY-rad(fr['big'][e[2]])-40,f'+{e[3]}',COL[e[2]],0,64])
    for (s,x0,row,hop,v,m) in fr['ch'] if not ending else []:
        p=(8-hop)/8 if hop>0 else 0; yy=ROWS[row]+80*p-math.sin(math.pi*p)*26
        sc=1+0.25*min(math.log10(v),2) if v>1 else 1
        img=SMALL[s] if sc==1 else SMALL[s].resize((int(SMALL[s].size[0]*sc),int(SMALL[s].size[1]*sc)))
        im.alpha_composite(img,(int(x0-img.size[0]/2),int(yy-img.size[1]/2)))
        if v>1: ctext(d,x0,yy-img.size[1]/2-34,str(v),font(30 if v<100 else 38),(255,230,80) if v>=20 else (255,255,255),3)
    for (s,x0,y0,v,k) in fr['fly'] if not ending else []:
        p=k/14; bx=x0+(CX[s]-x0)*p; by=y0+(CY-y0)*p-math.sin(math.pi*p)*120
        im.alpha_composite(SMALL[s],(int(bx-27),int(by-29)))
    # big blobs
    for s in (0,1):
        v=fr['big'][s]; rr=rad(v)
        if ending:
            k=t-(INTRO+len(F))
            if s==lose:
                rr*=max(0,1-k/20)
                if k<20:
                    for _ in range(6): parts.append([CX[s]+random.uniform(-rr,rr),CY+random.uniform(-rr,rr)*.6,random.uniform(-1,1),random.uniform(-7,-3),(230,230,230),0,'steam'])
            else: rr*=1+0.04*math.sin(k*.4)
        if rr<4: continue
        src=EF if s==0 else EW; w2=int(2*rr); h2=int(2*rr*src.size[1]/src.size[0])
        bimg=src.resize((max(w2,2),max(h2,2)),Image.BILINEAR)
        im.alpha_composite(bimg,(int(CX[s]-w2/2),int(CY-h2/2-rr*0.1)))
        if not (ending and s==lose):
            fn=font(max(44,min(96,int(rr*0.4)))); txt=str(int(v)); tw=d.textlength(txt,font=fn); by=CY+h2/2-rr*0.1-fn.size*0.6
            d.rounded_rectangle([CX[s]-tw/2-16,by-6,CX[s]+tw/2+16,by+fn.size+10],radius=14,fill=(0,0,0,200)); ctext(d,CX[s],by,txt,fn,COL[s],0)
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[5]+=1
        if p[6]=='drop': p[3]+=0.6
        sz=9 if p[6]=='drop' else 7+p[5]*0.5; a=max(0,230-p[5]*10)
        lay=d; d.ellipse([p[0]-sz,p[1]-sz,p[0]+sz,p[1]+sz],fill=p[4]+(a,))
    parts[:]=[p for p in parts if p[5]<22]
    for p in pops:
        p[4]+=1; ctext(d,p[0],p[1]-p[4]*2,p[2],font(p[5]),p[3],4)
    pops[:]=[p for p in pops if p[4]<26]
    if t<INTRO:
        d.rectangle([0,1180,W,1360],fill=(0,0,0,200)); ctext(d,W/2,1195,'BIGGER ONE TOUCHES',font(68),(255,255,255)); ctext(d,W/2,1280,'= WINS',font(64),(255,220,0))
    if ending and t-(INTRO+len(F))>=18:
        ctext(d,W/2,1740,f'{NAME[win]} WINS!',font(110),COL[win],6)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=win),open(OUT+'.json','w')); print('done',total)
