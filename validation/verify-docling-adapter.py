"""Actual pinned Docling conversions and source-evidence boundaries, no mocks.

Run inside the app image after local Docling model provisioning:
  PYTHONPATH=/workspace/src python /workspace/validation/verify-docling-adapter.py
All new fixtures/results are written on the /runtime F-backed bind.
"""
from __future__ import annotations
import hashlib
import io
import json
import platform
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from yoloongppt.docling_adapter import DOCLING_VERSION, parse_docling
from yoloongppt.errors import TaskError
from yoloongppt.schemas import SchemaRegistry

ROOT = Path('/workspace')
OUT = Path('/runtime/docling-validation') / ('component-' + uuid4().hex)
OUT.mkdir(parents=True, exist_ok=True)
schemas = SchemaRegistry()
checks = []
failures = []


def check(name, condition, observation=None):
    item = {'id': name, 'passed': bool(condition), 'observed': observation}
    checks.append(item)
    if not condition:
        raise AssertionError(item)


def convert(name, kind, raw):
    sid = 'source_' + str(uuid4()); aid = 'asset_' + str(uuid4())
    result = parse_docling(kind, raw, source_id=sid, asset_id=aid, locator=name)
    json.dumps(result, ensure_ascii=False, allow_nan=False)
    check(name + ':strict-json', True)
    schemas.validate('input-format-result.schema.json', result)
    check(name + ':schema', True)
    check(name + ':hash', result['source_sha256'] == hashlib.sha256(raw).hexdigest())
    check(name + ':version', result['parser_version'].startswith('docling-' + DOCLING_VERSION + ':'))
    check(name + ':identities', all(s['anchor']['source_id'] == sid and s['anchor']['asset_id'] == aid for s in result['segments']))
    check(name + ':complete-docling-json', result['document']['docling']['schema_name'] == 'DoclingDocument')
    check(name + ':local-only', result['document']['docling_conversion']['local_only'] is True)
    check(name + ':not-semantic-truth', all(s['metadata']['semantic_claim_status'] == 'not_inferred' for s in result['segments']))
    (OUT / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def rejects(name, kind, raw, expected):
    try:
        parse_docling(kind, raw, source_id='source_' + str(uuid4()))
    except TaskError as exc:
        item = exc.result('trace_' + str(uuid4()))
        failures.append({'case': name, 'result': item})
        check(name, exc.code in expected, exc.code)
        check(name + ':structured-error', exc.component in {'DoclingAdapter', 'InputFormatParser'})
    else:
        check(name, False, 'unexpected_success')


def main():
    docx_raw = (ROOT / 'validation/stage-closure-artifacts/components/docx/report.docx').read_bytes()
    docx = convert('rich-docx', 'docx', docx_raw)
    check('docx-native-paragraph-anchor', any(s['anchor']['locator']['kind'] == 'docx_block' for s in docx['segments']))
    check('docx-native-image-preservation', any(p['part'].startswith('word/media/') for p in docx['document']['package_parts']))
    check('docx-no-fabricated-page', all(s['anchor']['locator'].get('page_location', {}).get('status') != 'measured' for s in docx['segments']))
    check('docx-docling-table', bool(docx['document']['docling']['tables']))
    check('docx-docling-join-contract', all('docling' in s['metadata'].get('source_context', {}) for s in docx['segments']))

    xlsx_raw = (ROOT / 'validation/source-semantic-artifacts/integration-input/artificial-data.xlsx').read_bytes()
    xlsx = convert('semantic-xlsx', 'xlsx', xlsx_raw)
    check('xlsx-native-cell-anchor', all(s['anchor']['locator']['kind'] == 'tabular_cell' for s in xlsx['segments']))
    check('xlsx-formula-cache', any(s['data'].get('formula') and s['data'].get('cached_value_status') == 'present_unverified_freshness' for s in xlsx['segments']))
    check('xlsx-two-sheets', len(xlsx['document']['sheets']) == 2)
    check('xlsx-docling-tables', bool(xlsx['document']['docling']['tables']))

    pdf_raw = (ROOT / 'validation/stage-closure-artifacts/components/pdf/artificial-source.pdf').read_bytes()
    pdf = convert('text-pdf', 'pdf', pdf_raw)
    check('pdf-four-pages', len(pdf['document']['docling_pages']) == 4)
    check('pdf-page-anchors', all(s['anchor']['locator']['page_number'] >= 1 for s in pdf['segments']))
    check('pdf-bboxes', any(s['data'].get('prov') for s in pdf['segments']))
    check('pdf-structure', bool(pdf['document']['docling']['texts']))

    # Raster-only scan is a real PDF without an embedded text layer.
    image = Image.new('RGB', (1600, 600), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 54)
    draw.text((70, 100), 'Campus Energy Report', font=font, fill='black')
    draw.text((70, 210), 'Building A: 100 kWh', font=font, fill='black')
    draw.text((70, 320), 'Building B: 80 kWh', font=font, fill='black')
    png = io.BytesIO(); image.save(png, format='PNG')
    scan_pdf = io.BytesIO(); image.save(scan_pdf, format='PDF', resolution=150.0)
    (OUT / 'scan.png').write_bytes(png.getvalue())
    (OUT / 'scan.pdf').write_bytes(scan_pdf.getvalue())
    for kind, raw in [('pdf', scan_pdf.getvalue()), ('image', png.getvalue())]:
        result = convert('scan-' + kind, kind, raw)
        cells = [cell for page in result['document']['docling_pages'] for cell in page['ocr_cells']]
        check(kind + ':actual-ocr', bool(cells))
        check(kind + ':real-confidence', all(isinstance(cell['confidence'], (int, float)) and 0 <= cell['confidence'] <= 1 and cell['from_ocr'] for cell in cells))
        check(kind + ':ocr-numeric-content', any('100' in cell['text'] for cell in cells), [c['text'] for c in cells])
        check(kind + ':ocr-page', all(page['page_number'] == 1 for page in result['document']['docling_pages']))
        if kind == 'pdf':
            ocr = result['document']['ocr_evidence']
            schemas.validate('ocr-evidence.schema.json', ocr)
            check('scan-pdf:original-ocr-schema', True)
            check('scan-pdf:actual-processor', ocr['processor']['execution_status'] == 'executed')
            check('scan-pdf:weight-license', ocr['processor']['license_status'] == 'known', ocr['processor'])
            check('scan-pdf:source-asset', ocr['source_asset_id'] == result['segments'][0]['anchor']['asset_id'])
            check('scan-pdf:text-layer-absent', ocr['evidence']['pages'][0]['text_layer_status'] == 'absent')
            check('scan-pdf:measured-frame', ocr['evidence']['pages'][0]['coordinate_frame']['width'] > 0)
            check('scan-pdf:weight-hashes', all(len(f['sha256']) == 64 for f in result['document']['ocr_model_identity']['files']))

    requests = []
    class Trap(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path); self.send_response(404); self.end_headers()
        def log_message(self, *args):
            pass
    server = HTTPServer(('127.0.0.1', 0), Trap)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        html = f'<html><body><h1>Local evidence</h1><p>Energy 100 kWh.</p><img src="http://127.0.0.1:{server.server_port}/forbidden.png"><img src="file:///etc/passwd"></body></html>'.encode()
        result = convert('external-html', 'html', html)
        check('html-no-resource-request', not requests, requests)
        check('html-text', any('100 kWh' in s['raw_text'] for s in result['segments']))
        check('html-unfetched-explicit', any(w['code'] == 'HTML_EXTERNAL_RESOURCES_NOT_FETCHED' for w in result['warnings']))
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)

    rejects('empty-input', 'pdf', b'', {'INPUT_SIZE_LIMIT'})
    rejects('disguised-pdf', 'pdf', b'<html>bad</html>', {'INPUT_FORMAT_DISGUISED'})
    rejects('corrupt-pdf', 'pdf', b'%PDF-1.7\ncorrupt\n%%EOF', {'DOCLING_CONVERSION_FAILED'})
    rejects('corrupt-docx', 'docx', b'not a zip', {'INPUT_ARCHIVE_CORRUPT'})
    rejects('unsupported-format', 'exe', b'fake', {'DOCLING_FORMAT_UNSUPPORTED'})
    blank = Image.new('RGB', (800, 800), 'white'); buffer = io.BytesIO(); blank.save(buffer, format='PDF')
    rejects('blank-scan-no-evidence', 'pdf', buffer.getvalue(), {'INPUT_NO_PARSED_EVIDENCE'})


if __name__ == '__main__':
    error = None
    try:
        main()
    except Exception as exc:
        error = {'exception_type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        report = {'docling_version': DOCLING_VERSION, 'python': platform.python_version(),
                  'requirement_ids': ['IN-003', 'IN-004', 'IN-005', 'IN-008', 'IN-016', 'SYS-003'],
                  'checks': checks, 'failures': failures, 'error': error,
                  'passed': error is None, 'evidence_path': str(OUT),
                  'boundary': 'Real Docling component checks; does not establish semantic truth or full system AC.'}
        (OUT / 'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'output': str(OUT)}, ensure_ascii=False))
