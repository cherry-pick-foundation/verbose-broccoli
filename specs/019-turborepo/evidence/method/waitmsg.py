"""Wait for a non-heartbeat Orca message; acknowledge heartbeat-only deliveries."""
import json, subprocess, sys, time
RUN = "run_d06084761156"
OUT = sys.argv[1]
deadline = time.time() + float(sys.argv[2] if len(sys.argv) > 2 else 1800)
dec = json.JSONDecoder()
while time.time() < deadline:
    p = subprocess.run(["orca-ide", "orchestration", "check", "--run", RUN, "--wait", "--types",
                        "worker_done,escalation,question", "--timeout-ms", "600000", "--json"],
                       capture_output=True, text=True, cwd="/home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo")
    text = p.stdout; i = 0; docs = []
    while i < len(text):
        while i < len(text) and text[i].isspace(): i += 1
        if i >= len(text): break
        try:
            d, i = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            break
        if not d.get("_keepalive"): docs.append(d)
    real = False
    for d in docs:
        r = d.get("result", d)
        msgs = r.get("messages", [])
        if any(m["type"] != "heartbeat" for m in msgs):
            real = True
        elif r.get("deliveryId"):
            subprocess.run(["orca-ide", "orchestration", "check", "--ack", r["deliveryId"], "--json"], capture_output=True,
                           cwd="/home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo")
    if real:
        open(OUT, "w").write(text)
        print("message"); sys.exit(0)
    time.sleep(5)
print("timeout")
