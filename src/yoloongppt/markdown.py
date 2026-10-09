"""IN-002 structured Markdown, preserving original Unicode text and block ranges."""
import re
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin

from .errors import TaskError


class MarkdownParser:
    def __init__(self, raw):
        self.raw = raw
        self.lines = raw.splitlines(keepends=True)
        self.offsets = [0]
        for line in self.lines:
            self.offsets.append(self.offsets[-1] + len(line))
        self.env = {}
        # Baseline treats an unindented footnote definition as separate even after
        # a lazy blockquote paragraph. Insert a parser-only blank and map it back.
        parser_lines = []; self.line_map = []; self.definitions = []; fence = None
        for n, line in enumerate(self.lines):
            marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
            if marker:
                if fence is None:fence = marker.group(1)
                elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):fence = None
            definition = re.match(r'^ {0,3}\[\^([^\]]+)\]:(.*)', line) if fence is None else None
            if definition:self.definitions.append((n, definition.group(1), definition.group(2)))
            if definition and n and self.lines[n-1].strip():
                parser_lines.append('\n'); self.line_map.append(n)
            parser_lines.append(line); self.line_map.append(n)
        self.line_map.append(len(self.lines))
        parser = MarkdownIt('commonmark', {'html': False, 'maxNesting': 128})
        parser.enable('table').use(footnote_plugin)
        parser_raw = ''.join(parser_lines)
        self.tokens = parser.parse(parser_raw[1:] if parser_raw.startswith('\ufeff') else parser_raw, self.env)
        if len({label for _, label, _ in self.definitions}) != len(self.definitions):
            raise TaskError('MARKDOWN_FOOTNOTE_DUPLICATE', '脚注标签重复；没有静默选择或覆盖。', 'SourceLoader', ['IN-002'])
        if any(token.level >= 126 for token in self.tokens):
            raise TaskError('MARKDOWN_NESTING_LIMIT', 'Markdown嵌套达到解析限制，停止而不扁平化。', 'SourceLoader', ['IN-002'])
        for token in self.tokens:
            if token.map:token.map = [self.line_map[token.map[0]], self.line_map[token.map[1]]]
        self.index = 0
        self.block_index = 0

    def location(self, mapping):
        start, end = mapping or [0, len(self.lines)]
        begin = self.offsets[min(start, len(self.offsets)-1)]
        finish = self.offsets[min(end, len(self.offsets)-1)]
        return {'source_ref': 'raw_markdown', 'start_offset': begin, 'end_offset': finish,
                'offset_unit': 'unicode_code_point', 'line_start': start+1, 'line_end': max(start+1, end)}

    def inline(self, tokens, loc):
        root = []; stack = [root]
        for token in tokens or []:
            kind = token.type
            if kind in {'em_open', 'strong_open', 'link_open'}:
                if kind == 'link_open':
                    node = {'kind': 'link', 'label': [], 'destination': token.attrGet('href') or '',
                            'title': token.attrGet('title'), 'source_location': loc}
                    children = node['label']
                else:
                    node = {'kind': 'emphasis' if kind == 'em_open' else 'strong', 'children': [], 'source_location': loc}
                    children = node['children']
                stack[-1].append(node); stack.append(children)
            elif kind in {'em_close', 'strong_close', 'link_close'}:
                stack.pop()
            elif kind == 'text':
                stack[-1].append({'kind': 'text', 'text': token.content, 'source_location': loc})
            elif kind == 'code_inline':
                stack[-1].append({'kind': 'inline_code', 'literal': token.content, 'source_location': loc})
            elif kind in {'softbreak', 'hardbreak'}:
                stack[-1].append({'kind': 'line_break', 'break_kind': 'soft' if kind == 'softbreak' else 'hard', 'source_location': loc})
            elif kind == 'image':
                stack[-1].append({'kind': 'image', 'alt_text': token.content, 'destination': token.attrGet('src') or '',
                                  'title': token.attrGet('title'), 'source_location': loc})
            elif kind == 'footnote_ref':
                if 'label' not in token.meta:
                    raise TaskError('MARKDOWN_INLINE_FOOTNOTE_UNSUPPORTED', '匿名行内脚注尚未映射，原文保留。', 'SourceLoader', ['IN-002'])
                stack[-1].append({'kind': 'citation', 'raw_marker': '[^'+str(token.meta['label'])+']', 'source_location': loc})
            elif kind == 'footnote_anchor':
                # Generated return links are renderer metadata, not source text.
                continue
            else:
                raise TaskError('MARKDOWN_TOKEN_UNSUPPORTED', '该Markdown节点未映射；原文保留，未生成扁平化替代。',
                                'SourceLoader', ['IN-002', 'SYS-003'], [{'token_type': kind}])
        return root

    def blocks(self, stop=None):
        result = []
        while self.index < len(self.tokens):
            token = self.tokens[self.index]; self.index += 1
            if token.type == stop:
                return result
            loc = self.location(token.map)
            base = {'block_index': self.block_index, 'source_location': loc}; self.block_index += 1
            if token.type in {'heading_open', 'paragraph_open'}:
                inline = self.tokens[self.index]; self.index += 1
                while self.tokens[self.index].type == 'footnote_anchor':self.index += 1
                self.index += 1
                node = {'kind': 'heading' if token.type == 'heading_open' else 'paragraph',
                        **base, 'content': self.inline(inline.children, loc)}
                if token.type == 'heading_open':node['level'] = int(token.tag[1:])
            elif token.type in {'fence', 'code_block'}:
                node = {'kind': 'code_block', **base, 'fence_char': None, 'fence_length': None,
                        'language': token.info.strip() or None, 'literal': token.content}
                if token.type == 'fence':
                    node.update(fence_char='backtick' if token.markup[0] == '`' else 'tilde', fence_length=len(token.markup))
            elif token.type == 'blockquote_open':
                node = {'kind': 'blockquote', **base, 'blocks': self.blocks('blockquote_close')}
            elif token.type in {'bullet_list_open', 'ordered_list_open'}:
                ordered = token.type == 'ordered_list_open'; items = []
                start = int(token.attrGet('start') or 1) if ordered else None
                while self.tokens[self.index].type == 'list_item_open':
                    item = self.tokens[self.index]; self.index += 1
                    item_loc = self.location(item.map)
                    original_line = self.lines[item.map[0]] if item.map else ''
                    marker = re.search(r'(?:^|\s)([-+*]|\d+[.)])\s', original_line)
                    items.append({'marker': marker.group(1) if marker else item.markup,
                                  'ordinal': start+len(items) if ordered else None,
                                  'blocks': self.blocks('list_item_close'), 'source_location': item_loc})
                self.index += 1
                node = {'kind': 'list', **base, 'list_kind': 'ordered' if ordered else 'unordered', 'start_number': start, 'items': items}
            elif token.type == 'table_open':
                rows = []; alignments = []; header = []
                row_loc = loc; cells = []
                while self.tokens[self.index].type != 'table_close':
                    part = self.tokens[self.index]; self.index += 1
                    if part.type == 'tr_open':cells = []; row_loc = self.location(part.map)
                    elif part.type in {'th_open', 'td_open'}:
                        inline = self.tokens[self.index]; self.index += 2
                        cells.append({'content': self.inline(inline.children, row_loc), 'source_location': row_loc})
                        if part.type == 'th_open':alignments.append((part.attrGet('style') or 'default').split(':')[-1])
                    elif part.type == 'tr_close':
                        if not header:header = cells
                        else:
                            source_line = self.lines[row_loc['line_start']-1].strip()
                            pieces = ['']; slash_count = 0
                            for char in source_line:
                                if char == '|' and slash_count % 2 == 0:pieces.append('')
                                else:pieces[-1] += char
                                slash_count = slash_count+1 if char == '\\' else 0
                            if source_line.startswith('|'):pieces = pieces[1:]
                            if source_line.endswith('|') and not source_line.endswith('\\|'):pieces = pieces[:-1]
                            if len(pieces) != len(header):
                                raise TaskError('MARKDOWN_TABLE_WIDTH_MISMATCH', '表格行宽不一致，禁止补空或丢弃额外单元格。',
                                                'SourceLoader', ['IN-002'], [{'line': row_loc['line_start'], 'expected_columns': len(header), 'actual_columns': len(pieces)}])
                            rows.append(cells)
                self.index += 1
                node = {'kind': 'table', **base, 'header': header, 'alignments': alignments, 'rows': rows}
            elif token.type == 'footnote_open':
                label = str(token.meta['label']); children = self.blocks('footnote_close')
                content = []
                for child in children:
                    if child['kind'] != 'paragraph':
                        raise TaskError('MARKDOWN_FOOTNOTE_STRUCTURE_UNSUPPORTED', '复杂脚注结构未支持，原文保留。', 'SourceLoader', ['IN-002'])
                    content.extend(child['content'])
                match = re.search(r'^ {0,3}\[\^'+re.escape(label)+r'\]:', self.raw, re.M)
                if match:
                    line = self.raw[:match.start()].count('\n')
                    end_line = max([line+1]+[child['source_location']['line_end'] for child in children])
                    loc = self.location([line, end_line])
                node = {'kind': 'footnote_definition', **base, 'source_location': loc, 'label': label, 'content': content}
            elif token.type in {'footnote_block_open', 'footnote_block_close', 'footnote_anchor'}:
                self.block_index -= 1
                continue
            else:
                raise TaskError('MARKDOWN_BLOCK_UNSUPPORTED', '该Markdown结构未映射，停止解析并保留原文。',
                                'SourceLoader', ['IN-002', 'SYS-003'], [{'token_type': token.type}])
            result.append(node)
        return result

    def parse(self):
        source = {'kind': 'raw_text', 'source_ref': 'raw_markdown'}
        blocks = sorted(self.blocks(), key=lambda b: b['source_location']['start_offset'])
        labels = {block['label'] for block in blocks if block['kind'] == 'footnote_definition'}
        for line, label, content in self.definitions:
            if label in labels:continue
            if line+1 < len(self.lines) and self.lines[line+1].startswith(('    ', '\t')):
                raise TaskError('MARKDOWN_FOOTNOTE_STRUCTURE_UNSUPPORTED', '未引用的多行脚注尚未映射，原文保留。', 'SourceLoader', ['IN-002'])
            loc = self.location([line, line+1])
            children = MarkdownIt('commonmark', {'html': False}).parseInline(content)[0].children
            blocks.append({'kind': 'footnote_definition', 'block_index': self.block_index, 'label': label,
                           'content': self.inline(children, loc), 'source_location': loc})
            self.block_index += 1
        blocks.sort(key=lambda b: b['source_location']['start_offset'])
        return {'record_type': 'markdown_parse_result', 'raw_markdown': self.raw, 'source': source,
                'raw_asset_refs': [], 'status': 'parsed', 'document': {'model_type': 'TextDocumentModel', 'source': source,
                'blocks': blocks}, 'errors': []}


def parse_plain_text(raw):
    # Plain text uses the same document contract without interpreting Markdown.
    source = {'kind': 'raw_text', 'source_ref': 'raw_markdown'}
    lines = raw.splitlines(keepends=True); blocks = []; offset = 0; start = None; start_line = 1
    for n, line in enumerate(lines + ['']):
        if line.strip() and start is None:start = offset; start_line = n+1
        if not line.strip() and start is not None:
            loc = {'source_ref': 'raw_markdown', 'start_offset': start, 'end_offset': offset,
                   'offset_unit': 'unicode_code_point', 'line_start': start_line, 'line_end': max(start_line, n)}
            blocks.append({'kind': 'paragraph', 'block_index': len(blocks), 'source_location': loc,
                           'content': [{'kind': 'text', 'text': raw[start:offset], 'source_location': loc}]})
            start = None
        offset += len(line)
    return {'record_type': 'markdown_parse_result', 'raw_markdown': raw, 'source': source, 'raw_asset_refs': [],
            'status': 'parsed', 'document': {'model_type': 'TextDocumentModel', 'source': source, 'blocks': blocks}, 'errors': []}
