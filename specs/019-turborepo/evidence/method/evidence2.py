import json, collections, re
S = "/tmp/claude-1000/-home-choi-eunchang-workspaces-verbose-broccoli-feature-turborepo/ca64935e-e9f7-4ed8-9107-8675f8f79090/scratchpad"
E = "/home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo/specs/019-turborepo/evidence"
batches = [("20", "sites2/items_full.json", "classify/classify_20.json", "classify/context20.txt"),
           ("21", "sites2/items21.json", "classify/classify_21.json", "classify/context20.txt"),
           ("22", "sites2/items22.json", "classify/classify_22.json", "classify/context20.txt"),
           ("23", "sites2/items23.json", "classify/classify_23.json", "classify/context20.txt")]
extra = [(b, i, r) for b, i, r, c in json.load(open(f"{S}/extra_batches.json"))] if False else []
user_rule = {"X099", "X107", "X140", "X120", "X129"}
out = {"tool": "backfire_classify", "date": "2026-09-29", "purpose": "Select the change sites for removing Deno completely from this repository after the develop merge; only must_change and delete sites will be edited.",
       "classes": json.load(open(f"{S}/classify/classes.json")), "batches": [],
       "user_rule": {"rows": sorted(user_rule), "rule": "The user's decision of 2026-09-29, relayed by develop-bf: remove Deno completely; no deno.json, deno.lock, plugins/code/deno.json, @deno/shim-deno or other Deno-API shim, no Deno in doctor, orca.yaml or the GitHub workflows. Applied to rows whose re-asked classification stayed 'review'."}}
rows = {}
for n, ip, rp, cp in batches:
    items = json.load(open(f"{S}/{ip}")); res = json.load(open(f"{S}/{rp}"))
    out["batches"].append({"batch": n, "context": open(f"{S}/{cp}").read(), "items": items, "results": res})
    for it in items:
        base = re.sub(r"#(ctx|t\d+)$", "", it["id"])
        rows[base] = (it if base == it["id"] else rows.get(base, (it,))[0], res[it["id"]], n)
json.dump(out, open(f"{E}/classify-full-removal.json", "w"), indent=1, ensure_ascii=False)
sel = lambda r: r["classification"] in ("must_change", "delete") and r["decision"] == "auto"
by = collections.defaultdict(list); counts = collections.Counter()
for k, (it, r, n) in rows.items():
    tag = "SELECT" if sel(r) else ("SELECT(user rule)" if k in user_rule else "leave")
    counts[tag] += 1
    by[it["file"]].append((tag, k, it, r))
body = []
for f in sorted(by):
    body += [f"## `{f}`", ""]
    for tag, k, it, r in sorted(by[f], key=lambda x: (x[0] == "leave", x[1])):
        ls = it["lines"]; lt = ",".join(map(str, ls[:40])) + ("…" if len(ls) > 40 else "")
        body.append(f"- {tag} `{k}` {it['kind']}: {r['classification']} ({r['decision']}, {r['confidence']:.2f}); lines {lt}")
    body.append("")
head = ["# Selected change sites: full Deno removal", "",
        "Generated on 2026-09-29 from [classify-full-removal.json](classify-full-removal.json), the classification of the merged tree (after `develop` 8ce9b2a) for removing Deno completely. SELECT means must_change or delete with an `auto` decision. Rows re-asked with their file context (batch 21) replace their first result. `SELECT(user rule)` rows stayed `review` after the re-ask and are selected by the user's rule instead (see `user_rule` in the JSON). `leave` rows stay unchanged.", "",
        "Counts: " + "; ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + f" (total {sum(counts.values())}).", ""]
open(f"{E}/selected-sites-full-removal.md", "w").write("\n".join(head + body))
print(counts)
