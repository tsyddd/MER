"""Build the frozen Gemini graphs of the 320 train samples (server, Linux).

Runs the original PPCT pipeline with the Gemini provider (perception -> temporal -> joint -> program graph ->
organization -> final, engine.sample(row, 'gemini', 'ppct')) exactly as was done for the 80 validation samples; gold labels
are never sent. The graphs are then copied to data/gemini_graph_train_v4 with a manifest (same fields as the validation
manifest in data/gemini_graph_three_experts_v1, which is not touched). Resumable: engine stages are cached.

Usage: python scripts/gen_train_graphs.py --workers 4
"""
import argparse
import concurrent.futures
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import Client, digest, sample, save, update_log  # noqa: E402
from reference.ppct_api.schemas import GraphOutput  # noqa: E402

DEST = ROOT / 'data' / 'gemini_graph_train_v4'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    rows = [json.loads(l) for l in (ROOT / 'data/manifests/train.jsonl').read_text().splitlines() if l.strip()]
    assert len(rows) == len({r['id'] for r in rows}) == 320
    model = Client('gemini').model
    update_log(f'训练集图谱生成启动：Gemini 原 PPCT 流程，{len(rows)} 条，workers={a.workers}；输出 outputs/ppct/gemini/<id>，冻结图谱目录 data/gemini_graph_train_v4。')
    status = {}
    for rnd in range(2):  # second pass retries errors; finished stages are cached
        todo = [r for r in rows if status.get(r['id']) != 'success']
        if not todo:
            break

        def one(r):
            res = sample(r, 'gemini', 'ppct')
            print(json.dumps(dict(id=r['id'], status=res['status'], stage=res.get('stage'), error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
            return r['id'], res['status']
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            status.update(dict(pool.map(one, todo)))
    manifest = {}
    DEST.mkdir(parents=True, exist_ok=True)
    for r in rows:
        src = ROOT / 'outputs/ppct/gemini' / r['id'] / 'graph.json'
        if status.get(r['id']) != 'success' or not src.exists():
            continue
        graph = GraphOutput.model_validate_json(src.read_text())
        assert graph.nodes
        dst = DEST / r['id'] / 'graph.json'
        if dst.exists():
            assert digest(src) == digest(dst), 'Frozen graph differs; refuse overwrite'
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        manifest[r['id']] = dict(path=str(dst), sha256=digest(dst), source=str(src), source_provider='gemini', source_model=model,
                                 contains_audio_derived_nodes=any('audio' in n.evidence_sources for n in graph.nodes))
    save(DEST / 'manifest.json', manifest)
    failed = [r['id'] for r in rows if r['id'] not in manifest]
    update_log(f'训练集图谱生成结束：成功 {len(manifest)}/{len(rows)}；失败 {len(failed)}（{", ".join(failed[:10])}{"…" if len(failed) > 10 else ""}）。清单 data/gemini_graph_train_v4/manifest.json。')
    print(json.dumps(dict(ok=len(manifest), failed=failed), ensure_ascii=False))
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
