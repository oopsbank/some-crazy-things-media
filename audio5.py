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
    if k=='ultcharge': add(sweep(200,1600,.53,1.5),ts,.35); add(noise(.53,1.5)*np.linspace(0,1,int(SR*.53)),ts,.25)
    elif k=='dig': add(noise(.5,5),ts,.35); add(thud(70),ts,.5); add(noise(.08,40),ts+.12,.3)
    elif k=='popup': add(thud(50),ts,1.0); add(noise(.5,6),ts,.6)
    elif k=='bury': add(sweep(300,120,.4,6),ts,.4)
    elif k=='buryhit': add(thud(45),ts,1.0); add(noise(.7,4),ts,.6); [add(thud(80),ts+.15+j*.1,.4) for j in range(3)]
    elif k=='splat': add(noise(.2,15),ts,.3)
    elif k=='unbury': add(noise(.3,8),ts,.3)
    elif k=='whirl': add(noise(1.3,1.2)*(0.6+0.4*np.sin(np.arange(int(SR*1.3))/SR*2*np.pi*9)),ts,.35)
    elif k=='whirlhit': add(tone(1900,.05,50),ts,.18); add(noise(.04,60),ts,.15)
    elif k=='timber': [add(noise(.06,40),ts+j*.09,.35) for j in range(5)]; add(sweep(900,300,.9,2),ts+.2,.2)
    elif k=='crash': add(thud(35),ts,1.0); add(thud(55),ts+.05,.9); add(noise(1.2,2.5),ts,1.0)
    elif k=='bump': add(thud(160),ts,.4)
add(noise(.5,8),end,.8); add(thud(70),end,1)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.4+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
