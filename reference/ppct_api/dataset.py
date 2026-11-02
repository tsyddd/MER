import csv
from pathlib import Path
def load_emer(video_root:Path,labels:Path,subtitles:Path,limit:int|None=None):
    labs={r['name']:r['discrete'] for r in csv.DictReader(labels.open(encoding='utf-8-sig'))}; subs={r['name']:r['chinese'] for r in csv.DictReader(subtitles.open(encoding='utf-8-sig'))}; rows=[]
    for name,label in labs.items():
        video=video_root/f'{name}.mp4'
        if video.exists(): rows.append({'sample_id':name,'video':str(video),'subtitle':subs.get(name,''),'label':label})
        if limit is not None and len(rows)>=limit: break
    return rows
