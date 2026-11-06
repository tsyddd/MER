"""Tag debate-related 2026 ACL/EMNLP papers by relevance to the PPCT emotion project."""
import json, re, sys, collections

hits = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]

TAGS = {
    "A从众/说服": r"conform|sycophan|herd|persuas|majority (?:vote|opinion|pressure)|stubborn|change (?:their|its) (?:answer|mind)|flip|echo|groupthink|wrong consensus|social influence|peer pressure",
    "B同质/多样性": r"homogen|heterogene|divers|correlated|independen|same (?:model|base)|different (?:models|LLMs)|model diversity|persona",
    "C何时辩论/路由/成本": r"when to debate|adaptive|rout|trigger|early.?stop|cost|efficien|token|cascade|confidence|calibrat|uncertain|disagree|conformal",
    "D证据/验证/裁判": r"evidence|ground|verif|judge|hallucinat|fact.?check|faithful|arbiter|moderator",
    "E多模态/情绪": r"multimodal|multi-modal|vision|visual|audio|speech|video|emotion|affect|sentiment|MLLM|VLM|LVLM",
    "F反思/自我纠错": r"reflect|self-correct|self-refine|self-consisten|feedback|revise|memory|experience",
    "G少数派/错误共识": r"minorit|dissent|correct (?:answer|agent)s? (?:is|are|get|was)|abandon|wrong answer|error propagation|degrad|hurt|fail|collapse|problem drift|illusion",
}
rows = []
for p in hits:
    s = p["title"] + " " + p["abstract"]
    if not re.search(r"debate", s, re.I):
        continue
    if not re.search(r"agent|LLM|language model|MLLM", s, re.I):
        continue
    tags = [k for k, pat in TAGS.items() if re.search(pat, s, re.I)]
    gh = re.findall(r"https?://(?:www\.)?github\.com/[\w.\-]+/[\w.\-]+", p["abstract"] + " " + p.get("software", ""))
    rows.append({**p, "tags": tags, "ntags": len(tags), "gh_in_abs": gh})
rows.sort(key=lambda r: (-r["ntags"], r["id"]))
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("debate papers:", len(rows))
c = collections.Counter(r["volume"].replace("2026.", "") for r in rows)
print(dict(c))
print("with github link in abstract/software:", sum(1 for r in rows if r["gh_in_abs"]))
for r in rows[:70]:
    print(f"{r['ntags']} {r['volume'].replace('2026.',''):15s} {r['id']:26s} {r['title'][:100]} | {','.join(t[0] for t in r['tags'])}")
