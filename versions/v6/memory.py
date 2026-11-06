"""Experience memory of R2-MAD (numpy re-implementation of the original ChromaDB + MMR retrieval, per provider).

Record = (sample, expert role, round r in {0,1,2}):
  key   text = Q + the expert's compact output of round r-1 + the debate summary of round r-1   (round 0: Q only)
  value text = Q + gold label + the expert's compact output of round r + stance changed + correct / incorrect
  response text = compact output of round r (for the peer-reliability estimate)
  meta: role, dataset, round, previous consensus ratio, correct (primary answer == gold)
Embeddings: BAAI/bge-m3 (CLS pooling, L2-normalised); similarity = cosine = dot product. Gold labels appear only in value texts and `correct`.

Retrieval (original debate-state-aware policy): filter same role (+ same dataset) -> top-3n by key similarity -> MMR picks n:
  score = lam * sim(case, query) * correct - (1 - lam) * max cosine(value(case), value(selected)),  lam = 1 - 0.9 * previous consensus ratio.
Peer reliability (original): for every other expert o, sum over candidate cases c of sim(current response of o, o's response in c's previous round)
  * correct(c) / sum of those sims; > 0.55 high, < 0.45 low. (If the sims sum to ~0 no mark is given; the original would divide by eps and mark low.)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

GAMMA = 0.9
HIGH, LOW = 0.55, 0.45


def value_text(question, solution, response, stance_changed, correct):
    changed = '不适用（第0轮）' if stance_changed is None else ('该专家改变了立场。' if stance_changed else '该专家没有改变立场。')
    return (f'<example_question>\n{question}\n</example_question>\n<example_solution>\n标准标签：{solution}\n</example_solution>\n'
            f'<example_agent_response>\n{response}\n</example_agent_response>\n<example_agent_stance_changed>\n{changed}\n</example_agent_stance_changed>\n'
            f'<example_agent_response_correctness>\n{"该回答正确。" if correct else "该回答不正确。"}\n</example_agent_response_correctness>')


class Memory:
    def __init__(self, folder):
        folder = Path(folder)
        self.records = [json.loads(l) for l in (folder / 'records.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        z = np.load(folder / 'embeddings.npz')
        assert z['ids'].tolist() == [r['db_id'] for r in self.records], 'embeddings and records are out of sync'
        norm = lambda a: (a.astype(np.float32) / np.maximum(np.linalg.norm(a.astype(np.float32), axis=1, keepdims=True), 1e-8))  # noqa: E731
        self.K, self.V, self.R = norm(z['keys']), norm(z['values']), norm(z['responses'])
        self.by_role_ds = {}
        self.index = {}
        for i, r in enumerate(self.records):
            self.by_role_ds.setdefault((r['role'], r['dataset']), []).append(i)
            self.index[(r['qid'], r['round'], r['role'])] = i
        self.correct = np.array([1.0 if r['correct'] else 0.0 for r in self.records])

    def retrieve(self, role, dataset, qvec, n, prev_ratio):
        """-> (selected indices in pick order, candidate indices (top-3n by similarity), similarities of candidates)."""
        idx = np.array(self.by_role_ds.get((role, dataset), []), dtype=int)
        if len(idx) == 0:
            return [], [], np.array([])
        sims = self.K[idx] @ qvec
        order = np.argsort(-sims, kind='stable')[:3 * n]
        cand = idx[order]
        csim = sims[order]
        lam = 1.0 - GAMMA * prev_ratio
        vm = self.V[cand] @ self.V[cand].T
        selected, remaining = [], list(range(len(cand)))
        for _ in range(min(n, len(cand))):
            maxsel = np.zeros(len(cand)) if not selected else vm[:, selected].max(axis=1)
            scores = np.full(len(cand), -np.inf)
            for i in remaining:
                scores[i] = lam * csim[i] * self.correct[cand[i]] - (1.0 - lam) * maxsel[i]
            best = int(np.argmax(scores))
            selected.append(best)
            remaining.remove(best)
        return [int(cand[i]) for i in selected], [int(c) for c in cand], csim

    def peer_reliability(self, cand, peer_vecs):
        """peer_vecs: {role: unit vector of that peer's previous-round compact output} -> {role: 'high' | 'low' | None}."""
        out = {}
        for role, vec in peer_vecs.items():
            wsum = ssum = 0.0
            for c in cand:
                rec = self.records[c]
                if rec['round'] < 1:
                    continue
                j = self.index.get((rec['qid'], rec['round'] - 1, role))
                if j is None:
                    continue
                sim = max(float(vec @ self.R[j]), 0.0)
                wsum += sim * self.correct[c]
                ssum += sim
            conf = wsum / ssum if ssum > 1e-6 else None
            out[role] = None if conf is None else ('high' if conf > HIGH else 'low' if conf < LOW else None)
        return out
