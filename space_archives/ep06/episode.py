import sys, json, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from script_ep import EPISODE, LINES, SCENES
W, H, FPS = 1080, 1920, 30
GOLD=(244,188,66); CREAM=(255,238,204); GREY=(206,196,178); RED=(214,40,56); BLUE=(84,170,240); ORANGE=(242,132,42)
def F(s, w=800):
    f = ImageFont.truetype("fonts/Montserrat.ttf", s); f.set_variation_by_axes([w]); return f
def bg():
    a = np.zeros((H,W,3),np.uint8); g = np.linspace(0,1,H)[:,None]
    top=np.array([4,6,20]); bot=np.array([14,8,16])
    a[:] = (top*(1-g)+bot*g)[:,None,:].astype(np.uint8)[:, :, :] if False else (top[None,:]*(1-g)+bot[None,:]*g)[:,None,:]
    return Image.fromarray(a)
BG = bg(); random.seed(6)
STARS = [(random.randint(0,W),random.randint(0,H),random.random()*6.28,random.choice([1,1,2,2,3]),random.random()<.12) for _ in range(190)]
def ctext(d, x, y, s, fill, size, w=800, stroke=0, track=0):
    f = F(size, w); tw = d.textlength(s, font=f)
    d.text((x-tw/2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0,0,0))
def astronaut(d, cx=470, cy=690, r=168):
    d.rounded_rectangle((cx-r*.95, cy+r*.7, cx+r*.95, cy+r*3), 70, fill=(235,235,240))
    d.rounded_rectangle((cx-r*.5, cy+r*1.5, cx+r*.5, cy+r*1.7), 8, fill=ORANGE)
    d.ellipse((cx-r*1.4, cy+r*.9, cx-r*.7, cy+r*1.6), fill=(225,225,232)); d.ellipse((cx+r*.7, cy+r*.9, cx+r*1.4, cy+r*1.6), fill=(225,225,232))
    d.ellipse((cx-r,cy-r,cx+r,cy+r), fill=(245,245,248))
    d.rounded_rectangle((cx-r*.78,cy-r*.6,cx+r*.78,cy+r*.62), 80, fill=(14,16,34))
    d.ellipse((cx-r*.5,cy-r*.45,cx-r*.1,cy-r*.15), fill=(60,70,120))
def sun(img, cx, cy, t, big=False, col=GOLD):
    d = ImageDraw.Draw(img); R = 70 if not big else 110
    for i in range(22):
        a = i/22*6.283 + .12*t; L = R*(2.2 if i%2 else 1.6)
        d.line((cx+math.cos(a)*R*1.15, cy+math.sin(a)*R*1.15, cx+math.cos(a)*L, cy+math.sin(a)*L), fill=col, width=9)
    d.ellipse((cx-R,cy-R,cx+R,cy+R), fill=(*col,255))
def glow(layer, cx, cy, r, col):
    g = Image.new("RGBA", layer.size, (0,0,0,0)); ImageDraw.Draw(g).ellipse((cx-r,cy-r,cx+r,cy+r), fill=(*col,70))
    return Image.alpha_composite(layer, g.filter(ImageFilter.GaussianBlur(r/2)))
def scene(kind, p, t, n):
    L = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(L)
    if kind=="intro":
        ctext(d,540,490,"ВЫПУСК",CREAM,130); d.text((540,1010),str(EPISODE),font=F(900),fill=CREAM,anchor="mm")
        d.rounded_rectangle((100,1445,980,1540),30,fill=(168,26,44)); ctext(d,540,1470,"КАТЕГОРИЯ 2: НАУКА И ФИЗИКА",CREAM,40)
        ctext(d,540,1668,"КОСМИЧЕСКИЕ АРХИВЫ",GOLD,40)
    elif kind=="astro_q":
        astronaut(d); 
        for x,y,s in((300,420,90),(780,360,110)): ctext(d,x,y,"?",GOLD,s)
    elif kind in("astro_sun","plate"):
        if kind=="plate":
            d.rounded_rectangle((650,230,1180,1640),40,fill=(48,54,72))
            for i,s in enumerate(p["t"]): ctext(d,865,500+i*210,s,GOLD if i==2 else CREAM,64 if i<2 else 46)
            ctext(d,865,1500,p["cap"],GREY,30,700); astronaut(d)
        else:
            L = glow(L, 770,500,230 if p.get("big") else 150,(255,120,40) if p.get("big") else GOLD); sun(L,770,500,t,p.get("big"),(255,90,40) if p.get("big") else GOLD); d = ImageDraw.Draw(L)
            astronaut(d)
            for i,s in enumerate(p["acc"]): ctext(d,540,1130+i*115,s,(255,240,210),110 if p.get("big") else 96,800,5)
    elif kind=="title3":
        for i,s in enumerate(p["t"]): ctext(d,540,575+i*140-30,s,GOLD if i==2 else CREAM,84 if len(s)<14 else 70)
        d.line((300,1010,780,1010),fill=ORANGE,width=6); ctext(d,540,1135,p["cap"],BLUE,34,700)
    elif kind=="rings":
        k = (t%2)/2; 
        for i in range(5):
            r = 85+ (i+(k if p["grow"] else 1-k))*125; a = max(0,min(255,int(255*(1-r/760))))
            d.ellipse((540-r,880-r,540+r,880+r),outline=(*BLUE,a),width=5)
        d.ellipse((520,860,560,900),fill=GOLD)
        d.rounded_rectangle((160,1330,920,1425),40,fill=(20,30,60),outline=BLUE,width=3); ctext(d,540,1352,p["cap"],CREAM,42)
    elif kind=="icon":
        d.ellipse((520-340,720-340,520+340,720+340),outline=RED,width=44); ctext(d,520,560,"!",RED,420)
        ctext(d,540,1260,p["t"][0],GOLD,96); ctext(d,540,1370,p["t"][1],GOLD,96)
    elif kind=="final":
        ctext(d,540,330,"КОСМИЧЕСКИЕ",GOLD,96); ctext(d,540,520,"АРХИВЫ",CREAM,170)
        d.rounded_rectangle((170,790,910,915),50,fill=RED); ctext(d,540,825,"ПОДПИСАТЬСЯ",CREAM,56)
        yy = 1050+ 20*math.sin(t*5); d.polygon([(540-70,yy),(540+70,yy),(540+70,yy+120),(540+130,yy+120),(540,yy+250),(540-130,yy+120),(540-70,yy+120)],fill=RED)
    return L
def subs(sub, tl, tr, t):
    if not(tl<=t<=tr): return None
    w = sub.split(); ch = [" ".join(w[i:i+3]) for i in range(0,len(w),3)]
    tot = sum(len(c) for c in ch); acc=tl; span=tr-tl
    for c in ch:
        e = acc+span*len(c)/tot
        if t<e: return c, t-acc
        acc=e
    return ch[-1], 0
def render_frame(t, TM):
    img = BG.copy().convert("RGBA"); d = ImageDraw.Draw(img)
    for x,y,ph,s,plus in STARS:
        a = int(120+110*math.sin(t*2+ph)); c=(a,a,min(255,a+20))
        if plus: d.line((x-s*3,y,x+s*3,y),fill=c); d.line((x,y-s*3,x,y+s*3),fill=c)
        else: d.ellipse((x-s/2,y-s/2,x+s/2,y+s/2),fill=c)
    ts = [(0, TM["intro"][0]-0.06, "intro", {})]
    st = [0.0]+[TM["lines"][i][0]-0.1 for i in range(1,len(TM["lines"]))]
    idx = 0
    if t>=2.5: 
        idx=1
        for i in range(len(TM["lines"])):
            if t>=(TM["lines"][i][0]-0.1 if i>0 else 2.5): idx=i+2
    if idx<=1 and t<2.5: kind,p,t0 = "intro",{},0
    else: kind,p = SCENES[idx-2]; t0 = 2.5 if idx==2 else TM["lines"][idx-2][0]-0.1
    lt = t-t0; k = min(1,lt/0.45); L = scene(kind,p,t,EPISODE)
    if kind!="intro":
        a = np.array(L); a[...,3] = (a[...,3]*k).astype(np.uint8); L = Image.fromarray(a)
        L = Image.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,0)), L.transform((W,H),Image.AFFINE,(1,0,0,0,1,25*(1-k))))
    img = Image.alpha_composite(img,L); d = ImageDraw.Draw(img)
    if lt<0.14: img = Image.blend(img, Image.new("RGBA",(W,H),(0,0,0,255)), 0.5*(1-lt/0.14))
    d = ImageDraw.Draw(img); d.text((40,1852),"КОСМИЧЕСКИЕ АРХИВЫ",font=F(19),fill="white")
    for i,(tl,tr) in enumerate(TM["lines"]):
        r = subs(LINES[i][1], tl, min(tr+0.4, TM["lines"][i+1][0]-0.04 if i+1<len(TM["lines"]) else 999), t)
        if r:
            c,_ = r; sz=66
            while d.textlength(c,font=F(sz))>980 and sz>40: sz-=2
            ws=c.split(); key=max(ws,key=len); f=F(sz); tot=d.textlength(c,font=f); x=540-tot/2
            for wd in ws:
                d.text((x,1548),wd,font=f,fill=GOLD if wd==key else CREAM,stroke_width=4,stroke_fill=(0,0,0)); x+=d.textlength(wd+" ",font=f)
    return img.convert("RGB")
if __name__=="__main__":
    TM = json.load(open("timing.json"))
    if sys.argv[1]=="preview":
        ts = [1.5]+[(a+b)/2 for a,b in TM["lines"]]
        ims=[render_frame(t,TM).resize((270,480)) for t in ts]; cols=7; rows=(len(ims)+cols-1)//cols
        sh=Image.new("RGB",(270*cols,480*rows)); [sh.paste(im,((i%cols)*270,(i//cols)*480)) for i,im in enumerate(ims)]; sh.save("preview.png")
    else:
        n=int(TM["dur"]*FPS); pr=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","17","video_only.mp4"],stdin=subprocess.PIPE)
        for i in range(n): pr.stdin.write(render_frame(i/FPS,TM).tobytes())
        pr.stdin.close(); pr.wait()
