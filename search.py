#!/usr/bin/env python3
"""UPE78 Metasearch Engine - aggregates public search APIs."""
import json, sys, time, urllib.request, urllib.parse, re, html as htmlmod

UA = {"User-Agent": "upe78-metasearch/1.0 (github actions)"}

def fetch_json(url, timeout=15):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)[:200]}

def wiki(q):
    u = ("https://en.wikipedia.org/w/api.php?action=opensearch"
         f"&search={urllib.parse.quote(q)}&limit=6&namespace=0&format=json")
    d = fetch_json(u)
    if isinstance(d, list) and len(d) >= 4:
        return [{"source":"wikipedia","title":t,"url":l,"snippet":s}
                for t,l,s in zip(d[1],d[2],d[3])]
    return []

def ddg(q):
    u = f"https://api.duckduckgo.com/?q={urllib.parse.quote(q)}&format=json&no_html=1"
    d = fetch_json(u)
    out = []
    if isinstance(d, dict):
        if d.get("AbstractText"):
            out.append({"source":"ddg_abstract","title":d.get("Heading",q),"url":d.get("AbstractURL",""),"snippet":d["AbstractText"]})
        for t in d.get("RelatedTopics", [])[:8]:
            if isinstance(t, dict) and t.get("Text"):
                out.append({"source":"ddg","title":t["Text"][:80],"url":t.get("FirstURL",""),"snippet":t["Text"]})
    return out

def hn(q):
    d = fetch_json(f"http://hn.algolia.com/api/v1/search?query={urllib.parse.quote(q)}&hitsPerPage=8")
    return [{"source":"hackernews","title":h.get("title",""),
             "url":h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
             "snippet":f"{h.get('points',0)} pts | {h.get('num_comments',0)} comments"}
            for h in d.get("hits",[]) if isinstance(d, dict)]

def arxiv(q):
    u = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(q)}&max_results=6"
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            xml = r.read().decode()
        out = []
        for m in re.finditer(r"<entry>.*?<title>(.*?)</title>.*?<id>(.*?)</id>.*?<summary>(.*?)</summary>", xml, re.S):
            t = htmlmod.unescape(re.sub(r"\s+"," ",m.group(1)).strip())
            s = htmlmod.unescape(re.sub(r"\s+"," ",m.group(3)).strip())
            out.append({"source":"arxiv","title":t,"url":m.group(2).strip(),"snippet":s[:300]})
        return out
    except Exception:
        return []

def stack(q):
    u = ("https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance"
         f"&q={urllib.parse.quote(q)}&site=stackoverflow&pagesize=6")
    d = fetch_json(u)
    return [{"source":"stackoverflow","title":h.get("title",""),"url":h.get("link",""),
             "snippet":f"score {h.get('score',0)} | {h.get('answer_count',0)} answers"}
            for h in d.get("items",[]) if isinstance(d, dict)]

def main():
    q = sys.argv[1].strip()
    t0 = time.time()
    sources = {"wikipedia": wiki, "duckduckgo": ddg, "hackernews": hn, "arxiv": arxiv, "stackoverflow": stack}
    aggregated, errors = [], {}
    for name, fn in sources.items():
        try:
            res = fn(q)
            aggregated.extend(res)
            if not res: errors[name] = "no results"
        except Exception as e:
            errors[name] = str(e)[:200]
    out = {
        "engine": "upe78-metasearch v1.0",
        "query": q,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "latency_s": round(time.time()-t0, 2),
        "total_results": len(aggregated),
        "results": aggregated,
        "source_errors": errors,
    }
    print(json.dumps(out, indent=2))
    with open("results.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
