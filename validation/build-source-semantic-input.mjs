// Artificial input data for IN-008 / AC-005, never a real business report.
import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT/validation/source-semantic-artifacts/integration-input';
await fs.mkdir(root,{recursive:true});
const w=Workbook.create(),time=w.worksheets.add('月度数据'),category=w.worksheets.add('分类数据');
const serial=iso=>(Date.parse(iso+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000;
time.getRange('A1:D5').values=[['日期','用电量（千瓦时）','降低比例（%）','性质'],
 [serial('2026-01-01'),1200,.08,'人工验证数据，非真实业务'],
 [serial('2026-02-01'),1300,.09,'人工验证数据，非真实业务'],
 [serial('2026-03-01'),1250,.10,'人工验证数据，非真实业务'],
 ['三个月合计',null,null,'人工验证数据，非真实业务']];
time.getRange('A2:A4').setNumberFormat('yyyy-mm-dd');
time.getRange('B2:B5').setNumberFormat('0" 千瓦时"');
time.getRange('C2:C4').setNumberFormat('0%');
time.getRange('B5').formulas=[['=SUM(B2:B4)']];
category.getRange('A1:C4').values=[['分类','用电量（千瓦时）','性质'],['A楼',90,'人工验证数据，非真实业务'],['B楼',72,'人工验证数据，非真实业务'],['C楼',54,'人工验证数据，非真实业务']];
category.getRange('B2:B4').setNumberFormat('0" 千瓦时"');
for(const [sheet,range] of [[time,'A1:D5'],[category,'A1:C4']]){
 const r=sheet.getRange(range);r.format.font.name='Noto Sans CJK SC';r.format.font.size=12;r.format.wrapText=true;
 r.format.borders={preset:'all',style:'thin',color:'#CBD5E1'};
 sheet.getRange('A1:D1').format.fill='#DBEAFE';sheet.getRange('A1:D1').format.font.bold=true;
 r.format.columnWidth=24;r.format.rowHeight=36;
}
w.recalculate();
const inspect=await w.inspect({kind:'region',sheetId:'月度数据',range:'A1:D5',maxChars:3500});
await fs.writeFile(`${root}/workbook-inspect.ndjson`,inspect.ndjson);
await fs.writeFile(`${root}/monthly-preview.png`,new Uint8Array(await(await w.render({sheetName:'月度数据',range:'A1:D5',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(`${root}/artificial-data.xlsx`);
await fs.writeFile(`${root}/fixture-identity.json`,JSON.stringify({kind:'artificial_validation_source',requirements:['IN-008','IN-016','AC-005'],
 expected:{dates:['2026-01-01','2026-02-01','2026-03-01'],monthly_kwh:[1200,1300,1250],sum_kwh:3750,percent_display:['8%','9%','10%'],categories:['A楼','B楼','C楼'],category_kwh:[90,72,54]},
 formula_cache:'Artifact Tool calculated fixture at export; product parser must not execute formulas or claim cache freshness.'},null,2));
console.log(JSON.stringify({xlsx:`${root}/artificial-data.xlsx`,sheets:2,expected_sum:3750,artificial:true}));
