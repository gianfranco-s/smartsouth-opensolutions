# Relevamiento de alta de cliente — camino punta a punta (DVAL de referencia)

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md), [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md), [`relevamiento_alta_eby.md`](relevamiento_alta_eby.md), [`relevamiento_alta_boca.md`](relevamiento_alta_boca.md), [`relevamiento_alta_abb.md`](relevamiento_alta_abb.md) y [`relevamiento_alta_giar.md`](relevamiento_alta_giar.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Séptimo trazado, primer "plano" que se aborda formalmente.** DVAL (Dominique Val S.A.) es uno de los cuatro clientes que `verificacion_completitud_clientes.md` marca como **"plano"** — nunca tuvo una sesión propia, su score (~43%) es pura extrapolación por nombre/IP. A diferencia de ROMAN/GIAR/ABB, DVAL nunca fue el objetivo explícito de una sesión — pero varias sesiones ajenas (CEFAS, EBY) ya lo tocaron de rebote sin que nadie lo haya cerrado. Este plan junta esos restos y agrega lo que falta.

## Por qué DVAL ahora (impacto sobre el resto del relevamiento)

- **Ya hay evidencia de tráfico en vivo sin atribuir — el hallazgo central de este plan.** El `netstat -tn` sin sudo corrido en `WebLogic.191` el 25 ago 2026 (sesión CEFAS, ver `infra/findings.md` línea 147) mostró conexiones `ESTABLISHED` activas hacia dos IPs que en ese momento quedaron **sin identificar**: `192.1.1.90` y `192.1.1.238`. `192.1.1.238` es exactamente **`DBClientes.238`, la DB de DVAL** (`clients[DVAL].database.resolved[0].ip`). Es decir: sin ninguna sesión nueva, ya existe una foto de conexión Oracle real y activa desde el motor compartido hacia la DB de DVAL — el mismo tipo de dato que le dio capa 6 "en uso" a DCVIAJES/ESYOP, solo que nadie lo había cruzado hasta ahora.
- **La capa 3 (firewall/NAT) ya está cerrada de antes, sin sesión dedicada.** El NAT `FWOPEN` transcripto el 19 ago 2026 tiene una regla explícita: `WAN1:8088 → 192.1.1.191:80`, descripción literal `"NAT DVAL"`. Confirma además un patrón de acceso distinto al resto de la cartera: DVAL entra por **puerto WAN dedicado sin dominio ni NPM** (mismo patrón que Mafisa `:8089` y UIA `:8191`, los tres al mismo `WebLogic.191`) — no por `condorwork.com.ar`/`condor.solutions` como CEFAS/JOBS/EBY/ROMAN/BOCA/ABB.
- **Host de la capa 4 ya identificado y parcialmente recorrido dos veces (CEFAS 25 ago, EBY 1 sep) sin sudo.** No hace falta "descubrir" `WebLogic.191` — hace falta releer lo que ya se sabe de él con el filtro puesto en DVAL, y sumar un `netstat` fresco para confirmar que la conexión a `.238` sigue viva hoy (no era una foto de un instante irrepetible).
- **Rédito colateral: `192.1.1.90`, la otra IP sin identificar del mismo `netstat`.** Sigue sin resolver — no es DVAL (la matriz no le da esa IP), pero queda como cabo suelto a clasificar la próxima vez que se entre a `WebLogic.191`, junto con el `Database .90` (`CDRADM`) que ya se sabe compartido entre varios tenants de esa VM (visto en EBY) — podría ser el mismo host.
- **Barato si el "plano" resulta ser justamente eso — poco tráfico.** A diferencia de ROMAN (0 tráfico real pese a estar "configurado como producción"), acá la matriz ya avisa `status: "Pendiente de migración"` — un estado que en la cartera tiende a coincidir con uso real vigente (a diferencia de "de baja"/apagado como ABB). El objetivo no es una sorpresa grande, es cerrar capas baratas y confirmar con datos duros el patrón que ya se intuye.

## Estado de partida (12 sep 2026)

De `infra/inventory.json` → `clients[DVAL]`, `infra/findings.md`, `verificacion_completitud_clientes.md` (DVAL ~43%, "sin cambios" en las últimas dos rondas) y `source-files/extracted/matriz_servicios_por_cliente.json`:

- **Cliente:** `Dominique Val S.A.` (code `DVAL`). Estado matriz: **`"Pendiente de migración"`**. `admin_user: soportesmart`.
- **WebLogic (capa 4):** reclamado `WebLogic.191`, `wl_version: 11`, `esxi_host_relevamiento: 192.1.1.217`. Resuelto **por nombre, match exacto** → `WebLogic.191` / `192.1.1.191`. Confirmado en sesiones previas (CEFAS 25 ago, EBY 1 sep) como Oracle Forms & Reports **11g**, dominio `ClassicDomain` (`/app/oracle/mid/user_projects/domains/ClassicDomain`), managed servers `WLS_FORMS`/`WLS_REPORTS` — **el host más compartido del relevamiento**, sirve a DVAL, UIA, Mafisa, SIGO, EBY/Yacyretá, DCViajes, Tassaroli y CEFAS (8 clientes). **`soportesmart` no tiene `sudo` funcional en este host** en ninguna de las dos sesiones previas — no se pudo leer `formsweb.cfg`/`tnsnames.ora` específicos de ningún cliente acá, DVAL incluido.
- **Base de datos (capa 6):** reclamado `dbclientes238` — nombre **desactualizado** (`match: false`), resuelto **por IP** → VM real `DBClientes.238` (`192.1.1.238`). VM encendida, uptime 198 días, `esxi_host: 192.1.1.218`, backup Veeam quincenal (`Job_002_Backup_quincenal`, último 21-mar-2026). **Sin sesión propia todavía** — a diferencia de `DBClientes.190` (DCVIAJES/ABB), que ya tiene un bloque `confirmation` con acceso root real, `DBClientes.238` no tiene ningún acceso registrado.
- **Hallazgo sin cruzar hasta ahora:** `netstat -tn` de `WebLogic.191` (25 ago 2026, sin sudo) mostró conexión `ESTABLISHED` a `192.1.1.238` — anotada en `findings.md` como "sin identificar". **Es la DB de DVAL.** Primera evidencia de tráfico real del proyecto para este cliente, todavía no volcada a `inventory.json`.
- **Matriz (`matrix_detail`):** `sid_actual: "DVAL"`, `version_db: "11.2.0.4.0"`, `tamano: "24G"`, `charset: "WE8ISO8859P1"` (el estándar del parque), `servidor_db_destino: "BD 10.77.7.14"` / `ip_db_destino: "10.77.7.14"`, `sid_nuevo: "PRODDVAL"` — mismo patrón de migración pendiente que EBY/BOCA/GIAR (destino en `10.77.7.x`, todavía sin VM ni tráfico confirmado ahí). `version_condor: 2025`.
- **Productos (matriz):** Enterprise `Sí`, AFIP `Sí`, Work `No`, Discoverer `"No se"` (la propia fuente admite no saber), Condor Link / Self Service / Jasper / MicroStrategy **en blanco** — sin la señal "Condor Link: Sí + Self Service en blanco" que en CEFAS/BOCA/ROMAN resultó esconder un contenedor no declarado; acá no hay indicio de capa Docker propia. `validacion_pendiente: "Confirmar plan y fecha de migración."`
- **Firewall / NAT — ya cerrada.** `FWOPEN` (`FWOPEN-nat-rules/nat_rules.csv`, transcripto 19 ago 2026): `WAN1 TCP *:8088 → 192.1.1.191:80`, descripción `"NAT DVAL"`. Sin dominio, sin NPM — acceso directo por puerto WAN dedicado, igual que Mafisa (`:8089`) y UIA (`:8191`) al mismo `WebLogic.191`.
- **No aparece en ningún dump de NPM transcripto** (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`, `dockerdeb_proxy_host_2026-09-01.tsv`) — consistente con "no usa dominio", pero esos dumps no cubren los otros dos NPM que `relevamiento_alta_roman.md` deja pendientes (`OPENDOCKER04`, `VM-DOCKER-Clientes (1)`).

## El camino, capa por capa

| # | Capa | Estado (12 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | ⬜ **Probablemente no aplica.** Sin dominio conocido; la regla NAT usa un puerto WAN dedicado (`:8088`) directo a IP, patrón compartido con Mafisa/UIA en el mismo host. | *Completeness*: confirmar que ningún NPM (`DOCKER-DEB`, `VM-DOCKER-Clientes`, y los dos sin transcribir) tenga un proxy host `dval.*` — bajo costo, no bloqueante. |
| 2 | Nginx Proxy Manager | ⬜ **Probablemente no aplica**, mismo motivo que capa 1. | Mismo grep que capa 1. |
| 3 | Firewall / NAT | ✅ **Cerrada (19 ago 2026, de otra sesión).** `WAN1:8088 → 192.1.1.191:80`, `"NAT DVAL"`, confirmado en `FWOPEN-nat-rules/nat_rules.csv` y cargado en `inventory.json`. | Ninguno. |
| 4 | App — motor clásico | 🟡 **Host confirmado, config sin leer.** `WebLogic.191`, Forms & Reports 11g, `ClassicDomain`. Sin `sudo` en dos intentos previos (CEFAS, EBY) → no se pudo leer `formsweb.cfg` para ver si hay una sección `[dval]`/equivalente. | Reintentar `sudo` (puede que la cuenta haya cambiado de permisos desde ago/sep). Si sigue sin sudo: repetir el `netstat -tn` sin privilegios que ya funcionó una vez — confirmar si `192.1.1.238` sigue `ESTABLISHED` hoy. |
| 5 | App — capa Docker / reportes | ⬜ **Probablemente no aplica.** Matriz no marca Jasper/Self Service/Condor Link para DVAL (todos en blanco, sin el patrón de "Condor Link: Sí" que delató contenedores ocultos en otros clientes). | `grep -i dval` sobre cualquier `docker ps -a` que se corra de paso en `OPENDOCKER01`/`DOCKER-DEB` — bajo costo, no bloqueante. |
| 6 | Base de datos | 🔴 **Candidato confirmado por IP, acceso bloqueado por credencial (12/13 sep 2026).** `DBClientes.238` (`192.1.1.238`), encendida, uptime 198 días. Matriz: SID `DVAL`, Oracle `11.2.0.4.0`, `24G`, charset `WE8ISO8859P1`. `ssh root@192.1.1.238` **rechazado** (la credencial que sirvió en `.31`/`.32`/`.190` no vale acá); `ssh soportesmart@192.1.1.238` **también rechazado**. `netstat` repetido dos veces en `WebLogic.191` (con soportesmart, sin sudo) no volvió a mostrar `.238` `ESTABLISHED` en ninguna pasada (solo `192.1.1.90:1521` activa ambas veces) — la foto del 25 ago que sí la mostró queda como único indicio de tráfico real hasta ahora. | Conseguir credencial específica para `192.1.1.238` (anotado en `QUESTIONS.md`, junto con `10.77.7.15`/`.30`/`.151`) — sin eso, capa 6 queda frenada. Mientras tanto: repetir el `netstat -tn \| grep -E ':1521\|:1525'` en `WebLogic.191` en otro horario/día hábil para intentar recapturar la conexión a `.238` en vivo. |
| 7 | Almacenamiento / object store | ⬜ **Sin trazar, probablemente no aplica.** Sin mención de storage dedicado en la matriz ni en las sesiones previas sobre `WebLogic.191`. | Si se logra acceso a `WebLogic.191`: `ls /app/oracle/... clientes 2>/dev/null \| grep -i dval` (ajustar la ruta real, no confirmada por falta de sudo) + `mount \| grep -i dval`. Bajo costo, no bloqueante. |

## Orden de la sesión (qué correr, dónde)

Ordenado por información marginal: primero confirmar que el tráfico de `.238` sigue vivo (gratis, sin sudo), después intentar la DB directamente (es el único paso que realmente cierra algo nuevo).

### 1. `WebLogic.191` (`192.1.1.191`) — reconfirmar capa 4/6 sin sudo

**Cómo se entró antes:** SSH con `soportesmart`, forzando `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa` (host keys viejos). Sin `sudo` funcional en los dos intentos previos.

```
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.1.191
netstat -tn | grep -E '192\.1\.1\.238|192\.1\.1\.90'
sudo -l   # reintentar, por si cambió
```

Si `192.1.1.238` sigue `ESTABLISHED` → confirma tráfico DVAL vigente sin depender de acceso a la DB. Si aparece con puerto (`:1521`/`:1525`), anotarlo — ninguna sesión anterior llegó a ver el puerto real.

### 2. `DBClientes.238` (`192.1.1.238`) — cierre de capa 6

Sin credencial confirmada todavía (no hay ninguna probada específicamente contra esta IP). Probar primero el `root` que ya sirvió para `192.1.1.31`/`.190`/`.32` (BOCA/ABB/DCVIAJES/ESYOP) — mismo rango `192.1.1.x`, mismo patrón que esas cuatro:

```
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@192.1.1.238
cat /etc/oratab
ps -ef | grep pmon
sqlplus / as sysdba
  SELECT name, open_mode, cdb FROM v$database;
  SELECT username, machine, program FROM v$session WHERE username IS NOT NULL;
  SELECT username, MAX(timestamp) FROM dba_tab_modifications GROUP BY username ORDER BY 2 DESC;  -- último DML, filtrar CONDOR
  SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET';  -- ¿WE8ISO8859P1?
```

Si `/etc/oratab` muestra más de una instancia (como pasó en `.190` con `GRIMALDI`/`SECLA`/`REXTEST`/etc.), anotar todas — podrían ser cabos sueltos de otros clientes, igual que en ABB.

## Sesión 12/13 sep 2026 — qué se cerró y qué quedó bloqueado

- **Capa 3 confirmada de escritorio** (ya estaba cerrada de una sesión anterior, sin necesidad de acceso nuevo).
- **Capa 4 — `netstat` repetido, sin sudo.** `WebLogic.191` mostró en el momento de la consulta **solo** `192.1.1.90:1521 ESTABLISHED` (la DB compartida `Database .90`/`CDRADM`) — ni `.238` (DVAL) ni `.32` (CEFAS, que sí estaba activa el 25 ago) aparecieron. Es una foto de un instante tranquilo, no evidencia de inactividad de DVAL; queda pendiente repetir en otro horario.
- **Capa 6 — acceso directo a `192.1.1.238` bloqueado, las dos cuentas conocidas probadas.** `root` (la que sirvió en `.31`/`.32`/`.190`) **rechazada**; `soportesmart` (la que anda en `.191`) **también rechazada**. Sin una tercera cuenta conocida, este camino queda cerrado hasta conseguir credencial nueva. **Hallazgo colateral importante:** descarta la hipótesis de "root funciona por segmento de red `192.1.1.x`" que estaba anotada en `QUESTIONS.md` — `.238` es del mismo segmento que `.31`/`.32`/`.190` y aun así rechazó la misma credencial. No hay cuenta universal, cada host tiene su propia contraseña. Actualizado en `QUESTIONS.md`.
- **Balance:** DVAL queda con **1 de 7 capas cerradas en firme (la 3)**, capa 4 con host identificado pero sin config leída, y capa 6 **frenada por completo** (candidato confirmado por IP, dos cuentas probadas y rechazadas) — sin cambio de score real todavía, pero con el camino y el bloqueo mucho más claros que antes de esta sesión.

## Al terminar

1. Completar `clients[DVAL].database.resolved[0]` en `infra/inventory.json` con lo que confirme la sesión (`resolved_by: teamviewer`, SID real, `open_mode`, último DML) y sumar un `confirmation`/`notes` al VM `DBClientes.238` como el que ya tiene `DBClientes.190`.
2. Anotar en `infra/findings.md`, sección de resueltos, la reatribución de la conexión `192.1.1.238` del `netstat` del 25 ago (hasta ahora "sin identificar") a DVAL — y si `192.1.1.90` se identifica de paso, sumarla también.
3. Actualizar `matrix_detail.validacion_pendiente` de DVAL si la sesión aporta algo sobre el plan/fecha de migración a `10.77.7.14`/`PRODDVAL` (poco probable desde la DB actual, pero preguntar si hay banner/mensaje al respecto).
4. Actualizar `verificacion_completitud_clientes.md` (DVAL deja de ser "sin cambios") y `resumen_relevamiento_alta_cliente.md` con el resultado.
5. Si `WebLogic.191` sigue sin sudo: dejarlo anotado como limitación estructural del host (tercera vez que se confirma), no como algo a reintentar cada vez sin una razón nueva.
