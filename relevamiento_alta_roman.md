# Relevamiento de alta de cliente — camino punta a punta (ROMAN de referencia)

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md), [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md), [`relevamiento_alta_eby.md`](relevamiento_alta_eby.md) y [`relevamiento_alta_boca.md`](relevamiento_alta_boca.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Quinto trazado, elegido por costo marginal casi nulo + una pregunta abierta de la matriz.** ROMAN corre hoy sobre `OPENWLPROD01` (`10.77.7.201`), **el mismo box al que ya se entró por SSH con `soportesmart` + `sudo (ALL) ALL` el 2 sep 2026** para cerrar EBY. La capa 4 de ROMAN es prácticamente gratis: reconectar y leer `formsweb.cfg`/`tnsnames.ora` — que ya se leyeron completos, solo falta mirar las secciones de ROMAN. Lo genuinamente nuevo es **una** caja de DB (`OPENDBPROD03`, `10.77.7.30`) que nadie tocó nunca, y **resolver la duda que la propia matriz marca**: *"Confirmar si la base/servicio es TEST o producción."*

## Por qué ROMAN (impacto sobre el resto del relevamiento)

- **La capa 4 ya está casi hecha.** `OPENWLPROD01` es el único de los WL compartidos donde `soportesmart` tiene `sudo (ALL) ALL` (a diferencia de `WebLogic.191` y de `192.1.2.54`/BOCA, ambos sin sudo). El `tnsnames.ora` y el `formsweb.cfg` del dominio ya se volcaron el 2 sep para EBY — la parte de ROMAN es leer las secciones `[romanprod]`/`[romanqa]`/`[romanstest]` y los alias `PRODCSM`/`QACSM` que ya se sabe que están ahí.
- **Cierra la fila de Discrepancias de ROMAN.** La matriz marca dos cosas sin resolver: *"Versiones WL difieren (10 vs 11)"* y *"Confirmar si la base/servicio es TEST o producción."* La primera se cierra sola al mirar la pantalla de login del `7001` de `OPENWLPROD01` (ya confirmado **`12.2.1.4.0`** el 16 ago 2026 para GIAR en ese mismo box — cuarto caso del patrón "técnico decía 10/11, real es 12" después de GIAR, JOBS y BOCA). La segunda se cierra en la capa 6 con un `SELECT name, open_mode FROM v$database` + `v$session`.
- **Rédito colateral sobre GIAR.** `OPENWLPROD01` sirve a **EBY (cerrado), GIAR (~58%, pendiente de verificación en vivo) y ROMAN**. Una sesión de `ps -ef` / `netstat` en ese box para ROMAN deja de paso el snapshot que le falta a GIAR para pasar de "alias en `tnsnames.ora`" a "proceso/tráfico visto".
- **Primer acceso a `OPENDBPROD03` (`10.77.7.30`).** Caja de DB que no aparece en ningún trazado previo. Por ahora el `tnsnames.ora` solo la asocia a ROMAN (`PRODCSM`/`QACSM`) — menos co-inquilinos que `CLIENTES-DB` (BOCA) o `OPENDBPROD001` (Rex), pero es la que cierra la capa 6 de ROMAN y suma un host consolidado más al mapa.
- **Aclara el sitio aislado `192.1.3.252`.** El stack legado de ROMAN (`WL-CLIENTES` `172.18.5.40` + `DB-ROMAN` `172.18.5.43`) vive en el segundo host ESXi, "probablemente un sitio físico separado" según `topology.md` §2, todavía sin confirmar. Los dominios legados (`roman.condorwork.com.ar`, `roman.condorenterprise.com.ar`) están **deshabilitados** en el NPM de `VM-DOCKER-Clientes` — fuerte señal de que el legado está muerto, pero nadie lo confirmó.

## Estado de partida (6 sep 2026)

De `infra/inventory.json` → `clients[ROMAN]`, `infra/findings.md` y `infra/topology.md` §1:

- **Cliente:** `CSM Ciencia al Servicio del Movimiento S.A.` (code `ROMAN`, alias oficial **`CSM`** — de ahí los alias TNS `PRODCSM`/`QACSM`). Interfaces: Andrés Schemper (matriz `observaciones`).
- **Estado en inventario:** `"Entorno actual / posible test"` — el propio inventario ya duda de si lo que corre es prod.
- **Dos stacks, legado vs. nuevo:**
  - **Legado:** `WL-CLIENTES` (`172.18.5.40`, `resolved_by: name`, `match: true`, ESXi host `192.1.3.252`) + `DB-ROMAN` (`172.18.5.43`, reclamada `DB-02`, `resolved_by: ip`, `match: false`). Segmento aislado `172.18.5.x`. Dominios `roman.condorwork.com.ar` / `roman.condorenterprise.com.ar` → `172.18.5.40:80`, **ambos deshabilitados** en el NPM de `VM-DOCKER-Clientes` (visto 19 ago 2026). WL compartido con **Argocean** (`argocean.condorenterprise.com.ar` → mismo `172.18.5.40`, también deshabilitado).
  - **Nuevo (ruta actual):** `OPENWLPROD01` (`10.77.7.201:9001`, `resolved_by: teamviewer`). `romanprod.condor.solutions` / `romanqa.condor.solutions` → `10.77.7.201:9001`, **ambos habilitados** en el NPM de `DOCKER-DEB` (re-dump 1 sep 2026). DB: alias `PRODCSM`/`QACSM` en el `tnsnames.ora` real de `OPENWLPROD01` → `OPENDBPROD03` (`10.77.7.30`, **puerto `1525`** no 1521 — mismo patrón no estándar que `CLIENTES-DB`), `SERVICE_NAME=PRODCSM`/`QACSM` (hallado 2 sep 2026). Uptime bajo de la VM (61 días al 2 sep).
- **Tercer candidato de DB — `OPENDBDES011` (`10.77.7.151`).** VM `Oracle Linux 7`, ESXi host `192.1.1.224` (el mismo de `OPENWLPROD01`), **nota de vCenter literal "Roman test"**, 198 días de uptime. `DES` en el nombre = desarrollo/test. Encaja con `sid_actual: "TEST / romanstest"` de la matriz — candidato fuerte a la DB de **test** de ROMAN, y pieza central de la pregunta "TEST o prod". (De paso, `VINST2025` en el `tnsnames.ora` de `OPENWLPROD01` resuelve a esta misma IP — ver `findings.md` 2 sep 2026, "posible superposición de nombres".)
- **ORDS:** `ords-roman2.open.com.ar` → `10.77.7.12:8040`, **habilitado** (`10.77.7.12` **sin VM conocida** en el inventario — blind spot; la matriz también da `10.77.7.12` como `ip_db_destino` de **ABB** / `prodabb`, sin resolver). `ords-romans.open.com.ar` → `200.55.243.116:2235`, **deshabilitado**.
- **Matriz (`matrix_detail`):** `sid_actual: "TEST / romanstest"` ← **la disputa**. `version_db: 11.2.0.4.0` (Oracle 11g), `edicion_db` en blanco, `tamano: 26G`, `charset: WE8ISO8859P1` (el estándar del parque). **`servidor_db_destino` / `ip_db_destino` / `sid_nuevo` los tres en blanco** — a ROMAN la matriz no le asigna destino de migración, a diferencia de EBY/BOCA/GIAR. `version_condor: 2025`. `wl_version` reclamada: infra dice `10`, tabla funcional dice `WL 11`.
- **Productos (matriz):** Work `Sí`, Enterprise `Sí`, AFIP `Sí`, Condor Link `Sí`, Jasper `Sí`, Discoverer `Sí`, Self Service *(en blanco)*, MicroStrategy *(en blanco)*. → capa 5 = Jasper + Discoverer; el `Condor Link: Sí` es la misma pista a vigilar que en CEFAS/BOCA (puede haber un contenedor `condorlink`/`ss_*` pese al blanco en Self Service).
- **Cuenta:** `admin_user: soportesmart` — confirmada con `sudo (ALL) ALL` en `OPENWLPROD01` el 2 sep 2026. Sin credencial conocida todavía para `OPENDBPROD03` ni `OPENDBDES011`.
- **Discrepancia abierta (hoja de la matriz):** fila "ROMAN (CSM) / Versión de WebLogic" (`WL 11` vs `10`). `validacion_pendiente`: *"Versiones WL difieren (10 vs 11). Confirmar si la base/servicio es TEST o producción."*

## El camino, capa por capa

| # | Capa | Estado (6 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | ✅ **Cerrada — sin tráfico real (12/13 sep 2026).** Rutas: `romanprod.condor.solutions` (proxy host id **93**) / `romanqa.condor.solutions` (id **94**) → `10.77.7.201:9001` (`OPENWLPROD01`), ambos habilitados en `DOCKER-DEB` (contenedor `ssl-app-1`, `jc21/nginx-proxy-manager`). `proxy-host-93_access.log` + `proxy-host-94_access.log`: **0 requests `lservlet` en 5.097 requests totales** (log desde antes del 17-ago hasta hoy) — el 100% es escaneo de vulnerabilidades genérico (`wlwmanifest.xml`, `.env`, `.git/config`), IPs de bots. Coincide con el `access.log` de `WLS_FORMS` (6-sep, cero `config=csm`): **dos fuentes independientes confirman cero usuarios reales.** ORDS `ords-roman2.open.com.ar` (id 85) → `10.77.7.12:8040` sin trazar. Legado (`roman.condorwork.com.ar`, `roman.condorenterprise.com.ar` → `172.18.5.40`) y `ords-romans.open.com.ar` → `200.55.243.116:2235`: deshabilitados. | Ninguno bloqueante. *Completeness*: `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` sin otra ruta ROMAN; clasificar `ords-roman2` si se necesita cerrar del todo. |
| 2 | Nginx Proxy Manager | 🟡 **Identificado.** NPM actual = `DOCKER-DEB` (`192.1.1.37:81`) — las rutas `condor.solutions` de ROMAN están en su MariaDB interna. NPM legado = `VM-DOCKER-Clientes` (`192.1.1.38`) — tiene las entradas `roman.condorwork.com.ar` (id 4) y `roman.condorenterprise.com.ar` (id 6), ambas `enabled=0` desde 2022. | *Completeness*: confirmar que `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` (los 2 NPM sin transcribir) tampoco tengan entradas ROMAN. |
| 3 | Firewall / NAT | ⬜ **Sin trazar.** Hipótesis (mismo patrón que CEFAS/JOBS/EBY/BOCA): la ruta web de ROMAN entra por el NAT genérico de `DOCKER-DEB` (`200.55.243.94:80/443` → `192.1.1.37`), ruteo por Host header, sin regla dedicada. | Revisar `inventory.json` → `vms[FWOPEN].nat_rules.rules` buscando cualquier regla a `10.77.7.201:9001`, a `172.18.5.40`, o a `200.55.243.116:2235` (la IP del ORDS legado deshabilitado — ver si `.116` es una WAN de `FWOPEN` y si ese puerto `2235` sigue expuesto aunque el proxy host esté off). |
| 4 | App — motor clásico | ✅ **Cerrada a nivel config (6 sep 2026).** `OPENWLPROD01` / `WLS_FORMS` (compartido con EBY/GIAR, **sin managed server propio de ROMAN**). `formsweb.cfg` del dominio `base_domain` tiene secciones **reales** de ROMAN: `[csm]`/`[csmerp]`/`[csmFSAL]`/`[csmERPFSAL]` → `pageTitle=CSM PRODUCCION`, `userid=@PRODCSM`, `form=/u02/clientes/csm/cdr2/menues/{cdr2w,cdr2,finit}.fmx`, `envFile=csm.env`; QA: `[qacsmFSAL]`/`[qacsmerpFSAL]` → `userid=@QACSM`, `/u02/clientes/qacsm/...`. `csm.env` solo setea `FORMS_PATH` + `NLS_LANG=AMERICAN_AMERICA.WE8ISO8859P1` (sin `ORACLE_SID`/`TWO_TASK` — la DB la fija el alias `@PRODCSM`). **Versión WL = `12.2.1.4.0`** — cierra la disputa 10-vs-11 de la matriz a favor del 12. **Falta:** sesión/tráfico en vivo (ver capa 1). | Ninguno bloqueante para la config. La confirmación "en uso" viene de la capa 1 (access log NPM) o la capa 6 (`v$session`). |
| 5 | App — capa Docker / reportes | ⬜ **Sin trazar.** Matriz: Jasper `Sí`, Discoverer `Sí`, Condor Link `Sí`. | `grep -iE 'roman|csm' DOCKER-DEB-NginxProxyManager/proxy_hosts.csv` — ¿hay `romanjasper.*` / `roman.condorlink.*`? Si aparece, `sudo docker ps -a` en el host destino (probable `OPENDOCKER01` `192.1.1.110`, ya recorrido para JOBS/BOCA) `| grep -iE 'roman|csm'`. El `Condor Link: Sí` con `Self Service` en blanco es el mismo caso que CEFAS/BOCA — vigilar un `ss_front_roman`/`condorlink` aunque no esté declarado. |
| 6 | Base de datos | 🟡 **Cerrada a nivel config (0.9), sin verificación en vivo (1.0).** Config productiva → **`OPENDBPROD03`** (`10.77.7.30:1525`), alias `PRODCSM`/`QACSM`, `SERVICE_NAME=PRODCSM`/`QACSM` (leído en vivo del `tnsnames.ora` del dominio). Charset `WE8ISO8859P1` confirmado por `csm.env`. **Descartados de la ruta productiva:** `romanstest` y `OPENDBDES011` (`10.77.7.151`, la VM "Roman test" de vCenter) — no aparecen en el `formsweb.cfg` productivo; `DB-ROMAN` (`172.18.5.43`) legado, sin señal. `netstat` de `OPENWLPROD01` (sábado, box ocioso): 0 conexiones Oracle a `.30`. | (a) `v$session` en `OPENDBPROD03` / `PRODCSM` — **bloqueado por credencial de DB** (misma situación que `10.77.7.15`/`.22`; ver `QUESTIONS.md`). (b) Mientras tanto: `netstat -tn` en `OPENWLPROD01` un día hábil, ver si aparece tráfico a `10.77.7.30:1525`. |
| 7 | Almacenamiento / object store | ✅ **Cerrada — no aplica (6 sep 2026).** `/u02/clientes/csm` y `/u02/clientes/qacsm`: 2.5G c/u, `oracle:oinstall`, creados 3-mar-2026, en el **filesystem local** de `OPENWLPROD01`. `mount`/`fstab`: el único volumen dedicado bajo `/u02/clientes/` es `ebyprod` (`vg--eby-lv--eby`) — ROMAN no tiene mount NFS ni volumen propio. | Ninguno. Cabo suelto no crítico: si Condor Link (matriz `Sí`) está vivo, podría haber un `/u02/clientes/csm/.../condorlink` — reabrir solo con evidencia de Condor Link. |

## Sesión 6 sep 2026 — qué se cerró

SSH + `sudo (ALL) ALL` a `OPENWLPROD01` (reusando el acceso del 2 sep de EBY). Resultado:

- **Capa 4 cerrada a nivel config.** ROMAN corre (está *configurado*) en `WLS_FORMS`, compartido con EBY/GIAR. Secciones `[csm]`/`[csmerp]`/`[csmFSAL]`/`[csmERPFSAL]` → "CSM PRODUCCION", `userid=@PRODCSM`. QA → `@QACSM`. WL `12.2.1.4.0` (cierra 10-vs-11).
- **Capa 6 a 0.9.** `PRODCSM`/`QACSM` → `10.77.7.30:1525` (`OPENDBPROD03`). **`romanstest` / `OPENDBDES011` quedan descartados de la ruta productiva** — la config no los usa. Charset `WE8ISO8859P1` confirmado.
- **Capa 7 cerrada — no aplica.** `/u02/clientes/csm` + `/qacsm` (2.5G c/u) en filesystem local, sin NFS.
- **Cabo abierto — "en uso" sin confirmar.** 5 días de `access.log` de `WLS_FORMS` (Sep 2–6, con hábiles): **cero `config=csm`**, solo tráfico de EBY. Las únicas líneas "roman" son un bot escaneando backups (`/romanprod.condor.solutions.zip` etc., 404). `netstat` del box (sábado): 0 conexiones a `.30`. **ROMAN está configurado como producción pero sin tráfico observado** — coincide con `status: "Entorno actual / posible test"`.
- **Observación de seguridad menor:** los dominios `*.condor.solutions` son enumerables y hay bots escaneando `romanprod`/`romanqa` por archivos de backup expuestos. Anotado en `findings.md`.

## Sesión 12/13 sep 2026 — capa 1 cerrada, credencial de DB sigue bloqueada

- **Capa 1 cerrada — sin tráfico real.** Acceso a `DOCKER-DEB` (`192.1.1.37`), NPM en contenedor `ssl-app-1`. `proxy-host-93_access.log` (`romanprod`) + `proxy-host-94_access.log` (`romanqa`): **0 requests `lservlet` en 5.097 requests totales**, 100% escaneo de vulnerabilidades (bots). Junto con el `access.log` de `WLS_FORMS` (6-sep), son **dos fuentes independientes** confirmando cero uso real de ROMAN por esta ruta.
- **Credencial de DB probada y rechazada.** `ssh root@10.77.7.30` (`OPENDBPROD03`) falló — el mismo `root` que cerró la capa 6 de BOCA el mismo día (`192.1.1.32`) no sirve en el segmento `10.77.7.x`. Tampoco funcionó en `.151` (`OPENDBDES011`) ni `.15` (DB de EBY). Capa 6 sigue en 0.9. Ver `QUESTIONS.md`.
- **Nota operativa:** `soportesmart` falló una vez al conectar a `.37` y entró en el reintento — sin causa clara, no reproducido en otro host. Si vuelve a pasar, probar en paralelo contra `192.1.1.191` y `10.77.7.201` para distinguir problema de cuenta vs. de host puntual.
- **Tercera ruta revisada — `ords-roman2.open.com.ar` (id 85, → `10.77.7.12:8040`), mismo resultado y algo más.** `proxy-host-85_access.log`: 322 requests totales, **305 `499`** (nginx sin respuesta del backend) + **9 `504`** (timeout) = 95% fallas de backend. Los 8 restantes: 5× `200` (renovación de certificado Let's Encrypt, `/.well-known/acme-challenge/` — no es tráfico de aplicación) + 3× `400`. **Cero requests de aplicación real, y el backend `10.77.7.12:8040` probablemente ni está levantado** — coincide con que `.12` es blind spot sin VM en el inventario.
- **Balance:** ROMAN queda con **6 de 7 capas cerradas** (1, 2, 4, 6 —a nivel config—, 7; falta 3 y 5 por trazar, bajo costo) y la confirmación, ahora por **tres rutas independientes** (Forms vía `WLS_FORMS`, `romanprod`/`romanqa`, y `ords-roman2`), de que **ROMAN está configurado como producción de punta a punta pero sin un solo usuario activo**. El único paso que falta para 100% es `v$session` en `OPENDBPROD03`, bloqueado por credencial.

## Capa 1 — rutas de entrada (detalle)

Sacado de `DOCKER-DEB-NginxProxyManager/dockerdeb_proxy_host_2026-09-01.tsv` + `proxy_hosts.csv` y de `source-files/VM-DOCKER-Clientes.md`.

| Dominio | id | NPM | → destino | `enabled` | Nota |
|---|---|---|---|---|---|
| `romanprod.condor.solutions` | 93 | `DOCKER-DEB` | `10.77.7.201:9001` — `OPENWLPROD01` (Forms, compartido con EBY + GIAR) | 1 | creado 2026-03-03; **ruta actual probable** |
| `romanqa.condor.solutions` | 94 | `DOCKER-DEB` | `10.77.7.201:9001` | 1 | mod. 2026-06-17 — la más nueva |
| `ords-roman2.open.com.ar` | 85 | `DOCKER-DEB` | `10.77.7.12:8040` — sin VM conocida | 1 | creado 2026-01-12; `.12` es blind spot (también `ip_db_destino` de ABB en la matriz) |
| `ords-romans.open.com.ar` | 47 | `DOCKER-DEB` | `200.55.243.116:2235` | 0 | de 2023, deshabilitado |
| `roman.condorwork.com.ar` | 4 | `VM-DOCKER-Clientes` | `172.18.5.40:80` — `WL-CLIENTES` (legado, sitio `192.1.3.252`) | 0 | deshabilitado desde 2022 |
| `roman.condorenterprise.com.ar` | 6 | `VM-DOCKER-Clientes` | `172.18.5.40:80` | 0 | deshabilitado desde 2022 |

El patrón habilitado/deshabilitado dice "ROMAN migró de `WL-CLIENTES` (`172.18.5.40`, sitio aislado) al WL compartido `OPENWLPROD01`" — mismo movimiento que EBY y GIAR — pero **sin confirmar en vivo** (nadie vio procesos/tráfico de ROMAN en `OPENWLPROD01` todavía, solo el estado del NPM y el alias TNS).

## Orden de la sesión (qué correr, dónde)

Ordenado por información marginal: primero el box donde una sola sesión cierra capas 4, 6 (por `netstat`) y 7, y de paso ayuda a GIAR.

### 1. `OPENWLPROD01` (`10.77.7.201`) — ya accesible con `sudo (ALL) ALL`

**Cómo se entró (2 sep 2026, para reusar):** SSH directo con `soportesmart` (host key vieja — agregar `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa` si el cliente lo pide). `sudo` sin restricción.

Correr, en orden:

1. `sudo grep -iE 'roman|csm' /u01/app/oracle/product/12.2.1/user_projects/domains/base_domain/config/fmwconfig/servers/*/applications/formsapp_*/config/formsweb.cfg` (ajustar la ruta al `formsweb.cfg` real ya localizado el 2 sep) — secciones `[romanprod]`/`[romanqa]`/`[romanstest]`, ver `form=`, `userid=` (si está preconfigurado), y a qué alias TNS apuntan.
2. `sudo grep -iE -A4 'PRODCSM|QACSM|ROMAN' .../tnsnames.ora` — confirmar `HOST`/`PORT`/`SERVICE_NAME` de cada alias (ya visto: `PRODCSM`/`QACSM` → `10.77.7.30:1525`). Ver si hay un alias `ROMANSTEST` / `romanstest` apuntando a `10.77.7.151` (`OPENDBDES011`).
3. `ps -ef | grep -o -- '-Dweblogic.Name=[^ ]*' | sort -u` — inventario de managed servers; identificar el de ROMAN o confirmar que comparte `WLS_FORMS` con EBY/GIAR.
4. `netstat -tn | grep -E ':1521|:1525'` — **el dato clave de la capa 6**: a qué IP de DB van las conexiones reales. `.30` → stack nuevo; `.151` → TEST; `172.18.5.43` → legado vivo (improbable).
5. `sudo ls -la /u02/clientes/ | grep -iE 'roman|csm'` + `mount | grep clientes` — capa 7.
6. `curl -s http://127.0.0.1:7001/console/login/LoginForm.jsp | grep -i version` (o mirar la pantalla) — cierra `10 vs 11` → `12.2.1.4.0`.

**Rédito GIAR de paso:** en el mismo `ps -ef` / `netstat`, anotar cualquier proceso/coneción atribuible a GIAR (`giar`, `10.10.1.9`, `10.77.7.11`/`PRODGIAR`) — es lo que le falta a GIAR para pasar de "alias TNS" a "verificado en vivo".

### 2. DB ganadora del `netstat` (`OPENDBPROD03` `10.77.7.30:1525` **o** `OPENDBDES011` `10.77.7.151`) — cierre de capa 6

Depende de conseguir credencial (no hay una conocida para estos dos hosts todavía — ver `QUESTIONS.md`, misma situación que `.22`/`10.77.7.15`). Si se consigue: `sqlplus` → `v$database` (dirime `PRODCSM` vs `romanstest` → **cierra la pregunta "TEST o producción"**), `nls_database_parameters` (charset), `v$session` (esperar `machine=10.77.7.201`, usuarios nominales de ROMAN — mismo tipo de evidencia que cerró Rex Argentina el 6 sep).

### 3. `DOCKER-DEB` (`192.1.1.37`) — capas 1 y 5, sin sesión nueva

Los access logs (`/data/logs/proxy_host-*.log` o equivalente, ya usados para EBY/BOCA) clasifican `romanprod` / `romanqa` / `ords-roman2` por tráfico real. `grep -iE 'roman|csm'` sobre `proxy_hosts.csv` para descartar/encontrar Jasper o Condor Link de ROMAN.

## Al terminar

1. Completar `clients[ROMAN].weblogic.resolved` (dominio, managed servers, versión real `12.2.1.4.0`) y `clients[ROMAN].database.resolved` (SID real, `service_name_confirmed`, `resolved_by: teamviewer`, cuál de `.30`/`.151`/`.43` está en uso) en `infra/inventory.json`. Actualizar `clients[ROMAN].matrix_detail`: `validacion_pendiente` → resuelto, `wl_version` real, y **la respuesta explícita a "TEST o producción"**.
2. Mover a "Resueltos / confirmados" en `infra/findings.md`, con fecha: la fila "ROMAN (CSM) / Versión de WebLogic" de la tabla de Discrepancias, y la nota sobre `OPENDBDES011` ("Roman test") como candidato — resuelto a favor / en contra según el `netstat`.
3. Según el resultado del `netstat`: marcar el stack legado (`WL-CLIENTES` `172.18.5.40` + `DB-ROMAN` `172.18.5.43`) como **confirmado muerto** o **todavía con tráfico**; si muerto, anotarlo en el ítem 2 de "Todavía abierto" de `findings.md` (el sitio `192.1.3.252`) — un tenant menos que justifica mantener ese sitio.
4. Si salió evidencia en vivo de **GIAR** en la misma sesión (proceso/tráfico en `OPENWLPROD01`): pasar su capa 4/6 de "alias en `tnsnames.ora`" a "verificado en vivo" en `inventory.json` y anotarlo en `findings.md`.
5. `10.77.7.12` (`ords-roman2`) y — si aparece — cualquier VM nueva detrás de `.30`/`.151`: revisar contra `blind_spots` en `inventory.json`.
6. Regenerar `infra/topology.md` §1 si cambió el mapeo cliente → WL → DB de ROMAN (recorrer `clients[]`, no editar el Mermaid a mano — ver `CLAUDE.md`). Los nodos actuales de ROMAN (`n_WL_CLIENTES`, `n_DB_ROMAN`, `n_OPENDBPROD03`, `n_OPENWLPROD01`) están curados a mano — actualizarlos con la evidencia del trazado.
7. Actualizar `verificacion_completitud_clientes.md` (score por capa de ROMAN) y `resumen_relevamiento_alta_cliente.md`; cargar el aporte de ROMAN a la receta generalizada.

## Receta generalizada (completar cuando converjan CEFAS + JOBS + EBY + BOCA + ROMAN)

*(Vacío a propósito — se llena cuando los trazados converjan, no antes.)*

**Aporte específico que se espera de ROMAN:** el caso "cliente que **ya migró** al box nuevo compartido (`OPENWLPROD01`), cuyo stack legado (`WL-CLIENTES`/`DB-ROMAN` en el sitio aislado `192.1.3.252`) **parece muerto pero nadie lo confirmó**, y cuya pregunta central es de **higiene de metadato**: ¿lo que corre en producción es realmente producción o es la base de TEST (`romanstest` / `OPENDBDES011`)? — se responde con `netstat` desde el WL + `v$database` en la DB." Contraste con EBY (dos stacks vivos en paralelo), BOCA (box compartido sin sudo, todo por la DB), Rex Argentina (confirmado en vivo por `v$session` en una CDB compartida) y CEFAS/JOBS (cadena dedicada ya accesible). ROMAN aporta además el primer trazado hasta `OPENDBPROD03` y la prueba de si el sitio `192.1.3.252` tiene todavía un tenant vivo o es puro legado apagable.
