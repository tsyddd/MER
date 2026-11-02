from __future__ import annotations
import cv2
import json
import numpy as np
from pathlib import Path

def extract_frames(video: Path, output: Path, count: int = 8) -> list[str]:
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open video: {video}')
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise RuntimeError(f'video has no frames: {video}')
    indices = sorted(set(round(i * (total - 1) / max(1, count - 1)) for i in range(min(count, total))))
    frames = []
    for out_index, frame_index in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok:
            cap.release()
            raise RuntimeError(f'failed to read frame {frame_index} from {video}')
        path = output / f'frame_{out_index:02d}.jpg'
        if not cv2.imwrite(str(path), frame):
            cap.release()
            raise RuntimeError(f'failed to write frame: {path}')
        frames.append(str(path))
    cap.release()
    if not frames:
        raise RuntimeError(f'no frames extracted: {video}')
    return frames

def extract_contact_sheets(video: Path, output: Path) -> list[str]:
    """32 uniformly sampled frames, four chronological tiles per 2x2 sheet."""
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open video: {video}')
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if total <= 0 or fps <= 0:
        cap.release()
        raise RuntimeError(f'invalid video metadata: {video}')
    indices = [round(i * (total - 1) / 31) for i in range(32)]
    tiles = []; records = []
    try:
        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok: raise RuntimeError(f'cannot read frame {idx}: {video}')
            raw = output / f'frame_{i:02d}.jpg'
            if not cv2.imwrite(str(raw), frame): raise RuntimeError(f'cannot write {raw}')
            h,w = frame.shape[:2]; scale = min(640/w,480/h)
            resized = cv2.resize(frame,(max(1,round(w*scale)),max(1,round(h*scale))))
            tile = np.zeros((510,640,3),dtype=np.uint8)
            rh,rw = resized.shape[:2]; x=(640-rw)//2; y=30+(480-rh)//2
            tile[y:y+rh,x:x+rw]=resized
            cv2.putText(tile,f'{i+1:02d}/32  t={idx/fps:.2f}s',(8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1,cv2.LINE_AA)
            tiles.append(tile)
            records.append({'sample_index':i,'frame_index':idx,'seconds':idx/fps,'raw_frame':str(raw.resolve()),'sheet_index':i//4,'tile_position':i%4})
    finally:
        cap.release()
    sheets=[]
    for i in range(8):
        group=tiles[i*4:i*4+4]
        sheet=np.vstack([np.hstack(group[:2]),np.hstack(group[2:])])
        path=output/f'sheet_{i:02d}.jpg'
        if not cv2.imwrite(str(path),sheet): raise RuntimeError(f'cannot write {path}')
        sheets.append(str(path.resolve()))
    (output/'sampling.json').write_text(json.dumps({'source':str(video),'sampled_count':32,'unique_frame_count':len(set(indices)),'sheet_count':8,'layout':'2x2: top-left, top-right, bottom-left, bottom-right','frames':records},ensure_ascii=False,indent=2)+'\n')
    return sheets
