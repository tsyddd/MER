"""Native-video/audio PPCT prompts; no emotion ground truth is supplied."""
from .prompts import EVIDENCE_PROMPT, TEMPORAL_PROMPT, JOINT_PROMPT, ORGANIZATION_PROMPT

AV_INPUT = '''输入为原始视频文件，保留其中的音轨。联合观察画面并聆听音轨；外部字幕是独立的语言来源。能听到时记录实际台词、音量变化、语速、停顿、笑声等可听事实，不能把声音直接命名为情绪。Process 可记录当前说话和回应；Person 可记录同一说话人的音量、语速及停顿等声音表现，content 明确人物和可听特征，evidence_sources 标记 audio。visual 只标画面依据，subtitle 只标外部字幕依据，不能把字幕推断成听到的声音。不能实际听到时如实说明，不捏造音轨事实。所有边只能连接同层节点；不输出跨层边。'''

GEMINI_EVIDENCE_PROMPT = EVIDENCE_PROMPT.replace('画面或字幕核对','画面、音轨或字幕核对') + '\n\n' + AV_INPUT
GEMINI_TEMPORAL_PROMPT = TEMPORAL_PROMPT + '\n\n' + AV_INPUT
GEMINI_JOINT_PROMPT = JOINT_PROMPT + '\n\n' + AV_INPUT
GEMINI_ORGANIZATION_PROMPT = ORGANIZATION_PROMPT.replace('观看按时间排列的视频帧','观看原始视频并聆听音轨').replace('画面与字幕事实','画面、音轨与字幕事实') + '\n\n' + AV_INPUT
