"""Run bounded real Poppler and candidate-integrity checks, without model calls."""
import copy
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from yoloongppt.errors import TaskError
from yoloongppt.input_formats import parse_pdf
from yoloongppt.pdf_evidence import enhance_pdf


ROOT = Path('/workspace')
output = Path('/runtime/source-semantic-pdf')/('component-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(uuid4())[:8])
output.mkdir(parents=True,exist_ok=False)
checks=[]


def check(name, condition, observed=None):
    if not condition:
        (output/'failure.json').write_text(json.dumps({'passed':False,'failed_check':name,'completed_checks':checks,
            'model_calls':0,'source_sha256':hashlib.sha256((ROOT/'src/yoloongppt/pdf_evidence.py').read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
    assert condition, name
    checks.append({'id':name,'passed':True,'observed':observed})


def pdf_fixture():
    """Explicit artificial 4-page PDF with ruled grid, parallel prose, continuation, image-only page."""
    objects=[]
    def obj(data):
        objects.append(data);return len(objects)
    obj(b'');obj(b'')
    font=obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    image_data=bytes([220,40,40,40,200,40,40,40,220,220,200,40])*8
    image=obj(f'<< /Type /XObject /Subtype /Image /Width 8 /Height 4 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(image_data)} >>\nstream\n'.encode()+image_data+b'\nendstream')
    pages=[]
    for page in range(4):
        commands=[]
        def text(x,y,value,size=12):
            value=value.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            commands.append(f'BT /F1 {size} Tf 1 0 0 1 {x} {800-y} Tm ({value}) Tj ET')
        if page in {0,2}:
            text(40,40,'Artificial PDF source: geometry candidates',20)
            data=[['Metric','2025','2026'],['Energy','100','100'],['Water','45','40'],['Emissions','8','8']]
            for row,values in enumerate(data):
                for x,value in zip([40,200,340],values):text(x,120+row*40,value)
            if page == 0:
                commands.append('40 545 m 480 545 l S 40 665 m 480 665 l S')
        elif page == 1:
            text(40,40,'Artificial parallel columns, not confirmed table',20)
            for row in range(3):
                text(40,120+40*row,['Left note A','Left note B','Left note C'][row])
                text(340,120+40*row,['Right note A','Right note B','Right note C'][row])
        else:
            commands.append('q 200 0 0 100 40 600 cm /Im1 Do Q')
        stream='\n'.join(commands).encode('ascii')
        content=obj(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
        pages.append(obj(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 {font} 0 R >> /XObject << /Im1 {image} 0 R >> >> /Contents {content} 0 R >>'.encode()))
    objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>'
    objects[1]=f'<< /Type /Pages /Kids [{" ".join(str(p)+" 0 R" for p in pages)}] /Count 4 >>'.encode()
    raw=b'%PDF-1.4\n';offsets=[]
    for index,data in enumerate(objects,1):
        offsets.append(len(raw));raw+=str(index).encode()+b' 0 obj\n'+data+b'\nendobj\n'
    start=len(raw)
    raw+=f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()+b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    raw+=f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    return raw


raw=pdf_fixture();(output/'artificial-source.pdf').write_bytes(raw)
document,segments,base_warnings=parse_pdf(raw,'source_pdf_fixture','asset_pdf_fixture')
before=copy.deepcopy((document,segments))
enhanced,enriched,warnings=enhance_pdf(document,segments)
check('real_poppler_four_pages',len(document['pages'])==4)
check('arguments_not_mutated',(document,segments)==before)
check('raw_text_and_anchor_exact',[(s['raw_text'],s['anchor']) for s in segments]==[(s['raw_text'],s['anchor']) for s in enriched])
check('all_original_text_words_geometry_preserved',all(
    all(block[k]==enhanced['pages'][pi]['blocks'][bi][k] for k in ['kind','text','lines','bbox','coordinate_space'])
    for pi,page in enumerate(document['pages']) for bi,block in enumerate(page['blocks'])))
original_words=[(pi+1,bi,li,wi,w['text'],w['bbox']) for pi,p in enumerate(document['pages']) for bi,b in enumerate(p['blocks']) for li,l in enumerate(b['lines']) for wi,w in enumerate(l['words'])]
inventory=[(p['page_number'],w['block_index'],w['line_index'],w['word_index'],w['text'],w['bbox']) for p in enhanced['pages'] for w in p['evidence_candidates']['word_inventory']]
check('one_distinct_anchor_per_original_word',original_words==inventory and len({w['word_id'] for p in enhanced['pages'] for w in p['evidence_candidates']['word_inventory']})==len(original_words),len(original_words))
check('word_native_locators_include_page_block_line_word',all(',line=' in w['anchor']['native_locator'] and ',word=' in w['anchor']['native_locator'] and w['anchor']['locator']['page_number']==p['page_number'] for p in enhanced['pages'] for w in p['evidence_candidates']['word_inventory']))
grid=enhanced['pages'][0]['evidence_candidates']['table_candidates']
check('real_grid_four_rows_three_columns',any(g['row_count']==4 and g['column_count']==3 for g in grid),[(g['row_count'],g['column_count']) for g in grid])
chosen=next(g for g in grid if g['row_count']==4 and g['column_count']==3)
check('grid_cells_keep_numbers_and_units_as_raw_quotes',[[c['quote'] for c in r['cells']] for r in chosen['rows']]==[['Metric','2025','2026'],['Energy','100','100'],['Water','45','40'],['Emissions','8','8']])
check('duplicate_100_and_8_are_distinct',len([w for w in enhanced['pages'][0]['evidence_candidates']['word_inventory'] if w['text']=='100'])==2 and len([w for w in enhanced['pages'][0]['evidence_candidates']['word_inventory'] if w['text']=='8'])==2)
check('no_cell_reuses_word_in_same_grid',len([wid for r in chosen['rows'] for c in r['cells'] for wid in c['word_ids']])==len({wid for r in chosen['rows'] for c in r['cells'] for wid in c['word_ids']}))
check('ruled_pdf_does_not_invent_rule_evidence',chosen['rule_line_evidence']=='not_parsed' and chosen['table_semantics']=='unconfirmed')
parallel=enhanced['pages'][1]['evidence_candidates']
check('parallel_prose_not_confirmed_table',all(g['interpretation_options']==['table','parallel_columns'] and g['table_semantics']=='unconfirmed' for g in parallel['table_candidates']) and bool(parallel['table_candidates']))
check('parallel_cells_not_concatenated',any([c['quote'] for c in r['cells']]==['Left note A','Right note A'] for r in parallel['row_candidates']))
check('parallel_reading_order_explicit',parallel['reading_order_status']=='ambiguous_parallel_columns')
check('continuation_not_joined_across_pages',all(g['page_number']==p['page_number'] and g['cross_page_merge']=='not_executed' for p in enhanced['pages'] for g in p['evidence_candidates']['table_candidates']))
check('heading_geometric_candidate_retains_quote',any(h['quote']=='Artificial PDF source: geometry candidates' and h['claim_status']=='candidate_not_semantic_truth' for h in enhanced['pages'][0]['evidence_candidates']['heading_candidates']))
check('image_only_page_not_called_blank_or_ocr_completed',not enhanced['pages'][3]['evidence_candidates']['word_inventory'] and any(w['code']=='PDF_PAGE_NO_TEXT_EVIDENCE' and w['page_number']==4 for w in warnings))
images=enhanced['image_inventory']['images']
check('real_pdfimages_inventory_fields',len(images)==1 and images[0]['page_number']==4 and images[0]['width_px']==8 and images[0]['height_px']==4 and images[0]['type']=='image' and images[0]['object_id']['number']==4 and images[0]['density_ppi']['x']>0,images)
check('image_list_no_fake_position_asset_ocr_relation',all(i['bbox'] is None and i['asset_id'] is None and i['relationship_status']=='unknown' for i in images) and enhanced['image_inventory']['ocr_status']=='not_executed')
check('source_context_on_every_segment',all(s['metadata']['source_context']['source_kind']=='pdf' and s['metadata']['source_context']['source_anchor']==s['anchor'] for s in enriched))
check('context_quotes_point_to_original_block',all(c['quote'] in next(s['raw_text'] for s in segments if s['anchor']==c['source_anchor']) for s in enriched for r in s['metadata']['source_context']['row_candidates'] for c in r['cells']))
check('candidate_word_refs_all_registered',all(set(c['word_ids']) <= {w['word_id'] for w in p['evidence_candidates']['word_inventory']} for p in enhanced['pages'] for r in p['evidence_candidates']['row_candidates'] for c in r['cells']))


def reject(name, mutate):
    bad_doc,bad_segments=copy.deepcopy((document,segments));mutate(bad_doc,bad_segments)
    try:enhance_pdf(bad_doc,bad_segments)
    except TaskError as exc:check(name,exc.code=='PDF_EVIDENCE_INVALID' and exc.component=='PdfEvidence',exc.result('component-fixture')['error'])
    else:raise AssertionError(name+' accepted')


reject('fail_missing_page_geometry',lambda d,s:d['pages'][0].pop('width'))
reject('fail_nan_word_coordinate',lambda d,s:(d['pages'][0]['blocks'][0]['lines'][0]['words'][0]['bbox'].update(xMin=float('nan')),s[0]['data']['lines'][0]['words'][0]['bbox'].update(xMin=float('nan'))))
reject('fail_inverted_word_coordinate',lambda d,s:(d['pages'][0]['blocks'][0]['lines'][0]['words'][0]['bbox'].update(xMax=-1),s[0]['data']['lines'][0]['words'][0]['bbox'].update(xMax=-1)))
reject('fail_changed_segment_text',lambda d,s:s[0].update(raw_text='changed 999'))
reject('fail_anchor_wrong_page_number',lambda d,s:s[0]['anchor']['locator'].update(page_number=99))
reject('fail_duplicate_block_anchor',lambda d,s:s.append(copy.deepcopy(s[0])))
reject('fail_missing_block_segment',lambda d,s:s.pop(0))
reject('fail_missing_native_locator',lambda d,s:s[0]['anchor'].pop('native_locator'))
for name,raw_inventory,expected in [('inventory_unavailable',None,'unavailable'),('inventory_header_unknown','new format\n1 0 image 8 4 rgb','unrecognized'),('inventory_malformed_row',document['image_inventory_raw']+'\n9 0 image unknown\n','partial')]:
    d=copy.deepcopy(document);d['image_inventory_raw']=raw_inventory
    result,_,notes=enhance_pdf(d,segments)
    check(name,result['image_inventory']['status']==expected and bool(notes))
d=copy.deepcopy(document);d['image_inventory_raw']+='\n'+images[0]['raw_row']+'\n'
result,_,notes=enhance_pdf(d,segments)
check('duplicate_image_rows_preserved_not_overwritten',len(result['image_inventory']['images'])==2 and any(w['code']=='PDF_IMAGE_INVENTORY_DUPLICATE' for w in notes))
d,s=copy.deepcopy((document,segments)); target=next(i for i,b in enumerate(d['pages'][0]['blocks']) if len(b['lines'][0]['words'])>1)
d['pages'][0]['blocks'][target]['lines'][0]['words'].reverse()
line=d['pages'][0]['blocks'][target]['lines'][0];line['text']=' '.join(w['text'] for w in line['words'])
block=d['pages'][0]['blocks'][target];block['text']='\n'.join(l['text'] for l in block['lines'])
ss=next(x for x in s if x['anchor']['locator']['page_index']==0 and x['anchor']['locator']['element_index']==target)
ss['data']=copy.deepcopy(block);ss['raw_text']=block['text']
result,_,notes=enhance_pdf(d,s)
check('reversed_word_order_preserved_and_not_regrouped',any(w['code']=='PDF_LINE_ORDER_AMBIGUOUS' for w in notes) and result['pages'][0]['blocks'][target]['lines'][0]['words']==line['words'])
try:parse_pdf(b'%PDF-1.4\ncorrupt','source_pdf_fixture','asset_pdf_fixture')
except TaskError as exc:check('real_corrupt_pdf_has_structured_failure',exc.code=='PDF_PASSWORD_OR_CORRUPT',exc.code)
else:raise AssertionError('corrupt pdf accepted')

for name,d in [('page_candidate_limit',{'format':'pdf','pages':[{'blocks':[]}] * 257}),
               ('word_candidate_limit',{'format':'pdf','pages':[{'blocks':[{'lines':[{'words':[{}] * 4097}]}]}]})]:
    try:enhance_pdf(d,[])
    except TaskError as exc:check(name,exc.code=='PDF_EVIDENCE_LIMIT',exc.code)
    else:raise AssertionError(name)

for name,value in [('parsed-before.json',{'document':document,'segments':segments,'warnings':base_warnings}),('enhanced.json',{'document':enhanced,'segments':enriched,'warnings':warnings})]:
    (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run(['pdftoppm','-f','1','-l','1','-r','90','-png',str(output/'artificial-source.pdf'),str(output/'page')],check=True,capture_output=True,timeout=30)
report={'passed':True,'checks':checks,'model_calls':0,'real_tools':['Poppler pdfinfo','Poppler pdftotext -bbox-layout','Poppler pdfimages -list','Poppler pdftoppm'],
        'task_ids':['TASK-IN-004','TASK-IN-016','TASK-SYS-003'],'requirement_ids':['IN-004','IN-016','SYS-003'],'ac_ids':['AC-003'],
        'versions':{'poppler':subprocess.run(['pdftotext','-v'],capture_output=True,text=True).stderr.strip()},
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/yoloongppt/pdf_evidence.py',ROOT/'validation/verify-pdf-evidence.py',ROOT/'src/yoloongppt/input_formats.py']},
        'fixture_sha256':hashlib.sha256(raw).hexdigest(),'word_count':len(original_words),
        'boundary':'Artificial component fixture and real local Poppler parsing only. No semantic truth, OCR, model summary, product generation, image extraction, visual QA, or full AC-003 acceptance.'}
(output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(checks),'report':str(output/'report.json'),'word_count':len(original_words)},ensure_ascii=False))
