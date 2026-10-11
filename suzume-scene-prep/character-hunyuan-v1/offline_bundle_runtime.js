/* Local single-file archive. No server, external scripts, or external assets. */
(() => {
  const config = window.OFFLINE_CONFIG;
  const cache = new Map();
  const urls = Object.create(null);
  const status = document.querySelector('#archive-status');
  const stage = document.querySelector('#archive-stage');
  const info = window.__offline = {ready:false, selected:null, errors:[], missing:[], requests:[]};
  window.__offlineBlobs = urls;
  let generation = 0;
  function message(text) { status.textContent = text; }
  async function blob(key) {
    if (cache.has(key)) return cache.get(key);
    const task = (async () => {
      const node = document.getElementById(config.assets[key]?.id);
      if (!node) throw new Error('缺少内嵌资源：' + key);
      const encoded = node.textContent.trim();
      const binary = atob(encoded);
      const bytes = new Uint8Array(binary.length);
      for (let n=0; n<binary.length; n++) bytes[n]=binary.charCodeAt(n);
      let data = new Blob([bytes]);
      if (config.assets[key].gzip) {
        if (!window.DecompressionStream) throw new Error('请使用新版 Chrome 或 Edge 打开此文件');
        data = await new Response(data.stream().pipeThrough(new DecompressionStream('gzip'))).blob();
      }
      const result = new Blob([data], {type:config.assets[key].mime});
      urls['/' + key] = URL.createObjectURL(result);
      node.remove();
      return result;
    })();
    cache.set(key,task);
    return task;
  }
  window.__offlineGetBlob = blob;
  window.__offlineChildStatus = (id, ready, error) => {
    if (id !== info.selected) return;
    if (error) {info.errors.push(error); message('载入失败：'+error);}
    else if (ready) {info.ready=true; message('已就绪 · 拖动旋转，滚轮缩放');}
  };
  function active(id) {
    for (const button of document.querySelectorAll('[data-scene]')) {
      button.setAttribute('aria-pressed', String(button.dataset.scene===id));
    }
  }
  function childBootstrap(scene) {
    return `<script>
      (()=>{
        const id=${JSON.stringify(scene.id)};
        const base=${JSON.stringify('https://suzume.offline/'+scene.source)};
        const originalFetch=window.fetch.bind(window);
        const resolve=input=>{
          const raw=typeof input==='string'?input:(input.url||String(input));
          if (/^(blob:|data:)/i.test(raw)) return raw;
          const key=decodeURIComponent(new URL(raw,base).pathname);
          const url=parent.__offlineBlobs[key];
          if(!url){parent.__offline.missing.push(key);throw Error('缺少内嵌资源：'+key);}
          parent.__offline.requests.push(key);
          return url;
        };
        window.__offlineResolve=resolve;
        window.fetch=(input,options)=>originalFetch(resolve(input),options);
        window.addEventListener('error',event=>parent.__offlineChildStatus(id,false,event.message));
        window.addEventListener('unhandledrejection',event=>parent.__offlineChildStatus(id,false,String(event.reason)));
        new MutationObserver(()=>{
          const root=document.getElementById('suzume-full-scene');
          if(root&&root.dataset.ready==='true')parent.__offlineChildStatus(id,true);
          const error=root&&root.querySelector('.full-loading');
          if(error&&!error.hidden&&error.textContent.includes('无法'))parent.__offlineChildStatus(id,false,error.textContent);
        }).observe(document.documentElement,{subtree:true,attributes:true,childList:true});
      })();
    <\/script>`;
  }
  async function showScene(id) {
    const token=++generation;
    const scene=config.scenes.find(item=>item.id===id);
    if(!scene)return;
    active(id); info.ready=false; info.selected=id;
    stage.replaceChildren();
    const placeholder=document.createElement('div'); placeholder.className='placeholder';
    placeholder.textContent='正在展开 '+scene.label+'…';stage.append(placeholder);
    message('正在读取文件内的模型与贴图…');
    try {
      let done=0;
      // Sequential inflation bounds the peak memory used by large geometry buffers.
      for(const key of scene.assets){
        if(token!==generation)return;
        await blob(key);
        placeholder.textContent='正在展开 '+scene.label+' · '+(++done)+' / '+scene.assets.length;
      }
      let html=await (await blob(scene.source)).text();
      html=html.replace(/<footer>[\s\S]*?<\/footer>/i,'');
      html=html.replace(/<title>[\s\S]*?<\/title>/i,'<title>'+scene.label+' · 离线版</title>');
      html=html.replace(/suzume-(poster|movie)-view-v(\d+)/g,'suzume-offline-$1-view-v$2');
      const scripts=[...html.matchAll(/<script\b[^>]*\bsrc="([^"]+)"[^>]*><\/script>/g)];
      for(const match of scripts){
        const key=scene.source.slice(0,scene.source.lastIndexOf('/')+1)+match[1];
        const body=(await (await blob(key)).text()).replace(/<\/script/gi,'<\\/script');
        html=html.replace(match[0],'<script>'+body+'<\/script>');
      }
      html=html.replace('(async()=>{','THREE.DefaultLoadingManager.setURLModifier(window.__offlineResolve);\n(async()=>{');
      html=html.replace('<script>',childBootstrap(scene)+'<script>');
      // Keep all original geometry and interaction code; only relocate its resources.
      html=html.replace('</main>',`<style>main{padding:10px 18px 14px}header{margin-bottom:10px}header h1{font-size:19px}#suzume-full-scene .full-stage{width:min(100%,calc((100vh - 150px)*.708))!important;max-height:none!important}#suzume-full-scene .full-stage.landscape{width:min(100%,calc((100vh - 150px)*1.333333))!important}#suzume-full-scene .full-stage.opening-reference{width:min(100%,calc((100vh - 150px)*1.541))!important}</style></main>`);
      if(token!==generation)return;
      const frame=document.createElement('iframe');frame.id='scene-frame';
      frame.title=scene.label+'，可自由旋转的三维场景';
      frame.srcdoc=html;stage.replaceChildren(frame);
      message('模型与贴图已读取，正在绘制场景…');
    }catch(error){
      info.errors.push(String(error));placeholder.textContent='载入失败：'+error.message;message('载入失败');
    }
  }
  async function showGallery(){
    const token=++generation;active('renders');info.selected='renders';info.ready=false;
    stage.replaceChildren();const gallery=document.createElement('div');gallery.className='gallery';stage.append(gallery);
    message('正在读取内嵌渲染图…');
    for(const picture of config.renders){
      await blob(picture.key);if(token!==generation)return;
      const figure=document.createElement('figure');const image=document.createElement('img');
      image.src=urls['/'+picture.key];image.alt=picture.label;
      const caption=document.createElement('figcaption');caption.textContent=picture.label;
      const save=document.createElement('button');save.textContent='保存原图';
      save.addEventListener('click',()=>download(picture.key,picture.name,save));
      figure.append(image,caption,save);gallery.append(figure);
    }
    info.ready=true;message('原始分辨率渲染图 · 可直接保存');
  }
  async function download(key,name,button){
    const label=button?.textContent;
    if(button){button.disabled=true;button.textContent='正在准备文件…';}
    try{
      await blob(key);const anchor=document.createElement('a');
      anchor.href=urls['/'+key];anchor.download=name;document.body.append(anchor);anchor.click();anchor.remove();
    }catch(error){info.errors.push(String(error));message(error.message);}
    finally{if(button){button.disabled=false;button.textContent=label;}}
  }
  for(const button of document.querySelectorAll('[data-scene]'))button.addEventListener('click',()=>button.dataset.scene==='renders'?showGallery():showScene(button.dataset.scene));
  document.querySelector('[data-download-model]')?.addEventListener('click',event=>download(config.model.key,config.model.name,event.currentTarget));
  document.querySelector('[data-fullscreen]')?.addEventListener('click',()=>document.fullscreenElement?document.exitFullscreen():stage.requestFullscreen());
  const requested=new URLSearchParams(location.search).get('scene');
  const initial=config.scenes.some(s=>s.id===requested)?requested:config.initial;
  if(initial==='renders')showGallery();else showScene(initial);
})();
