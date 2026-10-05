import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os,sys; OUT=(sys.argv[1] if len(sys.argv)>1 else '.').rstrip('/')+'/'; os.makedirs(OUT+'assets',exist_ok=True); os.makedirs(OUT+'store',exist_ok=True)
LORA=next((p for p in ['/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf','/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'] if os.path.exists(p)), None)
def font(sz, w=700):
    if not LORA: return ImageFont.load_default()
    f=ImageFont.truetype(LORA, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def hexc(h,a=255): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))+(a,)
def grad(w,h,top,bot):
    im=Image.new('RGBA',(w,h)); d=ImageDraw.Draw(im); t=hexc(top); b=hexc(bot)
    for y in range(h):
        k=y/(h-1); d.line([(0,y),(w,y)], fill=tuple(int(t[i]+(b[i]-t[i])*k) for i in range(3))+(255,))
    return im
def hill(d,w,h,base,amp,phase,col,freq=1.0):
    pts=[(0,h)]
    for x in range(0,w+1,max(1,w//200)):
        y=base+amp*math.sin(x/w*math.pi*2*freq+phase)+amp*.35*math.sin(x/w*math.pi*5.3*freq+phase*2)
        pts.append((x,y))
    pts.append((w,h)); d.polygon(pts, fill=col)
def sun(im,cx,cy,r):
    glow=Image.new('RGBA',im.size,(0,0,0,0)); g=ImageDraw.Draw(glow)
    g.ellipse([cx-r*2.2,cy-r*2.2,cx+r*2.2,cy+r*2.2], fill=(255,236,170,120)); glow=glow.filter(ImageFilter.GaussianBlur(r*.6))
    im.alpha_composite(glow); d=ImageDraw.Draw(im); d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=hexc('#f6c84c'))
    d.ellipse([cx-r*.78,cy-r*.85,cx+r*.55,cy+r*.45], fill=hexc('#f9d870'))
def flower(d,cx,cy,r,petal='#e8684a',petal2='#f08a6c',center='#f4c34a',n=7,rot=0):
    for k in range(n):
        a=rot+k/n*math.tau; px=cx+math.cos(a)*r*.62; py=cy+math.sin(a)*r*.62; pr=r*.46
        d.ellipse([px-pr,py-pr,px+pr,py+pr], fill=hexc(petal))
    for k in range(n):
        a=rot+(k+.5)/n*math.tau; px=cx+math.cos(a)*r*.45; py=cy+math.sin(a)*r*.45; pr=r*.3
        d.ellipse([px-pr,py-pr,px+pr,py+pr], fill=hexc(petal2))
    cr=r*.36; d.ellipse([cx-cr,cy-cr,cx+cr,cy+cr], fill=hexc(center)); d.ellipse([cx-cr*.55,cy-cr*.7,cx+cr*.2,cy-cr*.05], fill=hexc('#f9dc84'))
def leaf(d,x,y,lx,ly,wid,col):
    pts=[]; n=24
    for i in range(n+1):
        t=i/n; px=x+lx*t; py=y+ly*t; s=math.sin(t*math.pi)*wid; nx,ny=-ly,lx; L=math.hypot(nx,ny); pts.append((px+nx/L*s,py+ny/L*s))
    for i in range(n,-1,-1):
        t=i/n; px=x+lx*t; py=y+ly*t; s=math.sin(t*math.pi)*wid*.2; nx,ny=-ly,lx; L=math.hypot(nx,ny); pts.append((px-nx/L*s,py-ny/L*s))
    d.polygon(pts, fill=hexc(col))
def big_flower(im,cx,cy,S):
    d=ImageDraw.Draw(im)
    d.line([(cx,cy),(cx+S*.03,cy+S*.55)], fill=hexc('#4f8a35'), width=int(S*.045))
    leaf(d,cx+S*.02,cy+S*.36,S*.26,-S*.12,S*.08,'#5e9c3f'); leaf(d,cx+S*.01,cy+S*.44,-S*.24,-S*.1,S*.075,'#6aa94a')
    flower(d,cx,cy,S*.27,rot=.2)
S=4096
bg=grad(S,S,'#a9dcef','#e4f3d4'); d=ImageDraw.Draw(bg)
sun(bg,int(S*.74),int(S*.26),int(S*.11))
d=ImageDraw.Draw(bg)
hill(d,S,S,S*.66,S*.04,0.6,hexc('#8fc06a'),.8); hill(d,S,S,S*.76,S*.035,2.2,hexc('#6fa64d'),1.1); hill(d,S,S,S*.87,S*.02,4.0,hexc('#5a9140'),1.3)
random.seed(3)
for k in range(70):
    x=random.uniform(0,S); y=random.uniform(S*.8,S*.98); r=S*random.uniform(.006,.012)
    d.ellipse([x-r,y-r,x+r,y+r], fill=hexc(random.choice(['#f6f0dc','#f4c34a','#e98fb0','#ffffff'])))
fg=Image.new('RGBA',(S,S),(0,0,0,0)); big_flower(fg,S*.5,S*.42,S*.62)
sh=Image.new('RGBA',(S,S),(0,0,0,0)); sh.alpha_composite(fg); sh=Image.eval(sh.split()[3],lambda a:int(a*.25)); shadow=Image.new('RGBA',(S,S),(30,50,20,0)); shadow.putalpha(sh); shadow=shadow.filter(ImageFilter.GaussianBlur(S*.012))
fg2=Image.new('RGBA',(S,S),(0,0,0,0)); fg2.alpha_composite(shadow,(int(S*.012),int(S*.02))); fg2.alpha_composite(fg)
icon=bg.copy(); icon.alpha_composite(fg2)
icon.resize((1024,1024),Image.LANCZOS).convert('RGB').save(OUT+'assets/icon-only.png')
bg.resize((1024,1024),Image.LANCZOS).convert('RGB').save(OUT+'assets/icon-background.png')
fgs=fg2.resize((int(S*.72),int(S*.72)),Image.LANCZOS); fgA=Image.new('RGBA',(S,S),(0,0,0,0)); fgA.alpha_composite(fgs,(int(S*.14),int(S*.15)))
fgA.resize((1024,1024),Image.LANCZOS).save(OUT+'assets/icon-foreground.png')
icon.resize((512,512),Image.LANCZOS).convert('RGB').save(OUT+'store/play-icon-512.png')
SP=2732; sp=grad(SP,SP,'#bfe3c8','#a7c197'); ic=icon.resize((620,620),Image.LANCZOS)
m=Image.new('L',(620,620),0); ImageDraw.Draw(m).rounded_rectangle([0,0,619,619],radius=140,fill=255); sp.paste(ic,((SP-620)//2,(SP-620)//2-160),m)
d=ImageDraw.Draw(sp); f=font(170); t='Gartenglück'; w=d.textlength(t,font=f); d.text(((SP-w)/2,SP/2+230),t,font=f,fill=hexc('#26311f'))
sp.convert('RGB').save(OUT+'assets/splash.png')
spd=grad(SP,SP,'#34452a','#1f2a18'); spd.paste(ic,((SP-620)//2,(SP-620)//2-160),m); d=ImageDraw.Draw(spd); d.text(((SP-w)/2,SP/2+230),t,font=f,fill=hexc('#f6f0dc')); spd.convert('RGB').save(OUT+'assets/splash-dark.png')
W,H=3072,1500; fe=grad(W,H,'#9fd6ec','#e8f4d6'); sun(fe,int(W*.86),int(H*.2),int(H*.09)); d=ImageDraw.Draw(fe)
for cx,cy,s in [(.18,.16,1),(.55,.1,.8),(.7,.26,.6)]:
    for dx,dy,r in [(0,0,.07),(.05,.01,.055),(-.05,.015,.05),(.025,-.03,.05)]:
        x=W*(cx+dx*s); y=H*(cy+dy*s); rr=H*r*s; d.ellipse([x-rr*1.6,y-rr,x+rr*1.6,y+rr], fill=(255,255,255,235))
hill(d,W,H,H*.55,H*.04,1.0,hexc('#93c36d'),.7)
hx,hy=W*.78,H*.5; d.rectangle([hx-170,hy-60,hx+170,hy+170], fill=hexc('#f3e6c8')); d.polygon([(hx-210,hy-50),(hx,hy-230),(hx+210,hy-50)], fill=hexc('#c45b3c'))
d.rectangle([hx-40,hy+40,hx+40,hy+170], fill=hexc('#7a5234')); d.rectangle([hx-140,hy+10,hx-75,hy+75], fill=hexc('#9fd0e6')); d.rectangle([hx+75,hy+10,hx+140,hy+75], fill=hexc('#9fd0e6'))
hill(d,W,H,H*.68,H*.03,2.4,hexc('#73a94f'),1.0)
d.ellipse([W*.52,H*.74,W*.74,H*.86], fill=hexc('#6fb3cf')); d.ellipse([W*.55,H*.76,W*.68,H*.8], fill=hexc('#a5d6ea'))
d.polygon([(W*.76,H*.67),(W*.8,H*.67),(W*.9,H),(W*.72,H)], fill=hexc('#d8c39a'))
hill(d,W,H,H*.92,H*.015,4.0,hexc('#5f9442'),1.6)
random.seed(7)
for k in range(160):
    x=random.uniform(W*.02,W*.98); y=random.uniform(H*.72,H*.99)
    if W*.5<x<W*.76 and y<H*.88: continue
    if W*.7<x<W*.92 and y>H*.67: continue
    r=H*random.uniform(.012,.024); col=random.choice(['#e8684a','#f4c34a','#e98fb0','#b98ae0','#ffffff','#f08a3c'])
    d.line([(x,y),(x,y+r*2.2)], fill=hexc('#4f8a35'), width=8); flower(d,x,y,r,petal=col,petal2=col,center='#f9dc84',n=6,rot=random.random())
f1=font(250,700); f2=font(96,500); t1='Gartenglück'; t2='Dein eigener Traumgarten'
tw=d.textlength(t1,font=f1); x0=W*.06; y0=H*.2
pan=Image.new('RGBA',(W,H),(0,0,0,0)); pd=ImageDraw.Draw(pan); pd.rounded_rectangle([x0-70,y0-40,x0+tw+90,y0+470],radius=80,fill=(246,240,220,215)); fe.alpha_composite(pan)
d=ImageDraw.Draw(fe); d.text((x0,y0),t1,font=f1,fill=hexc('#26311f')); d.text((x0+8,y0+320),t2,font=f2,fill=hexc('#4f6b3a'))
fe.resize((1024,500),Image.LANCZOS).convert('RGB').save(OUT+'store/feature-graphic-1024x500.png')
print('ok')
