"""Record the actual live run without upgrading original acceptance."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'validation/native-capacity-live-artifacts'
current=base/'current-resumed'
def read(path):return json.loads(path.read_text('utf-8'))
report_path=ROOT/'validation/native-capacity-integration.json'
report=read(report_path)
checks=read(base/'current-driver/summary.json')
qa=read(current/'quality-report.json');completion=read(current/'completion-decision.json')
assert checks['run_id']=='468ac35a-eef5-424f-9585-2fa45ad6722a'
assert len(checks['checks'])==9 and all(c['passed'] for c in checks['checks'])
assert qa['p0_issue_count']==0 and completion['state']=='warning' and completion['final_allowed'] is False
manifest=read(current/'version-manifest.json')
for field in ('source_hashes','contract_hashes'):
    for path,expected in manifest.get(field,{}).items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,(field,path)
for name,expected in manifest['schemas'].items():
    assert hashlib.sha256((ROOT/'contracts'/name).read_bytes()).hexdigest()==expected,('schema',name)
note=('三个组件已接visual→narrative/adaptive→layout/compile→原生写入→实际render/QA。'
      '实际API新生成ad03ceec复用人工原始输入，真实事实/内容/图像审查调用，产出4页但标题分页产生2项P0；'
      '增加可见原表分页说明并预留容量后，恢复468ac35a逐字复用该真实事实/内容种子，重新写入/渲染/实际模型复审，'
      '9项集成检查通过：8个原生图片、完整混合长标题、14行表格、3→4页、模型种子来源复用与真实新审查。'
      '当前P0=0、5项警告保留，DEC040=warning/final_allowed=false，完整原验收未通过。'
      '模板68/图库32/自适应161各历史版本，模板2/图库5/上下文15/分页说明10增量及同PDF228只读检查分别记录；不冒称当前全套重跑。')
report['integration_note']=note
report['fresh_api']={'runtime_status':'executed','owner':'root','result_pending':False,
    'initial_real_generation':'ad03ceec-a393-48a3-840e-4e2f52c50613',
    'current_resumed_run':checks['run_id'],'check_count':9,'output_pages':4,
    'fresh_fact_and_content_calls_this_resume':False,'fresh_review_this_resume':True,
    'p0_issue_count':0,'warning_issue_count':5,'completion':completion,
    'evidence':'validation/native-capacity-live-artifacts/current-resumed/',
    'retained_failures':['language-conflict','resource-identity-missing','pagination-title-p0'],
    'system_acceptance':'not_passed'}
report['context_increment']={'check_count':15,'model_calls':0,'render_calls':0,
    'evidence':'validation/native-capacity-live-artifacts/context-increment/'}
report['adaptive']['pagination_notice_increment']={'check_count':10,'model_calls':0,'render_calls':0,
    'evidence':'validation/native-capacity-live-artifacts/pagination-increment/',
    'source_sha256':hashlib.sha256((ROOT/'src/yoloongppt/adaptive_content.py').read_bytes()).hexdigest()}
if '后续10项分页说明' not in report['adaptive']['note']:
    report['adaptive']['note']+=' 后续10项分页说明定向检查及当前真实恢复的14行表格，原161项并未重跑。'
for id,item in report['acceptance'].items():
    item['state']='部分执行'
    # Preserve historic component limits while replacing the obsolete pending assertion.
    component_note=item.setdefault('component_stage_note',item['note'].split(' 当前真实四页恢复')[0])
    item['note']='组件汇总时记录：'+component_note+' 集成后新增：当前真实四页恢复及独立模型复审已执行（人工素材输入），P0=0、5警告保留；详见fresh_api。完整原条件仍未通过。'
    if 'native-capacity-live-artifacts/current-resumed' not in item['evidence']:
        item['evidence']+='；validation/native-capacity-live-artifacts/current-resumed/quality-report.json；validation/native-capacity-integration.json'
report['environment_recovery']={
    'uac_recovery_executed':False,'uac_result':'User saw no dialog; administrator launch returned cancelled.',
    'actual_recovery':'Stop hanging user WSL/Docker processes; WSL shutdown; disable failing optional default Ubuntu Docker integration with backup; restart Docker Desktop and compose app.',
    'docker_engine_observed':'27.4.0','docker_data_directory':'F:/DockerDesktopWSL',
    'ubuntu_directory':'F:/WSL/Ubuntu','ubuntu_user':'yoloong',
    'ubuntu_user_command':'wsl -d Ubuntu -u yoloong /bin/true returned 0 after authorized missing-user creation.',
    'product_runtime_dependencies':'Docker only','sensitive_values_recorded':False}
report['current_source_and_contract_hashes']=manifest
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'run_id':checks['run_id'],'checks':9,'p0':0,'warnings':5,'system_acceptance':'not_passed'}))
