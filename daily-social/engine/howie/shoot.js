const {chromium}=require('playwright');const fs=require('fs');
const svg=fs.readFileSync('howie.svg','utf8');
const poses={idle:[12,12,0,0,0],pointL:[78,14,1,0,0],pointR:[14,78,0,1,0],wave:[14,112,0,0,1],cheer:[100,100,0,0,1]};
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'});const p=await b.newPage({viewport:{width:1400,height:1500}});
await p.setContent(`<html><body style="margin:0;background:transparent"><div id=w style="padding:150px 190px 60px">${svg}</div></body></html>`);
for(const [n,[aL,aR,fl,fr,open]] of Object.entries(poses)){
 await p.evaluate(([aL,aR,fl,fr,open])=>{const g=id=>document.getElementById(id);
  g('m-armL').setAttribute('transform',`rotate(${aL} 140 258)`);g('m-armR').setAttribute('transform',`rotate(${-aR} 280 258)`);
  g('m-fL').style.display=fl?'':'none';g('m-fR').style.display=fr?'':'none';g('m-smile').style.display=open?'none':'';g('m-open').style.display=open?'':'none';},[aL,aR,fl,fr,open]);
 await p.locator('#w').screenshot({path:`howie-${n}.png`,omitBackground:true});}
await b.close()})();
