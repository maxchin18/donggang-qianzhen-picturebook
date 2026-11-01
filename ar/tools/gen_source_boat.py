"""Union original-art outlines into ONE continuous, closed surface per boat.

Dependencies: numpy shapely triangle. Run from any directory. Source artwork is
never edited. Thin rigging stays vector-based; holes remain transparent.
"""
from pathlib import Path
from collections import Counter
import json, base64
import numpy as np
import triangle
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely import set_precision

ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'ar/p02/source-boat-shapes.json'
OUT=ROOT/'ar/p02/source-boat-meshes.json'


def ellipse(p):
    x,y,rx,ry=p
    a=np.linspace(0,2*np.pi,48,endpoint=False)
    return Polygon(np.column_stack((x+np.cos(a)*rx,y+np.sin(a)*ry)))


def build(name,d):
    rigid=set_precision(unary_union([Polygon(d[key]).buffer(0) for key in ['hull','cabin','stern','equipment']]),.01)
    people=[set_precision(Polygon(p).buffer(0),.01) for p in d['crew']]
    shapes=[rigid,*people]
    # The hauled tuna is now a separate COMPLETE fish mesh. Do not leave its
    # old cropped tail/waves in the vessel surface.
    shapes += [LineString(p).buffer(w/2,cap_style='square',join_style='round') for p,w in d['poles']]
    shapes += [ellipse(p) for p in d['circles']+d['lamps']]
    for x,y,rx,ry in d['lamps']:
        shapes.append(LineString([(x,y-ry-22),(x,y-ry+2)]).buffer(1.5))
    if name=='main':
        for p,w in [([[6,250],[142,268],[356,308],[531,350]],5),([[530,279],[548,302]],4),([[769,359],[802,437],[879,488]],6)]:
            shapes.append(LineString(p).buffer(w/2))
        for i,x in enumerate([149,205,260,313,367,418,469,517]):
            shapes.append(LineString([(x,271+i*10),(x-2,294+i*10)]).buffer(2))
    else: shapes.append(LineString([(1361,340),(1395,397),(1428,429)]).buffer(2))
    union=set_precision(unary_union(shapes).buffer(0),.01)
    components=list(union.geoms) if union.geom_type=='MultiPolygon' else [union]
    # All anatomical landmarks must belong to the same connected painted region.
    landmarks=[[514,174],[492,191],[538,207],[527,218],[543,190],[548,200]] if name=='main' else []
    if landmarks:
        owner=next(p for p in components if p.covers(Point(514,174)))
        assert all(owner.covers(Point(*p)) for p in landmarks),'Incomplete left fisherman head'
    all_xy=[];all_tri=[]
    for poly in components:
        if poly.area<.05:continue
        # Preserve the INTERNAL hull and person boundaries too. Without these
        # constraints a triangle can carry a moving sleeve across painted hull
        # pixels even when its hull-side vertex has zero skin weight.
        lines=unary_union([poly.boundary,rigid.boundary.intersection(poly),
                          *[p.boundary.intersection(poly) for p in people]])
        vertices=[];segments=[];lookup={}
        for line in (list(lines.geoms) if hasattr(lines,'geoms') else [lines]):
            if line.geom_type!='LineString':continue
            indices=[]
            for x,y in line.coords:
                key=(round(x,7),round(y,7))
                if key not in lookup:lookup[key]=len(vertices);vertices.append((x,y))
                indices.append(lookup[key])
            segments.extend((a,b) for a,b in zip(indices,indices[1:]) if a!=b)
        holes=[list(Polygon(r).representative_point().coords)[0] for r in poly.interiors]
        data={'vertices':np.array(vertices),'segments':np.array(segments)}
        if holes:data['holes']=np.array(holes)
        # Internal crew/rigging intersections can make acute subpixel angles.
        # Area refinement is sufficient here; angle refinement can endlessly
        # split those constraints without improving a single rendered pixel.
        mesh=triangle.triangulate(data,'pa24Q')
        offset=len(all_xy);all_xy.extend(mesh['vertices'].tolist());all_tri.extend((mesh['triangles']+offset).tolist())
    xy=np.array(all_xy);tri=np.array(all_tri,dtype=np.uint32)
    # Semantic skin weights only cover the painted crew, never hull/cabin or
    # the background around them. Blend at their fixed contact with the boat.
    skin=np.zeros((len(xy),4),dtype='<f4');lamps=unary_union([ellipse(p) for p in d['lamps']])
    rigid_skin=rigid.buffer(1e-6);person_skin=[p.buffer(1e-6) for p in people];lamp_skin=lamps.buffer(1e-6)
    for i,(x,y) in enumerate(xy):
        point=Point(x,y)
        distance=rigid.distance(point)
        if rigid_skin.covers(point) or distance<.02:continue
        k=np.clip(distance/10,0,1);k=k*k*(3-2*k)
        for j,person in enumerate(person_skin):
            if person.covers(point) or person.distance(point)<.02:skin[i,j]=k
        if not skin[i,:3].any() and (lamp_skin.covers(point) or lamp_skin.distance(point)<.02):skin[i,3]=1
    # No triangle painted as rigid boat may be influenced by a crew member.
    rigid_triangles=0
    for indices in tri:
        if rigid.contains(Point(*xy[indices].mean(axis=0))):
            rigid_triangles+=1
            assert np.max(skin[indices])==0,('Crew weights leaked into rigid hull',xy[indices].tolist(),skin[indices].tolist())
    # Continuous depth field, independent of the original cutout pieces.
    def gauss(cx,cy,rx,ry):return np.exp(-(((xy[:,0]-cx)/rx)**2+((xy[:,1]-cy)/ry)**2))
    if name=='main':
        depth=.004+.018*gauss(450,370,490,110)+.014*gauss(325,220,145,100)
        for cx,cy in [(510,247),(610,277),(715,298)]:depth += .018*gauss(cx,cy,45,76)
    else:
        depth=.004+.012*gauss(1260,350,260,70)+.009*gauss(1210,290,85,60)
        for cx,cy in [(1347,320),(1428,332)]:depth += .011*gauss(cx,cy,22,36)
    center=d['center'];n=len(xy)
    front=np.column_stack(((xy[:,0]-center[0])/1536,(center[1]-xy[:,1])/1536,depth))
    back=front.copy();back[:,2]=-.004
    pos=np.concatenate((front,back)).astype('<f4')
    uv=np.column_stack((xy[:,0]/1536,1-xy[:,1]/1024)).astype('<f4');uv=np.concatenate((uv,uv))
    edges=Counter();directed={};faces=[]
    for a,b,c in tri.tolist():
        ab=front[b,:2]-front[a,:2];ac=front[c,:2]-front[a,:2]
        if ab[0]*ac[1]-ab[1]*ac[0]<0:b,c=c,b
        faces.extend((a,b,c,a+n,c+n,b+n))
        for u,v in [(a,b),(b,c),(c,a)]:key=tuple(sorted((u,v)));edges[key]+=1;directed[key]=(u,v)
    front_count=len(faces)
    for key,count in edges.items():
        if count==1:
            u,v=directed[key];faces.extend((v,u,u+n,v,u+n,v+n))
    faces=np.array(faces,dtype='<u4' if len(pos)>65535 else '<u2');audit=Counter()
    for a,b,c in faces.reshape(-1,3).tolist():
        audit.update([tuple(sorted((a,b))),tuple(sorted((b,c))),tuple(sorted((c,a)))])
    assert all(n==2 for n in audit.values()),'Open/nonmanifold surface'
    def enc(a):return base64.b64encode(a.tobytes()).decode()
    print(f'{name}: {len(pos)} vertices, {len(faces)//3} triangles, open edges=0, protected head landmarks={len(landmarks)}')
    fish_outline=[]
    if d.get('fish'):
        protected=Polygon(d['fish']).buffer(0).buffer(18,join_style='round').simplify(1.2)
        if protected.geom_type=='MultiPolygon':protected=max(protected.geoms,key=lambda p:p.area)
        tolerance=1.2
        while len(protected.exterior.coords)>65:
            tolerance+=.25;protected=protected.simplify(tolerance)
        fish_outline=[list(p) for p in list(protected.exterior.coords)[:-1]]
    head_outline=[[493, 182], [501, 175], [512, 171], [524, 170], [535, 173], [542, 178], [547, 185], [547, 193], [552, 198], [553, 203], [542, 203], [541, 209], [536, 215], [530, 219], [540, 225], [542, 233], [530, 226], [510, 218], [504, 207], [497, 199], [490, 195], [490, 188]] if name=='main' else []
    print(f'  rigid triangles={rigid_triangles}, maximum rigid skin weight=0')
    return dict(p=enc(pos),u=enc(uv),s=enc(np.concatenate((skin,skin))),i=enc(faces),i32=len(pos)>65535,frontCount=front_count,center=center,landmarks=landmarks,fishOutline=fish_outline,headOutline=head_outline,
                rigidShapes=[d[key] for key in ['hull','cabin','stern','equipment']],crewShapes=d['crew'],
                crew=[[505,330,510,248,68,115,532,276],[612,334,610,277,58,95,617,299],[716,350,715,299,58,98,714,334]] if name=='main' else [[1348,350,1346,320,30,55,1350,334],[1427,362,1428,332,30,55,1427,334]])


if __name__=='__main__':
    spec=json.loads(SPEC.read_text(encoding='utf-8'))
    OUT.write_text(json.dumps({k:build(k,v) for k,v in spec.items()},separators=(',',':')),encoding='utf-8')
