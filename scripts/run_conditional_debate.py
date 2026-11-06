"""Conditional debate on top of saved v3 expert outputs. Two modes:
  default : TEXT-ONLY (no raw media; runs on any machine, key read from the local cc-switch DB)
  --media : experts/judge also receive the same 8 frames + audio + subtitle as v3 (run on the server with the
            project's own engine.Client and configs; needs data/frames8 and the audio files)

Text-only protocol (the --media mode differs only by providing the raw media again):

Protocol
- Round 0 = the already saved v3 expert outputs (graph / audio_subtitle / image). Nothing is re-run.
- If the three labels agree -> adopt, no model call.
- Otherwise up to R debate rounds: each expert sees the other two experts' label + evidence + counter-evidence
  (and its own previous output), may revise or hold. Experts run in parallel within a round (Du-style).
- Still split after R rounds -> text-only judge call (v3 summary prompt + a no-media note).
- Raw frames/audio are NOT provided (not available locally), so this is a reduced version of the designed protocol.

Gold labels are never sent to the model; they are read only by evaluate() after inference.
The API key is read at runtime from the local cc-switch database (current Codex provider) and is never
printed or written to disk. Results go to a NEW directory; older versions are untouched.

Usage:
  python scripts/run_conditional_debate.py --smoke            # one split sample, 1 round
  python scripts/run_conditional_debate.py                     # all 80 (calls only for split samples)
  python scripts/run_conditional_debate.py --evaluate-only
"""
import argparse
import json
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'versions' / 'v3'))
import emotion_wheel_prompts as P  # noqa: E402

PROVIDER = 'gemini'
MODEL = 'gemini-3.8-flash-high'  # same model name recorded in the saved v3 results
V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3' / PROVIDER
GRAPHS = ROOT / 'data' / 'gemini_graph_three_experts_v1'
OUT = ROOT / 'outputs' / 'gemini_conditional_debate_v4_textonly' / PROVIDER  # replaced in main() for --media
METRICS = ROOT / 'metrics' / 'gemini_conditional_debate_v4_textonly.json'
ROLES = ['graph', 'audio_subtitle', 'image']
RNAME = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家'}
MAX_ROUNDS = 2
VERSION = 'gemini_conditional_debate_v4_textonly'

DEBATE_NOTE_TEXT = '''
【辩论轮（仅在三位专家标签不一致时触发）】
你已在上一轮独立给出判断。现在你会看到另外两位专家的判断、证据与反证。请：
1. 逐条核对对方的证据：哪些你认同，哪些你认为不成立、来源不可信或只是同源重复。本轮没有提供原始图片或音频，你只能依据你上一轮写下的观察、另两位专家写下的观察、字幕，以及（仅图谱专家）图谱与组织文本；不得声称重新看过画面、听过声音，也不得把对方的转述当成你亲眼所见。
2. 如果对方给出了你此前没注意到、可以定位的证据，并且足以改变结论，可以修改答案；否则必须坚持，并说明对方的论证哪里不足。不要因为别人意见不同就让步，也不要为了达成一致而改变。
3. 仍然只选一个 allowed_labels 原始标签，沿用“先给一个开放情绪词，再映射成标签”的方式。
输出的 JSON 在原字段基础上增加两个字段："changed"（true/false，相对上一轮答案是否改变）和 "response_to_others"（对另两位关键论点的回应，各一到两句）。其余字段要求不变。'''

JUDGE_NOTE_TEXT = '''
【本次为文本辩论后的裁判】
本次没有提供原始帧或音轨：请忽略上文中“回看对应帧、实际音轨”的要求，改为核对三位专家证据之间的一致性、具体性和可信度。你收到的是字幕、三位专家第 0 轮的独立判断，以及辩论后的最新判断（含 response_to_others）。专家的开放情绪和答案只是意见，不能按人数投票；同源重复的证据只算一项；不能为迎合任何一方编造事实。
输出仍为 {"reason":"...","answer":"一个本数据集Level1标签","evidence_refs":[]}，evidence_refs 引用你在理由中实际用到的专家证据（如 "image:E1"）。'''


DEBATE_NOTE_MEDIA = '''
【辩论轮（仅在三位专家标签不一致时触发）】
你已在上一轮独立给出判断。现在你会看到另外两位专家的判断、证据与反证；你仍然收到与上一轮相同的原始媒体（8 帧、可用音轨、字幕）。请：
1. 逐条核对对方的证据：对方引用的帧号、时间、字幕或节点，请回到原始媒体亲自核实。能核实的，写明你核实到了什么；核实不了、或与媒体不符的，指出来；同源重复的证据只算一项。没有提供音轨时不得声称听过声音。
2. 如果核实后发现对方的证据成立，并足以改变结论，可以修改答案；否则必须坚持，并说明对方哪里不足。不要因为别人意见不同就让步，也不要为了达成一致而改变；同样不要因为自己上一轮的答案而固执，一切以媒体为准。
3. 仍然只选一个 allowed_labels 原始标签，沿用“先给一个开放情绪词，再映射成标签”的方式。
输出的 JSON 在原字段基础上增加两个字段："changed"（true/false，相对上一轮答案是否改变）和 "response_to_others"（对另两位关键论点的回应，各一到两句，注明你在媒体里核实到了什么）。其余字段要求不变。'''

JUDGE_NOTE_MEDIA = '''
【辩论后的裁判】
你收到原始媒体、字幕、三位专家第 0 轮的独立判断，以及辩论后的最新判断（含 response_to_others）。请独立回看媒体并核对专家证据；专家的开放情绪和答案只是意见，不能按人数投票；同源重复的证据只算一项；不能为迎合任何一方编造事实。
输出仍为 {"reason":"...","answer":"一个本数据集Level1标签","evidence_refs":[]}，evidence_refs 引用你在理由中实际用到的专家证据（如 "image:E1"）。'''


# ------------------------------------------------------------------ credentials / client
def read_credentials():
    """Current Codex provider in the local cc-switch database -> (base_url, api_key). Never printed."""
    db = Path.home() / '.cc-switch' / 'cc-switch.db'
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    row = con.execute("select settings_config from providers where app_type='codex' and is_current=1").fetchone()
    con.close()
    cfg = json.loads(row[0])
    key = (cfg.get('auth') or {}).get('OPENAI_API_KEY')
    m = re.search(r'base_url\s*=\s*"([^"]+)"', cfg.get('config') or '')
    if not key or not m:
        raise SystemExit('cc-switch current Codex provider has no api key / base_url')
    return m.group(1).rstrip('/'), key


class Client:
    def __init__(self):
        self.base, self.key = read_credentials()
        self.url = self.base + '/chat/completions'
        self.session = requests.Session()
        self.session.trust_env = False

    def clean(self, text):
        return str(text).replace(self.key, '[REDACTED]')

    def chat(self, system, payload, max_tokens=2400, frames=None, audio=None):  # media args unused in text-only mode
        body = {'model': MODEL, 'messages': [{'role': 'system', 'content': system},
                                             {'role': 'user', 'content': [{'type': 'text', 'text': json.dumps(payload, ensure_ascii=False)}]}],
                'max_tokens': max_tokens, 'temperature': 0}
        t0 = time.time()
        r = self.session.post(self.url, json=body, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.key}, timeout=(30, 300))
        if not r.ok:
            raise RuntimeError(f'HTTP {r.status_code}: ' + self.clean(r.text)[:400])
        raw = r.json()
        msg = raw['choices'][0]['message']
        text = msg.get('content') or ''
        if isinstance(text, list):
            text = ''.join(p.get('text', '') for p in text if isinstance(p, dict))
        if not text:
            raise ValueError('empty content; finish_reason=' + str(raw['choices'][0].get('finish_reason')))
        return text, raw.get('usage'), time.time() - t0


class EngineClient:
    """Server mode: the project's own engine.Client (its configs/providers.json + configs/private_api.json)."""

    def __init__(self):
        sys.path.insert(0, str(ROOT))
        import engine  # noqa: PLC0415  (Linux only: fcntl, cv2)
        self.engine = engine
        self.c = engine.Client(PROVIDER)
        self.base = self.c.config['base_url']
        self.audio_supported = bool(self.c.config.get('audio_supported'))

    def clean(self, text):
        return self.c.clean(text)

    def media(self, row):
        info = self.engine.prepare_frames(row)
        return info['frames'], (row['audio'] if self.audio_supported else None), info['seconds']

    def chat(self, system, payload, max_tokens=2400, frames=None, audio=None):
        text, raw, secs = self.c.generate(system, payload, frames, audio, max_tokens)
        return text, raw.get('usage'), secs


def parse_json(text):
    t = text.strip()
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t)
    i, j = t.find('{'), t.rfind('}')
    if i < 0 or j < 0:
        raise ValueError('no JSON object in response')
    return json.loads(t[i:j + 1])


def call(client, system, payload, validate, max_tokens=2400, tries=4, frames=None, audio=None):
    err = None
    for k in range(tries):
        try:
            text, usage, secs = client.chat(system, payload, max_tokens, frames, audio)
            obj = parse_json(text)
            validate(obj)
            return obj, usage, secs
        except Exception as exc:  # noqa: BLE001
            err = client.clean(exc)
            time.sleep(min(60, 5 * (k + 1) * (3 if 'HTTP 429' in err else 1)))
    raise RuntimeError('failed after retries: ' + str(err))


# ------------------------------------------------------------------ data
def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


def jsave(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf8')


def manifest():
    rows = {}
    for line in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r['id']] = r
    return rows


def compact(e):
    keep = ('expert', 'answer', 'open_emotion', 'mapping_reason', 'reason', 'evidence', 'counterevidence')
    return {k: e.get(k) for k in keep if k in e}


def validator(classes):
    def v(o):
        assert isinstance(o, dict) and o.get('answer') in classes, 'answer must be an allowed label'
        assert isinstance(o.get('open_emotion'), str) and o['open_emotion'].strip(), 'open_emotion required'
        assert isinstance(o.get('reason'), str) and o['reason'].strip(), 'reason required'
        assert isinstance(o.get('mapping_reason'), str) and o['mapping_reason'].strip(), 'mapping_reason required'
        assert isinstance(o.get('evidence'), list) and o['evidence'], 'evidence required'
    return v


def judge_validator(classes):
    def v(o):
        assert isinstance(o, dict) and o.get('answer') in classes and isinstance(o.get('reason'), str) and o['reason'].strip()
    return v


def run_sample(client, row, rounds=MAX_ROUNDS, media=False):
    sid = row['id']
    classes = row['classes']
    folder = OUT / sid
    r0 = {r: jread(V3 / sid / f'expert_{r}.json') for r in ROLES}
    labels0 = [r0[r]['answer'] for r in ROLES]
    base = {'id': sid, 'dataset': row['dataset'], 'round0_labels': dict(zip(ROLES, labels0))}
    if len(set(labels0)) == 1:
        res = dict(base, triggered=False, final=labels0[0], rounds_run=0, round_labels=[], judge=None)
        jsave(folder / 'result.json', res)
        return res
    graph = jread(GRAPHS / sid / 'graph.json')
    organization = (jread(V3 / sid / 'organization.json') or {}).get('text', '')
    frames = audio = None
    media_payload = {}
    if media:
        frames, audio, seconds = client.media(row)
        media_payload = {'frame_times_seconds': seconds, 'audio_provided': bool(audio)}
    state = {r: compact(r0[r]) for r in ROLES}
    history = [dict(round=0, outputs={r: compact(r0[r]) for r in ROLES})]
    round_labels, usage = [], []
    for rd in range(1, rounds + 1):
        if len({state[r]['answer'] for r in ROLES}) == 1:
            break
        new = {}
        for role in ROLES:
            cache = jread(folder / f'round{rd}_{role}.json')
            if cache:
                new[role] = cache['output']
                continue
            others = {RNAME[o]: state[o] for o in ROLES if o != role}
            payload = {'round': rd, 'target_speaker': row.get('speaker') or 'main person', 'subtitle': row.get('subtitle', ''),
                       'allowed_labels': classes, 'your_previous_output': state[role], 'other_experts': others, **media_payload}
            if role == 'graph':
                payload.update(graph=graph, organization=organization)
            system = P.expert(role, classes) + (DEBATE_NOTE_MEDIA if media else DEBATE_NOTE_TEXT)
            out, use, secs = call(client, system, payload, validator(classes), frames=frames, audio=audio)
            jsave(folder / f'round{rd}_{role}.json', dict(output=out, usage=use, seconds=secs))
            new[role] = out
        state = {r: compact(new[r]) | {'changed': new[r].get('changed'), 'response_to_others': new[r].get('response_to_others')} for r in ROLES}
        history.append(dict(round=rd, outputs=state))
        round_labels.append({r: state[r]['answer'] for r in ROLES})
    final_labels = [state[r]['answer'] for r in ROLES]
    judge = None
    if len(set(final_labels)) == 1:
        final = final_labels[0]
    else:
        jc = jread(folder / 'judge.json')
        if jc and jc.get('rounds') == len(history) - 1:  # a judge cached after a different number of rounds is stale
            judge = jc['output']
        else:
            system = P.summary(classes) + (JUDGE_NOTE_MEDIA if media else JUDGE_NOTE_TEXT)
            payload = {'target_speaker': row.get('speaker') or 'main person', 'subtitle': row.get('subtitle', ''), 'allowed_labels': classes,
                       'round0_experts': history[0]['outputs'], 'latest_experts': history[-1]['outputs'], 'debate_rounds_run': len(history) - 1, **media_payload}
            judge, use, secs = call(client, system, payload, judge_validator(classes), 2200, frames=frames, audio=audio)
            jsave(folder / 'judge.json', dict(output=judge, usage=use, seconds=secs, rounds=len(history) - 1))
        final = judge['answer']
    res = dict(base, triggered=True, final=final, rounds_run=len(history) - 1, round_labels=round_labels,
               final_expert_labels=dict(zip(ROLES, final_labels)), judge=judge)
    jsave(folder / 'result.json', res)
    return res


# ------------------------------------------------------------------ evaluation (gold used only here)
def evaluate(rows):
    from collections import Counter
    gold = {i: r['label'] for i, r in rows.items()}
    n = 0
    acc = Counter()
    flips = Counter()
    detail = []
    for sid, g in gold.items():
        base_sum = (jread(V3 / sid / 'summary.json') or {}).get('answer')
        r0 = [(jread(V3 / sid / f'expert_{r}.json') or {}).get('answer') for r in ROLES]
        res = jread(OUT / sid / 'result.json')
        if not res or None in r0 or base_sum is None:
            continue
        n += 1
        top = Counter(r0).most_common()
        vote = top[0][0] if len(top) < 3 else None
        rl = res['round_labels']

        def after(k):  # labels after round k (k>=1), falling back to final state if debate ended earlier
            lab = rl[min(k, len(rl)) - 1] if rl else dict(zip(ROLES, r0))
            c = Counter(lab.values()).most_common()
            return c[0][0] if len(c) < 3 else base_sum
        acc['A 现状：v3 汇总器'] += base_sum == g
        acc['B 三专家多数投票（平票算错）'] += vote == g
        acc['C1 条件辩论 R=1（仍分歧取多数；1-1-1 沿用汇总器）'] += after(1) == g
        acc['C2 条件辩论 R=2（同上）'] += after(2) == g
        acc['D2 条件辩论 R=2 + 文本裁判（仍分歧才调用）'] += res['final'] == g
        if res['triggered']:
            flips['触发辩论的样本'] += 1
            flips['其中 现状汇总器答对'] += base_sum == g
            flips['其中 D2 答对'] += res['final'] == g
            flips['D2 由错变对（相对现状）'] += (base_sum != g and res['final'] == g)
            flips['D2 由对变错（相对现状）'] += (base_sum == g and res['final'] != g)
            flips['专家在辩论中改变过答案（任一专家）'] += any(res['round_labels'][-1].get(r) != dict(zip(ROLES, r0))[r] for r in ROLES) if res['round_labels'] else 0
            flips['辩论后达成一致'] += len(set((res.get('final_expert_labels') or {}).values())) == 1
            flips['辩论后一致且正确'] += (len(set((res.get('final_expert_labels') or {}).values())) == 1 and res['final'] == g)
            flips['辩论后一致但错误'] += (len(set((res.get('final_expert_labels') or {}).values())) == 1 and res['final'] != g)
        detail.append(dict(id=sid, gold=g, round0=dict(zip(ROLES, r0)), v3_summary=base_sum, triggered=res['triggered'],
                           round_labels=res['round_labels'], final=res['final']))
    return n, dict(acc), dict(flips), detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--provider', choices=['gemini', 'gpt'], default='gemini', help='model used for ALL experts and the judge')
    ap.add_argument('--media', action='store_true', help='provide frames+audio again (server mode, uses engine.Client)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--evaluate-only', action='store_true')
    ap.add_argument('--ids', nargs='*')
    args = ap.parse_args()
    global PROVIDER, MODEL, V3, OUT, METRICS, VERSION
    PROVIDER = args.provider
    if PROVIDER != 'gemini' and not args.media:
        sys.exit('text-only mode is wired to the cc-switch Gemini key only; use --media (server) for other providers')
    V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3' / PROVIDER  # round 0 = saved v3 expert outputs of the SAME provider
    VERSION = f'{PROVIDER}_conditional_debate_v4_' + ('media' if args.media else 'textonly')
    OUT = ROOT / 'outputs' / VERSION / PROVIDER
    METRICS = ROOT / 'metrics' / (VERSION + '.json')
    rows = manifest()
    ids = [i for i in rows if (not args.ids or i in args.ids)]
    if not args.evaluate_only:
        split = [i for i in ids if len({(jread(V3 / i / f'expert_{r}.json') or {}).get('answer') for r in ROLES}) > 1]
        todo = split[:1] if args.smoke else ids
        rounds = 1 if args.smoke else MAX_ROUNDS
        client = EngineClient() if args.media else Client()
        if args.media:
            MODEL = client.c.model  # the provider's model name from the project's configs/providers.json
        jsave(OUT / 'input_protocol.json', dict(version=VERSION, model=MODEL, provider=PROVIDER, text_only=not args.media, raw_media_provided=args.media,
              audio_provided=bool(args.media and getattr(client, 'audio_supported', False)),
              round0='saved v3 expert outputs of the same provider, not re-run', max_rounds=MAX_ROUNDS, gold_not_sent=True,
              key_source='project configs/private_api.json via engine.Client' if args.media else 'cc-switch current codex provider (runtime only)'))
        print('endpoint host:', client.base.split('/')[2], '| samples:', len(todo), '| split among all 80:', len(split), flush=True)
        done = 0

        def work(i):
            return run_sample(client, rows[i], rounds, args.media)
        with ThreadPoolExecutor(args.workers) as ex:
            for res in ex.map(work, todo):
                done += 1
                print(f"[{done}/{len(todo)}] {res['id']} triggered={res['triggered']} rounds={res['rounds_run']} final={res['final']}", flush=True)
    n, acc, flips, detail = evaluate(rows)
    out = dict(version=VERSION, n=n, accuracy=acc, debate_stats=flips, per_sample=detail)
    jsave(METRICS, out)
    print(f'n={n}')
    for k, v in acc.items():
        print(f'  {k}: {v}/{n} = {100 * v / n:.1f}%')
    for k, v in flips.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
