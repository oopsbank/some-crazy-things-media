import json, numpy as np, wave, sys
m=json.load(open(sys.argv[1])); SR=44100; CAP=m['cap']
N=int(SR*(m['intro']+m['n']+m['end'])/30)+SR; out=np.zeros(N); rng=np.random.default_rng(7)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,dec): return np.exp(-np.arange(n)/SR*dec)
def tone(f,dur,dec,sq=False):
    n=int(SR*dur); tt=np.arange(n)/SR; s=np.sin(2*np.pi*f*tt); s=np.sign(s)*.5 if sq else s; return s*env(n,dec)
def kick(): n=int(SR*.25); tt=np.arange(n)/SR; fr=55*(1+2*np.exp(-tt*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*env(n,14)
def noise(d,dec): n=int(SR*d); return rng.normal(0,1,n)*env(n,dec)
end=(m['intro']+m['n'])/30; t=m['intro']/30
while t<end:
    p=(t*30-m['intro'])/m['n']; add(kick(),t,.35); add(noise(.05,70),t+.15,.1+.1*p); t+=.32*(1-.3*p)
add(tone(880,.6,4)+tone(1320,.6,4)*.5,.05,.4)
lv=[0,0]; last={}
for e in m['ev']:
    ts=(e[0]+m['intro'])/30
    if e[1]=='drop':
        s=e[2]; lv[s]+=1
        if ts-last.get(s,-1)>.045:
            f=(300 if s==0 else 360)*2**(1.5*lv[s]/CAP); add(tone(f,.06,45),ts,.11); last[s]=ts
    elif e[1]=='mult' and e[3]>=5:
        for j in range(1 if e[3]<10 else 3): add(tone(1200*(1+j*.25),.12,18,True),ts+j*.06,.12 if e[3]<10 else .2)
    elif e[1]=='trap' and ts-last.get('t',-1)>.15: add(noise(.08,40),ts,.08); last['t']=ts
n=int(SR*1.5); add(np.convolve(rng.normal(0,1,n),np.ones(30)/30,'same')*env(n,2)*3,end,.6); add(kick(),end,1)
for j,f in enumerate([523,659,784,1047]): add(tone(f,.5,3,True),end+.5+j*.12,.25)
out/=np.abs(out).max()/0.85
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
