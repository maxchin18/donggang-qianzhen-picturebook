import numpy as np, cv2, json, base64, sys
from PIL import Image
TH={'tuna_big':0.2,'tuna_m':0.2,'tuna_r':0.2,'gull1':0.12,'gull2':0.12,'boat2':0.12}
out={}
for name,tk in TH.items():
    im=np.array(Image.open(f'ar/p02/{name}.png').convert('RGBA'))
    H,W=im.shape[:2]; N=84
    cols=N if W>=H else max(8,round(N*W/H)); rows=round(cols*H/W)
    a=cv2.resize(im[:,:,3],(cols+1,rows+1),interpolation=cv2.INTER_AREA)
    mask=(a>110).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(mask); big=st[1:,4].max(); keep=np.zeros_like(mask)
    for i in range(1,n):
        if st[i,4]>=0.05*big: keep[lab==i]=1
    mask=keep
    dt=cv2.distanceTransform(mask,cv2.DIST_L2,5); dt=cv2.GaussianBlur(dt,(5,5),0)*mask; md=dt.max()
    verts=cv2.dilate(mask,np.ones((3,3),np.uint8))>0
    hp=H/W; idx=-np.ones(verts.shape,int); pos=[]; uv=[]
    for j in range(rows+1):
        for i in range(cols+1):
            if verts[j,i]:
                idx[j,i]=len(pos); pos.append((i/cols-0.5,(0.5-j/rows)*hp,tk*hp*np.sqrt(max(dt[j,i],0)/md))); uv.append((i/cols,1-j/rows))
    nf=len(pos); tris=[]
    for j in range(rows):
        for i in range(cols):
            q=[idx[j,i],idx[j,i+1],idx[j+1,i+1],idx[j+1,i]]
            if min(q)<0: continue
            tris+=[q[0],q[3],q[2],q[0],q[2],q[1]]
    bt=[]
    for k in range(0,len(tris),3): a_,b_,c_=tris[k:k+3]; bt+=[a_+nf,c_+nf,b_+nf]
    P=np.array(pos+[(x,y,-z) for x,y,z in pos],np.float32).ravel(); U=np.array(uv+uv,np.float32).ravel(); I=np.array(tris+bt,np.uint16).ravel()
    out[name]=dict(p=base64.b64encode(P.tobytes()).decode(),u=base64.b64encode(U.tobytes()).decode(),i=base64.b64encode(I.tobytes()).decode(),i32=False,ratio=hp)
json.dump(out,open('ar/p02/meshes.json','w'))
