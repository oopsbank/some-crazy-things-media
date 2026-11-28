import math, random
N=40; CS=24; AX=60; AY=470
TOTAL=N*N; TARGET=int(TOTAL*0.62); TL=900
SK_CD=[150,150]
SNOW=80
class Ball: __slots__=('t','x','y','vx','vy','life')
def simulate(seed, record=False):
    rnd=random.Random(seed)
    g=[[0 if i<N//2 else 1 for j in range(N)] for i in range(N)]  # g[x][y]
    cnt=[TOTAL//2,TOTAL//2]; balls=[]; items=[]; ev=[]; frames=[]
    def addball(t,x,y,life=-1):
        b=Ball(); b.t=t; b.x,b.y=x,y; a=rnd.uniform(0,6.28); b.vx,b.vy=math.cos(a),math.sin(a); b.life=life; balls.append(b)
    for t in (0,1):
        for k in range(3): addball(t,(N*CS*.25 if t==0 else N*CS*.75)+rnd.uniform(-80,80),N*CS*(k+1)/4)
    speed=[1.0,1.0]; boost=[0,0]; cd=[rnd.uniform(70,110),rnd.uniform(70,110)]; last=[False,False]
    win=None; f=0; lead=[]
    def setc(i,j,t,conv):
        if 0<=i<N and 0<=j<N and g[i][j]!=t: g[i][j]=t; cnt[t]+=1; cnt[1-t]-=1; conv.append((i,j,t))
    def blast(ci,cj,rad,t,conv):
        for i in range(ci-rad,ci+rad+1):
            for j in range(cj-rad,cj+rad+1):
                if (i-ci)**2+(j-cj)**2<=rad*rad: setc(i,j,t,conv)
    while f<TL:
        conv=[]; shake=0
        # items
        if f%50==25:
            kind=rnd.choice(['star','star','bomb','bolt'])
            items.append([kind,rnd.uniform(40,N*CS-40),rnd.uniform(40,N*CS-40),f]); ev.append((f,'item',kind))
        # skills
        for t in (0,1):
            cd[t]-=1
            mb=[b for b in balls if b.t==t]
            if cd[t]<=0 and mb:
                cd[t]=SK_CD[t]; b=rnd.choice(mb); ev.append((f,'cast',t,b.x,b.y))
                if t==0:   # METEOR: 4 small blasts on random enemy border cells
                    border=[(i,j) for i in range(N) for j in range(N) if g[i][j]==1 and any(0<=i+di<N and g[i+di][j]==0 for di in(-1,1))]
                    for k in range(4):
                        if border: ci,cj=rnd.choice(border); blast(ci,cj,3,0,conv); ev.append((f,'meteor',ci,cj))
                else:      # TSUNAMI: sweep a 5-row band leftward 14 cells from the front
                    j0=int(b.y//CS)
                    for j in range(j0-2,j0+3):
                        if 0<=j<N:
                            front=max([i for i in range(N) if g[i][j]==1] or [N-1])
                            fr=min([i for i in range(N) if g[i][j]==1] or [N])
                            for i in range(fr-14,fr): setc(i,j,1,conv)
                    ev.append((f,'wave',j0))
                shake=8
            if not last[t] and cnt[t]<TOTAL*0.40 and mb:
                last[t]=True; ev.append((f,'last',t))
                for k in range(8): b=rnd.choice(mb); addball(t,b.x,b.y,-1)
                shake=14
        # move
        for b in balls:
            sp=7.0*(1.8 if boost[b.t]>0 else 1)
            for sub in range(3):
                st=sp/3
                for axis in (0,1):
                    if axis==0:
                        nx=b.x+b.vx*st
                        if nx<10 or nx>N*CS-10: b.vx=-b.vx; continue
                        i,j=int((nx+(8 if b.vx>0 else -8))//CS),int(b.y//CS)
                        if g[i][j]!=b.t: setc(i,j,b.t,conv); b.vx=-b.vx; continue
                        b.x=nx
                    else:
                        ny=b.y+b.vy*st
                        if ny<10 or ny>N*CS-10: b.vy=-b.vy; continue
                        i,j=int(b.x//CS),int((ny+(8 if b.vy>0 else -8))//CS)
                        if g[i][j]!=b.t: setc(i,j,b.t,conv); b.vy=-b.vy; continue
                        b.y=ny
                i,j=int(b.x//CS),int(b.y//CS)
                if g[i][j]!=b.t: setc(i,j,b.t,conv)
            a=math.atan2(b.vy,b.vx)+rnd.uniform(-.03,.03); b.vx,b.vy=math.cos(a),math.sin(a)
            for it in items:
                if it[0] and math.hypot(it[1]-b.x,it[2]-b.y)<30:
                    kind=it[0]; it[0]=None; ev.append((f,'pick',b.t,kind,it[1],it[2]))
                    if kind=='star':
                        for k in range(3): addball(b.t,b.x,b.y)
                    elif kind=='bomb': blast(int(it[1]//CS),int(it[2]//CS),6,b.t,conv); shake=10
                    else: boost[b.t]=100
        items=[it for it in items if it[0] and f-it[3]<240]
        for t in (0,1): boost[t]=max(0,boost[t]-1)
        # army size follows territory (snowball)
        if f%12==0:
            for t in (0,1):
                mb=[b for b in balls if b.t==t]; tgt=int(round((cnt[t]/TOTAL)**2*SNOW))+(6 if last[t] else 0)
                if len(mb)<tgt and mb: b=rnd.choice(mb); addball(t,b.x,b.y); ev.append((f,'spawn',t))
                elif len(mb)>max(tgt,2): balls.remove(mb[0])
        if record: frames.append(dict(conv=conv,balls=[(b.t,b.x,b.y) for b in balls],items=[(it[0],it[1],it[2]) for it in items],cnt=list(cnt),cd=list(cd),boost=list(boost),shake=shake))
        lead.append(0 if cnt[0]>cnt[1] else 1)
        f+=1
        if max(cnt)>=TARGET: win=0 if cnt[0]>cnt[1] else 1; break
    if win is None: win=0 if cnt[0]>cnt[1] else 1
    lc=sum(1 for k in range(1,len(lead)) if lead[k]!=lead[k-1])
    return dict(frames=frames,ev=ev,win=win,cnt=cnt,n=f,lc=lc,ko=max(cnt)>=TARGET)
if __name__=='__main__':
    import collections
    rs=[]
    for sd in range(150):
        r=simulate(sd); rs.append((r['ko'],r['lc'],sd,r['n'],r['win'],r['cnt']))
    print(collections.Counter(x[4] for x in rs), sum(x[0] for x in rs), sum(x[3] for x in rs)/len(rs))
    k=[x for x in rs if x[0] and 600<=x[3]]; k.sort(key=lambda x:-x[1]); print(k[:10])
