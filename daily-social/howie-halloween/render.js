const {chromium}=require('playwright');const fs=require('fs');
const [,,dur,out,only]=process.argv;const T=JSON.parse(fs.readFileSync('timeline.json'));fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'});
const p=await b.newPage({viewport:{width:1080,height:1920}});await p.goto('file://'+__dirname+'/halloween.html');await p.evaluate(t=>setup(t.MV,t.PO,t.BU),T);await p.evaluate(()=>document.fonts.ready);
const n=Math.round(parseFloat(dur)*30);const list=only?only.split(',').map(Number):[...Array(n).keys()];
for(const f of list){await p.evaluate(t=>__seek(t),f/30);await p.screenshot({path:`${out}/h${String(f).padStart(4,'0')}.png`,omitBackground:true,clip:{x:0,y:1000,width:1080,height:680}})}
await b.close()})();
