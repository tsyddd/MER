from .schemas import EvidenceOutput,GraphOutput,GraphEdge,RelationOutput
def candidate_pairs(nodes): return [{'source':nodes[i].id,'target':nodes[j].id} for i in range(len(nodes)) for j in range(i+1,len(nodes))]
def build_graph(evidence:EvidenceOutput,relations:dict[str,RelationOutput]):
    by_id={n.id:n for n in evidence.nodes}; edges=[GraphEdge(source=e.source,target=e.target,relation=e.relation,reason=e.reason,entity_anchor=e.entity_anchor) for e in evidence.temporal_relations]
    for layer,out in relations.items():
        for e in out.edges:
            if e.source not in by_id or e.target not in by_id: raise ValueError(f'{layer} relation endpoint missing: {e.source}->{e.target}')
            if by_id[e.source].type!=layer or by_id[e.target].type!=layer: raise ValueError(f'{layer} relation crosses layer')
            edges.append(GraphEdge(source=e.source,target=e.target,relation=e.relation,reason=e.reason))
    return GraphOutput(nodes=evidence.nodes,edges=edges)
