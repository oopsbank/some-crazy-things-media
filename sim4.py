"""Octopus vs Crab. Side 'a' = Octopus, side 'b' = Crab.
Octopus: INK (3 blobs, INK_DMG each, slows crab), WHIP (tentacle lash in WHIP_RANGE, WHIP_DMG + pull),
         ult KRAKEN (KR_N tentacles erupt where the crab is heading, KR_DMG each)
Crab:    BUBBLES (4 homing bubbles, BUB_DMG each), CLAW (dash, CLAW_DMG on contact),
         ult CRUSH (leap onto the octopus, CRUSH_DMG shockwave in CRUSH_R)
"""
import math, random
AX0,AY0,AX1,AY1 = 120,420,960,1260
R=58; SPEED=11.0
CD={'ink':75,'whip':95,'kraken':430,'bubbles':80,'claw':105,'crush':370}
INK_DMG=2; INK_SLOW=45; WHIP_RANGE=330; WHIP_DMG=8
KR_N=5; KR_GAP=12; KR_WARN=16; KR_R=80; KR_DMG=9; KR_LEAD=0.5
BUB_DMG=2; BUB_SPREAD=(-.35,0,.35); CLAW_T=28; CLAW_DMG=7; CRUSH_T=26; CRUSH_R=190; CR_LEAD=(0.2,0.5); CRUSH_DMG=18; BUMP=2
class Ball:
    def __init__(s,x,y,a): s.x,s.y=x,y; s.vx=math.cos(a)*SPEED; s.vy=math.sin(a)*SPEED; s.hp=100
def clampxy(x,y): return min(max(x,AX0+R),AX1-R),min(max(y,AY0+R),AY1-R)
def simulate(seed, record=False):
    rnd=random.Random(seed)
    a=Ball(330,1000,rnd.uniform(0,6.28)); b=Ball(750,680,rnd.uniform(0,6.28))
    cd=dict(CD)
    inks=[]; bubs=[]; krak=[]; inked=0; claw=0; jump=None; bumpcd=0; ev=[]; frames=[]; lead=[]
    f=0
    while f<2000:
        casts=[]; hits=[]; whip=None; erupt=[]; landed=None
        for k in cd: cd[k]-=1
        if jump: cd['claw']=max(cd['claw'],1)  # no dash mid-air
        def hurt(o,side,dm,kind,evk=None):
            if side=='b' and jump: return
            o.hp-=dm; hits.append((side,dm,kind))
            if evk: ev.append((f,evk))
        # --- octopus skills
        if cd['ink']<=0:
            cd['ink']=CD['ink']; casts.append('ink'); base=math.atan2(b.y-a.y,b.x-a.x)
            for da in (-.2,0,.2):
                g=base+da; inks.append(dict(x=a.x+math.cos(g)*R,y=a.y+math.sin(g)*R,vx=math.cos(g)*14,vy=math.sin(g)*14,a=g))
        if cd['whip']<=0:
            cd['whip']=CD['whip']; casts.append('whip')
            dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
            if d<=WHIP_RANGE and not jump:
                hurt(b,'b',WHIP_DMG,'whip','whiphit'); b.vx,b.vy=-dx/d,-dy/d; whip=(a.x,a.y,b.x,b.y,True)
            else:
                L=min(d,WHIP_RANGE); whip=(a.x,a.y,a.x+dx/d*L,a.y+dy/d*L,False)
        if cd['kraken']<=0:
            cd['kraken']=CD['kraken']; casts.append('kraken')
            for k in range(KR_N): krak.append(dict(t=-k*KR_GAP,x=None,y=None))
        # --- crab skills
        if cd['bubbles']<=0 and not jump:
            cd['bubbles']=CD['bubbles']; casts.append('bubbles'); base=math.atan2(a.y-b.y,a.x-b.x)
            for da in BUB_SPREAD:
                g=base+da; bubs.append(dict(x=b.x+math.cos(g)*R,y=b.y+math.sin(g)*R,a=g,s=0))
        if cd['claw']<=0:
            cd['claw']=CD['claw']; claw=CLAW_T; casts.append('claw')
            g=math.atan2(a.y-b.y,a.x-b.x); b.vx,b.vy=math.cos(g),math.sin(g)
        if cd['crush']<=0 and not jump:
            cd['crush']=CD['crush']; casts.append('crush')
            ld=rnd.uniform(*CR_LEAD); tx,ty=clampxy(a.x+a.vx*CRUSH_T*ld,a.y+a.vy*CRUSH_T*ld)
            jump=dict(t=0,x0=b.x,y0=b.y,tx=tx,ty=ty)
        for c in casts: ev.append((f,'cast',c))
        # --- movement
        sb=SPEED*(1.8 if claw>0 else 1)*(0.6 if inked>0 else 1)
        movers=[(a,SPEED)]+([] if jump else [(b,sb)])
        for o,sp in movers:
            m=math.hypot(o.vx,o.vy) or 1; o.vx*=sp/m; o.vy*=sp/m
            o.x+=o.vx; o.y+=o.vy
            if o.x<AX0+R: o.x=AX0+R; o.vx=abs(o.vx)
            if o.x>AX1-R: o.x=AX1-R; o.vx=-abs(o.vx)
            if o.y<AY0+R: o.y=AY0+R; o.vy=abs(o.vy)
            if o.y>AY1-R: o.y=AY1-R; o.vy=-abs(o.vy)
        if jump:
            jump['t']+=1; u=jump['t']/CRUSH_T
            b.x=jump['x0']+(jump['tx']-jump['x0'])*u; b.y=jump['y0']+(jump['ty']-jump['y0'])*u
            if jump['t']>=CRUSH_T:
                landed=(b.x,b.y); ev.append((f,'land')); jump=None
                if math.hypot(a.x-b.x,a.y-b.y)<CRUSH_R: hurt(a,'a',CRUSH_DMG,'crush')
                g=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(g),math.sin(g)
        # --- body contact
        dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
        if d<2*R and not jump:
            nx,ny=dx/d,dy/d; p1=a.vx*nx+a.vy*ny; p2=b.vx*nx+b.vy*ny
            if p1-p2>0: a.vx+=(p2-p1)*nx; a.vy+=(p2-p1)*ny; b.vx+=(p1-p2)*nx; b.vy+=(p1-p2)*ny
            ov=2*R-d; a.x-=nx*ov/2; a.y-=ny*ov/2; b.x+=nx*ov/2; b.y+=ny*ov/2
            if bumpcd<=0:
                bumpcd=10
                if claw>0: hurt(a,'a',CLAW_DMG,'claw','clawhit'); claw=0
                else: hurt(b,'b',BUMP,'bump'); hurt(a,'a',BUMP,'bump','bump')
        bumpcd-=1; claw-=1; inked-=1
        # --- projectiles
        keep=[]
        for p in inks:
            p['x']+=p['vx']; p['y']+=p['vy']
            if not(AX0<p['x']<AX1 and AY0<p['y']<AY1): continue
            if not jump and math.hypot(p['x']-b.x,p['y']-b.y)<R+10:
                hurt(b,'b',INK_DMG,'ink','inkhit'); inked=INK_SLOW; continue
            keep.append(p)
        inks=keep; keep=[]
        for p in bubs:
            p['s']+=1; want=math.atan2(a.y-p['y'],a.x-p['x']); da=(want-p['a']+math.pi)%(2*math.pi)-math.pi
            p['a']+=max(-.05,min(.05,da)); p['x']+=math.cos(p['a'])*9; p['y']+=math.sin(p['a'])*9
            if p['s']>110 or not(AX0<p['x']<AX1 and AY0<p['y']<AY1): continue
            if math.hypot(p['x']-a.x,p['y']-a.y)<R+12: hurt(a,'a',BUB_DMG,'bubble','bubhit'); continue
            keep.append(p)
        bubs=keep
        # --- kraken tentacles: lock target KR_WARN frames ahead, then erupt
        keep=[]
        for k in krak:
            k['t']+=1
            if k['t']==1: k['x'],k['y']=clampxy(b.x+b.vx*KR_WARN*KR_LEAD,b.y+b.vy*KR_WARN*KR_LEAD)
            if k['t']==KR_WARN+1:
                erupt.append((k['x'],k['y'])); ev.append((f,'erupt'))
                if not jump and math.hypot(b.x-k['x'],b.y-k['y'])<KR_R: hurt(b,'b',KR_DMG,'kraken','krakhit')
            if k['t']<KR_WARN+14: keep.append(k)
        krak=keep
        if record:
            frames.append(dict(a=(a.x,a.y,a.hp),b=(b.x,b.y,b.hp),cd=dict(cd),casts=casts,hits=hits,
                inks=[(p['x'],p['y'],p['a']) for p in inks],bubs=[(p['x'],p['y']) for p in bubs],
                krak=[(k['x'],k['y'],k['t']) for k in krak if k['t']>=1],erupt=erupt,whip=whip,
                inked=inked>0,claw=claw>0,jump=(jump['t']/CRUSH_T,jump['tx'],jump['ty']) if jump else None,landed=landed))
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
        if 880<=r['n']<=1100 and 0<wh<=8 and casts.count('kraken')>=2 and casts.count('crush')>=2:
            res.append((r['changes'],sd,r['n'],r['win'],wh))
    ns.sort(); print(wins,'median frames',ns[len(ns)//2]); res.sort(reverse=True); print(res[:10])
