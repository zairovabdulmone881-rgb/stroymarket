import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.getcwd()); from script_ep import LINES, TEMPLATE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
W,H,FPS=1080,1920,30
WHITE=(245,245,248); RED=(214,40,56); BLUE=(84,170,240); GREY=(120,130,150)
FONT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"Montserrat.ttf")
def F(s,w=800):
    f=ImageFont.truetype(FONT,s); f.set_variation_by_axes([w]); return f
ACC=(255,214,120)
def base():
    a=np.zeros((H,W,3),np.float32); yy=np.linspace(0,1,H)[:,None]; xx=np.linspace(-1,1,W)[None,:]
    g=np.exp(-((xx**2)*1.4+((yy-0.62)**2)*5))
    a[...,0]=4+10*g; a[...,1]=6+22*g; a[...,2]=12+60*g
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")
BG=base()
def line(d,p,q,w=12,c=WHITE): d.line([p,q],fill=c,width=int(w))
def figure(d,x,fy,s=1.0,pose="stand",t=0.0,hold=None,flash=False):
    lw=14*s; hip=(x,fy-130*s); neck=(x,fy-250*s)
    if pose=="sit": hip=(x,fy-34*s); neck=(x,fy-150*s)
    d.ellipse((neck[0]-28*s,neck[1]-62*s,neck[0]+28*s,neck[1]-6*s),outline=WHITE,width=int(lw*0.8))
    line(d,neck,hip,lw)
    sh=(x,neck[1]+22*s)
    if pose in("stand","walk","carry"):
        ph=t*6.5 if pose!="stand" else 0
        for sd in(-1,1):
            ang=sd*0.5*math.sin(ph) if pose!="stand" else sd*0.08
            line(d,hip,(hip[0]+math.sin(ang)*135*s,fy),lw)
    else:
        line(d,hip,(hip[0]+95*s,hip[1]-15*s),lw); line(d,(hip[0]+95*s,hip[1]-15*s),(hip[0]+95*s,fy),lw)
        line(d,hip,(hip[0]+40*s,hip[1]+5*s),lw)
    hand=None
    if flash:
        hand=(x+120*s,sh[1]+10*s); line(d,sh,hand,lw); line(d,sh,(x-40*s,sh[1]+90*s),lw)
    elif pose=="carry":
        hand=(x+70*s,sh[1]+90*s); line(d,sh,hand,lw); line(d,sh,(x+20*s,sh[1]+100*s),lw)
    elif pose=="walk":
        sw=0.5*math.sin(t*6.5)
        for sd in(-1,1): line(d,sh,(x+math.sin(-sd*sw)*100*s,sh[1]+90*s),lw)
    else:
        line(d,sh,(x-60*s,sh[1]+95*s),lw); line(d,sh,(x+60*s,sh[1]+95*s),lw)
    return hand
def caption(img,txt,k):
    d=ImageDraw.Draw(img); words=txt.split(); key=max(words,key=len)
    for sz in (58,52,46,42):
        f=F(sz); lines=[]; cur=""
        for w in words:
            tst=(cur+" "+w).strip()
            if d.textlength(tst,font=f)>960: lines.append(cur); cur=w
            else: cur=tst
        lines.append(cur)
        if len(lines)<=3: break
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dl=ImageDraw.Draw(L); y=120
    for ln in lines:
        tot=dl.textlength(ln,font=f); x=540-tot/2
        for w in ln.split():
            dl.text((x,y),w,font=f,fill=(*(ACC if w==key else WHITE),int(255*k)),stroke_width=3,stroke_fill=(0,0,0,int(255*k))); x+=dl.textlength(w+" ",font=f)
        y+=int(sz*1.35)
    return Image.alpha_composite(img,L)
# ---------- сцены ----------
def hw(y): return 22+250*(abs(y-930)/550)**0.75
def sc_hourglass(img,t,T):
    d=ImageDraw.Draw(img); p=min(1,t/T); cx=540
    ytop=int(520+(880-520)*p); ypile=int(1480-(1480-1190)*p)
    for y in range(ytop,930): h=hw(y)-6; d.line([(cx-h,y),(cx+h,y)],fill=RED)
    for y in range(ypile,1480): h=hw(y)-6; d.line([(cx-h,y),(cx+h,y)],fill=(190,32,48))
    d.line([(cx,930),(cx,ypile)],fill=RED,width=5)
    for i in range(14):
        yy=930+((t*260+i*53)%max(10,ypile-930)); d.ellipse((cx-3+((i*7)%9-4),yy-3,cx+3+((i*7)%9-4),yy+3),fill=RED)
    pts=[(cx-hw(y),y) for y in range(380,1481,10)]; pts2=[(cx+hw(y),y) for y in range(380,1481,10)]
    d.line(pts,fill=(170,190,215),width=6); d.line(pts2,fill=(170,190,215),width=6)
    d.line([(cx-hw(380),380),(cx+hw(380),380)],fill=(170,190,215),width=8); d.line([(cx-hw(1480),1480),(cx+hw(1480),1480)],fill=(170,190,215),width=8)
    figure(d,cx-90,ypile,0.8,"sit",t)
def sc_buckets(img,t,T):
    d=ImageDraw.Draw(img); gy=1300; A=T*0.45; B=T*0.62
    d.line([(0,gy),(W,gy)],fill=GREY,width=5)
    d.rectangle((60,1130,300,gy),outline=BLUE,width=6)
    d.rectangle((66,1150,294,gy-4),fill=(40,100,170))
    d.rectangle((780,880,1000,gy),outline=WHITE,width=6)
    lvl=0.18*min(t/A,1) if t<B else 0.18+0.7*min(1,(t-B-1.0)/(T-B-1.5)) if t>B+1 else 0.18
    hh=int((gy-886)*lvl); d.rectangle((786,gy-4-hh,994,gy-4),fill=BLUE)
    if t<B:
        if t<A:
            ph=(t%4.0)/4.0
            if ph<0.5: x=330+(740-330)*(ph/0.5); full=True
            else: x=740-(740-330)*((ph-0.5)/0.5); full=False
            hand=figure(d,x,gy,1.0,"carry",t)
            bx,by=hand[0],hand[1]+30
            d.polygon([(bx-30,by),(bx+30,by),(bx+22,by+50),(bx-22,by+50)],outline=WHITE,fill=(40,100,170) if full else None)
        else:
            figure(d,560,gy,1.0,"stand",t)
            e=300+(780-300)*min(1,(t-A)/(B-A)); d.rectangle((300,1246,e,1274),fill=(110,120,140))
    else:
        d.rectangle((300,1246,780,1274),fill=(110,120,140))
        for i in range(24):
            x=300+((i*20+t*220)%480); d.rectangle((x,1254,x+10,1266),fill=BLUE)
        figure(d,560,gy,1.0,"sit",t)
    lab="ВЕДРО" if t<A else ("" if t<B else "ТРУБА")
    if lab:
        L=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(L).text((540,1480),lab,font=F(90),fill=(*BLUE,200),anchor="mm"); img.alpha_composite(L)
def sc_flash(img,t,T,idx,lt):
    gy=1300; hx0=250; d=ImageDraw.Draw(img); d.line([(0,gy),(W,gy)],fill=GREY,width=5)
    d2=ImageDraw.Draw(img); hand=figure(d2,hx0,gy,1.05,"stand",t,flash=True)
    ax,ay=hand; top=ay-420-50*math.sin(t*0.9)
    C=Image.new("RGBA",(W,H),(0,0,0,0)); dc=ImageDraw.Draw(C)
    dc.polygon([(ax,ay),(W,top),(W,gy)],fill=(255,240,190,70)); C=C.filter(ImageFilter.GaussianBlur(6)); img.alpha_composite(C)
    d=ImageDraw.Draw(img); d.ellipse((ax-10,ay-10,ax+10,ay+10),fill=(255,250,220))
    figure(d,930,gy,0.8,"stand",t)
    k=min(1,lt/0.5); a=int(255*k); I=Image.new("RGBA",(W,H),(0,0,0,0)); di=ImageDraw.Draw(I); cx,cy=640,820
    if idx==1:
        di.ellipse((cx-50,cy-50,cx+50,cy+50),fill=(255,214,120,a))
        for i in range(16):
            an=i/16*6.283+t*0.4; di.line((cx+math.cos(an)*70,cy+math.sin(an)*70,cx+math.cos(an)*115,cy+math.sin(an)*115),fill=(255,214,120,a),width=7)
    elif idx==2:
        di.ellipse((cx-70,cy-70,cx+70,cy+70),fill=(230,170,110,a))
        an=t*1.2; di.arc((cx-110,cy-110,cx+110,cy+110),an*57.3,an*57.3+250,fill=(255,255,255,a),width=6)
    elif idx==3:
        for j in range(4):
            pts=[(x,cy-60+j*45+14*math.sin(x/38+t*2+j)) for x in range(cx-170,cx+171,10)]; di.line(pts,fill=(*BLUE,a),width=9)
    img.alpha_composite(I)
def frame(t,TM):
    T=TM["dur"]; img=BG.copy()
    idx=0; lt=0
    for i,(a,b) in enumerate(TM["lines"]):
        if t>=a-0.05: idx=i+1 if TEMPLATE!="flashlight" else i; lt=t-a
    if TEMPLATE=="hourglass": sc_hourglass(img,t,T)
    elif TEMPLATE=="buckets": sc_buckets(img,t,T)
    else: sc_flash(img,t,T,idx,lt)
    ci=None
    for i,(a,b) in enumerate(TM["lines"]):
        nxt=TM["lines"][i+1][0]-0.04 if i+1<len(TM["lines"]) else 99
        if a-0.05<=t<=min(b+0.35,nxt): ci=(i,t-a)
    if ci: img=caption(img,LINES[ci[0]][1],min(1,(ci[1]+0.05)/0.2))
    return img.convert("RGB")
if __name__=="__main__":
    TM=json.load(open("timing.json"))
    if sys.argv[1]=="preview":
        ts=[0.2]+[(a+b)/2 for a,b in TM["lines"]]+[TM["dur"]-0.3]
        ims=[frame(t,TM).resize((360,640)) for t in ts]; sh=Image.new("RGB",(360*len(ims),640)); [sh.paste(im,(i*360,0)) for i,im in enumerate(ims)]; sh.save("preview.png")
    else:
        n=int(TM["dur"]*FPS); pr=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","17","video_only.mp4"],stdin=subprocess.PIPE)
        for i in range(n): pr.stdin.write(frame(i/FPS,TM).tobytes())
        pr.stdin.close(); pr.wait()
