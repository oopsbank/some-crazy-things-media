import math, random
LW=470; LX=[45,565]; TOP=300; PR=10
GLASS_TOP=1430; GLASS_BOT=1860; CAP=300
TILES=[(1,110),(2,95),(3,80),(5,60),(10,40)]
PERIOD=sum(w for _,w in TILES); CONV=2.2
GATE_Y=860; TRAP=(250,420,1150)
def pegs():
    P=[]
    for row in range(4):
        y=400+row*60; off=0 if row%2==0 else 47
        for k in range(6):
            x=40+off+k*94
            if 15<x<LW-15: P.append((x,y,10))
    for row in range(3):
        y=1230+row*58; off=47 if row%2==0 else 0
        for k in range(6):
            x=40+off+k*94
            if 15<x<LW-15: P.append((x,y,10))
    return P
PEGS=pegs(); BAR=(LW/2,700,150)
def mirror(x,s): return x if s==0 else LW-x
def tile_at(x,f,s):
    u=(mirror(x,s)+f*CONV)%PERIOD; acc=0
    for m,w in TILES:
        if acc<=u<acc+w: return m
        acc+=w
    return 1
class D: __slots__=('x','y','vx','vy','g','alive')
def glass_x(y):  # half-width at y (relative to lane center)
    t=(y-GLASS_TOP)/(GLASS_BOT-GLASS_TOP); return 200-50*t
def simulate(seed, record=False):
    rnd=random.Random(seed); hitp=[]; ds=[[],[]]; lvl=[0,0]; ev=[]; frames=[]; win=None; f=0; ang=0; lead=[]
    while f<2000:
        ang+=0.05
        for s in (0,1):
            if f%4==0 and win is None:
                d=D(); d.x=LW/2+rnd.uniform(-80,80); d.y=TOP; d.vx=rnd.uniform(-1.5,1.5); d.vy=0; d.g=False; d.alive=True; ds[s].append(d)
            new=[]
            for d in ds[s]:
                d.vy+=0.38; d.vx*=0.995
                sp=math.hypot(d.vx,d.vy)
                if sp>11: d.vx*=11/sp; d.vy*=11/sp
                oy=d.y; d.x+=d.vx; d.y+=d.vy
                if d.y<GLASS_TOP-10:
                    if d.x<PR: d.x=PR; d.vx=abs(d.vx)*.7
                    if d.x>LW-PR: d.x=LW-PR; d.vx=-abs(d.vx)*.7
                for (px,py,pr) in PEGS:
                    px=mirror(px,s); dx,dy=d.x-px,d.y-py; dd=math.hypot(dx,dy)
                    if 0<dd<pr+PR:
                        if record: hitp.append((s,px,py))
                        nx,ny=dx/dd,dy/dd; d.x=px+nx*(pr+PR); d.y=py+ny*(pr+PR); vn=d.vx*nx+d.vy*ny
                        if vn<0: d.vx-=1.6*vn*nx; d.vy-=1.6*vn*ny; d.vx+=rnd.uniform(-.4,.4)
                bx,by,bl=BAR; a=ang if s==0 else -ang; ux,uy=math.cos(a),math.sin(a)
                tp=max(-bl,min(bl,(d.x-bx)*ux+(d.y-by)*uy)); cx,cy=bx+ux*tp,by+uy*tp; dx,dy=d.x-cx,d.y-cy; dd=math.hypot(dx,dy)
                if 0<dd<PR+6:
                    nx,ny=dx/dd,dy/dd; d.x=cx+nx*(PR+6); d.y=cy+ny*(PR+6)
                    w=0.05 if s==0 else -0.05; svx,svy=-w*(cy-by),w*(cx-bx); vn=(d.vx-svx)*nx+(d.vy-svy)*ny
                    if vn<0: d.vx-=1.5*vn*nx; d.vy-=1.5*vn*ny
                if oy<GATE_Y<=d.y and not d.g:
                    d.g=True; m=tile_at(d.x,f,s)
                    if m>1:
                        ev.append((f,'mult',s,m,d.x))
                        for k in range(m-1):
                            q=D(); q.x=d.x+rnd.uniform(-14,14); q.y=d.y+rnd.uniform(-6,6); q.vx=rnd.uniform(-4,4); q.vy=d.vy*rnd.uniform(.6,1); q.g=True; q.alive=True; new.append(q)
                tx0,tx1,ty=TRAP
                if s==1: tx0,tx1=LW-tx1,LW-tx0
                if oy<ty<=d.y and tx0<d.x<tx1: d.alive=False; ev.append((f,'trap',s,d.x)); continue
                surf=GLASS_BOT-(GLASS_BOT-GLASS_TOP)*min(lvl[s],CAP)/CAP
                if d.y>=surf-4:
                    d.alive=False
                    if win is None:
                        lvl[s]+=1; ev.append((f,'drop',s,d.x))
                        if lvl[s]>=CAP: win=s; ev.append((f,'win',s)); endf=f
            ds[s]=[d for d in ds[s] if d.alive]+new
        if record: frames.append(dict(ang=ang,lvl=tuple(lvl),ds=[[(d.x,d.y,d.vx,d.vy) for d in ds[s]] for s in (0,1)],hp=hitp)); hitp=[]
        lead.append(0 if lvl[0]>lvl[1] else (1 if lvl[1]>lvl[0] else -1))
        f+=1
        if win is not None: break
    lc=0; last=-1
    for l in lead:
        if l>=0 and last>=0 and l!=last: lc+=1
        if l>=0: last=l
    return dict(frames=frames,ev=ev,win=win,lvl=lvl,n=f,lc=lc)
if __name__=='__main__':
    out=[]
    for sd in range(120):
        r=simulate(sd)
        if r['win'] is None: continue
        out.append((r['lvl'][1-r['win']]/CAP>=.9, r['lc'], sd, r['n'], r['win'], r['lvl']))
    import statistics; print(len(out), statistics.mean(o[3] for o in out))
    out.sort(reverse=True); print(out[:10])
