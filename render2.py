import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim2 import simulate, AX0,AY0,AX1,AY1,R,CD
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
EH,ES=emoji('🦔',86),emoji('🐍',86)
OR=(255,170,60); GR=(110,240,100); PU=(190,90,255)
NAMES={'burst':'SPIKE BURST!','roll':'ROLL!','venom':'VENOM!','shed':'SHED SKIN!'}
INTRO=30; END=70
pops=[]; flashes=[]; parts=[]; ghosts=[]
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill)
total=INTRO+len(F)+END; loser='s' if r['win']=='h' else 'h'
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; ending=t>=INTRO+len(F); live=INTRO<=t<INTRO+len(F)
    im=Image.new('RGBA',(W,H),(0,0,0,255)); d=ImageDraw.Draw(im)
    f1=font(64); P=[('HEDGEHOG',OR),(' vs ',(230,230,230)),('SNAKE',GR)]
    tw=sum(d.textlength(p,font=f1) for p,_ in P); x=(W-tw)/2
    for p,c in P: d.text((x,190),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
    d.rectangle([AX0-6,AY0-6,AX1+6,AY1+6],outline=(150,150,150),width=6)
    hx,hy,hhp=fr['h']; sx,sy,shp=fr['s']
    if live:
        for c in fr['casts']:
            who=(hx,hy,OR) if c in('burst','roll') else (sx,sy,GR if c=='shed' else PU)
            flashes.append([c,who[0],who[1],who[2],0])
        for (tg,dm,k) in fr['hits']:
            bx,by=(hx,hy) if tg=='h' else (sx,sy)
            col={'spike':OR,'roll':OR,'bump':(255,255,255),'venom':PU,'poison':PU}[k]
            pops.append([bx+random.uniform(-30,30),by-70,f'-{dm}',col,0,52 if k!='poison' else 38])
        if fr['roll']: ghosts.append([hx,hy,0])
    if live:
        for c in fr['casts']:
            if c=='shed': pops.append([sx,sy-80,'+8',GR,0,60])
    # ghosts (roll trail)
    for g in ghosts:
        g[2]+=1; a=max(0,140-g[2]*14); d.ellipse([g[0]-R,g[1]-R,g[0]+R,g[1]+R],fill=(255,120,30,a) if False else None,outline=(255,150,50),width=3) if a>0 else None
    ghosts[:]=[g for g in ghosts if g[2]<10]
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    for (px,py,o,a) in fr['proj'] if not ending else []:
        if o=='h':
            p=[(px+math.cos(a)*34,py+math.sin(a)*34),(px+math.cos(a+2.7)*14,py+math.sin(a+2.7)*14),(px+math.cos(a-2.7)*14,py+math.sin(a-2.7)*14)]
            ld.polygon(p,fill=(255,200,120),outline=(120,60,20))
        else:
            ld.ellipse([px-13,py-13,px+13,py+13],fill=(170,70,255,230)); ld.ellipse([px-6,py-6,px+6,py+6],fill=(220,255,120,255))
    def draw_h():
        if fr['roll'] and not ending: ld.ellipse([hx-R-14,hy-R-14,hx+R+14,hy+R+14],fill=(255,120,30,90))
        if fr['poison'] and not ending: ld.ellipse([hx-R-8,hy-R-8,hx+R+8,hy+R+8],outline=(170,70,255,255),width=8)
        for k in range(14):
            a=k/14*2*math.pi+(t*0.3 if fr['roll'] else t*0.02)
            p=[(hx+math.cos(a-.15)*(R-4),hy+math.sin(a-.15)*(R-4)),(hx+math.cos(a)*(R+18),hy+math.sin(a)*(R+18)),(hx+math.cos(a+.15)*(R-4),hy+math.sin(a+.15)*(R-4))]
            ld.polygon(p,fill=(120,75,35),outline=(240,200,140))
        ld.ellipse([hx-R,hy-R,hx+R,hy+R],fill=(230,140,50),outline=(255,255,255),width=5)
        lay.alpha_composite(EH,(int(hx-43),int(hy-43)))
    def draw_s():
        ld.ellipse([sx-R,sy-R,sx+R,sy+R],fill=(50,170,70),outline=(255,255,255),width=5)
        lay.alpha_composite(ES,(int(sx-43),int(sy-43)))
    if ending:
        k=t-(INTRO+len(F))
        if k==0:
            lx,ly,col=(hx,hy,OR) if loser=='h' else (sx,sy,GR)
            for _ in range(70):
                a=random.uniform(0,6.28); v=random.uniform(4,18); parts.append([lx,ly,math.cos(a)*v,math.sin(a)*v,col])
        draw_s() if loser=='h' else draw_h()
    else: draw_h(); draw_s()
    for fl in flashes:
        fl[4]+=1; c,fx,fy,col,k=fl
        if k<12: rr=R+k*12; ld.ellipse([fx-rr,fy-rr,fx+rr,fy+rr],outline=col+(max(0,255-k*20),),width=8)
    for p in parts:
        p[0]+=p[2]; p[1]+=p[3]; p[2]*=.94; p[3]*=.94; ld.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill=p[4])
    for p in pops:
        p[4]+=1; a=max(0,255-p[4]*10); ld.text((p[0]-30,p[1]-p[4]*2),p[2],font=font(p[5]),fill=p[3]+(a,),stroke_width=3,stroke_fill=(0,0,0,a))
    pops[:]=[p for p in pops if p[4]<26]
    im.alpha_composite(lay); d=ImageDraw.Draw(im)
    # cast name banner (one at a time, latest)
    cur=[f for f in flashes if f[4]<24]
    if cur and not ending:
        c=cur[-1]; ctext(d,W/2,AY0-90,NAMES[c[0]],font(64),c[3])
    flashes[:]=cur
    # bars
    for side in (0,1):
        hp=max(hhp if side==0 else shp,0)
        if ending and ((side==0 and loser=='h') or (side==1 and loser=='s')): hp=0
        col=OR if side==0 else GR; x0=140 if side==0 else 610; y0=1290
        hs=f'HP {hp}'; ctext(d,x0+165,y0,hs,font(54),col)
        d.rounded_rectangle([x0,y0+70,x0+330,y0+100],radius=10,outline=col,width=3)
        d.rounded_rectangle([x0+4,y0+74,x0+4+322*hp/100,y0+96],radius=8,fill=col)
        sk=('burst','roll') if side==0 else ('venom','shed')
        for j,k in enumerate(sk):
            yy=y0+125+j*62; prog=1-max(fr['cd'][k],0)/CD[k] if live else (0 if t<INTRO else 1)
            ready=prog>.97
            d.rounded_rectangle([x0,yy,x0+330,yy+46],radius=12,outline=(200,200,200),width=3)
            d.rounded_rectangle([x0+4,yy+4,x0+4+322*prog,yy+42],radius=10,fill=(PU if k=='venom' else col) if not ready else (255,255,255))
            lab=NAMES[k].rstrip('!'); fl=font(28); w=d.textlength(lab,font=fl)
            d.text((x0+165-w/2,yy+7),lab,font=fl,fill=(255,255,255),stroke_width=3,stroke_fill=(0,0,0))
    if t<INTRO: ctext(d,W/2,780,'WHO WINS?',font(110),(255,255,255))
    if ending and t-(INTRO+len(F))>=12:
        txt=('HEDGEHOG' if r['win']=='h' else 'SNAKE')+' WINS!'; ctext(d,W/2,1600,txt,font(96),OR if r['win']=='h' else GR)
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=r['win']),open(OUT+'.json','w')); print('done',total)
