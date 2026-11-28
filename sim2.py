import math, random
AX0,AY0,AX1,AY1 = 120,420,960,1260
R=58; SPEED=11.0
CD={'burst':80,'roll':130,'venom':75,'shed':280}
class Ball:
    def __init__(s,x,y,a): s.x,s.y=x,y; s.vx=math.cos(a)*SPEED; s.vy=math.sin(a)*SPEED; s.hp=100
def simulate(seed, record=False):
    rnd=random.Random(seed)
    h=Ball(330,1000,rnd.uniform(0,6.28)); s=Ball(750,680,rnd.uniform(0,6.28))
    cd={'burst':60,'roll':120,'venom':40,'shed':200}
    proj=[]; poison=0; roll=0; bumpcd=0; ev=[]; frames=[]; lead=[]
    f=0
    while f<2000:
        casts=[]
        for k in cd: cd[k]-=1
        if cd['burst']<=0:
            cd['burst']=CD['burst']; casts.append('burst')
            for i in range(12):
                a=i/12*2*math.pi; proj.append(dict(x=h.x+math.cos(a)*R,y=h.y+math.sin(a)*R,vx=math.cos(a)*16,vy=math.sin(a)*16,o='h',a=a))
        if cd['roll']<=0: cd['roll']=CD['roll']; roll=45; casts.append('roll')
        if cd['venom']<=0:
            cd['venom']=CD['venom']; casts.append('venom')
            base=math.atan2(h.y-s.y,h.x-s.x)
            for da in (-.22,0,.22):
                a=base+da; proj.append(dict(x=s.x+math.cos(a)*R,y=s.y+math.sin(a)*R,vx=math.cos(a)*15,vy=math.sin(a)*15,o='s',a=a))
        if cd['shed']<=0:
            cd['shed']=CD['shed']; casts.append('shed'); heal=min(8,100-s.hp); s.hp+=heal; ev.append((f,'shed',heal))
        for c in casts: ev.append((f,'cast',c))
        hs=SPEED*(1.9 if roll>0 else 1); roll-=1
        for b,sp in ((h,hs),(s,SPEED)):
            m=math.hypot(b.vx,b.vy); b.vx*=sp/m; b.vy*=sp/m
            b.x+=b.vx; b.y+=b.vy
            if b.x<AX0+R: b.x=AX0+R; b.vx=abs(b.vx)
            if b.x>AX1-R: b.x=AX1-R; b.vx=-abs(b.vx)
            if b.y<AY0+R: b.y=AY0+R; b.vy=abs(b.vy)
            if b.y>AY1-R: b.y=AY1-R; b.vy=-abs(b.vy)
        dx,dy=s.x-h.x,s.y-h.y; d=math.hypot(dx,dy) or 1
        hits=[]
        if d<2*R:
            nx,ny=dx/d,dy/d; p1=h.vx*nx+h.vy*ny; p2=s.vx*nx+s.vy*ny
            if p1-p2>0: h.vx+=(p2-p1)*nx; h.vy+=(p2-p1)*ny; s.vx+=(p1-p2)*nx; s.vy+=(p1-p2)*ny
            ov=2*R-d; h.x-=nx*ov/2; h.y-=ny*ov/2; s.x+=nx*ov/2; s.y+=ny*ov/2
            if bumpcd<=0:
                bumpcd=10
                if roll>0: s.hp-=10; hits.append(('s',10,'roll')); ev.append((f,'rollhit'))
                else: s.hp-=2; h.hp-=2; hits.append(('s',2,'bump')); hits.append(('h',2,'bump')); ev.append((f,'bump'))
        bumpcd-=1
        keep=[]
        for p in proj:
            p['x']+=p['vx']; p['y']+=p['vy']
            if not(AX0<p['x']<AX1 and AY0<p['y']<AY1): continue
            tgt=s if p['o']=='h' else h
            if math.hypot(p['x']-tgt.x,p['y']-tgt.y)<R+8:
                if p['o']=='h': s.hp-=6; hits.append(('s',6,'spike')); ev.append((f,'spikehit'))
                else: h.hp-=3; poison=min(poison+20,60); hits.append(('h',3,'venom')); ev.append((f,'venomhit'))
                continue
            keep.append(p)
        proj=keep
        if poison>0:
            poison-=1
            if poison%10==0: h.hp-=1; hits.append(('h',1,'poison'))
        if record:
            frames.append(dict(h=(h.x,h.y,h.hp),s=(s.x,s.y,s.hp),cd=dict(cd),proj=[(p['x'],p['y'],p['o'],p['a']) for p in proj],casts=casts,hits=hits,roll=roll>0,poison=poison>0))
        lead.append(1 if h.hp>s.hp else (-1 if s.hp>h.hp else 0))
        f+=1
        if h.hp<=0 or s.hp<=0: break
    win='h' if s.hp<=0 else 's'
    ch=0; last=0
    for l in lead:
        if l and last and l!=last: ch+=1
        if l: last=l
    return dict(frames=frames,ev=ev,n=f,win=win,hh=h.hp,sh=s.hp,changes=ch)
if __name__=='__main__':
    res=[];wins={'h':0,'s':0}
    for sd in range(500):
        r=simulate(sd); wins[r['win']]+=1
        wh=r['hh'] if r['win']=='h' else r['sh']
        if 800<=r["n"]<=1150 and 0<wh<=10: res.append((r['changes'],sd,r['n'],r['win'],wh))
    print(wins); res.sort(reverse=True); print(res[:10])
