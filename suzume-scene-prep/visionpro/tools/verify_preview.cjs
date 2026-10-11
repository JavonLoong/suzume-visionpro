const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),out=path.join(root,'validation');
const isolated=fs.mkdtempSync(path.join(os.tmpdir(),'SuzumeVisionPortal-'));
const target=path.join(isolated,'portal.html');
fs.copyFileSync(path.join(root,'铃芽之旅_VisionPro适配_离线预览.html'),target);
const report={networkDisabled:true,isolatedFile:target,requests:[],errors:[],consoleErrors:[],states:[]};
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-unsafe-swiftshader']});
 try{
  const context=await browser.newContext({viewport:{width:1360,height:980},deviceScaleFactor:1,offline:true});
  const page=await context.newPage();
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()))report.requests.push(r.url());});
  await page.goto(pathToFileURL(target).href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.portalPreviewReady||window.portalPreviewError,undefined,{timeout:90000});
  const error=await page.evaluate(()=>window.portalPreviewError);if(error)throw Error(error);
  async function capture(name){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));report.states.push({name,...await page.evaluate(()=>window.portalPreview.getState())});await page.screenshot({path:path.join(out,name+'.png')});}
  await capture('portal-front');
  await page.evaluate(()=>window.portalPreview.setPose({x:1.3,y:1.7,z:2.5}));
  await capture('portal-side');
  await page.evaluate(()=>window.portalPreview.setMode(true));
  await capture('world-full');
  if(report.requests.length||report.errors.length||report.consoleErrors.length)throw Error(JSON.stringify(report));
  report.pass=true;
 }finally{fs.writeFileSync(path.join(out,'preview_validation.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
