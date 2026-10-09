"""Observe public visual responses without changing official prompts/validation."""
import base64,hashlib,json,runpy,sys,urllib.request
from pathlib import Path
out=Path('/workspace/research/P02/validation');phase=sys.argv[1];label=sys.argv[2]
original=urllib.request.urlopen;count=0
class RecordedResponse:
 def __init__(self,response,data):self.response=response;self.data=data
 def __enter__(self):return self
 def __exit__(self,*args):self.response.close()
 def read(self):return self.data
def traced(request,*args,**kwargs):
 global count
 response=original(request,*args,**kwargs);data=response.read();count+=1
 payload=json.loads(data);message=payload.get('choices',[{}])[0].get('message',{})
 body=json.loads(request.data);content=body['messages'][-1]['content']
 images=[p['image_url']['url'] for p in content if p.get('type')=='image_url']
 report={'call':count,'phase':phase,'request_model':body['model'],'response_model':payload.get('model'),'request_id':payload.get('id'),'usage':payload.get('usage'),'context':content[0].get('text'),'input_image_sha256':[hashlib.sha256(base64.b64decode(i.split(',',1)[1])).hexdigest() for i in images],'public_response_content':message.get('content'),'private_reasoning_persisted':False,'scope':'observer only; original request/prompts/response bytes and validator unchanged'}
 (out/f'visual-{label}-{count:02}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'visual_call':count,'phase':phase,'images':len(images),'public_response_logged':True}),file=sys.stderr,flush=True)
 return RecordedResponse(response,data)
urllib.request.urlopen=traced
sys.path.insert(0,'/artifacts/main-skill/scripts')
sys.argv=['/artifacts/main-skill/scripts/pptagent.py','--config','/workspace/research/P02/config-deepseek.yaml',phase,'--workspace','/workspace/research/P02/outputs/official-six']
runpy.run_path(sys.argv[0],run_name='__main__')
