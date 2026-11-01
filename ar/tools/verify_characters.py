"""Browser regression and per-character views. Evidence stays outside tracked files.

python ar/tools/verify_characters.py --url http://localhost:8000/ar/ --out .ar-qa
Uses an existing Chromium and existing fake-camera fixtures (no browser install).
"""
import argparse
import asyncio
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://localhost:8000/ar/')
parser.add_argument('--out', default='.ar-qa')
parser.add_argument('--browser', default=str(Path.home() / 'AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe'))
parser.add_argument('--fixtures', default='.ar-qa/fixtures')
parser.add_argument('--mode', default='visual', choices=['visual', 'ar', 'regressions', 'lifecycle'])
args = parser.parse_args()
OUT = Path(args.out).resolve(); OUT.mkdir(parents=True, exist_ok=True)


async def setup(page, log):
    page.on('pageerror', lambda e: log['errors'].append(str(e)))
    page.on('console', lambda m: log['errors'].append(m.text) if m.type == 'error' else None)
    page.on('response', lambda r: log['httpFailures'].append([r.status, r.url]) if r.status >= 400 else None)
    await page.goto(args.url, wait_until='networkidle')


async def visual(p):
    log = {'errors': [], 'httpFailures': [], 'views': []}
    browser = await p.chromium.launch(executable_path=args.browser, args=['--autoplay-policy=user-gesture-required'])
    page = await browser.new_page(viewport={'width': 1200, 'height': 1100})
    await setup(page, log)
    await page.locator('#showPreview').click(); await page.locator('#pvPlay').click()
    await page.wait_for_function('!!window.__preview', timeout=45000)
    await page.wait_for_timeout(5000)
    log['audio'] = await page.evaluate('({time:__preview.audio.currentTime,paused:__preview.audio.paused})')
    await page.locator('#stage').screenshot(path=str(OUT / 'preview.png'))
    await page.evaluate('''() => {__preview.renderer.setAnimationLoop(null); __preview.controls.enabled=false; __preview.audio.pause();
      window.__view = (x,y,z,tx,ty,tz) => {const p=__preview;p.camera.position.set(x,y,z);p.camera.lookAt(tx,ty,tz);p.renderer.render(p.scene,p.camera);};
    }''')
    for name, eye in [('top', [0, 1.55, .001]), ('oblique', [0, .95, .85]), ('side', [0, .38, 1.25]), ('rear', [0, .65, -1.1])]:
        await page.evaluate('(eye) => {__upd(7); __view(...eye,0,.06,0);}', eye)
        await page.locator('#stage').screenshot(path=str(OUT / f'ensemble-{name}.png'))
        log['views'].append(f'ensemble-{name}')
    for sec in [3, 7, 12, 18, 24, 35, 50, 65]:
        for view, eye in [('top',[0,1.55,.001]),('oblique',[0,.95,.85])]:
            await page.evaluate('''v=>{for(let i=0;i<40;i++)__upd(v.sec);__view(...v.eye,0,.06,0);}''', {'sec':sec,'eye':eye})
            name=f'animation-{sec}-{view}'
            await page.locator('#stage').screenshot(path=str(OUT / f'{name}.png'))
            log['views'].append(name)
    # Isolate actual live character meshes, retaining the scene lights.
    await page.evaluate('''() => {
      const p=__preview; p.page.children.forEach(n=>{if(n.isMesh)n.visible=false;});
      p.cast.forEach(c=>{c.holder.visible=false;c.shadow.visible=false;});
      p.cast.boat.holder.visible=false;p.cast.distantBoat.holder.visible=false;
      p.cast.boatShadows.forEach(s=>s.visible=false);
    }''')
    for index, name in enumerate(['tuna_big', 'tuna_m', 'tuna_r', 'gull1', 'gull2']):
        await page.evaluate('''i=>{const c=__preview.cast[i];c.holder.visible=true;c.holder.position.set(0,0,.12);
          c.holder.rotation.set(0,0,0);c.pivot.rotation.set(0,0,0);c.body.scale.setScalar(1);c.uniforms.uTime.value=0;document.querySelector('#pvCap').hidden=true;}''', index)
        for view, eye in [('top',[0,.68,.001]),('oblique',[0,.48,.42]),('side',[0,.15,.60]),('back',[0,-.48,.42])]:
            await page.evaluate('(v)=>__view(...v,0,.12,0)', eye)
            await page.locator('#stage').screenshot(path=str(OUT / f'{name}-{view}.png'))
            log['views'].append(f'{name}-{view}')
        await page.evaluate('i=>__preview.cast[i].holder.visible=false', index)
    await page.evaluate('''()=>{const b=__preview.cast.boat;b.holder.visible=true;b.holder.position.set(0,0,0);b.holder.rotation.set(0,0,0);b.holder.scale.setScalar(1);}''')
    for view, eye in [('top',[0,.8,.001]),('front',[.15,.24,.55]),('rear',[0,.25,-.65])]:
        await page.evaluate('v=>__view(...v,0,.1,0)', eye)
        await page.locator('#stage').screenshot(path=str(OUT / f'boat-{view}.png'))
        log['views'].append(f'boat-{view}')
    for i in range(3):
        # Render a complete crew member alone in their real pose and materials.
        await page.evaluate('''i=>{const p=__preview,b=p.cast.boat;b.holder.visible=false;
          const person=b.crew[i].clone(true);person.name='qa-person';person.position.set(0,0,0);person.rotation.set(0,0,0);
          p.page.add(person);window.__qaPerson=person;}''', i)
        for view, eye in [('front',[0,.09,.20]),('side',[.20,.09,.01]),('rear',[0,.09,-.20]),('top',[0,.30,.001])]:
            await page.evaluate('v=>__view(...v,0,.06,0)', eye)
            await page.locator('#stage').screenshot(path=str(OUT / f'fisherman-{i+1}-{view}.png'))
            log['views'].append(f'fisherman-{i+1}-{view}')
        await page.evaluate('()=>__qaPerson.removeFromParent()')
    log['geometry'] = await page.evaluate('''()=>{const p=__preview;return {characters:p.cast.map(c=>({id:c.def.id,vertices:c.body.geometry.attributes.position.count,triangles:c.body.geometry.index.count/3})),crew:p.cast.boat.crew.map(f=>({name:f.name,arms:f.userData.arms.length,hands:f.userData.hands.length})),render:p.renderer.info.render};}''')
    await browser.close()
    (OUT / 'visual.json').write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    assert not log['errors'] and not log['httpFailures'], log
    assert not log['audio']['paused'] and log['audio']['time'] > 2, log['audio']
    print(json.dumps({'mode':'visual','views':len(log['views']),'errors':log['errors']},ensure_ascii=True))


STATE = '''()=>({visible:__ar.visible,audio:__ar.audio?{time:__ar.audio.currentTime,paused:__ar.audio.paused,ended:__ar.audio.ended}:null,
 cap:document.querySelector('#cap').hidden?'':document.querySelector('#cap').textContent,
 video:document.querySelector('#ar video')?.currentTime,error:!document.querySelector('#err').hidden})'''


async def ar(p):
    for fixture in ['portrait_front', 'portrait_slant_mild', 'landscape_framed', 'landscape']:
        log={'errors':[],'httpFailures':[],'samples':[],'fixture':fixture}
        camera_file = (Path(args.fixtures)/f'{fixture}.y4m').resolve()
        assert camera_file.is_file(), f'Missing fixture: {camera_file}'
        browser=await p.chromium.launch(executable_path=args.browser,args=['--autoplay-policy=user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-video-capture='+str(camera_file)])
        page=await browser.new_page(viewport={'width':844 if fixture.startswith('landscape') else 390,'height':390 if fixture.startswith('landscape') else 844},is_mobile=True,has_touch=True,permissions=['camera'])
        await setup(page,log); await page.locator('#startAR').tap();t0=time.monotonic();shots=set()
        while time.monotonic()-t0<24:
            st=await page.evaluate(STATE);st['elapsed']=round(time.monotonic()-t0,3);log['samples'].append(st)
            if st['visible'] and 'found' not in log:log['found']=st['elapsed']
            for threshold in [5,8,15,22]:
                if st['elapsed']>=threshold and threshold not in shots:
                    await page.screenshot(path=str(OUT/f'{fixture}-{threshold}.png'));shots.add(threshold)
            await page.wait_for_timeout(250)
        await page.locator('#exit').click();await page.wait_for_timeout(300)
        log['exit']=await page.evaluate('({engine:!!__ar.engine,canvases:document.querySelectorAll("#ar canvas").length,audioPaused:__ar.audio.paused})')
        await browser.close();(OUT/f'{fixture}.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
        captions=sorted({s['cap'] for s in log['samples'] if s['cap']})
        print(json.dumps({'case':fixture,'found':log.get('found'),'captions':len(captions),'errors':log['errors']},ensure_ascii=True),flush=True)
        assert 'found' in log and len(captions)==3 and not log['errors'] and not log['httpFailures']
        assert log['exit']=={'engine':False,'canvases':0,'audioPaused':True}


async def regressions(p):
    log={'errors':[],'httpFailures':[]}
    camera_file = (Path(args.fixtures)/'portrait_front.y4m').resolve()
    assert camera_file.is_file(), f'Missing fixture: {camera_file}'
    browser=await p.chromium.launch(executable_path=args.browser,args=['--autoplay-policy=user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-video-capture='+str(camera_file)])
    page=await browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,permissions=['camera'])
    async def delay(route):
        await asyncio.sleep(6)
        await route.continue_()
    await page.route('**/narration.m4a',delay)
    await setup(page,log);await page.locator('#startAR').tap();await page.wait_for_timeout(9500)
    log['slowAudio']=await page.evaluate(STATE)
    await page.wait_for_timeout(1500);log['slowAudioLater']=await page.evaluate(STATE)
    await page.locator('#exit').click();await page.unroute('**/narration.m4a',delay)
    await page.locator('#showPreview').click();await page.locator('#pvPlay').click()
    await page.wait_for_function('window.__preview?.audio.currentTime>1')
    await page.evaluate('document.querySelector("#startAR").click()')
    await page.wait_for_function('__ar.visible',timeout=30000);await page.wait_for_timeout(2000)
    log['switch']=await page.evaluate('({previewPaused:__preview.audio.paused,arPaused:__ar.audio.paused,arTime:__ar.audio.currentTime})')
    await browser.close();(OUT/'regressions.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    assert not log['slowAudio']['audio']['paused'] and log['slowAudioLater']['audio']['time']>log['slowAudio']['audio']['time']
    assert log['switch']['previewPaused'] and not log['switch']['arPaused'] and log['switch']['arTime']>1
    assert not log['errors'] and not log['httpFailures'],log
    print('slow audio and preview-to-AR regressions passed')


async def lifecycle(p):
    log={'errors':[],'httpFailures':[]}
    camera_file=(Path(args.fixtures)/'portrait_front.y4m').resolve()
    browser=await p.chromium.launch(executable_path=args.browser,args=['--autoplay-policy=user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-video-capture='+str(camera_file)])
    page=await browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,permissions=['camera'])
    await page.add_init_script('''window.__streams=[];const gum=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
      navigator.mediaDevices.getUserMedia=async(...args)=>{const s=await gum(...args);__streams.push(s);return s;};''')
    await setup(page,log)
    async def slow_mesh(route):
        await asyncio.sleep(5);await route.continue_()
    await page.route('**/meshes.json*',slow_mesh)
    await page.locator('#startAR').tap();await page.locator('#hud').wait_for(state='visible')
    await page.locator('#exit').click();await page.wait_for_timeout(6500)
    log['cancelDuringLoad']=await page.evaluate('({intro:!document.querySelector("#intro").hidden,engine:!!__ar.engine,audioPaused:__ar.audio.paused,liveTracks:__streams.flatMap(s=>s.getTracks()).filter(t=>t.readyState==="live").length})')
    assert log['cancelDuringLoad']=={'intro':True,'engine':False,'audioPaused':True,'liveTracks':0},log
    await page.unroute('**/meshes.json*',slow_mesh)
    for i in range(3):
        await page.locator('#startAR').tap();await page.wait_for_function('__ar.visible',timeout=30000)
        if i==0:
            # Synthetic visibility events check our resume UI; not OS background QA.
            await page.evaluate('''()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));
              Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));}''')
            log['foreground']=await page.evaluate('({paused:__ar.audio.paused,resumeVisible:!document.querySelector("#sound").hidden})')
            assert log['foreground']=={'paused':True,'resumeVisible':True}
            await page.locator('#sound').tap();await page.wait_for_timeout(500)
            assert not await page.evaluate('__ar.audio.paused')
        await page.locator('#exit').click();await page.wait_for_timeout(300)
        assert await page.evaluate('__streams.flatMap(s=>s.getTracks()).every(t=>t.readyState==="ended")')
    log['cycles']=3
    await browser.close();(OUT/'lifecycle.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    assert not log['errors'] and not log['httpFailures'],log
    print('cancel during loading, resume UI, and 3 start/exit cycles passed')


async def main():
    async with async_playwright() as p:
        await {'visual':visual,'ar':ar,'regressions':regressions,'lifecycle':lifecycle}[args.mode](p)

if __name__=='__main__':asyncio.run(main())
