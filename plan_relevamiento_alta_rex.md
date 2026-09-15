# Relevamiento de alta de cliente — camino punta a punta (Rex Argentina de referencia)

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md), [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md), [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md), [`plan_relevamiento_alta_boca.md`](plan_relevamiento_alta_boca.md), [`plan_relevamiento_alta_abb.md`](plan_relevamiento_alta_abb.md), [`plan_relevamiento_alta_roman.md`](plan_relevamiento_alta_roman.md) y [`plan_relevamiento_alta_giar.md`](plan_relevamiento_alta_giar.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Séptimo trazado cerrado del todo.** Rex Argentina es uno de los 2 clientes descubiertos que no estaban en los 13 originales del CSV de Relevamiento (junto a Argocean) — arrancó con cero recursos mapeados (ítem 2 de Tier 1 en `PLAN.md`) y avanzó en tandas sueltas desde el 19 ago 2026, hasta cerrarse del todo hoy.

## Hipótesis validada: dos módulos, no dos stacks en disputa

A diferencia de GIAR/ROMAN (donde "legado vs. nuevo" son dos versiones del mismo stack, y solo una está realmente viva), Rex tiene **dos módulos que conviven a propósito, sirviendo cosas distintas**:

- **Motor clásico (Oracle Forms)** — `serzarex.condor.solutions` → `OL8LABWL01` (`192.1.2.195:9001`) → Oracle `PRODREX01` (`OPENDBPROD001`/`CDBOPEN03`, PDB). Confirmado en vivo el 6 sep 2026: usuarios nominales reales (`MAIETA`, `CDELISE`, `MCORREA`, `JBRICEÑO`) conectados vía `frmweb`/`java`.
- **Self Service (Docker)** — sin dominio/NPM, expuesto directo por NAT de `FWOPEN` → `OPENDOCKER.57` (`192.1.1.57`, hostname real `dbdocker`) → contenedores `rex_frontend`/`rex_backend` → Postgres propio `rex_postgres`. Confirmado en vivo el 14 sep 2026.

Mismo patrón "Self Service separado del motor clásico" que ya se vio en CEFAS, pero acá la infraestructura Docker se descubrió primero (19 ago) y el motor clásico después (6 sep) — al revés que en CEFAS.

## El camino, capa por capa

| # | Capa | Estado | Detalle |
|---|---|---|---|
| 1 | Dominio de entrada | **Resuelto.** Solo aplica al motor clásico. | `serzarex.condor.solutions` → `192.1.2.195:9001`, habilitado en el NPM de `DOCKER-DEB` (visto 1 sep 2026). El módulo Self Service **no tiene dominio propio** — entra directo por NAT sobre la IP pública del firewall, sin pasar por ningún NPM (`OPENDOCKER.57` confirmado sin Nginx Proxy Manager corriendo — `docker_detail.runs_nginx_proxy_manager: false`). |
| 2 | Nginx Proxy Manager | **Resuelto.** No aplica al módulo Self Service. | El NPM de `DOCKER-DEB` sirve el dominio del motor clásico (capa 1). Self Service no pasa por NPM — confirmado por ausencia de contenedor NPM en `OPENDOCKER.57`. |
| 3 | Firewall / NAT | **Resuelto (14 sep 2026).** | Reglas de `FWOPEN` conocidas desde el 19 ago 2026 — `SS Rex Front` (WAN `4431`→`192.1.1.57:80`) y `SS Rex Back` (WAN `4433`→`192.1.1.57:4433`). Cerrado hoy del lado del host: `docker ps -a` en `192.1.1.57` muestra `rex_frontend` publicando exactamente el puerto `80` y `rex_backend` el puerto `4433` (→ contenedor `9001`) — los puertos reales de los contenedores coinciden letra por letra con las reglas NAT, cerrando el lazo firewall↔servicio real. |
| 4 | App — motor clásico | **Resuelto (6 sep 2026).** | `OL8LABWL01` confirmado como motor clásico real por tráfico Forms/Java real en `v$session` de `PRODREX01` (ver capa 6) — no solo candidato por nombre de dominio. |
| 5 | App — Docker (Self Service) | **Resuelto (14 sep 2026).** | Contenedores reales identificados por `docker ps -a` (el nombre `SelfRex` del relevamiento Docker original no existe como tal): `rex_frontend` (nginx), `rex_backend` (Jetty/Dropwizard), `rex_postgres` (Postgres 9.5) — los tres `Up` desde hace **2 años**, uptime real, no solo desplegados. |
| 6 | Base de datos | **Resuelto — dos bases, una por módulo.** | **Motor clásico:** `PRODREX01` (PDB en `OPENDBPROD001`/`CDBOPEN03`), confirmada en vivo el 6 sep 2026 vía `v$session` con usuarios nominales reales. Bonus de esa misma sesión: `QAREX01`, segundo ambiente en la misma CDB, sin tráfico visto todavía. El candidato secundario `PDBREXPROD`/`192.1.3.34` (alias `tnsnames.ora`, VM sin rastro en `ExportList.csv`) queda descartado como el real, sin resolver qué VM es — blind spot menor, no bloqueante. **Self Service:** `rex_postgres` (Postgres 9.5, propio del contenedor), confirmado en vivo el 14 sep 2026 — DB separada, no comparte datos con la Oracle del motor clásico. |
| 7 | Almacenamiento | **Resuelto (14 sep 2026) — y confirmado roto.** | `docker inspect rex_backend`/`rex_frontend` muestra que ambos montan el mismo bind `/data/selfrex/archivos` (destino `.../archivos/recibos` en el backend, `/opt/archivos` en el frontend) — es el storage real de recibos, no un mount huérfano. `df -h` en el host da **`Stale file handle`** sobre ese path — el NFS del lado servidor cambió o reinició y el cliente quedó con un handle inválido. Es el mismo mount que `inventory.json` (`OPENDOCKER.57.docker_detail`) ya marcaba genéricamente como "un NFS da error", ahora identificado como el de Rex. **Hallazgo operativo activo:** la app sigue arriba (nginx/Jetty responden), pero la carga/descarga de recibos probablemente falla mientras el mount esté en este estado — a reportar, no a "arreglar" sin que lo pida el cliente/equipo saliente. |

## Al terminar

1. ✅ `infra/inventory.json` — actualizado: `clients[Rex Argentina].status` → `"Activo / confirmado en vivo"`, notas con el trazado completo; `vms[OPENDOCKER.57].used_by_clients` incluye ahora a Rex (código `279`); `docker_detail.services`/`notes` corregidos con los nombres reales de contenedor y la identificación del NFS roto.
2. ✅ `infra/findings.md` — entrada nueva "Rex Argentina — trazado punta a punta cerrado, 7/7 (14 sep 2026)"; ítem 2 de la lista de prioridades por TeamViewer marcado resuelto.
3. ✅ `verificacion_completitud_clientes.md` — Rex Argentina de ~68% a **100%**; headline global actualizado.
4. ✅ `PLAN.md` — ítem 2 de Tier 1 marcado `RESUELTO`.
5. Pendiente, no bloqueante: identificar la VM detrás de `192.1.3.34` (`PDBREXPROD`) si alguna vez se retoma el barrido de blind spots del segmento `192.1.3.x`.
