import json, os
from pathlib import Path
from openai import OpenAI
client=OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'],base_url='https://api.deepseek.com',timeout=45,max_retries=0)
try:
    response=client.models.list()
    records=[]
    for model in response.data:
        raw=model.model_dump()
        records.append({k:raw[k] for k in ('id','name','input_modalities','output_modalities','context_window','max_output_tokens') if k in raw})
    report={'state':'passed','endpoint':'https://api.deepseek.com/models','models':records,'credential_source':'DEEPSEEK_API_KEY via docker exec environment; no key persisted'}
except Exception as error:
    report={'state':'failed','error_type':type(error).__name__,'status_code':getattr(error,'status_code',None)}
Path('/workspace/research/P02/validation/deepseek-models.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
