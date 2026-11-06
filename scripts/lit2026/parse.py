"""Parse ACL Anthology XML files and list volumes / filter papers by keywords.

usage: python -I parse.py <xml_dir> volumes
       python -I parse.py <xml_dir> filter <out.json>
"""
import sys, re, json, glob, os
import xml.etree.ElementTree as ET


def text(e):
    return "".join(e.itertext()).strip() if e is not None else ""


def load(xml_dir):
    papers = []
    vols = {}
    for path in sorted(glob.glob(os.path.join(xml_dir, "*.xml"))):
        root = ET.parse(path).getroot()
        cid = root.get("id")
        for vol in root.findall("volume"):
            vid = f"{cid}-{vol.get('id')}"
            meta = vol.find("meta")
            vols[vid] = text(meta.find("booktitle")) if meta is not None else ""
            n = 0
            for p in vol.findall("paper"):
                n += 1
                pid = f"{cid}-{vol.get('id')}.{p.get('id')}"
                authors = [text(a.find("first")) + " " + text(a.find("last")) for a in p.findall("author")]
                papers.append({
                    "id": pid,
                    "volume": vid,
                    "title": text(p.find("title")),
                    "abstract": text(p.find("abstract")),
                    "authors": authors,
                    "url": text(p.find("url")),
                    "pages": text(p.find("pages")),
                    "doi": text(p.find("doi")),
                    "attachments": [(a.get("type"), text(a)) for a in p.findall("attachment")],
                    "software": text(p.find("software")),
                    "revision": [text(r) for r in p.findall("revision")],
                })
            vols[vid] += f"  [{n} papers]"
    return papers, vols


if __name__ == "__main__":
    d, cmd = sys.argv[1], sys.argv[2]
    papers, vols = load(d)
    if cmd == "volumes":
        for k, v in vols.items():
            print(k, "|", v[:120])
        print("total papers:", len(papers))
    elif cmd == "filter":
        out = sys.argv[3]
        pat = re.compile(r"debate|multi-?agent|multiple agents|agents? (?:collaborat|discuss)|persuasi|consensus|sycophan|conform|multi-?llm|LLM(?:s)? (?:collaborat|discuss)|group discussion|panel|jury|peer review|devil", re.I)
        hits = [p for p in papers if pat.search(p["title"] + " " + p["abstract"])]
        json.dump(hits, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("hits:", len(hits), "of", len(papers))
