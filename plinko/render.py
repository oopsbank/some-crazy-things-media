import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont
from sim import simulate, LAY, LW, LX, TOP, GOAL_Y, TARGET, mirror
SEED=int(sys.argv[1]); OUT=sys.argv[2]
r=simulate(SEED, record=True); F=r['frames']
W,H=1080,1920
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
FC={}
def font(sz):
    if sz not in FC: FC[sz]=ImageFont.truetype(B,sz)
    return FC[sz]
ef=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji(ch):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=ef,embedded_color=True)
    return im.crop(im.getbbox())
EF,EW=emoji('🔥'),emoji('💧')
SM=[EF.resize((30,30),Image.LANCZOS),EW.resize((26,30),Image.LANCZOS)]
OR=(255,140,40); BL=(70,160,255)
COL=[OR,BL]; NAME=['FIRE','WATER']
INTRO=40; END=80
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',OUT],stdin=subprocess.PIPE)
def ctext(d,cx,y,t,fn,fill):
    w=d.textlength(t,font=fn); d.text((cx-w/2,y),t,font=fn,fill=fill)
# static background
bg=Image.new('RGBA',(W,H),(8,8,14,255)); d=ImageDraw.Draw(bg)
f1=font(70); parts=[('FIRE',OR),(' vs ',(230,230,230)),('WATER',BL)]
tw=sum(d.textlength(p,font=f1) for p,_ in parts); x=(W-tw)/2
for p,c in parts: d.text((x,150),p,font=f1,fill=c); x+=d.textlength(p,font=f1)
for s in (0,1):
    ox=LX[s]
    d.rectangle([ox-4,TOP-10,ox+LW+4,GOAL_Y+4],outline=(120,120,130),width=4)
    for (px,py,pr) in LAY['pegs']:
        px=mirror(px,s)+ox; d.ellipse([px-pr,py-pr,px+pr,py+pr],fill=(200,200,210))
    gx0,gx1,gy=LAY['gate']
    if s==1: gx0,gx1=LW-gx1,LW-gx0
    d.rectangle([ox+gx0,gy-14,ox+gx1,gy+14],fill=(40,200,90))
    ctext(d,ox+(gx0+gx1)/2,gy-20,'x2',font(34),(255,255,255))
    tx0,tx1,ty=LAY['trap']
    if s==1: tx0,tx1=LW-tx1,LW-tx0
    tc=(40,110,255) if s==0 else (255,60,20)
    d.rounded_rectangle([ox+tx0,ty-12,ox+tx1,ty+16],radius=12,fill=tc)
    ic=(EW if s==0 else EF).resize((36,40)); bg.alpha_composite(ic,(int(ox+(tx0+tx1)/2-18),int(ty-52)))
pops=[]
total=INTRO+len(F)+END
for t in range(total):
    i=min(max(t-INTRO,0),len(F)-1); fr=F[i]; ending=t>=INTRO+len(F)
    im=bg.copy(); d=ImageDraw.Draw(im)
    for s in (0,1):
        ox=LX[s]; bx,by,bl=LAY['bar']; a=fr['ang'] if s==0 else -fr['ang']
        x0,y0=ox+bx-math.cos(a)*bl,by-math.sin(a)*bl; x1,y1=ox+bx+math.cos(a)*bl,by+math.sin(a)*bl
        d.line([x0,y0,x1,y1],fill=(255,255,255),width=12); d.ellipse([ox+bx-10,by-10,ox+bx+10,by+10],fill=(255,210,0))
        for (x,y) in fr['ps'][s]:
            im.alpha_composite(SM[s],(int(ox+x-15),int(y-15)))
        # big blob
        c=fr['cnt'][s]; sz=int(90+130*(c/TARGET)**.7)
        if ending and s==r['win']: sz=int(sz*(1+0.06*math.sin(t*.4)))
        big=(EF if s==0 else EW).resize((sz,int(sz*1.1)),Image.LANCZOS)
        cx=ox+LW/2; im.alpha_composite(big,(int(cx-sz/2),int(1880-sz*1.1)))
        ctext(d,cx,GOAL_Y+18,f'{c}',font(78),COL[s])
    if t<INTRO:
        d.rectangle([0,860,W,1040],fill=(0,0,0))
        ctext(d,W/2,880,f'FIRST TO {TARGET}',font(100),(255,255,255)); ctext(d,W/2,985,'WINS',font(50),(255,220,0))
    if ending and t-(INTRO+len(F))>=10:
        w=r['win']; d.rectangle([0,860,W,1010],fill=(0,0,0)); ctext(d,W/2,870,f'{NAME[w]} WINS!',font(110),COL[w])
    proc.stdin.write(im.convert('RGB').tobytes())
proc.stdin.close(); proc.wait()
json.dump(dict(ev=r['ev'],intro=INTRO,n=len(F),end=END,win=r['win']),open(OUT+'.json','w')); print('done',total)
