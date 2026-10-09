"""Bounded original source/EvidenceStore checks in the actual Docker core."""
import copy,hashlib,json,sqlite3,subprocess,sys,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
from yoloongppt.errors import TaskError
from yoloongppt.evidence import EvidenceStore
from yoloongppt.schemas import SchemaRegistry,ROOT
from yoloongppt.sources import inspect_sources,PARSER_VERSION

schemas=SchemaRegistry();store=EvidenceStore('/runtime/source-validation-'+str(uuid4())+'.sqlite3');cases=[]
task=json.loads((ROOT/'validation/core-task.json').read_text(encoding='utf-8'))
task['task_id']='task_'+str(uuid4())
task['sources'][0]['source_id']='source_'+str(uuid4());task['sources'][0]['kind']='markdown'
raw=json.loads((ROOT/'contracts/text-document.fixtures.json').read_text(encoding='utf-8'))['fixtures'][0]['input']['raw_markdown']
task['sources'][0]['content']=raw

def record(id,condition,observed):
 assert condition,id
 cases.append({'id':id,'passed':True,'observed':observed})

def run(t):return inspect_sources(t,schemas,store,'trace_'+str(uuid4()))

def error_case(id,mutate,expected):
 t=copy.deepcopy(task);mutate(t)
 with store.connect() as db:before=db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]
 try:run(t)
 except TaskError as e:record(id,e.code==expected,e.code)
 else:raise AssertionError(id+' unexpectedly accepted')
 with store.connect() as db:assert db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]==before

normal=run(task);blocks=normal['documents'][0]['document']['document']['blocks']
record('original_Markdown_fixture',len(normal['evidence'])==7 and [b['kind'] for b in blocks]==['heading','paragraph','list','code_block','table','blockquote','footnote_definition'],{'block_kinds':[b['kind'] for b in blocks],'raw_text_preserved':normal['documents'][0]['document']['raw_markdown']==raw})
record('table_values_preserved',blocks[4]['rows'][0][1]['content'][0]['text']=='20%',{'data':'20%','rows':1,'columns':2})
record('nested_list_preserved',blocks[2]['items'][0]['blocks'][1]['kind']=='list','Nested list remains structural.')
t=copy.deepcopy(task);t['sources'][0].update(kind='text',content='# 纯文本\n\n保留🙂数字20%。\n');r=run(t)
record('plain_text_document',len(r['documents'][0]['document']['document']['blocks'])==2 and r['documents'][0]['document']['document']['blocks'][0]['kind']=='paragraph','Plain text is a TextDocumentModel; no Markdown inference.')
record('inline_link_citation_preserved',any(n['kind']=='link' for n in blocks[1]['content']) and any(n['kind']=='citation' for n in blocks[1]['content']),'Link and footnote reference retained.')
for e in normal['evidence']:
 a=e['anchor']['locator'];assert e['raw_text']==raw[a['start_char']:a['end_char']]
record('anchor_raw_roundtrip',True,{'segments':len(normal['evidence']),'offset_unit':'unicode_code_points'})
replay=run(task)
record('stable_evidence_replay',[e['evidence_id'] for e in replay['evidence']]==[e['evidence_id'] for e in normal['evidence']],'IDs remain identical on replay.')
e=normal['evidence'][0];record('lookup_by_ID',store.get(e['evidence_id'])==e,'Stored raw text/anchor/hash/parser version round-trip.')
record('canonical_SourceEvidence',e['content']==e['raw_text'] and e['data']['kind']=='heading' and e['confidence'] is None and e['metadata']['semantic_claim_status']=='not_inferred','Canonical content/data/asset_ref/confidence/metadata retained; no inferred truth confidence.')
changed=copy.deepcopy(task);changed['sources'][0]['content']='# 改后原文\n';after=run(changed)
record('immutable_old_snapshot',store.get(e['evidence_id'])==e and after['evidence'][0]['source_hash']!=e['source_hash'],'Old evidence retained, changed source snapshot stored separately.')
duplicate=copy.deepcopy(task);duplicate['sources'].append({**duplicate['sources'][0],'source_id':'source_'+str(uuid4())})
dups=run(duplicate)
record('duplicate_sources_kept',len(dups['source_bundle']['bundle']['sources'])==2 and len(dups['source_bundle']['bundle']['duplicate_groups'])==1 and dups['source_bundle']['coverage'][3]['status']=='unsupported','Hash candidates only; no source removal or claim of no semantic conflicts.')
for name,text,kind in [('unused_footnote','正文\n\n[^unused]: 未引用原文\n','footnote_definition'),('indented_code','    print("中文")\n','code_block'),('CRLF_and_emoji','# 中文🙂\r\n\r\n段落8%。\r\n','heading'),('UTF8_BOM','\ufeff# 标题\n','heading')]:
 t=copy.deepcopy(task);t['sources'][0]['source_id']='source_'+str(uuid4());t['sources'][0]['content']=text;r=run(t)
 doc=r['documents'][0]['document'];record(name,doc['raw_markdown']==text and any(b['kind']==kind for b in doc['document']['blocks']),{'raw_preserved':True,'kind':kind})
error_case('empty',lambda t:t['sources'][0].update(content='  \n'),'INPUT_EMPTY')
error_case('unsupported_DOCX',lambda t:t['sources'][0].update(kind='docx'),'INPUT_UNSUPPORTED')
error_case('binary_disguised',lambda t:t['sources'][0].update(content='text\x00binary'),'INPUT_FORMAT_DISGUISED')
error_case('table_extra_cells',lambda t:t['sources'][0].update(content='| a | b |\n| --- | --- |\n| 1 | 2 | 3 |\n'),'MARKDOWN_TABLE_WIDTH_MISMATCH')
error_case('table_missing_cells',lambda t:t['sources'][0].update(content='| a | b |\n| --- | --- |\n| 1 |\n'),'MARKDOWN_TABLE_WIDTH_MISMATCH')
error_case('footnote_duplicate',lambda t:t['sources'][0].update(content='[^a]: first\n\n[^a]: second\n'),'MARKDOWN_FOOTNOTE_DUPLICATE')
error_case('unsupported_rule',lambda t:t['sources'][0].update(content='---\n'),'MARKDOWN_BLOCK_UNSUPPORTED')
Path('/runtime/source-validation-file.md').write_text(raw,encoding='utf-8')
file_task=copy.deepcopy(task);file_task['sources'][0].pop('content');file_task['sources'][0]['locator']='/runtime/source-validation-file.md';file_task['sources'][0]['source_id']='source_'+str(uuid4())
with ThreadPoolExecutor(max_workers=2) as pool:parallel=list(pool.map(run,[file_task,file_task]))
record('concurrent_file_replay',parallel[0]['evidence']==parallel[1]['evidence'] and parallel[0]['documents']==parallel[1]['documents']
       and all(e['anchor']['asset_id'] is not None and e['raw_asset_refs']==[e['anchor']['asset_id']] for e in parallel[0]['evidence']),'Transaction resolves stable asset/evidence IDs for concurrent identical input.')
def change_origin(t):t['sources'][0].pop('content');t['sources'][0]['locator']='/runtime/source-validation-file.md'
error_case('source_origin_identity_conflict',change_origin,'SOURCE_ID_ORIGIN_CHANGED')
Path('/runtime/source-validation-bad.txt').write_bytes(b'\xff')
def file_location(t,path):t['sources'][0].pop('content');t['sources'][0]['locator']=path
error_case('missing_file',lambda t:file_location(t,'/runtime/does-not-exist.md'),'INPUT_NOT_FOUND')
error_case('outside_root',lambda t:file_location(t,'/etc/passwd'),'SOURCE_PATH_OUTSIDE_ROOT')
error_case('wrong_suffix',lambda t:file_location(t,'/runtime/evidence.sqlite3'),'INPUT_UNSUPPORTED')
error_case('non_UTF8_file',lambda t:file_location(t,'/runtime/source-validation-bad.txt'),'INPUT_ENCODING_UNSUPPORTED')
error_case('ambiguous_input',lambda t:t['sources'][0].update(locator='/runtime/source-validation-file.md'),'SOURCE_LOCATION_AMBIGUOUS')

def http(path,body=None):
 data=None if body is None else json.dumps(body,ensure_ascii=False).encode('utf-8')
 request=urllib.request.Request('http://127.0.0.1:8000'+path,data=data,headers={'Content-Type':'application/json'})
 try:response=urllib.request.urlopen(request,timeout=20)
 except urllib.error.HTTPError as e:response=e
 result=json.loads(response.read());assert response.headers['X-Trace-Id']==result['trace_id'];return response.status,result

deadline=time.monotonic()+30
while True:
 try:http('/health');break
 except urllib.error.URLError:
  if time.monotonic()>deadline:raise
  time.sleep(1)
Path('/runtime/source-validation-task.json').write_text(json.dumps(task,ensure_ascii=False),encoding='utf-8')
status,api=http('/inspect',task);record('HTTP_inspect',status==200 and len(api['evidence'])==7,{'evidence_count':7,'task_id':task['task_id']})
cli=subprocess.run([sys.executable,'-m','yoloongppt','inspect','/runtime/source-validation-task.json'],capture_output=True,text=True,encoding='utf-8');c=json.loads(cli.stdout)
record('CLI_HTTP_same_evidence',cli.returncode==0 and c['evidence']==api['evidence'],'Same persistent evidence from both product entries.')
status,got=http('/evidence/'+api['evidence'][0]['evidence_id']);record('HTTP_evidence_lookup',status==200 and got['evidence']==api['evidence'][0],'ID query returns the same versioned evidence.')
status,got=http('/evidence/evidence_'+str(uuid4()));record('HTTP_missing_evidence',status==404 and got['error']['code']=='EVIDENCE_NOT_FOUND',got['error']['code'])
for package in ['markdown-it-py','mdit-py-plugins','mdurl']:
 from importlib.metadata import distribution
 dist=distribution(package);licenses=[p for p in dist.files if 'LICENSE' in str(p).upper() or 'COPYING' in str(p).upper()]
 record('license_'+package,bool(licenses),[{'path':str(p),'sha256':hashlib.sha256(dist.locate_file(p).read_bytes()).hexdigest()} for p in licenses])
inputs=list((ROOT/'src/yoloongppt').glob('*.py'))+[ROOT/x for x in ['requirements.lock','contracts/source-bundle.schema.json','contracts/text-document.schema.json','contracts/source-evidence.schema.json']]
report={'requirement_ids':['SYS-003','SYS-004','IN-001','IN-002','IN-014','IN-015','IN-016'],'passed':True,'cases':cases,'parser_version':PARSER_VERSION,'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'boundary':'Source component checks only. IN-001 semantic intent extraction remains pending; inline locations are containing block; remaining formats, fact/conflict extraction, generation/QA/revision/E2E not accepted.'}
Path('/runtime/source-runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
Path('/runtime/source-runtime-example.json').write_text(json.dumps(api,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'cases':len(cases),'evidence':7},ensure_ascii=False))
