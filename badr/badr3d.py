import sys, os, json, math, random, subprocess
sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import render as R
from render import F, W, H, FPS, LINES
MUS=(64,138,214); QUR=(196,48,60); GOLD=(255,214,120); SAND=(176,140,90); DIM=(150,160,180); SKIN=(228,231,238)
WHITE=(245,246,250); BL=(120,190,255); RD=(255,120,130)
def lerp(a,b,u): return tuple(int(a[i]+(b[i]-a[i])*u) for i in range(3))
def sm(x): x=max(0,min(1,x)); return x*x*(3-2*x)
class Ctx: pass
# ---------- 3D-шейдинг примитивов ----------
def tube(d,p,q,r,col,n=None):
    n=n or (6 if r>9 else 4 if r>5 else 2)
    dark=tuple(int(v*0.36) for v in col); hi=tuple(min(255,int(v*1.1)+10) for v in col)
    for k in range(n):
        u=k/(n-1) if n>1 else 1.0
        c=lerp(dark,hi,u**1.25); rr=r*(1-0.74*u); ox=-0.55*r*0.45*u; oy=-0.8*r*0.45*u
        a=(p[0]+ox,p[1]+oy); b=(q[0]+ox,q[1]+oy)
        d.line([a,b],fill=c,width=max(1,int(rr*2)))
        d.ellipse((a[0]-rr,a[1]-rr,a[0]+rr,a[1]+rr),fill=c); d.ellipse((b[0]-rr,b[1]-rr,b[0]+rr,b[1]+rr),fill=c)
def sphere(d,c_,r,col,n=None):
    tube(d,c_,c_,r,col,n)
    if r>7: d.ellipse((c_[0]-r*0.5-r*0.12,c_[1]-r*0.55-r*0.12,c_[0]-r*0.5+r*0.12,c_[1]-r*0.55+r*0.12),fill=(255,255,255))
def V(a,L,dirn): return (math.sin(a)*dirn*L, math.cos(a)*L)
def fig(c,x,fy,s,col,ph=0.0,pose="walk",sw=None,dirn=1,run=1.0,lie=False,point=False,gcol=None):
    Hh=250*s; d=c.dF; t=c.t
    Lt=.215*Hh; Ls=.215*Hh; Lto=.31*Hh; Lu=.16*Hh; Lf=.15*Hh; hr=.066*Hh
    rt=max(1.8,.042*Hh); rs=max(1.5,.033*Hh); ru=max(1.5,.03*Hh); rf=max(1.2,.025*Hh); rto=max(2.5,.066*Hh)
    c.SH.append((x,fy,0.2*Hh))
    if lie:
        y=fy-rto*0.9; tube(d,(x-.3*Hh,y),(x+.05*Hh,y),rto,col); sphere(d,(x+.05*Hh+hr+.03*Hh,y),hr,SKIN)
        tube(d,(x-.3*Hh,y),(x-.62*Hh,y+rt*0.2),rt,SKIN); return
    a0=ph+t*7*run
    legs=[]
    for k in (0,1):
        if pose=="walk": a=a0+k*math.pi; th1=.55*math.sin(a); th2=th1-.75*max(0,math.cos(a))
        elif pose=="sit": th1,th2=(1.45,0.05)
        else: th1=(k*2-1)*.07; th2=th1
        k1=V(th1,Lt,dirn); k2=V(th2,Ls,dirn); legs.append((k1,(k1[0]+k2[0],k1[1]+k2[1])))
    drop=max(l[1][1] for l in legs); hip=(x,fy-drop)
    lean=(.18 if run>1.2 else .08) if pose=="walk" else 0.0
    sho=(hip[0]+dirn*math.sin(lean)*Lto, hip[1]-math.cos(lean)*Lto)
    head=(sho[0]+dirn*math.sin(lean)*(.045*Hh+hr), sho[1]-math.cos(lean)*(.045*Hh+hr))
    def leg(k):
        kn=(hip[0]+legs[k][0][0],hip[1]+legs[k][0][1]); an=(hip[0]+legs[k][1][0],hip[1]+legs[k][1][1])
        tube(d,hip,kn,rt,SKIN if gcol is None else gcol); tube(d,kn,an,rs,SKIN)
        tube(d,an,(an[0]+dirn*.075*Hh,an[1]),rs*0.95,SKIN)
    def arm(k,mode):
        if mode=="sword": au=1.5+.3*sw; af=1.9+.4*sw
        elif mode=="guard": au=-.5; af=-.15
        elif mode=="point": au=1.65; af=1.7
        elif pose=="walk": au=(-.62 if k==0 else .62)*math.sin(a0)*(1+.4*(run-1)); af=au+.45+.25*(run-1)
        else: au=(k*2-1)*.1+(.05 if k else -.05); af=au+.15
        e=V(au,Lu,dirn); el=(sho[0]+e[0],sho[1]+e[1]); w=V(af,Lf,dirn); wr=(el[0]+w[0],el[1]+w[1])
        tube(d,sho,el,ru,col); tube(d,el,wr,rf,SKIN); sphere(d,wr,rf*1.25,SKIN,3)
        if mode=="sword":
            ph_=2.3+.7*sw; sv=V(ph_,.36*Hh,dirn); tube(d,wr,(wr[0]+sv[0],wr[1]+sv[1]),max(1,.011*Hh),(214,218,228),3)
    leg(1); arm(1,"guard" if sw is not None else ("point" if False else "n")); 
    tube(d,hip,sho,rto,col); sphere(d,(hip[0],hip[1]),rto*0.95,col,3)
    leg(0); arm(0,"sword" if sw is not None else ("point" if point else "n"))
    tube(d,sho,(sho[0]+dirn*math.sin(lean)*.045*Hh,sho[1]-.045*Hh),rf*1.1,SKIN,3); sphere(d,head,hr,SKIN)
def camel(c,x,fy,s,dirn=-1,ph=0.0,rider=False):
    d=c.dF; t=c.t; col=(190,160,125); by=fy-108*s; c.SH.append((x,fy,70*s))
    for k,(lx,pp) in enumerate(((-52,0),(-30,2.2),(30,1.1),(52,3.3))):
        a=.45*math.sin(t*6+ph+pp); kn=(x+lx*s+math.sin(a)*22*s,by+48*s); an=(kn[0]+math.sin(a-.5*max(0,math.cos(t*6+ph+pp)))*26*s,fy)
        if k in(1,3): tube(d,(x+lx*s,by+22*s),kn,9*s,tuple(int(v*.8) for v in col)); tube(d,kn,an,7*s,tuple(int(v*.8) for v in col))
    tube(d,(x-55*s,by),(x+55*s,by),34*s,col); sphere(d,(x-8*s,by-44*s),23*s,col)
    for k,(lx,pp) in enumerate(((-52,0),(-30,2.2),(30,1.1),(52,3.3))):
        a=.45*math.sin(t*6+ph+pp); kn=(x+lx*s+math.sin(a)*22*s,by+48*s); an=(kn[0]+math.sin(a-.5*max(0,math.cos(t*6+ph+pp)))*26*s,fy)
        if k in(0,2): tube(d,(x+lx*s,by+22*s),kn,10*s,col); tube(d,kn,an,7.5*s,col)
    nb=(x+dirn*58*s,by-8*s); nt=(x+dirn*96*s,by-82*s); tube(d,nb,nt,14*s,col); tube(d,nt,(nt[0]+dirn*30*s,nt[1]-6*s),11*s,col)
    if rider: fig(c,x-8*s,by-44*s,0.6*s*1.4,GOLD,pose="stand",dirn=-dirn)
# ---------- сцена и эффекты ----------
def make_base():
    a=np.zeros((H,W,3),np.float32); yy=np.linspace(0,1,H)[:,None]; xx=np.linspace(-1,1,W)[None,:]
    g=np.exp(-((xx**2)*1.1+((yy-0.55)**2)*4.2)); h=np.exp(-(xx**2)*6)*np.exp(-((yy-0.25)**2)*14)
    a[...,0]=3+8*g+10*h; a[...,1]=5+20*g+18*h; a[...,2]=11+58*g+40*h
    v=1-0.55*(xx**2*0.8+(yy-0.5)**2*1.2); a*=np.clip(v,0.3,1)[...,None]
    rng=np.random.RandomState(1); a+=rng.normal(0,1.6,a.shape)
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8)).convert("RGBA")
BASE=make_base()
def make_rays():
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for x0,x1,x2 in((300,150,470),(560,380,720),(800,650,960)):
        d.polygon([(x0,0),(x1,1300),(x2,1300)],fill=(120,170,255,9))
    return L.filter(ImageFilter.GaussianBlur(26))
RAYS=make_rays()
_floor={}
def floor_img(gy):
    if gy not in _floor:
        h=H-gy; a=np.zeros((h,W,4),np.float32); u=np.linspace(0,1,h)[:,None]
        a[...,0]=(24-18*u)*np.ones((1,W)); a[...,1]=(32-24*u)*np.ones((1,W)); a[...,2]=(58-42*u)*np.ones((1,W)); a[...,3]=255
        hl=np.exp(-u*40)*np.exp(-((np.linspace(-1,1,W)[None,:])**2)*1.5); a[...,0]+=40*hl; a[...,1]+=70*hl; a[...,2]+=120*hl
        _floor[gy]=Image.fromarray(np.clip(a,0,255).astype(np.uint8),"RGBA")
    return _floor[gy]
def dunes(c,speed,y0):
    d=c.dB
    for sp,yy,col in((0.3,y0-90,(12,18,38,255)),(0.7,y0-40,(10,15,32,255))):
        pts=[(x,yy-30*math.sin((x+c.t*speed*sp)/190)-16*math.sin((x+c.t*speed*sp*1.5)/70)) for x in range(0,W+20,20)]
        d.polygon(pts+[(W,H),(0,H)],fill=col)
def set_floor(c,gy): c.B.alpha_composite(floor_img(gy),(0,gy)); c.gy=gy
def moon(c,cx,cy,r):
    G=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(G).ellipse((cx-r*1.7,cy-r*1.7,cx+r*1.7,cy+r*1.7),fill=(255,235,170,46)); c.B.alpha_composite(G.filter(ImageFilter.GaussianBlur(r*0.7)))
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for k in range(8):
        u=k/7; rr=r*(1-0.1*u); d.ellipse((cx-rr-u*r*.12,cy-rr-u*r*.12,cx+rr-u*r*.12,cy+rr-u*r*.12),fill=lerp((200,185,140),(255,246,214),u)+(255,))
    d.ellipse((cx+r*0.34,cy-r*0.3,cx+r*1.3,cy+r*0.72),fill=(0,0,0,0)); c.B.alpha_composite(L)
def text(c,x,y,s,size,col=WHITE,w=800,glow=True):
    f=F(size,w)
    if glow:
        G=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(G).text((x,y),s,font=f,fill=col+(120,),anchor="mm"); c.T.alpha_composite(G.filter(ImageFilter.GaussianBlur(10)))
    c.dT.text((x+0,y+3),s,font=f,fill=(0,0,0,170),anchor="mm"); c.dT.text((x,y),s,font=f,fill=col+(255,),anchor="mm")
def chip(c,x,y,s,size,col):
    f=F(size,700); tw=c.dT.textlength(s,font=f); pw,ph=tw+56,size*1.9
    c.dT.rounded_rectangle((x-pw/2,y-ph/2,x+pw/2,y+ph/2),radius=ph/2,fill=(10,18,40,200),outline=col+(255,),width=3)
    c.dT.text((x,y),s,font=f,fill=(240,244,252,255),anchor="mm")
def dust(c,x,y,n=10,dirn=1,sz=1.0):
    for i in range(n):
        a=(c.t*1.3+i/n)%1; r=(5+18*a)*sz; px=x-dirn*a*130*sz; py=y-a*34*sz
        cc=int(110*(1-a)); c.dF.ellipse((px-r,py-r,px+r,py+r),fill=(cc+40,cc+30,cc+14,int(150*(1-a))))
def flag(c,x,y,col,s=1.0):
    tube(c.dF,(x,y),(x,y-200*s),4*s,(200,200,210),3)
    t=c.t; pts=[(x+i*7*s,y-196*s+9*math.sin(t*6-i*0.55)*s) for i in range(13)]; p2=[(px,py+66*s) for px,py in pts]
    c.dF.polygon(pts+p2[::-1],fill=col+(255,)); c.dF.polygon([(px,py+10*s) for px,py in pts]+[(px,py+52*s) for px,py in p2[::-1]],fill=lerp(col,(255,255,255),.15)+(255,))
# ---------- сцены ----------
def s_date(c):
    dunes(c,40,1420); set_floor(c,1420); moon(c,540,690-30*sm(c.lt/1.5),104)
    text(c,540,1020,"17",330+10*math.sin(c.t*3)); text(c,540,1190,"РАМАДАНА",96,GOLD); chip(c,540,1300,"2 ГОД ХИДЖРЫ · 624 Г.",42,BL)
    for i in range(6): fig(c,(i*210+c.t*90)%1500-120,1700,0.95,MUS,i*0.9)
def s_chase(c):
    dunes(c,110,1380); set_floor(c,1380)
    for i in range(5):
        x=760+i*210-c.lt*190; camel(c,x,1520,1.15,-1,i); dust(c,x+90,1520,6,-1)
    if c.lt>0.4:
        for k in range(7): fig(c,1250+k*85-(c.lt-0.4)*300,1700,0.85,MUS,k*0.8,dirn=-1,run=1.5)
    chip(c,540,1010,"КАРАВАН КУРАЙШИТОВ · СИРИЯ → МЕККА",30,RD); chip(c,540,1830,"МУСУЛЬМАНЕ ИЗ МЕДИНЫ",34,BL)
def s_turn(c):
    p=c.p; dunes(c,90 if p<0.5 else 520,1380); set_floor(c,1380)
    if p<0.5:
        q=p/0.5
        for i in range(5):
            if q<0.35: x=900+i*200-q/0.35*600; dr=-1; y=1500
            else: x=900+i*200-600+(q-0.35)/0.65*900; dr=1; y=1500+130*sm((q-0.35)/0.3)
            camel(c,x,y,1.0,dr,i); dust(c,x-dr*80,y,5,dr)
        for k in range(5): fig(c,150+k*70,1560,1.0,MUS,k,pose="stand")
        if q>0.4:
            for k in range(5): text(c,150+k*70,1150-16*abs(math.sin(c.t*5+k)),"?",64,GOLD,glow=False)
        chip(c,540,1010,"ДРУГОЙ ПУТЬ",44,GOLD)
    else:
        q=(p-0.5)/0.5; x=1350-((q*3400)%1800)
        for i in range(10): yy=1150+i*60; xx=(x+i*173)%1300-100; c.dF.line([(xx,yy),(xx+170,yy)],fill=(90,105,135,160),width=3)
        camel(c,x,1540,1.25,-1,0,rider=True); dust(c,x+120,1540,8,-1,1.3)
        for k in range(3): c.dB.rectangle((70+k*62,1120-k*30,70+k*62+54,1400),fill=(40,22,34,255),outline=(196,48,60,255),width=3)
        chip(c,200,1060,"МЕККА",34,RD); chip(c,540,960,"ВЕСТЬ: КАРАВАН СПАСЁН",40,GOLD)
def s_army(c):
    dunes(c,160,1380); set_floor(c,1380)
    for row in range(4):
        for col in range(8):
            fig(c,60+c.lt*125+col*110-row*25,1500+row*66,0.62+row*0.07,QUR,col*0.7+row)
        dust(c,40+c.lt*125,1500+row*66,4,1)
    lx=60+c.lt*125+8*110; fig(c,lx,1520,1.1,GOLD,0); flag(c,lx+40,1520,QUR,1.1)
    chip(c,540,1010,"ВОЙСКО КУРАЙШИТОВ → БАДР",36,RD); chip(c,540,1830,"АБУ ДЖАХЛЬ ПРОДОЛЖИЛ ПОХОД",32,GOLD)
def s_count(c):
    p=c.p; dunes(c,15,1500); set_floor(c,1500)
    nb=int(31*sm(p/0.45)); nr=int(100*sm((p-0.45)/0.5))
    for i in range(nb):
        b=1+0.6*max(0,1-(p-(i/31)*0.45)*14); fig(c,80+(i%8)*58,1080+(i//8)*86,0.2*b,MUS,i,pose="stand")
    for j in range(nr):
        b=1+0.6*max(0,1-(p-0.45-(j/100)*0.5)*14); fig(c,560+(j%10)*48,600+(j//10)*86,0.2*b,QUR,j,pose="stand",dirn=-1)
    cb=int(313*sm(p/0.45)); cr=int(1000*sm((p-0.45)/0.5))
    text(c,270,1420,"≈%d"%cb,130,BL); text(c,800,1420,"≈%d"%cr,130,RD)
    chip(c,270,1545,"МУСУЛЬМАНЕ",34,BL); chip(c,800,1545,"КУРАЙШИТЫ",34,RD); text(c,540,1680,"1 ФИГУРКА = 10 ЧЕЛОВЕК",34,DIM,glow=False)
def s_wells(c):
    p=c.p; gy=1250; set_floor(c,gy)
    for k in range(5):
        x=120+k*170; cv=sm((p-(0.1+0.17*k))/0.15) if k<4 else 0
        c.dB.rounded_rectangle((x-48,gy+4,x+48,gy+170),radius=14,fill=(8,12,24,255),outline=(120,135,165,255),width=4)
        c.dB.rectangle((x-44,gy+24,x+44,gy+166),fill=(26,84,152,255))
        if k<4: c.dB.rectangle((x-44,gy+166-int(142*cv),x+44,gy+166),fill=SAND+(255,))
        if k<4 and 0<cv<1:
            for i in range(7): c.dF.ellipse((x-5+(i*9%30)-14,gy-90+((c.t*420+i*60)%120),x+5+(i*9%30)-14,gy-80+((c.t*420+i*60)%120)),fill=SAND+(255,))
    for sp in range(14):
        xx=800+((sp*37+c.t*60)%80)-40; c.dB.line([(xx,gy+40+(sp*17)%110),(xx+16,gy+40+(sp*17)%110)],fill=(170,215,255,255),width=3)
    for k in range(3): fig(c,560+k*70,gy-5,1.25,MUS,k,pose="walk" if p<0.7 else "stand")
    q=sm((p-0.35)/0.5)
    for k in range(4): fig(c,1260-q*190+k*60,gy-5,0.95,QUR,k,dirn=-1)
    chip(c,540,960,"КОЛОДЦЫ БАДРА",46,GOLD); chip(c,800,1500,"ОТКРЫТ ОДИН",28,BL); chip(c,330,1500,"ЗАКРЫТЫ",28,GOLD)
def s_duel(c):
    dunes(c,10,1380); set_floor(c,1380)
    for k in range(3):
        cx=250+k*290; a=math.sin(c.t*9+k*1.3)
        fig(c,cx-85,1620,1.5,MUS,0,pose="stand",sw=a); fig(c,cx+85,1620,1.5,QUR,0,pose="stand",sw=-a,dirn=-1)
        if abs(a)>0.8:
            for i in range(6):
                an=random.random()*6.28; c.dF.line([(cx,1330),(cx+math.cos(an)*30,1330+math.sin(an)*30)],fill=GOLD+(255,),width=3)
    text(c,540,1010,"3  НА  3",130,GOLD); chip(c,540,1830,"ПОЕДИНКИ ПЕРЕД БОЕМ",34,WHITE)
def s_battle(c):
    p=c.p; dunes(c,5,1380); set_floor(c,1380); shake=0
    adv=260*sm(p/0.4)+(120*max(0,(p-0.45)/0.55) if p>0.45 else 0)
    for row in range(4):
        for i in range(6):
            n=row*6+i; x=90+i*68+adv; fy=1470+row*62
            fig(c,x,fy,0.7+row*0.06,MUS,n,sw=(math.sin(c.t*9+n)) if p>0.3 else None,pose="walk" if p<0.4 else "stand")
    for row in range(5):
        for i in range(8):
            j=row*8+i; base=1000-i*62; fy=1470+row*52; x=base-260*sm(p/0.4)+(380*max(0,(p-0.45)/0.55)**1.3)
            if p>0.5+0.3*((j*7)%40)/40: fig(c,x,fy,0.7+row*0.05,QUR,j,lie=True)
            else: fig(c,x,fy,0.7+row*0.05,QUR,j,dirn=-1,sw=(-math.sin(c.t*9+j)) if 0.3<p<0.6 else None,pose="walk" if (p<0.4 or p>0.55) else "stand")
    if p<0.55:
        for k in range(6):
            u=((c.t*0.9+k/6)%1); ax=100+u*880 if k%2==0 else 980-u*880; ay=1150-math.sin(u*math.pi)*300; dx=26 if k%2==0 else -26
            c.dF.line([(ax,ay),(ax+dx,ay+(9 if u>0.5 else -9))],fill=(240,240,250,255),width=4)
    if 0.35<p<0.6: shake=14*random.random()
    text(c,540,1010,"БИТВА",120,GOLD)
    if p>0.7: chip(c,540,1830,"ПОБЕДА МУСУЛЬМАН",46,BL)
    c.shake=shake
def s_stats(c):
    p=c.p; base=1380; set_floor(c,1380)
    for k,(x,col,val,lab,st) in enumerate(((230,MUS,14,["МУСУЛЬМАНЕ","ПОГИБЛИ"],0.05),(540,QUR,70,["КУРАЙШИТЫ","ПОГИБЛИ"],0.4),(850,QUR,70,["КУРАЙШИТЫ","В ПЛЕНУ"],0.7))):
        u=sm((p-st)/0.2)
        if u<=0: continue
        h=int(val*5.6*u)+8
        for xi in range(-62,63,2): c.dF.rectangle((x+xi,base-h,x+xi+2,base),fill=lerp(lerp(col,(0,0,0),.6),lerp(col,(255,255,255),.25),math.sin((xi+62)/124*math.pi*0.9+0.2)**1.5)+(255,))
        text(c,x,base-h-80,("≈" if val==70 else "")+str(int(val*u)),120,lerp(col,(255,255,255),.35))
        fig(c,x,base-h-20,0.65*u+0.01,col,pose="stand")
        text(c,x,base+75,lab[0],36,lerp(col,(255,255,255),.45),glow=False); text(c,x,base+122,lab[1],36,WHITE,glow=False)
def s_teach(c):
    p=c.p; dunes(c,5,1380); set_floor(c,1380)
    c.dB.rounded_rectangle((50,780,520,1180),radius=18,fill=(18,30,26,255),outline=(190,200,215,255),width=8)
    for i in range(6):
        w=int(380*sm((p*1.4-i*0.12)/0.2))
        if w>0: c.dB.line([(85,835+i*58),(85+w,835+i*58+(10 if i%2 else -6))],fill=(215,225,230,255),width=5)
    fig(c,650,1250,1.5,QUR,pose="stand",dirn=-1,point=True)
    n=int(10*sm(p/0.7))
    for i in range(n):
        b=1+0.6*max(0,1-(p-(i/10)*0.7)*10); fig(c,160+(i%5)*125,1560+(i//5)*190,0.6*b,MUS,i,pose="stand")
    text(c,840,880,str(n),260,GOLD); chip(c,840,1040,"МУСУЛЬМАН",34,BL); chip(c,540,1850,"ГРАМОТА → СВОБОДА",40,GOLD)
def s_final(c):
    dunes(c,50,1420); set_floor(c,1420); moon(c,540,720,114+8*math.sin(c.t*2))
    text(c,540,1020,"БАДР",250+12*math.sin(c.t*3),GOLD); chip(c,540,1190,"ПЕРВОЕ КРУПНОЕ СРАЖЕНИЕ",36,WHITE); chip(c,540,1270,"МУСУЛЬМАН И КУРАЙШИТОВ",36,WHITE)
    for i in range(6): fig(c,(i*230+c.t*100)%1500-120,1650,0.9,MUS,i)
    for i in range(6): fig(c,1400-((i*230+c.t*100)%1500),1840,0.9,QUR,i,dirn=-1)
REFLECT=True; BLOOM=True; PAPER=False; PREFIX=''; FILL=(6,8,18,255)
def CAM(t): return 1.1,0.0,120.0
def backdrop(c):
    b=BASE.copy(); b.alpha_composite(RAYS); b.alpha_composite(bokeh(c.t)); return b
SC=[s_date,s_chase,s_turn,s_army,s_count,s_wells,s_duel,s_battle,s_stats,s_teach,s_final]
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
            col=GOLD if w==key else WHITE
            dl.text((x,y+3),w,font=f,fill=(0,0,0,int(170*k)),stroke_width=2,stroke_fill=(0,0,0,int(170*k))); dl.text((x,y),w,font=f,fill=col+(int(255*k),)); x+=dl.textlength(w+" ",font=f)
        y+=int(sz*1.35)
    return Image.alpha_composite(img,L)
_bok=None
def bokeh(t):
    s=Image.new("RGBA",(W//4,H//4),(0,0,0,0)); d=ImageDraw.Draw(s); rng=random.Random(7)
    for i in range(26):
        x=(rng.random()*W/4+t*rng.uniform(-6,6))%(W/4); y=(rng.random()*H/4-t*rng.uniform(2,9))%(H/4); r=rng.uniform(3,9)
        d.ellipse((x-r,y-r,x+r,y+r),fill=(150,190,255,int(rng.uniform(10,26)*(0.6+0.4*math.sin(t*1.5+i)))))
    return s.resize((W,H),Image.BICUBIC)
def frame(t,TM):
    random.seed(int(t*FPS)); c=Ctx(); c.t=t; c.SH=[]; c.shake=0
    idx=0
    for i,(a,b) in enumerate(TM["lines"]):
        if t>=a-0.05: idx=i
    a,b=TM["lines"][idx]; c.lt=max(0,t-(a-0.05)); c.p=max(0,min(1,(t-a)/max(0.1,b+0.3-a)))
    c.B=backdrop(c)
    c.F=Image.new("RGBA",(W,H),(0,0,0,0)); c.T=Image.new("RGBA",(W,H),(0,0,0,0))
    c.dB=ImageDraw.Draw(c.B); c.dF=ImageDraw.Draw(c.F); c.dT=ImageDraw.Draw(c.T); c.gy=1400
    SC[idx](c)
    # тени
    S=Image.new("RGBA",(W,H),(0,0,0,0)); ds=ImageDraw.Draw(S)
    for x,fy,r in c.SH: ds.ellipse((x-r*1.2,fy-r*0.22,x+r*1.2,fy+r*0.22),fill=(0,0,0,150))
    c.B.alpha_composite(S.filter(ImageFilter.GaussianBlur(7)))
    if REFLECT:
        # отражение в полу
        gy=c.gy; R_=c.F.transform((W,H),Image.AFFINE,(1,0,0,0,-1,2*gy+6),Image.BILINEAR)
        arr=np.array(R_); al=arr[...,3].astype(np.float32); yy=np.arange(H)[:,None]
        fade=np.clip(1-(yy-gy)/380,0,1)*0.3*(yy>gy); arr[...,3]=(al*fade).astype(np.uint8)
        R_=Image.fromarray(arr,"RGBA").filter(ImageFilter.GaussianBlur(2)); c.B.alpha_composite(R_)
    if PAPER:
        A=np.array(c.F)[...,3]; Sh=Image.new('RGBA',(W,H),(0,0,0,0)); Sh.putalpha(Image.fromarray(A).transform((W,H),Image.AFFINE,(1,0,-7,0,1,-11))); Sh=Image.composite(Image.new('RGBA',(W,H),(10,12,20,110)),Image.new('RGBA',(W,H),(0,0,0,0)),Sh.split()[3]); c.B.alpha_composite(Sh.filter(ImageFilter.GaussianBlur(3)))
    c.B.alpha_composite(c.F); c.B.alpha_composite(c.T); img=c.B
    z,dx,dy=CAM(t); img=img.transform((W,H),Image.AFFINE,(1/z,0,540-(540+dx)/z,0,1/z,1500+(dy-1500)/z),Image.BILINEAR,fillcolor=FILL)
    if BLOOM:
      sm_=img.convert("RGB").resize((W//4,H//4),Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W,H),Image.BICUBIC)
      sm_=sm_.point(lambda v:int(v*0.55)); img=ImageChops.add(img.convert("RGB"),sm_).convert("RGBA")
    if c.lt<0.25: img=Image.blend(img,Image.new("RGBA",(W,H),(0,0,0,255)),0.6*(1-c.lt/0.25))
    ci=None
    for i,(a,b) in enumerate(TM["lines"]):
        nxt=TM["lines"][i+1][0]-0.04 if i+1<len(TM["lines"]) else 99
        if a-0.05<=t<=min(b+0.35,nxt): ci=(i,t-a)
    if ci: img=caption(img,LINES[ci[0]][1],min(1,(ci[1]+0.05)/0.2))
    if c.shake: img=img.transform((W,H),Image.AFFINE,(1,0,random.uniform(-c.shake,c.shake),0,1,random.uniform(-c.shake,c.shake)))
    return img.convert("RGB")
def main(argv):
    TM=json.load(open("timing.json"))
    if argv[0]=="preview":
        ts=[(a+b)/2 for a,b in TM["lines"]]
        ims=[frame(t,TM).resize((300,533)) for t in ts]; cols=6; rows=(len(ims)+cols-1)//cols
        sh=Image.new("RGB",(300*cols,533*rows)); [sh.paste(im,((i%cols)*300,(i//cols)*533)) for i,im in enumerate(ims)]; sh.save(PREFIX+"preview.png")
    elif argv[0]=="one":
        frame(float(argv[1]),TM).save(PREFIX+"one.png")
    else:
        n=int(TM["dur"]*FPS); k=int(argv[1]); N=int(argv[2]); a=n*k//N; b=n*(k+1)//N
        pr=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","17",f"{PREFIX}seg_{k}.mp4"],stdin=subprocess.PIPE)
        for i in range(a,b): pr.stdin.write(frame(i/FPS,TM).tobytes())
        pr.stdin.close(); pr.wait()

if __name__=="__main__": main(sys.argv[1:])
