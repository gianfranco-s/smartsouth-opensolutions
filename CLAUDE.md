# opensolutions infra takeover

This is not a software project. It's a working directory for mapping the infrastructure of a
new client (Open Solutions / the CONDOR product ecosystem) we're taking over with very little
prior knowledge. There is no programmatic access to the on-premise hosts — all hands-on
investigation happens through TeamViewer. Azure is a separate, cloud-managed plane (see below).
This repo exists to build and maintain a single accurate picture of what's actually out there,
iteratively, over many sessions.

## Data sources — know which is which, and treat research material with a grain of salt

All source material lives in `source-files/`. Two tiers of trust:

- **`source-files/ExportList.csv`** — a raw export from vCenter (VMware vSphere). The closest
  thing we have to ground truth for the on-premise side: every VM that exists, power state, ESXi
  host, disk, guest OS as reported by VMware tools, and IP addresses. It only knows what the
  hypervisor knows — nothing about what's actually running inside a VM.
- **Everything else is internal working documentation, not verified ground truth** — a manually
  compiled CSV, forwarded internal emails, and documents an internal team produced while doing
  the same kind of discovery we're doing now. Cross-check every claim against ExportList.csv (or
  TeamViewer) before acting on it:
  - **`source-files/Relevamiento (sin claves) - VM Linux.csv`** — manually compiled, maps 13
    known clients to WebLogic/DB servers only. Known incomplete (only tracks one WL+one DB per
    client — see `infra/findings.md`) and known to contain at least one stale entry. The original
    file had plaintext admin credentials in a trailing column; stripped before this file was
    tracked in git.
  - **`source-files/*.eml`** — two forwarded internal emails (real Smart South / Open Solutions
    employee names and addresses in the headers). One reports early Nginx Proxy Manager findings;
    the other delivers a RAR of internal documentation.
  - **`source-files/extracted/`** — plain-text/JSON extractions from the RAR attachment (it's not
    re-extractable without a RAR tool, so the useful content was pulled out once and saved here):
    a richer **client-services matrix** (`matriz_servicios_por_cliente.json` — SIDs, DB
    versions, which Condor products each client uses, and the source team's own **Discrepancias**
    sheet where two of their internal data sources disagreed and neither was picked over the
    other), a **Docker infrastructure survey** (`relevamiento_docker.txt` — per-host container
    inventory, this is what resolved the nginx question, see findings.md), an **Azure
    architecture analysis** (`analisis_azure.txt` — subscriptions, AKS, VNets, VPN), a hosting
    service spec, and a product/business overview of the CONDOR ecosystem.
  - The matrix itself documents client churn (two of the original 13 clients are already
    decommissioned) — treat any status claim about a specific client as needing reconfirmation,
    not as current fact.
  - **Never re-add credentials to any tracked file.** If new source material includes them, strip
    before committing, same as was done for the Relevamiento CSV.

## What's in `infra/`

- **`inventory.json`** — the single source of truth for the on-premise side, plus a separate
  `azure` section for the cloud side (see below). All 129 VMs from ExportList.csv, each tagged
  with a `category` (confidence varies — several are now **confirmed** via the RAR material,
  most are still name-based guesses — see `infra/topology.md` §3 for the breakdown) and, for VMs
  referenced by a client, resolved links back to `clients[]`. 15 client records (13 from the
  original CSV + 2 found only in the richer matrix: Rex Argentina, Argocean), each with
  `weblogic`/`database` blocks showing what was *claimed* vs. what actually `resolved` against
  ExportList.csv (`resolved_by` shows name vs. IP match, `match: false` flags a stale name), plus
  a `matrix_detail` block for clients covered by the richer matrix. Docker hosts carry a
  `docker_detail` block with real per-container service inventory.
- **`topology.md`** — generated views: a Mermaid diagram of the client → WebLogic → DB mapping
  (on-premise), a second Mermaid diagram of the Azure/AKS topology (cloud), a category breakdown
  table, and ESXi host/cluster notes.
- **`findings.md`** — the payoff of cross-referencing everything: what's now confirmed (pfsense
  identity, nginx's real location, the Argocean client), what's newly discovered (2 extra
  clients, 2 decommissioned clients, the source team's own unresolved discrepancies), and what's
  still open. Read this first if you're new to the project — it's the prioritized list of what to
  verify next over TeamViewer or the Azure portal.

## Two separate infra planes — don't conflate them

1. **On-premise vSphere** (ExportList.csv + most of `infra/`) — accessed via TeamViewer, no API.
2. **Azure/AKS** (`inventory.json` → `azure`, `topology.md` §2) — where the Condor Work,
   Enterprise, and ProvIA application tiers actually run, as containers on AKS. Managed via the
   Azure portal/CLI, not TeamViewer. Connected to the on-premise side by a single Site-to-Site
   VPN terminating at `OPENVPNFW01` (confirmed pfSense). A VM name like `WL12C-PROD` existing in
   ExportList.csv does **not** mean that client's application logic runs there — check
   `matrix_detail.productos` and the Azure doc before assuming on-prem-only.

## How the categorization works (and its limits)

VM `category` in inventory.json started as regex over the VM *name* and vCenter's self-reported
guest OS — a hypothesis, not a fact. Several categories have since been upgraded to confirmed via
the RAR material (docker host container contents, one pfsense box confirmed by VPN peer IP). The
rest are still guesses pending TeamViewer verification. Don't let a category label read as more
certain than it is; when in doubt, open `findings.md`.

## Keeping this updated

This is a living map, not a one-time export. As TeamViewer/Azure-portal sessions confirm facts,
or new source material arrives:

1. Edit `infra/inventory.json` directly — flip a `category` from guess to confirmed, fill in
   `used_by_clients`, add a `notes` field, etc.
2. If the client-mapping diagram in `topology.md` §1 changes (a client's WL/DB reassigned, a new
   client added), regenerate it from the updated JSON rather than hand-editing the Mermaid — walk
   `clients[]`, one node per client and one per distinct resolved VM, dedupe, wire client→WL→DB.
   Keep it scoped to the client subset; a full 129-node diagram isn't readable. The Azure diagram
   (§2) is hand-maintained since it's a small, stable set of named resources — edit it directly.
3. If a genuinely new export or document lands, re-run the cross-reference (name match, fall back
   to IP match) rather than hand-merging — that's what caught the stale entries and the IP-only
   matches so far. New RAR/zip attachments: extract with `unar` (installed via Homebrew), pull
   plain text out of `.docx`/`.xlsx` (they're zipped XML — no extra dependencies needed, see the
   extraction approach already used for `source-files/extracted/`), and save the extracted text/
   JSON into `source-files/extracted/` rather than leaving it only in the archive.
4. When a finding in `findings.md` gets resolved, move it to a "Resolved" section with a date
   instead of leaving stale open questions next to live ones (see the current file for the
   pattern).

## Security

- Never commit credentials of any kind. If you're about to write a password into a tracked file,
  stop and ask first.
- This is a **private** GitHub repo (`git@github.com:gianfranco-s/smartsouth-opensolutions.git`).
  Raw source material (CSVs, emails, extracted docs) is committed intentionally, on the basis
  that the repo stays private — don't make it public, and don't copy this material elsewhere
  without the same care.
- Never push without being explicitly asked to, even though a remote is configured.
