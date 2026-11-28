"""Add the standard hook to a finished film (video+audio already muxed).
  python3 hook.py film.mp4 film_video.json out.mp4
Structure: [flash-forward of the ~1.4 s just before the final blow (winner not revealed) + "IT ENDED ON X HP!"] -> [fast rewind ~0.5 s] -> [fight from its first frame, no static intro,
"WHO WINS?" overlay for 1.6 s]. Frame numbers come from the render json (intro, n)."""
import sys, json, subprocess, os
from PIL import Image, ImageDraw, ImageFont
from pixelart import pixel_icon
SRC,META,OUT=sys.argv[1:4]
m=json.load(open(META)); FPS=30; W,H=1080,1920
fe=m['intro']+m['n']; he=fe-2; hs=max(m['intro'],he-42); ms=m['intro']   # stop BEFORE the final blow: no spoiler
whp=m.get('whp','?')
B='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
def f(s): return ImageFont.truetype(B,s)
def ctext(d,y,t,fn,fill,sw=8):
    w=d.textlength(t,font=fn); d.text(((W-w)/2,y),t,font=fn,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
tmp=os.path.splitext(OUT)[0]
# overlay 1: hook caption
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
ctext(d,1580,'IT ENDED ON',f(78),(255,220,60))
t2=f'{whp} HP!'; fn=f(150); w=d.textlength(t2,font=fn); x=(W-w-130)/2
d.text((x,1670),t2,font=fn,fill=(255,70,70),stroke_width=10,stroke_fill=(0,0,0))
e=pixel_icon('😱',120); im.alpha_composite(e,(int(x+w+10),1690))
im.save(tmp+'_o1.png')
# overlay 2: rewind label
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
for k in range(2):
    x0=330+k*70; d.polygon([(x0+60,1650),(x0+60,1750),(x0,1700)],fill=(255,255,255),outline=(0,0,0),width=5)
d.text((500,1645),'REWIND',font=f(96),fill=(255,255,255),stroke_width=8,stroke_fill=(0,0,0))
im.save(tmp+'_o2.png')
# overlay 3: who wins + pointing hand
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
t3='WHO WINS?'; fn=f(110); w=d.textlength(t3,font=fn); x=(W-w-120)/2
d.text((x,1640),t3,font=fn,fill=(255,255,255),stroke_width=9,stroke_fill=(0,0,0))
e=pixel_icon('👇',110); im.alpha_composite(e,(int(x+w+12),1645))
im.save(tmp+'_o3.png')
a,b=hs/FPS,he/FPS; mss=ms/FPS
fc=(f"[0:v]trim=start_frame={hs}:end_frame={he},setpts=PTS-STARTPTS[h0];[h0][1:v]overlay=0:0:shortest=1[vA];"
    f"[0:v]trim=start_frame={hs}:end_frame={he},setpts=PTS-STARTPTS,reverse,setpts=PTS/3,fps={FPS},hue=s=0.25,noise=alls=30:allf=t[r0];[r0][2:v]overlay=0:0:shortest=1[vB];"
    f"[0:v]trim=start_frame={ms},setpts=PTS-STARTPTS[m0];[m0][3:v]overlay=0:0:enable='lt(t,1.6)':eof_action=pass[vC];"
    f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[aA];"
    f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,areverse,atempo=2,atempo=1.5,volume=0.7[aB];"
    f"[0:a]atrim=start={mss},asetpts=PTS-STARTPTS[aC];"
    f"[vA][aA][vB][aB][vC][aC]concat=n=3:v=1:a=1[v][a]")
cmd=['ffmpeg','-y','-loglevel','error','-i',SRC,'-loop','1','-i',tmp+'_o1.png','-loop','1','-i',tmp+'_o2.png','-loop','1','-i',tmp+'_o3.png',
     '-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',OUT]
subprocess.run(cmd,check=True)
for k in (1,2,3): os.remove(f'{tmp}_o{k}.png')
print('hook ok',OUT)
