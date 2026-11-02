"""Dataset-specific project adaptation, not an official AffectGPT wheel."""
import json
import re
from pathlib import Path
import prompts_base as base

CONFIG_PATH=Path(__file__).with_name('emotion_wheels.json')
WHEELS=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
ORGANIZATION=base.ORGANIZATION


def dataset_name(classes):
    matches=[name for name,spec in WHEELS['datasets'].items() if set(spec['labels'])==set(classes)]
    assert len(matches)==1, 'Dataset must match original MER6 or MELD7 label space'
    return matches[0]


def wheel_text(classes):
    name=dataset_name(classes);spec=WHEELS['datasets'][name]
    lines=['【'+name+'项目适配情绪轮】',
        '这是项目自定义层级参考，不是数据集或AffectGPT官方情绪轮。Level1严格保留本数据集标签。']
    for root,family in spec['families'].items():
        lines.append(root+'（'+family['name']+'）：'+family['definition']+' 开放词示例：'+'；'.join(family['examples']))
    lines+=['【共同映射原则】']+WHEELS['shared_rules']+['【易混边界与类别缺失】']+spec['boundaries']
    return '\n'.join(lines)


EXPERT_SCHEMA='''【v3输出要求】先依据本领域证据形成一个开放词汇情绪词，再映射到上方情绪轮的一个Level1标签。开放词不限示例，应尽可能准确具体；只选一个中文或英文词/短语，不输出同义词列表、双语并列、复合多情绪或多个候选。
open_emotion是唯一开放情绪，answer是唯一映射后数据集标签，mapping_reason说明该开放情绪为什么在当前语境下映射到answer；近似投影需要说明限制。不能把三路结论预先统一，不能为了映射改变证据。
只返回JSON，字段恰好为：{"expert":"ROLE","reason":"有证据的情感推理","open_emotion":"一个开放情绪词或短语","answer":"一个原始Level1标签","mapping_reason":"结合轮中定义和当前证据解释映射","evidence":[{"id":"E1","source":"visual","anchor":"对应帧/音频/字幕/节点位置","observation":"观察事实","interpretation":"证据含义","polarity":"support"}],"counterevidence":"相反解释或限制"}。
证据编号、括号和定位写法仅作辅助，不因未写[E1]就判失败，但仍需非空具体证据，不得使用未提供的模态。不要输出<answer>包装。'''


def expert(role,classes):
    # Keep the four role rubrics, replace the v2 closed-label-only schema.
    text=base.EXPERTS[role].split('只返回JSON，字段恰好为：',1)[0]
    text=text.replace('只从allowed_labels选一个原始标签，不改标签空间，不使用情绪轮转换。',
        '先识别一个开放情绪，再按本数据集情绪轮映射成一个allowed_labels原始标签，不改标签空间。')
    return text+'\n'+wheel_text(classes)+'\n'+EXPERT_SCHEMA.replace('ROLE',role)


def summary(classes):
    text=base.SUMMARY.replace('不使用情绪轮映射，','参考本数据集适配轮核对语义，')
    return text+'\n'+wheel_text(classes)+'''\n【v3汇总】专家的open_emotion只是情绪解释，answer只是其映射意见；参考mapping_reason和原始证据判断，不能按映射标签多数投票，也不能用多个开放词的相似性代替证据。开放情绪相同但映射不同应检查语义边界，映射相同但证据同源不能重复计权。
summary不输出open_emotion、mapping_reason或第二个分类标签，只输出一个最终answer及其reason（保留原证据引用列表）。最终schema仍恰好为{"reason":"基于原媒体和专家证据的最终推理","answer":"一个本数据集Level1标签","evidence_refs":[]}。程序只包装一次<answer>label</answer>。'''


def validate_open(value):
    phrase=value.get('open_emotion')
    assert isinstance(phrase,str) and phrase.strip() and len(phrase.strip())<=80, 'One nonempty open emotion required'
    assert not re.search(r'[,，、;；/|\n]|\b(?:and|or)\b|以及|或者|既.*又',phrase,re.I), 'Open emotion must be one term, not a list'
    assert isinstance(value.get('mapping_reason'),str) and value['mapping_reason'].strip(), 'Mapping explanation required'
