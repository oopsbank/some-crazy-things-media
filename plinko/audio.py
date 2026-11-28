import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100
tot=(m['intro']+m['n']+m['end'])/30; N=int(SR*tot)+SR
out=np.zeros(N); rng=np.random.default_rng(2)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt)
    if sq: s=np.sign(s)*.5
    return s*env(n,dec)
def kick():
    n=int(SR*.25); tt=np.arange(n)/SR; fr=55*(1+2*np.exp(-tt*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,14)
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
t=m['intro']/30; beat=0.3; end=(m['intro']+m['n'])/30
while t<end:
    prog=(t*30-m['intro'])/m['n']; add(kick(),t,.4); add(noise(.06,60),t+beat/2,.12+.1*prog); t+=beat*(1-0.25*prog)
add(tone(880,.6,4)+tone(1320,.6,4)*.5,.05,.4)
last={}
for e in m['ev']:
    ts=(e[0]+m['intro'])/30
    if e[1]=='goal':
        k=('g',e[2])
        if ts-last.get(k,-1)>.05: add(tone(660 if e[2]==0 else 990,.07,40),ts,.12); last[k]=ts
    elif e[1]=='clone':
        k=('c',e[2])
        if ts-last.get(k,-1)>.08: add(tone(1400,.06,40,True),ts,.06); last[k]=ts
    elif e[1]=='trap':
        k=('t',e[2])
        if ts-last.get(k,-1)>.1: add(noise(.15,25),ts,.15); last[k]=ts
add(noise(.5,8),end,.6); add(kick(),end,1)
for k,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.3+k*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
