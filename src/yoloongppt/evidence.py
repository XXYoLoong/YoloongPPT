"""SYS-004: transactional local evidence, immutable source snapshots and stable IDs."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from .errors import TaskError


class EvidenceStore:
    def __init__(self, path=None):
        from .schemas import SchemaRegistry
        self.schemas = SchemaRegistry()
        self.path = Path(path or os.environ.get('YOLOONGPPT_EVIDENCE_DB', '/runtime/evidence.sqlite3'))
        if not self.path.is_absolute():
            raise TaskError('EVIDENCE_STORAGE_INVALID', '证据数据库必须使用已配置的绝对路径。', 'EvidenceStore', ['SYS-004'], status=500)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS evidence (source_id TEXT NOT NULL, source_hash TEXT NOT NULL, parser_version TEXT NOT NULL, segment_index INTEGER NOT NULL, evidence_id TEXT NOT NULL UNIQUE, body TEXT NOT NULL, PRIMARY KEY(source_id, source_hash, parser_version, segment_index))')
            db.execute('CREATE TABLE IF NOT EXISTS snapshots (source_id TEXT NOT NULL, source_hash TEXT NOT NULL, asset_id TEXT, raw BLOB NOT NULL, PRIMARY KEY(source_id, source_hash))')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with db:yield db
        finally:
            db.close()

    def save(self, snapshots, records):
        # Everything is parsed/schema checked before this transaction. An error
        # rolls back the entire operation rather than silently losing one source.
        result = []; assets = {}
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for snapshot in snapshots:
                db.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?,?,?)',
                           (snapshot['source_id'], snapshot['source_hash'], snapshot['asset_id'], snapshot['bytes']))
                assets[snapshot['source_id']] = db.execute('SELECT asset_id FROM snapshots WHERE source_id=? AND source_hash=?',
                                                         (snapshot['source_id'], snapshot['source_hash'])).fetchone()[0]
                if bool(assets[snapshot['source_id']]) != bool(snapshot['asset_id']):
                    raise TaskError('SOURCE_ID_ORIGIN_CHANGED', '同一来源ID不能在内联文本与文件资产间复用。', 'EvidenceStore', ['SYS-004'], status=409)
            for record in records:
                record = {**record, 'anchor': {**record['anchor'], 'asset_id': assets[record['source_id']]},
                          'asset_ref': assets[record['source_id']],
                          'raw_asset_refs': [assets[record['source_id']]] if assets[record['source_id']] else []}
                key = (record['source_id'], record['source_hash'], record['parser_version'], record['segment_index'])
                row = db.execute('SELECT body FROM evidence WHERE source_id=? AND source_hash=? AND parser_version=? AND segment_index=?', key).fetchone()
                if row:
                    saved = json.loads(row[0])
                    if saved['raw_text'] != record['raw_text'] or saved['anchor'] != record['anchor']:
                        raise TaskError('EVIDENCE_REPLAY_MISMATCH', '同版本证据重放不一致，事务已回滚。', 'EvidenceStore', ['SYS-004'], status=409)
                    result.append(saved)
                else:
                    record = {**record, 'evidence_id': 'evidence_' + str(uuid4())}
                    self.schemas.validate('source-evidence.schema.json', record)
                    db.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?)', (*key, record['evidence_id'], json.dumps(record, ensure_ascii=False)))
                    result.append(record)
        return result, assets

    def asset_id(self, source, source_hash, is_file):
        with self.connect() as db:
            row = db.execute('SELECT asset_id FROM snapshots WHERE source_id=? AND source_hash=?', (source, source_hash)).fetchone()
        if row and bool(row[0]) != is_file:
            raise TaskError('SOURCE_ID_ORIGIN_CHANGED', '同一来源ID不能在内联文本与文件资产间复用。', 'EvidenceStore', ['SYS-004'], status=409)
        return row[0] if row else ('asset_' + str(uuid4()) if is_file else None)

    def get(self, evidence_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM evidence WHERE evidence_id=?', (evidence_id,)).fetchone()
        if row is None:
            raise TaskError('EVIDENCE_NOT_FOUND', '未找到该证据ID。', 'EvidenceStore', ['SYS-004'], status=404)
        document = json.loads(row[0])
        # Prototype rows predating the canonical fields have no inferred data or
        # confidence. Preserve their original content/version rather than invent it.
        document.setdefault('content', document['raw_text'])
        document.setdefault('data', None)
        document.setdefault('asset_ref', document['anchor']['asset_id'])
        document.setdefault('confidence', None)
        document.setdefault('metadata', {'semantic_claim_status': 'not_inferred', 'legacy_data_status': 'not_stored'})
        self.schemas.validate('source-evidence.schema.json', document)
        return document
