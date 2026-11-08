import sys, os, json, math, random, subprocess
sys.path.insert(0, os.getcwd())
import render as R
from render import F, W, H, FPS, BG, caption, LINES, WHITE
from PIL import Image, ImageDraw, ImageFilter
MUS=(84,170,240); QUR=(222,50,66); GOLD=(255,214,120); SAND=(176,140,90); DIM=(150,160,180)
def seg(d,p,q,w=4,c=WHITE): d.line([p,q],fill=c,width=max(1,int(w)))
def sm(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def txt(d,x,y,s,size,col=WHITE,w=800,anchor="mm"): d.text((x,y),s,font=F(size,w),fill=col,anchor=anchor,stroke_width=3,stroke_fill=(0,0,0))
def mini(d,x,fy,s,col,t,ph=0.0,sword=None,dirn=1,pose="walk",lie=False,run=1.0):
    lw=max(2,int(6*s))
    if lie:
        seg(d,(x-50*s,fy-8*s),(x+34*s,fy-8*s),lw,col); d.ellipse((x+34*s,fy-26*s,x+62*s,fy-2*s),outline=col,width=lw); return
    hip=(x,fy-62*s); neck=(x,fy-108*s)
    d.ellipse((x-13*s,neck[1]-27*s,x+13*s,neck[1]-1*s),outline=col,width=lw)
    seg(d,neck,hip,lw,col)
    sw=0.6*math.sin(t*7*run+ph) if pose=="walk" else 0.1
    for sd in(-1,1): seg(d,hip,(x+dirn*math.sin(sd*sw)*55*s,fy),lw,col)
    sh=(x,neck[1]+8*s)
    if sword is not None:
        hand=(x+dirn*34*s,sh[1]+22*s); seg(d,sh,hand,lw,col)
        tip=(hand[0]+dirn*math.cos(sword)*50*s,hand[1]+math.sin(sword)*50*s); seg(d,hand,tip,lw*0.8,(225,225,235))
        seg(d,sh,(x-dirn*20*s,sh[1]+34*s),lw,col)
    else:
        for sd in(-1,1): seg(d,sh,(x+dirn*math.sin(-sd*sw)*34*s,sh[1]+38*s),lw,col)
def camel(d,x,gy,s,t,dirn=-1,ph=0.0,col=(214,176,116)):
    lw=max(3,int(7*s)); by=gy-120*s
    d.ellipse((x-75*s,by-32*s,x+75*s,by+32*s),outline=col,width=lw)
    d.ellipse((x-22*s,by-62*s,x+22*s,by-26*s),outline=col,width=lw)
    nx=x+dirn*72*s; seg(d,(nx,by-10*s),(x+dirn*104*s,by-98*s),lw,col)
    d.ellipse((x+dirn*104*s-16*s,by-114*s,x+dirn*104*s+16*s,by-92*s),outline=col,width=lw)
    for k,lx in enumerate((-55,-25,25,55)):
        a=0.5*math.sin(t*6+ph+k*1.6); seg(d,(x+lx*s,by+26*s),(x+lx*s+math.sin(a)*34*s,gy),lw,col)
def dunes(img,t,speed,y0=1330):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for lay,(sp,yy,c) in enumerate(((0.35,y0-70,(14,20,42,255)),(1.0,y0,(10,14,30,255)))):
        pts=[(x,yy-34*math.sin((x+t*speed*sp)/170)-20*math.sin((x+t*speed*sp*1.4)/66)) for x in range(0,W+20,20)]
        d.polygon(pts+[(W,H),(0,H)],fill=c)
    img.alpha_composite(L)
def dust(d,x,y,t,n=9,dirn=1):
    for i in range(n):
        a=(t*1.3+i/n)%1; r=5+16*a; px=x-dirn*a*120; py=y-a*30
        c=int(95*(1-a)); d.ellipse((px-r,py-r,px+r,py+r),fill=(c+25,c+18,c+8))
def flag(d,x,y,t,col,s=1.0):
    seg(d,(x,y),(x,y-170*s),5,WHITE)
    pts=[(x+i*6*s,y-165*s+8*math.sin(t*6-i*0.5)*s+i*0.4*s) for i in range(0,13)]
    pts2=[(px,py+55*s) for px,py in pts]; d.polygon(pts+pts2[::-1],fill=col)
def moon(img,cx,cy,r,a=255):
    G=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(G).ellipse((cx-r*1.6,cy-r*1.6,cx+r*1.6,cy+r*1.6),fill=(255,235,170,40)); img.alpha_composite(G.filter(ImageFilter.GaussianBlur(r*0.6)))
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(250,238,200,a)); d.ellipse((cx+r*0.36,cy-r*0.22-r*0.06,cx+r*1.26,cy+r*0.78-r*0.06),fill=(0,0,0,0))
    img.alpha_composite(L)
GY=1400
def s_date(img,d,t,lt,p):
    dunes(img,t,40); moon(img,540,720-30*sm(lt/1.5),100)
    txt(d,540,1010,"17",300+10*math.sin(t*3)); txt(d,540,1170,"РАМАДАНА",96,GOLD); txt(d,540,1262,"2 ГОД ХИДЖРЫ · 624 Г.",52,WHITE)
    for i in range(7): mini(d,(i*210+t*90)%1500-120,1560,0.8,MUS,t,i*0.9)
def s_chase(img,d,t,lt,p):
    dunes(img,t,110)
    for i in range(5):
        x=760+i*200-lt*190; camel(d,x,GY,0.9,t,-1,i); dust(d,x+80,GY,t+i*.3,6,-1)
    if lt>0.4:
        for k in range(8):
            x=1250+k*70-(lt-0.4)*300; mini(d,x,GY+40,1.0,MUS,t,k*0.8,dirn=-1,run=1.4)
    txt(d,540,980,"КАРАВАН КУРАЙШИТОВ · СИРИЯ → МЕККА",34,QUR); txt(d,540,1600,"МУСУЛЬМАНЕ ИЗ МЕДИНЫ",44,MUS)
def s_turn(img,d,t,lt,p):
    dunes(img,t,90 if p<0.5 else 520)
    if p<0.5:
        q=p/0.5
        for i in range(5):
            if q<0.35: x=900+i*190-q/0.35*600; dr=-1; y=GY
            else: x=900+i*190-600+ (q-0.35)/0.65*900; dr=1; y=GY+110*sm((q-0.35)/0.3)
            camel(d,x,y,0.8,t,dr,i); dust(d,x-dr*70,y,t+i*.2,5,dr)
        for k in range(6): mini(d,170+k*60,GY+30,1.0,MUS,t,0,pose="stand")
        if q>0.4:
            for k in range(6): txt(d,170+k*60,GY-170-18*abs(math.sin(t*5+k)),"?",50,GOLD)
        txt(d,540,980,"ДРУГОЙ ПУТЬ",70,GOLD)
        if q>0.35:
            for i in range(8): seg(d,(260+i*110,GY+112),(300+i*110,GY+112),4,GOLD)
    else:
        q=(p-0.5)/0.5; x=1300-((q*3200)%1700)
        for i in range(10): yy=1100+i*60; xx=(x+i*173)%1200; seg(d,(xx,yy),(xx+160,yy),3,(80,90,110))
        camel(d,x,GY,1.0,t*2,-1); mini(d,x,GY-110,0.8,GOLD,t,pose="stand"); dust(d,x+90,GY,t,8,-1)
        d.rectangle((60,1090,260,GY),outline=QUR,width=5)
        for k in range(3): d.rectangle((80+k*60,1010+k*10,110+k*60,1090),outline=QUR,width=5)
        txt(d,160,1030,"МЕККА",34,QUR); txt(d,540,960,"ВЕСТЬ: КАРАВАН СПАСЁН",58,GOLD)
def s_army(img,d,t,lt,p):
    dunes(img,t,160)
    for row in range(4):
        for col in range(8):
            x=80+lt*125+col*95-row*20; fy=GY+row*48-30; s=0.8+row*0.08
            mini(d,x,fy,s,QUR,t,col*0.7+row,dirn=1)
        dust(d,60+lt*125,GY+row*48-30,t+row,4,1)
    lx=80+lt*125+8*95; mini(d,lx,GY-5,1.25,GOLD,t,0); flag(d,lx+30,GY-5,t,QUR,1.0)
    txt(d,540,990,"ВОЙСКО КУРАЙШИТОВ → БАДР",50,QUR); txt(d,540,1640,"АБУ ДЖАХЛЬ ПРОДОЛЖИЛ ПОХОД",40,GOLD)
def s_count(img,d,t,lt,p):
    dunes(img,t,15,1480)
    nb=int(31*sm(p/0.45)); nr=int(100*sm((p-0.45)/0.5))
    for i in range(nb):
        bump=1+0.5*max(0,1-(p-(i/31)*0.45)*14)
        mini(d,70+(i%8)*55,1020+(i//8)*62,0.35*bump,MUS,t,i,pose="stand")
    for j in range(nr):
        bump=1+0.5*max(0,1-(p-0.45-(j/100)*0.5)*14)
        mini(d,570+(j%10)*46,640+(j//10)*62,0.35*bump,QUR,t,j,pose="stand",dirn=-1)
    cb=int(313*sm(p/0.45)); cr=int(1000*sm((p-0.45)/0.5))
    txt(d,270,1400,"≈%d"%cb,120,MUS); txt(d,800,1400,"≈%d"%cr,120,QUR)
    txt(d,270,1500,"МУСУЛЬМАНЕ",44,MUS); txt(d,800,1500,"КУРАЙШИТЫ",44,QUR); txt(d,540,1650,"1 ФИГУРКА = 10 ЧЕЛОВЕК",36,DIM)
def s_wells(img,d,t,lt,p):
    gy=1250; d.rectangle((0,gy,W,H),fill=(14,18,34)); d.line([(0,gy),(W,gy)],fill=DIM,width=5)
    for k in range(5):
        x=120+k*170; cover=sm((p-(0.1+0.17*k))/0.15) if k<4 else 0
        d.rectangle((x-45,gy,x+45,gy+150),outline=DIM,width=4); d.rectangle((x-43,gy+2,x+43,gy+148),fill=(30,90,160) if k==4 else (30,90,160))
        if k<4: d.rectangle((x-43,gy+148-int(146*cover),x+43,gy+148),fill=SAND)
        if k<4 and 0<cover<1:
            for i in range(6): d.ellipse((x-4+(i*9%25)-12,gy-80+((t*400+i*60)%110),x+4+(i*9%25)-12,gy-72+((t*400+i*60)%110)),fill=SAND)
    for sp in range(14): xx=800+((sp*37+t*60)%80)-40; seg(d,(xx,gy+30+(sp*17)%100),(xx+16,gy+30+(sp*17)%100),3,(170,210,255))
    for k in range(3): mini(d,590+k*55,gy,1.3,MUS,t,k,pose="walk" if p<0.7 else "stand")
    q=sm((p-0.35)/0.5)
    for k in range(4): mini(d,1250-q*210+k*50,gy,1.0,QUR,t,k,dirn=-1)
    txt(d,540,980,"КОЛОДЦЫ БАДРА",64,GOLD); txt(d,800,1450,"ОТКРЫТ ОДИН",38,(170,210,255)); txt(d,330,1450,"ЗАКРЫТЫ",38,SAND)
def s_duel(img,d,t,lt,p):
    dunes(img,t,10)
    for k in range(3):
        cx=200+k*340; a=math.sin(t*9+k*1.3)
        mini(d,cx-55,GY+30,1.5,MUS,t,0,sword=-1.0+0.8*a,pose="stand")
        mini(d,cx+55,GY+30,1.5,QUR,t,0,sword=-1.0-0.8*a,dirn=-1,pose="stand")
        if abs(a)>0.8:
            for i in range(5): ang=random.random()*6.28; seg(d,(cx,GY-150),(cx+math.cos(ang)*28,GY-150+math.sin(ang)*28),3,GOLD)
    txt(d,540,980,"3  НА  3",110,GOLD); txt(d,540,1640,"ПОЕДИНКИ ПЕРЕД БОЕМ",44,WHITE)
def s_battle(img,d,t,lt,p):
    dunes(img,t,5); shake=0
    adv=260*sm(p/0.4)+(120*max(0,(p-0.45)/0.55) if p>0.45 else 0)
    for i in range(24):
        x=100+(i%6)*62+adv; fy=GY-30+(i//6)*50
        near=abs(x-540)<260; mini(d,x,fy,0.9,MUS,t,i,sword=(-1.0+0.9*math.sin(t*9+i)) if p>0.3 else None,pose="walk" if p<0.4 else "stand")
    for j in range(40):
        base=980-(j%8)*58; fy=GY-30+(j//8)*42; x=base-260*sm(p/0.4)+(380*max(0,(p-0.45)/0.55)**1.3)
        if p>0.5+0.3*((j*7)%40)/40: mini(d,x,fy,0.9,QUR,t,j,lie=True)
        else: mini(d,x,fy,0.9,QUR,t,j,dirn=-1,sword=(-1.0-0.9*math.sin(t*9+j)) if 0.3<p<0.6 else None,pose="walk" if (p<0.4 or p>0.55) else "stand")
    if p<0.55:
        for k in range(6):
            u=((t*0.9+k/6)%1); ax=100+u*880 if k%2==0 else 980-u*880; ay=1050-math.sin(u*math.pi)*260
            seg(d,(ax,ay),(ax+(26 if k%2==0 else -26),ay+(8 if u>0.5 else -8)),4,(235,235,245))
    if 0.35<p<0.6: shake=14*random.random()
    txt(d,540,980,"БИТВА",100,GOLD)
    if p>0.7: txt(d,540,1680,"ПОБЕДА МУСУЛЬМАН",64,MUS)
    return shake
def s_stats(img,d,t,lt,p):
    base=1350; d.line([(60,base),(1020,base)],fill=DIM,width=4)
    for k,(x,col,val,lab,st) in enumerate(((230,MUS,14,["МУСУЛЬМАНЕ","ПОГИБЛИ"],0.05),(540,QUR,70,["КУРАЙШИТЫ","ПОГИБЛИ"],0.4),(850,QUR,70,["КУРАЙШИТЫ","В ПЛЕНУ"],0.7))):
        u=sm((p-st)/0.2)
        if u<=0: continue
        h=int(val*5.6*u); d.rectangle((x-62,base-h,x+62,base),fill=col)
        txt(d,x,base-h-70,("≈" if val==70 else "")+str(int(val*u)),110,col)
        mini(d,x,base-h-150,1.0*u,col,t,pose="stand")
        if k==2: seg(d,(x-30,base-h-240),(x+30,base-h-240),5,GOLD)
        txt(d,x,base+60,lab[0],38,col); txt(d,x,base+105,lab[1],38,WHITE)
def s_teach(img,d,t,lt,p):
    dunes(img,t,5)
    d.rectangle((60,760,520,1130),outline=WHITE,width=6)
    for i in range(6):
        w=int(380*sm((p*1.4-i*0.12)/0.2)); 
        if w>0: seg(d,(90,810+i*55),(90+w,810+i*55+(10 if i%2 else -6)),5,(200,200,215))
    mini(d,640,1180,1.8,QUR,t,0,sword=-2.2+0.4*math.sin(t*5),dirn=-1,pose="stand")
    n=int(10*sm(p/0.7))
    for i in range(n):
        bump=1+0.6*max(0,1-(p-(i/10)*0.7)*10); mini(d,170+(i%5)*120,1330+(i//5)*130,0.6*bump,MUS,t,i,pose="stand")
    txt(d,830,860,str(n),240,GOLD); txt(d,830,1020,"МУСУЛЬМАН",44,MUS); txt(d,540,1640,"ГРАМОТА → СВОБОДА",56,GOLD)
def s_final(img,d,t,lt,p):
    dunes(img,t,50); moon(img,540,740,110+8*math.sin(t*2))
    txt(d,540,1010,"БАДР",230+12*math.sin(t*3),GOLD); txt(d,540,1170,"ПЕРВОЕ КРУПНОЕ СРАЖЕНИЕ",52,WHITE); txt(d,540,1240,"МУСУЛЬМАН И КУРАЙШИТОВ",52,WHITE)
    for i in range(6): mini(d,(i*230+t*100)%1500-120,1560,0.9,MUS,t,i)
    for i in range(6): mini(d,1400-((i*230+t*100)%1500),1700,0.9,QUR,t,i,dirn=-1)
SC=[s_date,s_chase,s_turn,s_army,s_count,s_wells,s_duel,s_battle,s_stats,s_teach,s_final]
def frame(t,TM):
    random.seed(int(t*FPS))
    img=Image.new("RGBA",(W,H),(0,0,0,0)); idx=0
    for i,(a,b) in enumerate(TM["lines"]):
        if t>=a-0.05: idx=i
    a,b=TM["lines"][idx]; lt=max(0,t-(a-0.05)); p=max(0,min(1,(t-a)/max(0.1,b+0.3-a)))
    d=ImageDraw.Draw(img); sh=SC[idx](img,d,t,lt,p) or 0
    z=1.12; img=img.transform((W,H),Image.AFFINE,(1/z,0,540-540/z,0,1/z,1450+(110-1450)/z)); B=BG.copy(); B.alpha_composite(img); img=B
    if lt<0.25: img=Image.blend(img,Image.new("RGBA",(W,H),(0,0,0,255)),0.6*(1-lt/0.25))
    ci=None
    for i,(a,b) in enumerate(TM["lines"]):
        nxt=TM["lines"][i+1][0]-0.04 if i+1<len(TM["lines"]) else 99
        if a-0.05<=t<=min(b+0.35,nxt): ci=(i,t-a)
    if ci: img=caption(img,LINES[ci[0]][1],min(1,(ci[1]+0.05)/0.2))
    if sh: img=img.transform((W,H),Image.AFFINE,(1,0,random.uniform(-sh,sh),0,1,random.uniform(-sh,sh)))
    return img.convert("RGB")
if __name__=="__main__":
    TM=json.load(open("timing.json"))
    if sys.argv[1]=="preview":
        ts=[(a+b)/2 for a,b in TM["lines"]]
        ims=[frame(t,TM).resize((300,533)) for t in ts]; cols=6; rows=(len(ims)+cols-1)//cols
        sh=Image.new("RGB",(300*cols,533*rows)); [sh.paste(im,((i%cols)*300,(i//cols)*533)) for i,im in enumerate(ims)]; sh.save("preview.png")
    else:
        n=int(TM["dur"]*FPS); pr=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","17","video_only.mp4"],stdin=subprocess.PIPE)
        for i in range(n): pr.stdin.write(frame(i/FPS,TM).tobytes())
        pr.stdin.close(); pr.wait()
