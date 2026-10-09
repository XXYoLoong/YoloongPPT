import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

// Execute in the already built, pinned upstream research copy inside Docker.
const sourceRoot=process.env.P04_SOURCE_ROOT??process.cwd();
const evidenceRoot=process.env.P04_EVIDENCE_ROOT??'/evidence';
const out=path.join(evidenceRoot,'validation');
const scratch=process.env.TMPDIR??'/tmp';
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const map=JSON.parse(await readFile(path.join(evidenceRoot,'template-map.json'),'utf8'));
const capability=JSON.parse(await readFile(path.join(evidenceRoot,'capability-map.json'),'utf8'));
await mkdir(out,{recursive:true});
await mkdir(scratch,{recursive:true});
assert.equal(map.commit,'c3605ebc487fc6c7d4f4139761e46d7021cd656c');
assert.equal(capability.commit,map.commit);
const references=[...map.source_modules,...map.templates.map(x=>x.source),...map.layouts.map(x=>x.source)];
for(const ref of references) assert.equal(hash(await readFile(path.join(sourceRoot,ref.path))),ref.sha256,ref.path);
assert.equal(new Set(capability.ppt_objects.map(x=>x.requirement_id)).size,30);
for(const item of [...map.templates,...map.layouts]) assert.deepEqual(JSON.parse(await readFile(path.join(sourceRoot,item.source.path),'utf8')),item.definition);
if(process.argv.includes('--static')){
  const code=await Promise.all(['src/core/engine/pptx-builder.ts','src/core/engine/ppt-adapter.ts','src/commands/create.ts'].map(p=>readFile(path.join(sourceRoot,p),'utf8')));
  for(const api of ['addChart','addTable','addNotes','addMedia','defineSlideMaster']) assert.ok(!code.some(s=>new RegExp('\\.'+api+'\\s*\\(').test(s)),api);
  assert.ok(code[0].includes('if (cursorY >= bottomLimit) break;'));
  const slotCode=await readFile(path.join(sourceRoot,'src/core/engine/slide-renderer.ts'),'utf8');
  for(const field of ['chartData','timelineData','comparisonItems']) assert.ok(!slotCode.includes(field));
  const report={requirement_ids:['RES-P04-04','RES-P04-05'],commit:map.commit,result:'static_passed',source_hashes_verified:references.length,templates:map.templates.length,layouts:map.layouts.length,ppt_object_records:30,
    confirmed:['assets equal pinned JSON','wrapper has no addChart/addTable/addNotes/addMedia/defineSlideMaster call','chart/timeline/comparison data not consumed by SLOT_MAP','writer contains height-limit break'],
    runtime_status:'not_executed_by_static_check',scope:'source research only; not runtime, product or AC acceptance'};
  await writeFile(path.join(out,'verify-res-p04-04-05-static.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
  process.exit(0);
}
const requireFromSource=createRequire(path.join(sourceRoot,'package.json'));
const JSZip=requireFromSource('jszip');
const load=async relative=>import(pathToFileURL(path.join(sourceRoot,'dist',relative)).href);
const {TemplateManager}=await load('core/template/template-manager.js');
const {LayoutLoader}=await load('core/engine/layout-loader.js');
const {SlideRenderer}=await load('core/engine/slide-renderer.js');
const {PPTXBuilder}=await load('core/engine/pptx-builder.js');
const tm=new TemplateManager(path.join(sourceRoot,'src/templates'));
const ll=new LayoutLoader(path.join(sourceRoot,'src/layouts'));
const renderer=new SlideRenderer(path.join(sourceRoot,'src/layouts'));
assert.deepEqual(await tm.list(),map.templates.map(x=>x.id));
assert.deepEqual(await ll.list(),map.layouts.map(x=>x.id).sort());
for(const item of map.templates){
  assert.deepEqual(await tm.get(item.id),item.definition);
  assert.equal((await tm.validate(item.id)).valid,true);
}
for(const item of map.layouts) assert.deepEqual(await ll.load(item.id),item.definition);
assert.equal(await tm.get('__missing__'),null);
assert.equal(await ll.load('__missing__'),null);
assert.deepEqual(ll.resolveVariables({color:'{{colors.missing}}'},{}),{color:'{{colors.missing}}'});
const invalidDir=path.join(scratch,'p04-invalid-layout');
await mkdir(invalidDir,{recursive:true});
await writeFile(path.join(invalidDir,'invalid.layout.json'),JSON.stringify({name:'invalid',root:{tagName:'div',style:{width:123}}}));
assert.equal(await new LayoutLoader(invalidDir).load('invalid'),null);
const template=await tm.get('tech');
const normalSlide={title:'P04_NORMAL_TITLE',layout:'bullet',bulletPoints:['P04_NORMAL_ONE','P04_NORMAL_TWO']};
const normalTree=renderer.render(normalSlide,await ll.load('bullet'),template);
const outputs=[];
async function buildAndInspect(name,tree){
  const builder=new PPTXBuilder(template);
  builder.addSlide(tree);
  const filename=path.join(out,name+'.pptx');
  await builder.build(filename);
  const raw=await readFile(filename);
  const zip=await JSZip.loadAsync(raw);
  const slideXml=await zip.file('ppt/slides/slide1.xml').async('string');
  const xmlParts=await Promise.all(Object.values(zip.files).filter(f=>!f.dir&&f.name.endsWith('.xml')).map(f=>f.async('string')));
  outputs.push({path:'validation/'+name+'.pptx',sha256:hash(raw),bytes:raw.length});
  return {zip,slideXml,allXml:xmlParts.join('\n')};
}
const normal=await buildAndInspect('template-normal',normalTree);
for(const text of [normalSlide.title,...normalSlide.bulletPoints]) assert.ok(normal.slideXml.includes(text));
const chartSlide={title:'P04_CHART_TITLE',layout:'chart',bulletPoints:['P04_CHART_BULLET'],chartData:{type:'bar',labels:['DATA_LABEL'],datasets:[{label:'SERIES_UNCONSUMED',data:[123]}]},speakerNotes:'P04_NOTES_UNCONSUMED'};
const chartTree=renderer.render(chartSlide,await ll.load('chart'),template);
assert.ok(!JSON.stringify(chartTree).includes('SERIES_UNCONSUMED'));
const chart=await buildAndInspect('chart-boundary',chartTree);
assert.ok(!Object.values(chart.zip.files).some(f=>!f.dir&&f.name.startsWith('ppt/charts/')));
assert.ok(!chart.allXml.includes('P04_NOTES_UNCONSUMED'));
const bullets=Array.from({length:60},(_,i)=>`P04_OVERFLOW_${String(i).padStart(2,'0')}_`+'long-content '.repeat(15));
const overflow=await buildAndInspect('overflow-boundary',renderer.render({title:'P04_OVERFLOW_TITLE',layout:'bullet',bulletPoints:bullets},await ll.load('bullet'),template));
const visible=bullets.filter(b=>overflow.slideXml.includes(b.split('long-content')[0])).length;
assert.ok(visible>0&&visible<bullets.length);
assert.ok(!overflow.slideXml.includes('P04_OVERFLOW_59_'));
const unknownTree=renderer.render({title:'test',layout:'custom',bulletPoints:[]},{name:'custom',description:'unknown slot',root:{tagName:'div',slot:'chartData',style:{}}},template);
assert.deepEqual(unknownTree.children,[]);
const blocker=path.join(scratch,'p04-output-blocker');
await writeFile(blocker,'not a directory');
const failing=new PPTXBuilder(template);
failing.addSlide(normalTree);
let outputFailure;
try{await failing.build(path.join(blocker,'output.pptx'));assert.fail('expected output-path failure');}
catch(error){assert.ok(['EEXIST','ENOTDIR'].includes(error.code));outputFailure={code:error.code,message:'output parent is a file'};}
const report={requirement_ids:['RES-P04-04','RES-P04-05'],task_ids:['TASK-RES-P04-04','VERIFY-RES-P04-04','TASK-RES-P04-05','VERIFY-RES-P04-05'],commit:map.commit,
  environment:{node:process.version,network:'Docker --network none',scope:'research runtime observation, not product selection'},
  source_hashes_verified:references.length,templates:map.templates.length,layouts:map.layouts.length,ppt_object_records:capability.ppt_objects.length,
  cases:{normal:'5 templates and 8 layouts match source; native text PPTX package produced',boundary:{unresolved_variable:'preserved',unknown_slot:'empty children',chart_data:'not consumed; no chart parts',speaker_notes:'requested content not written',overflow:{requested:60,written:visible,omitted:60-visible,reported_by_upstream:false}},failure:{missing_template:'null',missing_layout:'null',invalid_schema:'null',outputFailure}},
  outputs,reused_evidence:['validation/minimal-html-poc.pptx','validation/edge-nested-html-poc.pptx','validation/topic-route-normal.pptx','validation/verify-res-p04-02.json'],
  limitations:['No real model/Vision calls','No Office/LibreOffice raster rendering or editability review','No product runtime/CapabilityStatus or AC acceptance']};
await writeFile(path.join(out,'verify-res-p04-04-05.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({result:'passed',templates:5,layouts:8,objects:30,overflow:report.cases.boundary.overflow,outputFailure}));
