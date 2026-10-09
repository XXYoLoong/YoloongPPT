"""Use the authorized model for HTML content; no nested author agent or mock."""
import hashlib,json,os,re,sys,time
from pathlib import Path
from openai import OpenAI
root=Path('/workspace/research/P02');workspace=root/'outputs/official-six'
workspace.mkdir(parents=True,exist_ok=True);(workspace/'slides').mkdir(exist_ok=True)
system='''You author presentation HTML from a supplied factual brief. Return only a JSON object with a slides array of exactly six objects: page (integer 1..6), title (Chinese), html (complete self-contained HTML document). No Markdown fences. Do not invent facts or turn planned work into completed work. Use editable text and CSS div rectangles only; no scripts, SVG, canvas, external URLs/fonts/images. Each body is exactly 1280px by 720px, margin:0, box-sizing:border-box. Use simple static positioned div wrappers and p/h1/h2 text (one source line per text element), no CSS grid/flex. Place background/border on div, never on p/h1/h2. Use font-family:'Noto Sans CJK SC',sans-serif; heading 34..46px, body 22..26px, labels >=18px. Give all positioned text explicit generous widths/heights. Keep content within x=64..1216,y=48..660. High contrast light canvas #F5F3EF, dark text #182231, accent #2563EB. At most three substantive points per page, approximately 120 Chinese characters per page. Vary page layouts using editorial cover, horizontal process, three columns, comparison, checklist and conclusion. Do not use tightly packed cards or shrink-to-fit. Each slide needs a small page number and a short accurate source label from brief. This is a research reproduction, not a product deliverable.'''
brief='''请为工程团队生成六页中文演示文稿《AI PPT 首条链路交付计划》。用途：P02 官方 Skill 研究复现。
以下是完整事实边界，来源为 YoloongPPT V0.3 需求矩阵和 GOAL.md；只呈现这些内容，无需联网研究。
第1页：主题与结论——用真实文本输入，打通可编辑PPTX生成、QA和局部修订；这是计划目标，尚未交付产品链路。
第2页：全局范围——308条主需求、453个任务；S00–S44全链路；AC-001–030验收。约10页是首条产品链路目标；本研究示例固定6页。来源：需求矩阵/GOAL.md。
第3页：首条链路——文本或Markdown→TaskSpec/来源证据→内容、模板与布局→原生PPTX写入。来源：AC-001、GOV-008。
第4页：质量与修订——渲染；结构、视觉、事实、可编辑性QA；局部修订后再验收，追踪对象差异与来源。来源：GOV-008、AC-027/028/030。
第5页：当前研究发现——P05候选默认图表为图片；旧页模板删除报错；直接图表写入存在补零风险。把能力边界与fallback明确记录，不能概括为全能力支持。来源：RES-P05-03/04/05。不要声称这些问题已被产品修复。
第6页：执行约束与下一步——产品语言/运行时尚未选定；本机Docker隔离，项目数据F盘；默认开发分支yoloongdevlop，中文任务日志+Git提交。先完成候选对照/许可决策，再实施首条链路。来源：AGENTS.md、RES-031/032、GOAL.md。
六页内容都用中文，术语TaskSpec/PPTX/QA等可保留；每页标题必须表达清晰意思。'''
(root/'validation/author-prompts.json').write_text(json.dumps({'system':system,'brief':brief,'constraint':'exactly6; 1280x720; source facts; no remote assets'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
client=OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'],base_url='https://api.deepseek.com',timeout=180,max_retries=0)
start=time.time();content='';usage=None;finish=None;request_id=None
try:
 stream=client.chat.completions.create(model='deepseek-flash',messages=[{'role':'system','content':system},{'role':'user','content':brief}],response_format={'type':'json_object'},max_tokens=12000,temperature=0.3,extra_body={'thinking':{'type':'disabled'}},stream=True,stream_options={'include_usage':True})
 last=0
 for chunk in stream:
  request_id=chunk.id
  if chunk.usage:usage=chunk.usage.model_dump()
  for choice in chunk.choices:
   content+=choice.delta.content or ''
   if choice.finish_reason:finish=choice.finish_reason
  if time.time()-last>20:print(json.dumps({'phase':'author_stream','elapsed_seconds':round(time.time()-start),'content_chars':len(content)}),flush=True);last=time.time()
 # Persist only public final content; never persist reasoning_content or credentials.
 (root/'validation/author-response.json').write_text(content+'\n',encoding='utf-8')
 data=json.loads(content);slides=data['slides'];assert len(slides)==6
 assert [s['page'] for s in slides]==list(range(1,7))
 for s in slides:
  html=s['html'];assert '<html' in html.lower() and '<body' in html.lower()
  assert not re.search(r'<script\b|<svg\b|<canvas\b|https?://',html,re.I)
  assert '1280' in html and '720' in html
  (workspace/'slides'/f"slide{s['page']:02}.html").write_text(html+'\n',encoding='utf-8')
 report={'state':'passed','model':'deepseek-flash','endpoint':'https://api.deepseek.com/chat/completions','request_id':request_id,'finish_reason':finish,'usage':usage,'elapsed_seconds':round(time.time()-start,2),'slides':len(slides),'thinking':'disabled for content authoring; official visual caller uses provider default','credential_source':'DEEPSEEK_API_KEY forwarded by name only','source':'validation/author-prompts.json','output_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((workspace/'slides').glob('*.html'))}}
except Exception as e:
 report={'state':'failed','error_type':type(e).__name__,'status_code':getattr(e,'status_code',None),'elapsed_seconds':round(time.time()-start,2),'content_chars':len(content)}
(root/'validation/author-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
if report['state']!='passed':sys.exit(1)
