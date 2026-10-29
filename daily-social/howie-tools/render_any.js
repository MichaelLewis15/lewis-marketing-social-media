// usage: node render_any.js page.html timeline.json duration outdir
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const [,,page,tl,dur,out]=process.argv;const T=JSON.parse(fs.readFileSync(tl));fs.rmSync(out,{recursive:true,force:true});fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'});
const p=await b.newPage({viewport:{width:1080,height:1920}});await p.goto('file://'+path.resolve(page));await p.evaluate(t=>setup(t.MV,t.PO,t.BU),T);await p.evaluate(()=>document.fonts.ready);
const n=Math.round(parseFloat(dur)*30);
for(let f=0;f<n;f++){await p.evaluate(t=>__seek(t),f/30);await p.screenshot({path:`${out}/h${String(f).padStart(4,'0')}.png`,omitBackground:true,clip:{x:0,y:1000,width:1080,height:680}})}
await b.close()})();
