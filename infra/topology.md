# Topología de infraestructura (vistas generadas)

Generado a partir de [`inventory.json`](inventory.json). No editar los diagramas de abajo a mano — regenerarlos desde el JSON (ver CLAUDE.md) cada vez que el JSON cambie, para que nunca queden desincronizados.

**Alcance: solo on-premise (vSphere).** La infraestructura en proveedores cloud (Azure/AWS) se estacionó fuera del alcance de este relevamiento — ver [../cloud-infra/README.md](../cloud-infra/README.md) para lo que ya se había encontrado ahí antes de acotar el foco.

## 1. Mapeo Cliente → WebLogic → Base de datos (vSphere on-premise)

Construido resolviendo los servidores WebLogic/DB declarados de cada cliente (del CSV de Relevamiento y, donde hay más detalle, de la matriz de clientes `Matriz_servicios_por_cliente_Hosting_V2.xlsx`) contra el inventario real de VMs en ExportList.csv — matcheado por nombre, y si el nombre no coincide, por IP (ver `resolved_by` en el JSON). 15 clientes en total: los 13 del CSV original de Relevamiento, más **Rex Argentina** y **Argocean**, ambos encontrados solo en la matriz más completa (ver findings.md). **ABB y Arris/GIAR están marcados en la matriz como ya dados de baja** — se mantienen en el diagrama porque sus VMs todavía existen y corren, pero no tratarlos como producción activa sin confirmar el estado actual.

Prestar atención a las instancias compartidas: varios clientes están en la *misma* VM de WebLogic y/o la misma VM de base de datos — es un dato de radio de impacto que conviene saber antes de tocar cualquiera de ellas.

```mermaid
flowchart LR
  n_ABB["ABB S.A.<br/>(ABB)<br/><i>DADA DE BAJA</i>"]
  n_WL12C_Desarrollo_2_54["WL: WL12C-Desarrollo.2.54"]
  n_ABB --> n_WL12C_Desarrollo_2_54
  n_DBClientes_12C_31[("DB: DBClientes-12C.31")]
  n_WL12C_Desarrollo_2_54 --> n_DBClientes_12C_31
  n_DBClientes_190[("DB: DBClientes.190")]
  n_WL12C_Desarrollo_2_54 --> n_DBClientes_190
  n_GIAR["Arris de Argentina S.A.<br/>(GIAR)<br/><i>DADA DE BAJA</i>"]
  n_OPENWLPROD01["WL: OPENWLPROD01"]
  n_GIAR --> n_OPENWLPROD01
  n_DB_GIAR[("DB: DB-GIAR")]
  n_OPENWLPROD01 --> n_DB_GIAR
  n_CEFAS["Cefas S.A.<br/>(CEFAS)"]
  n_WebLogic_191["WL: WebLogic.191"]
  n_CEFAS --> n_WebLogic_191
  n_CLIENTES_DB[("DB: CLIENTES-DB")]
  n_WebLogic_191 --> n_CLIENTES_DB
  n_BOCA["Club Atlético Boca Juniors<br/>(BOCA)"]
  n_BOCA --> n_WL12C_Desarrollo_2_54
  n_WL12C_Desarrollo_2_54 --> n_CLIENTES_DB
  n_ROMAN["CSM Ciencia al Servicio del Movimiento S.A.<br/>(ROMAN)"]
  n_WL_CLIENTES["WL: WL-CLIENTES"]
  n_ROMAN --> n_WL_CLIENTES
  n_DB_ROMAN[("DB: DB-ROMAN")]
  n_WL_CLIENTES --> n_DB_ROMAN
  n_DCVIAJES["DC Viajes y Turismo S.A.<br/>(DCVIAJES)"]
  n_DCVIAJES --> n_WebLogic_191
  n_WebLogic_191 --> n_DBClientes_190
  n_DVAL["Dominique Val S.A.<br/>(DVAL)"]
  n_DVAL --> n_WebLogic_191
  n_DBClientes_238[("DB: DBClientes.238")]
  n_WebLogic_191 --> n_DBClientes_238
  n_ENERFLEX["Enerflex Solutions Argentina SRL<br/>(ENERFLEX)"]
  n_WL12C_PROD["WL: WL12C-PROD"]
  n_ENERFLEX --> n_WL12C_PROD
  n_CLIENTES_DB2[("DB: CLIENTES-DB2")]
  n_WL12C_PROD --> n_CLIENTES_DB2
  n_ESYOP["Ente Servicios y Obras Públicas (ESYOP)<br/>(ESYOP)"]
  n_WebLogic_19["WL: WebLogic.19"]
  n_ESYOP --> n_WebLogic_19
  n_WebLogic_19 --> n_DBClientes_12C_31
  n_EBY["Entidad Binacional Yacyretá<br/>(EBY)"]
  n_EBY --> n_WL12C_Desarrollo_2_54
  n_OPENDBPROD006[("DB: OPENDBPROD006")]
  n_WL12C_Desarrollo_2_54 --> n_OPENDBPROD006
  n_JOBS["Jobs Servicios de Recursos Humanos SRL<br/>(JOBS)"]
  n_JOBS --> n_WL12C_PROD
  n_WL12C_PROD --> n_CLIENTES_DB2
  n_HEINLEIN["Heinlein<br/>(HEINLEIN)"]
  n_OL8LABWL01["WL: OL8LABWL01"]
  n_HEINLEIN --> n_OL8LABWL01
  n_OPENDBPROD001[("DB: OPENDBPROD001")]
  n_OL8LABWL01 --> n_OPENDBPROD001
  n_MAIPU["Maipú<br/>(MAIPU)"]
  n_DMWL01["WL: DMWL01"]
  n_MAIPU --> n_DMWL01
  n_DASADBPROD01[("DB: DASADBPROD01")]
  n_DMWL01 --> n_DASADBPROD01
  n_279["Rex Argentina<br/>(279)"]
  n_279 -.->|"servidor todavía sin identificar"| unknown_n_279((?))
  n_Argocean["Argocean<br/>(Argocean)"]
  n_DB_ARGOCEAN[("DB: DB-ARGOCEAN")]
  n_Argocean --> n_DB_ARGOCEAN
```

**Leer este diagrama con cuidado — un nodo es engañoso:** `WL12C-Desarrollo.2.54 → DBClientes.190` y `WebLogic.191 → DBClientes.190` aparecen ambos porque ABB y DCVIAJES se resolvieron cada uno por separado; no significa que ABB y DCVIAJES compartan una instancia de WebLogic. Verificar contra `clients[].database.resolved` en el JSON antes de asumir que una flecha implica un WL compartido.

> La topología Azure/AKS que estaba acá se movió a [`../cloud-infra/topology-cloud.md`](../cloud-infra/topology-cloud.md) — infraestructura cloud fuera de alcance por ahora, ver [`../cloud-infra/README.md`](../cloud-infra/README.md).

## 2. Inventario de VMs por categoría (las 129 VMs del sitio principal, de ExportList.csv)

Solo los totales — ver `inventory.json` → `vms[].category` para la lista de miembros de cada grupo. Las categorías se asignaron por coincidencia de nombre/SO salvo que se indique lo contrario por confirmación vía el material de los emails/RAR (ver findings.md para qué está confirmado y qué sigue siendo conjetura). Acotado al sitio principal — las 15 VMs del sitio Piedras (`vms[].site == "Piedras"`) tienen su propia tabla en la §3 de abajo, tanto por ser un cluster/host separado como por venir de un export distinto (`ExportList-Piedras-Full.csv`).

| Categoría | Cantidad | Confianza |
|---|---|---|
| database | 30 | Mixta — varias confirmadas vía el mapeo de clientes, el resto inferidas solo por nombre |
| weblogic_app | 18 | Mixta — varias confirmadas vía el mapeo de clientes, el resto inferidas solo por nombre |
| workstation_or_jumphost | 20 | Inferida (SO invitado Windows 7/10 + nombre) |
| infra_generic_unclear | 12 | Desconocida — el nombre genérico `OPENINFRxx` no dice nada sobre el rol |
| docker_host_confirmed / docker_host_confirmed_nginx_proxy_manager | 9 | **Confirmada** — detalle a nivel contenedor del relevamiento de Docker, incl. cuáles 4 corren Nginx Proxy Manager |
| firewall_confirmed_pfsense | 1 (`OPENVPNFW01`) | **Confirmada** vía coincidencia de IP con el peer de VPN de Azure |
| firewall_candidate_pfsense | 8 | Inferida (SO invitado FreeBSD + nombre con fw/vpn), todavía sin confirmar |
| unclear | 17 | Sin señal en el nombre, o una conjetura previa (candidato a nginx) que resultó incorrecta |
| bi_reporting | 4 | Inferida (Jasper/MicroStrategy en el nombre) |
| backup | 2 | Inferida (Veeam en el nombre) |
| source_repo | 2 | Inferida (SVN en el nombre) |
| domain_controller, file_server, monitoring, mail, storage_nas, virtualization_mgmt | 1 cada una | Inferida por nombre/SO |

## 3. Hosts / clusters ESXi

13 IPs de host ESXi en total, entre `ExportList.csv` (sitio principal) y `ExportList-Piedras-Full.csv` (sitio Piedras, confirmado el 18 ago 2026 — ver abajo):

- **192.1.1.214 – 192.1.1.224** (11 hosts) — cluster principal, aloja la mayoría de las VMs WL/DB de cara al cliente.
- **192.1.3.252** (1 host) — aloja un conjunto distinto de VMs en otros rangos de IP (`172.18.5.x`, `10.10.1.x`, `192.1.3.x`) incluyendo `WL-ROMAN`, `DB-ROMAN`, `DB-GIAR`, `WL-GIAR`, `FW`, `WL12-Clientes`. **Probablemente un sitio físico separado o una máquina standalone fuera del cluster principal** — todavía sin confirmar, no comparte el patrón de gestión 192.1.1.x de los demás.
- **192.168.100.4** (1 host) — **sitio "Piedras", confirmado.** Ver sección aparte abajo.

### Sitio "Piedras" — confirmado (18 ago 2026)

Lo que era una mención verbal sin más rastro que el nombre de una VM de backup (`VEEAM-PIEDRAS`, dentro del cluster principal — no coincide con esto) quedó confirmado por dos vías independientes el mismo día: una sesión de TeamViewer activa dentro de un host en `192.168.100.165/24` (mismo subnet que el dashboard pfSense "Open - Piedras" en `192.168.100.1` que no había respondido durante el relevamiento manual de firewalls), y un export de vCenter propio del sitio (`ExportList-Piedras-Full.csv`) que lista 15 VMs en un host ESXi separado, `192.168.100.4`.

Solo 2 de las 15 VMs están encendidas — el resto no reporta IP en el export (vCenter solo ve la IP de un invitado con VMware Tools corriendo, mismo patrón que `OPENDOCKER03` en el sitio principal):

| VM | Estado | Rol (inferido) |
|---|---|---|
| `Win10-Piedras` | Encendido, `192.168.100.165` | Estación desde la que se confirmó el sitio — sesión de TeamViewer activa |
| `DC2` | Encendido, `192.168.100.2` | Controlador de dominio (el sitio principal tiene `DC1`) — sugiere que Piedras es un sitio AD replicado, no aislado |
| `OpenPiedrasFw01` | Apagado | Candidato fuerte a pfSense (FreeBSD, 2 NICs, nombre) — probablemente el firewall detrás del dashboard `192.168.100.1` que "no responde"; estar apagada lo explicaría |
| `PiedrasDB01`, `PiedrasWL01` | Apagadas | DB/WL propios del sitio — `PiedrasWL01` tiene una nota explícita de que es un WebLogic de prueba/licencia, no producción |
| `weblogic14C01`, `OPENDB_31`, `OPENDBRMAN` | Apagadas | WebLogic/DB adicionales |
| `OPENSHARE`, `OPENAPPS`, `COBRA`, `CLIENTESRDP` | Apagadas | Almacenamiento compartido, apps, y una VM (`COBRA`) que no coincide con ningún cliente conocido — mismo patrón por el que se encontró Argocean, sin confirmar todavía |
| `OEM`, `OPENMONITOR10`, `OPEN_GRAFANA` | Apagadas | Monitoreo/administración del sitio |

Detalle completo, notas de cada VM y hallazgos derivados en `infra/inventory.json` → `meta.piedras_site` / `vms[].site == "Piedras"` y en `infra/findings.md`.

## Cómo regenerar estos diagramas

El diagrama de mapeo de clientes en la sección 1 es generado, no dibujado a mano. Si `inventory.json` cambia, regenerarlo con el mismo enfoque: recorrer `clients[]`, emitir un nodo por cliente y uno por cada `resolved_vm` distinta bajo `weblogic`/`database`, deduplicar nodos, y conectar cliente→WL→DB. Mantenerlo acotado al subconjunto de clientes — un diagrama con las 129 VMs no se puede leer y no vale la pena construirlo; el JSON es la fuente de verdad para el resto.
