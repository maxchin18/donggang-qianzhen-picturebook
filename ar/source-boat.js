import * as THREE from 'three';

// These outlines select the ORIGINAL page pixels. No redrawn faces, uniforms,
// hulls or equipment: source x/y also determine every texture UV exactly.
let artwork;
const SW = 1536, SH = 1024;
const MAIN = {
  center: [460,260],
  hull: [[0,280],[106,271],[146,280],[394,329],[535,363],[636,345],[740,353],[807,364],[920,365],[905,452],[840,457],[786,452],[738,464],[686,449],[618,456],[557,449],[509,448],[469,445],[411,442],[354,433],[298,429],[236,419],[179,410],[118,406],[83,394],[0,384]],
  cabin: [[184,164],[323,158],[335,131],[399,137],[408,174],[470,195],[467,203],[455,207],[445,305],[371,302],[345,251],[324,229],[261,226],[214,236],[182,259],[174,222]],
  stern: [[0,237],[34,234],[59,239],[93,228],[116,246],[156,235],[181,253],[180,279],[100,273],[0,287]],
  equipment: [[712,244],[818,246],[845,257],[842,263],[827,266],[823,310],[844,306],[862,313],[882,307],[895,312],[900,363],[759,361],[744,325],[733,293],[713,281]],
  crew: [
    [[499,178],[512,171],[527,174],[543,190],[531,199],[537,213],[529,220],[538,254],[537,262],[546,275],[549,287],[535,286],[529,280],[523,306],[524,340],[505,337],[500,315],[489,333],[463,332],[460,307],[456,282],[461,263],[471,251],[461,242],[455,227],[462,211],[477,202],[490,195]],
    [[604,216],[615,212],[626,217],[631,230],[628,238],[635,248],[643,257],[649,269],[652,285],[655,334],[636,337],[618,319],[603,304],[586,291],[566,293],[558,291],[558,281],[568,267],[576,254],[590,249],[599,239]],
    [[711,247],[725,244],[739,247],[749,255],[749,262],[743,269],[751,277],[756,294],[750,311],[749,346],[728,351],[711,343],[695,346],[680,338],[684,318],[681,305],[668,302],[665,287],[677,280],[692,276],[700,266]],
  ],
  fish: [[547,282],[581,290],[610,314],[637,347],[668,399],[700,452],[719,481],[741,469],[786,459],[763,483],[748,500],[756,515],[733,508],[721,516],[708,508],[681,496],[656,479],[636,460],[611,430],[591,400],[573,371],[557,341],[545,316],[543,297]],
  poles: [
    [[[344,24],[335,145]],12], [[[342,88],[321,152]],7], [[[423,44],[415,169]],10],
    [[[347,39],[424,50]],4], [[[340,96],[421,103],[522,121],[622,143],[718,168],[807,193]],9],
    [[[465,82],[455,193]],7], [[[643,90],[627,228]],9], [[[716,148],[710,259]],9],
    [[[786,140],[782,245]],9], [[[899,215],[890,355]],10], [[[884,350],[899,216],[914,365]],5],
    [[[369,0],[361,136]],5], [[[400,0],[392,141]],4], [[[550,0],[536,149]],4],
    [[[572,0],[559,155]],5], [[[636,31],[624,162]],3], [[[681,112],[669,249]],4],
    [[[807,142],[805,252]],4], [[[14,236],[9,283],[116,270],[147,294]],5],
    [[[106,192],[102,276]],11], [[[185,150],[176,250]],11],
    [[[159,205],[158,269],[422,317],[532,342]],5],
  ],
  circles: [[345,24,11,12],[423,43,11,12],[463,78,9,11],[644,86,9,9],[785,139,11,11],
    [182,245,41,40],[312,273,62,46],[776,322,44,48],[831,336,29,31]],
  lamps: [[451,157,21,25],[488,163,21,25],[526,173,20,25],[564,181,20,25],[603,188,19,25],
    [641,196,18,24],[681,205,18,24],[721,214,18,23],[761,222,17,22],[803,231,16,21]],
};
const DISTANT = {
  center: [1260,280],
  hull: [[1040,319],[1111,320],[1208,348],[1327,353],[1455,345],[1478,337],[1463,385],[1412,394],[1348,396],[1274,397],[1203,390],[1139,392],[1080,383],[1040,370]],
  cabin: [[1131,270],[1184,266],[1208,249],[1231,250],[1228,268],[1272,282],[1266,290],[1260,342],[1215,337],[1190,314],[1140,307],[1129,314]],
  stern: [[1042,298],[1080,294],[1125,306],[1132,330],[1100,330],[1040,321]],
  equipment: [[1297,314],[1321,321],[1340,346],[1386,341],[1405,324],[1446,329],[1457,345],[1330,358],[1290,344]],
  crew: [
    [[1340,293],[1351,289],[1359,299],[1355,308],[1361,320],[1358,340],[1349,352],[1335,347],[1327,335],[1329,318],[1335,311]],
    [[1421,305],[1430,301],[1438,306],[1440,316],[1445,326],[1441,350],[1436,365],[1423,362],[1413,351],[1408,332],[1413,319]],
  ],
  poles: [
    [[[1118,243],[1108,321]],7], [[[1188,243],[1183,280]],6], [[[1202,208],[1198,267]],6],
    [[[1262,165],[1256,275]],6], [[[1297,221],[1294,284]],5], [[[1334,228],[1330,321]],5],
    [[[1370,242],[1366,325]],5], [[[1406,257],[1400,338]],6], [[[1115,247],[1408,256]],5],
    [[[1219,183],[1214,249]],3], [[[1227,157],[1223,251]],3], [[[1278,167],[1272,278]],3],
    [[[1311,213],[1304,292]],3], [[[1410,294],[1422,347]],4],
    [[[1044,298],[1120,305],[1233,346],[1457,347]],4],
  ],
  circles: [[1262,164,6,8],[1189,242,6,8],[1370,241,6,7],[1406,257,5,7],
    [1125,327,25,22],[1171,342,35,26],[1313,347,24,25],[1258,260,15,14]],
  lamps: [[1268,265,10,15],[1286,268,10,15],[1305,270,10,15],[1323,272,10,15],
    [1342,274,10,15],[1360,276,10,15],[1378,278,10,15],[1396,280,10,15]],
};

function ellipse(cx, cy, rx, ry) {
  return Array.from({length:32},(_,i)=>[cx+Math.cos(i/32*Math.PI*2)*rx,cy+Math.sin(i/32*Math.PI*2)*ry]);
}

// Rounded, CLOSED relief volumes. Every front/back/edge vertex uses the
// original x/y UV, so the normal view preserves the illustration exactly.
function reliefGeometry(points, center, thickness, levels) {
  const contour=points.map(([x,y])=>new THREE.Vector2((x-center[0])/SW,(center[1]-y)/SW));
  let xy=contour.map(p=>[p.x,p.y]),triangles=THREE.ShapeUtils.triangulateShape(contour,[]);
  const used=[...new Set(triangles.flat())].sort((a,b)=>a-b),remap=new Map(used.map((v,i)=>[v,i]));
  xy=used.map(i=>xy[i]);triangles=triangles.map(t=>t.map(i=>remap.get(i)));
  const edgeKey=(a,b)=>a<b?`${a},${b}`:`${b},${a}`;
  let edges=new Map();
  triangles.forEach(t=>t.forEach((a,i)=>{const key=edgeKey(a,t[(i+1)%3]);edges.set(key,(edges.get(key)||0)+1);}));
  let boundary=new Set([...edges].filter(([,n])=>n===1).map(([key])=>key));
  let boundaryVertices=new Set([...boundary].flatMap(key=>key.split(',').map(Number)));
  for(let pass=0;pass<levels;pass++){
    const mids=new Map(),nextBoundary=new Set(),next=[];
    const mid=(a,b)=>{
      const key=edgeKey(a,b);if(mids.has(key))return mids.get(key);
      const index=xy.length;xy.push([(xy[a][0]+xy[b][0])/2,(xy[a][1]+xy[b][1])/2]);mids.set(key,index);
      if(boundary.has(key)){boundaryVertices.add(index);nextBoundary.add(edgeKey(a,index));nextBoundary.add(edgeKey(b,index));}
      return index;
    };
    triangles.forEach(([a,b,c])=>{const ab=mid(a,b),bc=mid(b,c),ca=mid(c,a);next.push([a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]);});
    triangles=next;boundary=nextBoundary;
  }
  const distance=([x,y])=>{
    let d=Infinity;
    for(let i=0;i<contour.length;i++){
      const a=contour[i],b=contour[(i+1)%contour.length],dx=b.x-a.x,dy=b.y-a.y;
      const t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));
      d=Math.min(d,Math.hypot(x-a.x-t*dx,y-a.y-t*dy));
    }return d;
  };
  const distances=xy.map(distance),maxDistance=Math.max(...distances,1e-8),position=[],uv=[],front=[],walls=[];
  xy.forEach(([x,y],i)=>{position.push(x,y,.0015+(boundaryVertices.has(i)?0:thickness*Math.pow(distances[i]/maxDistance,.65)));uv.push((x*SW+center[0])/SW,1-(center[1]-y*SW)/SH);});
  xy.forEach(([x,y])=>{position.push(x,y,-.002);uv.push((x*SW+center[0])/SW,1-(center[1]-y*SW)/SH);});
  const n=xy.length;
  triangles.forEach(([a,b,c])=>{
    if((xy[b][0]-xy[a][0])*(xy[c][1]-xy[a][1])-(xy[b][1]-xy[a][1])*(xy[c][0]-xy[a][0])<0)[b,c]=[c,b];
    front.push(a,b,c,a+n,c+n,b+n);
    [[a,b],[b,c],[c,a]].forEach(([u,v])=>{if(boundary.has(edgeKey(u,v)))walls.push(v,u,u+n,v,u+n,v+n);});
  });
  const index=[...front,...walls],audit=new Map();
  for(let i=0;i<index.length;i+=3)for(let j=0;j<3;j++){
    const key=edgeKey(index[i+j],index[i+(j+1)%3]);audit.set(key,(audit.get(key)||0)+1);
  }
  if([...audit.values()].some(n=>n!==2))throw new Error('Source relief has an open/nonmanifold edge');
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(position,3));
  geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geo.setIndex(index);
  geo.addGroup(0,front.length,0);geo.addGroup(front.length,walls.length,1);geo.computeVertexNormals();
  geo.userData.closed=true;geo.userData.reliefDepth=thickness;
  return geo;
}

function animateArt(mat, time, kind, center) {
  mat.onBeforeCompile = shader => {
    shader.uniforms.uArtTime = time;
    shader.uniforms.uArtKind = {value:kind};
    shader.uniforms.uArtCenter = {value:new THREE.Vector2(...center)};
    shader.vertexShader = `uniform float uArtTime; uniform float uArtKind; uniform vec2 uArtCenter;\n` +
      shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
        vec2 pixel=vec2(uv.x*1536.0,(1.0-uv.y)*1024.0);
        if(uArtKind>1.5){
          float tail=clamp((pixel.y-330.0)/175.0,0.0,1.0);
          transformed.x+=sin(uArtTime*5.2-pixel.y*.012)*.0065*tail*tail;
          transformed.y+=sin(uArtTime*3.5)*.0022*tail;
          transformed.z+=sin(uArtTime*4.5)*.006*tail;
        }else if(uArtKind>.5){
          float hands=exp(-dot((pixel-uArtCenter)/vec2(32.0,27.0),(pixel-uArtCenter)/vec2(32.0,27.0)));
          transformed.y+=sin(uArtTime*1.9)*.0025*hands;
          transformed.x+=sin(uArtTime*1.9)*.0018*hands;
          transformed.z+=sin(uArtTime*1.9)*.002*hands;
        }
      `);
  };
}

export async function buildSourceBoat(parent, distant=false) {
  if (!artwork) artwork = new THREE.TextureLoader().loadAsync('../assets/pages/p02.webp').then(tex=>{
    tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=4;return tex;
  }).catch(e=>{artwork=null;throw e;});
  const texture=await artwork, def=distant?DISTANT:MAIN;
  const holder=new THREE.Group(),boat=new THREE.Group();holder.add(boat);parent.add(holder);
  holder.position.set(def.center[0]/SW-.5,(SH/2-def.center[1])/SW,0);
  boat.name=distant?'distant-original-boat':'main-original-boat';
  const pieces=[],time={value:0};
  function piece(points,name,z,kind=0,hand=[0,0]) {
    const major=kind||['original-hull','original-cabin','original-deck','original-stern'].includes(name);
    const thickness=(kind===1?.025:kind===2?.014:name==='original-hull'?.032:name==='original-cabin'?.024:major?.018:.004)*(distant?.55:1);
    const geo=reliefGeometry(points,def.center,thickness,major?2:1);
    const mat=new THREE.MeshBasicMaterial({map:texture,transparent:true,opacity:0});
    const side=new THREE.MeshStandardMaterial({map:texture,color:0xb3c6d1,roughness:1,transparent:true,opacity:0});
    if(kind){animateArt(mat,time,kind,hand);animateArt(side,time,kind,hand);}
    const mesh=new THREE.Mesh(geo,[mat,side]);mesh.name=name;mesh.position.z=z;boat.add(mesh);pieces.push(mesh);
    if(kind===1||name==='original-fishing-lamp'){
      const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
      const pivotX=((Math.min(...xs)+Math.max(...xs))/2-def.center[0])/SW;
      const pixelY=kind===1?Math.max(...ys)-5:Math.min(...ys)-10;
      const pivotY=(def.center[1]-pixelY)/SW;
      geo.translate(-pivotX,-pivotY,0);mesh.position.x=pivotX;mesh.position.y=pivotY;
    }
    mesh.userData.sourcePixels=true;mesh.userData.sourceCenter=def.center;
    return mesh;
  }
  function strip(points,width,z=.002) {
    for(let i=1;i<points.length;i++){
      const [ax,ay]=points[i-1],[bx,by]=points[i],length=Math.hypot(bx-ax,by-ay);
      const dx=-(by-ay)/length*width/2,dy=(bx-ax)/length*width/2;
      piece([[ax+dx,ay+dy],[bx+dx,by+dy],[bx-dx,by-dy],[ax-dx,ay-dy]],'original-rigging',z);
    }
  }
  def.poles.forEach(([p,w])=>strip(p,w));
  def.circles.forEach(p=>piece(ellipse(...p),'original-equipment',.003));
  piece(def.stern,'original-stern',.004);
  piece(def.cabin,'original-cabin',.005);
  piece(def.equipment,'original-deck',.006);
  const crew=def.crew.map((p,i)=>piece(p,`${distant?'distant':'main'}-fisherman-${i+1}`,.008,1,
    distant?[1350+i*77,334]:[[532,276],[617,299],[714,334]][i]));
  def.lamps.forEach(([x,y,rx,ry])=>{
    strip([[x,y-ry-22],[x,y-ry+2]],3,.003);
    piece(ellipse(x,y,rx,ry),'original-fishing-lamp',.004);
  });
  piece(def.hull,'original-hull',.011);
  const tuna=def.fish?piece(def.fish,'original-hanging-tuna',.014,2):null;
  // Original railings and original hauling ropes; preserve their source pixels.
  if(!distant){
    strip([[6,250],[142,268],[356,308],[531,350]],5,.013);
    [149,205,260,313,367,418,469,517].forEach((x,i)=>strip([[x,271+i*10],[x-2,294+i*10]],4,.013));
    strip([[530,279],[548,302]],4,.015);
    strip([[769,359],[802,437],[879,488]],6,.013);
  }else strip([[1361,340],[1395,397],[1428,429]],4,.012);
  return {
    holder,boat,crew,tuna,texture,pieces,sourceCenter:def.center,
    fishing:{source:true},
    update(t){
      const k=Math.max(0,Math.min(1,t/2.2)),smooth=k*k*(3-2*k);
      time.value=Math.max(0,t);
      holder.position.z=.045*smooth+Math.sin(t*1.25)*.0025*smooth;
      holder.rotation.z=Math.sin(t*.85)*.0035*smooth;
      crew.forEach((p,i)=>{p.rotation.x=Math.sin(t*1.65+i*.4)*.07*smooth;p.rotation.z=Math.sin(t*1.65+i*.4)*.028*smooth;});
      pieces.forEach((p,i)=>{
        p.material.forEach(m=>{m.opacity=smooth;});
        if(p.name==='original-fishing-lamp')p.rotation.z=Math.sin(t*1.3+i*.3)*.035*smooth;
      });
    },
  };
}
