"""bge-m3 dense embedding (CLS pooling, L2-normalised) with plain transformers (the server .venv has no sentence-transformers).
Weights: /media/liang/12T/han/cache/bge-m3 (downloaded from the hf-mirror). Same vectors as SentenceTransformer('BAAI/bge-m3')."""
from __future__ import annotations
import numpy as np

PATH = '/media/liang/12T/han/cache/bge-m3'


class Embedder:
    def __init__(self, path=PATH, device='cuda', max_length=2048):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.device = device
        self.max_length = max_length
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModel.from_pretrained(path, torch_dtype=torch.float16).to(device).eval()

    def encode(self, texts, batch=8):
        torch = self.torch
        out = []
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        vecs = [None] * len(texts)
        with torch.no_grad():
            for s in range(0, len(order), batch):
                ids = order[s:s + batch]
                enc = self.tok([texts[i] for i in ids], padding=True, truncation=True, max_length=self.max_length, return_tensors='pt').to(self.device)
                h = self.model(**enc).last_hidden_state[:, 0].float()
                h = torch.nn.functional.normalize(h, dim=-1).cpu().numpy()
                for i, v in zip(ids, h):
                    vecs[i] = v
        return np.stack(vecs).astype(np.float32)

    def encode_one(self, text):
        return self.encode([text])[0]
