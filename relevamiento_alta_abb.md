# Relevamiento de alta de cliente — camino punta a punta (ABB de referencia)

> ✅ **CERRADO — 7/7 capas (6 sep 2026).** DB productiva confirmada: **`192.1.1.31`** (`DBClientes-12C.31`, instancia `ABB`, schema de app `CONDOR`), por `sqlplus`/`dba_tab_modifications` con `root@192.1.1.31`. `192.1.1.190` descartada (no tiene instancia `ABB`, solo `abbhist`/`abbtubio` históricas apagadas; es el box de DCVIAJES). Discrepancia "ABB / DB actual" resuelta a favor de la fuente funcional. **Hallazgo colateral:** ABB sin una sola sesión Forms ni un DML desde el **1‑jul‑2026** — apagado de hecho, dato de apoyo para la pregunta de baja en `QUESTIONS.md`. Bonos: capa 6 de **ESYOP** verificada en vivo y de **DCVIAJES** parcial. Detalle en `infra/findings.md` ("Resueltos / confirmados", 6 sep 2026) y `infra/inventory.json` (`clients[ABB]`, `clients[ESYOP]`, `clients[DCVIAJES]`). Lo de abajo es el plan tal como se ejecutó.

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md), [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md), [`relevamiento_alta_eby.md`](relevamiento_alta_eby.md) y [`relevamiento_alta_boca.md`](relevamiento_alta_boca.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Quinto trazado, elegido porque es el último cabo de Tier 1 que podemos cerrar nosotros por TeamViewer — y porque el rédito que se esperaba de rebote no salió.** El plan de BOCA (`relevamiento_alta_boca.md`) contaba con leer el datasource de ABB en la consola de `192.1.2.54` de paso, ya que ABB y BOCA son co‑inquilinos de ese WebLogic. La sesión del 6 sep 2026 entró al box pero **no tiene consola de WebLogic ni `sudo`** — el datasource de ABB no es legible desde ahí. ABB (Tier 1 #4 en `PLAN.md`) quedó abierto, y su discrepancia de DB está marcada **prioridad Alta** en la hoja Discrepancias de la matriz. Este trazado lo cierra por la vía que queda: `sqlplus` / `v$session` directo en las dos DBs candidatas.

> ⚠️ **ABB puede estar dado de baja — pero eso no bloquea este trazado.** Una nota informal en la matriz dice que ABB y GIAR "están de baja pero por el momento se mantiene sus bases"; el campo formal `Estado / migración` de la misma planilla dice **"Mantenimiento solamente"**. La contradicción es una **pregunta de negocio para el equipo saliente** (ver `QUESTIONS.md`), no algo que se resuelva mirando un servidor. Lo que este trazado sí aporta a esa pregunta: si `abb.condorwork.com.ar` todavía recibe tráfico real (access log, capa 1). Y las DBs se relevan igual — están retenidas y **compartidas con clientes activos** (ESYOP en `.31`, DCVIAJES en `.190`), así que saber cuál es cuál importa aunque ABB se apague mañana.

## Por qué ABB (impacto sobre el resto del relevamiento)

- **Cierra el último ítem de Tier 1 que depende solo de nosotros.** De los 4 ítems de Tier 1 en `PLAN.md`: #1 (mapa dominio→NPM→NAT) está en curso, #2 (DB de Rex) y #3 (ruta de EBY) quedaron con cabos que necesitan más que una sesión. #4 (ABB) es el único que una sola sesión de `sqlplus` puede cerrar del todo.
- **Discrepancia prioridad Alta.** Fila "ABB / DB actual" de la hoja Discrepancias: la fuente funcional dice `192.1.1.31 / SID ABB`; el inventario técnico dice **las dos IPs** (`192.1.1.31` y `192.1.1.190`). Acción pedida por el propio documento: *"Identificar la base productiva y la secundaria/histórica."*
- **Da verificación de capa 6 en vivo, gratis, a un cliente "plano":**
  - Si la DB productiva de ABB es **`192.1.1.31`** (`DBClientes-12C.31`) → esa DB la comparte con **ESYOP** (`clients[ESYOP].database` la resuelve ahí por IP, `match: false`) → ESYOP pasa de "identificado por nombre" a "verificado en vivo".
  - Si es **`192.1.1.190`** (`DBClientes.190`) → la comparte con **DCVIAJES** → ídem DCVIAJES.
  - Ninguno de los dos ("planos": DVAL, DCVIAJES, ESYOP, Argocean) tuvo nunca una sesión propia — su score es extrapolación.
- **La señal ya apunta a `.31`.** El campo `notes` de `DBClientes-12C.31` en `inventory.json` trae lo que parece un `/etc/oratab` transcripto:
  ```
  aqualum : N
  esyop   : Y
  abbhist : N
  ABB     : Y
  abbtubio: N
  ```
  La instancia `ABB` está en ese host y marcada para autostart (`Y`), junto a `abbhist` y `abbtubio` (`N` — arranque manual; probablemente histórico/secundario, coinciden con la lectura de `findings.md` de que son sub‑esquemas de ABB, no clientes nuevos). Falta la confirmación en vivo de que **la aplicación** pega ahí y no en `.190` — para eso, `v$session WHERE machine='192.1.2.54'`.

## Estado de partida (6 sep 2026)

De `infra/inventory.json` → `clients[ABB]`, `infra/findings.md`, `infra/topology.md` §1 y la sesión de BOCA:

- **WL:** `WL12C-Desarrollo.2.54` (`192.1.2.54`), `resolved_by: name`, `match: true`. **Ya accedido el 6 sep 2026** (trazado BOCA) — dominio `base_domain`, Oracle Forms & Reports **12.2.1.4.0** (confirma `wl_version: 12.2` de la matriz; mismo molde que `WL12C-PROD`/`OPENWLPROD01`). Managed servers: `AdminServer`, `WLS_FORMS`, `WLS_REPORTS`, `Ords-Bocat`, `ORDS-CEFAST`, `ORDS-EBY`, `ORDS-JOBS`, `ORDS-T2022DEV01`, `Server-Ords`, `Server-ordsERP19`. **No hay managed server dedicado a ABB** — ABB va sobre el `WLS_FORMS` compartido (mismo que sirve `cabj.condorwork.com.ar` de BOCA). Sin `sudo`, sin credencial de consola, árbol `oracle:oinstall` cerrado → `tnsnames.ora` / datasources **no legibles** desde este box.
- **DB:** dos candidatos, sin resolver cuál es productivo:
  - `DBClientes-12C.31` (`192.1.1.31`) — `resolved_by: ip`, `match: false` (el nombre reclamado era `dbclientes`). Corre las instancias `ABB` (autostart) + `abbhist` + `abbtubio`, y `esyop` (autostart). Backup Veeam `Job_002_Backup_quincenal`, último `7/10/2025`. Compartida con **ESYOP**.
  - `DBClientes.190` (`192.1.1.190`) — `resolved_by: name`, `match: true` (coincide con el reclamado `dbclientes.190`). Compartida con **DCVIAJES**.
- **Matriz (`matrix_detail`):** `sid_actual: ABB`, `version_db: 12.2.0.1.0`, `edicion: SE`, `tamaño: 20G`, `charset: WE8ISO8859P1`, destino `BD 10.77.7.12` / `10.77.7.12`, `sid_nuevo: prodabb`, `version_condor: 2024`. Productos: Work `Sí`, Enterprise `No`, **el resto en blanco** (sin Jasper, sin Self Service, sin Condor Link, sin Discoverer) → capa 5 y 7 probablemente "no aplica".
  - `10.77.7.12` es blind spot: la matriz **también** lo da como destino de **DCVIAJES** (`sid_nuevo: "No existe, crear"`) — mismo patrón de consolidación legado→nuevo que EBY/CEFAS/GIAR. No resuelve a ninguna VM ni tiene regla NAT. Tráfico productivo sigue en `.31`/`.190`.
  - `validacion_pendiente` (matriz): *"Confirmar qué IP DB actual corresponde a producción y el servidor WL definitivo."*
- **Estado:** `"Mantenimiento solamente"` (campo formal) — ver el aviso de arriba sobre la nota informal contradictoria.
- **Cuenta:** `admin_user: soportesmart` (la compartida — funciona en hosts de app/middleware, históricamente **rechazada en hosts de DB**). `192.1.1.32` se accedió el 25 ago por una vía "que se resolvió"; para EBY se consiguió `root` en `192.1.1.90`. **Falta saber si alguna de esas credenciales entra a `.31` / `.190`** — es el bloqueo real de este trazado (ver "Orden de la sesión").

## El camino, capa por capa

| # | Capa | Estado (6 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | 🟡 **Conocido, sin verificar si está vivo.** `abb.condorwork.com.ar` (NPM `DOCKER-DEB`, `proxy_host` id 28) → `192.1.2.54:9001` (`WLS_FORMS` compartido). SSL Let's Encrypt, marcado "Online" desde oct‑2022, pero `updated_at` de la fila = `2023-12-29` — sin toques desde entonces. No hay alias secundario ni `ords-abb` / `abbjasper` en el dump de NPM. | **Access log** en `DOCKER-DEB` (`sudo docker exec ssl-app-1`) — ubicar el archivo real por contenido (no por número), `find /data/logs -name "proxy_host-*.log" -exec grep -l "abb.condorwork.com.ar" {} \;`; ver si hay `POST /forms/lservlet` `200` reciente. Responde de paso la pregunta de negocio: ¿ABB todavía tiene usuarios? |
| 2 | Nginx Proxy Manager | ✅ **Resuelto.** El NPM de ABB es `DOCKER-DEB` (`192.1.1.37:81`) — la ruta está en su MariaDB interna (id 28). `VM-DOCKER-Clientes` (`192.1.1.38`) no tiene entrada ABB. | *Completeness*: confirmar que `OPENDOCKER04` / `VM-DOCKER-Clientes (1)` tampoco (mismo pendiente que BOCA/EBY). |
| 3 | Firewall / NAT | 🟢 **Resuelto por patrón.** La ruta web de ABB no tiene regla dedicada — entra por el NAT genérico de `DOCKER-DEB` (`200.55.243.94:80/443` → `192.1.1.37`, ruteo por Host header — mismo patrón que CEFAS/JOBS/EBY/BOCA). **Herencia de BOCA:** `FWOPEN` regla `test` → WAN TCP `9998` → `192.1.2.54:9001`, `source: *` — expone a Internet el puerto Forms compartido (BOCA + ABB + `condor.open.com.ar`) sin pasar por NPM. Ya anotado como hallazgo de exposición en `findings.md`; no es ruta de ABB per se pero es superficie del box. | Ninguno propio de ABB. |
| 4 | App — motor clásico | 🟢 **Resuelto por herencia (6 sep 2026).** ABB va sobre `WLS_FORMS` en `192.1.2.54` — mismo managed server, dominio y versión que BOCA (`base_domain`, F&R 12.2.1.4.0). Sin managed server ni ORDS dedicado a ABB. **Confirma `wl_version: 12.2`** de la matriz — cuarto caso del patrón "técnico decía 11, real es 12" (tras GIAR, JOBS, BOCA). | Ninguno *desde este box* — sin `sudo`/consola no se leen datasources. La DB a la que pega `WLS_FORMS` para ABB se confirma **desde la capa 6** (`v$session`), no desde `.2.54`. |
| 5 | App — capa Docker / reportes | 🟡 **Probable "no aplica".** La matriz tiene Jasper / Self Service / Condor Link / Discoverer **en blanco** para ABB (solo Work `Sí`). No hay `abbjasper` ni `abb-*` en el dump de NPM. | `sudo docker ps -a \| grep -iE 'abb'` en `OPENDOCKER01` (`192.1.1.110`) — ya recorrido para JOBS y BOCA, costo marginal cero. Si no hay contenedor → cerrar "no aplica". |
| 6 | Base de datos | ⬜ **El trazado entero. Discrepancia prioridad Alta.** Dos candidatos: `192.1.1.31` (`DBClientes-12C.31`, instancia `ABB` autostart + `abbhist`/`abbtubio`, compartida con ESYOP) vs `192.1.1.190` (`DBClientes.190`, compartida con DCVIAJES). Matriz: `SID ABB`, charset `WE8ISO8859P1`, 12.2.0.1.0 SE, 20G. Señal previa favorece `.31` (oratab), sin confirmar en vivo. | `sqlplus` + `v$session` en **las dos** — ver "Detalle capa 6" abajo. Requiere credencial para hosts de DB (ver "Orden de la sesión"). |
| 7 | Almacenamiento / object store | 🟡 **Probable "no aplica".** Forms de ABB en `.2.54`, no en `.191` (donde vive `/clientes/`); matriz sin Condor Link / Self Service. Espejo del cierre de BOCA. | `ls -la /clientes/` en `WebLogic.191` ya se corrió para BOCA (solo `cefas` + `lost+found`) — no hay `/clientes/abb`. Cabo no crítico: un `/u02/clientes/abb*` en `.2.54` no sería legible sin `sudo`. Cerrar "no aplica" salvo que aparezca evidencia. |

## Detalle capa 1 — la ruta de entrada

Única fila de ABB en `DOCKER-DEB-NginxProxyManager/` (`proxy_hosts.csv` + `dockerdeb_proxy_host_2026-09-01.tsv` + `dockerdeb_nginx_confs_2026-09-01.txt`):

| Dominio | id | → destino | `enabled` | Nota |
|---|---|---|---|---|
| `abb.condorwork.com.ar` | 28 | `192.1.2.54:9001` — `WLS_FORMS` (Forms, compartido con BOCA `cabj` + `condor.open.com.ar`) | 1 | SSL LE, "Online" desde 19‑oct‑2022; `updated_at` fila = 29‑dic‑2023. Conf nginx: `proxy_host/28.conf`. |

No hay segundo alias, ni `ords-abb.open.com.ar`, ni `abbjasper.*`. Contraste con BOCA (4 rutas) y EBY (10) — ABB tiene la huella de NPM más chica de los clientes trazados, consistente con "mantenimiento solamente".

**Pendiente:** clasificar la ruta por access log — viva / muerta / test — igual que se hizo con EBY y BOCA. Es el dato que más pesa para la pregunta de negocio "¿ABB sigue operando?".

## Detalle capa 6 — las dos DBs candidatas

Correr en **las dos**, comparar:

### `192.1.1.31` (`DBClientes-12C.31`)

```sh
cat /etc/oratab                       # confirmar qué instancias corren (esperado: ABB, abbhist, abbtubio, esyop, aqualum)
export ORACLE_SID=ABB
sqlplus / as sysdba
```
```sql
SELECT name, open_mode, log_mode FROM v$database;
SELECT value FROM nls_database_parameters WHERE parameter='NLS_CHARACTERSET';   -- esperado WE8ISO8859P1
SELECT username, machine, program, status, COUNT(*)
  FROM v$session WHERE username IS NOT NULL
  GROUP BY username, machine, program, status ORDER BY 5 DESC;
-- clave: ¿hay sesiones con machine='192.1.2.54' (el WLS_FORMS compartido)? -> esta es la DB productiva de ABB
SELECT COUNT(*) FROM v$session WHERE machine='192.1.2.54';
```
Si están `abbhist` / `abbtubio` como instancias reales (no solo esquemas), repetir el `v$database` con cada `ORACLE_SID` para ver si son bases separadas o alias. Chequear también `esyop` de paso (`SELECT ... WHERE machine='192.1.1.19'` — el WL de ESYOP) → cierra capa 6 de ESYOP en vivo.

### `192.1.1.190` (`DBClientes.190`)

Mismo bloque, `ORACLE_SID` según lo que liste `/etc/oratab` (candidatos: `ABB`, `DCVIAJES`). Buscar igualmente `machine='192.1.2.54'` para ABB y `machine` del WL de DCVIAJES (`192.1.1.191`, `WebLogic.191`) → cierra capa 6 de DCVIAJES en vivo.

**Criterio de decisión:** la DB con sesiones activas de `machine='192.1.2.54'` y `program` tipo `frmweb`/`oracle` bajo un schema de ABB es la **productiva**; la otra retiene una copia **secundaria / histórica** (o nada de ABB). Anotar las dos, no descartar la perdedora en silencio — la hoja Discrepancias pide identificar *ambos* roles.

## Orden de la sesión (qué correr, dónde)

Los tres hosts ya se accedieron en trazados anteriores. Lo único nuevo es la **credencial para los hosts de DB**.

### 0. Resolver credencial para `192.1.1.31` y `192.1.1.190` — bloqueante

`soportesmart` viene siendo rechazada en hosts de DB (`.90`, `.22`, `10.77.7.15` durante EBY). Vías, en orden:
1. Probar la credencial `root` conseguida para `192.1.1.90` (EBY) — puede ser la misma para toda la familia `DBClientes*`.
2. Probar la vía por la que se entró a `192.1.1.32` el 25 ago (trazado CEFAS — `findings.md` la describe como "se resolvió").
3. Si ninguna entra: es un pedido concreto y acotado al equipo saliente (credencial de SO para `DBClientes-12C.31` / `DBClientes.190`) — sumar a `QUESTIONS.md` como ítem operativo, no de negocio.

### 1. `DOCKER-DEB` (`192.1.1.37`) — access log de `abb.condorwork.com.ar` (capa 1)

SSH directo (acepta `soportesmart`). `sudo docker exec ssl-app-1 sh -c 'find /data/logs -name "proxy_host-*.log" -exec grep -l "abb.condorwork.com.ar" {} \;'`, después `tail`/`grep "POST /forms/lservlet"` en el archivo que salga. **Gotcha ya conocido:** el número de archivo `proxy_host-<N>.log` **no** coincide con el `id` de la tabla — ubicarlo por contenido. Ver `relevamiento_alta_jobs.md` punto 2.

### 2. `192.1.1.31` y `192.1.1.190` — `sqlplus` / `v$session` (capa 6)

Bloques SQL de "Detalle capa 6". Es el corazón del trazado.

### 3. `OPENDOCKER01` (`192.1.1.110`) — `docker ps` (capa 5)

`sudo docker ps -a | grep -iE 'abb'`. Ya recorrido para JOBS y BOCA. Esperado: nada → capa 5 "no aplica".

### (no hace falta volver a `192.1.2.54`)

La capa 4 quedó cerrada por herencia de la sesión de BOCA. Si en el futuro se consigue `sudo` o credencial de consola en `.2.54`, leer el datasource de ABB sería la confirmación redundante — no es necesaria si la capa 6 resuelve con `v$session`.

## Al terminar

1. Completar `clients[ABB].database.resolved` en `infra/inventory.json`: marcar cuál candidato es `productive` vs `secondary/historical`, `resolved_by: teamviewer`, `service_name_confirmed`, charset real. Actualizar `clients[ABB].matrix_detail.validacion_pendiente` → resuelto (o la parte de DB; el "servidor WL definitivo" ya está: `192.1.2.54`, sin WL nuevo).
2. Mover a "Resueltos / confirmados" en `infra/findings.md`, con fecha: la fila **"ABB / DB actual"** de la tabla de Discrepancias.
3. Cerrar **Tier 1 #4** en `PLAN.md`.
4. Según a qué DB resolvió: pasar la capa 6 de **ESYOP** (`.31`) o **DCVIAJES** (`.190`) de "identificado por nombre" a "verificado en vivo" en `inventory.json` + nota en `findings.md`. Es el rédito principal de haber elegido ABB.
5. Registrar el resultado del access log de capa 1 en `findings.md` — y, si `abb.condorwork.com.ar` resultó **sin tráfico reciente**, anotarlo como insumo para la pregunta de baja de ABB en `QUESTIONS.md` (dato de apoyo, no decisión).
6. Regenerar `infra/topology.md` §1 si cambió el mapeo cliente → WL → DB de ABB, ESYOP o DCVIAJES (recorrer `clients[]`, no editar el Mermaid a mano — ver `CLAUDE.md`). En particular, el nodo `WL12C-Desarrollo.2.54 → DBClientes.190` de ABB puede tener que colapsarse a una sola DB.
7. Actualizar `verificacion_completitud_clientes.md` y `resumen_relevamiento_alta_cliente.md`; cargar el aporte de ABB a la receta generalizada.

## Receta generalizada (completar cuando converjan CEFAS + JOBS + EBY + BOCA + ABB)

*(Vacío a propósito — se llena cuando los trazados converjan, no antes.)*

**Aporte específico que se espera de ABB:** el caso "cliente en mantenimiento / posible baja, huella mínima (una sola ruta de NPM, sin managed server ni contenedor dedicado, sin storage), cuyo único trabajo real es **dirimir cuál de dos DBs candidatas es la productiva por `v$session`**, y de paso cerrar en vivo a un co‑inquilino que nunca tuvo sesión propia". Es el contraste con BOCA (que obligaba a entrar a un box nuevo) y con EBY (árbol de candidatos frondoso). ABB aporta además el método para resolver una discrepancia "DB actual = dos IPs" sin acceso a la consola de WebLogic: `v$session WHERE machine=<IP del WL>` en cada candidata.
