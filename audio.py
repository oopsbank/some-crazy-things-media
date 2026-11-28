import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100
N=int(SR*(m['intro']+m['n']+m['end'])/30)+SR; out=np.zeros(N); rng=np.random.default_rng(5)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt); s=np.sign(s)*.5 if sq else s; return s*env(n,dec)
def sweep(f0,f1,dur,dec): n=int(SR*dur); fr=np.linspace(f0,f1,n); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,dec)
def kick(): n=int(SR*.25); tt=np.arange(n)/SR; fr=55*(1+2*np.exp(-tt*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,14)
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
end=(m['intro']+m['n'])/30; t=m['intro']/30
while t<end: add(kick(),t,.35); add(noise(.05,70),t+.16,.1); t+=.32
add(tone(880,.6,4)+tone(1320,.6,4)*.5,.05,.4)
# traffic hum
n=len(out); out+=np.convolve(rng.normal(0,1,n),np.ones(200)/200,'same')*.25
last={}
for e in m['ev']:
    ts=(e[0]+m['intro'])/30; k=e[1]
    if k=='splat':
        if ts-last.get(k,-1)>.12: add(noise(.12,30),ts,.25 if e[2]==0 else .2); add(tone(200 if e[2]==0 else 700,.08,40),ts,.15); last[k]=ts
    elif k=='mult' and e[3]>=3:
        g={3:.15,5:.2,20:.35,100:.5}[e[3]]; f0={3:700,5:900,20:1200,100:1500}[e[3]]
        for j in range(1 if e[3]<20 else 3): add(tone(f0*(1+j*.25),.15,15,True),ts+j*.07,g)
    elif k=='spawn':
        for j in range(2): add(tone((1000 if e[2]==0 else 1250)*(1+j*.25),.12,18,True),ts+j*.07,.18)
    elif k=='skill': add(sweep(150,1600,.9,2),ts,.6); add(noise(1.0,3),ts,.35)
    elif k=='zap': add(noise(.2,15),ts,.2)
    elif k=='fizzle': add(noise(.25,12),ts,.18)
    elif k in ('feed','eat'):
        if e[3]>=1000: add(sweep(200,900,.4,5),ts,.5); add(kick(),ts,.6)
        elif ts-last.get(k,-1)>.07: add(tone(500 if e[2]==0 else 800,.06,40),ts,.12); last[k]=ts
add(noise(1.2,3),end,.7); add(sweep(800,200,.8,3),end,.4)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.6+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
