"""Model access for SkillOpt-V5E (design: docs/v6-skillopt-v5e-design.html).

OptClient extends the project's Client with generate_parts(): the user message is an ordered list of parts
(text / image / audio), so one request can carry several samples, each with its own frames and audio clip, labelled in between.
It shares the v6 cross-process request slots (Gemini 5 / GPT 4 requests in flight) and the key handling of engine.Client.
The optimizer model of a provider defaults to the provider's configured model; GPT can be overridden with the environment
variable SKILLOPT_GPT_OPT_MODEL (user decision: the GPT optimizer is "6.1 SOL"; the exact API name is checked in the smoke test).
"""
from __future__ import annotations
import base64
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as v6c  # noqa: E402  (loads engine, v4 pipeline, request slots)
from common import ROOT, Client, LIMITS, _Slot  # noqa: E402


class OptClient(Client):
    def __init__(self, provider, model=None):
        super().__init__(provider)
        if model:
            self.model = model

    def generate_parts(self, system, parts, max_tokens=4096):
        content = []
        for kind, value in parts:
            if kind == 'text':
                content.append({'type': 'text', 'text': value})
            elif kind == 'image':
                content.append({'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(Path(value).read_bytes()).decode()}})
            elif kind == 'audio':
                if self.provider == 'gpt':
                    raise ValueError('GPT has no audio input')
                content.append({'type': 'input_audio', 'input_audio': {'data': base64.b64encode(Path(value).read_bytes()).decode(), 'format': 'wav'}})
            else:
                raise ValueError(kind)
        body = {'model': self.model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}],
                'max_tokens': max_tokens, 'temperature': 0}
        headers = {'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        started = time.time()
        if self.provider in LIMITS:
            with _Slot(self.provider):
                r = self.session.post(self.url, json=body, headers=headers, timeout=(45, 900))
        else:
            r = self.session.post(self.url, json=body, headers=headers, timeout=(45, 900))
        if not r.ok:
            raise RuntimeError(f'HTTP {r.status_code}: ' + self.clean(r.text)[:1500])
        raw = r.json()
        msg = raw['choices'][0]['message']
        text = msg.get('content') or ''
        if isinstance(text, list):
            text = ''.join(p.get('text', '') for p in text if isinstance(p, dict))
        if not text:
            raise ValueError('API returned no final content; finish_reason=' + str(raw['choices'][0].get('finish_reason')))
        return text, raw, time.time() - started

    def list_models(self):
        """Model ids offered by the endpoint (ids only; no key or other data is returned)."""
        r = self.session.get(self.url.rsplit('/chat/completions', 1)[0] + '/models',
                             headers={'Authorization': 'Bearer ' + self.key} if self.key else {}, timeout=(30, 60))
        r.raise_for_status()
        return sorted(m['id'] for m in r.json().get('data', []) if isinstance(m, dict) and 'id' in m)


def optimizer_client(provider):
    """The client of the reflection / merge / ranking model: Gemini -> the same Gemini; GPT -> SKILLOPT_GPT_OPT_MODEL or the configured model."""
    model = os.environ.get('SKILLOPT_GPT_OPT_MODEL') if provider == 'gpt' else None
    return OptClient(provider, model or None)
