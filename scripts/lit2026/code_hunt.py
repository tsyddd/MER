"""Find code links for papers: arXiv title search -> arXiv PDF text (or CVPR open-access PDF) -> github/hf links.

usage: python -X utf8 -I code_hunt.py <titles.json> <out.json> <workdir>
titles.json: [{"title":..., "venue":..., "url":...}, ...]
Read-only: plain GETs of public pages/PDFs; PDFs are saved in <workdir> and only parsed with pdftotext.
"""
import json, re, subprocess, sys, time, os, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

items = json.load(open(sys.argv[1], encoding='utf-8'))
out_path, wd = sys.argv[2], sys.argv[3]
os.makedirs(wd, exist_ok=True)
NS = {'a': 'http://www.w3.org/2005/Atom', 'x': 'http://arxiv.org/schemas/atom'}
UA = {'User-Agent': 'lit-check/1.0'}
LINK = re.compile(r'(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co|anonymous\.4open\.science)/[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)?')


def get(url, tries=3, timeout=60):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:
            err = e
            time.sleep(2 + 2 * k)
    raise err


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def pdf_links(pdf_bytes, name):
    p = os.path.join(wd, name + '.pdf')
    open(p, 'wb').write(pdf_bytes)
    txt = subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore').stdout
    flat = re.sub(r'(github\.com/[A-Za-z0-9_.\-]*)\s*\n\s*([A-Za-z0-9_.\-/]+)', r'\1\2', txt)
    found = sorted({m.rstrip('.,;)') for m in LINK.findall(flat)})
    ctx = []
    for m in re.finditer(r'(?i)(code|implementation|source)[^\n]{0,120}(github|anonymous|huggingface)', flat):
        ctx.append(flat[max(0, m.start() - 40): m.end() + 60].replace('\n', ' '))
    return found, ctx[:2]


res = []
for it in items:
    t = it['title']
    rec = {'title': t, 'venue': it['venue'], 'arxiv': None, 'links': [], 'ctx': [], 'note': ''}
    try:
        if it['venue'].startswith('CVPR'):
            pdf = it['url'].replace('/html/', '/papers/').replace('.html', '.pdf')
            rec['links'], rec['ctx'] = pdf_links(get(pdf), 'cvpr_' + norm(t)[:30])
            rec['note'] = 'cvpr-openaccess-pdf'
        else:
            q = urllib.parse.quote('ti:"' + re.sub(r'[:"\-]', ' ', t) + '"')
            root = ET.fromstring(get(f'https://export.arxiv.org/api/query?search_query={q}&max_results=3'))
            hit = None
            for e in root.findall('a:entry', NS):
                et = re.sub(r'\s+', ' ', e.find('a:title', NS).text or '')
                if norm(et)[:40] == norm(t)[:40]:
                    hit = (e.find('a:id', NS).text.rsplit('/', 1)[-1], et, e.find('a:summary', NS).text or '', (e.find('x:comment', NS).text if e.find('x:comment', NS) is not None else ''))
                    break
            time.sleep(3.2)
            if not hit:
                rec['note'] = 'no arXiv match'
            else:
                aid = re.sub(r'v\d+$', '', hit[0])
                rec['arxiv'] = aid
                rec['comment'] = hit[3]
                links = set(LINK.findall(hit[2] + ' ' + (hit[3] or '')))
                try:
                    l2, rec['ctx'] = pdf_links(get(f'https://arxiv.org/pdf/{aid}'), 'ax_' + aid.replace('/', '_'))
                    links |= set(l2)
                except Exception as e:
                    rec['note'] = f'pdf fail: {type(e).__name__}'
                rec['links'] = sorted(links)
                time.sleep(2)
    except Exception as e:
        rec['note'] = f'ERR {type(e).__name__}: {e}'
    res.append(rec)
    print(f"{it['venue'][:5]} | {t[:60]} | arxiv={rec['arxiv']} | links={rec['links'][:3]} | {rec['note']}", flush=True)
    json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
