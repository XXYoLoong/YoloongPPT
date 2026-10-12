"""TASK-IN-008/016/SYS-003 targeted actual-byte component checks; zero models."""
import copy
import hashlib
import io
import json
import platform
import sys
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

import xlsxwriter

from yoloongppt.errors import TaskError
from yoloongppt.input_formats import parse_xlsx, NS
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.xlsx_evidence import enhance_xlsx

ROOT = Path('/workspace')
OUTPUT = Path('/runtime/source-semantic-xlsx') / ('component-' + __import__('uuid').uuid4().hex)
OUTPUT.mkdir(parents=True, exist_ok=True)
checks = []
schemas = SchemaRegistry()
SOURCE = 'source_3266d3a6-425a-44fd-8618-6a3ad98f6017'
ASSET = 'asset_1e6e8a9e-7731-4d27-a334-28788224b0bc'


def check(name, passed, observed=None):
    checks.append({'id':name,'passed':bool(passed),'observed':observed})
    if not passed: raise AssertionError(name)


def reject(name, document, segments, code):
    try: enhance_xlsx(document, segments)
    except TaskError as error: check(name, error.code == code, error.result('component-check')['error'])
    else: check(name, False, 'unexpectedly accepted')


def repack(raw, edit):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive: parts = {n:archive.read(n) for n in archive.namelist()}
    edit(parts)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items(): archive.writestr(name,content)
    return buffer.getvalue()


def workbook(date1904=False):
    buffer = io.BytesIO(); book = xlsxwriter.Workbook(buffer, {'in_memory':True,'date_1904':date1904})
    sheet = book.add_worksheet('分类时序')
    formats = {name:book.add_format({'num_format':code}) for name,code in {
        'date':'yyyy-mm-dd', 'power':'#,##0.00" kWh"', 'percent':'0.00%', 'integer':'0',
        'unit':'0.0"万元"', 'negative':'0.00;[Red](0.00);"零";"文:"@',
        'literal_semicolon':'0";件"', 'optional':'0.0##', 'zero_pad':'00000',
        'month':'yyyy"年"m"月"d"日"', 'datetime':'yyyy-mm-dd hh:mm:ss',
        'unknown_scientific':'0.00E+00', 'unknown_scaled':'0.0,,"M"', 'unknown_fraction':'# ?/?',
        'unknown_condition':'[>=100]0;0', 'unknown_locale':'[$-409]m/d/yy',
        'unknown_fill':'0* ', 'hide':';;;', 'text_hide':'0;0;0;', 'date_builtin':'mm-dd-yy',
        'date_duration':'[h]:mm:ss'}.items()}
    sheet.write_row('A1',['日期','类别','电量（kWh）','下降比例','收入（万元）'])
    rows = [(39267 if date1904 else 40729, '楼宇A', 1234.567, 0.08, 23.45),
            ((39267 if date1904 else 40729)+1,'楼宇B',987.5,0.125,25.1)]
    for row_index,row in enumerate(rows,1):
        sheet.write_number(row_index,0,row[0],formats['date']); sheet.write_string(row_index,1,row[1])
        sheet.write_number(row_index,2,row[2],formats['power']); sheet.write_number(row_index,3,row[3],formats['percent'])
        sheet.write_number(row_index,4,row[4],formats['unit'])
    sheet.add_table('A1:E3',{'columns':[{'header':s} for s in ['日期','类别','电量（kWh）','下降比例','收入（万元）']]})
    sheet.write_formula('C4','=SUM(C2:C3)',formats['power'],2222.067)
    chart = book.add_chart({'type':'column'}); chart.add_series({'categories':"'分类时序'!$B$2:$B$3",'values':"'分类时序'!$C$2:$C$3"})
    sheet.insert_chart('G1',chart)
    boundary = book.add_worksheet('边界')
    values = {
        'A1':(12.5,'negative'),'A2':(-12.5,'negative'),'A3':(0,'negative'),
        'A4':(123,'zero_pad'),'A5':(1.23,'optional'),'A6':(1.2,'optional'),
        'A7':(42,'literal_semicolon'),'A8':(1.2345,'unknown_scientific'),
        'A9':(12200000,'unknown_scaled'),'A10':(1.5,'unknown_fraction'),
        'A11':(101,'unknown_condition'),'A12':(40729,'unknown_locale'),
        'A13':(42,'unknown_fill'),'A14':(42,'hide'),'A15':(40729,'date_builtin'),
        'A16':(60,'date'),'A17':(0,'date'),'A18':(-1,'date'),
        'A19':(40729.5,'datetime'),'A20':(40729.12345,'datetime'),
        'A21':(40729,'month'),'A22':(1.5,'date_duration')}
    for address,(value,fmt) in values.items(): boundary.write_number(address,value,formats[fmt])
    boundary.write_string('B1','中文原文'); boundary.write_boolean('B2',True); boundary.write_boolean('B3',False)
    boundary.write_string('B4','中文',formats['negative']); boundary.write_string('B5','隐藏文字',formats['text_hide'])
    boundary.write_number('B6',1.23456789012345); boundary.write_number('B7',-12.5,formats['integer'])
    boundary.write_number('B8',42,formats['integer']); boundary.conditional_format('B8',{'type':'cell','criteria':'>','value':0,'format':formats['percent']})
    boundary.write_formula('C1','=1+1',formats['integer'],2)
    boundary.write_formula('C2','=1+1',formats['integer'],2)
    boundary.write_formula('C3',"='[1]Sheet1'!A1",formats['integer'],7)
    boundary.write_formula('C4','=1/0',formats['integer'],'#DIV/0!')
    boundary.merge_range('D1:E1','合并标题'); boundary.write_number('E1',99,formats['integer'])
    boundary.write_string('F2','隐藏行原文'); boundary.set_row(1,None,None,{'hidden':True})
    boundary.write_number('G3',88,formats['integer']); boundary.set_column('G:G',None,None,{'hidden':True})
    hidden = book.add_worksheet('隐藏表'); hidden.write_string('A1','隐藏表原文'); hidden.hide()
    book.close(); raw = buffer.getvalue()
    def adjust(parts):
        sheet_node = ET.fromstring(parts['xl/worksheets/sheet2.xml'])
        for cell in sheet_node.findall('.//s:c',NS):
            if cell.get('r') == 'C2': cell.remove(cell.find('s:v',NS))
            if cell.get('r') == 'A15':
                # XlsxWriter serializes mm-dd-yy as a custom format. The boundary
                # intentionally requires the actual locale-dependent built-in 14.
                styles = ET.fromstring(parts['xl/styles.xml'])
                styles.find('s:cellXfs',NS)[int(cell.get('s'))].set('numFmtId','14')
                parts['xl/styles.xml'] = ET.tostring(styles,encoding='utf-8',xml_declaration=True)
        row = sheet_node.find('s:sheetData/s:row',NS)
        for ref,typ,value in [('H1','d','2026-10-11T12:30:00Z'),('I1','d','2026-02-30'),('J1','n','NaN'),('K1','n','1e9999')]:
            cell = ET.SubElement(row,'{'+NS['s']+'}c',{'r':ref,'t':typ}); ET.SubElement(cell,'{'+NS['s']+'}v').text = value
        parts['xl/worksheets/sheet2.xml'] = ET.tostring(sheet_node,encoding='utf-8',xml_declaration=True)
        rels = ET.Element('Relationships',{'xmlns':'http://schemas.openxmlformats.org/package/2006/relationships'})
        ET.SubElement(rels,'Relationship',{'Id':'external1','Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
                                         'Target':'https://example.invalid/not-fetched','TargetMode':'External'})
        parts['xl/worksheets/_rels/sheet2.xml.rels'] = ET.tostring(rels)
        link = ET.Element('{'+NS['s']+'}externalLink')
        external = ET.SubElement(link,'{'+NS['s']+'}externalBook',{'{'+NS['r']+'}id':'rId1'})
        sheet_names = ET.SubElement(external,'{'+NS['s']+'}sheetNames')
        ET.SubElement(sheet_names,'{'+NS['s']+'}sheetName',{'val':'Sheet1'})
        parts['xl/externalLinks/externalLink1.xml'] = ET.tostring(link)
        parts['xl/externalLinks/_rels/externalLink1.xml.rels'] = b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLinkPath" Target="missing.xlsx" TargetMode="External"/></Relationships>'
        wb = ET.fromstring(parts['xl/workbook.xml']); references = ET.SubElement(wb,'{'+NS['s']+'}externalReferences')
        ET.SubElement(references,'{'+NS['s']+'}externalReference',{'{'+NS['r']+'}id':'externalBook1'})
        parts['xl/workbook.xml'] = ET.tostring(wb)
        wb_rels = ET.fromstring(parts['xl/_rels/workbook.xml.rels'])
        ET.SubElement(wb_rels,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',{'Id':'externalBook1','Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink','Target':'externalLinks/externalLink1.xml'})
        parts['xl/_rels/workbook.xml.rels'] = ET.tostring(wb_rels)
        content_types = ET.fromstring(parts['[Content_Types].xml'])
        ET.SubElement(content_types,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',{'PartName':'/xl/externalLinks/externalLink1.xml','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.externalLink+xml'})
        parts['[Content_Types].xml'] = ET.tostring(content_types)
    return repack(raw,adjust)


def parse_fixture(filename, raw):
    (OUTPUT/filename).write_bytes(raw)
    d,s,w = parse_xlsx(raw,SOURCE,ASSET); before_d = copy.deepcopy(d); before_s = copy.deepcopy(s)
    enriched_d,enriched_s,warnings = enhance_xlsx(d,s)
    check(filename+'_input_unmutated',d == before_d and s == before_s)
    check(filename+'_all_cells_and_anchors_preserved',len(enriched_s)==len(s) and [i['anchor'] for i in s]==[i['anchor'] for i in enriched_s])
    for item in enriched_s: schemas.validate('source-anchor.schema.json',item['anchor'])
    check(filename+'_anchor_schema_valid',True,{'segments':len(enriched_s)})
    for old,new in zip(s,enriched_s):
        for k,v in old['data'].items():
            if new['data'][k] != v: raise AssertionError(filename+'_original_'+k+'_changed')
    check(filename+'_all_original_cell_data_preserved',True)
    evidence = {'fixture':filename,'fixture_sha256':hashlib.sha256(raw).hexdigest(),'document':enriched_d,'segments':enriched_s,
                'base_parser_warnings':w,'projection_warnings':warnings,'model_calls':0}
    (OUTPUT/(filename+'.evidence.json')).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    return enriched_d,enriched_s,warnings,before_d,before_s


def get(segments,sheet,ref): return next(i for i in segments if i['anchor']['locator']['sheet_name']==sheet and i['anchor']['locator']['cell_ref']==ref)


try:
    d,s,w,original_d,original_s = parse_fixture('classified-timeseries-1900.xlsx',workbook())
    check('numeric_thousands_rounding_and_literal_unit',get(s,'分类时序','C2')['raw_text']=='1,234.57 kWh')
    check('percent_display_scale_preserves_raw_fraction',get(s,'分类时序','D2')['raw_text']=='8.00%' and get(s,'分类时序','D2')['data']['stored_value']=='0.08'
          and get(s,'分类时序','D2')['metadata']['source_context']['display_projection']['numeric_scale']=='100')
    check('quoted_chinese_unit_projection',get(s,'分类时序','E2')['raw_text']=='23.5万元')
    check('1900_serial_date_custom_format',get(s,'分类时序','A2')['raw_text']=='2011-07-05')
    check('formula_only_saved_cache_and_freshness',get(s,'分类时序','C4')['raw_text']=='2,222.07 kWh' and get(s,'分类时序','C4')['data']['formula']=='SUM(C2:C3)'
          and get(s,'分类时序','C4')['metadata']['source_context']['cache_freshness']=='unverified')
    check('positive_negative_zero_sections', [get(s,'边界',r)['raw_text'] for r in ['A1','A2','A3']]==['12.50','(12.50)','零'])
    check('padding_and_optional_decimals',[get(s,'边界',r)['raw_text'] for r in ['A4','A5','A6']]==['00123','1.23','1.2'])
    check('quoted_semicolon_is_literal',get(s,'边界','A7')['raw_text']=='42;件')
    check('locale_boundary_is_actual_builtin_14',get(s,'边界','A15')['data']['number_format_id']==14)
    for ref in ['A8','A9','A10','A11','A12','A13','A15','A18','A20','A22','I1','J1','K1']:
        check('unsupported_'+ref+'_never_raw_numeric_fact',get(s,'边界',ref)['raw_text']=='' and get(s,'边界',ref)['data']['display_projection']['status']=='unsupported',
              get(s,'边界',ref)['data']['display_projection']['reason'])
    check('noncalendar_1900_day_zero_and_fake_leap_day',all(get(s,'边界',r)['raw_text']=='' and get(s,'边界',r)['data']['display_projection']['reason']=='excel_1900_noncalendar_serial' for r in ['A16','A17']))
    check('whole_precision_datetime',get(s,'边界','A19')['raw_text']=='2011-07-05 12:00:00')
    check('chinese_date_literals',get(s,'边界','A21')['raw_text']=='2011年7月5日')
    check('text_and_boolean_source_types',[get(s,'边界',r)['raw_text'] for r in ['B1','B2','B3']]==['中文原文','TRUE','FALSE'])
    check('custom_text_fourth_section',get(s,'边界','B4')['raw_text']=='文:中文')
    check('intentional_hidden_formats_not_raw_fact',get(s,'边界','A14')['raw_text']=='' and get(s,'边界','A14')['data']['display_projection']['status']=='hidden_by_format'
          and get(s,'边界','B5')['raw_text']=='')
    check('general_exact_scalar_marked_not_excel_display',get(s,'边界','B6')['metadata']['source_context']['display_projection']['status']=='typed_numeric_projection'
          and not get(s,'边界','B6')['metadata']['source_context']['display_projection']['excel_rendered'])
    check('automatic_negative_plain_format',get(s,'边界','B7')['raw_text']=='-13')
    check('conditional_format_final_display_unresolved',get(s,'边界','B8')['raw_text']=='' and get(s,'边界','B8')['data']['display_projection']['reason']=='conditional_final_display_unresolved')
    check('formula_missing_cache_preserved_nontext',get(s,'边界','C2')['raw_text']=='' and get(s,'边界','C2')['data']['formula']=='1+1'
          and get(s,'边界','C2')['data']['display_projection']['reason']=='formula_cache_missing')
    check('external_formula_not_evaluated',get(s,'边界','C3')['raw_text']=='7' and get(s,'边界','C3')['metadata']['source_context']['external_formula_reference_candidate']
          and get(s,'边界','C3')['metadata']['source_context']['cache_freshness']=='unverified')
    check('error_cache_not_fact_text',get(s,'边界','C4')['raw_text']=='' and get(s,'边界','C4')['data']['display_projection']['logical_type']=='error')
    check('merged_covered_value_preserved_nontext',get(s,'边界','E1')['raw_text']=='' and get(s,'边界','E1')['data']['stored_value']=='99'
          and get(s,'边界','E1')['data']['merge_membership']['role']=='covered')
    check('hidden_sheet_row_column_explicit',all(not get(s,sheet,ref)['metadata']['source_context']['visibility']['visible']
          for sheet,ref in [('边界','F2'),('边界','G3'),('隐藏表','A1')]))
    check('source_iso_datetime_and_timezone_preserved',get(s,'边界','H1')['raw_text']=='2026-10-11T12:30:00Z')
    ctx = get(s,'分类时序','C2')['metadata']['source_context']
    check('anchored_header_range_unit_candidates',ctx['header_candidates'][0]['cell_ref']=='C1' and ctx['range_candidates'][0]['range_ref']=='A1:E3'
          and any(u['text']=='kWh' and u['origin']=='header_parenthesized_text' for u in ctx['unit_candidates'])
          and all('anchor' in u for u in ctx['unit_candidates']),ctx)
    check('chart_candidates_keep_numeric_cells_not_date_serials',d['sheets'][0]['chart_candidates'][0]['value_cell_refs']==['C2','C3']
          and all(x['series_column_index'] != 0 for x in d['sheets'][0]['chart_candidates']),d['sheets'][0]['chart_candidates'])
    check('drawings_and_external_links_unresolved_not_fetched',{'XLSX_DRAWING_SEMANTICS_UNRESOLVED','XLSX_EXTERNAL_RELATIONSHIP_NOT_FETCHED','XLSX_EXTERNAL_LINK_PARTS_NOT_EVALUATED'} <= {x['code'] for x in w})
    d4,s4,w4,_,_ = parse_fixture('classified-timeseries-1904.xlsx',workbook(True))
    check('1904_epoch_and_1462_day_difference',get(s4,'分类时序','A2')['raw_text']=='2011-07-05'
          and Decimal(get(s,'分类时序','A2')['data']['stored_value'])-Decimal(get(s4,'分类时序','A2')['data']['stored_value'])==1462)
    check('1904_zero_valid_date',get(s4,'边界','A17')['raw_text']=='1904-01-01')
    altered = copy.deepcopy(original_s); altered[0]['anchor']['native_locator']+='-tampered'
    reject('tampered_native_anchor_rejected',original_d,altered,'XLSX_PROJECTION_ANCHOR_INVALID')
    altered = copy.deepcopy(original_s); altered.append(copy.deepcopy(altered[0]))
    reject('duplicate_evidence_anchor_rejected',original_d,altered,'XLSX_PROJECTION_DUPLICATE_CELL')
    altered = copy.deepcopy(original_d); altered['sheets'][0]['cells'].append(copy.deepcopy(altered['sheets'][0]['cells'][0]))
    reject('duplicate_native_cell_rejected',altered,original_s,'XLSX_PROJECTION_DUPLICATE_CELL')
    altered = copy.deepcopy(original_d); altered['sheets'][0]['merged_ranges']=['A1:B2','B2:C3']
    reject('overlapping_merge_rejected',altered,original_s,'XLSX_PROJECTION_MERGE_OVERLAP')
    altered = copy.deepcopy(original_d); altered['sheets'][0]['raw_xml']='<!DOCTYPE a [<!ENTITY x "bad">]><a/>'
    reject('enhancement_entity_xml_rejected',altered,original_s,'XLSX_PROJECTION_XML_INVALID')
    altered = copy.deepcopy(original_d); altered['date_system']='unknown'
    reject('unknown_epoch_rejected',altered,original_s,'XLSX_PROJECTION_INPUT_INVALID')
    check('utf8_chinese_json_roundtrip',json.loads((OUTPUT/'classified-timeseries-1900.xlsx.evidence.json').read_text(encoding='utf-8'))['segments'][1]['raw_text']=='类别')
except Exception:
    (OUTPUT/'checks-failed.json').write_text(json.dumps({'passed':False,'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
    raise
report = {'passed':True,'checks':checks,'model_calls':0,'requirement_ids':['IN-008','IN-016','SYS-003'],
          'task_ids':['TASK-IN-008','TASK-IN-016','TASK-SYS-003'],'acceptance_scenarios':['AC-005'],
          'versions':{'python':sys.version,'xlsxwriter':xlsxwriter.__version__,'platform':platform.platform()},
          'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/yoloongppt/xlsx_evidence.py',ROOT/'src/yoloongppt/input_formats.py',Path(__file__)]},
          'fixture_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.glob('*.xlsx')},
          'boundary':'Actual saved-byte component checks; no Excel rendering, no formula refresh, no model or PPTX/QA integration, AC-005 not passed.'}
(OUTPUT/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(checks),'model_calls':0,'report':str(OUTPUT/'checks.json')},ensure_ascii=False))
