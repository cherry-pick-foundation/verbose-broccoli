"""Print every JSON document in an Orca check output file (they may be concatenated)."""
import json, sys
text = open(sys.argv[1]).read()
dec = json.JSONDecoder(); i = 0
while i < len(text):
    while i < len(text) and text[i].isspace(): i += 1
    if i >= len(text): break
    try:
        d, i = dec.raw_decode(text, i)
    except json.JSONDecodeError:
        break
    if d.get("_keepalive"): continue
    r = d.get("result", d)
    print("delivery", r.get("deliveryId"), "timedOut", r.get("timedOut"), "ack", r.get("acknowledged"), "error", d.get("error"))
    for m in r.get("messages", []):
        print("---", m["id"], m["type"], m["subject"], m["from_handle"])
        print(m["body"][:int(sys.argv[2]) if len(sys.argv) > 2 else 5000])
