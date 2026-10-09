"""Authorized DeepSeek calls. Credentials never enter request artifacts or errors."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .errors import TaskError
from .jsonio import load_json


class DeepSeek:
    def __init__(self, config):
        if config.get('provider') != 'deepseek' or config.get('base_url', 'https://api.deepseek.com').rstrip('/') != 'https://api.deepseek.com':
            raise TaskError('PROVIDER_UNSUPPORTED', '当前适配器只支持DeepSeek官方HTTPS入口。', 'ModelProvider', ['SYS-005'])
        self.model = config['model']
        self.key = os.environ.get(config.get('api_key_env', 'DEEPSEEK_API_KEY'), '')
        if not self.key and config.get('api_key_env', 'DEEPSEEK_API_KEY') == 'DEEPSEEK_API_KEY':
            path = Path('/runtime/secrets/deepseek_api_key')
            self.key = path.read_text(encoding='utf-8').strip() if path.is_file() else ''
        if not self.key:
            raise TaskError('PROVIDER_CREDENTIAL_MISSING', '容器未获得授权的模型凭据。', 'ModelProvider', ['SYS-005'], status=503)
        parameters = config.get('parameters', {})
        if set(parameters) - {'temperature', 'max_tokens', 'timeout_seconds'}:
            raise TaskError('PROVIDER_PARAMETER_UNSUPPORTED', '当前供应商参数仅支持temperature/max_tokens/timeout_seconds。', 'ModelProvider', ['SYS-005'])
        self.parameters = {'temperature': 0.2, 'max_tokens': 12000, 'timeout_seconds': 180, **parameters}
        if (not isinstance(self.parameters['max_tokens'], int) or not 512 <= self.parameters['max_tokens'] <= 32000
                or not isinstance(self.parameters['timeout_seconds'], (int, float)) or not 5 <= self.parameters['timeout_seconds'] <= 300
                or not isinstance(self.parameters['temperature'], (int, float)) or not 0 <= self.parameters['temperature'] <= 2):
            raise TaskError('PROVIDER_PARAMETER_INVALID', '供应商参数超出已验证范围。', 'ModelProvider', ['SYS-005'])

    def request(self, path, payload=None):
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        request = urllib.request.Request('https://api.deepseek.com/' + path, data=raw,
                                         headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        # Do not follow redirects with credentials, even if the provider changes.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=self.parameters['timeout_seconds']) as response:
                body = response.read(8 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as error:
            raise TaskError('PROVIDER_HTTP_ERROR', '供应商请求失败，未回显正文或凭据。', 'ModelProvider', ['SYS-005'],
                            [{'status': error.code}], status=502) from None
        except (OSError, urllib.error.URLError):
            raise TaskError('PROVIDER_CONNECTION_FAILED', '供应商连接失败或超时；没有自动重试/替换模型。', 'ModelProvider', ['SYS-005'], status=502) from None
        if len(body) > 8 * 1024 * 1024:
            raise TaskError('PROVIDER_RESPONSE_LIMIT', '供应商响应超限；没有截断解析。', 'ModelProvider', ['SYS-005'], status=502)
        return load_json(body, 'ModelProvider')

    def complete(self, messages):
        models = [m['id'] for m in self.request('models')['data']]
        if self.model not in models:
            raise TaskError('PROVIDER_MODEL_UNAVAILABLE', '配置模型不在供应商实际列表，未替换为其他模型。', 'ModelProvider', ['SYS-005'], status=503)
        payload = {'model': self.model, 'messages': messages, 'response_format': {'type': 'json_object'},
                   'thinking': {'type': 'disabled'}, 'temperature': self.parameters['temperature'],
                   'max_tokens': self.parameters['max_tokens'], 'stream': False}
        start = time.monotonic()
        response = self.request('chat/completions', payload)
        try:
            choice = response['choices'][0]
            if choice['finish_reason'] != 'stop':
                raise TaskError('MODEL_OUTPUT_INCOMPLETE', '模型输出未正常结束；禁止使用截断内容。', 'ModelProvider', ['SYS-005'], status=502)
            content = choice['message']['content']
            if not isinstance(content, str) or not content.strip():
                raise TaskError('MODEL_OUTPUT_EMPTY', '模型返回空内容；未使用合成响应替代。', 'ModelProvider', ['SYS-005'], status=502)
        except (KeyError, IndexError, TypeError):
            raise TaskError('MODEL_RESPONSE_INVALID', '供应商响应形状异常。', 'ModelProvider', ['SYS-005'], status=502) from None
        result = load_json(content.encode('utf-8'), 'ModelProvider')
        metadata = {'provider': 'deepseek', 'requested_model': self.model, 'returned_model': response.get('model'),
                    'response_id': response.get('id'), 'usage': response.get('usage'),
                    'available_models': models, 'parameters': {k: v for k, v in payload.items() if k != 'messages'},
                    'request_sha256': hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest(),
                    'response_content_sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
                    'duration_seconds': round(time.monotonic() - start, 3), 'real_model_call': True}
        return result, metadata
