"""Focused whole-catch and full-head regression, including live GPU coverage.

The independent complete-page probe is not clipped to the actual mesh. Compare
it with the animated actual mesh over 96 poses, so a clipped nose, body gap or
severed tail cannot pass by checking a small interior color sample.
"""
import asyncio,argparse,io,json,base64
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw
from scipy.ndimage import binary_fill_holes
from playwright.async_api import async_playwright

ap=argparse.ArgumentParser()
ap.add_argument('--url',default='http://localhost:8000/ar/')
ap.add_argument('--out',default='.ar-qa/catch-integrity')
ap.add_argument('--browser',default=str(Path.home()/'AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe'))
args=ap.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)


async def main():
    log={'url':args.url,'errors':[],'httpFailures':[],'coverage':[],'motion':[],'photos':[],'liveSamples':[]}
    source=np.asarray(Image.open(Path(__file__).resolve().parents[2]/'assets/pages/p02.webp').convert('RGB'))
    rgb=source[170:227,488:549].astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    skin=(r>120)&(r>g*1.2)&(g>45)&(g>b*1.2)
    hat=(b>r*1.5)&(b>g*1.1)&(g<110)&(r<75)
    hair=(r<55)&(g<70)&(b<75)
    semantic=cv2.morphologyEx((skin|hat|hair).astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    n,lab,stats,_=cv2.connectedComponentsWithStats(semantic,8);semantic=(lab==1+np.argmax(stats[1:,4]))
    semantic=binary_fill_holes(semantic);full=np.zeros(source.shape[:2],np.uint8);full[170:227,488:549]=semantic*255
    image=Image.fromarray(full);image.save(out/'independent-face-reference.png');buffer=io.BytesIO();image.save(buffer,format='PNG')
    mask_url='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=args.browser,args=['--autoplay-policy=user-gesture-required'])
        page=await browser.new_page(viewport={'width':1200,'height':1100})
        page.on('pageerror',lambda e:log['errors'].append(str(e)))
        page.on('console',lambda m:log['errors'].append(m.text) if m.type=='error' else None)
        page.on('response',lambda r:log['httpFailures'].append([r.status,r.url]) if r.status>=400 else None)
        await page.goto(args.url,wait_until='networkidle');await page.locator('#showPreview').click();await page.locator('#pvPlay').click()
        await page.wait_for_function('window.__preview?.audio.currentTime>2',timeout=45000)
        # Record the running animation before any manual pose or clock control.
        await page.evaluate('''()=>{const p=__preview;document.querySelector('#pvCap').hidden=true;
          const target=p.page.position.clone().set(650/1536-.5,(512-365)/1536,.04);p.page.localToWorld(target);
          p.camera.position.copy(target).add(p.page.position.clone().set(0,1.5,0));p.camera.up.set(0,0,-1);p.camera.lookAt(target);p.camera.zoom=2.5;p.camera.updateProjectionMatrix();}''')
        film=[]
        for i in range(32):
            film.append(Image.open(io.BytesIO(await page.locator('#stage').screenshot())).convert('RGB'))
            log['liveSamples'].append(await page.evaluate('''()=>({audio:__preview.audio.currentTime,fish:__preview.cast.boat.caughtUniforms.uTime.value,crew:__preview.cast.boat.crew.map(b=>b.rotation.z)})'''))
            await page.wait_for_timeout(100)
        assert log['liveSamples'][-1]['audio']-log['liveSamples'][0]['audio']>3
        assert log['liveSamples'][-1]['fish']>log['liveSamples'][0]['fish']
        for j in range(3):
            assert max(s['crew'][j] for s in log['liveSamples'])-min(s['crew'][j] for s in log['liveSamples'])>.15
        duration=round((log['liveSamples'][-1]['audio']-log['liveSamples'][0]['audio'])*1000/31)
        film[0].save(out/'live-motion.webp',save_all=True,append_images=film[1:],duration=duration,loop=0,quality=85)
        await page.evaluate('''async maskURL=>{
          const p=__preview;p.renderer.setAnimationLoop(null);p.audio.pause();document.querySelector('#pvCap').hidden=true;
          const mod=await import('./source-boat.js?v=rigid-2');window.__probes={};
          for(const part of ['fish','head']){__probes[part]=[await mod.makeCoverageProbe(p.cast.boat,part,false,part==='head'?maskURL:null),await mod.makeCoverageProbe(p.cast.boat,part,true,part==='head'?maskURL:null)];
            __probes[part].forEach(m=>{m.visible=false;(part==='fish'?p.cast.boat.catchPivot:p.cast.boat.holder).add(m);});}
          window.__blackOccluder=mod.makeBlackOccluder(p.cast.boat);
          window.__focus=(x,z)=>{const t=p.page.position.clone().set(650/1536-.5,(512-365)/1536,.04);p.page.localToWorld(t);
            p.camera.position.copy(t).add(p.page.position.clone().set(x,1.5,z));p.camera.up.set(0,0,-1);p.camera.lookAt(t);p.camera.zoom=2.5;p.camera.updateProjectionMatrix();};
          __focus(0,0);
          window.__renderTime=t=>{__upd(t);p.renderer.render(p.scene,p.camera);};
        }''',mask_url)
        log['catchModel']=await page.evaluate('''()=>{const g=__preview.cast.boat.tuna.geometry,idx=g.index.array,edges=new Map(),parent=Array.from({length:g.attributes.position.count},(_,i)=>i);
          const find=a=>{while(parent[a]!==a){parent[a]=parent[parent[a]];a=parent[a];}return a;};
          for(let i=0;i<idx.length;i+=3)for(let j=0;j<3;j++){const a=idx[i+j],b=idx[i+(j+1)%3],key=a<b?`${a},${b}`:`${b},${a}`;edges.set(key,(edges.get(key)||0)+1);parent[find(a)]=find(b);}
          return {vertices:g.attributes.position.count,triangles:idx.length/3,openEdges:[...edges.values()].filter(x=>x!==2).length,components:new Set([...idx].map(find)).size};}''')
        assert log['catchModel']['openEdges']==0 and log['catchModel']['components']==1,log['catchModel']
        # Real source colors, normal and two mild viewing angles.
        for angle,x,z in [('front',0,0),('left',.35,.20),('right',-.35,.20)]:
            await page.evaluate('v=>__focus(v[0],v[1])',[x,z])
            for i in range(16):
                t=3+i*.5;await page.evaluate('__renderTime',t)
                name=f'catch-{angle}-{i:02d}.png';await page.locator('#stage').screenshot(path=str(out/name));log['photos'].append(name)
        # Actual camera landmarks/bones changing, not only a running audio clock.
        for i in range(96):
            t=3+i*.1
            state=await page.evaluate('''t=>{__upd(t);return {t,crew:__preview.cast.boat.crew.map(b=>[b.rotation.x,b.rotation.z]),fishTime:__preview.cast.boat.rig.time.value};}''',t)
            log['motion'].append(state)
        for j in range(3):
            span=max(s['crew'][j][1] for s in log['motion'])-min(s['crew'][j][1] for s in log['motion'])
            assert span>.15,(j,span)
        # Hide everything except the actual or independent reference probe.
        await page.evaluate('''()=>{const p=__preview;__focus(0,0);p.scene.background=p.cast.boat.boat.material[0].color.clone().set(0x000000);
          p.page.children.forEach(m=>{if(m.isMesh)m.visible=false;});p.cast.forEach(c=>{c.holder.visible=false;c.shadow.visible=false;});
          p.cast.boatShadows.forEach(m=>m.visible=false);p.cast.distantBoat.holder.visible=false;p.cast.boat.boat.visible=false;p.cast.boat.tuna.visible=false;p.cast.boat.boat.material=__blackOccluder;}''')
        kernel=np.ones((5,5),np.uint8)
        for part in ['fish','head']:
            for i in range(96):
                t=3+i*.1;masks=[]
                for which in range(2):
                    await page.evaluate('''v=>{const p=__preview;__upd(v.t);p.cast.boat.boat.visible=v.part==='fish'&&v.which===0;__probes[v.part].forEach((m,j)=>m.visible=j===v.which);p.renderer.render(p.scene,p.camera);}''',{'t':t,'part':part,'which':which})
                    data=await page.locator('#stage').screenshot();mask=np.asarray(Image.open(io.BytesIO(data)).convert('L'))>220;masks.append(mask)
                actual,expected=masks;assert expected.sum()>100,part
                ey,ex=np.where(expected);assert min(ex.min(),ey.min(),expected.shape[1]-1-ex.max(),expected.shape[0]-1-ey.max())>=10,(part,'cropped by viewport')
                missing=expected & ~cv2.dilate(actual.astype(np.uint8),kernel).astype(bool)
                rate=float(missing.sum()/expected.sum())
                n,labels,stats,_=cv2.connectedComponentsWithStats(actual.astype(np.uint8),8)
                largest=int(stats[1:,cv2.CC_STAT_AREA].max()) if n>1 else 0
                fraction=largest/max(1,int(actual.sum()))
                holes=cv2.floodFill((~actual).astype(np.uint8),None,(0,0),2)[1]==1
                max_hole=0
                if holes.any():
                    hn,_,hs,_=cv2.connectedComponentsWithStats(holes.astype(np.uint8),8)
                    if hn>1:max_hole=int(hs[1:,cv2.CC_STAT_AREA].max())
                ay,ax=np.where(actual)
                record={'part':part,'time':round(t,1),'missingRatio':round(rate,7),'largestComponentRatio':round(fraction,7),'largestHolePixels':max_hole,'pixels':int(actual.sum()),'center':[round(float(ax.mean()),4),round(float(ay.mean()),4)]}
                log['coverage'].append(record)
                if i in [0,24,48,72,95]:
                    Image.fromarray(actual.astype('uint8')*255).save(out/f'mask-{part}-{i:02d}.png')
                assert rate<(.02 if part=='fish' else .005) and fraction>.995 and max_hole<9,record
            await page.evaluate('part=>__probes[part].forEach(m=>m.visible=false)',part)
        await browser.close()
    heads=[r for r in log['coverage'] if r['part']=='head'];log['visibleHeadTravelPixels']=max(r['center'][0] for r in heads)-min(r['center'][0] for r in heads)
    assert log['visibleHeadTravelPixels']>12,log['visibleHeadTravelPixels']
    (out/'catch-integrity.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    assert not log['errors'] and not log['httpFailures'],log
    # Contact sheets keep the entire fish, not just its tail, in every frame.
    for angle in ['front','left','right']:
        sheet=Image.new('RGB',(1600,1304),'#d7e0e1');draw=ImageDraw.Draw(sheet)
        for i in range(16):
            im=Image.open(out/f'catch-{angle}-{i:02d}.png').convert('RGB');im.thumbnail((400,300));x=i%4*400;y=i//4*326
            sheet.paste(im,(x,y+26));draw.text((x+8,y+6),f'{angle} t={3+i*.5:.1f}',fill='black')
        sheet.save(out/f'contact-{angle}.jpg',quality=91)
    print(json.dumps({'coverageFrames':len(log['coverage']),'photos':len(log['photos']),'maxMissing':max(s['missingRatio'] for s in log['coverage']),'minConnected':min(s['largestComponentRatio'] for s in log['coverage']),'maxHole':max(s['largestHolePixels'] for s in log['coverage']),'errors':log['errors']},ensure_ascii=True))


if __name__=='__main__':asyncio.run(main())
