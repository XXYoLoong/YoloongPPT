// Research instrumentation only: expose private readers in memory, never patch upstream files.
const fs = require('fs');
const path = require('path');
const Module = require('module');
const root = '/artifacts/main-skill/.venv/lib/python3.11/site-packages/deeppresenter/html2pptx';
const filename = path.join(root, 'html2pptx.js');
const loaded = new Module(filename, module);
loaded.filename = filename;
loaded.paths = Module._nodeModulePaths(root);
loaded._compile(fs.readFileSync(filename, 'utf8') + '\nmodule.exports.researchReaders={extractSlideData,getBodyDimensions};', filename);
const html2pptx = loaded.exports;
const { chromium } = loaded.require('playwright');
const PptxGenJS = loaded.require('pptxgenjs');
const out = '/workspace/research/P02/outputs/maps-probes';
(async () => {
  const browser = await chromium.launch({headless:true});
  const pres = new PptxGenJS(); pres.layout='LAYOUT_WIDE'; pres._layoutLocked=true;
  const captures=[];
  try {
    for (const name of ['native-table','raster-slot']) {
      const file=path.join(out,name+'.html');
      const page=await browser.newPage({viewport:{width:1280,height:720}});
      await page.goto('file://'+file); await page.evaluate(()=>document.fonts.ready);
      const dimensions=await html2pptx.researchReaders.getBodyDimensions(page);
      const ir=await html2pptx.researchReaders.extractSlideData(page);
      await page.screenshot({path:path.join(out,name+'.png')});
      await page.close();
      const converted=await html2pptx(file,pres);
      captures.push({name,dimensions,ir,returned_placeholders:converted.placeholders});
    }
  } finally { await browser.close(); }
  await pres.writeFile({fileName:path.join(out,'objects.pptx')});
  let svgFailure;
  try { await html2pptx(path.join(out,'svg-failure.html'),new PptxGenJS()); svgFailure={rejected:false}; }
  catch (error) { svgFailure={rejected:true,error:error.message,stack:error.stack}; }
  fs.writeFileSync(path.join(out,'svg-failure.json'),JSON.stringify(svgFailure,null,2)+'\n');
  fs.writeFileSync(path.join(out,'dom-ir.json'),JSON.stringify({instrumentation:'private reader exports appended in memory; official conversion unchanged; pre-CDP font IR',captures},null,2)+'\n');
  console.log(JSON.stringify({ok:true,pages:captures.length,placeholder_counts:captures.map(c=>c.returned_placeholders.length)}));
})().catch(error=>{console.error(error.stack);process.exit(1);});
