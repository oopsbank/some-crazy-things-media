import math, random
N=48; CS=20; AX=60; AY=440
TEAMS=['fire','water','leaf','bolt']
CD={'fire':110,'water':130,'leaf':170,'bolt':100}
TARGET=int(N*N*0.4)
class Ball: __slots__=('t','x','y','vx','vy','life')
def simulate(seed, record=False, maxf=1200):
    rnd=random.Random(seed)
    g=[[0]*N for _ in range(N)]
    for i in range(N):
        for j in range(N): g[i][j]=(0 if i<N//2 else 1) if j<N//2 else (2 if i<N//2 else 3)  # g[x][y]
    starts=[(N*CS*.25,N*CS*.25),(N*CS*.75,N*CS*.25),(N*CS*.25,N*CS*.75),(N*CS*.75,N*CS*.75)]
    balls=[]
    for t in range(4):
        b=Ball(); b.t=t; b.x,b.y=starts[t]; a=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(a),math.sin(a); b.life=-1; balls.append(b)
    cd=[CD[TEAMS[t]]*rnd.uniform(.5,.8) for t in range(4)]
    cnt=[N*N//4]*4; alive=[True]*4; ev=[]; frames=[]; win=None; f=0; lead=[]
    SPEED=7.5; R=8
    def setc(i,j,t):
        o=g[i][j]
        if o!=t: g[i][j]=t; cnt[o]-=1; cnt[t]+=1; return True
        return False
    while f<maxf:
        conv=[]
        # skills
        for t in range(4):
            if not alive[t]: continue
            cd[t]-=1
            if cd[t]<=0:
                cd[t]=CD[TEAMS[t]]; mb=[b for b in balls if b.t==t]
                if not mb: continue
                b=mb[0]; ci,cj=int(b.x//CS),int(b.y//CS); ev.append((f,'cast',t,b.x,b.y))
                if t==0:
                    for i in range(ci-6,ci+7):
                        for j in range(cj-6,cj+7):
                            if 0<=i<N and 0<=j<N and (i-ci)**2+(j-cj)**2<=36 and setc(i,j,0): conv.append((i,j))
                elif t==1:
                    for k in range(3):
                        c=Ball(); c.t=1; c.x,c.y=b.x,b.y; a=math.atan2(b.vy,b.vx)+(k-1)*1.1; c.vx,c.vy=math.cos(a),math.sin(a); c.life=260; balls.append(c)
                elif t==2:
                    fr=set()
                    for i in range(N):
                        for j in range(N):
                            if g[i][j]==2:
                                for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
                                    a2,b2=i+di,j+dj
                                    if 0<=a2<N and 0<=b2<N and g[a2][b2]!=2: fr.add((a2,b2))
                    fr=list(fr); rnd.shuffle(fr)
                    for (i,j) in fr[:28]:
                        if setc(i,j,2): conv.append((i,j))
                else:
                    a=math.atan2(b.vy,b.vx); line=[]
                    for k in range(1,31):
                        for w in (-1,0,1):
                            i=int((b.x+math.cos(a)*k*CS-math.sin(a)*w*CS)//CS); j=int((b.y+math.sin(a)*k*CS+math.cos(a)*w*CS)//CS)
                            if 0<=i<N and 0<=j<N and setc(i,j,3): conv.append((i,j))
                    ev.append((f,'boltline',b.x,b.y,a))
        # move
        for b in balls:
            sp=SPEED*(1.0)
            for sub in range(3):
                st=sp/3
                nx=b.x+b.vx*st
                if nx<R or nx>N*CS-R: b.vx=-b.vx; nx=b.x
                else:
                    ex=nx+(R if b.vx>0 else -R); i,j=int(ex//CS),int(b.y//CS)
                    if 0<=i<N and g[i][j]!=b.t:
                        if setc(i,j,b.t): conv.append((i,j))
                        b.vx=-b.vx; nx=b.x
                b.x=nx
                ny=b.y+b.vy*st
                if ny<R or ny>N*CS-R: b.vy=-b.vy; ny=b.y
                else:
                    ey=ny+(R if b.vy>0 else -R); i,j=int(b.x//CS),int(ey//CS)
                    if 0<=j<N and g[i][j]!=b.t:
                        if setc(i,j,b.t): conv.append((i,j))
                        b.vy=-b.vy; ny=b.y
                b.y=ny
                i,j=int(b.x//CS),int(b.y//CS)
                if g[i][j]!=b.t and setc(i,j,b.t): conv.append((i,j))
            a=math.atan2(b.vy,b.vx)+rnd.uniform(-.02,.02); b.vx,b.vy=math.cos(a),math.sin(a)
            if b.life>0: b.life-=1
        balls=[b for b in balls if b.life!=0 and alive[b.t]]
        for t in range(4):
            if alive[t] and cnt[t]<=0: alive[t]=False; ev.append((f,'elim',t)); balls=[b for b in balls if b.t!=t]
        if record:
            frames.append(dict(conv=[(i,j,g[i][j]) for (i,j) in conv],balls=[(b.t,b.x,b.y,b.life) for b in balls],cnt=list(cnt),cd=list(cd),alive=list(alive)))
        lead.append(max(range(4),key=lambda t:cnt[t]))
        f+=1
        if max(cnt)>=TARGET: win=max(range(4),key=lambda t:cnt[t]); ev.append((f-1,'win',win)); break
    if win is None: win=max(range(4),key=lambda t:cnt[t])
    lc=sum(1 for k in range(1,len(lead)) if lead[k]!=lead[k-1])
    return dict(frames=frames,ev=ev,win=win,cnt=cnt,n=f,lc=lc,elim=sum(1 for a in alive if not a))
if __name__=='__main__':
    import collections
    rs=[]
    for sd in range(60):
        r=simulate(sd); rs.append((r['lc'],sd,r['n'],r['win'],r['cnt'],r['elim']))
    print(collections.Counter(x[3] for x in rs), sum(x[2] for x in rs)/len(rs))
    rs=[x for x in rs if 800<=x[2]<1600]; rs.sort(reverse=True); print(rs[:12])
