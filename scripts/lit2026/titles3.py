"""Extract (title, url) lists for CVPR / ICML / NeurIPS 2026 from the saved list pages and title-filter them.

usage: python -I titles3.py <dir_with_html> <out.json>
Reads cvpr_all.html, icml_list.html, nips_list.html (downloaded from openaccess.thecvf.com and *.cc/virtual).
"""
import json, re, sys, os, html

d, out = sys.argv[1], sys.argv[2]
rows = []

s = open(os.path.join(d, 'cvpr_all.html'), encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'<dt class="ptitle"><br><a href="([^"]+)">(.*?)</a></dt>', s, re.S):
    rows.append({'venue': 'CVPR 2026', 'title': html.unescape(re.sub(r'\s+', ' ', m.group(2))).strip(),
                 'url': 'https://openaccess.thecvf.com' + m.group(1)})
for f, venue in (('icml_list.html', 'ICML 2026'), ('nips_list.html', 'NeurIPS 2026')):
    s = open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()
    base = 'https://icml.cc' if venue.startswith('ICML') else 'https://neurips.cc'
    seen = set()
    for m in re.finditer(r'<li><a href="(/virtual/2026/poster/\d+)">(.*?)</a></li>', s, re.S):
        if m.group(1) in seen:
            continue
        seen.add(m.group(1))
        rows.append({'venue': venue, 'title': html.unescape(re.sub(r'\s+', ' ', m.group(2))).strip(), 'url': base + m.group(1)})

PAT = re.compile(
    r'debate|multi-?agent|multiple agents|agents? (?:collaborat|discuss|deliberat|ensemble)|deliberat|consensus|sycophan|conformity|'
    r'majority vot|voting|council|jury|persuasi|mixture[- ]of[- ]agents|multi-?llm|multi-?mllm|'
    r'emotion|affective|affect |sentiment|MER\b|MELD|empath', re.I)
cand = [r for r in rows if PAT.search(r['title'])]
json.dump({'all_count': len(rows), 'candidates': cand}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
from collections import Counter
print('all:', Counter(r['venue'] for r in rows))
print('title-candidates:', Counter(r['venue'] for r in cand))
