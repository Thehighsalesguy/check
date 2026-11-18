const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:+(process.argv[3]||1)});
await p.goto('file://'+process.cwd()+'/'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
await p.screenshot({path:process.argv[2].replace('.html','.png')});await b.close();})();
