"""Durable SQLite queue; each long operation has its own cancellable process group."""
import json
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4, UUID

from .errors import TaskError

OPERATIONS = {'generate','revise','resume','recheck','inspect','validate'}
TERMINAL = {'succeeded','failed','cancelled','interrupted'}


def now():
    return datetime.now(timezone.utc).isoformat()


class JobManager:
    def __init__(self, root='/runtime/jobs'):
        self.root = Path(root).resolve()
        if not self.root.is_relative_to(Path('/runtime')):
            raise TaskError('JOB_PATH_INVALID','作业必须保存在运行目录。','JobManager',['SYS-020'])
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root/'jobs.sqlite3'
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.lock = threading.RLock()
        self.active = {}
        self.thread = None
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, operation TEXT, state TEXT, trace_id TEXT, request TEXT, result TEXT, created_at TEXT, updated_at TEXT, pid INTEGER)')

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db, timeout=20)
        conn.row_factory = sqlite3.Row
        try:
            with conn: yield conn
        finally: conn.close()

    def event(self, job_id, operation, state, result=None):
        item={'time':now(),'level':'INFO','component':'JobManager','job_id':job_id,
              'event':'state_changed','operation':operation,'state':state,
              'result':result,'duration':None}
        with (self.root/'events.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(item,ensure_ascii=False,allow_nan=False)+'\n')

    def start(self):
        # Interrupted operations need explicit retry; no duplicate provider calls on restart.
        with self.connect() as conn:
            conn.execute("UPDATE jobs SET state='interrupted',pid=NULL,updated_at=? WHERE state IN ('running','cancelling')", (now(),))
        self.thread = threading.Thread(target=self.loop, name='ppt-job-queue', daemon=True)
        self.thread.start()

    def close(self):
        self.stop_event.set(); self.wake.set()
        with self.lock:
            for process in self.active.values():
                self.terminate(process)
        if self.thread:
            self.thread.join(timeout=5)

    @staticmethod
    def terminate(process):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass

    def submit(self, operation, request, trace):
        from .schemas import SchemaRegistry
        SchemaRegistry().validate('job-request.schema.json',{'operation':operation,'request':request})
        if operation not in OPERATIONS or not isinstance(request, dict):
            raise TaskError('JOB_REQUEST_INVALID','作业操作或输入无效。','JobManager',['SYS-020'])
        if operation in {'generate','inspect','validate'}:
            from .tasks import validate_task
            from .schemas import SchemaRegistry
            validate_task(request, SchemaRegistry(), trace)
        elif not isinstance(request.get('run_id'), str):
            raise TaskError('JOB_REQUEST_INVALID','该操作需run_id。','JobManager',['SYS-020'])
        job = str(uuid4()); stamp = now()
        folder = self.root/job; folder.mkdir()
        raw = json.dumps(request, ensure_ascii=False, allow_nan=False)
        (folder/'request.json').write_text(raw, encoding='utf-8')
        with self.connect() as conn:
            conn.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)', (job,operation,'queued',trace,raw,None,stamp,stamp,None))
        self.event(job,operation,'queued')
        self.wake.set()
        return self.status(job, trace)

    def status(self, job_id, trace):
        try:
            if str(UUID(job_id)) != job_id: raise ValueError()
        except (ValueError,TypeError,AttributeError):
            raise TaskError('JOB_ID_INVALID','作业ID必须为UUID。','JobManager',['SYS-020']) from None
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM jobs WHERE job_id=?',(job_id,)).fetchone()
        if not row:
            raise TaskError('JOB_NOT_FOUND','作业不存在。','JobManager',['SYS-020'],status=404)
        return {'ok':True,'trace_id':trace,'job':{k:row[k] for k in ['job_id','operation','state','trace_id','created_at','updated_at']},
                'result':json.loads(row['result']) if row['result'] else None}

    def cancel(self, job_id, trace):
        with self.lock:
            status = self.status(job_id,trace)
            state = status['job']['state']
            if state in TERMINAL: return status
            with self.connect() as conn:
                conn.execute('UPDATE jobs SET state=?,updated_at=? WHERE job_id=?', ('cancelled' if state=='queued' else 'cancelling',now(),job_id))
            if job_id in self.active: self.terminate(self.active[job_id])
            self.event(job_id,status['job']['operation'],'cancel_requested')
            self.wake.set()
        return self.status(job_id,trace)

    def retry(self, job_id, trace):
        prior = self.status(job_id,trace)
        if prior['job']['state'] not in {'failed','cancelled','interrupted'}:
            raise TaskError('JOB_RETRY_INVALID','仅失败、取消或中断作业可显式重试。','JobManager',['SYS-020'])
        with self.connect() as conn:
            row = conn.execute('SELECT operation,request FROM jobs WHERE job_id=?',(job_id,)).fetchone()
        result = self.submit(row['operation'],json.loads(row['request']),trace)
        result['retry_of'] = job_id
        return result

    def loop(self):
        while not self.stop_event.is_set():
            with self.lock:
                with self.connect() as conn:
                    row = conn.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created_at LIMIT 1").fetchone()
                    if row:
                        conn.execute("UPDATE jobs SET state='running',updated_at=? WHERE job_id=?",(now(),row['job_id']))
                if row:
                    folder=self.root/row['job_id']
                    try:
                        with (folder/'worker.log').open('wb') as log:
                            process=subprocess.Popen([sys.executable,'-m','yoloongppt.job_worker',row['operation'],str(folder),row['trace_id']],stdout=log,stderr=log,start_new_session=True)
                    except OSError:
                        result={'ok':False,'trace_id':row['trace_id'],'error':{'code':'JOB_PROCESS_START_FAILED','message':'作业进程不能启动。'}}
                        with self.connect() as conn:
                            conn.execute('UPDATE jobs SET state=?,result=?,updated_at=? WHERE job_id=?',('failed',json.dumps(result,ensure_ascii=False),now(),row['job_id']))
                        self.event(row['job_id'],row['operation'],'failed',{'error_code':'JOB_PROCESS_START_FAILED'})
                        continue
                    self.active[row['job_id']]=process
                    with self.connect() as conn:
                        conn.execute('UPDATE jobs SET pid=? WHERE job_id=?',(process.pid,row['job_id']))
                    self.event(row['job_id'],row['operation'],'running')
            if not row:
                self.wake.wait(0.5);self.wake.clear();continue
            while process.poll() is None and not self.stop_event.wait(0.1): pass
            if self.stop_event.is_set(): self.terminate(process)
            with self.lock:
                current=self.status(row['job_id'],row['trace_id'])['job']['state']
                path=folder/'result.json'
                if current=='cancelling':
                    result={'ok':False,'trace_id':row['trace_id'],'error':{'code':'JOB_CANCELLED','message':'用户已取消；子进程组已终止，已有审计产物保留。'}};state='cancelled'
                elif self.stop_event.is_set():
                    result={'ok':False,'trace_id':row['trace_id'],'error':{'code':'JOB_INTERRUPTED','message':'服务停止，显式重试或使用已有断点恢复。'}};state='interrupted'
                elif path.is_file():
                    result=json.loads(path.read_text('utf-8'));state='succeeded' if result.get('ok') else 'failed'
                else:
                    result={'ok':False,'trace_id':row['trace_id'],'error':{'code':'JOB_PROCESS_FAILED','message':'作业进程未返回结构化结果。'}};state='failed'
                with self.connect() as conn:
                    conn.execute('UPDATE jobs SET state=?,result=?,pid=NULL,updated_at=? WHERE job_id=?',(state,json.dumps(result,ensure_ascii=False),now(),row['job_id']))
                self.active.pop(row['job_id'],None)
                self.event(row['job_id'],row['operation'],state,{'ok':result.get('ok'),'run_id':result.get('run_id'),'error_code':result.get('error',{}).get('code')})
