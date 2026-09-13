# Resumen — relevamiento de alta de cliente (CEFAS + JOBS + EBY + BOCA + ROMAN)

Vistazo conjunto de los cuatro trazados punta a punta. Detalle completo, evidencia y pasos en [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md), [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md), [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md) y [`plan_relevamiento_alta_boca.md`](plan_relevamiento_alta_boca.md) — acá solo el estado.

## Panorama

| Capa | CEFAS | JOBS | EBY | BOCA |
|---|---|---|---|---|
| Dominio de entrada | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto |
| Nginx Proxy Manager | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto |
| Firewall / NAT | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto (+ hallazgo: `:9998` expone `.2.54:9001` a Internet) |
| App — motor clásico (WebLogic) | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto (ruta `eby-prod`) | ✅ Resuelto — `WLS_FORMS` en `192.1.2.54` |
| App — capa Docker / reportes | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto — no aplica | ✅ Resuelto — sin capa propia (`cabjjasper` ruta muerta) |
| Base de datos | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto (ruta `eby-prod`) | ✅ Resuelto — CDB `BOCA` / PDB `BOCAPDB`, schema `CONDOR` |
| Almacenamiento / object store | ✅ Resuelto | *(no aplica a este cliente)* | ✅ Resuelto — no aplica | ✅ Resuelto — no aplica |

**CEFAS, JOBS y BOCA: trazados completos, 7/7.** **EBY: 6/7** — la única nota abierta es a qué cliente corresponde cada sesión en `Database .90`/`CDRADM`, la DB compartida de la ruta paralela `yacyreta` (no bloqueante, la ruta productiva real ya está confirmada de punta a punta). **BOCA cerró su capa 6 el 12 sep 2026:** `root@192.1.1.32`, `ORACLE_SID=BOCA` reveló que es una **CDB** multitenant casi vacía — los datos reales viven en la PDB **`BOCAPDB`**, schema `CONDOR` (~22.5 GB), charset `WE8MSWIN1252` confirmado, con último DML **el mismo día de la consulta** (uso productivo activo, la mejor evidencia de capa 6 del proyecto). Resuelve la disputa "BOCA vs BOCAPDB": las dos fuentes tenían razón, a distinto nivel (CDB vs PDB) — mismo patrón que Rex/GIAR. El rédito planeado "una pantalla de consola cierra ABB de paso" **no salió** en `192.1.2.54` (sin consola ni sudo) — pero **ABB se cerró después por `sqlplus` directo con `root@192.1.1.31`: 7/7 capas**. DB productiva = `192.1.1.31` (instancia `ABB`, schema `CONDOR`); `192.1.1.190` descartada. Hallazgo colateral: **ABB apagado de hecho desde el 1‑jul‑2026** (cero sesiones/DML desde). Bonos: capa 6 en vivo para **ESYOP** (en uso, co‑inquilina de `.31`) y **DCVIAJES** (`.190`, parcial). **ROMAN: trazado formal iniciado** (sesión 6 sep) — capas 4/6/7 cerradas *a nivel config* en `OPENWLPROD01` (secciones `[csm]*` reales, `PRODCSM` → `OPENDBPROD03`, sin NFS, WL `12.2.1.4.0`), pero **sin una sola sesión/tráfico de ROMAN observado** en 5 días de logs — configurado como producción, posiblemente dormido. Capas 1-3 y 5 sin trazar. Falta: access log del NPM de `DOCKER-DEB` (`romanprod`, id 93) + `v$session` en `OPENDBPROD03`.

## CEFAS

**Descubierto:**
- **Dominio de entrada** — dos rutas activas: `cefas.condorwork.com.ar` (motor clásico) y `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` (Self Service).
- **Nginx Proxy Manager** — `VM-DOCKER-Clientes`, 9 proxy hosts, confirmado con acceso SSH real (no solo capturas).
- **Firewall / NAT** — `WAN1:80`/`443` → `192.1.1.38`. El dominio del motor clásico no tiene regla NAT propia, entra por el mismo camino vía Host header.
- **App — motor clásico** — `WebLogic.191` resultó ser **Oracle Forms & Reports 11g** (dominio `ClassicDomain`), no un WebLogic JavaEE genérico — compartido con al menos 7 clientes más (ver EBY abajo). El `connection refused` de la consola de admin quedó explicado: nunca tuvo NAT al puerto `7001`.
- **App — capa Docker (Self Service)** — `ss_back_cefas` solo tiene configurado `jdbc:postgresql://postgres:5432/selfservice` (su propio `ss_pg_cefas`); no habla con el Oracle del motor clásico. Las dos tecnologías conviven pero no comparten datos.
- **Base de datos — cuál usa hoy** — `netstat` en vivo en `WebLogic.191` confirma conexión activa a `192.1.1.32:1525` (`CLIENTES-DB`, la actual) y cero tráfico hacia `OPENDBPROD001` (destino de migración) — la migración de CEFAS todavía no cortó tráfico productivo.
- **Almacenamiento** — `VM-DOCKER-Clientes` monta por NFSv4 `192.1.1.191:/clientes/cefas/cdr2/condorlink` (el `uploadPath` de Self Service) — el servidor NFS es el mismo `WebLogic.191`, no un storage separado.
- **Base de datos — SID confirmado** — acceso logrado a `CLIENTES-DB` (`192.1.1.32`), `SELECT name FROM v$database;` devolvió **`CEFAS`** (no `CEFASPDB`). Trazado completo, las 7 capas resueltas.

**Falta:** nada — trazado de CEFAS completo.

## JOBS

**Descubierto:**
- **Dominio de entrada** — las dos rutas (`jobsprod.condorwork.com.ar` dedicado, `jobs.condorwork.com.ar` compartido con ABB/Boca) están **vivas en simultáneo**, cada una con una población de usuarios distinta — no es dedicado-real/compartido-legacy, confirmado por access logs de NPM.
- **Nginx Proxy Manager** — `DOCKER-DEB`, ya recorrido entero.
- **Firewall / NAT** — sin regla dedicada, entra por el mismo NAT del NPM de `DOCKER-DEB`.
- **App — motor clásico** — `WL12C-PROD` es Oracle Forms & Reports **12.2.1.4.0** (dominio `base_domain`, no `ClassicDomain`) — cierra la discrepancia WL 11/12 a favor del funcional. Managed servers identificados uno por uno (`AdminServer`, `WLS_FORMS1`, `WLS_REPORTS1`, `ORDS-Jobs`, `ORDS-Enerflex`, `ORDS-Open`), y su asignación a DB confirmada por PID (`sudo netstat -tnp`).
- **App — Docker/reportes** — `OPENDOCKER01` solo tiene `jasper-jobs-jasperreports-1` + su propia MariaDB — sin frontend/backend dedicado, a diferencia de CEFAS.
- **Base de datos** — `CLIENTES-DB2` (`192.1.1.51`) confirmada con NAT propio (restringido por origen), tráfico PID-a-PID verificado, y **SID exacto confirmado vía `tnsnames.ora`: `SERVICE_NAME=JOBS`**. Migración a `10.77.7.13`/`prodjobs` sigue sin VM ni NAT — tráfico productivo real sigue en `.51`.

**Falta:** nada — trazado de JOBS completo (7/7, sin capa de almacenamiento aplicable a este cliente).

## EBY

**Elegido por impacto, no por ser un caso limpio** — es el cliente que más infraestructura compartida toca de los 15 (destraba ~9 co-inquilinos). Resultó ser el trazado de mayor enredo real del parque.

**Descubierto:**
- **Dominio de entrada** — 10 proxy hosts reales en `DOCKER-DEB` (no 3-4 como se pensaba). Dos rutas Forms en **producción viva y concurrente**: `yacyreta.condorwork.com.ar` → `WebLogic.191` y `eby-prod.condorwork.com.ar` → `OPENWLPROD01` — ~1.5M requests cada una, mismo día. No es dedicado-vivo/compartido-legacy: **son dos stacks completos en paralelo**.
- **App — motor clásico** — confirmado para la ruta `eby-prod`: `OPENWLPROD01` es Forms & Reports 12.2.1 (`base_domain`), con 3 ambientes reales dedicados (`ebyprod`/`ebyqa`/`ebyaudit`, archivos `.env` + secciones de `formsweb.cfg` con sus `.fmx`). La ruta `yacyreta` (`WebLogic.191`, 11g) quedó sin poder leer su config específica por falta de sudo — no bloqueante.
- **Base de datos** — cerrada para la ruta `eby-prod`: `tnsnames.ora` real de `OPENWLPROD01` confirma alias `EBYPROD`/`EBYQA`/`EBYAUDIT` → `OPENDBPROD005` (`10.77.7.15`), coincide letra por letra con la matriz. La ruta `yacyreta` usa `Database .90`/`CDRADM`, una DB **compartida** (confirmado por `sqlplus` con credencial nueva) entre varios tenants de `WebLogic.191` — no exclusiva de EBY, nota abierta no bloqueante.
- **Almacenamiento y capa Docker** — ambos resueltos como "no aplica": sin mount NFS dedicado, sin instancia Jasper para EBY (a diferencia de CEFAS/JOBS/BOCA que sí tienen la suya).
- **Rédito colateral** — el mismo trazado (vía re-dump de NPM + `tnsnames.ora`) destrabó infraestructura nueva para **ROMAN** (WL y DB candidatos, primera vez con datos reales), **GIAR** (segunda DB candidata), **Rex Argentina** (primera DB jamás mapeada) y **Heinlein** (ambiente de test confirmado) — ninguno verificado en vivo todavía.

**Falta:** nada bloqueante. Nota abierta, no crítica: a qué cliente corresponde cada sesión activa en `Database .90`/`CDRADM` (ruta `yacyreta`).

## BOCA

**Cuarto trazado, elegido por impacto — no por ser complejo (al contrario).** Cadena más simple que queda (un WL, una DB, ya resueltos por nombre), pero tracearlo obliga a entrar por primera vez a `192.1.2.54` (`WL12C-Desarrollo`), el último WebLogic multi-inquilino sin acceder nunca — cierra de paso a **ABB** (Tier 1 #4) y da evidencia para **ESYOP**/**DCVIAJES** según a qué DB apunte ABB.

**Descubierto (sesión 6 sep 2026):**
- **Dominio / NPM / firewall** — `cabj.condorwork.com.ar` → `192.1.2.54:9001` es la ruta Forms **productiva viva** (access log de `DOCKER-DEB`: 3.84M `POST /forms/lservlet` `200`, últimos hoy, IPs residenciales AR). Los alias `boca.condorwork.com.ar` e id 17 están muertos desde 2022. Sin regla NAT dedicada; **hallazgo aparte:** `FWOPEN` regla `test` → WAN `9998` → `192.1.2.54:9001` (`source *`) expone ese Forms a Internet sin pasar por NPM.
- **App — motor clásico** — se accedió `192.1.2.54` por primera vez (SSH `soportesmart` vía ProxyJump por `DOCKER-DEB`; el puerto 22 no responde directo). Dominio `base_domain`, Oracle Forms & Reports **12.2.1.4.0**, mismo molde que JOBS/`OPENWLPROD01`. El nombre "Desarrollo" engaña: `WLS_FORMS` sirve prod real de BOCA; el box es un hub compartido Forms(prod)+ORDS(varios de test). Sin sudo / sin consola / árbol `oracle:oinstall` cerrado → no se pudo leer `tnsnames.ora` ni datasources.
- **Capa Docker / reportes** — no aplica: no hay contenedor `cabj`/`boca` en `OPENDOCKER01`, nada escucha en `:8090`, `cabjjasper` es ruta muerta. Mismo patrón que JOBS.
- **Almacenamiento** — no aplica: no hay `/clientes/boca` en `WebLogic.191` (la mención previa era un error de transcripción).

**Capa 6 cerrada (12 sep 2026):** `root@192.1.1.32`, `ORACLE_SID=BOCA`, `sqlplus` → `v$database` reveló `CDB=YES` — la CDB `BOCA` está casi vacía (solo schemas de infraestructura Oracle). Los datos reales viven en la PDB **`BOCAPDB`** (`ALTER SESSION SET CONTAINER=BOCAPDB`): schema `CONDOR` con **~22.5 GB** (2571 segmentos, coincide con los 18G de la matriz), charset `WE8MSWIN1252` confirmado dentro de la PDB. Último DML de `CONDOR`: **el mismo día de la consulta** — uso productivo activo confirmado en vivo, sin ambigüedad. La disputa "SID BOCA vs BOCAPDB" no era tal: las dos fuentes tenían razón, a distinto nivel (CDB vs PDB) — mismo patrón multitenant que Rex/GIAR (`CDBOPEN03`). **BOCA queda 7/7, trazado completo.** Ver `plan_relevamiento_alta_boca.md`.

**Rédito que no salió (de la sesión del 6 sep):** ABB. El plan contaba con leer su datasource en la consola de `192.1.2.54`, pero ese box no tiene consola ni sudo. Se resolvió después por otra vía — ver sección ABB abajo.

## ROMAN

**Quinto trazado, elegido por costo marginal casi nulo.** ROMAN corre sobre `OPENWLPROD01` — el mismo box con SSH+`sudo (ALL) ALL` ya conseguido para EBY el 2 sep. Objetivo doble: cerrar las capas baratas de una, y responder la duda que la propia matriz marca (*"¿la base/servicio es TEST o producción?"*).

**Descubierto (sesión 6 sep 2026):**
- **App — motor clásico (cerrada a nivel config)** — `formsweb.cfg` del dominio `base_domain` tiene secciones **reales** de ROMAN: `[csm]`/`[csmerp]`/`[csmFSAL]`/`[csmERPFSAL]` → `pageTitle=CSM PRODUCCION`, `userid=@PRODCSM`, `form=/u02/clientes/csm/cdr2/menues/*.fmx`; QA: `[qacsm*]` → `@QACSM`. Sin managed server propio — comparte `WLS_FORMS` con EBY/GIAR. Versión WL **`12.2.1.4.0`** — cierra la fila "ROMAN / Versión WL" de Discrepancias (era 10 vs 11).
- **Base de datos (0.9, config)** — `PRODCSM`/`QACSM` → `OPENDBPROD03` (`10.77.7.30:1525`), `SERVICE_NAME=PRODCSM`/`QACSM`, leído en vivo del `tnsnames.ora` del dominio. Charset `WE8ISO8859P1` confirmado por `csm.env`. **`romanstest` y `OPENDBDES011`** (`10.77.7.151`, la VM "Roman test" de vCenter) **descartados de la ruta productiva** — no figuran en el `formsweb.cfg` prod.
- **Almacenamiento** — no aplica: `/u02/clientes/csm` y `/qacsm` (2.5G c/u) en filesystem local de `OPENWLPROD01`, sin NFS dedicado (solo `ebyprod` tiene volumen propio).

**Falta — "en uso" sin confirmar:** 5 días de `access.log` de `WLS_FORMS` (con hábiles) no muestran **ni un request `config=csm`**, solo tráfico de EBY; `netstat` del box (sábado) sin conexiones a `.30`. ROMAN está *configurado* como producción pero puede estar dormido — coincide con `status: "Entorno actual / posible test"`. Cierre pendiente: (a) access log del NPM de `DOCKER-DEB` para `romanprod` (id 93); (b) `v$session` en `OPENDBPROD03` (bloqueado por credencial de DB). Ver `plan_relevamiento_alta_roman.md`.

**Observación de seguridad menor:** las únicas líneas "roman" en el access log son un bot escaneando backups (`/romanprod.condor.solutions.zip|.sql|.tar.gz`, todo `404`). Dominios `*.condor.solutions` enumerables y con escaneo automatizado.

## ABB

**Sexto trazado, elegido para cerrar el último cabo de Tier 1 que dependía solo de nosotros.** El plan de BOCA esperaba leer el datasource de ABB de rebote en `192.1.2.54` — imposible sin consola ni sudo. Se hizo por `sqlplus` directo con `root@192.1.1.31` (misma credencial que sirvió para `192.1.1.90` en EBY).

**Descubierto (sesión 6 sep 2026) — 7/7 capas:**
- **Base de datos (1.0)** — DB productiva = **`192.1.1.31`** (`DBClientes-12C.31`), instancia `ABB` (non‑CDB, `READ WRITE`, `NOARCHIVELOG`, arriba desde 31‑ene‑2026). Datos de la app en el schema **`CONDOR`** (~6.9 GB); el schema `ABB` del mismo box es legado (último DML 2021). Charset `WE8ISO8859P1` (= matriz). **`192.1.1.190` descartada** — no tiene instancia `ABB`, solo `abbhist`/`abbtubio` históricas apagadas; ese box es de DCVIAJES. **Discrepancia "ABB / DB actual" cerrada** a favor de la fuente funcional (`192.1.1.31 / SID ABB`).
- **Dominio / motor clásico / firewall / Docker / storage** — capas 1‑5 y 7 cerradas: `abb.condorwork.com.ar` (NPM `DOCKER-DEB` id 28) → `WLS_FORMS` en `192.1.2.54` (`base_domain`, F&R `12.2.1.4.0`, config `ABB` responde 200), sin managed server ni contenedor ni NFS dedicado; comparte con BOCA la exposición `FWOPEN` `test` → WAN `9998`.
- **Hallazgo colateral — ABB apagado de hecho desde el 1‑jul‑2026.** Access log de `abb.condorwork.com.ar` (198k líneas, oct‑2022 → hoy): última sesión Forms real el 01/07/2026 20:24 UTC; después solo 3 cargas de la pantalla de login (21‑jul, 18‑ago). El último DML del schema `CONDOR` en `.31` (`dba_tab_modifications`) es del **mismo instante** (01/07/2026 17:24 ART). No es prueba de la baja formal, pero es un dato duro que apoya la nota informal de la matriz — decisión de negocio pendiente en `QUESTIONS.md`.

**Bonos:**
- **ESYOP — capa 6 en vivo.** Co‑inquilina de `192.1.1.31` (`ora_pmon_esyop`). DB `ESYOP`, charset `WE8ISO8859P1` (= matriz), schema `CONDOR` con último DML 04/09/2026 → **en uso activo** (contraste total con ABB). Falta solo la sesión desde `WebLogic.19` para llegar a 1.0.
- **DCVIAJES — capa 6 parcial.** `192.1.1.190` (Oracle 11.2). DB `DCVIAJES` viva, charset `WE8ISO8859P1` (= matriz), schema `CONDOR` con DML del 04/09/2026 → en uso. Sin sesión capturada, AWR vacío.
- **Cabo suelto nuevo (bajo):** `192.1.1.190` lista en `/etc/oratab` instancias sin mapear — `GRIMALDI`/`GRIMA2015`/`GRIMATEMP`, `SECLA`/`SECLATEST`, `REXTEST`, `TOLEDO`. `REXTEST` podría ser el test de Rex Argentina.

**Falta:** nada bloqueante — trazado de ABB completo. No llega a 100% solo porque el cliente está apagado de hecho (no hay tráfico vivo que observar). Ver `plan_relevamiento_alta_abb.md`.
