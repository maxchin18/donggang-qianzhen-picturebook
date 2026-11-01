"""Rigid hull and fish-free background regression on the real browser renderer.

Compares the visible hull with the fish hidden against the fish-free repair
texture. Exercises both shader compilation orders and an intentional bad cache
key as a negative control. Separately checks every rigid triangle and 96 GPU
frames, then checks that normal moving-fish rendering leaves no old frame.
"""
import argparse,asyncio,base64,io,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from playwright.async_api import async_playwright

ap=argparse.ArgumentParser();ap.add_argument('--url',default='http://localhost:8000/ar/')
ap.add_argument('--out',default='.ar-qa/hull-wake');ap.add_argument('--browser',default=str(Path.home()/'AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe'))
args=ap.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[2]


async def main():
    log={'url':args.url,'errors':[],'httpFailures':[],'orders':[],'rigidFrames':[],'trailFrames':[]}
    spec=json.loads((root/'ar/p02/source-boat-shapes.json').read_text(encoding='utf-8'))
    # Independent semantic area where the ORIGINAL fish used to cover the hull.
    roi=Polygon(spec['main']['fish']).buffer(0).buffer(-4).intersection(Polygon(spec['main']['hull']).buffer(-4))
    mask=Image.new('L',(1536,1024));draw=ImageDraw.Draw(mask)
    for poly in (list(roi.geoms) if hasattr(roi,'geoms') else [roi]):draw.polygon(list(poly.exterior.coords),fill=255)
    buf=io.BytesIO();mask.save(buf,format='PNG');mask_url='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=args.browser,args=['--autoplay-policy=user-gesture-required'])
        page=await browser.new_page(viewport={'width':1200,'height':1100})
        page.on('pageerror',lambda e:log['errors'].append(str(e)))
        page.on('console',lambda m:log['errors'].append(m.text) if m.type=='error' else None)
        page.on('response',lambda r:log['httpFailures'].append([r.status,r.url]) if r.status>=400 else None)
        await page.goto(args.url,wait_until='networkidle');await page.locator('#showPreview').click();await page.locator('#pvPlay').click()
        await page.wait_for_function('window.__preview?.audio.currentTime>2',timeout=45000)
        await page.evaluate('''async maskURL=>{
          const p=__preview,b=p.cast.boat,f=p.cast.distantBoat;p.renderer.setAnimationLoop(null);p.audio.pause();document.querySelector('#pvCap').hidden=true;
          const mod=await import('./source-boat.js?v=rigid-2');window.__THREE=await import('three');
          window.__roiProbe=await mod.makeCoverageProbe(b,'head',false,maskURL);b.holder.add(__roiProbe);__roiProbe.visible=false;
          window.__keys=[b,f].map(a=>a.boat.material.map(m=>m.customProgramCacheKey()));
          window.__focusHull=(zoom=2.5)=>{const target=p.page.position.clone().set(650/1536-.5,(512-365)/1536,.04);p.page.localToWorld(target);
            p.camera.position.copy(target).add(p.page.position.clone().set(0,1.5,0));p.camera.up.set(0,0,-1);p.camera.lookAt(target);p.camera.zoom=zoom;p.camera.updateProjectionMatrix();};
          window.__frame=t=>{__upd(t);for(const a of [b,f]){a.holder.rotation.set(0,0,0);a.holder.position.z=.042;}p.renderer.render(p.scene,p.camera);};
          window.__fishBounds=()=>{const pos=b.tuna.geometry.attributes.position,pts=[];b.tuna.updateWorldMatrix(true,false);
            for(let i=0;i<pos.count;i++){
              const v=new __THREE.Vector3().fromBufferAttribute(pos,i).applyMatrix4(b.tuna.matrixWorld).project(p.camera);pts.push([(v.x+1)*p.renderer.domElement.clientWidth/2,(1-v.y)*p.renderer.domElement.clientHeight/2]);}
            return [Math.min(...pts.map(v=>v[0]))-12,Math.min(...pts.map(v=>v[1]))-12,Math.max(...pts.map(v=>v[0]))+12,Math.max(...pts.map(v=>v[1]))+12];};
          p.cast.forEach(c=>{c.holder.visible=false;c.shadow.visible=false;});p.cast.boatShadows.forEach(m=>m.visible=false);b.tuna.visible=false;
          b.boat.frustumCulled=f.boat.frustumCulled=false;
          window.__warm=(order,bad=false)=>{
            for(const [i,a] of [b,f].entries())a.boat.material.forEach((m,j)=>{m.dispose();m.customProgramCacheKey=()=>bad?'intentional-bad-key':__keys[i][j];m.needsUpdate=true;});
            b.boat.renderOrder=order==='main-first'?0:10;f.boat.renderOrder=order==='main-first'?10:0;
            b.boat.visible=f.boat.visible=true;f.holder.visible=true;__focusHull(.95);__frame(5);f.holder.visible=false;__focusHull();__frame(5);
          };__warm('distant-first');
        }''',mask_url)
        # Read the projected fish-free region through the ACTUAL hull surface.
        await page.evaluate('''()=>{const p=__preview;p.cast.boat.boat.visible=false;__roiProbe.visible=true;p.scene.background=new __THREE.Color(0);p.page.children.filter(m=>m.isMesh).forEach(m=>m.visible=false);__frame(5);}''')
        pixels=np.asarray(Image.open(io.BytesIO(await page.locator('#stage').screenshot())).convert('L'))>220
        assert pixels.sum()>1000;Image.fromarray(pixels.astype('uint8')*255).save(out/'fish-free-roi.png')
        await page.evaluate('''()=>{const p=__preview;__roiProbe.visible=false;p.cast.boat.boat.visible=true;p.scene.background=new __THREE.Color(0x0c315b);p.page.children.filter(m=>m.isMesh).forEach(m=>m.visible=true);}''')
        # Negative control deliberately recreates the previous shader-cache bug.
        for name,bad in [('negative-control',True),('distant-first',False),('main-first',False)]:
            await page.evaluate('v=>__warm(v[0],v[1])',['distant-first' if bad else name,bad])
            data=await page.locator('#stage').screenshot(path=str(out/f'{name}-no-fish.png'));actual=np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(int)
            await page.evaluate('''()=>{const p=__preview,b=p.cast.boat;b.boat.material.forEach(m=>{m.map=b.repair;m.needsUpdate=true;});__frame(5);}''')
            ref=np.asarray(Image.open(io.BytesIO(await page.locator('#stage').screenshot())).convert('RGB')).astype(int)
            diff=np.abs(actual-ref)[pixels];metric={'order':name,'meanRGBError':float(diff.mean()),'maxRGBError':int(diff.max()),'roiPixels':int(pixels.sum())}
            log['orders'].append(metric)
            await page.evaluate('''()=>{const b=__preview.cast.boat;b.boat.material.forEach(m=>{m.map=b.texture;m.needsUpdate=true;});}''')
            if bad:assert metric['meanRGBError']>10,metric
            else:assert metric['meanRGBError']<.25 and metric['maxRGBError']<4,metric
        # Verify every triangle belonging to rigid painted areas, not merely a
        # hand-picked subset that happens to have zero weights.
        geometry=await page.evaluate('''()=>{const g=__preview.cast.boat.boat.geometry;return {uv:[...g.attributes.uv.array],skin:[...g.attributes.artSkin.array],index:[...g.index.array]};}''')
        uv=np.array(geometry['uv']).reshape(-1,2);skin=np.array(geometry['skin']).reshape(-1,4);indices=np.array(geometry['index']).reshape(-1,3)
        rigid=unary_union([Polygon(spec['main'][k]) for k in ['hull','cabin','stern','equipment']])
        xy=np.column_stack((uv[:,0]*1536,(1-uv[:,1])*1024));selected=[]
        for tri in indices:
            if rigid.contains(Point(*xy[tri].mean(axis=0))):
                assert skin[tri].max()==0,('Hull vertex has movement weight',tri.tolist());selected.extend(tri.tolist())
        log['rigidTriangles']=len(selected)//3;assert log['rigidTriangles']>15000
        await page.evaluate('''selected=>{const p=__preview,b=p.cast.boat,g=b.boat.geometry.clone();g.setIndex(selected);g.clearGroups();
          const mat=b.boat.material[0].clone();mat.onBeforeCompile=b.boat.material[0].onBeforeCompile;mat.customProgramCacheKey=b.boat.material[0].customProgramCacheKey;
          window.__rigid=new __THREE.Mesh(g,mat);b.holder.add(__rigid);b.boat.visible=false;p.page.children.filter(m=>m.isMesh).forEach(m=>m.visible=false);p.scene.background=new __THREE.Color(0);__frame(3);
        }''',selected)
        reference=np.asarray(Image.open(io.BytesIO(await page.locator('#stage').screenshot())).convert('RGB')).astype(int)
        for i in range(96):
            t=3+i*.1;await page.evaluate('__frame',t)
            data=await page.locator('#stage').screenshot();frame=np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(int)
            diff=int(np.abs(frame-reference).max());log['rigidFrames'].append({'t':round(t,1),'maxRGBChange':diff});assert diff<=1,log['rigidFrames'][-1]
            if i in [0,32,64,95]:Image.open(io.BytesIO(data)).save(out/f'rigid-{i:02d}.png')
        await page.evaluate('''()=>{const p=__preview;__rigid.visible=false;p.cast.boat.boat.visible=true;p.cast.boat.tuna.visible=true;p.page.children.filter(m=>m.isMesh).forEach(m=>m.visible=true);p.scene.background=new __THREE.Color(0x0c315b);}''')
        for i in range(16):
            t=3+i*.5;bounds=await page.evaluate('t=>{__frame(t+7);const a=__fishBounds();__frame(t);return [a,__fishBounds()];}',t)
            data=await page.locator('#stage').screenshot(path=str(out/f'fish-motion-{i:02d}.png'));actual=np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(int)
            state=await page.evaluate('''t=>{const p=__preview,m=p.cast.boat.tuna.material;p.renderer.clear();__frame(t);return {opaque:!m.transparent,opacity:m.opacity,depthWrite:m.depthWrite};}''',t)
            fresh_data=await page.locator('#stage').screenshot();fresh=np.asarray(Image.open(io.BytesIO(fresh_data)).convert('RGB')).astype(int)
            # Compare the entire previous/current fish plus its surrounding
            # wake. A few MSAA edge pixels on a moving crew member are outside
            # this fish-trail test; complete heads have their own regression.
            x0=max(0,int(min(b[0] for b in bounds)));y0=max(0,int(min(b[1] for b in bounds)))
            x1=min(actual.shape[1],int(max(b[2] for b in bounds))+1);y1=min(actual.shape[0],int(max(b[3] for b in bounds))+1)
            delta=int(np.abs(actual-fresh)[y0:y1,x0:x1].max());log['trailFrames'].append({'t':t,'maxPreviousFrameResidue':delta,'fishAndWakeBox':[x0,y0,x1,y1],**state})
            if delta>1:
                Image.open(io.BytesIO(fresh_data)).save(out/f'fish-fresh-{i:02d}.png')
                Image.fromarray(np.abs(actual-fresh).astype('uint8')*4).save(out/f'fish-difference-{i:02d}.png')
                (out/'hull-wake-debug.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
            assert delta<=1 and state=={'opaque':True,'opacity':1,'depthWrite':True},log['trailFrames'][-1]
        await browser.close()
    assert not log['errors'] and not log['httpFailures'],log
    (out/'hull-wake.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'orders':log['orders'],'rigidTriangles':log['rigidTriangles'],'rigidFrames':len(log['rigidFrames']),'trailFrames':len(log['trailFrames']),'maxRigidRGBChange':max(r['maxRGBChange'] for r in log['rigidFrames']),'maxTrailResidue':max(r['maxPreviousFrameResidue'] for r in log['trailFrames']),'errors':log['errors']},ensure_ascii=True),flush=True)


if __name__=='__main__':asyncio.run(main())
