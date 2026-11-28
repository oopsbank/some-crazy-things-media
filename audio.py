import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100
N_=int(SR*(m['n']+m['end'])/30)+SR; out=np.zeros(N_); rng=np.random.default_rng(9)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N_,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt); s=np.sign(s)*.5 if sq else s; return s*env(n,dec)
def sweep(f0,f1,dur,dec): n=int(SR*dur); fr=np.linspace(f0,f1,n); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,dec)
def kick(): n=int(SR*.25); tt=np.arange(n)/SR; fr=55*(1+2*np.exp(-tt*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,14)
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
end=m['n']/30; t=0.0
while t<end:
    p=t/end; add(kick(),t,.35); add(noise(.05,70),t+.15,.1); t+=.34*(1-.3*p)
for k,c in enumerate(m['conv']):
    if c>0 and k%2==0: add(tone(900+min(c,20)*30,.03,90),k/30,.05)
for e in m['ev']:
    ts=e[0]/30
    if e[1]=='cast':
        tm=e[2]
        if tm==0: add(noise(.5,6),ts,.6); add(kick(),ts,.8)
        elif tm==1: [add(sweep(400,1200,.15,15),ts+j*.06,.25) for j in range(3)]
        elif tm==2: [add(tone(f,.25,8),ts+j*.05,.2) for j,f in enumerate([660,880,1100,1320])]
        else: add(noise(.3,10)*np.sign(np.sin(np.arange(int(SR*.3))/SR*2*np.pi*60)),ts,.5)
    if e[1]=='elim': add(sweep(600,100,.6,4),ts,.5)
for s in range(5,0,-1): add(tone(1000,.12,20,True),end-s,.3)
add(noise(1,4),end,.5)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.3+j*.12,.3)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
