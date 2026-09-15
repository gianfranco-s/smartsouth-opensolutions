# Relevamiento de alta de cliente — camino punta a punta (GIAR de referencia)

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md), [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md), [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md), [`plan_relevamiento_alta_boca.md`](plan_relevamiento_alta_boca.md) y [`plan_relevamiento_alta_abb.md`](plan_relevamiento_alta_abb.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Sexto trazado, elegido en vez de continuar ROMAN.** GIAR (Arris de Argentina S.A.) es el ítem 1 de la lista de prioridades de `infra/findings.md` ("Confirmar el estado real de ABB y GIAR — ¿de baja, o solo mantenimiento?"). ABB ya se cerró (apagado de hecho desde el 1-jul-2026). GIAR queda como el único de los dos sin verificación en vivo, y tiene una pieza que ningún otro cliente tuvo hasta ahora: **dos stacks completos y separados** — uno nuevo (compartido con EBY/ROMAN en `OPENWLPROD01`) y uno legado, entero, en el segundo sitio ESXi aislado (`192.1.3.252`), detrás de un firewall pfSense propio (`FW`) con IP pública dedicada.

## Por qué GIAR (impacto sobre el resto del relevamiento)

- **Cierra la pregunta de baja de ABB/GIAR.** La matriz se contradice a sí misma sobre GIAR: el campo formal dice `"Mantenimiento solamente"`, pero una nota suelta dice que GIAR (junto con ABB) "está de baja, se mantienen las bases". Con ABB ya resuelto por evidencia dura (cero sesiones/DML desde jul-2026), GIAR es el único de los dos que falta someter a la misma prueba.
- **Resuelve el "segundo host ESXi" (`192.1.3.252`), abierto desde hace semanas.** `topology.md` §2 lo marca como "probablemente un sitio separado, sin confirmar". Ahí viven **tanto** el legado de GIAR (`WL-GIAR` `10.10.1.50`, `DB-GIAR` `10.10.1.9`) **como** el legado de ROMAN (`WL-CLIENTES` `172.18.5.40`) y de Argocean (mismo `WL-CLIENTES`) — y el firewall que los expone, `FW` (`192.1.3.1`, ya confirmado pfSense, dashboard `fwClientes`). Trazar GIAR de punta a punta en este segmento resuelve de paso una pregunta que toca a tres clientes a la vez.
- **Hallazgo nuevo sin explotar todavía: `giarprod.condorenterprise.com.ar` → `200.55.243.117:80`, habilitado en el NPM de `DOCKER-DEB`.** Esa IP pública **no es de `DOCKER-DEB` ni de `FWOPEN`** — es una de las cinco IPs de la propia VM `FW` (`10.10.1.1`, `192.1.3.1`, `172.18.5.2`, `200.55.243.116`, `200.55.243.117`). O sea: el tráfico de GIAR entra por `DOCKER-DEB` pero **sale de nuevo hacia otro firewall público** (`FW`) antes de llegar a la app real — patrón que no se vio en ningún otro cliente del proyecto hasta ahora. Revisar el NAT de `FW` es lo que le da sentido a esta ruta.
- **Segunda DB candidata (`PRODGIAR`/`10.77.7.11`) ya tiene PDB viva, pero sin tráfico visto.** El 6 sep, `v$session` sobre `PRODGIAR` (en `OPENDBPROD001`/`CDBOPEN03`, el mismo box que resolvió Rex Argentina) solo mostró sesiones `SYS` internas — una foto de un instante, no evidencia de inactividad. Falta lo mismo que cerró ABB/BOCA/DCVIAJES/ESYOP: mirar `dba_tab_modifications` del schema de aplicación para un último-DML, que no depende de pescar una sesión en el momento exacto.
- **`OPENWLPROD01` ya es terreno conocido.** Mismo box con `sudo (ALL) ALL` usado para cerrar EBY y avanzar ROMAN — el `tnsnames.ora` ya reveló los alias `PRODGIAR`/`QAGIAR` → `10.77.7.11`. Falta releer `formsweb.cfg` buscando si hay una sección `[giar]`/`[prodgiar]` real (como las hay para `[csm]`/`[ebyprod]`) o si GIAR en ese box es solo un alias de DB sin app desplegada — cosa que cambiaría la interpretación de qué stack es "el real".

## Estado de partida (12 sep 2026)

De `infra/inventory.json` → `clients[GIAR]`, `infra/findings.md`, `verificacion_completitud_clientes.md` (GIAR ~58%) y `PLAN.md`:

- **Cliente:** `Arris de Argentina S.A.` (code `GIAR`). Producto: Enterprise `Sí`, AFIP `Sí`, Work `No`; Condor Link/Self Service/Jasper en blanco; `version_condor: 2025`. `observaciones` de la matriz: *"Ya se está usando como producción."* — dato a favor de que sigue vivo, en tensión directa con la nota de baja.
- **Estado en inventario:** `"Mantenimiento solamente"` (campo formal) vs. nota suelta de baja compartida con ABB (`status_note` en el JSON) — la misma disputa que tenía ABB antes de resolverse.
- **Dos stacks, legado vs. nuevo — igual patrón que ROMAN:**
  - **Legado:** `WL-GIAR` (`10.10.1.50`, RHEL 6, `esxi_host: 192.1.3.252`, uptime 627 días, `used_by_clients: []` — vínculo solo por *name hint*, no confirmado) + `DB-GIAR` (`10.10.1.9`, Oracle Linux 6, mismo host ESXi, uptime **1017 días**, sí está en `used_by_clients` de GIAR con `role: database`). Segmento `10.10.1.x`, detrás del firewall `FW` (`192.1.3.1`/`10.10.1.1`/`172.18.5.2`/`200.55.243.116`/`.117`).
  - **Nuevo (¿solo DB, sin app propia?):** `OPENWLPROD01` (`10.77.7.201`, compartido con EBY/ROMAN) — alias `PRODGIAR`/`QAGIAR` en su `tnsnames.ora` apuntan a `OPENDBPROD001` (`10.77.7.11`, PDB `PRODGIAR` confirmada `READ WRITE`). **`QAGIAR` no existe como PDB provisionada** (la QA de GIAR probablemente nunca se armó — mismo hallazgo que con `PRODCEFAS`).
- **Dominio de entrada nuevo (12 sep, sin explotar):** `giarprod.condorenterprise.com.ar` → `200.55.243.117:80`, **habilitado**, en el NPM de `DOCKER-DEB` (proxy host id **76** según `dockerdeb_proxy_host_2026-09-01.tsv`, creado 31-mar-2025). El destino es una IP pública de la propia VM `FW`, no una IP interna — la ruta continúa detrás de ese segundo firewall, sin trazar todavía.
- **Matriz (`matrix_detail`):** `sid_actual: GIARG`, `version_db: 11.2.0.4.0`, `edicion_db: EE`, `tamaño: 60G`, `charset: WE8ISO8859P1`, `servidor_db_destino`/`ip_db_destino: 10.77.7.11`, `sid_nuevo: prodgiar`.
- **WebLogic — versión ya resuelta (16 ago 2026):** `12.2.1.4.0`, confirmada en la pantalla de login de `10.77.7.201:7001/console` (sin credencial de consola) — cierra la fila "GIAR / Versión de WebLogic" de Discrepancias a favor del valor técnico.
- **Cuenta:** `soportesmart` con `sudo (ALL) ALL` en `OPENWLPROD01` (confirmado en las sesiones de EBY/ROMAN). Sin credencial conocida todavía para `OPENDBPROD001` más allá del acceso `su - oracle` ya usado para Rex; sin credencial para `WL-GIAR`/`DB-GIAR` (nunca se intentó `soportesmart`/`root` ahí).
- **Discrepancia de la matriz, sin cerrar:** solo queda la de EBY (servidor WebLogic) y Enerflex (charset) en la tabla — GIAR ya no tiene fila abierta ahí, la pregunta de fondo es el **estado del cliente** (`QUESTIONS.md`), no un dato técnico.

## El camino, capa por capa

| # | Capa | Estado (12 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | 🔴 **Blind spot confirmado (13 sep 2026): el único dominio conocido apunta al stack muerto.** `giarprod.condorenterprise.com.ar` (id 76, `DOCKER-DEB`) → `FW` → `WL-GIAR` (`10.10.1.50`), que está `Powered Off`. Esa ruta pública está rota de hecho. **Para el stack nuevo (`OPENWLPROD01`, confirmado con app real desplegada — ver capa 4) no existe ningún dominio conocido**: se revisaron las 101 rutas ya transcriptas de `DOCKER-DEB` filtrando por destino `10.77.7.201` — solo aparecen `eby-prod`/`eby-qa`/`romanprod`/`romanqa`, ninguna de GIAR. No sabemos por dónde (o si) entran usuarios reales al deployment que sí confirmamos que existe. | **Próximo paso concreto.** Revisar los 2 NPM sin transcribir del todo (`OPENDOCKER04`/`10.77.7.5:81` y `VM-DOCKER-Clientes (1)`/`192.1.3.4:81`) buscando cualquier entrada `giar*` o sin etiquetar hacia `10.77.7.201`. Si no aparece nada ahí tampoco, las opciones que quedan son: acceso solo por VPN interna (sin NPM público), o deployment real pero sin uso — ninguna de las dos se puede confirmar sin la sesión `v$session` en día hábil (ver capa 6). |
| 2 | Nginx Proxy Manager | 🟡 **Parcial.** `DOCKER-DEB` (`192.1.1.37:81`) tiene la entrada legada (`giarprod`), pero ninguna para el stack nuevo. | *Completeness*: revisar `OPENDOCKER04`/`VM-DOCKER-Clientes (1)` — ver capa 1, mismo paso. |
| 3 | Firewall / NAT | ✅ **CERRADA (12 sep 2026).** Transcripción completa del NAT de `FW` (`pfsense-192.1.3.1-nat-rules.txt`, 53 reglas, cargada en `inventory.json` → `vms[FW].nat_rules`) confirma: `200.55.243.117:80` → `10.10.1.50:80` ("GIAR WL http") y `:443` → `:443` ("GIAR WL"), `source: *` — coincide exacto con `giarprod.condorenterprise.com.ar` del NPM. `WL-GIAR` es el backend real, confirmado por config de firewall, no solo hipótesis. SSH también mapeado: `200.55.243.117:215` → `10.10.1.50:22`. `DB-GIAR` (`10.10.1.9`): SSH `.117:212`, Oracle `.117:1522`. Bonus: candidato de DB nuevo sin identificar, `10.1.1.10` ("GIAR DB 1521 NUEVO", `.117:51521`). | Ninguno — capa cerrada. |
| 4 | App — motor clásico | ✅ **Legado muerto, nuevo confirmado real (13 sep 2026).** `WL-GIAR` (`10.10.1.50`) `Powered Off` en vCenter — sin proceso posible. La ruta pública NAT-eada (`giarprod.condorenterprise.com.ar` → `FW` → `WL-GIAR`) está rota de hecho. Pero `OPENWLPROD01` tiene secciones reales `[giargprod]`/`[activaciongiarg]`/`[giargprodFSAL]` en `formsweb.cfg` (`pageTitle=Giarg PRODUCCION`, `userid=@PRODGIAR`) — deployment deliberado, no un alias de paso. | Ninguno para config. Falta sesión de usuario real en día hábil (capa 6). |
| 5 | App — Docker/reportes | ⬜ **Sin trazar.** Matriz no marca Jasper/Condor Link para GIAR (campos en blanco, no "No"). | `grep -i giar` sobre `proxy_hosts.csv`/`dockerdeb_proxy_host_2026-09-01.tsv` — ¿hay `giarjasper.*` o similar? Si aparece, `docker ps` en el host destino. Baja prioridad si el campo en blanco se confirma como "no aplica". |
| 6 | Base de datos | 🟡 **Legado descartado, nuevo sin sesión capturada dos veces (sábado y lunes).** `DB-GIAR` (`10.10.1.9`) confirmada `Apagado`. `PRODGIAR` (PDB en `OPENDBPROD001`): `v$session` filtrado por `con_id` repetido el 13-sep (domingo) y el 14-sep (lunes, día hábil) — **ambas veces solo la sesión `SYS` de la propia consulta, cero aplicación.** `dba_tab_modifications` sin estadísticas (0 filas, las 6 schemas de esta PDB). En tensión con `formsweb.cfg` real (`[giargprod]` deployment deliberado) y recompilación de procedimientos `CONDOR` 12/13-sep. | **PRÓXIMO PASO.** `access.log` de `WLS_FORMS` en `OPENWLPROD01` (ya con sudo) — buscar `config=giargprod`/`activaciongiarg`, mismo cierre que fue decisivo para ROMAN. Complementar con `netstat -tn \| grep 10.77.7.11` en el mismo box. |
| 7 | Almacenamiento | ⬜ **Sin trazar.** Sin indicio todavía de NFS/volumen dedicado. | Si la capa 4 confirma dónde vive la app real, `mount`/`fstab` en ese box — mismo patrón que CEFAS/EBY. Baja prioridad hasta cerrar 3, 4 y 6. |

## Orden de la sesión sugerido (qué correr, dónde)

Ordenado por costo marginal — primero lo que resuelve más de una capa a la vez.

### 1. ✅ `FW` (`192.1.3.1`) — hecho (12 sep 2026)

Dashboard pfSense accedido, credencial `smartsouth`. Las 53 reglas de NAT ya están transcriptas en `pfsense-192.1.3.1-nat-rules.txt` y cargadas en `inventory.json` → `vms[FW].nat_rules`. Resultado: capa 3 de GIAR cerrada (`200.55.243.117:80/443` → `10.10.1.50`/`WL-GIAR`), más colateral grande — `WL-ROMAN`/`DB-ROMAN-HISTORICO` resueltos, blind spot `200.55.243.116:2235` resuelto, y un blind spot nuevo (segundo stack CEFAS + cliente "SYT" sin documentar, ver `infra/findings.md` y `blind_spots` en `inventory.json`).

### 2. `WL-GIAR` (`10.10.1.50`) — ✅ resuelto, negativo (12 sep 2026)

~~SSH directo / vía NAT de `FW`.~~ **No hizo falta llegar a SSH:** al ir a vCenter para diagnosticar por qué el SSH directo no respondía, la VM apareció **`Powered Off`** — apagada de verdad, no solo sin sesiones. `ExportList20260912.csv` (refresh de vCenter del mismo día) confirma además que **`DB-GIAR` corrió la misma suerte** (`Encendido`→`Apagado`). **Todo el stack legado de GIAR está apagado.** Cierra capas 4 y 6 del legado por ausencia directa — no puede haber proceso vivo ni instancia Oracle levantada en una VM apagada. Evidencia más fuerte que la de ABB (que seguía encendida sin tráfico). Ver `infra/findings.md`.

### 3. `10.1.1.10` — candidato de DB nuevo, sin tocar todavía

Si el paso 2 confirma que `DB-GIAR` (legado) está mudo, este es el siguiente candidato: NAT `200.55.243.117:51521` → `10.1.1.10:1521`. Probar `ssh`/`sqlplus` directo a `10.1.1.10` si el segmento resulta alcanzable — ojo que la subred no coincide con ninguna conocida, podría ser un typo de pfSense por `10.10.1.10` (verificar ambas si la primera no responde).

### 4. `OPENDBPROD001`/`CDBOPEN03` (ya accesible, `su - oracle`)

1. `ALTER SESSION SET CONTAINER = PRODGIAR;`
2. `SELECT username, machine, program, COUNT(*) FROM v$session GROUP BY username, machine, program;` — repetir en un día hábil si el 6-sep fue sábado/día ocioso (verificar).
3. Buscar el schema de aplicación (probablemente `CONDOR`, como en el resto del parque) y correr `dba_tab_modifications` para un último-DML — el mismo truco que cerró ABB sin depender de pescar una sesión activa.

### 5. `DOCKER-DEB` (`192.1.1.37`) — ya con acceso de la sesión de ROMAN

`sudo docker exec <NPM> sh -c "find /data/logs -name 'proxy_host-*.log' -exec grep -l giarprod {} \;"` → `tail -50` del log que aparezca. Mismo procedimiento que para `romanprod`.

## Qué cerraría esta sesión

Si el paso 1 revela un NAT real y el paso 2 encuentra algo vivo en `WL-GIAR`/`DB-GIAR`: GIAR pasa de "dos candidatos sin confirmar" a un trazado con capas 3, 4, 6 y 7 cerradas — comparable a ABB/ROMAN. Si en cambio `WL-GIAR`/`DB-GIAR` están mudos (nada escuchando, sin instancia Oracle levantada): eso es evidencia dura de que el legado está muerto, y la pregunta se reduce a si `PRODGIAR` (el candidato nuevo) tiene tráfico real — lo que cierra el paso 3. Cualquiera de los dos resultados avanza directamente la pregunta abierta de `QUESTIONS.md` sobre la baja de GIAR.

## Actualización (12 sep 2026) — resultado del segundo escenario

El escenario "legado mudo" se confirmó, y más fuerte de lo esperado: no fue necesario ni SSH — `WL-GIAR` y `DB-GIAR` aparecieron directamente `Powered Off` en vCenter (confirmado además por `ExportList20260912.csv`, un refresh del mismo día). Todo el stack legado está apagado. La pregunta se reduce exactamente a lo previsto: **¿`PRODGIAR` (el candidato nuevo, en `OPENDBPROD001`) tiene tráfico real?**

**Avance parcial, sesión pausada por carga del servidor (12 sep 2026).** `ALTER SESSION SET CONTAINER = PRODGIAR` + `dba_segments` (top schemas por tamaño) dio un hallazgo nuevo interesante: además de `CONDOR` (7.5 GB, real), `CONDORBKP` (4.5 GB) y `CONDOR_ORIG` (4.2 GB) — que parecen ser copia viva/backup/original de una migración —, aparece un schema **`MOTOROLA`** (464 MB, 70 segmentos). GIAR = "Arris de Argentina S.A."; Arris adquirió el negocio de set-top-boxes de Motorola Home hace años — `MOTOROLA` podría ser el nombre legado real de los datos de GIAR, previo al rebrand a Arris. Sin confirmar todavía.

`dba_tab_modifications` para estos 6 schemas (`CONDOR`/`CONDORBKP`/`CONDOR_ORIG`/`MOTOROLA`/`CONDORBI`/`CONDORD`) dio **0 filas** — sin estadísticas de modificación trackeadas, no necesariamente sin uso. Se intentó `v$session` como alternativa, pero **sin filtrar por `CON_ID` la consulta mezcla sesiones de toda la CDB** (aparecieron `MAIETA`/`MCORREA`, que son usuarios ya vistos en la sesión de Rex Argentina — señal de que la vista no estaba acotada a `PRODGIAR`). La sesión se cortó dos veces y se decidió parar para no sobrecargar el server, sin llegar a correr la versión filtrada.

**Retomado (13 sep 2026).** `v$session` filtrado por `con_id` (corrigiendo el problema de mezclar toda la CDB): **cero sesiones de aplicación** en `PRODGIAR` — solo la sesión `SYS` de la propia consulta. Pero la consulta fue en sábado, mismo caveat que ya jugó en contra con ROMAN/DCVIAJES (no es prueba de inactividad real, solo de esta ventana). `dba_objects.last_ddl_time` sobre `MOTOROLA`/`CONDOR` dio una señal a favor de actividad: procedimientos de negocio de `CONDOR` (`EJECUTA_NOTIF`, `JENVIOALERTAS_VENCIMP`, `BORRA_DEBUG_APP`) tocados **12/13-sep-26** (hoy/ayer); el propio de `MOTOROLA` (`GENERA_ARCHIVOS`) no se toca desde 29-may-26.

**Decisivo: `formsweb.cfg` real de `OPENWLPROD01` tiene secciones dedicadas a GIAR.** Ruta real (la del glob corto no existía, hubo que ubicarla con `sudo find`): `/u01/app/oracle/product/12.2.1/user_projects/domains/base_domain/config/fmwconfig/servers/WLS_FORMS/applications/formsapp_12.2.1/config/formsweb.cfg`. `sudo grep -iE giar` encontró **`[giargprod]`** (`pageTitle=Giarg PRODUCCION`, `userid=@PRODGIAR`, `form=/u01/cliente/giarg/cdr2/menues/cdr2.fmx`), `[activaciongiarg]`, `[giargprodFSAL]` — "Giarg" coincide letra por letra con `sid_actual: GIARG` de la matriz. **Deployment real y deliberado, mismo patrón que EBY/ROMAN.** GIAR migró de verdad al stack nuevo — no es un alias de DB sin app, como se sospechaba horas antes.

**Estado final de la sesión: legado muerto (confirmado sin dudas), stack nuevo real y con señales de actividad (config + recompilación reciente de código), pero sin sesión de usuario capturada en vivo (sábado).** No se puede concluir "GIAR de baja" — al contrario, el hallazgo apunta a una migración exitosa. Único paso que queda: repetir la consulta de `v$session` un día hábil.

```sql
ALTER SESSION SET CONTAINER = PRODGIAR;
SELECT username, machine, program, status, COUNT(*)
FROM v$session
WHERE type='USER' AND con_id = (SELECT con_id FROM v$pdbs WHERE name='PRODGIAR')
GROUP BY username, machine, program, status
ORDER BY 5 DESC;
```

## Actualización (14 sep 2026, lunes — día hábil) — v$session repetido, mismo resultado vacío

Corrido el query filtrado por `con_id` en horario hábil (lunes 14-sep, no sábado). Resultado: **una sola fila, `SYS`/`sqlplus@opendbprod001.open`** — la sesión de la propia consulta. **Cero sesiones de aplicación** en `PRODGIAR` en este instante, ahora sin el caveat de "es fin de semana".

**No alcanza para declarar capa 6 en 0 todavía** — sigue siendo una foto de un instante (mismo límite que ya jugó en contra con ROMAN antes de que el `access.log` lo confirmara del todo), y `dba_tab_modifications` ya había dado 0 filas para los 6 schemas de esta PDB (sin estadísticas trackeadas, no es evidencia de inactividad por sí sola). Lo que sí cambia: ya no hay una excusa de "día no hábil" para el resultado negativo — sube el peso de la evidencia hacia "sin uso", pero todavía en tensión con el hallazgo de `formsweb.cfg` (deployment real) y la recompilación reciente de procedimientos de `CONDOR` (12/13-sep).

**Próximo paso, más barato que repetir `v$session` a ciegas:** replicar para GIAR el mismo cierre que sí fue decisivo para ROMAN — el `access.log` de `WLS_FORMS` en `OPENWLPROD01` (ya se tiene acceso `sudo` a ese box). Si aparece un `config=giargprod`/`activaciongiarg` con `POST /forms/lservlet 200` reciente → GIAR vivo, contradice el `v$session` vacío (sesión pooled que no quedó en la foto). Si no aparece nunca → mismo patrón que cerró ROMAN (cero tráfico en dos fuentes independientes), y ahí sí se puede tratar como resuelto.

```
sudo find /u01/app/oracle/product/12.2.1/user_projects/domains/base_domain/servers/WLS_FORMS/logs -iname "access*.log"
sudo grep -iE 'giarg|activaciongiarg' <access.log encontrado> | tail -50
```

Si el log rota diario y no llega a varios días atrás, complementar con `sudo netstat -tn | grep 10.77.7.11` (conexión Oracle real desde `OPENWLPROD01` hacia `PRODGIAR`, mismo chequeo que se usó para EBY/ROMAN).

## Cierre (14 sep 2026, lunes — día hábil): cuatro fuentes en cero, GIAR queda con el mismo perfil que ROMAN

- `netstat -tn | grep 10.77.7.11` en `OPENWLPROD01`: **sin resultado** — cero conexiones a la DB de GIAR.
- `access.log` de `WLS_FORMS` encontrado en `.../servers/WLS_FORMS/logs/access.log` (+ 7 rotados, `access.log00521`–`00527`, cubriendo jueves 10-sep a lunes 14-sep — 3 días hábiles completos). `grep -iE 'giarg|activaciongiarg'` sobre el actual **y** los rotados juntos (`access.log*`): **cero coincidencias.**
- `v$session` (con el filtro por `con_id` ya corregido) repetido en día hábil: **cero sesiones de aplicación**, igual que el sábado.

**Cuatro fuentes independientes, todas en cero** — más evidencia que la que cerró ROMAN (dos fuentes). GIAR tiene un deployment de producción real y deliberado (`formsweb.cfg`, alias `PRODGIAR`/`GIARG`) pero ningún usuario activo observable en ningún punto de la ruta, en ningún método de verificación probado. No es una prueba de baja formal (sigue siendo pregunta de negocio, `QUESTIONS.md`), pero la evidencia técnica ahora inclina claramente hacia la nota informal de la matriz ("de baja") por sobre el campo formal ("Mantenimiento solamente").

**Estado final de las 7 capas:**

| Capa | Estado |
|---|---|
| 1. Dominio de entrada | 🔴 Legado muerto; sin dominio conocido para el stack nuevo (nadie encontró por dónde entrarían usuarios reales) |
| 2. NPM | 🟡 Parcial — depende de 1 |
| 3. Firewall/NAT | ✅ Cerrada |
| 4. App — motor clásico | ✅ Cerrada (config real, sin tráfico) |
| 5. App — Docker/reportes | ⬜ Sin trazar, baja prioridad dado el resultado |
| 6. Base de datos | ✅ Cerrada — legado apagado, nuevo confirmado sin tráfico (4 fuentes) |
| 7. Almacenamiento | ⬜ Sin trazar, baja prioridad dado el resultado |

Sin más pasos bloqueantes para este trazado. Cabo suelto no crítico: el schema `MOTOROLA` (posible nombre legado pre-rebranding Arris/Motorola Home), sin confirmar y sin relación con la pregunta de tráfico.
