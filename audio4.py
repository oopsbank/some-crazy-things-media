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
    elif k=='ink': add(sweep(500,180,.18,14),ts,.3); add(noise(.12,30),ts,.15)
    elif k=='inkhit': add(noise(.15,25),ts,.35); add(thud(260),ts,.3)
    elif k=='whip': add(noise(.18,18)*np.linspace(0,1,int(SR*.18))**2,ts,.5); add(sweep(400,2400,.12,20),ts+.1,.25)
    elif k=='whiphit': add(thud(120),ts,.8); add(noise(.1,40),ts,.6)
    elif k=='kraken': add(thud(40),ts,1.0); add(sweep(50,140,1.2,2),ts,.6)
    elif k=='erupt': add(thud(55),ts,.7); add(noise(.35,9),ts,.45)
    elif k=='krakhit': add(thud(80),ts,.9)
    elif k=='bubbles': [add(tone(f,.12,25),ts+j*.04,.18) for j,f in enumerate([700,950,1250])]
    elif k=='bubhit': add(tone(1500,.07,40),ts,.22); add(noise(.05,60),ts,.15)
    elif k=='mine': add(tone(300,.1,20),ts,.25); add(tone(450,.1,20),ts+.08,.2)
    elif k=='minehit': add(thud(60),ts,1.0); add(noise(.4,8),ts,.6)
    elif k=='blink': add(sweep(2000,400,.15,12),ts,.3); add(sweep(400,2000,.15,12),ts+.12,.3)
    elif k=='blinkhit': add(thud(110),ts,.8); add(noise(.08,45),ts,.4)
    elif k=='pearl': add(tone(1800,.15,15),ts,.2)
    elif k=='ping': add(tone(2400,.08,35),ts,.18); add(tone(3600,.06,45),ts,.1)
    elif k=='pearlhit': add(thud(140),ts,.8); add(tone(2000,.1,30),ts,.25)
    elif k=='burrow': add(noise(.5,5),ts,.35); add(thud(70),ts,.5)
    elif k=='popup': add(thud(50),ts,1.0); add(noise(.5,6),ts,.6)
    elif k=='boomer': add(noise(.4,6)*np.abs(np.sin(np.arange(int(SR*.4))/SR*2*np.pi*14)),ts,.4)
    elif k=='boomhit': add(thud(100),ts,.8); add(tone(2200,.06,50),ts,.3); add(tone(2600,.06,50),ts+.05,.3)
    elif k=='crush': add(sweep(200,900,.85,1.5),ts,.35)
    elif k=='land': add(thud(38),ts,1.0); add(thud(60),ts+.04,.9); add(noise(1.1,3),ts,.9)
    elif k=='bump': add(thud(160),ts,.4)
add(noise(.5,8),end,.8); add(thud(70),end,1)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.4+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
