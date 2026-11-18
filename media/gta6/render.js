const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:1080,height:1350}});
const names={p1:'01_most_wanted',p2:'02_mission_passed',p3:'03_waypoint_set',p4:'04_rare_loot_19plus'};
for(const id of process.argv.slice(2)){await p.goto('file://'+process.cwd()+'/posts.html#'+id);await p.reload();
await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);await p.screenshot({path:names[id]+'.png'});}
await b.close();})();
