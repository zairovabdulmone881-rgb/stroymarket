import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import badr3d as B
W,H=B.W,B.H
def lerp(a,b,u): return tuple(int(a[i]+(b[i]-a[i])*u) for i in range(3))
def grad_img(stops,w=W,h=H,noise=0.0,seed=3):
    ys=np.arange(h); a=np.zeros((h,w,3),np.float32)
    for ch in range(3): a[...,ch]=np.interp(ys,[p for p,_ in stops],[c[ch] for _,c in stops])[:,None]
    if noise: a+=np.random.RandomState(seed).normal(0,noise,a.shape)
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8)).convert("RGBA")
def glowdot(img,cx,cy,r,col,al):
    G=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(G).ellipse((cx-r,cy-r,cx+r,cy+r),fill=col+(al,)); img.alpha_composite(G.filter(ImageFilter.GaussianBlur(r*0.5)))
# ---------------- плоские персонажи (вектор / бумага) ----------------
def poly(d,pts,fill,out=None,ow=3):
    d.polygon(pts,fill=fill)
    if out: d.line(pts+[pts[0]],fill=out,width=ow,joint="curve")
def limb(d,p,q,w,fill,out=None,ow=3):
    if out: d.line([p,q],fill=out,width=int(w+2*ow)); d.ellipse((p[0]-w/2-ow,p[1]-w/2-ow,p[0]+w/2+ow,p[1]+w/2+ow),fill=out); d.ellipse((q[0]-w/2-ow,q[1]-w/2-ow,q[0]+w/2+ow,q[1]+w/2+ow),fill=out)
    d.line([p,q],fill=fill,width=max(1,int(w))); d.ellipse((p[0]-w/2,p[1]-w/2,p[0]+w/2,p[1]+w/2),fill=fill); d.ellipse((q[0]-w/2,q[1]-w/2,q[0]+w/2,q[1]+w/2),fill=fill)
def Vv(a,L,dirn): return (math.sin(a)*dirn*L, math.cos(a)*L)
def make_flat(opts):
    PAL=opts["pal"]; OUT=opts.get("outline"); face=opts.get("face",True); shade=opts.get("shade",True)
    def fig(c,x,fy,s,col,ph=0.0,pose="walk",sw=None,dirn=1,run=1.0,lie=False,point=False,gcol=None):
        P=PAL.get(col,PAL["default"]); Hh=250*s; d=c.dF; t=c.t; ow=max(1,int(2.2*s*opts.get("ow",1.0))) if OUT else 0
        Lt=.22*Hh; Ls=.22*Hh; Lto=.30*Hh; Lu=.15*Hh; Lf=.14*Hh; hr=.07*Hh; skin=P["skin"]
        c.SH.append((x,fy,0.2*Hh))
        if lie:
            y=fy-.07*Hh; poly(d,[(x-.32*Hh,y+.06*Hh),(x+.1*Hh,y+.06*Hh),(x+.1*Hh,y-.08*Hh),(x-.32*Hh,y-.06*Hh)],P["robe"],OUT,ow)
            d.ellipse((x+.1*Hh,y-.1*Hh,x+.1*Hh+2*hr,y-.1*Hh+2*hr),fill=skin,outline=OUT,width=ow); return
        a0=ph+t*7*run; legs=[]
        for k in (0,1):
            if pose=="walk": a=a0+k*math.pi; th1=.55*math.sin(a); th2=th1-.75*max(0,math.cos(a))
            else: th1=(k*2-1)*.07; th2=th1
            k1=Vv(th1,Lt,dirn); k2=Vv(th2,Ls,dirn); legs.append((k1,(k1[0]+k2[0],k1[1]+k2[1])))
        drop=max(l[1][1] for l in legs); hip=(x,fy-drop)
        lean=(.14 if run>1.2 else .06) if pose=="walk" else 0.0
        sho=(hip[0]+dirn*math.sin(lean)*Lto, hip[1]-math.cos(lean)*Lto)
        head=(sho[0]+dirn*math.sin(lean)*(.04*Hh+hr), sho[1]-(.04*Hh+hr))
        for k in (1,0):
            kn=(hip[0]+legs[k][0][0],hip[1]+legs[k][0][1]); an=(hip[0]+legs[k][1][0],hip[1]+legs[k][1][1])
            limb(d,hip,kn,.06*Hh,P["pants"],OUT,ow); limb(d,kn,an,.05*Hh,skin,OUT,ow)
            d.ellipse((an[0]-.03*Hh+dirn*.03*Hh,an[1]-.025*Hh,an[0]+.07*Hh+dirn*.03*Hh,an[1]+.025*Hh),fill=P["sandal"])
        sway=.03*Hh*math.sin(a0) if pose=="walk" else 0; hem=hip[1]+.19*Hh; rw=.12*Hh
        robe=[(sho[0]-.09*Hh,sho[1]),(sho[0]+.09*Hh,sho[1]),(hip[0]+rw+sway,hem),(hip[0]-rw-sway,hem)]
        poly(d,robe,P["robe"],OUT,ow)
        if shade: poly(d,[(sho[0]+dirn*.0*Hh,sho[1]),(sho[0]+dirn*.09*Hh,sho[1]),(hip[0]+dirn*(rw+sway),hem),(hip[0],hem)],P["robe_dark"])
        d.rectangle((hip[0]-.1*Hh,hip[1]-.05*Hh,hip[0]+.1*Hh,hip[1]-.0*Hh),fill=P["accent"])
        def arm(k,mode):
            if mode=="sword": au=1.5+.3*sw; af=1.9+.4*sw
            elif mode=="guard": au=-.5; af=-.15
            elif mode=="point": au=1.65; af=1.7
            elif pose=="walk": au=(-.62 if k==0 else .62)*math.sin(a0)*(1+.4*(run-1)); af=au+.45+.25*(run-1)
            else: au=(k*2-1)*.1; af=au+.15
            e=Vv(au,Lu,dirn); el=(sho[0]+e[0],sho[1]+e[1]); w_=Vv(af,Lf,dirn); wr=(el[0]+w_[0],el[1]+w_[1])
            limb(d,sho,el,.055*Hh,P["robe"] if k==0 or not shade else P["robe_dark"],OUT,ow); limb(d,el,wr,.045*Hh,skin,OUT,ow)
            if mode=="sword":
                ph_=2.3+.7*sw; L=.38*Hh; cl=[]
                for i in range(9):
                    u=i/8; ang=ph_-0.35*u; v=Vv(ang,L*u,dirn); cl.append((wr[0]+v[0],wr[1]+v[1]))
                left=[]; right=[]
                for i,(px,py) in enumerate(cl):
                    u=i/8; wd=.016*Hh*(1-.65*u)+.002*Hh; left.append((px,py-wd)); right.append((px,py+wd))
                poly(d,left+right[::-1],(226,231,240),(70,76,90) if OUT is None else OUT,max(1,ow))
                d.line([(wr[0]-dirn*.02*Hh,wr[1]-.03*Hh),(wr[0]+dirn*.02*Hh,wr[1]+.03*Hh)],fill=(212,170,60),width=max(2,int(.018*Hh)))
        arm(1,"guard" if sw is not None else "n")
        arm(0,"sword" if sw is not None else ("point" if point else "n"))
        d.ellipse((head[0]-hr,head[1]-hr,head[0]+hr,head[1]+hr),fill=skin,outline=OUT,width=ow)
        kind=P["head"]
        if kind=="turban":
            d.ellipse((head[0]-hr*1.12,head[1]-hr*1.25,head[0]+hr*1.12,head[1]+hr*.2),fill=P["accent"],outline=OUT,width=ow)
            d.line([(head[0]-hr*1.0,head[1]-hr*.45),(head[0]+hr*1.0,head[1]-hr*.2)],fill=lerp(P["accent"],(0,0,0),.25),width=max(1,int(hr*.2)))
        else:
            poly(d,[(head[0]-dirn*hr*0.2,head[1]-hr*1.25),(head[0]+dirn*hr*1.05,head[1]-hr*.4),(head[0]+dirn*hr*1.0,head[1]+hr*.3),(head[0]-dirn*hr*1.5,head[1]+hr*1.9),(head[0]-dirn*hr*1.3,head[1]-hr*.6)],P["accent"],OUT,ow)
            d.arc((head[0]-hr*1.05,head[1]-hr*1.3,head[0]+hr*1.05,head[1]-hr*.1),180,360,fill=(30,26,30),width=max(2,int(hr*.28)))
        if face:
            d.ellipse((head[0]+dirn*hr*.35-hr*.12,head[1]-hr*.12,head[0]+dirn*hr*.35+hr*.12,head[1]+hr*.12),fill=(30,24,24))
            d.chord((head[0]-hr*.85,head[1]-hr*.15,head[0]+hr*.85,head[1]+hr*1.15),0,180,fill=P["beard"])
    return fig
def make_camel(flat_fig,opts):
    def camel(c,x,fy,s,dirn=-1,ph=0.0,rider=False):
        d=c.dF; t=c.t; col=opts["camel"]; dk=lerp(col,(0,0,0),.3); OUT=opts.get("outline"); ow=3 if OUT else 0; by=fy-108*s; c.SH.append((x,fy,70*s))
        for k,(lx,pp) in enumerate(((-52,0),(-30,2.2),(30,1.1),(52,3.3))):
            a=.45*math.sin(t*6+ph+pp); kn=(x+lx*s+math.sin(a)*22*s,by+48*s); an=(kn[0]+math.sin(a-.5*max(0,math.cos(t*6+ph+pp)))*26*s,fy)
            cc=dk if k in(1,3) else col; limb(d,(x+lx*s,by+22*s),kn,13*s,cc,OUT,ow); limb(d,kn,an,10*s,cc,OUT,ow)
        d.ellipse((x-68*s,by-34*s,x+68*s,by+36*s),fill=col,outline=OUT,width=ow); d.ellipse((x-50*s,by+6*s,x+50*s,by+34*s),fill=dk)
        d.ellipse((x-30*s,by-70*s,x+14*s,by-18*s),fill=col,outline=OUT,width=ow)
        d.rectangle((x-40*s,by-30*s,x+22*s,by-8*s),fill=opts["blanket"])
        nb=(x+dirn*58*s,by-8*s); nt=(x+dirn*96*s,by-84*s)
        limb(d,nb,nt,26*s,col,OUT,ow); d.ellipse((nt[0]-16*s+dirn*10*s,nt[1]-14*s,nt[0]+16*s+dirn*10*s,nt[1]+14*s),fill=col,outline=OUT,width=ow)
        d.ellipse((nt[0]+dirn*30*s-8*s,nt[1]-6*s,nt[0]+dirn*30*s+8*s,nt[1]+10*s),fill=dk); d.ellipse((nt[0]+dirn*4*s,nt[1]-4*s,nt[0]+dirn*4*s+6*s,nt[1]+2*s),fill=(30,24,24))
        if rider: flat_fig(c,x-8*s,by-30*s,0.62*s*1.3,B.GOLD,pose="stand",dirn=dirn)
    return camel
def make_flag(opts):
    OUT=opts.get("outline")
    def flag(c,x,y,col,s=1.0):
        d=c.dF; d.line([(x,y),(x,y-200*s)],fill=(70,60,60),width=max(3,int(5*s)))
        t=c.t; pts=[(x+i*7*s,y-196*s+9*math.sin(t*6-i*0.55)*s) for i in range(13)]; p2=[(px,py+66*s) for px,py in pts]
        poly(d,pts+p2[::-1],col,OUT,3)
    return flag
# ---------------- СТИЛЬ 1: вектор + параллакс ----------------
def setup_vector():
    MUS=(58,112,200); QUR=(176,60,54); GOLD=(232,178,62)
    pal={MUS:dict(robe=(240,234,214),robe_dark=(204,194,170),accent=(58,112,200),skin=(222,172,130),pants=(70,58,52),sandal=(120,80,50),beard=(60,40,30),head="turban"),
         QUR:dict(robe=(176,60,54),robe_dark=(138,44,42),accent=(228,198,142),skin=(214,160,118),pants=(60,46,44),sandal=(110,70,44),beard=(40,28,26),head="cloth"),
         GOLD:dict(robe=(232,178,62),robe_dark=(196,142,40),accent=(110,64,40),skin=(222,172,130),pants=(70,58,52),sandal=(120,80,50),beard=(60,40,30),head="turban"),
         "default":dict(robe=(220,220,220),robe_dark=(180,180,180),accent=(100,100,100),skin=(222,172,130),pants=(60,50,50),sandal=(110,70,44),beard=(60,40,30),head="turban")}
    opts=dict(pal=pal,camel=(214,170,112),blanket=(58,112,200),face=True,shade=True)
    B.MUS,B.QUR,B.GOLD=MUS,QUR,GOLD; B.BL=(150,200,255); B.RD=(255,150,140)
    ff=make_flat(opts); B.fig=ff; B.camel=make_camel(ff,opts); B.flag=make_flag(opts)
    SKY=grad_img([(0,(14,10,36)),(520,(34,20,66)),(900,(96,48,96)),(1180,(224,114,86)),(1340,(252,190,120)),(H,(252,190,120))])
    sun=SKY.copy(); glowdot(sun,790,1290,200,(255,170,90),120); ImageDraw.Draw(sun).ellipse((700,1200,880,1380),fill=(255,226,160,255))
    rng=random.Random(5); stars=[(rng.randint(0,W),rng.randint(0,820),rng.random()*6.28) for _ in range(80)]
    def backdrop(c):
        b=sun.copy(); d=ImageDraw.Draw(b)
        for x,y,ph in stars:
            a=int(120+110*math.sin(c.t*2+ph)); d.ellipse((x-2,y-2,x+2,y+2),fill=(255,244,220,a))
        return b
    def dunes(c,speed,y0):
        d=c.dB
        for sp,yy,col in((0.12,y0-190,(148,66,96,255)),(0.3,y0-110,(112,50,82,255)),(0.6,y0-45,(78,38,68,255))):
            pts=[(x,yy-34*math.sin((x+c.t*speed*sp)/230)-18*math.sin((x+c.t*speed*sp*1.5)/90)) for x in range(0,W+20,20)]
            d.polygon(pts+[(W,H),(0,H)],fill=col)
    def set_floor(c,gy):
        c.B.alpha_composite(grad_img([(0,(110,60,70)),(120,(78,40,62)),(H-gy,(40,24,46))],W,H-gy),(0,gy)); c.dB.line([(0,gy),(W,gy)],fill=(255,184,120,160),width=3); c.gy=gy
    def moon(c,cx,cy,r):
        glowdot(c.B,cx,cy,r*1.7,(255,220,170),50); L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L); d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(252,238,200,255)); d.ellipse((cx+r*.34,cy-r*.3,cx+r*1.3,cy+r*.72),fill=(0,0,0,0)); c.B.alpha_composite(L)
    B.backdrop=backdrop; B.dunes=dunes; B.set_floor=set_floor; B.moon=moon
    B.REFLECT=False; B.BLOOM=True; B.PAPER=False; B.FILL=(40,24,46,255)
    B.CAM=lambda t:(1.1+0.012*math.sin(t*0.5),14*math.sin(t*0.35),120+8*math.sin(t*0.4))
# ---------------- СТИЛЬ 2: бумажная аппликация ----------------
def setup_paper():
    MUS=(70,140,150); QUR=(200,84,60); GOLD=(236,184,84)
    pal={MUS:dict(robe=(246,236,210),robe_dark=(246,236,210),accent=(44,112,124),skin=(238,204,166),pants=(60,80,92),sandal=(200,120,70),beard=(60,50,44),head="turban"),
         QUR:dict(robe=(200,84,60),robe_dark=(200,84,60),accent=(240,214,160),skin=(232,190,150),pants=(48,60,70),sandal=(200,120,70),beard=(50,40,36),head="cloth"),
         GOLD:dict(robe=(236,184,84),robe_dark=(236,184,84),accent=(150,76,52),skin=(238,204,166),pants=(60,80,92),sandal=(200,120,70),beard=(60,50,44),head="turban"),
         "default":dict(robe=(230,224,210),robe_dark=(230,224,210),accent=(120,120,120),skin=(238,204,166),pants=(60,70,80),sandal=(200,120,70),beard=(60,50,44),head="turban")}
    opts=dict(pal=pal,camel=(222,170,110),blanket=(44,112,124),face=False,shade=False,outline=(250,242,220),ow=1.1)
    B.MUS,B.QUR,B.GOLD=MUS,QUR,GOLD; B.BL=(150,225,230); B.RD=(255,160,130)
    ff=make_flat(opts); B.fig=ff; B.camel=make_camel(ff,opts); B.flag=make_flag(opts)
    rng=np.random.RandomState(9); base=grad_img([(0,(18,38,58)),(H,(30,64,84))],noise=2.2)
    fib=Image.new("RGBA",(W,H),(0,0,0,0)); fd=ImageDraw.Draw(fib); r=random.Random(2)
    for _ in range(500): x=r.randint(0,W); y=r.randint(0,H); L=r.randint(8,26); a=r.uniform(0,3.14); fd.line([(x,y),(x+L*math.cos(a),y+L*math.sin(a))],fill=(255,255,255,10),width=1)
    base.alpha_composite(fib); stars=[(r.randint(0,W),r.randint(0,760),r.randint(3,6)) for _ in range(46)]
    def backdrop(c):
        b=base.copy(); d=ImageDraw.Draw(b)
        for x,y,s in stars: d.rectangle((x,y,x+s,y+s),fill=(250,240,214,170))
        return b
    def layer(c,pts,col,shift=14):
        d=c.dB; sh=[(x,y-shift) for x,y in pts]; d.polygon(sh+[(W,H),(0,H)],fill=(8,16,24,130)); d.polygon(pts+[(W,H),(0,H)],fill=col)
    def dunes(c,speed,y0):
        for sp,yy,col in((0.12,y0-200,(44,100,116,255)),(0.3,y0-120,(34,84,100,255)),(0.6,y0-50,(26,68,84,255))):
            pts=[(x,yy-40*math.sin((x+c.t*speed*sp)/220)-14*math.sin((x+c.t*speed*sp*1.7)/80)) for x in range(0,W+20,20)]
            layer(c,pts,col)
    def set_floor(c,gy):
        c.B.alpha_composite(grad_img([(0,(22,56,70)),(H-gy,(16,40,54))],W,H-gy,noise=2),(0,gy)); c.dB.line([(0,gy),(W,gy)],fill=(250,242,220,120),width=3); c.gy=gy
    def moon(c,cx,cy,r):
        d=c.dB; d.ellipse((cx-r+8,cy-r+12,cx+r+8,cy+r+12),fill=(8,16,24,120)); L=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(L); ld.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(250,238,206,255)); ld.ellipse((cx+r*.34,cy-r*.3,cx+r*1.3,cy+r*.72),fill=(0,0,0,0)); c.B.alpha_composite(L)
    def chip(c,x,y,s,size,col):
        f=B.F(size,800); tw=c.dT.textlength(s,font=f); pw,ph=tw+60,size*1.9
        c.dT.rounded_rectangle((x-pw/2+6,y-ph/2+9,x+pw/2+6,y+ph/2+9),radius=14,fill=(6,12,20,150)); c.dT.rounded_rectangle((x-pw/2,y-ph/2,x+pw/2,y+ph/2),radius=14,fill=(246,234,206,255))
        c.dT.text((x,y),s,font=f,fill=(24,44,58,255),anchor="mm")
    def text(c,x,y,s,size,col=(250,242,220),w=800,glow=True):
        f=B.F(size,w); c.dT.text((x+5,y+8),s,font=f,fill=(6,12,20,150),anchor="mm"); c.dT.text((x,y),s,font=f,fill=col+(255,),anchor="mm")
    B.backdrop=backdrop; B.dunes=dunes; B.set_floor=set_floor; B.moon=moon; B.chip=chip; B.text=text
    B.REFLECT=False; B.BLOOM=False; B.PAPER=True; B.FILL=(16,40,54,255)
    B.CAM=lambda t:(1.1+0.01*math.sin(t*0.6),10*math.sin(t*0.4),120)
# ---------------- СТИЛЬ 3: изометрия / low-poly ----------------
def box(d,bx,by,w,h,dp,col,sgn=1):
    top=lerp(col,(255,255,255),.38); side=lerp(col,(0,0,0),.42); ox=dp*0.7*sgn; oy=-dp*0.45
    if sgn>0: sidef=[(bx+w,by),(bx+w+ox,by+oy),(bx+w+ox,by-h+oy),(bx+w,by-h)]
    else: sidef=[(bx,by),(bx+ox,by+oy),(bx+ox,by-h+oy),(bx,by-h)]
    d.polygon(sidef,fill=side); d.rectangle((bx,by-h,bx+w,by),fill=col)
    d.polygon([(bx,by-h),(bx+w,by-h),(bx+w+ox,by-h+oy),(bx+ox,by-h+oy)],fill=top)
def setup_iso():
    MUS=(60,150,255); QUR=(255,86,110); GOLD=(255,200,70)
    def fig(c,x,fy,s,col,ph=0.0,pose="walk",sw=None,dirn=1,run=1.0,lie=False,point=False,gcol=None):
        Hh=250*s; d=c.dF; t=c.t; c.SH.append((x,fy,0.2*Hh)); sg=dirn; skin=(255,214,170); dark=(40,44,100); dp=.1*Hh
        if lie:
            box(d,x-.3*Hh,fy,.4*Hh,.14*Hh,dp,col,sg); box(d,x+.1*Hh,fy,.14*Hh,.14*Hh,dp,skin,sg); return
        a0=ph+t*7*run; sw_=.5*math.sin(a0) if pose=="walk" else 0
        for k in (1,0):
            a=a0+k*math.pi; off=(.5*math.sin(a) if pose=="walk" else (k*2-1)*.05)*.09*Hh*dirn; lift=max(0,math.cos(a))*.05*Hh if pose=="walk" else 0
            box(d,x-.075*Hh+(k*2-1)*.01*Hh*0+off+(.07*Hh if k else 0)*0,fy-lift,.07*Hh,.27*Hh,dp*.7,dark,sg)
        ty=fy-.27*Hh; box(d,x-.11*Hh,ty,.22*Hh,.3*Hh,.12*Hh,col,sg)
        def arm(k,mode):
            ax=x+(-.17 if k else .11)*Hh
            if mode=="sword":
                bx=x+dirn*.12*Hh; by=ty-.2*Hh; ang=-(1.0+.9*sw)*dirn; L=.4*Hh; ex=bx+math.cos(ang)*L*dirn*0+dirn*math.sin(1.2+.7*sw)*L; ey=by-math.cos(1.2+.7*sw)*L
                d.polygon([(bx,by-4),(ex,ey-3),(ex,ey+3),(bx,by+4)],fill=(226,232,246)); box(d,bx-.03*Hh,by+.12*Hh,.06*Hh,.2*Hh,dp*.5,skin,sg)
            elif mode=="point": box(d,x+dirn*.14*Hh-(.03*Hh),ty-.2*Hh,.2*Hh*0+.06*Hh,.06*Hh,dp*.5,skin,sg); box(d,x+dirn*(.12*Hh),ty-.22*Hh,.2*Hh,.055*Hh,dp*.5,col,sg)
            else:
                off=((-.6 if k==0 else .6)*math.sin(a0)*.07*Hh*dirn) if pose=="walk" else 0
                box(d,ax+off,ty-.05*Hh,.055*Hh,.22*Hh,dp*.6,col,sg); box(d,ax+off,ty+.18*Hh-.05*Hh,.055*Hh,.06*Hh,dp*.6,skin,sg)
        arm(1,"n" if sw is None else "n"); 
        hy=ty-.3*Hh; box(d,x-.085*Hh,hy,.17*Hh,.17*Hh,.1*Hh,skin,sg)
        hd=PALH.get(col,(255,255,255)); box(d,x-.095*Hh,hy-.12*Hh,.19*Hh,.06*Hh,.11*Hh,hd,sg)
        arm(0,"sword" if sw is not None else ("point" if point else "n"))
    PALH={MUS:(255,255,255),QUR:(40,30,50),GOLD:(120,70,40)}
    def camel(c,x,fy,s,dirn=-1,ph=0.0,rider=False):
        d=c.dF; t=c.t; col=(238,190,120); dk=(150,110,200); c.SH.append((x,fy,70*s))
        for k,(lx,pp) in enumerate(((-52,0),(-30,2.2),(30,1.1),(52,3.3))):
            a=.45*math.sin(t*6+ph+pp); lift=max(0,math.cos(t*6+ph+pp))*14*s; box(d,x+lx*s-8*s+math.sin(a)*14*s,fy-lift,16*s,70*s,12*s,tuple(int(v*(.7 if k in(1,3) else 1)) for v in col),1)
        box(d,x-66*s,fy-70*s,132*s,60*s,70*s,col,1); box(d,x-30*s,fy-130*s,50*s,36*s,40*s,lerp(col,(255,255,255),.1),1)
        nx=x+dirn*66*s-(10*s if dirn>0 else 26*s); box(d,nx,fy-130*s,26*s,76*s,20*s,col,1); box(d,nx+dirn*14*s,fy-190*s,44*s,26*s,24*s,col,1)
        if rider: fig(c,x-8*s,fy-130*s,0.8*s,GOLD,pose="stand",dirn=dirn)
    def flag(c,x,y,col,s=1.0):
        d=c.dF; box(d,x-3*s,y,6*s,200*s,6*s,(210,210,225),1); t=c.t
        pts=[(x+i*7*s,y-196*s+9*math.sin(t*6-i*0.55)*s) for i in range(13)]; p2=[(px,py+66*s) for px,py in pts]
        d.polygon(pts+p2[::-1],fill=col); d.polygon(pts[6:]+p2[6:][::-1],fill=lerp(col,(0,0,0),.25))
    B.MUS,B.QUR,B.GOLD=MUS,QUR,GOLD; B.BL=(150,210,255); B.RD=(255,150,170); B.fig=fig; B.camel=camel; B.flag=flag
    SKY=grad_img([(0,(10,8,40)),(640,(30,16,74)),(1000,(96,36,110)),(1300,(220,90,120)),(1420,(255,150,120)),(H,(255,150,120))])
    rng=random.Random(11); stars=[(rng.randint(0,W),rng.randint(0,820),rng.random()*6.28) for _ in range(90)]
    def backdrop(c):
        b=SKY.copy(); d=ImageDraw.Draw(b)
        for x,y,ph in stars: a=int(110+110*math.sin(c.t*2+ph)); d.rectangle((x-2,y-2,x+2,y+2),fill=(255,244,230,a))
        return b
    def dunes(c,speed,y0):
        d=c.dB
        for sp,yy,col,stp in((0.12,y0-200,(120,48,128,255),70),(0.3,y0-120,(92,36,112,255),54),(0.6,y0-48,(66,28,96,255),40)):
            pts=[]; xs=list(range(-40,W+120,60))
            for x in xs:
                v=math.floor((26*math.sin((x+c.t*speed*sp)/200)+14*math.sin((x+c.t*speed*sp*1.6)/75)+40)/stp)*stp*0.9
                pts+=[(x,yy-v),(x+60,yy-v)]
            d.polygon(pts+[(W+120,H),(-40,H)],fill=col)
    _fl={}
    def floor_(gy):
        if gy not in _fl:
            h=H-gy; im=Image.new("RGBA",(W,h),(30,32,86,255)); dd=ImageDraw.Draw(im); tw,th=200,70
            for r in range(-1,h//(th//2)+3):
                for q in range(-2,W//tw+3):
                    cx=q*tw+(tw//2 if r%2 else 0); cy=r*th//2; shade=((q+r)%2)
                    col=(40,44,112) if shade else (32,34,92)
                    dd.polygon([(cx,cy-th//2),(cx+tw//2,cy),(cx,cy+th//2),(cx-tw//2,cy)],fill=col,outline=(90,130,255))
            _fl[gy]=im
        return _fl[gy]
    def set_floor(c,gy): c.B.alpha_composite(floor_(gy),(0,gy)); c.gy=gy
    def moon(c,cx,cy,r):
        glowdot(c.B,cx,cy,r*1.7,(255,220,200),55); L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L); d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,244,222,255)); d.ellipse((cx+r*.34,cy-r*.3,cx+r*1.3,cy+r*.72),fill=(0,0,0,0)); c.B.alpha_composite(L)
    B.backdrop=backdrop; B.dunes=dunes; B.set_floor=set_floor; B.moon=moon
    B.REFLECT=False; B.BLOOM=True; B.PAPER=False; B.FILL=(30,32,86,255)
    B.CAM=lambda t:(1.1+0.012*math.sin(t*0.5),14*math.sin(t*0.35),120+6*math.sin(t*0.4))
def cream_text():
    orig=B.text
    def text(c,x,y,s,size,col=(245,246,250),w=800,glow=True):
        if col==B.GOLD: col=(255,246,214)
        orig(c,x,y,s,size,col,w,glow)
    B.text=text
def setup(name):
    {"vector":setup_vector,"paper":setup_paper,"iso":setup_iso}[name]()
    if name in("vector","iso"): cream_text()
def _unused(name): {"vector":setup_vector,"paper":setup_paper,"iso":setup_iso}[name]()
