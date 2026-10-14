"""TPL-004/007/008: reuse Presenton Template V2 schemas without its export core."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from .errors import TaskError

VENDOR = Path(__file__).resolve().parents[2] / 'vendor' / 'presenton_templates'


def _module(name):
    from .vendor_integrity import verify_vendor
    verify_vendor(VENDOR,'35bf44290f821323e003da854f78ffcb0e918167')
    package='_yoloongppt_presenton_templates'
    if package not in sys.modules:
        spec=importlib.util.spec_from_file_location(package,VENDOR/'__init__.py',submodule_search_locations=[str(VENDOR)])
        module=importlib.util.module_from_spec(spec);sys.modules[package]=module;spec.loader.exec_module(module)
    return __import__(package+'.'+name,fromlist=[name])


def _native_ir(pack):
    """Project known native slots; do not invent unknown capacities or assets."""
    layouts=[]
    for layout in pack['layouts']:
        elements=[]
        for index,slot in enumerate(layout['slots']):
            if 'text' not in slot['content_types']:
                continue
            capacity=slot.get('capacity',{})
            elements.append({'type':'text','name':'slot_'+str(index),'decorative':False,
                'runs':[{'text':slot.get('name') or ''}],'min_length':0,
                'max_length':capacity.get('characters'),
                'position':None,'size':None})
        layouts.append({'id':layout['part'],'description':layout.get('name') or layout['part'],
                        'components':[{'id':'native_slots','description':'Native OOXML slots','position':{'x':0,'y':0},'elements':elements}]})
    return {'layouts':layouts}


def analyze_upstream_template(template_ir, *, source=None):
    native=template_ir.get('record_type')=='native_template_pack'
    ir=_native_ir(template_ir) if native else copy.deepcopy(template_ir)
    layouts=ir.get('layouts')
    if not isinstance(layouts,list) or not layouts:
        raise TaskError('UPSTREAM_TEMPLATE_INVALID','Template must contain at least one layout.','TemplateRegistry',['TPL-003','TPL-004'])
    if len({x.get('id') for x in layouts})!=len(layouts):
        raise TaskError('UPSTREAM_TEMPLATE_INVALID','Duplicate layout IDs.','TemplateRegistry',['TPL-003'])
    try:
        # Native unknown capacities intentionally stay untyped candidates rather
        # than being assigned arbitrary Presenton preview-content bounds.
        if not native:
            _module('models.layouts').SlideLayouts.model_validate({'layouts':layouts})
        result=_module('schema').get_template_schema(ir,source_file=source or 'template.json')
        for layout in result['layouts']:
            if layout['schema'] is not None:Draft202012Validator.check_schema(layout['schema'])
    except (ValueError,TypeError,SchemaError) as exc:
        raise TaskError('UPSTREAM_TEMPLATE_INVALID',str(exc),'TemplateRegistry',['TPL-004','TPL-007']) from None
    versions=json.loads((VENDOR/'SOURCE.json').read_text('utf-8'))
    candidates=[]
    for original,generated in zip(layouts,result['layouts']):
        slots=[]
        for component in original.get('components',[]):
            schema=_module('schema').get_component_schema(component)
            for name,field in (schema or {}).get('properties',{}).items():
                slots.append({'slot_id':component['id']+'.'+name,'role':name,'content_type':field.get('x-element-type'),
                    'required':name in schema.get('required',[]),'schema':field,
                    'capacity':{'status':'unmeasured' if native else 'upstream_declared_not_render_verified',
                        'characters':field.get('maxLength'),'items':field.get('maxItems')},
                    'overflow_policy':'fail_or_explicit_paginate; no truncation',
                    'source_element_path':field.get('x-element-path')})
        if native:
            source_layout=next(x for x in template_ir['layouts'] if x['part']==original['id'])
            text_slots=[x for x in source_layout['slots'] if 'text' in x['content_types']]
            for slot,source_slot in zip(slots,text_slots):
                slot.update(native_slot_id=source_slot['slot_id'],placeholder_index=source_slot['placeholder_index'],
                    native_role=source_slot['role'],bounds=source_slot['bounds'],style_xml=source_slot.get('style_xml'),
                    required=source_slot.get('required'),brand_lock=source_slot.get('brand_lock'),
                    minimum_font_pt=source_slot.get('capacity',{}).get('minimum_font_pt'))
        candidates.append({'layout_id':original['id'],'slots':slots,'content_schema':generated['schema'],
                           'source_layout_part':original['id'] if native else None})
    return {'project':'Presenton','version':versions['commit'],'license':versions['license'],
            'schema':result,'layouts':candidates,'native_source':native,
            'scope':'Content/element/capacity schema reuse; no export-core or automatic asset/license assertion'}


def validate_template_content(analysis, layout_id, content):
    layout=next((x for x in analysis['layouts'] if x['layout_id']==layout_id),None)
    if layout is None or layout['content_schema'] is None:
        raise TaskError('UPSTREAM_TEMPLATE_LAYOUT_UNAVAILABLE','No editable schema for this layout.','TemplateRegistry',['TPL-006'])
    errors=list(Draft202012Validator(layout['content_schema']).iter_errors(content))
    if errors:
        raise TaskError('UPSTREAM_TEMPLATE_CAPACITY_FAILED','Content violates the actual upstream schema; no trimming performed.','TemplateRegistry',['TPL-007'],[{'path':list(e.path),'message':e.message} for e in errors])
    return {'valid':True,'layout_id':layout_id,'checks':'Presenton-generated JSON Schema','visual_fit':'requires actual font measurement, render and QA'}


def validate_native_slot_content(analysis, layout_id, slot_content):
    """Validate only caller-selected native slots using upstream field schemas.

    Unlike Presenton's generated content, a native template may legitimately
    leave unused placeholders untouched. Its required flags remain unknown.
    """
    layout=next((x for x in analysis['layouts'] if x['layout_id']==layout_id),None)
    if not analysis.get('native_source') or layout is None:
        raise TaskError('UPSTREAM_TEMPLATE_LAYOUT_UNAVAILABLE','Native layout was not analyzed.','TemplateRegistry',['TPL-006'])
    validated=[]
    for index,value in slot_content.items():
        slot=next((s for s in layout['slots'] if str(s['placeholder_index'])==str(index)),None)
        if slot is None:
            raise TaskError('UPSTREAM_TEMPLATE_SLOT_UNKNOWN','Native slot is not present in the upstream mapping.','TemplateRegistry',['TPL-004'])
        errors=list(Draft202012Validator(slot['schema']).iter_errors(value))
        if errors:
            raise TaskError('UPSTREAM_TEMPLATE_CAPACITY_FAILED','Selected native content violates upstream slot schema.','TemplateRegistry',['TPL-007'],[{'slot_id':slot['native_slot_id'],'message':e.message} for e in errors])
        validated.append({'slot_id':slot['native_slot_id'],'placeholder_index':slot['placeholder_index'],'capacity_status':slot['capacity']['status']})
    return {'valid':True,'layout_id':layout_id,'selected_slots':validated,'visual_fit':'existing measured native runtime plus actual render/QA required'}
