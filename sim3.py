"""Turtle vs Skunk. Side 'a' = Turtle, side 'b' = Skunk.
Turtle: SHELL (invulnerable SHELL_T f), BITE (dash at skunk, BITE_DMG on contact)
Skunk:  SPRAY (5 droplets, SPRAY_DMG each), STINK CLOUD (gas zone, 1 dmg / GAS_TICK f)
"""
import math, random
AX0,AY0,AX1,AY1 = 120,420,960,1260
R=58; SPEED=11.0
CD={'shell':170,'bite':100,'spray':70,'cloud':120}
SHELL_T=50; BITE_T=30; BITE_DMG=14; SPRAY_DMG=3; CLOUD_R=150; CLOUD_T=150; GAS_TICK=8; BUMP=2
class Ball:
    def __init__(s,x,y,a): s.x,s.y=x,y; s.vx=math.cos(a)*SPEED; s.vy=math.sin(a)*SPEED; s.hp=100
def simulate(seed, record=False):
    rnd=random.Random(seed)
    a=Ball(330,1000,rnd.uniform(0,6.28)); b=Ball(750,680,rnd.uniform(0,6.28))
    cd={'shell':90,'bite':50,'spray':30,'cloud':80}
    proj=[]; clouds=[]; shell=0; bite=0; bumpcd=0; ev=[]; frames=[]; lead=[]
    f=0
    while f<2000:
        casts=[]; hits=[]
        for k in cd: cd[k]-=1
        if cd['shell']<=0: cd['shell']=CD['shell']; shell=SHELL_T; casts.append('shell')
        if cd['bite']<=0:
            cd['bite']=CD['bite']; bite=BITE_T; casts.append('bite')
            ang=math.atan2(b.y-a.y,b.x-a.x); a.vx,a.vy=math.cos(ang),math.sin(ang)
        if cd['spray']<=0:
            cd['spray']=CD['spray']; casts.append('spray')
            base=math.atan2(a.y-b.y,a.x-b.x)
            for da in (-.3,-.15,0,.15,.3):
                g=base+da; proj.append(dict(x=b.x+math.cos(g)*R,y=b.y+math.sin(g)*R,vx=math.cos(g)*15,vy=math.sin(g)*15,a=g))
        if cd['cloud']<=0: cd['cloud']=CD['cloud']; casts.append('cloud'); clouds.append([b.x,b.y,CLOUD_T])
        for c in casts: ev.append((f,'cast',c))
        sa=SPEED*(1.8 if bite>0 else 1)
        for o,sp in ((a,sa),(b,SPEED)):
            m=math.hypot(o.vx,o.vy) or 1; o.vx*=sp/m; o.vy*=sp/m
            o.x+=o.vx; o.y+=o.vy
            if o.x<AX0+R: o.x=AX0+R; o.vx=abs(o.vx)
            if o.x>AX1-R: o.x=AX1-R; o.vx=-abs(o.vx)
            if o.y<AY0+R: o.y=AY0+R; o.vy=abs(o.vy)
            if o.y>AY1-R: o.y=AY1-R; o.vy=-abs(o.vy)
        def hurt_a(dm,kind):
            if shell>0: hits.append(('a',0,'block')); return
            a.hp-=dm; hits.append(('a',dm,kind))
        dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
        if d<2*R:
            nx,ny=dx/d,dy/d; p1=a.vx*nx+a.vy*ny; p2=b.vx*nx+b.vy*ny
            if p1-p2>0: a.vx+=(p2-p1)*nx; a.vy+=(p2-p1)*ny; b.vx+=(p1-p2)*nx; b.vy+=(p1-p2)*ny
            ov=2*R-d; a.x-=nx*ov/2; a.y-=ny*ov/2; b.x+=nx*ov/2; b.y+=ny*ov/2
            if bumpcd<=0:
                bumpcd=10
                if bite>0: b.hp-=BITE_DMG; hits.append(('b',BITE_DMG,'bite')); ev.append((f,'bitehit')); bite=0
                else: b.hp-=BUMP; hits.append(('b',BUMP,'bump')); hurt_a(BUMP,'bump'); ev.append((f,'bump'))
        bumpcd-=1; bite-=1
        keep=[]
        for p in proj:
            p['x']+=p['vx']; p['y']+=p['vy']
            if not(AX0<p['x']<AX1 and AY0<p['y']<AY1): continue
            if math.hypot(p['x']-a.x,p['y']-a.y)<R+8:
                hurt_a(SPRAY_DMG,'spray'); ev.append((f,'block' if shell>0 else 'sprayhit')); continue
            keep.append(p)
        proj=keep
        gas=False
        for c in clouds:
            c[2]-=1
            if math.hypot(a.x-c[0],a.y-c[1])<CLOUD_R+R*.5: gas=True
        clouds=[c for c in clouds if c[2]>0]
        if gas and f%GAS_TICK==0:
            if shell<=0: a.hp-=1; hits.append(('a',1,'gas'))
        shell-=1
        if record:
            frames.append(dict(a=(a.x,a.y,a.hp),b=(b.x,b.y,b.hp),cd=dict(cd),proj=[(p['x'],p['y'],p['a']) for p in proj],
                               clouds=[tuple(c) for c in clouds],casts=casts,hits=hits,shell=shell>0,bite=bite>0,gas=gas))
        lead.append(1 if a.hp>b.hp else (-1 if b.hp>a.hp else 0))
        f+=1
        if a.hp<=0 or b.hp<=0: break
    win='a' if b.hp<=0 else 'b'
    ch=0; last=0
    for l in lead:
        if l and last and l!=last: ch+=1
        if l: last=l
    return dict(frames=frames,ev=ev,n=f,win=win,ah=a.hp,bh=b.hp,changes=ch)
if __name__=='__main__':
    res=[];wins={'a':0,'b':0}; ns=[]
    for sd in range(500):
        r=simulate(sd); wins[r['win']]+=1; ns.append(r['n'])
        wh=r['ah'] if r['win']=='a' else r['bh']
        if 800<=r['n']<=1150 and 0<wh<=10: res.append((r['changes'],sd,r['n'],r['win'],wh))
    ns.sort(); print(wins,'median frames',ns[len(ns)//2]); res.sort(reverse=True); print(res[:10])
