# Relevamiento de alta de cliente — camino punta a punta (EBY de referencia)

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md) y [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta. Pero **EBY se eligió por impacto, no por ser un caso limpio**: es el cliente que más infraestructura compartida toca de los 15, así que trazarlo obliga a abrir sesión en los servidores WebLogic multi‑inquilino del parque y deja mapeados de paso ~9 clientes más. Ya estaba como ítem 3 de Tier 1 en `PLAN.md` y tiene dos filas abiertas en la hoja Discrepancias de la matriz.

**Uno de tres trazados en paralelo.** CEFAS = WL compartido + una migración de DB a medio hacer + capa Docker (Self Service). JOBS = cadena dedicada, de contraste. EBY = **máximo enredo**: cuatro ubicaciones WL candidatas a la vez y BD/WL "migrados" pero sin cierre. La receta generalizada se convalida contra los tres, no contra uno.

## Por qué EBY (impacto sobre el resto del relevamiento)

EBY aparece hoy asociado a **cuatro** servidores WebLogic distintos, sin saber cuál usan los usuarios reales:

| Candidato | Qué es | Fuente | Co‑inquilinos que quedan relevados de paso |
|---|---|---|---|
| `192.1.2.54:9001` (`WL12C-Desarrollo.2.54`) | WL "reclamado" en Relevamiento / "actual, compartido" en el inventario técnico | `inventory.json` `clients[EBY].weblogic` + hoja Discrepancias | **ABB, BOCA** + `condor.open.com.ar` genérico — **box nunca accedido** |
| `10.77.7.201:9001` (`OPENWLPROD01`) | destino "funcional" según la matriz; dominios `eby-prod` / `eby-qa.condorwork.com.ar` | NPM `DOCKER-DEB` (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`) + hoja Discrepancias | **GIAR** (mismo box) |
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
| 1 | Dominio de entrada | **Casi resuelto (1 sep 2026).** `DOCKER-DEB` tiene **9 proxy hosts** EBY/Yacyretá (no 3‑4), leídos de la tabla `proxy_host` real + confirmados contra los access logs de NPM. Dos rutas Forms **en producción viva y concurrente**: `yacyreta.condorwork.com.ar` → `192.1.1.191:80` (WebLogic.191) y `eby-prod.condorwork.com.ar` → `10.77.7.201:9001` (OPENWLPROD01), ambas con ~1.5M req 200 y tráfico del mismo día. `ords-eby.open.com.ar` → `192.1.2.54:7010` en uso real. `ebyprod.open.com.ar` → `10.77.8.201` muerto (solo 502 + scanners). `eby-qa` y `ords-ebyqa` → 0 tráfico. Detalle y tabla completa abajo (§ *Capa 1 — rutas de entrada*). | (a) Revisar `OPENDOCKER04` y `VM-DOCKER-Clientes (1)` — los 2 NPM sin transcribir. (b) Re-dump completo de `proxy_host` de `DOCKER-DEB` (`count(*) = 101`, la transcripción tiene 79). (c) Cargar bloque `entry_points` en `inventory.json` → `clients[EBY]`. |
| 2 | Nginx Proxy Manager | **Parcial.** Los 4 dominios salen del NPM de `DOCKER-DEB` (`192.1.1.37:81`), ya transcripto entero. `VM-DOCKER-Clientes` (`192.1.1.38:81`, 9 proxy hosts ya transcriptos) no muestra entrada EBY — reconfirmar. | Verificar en `OPENDOCKER04` y el 4º NPM que no haya otra ruta EBY. |
| 3 | Firewall / NAT | **Parcial.** Web entra por el NAT genérico de los NPM (`200.55.243.94:80/443` → `192.1.1.37`, ruteo por Host header — mismo patrón que CEFAS/JOBS). Oracle: regla `acceso YACYRETA` → `192.1.1.22:1521`, restringida por origen. | Confirmar que no hay regla NAT dedicada hacia ninguno de los 4 WL candidatos. Anotar el alias de origen de `acceso YACYRETA`. |
| 4 | App — motor clásico | **Parcial (1 sep 2026) — media pregunta ya respondida por los logs de NPM.** EBY corre Forms en producción **en dos motores a la vez**: `192.1.1.191` (WebLogic.191, F&R 11g compartido) y `10.77.7.201` (OPENWLPROD01, compartido con GIAR). No es "uno productivo / otro legado". `192.1.2.54` solo sirve ORDS (`:7010`) + tests, no el Forms principal. Falta: entrar a los dos motores vivos y ver qué módulos `.fmx` hay desplegados en cada uno y a qué DB pega cada uno. | Sesión en `192.1.1.191` y `10.77.7.201` (orden abajo). En cada uno: `formsweb.cfg` / config de EBY, managed server, y `netstat` a `:1521/:1525` para la DB. `192.1.2.54` sigue valiendo la visita pero por ABB/BOCA, no por EBY. |
| 5 | App — capa Docker / reportes | **Abierto.** Matriz: Jasper `Sí`, Discoverer `Sí`, Self Service en blanco. | Buscar instancia Jasper de EBY (patrón `*jasper.condorwork.com.ar` → `OPENDOCKER01`, como `cefasjasper`/`jobsjasper`). Buscar contenedores `ss_*_yacyreta` en los hosts Docker por si el compose `yacyreta-sfd` sigue vivo (probable legado). |
| 6 | Base de datos | **Parcial.** `OPENDBPROD006` (`192.1.1.22`) resuelta solo por IP (`match: false`); SID sin confirmar. Destino declarado `10.77.7.15` / `EBYPROD` — **`10.77.7.15` está viva** (responde `404` en `:9001` desde el cluster, y hay un `ords-ebyqa.open.com.ar` habilitado apuntándole) pero con **0 tráfico** en el log de NPM: infra pre-provisionada, migración no cortada. Sigue sin aparecer en `ExportList.csv` ni tener regla NAT. | `sqlplus` contra `192.1.1.22` (acceso interno): `SELECT name FROM v$database;`, `ps -ef \| grep pmon`, `cat /etc/oratab`. Confirmar SID (`MBA` vs `EBYPROD`), charset, y si hay sesiones de la app. Probar `sqlplus`/`curl` contra `10.77.7.15` para ver qué corre ya ahí. |
| 7 | Almacenamiento / object store | **Abierto / probablemente no aplica.** Solo relevante si aparece un `ss_back_yacyreta` con `uploadPath` (capa 5). | Si aparece: leer su `uploadPath` y cruzar con `mount` / `/etc/fstab` del host — mismo patrón que el NFS `192.1.1.191:/clientes/cefas/cdr2/condorlink` de CEFAS. Buscar un `/clientes/yacyreta/...` en `WebLogic.191`. |

## Capa 1 — rutas de entrada (detalle, 1 sep 2026)

Sacado de la tabla `proxy_host` de `DOCKER-DEB` (`ssl-db-1`, MariaDB) + los access logs de NPM (`ssl-app-1`, `/data/logs/proxy_host-<N>.log`). Estado medido al 1 sep 2026 ~18:00.

| Dominio | id | → destino | `enabled` | `modified_on` | Estado real (por access log) |
|---|---|---|---|---|---|
| `yacyreta.condorwork.com.ar` | 11 | `192.1.1.191:80` — **WebLogic.191** (F&R 11g, compartido con CEFAS/DVAL/…) | 1 | 2021-12-13 | 🟢 **producción viva** — 1.60M×200, última req **hoy 17:32**, Forms `/forms/lservlet`, UA `Java/1.8.0_121`, ~10 IPs de usuario dominantes |
| `eby-prod.condorwork.com.ar` | 81 | `10.77.7.201:9001` — **OPENWLPROD01** (compartido con GIAR) | 1 | 2025-09-01 | 🟢 **producción viva** — 1.45M×200, última req **hoy 17:48**, Forms, **misma población de IPs** que `yacyreta` |
| `ords-eby.open.com.ar` | 69 | `192.1.2.54:7010` — ORDS en el WL compartido | 1 | 2024-05-05 | 🟡 **en uso** — 44.5k×200 (+ mucho 404 de bots); IPs coinciden con las de EBY |
| `ebyprod.open.com.ar` | 82 | `10.77.8.201:9001` | 1 | 2025-09-29 | 🔴 **muerto** — 8.6k×502, 783×200, solo ruido de scanner (`185.177.72.x`); el backend responde ahora (`404`) pero nadie lo usa |
| `eby-qa.condorwork.com.ar` | 92 | `10.77.7.201:9001` | 1 | 2026-02-16 | ⚪ **0 tráfico** (sin archivo de log) |
| `ords-ebyqa.open.com.ar` | 90 | `10.77.7.15:9001` | 1 | 2025-07-28 | ⚪ **0 tráfico** — pero `10.77.7.15` responde (`404` en `:9001`): pre-provisionado para la migración |
| `yacyretatest.condorwork.com.ar` | 12 | `192.1.2.54:9001` | 1 | 2021-12-29 | test — no analizado en detalle |
| `yacyretatest.condorwork.com.ar:9002` | 15 | `192.1.2.54:9002` | 1 | 2021-12-28 | test (reports) |
| `yacyretatest.condor.com.ar` | 4 | `200.55.243.93:443` | 1 | 2021-12-09 | test, apunta a IP pública |

Conectividad probada desde `ssl-app-1` (`curl -skI`): los 6 destinos responden (`403`/`404` en `/`, ninguno 502/timeout) — todos son middle tiers Forms/WLS vivos. El diferenciador es el log, no la red.

**Hallazgo:** EBY corre Forms en **producción concurrente sobre dos motores** — `192.1.1.191` (que nadie mencionaba en las Discrepancias) y `10.77.7.201` (el "destino" de la fuente funcional). Solapamiento fuerte de IPs de cliente entre ambas rutas (`181.10.25.18`, `181.10.151.42`, `190.7.61.35`, `201.217.43.226`, `181.10.200.162`, `190.210.104.71`, `181.10.151.234`… — probable NAT de salida de EBY, útil para revisar reglas de firewall y para identificar tráfico EBY en otros logs). La fila "EBY / Servidor WebLogic" de Discrepancias se resuelve como **"ambos, en paralelo"**, no como uno u otro; `192.1.2.54` queda solo para ORDS + tests.

**Pendiente de capa 1:** (a) `OPENDOCKER04` y `VM-DOCKER-Clientes (1)` sin transcribir; (b) re-dump completo de `proxy_host` de `DOCKER-DEB` (101 vs 79 transcriptos); (c) bloque `entry_points` en `inventory.json`; (d) los 3 `yacyretatest.*` sin verificar.

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

### 4. `10.77.8.201` — IP sin VM conocida (ruta NPM muerta, backend arriba)

Responde `404` en `:9001` (no refused) — hay un WLS/OHS vivo ahí, pero `ebyprod.open.com.ar` no lo usa nadie (solo 502 + scanners en el log). Baja prioridad, es un blind spot a cerrar.

- `curl -sv http://10.77.8.201:9001/forms/frmservlet` y `ssh <cuenta>@10.77.8.201` desde una VM del cluster — determinar qué es. Cruzar contra `ExportList.csv` (no está) y contra las IPs de host ESXi. Candidato: NIC secundaria de `OPENWLPROD01` (`10.77.7.201`) o VM apagada al momento del export.

### 5. DB — `OPENDBPROD006` (`192.1.1.22`)

- Desde adentro (la regla NAT `acceso YACYRETA` está restringida por origen):
  `sqlplus / as sysdba` → `SELECT name, open_mode FROM v$database;`
  `SELECT value FROM nls_database_parameters WHERE parameter='NLS_CHARACTERSET';` (esperado `WE8ISO8859P1`)
- `ps -ef | grep pmon` — cuántas instancias corren y con qué SID (`MBA`? `EBYPROD`? ambas?).
- `SELECT username, program, machine, count(*) FROM v$session WHERE username IS NOT NULL GROUP BY username, program, machine;` — si hay sesiones de la app EBY, esta es la DB productiva; cruzar `machine` con cuál de los 4 WL candidatos.
- `nslookup 10.77.7.15` / `ping 10.77.7.15` — ¿la VM de DB destino ya existe?

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
