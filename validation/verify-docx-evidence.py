"""Actual Docker DOCX bytes, native relations and boundary checks; no model calls."""
import copy
import hashlib
import io
import json
import platform
import sys
import zipfile
from pathlib import Path
from uuid import uuid4

from PIL import Image

from yoloongppt.docx_evidence import enhance_docx
from yoloongppt.errors import TaskError
from yoloongppt.input_formats import parse_docx, parse_input
from yoloongppt.schemas import ROOT, SchemaRegistry

OUT = Path('/runtime/source-semantic-docx') / ('component-' + uuid4().hex)
OUT.mkdir(parents=True, exist_ok=True)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
PIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
P = 'http://schemas.openxmlformats.org/package/2006/relationships'
B = 'http://schemas.openxmlformats.org/officeDocument/2006/bibliography'
source = 'source_' + str(uuid4()); asset = 'asset_' + str(uuid4()); schemas = SchemaRegistry(); checks = []


def check(name, ok, observed=None):
    assert ok, (name, observed)
    checks.append({'id': name, 'passed': True, 'observed': observed})


def text(value, style=None):
    return '<w:p>' + ('<w:pPr><w:pStyle w:val="' + style + '"/></w:pPr>' if style else '') + '<w:r><w:t>' + value + '</w:t></w:r></w:p>'


def image(rid, drawing_id=1, linked=False):
    return f'''<w:p><w:r><w:drawing><wp:inline><wp:extent cx="2926080" cy="1463040"/>
<wp:docPr id="{drawing_id}" name="人工示意图" title="人工测试图片" descr="蓝色矩形仅用于来源结构验证"/>
<a:graphic><a:graphicData uri="{PIC}"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="source.png"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:{'link' if linked else 'embed'}="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="2926080" cy="1463040"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''


def cell(value, props='', nested=''):
    return '<w:tc><w:tcPr>' + props + '</w:tcPr>' + text(value) + nested + '</w:tc>'


def relation(id_, type_, target, external=False):
    return f'<Relationship Id="{id_}" Type="{R}/{type_}" Target="{target}"' + (' TargetMode="External"' if external else '') + '/>'


def build_fixture():
    buf = io.BytesIO(); Image.new('RGB', (320, 160), '#245C80').save(buf, format='PNG', dpi=(96, 96)); png = buf.getvalue()
    energy = '<w:tbl><w:tblPr><w:tblW w:w="7200" w:type="dxa"/></w:tblPr><w:tblGrid>' + '<w:gridCol w:w="2400"/>' * 3 + '</w:tblGrid>'
    energy += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + ''.join(cell(c) for c in ['楼宇', '基线（kWh）', '本期（kWh）']) + '</w:tr>'
    for row in [('A楼', '100', '90'), ('B楼', '80', '72'), ('C楼', '60', '54')]:energy += '<w:tr>' + ''.join(cell(c) for c in row) + '</w:tr>'
    energy += '</w:tbl>'
    merged = '<w:tbl><w:tblGrid>' + '<w:gridCol w:w="2400"/>' * 3 + '</w:tblGrid>'
    merged += '<w:tr>' + cell('合并测试（万元）', '<w:gridSpan w:val="2"/><w:vMerge w:val="restart"/>') + cell('备注') + '</w:tr>'
    nested = '<w:tbl><w:tblGrid><w:gridCol w:w="1000"/></w:tblGrid><w:tr>' + cell('嵌套单元格原文：2台') + '</w:tr></w:tbl>'
    merged += '<w:tr>' + cell('', '<w:gridSpan w:val="2"/><w:vMerge/>') + cell('保持空合并延续格', nested=nested) + '</w:tr></w:tbl>'
    body = text('人工测试：学校节能试点报告', 'Heading1')
    body += '<w:p><w:r><w:t>2026年试点包括A楼、B楼、C楼。数字均为人工构造的测试数据。</w:t></w:r><w:r><w:footnoteReference w:id="2"/></w:r></w:p>'
    body += text('各楼宇用电数据', 'Heading2') + energy
    body += '<w:p><w:hyperlink r:id="rIdLink"><w:r><w:t>测试资料来源</w:t></w:r></w:hyperlink><w:r><w:t>；引用书目：</w:t></w:r><w:fldSimple w:instr="CITATION TestSource \\l 2052"><w:r><w:t>（人工资料，2026）</w:t></w:r></w:fldSimple></w:p>'
    body += image('rIdImage') + text('图1：人工绘制的来源示意图', 'Caption')
    body += text('合并与嵌套结构边界', 'Heading2') + merged
    body += '<w:p><w:bookmarkStart w:id="1" w:name="TestBookmark"/><w:r><w:t>内部书签目标</w:t></w:r><w:bookmarkEnd w:id="1"/></w:p>'
    body += '<w:p><w:hyperlink w:anchor="TestBookmark"><w:r><w:t>转到书签</w:t></w:r></w:hyperlink><w:r><w:endnoteReference w:id="4"/></w:r></w:p>'
    body += '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> CITATION OtherSource </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>（补充人工资料）</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    body += '<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
    doc = f'<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:a="{A}" xmlns:wp="{WP}" xmlns:pic="{PIC}"><w:body>{body}</w:body></w:document>'
    rels = relation('rIdStyles', 'styles', 'styles.xml') + relation('rIdImage', 'image', 'media/source.png') + relation('rIdLink', 'hyperlink', 'https://example.invalid/artificial-source', True)
    rels += relation('rIdFootnotes', 'footnotes', 'footnotes.xml') + relation('rIdEndnotes', 'endnotes', 'endnotes.xml') + relation('rIdHeader', 'header', 'header1.xml') + relation('rIdFooter', 'footer', 'footer1.xml') + relation('rIdBib', 'customXml', '../customXml/item1.xml')
    parts = {
        'word/document.xml': doc,
        'word/styles.xml': f'<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:outlineLvl w:val="1"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/></w:style></w:styles>',
        'word/_rels/document.xml.rels': f'<Relationships xmlns="{P}">{rels}</Relationships>',
        'word/footnotes.xml': f'<w:footnotes xmlns:w="{W}" xmlns:r="{R}"><w:footnote w:id="-1" w:type="separator"><w:p><w:r><w:separator/></w:r></w:p></w:footnote><w:footnote w:id="2">' + text('注2：数字均为人工测试数据，无真实节能结论。') + '</w:footnote><w:footnote w:id="3">' + text('注3：不同脚注的独立定位。') + '</w:footnote></w:footnotes>',
        'word/endnotes.xml': f'<w:endnotes xmlns:w="{W}"><w:endnote w:id="4">' + text('尾注4：不推断来源真实性。') + '</w:endnote></w:endnotes>',
        'word/header1.xml': f'<w:hdr xmlns:w="{W}">' + text('人工报告页眉') + '</w:hdr>',
        'word/footer1.xml': f'<w:ftr xmlns:w="{W}">' + text('人工报告页脚') + '</w:ftr>',
        'customXml/item1.xml': f'<b:Sources xmlns:b="{B}"><b:Source><b:Tag>TestSource</b:Tag><b:Title>人工测试来源</b:Title><b:Year>2026</b:Year></b:Source><b:Source><b:Tag>OtherSource</b:Tag><b:Title>补充人工来源</b:Title></b:Source></b:Sources>',
        'word/media/source.png': png,
        '_rels/.rels': f'<Relationships xmlns="{P}">' + relation('rIdDocument', 'officeDocument', 'word/document.xml') + '</Relationships>',
    }
    types = '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
    for part, kind in [('word/document.xml', 'document.main'), ('word/styles.xml', 'styles'), ('word/footnotes.xml', 'footnotes'), ('word/endnotes.xml', 'endnotes'), ('word/header1.xml', 'header'), ('word/footer1.xml', 'footer')]:
        types += f'<Override PartName="/{part}" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{kind}+xml"/>'
    parts['[Content_Types].xml'] = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + types + '</Types>'
    return parts


def pack(parts):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as archive:
        for part, payload in parts.items():archive.writestr(part, payload)
    return buf.getvalue()


def enhanced(raw):
    doc, segs, warnings = parse_docx(raw, source, asset)
    # Works before and after root integrates the helper, without invoking twice.
    if 'structure_evidence' not in doc:doc, segs, extra = enhance_docx(raw, doc, segs); warnings += extra
    for seg in segs:schemas.validate('source-anchor.schema.json', seg['anchor'])
    return doc, segs, warnings


def reject(name, raw, code):
    try:enhanced(raw)
    except TaskError as error:check(name, error.code == code, error.code)
    else:raise AssertionError(name + ' unexpectedly accepted')


parts = build_fixture(); raw = pack(parts); (OUT / 'report.docx').write_bytes(raw)
doc, segs, warnings = enhanced(raw); evidence = doc['structure_evidence']
(OUT / 'report-parsed.json').write_text(json.dumps({'document': doc, 'segments': segs, 'warnings': warnings}, ensure_ascii=False, indent=2), encoding='utf-8')
check('actual_docx_zip_bytes', zipfile.is_zipfile(io.BytesIO(raw)) and len(doc['package_parts']) == len(parts), {'bytes': len(raw), 'source_sha256': hashlib.sha256(raw).hexdigest()})
check('heading_native_style_outline', next(s for s in segs if s['raw_text'] == '各楼宇用电数据')['metadata']['source_context']['heading_level'] == 2)
check('source_text_chinese_roundtrip', any(s['raw_text'] == '注2：数字均为人工测试数据，无真实节能结论。' for s in segs))
check('anchors_schema_and_unique', len({s['anchor']['native_locator'] for s in segs}) == len(segs), {'segments': len(segs)})
check('no_fake_physical_pages', all(s['anchor']['locator']['page_location']['status'] == 'pending' and not s['anchor']['locator']['page_location']['page_numbers'] for s in segs))
check('external_hyperlink_actual_target_not_fetched', evidence['hyperlinks'][0]['target'] == 'https://example.invalid/artificial-source' and evidence['hyperlinks'][0]['retrieval'] == 'not_fetched')
check('literal_uri_grounding_without_changing_paragraph',any(s['raw_text']=='https://example.invalid/artificial-source' and s['data']['kind']=='docx_hyperlink_target' for s in segs))
check('bookmark_unique_actual_native_target', evidence['hyperlinks'][1]['bookmark_status'] == 'resolved' and 'bookmarkStart' in evidence['hyperlinks'][1]['bookmark_native_locator'])
check('image_part_bytes_hash_dimensions', len(evidence['images']) == 1 and evidence['images'][0]['sha256'] == hashlib.sha256(parts['word/media/source.png']).hexdigest() and (evidence['images'][0]['pixel_width'], evidence['images'][0]['pixel_height']) == (320, 160))
check('image_alt_description_actual_extent', evidence['images'][0]['alt_text'] == '人工测试图片' and evidence['images'][0]['description'] == '蓝色矩形仅用于来源结构验证' and evidence['images'][0]['display_extent_emu'] == {'cx': 2926080, 'cy': 1463040})
check('image_nontext_no_ocr_or_permission', [s['raw_text'] for s in segs if s['data']['kind'] == 'docx_image'] == [''] and evidence['images'][0]['license'] == 'unknown' and evidence['images'][0]['ocr_status'] == 'not_executed')
check('footnote_exact_relationship_reference', next(r for r in evidence['note_references'] if r['kind'] == 'footnote')['note_text'] == '注2：数字均为人工测试数据，无真实节能结论。' and next(r for r in evidence['note_references'] if r['kind'] == 'footnote')['relationship_id'] == 'rIdFootnotes')
check('endnote_reference_actual_target', next(r for r in evidence['note_references'] if r['kind'] == 'endnote')['note_id'] == '4' and next(r for r in evidence['note_references'] if r['kind'] == 'endnote')['status'] == 'resolved')
check('note_id_and_part_unique', len({n['evidence_id'] for n in evidence['notes']}) == 4 and {n['note_id'] for n in evidence['notes']} == {'-1', '2', '3', '4'})
check('simple_complex_citations_separate', [c['citation_tag'] for c in evidence['citation_fields']] == ['TestSource', 'OtherSource'] and all(c['bibliography_status'] == 'resolved' for c in evidence['citation_fields']))
check('citation_native_bibliography_not_truth', evidence['citation_fields'][0]['bibliography']['fields'][1]['text'] == '人工测试来源' and evidence['citation_fields'][0]['semantic_status'] == 'not_inferred')
energy = next(t for t in evidence['tables'] if t['table_index'] == 0)
merged = next(t for t in evidence['tables'] if t['table_index'] == 1)
check('table_logical_grid_exact_cells', len(energy['rows']) == 4 and energy['declared_grid_columns'] == 3 and energy['rows'][2]['cells'][1]['text'] == '80' and energy['rows'][2]['cells'][1]['logical_grid']['column_start'] == 1)
check('units_header_candidates_no_assumption', next(s for s in segs if s['raw_text'] == '80')['metadata']['source_context']['column_header_candidates'][0]['units'][0]['raw_text'] == 'kWh' and next(s for s in segs if s['raw_text'] == '80')['metadata']['source_context']['column_header_candidates'][0]['relation_status'] == 'candidate')
check('merged_owner_references_empty_continuation', merged['rows'][1]['cells'][0]['logical_grid']['vertical_owner_evidence_id'] == merged['rows'][0]['cells'][0]['evidence_id'] and merged['rows'][1]['cells'][0]['text'] == '' and merged['rows'][1]['cells'][0]['logical_grid']['column_span'] == 2)
check('nested_table_separate_evidence_no_parent_flattening', any(t['parent_table_cell_path'] is not None for t in evidence['tables']) and any(s['raw_text'] == '嵌套单元格原文：2台' for s in segs) and merged['rows'][1]['cells'][1]['text'] == '保持空合并延续格')
check('caption_adjacency_marked_candidate', evidence['caption_candidates'][0]['targets'][0]['evidence_id'] == evidence['images'][0]['evidence_id'] and evidence['caption_candidates'][0]['relationship_status'] == 'candidate')
check('section_header_footer_real_relationships', evidence['sections'][0]['story_references'][0]['target_part'] == 'word/header1.xml' and evidence['sections'][0]['story_references'][1]['target_part'] == 'word/footer1.xml')
check('context_no_xml_or_ocr_text', all('raw_xml' not in json.dumps(s['metadata']['source_context'], ensure_ascii=False) for s in segs))
check('input_dicts_not_mutated', enhance_docx(raw, *[copy.deepcopy(x) for x in parse_docx(raw, source, asset)[:2]])[1][0]['raw_text'] == segs[0]['raw_text'])

boundary = dict(parts); del boundary['word/media/source.png']; boundary['word/document.xml'] = parts['word/document.xml'].replace('w:id="2"', 'w:id="999"').replace('<w:gridSpan w:val="2"/>', '<w:gridSpan w:val="999999999"/>').replace('CITATION TestSource \\l 2052', 'CITATION TestSource \\m MissingSource')
badraw = pack(boundary); (OUT / 'boundary-missing.docx').write_bytes(badraw); bd, bs, bw = enhanced(badraw)
(OUT / 'boundary-parsed.json').write_text(json.dumps({'document': bd, 'segments': bs, 'warnings': bw}, ensure_ascii=False, indent=2), encoding='utf-8')
check('missing_image_no_fabricated_pixels', bd['structure_evidence']['images'][0]['status'] == 'unresolved' and bd['structure_evidence']['images'][0]['sha256'] is None and any(w['code'] == 'DOCX_IMAGE_PART_MISSING' for w in bw))
check('orphan_note_explicit_not_guessed', any(w['code'] == 'DOCX_NOTE_REFERENCE_UNRESOLVED' for w in bw) and bd['structure_evidence']['note_references'][0]['note_text'] is None)
check('huge_grid_bounded_no_content_drop', any(w['code'] == 'DOCX_GRID_VALUE_INVALID' for w in bw) and any(s['raw_text'] == '合并测试（万元）' for s in bs))
check('multi_citation_missing_secondary_not_claimed_resolved', bd['structure_evidence']['citation_fields'][0]['citation_tags'] == ['TestSource', 'MissingSource'] and bd['structure_evidence']['citation_fields'][0]['bibliography_status'] == 'unresolved')
external = dict(parts); external['word/document.xml'] = parts['word/document.xml'].replace(image('rIdImage'), image('rIdRemote', linked=True)); external['word/_rels/document.xml.rels'] = parts['word/_rels/document.xml.rels'].replace('</Relationships>', relation('rIdRemote', 'image', 'https://example.invalid/remote.png', True) + '</Relationships>')
ed, es, ew = enhanced(pack(external)); (OUT / 'boundary-external.docx').write_bytes(pack(external))
check('external_image_not_retrieved', ed['structure_evidence']['images'][0]['status'] == 'external_not_fetched' and ed['structure_evidence']['images'][0]['bytes'] is None and any(w['code'] == 'DOCX_EXTERNAL_IMAGE_NOT_FETCHED' for w in ew))
duplicate = dict(parts); duplicate['word/footnotes.xml'] = parts['word/footnotes.xml'].replace('w:id="3"', 'w:id="2"'); duplicate_raw = pack(duplicate); (OUT / 'boundary-duplicate-note.docx').write_bytes(duplicate_raw)
reject('duplicate_note_identity_rejected', duplicate_raw, 'DOCX_NOTE_ID_AMBIGUOUS')
duplicate = dict(parts); duplicate['word/_rels/document.xml.rels'] = parts['word/_rels/document.xml.rels'].replace('Id="rIdStyles"', 'Id="rIdImage"'); duplicate_raw = pack(duplicate); (OUT / 'boundary-duplicate-relationship.docx').write_bytes(duplicate_raw)
reject('duplicate_relationship_identity_rejected', duplicate_raw, 'DOCX_RELATIONSHIP_AMBIGUOUS')
unsafe = dict(parts); unsafe['word/_rels/document.xml.rels'] = parts['word/_rels/document.xml.rels'].replace('Target="media/source.png"', 'Target="../../escape.png"')
reject('unsafe_internal_relationship_rejected', pack(unsafe), 'INPUT_UNSAFE_RELATIONSHIP')
unclosed = dict(parts); unclosed['word/document.xml'] = parts['word/document.xml'].replace('<w:r><w:fldChar w:fldCharType="end"/></w:r>', '')
ud, us, uw = enhanced(pack(unclosed)); check('unclosed_complex_field_preserved_not_citation', any(w['code'] == 'DOCX_FIELD_UNCLOSED' for w in uw) and [c['citation_tag'] for c in ud['structure_evidence']['citation_fields']] == ['TestSource'])

original = (ROOT / 'AI_PPT_PDR_完整需求定义_V0.3.docx').read_bytes(); od, os, ow = enhanced(original)
check('original_requirement_docx_current_enhance', len(os) > 308 and all(s['anchor']['locator']['page_location']['status'] == 'pending' for s in os), {'segments': len(os), 'tables': len(od['structure_evidence']['tables']), 'images': len(od['structure_evidence']['images']), 'warnings': len(ow), 'source_sha256': hashlib.sha256(original).hexdigest()})
report = {'passed': True, 'checks': checks, 'requirement_ids': ['IN-003', 'IN-016', 'SYS-003'],
          'task_ids': ['TASK-IN-003', 'TASK-IN-016', 'TASK-SYS-003'], 'acceptance_context': 'AC-002 component evidence, not full acceptance',
          'runtime': {'python': sys.version, 'platform': platform.platform(), 'model_calls': 0},
          'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT / 'src/yoloongppt/docx_evidence.py', ROOT / 'src/yoloongppt/input_formats.py', Path(__file__)]},
          'fixture_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')},
          'remaining': ['Word physical-page layout/rendering', 'nonstandard story filenames unsupported by original parser', 'image OCR/meaning', 'citation semantic truth', 'full AC-002 PPTX/render/QA/decision acceptance'],
          'boundary': 'Actual package bytes, native relationships and schema anchors; no external retrieval, license inference or semantic truth claim.'}
(OUT / 'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'passed': True, 'checks': len(checks), 'report': str(OUT / 'checks.json'), 'model_calls': 0}, ensure_ascii=False))
