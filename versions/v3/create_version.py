"""Freeze independent v3 code and assets; refuse to overwrite different files."""
import ast
import hashlib
import html
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def write_once(name,text):
    path=HERE/name
    if path.exists():
        assert path.read_text(encoding='utf-8')==text, 'Refuse overwriting existing v3 file: '+name
    else:path.write_text(text,encoding='utf-8')


old_prompts=(ROOT/'shared_media_expert_prompts_v2.py').read_text()
tree=ast.parse((ROOT/'frozen_graph_expert_prompts.py').read_text())
organization=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ORGANIZATION' for t in n.targets))
old_prompts=old_prompts.replace('from frozen_graph_expert_prompts import ORGANIZATION','ORGANIZATION = '+repr(organization))
write_once('prompts_base.py',old_prompts)
write_once('citation_policy_v3.py',(ROOT/'citation_policy_v2.py').read_text().replace("'soft_citations_20261101'","'v3_soft_citations_20261101'"))

source=(ROOT/'shared_media_experts_v2.py').read_text()
source=source.replace('import citation_policy_v2 as citations','import citation_policy_v3 as citations')
source=source.replace('from engine import ROOT,', 'sys.path.insert(0,str(Path(__file__).resolve().parents[2]))\nfrom engine import ROOT,')
source=source.replace('import shared_media_expert_prompts_v2 as prompts','import emotion_wheel_prompts as prompts')
source=source.replace("VERSION = 'gemini_graph_shared_media_v2'", "VERSION = 'gemini_graph_emotion_wheel_v3'")
source=source.replace("assert set(value)=={'expert','reason','answer','evidence','counterevidence'}", "assert set(value)=={'expert','reason','open_emotion','answer','mapping_reason','evidence','counterevidence'}\n    prompts.validate_open(value)")
source=source.replace("prompts.EXPERTS[role]", "prompts.expert(role,row['classes'])")
source=source.replace("prompts.SUMMARY,", "prompts.summary(row['classes']),")
source=source.replace("prompts.SUMMARY if name=='summary' else prompts.EXPERTS[name.removeprefix('expert_')]", "prompts.summary(row['classes']) if name=='summary' else prompts.expert(name.removeprefix('expert_'),row['classes'])")
source=source.replace("raw_audio_provided=bool(audio),graph_contains_audio_derived_nodes=", "wheel_version=prompts.WHEELS['version'],expert_emotions={role:dict(open_emotion=e['open_emotion'],mapped_label=e['answer'],mapping_reason=e['mapping_reason']) for role,e in experts.items()},\n                raw_audio_provided=bool(audio),graph_contains_audio_derived_nodes=")
source=source.replace('shared_raw_media=True,development_reflect=True))', "shared_raw_media=True,development_reflect=True,wheel_version=prompts.WHEELS['version'],wheel_sha256=digest(prompts.CONFIG_PATH)))")
source=source.replace('one_manual_development_reflect=True))', "one_manual_development_reflect=True,wheel_version=prompts.WHEELS['version'],wheel_sha256=digest(prompts.CONFIG_PATH)))")
source=source.replace("assert result['version']==VERSION and result['frames']==8", "assert result['wheel_version']==prompts.WHEELS['version']\n            assert result['version']==VERSION and result['frames']==8")
source=source.replace("expert={'expert':'image','reason':", "expert={'expert':'image','open_emotion':'愉快','mapping_reason':'当前愉悦属于joy家族','reason':")
source=source.replace("print('Shared-media routing, graph access, evidence references, audio capability, label space, no-gold and cache invalidation checks passed')", '''
    for ds,spec in prompts.WHEELS['datasets'].items():
        assert prompts.dataset_name(spec['labels'])==ds
        for role in ['graph','audio_subtitle','image']:
            system=prompts.expert(role,spec['labels'])
            assert ds in system and 'open_emotion' in system and 'mapping_reason' in system
            assert '不使用情绪轮转换' not in system
        assert ds in prompts.summary(spec['labels'])
    for bad in [[],['sad'], '开心、悲伤','sad and angry']:
        try:prompts.validate_open(dict(open_emotion=bad,mapping_reason='test'))
        except AssertionError:pass
        else:raise AssertionError('Multiple/empty open emotions accepted')
    try:validate(dict(summary,open_emotion='开心'),'summary',row['classes'],graph)
    except AssertionError:pass
    else:raise AssertionError('Summary emitted extra open classification')
    print('V3 wheels/routing/open+mapped single emotions/summary single label/no-gold/cache/soft citations checks passed')''')
source=source.replace('V2: frozen Gemini graph', 'V3: dataset-adapted hierarchical wheels; one open emotion + one mapped label per expert, one final closed label only from summary. Frozen Gemini graph')
source=source.replace('evidence reference validity', 'nonblocking citation diagnostics and single open/mapped emotion fields')
source=source.replace("document=dict(version=VERSION,complete=", "document=dict(version=VERSION,wheel_version=prompts.WHEELS['version'],mapping_semantics_automatically_verified=False,complete=")
write_once('pipeline.py',source)

config=json.loads((HERE/'emotion_wheels.json').read_text())
colors=['#F5C451','#E7776E','#8BAFE1','#A792C4','#70BFB5','#9AB866']
for ds,spec in config['datasets'].items():
    families=[(k,v) for k,v in spec['families'].items() if k!='neutral'];count=len(families)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">',
        '<rect width="1000" height="1000" fill="#fbfaf7"/>',
        '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" text-anchor="middle" fill="#24313b">',
        '<text x="500" y="48" font-size="27">'+ds+' · v3 项目适配情绪轮</text>',
        '<text x="500" y="77" font-size="16">内圈为任务标签 · 外圈为开放词示例 · 非官方心理学量表</text>']
    def xy(radius,theta):return (500+radius*math.cos(theta),510+radius*math.sin(theta))
    for i,(label,family) in enumerate(families):
        a=-math.pi/2+2*math.pi*i/count;b=a+2*math.pi/count;mid=(a+b)/2
        for r1,r2,opacity in [(100,220,1),(220,375,.42)]:
            x1,y1=xy(r1,a);x2,y2=xy(r2,a);x3,y3=xy(r2,b);x4,y4=xy(r1,b)
            path=f'M {x1} {y1} L {x2} {y2} A {r2} {r2} 0 0 1 {x3} {y3} L {x4} {y4} A {r1} {r1} 0 0 0 {x1} {y1} Z'
            parts.append(f'<path d="{path}" fill="{colors[i]}" fill-opacity="{opacity}" stroke="white" stroke-width="3"/>')
        x,y=xy(160,mid)
        parts.extend([f'<text x="{x}" y="{y-5}" font-size="21">{html.escape(label)}</text>',f'<text x="{x}" y="{y+21}" font-size="19">{family["name"]}</text>'])
        x,y=xy(290,mid)
        for j,term in enumerate(family['examples']):
            chinese=term.split('/')[0].strip()
            parts.append(f'<text x="{x}" y="{y-34+j*24}" font-size="18">{html.escape(chinese)}</text>')
    parts+=['<circle cx="500" cy="510" r="98" fill="#e7e8e7" stroke="white" stroke-width="3"/>',
        '<text x="500" y="501" font-size="23">neutral</text><text x="500" y="530" font-size="20">中性 / 平稳</text>',
        '<text x="500" y="936" font-size="17">位置仅用于展示层级，不定义情绪对立、距离或混合比例</text>',
        '<text x="500" y="963" font-size="16">未列词可结合证据映射；neutral不是不确定性默认类别</text></g></svg>']
    write_once(ds+'_emotion_wheel.svg','\n'.join(parts))

manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file() and p.name not in {'source_manifest.json'}}
manifest_path=HERE/'source_manifest.json'
if manifest_path.exists():
    assert json.loads(manifest_path.read_text())==manifest, 'V3 files changed; create a new version rather than overwrite'
else:manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Independent v3 created; prior versions untouched; source manifest saved')
