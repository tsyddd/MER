from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
Layer = Literal['process','person','context']
TemporalRelation = Literal['after','simultaneous']
JointRelation = Literal['process_joint','person_joint','context_joint']
Labels = Literal['happy','sad','neutral','angry','worried','surprise']
class EvidenceNode(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1); type:Layer; content:str=Field(min_length=1); time_index:int=Field(ge=0)
    evidence_sources:list[Literal['visual','audio','subtitle','provided_context']]=Field(default_factory=list)
    dimension:str|None=None
    evidence_status:Literal['observed','explicitly_stated','strongly_supported','uncertain']|None=None
class TemporalEdge(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source:str; target:str; relation:TemporalRelation; reason:str=Field(min_length=1); entity_anchor:str|None=None
class EvidenceOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    nodes:list[EvidenceNode]=Field(default_factory=list); temporal_relations:list[TemporalEdge]=Field(default_factory=list)
    @model_validator(mode='after')
    def validate_all(self):
        ids=[n.id for n in self.nodes]
        if len(ids)!=len(set(ids)): raise ValueError('evidence node ids must be unique')
        by_id={n.id:n for n in self.nodes}
        for e in self.temporal_relations:
            if e.source not in by_id or e.target not in by_id: raise ValueError(f'temporal endpoint missing: {e.source}->{e.target}')
            if by_id[e.source].type!=by_id[e.target].type: raise ValueError('temporal edge crosses layer')
            if e.source==e.target: raise ValueError('temporal self-edge')
        return self

class RawTemporalEdge(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=1); source:str; target:str; entity_anchor:str=Field(min_length=1)
    relation:Literal['process_temporal','person_temporal','context_temporal']
    temporal_relation:TemporalRelation

class RawEvidenceNode(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1); type:Layer; content:str=Field(min_length=1)
    evidence_sources:list[Literal['visual','audio','subtitle','provided_context']]=Field(default_factory=list)
    time_index:int=Field(ge=0); dimension:str|None=None
    evidence_status:Literal['observed','explicitly_stated','strongly_supported','uncertain']|None=None

class RawEvidenceLayer(BaseModel):
    model_config=ConfigDict(extra='forbid')
    nodes:list[RawEvidenceNode]=Field(default_factory=list)

class RawEvidenceOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    process:RawEvidenceLayer
    person:RawEvidenceLayer
    context:RawEvidenceLayer

class JointJudgmentEdge(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=1); source:str; target:str
    relation:JointRelation

class JointJudgmentOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    edges:list[JointJudgmentEdge]=Field(default_factory=list)

class TemporalJudgmentOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    edges:list[RawTemporalEdge]=Field(default_factory=list)
class JointEdge(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=1); source:str; target:str; relation:JointRelation
class RelationOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    edges:list[JointEdge]=Field(default_factory=list,max_length=30)
class GraphEdge(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source:str; target:str; relation:Literal['after','simultaneous','process_joint','person_joint','context_joint']; reason:str; entity_anchor:str|None=None
class GraphOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    nodes:list[EvidenceNode]; edges:list[GraphEdge]
    @model_validator(mode='after')
    def validate_edges(self):
        by_id={n.id:n for n in self.nodes}; seen=set()
        for e in self.edges:
            if e.source not in by_id or e.target not in by_id: raise ValueError(f'graph endpoint missing: {e.source}->{e.target}')
            if e.source==e.target: raise ValueError('graph self-edge')
            if e.relation.endswith('_joint') and by_id[e.source].type!=by_id[e.target].type: raise ValueError('joint edge crosses layer')
            key=(e.source,e.target,e.relation)
            if key in seen: raise ValueError(f'duplicate edge: {key}')
            seen.add(key)
        return self
class OrganizationOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text:str=Field(min_length=1)
class ReasoningOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=1); answer:Labels

class ExpertOutput(BaseModel):
    """A complete independent final-reasoning proposal."""
    model_config=ConfigDict(extra='forbid')
    expert:Literal['video','ppct','subtitle']
    reason:str=Field(min_length=1)
    answer:Labels
    evidence_refs:list[str]=Field(default_factory=list,max_length=20)

class SummaryOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=1)
    answer:Labels

class SkillCandidate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    rationale:str=Field(min_length=1)
    edits:list[dict]=Field(default_factory=list,max_length=3)
    # Each edit is constrained by the runner to {branch, operation, rule}.

class EvolutionCritique(BaseModel):
    model_config=ConfigDict(extra='forbid')
    sample_id:str
    error_type:str=Field(min_length=1)
    evidence_issue:str=Field(min_length=1)
    relation_issue:str=Field(min_length=1)
    reasoning_issue:str=Field(min_length=1)
    prompt_change:str=Field(min_length=1)
    revised_rule:str=Field(min_length=1)
