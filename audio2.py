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
    if k=='burst': add(noise(.25,12),ts,.35); add(sweep(300,1200,.2,10),ts,.3)
    elif k=='roll': add(sweep(120,400,.5,4),ts,.4)
    elif k=='venom': add(sweep(900,300,.18,15),ts,.3)
    elif k=='shed': [add(tone(f,.3,8),ts+j*.06,.25) for j,f in enumerate([880,1175,1568])]
    elif k=='spikehit': add(thud(220),ts,.55)
    elif k=='rollhit': add(thud(90),ts,1.0); add(noise(.2,20),ts,.4)
    elif k=='venomhit': add(noise(.12,30),ts,.35); add(tone(300,.1,30),ts,.2)
    elif k=='bump': add(thud(160),ts,.4)
add(noise(.5,8),end,.8); add(thud(70),end,1)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.4+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
