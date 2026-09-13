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
| 1 | Dominio de entrada | 🟡 **Identificado, sin tráfico verificado.** `giarprod.condorenterprise.com.ar` (id 76, `DOCKER-DEB`) → `200.55.243.117:80` (IP pública de `FW`, no de una VM app). Legado: sin dominio propio conocido todavía para `WL-GIAR`. | Buscar el access log real (`sudo docker exec <NPM> sh -c "find /data/logs -name 'proxy_host-*.log' -exec grep -l giarprod {} \;"` — el patrón que ya usamos en ROMAN, porque el nombre de archivo no coincide siempre con el `id`). `POST/GET` recientes → GIAR vivo por esta ruta. |
| 2 | Nginx Proxy Manager | 🟢 **Identificado.** `DOCKER-DEB` (`192.1.1.37:81`) tiene la entrada. | *Completeness*: revisar si `OPENDOCKER04`/`VM-DOCKER-Clientes (1)` (los 2 NPM sin transcribir del todo) tienen alguna otra entrada `giar*`. |
| 3 | Firewall / NAT | ✅ **CERRADA (12 sep 2026).** Transcripción completa del NAT de `FW` (`pfsense-192.1.3.1-nat-rules.txt`, 53 reglas, cargada en `inventory.json` → `vms[FW].nat_rules`) confirma: `200.55.243.117:80` → `10.10.1.50:80` ("GIAR WL http") y `:443` → `:443` ("GIAR WL"), `source: *` — coincide exacto con `giarprod.condorenterprise.com.ar` del NPM. `WL-GIAR` es el backend real, confirmado por config de firewall, no solo hipótesis. SSH también mapeado: `200.55.243.117:215` → `10.10.1.50:22`. `DB-GIAR` (`10.10.1.9`): SSH `.117:212`, Oracle `.117:1522`. Bonus: candidato de DB nuevo sin identificar, `10.1.1.10` ("GIAR DB 1521 NUEVO", `.117:51521`). | Ninguno — capa cerrada. |
| 4 | App — motor clásico | 🟡 **Backend identificado (capa 3), falta confirmar que está vivo.** `WL-GIAR` (`10.10.1.50`) es el backend real de la ruta nueva/pública (confirmado por NAT). Nadie entró todavía. `OPENWLPROD01` sigue con el alias de DB sin confirmar sección `formsweb.cfg` propia. | **PRÓXIMO PASO INMEDIATO.** SSH a `10.10.1.50` — probar directo si el segmento es alcanzable desde la red interna (`ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@10.10.1.50`); si no responde, usar la ruta NAT ya confirmada: `ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa -p 215 soportesmart@200.55.243.117`. Adentro: `sudo ss -tlnp` / `ps -ef \| grep -iE 'java\|weblogic\|forms'` — ¿hay algo escuchando en :80/:443? En `OPENWLPROD01` (ya con sudo): `sudo grep -iE 'giar' .../formsweb.cfg` — si no hay sección `[giar]`/`[prodgiar]`, GIAR no tiene app desplegada ahí, solo el alias TNS "de paso" (mismo caso que se descartó para `PRODCEFAS`/`QAGIAR` en Rex). |
| 5 | App — Docker/reportes | ⬜ **Sin trazar.** Matriz no marca Jasper/Condor Link para GIAR (campos en blanco, no "No"). | `grep -i giar` sobre `proxy_hosts.csv`/`dockerdeb_proxy_host_2026-09-01.tsv` — ¿hay `giarjasper.*` o similar? Si aparece, `docker ps` en el host destino. Baja prioridad si el campo en blanco se confirma como "no aplica". |
| 6 | Base de datos | 🟡 **Dos candidatos, ninguno cerrado del todo.** `PRODGIAR` (PDB en `OPENDBPROD001`, `READ WRITE`, solo sesiones `SYS` vistas el 6-sep) vs. `DB-GIAR` (legado, `10.10.1.9`, nunca accedida). | (a) Repetir `ALTER SESSION SET CONTAINER=PRODGIAR; SELECT username,machine,count(*) FROM v$session GROUP BY username,machine;` en `CDBOPEN03` — o mejor, imitar el cierre de ABB: `SELECT table_name, MAX(timestamp) FROM dba_tab_modifications WHERE ... GROUP BY table_name ORDER BY 2 DESC` sobre el schema de aplicación (¿`CONDOR`, como en el resto? confirmar nombre) para un último-DML que no dependa de pescar una sesión activa. (b) SSH/`sqlplus` a `10.10.1.9` (`DB-GIAR`) — `ps -ef \| grep pmon` primero, para ver si hay siquiera una instancia Oracle levantada (si no, el legado ya está descartado sin necesitar credencial). |
| 7 | Almacenamiento | ⬜ **Sin trazar.** Sin indicio todavía de NFS/volumen dedicado. | Si la capa 4 confirma dónde vive la app real, `mount`/`fstab` en ese box — mismo patrón que CEFAS/EBY. Baja prioridad hasta cerrar 3, 4 y 6. |

## Orden de la sesión sugerido (qué correr, dónde)

Ordenado por costo marginal — primero lo que resuelve más de una capa a la vez.

### 1. ✅ `FW` (`192.1.3.1`) — hecho (12 sep 2026)

Dashboard pfSense accedido, credencial `smartsouth`. Las 53 reglas de NAT ya están transcriptas en `pfsense-192.1.3.1-nat-rules.txt` y cargadas en `inventory.json` → `vms[FW].nat_rules`. Resultado: capa 3 de GIAR cerrada (`200.55.243.117:80/443` → `10.10.1.50`/`WL-GIAR`), más colateral grande — `WL-ROMAN`/`DB-ROMAN-HISTORICO` resueltos, blind spot `200.55.243.116:2235` resuelto, y un blind spot nuevo (segundo stack CEFAS + cliente "SYT" sin documentar, ver `infra/findings.md` y `blind_spots` en `inventory.json`).

### 2. `WL-GIAR` (`10.10.1.50`) — PRÓXIMO PASO

1. SSH — probar primero directo (puede que el segmento sea alcanzable desde la red interna sin pasar por NAT):
   ```
   ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@10.10.1.50
   ```
   Si no responde, usar la ruta NAT ya confirmada (puerto `215` en la IP pública de `FW`):
   ```
   ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa -p 215 soportesmart@200.55.243.117
   ```
2. `sudo ss -tlnp` o `netstat -tlnp` — ¿algo escucha en `:80`/`:443` (lo que confirmaría la ruta NAT) o en otro puerto de Forms/WebLogic?
3. `ps -ef | grep -iE 'java|weblogic|forms'` — ¿hay un proceso de aplicación vivo?
4. Si responde: repetir en `10.10.1.9` (`DB-GIAR`, SSH directo o `-p 212` en `200.55.243.117`) — `ps -ef | grep pmon` para ver si hay una instancia Oracle levantada, y `cat /etc/oratab`.

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
