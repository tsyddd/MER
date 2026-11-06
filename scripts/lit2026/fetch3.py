"""Fetch abstracts (and any non-venue links) for a title shortlist from CVPR/ICML/NeurIPS 2026 paper pages.

usage: python -X utf8 -I fetch3.py <cand_or_all.json> <shortlist.txt> <out.json>
shortlist.txt: one title substring per line (case-insensitive); matched against the 'candidates' list.
Polite: 0.8 s between requests, plain GET, no login, no JS execution.
"""
import json, re, sys, time, html, urllib.request

cand = json.load(open(sys.argv[1], encoding='utf-8'))['candidates']
subs = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
out = []


def abstract_of(page, venue):
    if venue.startswith('CVPR'):
        m = re.search(r'<div id="abstract">(.*?)</div>', page, re.S)
    else:
        m = re.search(r'<div class="abstract-text-inner[^"]*"[^>]*>(.*?)</div>', page, re.S)
        if not m:
            m = re.search(r'class="abstract-text[^"]*"[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return ''
    t = re.sub(r'<[^>]+>', ' ', m.group(1))
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


for sub in subs:
    hits = [r for r in cand if sub.lower() in r['title'].lower()]
    if not hits:
        print('NO MATCH:', sub)
        continue
    r = hits[0]
    try:
        page = urllib.request.urlopen(urllib.request.Request(r['url'], headers={'User-Agent': 'lit-check/1.0'}), timeout=40).read().decode('utf-8', 'ignore')
    except Exception as e:
        print('ERR', sub, e)
        continue
    ab = abstract_of(page, r['venue'])
    links = sorted(set(re.findall(r'https?://(?:www\.)?(?:github\.com|huggingface\.co|gitlab\.com)/[^\s"\'<>)]+', page)))
    out.append({**r, 'abstract': ab, 'page_code_links': links})
    print(f"{r['venue'][:5]} | {r['title'][:70]} | abs={len(ab)} | links={links[:2]}")
    time.sleep(0.8)
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
