import cv2, numpy as np
from PIL import Image
art=cv2.imread('art_raw.png')
H,W=art.shape[:2]
hsv=cv2.cvtColor(art,cv2.COLOR_BGR2HSV)

# 1) remove Instagram UI overlays (heart, counts, comment, repost, 1/3 badge)
ui=np.zeros((H,W),np.uint8)
white=((art.min(axis=2)>200)&(hsv[...,1]<40)).astype(np.uint8)
for (x0,y0,x1,y1) in [(1030,825,1125,918),(1035,932,1120,985),(1030,1040,1125,1205),(1030,1255,1125,1440)]:
    ui[y0:y1,x0:x1]=white[y0:y1,x0:x1]
ui[40:125,1020:1135]=1   # "1/3" badge
ui=cv2.dilate(ui,np.ones((7,7),np.uint8),iterations=2)
art=cv2.inpaint(art,ui,9,cv2.INPAINT_TELEA)

# 2) erase Slap Burger marks on the bags
bags={'W1':((70,672,292,822),-1.5),'W2':((364,680,584,828),1.5),'M1':((594,548,796,706),0.0),'M2':((840,575,1054,718),2.0)}
hsv=cv2.cvtColor(art,cv2.COLOR_BGR2HSV)
for k,((x0,y0,x1,y1),_) in bags.items():
    m=np.zeros((H,W),np.uint8)
    roi=hsv[y0:y1,x0:x1]
    m[y0:y1,x0:x1]=((roi[...,1]>55)|(roi[...,2]<120)).astype(np.uint8)
    m=cv2.dilate(m,np.ones((5,5),np.uint8),iterations=2)
    art=cv2.inpaint(art,m,11,cv2.INPAINT_TELEA)
# smooth the erased patch a little so no ghosting, keep paper tone
paper=art.copy()
for k,((x0,y0,x1,y1),_) in bags.items():
    p=art[y0:y1,x0:x1]; art[y0:y1,x0:x1]=cv2.bilateralFilter(cv2.medianBlur(p,7),9,40,9)

# 3) print V&M logo onto each bag, shaded by the paper underneath
logo=Image.open('logo.png').convert('RGBA')
out=Image.fromarray(cv2.cvtColor(art,cv2.COLOR_BGR2RGB)).convert('RGBA')
for k,((x0,y0,x1,y1),rot) in bags.items():
    bw=x1-x0; lw=int(bw*0.98); lh=int(lw*logo.height/logo.width)
    L=logo.resize((lw,lh),Image.LANCZOS).rotate(-rot,resample=Image.BICUBIC,expand=True)
    cx=(x0+x1)//2; cy=(y0+y1)//2
    px,py=cx-L.width//2,cy-L.height//2
    # paper shading
    reg=np.asarray(out.crop((px,py,px+L.width,py+L.height)).convert('L')).astype(np.float32)
    shade=np.clip(reg/np.percentile(reg,80),0.72,1.06)[...,None]
    la=np.asarray(L).astype(np.float32)
    rgb=np.clip(la[...,:3]*shade,0,255)
    # slight print softness
    Lp=Image.fromarray(np.dstack([rgb,la[...,3:]*0.97]).astype(np.uint8),'RGBA')
    out.alpha_composite(Lp,(px,py))
out=out.convert('RGB')
# 4) 4:5 crop and resize for Instagram
w=int(H*0.8); out=out.crop((0,0,w,H)).resize((1080,1350),Image.LANCZOS)
out.save('vm_gta6_bags.jpg',quality=95)
