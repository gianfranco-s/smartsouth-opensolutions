# Relevamiento de alta de cliente — camino punta a punta (BOCA de referencia)

> ✅ **CERRADO — 7/7 capas (12 sep 2026).** Capa 6 cerrada en `CLIENTES-DB` (`192.1.1.32`, `root`): la instancia `ORACLE_SID=BOCA` es una **CDB** multitenant, prácticamente vacía a nivel raíz; los datos reales viven en la **PDB `BOCAPDB`** (`READ WRITE`), schema `CONDOR` (~22.5 GB, coincide con los 18G de la matriz), charset `WE8MSWIN1252` confirmado. **Último DML de `CONDOR`: 12/09/2026 21:37 — el mismo día de la consulta**, uso productivo activo confirmado en vivo. La disputa "BOCA vs BOCAPDB" de Discrepancias no era tal: las dos fuentes tenían razón, a distinto nivel (CDB vs PDB) — mismo patrón que Rex/GIAR (`CDBOPEN03`). Detalle en `infra/findings.md` ("Resueltos / confirmados", 12 sep 2026) y `infra/inventory.json` (`clients[BOCA].database.resolved`). Lo de abajo es el plan tal como se ejecutó.

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md), [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) y [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Cuarto trazado, elegido por impacto — no por ser complejo (al contrario).** BOCA tiene la cadena más simple que queda: **un** WebLogic (`WL12C-Desarrollo.2.54`) y **una** DB (`CLIENTES-DB`), los dos ya resueltos por nombre+IP, sin migración de WL pendiente (`status: "Destino definido / sin WL nuevo"`). Se elige igual porque tracearlo **obliga a entrar por primera vez a `192.1.2.54`** — el último WebLogic multi‑inquilino del parque que nadie accedió nunca — y esa sola sesión deja evidencia en vivo para varios clientes más.

> ⚠️ **Restricción operativa (matriz):** *"No realizar tareas los domingos"* para BOCA. Cualquier sesión que toque `192.1.2.54` o `192.1.1.32` en día/horario sensible respeta esto.

## Por qué BOCA (impacto sobre el resto del relevamiento)

`192.1.2.54` (`WL12C-Desarrollo.2.54`) sirve, en la misma instancia:

| Co‑inquilino | Qué corre ahí | Qué se cierra al leer sus datasources / sesiones |
|---|---|---|
| **ABB** | Forms en `:9001` (`abb.condorwork.com.ar`) | **Tier 1 #4** — cuál de `192.1.1.31` (`DBClientes-12C.31`) vs `192.1.1.190` (`DBClientes.190`) es la DB productiva. Se lee de la URL JDBC en una pantalla. |
| **EBY** (cola) | ORDS en `:7010` (`ords-eby.open.com.ar`) | último cabo suelto de EBY — ver `plan_relevamiento_alta_eby.md` capa 1. |
| `condor.open.com.ar` | Forms genérico en `:9001` | dominio sin cliente asignado — clasificarlo. |
| **JOBS** (test) | ORDS en `:7002` (`ords-jobst.open.com.ar`) | ya mapeado, confirma de paso. |
| Yacyretá test | `:9002` | entornos test de EBY. |

Y por herencia de las DBs de **ABB**:

- Si el datasource de ABB apunta a **`192.1.1.31`** → esa DB la comparte con **ESYOP** (`WebLogic.19`, resuelto por IP `match: false`) → ESYOP gana verificación de capa 6 en vivo.
- Si apunta a **`192.1.1.190`** → la comparte con **DCVIAJES** (`WebLogic.191`) → ídem DCVIAJES.

> ⚠️ **Ajuste tras la sesión del 6 sep:** `192.1.2.54` **sí corre el Forms productivo de BOCA** (`WLS_FORMS`, confirmado por access log), pero **no tiene credencial de consola ni sudo** — no se pueden leer los datasources. El rédito "una pantalla cierra ABB+BOCA+EBY" **no aplica**: hay que cerrar cada uno por su DB. Para BOCA eso es barato (capa 6, `CLIENTES-DB` ya accesible). Para **ABB** hay que buscar otra vía — su datasource no es legible desde `.2.54`; queda Tier 1 #4 abierto, a resolver por `sqlplus`/`v$session` en `192.1.1.31` y `192.1.1.190` directamente.

**Ventaja sobre EBY:** casi todas las capas de BOCA cierran barato porque la infra ya está tocada:

- **DB (`CLIENTES-DB` / `192.1.1.32`) ya es accesible.** Se logró acceso el 25 ago 2026 en el trazado de CEFAS, y `ps -ef | grep pmon` **ya mostró `ora_pmon_BOCA`** corriendo ahí, junto a `ora_pmon_CEFAS` y `ora_pmon_wl12prod`. Capa 6 = reconectar y correr un `SELECT`.
- **Jasper (`cabjjasper` → `192.1.1.110:8090`) está en `OPENDOCKER01`**, el mismo host donde ya se hizo `docker ps` para JOBS.
- Lo único genuinamente nuevo es el box `192.1.2.54`.

## Estado de partida (6 sep 2026)

De `infra/inventory.json` → `clients[BOCA]`, `infra/findings.md` y `infra/topology.md` §1:

- **WL:** `WL12C-Desarrollo.2.54` (`192.1.2.54`), `resolved_by: name`, `match: true`. `wl_version` reclamada **`12.2`** (sin verificar en vivo — mismo patrón 11/12 ya corregido en GIAR y JOBS a favor del 12). ESXi host reclamado `192.1.1.214`.
- **DB:** `CLIENTES-DB` (`192.1.1.32`), `resolved_by: name`, `match: true`. Compartida con **CEFAS** (`ora_pmon_CEFAS`, SID `CEFAS` ya confirmado ahí) y con el schema de dominio de **JOBS** (`ora_pmon_wl12prod`).
- **Matriz:** `sid_actual: "BOCA / BOCAPDB"` ← **la disputa**. `version_db: 19.24.0.0.0` (Oracle **19c** — la más nueva de todos los clientes del parque), `edicion: SE`, `tamaño: 18G`, `charset: WE8MSWIN1252` (**Windows‑1252 — distinto del `WE8ISO8859P1` de casi todos los demás**, vale confirmarlo). Destino: `BD 10.77.7.13` / SID `prodboca`. `version_condor: 2025`.
- **`10.77.7.13`** es blind spot: la matriz también lo da como destino de **JOBS** (`prodjobs`), y no resuelve a ninguna VM ni tiene regla NAT. Tráfico productivo sigue en `.32`.
- **Productos (matriz):** Work `Sí`, Condor Link `Sí`, Jasper `Sí`, Discoverer `Sí`, Self Service *(en blanco)*. → capa 5 = Jasper (`cabjjasper`, confirmado por NPM) + Discoverer. El `Condor Link: Sí` es una pista a vigilar: puede haber un contenedor tipo `condorlink`/Self Service pese al blanco en Self Service (mismo caso que CEFAS, donde Condor Link = `cefas.condorlink.com.ar` → `ss_front_cefas`).
- **Estado en inventario:** `"Destino definido / sin WL nuevo"` — BOCA **no** tendría WebLogic nuevo, se queda en `.2.54`; solo migración de DB a `.13`.
- **Cuenta:** `admin_user: soportesmart` (la compartida; funciona en hosts de app/middleware, rechazada en hosts de DB — pero `192.1.1.32` ya se accedió el 25 ago por una vía que "se resolvió", ver `findings.md`).
- **Discrepancia abierta (hoja de la matriz):** fila "BOCA / SID" (`BOCA` vs `BOCAPDB`). `validacion_pendiente`: *"Confirmar SID actual: BOCA o BOCAPDB y plan para WL nuevo."*

## El camino, capa por capa

| # | Capa | Estado (6 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | ✅ **Resuelto (6 sep 2026).** `cabj.condorwork.com.ar` (NPM id 18) → `192.1.2.54:9001` es la ruta Forms **productiva viva** de BOCA — access log de `DOCKER-DEB` (`proxy_host-18.log`): 3.84M `POST /forms/lservlet` `200`, últimos hoy, IPs residenciales AR, UA `Java/1.8.0_421` (volumen bajo de finde pero real). `boca.condorwork.com.ar` (id 19) e id 17 = alias muertos desde 2022. `ords-boca.open.com.ar` → `:7005`, `cabjjasper.condorwork.com.ar` → `192.1.1.110:8090`. | Ninguno bloqueante. *Completeness*: confirmar que `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` no tengan otra ruta BOCA. |
| 2 | Nginx Proxy Manager | ✅ **Resuelto.** El NPM de BOCA es `DOCKER-DEB` (`192.1.1.37:81`) — las 4 rutas están en su MariaDB interna. `VM-DOCKER-Clientes` (`192.1.1.38`) no tiene ninguna entrada BOCA. | *Completeness*: confirmar que `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` tampoco (ambos responden en `:81` desde `DOCKER-DEB`). |
| 3 | Firewall / NAT | 🟢 **Resuelto.** La ruta web productiva de BOCA no tiene regla dedicada — entra por el NAT genérico de `DOCKER-DEB` (`200.55.243.94:80/443` → `192.1.1.37`), ruteo por Host header (mismo patrón que CEFAS/JOBS/EBY). **Pero `FWOPEN` sí tiene una regla directa al mismo middle tier:** `test` → WAN TCP `9998` → `192.1.2.54:9001` (`inventory.json` → `vms[FWOPEN].nat_rules.rules`). Expone el puerto Forms compartido (BOCA + ABB + `condor.open.com.ar`) a Internet sin pasar por NPM, etiquetada solo como "test", `source: *`. No es ruta de BOCA per se, pero es superficie de ataque del box que vamos a relevar — anotar en `findings.md` como hallazgo de exposición (mismo tenor que `vcenter`/`firewall` en WAN). | Ninguno para la ruta de BOCA. Verificar en la sesión si `:9998` responde algo servible desde afuera. |
| 4 | App — motor clásico | ✅ **Resuelto (6 sep 2026).** El Forms productivo de BOCA corre en `192.1.2.54` / `WLS_FORMS` (confirmado por access log, ver capa 1). Dominio `base_domain`, Forms & Reports **12.2.1.4.0** (`/u01/app/oracle/product/12.2.1/user_projects/domains/base_domain`) — mismo molde que JOBS/`OPENWLPROD01`. El nombre "Desarrollo" de la VM engaña: es un hub compartido Forms (prod) + ORDS (varios de test), managed servers `AdminServer`/`WLS_FORMS`/`WLS_REPORTS` + `Ords-Bocat`/`ORDS-CEFAST`/`ORDS-EBY`/`ORDS-JOBS`/`ORDS-T2022DEV01`/`Server-Ords`/`Server-ordsERP19`. DB local `fmwdb` = repositorio RCU del dominio, no cliente. **No se pudo leer `tnsnames.ora`/datasources** (sin sudo — `soportesmart` solo en su grupo; sin cred de consola; árbol `oracle:oinstall` cerrado). | Ninguno para la capa 4. La DB a la que pega `WLS_FORMS` se confirma desde la capa 6, no desde este box. |
| 5 | App — capa Docker / reportes | ✅ **Resuelto — sin capa Docker propia (6 sep 2026).** `sudo docker ps -a` en `OPENDOCKER01` (`192.1.1.110`): **no hay contenedor `cabj`/`boca`** (ni corriendo ni parado), y nada escucha en `:8090` (`ss -tlnp`). El proxy host `cabjjasper.condorwork.com.ar` → `192.1.1.110:8090` es **ruta muerta**. Solo están el Jasper genérico `jasper-open-release-*` (`:8099`) y `jasper-jobs-*` (`:8098`). Mismo patrón que JOBS: motor clásico + reportería, sin frontend/backend containerizado. | Ninguno bloqueante. Cabo suelto no crítico: la reportería real de BOCA es probablemente `WLS_REPORTS` en el propio `192.1.2.54` (managed server existe; `yacyretatest` usa `.2.54:9002` para reports) + Discoverer (matriz `Sí`). Confirmar solo si se necesita. |
| 6 | Base de datos | ✅ **Cerrada (12 sep 2026).** `root@192.1.1.32`, `ORACLE_SID=BOCA`. `v$database` → `CDB=YES`: la CDB `BOCA` está casi vacía (solo schemas de infraestructura Oracle); los datos reales viven en la **PDB `BOCAPDB`** (`ALTER SESSION SET CONTAINER=BOCAPDB`), schema `CONDOR` (~22.5 GB), charset `WE8MSWIN1252` confirmado dentro de la PDB. Último DML de `CONDOR`: **12/09/2026 21:37** — uso activo el mismo día. Sesiones vía ORDS local (`CONDOR`, `ORDS_PUBLIC_USER`) inactivas al momento de mirar; nada desde `192.1.2.54` en el instante exacto, pero el DML reciente ya prueba el uso — no hizo falta capturar la sesión en el instante. | Ninguno — capa cerrada. |
| 7 | Almacenamiento / object store | ✅ **Resuelto — no aplica (6 sep 2026).** `ls -la /clientes/` en `WebLogic.191` muestra solo `cefas` y `lost+found` — **no hay `/clientes/boca`** (la mención previa en `findings.md` a una carpeta `boca` acá era un error de transcripción). Coherente: el Forms de BOCA corre en `.2.54`, no en `.191`. Sin mount NFS ni container (capa 5). | Ninguno. Cabo suelto no crítico: si BOCA usa Condor Link (matriz `Sí`), podría haber un `/u02/clientes/boca*` en el propio `192.1.2.54`, no legible sin sudo. Reabrir solo si aparece evidencia de Condor Link vivo para BOCA. |

## Capa 1 — rutas de entrada (detalle)

Sacado de `DOCKER-DEB-NginxProxyManager/proxy_hosts.csv` + `dockerdeb_proxy_host_2026-09-01.tsv` + `dockerdeb_nginx_confs_2026-09-01.txt`.

| Dominio | id | → destino | `enabled` | Nota |
|---|---|---|---|---|
| `cabj.condorwork.com.ar` | 17 / 18 | `192.1.2.54:9001` — **WL12C-Desarrollo** (Forms, compartido con ABB + `condor.open.com.ar`) | 1 | dominio productivo actual (SSL Let's Encrypt, "Online" desde mar‑2022) |
| `boca.condorwork.com.ar` | 19 | `192.1.2.54:9001` | 1 | segundo alias al mismo backend |
| `ords-boca.open.com.ar` | 48 | `192.1.2.54:7005` — ORDS dedicado en el mismo box | 1 | puerto propio (`:7005`), mismo patrón que `ords-eby`:7010 |
| `cabjjasper.condorwork.com.ar` | 54 | `192.1.1.110:8090` — **`OPENDOCKER01`** | 1 | capa 5 — Jasper reports (SSL LE, "Online" desde dic‑2023) |

Pendiente: clasificar cada una por access log (viva / muerta / test), igual que se hizo con EBY. `cabj` y `boca` apuntan al mismo backend — confirmar si las dos tienen tráfico real o una es alias muerto.

## Orden de la sesión (qué correr, dónde)

Ordenado por información marginal: primero el box de cero cobertura.

### 1. `192.1.2.54` (`WL12C-Desarrollo`) — ✅ accedido 6 sep 2026: corre el Forms prod de BOCA, sin consola/sudo

**Cómo se entró (para reusar):** el puerto 22 de `192.1.2.54` **no responde directo** desde la estación de TeamViewer — hay que rebotar por una caja de la LAN. Comando que funcionó (PowerShell, una línea):
```
ssh -J soportesmart@192.1.1.37 -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.2.54
```
(`192.1.1.37` = `DOCKER-DEB`, que sí acepta SSH directo.)

**Qué se encontró:**

- **Versión:** `http://192.1.2.54:7001/console/login/LoginForm.jsp` → `12.2.1.4.0`. Confirma `wl_version: 12.2` de BOCA/ABB — tercer caso del patrón "técnico decía 11, real es 12" (después de GIAR y JOBS).
- **Dominio:** `base_domain`, Oracle Forms & Reports 12.2.1, `/u01/app/oracle/product/12.2.1/user_projects/domains/base_domain` — mismo molde que JOBS (`WL12C-PROD`) y `OPENWLPROD01`.
- **Managed servers** (`ps -ef | grep -o -- '-Dweblogic.Name=[^ ]*'`): `AdminServer`, `WLS_FORMS`, `WLS_REPORTS`, `Ords-Bocat`, `ORDS-CEFAST`, `ORDS-EBY`, `ORDS-JOBS`, `ORDS-T2022DEV01`, `Server-Ords`, `Server-ordsERP19`. Hub compartido Forms+ORDS; los nombres de ORDS gritan test/dev.
- **DB local:** `ora_pmon_fmwdb` (`/etc/oratab`: `fmwdb:/u01/app/oracle/product/12.2.0/dbhome_1:Y`) — es el repositorio RCU del propio dominio FMW, **no** una base de cliente. Explica el tráfico pesado a `127.0.0.1:1521`.
- **`netstat -tn` (sin sudo — `soportesmart` solo en su grupo, sin `oinstall`/`dba`, sin sudoers):** destinos Oracle remotos —
  | Destino | Conexiones | VM |
  |---|---|---|
  | `192.1.1.44:1521` | ~20 EST (dominante) | `Database .44 - Clientes TEST` |
  | `192.1.2.240:1521` | ~10 EST | `OPENDB19DEV01` (Oracle 19c dev) |
  | `192.1.1.25:1521` | ~4 EST | `Database.25` = CONDORERP(T2022), ERP interno |
  | `192.1.1.32:1525` | 2 EST + varios CLOSE_WAIT | `CLIENTES-DB` (prod BOCA/CEFAS) |
  | `192.1.1.22:1521` | solo CLOSE_WAIT / SYN_SENT | `OPENDBPROD006` — algo (¿`ORDS-EBY`?) intenta y no engancha |
- **`netstat -tn | grep :9001`:** en el momento de mirar (domingo) no había sesiones de usuario establecidas — pero el access log de `DOCKER-DEB` (paso siguiente) mostró que **sí hay Forms productivo**: `cabj.condorwork.com.ar` → 3.84M `POST /forms/lservlet` `200`, últimos hoy, IPs residenciales AR. El `netstat` lo agarró en un valle de fin de semana, no es que esté muerto.
- **Muro de permisos:** sin sudo, sin credencial de consola, árbol `/u01/app/oracle` en `oracle:oinstall` sin lectura para otros → no se pudo leer `tnsnames.ora` ni datasources. Mismo caso que `WebLogic.191`.

**Conclusión:** `192.1.2.54` corre el Forms **productivo** de BOCA en `WLS_FORMS` (el nombre "Desarrollo" de la VM engaña — es hub compartido prod+test, como `WL12C-PROD`). Capa 4 cerrada. Lo que este box **no** puede dar sin mejor credencial: a qué DB pega — eso se confirma desde la capa 6 (`CLIENTES-DB`). Este box no requiere más sesión.

### 2. `192.1.1.32` (`CLIENTES-DB`) — ya accesible, cierre de capa 6

Reusar el acceso logrado el 25 ago 2026 (trazado CEFAS). Comandos en la fila "Capa 6" de la tabla. Es el mismo host de CEFAS (SID `CEFAS` ya confirmado) y del schema de dominio de JOBS (`ora_pmon_wl12prod`) — tres instancias Oracle en la misma VM.

### 3. `OPENDOCKER01` (`192.1.1.110`) — ya recorrido para JOBS, cierre de capa 5

`sudo docker ps | grep -iE 'cabj|boca|jasper'`. Si hay un `jasper-cabj-*`, leer su compose/config para ver qué DB usa (esperado: su propia MariaDB, sin tocar el Oracle del motor clásico — mismo patrón que `jasper-jobs-jasperreports-1`).

## Al terminar

1. Completar `clients[BOCA].database.resolved` (SID real, `service_name_confirmed`, `resolved_by: teamviewer`) y `clients[BOCA].weblogic.resolved` (dominio, managed servers) en `infra/inventory.json`; actualizar `clients[BOCA].matrix_detail` (`validacion_pendiente` → resuelto, charset confirmado, `wl_version` real).
2. Si de la misma sesión salió el datasource de **ABB**: cerrar **Tier 1 #4** en `PLAN.md` y la fila "ABB / DB actual" de la tabla de Discrepancias en `infra/findings.md`; y — según a qué IP apunte — pasar la capa 6 de **ESYOP** (`.31`) o **DCVIAJES** (`.190`) de "identificado por nombre" a "verificado en vivo".
3. Mover a "Resueltos / confirmados" en `infra/findings.md`, con fecha: la fila "BOCA / SID" de la tabla de Discrepancias.
4. Para cada co‑inquilino de `.2.54` con evidencia nueva (sesión activa vista, datasource leído): pasar su capa 4/6 a "verificado en vivo" en `inventory.json` y anotarlo en `findings.md` — es el rédito principal de haber elegido BOCA.
5. Regenerar `infra/topology.md` §1 si cambió el mapeo cliente → WL → DB de BOCA, ABB, EBY, ESYOP o DCVIAJES (recorrer `clients[]`, no editar el Mermaid a mano — ver `CLAUDE.md`).
6. Actualizar `verificacion_completitud_clientes.md` y `resumen_relevamiento_alta_cliente.md`; cargar el aporte de BOCA a la receta generalizada.

## Receta generalizada (completar cuando converjan CEFAS + JOBS + EBY + BOCA)

*(Vacío a propósito — se llena cuando los trazados converjan, no antes.)*

**Aporte específico que se espera de BOCA:** el caso "cliente sin enredo — un WL, una DB, los dos ya conocidos por nombre, sin migración de WL — cuyo único trabajo real es **entrar al box compartido que nadie tocó y leer datasources**, y de paso cerrar a los co‑inquilinos". Es el contraste con EBY (árbol de candidatos frondoso, dos stacks en paralelo) y con JOBS (cadena dedicada ya accesible). BOCA aporta además el primer dato del parque de una DB Oracle **19c** y charset **Windows‑1252**, y la prueba de si `192.1.2.54` acepta `soportesmart` (como los demás hosts de app) o no.
