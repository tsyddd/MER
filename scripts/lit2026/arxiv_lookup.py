"""Look up arXiv versions by title; report id, comment, and any github links in abstract/comment. Read-only."""
import sys, re, json, urllib.parse, urllib.request, time
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
titles = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
out = {}
for t in titles:
    q = urllib.parse.quote('ti:"' + re.sub(r'[:"]', " ", t) + '"')
    url = f"https://export.arxiv.org/api/query?search_query={q}&max_results=3"
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lit-check/1.0"}), timeout=40).read()
        root = ET.fromstring(data)
    except Exception as e:
        print("ERR", t[:50], e)
        continue
    found = []
    for e in root.findall("a:entry", NS):
        title = re.sub(r"\s+", " ", e.find("a:title", NS).text or "")
        aid = (e.find("a:id", NS).text or "").rsplit("/", 1)[-1]
        com = e.find("x:comment", NS)
        com = com.text if com is not None else ""
        summ = e.find("a:summary", NS).text or ""
        gh = re.findall(r"github\.com/[\w.\-]+/[\w.\-]+", summ + " " + (com or ""))
        found.append({"id": aid, "title": title, "comment": com, "gh": gh, "pub": (e.find("a:published", NS).text or "")[:10]})
    out[t] = found
    best = found[0] if found else None
    sim = best and re.sub(r"\W", "", best["title"].lower())[:30] == re.sub(r"\W", "", t.lower())[:30]
    print(("MATCH " if sim else "weak  ") + t[:60], "->", (best["id"], best["pub"], best["gh"], (best["comment"] or "")[:70]) if best else None)
    time.sleep(3.2)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
