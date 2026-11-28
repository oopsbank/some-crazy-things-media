"""Octopus vs Crab. Side 'a' = Octopus, side 'b' = Crab. Every move is unique across the roster (see HANDOFF skill registry).
Skill 1 = A1/B1 (fixed: INK MINE / PEARL). INK, CAMO BLINK, BUBBLES, BURROW are implemented but unused.
Octopus: skill 1 = INK (3 blobs, slow) -> INK MINE (trap, explodes on contact) -> CAMO BLINK (teleport behind crab + strike)
         skill 2 = TENTACLE WHIP (lash in range + pull); ult KRAKEN (tentacles erupt where the crab is heading)
Crab:    skill 1 = BUBBLES (3 homing) -> PEARL (ricochets off walls) -> BURROW (dig under, pop up under the octopus)
         skill 2 = CLAW BOOMERANG (flies out and returns, can hit both ways); ult CRAB CRUSH (leap + shockwave)
"""
import math, random
AX0,AY0,AX1,AY1 = 120,420,960,1260
R=58; SPEED=11.0
CD={'s1a':90,'whip':95,'kraken':430,'s1b':70,'boomer':105,'crush':370}
A1=('mine',); B1=('pearl',)   # fixed skill 1 (tuple kept so moves can be swapped easily)
INK_DMG=2; INK_SLOW=45; MINE_DMG=4; MINE_ARM=12; MINE_LIFE=330; BLINK_DMG=5
WHIP_RANGE=330; WHIP_DMG=6
KR_N=5; KR_GAP=12; KR_WARN=16; KR_R=90; KR_DMG=8; KR_LEAD=0.5
BUB_DMG=2; BUB_SPREAD=(-.35,0,.35); PEARL_DMG=7; PEARL_V=17; PEARL_BOUNCES=3
BURROW_T=34; BURROW_DMG=8; BURROW_R=170
BOOM_V=20; BOOM_OUT=18; BOOM_DMG=4
CRUSH_T=26; CRUSH_R=190; CR_LEAD=(0.2,0.5); CRUSH_DMG=18; BUMP=1
class Ball:
    def __init__(s,x,y,a): s.x,s.y=x,y; s.vx=math.cos(a)*SPEED; s.vy=math.sin(a)*SPEED; s.hp=100
def clampxy(x,y): return min(max(x,AX0+R),AX1-R),min(max(y,AY0+R),AY1-R)
def inside(x,y): return AX0<x<AX1 and AY0<y<AY1
def simulate(seed, record=False):
    rnd=random.Random(seed)
    a=Ball(330,1000,rnd.uniform(0,6.28)); b=Ball(750,680,rnd.uniform(0,6.28))
    cd=dict(CD)
    inks=[]; mines=[]; bubs=[]; pearls=[]; booms=[]; krak=[]
    st=dict(inked=0,burrow=0,jump=None)
    ia=ib=0; bumpcd=0; ev=[]; frames=[]; lead=[]
    f=0
    while f<2000:
        casts=[]; hits=[]; whip=None; erupt=[]; landed=None; blink=None; minebooms=[]; popup=None
        for k in cd: cd[k]-=1
        def hidden(): return st['jump'] is not None or st['burrow']>0
        def hurt(o,side,dm,kind,evk=None):
            if side=='b' and hidden(): return
            o.hp-=dm; hits.append((side,dm,kind))
            if evk: ev.append((f,evk))
        # --- octopus skills
        if cd['s1a']<=0:
            mv=A1[ia%len(A1)]; ia+=1; cd['s1a']=CD['s1a']; casts.append(mv); base=math.atan2(b.y-a.y,b.x-a.x)
            if mv=='ink':
                for da in (-.2,0,.2):
                    g=base+da; inks.append(dict(x=a.x+math.cos(g)*R,y=a.y+math.sin(g)*R,vx=math.cos(g)*14,vy=math.sin(g)*14,a=g))
            elif mv=='mine': mines.append(dict(x=a.x,y=a.y,t=0))
            else:
                m=math.hypot(b.vx,b.vy) or 1; ox,oy=a.x,a.y
                a.x,a.y=clampxy(b.x-b.vx/m*(2*R+25),b.y-b.vy/m*(2*R+25)); a.vx,a.vy=b.vx,b.vy
                blink=(ox,oy,a.x,a.y); hurt(b,'b',BLINK_DMG,'blink','blinkhit')
        if cd['whip']<=0:
            cd['whip']=CD['whip']; casts.append('whip')
            dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
            if d<=WHIP_RANGE and not hidden():
                hurt(b,'b',WHIP_DMG,'whip','whiphit'); b.vx,b.vy=-dx/d,-dy/d; whip=(a.x,a.y,b.x,b.y,True)
            else:
                L=min(d,WHIP_RANGE); whip=(a.x,a.y,a.x+dx/d*L,a.y+dy/d*L,False)
        if cd['kraken']<=0:
            cd['kraken']=CD['kraken']; casts.append('kraken')
            for k in range(KR_N): krak.append(dict(t=-k*KR_GAP,x=None,y=None))
        # --- crab skills (not while airborne / underground)
        if cd['s1b']<=0 and not hidden():
            mv=B1[ib%len(B1)]; ib+=1; cd['s1b']=CD['s1b']; casts.append(mv); base=math.atan2(a.y-b.y,a.x-b.x)
            if mv=='bubbles':
                for da in BUB_SPREAD:
                    g=base+da; bubs.append(dict(x=b.x+math.cos(g)*R,y=b.y+math.sin(g)*R,a=g,s=0))
            elif mv=='pearl':
                pearls.append(dict(x=b.x+math.cos(base)*R,y=b.y+math.sin(base)*R,vx=math.cos(base)*PEARL_V,vy=math.sin(base)*PEARL_V,n=0,s=0))
            else: st['burrow']=BURROW_T
        if cd['boomer']<=0 and not hidden():
            cd['boomer']=CD['boomer']; casts.append('boomer'); g=math.atan2(a.y-b.y,a.x-b.x)
            booms.append(dict(x=b.x,y=b.y,vx=math.cos(g)*BOOM_V,vy=math.sin(g)*BOOM_V,s=0,ho=False,hb=False,rot=0))
        if cd['crush']<=0 and not hidden():
            cd['crush']=CD['crush']; casts.append('crush')
            ld=rnd.uniform(*CR_LEAD); tx,ty=clampxy(a.x+a.vx*CRUSH_T*ld,a.y+a.vy*CRUSH_T*ld)
            st['jump']=dict(t=0,x0=b.x,y0=b.y,tx=tx,ty=ty)
        for c in casts: ev.append((f,'cast',c))
        # --- movement
        if st['burrow']>0:   # tunnel toward the octopus underground
            g=math.atan2(a.y-b.y,a.x-b.x); b.vx,b.vy=math.cos(g),math.sin(g)
        sb=SPEED*(1.5 if st['burrow']>0 else 1)*(0.6 if st['inked']>0 else 1)
        movers=[(a,SPEED)]+([] if st['jump'] else [(b,sb)])
        for o,sp in movers:
            m=math.hypot(o.vx,o.vy) or 1; o.vx*=sp/m; o.vy*=sp/m
            o.x+=o.vx; o.y+=o.vy
            if o.x<AX0+R: o.x=AX0+R; o.vx=abs(o.vx)
            if o.x>AX1-R: o.x=AX1-R; o.vx=-abs(o.vx)
            if o.y<AY0+R: o.y=AY0+R; o.vy=abs(o.vy)
            if o.y>AY1-R: o.y=AY1-R; o.vy=-abs(o.vy)
        j=st['jump']
        if j:
            j['t']+=1; u=j['t']/CRUSH_T
            b.x=j['x0']+(j['tx']-j['x0'])*u; b.y=j['y0']+(j['ty']-j['y0'])*u
            if j['t']>=CRUSH_T:
                landed=(b.x,b.y); ev.append((f,'land')); st['jump']=None
                if math.hypot(a.x-b.x,a.y-b.y)<CRUSH_R: hurt(a,'a',CRUSH_DMG,'crush')
                g=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(g),math.sin(g)
        if st['burrow']>0:
            st['burrow']-=1
            if st['burrow']==0:
                popup=(b.x,b.y); ev.append((f,'popup'))
                if math.hypot(a.x-b.x,a.y-b.y)<BURROW_R: hurt(a,'a',BURROW_DMG,'burrow')
                g=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(g),math.sin(g)
        # --- body contact
        dx,dy=b.x-a.x,b.y-a.y; d=math.hypot(dx,dy) or 1
        if d<2*R and not hidden():
            nx,ny=dx/d,dy/d; p1=a.vx*nx+a.vy*ny; p2=b.vx*nx+b.vy*ny
            if p1-p2>0: a.vx+=(p2-p1)*nx; a.vy+=(p2-p1)*ny; b.vx+=(p1-p2)*nx; b.vy+=(p1-p2)*ny
            ov=2*R-d; a.x-=nx*ov/2; a.y-=ny*ov/2; b.x+=nx*ov/2; b.y+=ny*ov/2
            if bumpcd<=0: bumpcd=10; hurt(b,'b',BUMP,'bump'); hurt(a,'a',BUMP,'bump','bump')
        bumpcd-=1; st['inked']-=1
        # --- octopus projectiles / traps
        keep=[]
        for p in inks:
            p['x']+=p['vx']; p['y']+=p['vy']
            if not inside(p['x'],p['y']): continue
            if not hidden() and math.hypot(p['x']-b.x,p['y']-b.y)<R+10:
                hurt(b,'b',INK_DMG,'ink','inkhit'); st['inked']=INK_SLOW; continue
            keep.append(p)
        inks=keep; keep=[]
        for m in mines:
            m['t']+=1
            if m['t']>MINE_ARM and not hidden() and math.hypot(m['x']-b.x,m['y']-b.y)<R+28:
                minebooms.append((m['x'],m['y'])); hurt(b,'b',MINE_DMG,'mine','minehit'); st['inked']=INK_SLOW; continue
            if m['t']<MINE_LIFE: keep.append(m)
        mines=keep
        # --- crab projectiles
        keep=[]
        for p in bubs:
            p['s']+=1; want=math.atan2(a.y-p['y'],a.x-p['x']); da=(want-p['a']+math.pi)%(2*math.pi)-math.pi
            p['a']+=max(-.05,min(.05,da)); p['x']+=math.cos(p['a'])*9; p['y']+=math.sin(p['a'])*9
            if p['s']>110 or not inside(p['x'],p['y']): continue
            if math.hypot(p['x']-a.x,p['y']-a.y)<R+12: hurt(a,'a',BUB_DMG,'bubble','bubhit'); continue
            keep.append(p)
        bubs=keep; keep=[]
        for p in pearls:
            p['x']+=p['vx']; p['y']+=p['vy']; p['s']+=1; bounced=False
            if p['x']<AX0+14 or p['x']>AX1-14: p['vx']*=-1; p['x']=min(max(p['x'],AX0+14),AX1-14); bounced=True
            if p['y']<AY0+14 or p['y']>AY1-14: p['vy']*=-1; p['y']=min(max(p['y'],AY0+14),AY1-14); bounced=True
            if bounced: p['n']+=1; ev.append((f,'ping'))
            if p['n']>PEARL_BOUNCES or p['s']>150: continue
            if math.hypot(p['x']-a.x,p['y']-a.y)<R+14: hurt(a,'a',PEARL_DMG,'pearl','pearlhit'); continue
            keep.append(p)
        pearls=keep; keep=[]
        for p in booms:
            p['s']+=1; p['rot']+=0.6
            if p['s']>BOOM_OUT:   # curve back to the crab
                g=math.atan2(b.y-p['y'],b.x-p['x']); sp=BOOM_V*1.1
                p['vx']+=(math.cos(g)*sp-p['vx'])*.25; p['vy']+=(math.sin(g)*sp-p['vy'])*.25
            p['x']+=p['vx']; p['y']+=p['vy']
            if math.hypot(p['x']-a.x,p['y']-a.y)<R+20:
                if p['s']<=BOOM_OUT and not p['ho']: p['ho']=True; hurt(a,'a',BOOM_DMG,'boomer','boomhit')
                elif p['s']>BOOM_OUT+5 and not p['hb']: p['hb']=True; hurt(a,'a',BOOM_DMG,'boomer','boomhit')
            if p['s']>BOOM_OUT+4 and math.hypot(p['x']-b.x,p['y']-b.y)<R: continue
            if p['s']>90: continue
            keep.append(p)
        booms=keep
        # --- kraken tentacles
        keep=[]
        for k in krak:
            k['t']+=1
            if k['t']==1: k['x'],k['y']=clampxy(b.x+b.vx*KR_WARN*KR_LEAD,b.y+b.vy*KR_WARN*KR_LEAD)
            if k['t']==KR_WARN+1:
                erupt.append((k['x'],k['y'])); ev.append((f,'erupt'))
                if not hidden() and math.hypot(b.x-k['x'],b.y-k['y'])<KR_R: hurt(b,'b',KR_DMG,'kraken','krakhit')
            if k['t']<KR_WARN+14: keep.append(k)
        krak=keep
        if record:
            j=st['jump']
            frames.append(dict(a=(a.x,a.y,a.hp),b=(b.x,b.y,b.hp),cd=dict(cd),casts=casts,hits=hits,
                inks=[(p['x'],p['y'],p['a']) for p in inks],mines=[(m['x'],m['y'],m['t']) for m in mines],minebooms=minebooms,blink=blink,
                bubs=[(p['x'],p['y']) for p in bubs],pearls=[(p['x'],p['y'],p['vx'],p['vy']) for p in pearls],
                booms=[(p['x'],p['y'],p['rot'],p['s']>BOOM_OUT) for p in booms],burrow=st['burrow']>0,popup=popup,
                krak=[(k['x'],k['y'],k['t']) for k in krak if k['t']>=1],erupt=erupt,whip=whip,inked=st['inked']>0,
                jump=(j['t']/CRUSH_T,j['tx'],j['ty']) if j else None,landed=landed,n1a=A1[ia%len(A1)],n1b=B1[ib%len(B1)]))
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
