const {chromium}=require('playwright');const S=process.argv[2];const cam=process.argv[3];const vw=+process.argv[4],vh=+process.argv[5];const tag=process.argv[6];
(async()=>{await require(S+'/common.js').serve('/home/claude/donggang-qianzhen-picturebook',8767);
const b=await chromium.launch({args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-video-capture='+cam,'--autoplay-policy=user-gesture-required']});
const ctx=await b.newContext({viewport:{width:vw,height:vh},permissions:['camera'],isMobile:true,hasTouch:true,userAgent:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'});
await require(S+'/common.js')(ctx,S);
const p=await ctx.newPage();p.on('pageerror',e=>console.log('pageerror',e.message));p.on('console',m=>{console.log('console',m.type(),m.text().slice(0,200))});
await p.goto('http://localhost:8767/ar/index.html');await p.waitForTimeout(800);
console.log('QR handoff hidden on phone:',await p.evaluate(()=>document.getElementById('handoff').hidden));
await p.tap('#startAR');const t0=Date.now();
let found=false;for(let i=0;i<40;i++){await p.waitForTimeout(500);if(await p.evaluate(()=>window.__ar&&window.__ar.visible)){found=true;break;}}
console.log('target found:',found,'after',((Date.now()-t0)/1000).toFixed(1),'s');
const st=async()=>p.evaluate(()=>({t:+window.__ar.audio.currentTime.toFixed(2),paused:window.__ar.audio.paused,cap:document.getElementById('cap').textContent,soundBtn:!document.getElementById('sound').hidden}));
await p.waitForTimeout(1000);await p.screenshot({path:`${S}/${tag}1.png`});console.log('+1s',await st());
await p.waitForTimeout(3000);await p.screenshot({path:`${S}/${tag}2.png`});console.log('+4s',await st());
await p.waitForTimeout(4000);await p.screenshot({path:`${S}/${tag}3.png`});console.log('+8s',await st());
await b.close();process.exit(0);})();
