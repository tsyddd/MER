"""Read-only verification of GitHub repos via `gh api` (GET only)."""
import json, subprocess, sys, base64, re

repos = [l.split() for l in open(sys.argv[1], encoding="utf-8").read().strip().splitlines()]
out = {}
SRC = (".py", ".ipynb", ".js", ".ts", ".sh", ".java", ".cpp", ".c", ".go", ".rs", ".yaml", ".yml", ".json")
CODE = (".py", ".ipynb", ".js", ".ts", ".java", ".cpp", ".go", ".rs", ".sh")


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        return None, r.stderr.strip()[:150]
    try:
        return json.loads(r.stdout), None
    except Exception as e:
        return None, str(e)


for pid, slug in repos:
    info, err = gh(f"repos/{slug}")
    if info is None:
        out[pid] = {"slug": slug, "ok": False, "err": err}
        print(f"{pid:28s} {slug:55s} NOT FOUND ({err})")
        continue
    br = info.get("default_branch", "main")
    tree, _ = gh(f"repos/{slug}/git/trees/{br}?recursive=1")
    files = [t["path"] for t in (tree or {}).get("tree", []) if t["type"] == "blob"]
    code = [f for f in files if f.endswith(CODE)]
    readme, _ = gh(f"repos/{slug}/readme")
    rtxt = ""
    if readme and readme.get("content"):
        rtxt = base64.b64decode(readme["content"]).decode("utf-8", "ignore")
    res = {
        "slug": slug, "ok": True, "stars": info["stargazers_count"], "forks": info["forks_count"],
        "pushed": info["pushed_at"][:10], "created": info["created_at"][:10], "license": (info.get("license") or {}).get("spdx_id"),
        "archived": info["archived"], "fork": info["fork"], "size_kb": info["size"], "desc": info.get("description"),
        "n_files": len(files), "n_code_files": len(code), "truncated": (tree or {}).get("truncated", False),
        "top": sorted({f.split("/")[0] for f in files})[:14], "readme_len": len(rtxt),
        "readme_head": re.sub(r"\s+", " ", rtxt[:260]),
        "readme_mentions_venue": bool(re.search(r"ACL|EMNLP|Findings", rtxt)),
    }
    out[pid] = res
    print(f"{pid:28s} {slug:50s} stars={res['stars']:<4} pushed={res['pushed']} code_files={res['n_code_files']:<4} files={res['n_files']:<4} lic={res['license']} venue_in_readme={res['readme_mentions_venue']}")
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
