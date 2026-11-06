"""Fetch abstracts for ALL title-candidates (cand.json) not yet fetched. Polite (0.7 s), retries, incremental save.

usage: python -X utf8 -I fetch_all.py <cand.json> <already_fetched.json> <out.json>
"""
import json, re, sys, time, html, urllib.request

cand = json.load(open(sys.argv[1], encoding='utf-8'))['candidates']
done = {r['url'] for r in json.load(open(sys.argv[2], encoding='utf-8'))}
out_path = sys.argv[3]
todo = [r for r in cand if r['url'] not in done]
print('to fetch:', len(todo), flush=True)
res = []


def abstract_of(page, venue):
    if venue.startswith('CVPR'):
        m = re.search(r'<div id="abstract">(.*?)</div>', page, re.S)
    else:
        m = re.search(r'<div class="abstract-text-inner[^"]*"[^>]*>(.*?)</div>', page, re.S) or re.search(r'class="abstract-text[^"]*"[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return ''
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))).strip()


for i, r in enumerate(todo):
    page = None
    for k in range(3):
        try:
            page = urllib.request.urlopen(urllib.request.Request(r['url'], headers={'User-Agent': 'lit-check/1.0'}), timeout=40).read().decode('utf-8', 'ignore')
            break
        except Exception:
            time.sleep(2 + 2 * k)
    if page is None:
        print('FAIL', r['title'][:60], flush=True)
        continue
    links = sorted(set(re.findall(r'https?://(?:www\.)?(?:github\.com|huggingface\.co|gitlab\.com)/[^\s"\'<>)]+', page)))
    res.append({**r, 'abstract': abstract_of(page, r['venue']), 'page_code_links': links})
    if i % 25 == 0:
        print(i, len(res), flush=True)
        json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
    time.sleep(0.7)
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
print('done', len(res), flush=True)
