"""Native artifact/content checks and recorded human QA finding; no models/render."""
import json,hashlib
from pathlib import Path
from zipfile import ZipFile
from pptx import Presentation

ROOT=Path('/runtime/stage-closure');load=lambda p:json.loads(p.read_text('utf-8'))
flow=load(ROOT/'description-flow-evidence.json');before=Path('/runtime/runs')/flow['generated_run_id'];after=Path('/runtime/runs')/flow['revised_run_id']
deck=load(before/'deck-spec.json');revised=load(after/'deck-spec.json');checks=[]
def test(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
presentation=Presentation(after/'deck.pptx');chart=next(s.chart for slide in presentation.slides for s in slide.shapes if s.has_chart)
test('actual_native_categories_preserved',[c.label for c in chart.plots[0].categories]==['A楼','B楼','C楼'])
test('actual_native_series_values',sorted(tuple(s.values) for s in chart.series)==sorted([(100.,80.,60.),(90.,72.,54.)]))
test('actual_series_semantic_names',any('基线' in s.name and tuple(s.values)==(100.,80.,60.) for s in chart.series) and any('本期' in s.name and tuple(s.values)==(90.,72.,54.) for s in chart.series))
tables=[s.table for slide in presentation.slides for s in slide.shapes if s.has_table]
native_cells=[c.text for table in tables for row in table.rows for c in row.cells]
test('native_table_data_and_units',all(any(t in c for c in native_cells) for t in ['A楼','B楼','C楼','100','80','60','90','72','54','千瓦时']))
with ZipFile(before/'deck.pptx') as a,ZipFile(after/'deck.pptx') as b:
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    test('only_selected_slide_part_changed',changed==['ppt/slides/slide1.xml'])
test('selected_source_bytes_unchanged',(before/'approved-source-result.json').read_bytes()==(after/'approved-source-result.json').read_bytes())
test('final_qa_p0_and_gate',load(after/'quality-report.json')['p0_issue_count']==0 and not load(after/'completion-decision.json')['final_allowed'])
original_body=next(e for e in deck['slides'][0]['elements'] if e['role']=='body')
final_body=next(e for e in revised['slides'][0]['elements'] if e['object_id']==original_body['object_id'])
needles=['制作中文PPT','制作中文 PPT','偏好','软预算']
bad=[t for t in original_body['text'] if any(word in t for word in needles)]
test('observed_instruction_leak_fixed',len(bad)>0 and not any(word in '\n'.join(final_body['text']) for word in needles))
issue={'parent_run_id':before.name,'revised_run_id':after.name,'slide_id':deck['slides'][0]['slide_id'],'object_id':original_body['object_id'],
       'type':'task_instruction_leak','severity':'P1','measurement':{'instruction_paragraph_count':len(bad),'observed_text':bad},
       'threshold':{'maximum':0},'action':{'kind':'local_text_revision','preserve_other_objects':True},
       'detected_by':'agent_visual_inspection_of_actual_render','automatic_detection':'not_implemented_for_this_case',
       'evidence':{'before_png':'render/slide-1.png','before_sha256':hashlib.sha256((before/'render/slide-1.png').read_bytes()).hexdigest(),
                   'after_png':'render/slide-1.png','after_sha256':hashlib.sha256((after/'render/slide-1.png').read_bytes()).hexdigest()},
       'status':'corrected_by_explicit_local_revision','original_qa_reports_preserved':True}
(ROOT/'manual-visual-issue.json').write_text(json.dumps(issue,ensure_ascii=False,indent=2)+'\n','utf-8')
report={'passed':True,'checks':checks,'model_calls':0,'render_calls':0,'generated_run_id':before.name,'revised_run_id':after.name,
        'native_slides':len(presentation.slides),'native_objects':sum(len(s.shapes) for s in presentation.slides),'changed_parts':changed,
        'scope':'Actual native values/fidelity and visual-found issue correction; full baseline/semantic QA remains incomplete.'}
(ROOT/'delivery-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(report,ensure_ascii=False))
