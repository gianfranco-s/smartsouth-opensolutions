#!/usr/bin/env python3
"""Regenerate the client -> WebLogic -> DB Mermaid diagram from inventory.json.

Prints a ```mermaid fenced block to stdout, ready to paste into
infra/topology.md section 1. Does not edit topology.md directly — the
surrounding prose (client count, caveats) needs a human/agent read after
inventory.json changes, so this only regenerates the diagram body.

Usage:
    gen_client_diagram.py [path/to/inventory.json]
"""
import json
import sys


def sid(s):
    return "n_" + "".join(c if c.isalnum() else "_" for c in s)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "infra/inventory.json"
    inv = json.load(open(path, encoding="utf-8"))

    lines = ["```mermaid", "flowchart LR"]
    seen_wl, seen_db = set(), set()

    for c in inv["clients"]:
        label = c.get("code") or c["name"][:12]
        cid = sid(label)
        status_note = "<br/><i>DADA DE BAJA</i>" if c.get("status_note") else ""
        lines.append(f'  {cid}["{c["name"]}<br/>({label}){status_note}"]')

        for m in c["weblogic"]["resolved"]:
            if m["resolved_vm"]:
                wid = sid(m["resolved_vm"])
                if wid not in seen_wl:
                    lines.append(f'  {wid}["WL: {m["resolved_vm"]}"]')
                    seen_wl.add(wid)
                lines.append(f'  {cid} --> {wid}')

        for m in c["database"]["resolved"]:
            if m["resolved_vm"]:
                did = sid(m["resolved_vm"])
                if did not in seen_db:
                    lines.append(f'  {did}[("DB: {m["resolved_vm"]}")]')
                    seen_db.add(did)
                wl_ids = [sid(m2["resolved_vm"]) for m2 in c["weblogic"]["resolved"] if m2["resolved_vm"]]
                if wl_ids:
                    lines.append(f'  {wl_ids[0]} --> {did}')
                else:
                    lines.append(f'  {cid} --> {did}')

        if not c["weblogic"]["resolved"] and not c["database"]["resolved"]:
            lines.append(f'  {cid} -.->|"servidor todavía sin identificar"| unknown_{cid}((?))')

    lines.append("```")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
