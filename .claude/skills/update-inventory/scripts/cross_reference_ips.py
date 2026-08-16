#!/usr/bin/env python3
"""Find IPs mentioned in source-files/ that aren't in infra/inventory.json.

This is how the Azure "Core" VM (10.66.66.33) and the unnamed NFS-adjacent
gaps got found: scan every source doc for IPv4-looking tokens, then diff
against every IP already known (VM guest IPs, ESXi hosts). What's left is
either a real gap worth investigating, or a false positive (email header
timestamps like "08.13.06.44", mail relay IPs, version-number look-alikes
all show up this way — expect to eyeball the output, not trust it blindly).

Usage:
    cross_reference_ips.py [repo_root]

Defaults to the current directory. Reads infra/inventory.json and (if
present) cloud-infra/inventory-cloud.json, scans source-files/**/*.{txt,csv,eml,json}.
"""
import json
import re
import sys
import glob
import os

IP_RE = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')


def known_ips_from_inventory(path):
    ips = set()
    if not os.path.exists(path):
        return ips
    inv = json.load(open(path, encoding="utf-8"))
    for v in inv.get("vms", []):
        ips.update(v.get("ipv4", []))
        if v.get("esxi_host"):
            ips.add(v["esxi_host"])
    # catch any IP anywhere else in the JSON (azure blocks, blind_spots, etc.)
    ips.update(IP_RE.findall(json.dumps(inv)))
    return ips


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    known = known_ips_from_inventory(os.path.join(root, "infra", "inventory.json"))
    known |= known_ips_from_inventory(os.path.join(root, "cloud-infra", "inventory-cloud.json"))

    patterns = ["source-files/**/*.txt", "source-files/**/*.csv", "source-files/**/*.eml",
                "source-files/**/*.json", "cloud-infra/source/**/*.txt"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(root, p), recursive=True))

    hits = {}
    for f in files:
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for ip in IP_RE.findall(text):
            hits.setdefault(ip, set()).add(os.path.relpath(f, root))

    missing = {ip: srcs for ip, srcs in hits.items() if ip not in known}
    if not missing:
        print("No IPs found in source-files/ that aren't already in inventory.")
        return

    print(f"{len(missing)} IP(s) mentioned in source material but not in inventory.json:\n")
    for ip in sorted(missing):
        print(f"  {ip}  ->  {', '.join(sorted(missing[ip]))}")
    print("\nEyeball these — expect false positives (date fragments in email headers, "
          "mail relay IPs, subnet masks). Each real hit is worth a findings.md entry.")


if __name__ == "__main__":
    main()
