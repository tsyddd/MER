"""Omni-only structural repairs. Never synthesize observations, reasons or edges."""
import re
import json

LAYERS = ('process', 'person', 'context')


def recover_truncated_perception(text):
    """Keep only complete, explicitly typed observation objects in a cut-off response."""
    decoder = json.JSONDecoder()
    grouped = {layer: {'nodes': []} for layer in LAYERS}
    seen = set()
    for match in re.finditer(r'\{', text):
        try:
            node, _ = decoder.raw_decode(text, match.start())
        except ValueError:
            continue
        if not isinstance(node, dict):
            continue
        layer = node.get('type', node.get('layer'))
        content = node.get('content')
        if layer not in LAYERS or not isinstance(content, str) or not content.strip() or not node.get('id'):
            continue
        key = (layer, content.strip())
        if key in seen:
            continue
        seen.add(key)
        grouped[layer]['nodes'].append(node)
    if not seen:
        raise ValueError('Truncated perception contains no complete observation nodes')
    return grouped, ['Recovered '+str(len(seen))+' complete typed nodes from length-truncated response; discarded incomplete tail and exact repeated content; no observation text synthesized']


def normalize(stage, obj, payload):
    original = repr(obj)
    notes = []
    if isinstance(obj, dict) and isinstance(obj.get(stage), dict):
        obj = obj[stage]
    if stage == 'perception':
        if not isinstance(obj, dict):
            raise ValueError('Perception is not an object')
        grouped = {layer: [] for layer in LAYERS}
        if isinstance(obj.get('nodes'), list):
            for node in obj['nodes']:
                if isinstance(node, dict) and node.get('type', node.get('layer')) in grouped:
                    grouped[node.get('type', node.get('layer'))].append(node)
        else:
            for layer in LAYERS:
                value = obj.get(layer, {})
                grouped[layer] = value.get('nodes', []) if isinstance(value, dict) else value
        result = {layer: {'nodes': []} for layer in LAYERS}
        seen = set()
        for layer, nodes in grouped.items():
            for index, node in enumerate(nodes if isinstance(nodes, list) else []):
                if not isinstance(node, dict):
                    notes.append('Removed nonobject node'); continue
                content = node.get('content', node.get('description', node.get('text')))
                if not isinstance(content, str) or not content.strip():
                    notes.append('Removed node without observed content'); continue
                ident = str(node.get('id', node.get('node_id', f'{layer}_{index}'))).strip()
                if not ident or ident in seen:
                    notes.append('Removed duplicate/empty node identifier'); continue
                seen.add(ident)
                phase = node.get('time_index', 0)
                try: phase = max(0, int(phase))
                except (ValueError, TypeError):
                    phase = 0; notes.append('Unspecified phase normalized to zero')
                sources = node.get('evidence_sources', [])
                if isinstance(sources, str): sources = [sources]
                sources = [s for s in sources if s in ('visual','audio','subtitle','provided_context')]
                result[layer]['nodes'].append(dict(id=ident, type=layer, content=content.strip(),
                                                   time_index=phase, evidence_sources=sources))
        if not seen:
            raise ValueError('Omni produced no usable evidence nodes')
        obj = result
    elif stage in ('temporal', 'joint'):
        nodes = {n['id']: n for n in payload['nodes']}
        edges = obj.get('edges', obj.get('relations', [])) if isinstance(obj, dict) else obj
        if not isinstance(edges, list):
            raise ValueError('Edges are not a list')
        result, seen = [], set()
        for edge in edges:
            if not isinstance(edge, dict):
                notes.append('Removed nonobject edge'); continue
            a, b = str(edge.get('source', edge.get('from', ''))), str(edge.get('target', edge.get('to', '')))
            reason = edge.get('reason', edge.get('explanation', ''))
            if a not in nodes or b not in nodes or a == b or nodes[a]['type'] != nodes[b]['type'] or not isinstance(reason, str) or not reason.strip():
                notes.append('Removed invalid endpoints/layer or missing edge reason'); continue
            layer = nodes[a]['type']
            clean = dict(source=a, target=b, reason=reason.strip(), relation=layer+'_'+stage)
            if stage == 'temporal':
                relation = edge.get('temporal_relation', edge.get('relation'))
                relation = {'later':'after','same_time':'simultaneous'}.get(relation, relation)
                anchor = edge.get('entity_anchor')
                if relation not in ('after', 'simultaneous') or not isinstance(anchor,str) or not anchor.strip():
                    notes.append('Removed unclear temporal relation/anchor'); continue
                if (relation == 'after' and nodes[a]['time_index'] <= nodes[b]['time_index']) or (relation == 'simultaneous' and nodes[a]['time_index'] != nodes[b]['time_index']):
                    notes.append('Removed temporally inconsistent edge'); continue
                clean.update(temporal_relation=relation, entity_anchor=anchor)
                key = (a,b,relation)
            else:
                allowed = payload.get('candidate_pairs', {}).get(layer, [])
                if not any({p['source'],p['target']} == {a,b} for p in allowed):
                    notes.append('Removed pair outside candidates'); continue
                key = tuple(sorted([a,b]))
            if key in seen or (stage == 'joint' and sum(e['relation']==layer+'_joint' for e in result)>=30):
                notes.append('Removed duplicate/excess edge'); continue
            seen.add(key); result.append(clean)
        obj = {'edges': result}
    elif stage == 'organization':
        if isinstance(obj, str): obj = {'text': obj}
        elif isinstance(obj, dict): obj = {'text': obj.get('text', obj.get('organization_text', obj.get('organization', '')))}
        text = obj.get('text') if isinstance(obj, dict) else None
        if not isinstance(text,str) or len(text.strip()) < 20:
            raise ValueError('Omni organization is empty/too short')
        nodes = payload['graph']['nodes']
        if not any(n['id'] in text or any(n['content'][i:i+5] in text for i in range(max(0,len(n['content'])-4))) for n in nodes):
            raise ValueError('Organization cannot be traced to input node identifiers/content')
    if repr(obj) != original and not notes:
        notes.append('Normalized wrapper/field types; observation text retained')
    return obj, notes
