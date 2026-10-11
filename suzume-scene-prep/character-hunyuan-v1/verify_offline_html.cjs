const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const output=path.join(__dirname,'离线HTML');
const checks=path.join(output,'验证');fs.mkdirSync(checks,{recursive:true});
const name=process.argv[2]||'铃芽之旅_v38_海报庭院.html';
const isolated=fs.mkdtempSync(path.join(os.tmpdir(),'SuzumeOffline-'));
const target=path.join(isolated,name);fs.copyFileSync(path.join(output,name),target);
const report={file:name,isolatedFile:target,networkDisabled:true,requests:[],errors:[],consoleErrors:[],scenes:[]};
let currentPage;

(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-unsafe-swiftshader']});
 try{
  const context=await browser.newContext({viewport:{width:1100,height:950},deviceScaleFactor:1,acceptDownloads:true,offline:true});
  await context.route(/^https?:\/\//,route=>{report.requests.push(route.request().url());return route.abort();});
  const page=await context.newPage();
  currentPage=page;
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('console',msg=>{if(msg.type()==='error')report.consoleErrors.push(msg.text().slice(0,1600));});
  page.on('request',req=>{if(/^https?:/.test(req.url()))report.requests.push(req.url());});
  console.log('LOADING',name);
  await page.goto(pathToFileURL(target).href,{waitUntil:'domcontentloaded',timeout:120000});
  async function waitReady(){
   await page.waitForFunction(()=>window.__offline?.ready||window.__offline?.errors.length,undefined,{timeout:120000});
   const status=await page.evaluate(()=>({info:window.__offline,status:document.querySelector('#archive-status').textContent}));
   if(!status.info.ready||status.info.errors.length)throw Error(JSON.stringify(status));
   return status;
  }
  let status=await waitReady();console.log('READY',status.info.selected);
  const ids=await page.evaluate(()=>OFFLINE_CONFIG.scenes.map(s=>s.id));
  for(const id of ids){
   if(status.info.selected!==id){
    await page.evaluate(id=>document.querySelector('[data-scene="'+id+'"]').click(),id);
    status=await waitReady();console.log('READY',id);
   }
   const frame=page.frames().find(f=>f!==page.mainFrame());
   const state=await frame.evaluate(()=>{
    const root=document.getElementById('suzume-full-scene');
    const motion=root.querySelector('[data-motion]');
    if(motion.getAttribute('aria-pressed')==='true')motion.click();
    return {ready:root.dataset.ready,views:[...root.querySelector('[data-view]').options].map(o=>o.value),door:root.querySelector('[data-door]').textContent,
     canvasSize:[root.querySelector('canvas').width,root.querySelector('canvas').height],inspectionKeys:Object.keys(root).filter(k=>!k.startsWith('__react'))};
   });
   state.initialCamera=await frame.evaluate(()=>document.getElementById('suzume-full-scene').inspectModel().camera.position.toArray());
   await page.screenshot({path:path.join(checks,id+'-offline-front.png'),fullPage:false,timeout:60000});
   // Select a different camera, then the other world, using page controls only.
   for(const view of ['right','night']){
    await frame.evaluate(view=>{const select=document.querySelector('[data-view]');select.value=view;select.dispatchEvent(new Event('change',{bubbles:true}));},view);
    await frame.waitForFunction(view=>document.querySelector('[data-view]').value===view,view);
    const camera=await frame.evaluate(()=>document.getElementById('suzume-full-scene').inspectModel().camera.position.toArray());
    if(view==='right'&&JSON.stringify(camera)===JSON.stringify(state.initialCamera))throw Error('Camera did not move');
    await page.screenshot({path:path.join(checks,id+'-offline-'+view+'.png'),timeout:60000});
   }
   const door=await frame.evaluate(()=>{
    const select=document.querySelector('[data-view]');select.value='close';select.dispatchEvent(new Event('change',{bubbles:true}));
    const b=document.querySelector('[data-door]');const before=b.getAttribute('aria-pressed');b.click();return {before,after:b.getAttribute('aria-pressed')};
   });
   if(door.before===door.after)throw Error('Door toggle did not change state: '+id);
   report.scenes.push({id,...state,doorToggle:door});
  }
  if(await page.locator('[data-scene="renders"]').count()){
   await page.evaluate(()=>document.querySelector('[data-scene="renders"]').click());await waitReady();
   await page.waitForFunction(()=>[...document.querySelectorAll('.gallery img')].every(i=>i.complete&&i.naturalWidth>0));
   report.gallery=await page.evaluate(()=>[...document.querySelectorAll('.gallery img')].map(i=>({alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})));
   const dl=page.waitForEvent('download');await page.evaluate(()=>document.querySelector('.gallery button').click());
   const download=await dl;const location=await download.path();
   report.renderDownloadSha256=crypto.createHash('sha256').update(fs.readFileSync(location)).digest('hex');
   const source=fs.readFileSync(path.join(__dirname,'poster-arches-v49/poster-front-v49.png'));
   if(report.renderDownloadSha256!==crypto.createHash('sha256').update(source).digest('hex'))throw Error('Render download byte mismatch');
  }
  if(await page.locator('[data-download-model]').count()){
   const pending=page.waitForEvent('download',{timeout:120000});await page.evaluate(()=>document.querySelector('[data-download-model]').click());
   const download=await pending;const location=await download.path();
   report.nativeDownloadSha256=crypto.createHash('sha256').update(fs.readFileSync(location)).digest('hex');
   const source=fs.readFileSync(path.join(__dirname,'poster-v38/Suzume_dual_scene_v38.blend'));
   if(report.nativeDownloadSha256!==crypto.createHash('sha256').update(source).digest('hex'))throw Error('Blender download byte mismatch');
  }
  report.final=await page.evaluate(()=>window.__offline);
  if(report.final.missing.length||report.errors.length||report.requests.length||report.consoleErrors.length)throw Error('Offline browser validation failed: '+JSON.stringify({missing:report.final.missing,errors:report.errors,network:report.requests,console:report.consoleErrors}));
  report.passed=true;
 }catch(error){
  report.failure=String(error);console.error('FAILED',report.failure);process.exitCode=1;
  if(currentPage){try{report.debug=await currentPage.evaluate(()=>({info:window.__offline,status:document.querySelector('#archive-status')?.textContent,childText:document.querySelector('iframe')?.contentDocument?.querySelector('.full-loading')?.textContent}));await currentPage.screenshot({path:path.join(checks,name+'-failure.png'),timeout:20000});}catch(e){report.debugError=String(e);}}
 }
 finally{await browser.close();fs.writeFileSync(path.join(checks,name+'.json'),JSON.stringify(report,null,2));console.log('REPORT',JSON.stringify(report));}
})();
