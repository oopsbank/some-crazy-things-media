"""Shovel vs Axe. Side 'a' = Shovel, side 'b' = Axe. Only skill 1 + ultimate (user asked: no skill 2).
Shovel: DIG (tunnel underground toward the axe, untargetable, pop-up AoE)   | ult BURY (dirt clod; on hit the axe is buried: rooted, silenced, DoT)
Axe:    WHIRLWIND (spinning damage aura around itself)                     | ult TIMBER (telegraphed line strike: a tree falls across the arena)
"""
import math, random
AX0,AY0,AX1,AY1 = 120,420,960,1260
R=58; SPEED=11.0
CD={'dig':80,'bury':380,'whirl':70,'timber':340}
DIG_T=34; DIG_R=160; DIG_DMG=14
CLOD_V=15; BURY_LEAD=(-0.4,0.6); BURY_T=60; BURY_TICK=10; BURY_DMG=4
WHIRL_T=40; WHIRL_R=150; WHIRL_TICK=6; WHIRL_DMG=5
TIMBER_WARN=24; TIMBER_W=80; TIMBER_DMG=30; TIMBER_FALL=8; TIMBER_SPREAD=0.25
BUMP=3
class Ball:
    def __init__(s,x,y,a): s.x,s.y=x,y; s.vx=math.cos(a)*SPEED; s.vy=math.sin(a)*SPEED; s.hp=100
def clampxy(x,y): return min(max(x,AX0+R),AX1-R),min(max(y,AY0+R),AY1-R)
def inside(x,y): return AX0<x<AX1 and AY0<y<AY1
def line_ends(px,py,ang):
    """Segment through (px,py) with direction ang, clipped to the arena."""
    dx,dy=math.cos(ang),math.sin(ang); ts=[]
    for t in ((AX0-px)/dx if dx else None,(AX1-px)/dx if dx else None,(AY0-py)/dy if dy else None,(AY1-py)/dy if dy else None):
        if t is None: continue
        x,y=px+dx*t,py+dy*t
        if AX0-1<=x<=AX1+1 and AY0-1<=y<=AY1+1: ts.append(t)
    t0,t1=min(ts),max(ts); return (px+dx*t0,py+dy*t0,px+dx*t1,py+dy*t1)
def seg_dist(px,py,x0,y0,x1,y1):
    vx,vy=x1-x0,y1-y0; L=vx*vx+vy*vy or 1; u=max(0,min(1,((px-x0)*vx+(py-y0)*vy)/L))
    return math.hypot(px-(x0+vx*u),py-(y0+vy*u))
def simulate(seed, record=False):
    rnd=random.Random(seed)
    a=Ball(330,1000,rnd.uniform(0,6.28)); b=Ball(750,680,rnd.uniform(0,6.28))
    cd=dict(CD)
    dig=0; digto=None; buried=0; whirl=0; clods=[]; trees=[]; bumpcd=0; ev=[]; frames=[]; lead=[]
    f=0
    while f<2000:
        casts=[]; hits=[]; popup=None; crash=[]; clodhit=None
        for k in ('dig','bury'): cd[k]-=1
        if buried<=0:
            for k in ('whirl','timber'): cd[k]-=1
        def hurt(o,side,dm,kind,evk=None):
            if side=='a' and dig>0: return
            o.hp-=dm; hits.append((side,dm,kind))
            if evk: ev.append((f,evk))
        # --- shovel
        if cd['dig']<=0 and dig<=0:
            cd['dig']=CD['dig']; casts.append('dig'); dig=DIG_T; digto=(b.x,b.y)
        if cd['bury']<=0 and dig<=0:
            cd['bury']=CD['bury']; casts.append('bury')
            lead_=rnd.uniform(*BURY_LEAD); d=math.hypot(b.x-a.x,b.y-a.y); tt=d/CLOD_V
            tx,ty=b.x+b.vx*tt*lead_,b.y+b.vy*tt*lead_; g=math.atan2(ty-a.y,tx-a.x)
            clods.append(dict(x=a.x,y=a.y,vx=math.cos(g)*CLOD_V,vy=math.sin(g)*CLOD_V,s=0))
        # --- axe (silenced while buried)
        if buried<=0:
            if cd['whirl']<=0: cd['whirl']=CD['whirl']; casts.append('whirl'); whirl=WHIRL_T
            if cd['timber']<=0:
                cd['timber']=CD['timber']; casts.append('timber')
                ang=math.atan2(a.vy,a.vx)+rnd.uniform(-TIMBER_SPREAD,TIMBER_SPREAD); trees.append(dict(t=0,seg=line_ends(a.x,a.y,ang),ang=ang))
        for c in casts: ev.append((f,'cast',c))
        # --- movement
        if dig>0:   # tunnel straight to where the axe WAS when the dig started
            g=math.atan2(digto[1]-a.y,digto[0]-a.x); a.vx,a.vy=math.cos(g),math.sin(g)
            if math.hypot(digto[0]-a.x,digto[1]-a.y)<SPEED*1.5: dig=1
        movers=[(a,SPEED*(1.5 if dig>0 else 1))]+([] if buried>0 else [(b,SPEED*(1.15 if whirl>0 else 1))])
        for o,sp in movers:
            m=math.hypot(o.vx,o.vy) or 1; o.vx*=sp/m; o.vy*=sp/m
            o.x+=o.vx; o.y+=o.vy
            if o.x<AX0+R: o.x=AX0+R; o.vx=abs(o.vx)
            if o.x>AX1-R: o.x=AX1-R; o.vx=-abs(o.vx)
            if o.y<AY0+R: o.y=AY0+R; o.vy=abs(o.vy)
            if o.y>AY1-R: o.y=AY1-R; o.vy=-abs(o.vy)
        if dig>0:
            dig-=1
            if dig==0:
                popup=(a.x,a.y); ev.append((f,'popup'))
                if math.hypot(a.x-b.x,a.y-b.y)<DIG_R: hurt(b,'b',DIG_DMG,'dig')
                g=rnd.uniform(0,6.28); a.vx,a.vy=math.cos(g),math.sin(g)
        # --- body contact
        dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
        if d<2*R and dig<=0:
            nx,ny=dx/d,dy/d
            if buried>0:   # buried axe is an immovable wall
                ov=2*R-d; a.x-=nx*ov; a.y-=ny*ov; p=a.vx*nx+a.vy*ny
                if p>0: a.vx-=2*p*nx; a.vy-=2*p*ny
            else:
                p1=a.vx*nx+a.vy*ny; p2=b.vx*nx+b.vy*ny
                if p1-p2>0: a.vx+=(p2-p1)*nx; a.vy+=(p2-p1)*ny; b.vx+=(p1-p2)*nx; b.vy+=(p1-p2)*ny
                ov=2*R-d; a.x-=nx*ov/2; a.y-=ny*ov/2; b.x+=nx*ov/2; b.y+=ny*ov/2
            if bumpcd<=0: bumpcd=10; hurt(b,'b',BUMP,'bump'); hurt(a,'a',BUMP,'bump','bump')
        bumpcd-=1
        # --- whirlwind aura
        if whirl>0:
            whirl-=1
            if buried>0: whirl=0
            elif f%WHIRL_TICK==0 and math.hypot(a.x-b.x,a.y-b.y)<WHIRL_R+R*.5: hurt(a,'a',WHIRL_DMG,'whirl','whirlhit')
        # --- clods
        keep=[]
        for c in clods:
            c['x']+=c['vx']; c['y']+=c['vy']; c['s']+=1
            if not inside(c['x'],c['y']) or c['s']>80: ev.append((f,'splat')); continue
            if math.hypot(c['x']-b.x,c['y']-b.y)<R+16:
                buried=BURY_T; whirl=0; clodhit=(b.x,b.y); ev.append((f,'buryhit')); continue
            keep.append(c)
        clods=keep
        if buried>0:
            if buried%BURY_TICK==0: hurt(b,'b',BURY_DMG,'bury')
            buried-=1
            if buried==0: g=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(g),math.sin(g); ev.append((f,'unbury'))
        # --- falling trees
        keep=[]
        for tr in trees:
            tr['t']+=1
            if tr['t']==TIMBER_WARN:
                crash.append(tr['seg']); ev.append((f,'crash'))
                if seg_dist(a.x,a.y,*tr['seg'])<TIMBER_W*.5+R*.6: hurt(a,'a',TIMBER_DMG,'timber')
            if tr['t']<TIMBER_WARN+TIMBER_FALL+20: keep.append(tr)
        trees=keep
        if record:
            frames.append(dict(a=(a.x,a.y,a.hp),b=(b.x,b.y,b.hp),cd=dict(cd),casts=casts,hits=hits,dig=dig>0,popup=popup,
                buried=buried,whirl=whirl>0,clods=[(c['x'],c['y'],c['s']) for c in clods],clodhit=clodhit,
                trees=[(tr['seg'],tr['t'],tr['ang']) for tr in trees],crash=crash))
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
        casts=[e[2] for e in r['ev'] if e[1]=='cast']
        if 900<=r['n']<=1100 and 0<wh<=8 and casts.count('bury')>=2 and casts.count('timber')>=2:
            res.append((r['changes'],sd,r['n'],r['win'],wh))
    ns.sort(); print(wins,'median frames',ns[len(ns)//2]); res.sort(reverse=True); print(res[:10])
