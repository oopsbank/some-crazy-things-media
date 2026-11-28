# 1v1 duel between a red dot and a blue dot. Every skill is telegraphed by a red warning zone first;
# fighters can dash (with i-frames) out of zones. Deterministic per seed.
import math, random
W=1080
AX0,AX1,AY0,AY1=60,1020,350,1320          # arena (sand between the two gates)
R_DOT=16
HP0=1000
DASHV,DASHT,DASHCD=24,8,80
NAMES={0:['SLASH','CHARGE','METEOR STORM'],1:['ICE SHARDS','SHOCKWAVE','THUNDER JUDGEMENT']}
CD={0:[55,150,420],1:[55,150,420]}
INTRO=50

def segd(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy or 1; t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-ax-t*dx,py-ay-t*dy)
def angdiff(a,b): return abs((a-b+math.pi)%(2*math.pi)-math.pi)
def inzone(z,x,y,pad=0):
    k=z['k']
    if k=='c': return math.hypot(x-z['x'],y-z['y'])<z['r']+pad
    if k=='l': return segd(x,y,z['x0'],z['y0'],z['x1'],z['y1'])<z['w']/2+pad
    if k=='cone':
        dd=math.hypot(x-z['x'],y-z['y'])
        return dd<z['r']+pad and (dd<20 or angdiff(math.atan2(y-z['y'],x-z['x']),z['a'])<z['h'])
    if k=='m': return any(inzone(s,x,y,pad) for s in z['subs'])
def clampA(x,y): return min(max(x,AX0),AX1),min(max(y,AY0),AY1)

class F: pass
def simulate(seed, record=False):
    rnd=random.Random(seed)
    fs=[]
    for i,(x,y,ty) in enumerate(((540,1395,1130),(540,270,540))):
        f=F(); f.i=i; f.x,f.y=x,y; f.ty=ty; f.hp=HP0; f.state='intro'; f.t=0
        f.cd=[rnd.randint(10,40),rnd.randint(60,110),rnd.randint(290,360)]; f.gcd=0; f.dcd=0
        f.dash=(0,0); f.strafe=rnd.choice((-1,1)); f.st_t=rnd.randint(40,90); f.flash=0; f.charge=None; f.cast=None
        f.react=set(); f.flee=None; f.aura=0
        fs.append(f)
    tele=[]; proj=[]; ev=[]; frames=[]; winner=None; endf=None; tid=[0]
    def T(owner,skill,zone,start,dur,dmg,extra=None):
        tid[0]+=1; tele.append(dict(id=tid[0],o=owner,s=skill,z=zone,start=start,end=start+dur,dmg=dmg,ex=extra or {}))
    def damage(v,d,src,fr):
        if v.state=='dash' or v.hp<=0: ev.append((fr,'miss',v.i,v.x,v.y)); return
        v.hp=max(0,v.hp-d); v.flash=6; ev.append((fr,'hit',v.i,d,v.x,v.y,src))
    def escape(f,zone,dist):
        best=None
        for k in range(24):
            a=2*math.pi*k/24; x,y=f.x+math.cos(a)*dist,f.y+math.sin(a)*dist
            if not(AX0<=x<=AX1 and AY0<=y<=AY1): continue
            if inzone(zone,x,y,R_DOT+8): continue
            # prefer directions that don't run straight into the enemy
            e=fs[1-f.i]; sc=math.hypot(x-e.x,y-e.y)*0.2+rnd.random()*30
            if best is None or sc>best[0]: best=(sc,a)
        return None if best is None else best[1]
    fr=0
    while fr<2400:
        for f in fs:
            e=fs[1-f.i]
            if f.hp<=0: continue
            for k in range(3): f.cd[k]=max(0,f.cd[k]-1)
            f.gcd=max(0,f.gcd-1); f.dcd=max(0,f.dcd-1); f.flash=max(0,f.flash-1); f.aura=max(0,f.aura-1)
            if f.state=='intro':
                f.y+= (f.ty-f.y)*0.08
                if fr>=INTRO: f.state='free'
                continue
            if winner is not None: continue
            if f.state=='dash':
                f.x+=f.dash[0]; f.y+=f.dash[1]; f.x,f.y=clampA(f.x,f.y); f.t-=1
                if f.t<=0: f.state='free'
                continue
            if f.state=='charge':
                c=f.charge; c['k']+=1; p=c['k']/c['n']
                f.x=c['x0']+(c['x1']-c['x0'])*p; f.y=c['y0']+(c['y1']-c['y0'])*p
                if not c['hit'] and math.hypot(f.x-e.x,f.y-e.y)<R_DOT*2+18:
                    c['hit']=True; damage(e,170,'CHARGE',fr)
                if c['k']>=c['n']: f.state='free'; ev.append((fr,'charge_end',f.i,f.x,f.y))
                continue
            if f.state=='cast':
                f.t-=1
                if f.t<=0: f.state='free'
                continue
            # ---- free: react to enemy warning zones ----
            danger=[t for t in tele if t['o']!=f.i and t['start']<=fr<t['end'] and inzone(t['z'],f.x,f.y,R_DOT)]
            if danger:
                t=min(danger,key=lambda q:q['end'])
                if t['id'] not in f.react:
                    f.react.add(t['id'])
                    if f.dcd==0 and rnd.random()<0.72 and t['end']-fr<=rnd.randint(8,22) or (f.dcd==0 and t['end']-fr<=6 and rnd.random()<0.5):
                        a=escape(f,t['z'],DASHV*DASHT)
                        if a is not None:
                            f.state='dash'; f.t=DASHT; f.dash=(math.cos(a)*DASHV,math.sin(a)*DASHV); f.dcd=DASHCD
                            ev.append((fr,'dash',f.i,f.x,f.y,a)); continue
                    else: f.react.discard(t['id']) if t['end']-fr>22 else None
                a=escape(f,t['z'],60)
                if a is not None:
                    f.x+=math.cos(a)*3.6; f.y+=math.sin(a)*3.6; f.x,f.y=clampA(f.x,f.y)
                continue
            # ---- choose a skill ----
            d=math.hypot(e.x-f.x,e.y-f.y); ang=math.atan2(e.y-f.y,e.x-f.x)
            cast=None
            # one skill at a time: wait until our previous skill has fully resolved
            busy=any(t['o']==f.i for t in tele) or (f.i==1 and len(proj)>0)
            if f.gcd==0 and e.hp>0 and not busy:
                if f.cd[2]==0: cast=2
                elif f.cd[1]==0 and (f.i==1 or d<540): cast=1
                elif f.cd[0]==0 and (f.i==1 or d<190): cast=0
            if cast is not None:
                f.cd[cast]=CD[f.i][cast]+rnd.randint(-10,10); f.gcd=24; nm=NAMES[f.i][cast]
                ev.append((fr,'cast',f.i,cast,nm))
                if f.i==0 and cast==0:
                    T(0,'SLASH',dict(k='cone',x=f.x,y=f.y,a=ang,r=180,h=math.radians(55)),fr,14,85)
                    f.state='cast'; f.t=14
                elif f.i==0 and cast==1:
                    L=540; x1,y1=clampA(f.x+math.cos(ang)*L,f.y+math.sin(ang)*L)
                    T(0,'CHARGE',dict(k='l',x0=f.x,y0=f.y,x1=x1,y1=y1,w=86),fr,22,0,dict(x1=x1,y1=y1))
                    f.state='cast'; f.t=22
                elif f.i==0 and cast==2:
                    f.aura=40
                    for k in range(7):
                        if k==0: x,y=e.x,e.y
                        else:
                            a=rnd.uniform(0,2*math.pi); r=rnd.uniform(90,240); x,y=clampA(e.x+math.cos(a)*r,e.y+math.sin(a)*r)
                        T(0,'METEOR',dict(k='c',x=x,y=y,r=105),fr+k*8,36,115)
                    f.state='cast'; f.t=24
                elif f.i==1 and cast==0:
                    subs=[]
                    for da in (-0.27,0,0.27):
                        a=ang+da; subs.append(dict(k='l',x0=f.x,y0=f.y,x1=f.x+math.cos(a)*680,y1=f.y+math.sin(a)*680,w=34))
                    T(1,'SHARDS',dict(k='m',subs=subs),fr,15,0,dict(angs=[ang-0.27,ang,ang+0.27],x=f.x,y=f.y))
                    f.state='cast'; f.t=15
                elif f.i==1 and cast==1:
                    T(1,'SHOCK',dict(k='c',x=e.x,y=e.y,r=140),fr,26,155)
                    f.state='cast'; f.t=10
                elif f.i==1 and cast==2:
                    f.aura=48
                    subs=[dict(k='c',x=e.x,y=e.y,r=190),dict(k='l',x0=AX0-40,y0=e.y,x1=AX1+40,y1=e.y,w=104),dict(k='l',x0=e.x,y0=AY0-40,x1=e.x,y1=AY1+40,w=104)]
                    T(1,'THUNDER',dict(k='m',subs=subs),fr,46,0,dict(x=e.x,y=e.y))
                    f.state='cast'; f.t=22
                continue
            # ---- move: red wants melee range, blue keeps distance; strafe around ----
            pref=150 if f.i==0 else 330
            f.st_t-=1
            if f.st_t<=0: f.strafe*=-1; f.st_t=rnd.randint(40,100)
            rad=max(-1,min(1,(d-pref)/80)); tan=f.strafe*0.8
            vx=math.cos(ang)*rad-math.sin(ang)*tan; vy=math.sin(ang)*rad+math.cos(ang)*tan
            n=math.hypot(vx,vy) or 1; sp=3.7 if f.i==0 else 2.8
            f.x+=vx/n*sp; f.y+=vy/n*sp; f.x,f.y=clampA(f.x,f.y)
        # ---- resolve telegraphs ----
        for t in [t for t in tele if t['end']==fr]:
            o=fs[t['o']]; v=fs[1-t['o']]; z=t['z']
            if t['s']=='SLASH':
                ev.append((fr,'slash',0,z['x'],z['y'],z['a']))
                if inzone(z,v.x,v.y,R_DOT*0.6): damage(v,t['dmg'],'SLASH',fr)
            elif t['s']=='CHARGE':
                o.state='charge'; o.charge=dict(x0=o.x,y0=o.y,x1=t['ex']['x1'],y1=t['ex']['y1'],k=0,n=10,hit=False)
                ev.append((fr,'charge',0,o.x,o.y))
            elif t['s']=='METEOR':
                ev.append((fr,'meteor',0,z['x'],z['y']))
                if inzone(z,v.x,v.y,R_DOT*0.6): damage(v,t['dmg'],'METEOR',fr)
            elif t['s']=='SHARDS':
                for a in t['ex']['angs']: proj.append(dict(x=t['ex']['x'],y=t['ex']['y'],a=a,d=0,alive=True))
                ev.append((fr,'shards',1,t['ex']['x'],t['ex']['y']))
            elif t['s']=='SHOCK':
                ev.append((fr,'shock',1,z['x'],z['y']))
                if inzone(z,v.x,v.y,R_DOT*0.6): damage(v,t['dmg'],'SHOCK',fr)
            elif t['s']=='THUNDER':
                ev.append((fr,'thunder',1,t['ex']['x'],t['ex']['y']))
                if inzone(z['subs'][0],v.x,v.y,R_DOT*0.6): damage(v,280,'THUNDER',fr)
                elif inzone(z,v.x,v.y,R_DOT*0.6): damage(v,170,'THUNDER',fr)
        tele=[t for t in tele if t['end']>fr]
        for p in proj:
            p['x']+=math.cos(p['a'])*30; p['y']+=math.sin(p['a'])*30; p['d']+=30
            v=fs[0]
            if v.hp>0 and math.hypot(p['x']-v.x,p['y']-v.y)<R_DOT+12:
                p['alive']=False; ev.append((fr,'shard_hit',1,p['x'],p['y'])); damage(v,60,'SHARDS',fr)
            if p['d']>700: p['alive']=False
        proj=[p for p in proj if p['alive']]
        if winner is None:
            dead=[f for f in fs if f.hp<=0]
            if dead:
                winner=1-dead[0].i; endf=fr; ev.append((fr,'ko',dead[0].i,dead[0].x,dead[0].y))
        if record:
            frames.append(dict(f=[(f.x,f.y,f.hp,f.state,f.flash,[f.cd[k]/CD[f.i][k] for k in range(3)],f.aura) for f in fs],
                               tele=[(t['s'],t['o'],t['z'],(fr-t['start'])/(t['end']-t['start'])) for t in tele if t['start']<=fr],
                               proj=[(p['x'],p['y'],p['a']) for p in proj]))
        fr+=1
        if endf is not None and fr>endf: break
    ults=[sum(1 for e in ev if e[1]=='cast' and e[2]==i and e[3]==2) for i in (0,1)]
    dashes=sum(1 for e in ev if e[1]=='dash')
    return dict(frames=frames,ev=ev,win=winner,n=fr,endf=endf,hp=[f.hp for f in fs],ults=ults,dashes=dashes)

if __name__=='__main__':
    out=[]
    for sd in range(300):
        r=simulate(sd)
        if r['win'] is None: continue
        out.append((r['hp'][r['win']],sd,r['endf'],r['win'],r['ults'],r['dashes']))
    import collections
    print(collections.Counter(o[3] for o in out), sorted(o[2] for o in out)[len(out)//2])
    good=[o for o in out if 600<=o[2]<=1000 and min(o[4])>=1]; good.sort()
    for o in good[:12]: print(o)
