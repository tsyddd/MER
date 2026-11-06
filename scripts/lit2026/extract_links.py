"""Extract code/dataset links from the full text of downloaded PDFs (pdftotext, no PDF code is executed)."""
import re, subprocess, sys, os, json

pdf_dir, ids_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
res = {}
for pid in open(ids_file).read().split():
    path = os.path.join(pdf_dir, pid + ".pdf")
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
    # join hyphen/linebreak splits inside URLs a bit
    flat = re.sub(r"(https?://[^\s]*)\s*\n\s*([\w./\-]+)", r"\1\2", txt)
    links = set(re.findall(r"(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co|anonymous\.4open\.science|zenodo\.org|bitbucket\.org)/[^\s)\]}>,;\"']+", flat))
    links = sorted({l.rstrip(".") for l in links})
    # context lines mentioning code availability
    ctx = []
    for m in re.finditer(r"(?i)(code|source code|implementation|repository|released|publicly available|open-?source)[^\n]{0,160}(github|http)", flat):
        ctx.append(flat[max(0, m.start() - 60): m.end() + 80].replace("\n", " "))
    res[pid] = {"links": links, "ctx": ctx[:3], "pages_chars": len(txt)}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in res.items():
    print(k, v["links"][:6] if v["links"] else "-- NO LINK --")
