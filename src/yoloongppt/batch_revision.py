"""REV-003–006/009/010: scoped multi-object edits with native preservation and QA."""
import copy
import json
import math

from .artifacts import RunArtifacts, sha256
from .errors import TaskError
from .facts import approved_text
from .quality import numbers


def fail(code,message,details=None):
    raise TaskError(code,message,'RevisionEngine',['REV-003','REV-004','REV-005','REV-010','SYS-016'],details or [])


def _source_text(slide,sources):
    evidence={e['evidence_id']:e for e in sources['evidence']}
    refs=slide['source_refs']
    if set(refs)-set(evidence):fail('REVISION_EVIDENCE_UNKNOWN','修订页引用不存在的证据。')
    raw='\n'.join(approved_text(sources,evidence[r]) for r in refs)
    values=sources.get('fact_boundary',{}).get('assumption_values',{})
    aids=slide['content'].get('assumption_refs',[])
    if set(aids)-set(values):fail('REVISION_ASSUMPTION_UNKNOWN','修订页引用未知假设。')
    return raw+'\n'+'\n'.join(values[a]['raw_text'] for a in aids)


def _guard_numbers(value,slide,sources):
    text=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
    extra=numbers(text)-numbers(_source_text(slide,sources))
    # A JSON numeric integral float represents the same selected quantity.
    extra={n for n in extra if not (n.endswith('.0') and n[:-2] in numbers(_source_text(slide,sources)))}
    if extra:fail('REVISION_FACT_UNSUPPORTED','修订使用未选或无来源数值，未写入PPT。',[{'numbers':sorted(extra),'slide_id':slide['slide_id']}])


def _sync_text(slide,element,value,image_index=None,caption_refs=None,body_span=None):
    element['text']=copy.deepcopy(value)
    if element['role']=='title':
        if len(value)!=1:fail('REVISION_TITLE_INVALID','标题必须为一个完整段落。')
        slide['content']['title']=value[0]
    elif element.get('slot_key','').startswith('caption.'):
        images=slide['content'].get('images') or []
        if image_index is None or len(value)!=1 or image_index>=len(images):fail('REVISION_CAPTION_BINDING_AMBIGUOUS','图注没有唯一图片绑定。')
        images[image_index]['caption']=value[0]
        images[image_index]['caption_source_refs']=caption_refs
        element['source_refs']=caption_refs
        image_slot='asset.'+element['slot_key'].split('.',1)[1]
        linked=[e for e in slide['elements'] if e.get('slot_key')==image_slot and e['type']=='image']
        if len(linked)!=1:fail('REVISION_CAPTION_BINDING_AMBIGUOUS','图注没有唯一原生图片对象。')
        linked[0]['data']['caption']=value[0]
        linked[0]['data']['caption_source_refs']=caption_refs
    elif element['role']=='body':
        if body_span is not None:return
        fail('REVISION_CONTENT_BINDING_AMBIGUOUS','正文修订缺少不可变原文片段绑定。')


def _apply_spec(edit,slide,element,deck,sources,registered):
    """Return real native patch operation/value; update the exact execution spec."""
    op=edit['operation'];value=copy.deepcopy(edit['value']);kind=element['type']
    if op=='text':
        if kind!='text':fail('REVISION_TEXT_TARGET_UNSUPPORTED','文本批次当前仅修改原生文本对象。')
        _guard_numbers('\n'.join(value),slide,sources)
        caption_refs=None
        if element.get('slot_key','').startswith('caption.'):
            if len(value)!=1:fail('REVISION_CAPTION_BINDING_AMBIGUOUS','图注必须为一个完整段落。')
            candidates=[e['evidence_id'] for e in sources['evidence'] if e['evidence_id'] in slide['source_refs'] and value[0] in approved_text(sources,e)]
            if not candidates:fail('REVISION_CAPTION_EVIDENCE_MISMATCH','修订图注必须逐字属于已选页面证据。')
            if len(candidates)!=1:fail('REVISION_CAPTION_EVIDENCE_AMBIGUOUS','新图注属于多个已选证据，缺少唯一来源映射。')
            caption_refs=candidates
        _sync_text(slide,element,value,edit.get('content_image_index'),caption_refs,edit.get('body_span'))
        return 'text','\n'.join(value)
    if op=='table_cell':
        if kind!='table':fail('REVISION_TABLE_TARGET_INVALID','单元格修改目标不是表格。')
        data=element['data'];r=value['row'];c=value['column'];rows=[data['columns'],*data['rows']]
        if r>=len(rows) or c>=len(rows[0]):fail('REVISION_TABLE_CELL_INVALID','单元格超出当前表格。')
        _guard_numbers(value['text'],slide,sources)
        rows[r][c]=value['text'];slide['content']['table']=copy.deepcopy(data)
    elif op=='chart_data':
        if kind!='chart':fail('REVISION_CHART_TARGET_INVALID','数据修改目标不是原生图表。')
        from .native_objects import chart_data
        chart_data(value);_guard_numbers(value,slide,sources)
        element['data'].update(value);slide['content']['chart']=copy.deepcopy(element['data'])
    elif op=='image':
        if kind!='image':fail('REVISION_IMAGE_TARGET_INVALID','换图目标不是原生图片。')
        from .asset_resolver import allowed_path
        from .assets import inspect_image
        entries=[a for a in registered if a['asset_id']==value['asset_id']]
        if len(entries)!=1:fail('REVISION_ASSET_UNKNOWN','换图必须引用父运行唯一登记的asset_id。')
        asset=entries[0]
        if asset.get('usage_status')!='authorized':fail('REVISION_ASSET_USAGE_UNAUTHORIZED','替换素材没有已记录的使用授权。')
        path=allowed_path(asset['path']);meta=inspect_image(path.read_bytes())
        if meta['sha256']!=asset['sha256']:fail('REVISION_ASSET_CHANGED','替换素材与登记哈希不一致。')
        data=element['data']
        if data.get('fit')!='contain' or any(data.get('crop',[0,0,0,0])):
            fail('REVISION_IMAGE_CROP_POLICY_REQUIRED','有裁切的图片替换须明确新裁切政策，未沿用旧像素裁切。')
        # Contain refits inside the selected object's existing rectangle.
        x,y,w,h=element['bounds'];scale=min(w/meta['width'],h/meta['height'])
        nw,nh=meta['width']*scale,meta['height']*scale
        element['bounds']=[x+(w-nw)/2,y+(h-nh)/2,nw,nh]
        data.update(asset_id=asset['asset_id'],path=str(path),sha256=meta['sha256'],width_px=meta['width'],height_px=meta['height'],crop=[0,0,0,0])
        data['fit_result']={**data.get('fit_result',{}),'bounds':element['bounds'],'crop':[0,0,0,0],
                           'effective_dpi':round(1/scale,2),'quality':'low_resolution' if 1/scale<96 else 'nominal_96dpi_or_above',
                           'warning':'Below 96 DPI at display size; no fabricated upscaling.' if 1/scale<96 else None,'pixel_removal_explicit':False}
        images=slide['content'].get('images') or ([slide['content']['image']] if slide['content'].get('image') else [])
        # slot_key is kept, and the binding is changed only for this element.
        index=edit.get('content_image_index')
        if index is None or index>=len(images):fail('REVISION_IMAGE_BINDING_AMBIGUOUS','图片无法唯一绑定原内容记录。')
        images[index].update({k:data[k] for k in ['asset_id','path','sha256','width_px','height_px']})
        return 'image_replace',{'path':str(path)}
    elif op=='geometry':
        if kind=='connector':fail('REVISION_CONNECTOR_REROUTE_UNSUPPORTED','连接线移动须成对端点重算。')
        x,y,w,h=value
        if not all(math.isfinite(n) for n in value) or x<0 or y<0 or w<=0 or h<=0 or x+w>deck['width_inches']+1e-6 or y+h>deck['height_inches']+1e-6:
            fail('REVISION_GEOMETRY_INVALID','几何修改越出页面或尺寸非法。')
        element['bounds']=value
    elif op=='format':
        if kind!='text':fail('REVISION_FORMAT_TARGET_UNSUPPORTED','格式批次当前只修改原生文本。')
        allowed={'color','bold','font_size'}
        if set(value)-allowed:fail('REVISION_FORMAT_UNSUPPORTED','当前运行规格仅消费color/bold/font_size；其他字段未忽略。')
        if 'font_size' in value:
            if value['font_size']<max(12,slide['style'].get('minimum_size',16)):fail('REVISION_FONT_TOO_SMALL','修订字号低于页面可读性门槛。')
            element['font_size']=value['font_size']
        element.setdefault('format',{}).update({k:v for k,v in value.items() if k!='font_size'})
    elif op=='alt_text':
        _guard_numbers(value,slide,sources)
        if kind not in {'image','shape'}:fail('REVISION_ALT_TARGET_UNSUPPORTED','替代文字当前只消费图片/形状；连接线descr用于关系证据，未覆盖关系。')
        element.setdefault('data',{})['alt_text']=value
        if kind=='image' and edit.get('content_image_index') is not None:
            images=slide['content'].get('images') or ([slide['content']['image']] if slide['content'].get('image') else [])
            images[edit['content_image_index']]['alt_text']=value
    elif op=='notes':
        _guard_numbers(value,slide,sources);slide['content']['notes']=value
        value=value+'\n\n来源：'+'\n'.join(slide['source_refs'])
    else:fail('REVISION_OPERATION_UNSUPPORTED','修订操作未连接执行器。')
    return op,value


def _body_binding(original_slide,original_element):
    body=original_slide['content']['body'];old=original_element['text']
    matches=[n for n in range(len(body)-len(old)+1) if old and body[n:n+len(old)]==old]
    if len(matches)!=1:fail('REVISION_CONTENT_BINDING_AMBIGUOUS','正文对象无法唯一绑定修订前的正文片段。')
    return [matches[0],len(old)]


def _image_content_index(slide,element):
    """Asset identity is mutable; the native object/slot binding stays stable."""
    native_images=[e for e in slide['elements'] if e['type']=='image']
    images=slide['content'].get('images') or ([slide['content']['image']] if slide['content'].get('image') else [])
    if element['type']=='image':linked=element
    else:
        slot='asset.'+element['slot_key'].split('.',1)[1]
        matches=[e for e in native_images if e['slot_key']==slot]
        if len(matches)!=1:fail('REVISION_IMAGE_BINDING_AMBIGUOUS','图注缺少唯一稳定原生图片槽位。')
        linked=matches[0]
    indices=[i for i,e in enumerate(native_images) if e['object_id']==linked['object_id']]
    if len(indices)!=1 or len(native_images)!=len(images):fail('REVISION_IMAGE_BINDING_AMBIGUOUS','原生图片与内容记录不是一一映射。')
    index=indices[0]
    if images[index]['asset_id']!=linked['data']['asset_id'] or (images[index].get('sha256') and images[index]['sha256']!=linked['data']['sha256']):
        fail('REVISION_IMAGE_BINDING_CHANGED','稳定图片槽位与对应内容记录不一致。')
    return index


def _update_bodies(deck,before,pending):
    for slide in deck['slides']:
        replacements=pending.get(slide['slide_id'],[])
        if not replacements:continue
        occupied=set()
        for span,value in replacements:
            positions=set(range(span[0],span[0]+span[1]))
            if positions&occupied:fail('REVISION_CONTENT_BINDING_CONFLICT','多个对象修订覆盖同一原正文片段。')
            occupied|=positions
        body=copy.deepcopy(next(s['content']['body'] for s in before['slides'] if s['slide_id']==slide['slide_id']))
        for span,value in sorted(replacements,key=lambda item:item[0][0],reverse=True):body[span[0]:span[0]+span[1]]=value
        slide['content']['body']=body


def _finalize_geometry(patches,elements,native_ids,auto_geometry,explicit_geometry):
    for patch in patches:
        for oid in auto_geometry&explicit_geometry:
            if patch['object_id']==native_ids[oid] and patch['operation']=='geometry':patch['value']=copy.deepcopy(elements[oid][1]['bounds'])
    for oid in auto_geometry-explicit_geometry:
        patches.append({'object_id':native_ids[oid],'operation':'geometry','value':copy.deepcopy(elements[oid][1]['bounds'])})


def revise_batch(run_id,request,schemas,trace):
    from .operations import run_folder,artifacts as verify_artifacts
    from .existing_deck import inspect_deck,apply_patch
    from .revision import revision_sources,DECISION_FILES,_finish_quality
    from .revision_scope import resolve_revision
    from .rendering import render
    from .writer import capacity
    schemas.validate('revision-batch-request.schema.json',request)
    prior=run_folder(run_id);verify_artifacts(run_id,trace)
    load=lambda n:json.loads((prior/n).read_text('utf-8'))
    deck=load('deck-spec.json');before=copy.deepcopy(deck);object_map=load('object-map.json');sources=revision_sources(prior)
    schemas.validate('deck-execution.schema.json',deck);schemas.validate('deck-execution.schema.json',object_map)
    task=load('task-effective.json') if (prior/'task-effective.json').is_file() else load('task.json')
    native=inspect_deck(prior/'deck.pptx');artifacts=RunArtifacts()
    from .observability import version_manifest
    artifacts.json('version-manifest.json',version_manifest(schemas))
    artifacts.json('revision-request.json',request)
    for name in DECISION_FILES:
        if (prior/name).is_file():artifacts.json(name,load(name))
    registered=load('resolved-assets.json')['entries'] if (prior/'resolved-assets.json').is_file() else []
    native['registered_assets']=registered
    try:
        resolved=resolve_revision(request,deck,object_map,native,sources,task,artifacts,schemas)
        artifacts.json('revision-intent.json',resolved)
        elements={e['object_id']:(s,e) for s in deck['slides'] for e in s['elements']}
        mapped={o['logical_object_id']:o for o in object_map['objects']}
        native_slides={s['slide_index']:s for s in native['slides']}
        patches=[];actions=[];orders=set();targets=set();native_ids={};auto_geometry=set();body_pending={}
        for oid,(s,e) in elements.items():
            m=mapped.get(oid)
            found=[] if m is None else [o for o in native_slides[s['order']]['objects'] if o['shape_id']==m['shape_id'] and o['name']==m['name']]
            if len(found)!=1:fail('REVISION_OBJECT_MAP_STALE','原生对象与逻辑映射不一致。',[{'object_id':oid}])
            native_ids[oid]=found[0]['object_id']
        # Prepare all edits and validate the final spec before any PPTX write.
        for edit in resolved['edits']:
            oid=edit['object_id'];s,e=elements[oid];old=copy.deepcopy(e)
            original_slide=next(p for p in before['slides'] if p['slide_id']==s['slide_id'])
            original_element=next(p for p in original_slide['elements'] if p['object_id']==oid)
            if edit['operation']=='text' and e['role']=='body' and not e.get('slot_key','').startswith('caption.'):
                span=_body_binding(original_slide,original_element)
                edit={**edit,'body_span':span}
                body_pending.setdefault(s['slide_id'],[]).append((span,edit['value']))
            if e['type']=='image' or e.get('slot_key','').startswith('caption.'):
                edit={**edit,'content_image_index':_image_content_index(original_slide,original_element)}
            op,value=_apply_spec(edit,s,e,deck,sources,registered)
            patches.append({'object_id':native_ids[oid],'operation':op,'value':value})
            if edit['operation']=='image' and e['bounds']!=old['bounds']:
                auto_geometry.add(oid)
            actions.append({'object_id':oid,'slide_id':s['slide_id'],'operation':edit['operation'],'before_spec':old,'after_spec':copy.deepcopy(e)})
            orders.add(s['order']);targets.add(oid)
        _update_bodies(deck,before,body_pending)
        explicit_geometry={e['object_id'] for e in resolved['edits'] if e['operation']=='geometry'}
        _finalize_geometry(patches,elements,native_ids,auto_geometry,explicit_geometry)
        for oid in targets:
            s,e=elements[oid]
            if e['type']=='text':
                f=e.get('format',{});capacity(e['text'],e['bounds'],e['font_size'],padding=f.get('margin',.12),paragraph_spacing=f.get('paragraph_spacing',10))
            if e['type']=='image' and oid in auto_geometry|explicit_geometry:
                data=e['data'];ratio=data['width_px']/data['height_px'];w,h=e['bounds'][2:]
                if data.get('fit')=='contain' and abs(w/h-ratio)>1e-4:
                    fail('REVISION_IMAGE_STRETCH_FORBIDDEN','contain图片的新边界改变原始宽高比，未写入拉伸图片。')
                dpi=data['width_px']/w
                data.setdefault('fit_result',{}).update(bounds=copy.deepcopy(e['bounds']),effective_dpi=round(dpi,2),
                    quality='low_resolution' if dpi<96 else 'nominal_96dpi_or_above',warning='Below 96 DPI at display size; no fabricated upscaling.' if dpi<96 else None)
        for action in actions:
            action['intermediate_after_spec']=action['after_spec']
            action['after_spec']=copy.deepcopy(elements[action['object_id']][1])
        if not patches:fail('REVISION_BATCH_EMPTY','修订批次没有可执行修改。')
        schemas.validate('deck-execution.schema.json',deck)
        artifacts.json('revision-before-spec.json',before);artifacts.json('revision-after-spec.json',deck)
        report=apply_patch(prior/'deck.pptx',artifacts.path/'deck.pptx',{'expected_sha256':sha256(prior/'deck.pptx'),'patches':patches,
                            'locked_object_ids':[native_ids[x] for x in resolved['locked_object_ids']]})
        for name,value in [('task.json',task),('deck-spec.json',deck),('source-result.json',load('source-result.json')),('object-map.json',object_map)]:artifacts.json(name,value)
        artifacts.json('native-revision-report.json',report)
        renders=render(artifacts.path/'deck.pptx',deck,artifacts.path);artifacts.json('render-report.json',renders)
        quality,decision=_finish_quality(task,deck,sources,object_map,renders,artifacts,prior,sorted(orders),schemas,trace)
        history={'parent_run_id':run_id,'trace_id':trace,'instruction':request['instruction'],'mode':request.get('mode','revision'),
                 'scope':resolved['scope'],'locked_object_ids':resolved['locked_object_ids'],'actions':actions,
                 'before_pptx_hash':sha256(prior/'deck.pptx'),'after_pptx_hash':sha256(artifacts.path/'deck.pptx'),
                 'changed_parts':report['changed_parts'],'unchanged_parts_byte_preserved':True,'entity_ids_preserved':True,
                 'quality_before':load('quality-report.json'),'quality_after':quality,'rerun_nodes':['selected_native_objects','render','QA'],
                 'before_spec':'revision-before-spec.json','after_spec':'revision-after-spec.json','execution_report':report}
        history['derived_projection_changes']=[{'slide_id':s['slide_id'],'object_id':e['object_id'],'before_spec':old,'after_spec':e,'native_changed':False,
                                               'reason':'Visible caption binding metadata follows the explicitly selected caption; native object payload is preserved.'}
                                              for s in deck['slides'] for e in s['elements'] if e['object_id'] not in targets
                                              for old in [next(o for p in before['slides'] for o in p['elements'] if o['object_id']==e['object_id'])] if old!=e]
        artifacts.json('revision-history.json',history)
        result={'ok':True,'trace_id':trace,'operation':'revise','state':'draft_revised','run_id':artifacts.run_id,'parent_run_id':run_id,
                'artifact_root':str(artifacts.path),'pptx':str(artifacts.path/'deck.pptx'),'scope':resolved['scope'],
                'changed_parts':report['changed_parts'],'qa':{'p0_issue_count':quality['p0_issue_count'],'status':'partial'},
                'completion':decision['completion'],'system_acceptance':'not_passed'}
        artifacts.json('result.json',result);artifacts.json('manifest.json',{'run_id':artifacts.run_id,'artifacts':artifacts.manifest()})
        return result
    except TaskError as error:
        artifacts.json('failure.json',error.result(trace))
        artifacts.json('manifest.json',{'run_id':artifacts.run_id,'artifacts':artifacts.manifest()})
        error.details.append({'run_id':artifacts.run_id,'failure_recorded':True})
        raise
