# VMs apagadas — detalle

Complementa [`informe_ejecutivo_infraestructura.md`](informe_ejecutivo_infraestructura.md). Fuente: `infra/inventory.json` (`power_state`), poblado desde `ExportList.csv` / `ExportList-Piedras-Full.csv`.

Del total de 144 VMs relevadas, **46 están apagadas**: 33 en el sitio principal y 13 en el sitio Piedras. Solo dos del sitio principal (`OpenRepo`, `OPENWLCLI01`) tienen una nota que explica por qué están apagadas — el resto es simplemente el estado que reporta el export, sin más contexto todavía.

## Sitio principal (33 VMs apagadas)

### Con nota que explica el apagado

- **`OpenRepo`** (`source_repo`): "en teoria no se usa mas x migracion a git" — repositorio de código legado, reemplazado por git.
- **`OPENWLCLI01`** (`weblogic_app`): "(se clonó de la 10.77.7.201) dejar apagada" — clon intencional de `OPENWLPROD01` (EBY/GIAR), no productivo.

### Estaciones / jumphosts de acceso personal (15)

Notas indican que eran accesos dedicados a personas puntuales, no infraestructura de cliente:

- `MAGUILERA-OPEN1`, `MAGUILERA-OPEN2`, `MAGUILERA-OPEN3` — nota: "Acceso a Mario Aguilera"
- `MARCO-OPEN1`, `MARCO-OPEN2`, `MARCO-OPEN3` — nota: "Virtual Florencia de Victor"
- `OPEN1`, `OPEN2`, `OPEN3` — nota: "Virtual OPENx con W7 remota para uso en caso de que VMs..."
- `OPEN1-W10`, `OPEN2-W10`, `OPEN3-W10` — sin nota adicional
- `COCO ORT` — nota: "PRESTADA A COCO PARA CONEXIÓN A ORT"
- `OPENCLIRDP02`, `OPENCLIVPN02`, `OPENCLIVPN03`, `OPENCLIVPN04` — sin nota adicional

### Bases de datos (6)

- `Database 12c .17` — nota menciona ERP/TABLEROERP
- `DB-ARGOCEAN` — DB del cliente Argocean; su WebLogic asociado (`WL-CLIENTES`) también aparece deshabilitado en NPM — el stack completo de ese cliente parece apagado
- `DB-TEST`
- `OL8DBMULTI01`
- `OPENORACLEDB02` — nota menciona `PDBOPENWL12PROD01`
- `OPENSYTDB01`

### WebLogic (2)

- **`OPENWLPROD001`** — nota: "ORIG de los openwl01X" — sugiere ser el origen de una cadena de clones (posiblemente el original del que se clonó `OPENWLCLI01`, aunque ese apunta explícitamente a `OPENWLPROD01`/`10.77.7.201`, no a este).
- **`OPENWLPROD02`** — nota contiene el mismo fragmento "test weblogix simple licence. 12.2.1.19 y db 23ia" ya visto en `PiedrasWL01` y en la nota de `OPENWLCLI01` — mismo patrón de contaminación de la columna Notas entre VMs no relacionadas, documentado en `infra/findings.md`. No tratar como dato propio de esta VM sin confirmar.

### Otras (5)

- **`VM_FW`** (`firewall_candidate_pfsense`) — uno de los 2 candidatos a pfSense todavía sin confirmar (el otro, `OPENFWCLI02`, está encendido).
- **`OPENDOCKER03`** (`docker_host_confirmed`) — host Docker, apagado al momento de este export.
- `DEV12C` (`unclear`) — nota: "usa desarrollo para modificar forms"
- `MICRO` (`unclear`) — nota: "lo usa angie"
- `openbackend01` (`unclear`)
- `OpenDevServices` (`unclear`)

## Sitio Piedras (13 de 15 VMs apagadas)

Detalle completo en `infra/topology.md` §3. Apagadas: `OpenPiedrasFw01` (candidato a pfSense del sitio), `PiedrasDB01`, `PiedrasWL01` (nota propia: WebLogic de prueba/licencia, no productivo), `weblogic14C01`, `OPENDB_31`, `OPENDBRMAN`, `OPENSHARE`, `OPENAPPS`, `COBRA`, `CLIENTESRDP`, `OEM`, `OPENMONITOR10`, `OPEN_GRAFANA`. Encendidas: `Win10-Piedras`, `DC2`.

## Nota de método

Ninguna de las VMs listadas arriba (salvo `OpenRepo` y `OPENWLCLI01`) tiene confirmación por TeamViewer de que su apagado sea definitivo o de qué rol cumplía — es el estado tal como lo reporta el export de vCenter en el momento del snapshot. No tratar "apagada" como sinónimo de "en desuso" sin ese contexto adicional.
