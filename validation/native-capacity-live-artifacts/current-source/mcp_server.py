"""MCP stdio JSON-RPC transport; actual core tools, not a mock server (SYS-021)."""
import json
import sys
from .errors import TaskError, internal_error, trace_id
from .operations import dispatch

PROTOCOLS=('2024-11-05','2025-03-26','2025-06-18')
TOOLS={
 'register_template':('登记真实模板并保存母版、布局、主题、来源与许可。',{'type':'object','required':['path'],'properties':{'path':{'type':'string'},'source':{'type':'string'},'license':{'type':'string'}},'additionalProperties':False}),
 'get_template':('按稳定ID读取模板并核对hash。',{'type':'object','required':['template_id'],'properties':{'template_id':{'type':'string'}},'additionalProperties':False}),
 'resolve_assets':('把声明素材解析为真实文件，核对hash与使用授权。',{'type':'object'}),
 'create_deck':('按TaskSpec真实生成可编辑PPTX及渲染/QA产物。',{'type':'object'}),
 'revise_deck':('局部修订现有运行产物。',{'type':'object','required':['run_id','request'],'properties':{'run_id':{'type':'string'},'request':{'type':'object'}},'additionalProperties':False}),
 'inspect':('解析来源并保存原文及证据锚点。',{'type':'object'}),
 'validate':('校验TaskSpec与注册契约。',{'type':'object'}),
 'capabilities':('查询真实能力及明确限制。',{'type':'object','additionalProperties':False}),
 'debug':('独立执行已接入决策节点。',{'type':'object','required':['node_id','input'],'properties':{'node_id':{'type':'string'},'input':{'type':'object'}},'additionalProperties':False}),
 'artifacts':('返回运行产物路径并核对清单哈希。',{'type':'object','required':['run_id'],'properties':{'run_id':{'type':'string'}},'additionalProperties':False}),
 'inspect_deck':('解析已有PPT的稳定对象索引。',{'type':'object','required':['path'],'properties':{'path':{'type':'string'}},'additionalProperties':False}),
 'edit_deck':('按哈希与精确对象选择器修改已有PPT并保存副本。',{'type':'object','required':['path','request'],'properties':{'path':{'type':'string'},'request':{'type':'object'}},'additionalProperties':False}),
 'parse_template':('抽取原生模板母版、主题、布局及槽位。',{'type':'object','required':['path'],'properties':{'path':{'type':'string'}},'additionalProperties':False}),
 'instantiate_template':('保留原生模板，填充指定文本占位符并新增页面。',{'type':'object','required':['path','layout_part','slot_content'],'properties':{'path':{'type':'string'},'layout_part':{'type':'string'},'slot_content':{'type':'object'}},'additionalProperties':False}),
 'compose_native':('执行调用方指定的原生文字、形状、线、组、图像、表、图表。',{'type':'object','required':['slides'],'properties':{'slides':{'type':'array','minItems':1,'maxItems':30}},'additionalProperties':False}),
 'inventory_assets':('登记允许目录的资产规格与哈希/感知重复候选；不猜许可或语义。',{'type':'object','required':['directory'],'properties':{'directory':{'type':'string'}},'additionalProperties':False})}


def handle(message):
    if not isinstance(message,dict) or message.get('jsonrpc')!='2.0':
        return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Invalid Request'}}
    method=message.get('method');ident=message.get('id')
    if 'id' not in message:
        return None
    base={'jsonrpc':'2.0','id':ident}
    params=message.get('params',{})
    if not isinstance(params,dict):
        return {**base,'error':{'code':-32602,'message':'Invalid params'}}
    if method=='initialize':
        version=params.get('protocolVersion')
        return {**base,'result':{'protocolVersion':version if version in PROTOCOLS else PROTOCOLS[-1],
                               'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'YoloongPPT','version':'0.1.0'}}}
    if method=='ping': return {**base,'result':{}}
    if method=='tools/list':
        return {**base,'result':{'tools':[{'name':name,'description':desc,'inputSchema':schema} for name,(desc,schema) in TOOLS.items()]}}
    if method=='tools/call':
        name=params.get('name');arguments=params.get('arguments',{})
        if name not in TOOLS or not isinstance(arguments,dict):
            return {**base,'error':{'code':-32602,'message':'Unknown tool or invalid arguments'}}
        trace=trace_id()
        try:
            from jsonschema import Draft202012Validator
            if list(Draft202012Validator(TOOLS[name][1]).iter_errors(arguments)):
                raise TaskError('MCP_ARGUMENT_INVALID','工具输入不符合契约。','MCP',['SYS-021'])
            result=dispatch(name,arguments,trace)
        except TaskError as error: result=error.result(trace)
        except Exception: result=internal_error().result(trace)
        return {**base,'result':{'content':[{'type':'text','text':json.dumps(result,ensure_ascii=False,allow_nan=False)}],
                                'structuredContent':result,'isError':not result.get('ok')}}
    return {**base,'error':{'code':-32601,'message':'Method not found'}}


def serve():
    # MCP stdio is newline-delimited JSON, one complete message per line.
    initialized=False
    negotiated=False
    while True:
        raw=sys.stdin.buffer.readline(4*1024*1024+1)
        if not raw: return
        if len(raw)>4*1024*1024:
            result={'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Message size limit exceeded'}}
            if not raw.endswith(b'\n'):
                while True:
                    tail=sys.stdin.buffer.readline(4*1024*1024)
                    if not tail or tail.endswith(b'\n'): break
        else:
            try:
                message=json.loads(raw)
                method=message.get('method') if isinstance(message,dict) else None
                if method=='initialize':
                    result=handle(message);negotiated=True
                elif method=='notifications/initialized' and negotiated:
                    initialized=True;result=None
                elif method not in {'ping'} and not initialized and isinstance(message,dict) and 'id' in message:
                    result={'jsonrpc':'2.0','id':message['id'],'error':{'code':-32002,'message':'Server not initialized'}}
                else:result=handle(message)
            except (ValueError,UnicodeError): result={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}
        if result is not None:
            print(json.dumps(result,ensure_ascii=False,allow_nan=False),flush=True)


if __name__=='__main__':
    serve()
