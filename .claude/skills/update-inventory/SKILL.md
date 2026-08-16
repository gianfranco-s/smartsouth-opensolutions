---
name: update-inventory
description: Update this project's infra inventory when new source material arrives (a CSV, a forwarded email, a RAR/zip attachment full of docs). Use whenever source-files/ gains a new file, or when re-verifying inventory.json against everything already there.
---

# Updating the infra inventory

This project (`opensolutions` infra takeover) maintains `infra/inventory.json` as the single
source of truth for on-premise infrastructure, generated views in `infra/topology.md`, and a
prioritized gap list in `infra/findings.md`. See `CLAUDE.md` at the repo root for the full data
model and conventions — this skill covers the mechanical steps of extending it, so you don't
re-derive the same parsing code from scratch each session.

**Scope reminder:** this discovery is currently on-premise only. Cloud-provider findings (Azure,
AWS) go to `cloud-infra/`, not `infra/` — see `cloud-infra/README.md`.

## When new source material lands

1. **Plain CSV/text**: read it directly, no tooling needed.
2. **A new `.docx` or `.xlsx`** (e.g. delivered as an email attachment): extract it with
   `scripts/extract_office_doc.py <file> [output]`. Both formats are zipped XML — this needs no
   installed dependencies (no python-docx/openpyxl). Save the output into
   `source-files/extracted/` (or `cloud-infra/source/` if it's cloud-specific) rather than
   leaving it only accessible by re-running the script.
3. **A `.rar` or `.zip` attachment**: extract with `unar` first (`brew install unar` if not
   already installed — check with `which unar` before installing). Then run step 2 on whatever
   Office docs come out of it.
4. **Read what you extracted** and decide what's new. This part isn't scriptable — deciding
   "this describes a previously-unknown VM" or "this contradicts an existing client record"
   takes judgment, the same way the Azure Core VM and the Piedras firewall trace were found by
   reading, not by a script.

## Checking for infrastructure not yet in the inventory

Run `scripts/cross_reference_ips.py` from the repo root. It scans everything under
`source-files/` (and `cloud-infra/source/`) for IPv4-looking tokens and diffs them against every
IP already in `infra/inventory.json` and `cloud-infra/inventory-cloud.json`. This is exactly how
the standalone Azure "Core" VM (`10.66.66.33`) got found — it was named in a doc but had never
been logged as a resource anywhere.

**Expect false positives** and triage the output by hand: email header timestamps parse as
IP-like tokens (e.g. `08.13.06.44`), mail relay IPs show up, and ESXi host IPs will look
"missing" if you run this before the script's own known-IP collection picks them up (it does, by
default — but double check if you fork this for a new field). Every real hit is worth a line in
`infra/findings.md`, not just a JSON edit — explain what it is and where it came from.

## Regenerating the client → WebLogic → DB diagram

`infra/topology.md` §1 has a Mermaid diagram generated from `clients[]` in inventory.json — never
hand-edit it. After changing `inventory.json`, run:

```
python3 .claude/skills/update-inventory/scripts/gen_client_diagram.py infra/inventory.json
```

and paste the output block over the existing one in `topology.md`. It only regenerates the
diagram itself — re-read the surrounding prose (client count, decommission flags, caveats) and
update it by hand if it no longer matches.

## Formatting convention: one line per paragraph

This project keeps markdown files unwrapped — every paragraph and bullet is a single source
line (no manual mid-paragraph line breaks), so diffs stay clean. Fenced code blocks (including
Mermaid diagrams) and table rows are exempt. After editing any `.md` file by hand, run:

```
python3 .claude/skills/update-inventory/scripts/unwrap_md.py path/to/file.md [more files...]
```

## Before committing

- Never commit credentials. If new source material has a password column, verify it's actually
  empty before adding the file — don't assume from the filename (`Relevamiento (sin claves)...`
  turned out to have no credentials in the firewall CSV, but the original VM-mapping CSV did, and
  needed stripping).
- Validate JSON after every edit: `python3 -c "import json; json.load(open('infra/inventory.json'))"`.
- Move resolved items in `infra/findings.md` to a "Resueltos" section instead of deleting them.
- This is a private repo with a configured remote — commit freely, but never push without being
  explicitly asked.
