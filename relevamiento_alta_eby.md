# Relevamiento de alta de cliente — camino punta a punta (EBY de referencia)

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md) y [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta. Pero **EBY se eligió por impacto, no por ser un caso limpio**: es el cliente que más infraestructura compartida toca de los 15, así que trazarlo obliga a abrir sesión en los servidores WebLogic multi‑inquilino del parque y deja mapeados de paso ~9 clientes más. Ya estaba como ítem 3 de Tier 1 en `PLAN.md` y tiene dos filas abiertas en la hoja Discrepancias de la matriz.

**Uno de tres trazados en paralelo.** CEFAS = WL compartido + una migración de DB a medio hacer + capa Docker (Self Service). JOBS = cadena dedicada, de contraste. EBY = **máximo enredo**: arrancó con cuatro ubicaciones WL candidatas; al 1 sep 2026 los logs de NPM confirmaron que corre en producción sobre **dos motores a la vez** (`192.1.1.191` + `10.77.7.201`), el tercero (`10.77.8.201`) es un clon apagado y el cuarto (`192.1.2.54`) solo sirve ORDS. La receta generalizada se convalida contra los tres, no contra uno.

**Estado al 12 sep 2026: 7 de 7 capas cerradas — EBY completo.** 1–3 (rutas de entrada, NPM, firewall/NAT), 4 y 6 (motor clásico y DB de la ruta productiva real, `eby-prod`/`OPENWLPROD01`/`OPENDBPROD005`, confirmados por `formsweb.cfg` + `tnsnames.ora` reales) y 7 (storage, no aplica) cerradas. Capa 5 cerrada como "no aplica" por desk-check. **Único cabo suelto cerrado el 12 sep 2026:** `sqlplus` directo a `Database .90`/`CDRADM` (`root@192.1.1.90`) confirmó que esa DB compartida NO es de EBY — de los 8 inquilinos de `WebLogic.191`, solo `SIGO` tiene schema propio ahí (2.6 GB, uso activo el mismo día). La ruta paralela `yacyreta`/`WebLogic.191` no tiene DB de EBY identificable; `eby-prod` sigue siendo la única ruta productiva real de EBY. Ver `infra/findings.md` → "EBY — capa 6 cerrada del todo, 7/7".

## Por qué EBY (impacto sobre el resto del relevamiento)

EBY aparece hoy asociado a **cuatro** servidores WebLogic distintos, sin saber cuál usan los usuarios reales:

| Candidato | Qué es | Fuente | Co‑inquilinos que quedan relevados de paso |
|---|---|---|---|
| `192.1.2.54:9001` (`WL12C-Desarrollo.2.54`) | WL "reclamado" en Relevamiento / "actual, compartido" en el inventario técnico | `inventory.json` `clients[EBY].weblogic` + hoja Discrepancias | **ABB, BOCA** + `condor.open.com.ar` genérico — **box nunca accedido** |
| `10.77.7.201:9001` (`OPENWLPROD01`) | destino "funcional" según la matriz; dominios `eby-prod` / `eby-qa.condorwork.com.ar` | NPM `DOCKER-DEB` (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`) + hoja Discrepancias | **GIAR** + **ROMAN** (`romanprod`/`romanqa.condor.solutions` → mismo box, habilitados — ver `findings.md` 1 sep 2026) |
| `192.1.1.191:80` (`WebLogic.191`) | dominio `yacyreta.condorwork.com.ar` | NPM `DOCKER-DEB` (`findings.md`) | **DVAL, UIA, Mafisa, SIGO, DCViajes, Tassaroli** (CEFAS ya cerrado acá) |
| `10.77.8.201:9001` | dominio `ebyprod.open.com.ar`; IP sin VM conocida en `ExportList.csv` | NPM `DOCKER-DEB` (`findings.md` "Todavía abierto" #4) | resolverla cierra un blind spot |

Resolver "en cuál corre EBY de verdad" obliga a mirar, en cada uno de los cuatro, sesiones activas / datasource JDBC / apps desplegadas **por cliente**. Eso produce evidencia en vivo para **~9 clientes más** en una sola pasada, y cierra de paso tres filas de disputa: EBY (servidor WL), ABB (cuál de `.31` / `.190` es la DB productiva — Tier 1 #4) y BOCA (SID `BOCA` vs `BOCAPDB`).

> **Actualización (1 sep 2026):** los access logs de NPM ya confirmaron el enredo — EBY corre Forms en producción **simultánea** sobre `192.1.1.191` **y** `10.77.7.201` (ver § *Capa 1 — rutas de entrada*). El "árbol de candidatos" era literal. La sesión pendiente ahora es sobre esos dos motores + `192.1.2.54` (por ABB/BOCA).

## Estado de partida (1 sep 2026)

De `infra/inventory.json` → `clients[EBY]`, `infra/findings.md` y `infra/topology.md` §1:

- **WL reclamado:** `WL12C-Desarrollo.2.54` (`192.1.2.54`), `wl_version` reclamada `11` (sin verificar — mismo patrón de discrepancia 11/12 que ya se corrigió en GIAR y JOBS a favor del 12).
- **DB reclamada:** `DB_YACY.22`, resuelta **por IP** a `OPENDBPROD006` (`192.1.1.22`) con `match: false` — el nombre reclamado no coincide con ninguna VM, solo la IP.
- **Matriz:** SID actual `MBA` (Oracle 11.2.0.4.0 EE, 51 G, charset `WE8ISO8859P1`); destino `BD 10.77.7.15` / SID `EBYPROD`. `observaciones`: *"BD y WL migrados; falta actualizar la base mediante import, configurar VPN del cliente y revisar FSAL."* `validacion_pendiente`: *"Confirmar si el WL actual es realmente de desarrollo y validar la nueva VM DB ya creada."*
- **Productos (matriz):** Work `Sí`, Condor Link `Sí`, Jasper `Sí`, Discoverer `Sí`, Self Service *(en blanco)*. → EBY probablemente **no** tiene contenedores Self Service propios; la capa 5 acá es reportería (Jasper/Discoverer), no una app Docker. Pista contraria a vigilar: el contenedor `ss_pg_cefas` de CEFAS corre la imagen `self-service-database:yacyreta-sfd`, lo que implica que existió un compose de Self Service de Yacyretá para copiar — puede ser legado.
- **Estado en inventario:** `"Migrado / actualización pendiente"`. `OPENDBPROD006` tiene 28 días de uptime — el más bajo de todos los servidores de cliente encendidos (señal débil de migración reciente, ver `findings.md`).
- **NAT:** regla `acceso YACYRETA` en `FWOPEN` → `192.1.1.22:1521` (`inventory.json` → `vms[FWOPEN].nat_rules`), restringida por origen. Coincide con la IP de `OPENDBPROD006`.
- **Cuenta:** `admin_user: soportesmart` (la misma cuenta compartida; fue **rechazada** en la consola de GIAR — ver `findings.md` —, así que no asumir que abre las consolas WebLogic).
- **Discrepancias abiertas (hoja de la matriz):** fila "EBY / Servidor WebLogic" (destino `10.77.7.201` vs actual `192.1.2.54`); y validar la VM de DB nueva / SID (`MBA` → `EBYPROD`).

## El camino, capa por capa

| # | Capa | Estado (1 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | ✅ **Resuelto (1 sep 2026).** 10 proxy hosts EBY/Yacyretá leídos de la tabla `proxy_host` real de `DOCKER-DEB` + clasificados contra los access logs (viva / muerta / test) — tabla completa abajo (§ *Capa 1 — rutas de entrada*). Dos rutas Forms en producción viva concurrente (`yacyreta.condorwork.com.ar` → `192.1.1.191:80`; `eby-prod.condorwork.com.ar` → `10.77.7.201:9001`), ORDS en `192.1.2.54:7010` y en `10.77.7.15` (`OPENDBPROD005`), `ebyprod.open.com.ar` → `10.77.8.201` muerto (VM apagada). | Ninguno bloqueante. *Completeness* (ver *Al terminar*): transcribir `OPENDOCKER04` + `VM-DOCKER-Clientes (1)`, reconciliar `proxy_hosts.csv` a 101, cargar `entry_points` en `inventory.json`. |
| 2 | Nginx Proxy Manager | ✅ **Resuelto (1 sep 2026).** El NPM de EBY es `DOCKER-DEB` (`192.1.1.37:81`) — las 10 rutas están en su MariaDB interna. `VM-DOCKER-Clientes` (`192.1.1.38`, 9 proxy hosts ya transcriptos para CEFAS) no tiene ninguna entrada EBY. | *Completeness*: confirmar que `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` tampoco tienen rutas EBY (ambos responden en `:81` desde `DOCKER-DEB`). |
| 3 | Firewall / NAT | ✅ **Resuelto, sin regla dedicada (1 sep 2026).** Mismo patrón que CEFAS/JOBS: la web de EBY entra por el NAT genérico de `DOCKER-DEB` (`200.55.243.94:80/443` → `192.1.1.37`), ruteo por Host header dentro del NPM. `FWOPEN` (46 reglas, tabla completa en `inventory.json`) no tiene NAT web hacia ningún WL. Única regla EBY-específica: `acceso YACYRETA` → `192.1.1.22:1521` (Oracle, restringida por origen). | Ninguno. |
| 4 | App — motor clásico | ✅ **Resuelto para la ruta `eby-prod` (2 sep 2026).** EBY corre Forms en producción **en dos motores a la vez**: `192.1.1.191` (WebLogic.191, F&R 11g, `ClassicDomain`, bloqueado sin sudo) y `10.77.7.201` (OPENWLPROD01, F&R **12.2.1**, dominio **`base_domain`**, `sudo (ALL) ALL` disponible). En `OPENWLPROD01`: 3 ambientes reales confirmados en `formsweb.cfg` — `[ebyprod]` → `/u02/clientes/ebyprod/cdr2/menues/cdr2w.fmx`, `[ebyqa]` → `/u02/clientes/ebyqa/cdr2/menues/cdr2w.fmx`, `[ebyaudit]` → `/u02/clientes/ebyaudit/cdr2/menues/cdr2w.fmx` (más las variantes `FSAL`/`activacion*` de cada uno). Sin `userid=` preconfigurado — el login lo tipea el usuario en la pantalla de Forms (coincide con la sesión real de `AGARCIA` vista en capa 6). | Ninguno para `eby-prod`. La ruta `yacyreta`/`WebLogic.191` queda sin poder confirmar sus módulos exactos (permission wall sin sudo) — no bloqueante, dado que `eby-prod` es la ruta con archivos/DB dedicados. |
| 5 | App — capa Docker / reportes | ✅ **Resuelto — no aplica (2 sep 2026).** Revisadas las 101 rutas de `DOCKER-DEB` (desk-check, sin sesión): no existe ningún `*jasper*` para EBY/Yacyretá, a diferencia de `cefasjasper`/`cabjjasper`/`jobsjasper` que sí están. Junto con el `ls -la /clientes/` negativo (capa 7) y `Self Service` en blanco de la matriz, cierra la capa: EBY no tiene componente Docker/reportes containerizado. | Ninguno. |
| 6 | Base de datos | ✅ **Resuelto de punta a punta (12 sep 2026).** Ruta `eby-prod`: tres alias TNS confirmados con `SERVICE_NAME` exacto: `EBYPROD`, `EBYQA`, `EBYAUDIT` — los tres a `10.77.7.15` (`OPENDBPROD005`), puerto 1521, vía `tnsnames.ora` real de `OPENWLPROD01` (2 sep 2026). `EBYPROD` coincide letra por letra con `sid_nuevo` de la matriz. Ruta `yacyreta`: `sqlplus` directo a `Database .90`/`CDRADM` (`root@192.1.1.90`, 12 sep 2026) confirmó que **no** es la DB de EBY — de los 8 inquilinos de `WebLogic.191`, solo `SIGO` tiene schema propio ahí. La ruta paralela no tiene DB de EBY identificable. | Ninguno. Capa cerrada por completo — ruta productiva confirmada por config oficial, ruta paralela descartada por evidencia directa `sqlplus`. |
| 7 | Almacenamiento / object store | ✅ **Resuelto — no aplica (1 sep 2026).** `ls -la /clientes/` en `WebLogic.191` no muestra ninguna carpeta de EBY/Yacyretá (al 6 sep 2026 solo `cefas` y `lost+found`). Sin mount NFS dedicado para EBY. Coincide con la matriz (`Self Service` en blanco para EBY) y con el resultado de capa 5. | Ninguno. Reabrir solo si capa 5 encuentra un `ss_*_yacyreta` vivo en otro host. |

## Capa 1 — rutas de entrada (detalle, 1 sep 2026)

Sacado de la tabla `proxy_host` de `DOCKER-DEB` (`ssl-db-1`, MariaDB) + los access logs de NPM (`ssl-app-1`, `/data/logs/proxy_host-<N>.log`). Estado medido al 1 sep 2026 ~18:00.

| Dominio | id | → destino | `enabled` | `modified_on` | Estado real (por access log) |
|---|---|---|---|---|---|
| `yacyreta.condorwork.com.ar` | 11 | `192.1.1.191:80` — **WebLogic.191** (F&R 11g, compartido con CEFAS/DVAL/…) | 1 | 2021-12-13 | 🟢 **producción viva** — 1.60M×200, última req **hoy 17:32**, Forms `/forms/lservlet`, UA `Java/1.8.0_121`, ~10 IPs de usuario dominantes |
| `eby-prod.condorwork.com.ar` | 81 | `10.77.7.201:9001` — **OPENWLPROD01** (compartido con GIAR) | 1 | 2025-09-01 | 🟢 **producción viva** — 1.45M×200, última req **hoy 17:48**, Forms, **misma población de IPs** que `yacyreta` |
| `ords-eby.open.com.ar` | 69 | `192.1.2.54:7010` — ORDS en el WL compartido | 1 | 2024-07-23 | 🟡 **en uso** — 44.5k×200 (+ mucho 404 de bots); IPs coinciden con las de EBY |
| `ords-yacy.open.com.ar` | 80 | `10.77.7.15:8080` — **`OPENDBPROD005`** (DB destino de migración) | 1 | 2025-08-14 | ⚪ revisar log (creado ago-2025) |
| `ords-ebyqa.open.com.ar` | 91 | `10.77.7.15:8040` — **`OPENDBPROD005`** | 1 | 2026-02-05 | ⚪ **0 tráfico** (sin archivo de log) |
| `ebyprod.open.com.ar` | 82 | `10.77.8.201:9001` — **`OPENWLCLI01`** (clon "dejar apagada" de `OPENWLPROD01`, `state: Apagado`) | 1 | 2025-09-29 | 🔴 **muerto** — 8.6k×502, 783×200, solo scanner (`185.177.72.x`); apunta a una VM deliberadamente apagada |
| `eby-qa.condorwork.com.ar` | 92 | `10.77.7.201:9001` — OPENWLPROD01 | 1 | 2026-02-05 | ⚪ **0 tráfico** (sin archivo de log) |
| `yacyretatest.condorwork.com.ar` | 12 | `192.1.2.54:9002` (conf viva) | 1 | 2021-12-29 | test — no analizado en detalle |
| `yacyretatest.condorwork.com.ar:9002` | 15 | `192.1.2.54:9002` | 1 | 2021-12-28 | test (reports) |
| `yacyretatest.condor.com.ar` | 4 | `200.55.243.91:443` | 1 | 2021-12-09 | test, apunta a IP pública |

Conectividad probada desde `ssl-app-1` (`curl -skI`): todos los destinos responden (`403`/`404` en `/`, ninguno 502/timeout) — todos son middle tiers Forms/WLS/ORDS vivos. El diferenciador es el log, no la red.

**Nota (cruce con inventario, 1 sep 2026):** `10.77.7.15` = `OPENDBPROD005` (VM **encendida**, ya en `inventory.json`, nota literal `"ebyprod"`) → es la DB destino de migración de EBY, con dos ORDS apuntándole. `10.77.8.201` = `OPENWLCLI01` (clon apagado a propósito). Ambos blind spots cerrados — ver `infra/findings.md`.

**Hallazgo:** EBY corre Forms en **producción concurrente sobre dos motores** — `192.1.1.191` (que nadie mencionaba en las Discrepancias) y `10.77.7.201` (el "destino" de la fuente funcional). Solapamiento fuerte de IPs de cliente entre ambas rutas (`181.10.25.18`, `181.10.151.42`, `190.7.61.35`, `201.217.43.226`, `181.10.200.162`, `190.210.104.71`, `181.10.151.234`… — probable NAT de salida de EBY, útil para revisar reglas de firewall y para identificar tráfico EBY en otros logs). La fila "EBY / Servidor WebLogic" de Discrepancias se resuelve como **"ambos, en paralelo"**, no como uno u otro; `192.1.2.54` queda solo para ORDS + tests.

**Pendiente de capa 1:** (a) transcribir los NPM de `OPENDOCKER04` (`10.77.7.5:81`) y `VM-DOCKER-Clientes (1)` (`192.1.3.4:81`) — ambos responden desde `DOCKER-DEB`; (b) reconciliar `DOCKER-DEB-NginxProxyManager/proxy_hosts.csv` (79) contra el dump nuevo de 101 y cargar en `inventory.json` → `clients[EBY].entry_points`; (c) revisar el log de `ords-yacy`/`ords-eby` para ver si el ORDS de EBY tiene uso real; (d) los 3 `yacyretatest.*` sin verificar.

> El re-dump completo de `DOCKER-DEB` (101 proxy hosts) ya está hecho — `DOCKER-DEB-NginxProxyManager/dockerdeb_*_2026-09-01.*`. Hallazgos que exceden a EBY (ROMAN migrado a `OPENWLPROD01`, rebrand a `condor.solutions`, `serzarex`, etc.) en `infra/findings.md`.

## Orden de la sesión (qué correr, dónde)

Ordenado por información marginal: primero el box de cero cobertura.

### 1. `192.1.2.54` (`WL12C-Desarrollo`) — nunca accedido, mayor valor marginal

> Nota (1 sep 2026): para **EBY** este box quedó degradado — los logs de NPM muestran que solo sirve `ords-eby` (`:7010`) + entornos test, no el Forms productivo. Sigue siendo la visita de mayor valor **por ABB y BOCA** (datasources en una sola pantalla, cierra Tier 1 #4).

- Versión de WL sin credencial:
  `http://192.1.2.54:7001/console/login/LoginForm.jsp` → lee "Versión de WebLogic Server: …" (cierra la discrepancia `wl_version: 11` de EBY, y sirve de comparación para la de ROMAN).
- Si abre la consola: **Services → Data Sources** → leer la URL JDBC de los datasources de **EBY, ABB y BOCA** en una sola pantalla — dice literalmente a qué IP/SID apunta cada uno en producción. Cierra Tier 1 #4 (ABB) y el SID de BOCA de una. **Deployments → Monitoring** → sesiones activas por app.
- Si no hay credencial de consola: SSH forzando host keys viejos (mismo caso que `WebLogic.191`, ver `findings.md`):
  `ssh -oHostKeyAlgorithms=+ssh-rsa <cuenta>@192.1.2.54`
  - `ps -ef | grep -o -- '-Dweblogic.Name=[^ ]*'` — managed servers
  - `ps -ef | grep -i domain` — nombre y path del dominio (¿`base_domain`? ¿`ClassicDomain`? ¿Forms & Reports como `WebLogic.191` / `WL12C-PROD`?)
  - `sudo netstat -tnp | grep -E ':1521|:1525'` — asignación PID → DB (mismo método que se usó en JOBS)
  - `grep -ril -e eby -e yacyret /app/oracle/*/user_projects/domains/*/config/ 2>/dev/null` — rastro de EBY en la config

### 2. `192.1.1.191` (`WebLogic.191`) — SSH ya funciona (vía CEFAS) — **motor Forms productivo de EBY confirmado**

Los logs de NPM confirman que `yacyreta.condorwork.com.ar` sirve Forms de EBY desde acá, en producción viva. Objetivo de la sesión: qué módulos `.fmx` de EBY hay y a qué DB pegan.

- ~~`ssh -oHostKeyAlgorithms=+ssh-rsa <cuenta>@192.1.1.191`~~ ✅ hecho.
- ~~`netstat -tn` agrupado por IP de origen~~ ✅ hecho — ver capa 6: **78% de las conexiones Oracle van a `192.1.1.90`, ninguna a `192.1.1.22`**. Hallazgo principal de esta sesión.
- ~~`sudo` / `formsweb.cfg` / `tnsnames.ora`~~ ❌ **bloqueado sin sudo** — `soportesmart` no está en sudoers, y el árbol `/app/oracle/...` no es legible sin él (`oracle:oinstall`, sin permiso de "otros"). No reintentar sin credencial nueva.
- ~~`ls -la /clientes/`~~ ✅ hecho — sin carpeta EBY/Yacyretá. Cierra capa 7 (no aplica).

### 2.5. `192.1.1.90` (`Database .90`) — ✅ **resuelta (12 sep 2026)**

~~Domina el tráfico Oracle en vivo de `WebLogic.191` (14/18 conexiones) — candidata más fuerte a DB real de EBY.~~ Con la credencial `root` conseguida el 2 sep (ver `QUESTIONS.md`), `sqlplus` a `CDRADM` confirmó lo contrario: **de los 8 inquilinos de `WebLogic.191`, solo `SIGO` tiene schema propio en esta DB** (2.6 GB, uso activo el mismo día). `Database .90` queda descartada como DB de EBY — detalle completo en `infra/findings.md` → "EBY — capa 6 cerrada del todo, 7/7" y en `inventory.json` → `vms['Database .90'].db_detail`.

### 3. `10.77.7.201` (`OPENWLPROD01`) — **segundo motor Forms productivo de EBY, en progreso (2 sep 2026)**

Los logs de NPM confirman que `eby-prod.condorwork.com.ar` sirve Forms de EBY desde acá, en producción viva y concurrente con `192.1.1.191` (§2).

- ~~Versión ya confirmada (`12.2.1.4.0`)~~ ✅. Dominio identificado: **`base_domain`**, F&R 12.2.1, `/u01/app/oracle/product/12.2.1/user_projects/domains/base_domain` (mismo estilo que `WL12C-PROD`/JOBS). Managed servers: `AdminServer`, `WLS_FORMS`, `WLS_REPORTS`.
- ~~`netstat -tn | grep -E ':1521|:1525'`~~ ✅ — **3/3 conexiones reales van a `10.77.7.15`** (`OPENDBPROD005`), cero a `.22`/`.90`. Ver capa 6.
- ~~`sudo`~~ ✅ funciona acá (`ALL) ALL`) — a diferencia de `192.1.1.191`. `sudo grep -ril eby/yacyret` encontró `ebyprod.env`, `ebyqa.env`, `ebyaudit.env` bajo `.../formsapp_12.2.1/config/` — deployment dedicado confirmado.
- **Pendiente:** leer `ORACLE_SID`/`TWO_TASK` de los 3 `.env` + secciones EBY de `formsweb.cfg`/`tnsnames.ora` (comandos ya dados, en curso).
- Mismo box que GIAR — de paso, confirmar el estado real de GIAR (¿de baja o solo mantenimiento? — Tier 1 #1). Todavía sin hacer.

### 4. `10.77.8.201` = `OPENWLCLI01` — cerrado, no hace falta sesión

Resuelto por cruce con inventario (1 sep 2026): es el clon apagado a propósito de `OPENWLPROD01` (`state: Apagado`, nota "dejar apagada"). Por eso `ebyprod.open.com.ar` da 502. No requiere acción — la ruta NPM se puede deshabilitar cuando se limpie el NPM.

### 5. DB — ✅ resuelta (12 sep 2026)

~~`soportesmart` por SSH fue rechazada en los tres hosts de DB probados: `192.1.1.90` (`Database .90`), `192.1.1.22` (`OPENDBPROD006`, origen reclamado) y `10.77.7.15` (`OPENDBPROD005`, destino).~~ `root` (credencial conseguida el 2 sep, ver `QUESTIONS.md`) sí abrió `192.1.1.90`: `sqlplus` a `CDRADM` descartó esa DB para EBY (solo `SIGO` tiene schema ahí — ver §2.5). `10.77.7.15` ya no hace falta por `sqlplus` directo — su capa 6 quedó cerrada por `tnsnames.ora` oficial (§3). `192.1.1.22` queda sin acceso directo, pero también sin evidencia de tráfico real (netstat de `WebLogic.191`, 1 sep, dio 0 conexiones ahí) — no bloqueante.

## Al terminar

1. Completar `clients[EBY].weblogic.resolved` y `clients[EBY].database.resolved` en `infra/inventory.json` con el servidor y SID reales (`resolved_by: teamviewer`), y actualizar `clients[EBY].matrix_detail` (`validacion_pendiente` → resuelto, `wl_version` real).
2. Mover a "Resueltos / confirmados" en `infra/findings.md`, con fecha: la fila "EBY / Servidor WebLogic" de la tabla de Discrepancias, y — si salieron de la misma sesión — las filas de ABB (DB) y BOCA (SID). Actualizar el ítem 3 de Tier 1 en `PLAN.md`.
3. Para cada co‑inquilino con evidencia nueva (sesión activa vista, datasource leído), pasar su capa 4/6 de "identificado por nombre" a "verificado en vivo" en `inventory.json` y anotarlo en `findings.md` — es el rédito principal de haber elegido EBY.
4. Si `10.77.8.201` (o `10.77.7.15`) resultó ser algo real, sacarlo de `blind_spots` en `inventory.json` y documentarlo.
5. Regenerar `infra/topology.md` §1 si cambió el mapeo cliente → WL → DB de EBY, ABB o BOCA (recorrer `clients[]`, no editar el Mermaid a mano — ver `CLAUDE.md`).
6. Cargar el aporte de EBY a la receta generalizada (abajo) y actualizar `resumen_relevamiento_alta_cliente.md`.

## Receta generalizada (completar después de cruzar con CEFAS y JOBS)

*(Vacío a propósito — se llena cuando los tres trazados converjan, no antes.)*

**Aporte específico que se espera de EBY:** el caso "cliente con la migración BD+WL declarada 'hecha' pero sin cierre, y varios WL candidatos listados a la vez". Cómo distinguir, con la misma evidencia disponible, el WL/DB **productivo** del **destino de migración** y del **legado** cuando la documentación lista los tres sin marcar cuál está vivo — método: sesiones activas + `netstat` en vivo, no la config declarada ni la matriz. CEFAS tenía una sola migración pendiente (DB); JOBS ninguna; EBY es el del árbol de candidatos más frondoso.

## Cierre (12 sep 2026)

**EBY queda en 7 de 7 capas cerradas.** El único cabo suelto (a qué cliente correspondía la DB compartida `Database .90`/`CDRADM` detrás de la ruta legada `yacyreta`) se cerró por `sqlplus` directo: esa DB no es de EBY — de los 8 inquilinos de `WebLogic.191`, solo `SIGO` tiene schema propio ahí, en uso activo el mismo día. Bono: resuelve de paso el blind spot de `SIGO` (uno de los 4 clientes de `.191` sin VM mapeada). Detalle completo en `infra/findings.md` → "EBY — capa 6 cerrada del todo, 7/7".
