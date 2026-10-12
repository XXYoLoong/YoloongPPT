"""IN-004/016, SYS-003: conservative geometry candidates over Poppler evidence.

These candidates supply context to fact interpretation. They never replace the
preserved text, prove table semantics, invent cells, or perform OCR.
"""
import copy
import hashlib
import json
import math
import statistics
from collections import Counter

from .errors import TaskError


VERSION = 'pdf-geometry-1'
MAX_PAGES = 256
MAX_WORDS_PER_PAGE = 4096
MAX_WORDS = 65536
POLICY = {
    'coordinate_space': 'pdf_points_top_left',
    'semantic_claim_status': 'candidate_not_semantic_truth',
    'table_lines': 'not_parsed_by_bbox_layout',
    'missing_cells': 'not_created',
    'duplicate_text': 'preserved_as_distinct_word_anchors',
    'cross_page_tables': 'not_joined',
    'ocr': 'not_executed',
    'image_geometry_and_relationships': 'unknown_from_pdfimages_list',
    'grouping_thresholds': {'word_gap_min_pt': 12, 'word_gap_height_factor': 1.5,
                            'row_center_max_pt': 3, 'row_height_factor': .3,
                            'column_start_tolerance_pt': 4, 'grid_min_rows': 3,
                            'grid_min_columns': 2, 'grid_max_columns': 12,
                            'grid_max_vertical_gap_height_factor': 3},
}


def _fail(message, details=None):
    raise TaskError('PDF_EVIDENCE_INVALID', message, 'PdfEvidence',
                    ['IN-004', 'IN-016', 'SYS-003'], details or [])


def _number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def _bbox(value, location):
    if not isinstance(value, dict) or any(not _number(value.get(k)) for k in ('xMin', 'yMin', 'xMax', 'yMax')):
        _fail('PDF原始几何缺少有限坐标；未猜测位置。', [{'location': location}])
    if value['xMax'] < value['xMin'] or value['yMax'] < value['yMin']:
        _fail('PDF原始几何边界反向。', [{'location': location}])
    return copy.deepcopy(value)


def _union(items):
    return {k: (min if k.endswith('Min') else max)(x['bbox'][k] for x in items)
            for k in ('xMin', 'yMin', 'xMax', 'yMax')}


def _height(item):
    return item['bbox']['yMax'] - item['bbox']['yMin']


def _center(item):
    return (item['bbox']['yMin'] + item['bbox']['yMax']) / 2


def _id(page, kind, number):
    return f'pdf:p{page}:{kind}{number}'


def _image_inventory(raw, page_count, warnings):
    result = {'status': 'unavailable' if raw is None else 'parsed', 'images': [],
              'unparsed_rows': [], 'geometry_status': 'unknown', 'ocr_status': 'not_executed',
              'asset_extraction_status': 'not_executed', 'relationship_status': 'unknown'}
    if raw is None:
        warnings.append({'code': 'PDF_IMAGE_CONTEXT_UNAVAILABLE', 'message': '图片清单不可用，不把未知数量写成零。'})
        return result
    if not isinstance(raw, str):
        _fail('PDF图片清单必须保留Poppler原始文本。')
    lines = raw.splitlines()
    header = any('object ID' in x and 'x-ppi' in x and 'y-ppi' in x and 'ratio' in x for x in lines)
    if not header:
        result.update(status='unrecognized', unparsed_rows=lines)
        warnings.append({'code': 'PDF_IMAGE_INVENTORY_FORMAT_UNKNOWN', 'message': '图片清单列标题未知，原始文本保留，未猜测字段。'})
        return result
    seen = set()
    for line in lines:
        if not line.strip() or 'object ID' in line or set(line.strip()) <= {'-'}:
            continue
        fields = line.split()
        try:
            if len(fields) != 16:
                raise ValueError('column count')
            page, index, width, height, components, bits, obj, generation = [int(fields[i]) for i in (0,1,3,4,6,7,10,11)]
            density_x, density_y = float(fields[12]), float(fields[13])
            if (page < 1 or page > page_count or index < 0 or width < 1 or height < 1 or
                    min(components, bits, obj, generation, density_x, density_y) < 0 or
                    not math.isfinite(density_x) or not math.isfinite(density_y)):
                raise ValueError('invalid value')
        except (ValueError, OverflowError):
            result['unparsed_rows'].append(line)
            continue
        key = (page, index)
        item = {'image_id': _id(page, 'image', index), 'page_number': page, 'image_index': index,
                'type': fields[2], 'width_px': width, 'height_px': height, 'color_space': fields[5],
                'components': components, 'bits_per_component': bits, 'encoding': fields[8],
                'interpolation': fields[9], 'object_id': {'number': obj, 'generation': generation},
                'density_ppi': {'x': density_x, 'y': density_y}, 'stored_size_raw': fields[14],
                'ratio_raw': fields[15], 'raw_row': line, 'bbox': None, 'asset_id': None,
                'relationship_status': 'unknown', 'anchor': {'native_locator': f'pdf:page={page},image={index},object={obj}:{generation}',
                    'locator': {'kind': 'pdf_image_inventory', 'page_number': page, 'page_index': page-1,
                                'image_index': index, 'object_id': obj, 'object_generation': generation},
                    'locator_status': 'inventory_only_no_page_geometry'}}
        if key in seen:
            result['status'] = 'partial'
            item['identity_status'] = 'duplicate_inventory_index'
            warnings.append({'code': 'PDF_IMAGE_INVENTORY_DUPLICATE', 'page_number': page, 'image_index': index,
                             'message': '清单页/序号重复，两条原记录保留，未覆盖或认定同一图像。'})
        seen.add(key)
        result['images'].append(item)
    if result['unparsed_rows']:
        result['status'] = 'partial'
        warnings.append({'code': 'PDF_IMAGE_INVENTORY_ROWS_UNKNOWN', 'count': len(result['unparsed_rows']),
                         'message': '部分图片清单行未识别，原始行保留，不声称清单完整。'})
    return result


def _fragments(page, block_index, line_index, line, word_items, warnings):
    if not word_items:
        return []
    if any(a['bbox']['xMin'] > b['bbox']['xMin'] for a,b in zip(word_items, word_items[1:])):
        warnings.append({'code': 'PDF_LINE_ORDER_AMBIGUOUS', 'page_number': page,
                         'block_index': block_index, 'line_index': line_index,
                         'message': '字原序与横向坐标冲突，逐字证据保留，该行不参与行列推断。'})
        return []
    median_height = statistics.median(_height(x) for x in word_items)
    threshold = max(12, median_height * 1.5)
    groups = [[]]
    for word in word_items:
        if groups[-1] and word['bbox']['xMin'] - groups[-1][-1]['bbox']['xMax'] > threshold:
            groups.append([])
        groups[-1].append(word)
    fragments = []
    for fi, group in enumerate(groups):
        if any(a['bbox']['xMax'] > b['bbox']['xMin'] + 1 for a,b in zip(group, group[1:])):
            warnings.append({'code': 'PDF_WORD_OVERLAP_AMBIGUOUS', 'page_number': page,
                             'block_index': block_index, 'line_index': line_index,
                             'message': '字坐标重叠，原文保留，该片段不用于网格候选。'})
            continue
        quote = ' '.join(w['text'] for w in group)
        # Quote is derived exactly as the existing Poppler adapter builds lines.
        if quote not in line['text']:
            _fail('PDF片段逐字引用与原始行不一致。')
        fragments.append({'fragment_id': _id(page, f'b{block_index}:l{line_index}:f', fi),
                          'block_index': block_index, 'line_index': line_index, 'quote': quote,
                          'bbox': _union(group), 'word_ids': [w['word_id'] for w in group],
                          'word_anchors': [copy.deepcopy(w['anchor']) for w in group],
                          'source_anchor': copy.deepcopy(group[0]['block_anchor']),
                          'claim_status': 'geometric_fragment_only'})
    return fragments


def _rows(page, fragments):
    rows = []
    for fragment in sorted(fragments, key=lambda x: (_center(x), x['bbox']['xMin'], x['fragment_id'])):
        eligible = []
        for row in rows:
            # All-pairs baseline agreement avoids transitive chaining across rows.
            if all(abs(_center(fragment)-_center(x)) <= min(3, min(_height(fragment), _height(x))*.3)
                   for x in row['fragments']):
                eligible.append(row)
        if len(eligible) == 1:
            eligible[0]['fragments'].append(fragment)
        else:
            rows.append({'fragments': [fragment]})
    rows.sort(key=lambda x: (min(_center(f) for f in x['fragments']), min(f['bbox']['xMin'] for f in x['fragments'])))
    result = []
    for ri, row in enumerate(rows):
        cells = sorted(row['fragments'], key=lambda x: (x['bbox']['xMin'], x['fragment_id']))
        overlap = any(a['bbox']['xMax'] > b['bbox']['xMin'] + 1 for a,b in zip(cells,cells[1:]))
        result.append({'candidate_id': _id(page, 'row', ri), 'kind': 'geometric_row',
                       'page_number': page, 'bbox': _union(cells), 'cells': cells,
                       'claim_status': 'candidate_not_semantic_truth',
                       'ambiguity': ['horizontal_overlap'] if overlap else [],
                       'association_basis': 'same_geometric_baseline_no_text_concatenation'})
    return result


def _grids(page, rows):
    candidates = []; current = []
    def flush():
        if len(current) >= 3:
            candidates.append({'candidate_id': _id(page, 'grid', len(candidates)),
                'kind': 'aligned_grid_candidate', 'page_number': page, 'row_ids': [r['candidate_id'] for r in current],
                'row_count': len(current), 'column_count': len(current[0]['cells']),
                'bbox': _union(current), 'rows': copy.deepcopy(current),
                'claim_status': 'candidate_not_semantic_truth', 'table_semantics': 'unconfirmed',
                'interpretation_options': ['table', 'parallel_columns'],
                'rule_line_evidence': 'not_parsed', 'header_status': 'not_inferred',
                'missing_cells': 'not_created', 'cross_page_merge': 'not_executed'})
        current.clear()
    for row in rows:
        cells = row['cells']
        if row['ambiguity'] or not 2 <= len(cells) <= 12:
            flush(); continue
        compatible = bool(current) and len(cells) == len(current[0]['cells']) and all(
            abs(cell['bbox']['xMin'] - base['bbox']['xMin']) <= 4
            for cell,base in zip(cells,current[0]['cells']))
        if compatible:
            gap = row['bbox']['yMin'] - current[-1]['bbox']['yMax']
            compatible = gap >= -1 and gap <= 3*max(_height(row), _height(current[-1]))
        if current and not compatible:
            flush()
        current.append(row)
    flush()
    return candidates


def _columns(page, fragments):
    clusters = []
    for fragment in sorted(fragments, key=lambda x: x['bbox']['xMin']):
        found = [c for c in clusters if abs(c[0]['bbox']['xMin']-fragment['bbox']['xMin']) <= 4]
        if len(found) == 1:
            found[0].append(fragment)
        else:
            clusters.append([fragment])
    result=[]
    for cluster in (c for c in clusters if len(c)>=3):
        width=statistics.median(f['bbox']['xMax']-f['bbox']['xMin'] for f in cluster)
        # A wide heading sharing the left margin must not swallow both columns.
        members=[f for f in cluster if f['bbox']['xMax']-f['bbox']['xMin']<=max(width*1.6,width+12)]
        if len(members)<3:continue
        result.append({'candidate_id':_id(page,'column',len(result)), 'kind':'aligned_text_column_candidate',
            'bbox':_union(members),'fragment_ids':[f['fragment_id'] for f in members],
            'excluded_wide_fragment_ids':[f['fragment_id'] for f in cluster if f not in members],
            'claim_status':'candidate_not_semantic_truth','basis':'repeated_left_margin_with_width_outliers_unassigned'})
    return result


def enhance_pdf(document, segments):
    """Return copies with candidates/context; original text, anchors and geometry stay intact."""
    if not isinstance(document, dict) or document.get('format') != 'pdf' or not isinstance(document.get('pages'), list) or not document['pages']:
        _fail('PDF证据上下文需要已有PDF页和Poppler几何。')
    if not isinstance(segments, list):
        _fail('PDF来源片段结构无效。')
    if len(document['pages']) > MAX_PAGES:
        raise TaskError('PDF_EVIDENCE_LIMIT','PDF候选页数超过有界处理限制，未丢页。','PdfEvidence',['IN-004','IN-016','SEC-004'],[{'pages':len(document['pages']),'maximum':MAX_PAGES}])
    total_words = 0
    for pi,page in enumerate(document['pages']):
        blocks=page.get('blocks') if isinstance(page,dict) else None
        if not isinstance(blocks,list):_fail('PDF页块结构无效。')
        count=0
        for block in blocks:
            lines=block.get('lines') if isinstance(block,dict) else None
            if not isinstance(lines,list):_fail('PDF文本块缺少原始行。')
            for line in lines:
                words=line.get('words') if isinstance(line,dict) else None
                if not isinstance(words,list):_fail('PDF行缺少原始字。')
                count += len(words)
        total_words += count
        if count > MAX_WORDS_PER_PAGE or total_words > MAX_WORDS:
            raise TaskError('PDF_EVIDENCE_LIMIT','PDF字数超过候选处理限制，未裁剪原文。','PdfEvidence',['IN-004','IN-016','SEC-004'],[{'page_index':pi,'page_words':count,'total_words':total_words,'page_maximum':MAX_WORDS_PER_PAGE,'total_maximum':MAX_WORDS}])
    doc, result = copy.deepcopy(document), copy.deepcopy(segments)
    warnings = []; segment_map = {}; page_contexts = []
    for index, segment in enumerate(result):
        if (not isinstance(segment, dict) or not isinstance(segment.get('anchor'), dict) or not isinstance(segment.get('data'), dict)
                or not isinstance(segment.get('raw_text'), str) or not isinstance(segment['anchor'].get('native_locator'), str)
                or not segment['anchor']['native_locator'] or not isinstance(segment.get('metadata', {}), dict)):
            _fail('PDF来源片段缺少原始锚点/数据。', [{'segment_index': index}])
        loc = segment['anchor'].get('locator', {})
        if loc.get('kind') != 'pdf_element' or not isinstance(loc.get('page_index'), int):
            _fail('PDF来源片段缺少原生页定位。', [{'segment_index': index}])
        if loc['page_index'] < 0 or loc['page_index'] >= len(doc['pages']) or loc.get('page_number') != loc['page_index']+1:
            _fail('PDF来源片段页码与原页不一致。', [{'segment_index': index}])
        key = (loc['page_index'], loc.get('element_index'))
        if key in segment_map:
            _fail('PDF来源片段页/块锚点重复，未覆盖证据。', [{'segment_index': index}])
        segment_map[key] = segment
    for pi,page in enumerate(doc['pages']):
        number = pi+1
        if page.get('page_number') != number or any(not _number(page.get(k)) or page[k] <= 0 for k in ('width','height')) or not isinstance(page.get('blocks'), list):
            _fail('PDF页码/尺寸/块结构无效。', [{'page_index': pi}])
        words = []; fragments = []; block_words = {}
        for bi,block in enumerate(page['blocks']):
            if not isinstance(block,dict):
                _fail('PDF文本块结构无效。')
            segment = segment_map.get((pi,bi))
            if segment is None or segment['raw_text'] != block.get('text') or any(segment['data'].get(k) != block.get(k) for k in ('kind','text','lines','bbox','coordinate_space')):
                _fail('PDF页块与原片段文本/坐标不一致。', [{'page_number':number,'block_index':bi}])
            _bbox(block.get('bbox'), f'page={number},block={bi}')
            if not isinstance(block.get('lines'),list):
                _fail('PDF文本块缺少原始行。')
            block_words[bi] = []
            for li,line in enumerate(block['lines']):
                if not isinstance(line,dict) or not isinstance(line.get('words'),list) or any(not isinstance(w,dict) or not isinstance(w.get('text'),str) for w in line['words']):
                    _fail('PDF行/字原始结构无效。')
                _bbox(line.get('bbox'),f'page={number},block={bi},line={li}')
                if not isinstance(line.get('words'),list) or line.get('text') != ' '.join(w.get('text','') for w in line['words']):
                    _fail('PDF行原文与逐字文本不一致。')
                line_words=[]
                for wi,word in enumerate(line['words']):
                    if not isinstance(word.get('text'),str):
                        _fail('PDF字证据必须为原字符串。')
                    bounds = _bbox(word.get('bbox'),f'page={number},block={bi},line={li},word={wi}')
                    loc=copy.deepcopy(segment['anchor']['locator']); loc.update(object_kind='word',line_index=li,word_index=wi,bbox=copy.deepcopy(bounds),coordinate_space='pdf_points_top_left')
                    word_anchor=copy.deepcopy(segment['anchor']); word_anchor.update(native_locator=segment['anchor']['native_locator']+f',line={li},word={wi}',locator=loc)
                    item={'word_id':_id(number,f'b{bi}:l{li}:w',wi),'text':word['text'],'bbox':bounds,
                          'block_index':bi,'line_index':li,'word_index':wi,'anchor':word_anchor,
                          'block_anchor':copy.deepcopy(segment['anchor'])}
                    words.append(item); block_words[bi].append(item); line_words.append(item)
                fragments.extend(_fragments(number,bi,li,line,line_words,warnings))
            if block['text'] != '\n'.join(l['text'] for l in block['lines']):
                _fail('PDF块原文与原始行不一致。')
        expected_keys = {(pi,bi) for bi in range(len(page['blocks']))} if page['blocks'] else {(pi,None)}
        if {key for key in segment_map if key[0] == pi} != expected_keys:
            _fail('PDF页/块锚点全集与片段不一致。', [{'page_number':number}])
        rows=_rows(number,fragments); grids=_grids(number,rows); columns=_columns(number,fragments)
        median=statistics.median(_height(w) for w in words) if words else 0
        headings=[{'candidate_id':_id(number,'heading',i),'kind':'heading_candidate','page_number':number,
                   'quote':f['quote'],'bbox':copy.deepcopy(f['bbox']),'word_ids':f['word_ids'],
                   'word_anchors':copy.deepcopy(f['word_anchors']),'source_anchor':copy.deepcopy(f['source_anchor']),
                   'basis':'upper_page_word_bbox_height_above_page_median','claim_status':'candidate_not_semantic_truth'}
                  for i,f in enumerate(f for f in fragments if median > 0 and _height(f)>=median*1.3 and f['bbox']['yMin']<page['height']*.25)]
        duplicates={text:count for text,count in Counter(w['text'] for w in words).items() if count>1}
        reading_ambiguity=any(a['bbox']['xMax']<b['bbox']['xMin'] and max(a['bbox']['yMin'],b['bbox']['yMin'])<min(a['bbox']['yMax'],b['bbox']['yMax'])
                              for a in columns for b in columns if a is not b)
        context={'page_number':number,'coordinate_space':'pdf_points_top_left','word_inventory':words,
                 'row_candidates':rows,'table_candidates':grids,'column_candidates':columns,'heading_candidates':headings,
                 'reading_order_status':'ambiguous_parallel_columns' if reading_ambiguity else 'poppler_order_preserved_not_semantically_verified',
                 'duplicate_text_counts':duplicates,'cross_page_tables':'not_joined','claim_status':'candidate_not_semantic_truth'}
        page['evidence_candidates']=copy.deepcopy(context); page_contexts.append(context)
        if not words:
            warnings.append({'code':'PDF_PAGE_NO_TEXT_EVIDENCE','page_number':number,'message':'本页无可提取字，未声明空白或OCR已完成。'})
        if grids:
            warnings.append({'code':'PDF_GRID_SEMANTICS_UNCONFIRMED','page_number':number,'candidate_ids':[g['candidate_id'] for g in grids],
                             'message':'重复几何对齐保留为网格候选；表格/并列正文、标题、单位、行列语义仍需证据复核，无表线信息。'})
        elif words:
            warnings.append({'code':'PDF_GRID_NOT_FOUND','page_number':number,'message':'本页未满足有界网格条件，不代表不存在表格；未创建空单元格。'})
        if reading_ambiguity:
            warnings.append({'code':'PDF_READING_ORDER_UNRESOLVED','page_number':number,'message':'存在纵向重叠的并列列候选，不串接不同列或声称已解读正文顺序。'})
        if duplicates:
            warnings.append({'code':'PDF_REPEATED_WORDS_PRESERVED','page_number':number,'repeated_text_counts':duplicates,
                             'message':'重复文本/数字保留独立字锚点，没有合并成唯一值。'})
        for key,segment in segment_map.items():
            if key[0] != pi:continue
            bi=key[1]; word_ids={w['word_id'] for w in block_words.get(bi,[])}
            source_context={'source_kind':'pdf','page_number':number,'block_index':bi,
                'source_anchor':copy.deepcopy(segment['anchor']),'word_evidence':copy.deepcopy(block_words.get(bi,[])),
                'row_candidates':[copy.deepcopy(r) for r in rows if any(word_ids.intersection(c['word_ids']) for c in r['cells'])],
                'table_candidates':[copy.deepcopy(g) for g in grids if any(word_ids.intersection(c['word_ids']) for r in g['rows'] for c in r['cells'])],
                'heading_candidates':[copy.deepcopy(h) for h in headings if word_ids.intersection(h['word_ids'])],
                'reading_order_status':context['reading_order_status'],'claim_status':'candidate_not_semantic_truth',
                'boundary':copy.deepcopy(POLICY)}
            segment.setdefault('metadata',{})['source_context']=source_context
            segment['data']['evidence_candidates']={'row_ids':[r['candidate_id'] for r in source_context['row_candidates']],
                'table_ids':[g['candidate_id'] for g in source_context['table_candidates']],
                'heading_ids':[h['candidate_id'] for h in source_context['heading_candidates']]}
    inventory=_image_inventory(doc.get('image_inventory_raw'),len(doc['pages']),warnings)
    # Bind only original source identity, never guessed page geometry or assets.
    for image in inventory['images']:
        original=next((s['anchor'] for key,s in segment_map.items() if key[0] == image['page_number']-1),None)
        if original:
            image['anchor'].update(source_id=original.get('source_id'),asset_id=original.get('asset_id'))
    doc['image_inventory']=inventory
    doc['evidence_analysis']={'version':VERSION,'claim_status':'candidate_not_semantic_truth',
        'policy':copy.deepcopy(POLICY),'word_count':sum(len(p['word_inventory']) for p in page_contexts),
        'table_candidate_count':sum(len(p['table_candidates']) for p in page_contexts),
        'image_inventory_status':inventory['status'],'boundary':'Geometry is context for evidence review, not semantic extraction or AC acceptance.'}
    doc['evidence_analysis']['preserved_evidence_sha256']=hashlib.sha256(json.dumps(
        [{'raw_text':s['raw_text'],'anchor':s['anchor']} for s in segments],ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    return doc,result,warnings
