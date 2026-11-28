import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100
N=int(SR*(m['n']+m['end'])/30)+SR; out=np.zeros(N); rng=np.random.default_rng(7)
def add(sig,t,g=1.0):
    i=int(t*SR)
    if i>=N: return
    j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt); s=np.sign(s)*.5 if sq else s; return s*env(n,dec)
def sweep(f0,f1,dur,dec): n=int(SR*dur); fr=np.linspace(f0,f1,n); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,dec)
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
def lp(x,k): return np.convolve(x,np.ones(k)/k,'same')
def boom(d=1.0,dec=4): n=int(SR*d); tt=np.arange(n)/SR; fr=45*(1+3*np.exp(-tt*12)); return (np.sin(2*np.pi*np.cumsum(fr)/SR)+lp(rng.normal(0,1,n),30)*0.8)*env(n,dec)
def whoosh(d=.25): return lp(noise(d,6),12)*np.sin(np.linspace(0,np.pi,int(SR*d)))
def zap(d=.3): n=int(SR*d); return np.sign(np.sin(2*np.pi*np.cumsum(rng.uniform(300,2400,n))/SR))*env(n,10)*0.4
def crack():
    z=zap(.6)*0.6; z[:int(SR*.12)]+=noise(.12,25); return z
# background drum loop
end=m['n']/30; t=0.0
while t<end:
    add(boom(.25,14),t,.25); add(noise(.04,80),t+.18,.08); t+=.36
for e in m['ev']:
    ts=e[0]/30; k=e[1]
    if k=='cast':
        add(sweep(400,900,.15,10),ts,.12)
        if e[3]==2: add(sweep(150,1400,1.0,2),ts,.35); add(boom(.8,3),ts,.25)
    elif k=='slash': add(whoosh(.18)*1.5,ts,.5); add(noise(.05,60),ts+.05,.2)
    elif k=='charge': add(whoosh(.4),ts,.6); add(sweep(120,60,.4,4),ts,.3)
    elif k=='charge_end': add(boom(.4,8),ts,.4)
    elif k=='meteor': add(boom(.9,4),ts,.6)
    elif k=='shards':
        for j in range(3): add(tone(1800+j*300,.12,25),ts+j*.03,.15)
    elif k=='shard_hit': add(tone(2600,.1,30),ts,.15); add(noise(.06,40),ts,.12)
    elif k=='shock': add(zap(.45),ts,.6); add(boom(.4,8),ts,.3)
    elif k=='thunder': add(crack(),ts,.8); add(boom(1.5,2.5),ts+.05,.7)
    elif k=='hit': add(noise(.08,40),ts,.25); add(tone(140,.12,25),ts,.35)
    elif k=='miss': add(whoosh(.15),ts,.3)
    elif k=='dash': add(whoosh(.2),ts,.45)
    elif k=='ko': add(boom(1.5,2.5),ts,.9); add(sweep(900,100,.8,3),ts,.3)
for (fr,k) in m['extra']:
    ts=fr/30
    if k=='fight': add(sweep(300,1200,.3,6),ts,.4); add(boom(.5,6),ts,.4)
    elif k=='final_cast': add(sweep(100,2000,2.0,1.2),ts,.4); add(lp(noise(2.0,1.0),40),ts,.6)
    elif k=='alarm':
        for j in range(4): add(tone(880,.18,6,True),ts+j*.4,.25); add(tone(660,.18,6,True),ts+j*.4+.2,.25)
    elif k=='meteor_fall': add(sweep(1500,200,.55,1.5),ts,.4); add(lp(noise(.55,1),20),ts,.5)
    elif k=='thunder': add(crack(),ts,.6)
    elif k=='mega_boom': add(boom(3.0,1.2),ts,1.0); add(lp(noise(3.0,1.0),60),ts,.8); add(sweep(400,40,2.0,1.5),ts,.5)
    elif k=='win':
        for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),ts+j*.13,.3)
out/=np.abs(out).max()/0.9
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
