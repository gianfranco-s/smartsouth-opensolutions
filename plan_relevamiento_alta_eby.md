# Relevamiento de alta de cliente — camino punta a punta (EBY de referencia)

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md) y [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta. Pero **EBY se eligió por impacto, no por ser un caso limpio**: es el cliente que más infraestructura compartida toca de los 15, así que trazarlo obliga a abrir sesión en los servidores WebLogic multi‑inquilino del parque y deja mapeados de paso ~9 clientes más. Ya estaba como ítem 3 de Tier 1 en `PLAN.md` y tiene dos filas abiertas en la hoja Discrepancias de la matriz.

**Uno de tres trazados en paralelo.** CEFAS = WL compartido + una migración de DB a medio hacer + capa Docker (Self Service). JOBS = cadena dedicada, de contraste. EBY = **máximo enredo**: arrancó con cuatro ubicaciones WL candidatas; al 1 sep 2026 los logs de NPM confirmaron que corre en producción sobre **dos motores a la vez** (`192.1.1.191` + `10.77.7.201`), el tercero (`10.77.8.201`) es un clon apagado y el cuarto (`192.1.2.54`) solo sirve ORDS. La receta generalizada se convalida contra los tres, no contra uno.

**Estado al 1 sep 2026:** capas 1–3 cerradas (rutas de entrada, NPM y firewall/NAT — mismo nivel de evidencia que CEFAS/JOBS). Capas 4–7 abiertas y todas dependen de **una sola sesión SSH pendiente** a `192.1.1.191` + `10.77.7.201` + `sqlplus` a las dos DBs — ninguna sesión de este trazado tocó todavía un WebLogic (fueron todas a NPM/`DOCKER-DEB`).

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
| 4 | App — motor clásico | **Parcial (1 sep 2026) — media pregunta ya respondida por los logs de NPM.** EBY corre Forms en producción **en dos motores a la vez**: `192.1.1.191` (WebLogic.191, F&R 11g compartido) y `10.77.7.201` (OPENWLPROD01, compartido con GIAR). No es "uno productivo / otro legado". `192.1.2.54` solo sirve ORDS (`:7010`) + tests, no el Forms principal. Falta: entrar a los dos motores vivos y ver qué módulos `.fmx` hay desplegados en cada uno y a qué DB pega cada uno. | Sesión en `192.1.1.191` y `10.77.7.201` (orden abajo). En cada uno: `formsweb.cfg` / config de EBY, managed server, y `netstat` a `:1521/:1525` para la DB. `192.1.2.54` sigue valiendo la visita pero por ABB/BOCA, no por EBY. |
| 5 | App — capa Docker / reportes | **Abierto.** Matriz: Jasper `Sí`, Discoverer `Sí`, Self Service en blanco. | Buscar instancia Jasper de EBY (patrón `*jasper.condorwork.com.ar` → `OPENDOCKER01`, como `cefasjasper`/`jobsjasper`). Buscar contenedores `ss_*_yacyreta` en los hosts Docker por si el compose `yacyreta-sfd` sigue vivo (probable legado). |
| 6 | Base de datos | **Parcial — origen y destino ya identificados como VMs reales.** Origen: `OPENDBPROD006` (`192.1.1.22`), SID actual `MBA` sin confirmar. **Destino: `10.77.7.15` = `OPENDBPROD005`** — VM encendida, ya en `inventory.json`, nota literal `"ebyprod"` (= SID `EBYPROD` de la matriz), con dos ORDS habilitados apuntándole (`ords-yacy` :8080, `ords-ebyqa` :8040). Falta: SID/charset exactos de ambas y si la migración ya movió tráfico. | `sqlplus` contra `192.1.1.22` **y** `10.77.7.15` (acceso interno): `SELECT name FROM v$database;`, `ps -ef \| grep pmon`, `cat /etc/oratab`. En `OPENWLPROD01` (`10.77.7.201`), `netstat -tn \| grep 1521` para ver a cuál de las dos pega hoy el Forms de EBY. |
| 7 | Almacenamiento / object store | **Abierto / probablemente no aplica.** Solo relevante si aparece un `ss_back_yacyreta` con `uploadPath` (capa 5). | Si aparece: leer su `uploadPath` y cruzar con `mount` / `/etc/fstab` del host — mismo patrón que el NFS `192.1.1.191:/clientes/cefas/cdr2/condorlink` de CEFAS. Buscar un `/clientes/yacyreta/...` en `WebLogic.191`. |

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

- `ssh -oHostKeyAlgorithms=+ssh-rsa <cuenta>@192.1.1.191`
- `netstat -tn` agrupado por IP de origen — sesiones activas hacia EBY y hacia el resto de inquilinos (DVAL, UIA, Mafisa, SIGO, DCViajes, Tassaroli). Cada IP de cliente con conexiones = evidencia de que ese cliente está vivo acá **ahora**.
- Si se consigue `sudo` (la vez de CEFAS no había): `formsweb.cfg` y `tnsnames.ora` bajo `Oracle_FRHome1` — mapea cada `config` de Forms a su cliente y su TNS de DB. Esto cierra capas 4 y 6 para **6 clientes de un saque**.
- `ls -la /clientes/` — ver si hay un `/clientes/yacyreta/...` además del `/clientes/cefas/...` ya conocido (capa 7).

### 3. `10.77.7.201` (`OPENWLPROD01`) — **segundo motor Forms productivo de EBY confirmado**

Los logs de NPM confirman que `eby-prod.condorwork.com.ar` sirve Forms de EBY desde acá, en producción viva y concurrente con `192.1.1.191` (§2). Ya no es "el destino de migración a validar" — está en uso.

- Versión ya confirmada (`12.2.1.4.0`, ver `findings.md`); reintentar la consola.
- **Deployments / `formsweb.cfg`** → qué app/módulos EBY hay `Active` acá, y en qué se diferencian de los de `192.1.1.191` (¿misma app en dos sitios? ¿módulos distintos? ¿migración a medias?).
- `netstat -tn | grep -E ':1521|:1525'` — a qué DB pega el Forms de EBY desde este box.
- Mismo box que GIAR — de paso, confirmar el estado real de GIAR (¿de baja o solo mantenimiento? — Tier 1 #1).

### 4. `10.77.8.201` = `OPENWLCLI01` — cerrado, no hace falta sesión

Resuelto por cruce con inventario (1 sep 2026): es el clon apagado a propósito de `OPENWLPROD01` (`state: Apagado`, nota "dejar apagada"). Por eso `ebyprod.open.com.ar` da 502. No requiere acción — la ruta NPM se puede deshabilitar cuando se limpie el NPM.

### 5. DB — origen `OPENDBPROD006` (`192.1.1.22`) y destino `OPENDBPROD005` (`10.77.7.15`)

Las dos son VMs reales del inventario. Falta el `sqlplus` a cada una.

- Desde adentro (la regla NAT `acceso YACYRETA` está restringida por origen), en **ambos** hosts:
  `sqlplus / as sysdba` → `SELECT name, open_mode FROM v$database;`
  `SELECT value FROM nls_database_parameters WHERE parameter='NLS_CHARACTERSET';` (esperado `WE8ISO8859P1`)
- `ps -ef | grep pmon` — SID(s) corriendo (`MBA` en el origen, `EBYPROD`/`ebyprod` en el destino).
- En `OPENWLPROD01` (`10.77.7.201`) y `WebLogic.191` (`192.1.1.191`): `netstat -tn | grep 1521` — a cuál de las dos DBs pega hoy el Forms de EBY. Si todo va a `192.1.1.22` y nada a `10.77.7.15`, la migración no cortó (mismo patrón que CEFAS/JOBS).

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
