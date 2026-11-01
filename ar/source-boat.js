import * as THREE from 'three';

// One unioned, closed surface per vessel: each original pixel exists once.
// Shared continuous deformation prevents faces, fins and tails from being
// sliced by independently moving overlapping cutouts.
let artwork,meshData,repairImage;
const decode=(s,T)=>{const raw=atob(s),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);return new T(bytes.buffer);};
const ready=t=>{const k=Math.max(0,Math.min(1,t/2.2));return k*k*(3-2*k);};

function rigMaterial(mat,rig){
  mat.onBeforeCompile=shader=>{
    shader.uniforms.uArtTime=rig.time;shader.uniforms.uArtReady=rig.ready;
    shader.uniforms.uArtCenter={value:rig.center};shader.uniforms.uDistant={value:rig.distant?1:0};
    shader.uniforms.uCrewPivot={value:rig.pivots};shader.uniforms.uCrewField={value:rig.fields};
    shader.uniforms.uCrewPose={value:rig.poses};shader.uniforms.uCrewHands={value:rig.hands};shader.uniforms.uCrewHeads={value:rig.heads};
    shader.vertexShader=`
      uniform float uArtTime,uArtReady,uDistant;
      uniform vec2 uArtCenter;
      uniform vec4 uCrewPivot[3],uCrewField[3],uCrewPose[3],uCrewHands[3],uCrewHeads[3];
      vec2 sourceRotate(vec2 p,float a){return vec2(p.x*cos(a)-p.y*sin(a),p.x*sin(a)+p.y*cos(a));}
    `+shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
      vec2 pixel=vec2(uv.x*1536.0,(1.0-uv.y)*1024.0);
      vec2 moved=pixel;float lift=0.0;float protectedHead=0.0;
      for(int i=0;i<3;i++){
        vec4 field=uCrewField[i];
        float radius=length((pixel-field.xy)/field.zw);
        float weight=(1.0-smoothstep(1.02,1.65,radius))*uCrewPivot[i].z;
        for(int j=0;j<3;j++){
          float head=(1.0-smoothstep(1.0,1.25,length((pixel-uCrewHeads[j].xy)/uCrewHeads[j].zw)))*uCrewPivot[j].z;
          protectedHead=max(protectedHead,head);if(j!=i)weight*=1.0-head;
        }
        vec2 delta=pixel-uCrewPivot[i].xy;
        moved+=(sourceRotate(delta,uCrewPose[i].x)-delta)*weight;
        lift+=-delta.y/1536.0*sin(uCrewPose[i].y)*weight;
        vec2 hand=(pixel-uCrewHands[i].xy)/uCrewHands[i].zw;
        float grip=exp(-dot(hand,hand))*weight;
        moved+=vec2(-4.5,-6.0)*uCrewPose[i].z*grip;
        lift+=(.065*uArtReady+uCrewPose[i].z*.003)*grip;
      }
      float lamps=exp(-pow((pixel.y-(uDistant>.5?271.0:190.0))/29.0,2.0));
      moved.x+=sin(uArtTime*1.3+pixel.x*.012)*.9*lamps*(1.0-protectedHead)*uArtReady;
      transformed.xy=vec2((moved.x-uArtCenter.x)/1536.0,(uArtCenter.y-moved.y)/1536.0);
      transformed.z+=lift;
    `);
    if(!rig.distant){
      shader.uniforms.uCatchRepair={value:rig.repair};
      shader.uniforms.uCatchOutline={value:Array.from({length:64},(_,i)=>new THREE.Vector2(...(rig.catchOutline[i]||[0,0])))};
      shader.uniforms.uCatchCount={value:rig.catchOutline.length};
      shader.fragmentShader=`uniform sampler2D uCatchRepair;uniform vec2 uCatchOutline[64];uniform int uCatchCount;
        bool oldCatchPixel(vec2 p){bool inside=false;vec2 a=uCatchOutline[uCatchCount-1];for(int i=0;i<64;i++){if(i>=uCatchCount)break;vec2 b=uCatchOutline[i];if((a.y>p.y)!=(b.y>p.y)){if(p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)inside=!inside;}a=b;}return inside;}
      `+shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
        vec2 sourcePixel=vec2(vMapUv.x*1536.0,(1.0-vMapUv.y)*1024.0);
        bool glove=false;
        if(diffuseColor.b>diffuseColor.r*1.6&&diffuseColor.g>.045){
          if(length((sourcePixel-vec2(532.0,276.0))/vec2(16.0,14.0))<1.0||length((sourcePixel-vec2(617.0,299.0))/vec2(18.0,14.0))<1.0||length((sourcePixel-vec2(714.0,334.0))/vec2(18.0,14.0))<1.0)glove=true;
        }
        if(!glove&&oldCatchPixel(sourcePixel))diffuseColor.rgb=texture2D(uCatchRepair,vMapUv).rgb;
      `);
    }
  };
}

export async function buildSourceBoat(parent,distant=false,fishMaker=null){
  if(!artwork)artwork=new THREE.TextureLoader().loadAsync('../assets/pages/p02.webp').then(t=>{t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;}).catch(e=>{artwork=null;throw e;});
  if(!meshData)meshData=fetch('p02/source-boat-meshes.json?v=continuous-1').then(r=>{if(!r.ok)throw new Error(`Source mesh HTTP ${r.status}`);return r.json();}).catch(e=>{meshData=null;throw e;});
  if(!repairImage)repairImage=new THREE.TextureLoader().loadAsync('p02/catch-background.webp').then(t=>{t.colorSpace=THREE.SRGBColorSpace;return t;}).catch(e=>{repairImage=null;throw e;});
  const [texture,data,repair]=await Promise.all([artwork,meshData,repairImage]),m=data[distant?'distant':'main'];
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.BufferAttribute(decode(m.p,Float32Array),3));
  geometry.setAttribute('uv',new THREE.BufferAttribute(decode(m.u,Float32Array),2));
  geometry.setIndex(new THREE.BufferAttribute(decode(m.i,m.i32?Uint32Array:Uint16Array),1));
  geometry.addGroup(0,m.frontCount,0);geometry.addGroup(m.frontCount,geometry.index.count-m.frontCount,1);
  geometry.computeVertexNormals();geometry.userData.closed=true;
  const rig={time:{value:0},ready:{value:0},center:new THREE.Vector2(...m.center),distant,
    pivots:[],fields:[],poses:[],hands:[],heads:[],repair,catchOutline:m.fishOutline};
  const crew=m.crew.map((spec,i)=>{
    const bone=new THREE.Bone();bone.name=`${distant?'distant':'main'}-fisherman-${i+1}`;
    bone.userData.sourcePixels=true;bone.userData.sourcePivot=spec.slice(0,2);
    rig.pivots.push(new THREE.Vector4(spec[0],spec[1],1,0));
    rig.fields.push(new THREE.Vector4(...spec.slice(2,6)));rig.poses.push(new THREE.Vector4());
    rig.hands.push(new THREE.Vector4(spec[6],spec[7],distant?20:42,distant?20:34));
    rig.heads.push(new THREE.Vector4(...(distant?[[1349,302,15,17],[1428,313,15,17]][i]:[[518,198,34,32],[615,234,24,26],[729,266,26,26]][i])));return bone;
  });
  while(rig.pivots.length<3){rig.pivots.push(new THREE.Vector4(0,0,0,0));rig.fields.push(new THREE.Vector4(0,0,1,1));rig.poses.push(new THREE.Vector4());rig.hands.push(new THREE.Vector4(0,0,1,1));rig.heads.push(new THREE.Vector4(0,0,1,1));}
  const front=new THREE.MeshBasicMaterial({map:texture,transparent:true,opacity:0});
  const sides=new THREE.MeshStandardMaterial({map:texture,color:0xb3c6d1,roughness:1,transparent:true,opacity:0});
  rigMaterial(front,rig);rigMaterial(sides,rig);
  const boat=new THREE.Mesh(geometry,[front,sides]);boat.name=distant?'distant-continuous-art':'main-continuous-art';
  boat.userData.sourcePixels=true;boat.userData.continuous=true;
  const holder=new THREE.Group();holder.add(boat);parent.add(holder);
  holder.position.set(m.center[0]/1536-.5,(512-m.center[1])/1536,0);
  let caught=null,catchPivot=null;
  if(!distant){
    caught=await fishMaker(.215);catchPivot=new THREE.Group();holder.add(catchPivot);catchPivot.add(caught.mesh);
    catchPivot.position.set((550-m.center[0])/1536,(m.center[1]-288)/1536,.110);
    caught.mesh.position.x=-.215*.47;caught.mesh.scale.y=-1;caught.mesh.name='whole-hauled-tuna';caught.uniforms.uAmp.value*=.4;
  }
  return {holder,boat,crew,texture,repair,pieces:[boat],tuna:caught?.mesh,catchPivot,caughtUniforms:caught?.uniforms,sourceCenter:m.center,
    rig,landmarks:m.landmarks,fishOutline:m.fishOutline,headOutline:m.headOutline,fishing:{source:true},
    update(t){
      const k=ready(t);rig.time.value=Math.max(0,t);rig.ready.value=k;
      holder.position.z=.042*k+Math.sin(t*1.25)*.0025*k;
      holder.rotation.z=Math.sin(t*.85)*.003*k;
      if(caught){catchPivot.rotation.set(Math.sin(t*2.4)*.025*k,Math.sin(t*1.9)*.025*k,2.28+Math.sin(t*2.0)*.025*k);caught.uniforms.uTime.value=t*.55;}
      if(caught){catchPivot.scale.setScalar(Math.max(.001,k));caught.mesh.material.transparent=true;caught.mesh.material.opacity=k;}
      crew.forEach((bone,i)=>{
        const pull=Math.sin(t*1.8+i*.3);
        bone.rotation.z=pull*(distant?.045:.080)*k;
        bone.rotation.x=pull*(distant?.055:.12)*k;
        rig.poses[i].set(bone.rotation.z,bone.rotation.x,pull*k,0);
      });
      front.opacity=sides.opacity=k;
    },
  };
}

// QA-only probe: same live vertex rig on either the actual closed surface or an
// independent complete page grid. Pixel comparison detects missing anatomy,
// clipped nose/chin, holes and disconnected tail pixels over the entire motion.
export async function makeCoverageProbe(art,part,reference=false,maskDataUrl=null){
  if(part==='fish'){
    const material=art.tuna.material.clone(),configure=art.tuna.material.onBeforeCompile;
    material.color.set(0xffffff);material.onBeforeCompile=shader=>{
      configure(shader);shader.fragmentShader=shader.fragmentShader.replace('#include <dithering_fragment>','#include <dithering_fragment>\ngl_FragColor=vec4(1.0);');
    };
    const probe=new THREE.Mesh(art.tuna.geometry.clone(),material);
    probe.position.copy(art.tuna.position);probe.quaternion.copy(art.tuna.quaternion);probe.scale.copy(art.tuna.scale);
    probe.userData.coverageProbe=true;return probe;
  }
  const geometry=reference?new THREE.PlaneGeometry(1,1024/1536,384,256):art.boat.geometry.clone();
  const mat=new THREE.MeshBasicMaterial({map:art.texture,side:THREE.DoubleSide});
  rigMaterial(mat,art.rig);
  const maskTexture=maskDataUrl?await new THREE.TextureLoader().loadAsync(maskDataUrl):null;
  if(maskTexture){maskTexture.minFilter=maskTexture.magFilter=THREE.NearestFilter;}
  const configure=mat.onBeforeCompile,polygon=part==='fish'?art.fishOutline:art.headOutline;
  mat.onBeforeCompile=shader=>{
    configure(shader);
    const points=Array.from({length:64},(_,i)=>new THREE.Vector2(...(polygon[i]||[0,0])));
    shader.uniforms.uMaskPoints={value:points};shader.uniforms.uMaskCount={value:polygon.length};
    shader.uniforms.uProtectedImage={value:maskTexture||art.texture};shader.uniforms.uUseProtectedImage={value:maskTexture?1:0};
    shader.fragmentShader=`uniform vec2 uMaskPoints[64];uniform int uMaskCount;uniform sampler2D uProtectedImage;uniform float uUseProtectedImage;
      bool protectedPixel(vec2 p){bool inside=false;vec2 a=uMaskPoints[uMaskCount-1];
        for(int i=0;i<64;i++){if(i>=uMaskCount)break;vec2 b=uMaskPoints[i];
          if((a.y>p.y)!=(b.y>p.y)){float crossing=(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x;if(p.x<crossing)inside=!inside;}a=b;
        }return inside;}
    `+shader.fragmentShader.replace('#include <dithering_fragment>',
      '#include <dithering_fragment>\nbool keep=uUseProtectedImage>.5?texture2D(uProtectedImage,vMapUv).r>.5:protectedPixel(vec2(vMapUv.x*1536.0,(1.0-vMapUv.y)*1024.0));\nif(!keep)discard;\ngl_FragColor=vec4(1.0);');
  };
  const mesh=new THREE.Mesh(geometry,mat);mesh.userData.coverageProbe=true;
  return mesh;
}

export function makeBlackOccluder(art){
  const material=new THREE.MeshBasicMaterial({map:art.texture});rigMaterial(material,art.rig);
  const configure=material.onBeforeCompile;material.onBeforeCompile=shader=>{configure(shader);shader.fragmentShader=shader.fragmentShader.replace('#include <dithering_fragment>','#include <dithering_fragment>\ngl_FragColor=vec4(0.0,0.0,0.0,1.0);');};return material;
}
