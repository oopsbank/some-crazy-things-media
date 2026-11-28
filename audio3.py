import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100
N=int(SR*(m['intro']+m['n']+m['end'])/30)+SR; out=np.zeros(N); rng=np.random.default_rng(3)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt); s=np.sign(s)*.5 if sq else s; return s*env(n,dec)
def sweep(f0,f1,dur,dec):
    n=int(SR*dur); fr=np.linspace(f0,f1,n); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,dec)
def thud(f):
    n=int(SR*.25); tt=np.arange(n)/SR; fr=f*(1+2*np.exp(-tt*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,14)+rng.normal(0,1,n)*env(n,60)*.4
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
end=(m['intro']+m['n'])/30; t=m['intro']/30
while t<end: add(thud(55),t,.3); add(noise(.05,70),t+.165,.1); t+=.33
add(tone(880,.6,4)+tone(1320,.6,4)*.5,.05,.4)
last={}
for e in m['ev']:
    ts=(e[0]+m['intro'])/30; k=e[1] if e[1]!='cast' else e[2]
    if ts-last.get(k,-1)<.06: continue
    last[k]=ts
    if k=='shell': add(thud(140),ts,.4); add(tone(660,.25,10),ts,.2)
    elif k=='bite': add(sweep(150,500,.3,6),ts,.45)
    elif k=='spray': add(noise(.3,10),ts,.3); add(sweep(1200,500,.2,12),ts,.15)
    elif k=='cloud': add(noise(.6,4),ts,.25); add(sweep(200,90,.5,5),ts,.3)
    elif k=='bitehit': add(thud(90),ts,1.0); add(noise(.15,25),ts,.45)
    elif k=='sprayhit': add(noise(.1,35),ts,.3); add(tone(350,.08,35),ts,.2)
    elif k=='block': add(tone(1500,.15,25),ts,.25); add(tone(2250,.12,30),ts,.12)
    elif k=='bump': add(thud(160),ts,.4)
add(noise(.5,8),end,.8); add(thud(70),end,1)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.4+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
