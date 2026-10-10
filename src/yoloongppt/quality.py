"""SYS-015: independent structure/editability/source-number/render checks."""
import json
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from PIL import Image
from pptx import Presentation

from .artifacts import entity
from .facts import approved_text

NUMBER = re.compile(r'(?<![0-9A-Za-z_.])-?\d+(?:\.\d+)?%?')


def numbers(text):
    # Typed provenance IDs are metadata, not asserted quantities.
    text=re.sub(r'\b[a-z_]+_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b','',text)
    return set(NUMBER.findall(text))


def check(deck, pptx, object_map, sources, renders, root):
    issues = []; checks = []
    def issue(code, slide_id, detail, severity='P0'):
        issues.append({'issue_id': entity('issue'), 'code': code, 'slide_id': slide_id, 'severity': severity, 'detail': detail})
    presentation = Presentation(pptx)
    if len(presentation.slides) != len(deck['slides']):issue('SLIDE_COUNT', None, '实际PPTX页数不同。')
    with ZipFile(pptx) as archive:
        if archive.testzip() is not None:issue('ZIP_CORRUPT', None, '压缩包CRC失败。')
        for name in archive.namelist():
            if name.endswith(('.xml', '.rels')):
                try:ET.fromstring(archive.read(name))
                except ET.ParseError:issue('XML_INVALID', None, name)
        checks.append({'kind': 'structure', 'check': 'OOXML ZIP CRC and XML parsing', 'status': 'executed'})
        workbooks = [n for n in archive.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]
    lookup = {e['evidence_id']: e for e in sources['evidence']}
    shape_lookup = {o['logical_object_id']: o for o in object_map['objects']}
    pages_text = (Path(root)/renders['render_text_path']).read_text(encoding='utf-8').split('\f')
    bbox_pages=None
    if renders.get('render_bbox_path'):
        bbox_pages=ET.parse(Path(root)/renders['render_bbox_path']).findall('.//{http://www.w3.org/1999/xhtml}page')
    for index, spec in enumerate(deck['slides']):
        if index >= len(presentation.slides):break
        slide = presentation.slides[index]
        refs = spec['source_refs']
        raw = '\n'.join(approved_text(sources,lookup[r]) for r in refs)
        content = spec['content']
        assumption_values=sources.get('fact_boundary',{}).get('assumption_values',{})
        aids=content.get('assumption_refs',[])
        if set(aids)-set(assumption_values):issue('ASSUMPTION_REFERENCE_UNKNOWN',spec['slide_id'],{'assumption_refs':aids})
        if aids and not any('【假设】' in t or '【推算】' in t or '【来源明确假设】' in t for t in content['body']):
            issue('ASSUMPTION_NOT_VISIBLE',spec['slide_id'],'假设/推算未在可见正文标明。')
        raw+='\n'+'\n'.join(assumption_values[a]['raw_text'] for a in aids if a in assumption_values)
        displayed = '\n'.join([content['title'], *content['body']])
        if content['table']:
            displayed += '\n' + '\n'.join(' '.join(row) for row in [content['table']['columns'], *content['table']['rows']])
        new_numbers = numbers(displayed) - numbers(raw)
        if new_numbers:issue('FACT_NUMBER_UNSUPPORTED', spec['slide_id'], {'numbers_not_found_in_cited_evidence': sorted(new_numbers)})
        note_numbers=numbers(content['notes'])-numbers(raw)
        # Auditing an explicitly rejected value in a negative clause is valid
        # provenance, never permission to put that value in presentation copy.
        rejected=set()
        for group in sources.get('evidence_resolution',{}).get('groups',[]):
            if group['conflicting']:
                chosen=next(c for c in group['claims'] if c['claim_id']==group['selected_claim_id'])
                for c in group['claims']:
                    if c['value']!=chosen['value']:rejected|=numbers(c['value']['raw_text'])
        audited=set()
        for clause in re.split('[。；\n]',content['notes']):
            if re.search(r'不采用(?:冲突值)?|未采用(?:冲突值)?|已否决|已排除',clause):audited|=numbers(clause)&rejected
        unsupported_notes=note_numbers-audited
        if unsupported_notes:issue('FACT_NOTE_NUMBER_UNSUPPORTED',spec['slide_id'],{'numbers':sorted(unsupported_notes)})
        if content['chart']:
            for series in content['chart']['series']:
                for value in series['values']:
                    # Numeric identity only. It does not prove matching entity/unit.
                    candidates = {str(value), format(value, 'g')}
                    if not candidates & {n.rstrip('%') for n in numbers(raw)}:
                        issue('CHART_VALUE_UNSUPPORTED', spec['slide_id'], {'value': value})
        for element in spec['elements']:
            mapping = shape_lookup.get(element['object_id'])
            found = [s for s in slide.shapes if s.name == element['object_id']]
            if len(found) != 1 or mapping is None:
                issue('OBJECT_MAP_MISSING', spec['slide_id'], {'object_id': element['object_id']});continue
            shape = found[0]
            if shape.shape_id != mapping['shape_id'] or mapping['part'] != str(slide.part.partname):issue('OBJECT_MAP_MISMATCH', spec['slide_id'], element['object_id'])
            if shape.left < 0 or shape.top < 0 or shape.left+shape.width > presentation.slide_width+2 or shape.top+shape.height > presentation.slide_height+2:
                issue('OBJECT_OUT_OF_BOUNDS', spec['slide_id'], element['object_id'])
            if element['type'] == 'text':
                if not shape.has_text_frame or shape.text != '\n'.join(element['text']):issue('TEXT_NOT_EDITABLE_OR_CHANGED', spec['slide_id'], element['object_id'])
                if element['role'] != 'footer' and element['text']:
                    clean = lambda s: re.sub(r'\s+', '', s)
                    rendered = clean(pages_text[index]) if index < len(pages_text) else ''
                    if bbox_pages is not None:
                        # Filter actual PDF words to the owning native object's
                        # box before checking sequence; columns otherwise interleave.
                        x,y,w,h=element['bounds'];page=bbox_pages[index]
                        words=[]
                        for word in page.findall('{http://www.w3.org/1999/xhtml}word'):
                            left=float(word.attrib['xMin']);right=float(word.attrib['xMax']);top=float(word.attrib['yMin']);bottom=float(word.attrib['yMax'])
                            cx=(left+right)/2;cy=(top+bottom)/2
                            if x*72-1<=cx<=(x+w)*72+1 and y*72-1<=cy<=(y+h)*72+1:words.append(word.text or '')
                        rendered=clean(''.join(words))
                    if any(clean(t) not in rendered for t in element['text']):issue('RENDER_TEXT_MISSING', spec['slide_id'], element['object_id'])
            elif element['type'] == 'table':
                rows = [element['data']['columns'], *element['data']['rows']]
                if not shape.has_table:issue('TABLE_NOT_NATIVE', spec['slide_id'], element['object_id'])
                elif [[c.text for c in row.cells] for row in shape.table.rows] != rows:issue('TABLE_DATA_CHANGED', spec['slide_id'], element['object_id'])
            elif element['type'] == 'chart':
                if not shape.has_chart:issue('CHART_NOT_NATIVE', spec['slide_id'], element['object_id'])
                else:
                    if [list(s.values) for s in shape.chart.series] != [s['values'] for s in element['data']['series']]:issue('CHART_DATA_CHANGED', spec['slide_id'], element['object_id'])
                    if not workbooks:issue('CHART_WORKBOOK_MISSING', spec['slide_id'], element['object_id'])
        notes = slide.notes_slide.notes_text_frame.text
        if content['notes'] not in notes or any(r not in notes for r in refs):issue('NOTES_OR_REFERENCES_MISSING', spec['slide_id'], '备注/证据引用缺失。')
        checks.append({'slide_id': spec['slide_id'], 'kind': 'structure/editability/geometry/selected_source_numeric/visible_assumption/render_text', 'status': 'executed'})
    for artifact in renders['artifacts']:
        if artifact['type'] == 'png':
            with Image.open(Path(root)/artifact['path']) as image:
                colors = image.convert('RGB').resize((160, 90)).getcolors(14400)
                if colors is not None and len(colors) < 4:issue('RENDER_BLANK', artifact['slide_id'], '实际渲染缺少可见内容。')
    visible='\n'.join(t for slide in deck['slides'] for t in slide['content']['body'])
    for action in sources.get('fact_boundary',{}).get('actions',[]):
        if action['mode']=='placeholder' and action['label'] not in visible:
            issue('PLACEHOLDER_NOT_VISIBLE',None,{'fact_key':action['fact_key'],'label':action['label']})
    return {'qa_id': str(entity('artifact')), 'status': 'partial', 'issues': issues, 'checks': checks,
            'p0_issue_count': sum(i['severity'] == 'P0' for i in issues),
            'coverage': {'structure': 'partial', 'editability': 'partial', 'geometry': 'partial', 'fact_numeric': 'partial',
                         'visual_semantic': 'not_executed', 'fact_semantic': 'not_executed', 'accessibility': 'not_executed',
                         'powerpoint_compatibility': 'not_executed'},
            'acceptance': {'AC-001': 'not_passed', 'GOV-008': 'not_passed'},
            'reason': 'Numeric membership is not semantic truth; PNG/text presence is not visual approval. Full DEC/QA/revision acceptance remains required.'}
