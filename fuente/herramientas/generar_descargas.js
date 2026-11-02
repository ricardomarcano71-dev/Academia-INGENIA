// Genera la imagen (PNG) y el PDF de cada herramienta a partir de su "hoja" (?hoja).
// Uso: node fuente/herramientas/generar_descargas.js   (desde la raíz del repo; necesita Playwright + Chromium)
const {chromium}=require('playwright');const path=require('path');
const raiz=path.resolve(__dirname,'..','..'),dir=path.join(raiz,'herramientas');
// id: [ancho mm, alto mm]
const HOJAS={'tabla-periodica':[297,210],'tablas-multiplicar':[210,297]};
(async()=>{const b=await chromium.launch();
 for(const id of process.argv.slice(2).length?process.argv.slice(2):Object.keys(HOJAS)){const [w,h]=HOJAS[id];
  const pxw=Math.round(w/25.4*96),pxh=Math.round(h/25.4*96);
  const p=await b.newPage({viewport:{width:pxw,height:pxh},deviceScaleFactor:2.5});const errs=[];p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file://'+path.join(dir,id+'.html')+'?hoja');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(500);
  if(errs.length)throw new Error(id+': '+errs.join(' | '));
  await p.locator('#hoja').screenshot({path:path.join(dir,'descargas',id+'.png')});
  await p.pdf({path:path.join(dir,'descargas',id+'.pdf'),width:w+'mm',height:h+'mm',printBackground:true,margin:{top:0,right:0,bottom:0,left:0},pageRanges:'1'});
  console.log('listo',id);await p.close()}
 await b.close()})();
