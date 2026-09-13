# Topología de infraestructura (vistas generadas)

Generado a partir de [`inventory.json`](inventory.json). No editar los diagramas de abajo a mano — regenerarlos desde el JSON (ver CLAUDE.md) cada vez que el JSON cambie, para que nunca queden desincronizados.

**Alcance: solo on-premise (vSphere).** La infraestructura en proveedores cloud (Azure/AWS) se estacionó fuera del alcance de este relevamiento — ver [../cloud-infra/README.md](../cloud-infra/README.md) para lo que ya se había encontrado ahí antes de acotar el foco.

## 1. Mapeo Cliente → WebLogic → Base de datos (vSphere on-premise)

Construido resolviendo los servidores WebLogic/DB declarados de cada cliente (del CSV de Relevamiento y, donde hay más detalle, de la matriz de clientes `Matriz_servicios_por_cliente_Hosting_V2.xlsx`) contra el inventario real de VMs en ExportList.csv — matcheado por nombre, y si el nombre no coincide, por IP (ver `resolved_by` en el JSON). 15 clientes en total: los 13 del CSV original de Relevamiento, más **Rex Argentina** y **Argocean**, ambos encontrados solo en la matriz más completa (ver findings.md). **ABB y Arris/GIAR están marcados en la matriz como ya dados de baja** — se mantienen en el diagrama porque sus VMs todavía existen y corren, pero no tratarlos como producción activa sin confirmar el estado actual. **ABB (6 sep 2026):** trazado en vivo — DB productiva confirmada `192.1.1.31` (`DBClientes-12C.31`, instancia `ABB`, schema `CONDOR`); `DBClientes.190` **descartada** como DB de ABB (solo tiene sub‑bases históricas apagadas). Además, ABB **sin una sola sesión ni DML desde el 1‑jul‑2026** — apagado de hecho, lo que respalda la marca de baja (ver `findings.md`).

Prestar atención a las instancias compartidas: varios clientes están en la *misma* VM de WebLogic y/o la misma VM de base de datos — es un dato de radio de impacto que conviene saber antes de tocar cualquiera de ellas.

**EBY (12 sep 2026):** DB cerrada a un solo nodo real, `OPENDBPROD005` — la candidata `Database .90` (detrás de la ruta paralela `yacyreta`/`WebLogic.191`) quedó descartada por `sqlplus` directo (esa DB es de `SIGO`, un tenant de `WebLogic.191` sin código de cliente asignado, fuera del alcance de este diagrama). EBY sigue con **dos** nodos WL en el diagrama (`WebLogic.191` y `OPENWLPROD01`) porque ambos corren tráfico Forms productivo real y concurrente — no es ambigüedad sin resolver, son dos stacks vivos a la vez.

```mermaid
flowchart LR
  n_ABB["ABB S.A.<br/>(ABB)<br/><i>DADA DE BAJA</i>"]
  n_WL12C_Desarrollo_2_54["WL: WL12C-Desarrollo.2.54"]
  n_DBClientes_12C_31[("DB: DBClientes-12C.31")]
  n_DBClientes_190[("DB: DBClientes.190")]
  n_GIAR["Arris de Argentina S.A.<br/>(GIAR)<br/><i>DADA DE BAJA</i>"]
  n_OPENWLPROD01["WL: OPENWLPROD01"]
  n_DB_GIAR[("DB: DB-GIAR")]
  n_OPENDBPROD001[("DB: OPENDBPROD001")]
  n_CEFAS["Cefas S.A.<br/>(CEFAS)"]
  n_WebLogic_191["WL: WebLogic.191"]
  n_CLIENTES_DB[("DB: CLIENTES-DB")]
  n_BOCA["Club Atlético Boca Juniors<br/>(BOCA)"]
  n_ROMAN["CSM Ciencia al Servicio del Movimiento S.A.<br/>(ROMAN)"]
  n_WL_CLIENTES["WL: WL-CLIENTES"]
  n_DB_ROMAN[("DB: DB-ROMAN")]
  n_OPENDBPROD03[("DB: OPENDBPROD03")]
  n_DCVIAJES["DC Viajes y Turismo S.A.<br/>(DCVIAJES)"]
  n_DVAL["Dominique Val S.A.<br/>(DVAL)"]
  n_DBClientes_238[("DB: DBClientes.238")]
  n_ENERFLEX["Enerflex Solutions Argentina SRL<br/>(ENERFLEX)"]
  n_WL12C_PROD["WL: WL12C-PROD"]
  n_CLIENTES_DB2[("DB: CLIENTES-DB2")]
  n_ESYOP["Ente Servicios y Obras Públicas (ESYOP)<br/>(ESYOP)"]
  n_WebLogic_19["WL: WebLogic.19"]
  n_EBY["Entidad Binacional Yacyretá<br/>(EBY)"]
  n_OPENDBPROD005[("DB: OPENDBPROD005")]
  n_JOBS["Jobs Servicios de Recursos Humanos SRL<br/>(JOBS)"]
  n_HEINLEIN["Heinlein<br/>(HEINLEIN)"]
  n_OL8LABWL01["WL: OL8LABWL01"]
  n_MAIPU["Maipú<br/>(MAIPU)"]
  n_DMWL01["WL: DMWL01"]
  n_DASADBPROD01[("DB: DASADBPROD01")]
  n_279["Rex Argentina<br/>(279)"]
  n_192_1_3_34[("DB: VM sin identificar (192.1.3.34)")]
  n_Argocean["Argocean<br/>(Argocean)"]
  n_DB_ARGOCEAN[("DB: DB-ARGOCEAN")]
  n_ABB --> n_WL12C_Desarrollo_2_54
  n_WL12C_Desarrollo_2_54 --> n_DBClientes_12C_31
  n_GIAR --> n_OPENWLPROD01
  n_OPENWLPROD01 --> n_DB_GIAR
  n_OPENWLPROD01 --> n_OPENDBPROD001
  n_CEFAS --> n_WebLogic_191
  n_WebLogic_191 --> n_CLIENTES_DB
  n_BOCA --> n_WL12C_Desarrollo_2_54
  n_WL12C_Desarrollo_2_54 --> n_CLIENTES_DB
  n_ROMAN --> n_WL_CLIENTES
  n_WL_CLIENTES --> n_DB_ROMAN
  n_ROMAN --> n_OPENWLPROD01
  n_OPENWLPROD01 --> n_OPENDBPROD03
  n_DCVIAJES --> n_WebLogic_191
  n_WebLogic_191 --> n_DBClientes_190
  n_DVAL --> n_WebLogic_191
  n_WebLogic_191 --> n_DBClientes_238
  n_ENERFLEX --> n_WL12C_PROD
  n_WL12C_PROD --> n_CLIENTES_DB2
  n_ESYOP --> n_WebLogic_19
  n_WebLogic_19 --> n_DBClientes_12C_31
  n_EBY --> n_WL12C_Desarrollo_2_54
  n_EBY --> n_WebLogic_191
  n_EBY --> n_OPENWLPROD01
  n_OPENWLPROD01 --> n_OPENDBPROD005
  n_JOBS --> n_WL12C_PROD
  n_HEINLEIN --> n_OL8LABWL01
  n_OL8LABWL01 --> n_OPENDBPROD001
  n_MAIPU --> n_DMWL01
  n_DMWL01 --> n_DASADBPROD01
  n_279 --> n_OPENDBPROD001
  n_279 --> n_192_1_3_34
  n_279 --> n_OL8LABWL01
  n_Argocean --> n_WL_CLIENTES
  n_WL_CLIENTES --> n_DB_ARGOCEAN
```

**Leer este diagrama con cuidado — varios nodos son engañosos:**

- **`DBClientes-12C.31` la comparten ABB y ESYOP** (`WL12C-Desarrollo.2.54 → DBClientes-12C.31` y `WebLogic.19 → DBClientes-12C.31`): confirmado en vivo el 6 sep 2026 — instancias Oracle separadas (`ABB` y `esyop`) en el mismo box. `DBClientes.190` la usa **solo DCVIAJES** (vía `WebLogic.191`); la flecha ABB→`DBClientes.190` que había antes se quitó — ese box solo tiene sub‑bases históricas de ABB (`abbhist`/`abbtubio`, apagadas), no su DB productiva.
- **`EBY`, `ROMAN`, `GIAR` y `Rex Argentina` (`279`) tienen más de un nodo WL y/o DB** — a diferencia del resto, no es "un cliente, un servidor": son candidatos en paralelo (stack legado vs. nuevo, o candidatos sin confirmar todavía). El emparejamiento WL→DB que muestra el diagrama para estos cuatro está curado a mano con la evidencia real de cada trazado (`plan_relevamiento_alta_eby.md`, `infra/findings.md`), no generado mecánicamente — antes de tocar cualquiera de estos nodos, leer el detalle en `clients[].weblogic.resolved`/`.database.resolved` (campo `notes`), no asumir por la flecha. **Excepción: EBY ya no tiene ambigüedad de DB** (cerrado 12 sep 2026, un solo nodo `OPENDBPROD005`) — sus dos nodos WL siguen dobles porque ambos stacks están vivos en simultáneo, no porque falte resolver cuál es el real.
- **`OPENWLPROD01` y `OPENDBPROD001` son ahora los hosts más compartidos del segundo nivel** (después de `WebLogic.191`/8 clientes y `CLIENTES-DB`/3 instancias): `OPENWLPROD01` sirve a EBY, GIAR y ROMAN; `OPENDBPROD001` a Heinlein, CEFAS (destino), GIAR y Rex Argentina — ninguno de estos últimos tres verificado en vivo todavía, solo por `tnsnames.ora`/NPM.
- **Rex Argentina (`279`) tiene 2 candidatos de DB y 1 de WL, ninguno confirmado** — primera vez que aparece algo de infraestructura de Rex en este diagrama (antes no tenía ningún nodo resuelto).

> La topología Azure/AKS que estaba acá se movió a [`../cloud-infra/topology-cloud.md`](../cloud-infra/topology-cloud.md) — infraestructura cloud fuera de alcance por ahora, ver [`../cloud-infra/README.md`](../cloud-infra/README.md).

## 2. Inventario de VMs por categoría (las 129 VMs del sitio principal, de ExportList.csv)

Solo los totales — ver `inventory.json` → `vms[].category` para la lista de miembros de cada grupo. Las categorías se asignaron por coincidencia de nombre/SO salvo que se indique lo contrario por confirmación vía el material de los emails/RAR (ver findings.md para qué está confirmado y qué sigue siendo conjetura). Acotado al sitio principal — las 15 VMs del sitio Piedras (`vms[].site == "Piedras"`) tienen su propia tabla en la §3 de abajo, tanto por ser un cluster/host separado como por venir de un export distinto (`ExportList-Piedras-Full.csv`).

| Categoría | Cantidad | Confianza |
|---|---|---|
| database | 33 | Mixta — varias confirmadas vía el mapeo de clientes, el resto inferidas solo por nombre |
| workstation_or_jumphost | 20 | Inferida (SO invitado Windows 7/10 + nombre) |
| weblogic_app | 18 | Mixta — varias confirmadas vía el mapeo de clientes, el resto inferidas solo por nombre |
| unclear | 14 | Sin señal en el nombre, o una conjetura previa (candidato a nginx) que resultó incorrecta |
| infra_generic_unclear | 12 | Desconocida — el nombre genérico `OPENINFRxx` no dice nada sobre el rol |
| firewall_confirmed_pfsense | 7 (`OPENVPNFW01` por IP del peer VPN de Azure; `CliProFw01`, `DMFW01`, `FW`, `FWOPEN`, `OPENFWCLI001`, `OPENFWCLI10` por el relevamiento manual de pfSense) | **Confirmada** |
| docker_host_confirmed / docker_host_confirmed_nginx_proxy_manager | 9 (5 + 4) | **Confirmada** — detalle a nivel contenedor del relevamiento de Docker, incl. cuáles 4 corren Nginx Proxy Manager |
| bi_reporting | 4 | Inferida (Jasper/MicroStrategy en el nombre) |
| backup | 2 | Inferida (Veeam en el nombre) — incluye `VEEAM-PIEDRAS`, en el sitio principal pese al nombre, rol sin confirmar |
| firewall_candidate_pfsense | 2 (`OPENFWCLI02`, `VM_FW`) | Inferida (SO invitado FreeBSD + nombre con fw/vpn), todavía sin confirmar |
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

**Conectividad de red hacia el cluster principal, confirmada en vivo (18 ago 2026).** Desde la sesión de TeamViewer en `Win10-Piedras` (`192.168.100.165`), `http://192.1.1.38:81/` — el panel de Nginx Proxy Manager de `VM-DOCKER-Clientes`, en el cluster principal — respondió directamente, sin salto intermedio. Piedras no es un sitio aislado de red: alcanza al menos el segmento `192.1.1.x`, además del `10.77.254.x` ya inferido por el backup de `OPENDB_31` hacia `OPENBK`. Esto habilita mapear el ítem 1 de Tier 1 (dominio → NPM → servidor, ver `../plan_relevamiento_alta_cefas.md`) directamente desde una sesión a Piedras, sin necesitar un salto a una VM del cluster principal primero.

Detalle completo, notas de cada VM y hallazgos derivados en `infra/inventory.json` → `meta.piedras_site` / `vms[].site == "Piedras"` y en `infra/findings.md`.

## 4. Diagrama de red de alto nivel (sitios, firewalls, conectividad)

A diferencia de §1–§3 (que agrupan VMs por cliente o por categoría), esta vista es a nivel de **red**: qué sitios existen, qué firewall hay en el borde de cada uno, y qué conectividad entre sitios está confirmada vs. inferida. Es la vista que responde "¿qué hay en el datacenter Open y qué hay en la oficina Piedras, a alto nivel?".

**A mano, no generado del JSON** — a diferencia de §1, esta vista no se recorre mecánicamente desde `clients[]`; se arma leyendo `vms[].category` (firewalls, docker hosts) y `meta`/`esxi_hosts`/`piedras_esxi_hosts`. Si cambia la topología de red (un firewall nuevo confirmado, conectividad nueva entre sitios), actualizar el diagrama a mano y anotar la fuente en el label del enlace, igual que se hizo abajo.

```mermaid
flowchart TB
  Internet(("Internet"))
  AZURE["Azure — capa web/aplicación (en relevamiento)<br/>portales CONDOR (Work / Enterprise / ProvIA) · AKS East US<br/>Angular + backend .NET · Entra ID B2C<br/>los datos viven on-premise (vía ORDS) · ver plan_relevamiento_azure.md"]

  subgraph DC["Datacenter Open (sitio principal)"]
    direction TB
    EDGE["OPENVPNFW01 — pfSense borde (VPN)<br/>200.55.243.92 / .115<br/>solo OpenVPN UDP/2190 · VPN S2S a Azure casi sin uso (~487 MiB/30d)"]
    EDGE2["FWOPEN — pfSense borde (NAT) + interno<br/>200.55.243.90 / .94 · 192.1.1.11<br/>~46 reglas NAT: los 2 NPM (80/443), Oracle directo,<br/>consola de vCenter (192.1.1.29:443), su propio panel"]

    subgraph CLUSTER["Cluster ESXi principal<br/>192.1.1.214–224 (11 hosts) · LAN 192.1.1.x"]
      direction TB
      FWINT["6 pfSense internos confirmados<br/>FWOPEN · FW · CliProFw01<br/>OPENFWCLI001 · OPENFWCLI10 · DMFW01<br/>(+2 candidatos: OPENFWCLI02, VM_FW)"]
      NPM["4 hosts Docker con Nginx Proxy Manager<br/>DOCKER-DEB · OPENDOCKER04 · VM-DOCKER-Clientes (x2)<br/>ruteo por dominio + ORDS (ords-‹cliente›.open.com.ar)"]
      OTHERDOCKER["5 hosts Docker más<br/>(sin NPM)"]
      WLDB["VMs WebLogic / Forms-Reports / ORDS<br/>+ bases Oracle de clientes (ver §1)"]
      BACKUP["OPENBK — backup Veeam<br/>192.1.1.14 / 10.77.254.114"]
    end

    subgraph HOST2["Host ESXi standalone — ¿sitio separado? (sin confirmar)<br/>192.1.3.252"]
      direction TB
      GIARROMAN["WL-GIAR · DB-GIAR<br/>WL-ROMAN · DB-ROMAN · WL12-Clientes<br/>rangos 172.18.5.x / 10.10.1.x / 192.1.3.x"]
    end
  end

  subgraph PIEDRAS["Sitio Piedras (oficina) — confirmado 18 ago 2026<br/>subred 192.168.100.0/24"]
    direction TB
    PFW["OpenPiedrasFw01 — candidato pfSense<br/>192.168.100.1 — apagada"]
    PHOST["Host ESXi Piedras<br/>192.168.100.4 (15 VMs, 2 encendidas)"]
    PWIN["Win10-Piedras<br/>192.168.100.165"]
    PDC["DC2 — AD replicado<br/>192.168.100.2"]
  end

  AZURE -->|"HTTPS · ords-‹cliente›.open.com.ar<br/>(grueso del tráfico app↔datos)"| Internet
  Internet -->|"OpenVPN 2190/UDP (único puerto)"| EDGE
  Internet -->|"NAT entrante: 80/443, Oracle, admin"| EDGE2
  EDGE --> CLUSTER
  EDGE2 -->|"NAT 80/443 → los 2 NPM"| NPM
  NPM -->|"dominio / Host header"| WLDB
  NPM -->|"ords-‹cliente› → ORDS pegado a la base del cliente"| WLDB
  FWINT -.-> NPM
  CLUSTER -.->|"sin confirmar si es sitio físico distinto o standalone"| HOST2

  PWIN -->|"confirmado en vivo 18ago2026:<br/>http://192.1.1.38:81/ responde directo, sin salto"| NPM
  PHOST -.->|"inferido — nota de backup Veeam<br/>de OPENDB_31 apunta a OPENBK"| BACKUP
```

**Qué está confirmado vs. qué es todavía hipótesis, en este diagrama:**

- **Confirmado — hay dos firewalls de borde, no uno.** `OPENVPNFW01` (`200.55.243.92`) termina la VPN site-to-site con Azure y **solo** expone OpenVPN/2190 UDP — pero esa VPN hoy lleva tráfico casi nulo (~487 MiB/30d, ver `informe_ejecutivo_infraestructura_02.md`). `FWOPEN` (`200.55.243.90` / `.94`) es un segundo pfSense de cara a Internet con ~46 reglas NAT activas: los dos NPM en 80/443, acceso Oracle directo para varios clientes, **la consola de administración de vCenter** (`192.1.1.29:443`) y su propio panel. Esto **corrige** el hallazgo anterior de "solo OpenVPN expuesto" (ver `findings.md` → "Corregido: la exposición a Internet NO es mínima", 19 ago 2026). `FWOPEN` aparece dos veces en el diagrama a propósito: es a la vez pfSense interno del cluster y gateway NAT de borde.
- **Confirmado — el plano ORDS es la vía principal app↔datos.** Los portales CONDOR en Azure AKS consultan la base Core y pegan por HTTPS a `ords-‹cliente›.open.com.ar`, endpoints publicados por el NPM on-premise cuyo destino es un ORDS (Oracle REST Data Services) pegado a la base Oracle del cliente. El grueso del tráfico app→datos va por acá, por Internet — no por la VPN S2S. Clientes con `ords-` propio: Balanz, BOCA, CEFAS, EBY, JOBS, ROMAN (ver `informe_ejecutivo_infraestructura_02.md` y `findings.md`).
- **Confirmado — Piedras:** sitio real, con su propio host ESXi y subred `192.168.100.0/24`; la conectividad Piedras → cluster principal (`192.1.1.x`), probada en vivo llegando al panel de NPM de `VM-DOCKER-Clientes` sin salto intermedio.
- **Inferido, no probado en vivo:** la conectividad Piedras → `OPENBK` (backup) — viene de una nota de texto en `OPENDB_31`, no de una prueba de red hecha a mano.
- **Todavía abierto:** si el host `192.1.3.252` es un tercer sitio físico separado o una máquina standalone dentro del mismo datacenter (ver findings.md, "Todavía abierto" #2); si `OpenPiedrasFw01` es efectivamente el pfSense de Piedras (está apagada, sin confirmar por acceso directo); el rango `192.168.222.x` (endpoints ORDS de Balanz) que no aparece en ningún export — posible otra red aislada, como pasó con Piedras.

## Cómo regenerar estos diagramas

El diagrama de mapeo de clientes en la sección 1 es generado, no dibujado a mano. Si `inventory.json` cambia, regenerarlo con el mismo enfoque: recorrer `clients[]`, emitir un nodo por cliente y uno por cada `resolved_vm` distinta bajo `weblogic`/`database`, deduplicar nodos, y conectar cliente→WL→DB. Mantenerlo acotado al subconjunto de clientes — un diagrama con las 129 VMs no se puede leer y no vale la pena construirlo; el JSON es la fuente de verdad para el resto.
