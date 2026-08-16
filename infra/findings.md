# Findings & open questions

Sources: ExportList.csv (vCenter export, ground truth for "what VM exists"), Relevamiento CSV
(manual, 13 clients, WL+DB only), and — added later — two internal emails plus their RAR
attachment (`source-files/extracted/`), containing a richer client-services matrix, a Docker
infrastructure survey, and an Azure architecture analysis. **All Relevamiento-derived and email
material is internal working documentation, not verified ground truth — treat every finding
below with the same grain-of-salt the source documents themselves apply** (the matrix's own
"Discrepancias" sheet exists because Open's own team found their two data sources disagreeing).

## Resolved / confirmed

**nginx — resolved.** `Relevamiento_general_infraestructura_Docker_actualizado.docx` confirms
Nginx Proxy Manager runs as a container on 4 of the 9 docker hosts: `DOCKER-DEB`, `OPENDOCKER04`,
`VM-DOCKER-Clientes`, and `VM-DOCKER-Clientes (1)`. It's not a dedicated host category — it's a
containerized service. The earlier `web_frontend_nginx_candidate` guess (`OPENPORTAL01`,
`OPENPORTALCLI02`, `WEBSERVER`) was wrong; those VMs' actual role is still unconfirmed.

**pfsense — confirmed for at least one host.** `Analisis Azure.docx` documents Azure's
Site-to-Site VPN to the on-premise datacenter, explicitly naming the peer as "pfSense" at
`200.55.243.92`. That IP belongs to `OPENVPNFW01` in ExportList.csv — direct confirmation, not
just a FreeBSD-guest-OS guess. The other 8 `firewall_candidate_pfsense` VMs are still unconfirmed
guesses.

**`DB-ARGOCEAN` — resolved.** It's the database for a client called **Argocean**, per the
matrix's Discrepancias sheet ("DB 172.18.5.60 / SID MBA — No figura [en tabla funcional]").
Argocean isn't in the original 13-client list at all — it surfaced only in the discrepancy notes.
The VM is currently powered off in ExportList.csv, and no WebLogic server has been identified
for it yet.

## New: the "13 clients" is more like 15, with churn

The matrix (`Matriz_servicios_por_cliente_Hosting_V2.xlsx`) adds two clients not in the
Relevamiento CSV:

- **Rex Argentina** (code `279`) — "recently onboarded to hosting", PROD environment, uses
  Condor Work, DB referred to only as "REX Produccion" (not yet resolved to a specific VM —
  needs a TeamViewer lookup, ~15 users / 4,600 legajos per the matrix notes).
- **Argocean** — see above, DB-only so far, no WebLogic identified.

More importantly: **the matrix states ABB S.A. and Arris de Argentina S.A. (GIAR) are already
decommissioned clients** ("de baja"), with their databases retained temporarily only. That
changes their priority for a takeover — worth confirming this is still current before treating
either as a live production client. (Both are `used_by_clients` in inventory.json regardless,
since their VMs still exist and are powered on.)

## New: the matrix documents its own unresolved discrepancies

The matrix's "Discrepancias" sheet is Open's own team catching conflicts between a "funcional"
source (from a person named Fran) and the "técnico" inventory — worth carrying forward as-is
rather than re-deriving:

| Client | Issue | Functional says | Technical inventory says |
|---|---|---|---|
| GIAR | WebLogic version | WL 11 | 12.2 |
| ROMAN (CSM) | WebLogic version | WL 11 | 10 |
| JOBS | WebLogic version | WL 12 | 11 |
| ABB | Current DB | `192.1.1.31` / SID ABB | `192.1.1.31` and `192.1.1.190` (two IPs) |
| CEFAS | SID | CEFASPDB | CEFAS |
| BOCA | SID | BOCAPDB | BOCA |
| EBY | WebLogic server | destination `10.77.7.201` | actual, shared: `192.1.2.54` |
| Enerflex | Charset | `WE8ISO8859P15` | unverified — flagged as possibly mistyped |

The document explicitly did **not** pick one value over the other when sources disagreed — same
policy this project should follow. See `clients[].matrix_detail` in inventory.json for the full
per-client detail (SID, DB version/edition/size/charset, migration destination, which Condor
products each client uses).

## Still open

### 1. Relevamiento's WL+DB-only scope means absence ≠ new client

(See prior analysis, still holds.) Only 2 of 13 original clients show a naming hit for
additional undocumented infra: **GIAR** has an extra `WL-GIAR` instance beyond its mapped
`OPENWLPROD01`/`DB-GIAR`, and **ROMAN** has an extra `WL-ROMAN` and `DB-ROMAN-HISTORICO` beyond
its mapped `WL-CLIENTES`/`DB-ROMAN`. ~31 more WL/DB-pattern VMs carry no client-code substring at
all and still need a TeamViewer pass to classify as: another component of a known client, a
dev/QA/test copy, or a genuinely separate client (as Argocean turned out to be).

### 2. Two unresolved Relevamiento rows outside the 13 clients — one now explained

`opendocker03`'s claimed IP (`192.1.1.113`) doesn't appear in ExportList.csv — but that's
explained now: `OPENDOCKER03` is powered off ("Apagado") in the export, and vCenter only reports
a guest's IPs when VMware Tools is running. The Docker survey doc independently confirms
`OPENDOCKER03` is at `192.1.1.113` (Ubuntu 22.04, 1 active container — Portainer), so the
Relevamiento entry is correct; ExportList.csv just couldn't see it at capture time because the VM
was off. `portalDM` (IP `10.77.10.5`) likely = `OPENPORTAL01` (same IP) but still unconfirmed.

### 3. Second ESXi host (`192.1.3.252`) — likely separate site

Still unconfirmed whether this is a second physical location or a standalone box; hosts
GIAR's and ROMAN's non-`192.1.1.x` infrastructure.

### 4. Azure network has no internal segmentation (security finding, not just a mapping gap)

Both the prod and dev/test AKS environments in Azure use a single flat subnet for app traffic,
VPN, and internet-facing services — no NSGs, no Azure Firewall, no Private Endpoints. Worth
flagging to whoever owns security posture for this client, independent of the infra-mapping work.

## Suggested next TeamViewer / Azure-portal pass (priority order)

1. Confirm ABB and GIAR's decommissioned status before deprioritizing their environments.
2. Resolve Rex Argentina's DB VM identity — it's a current PROD client with no VM mapped yet.
3. Walk the remaining 8 `firewall_candidate_pfsense` VMs to confirm/deny pfsense, now that one
   (`OPENVPNFW01`) is confirmed — the others may share config.
4. Walk the 12 `infra_generic_unclear` (`OPENINFRxx`) VMs — no naming signal at all.
5. For the ~31 still-unmapped WL/DB-pattern VMs, classify each as prod-for-an-undocumented-client
   vs. dev/QA/test/historical vs. component of a known client.
6. Confirm the real role of `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER` now that the nginx
   guess for them is known to be wrong.
