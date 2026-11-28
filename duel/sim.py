# 1v1 duel between a red dot and a blue dot. Each match draws a different skill set for each fighter
# (2 normal skills + 1 ultimate from a library). Every skill is telegraphed by a warning zone first;
# fighters can dash (with i-frames) out of zones. One skill at a time per fighter. Deterministic per seed.
import math, random
W=1080
AX0,AX1,AY0,AY1=60,1020,350,1320          # arena (sand between the two gates)
R_DOT=16
HP0=1000
DASHV,DASHT,DASHCD=24,8,80
INTRO=50

# ---- skill library: type decides shape + behaviour, el decides the look ----
NORMAL={
 'SLASH':       dict(t='cone',el='steel',r=180,h=55,dur=14,dmg=85),
 'FLAME BREATH':dict(t='cone',el='fire',r=250,h=28,dur=18,dmg=95),
 'VOID CLAW':   dict(t='cone',el='void',r=165,h=70,dur=12,dmg=80),
 'CHARGE':      dict(t='dash',el='fire',L=540,w=86,dur=22,dmg=170,n=10),
 'BLINK STRIKE':dict(t='dash',el='void',L=440,w=70,dur=16,dmg=140,n=5),
 'SHOCKWAVE':   dict(t='circle',el='lightning',r=140,dur=26,dmg=155),
 'POISON POOL': dict(t='circle',el='poison',r=170,dur=30,dmg=140),
 'ICE SPIKE':   dict(t='circle',el='ice',r=115,dur=20,dmg=150),
 'ICE SHARDS':  dict(t='fan',el='ice',n=3,sp=0.27,v=30,dur=15,dmg=60,size=12),
 'FIREBALLS':   dict(t='fan',el='fire',n=2,sp=0.2,v=24,dur=15,dmg=85,size=18),
 'VOID BOLTS':  dict(t='fan',el='void',n=5,sp=0.2,v=27,dur=15,dmg=42,size=10),
 'FROST NOVA':  dict(t='nova',el='ice',r=200,dur=20,dmg=130),
 'THUNDER NOVA':dict(t='nova',el='lightning',r=230,dur=24,dmg=140),
 'LASER':       dict(t='beam',el='light',w=60,dur=26,dmg=160),
 'ACID BEAM':   dict(t='beam',el='poison',w=84,dur=30,dmg=150),
}
ULT={
 'METEOR STORM':     dict(t='rain',el='fire',n=7,r=105,stag=8,dur=36,dmg=115),
 'ICE AGE':          dict(t='rain',el='ice',n=9,r=82,stag=5,dur=30,dmg=90),
 'PLAGUE RAIN':      dict(t='rain',el='poison',n=10,r=90,stag=4,dur=32,dmg=80),
 'THUNDER JUDGEMENT':dict(t='cross',el='lightning',r=190,w=104,dur=46,dmg=280,dmg2=170),
 'STAR FALL':        dict(t='ring',el='light',n=8,R=175,r=85,dur=40,dmg=140),
 'LASER GRID':       dict(t='grid',el='void',w=70,gap=150,stag=14,dur=30,dmg=120),
 'BLACK HOLE':       dict(t='hole',el='void',r=230,dur=52,dmg=300,pull=1.7),
}
FINAL={'fire':'INFERNO APOCALYPSE','ice':'ABSOLUTE ZERO','poison':'PLAGUE OF DOOM','lightning':"HEAVEN'S WRATH",
       'light':'SUPERNOVA','void':'OBLIVION','steel':'THOUSAND BLADES'}
CD=[55,150,420]
MELEE=('cone','nova','dash')

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
def edge_point(x,y,a):
    # point where a ray from (x,y) at angle a leaves the arena
    best=2000; vx,vy=math.cos(a),math.sin(a)
    if abs(vx)>1e-6: best=min(best,((AX1 if vx>0 else AX0)-x)/vx)
    if abs(vy)>1e-6: best=min(best,((AY1 if vy>0 else AY0)-y)/vy)
    return x+vx*best,y+vy*best

def pick_sets(seed):
    rnd=random.Random(seed*7919+13)
    names=list(NORMAL); ults=list(ULT); sets=[]; used=set()
    for i in (0,1):
        a,b=rnd.sample([n for n in names if n not in used],2)
        u=rnd.choice([x for x in ults if not sets or x!=sets[0][2]])
        used|={a,b}; sets.append([a,b,u])
    return sets

class F: pass
def simulate(seed, record=False, sets=None):
    rnd=random.Random(seed)
    sets=sets or pick_sets(seed)
    fs=[]
    for i,(x,y,ty) in enumerate(((540,1395,1130),(540,270,540))):
        f=F(); f.i=i; f.x,f.y=x,y; f.ty=ty; f.hp=HP0; f.state='intro'; f.t=0; f.sk=sets[i]
        f.cd=[rnd.randint(10,40),rnd.randint(60,110),rnd.randint(290,360)]; f.gcd=0; f.dcd=0
        f.dash=(0,0); f.strafe=rnd.choice((-1,1)); f.st_t=rnd.randint(40,90); f.flash=0; f.charge=None
        f.react=set(); f.aura=0
        f.melee=any((NORMAL[n]['t'] in MELEE) for n in f.sk[:2])
        fs.append(f)
    tele=[]; proj=[]; ev=[]; frames=[]; winner=None; endf=None; tid=[0]
    def T(owner,name,typ,el,zone,start,dur,dmg,extra=None):
        tid[0]+=1; tele.append(dict(id=tid[0],o=owner,n=name,t=typ,el=el,z=zone,start=start,end=start+dur,dmg=dmg,ex=extra or {}))
    def damage(v,d,name,fr,big=False):
        if v.state=='dash' or v.hp<=0: ev.append((fr,'miss',v.i,v.x,v.y)); return
        v.hp=max(0,v.hp-d); v.flash=6; ev.append((fr,'hit',v.i,d,v.x,v.y,name,big))
    def escape(f,zone,dist):
        best=None
        for k in range(24):
            a=2*math.pi*k/24; x,y=f.x+math.cos(a)*dist,f.y+math.sin(a)*dist
            if not(AX0<=x<=AX1 and AY0<=y<=AY1): continue
            if inzone(zone,x,y,R_DOT+8): continue
            e=fs[1-f.i]; sc=math.hypot(x-e.x,y-e.y)*0.2+rnd.random()*30
            if best is None or sc>best[0]: best=(sc,a)
        return None if best is None else best[1]
    def cast(f,e,slot,fr):
        name=f.sk[slot]; S=(NORMAL if slot<2 else ULT)[name]; typ=S['t']; el=S['el']; o=f.i
        ang=math.atan2(e.y-f.y,e.x-f.x)
        ev.append((fr,'cast',o,slot,name,el))
        lock=12
        if typ=='cone':
            T(o,name,typ,el,dict(k='cone',x=f.x,y=f.y,a=ang,r=S['r'],h=math.radians(S['h'])),fr,S['dur'],S['dmg']); lock=S['dur']
        elif typ=='dash':
            x1,y1=clampA(f.x+math.cos(ang)*S['L'],f.y+math.sin(ang)*S['L'])
            T(o,name,typ,el,dict(k='l',x0=f.x,y0=f.y,x1=x1,y1=y1,w=S['w']),fr,S['dur'],S['dmg'],dict(x1=x1,y1=y1,n=S['n'])); lock=S['dur']
        elif typ=='circle':
            T(o,name,typ,el,dict(k='c',x=e.x,y=e.y,r=S['r']),fr,S['dur'],S['dmg']); lock=10
        elif typ=='nova':
            T(o,name,typ,el,dict(k='c',x=f.x,y=f.y,r=S['r']),fr,S['dur'],S['dmg']); lock=S['dur']
        elif typ=='fan':
            subs=[]; angs=[]
            for j in range(S['n']):
                a=ang+(j-(S['n']-1)/2)*S['sp']; angs.append(a)
                subs.append(dict(k='l',x0=f.x,y0=f.y,x1=f.x+math.cos(a)*700,y1=f.y+math.sin(a)*700,w=S['size']*2+12))
            T(o,name,typ,el,dict(k='m',subs=subs),fr,S['dur'],S['dmg'],dict(angs=angs,x=f.x,y=f.y,v=S['v'],size=S['size'])); lock=S['dur']
        elif typ=='beam':
            x1,y1=edge_point(f.x,f.y,ang)
            T(o,name,typ,el,dict(k='l',x0=f.x,y0=f.y,x1=x1,y1=y1,w=S['w']),fr,S['dur'],S['dmg']); lock=S['dur']+6
        elif typ=='rain':
            f.aura=40
            for k in range(S['n']):
                if k==0: x,y=e.x,e.y
                else:
                    a=rnd.uniform(0,2*math.pi); r=rnd.uniform(80,250); x,y=clampA(e.x+math.cos(a)*r,e.y+math.sin(a)*r)
                T(o,name,typ,el,dict(k='c',x=x,y=y,r=S['r']),fr+k*S['stag'],S['dur'],S['dmg'])
            lock=24
        elif typ=='cross':
            f.aura=48
            subs=[dict(k='c',x=e.x,y=e.y,r=S['r']),dict(k='l',x0=AX0-40,y0=e.y,x1=AX1+40,y1=e.y,w=S['w']),dict(k='l',x0=e.x,y0=AY0-40,x1=e.x,y1=AY1+40,w=S['w'])]
            T(o,name,typ,el,dict(k='m',subs=subs),fr,S['dur'],S['dmg'],dict(x=e.x,y=e.y,dmg2=S['dmg2'])); lock=22
        elif typ=='ring':
            f.aura=44
            T(o,name,typ,el,dict(k='c',x=e.x,y=e.y,r=110),fr,S['dur'],S['dmg'])
            for k in range(S['n']):
                a=2*math.pi*k/S['n']; x,y=clampA(e.x+math.cos(a)*S['R'],e.y+math.sin(a)*S['R'])
                T(o,name,typ,el,dict(k='c',x=x,y=y,r=S['r']),fr,S['dur'],S['dmg'])
            lock=22
        elif typ=='grid':
            f.aura=50
            for k,off in enumerate((-S['gap'],0,S['gap'])):
                yy=e.y+off; T(o,name,typ,el,dict(k='l',x0=AX0-40,y0=yy,x1=AX1+40,y1=yy,w=S['w']),fr+k*S['stag'],S['dur'],S['dmg'])
            for k,off in enumerate((-S['gap'],0,S['gap'])):
                xx=e.x+off; T(o,name,typ,el,dict(k='l',x0=xx,y0=AY0-40,x1=xx,y1=AY1+40,w=S['w']),fr+(k+3)*S['stag'],S['dur'],S['dmg'])
            lock=24
        elif typ=='hole':
            f.aura=52
            T(o,name,typ,el,dict(k='c',x=e.x,y=e.y,r=S['r']),fr,S['dur'],S['dmg'],dict(pull=S['pull'])); lock=20
        f.state='cast'; f.t=lock
    fr=0
    while fr<2400:
        for f in fs:
            e=fs[1-f.i]
            if f.hp<=0: continue
            for k in range(3): f.cd[k]=max(0,f.cd[k]-1)
            f.gcd=max(0,f.gcd-1); f.dcd=max(0,f.dcd-1); f.flash=max(0,f.flash-1); f.aura=max(0,f.aura-1)
            if f.state=='intro':
                f.y+=(f.ty-f.y)*0.08
                if fr>=INTRO: f.state='free'
                continue
            if winner is not None: continue
            for t in tele:     # black holes pull the enemy in
                if t['t']=='hole' and t['o']!=f.i and t['start']<=fr and f.state!='dash':
                    dx,dy=t['z']['x']-f.x,t['z']['y']-f.y; dd=math.hypot(dx,dy)
                    if 10<dd<t['z']['r']*1.6: f.x+=dx/dd*t['ex']['pull']; f.y+=dy/dd*t['ex']['pull']
            if f.state=='dash':
                f.x+=f.dash[0]; f.y+=f.dash[1]; f.x,f.y=clampA(f.x,f.y); f.t-=1
                if f.t<=0: f.state='free'
                continue
            if f.state=='charge':
                c=f.charge; c['k']+=1; p=c['k']/c['n']
                f.x=c['x0']+(c['x1']-c['x0'])*p; f.y=c['y0']+(c['y1']-c['y0'])*p
                if not c['hit'] and math.hypot(f.x-e.x,f.y-e.y)<R_DOT*2+18:
                    c['hit']=True; damage(e,c['dmg'],c['name'],fr,True)
                if c['k']>=c['n']: f.state='free'; ev.append((fr,'dash_end',f.i,f.x,f.y,c['el']))
                continue
            if f.state=='cast':
                f.t-=1
                if f.t<=0: f.state='free'
                continue
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
                    elif t['end']-fr>22: f.react.discard(t['id'])
                a=escape(f,t['z'],60)
                if a is not None:
                    f.x+=math.cos(a)*3.6; f.y+=math.sin(a)*3.6; f.x,f.y=clampA(f.x,f.y)
                continue
            d=math.hypot(e.x-f.x,e.y-f.y); ang=math.atan2(e.y-f.y,e.x-f.x)
            busy=any(t['o']==f.i for t in tele) or any(p['o']==f.i for p in proj)
            if f.gcd==0 and e.hp>0 and not busy:
                pick=None
                if f.cd[2]==0: pick=2
                else:
                    for slot in (1,0):
                        if f.cd[slot]>0: continue
                        S=NORMAL[f.sk[slot]]; tp=S['t']
                        ok=(tp=='cone' and d<S['r']*0.95) or (tp=='nova' and d<S['r']*0.9) or (tp=='dash' and d<S['L']) or tp in ('circle','fan','beam')
                        if ok: pick=slot; break
                if pick is not None:
                    f.cd[pick]=CD[pick]+rnd.randint(-10,10); f.gcd=24; cast(f,e,pick,fr); continue
            pref=150 if f.melee else 330
            f.st_t-=1
            if f.st_t<=0: f.strafe*=-1; f.st_t=rnd.randint(40,100)
            rad=max(-1,min(1,(d-pref)/80)); tan=f.strafe*0.8
            vx=math.cos(ang)*rad-math.sin(ang)*tan; vy=math.sin(ang)*rad+math.cos(ang)*tan
            n=math.hypot(vx,vy) or 1; sp=3.6 if f.melee else 2.9
            f.x+=vx/n*sp; f.y+=vy/n*sp; f.x,f.y=clampA(f.x,f.y)
        for t in [t for t in tele if t['end']==fr]:
            o=fs[t['o']]; v=fs[1-t['o']]; z=t['z']; typ=t['t']
            ev.append((fr,'res',t['o'],t['n'],typ,t['el'],z,t['ex']))
            big=typ in ('rain','cross','ring','grid','hole')
            if typ=='dash':
                o.state='charge'; o.charge=dict(x0=o.x,y0=o.y,x1=t['ex']['x1'],y1=t['ex']['y1'],k=0,n=t['ex']['n'],hit=False,dmg=t['dmg'],name=t['n'],el=t['el'])
            elif typ=='fan':
                for a in t['ex']['angs']: proj.append(dict(o=t['o'],x=t['ex']['x'],y=t['ex']['y'],a=a,d=0,v=t['ex']['v'],size=t['ex']['size'],el=t['el'],dmg=t['dmg'],n=t['n'],alive=True))
            elif typ=='cross':
                if inzone(z['subs'][0],v.x,v.y,R_DOT*0.6): damage(v,t['dmg'],t['n'],fr,True)
                elif inzone(z,v.x,v.y,R_DOT*0.6): damage(v,t['ex']['dmg2'],t['n'],fr,True)
            else:
                if inzone(z,v.x,v.y,R_DOT*0.6): damage(v,t['dmg'],t['n'],fr,big)
        tele=[t for t in tele if t['end']>fr]
        for p in proj:
            p['x']+=math.cos(p['a'])*p['v']; p['y']+=math.sin(p['a'])*p['v']; p['d']+=p['v']
            v=fs[1-p['o']]
            if v.hp>0 and math.hypot(p['x']-v.x,p['y']-v.y)<R_DOT+p['size']:
                p['alive']=False; ev.append((fr,'proj_hit',p['o'],p['x'],p['y'],p['el'])); damage(v,p['dmg'],p['n'],fr)
            if p['d']>720 or not(0<p['x']<W and 200<p['y']<1500): p['alive']=False
        proj=[p for p in proj if p['alive']]
        if winner is None:
            dead=[f for f in fs if f.hp<=0]
            if dead:
                winner=1-dead[0].i; endf=fr; ev.append((fr,'ko',dead[0].i,dead[0].x,dead[0].y))
        if record:
            frames.append(dict(f=[(f.x,f.y,f.hp,f.state,f.flash,f.aura) for f in fs],
                               tele=[(t['n'],t['o'],t['z'],(fr-t['start'])/(t['end']-t['start']),t['t'],t['el']) for t in tele if t['start']<=fr],
                               proj=[(p['x'],p['y'],p['a'],p['el'],p['size'],p['o']) for p in proj]))
        fr+=1
        if endf is not None and fr>endf: break
    ults=[sum(1 for e in ev if e[1]=='cast' and e[2]==i and e[3]==2) for i in (0,1)]
    dashes=sum(1 for e in ev if e[1]=='dash')
    return dict(frames=frames,ev=ev,win=winner,n=fr,endf=endf,hp=[f.hp for f in fs],ults=ults,dashes=dashes,sets=sets)

if __name__=='__main__':
    import collections
    out=[]
    for sd in range(400):
        r=simulate(sd)
        if r['win'] is None: continue
        out.append((r['hp'][r['win']],sd,r['endf'],r['win'],r['ults'],r['dashes'],r['sets']))
    print(collections.Counter(o[3] for o in out), sorted(o[2] for o in out)[len(out)//2])
    good=[o for o in out if 600<=o[2]<=1000 and min(o[4])>=1]; good.sort(key=lambda o:o[0])
    for o in good[:15]: print(o)
