"""Flag papers by whether their abstract suggests the method needs model internals / training, or is black-box & training-free.

usage: python -X utf8 -I blackbox_filter.py <papers.json> <out.json>
papers.json: list of {id/title/venue/abstract...}  (ACL Anthology rows or fetched venue rows)
Heuristic only: used to prioritise manual reading, not as a verdict.
"""
import json, re, sys

rows = json.load(open(sys.argv[1], encoding='utf-8'))
if isinstance(rows, dict):
    rows = rows.get('papers') or rows.get('candidates')

NEED_INTERNALS = re.compile(
    r'log-?probabilit|logprob|logit|token[- ](?:level )?(?:probabilit|entropy|likelihood)|token entropy|perplexity|hidden[- ]state|'
    r'hidden layer|activation|attention (?:head|map|weight)|steering|residual stream|representation (?:space|engineering)|'
    r'internal (?:state|representation|signal)|white-box|gradient|weights? (?:perturb|space)|model weights|latent (?:space|reasoning|memory)', re.I)
NEED_TRAINING = re.compile(
    r'fine-?tun|reinforcement learning|\bRL\b|GRPO|\bPPO\b|\bDPO\b|\bSFT\b|reward model|preference optimi[sz]ation|policy optimi[sz]ation|'
    r'we train|trained (?:on|with|to)|post-training|distill|LoRA|pre-?train(?:ing)? (?:a|an|our)', re.I)
BLACKBOX = re.compile(
    r'black-?box|training-?free|without (?:any )?(?:additional |extra )?(?:training|fine-?tuning)|no (?:additional )?training|'
    r'closed-source|proprietary|API[- ](?:based|only|access)|prompt-?only|prompting[- ]only|plug-and-play|inference-time|test-time|'
    r'zero-shot|model-agnostic|parameter-free|verbalized', re.I)
TOPIC = re.compile(
    r'debate|multi-?agent|multiple (?:LLM|agent|model)|multi-?LLM|ensemble|aggregat|consensus|voting|majority|deliberat|council|jury|'
    r'self-consistency|disagree|conformity|sycophan|routing|uncertain|calibrat|conformal|verification|adjudicat|arbitrat|panel|mixture[- ]of[- ]agents', re.I)

out = []
for r in rows:
    s = (r.get('title', '') + ' ' + r.get('abstract', ''))
    if not TOPIC.search(s):
        continue
    flags = {
        'internals': sorted({m.group(0).lower() for m in NEED_INTERNALS.finditer(s)})[:4],
        'training': sorted({m.group(0).lower() for m in NEED_TRAINING.finditer(s)})[:4],
        'blackbox': sorted({m.group(0).lower() for m in BLACKBOX.finditer(s)})[:4],
    }
    r2 = {k: r.get(k) for k in ('id', 'venue', 'volume', 'title', 'url')}
    r2['abstract'] = r.get('abstract', '')
    r2['flags'] = flags
    r2['clean'] = (not flags['internals']) and (not flags['training'])
    out.append(r2)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('topic-matching:', len(out), '| no internals/training flags:', sum(1 for r in out if r['clean']),
      '| clean & explicit black-box/training-free marker:', sum(1 for r in out if r['clean'] and r['flags']['blackbox']))
