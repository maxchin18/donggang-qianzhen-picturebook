module.exports=async function(ctx,S){
await ctx.route('https://cdn.jsdelivr.net/npm/**',r=>{const u=new URL(r.request().url()).pathname;let f=null;
if(u.startsWith('/npm/three@0.158.0/'))f=S+'/pkg/three/package/'+u.slice(19);else if(u.startsWith('/npm/mind-ar@1.2.5/'))f=S+'/pkg/package/'+u.slice(19);
f?r.fulfill({path:f,contentType:'application/javascript'}):r.abort();});
await ctx.route('https://cdnjs.cloudflare.com/**',r=>r.fulfill({path:S+'/pkg/qr/package/qrcode.js',contentType:'application/javascript'}));
await ctx.route('https://fonts.**',r=>r.abort());}
module.exports.serve=function(root,port){const http=require('http'),fs=require('fs'),path=require('path');
const types={'.html':'text/html','.js':'application/javascript','.png':'image/png','.webp':'image/webp','.m4a':'audio/mp4','.mind':'application/octet-stream','.mp4':'video/mp4'};
return new Promise(r=>{const s=http.createServer((q,res)=>{let f=path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname));
if(f.endsWith('/'))f+='index.html';fs.readFile(f,(e,d)=>{if(e){res.writeHead(404);res.end();return;}res.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});res.end(d);});}).listen(port,()=>r(s));});}
