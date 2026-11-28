import math, random
LW=470; LX=[45,565]      # lane left x
TOP=330; BOT=1500; GOAL_Y=1520; TARGET=100
PR=11
def lane_layout():
    pegs=[]
    for row in range(5):
        y=420+row*62; off=0 if row%2==0 else 47
        for k in range(6):
            x=40+off+k*94
            if 15<x<LW-15: pegs.append((x,y,10))
    for row in range(3):
        y=1290+row*62; off=47 if row%2==0 else 0
        for k in range(6):
            x=40+off+k*94
            if 15<x<LW-15: pegs.append((x,y,10))
    return dict(pegs=pegs, bar=(LW/2,800,150), gate=(30,250,975), trap=(270,440,1150))
LAY=lane_layout()
def mirror(x,side): return x if side==0 else LW-x
class P:
    __slots__=('x','y','vx','vy','cl','alive','born')
def simulate(seed, record=False):
    rnd=random.Random(seed)
    ps=[[],[]]; cnt=[0,0]; frames=[]; ev=[]
    f=0; ang=0.0; winner=None; finish=None
    while f<2400:
        ang+=0.045
        for side in (0,1):
            if f%5==0 and winner is None:
                p=P(); p.x=LW/2+rnd.uniform(-60,60); p.y=TOP; p.vx=rnd.uniform(-1.5,1.5); p.vy=0; p.cl=False; p.alive=True; p.born=f
                ps[side].append(p)
            new=[]
            for p in ps[side]:
                if not p.alive: continue
                p.vy+=0.38; p.vx*=0.995
                sp=math.hypot(p.vx,p.vy)
                if sp>11: p.vx*=11/sp; p.vy*=11/sp
                ox,oy=p.x,p.y
                p.x+=p.vx; p.y+=p.vy
                if p.x<PR: p.x=PR; p.vx=abs(p.vx)*.7
                if p.x>LW-PR: p.x=LW-PR; p.vx=-abs(p.vx)*.7
                for (px,py,pr) in LAY['pegs']:
                    px=mirror(px,side); dx,dy=p.x-px,p.y-py; d=math.hypot(dx,dy)
                    if d<pr+PR and d>0:
                        nx,ny=dx/d,dy/d; p.x=px+nx*(pr+PR); p.y=py+ny*(pr+PR)
                        vn=p.vx*nx+p.vy*ny
                        if vn<0: p.vx-=1.6*vn*nx; p.vy-=1.6*vn*ny; p.vx+=rnd.uniform(-.4,.4)
                # rotating bar
                bx,by,bl=LAY['bar']; a=ang if side==0 else -ang
                ux,uy=math.cos(a),math.sin(a); rx,ry=p.x-bx,p.y-by
                tproj=max(-bl,min(bl,rx*ux+ry*uy)); cx,cy=bx+ux*tproj,by+uy*tproj
                dx,dy=p.x-cx,p.y-cy; d=math.hypot(dx,dy)
                if d<PR+6 and d>0:
                    nx,ny=dx/d,dy/d; p.x=cx+nx*(PR+6); p.y=cy+ny*(PR+6)
                    # surface velocity of bar
                    w=0.045 if side==0 else -0.045; svx,svy=-w*(cy-by),w*(cx-bx)
                    rvx,rvy=p.vx-svx,p.vy-svy; vn=rvx*nx+rvy*ny
                    if vn<0: p.vx-=1.5*vn*nx; p.vy-=1.5*vn*ny
                # gate x2
                gx0,gx1,gy=LAY['gate']
                if side==1: gx0,gx1=LW-gx1,LW-gx0
                if oy<gy<=p.y and gx0<p.x<gx1 and not p.cl:
                    p.cl=True; q=P(); q.x=p.x+8; q.y=p.y; q.vx=-p.vx+rnd.uniform(-1,1); q.vy=p.vy; q.cl=True; q.alive=True; q.born=f
                    new.append(q); ev.append((f,'clone',side))
                tx0,tx1,ty=LAY['trap']
                if side==1: tx0,tx1=LW-tx1,LW-tx0
                if oy<ty<=p.y and tx0<p.x<tx1:
                    p.alive=False; ev.append((f,'trap',side,p.x,p.y)); continue
                if p.y>=GOAL_Y:
                    p.alive=False
                    if winner is None:
                        cnt[side]+=1; ev.append((f,'goal',side))
                        if cnt[side]>=TARGET: winner=side; finish=f; ev.append((f,'win',side))
            ps[side]=[p for p in ps[side] if p.alive]+new
        if record:
            frames.append(dict(ang=ang,cnt=tuple(cnt),ps=[[(p.x,p.y) for p in ps[s]] for s in (0,1)]))
        f+=1
        if winner is not None and f>finish+1: break
    return dict(frames=frames,ev=ev,win=winner,cnt=cnt,n=f)
if __name__=='__main__':
    out=[]
    for sd in range(120):
        r=simulate(sd)
        if r['win'] is None: continue
        lo=r['cnt'][1-r['win']]
        out.append((lo,sd,r['n'],r['win'],r['cnt']))
    out.sort(reverse=True); print(out[:10])
