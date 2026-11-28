import math, random
W=1080
ROWS=[230,310,390,470,550,630,710,790,870,950]   # 0 spawn,1-2 road A,3 walk,4 mult,5 walk,6-7 road B,8 walk,9 finish
LANES={1:(1,6.5),2:(-1,8.0),6:(-1,7.0),7:(1,8.5)}
CARW=150
TILES=[(1,150),(2,130),(3,115),(5,95),(20,62),(100,50)]
PERIOD=sum(w for _,w in TILES)+ 40
CONV=2.6
CX=[270,810]; CY=1490
START_N=5; BASE=50; SPAWN=2; DECAY=0.9975; GAP=(1300,2000); MAXN=40
K=3.5
def rad(v): return K*math.sqrt(max(v,0))+10
def tile_at(x,f):
    u=(x+f*CONV)%PERIOD; acc=0
    for m,w in TILES:
        if acc<=u<acc+w: return m
        acc+=w
    return 1
class C: pass
def simulate(seed, record=False):
    rnd=random.Random(seed)
    cars={l:[] for l in LANES}
    for l,(d,sp) in LANES.items():
        x=rnd.uniform(0,300)
        while x<W+400: cars[l].append(x); x+=rnd.uniform(*GAP)
    ch=[]; fly=[]; big=[100.0,100.0]; ev=[]; frames=[]; winner=None; f=0; endf=None; lead=[]
    def spawn(side,delay):
        c=C(); c.side=side; c.x=CX[side]+rnd.uniform(-210,210); c.row=0; c.hop=0; c.wait=delay; c.v=BASE; c.mult=None; c.alive=True
        ch.append(c); return c
    for side in (0,1):
        for k in range(START_N): spawn(side,k*rnd.randint(6,14)+rnd.randint(4,12))
    while f<1800:
        for l,(d,sp) in LANES.items():
            cs=[x+d*sp for x in cars[l]]
            if d>0:
                cs=[x for x in cs if x<W+200]
                if min(cs)>-CARW: cs.append(min(cs)-rnd.uniform(*GAP))
            else:
                cs=[x for x in cs if x>-200]
                if max(cs)<W+CARW: cs.append(max(cs)+rnd.uniform(*GAP))
            cars[l]=cs
        for c in list(ch):
            if c.hop>0:
                c.hop-=1
                if c.hop==0:
                    c.row+=1; c.wait=rnd.randint(3,15)
                    if c.row==4:
                        m=tile_at(c.x,f); c.v*=m; c.mult=m; ev.append((f,'mult',c.side,m,c.x))
                        if m>1 and winner is None and sum(1 for q in ch if q.side==c.side)<MAXN:
                            for k in range(SPAWN): spawn(c.side,rnd.randint(4,20)+k*8)
                            ev.append((f,'spawn',c.side,SPAWN))
                    if c.row==9:
                        c.alive=False; fly.append([c.side,c.x,ROWS[9],c.v,0]); 
            elif c.wait>0: c.wait-=1
            else: c.hop=8
            # collision
            y=ROWS[c.row]+(80*(8-c.hop)/8 if c.hop>0 else 0)
            for l in LANES:
                if abs(y-ROWS[l])<30:
                    for x in cars[l]:
                        if abs(c.x-x)<CARW/2+14:
                            c.alive=False; ev.append((f,'splat',c.side,c.x,y,c.v)); break
        ch=[c for c in ch if c.alive]
        for fl in fly:
            fl[4]+=1
            if fl[4]==14:
                if winner is None: big[fl[0]]+=fl[3]; ev.append((f,'feed',fl[0],fl[3]))
        fly=[fl for fl in fly if fl[4]<14]
        if winner is None:
            for s in (0,1): big[s]*=DECAY
            if rad(big[0])+rad(big[1])>=CX[1]-CX[0]:
                winner=0 if big[0]>big[1] else 1; endf=f; ev.append((f,'win',winner))
            elif min(big)<1:
                winner=0 if big[1]<1 else 1; endf=f; ev.append((f,'win',winner))
            elif not ch and not fly:
                winner=0 if big[0]>big[1] else 1; endf=f; ev.append((f,'win',winner))
        if record:
            frames.append(dict(cars={l:list(v) for l,v in cars.items()},ch=[(c.side,c.x,c.row,c.hop,c.v,c.mult) for c in ch],fly=[list(x) for x in fly],big=list(big)))
        lead.append(0 if big[0]>big[1] else 1)
        f+=1
        if endf is not None and f>endf: break
    lc=sum(1 for i in range(1,len(lead)) if lead[i]!=lead[i-1])
    m100=sum(1 for e in ev if e[1]=='mult' and e[3]==100)
    return dict(frames=frames,ev=ev,win=winner,n=f,big=big,lc=lc,m100=m100)
if __name__=='__main__':
    import collections
    out=[]
    for sd in range(150):
        r=simulate(sd)
        out.append((r['lc'],sd,r['n'],r['win'],[int(b) for b in r['big']],r['m100']))
    print(collections.Counter(o[3] for o in out), sum(o[2] for o in out)/len(out))
    out=[o for o in out if 750<=o[2]<=1200]; out.sort(reverse=True); print(out[:12])
