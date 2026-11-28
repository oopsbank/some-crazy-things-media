import math, random
import shapes
W=1080
ROWS=[230,310,390,470,550,630,710,790,870,950]   # 0 spawn,1-2 road A,3-5 walk (split at 4),6-7 road B,8 walk,9 finish
LANES={1:(1,6.5),2:(-1,8.0),6:(-1,7.0),7:(1,8.5)}
CARW=150
MULTS=[(1,150),(2,130),(3,115),(5,95),(20,62),(100,50)]   # head multiplier weights
SPLIT_ROW=4
CX=[270,810]; BOT=1890; TOPWIN=190; AR=shapes.AR
START_N=5; BASE=50; SPAWN=2; DECAY=0.9975; GAP=(1300,2000); MAXN=40
K=5.5; FEED=0.05
def rad(v): return K*math.sqrt(max(v,0))+10
def box(s,v):
    rr=rad(v); w=2*rr; h=w*AR; return CX[s]-rr,BOT-h,w,h
def hit(s,v,x,y):
    x0,y0,w,h=box(s,v); M=shapes.mask(s); mh,mw=M.shape
    for dx,dy in ((0,0),(-22,0),(22,0),(0,-26),(0,26)):
        u=(x+dx-x0)/w; q=(y+dy-y0)/h
        if 0<=u<1 and 0<=q<1 and M[int(q*mh),int(u*mw)]: return True
    return False
class C: pass
def simulate(seed, record=False):
    rnd=random.Random(seed)
    cars={l:[] for l in LANES}
    for l,(d,sp) in LANES.items():
        x=rnd.uniform(0,300)
        while x<W+400: cars[l].append(x); x+=rnd.uniform(*GAP)
    ch=[]; fly=[]; big=[100.0,100.0]; pend=[0.0,0.0]; ev=[]; frames=[]; winner=None; f=0; endf=None; lead=[]
    tot=sum(w for _,w in MULTS)
    def pick():
        u=rnd.uniform(0,tot)
        for m,w in MULTS:
            if u<w: return m
            u-=w
        return 1
    def spawn(side,delay):
        c=C(); c.side=side; c.x=CX[side]+rnd.uniform(-170,170); c.x=min(max(c.x,40),W-40)
        c.row=0; c.hop=0; c.wait=delay; c.mult=pick(); c.v=BASE*c.mult; c.alive=True; c.split=False
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
                    if c.row==SPLIT_ROW and c.mult>1 and winner is None and not c.split:
                        c.split=True
                        if sum(1 for q in ch if q.side==c.side)<MAXN:
                            for k in range(SPAWN): spawn(c.side,rnd.randint(4,20)+k*8)
                            ev.append((f,'spawn',c.side,SPAWN,c.x))
                    if c.row==9:
                        c.alive=False; fly.append([c.side,c.x,ROWS[9],c.v,0]); continue
            elif c.wait>0: c.wait-=1
            else: c.hop=8
            y=ROWS[c.row]+(80*(8-c.hop)/8 if c.hop>0 else 0)
            # touching any pixel of a big one: own side is absorbed, enemy fizzles
            if winner is None:
                if hit(c.side,big[c.side],c.x,y):
                    c.alive=False; pend[c.side]+=c.v; ev.append((f,'eat',c.side,c.v,c.x,y)); continue
                if hit(1-c.side,big[1-c.side],c.x,y):
                    c.alive=False; ev.append((f,'fizzle',c.side,c.v,c.x,y)); continue
            for l in LANES:
                if abs(y-ROWS[l])<30:
                    for x in cars[l]:
                        if abs(c.x-x)<CARW/2+14:
                            c.alive=False; ev.append((f,'splat',c.side,c.x,y,c.v)); break
                if not c.alive: break
        ch=[c for c in ch if c.alive]
        for fl in fly:
            fl[4]+=1
            if fl[4]==14:
                if winner is None: pend[fl[0]]+=fl[3]; ev.append((f,'feed',fl[0],fl[3]))
        fly=[fl for fl in fly if fl[4]<14]
        if winner is None:
            for s in (0,1):
                tr=min(pend[s],max(25,pend[s]*FEED)); big[s]+=tr; pend[s]-=tr; big[s]*=DECAY
            tops=[box(s,big[s])[1] for s in (0,1)]
            if min(tops)<=TOPWIN:
                winner=0 if tops[0]<=tops[1] else 1; endf=f; ev.append((f,'win',winner))
            elif (not ch and not fly and max(pend)<1) or f==1799:
                winner=0 if big[0]>big[1] else 1; endf=f; ev.append((f,'win',winner))
        if record:
            frames.append(dict(cars={l:list(v) for l,v in cars.items()},ch=[(c.side,c.x,c.row,c.hop,c.v,c.mult) for c in ch],fly=[list(x) for x in fly],big=list(big)))
        lead.append(0 if big[0]>big[1] else 1)
        f+=1
        if endf is not None and f>endf: break
    lc=sum(1 for i in range(1,len(lead)) if lead[i]!=lead[i-1])
    touch=min(box(s,big[s])[1] for s in (0,1))<=TOPWIN
    eats=sum(1 for e in ev if e[1]=='eat')
    return dict(frames=frames,ev=ev,win=winner,n=f,big=big,lc=lc,touch=touch,eats=eats)
if __name__=='__main__':
    out=[]
    for sd in range(400):
        r=simulate(sd)
        if not r['touch'] or not (800<=r['n']<=1250): continue
        b=r['big']; out.append((r['lc'],sd,r['n'],r['win'],int(b[0]),int(b[1]),round(abs(b[0]-b[1])/max(b),3),r['eats']))
    out.sort(key=lambda o:(-o[0],o[6])); print(len(out)); [print(o) for o in out[:15]]
