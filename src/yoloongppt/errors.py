"""SYS-001/006/007: safe structured failures shared by CLI and API."""
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def trace_id():
    return 'trace_' + str(uuid4())


@dataclass
class TaskError(Exception):
    code: str
    message: str
    component: str
    requirement_ids: list[str]
    details: list[dict[str, Any]] = field(default_factory=list)
    status: int = 422

    def result(self, trace):
        return {'ok': False, 'trace_id': trace, 'error': {
            'code': self.code, 'message': self.message, 'component': self.component,
            'requirement_ids': self.requirement_ids, 'details': self.details,
            'retryable': False}}


def internal_error():
    return TaskError('INTERNAL_ERROR', '组件执行异常；没有完成本次操作。',
                     'core', ['SYS-001', 'SYS-006', 'SYS-007'], status=500)
