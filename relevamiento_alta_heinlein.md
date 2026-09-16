# Relevamiento de alta de cliente — camino punta a punta (Heinlein de referencia)

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md), [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md), [`relevamiento_alta_eby.md`](relevamiento_alta_eby.md), [`relevamiento_alta_boca.md`](relevamiento_alta_boca.md), [`relevamiento_alta_abb.md`](relevamiento_alta_abb.md), [`relevamiento_alta_roman.md`](relevamiento_alta_roman.md), [`relevamiento_alta_giar.md`](relevamiento_alta_giar.md), [`relevamiento_alta_argocean.md`](relevamiento_alta_argocean.md), [`relevamiento_alta_esyop.md`](relevamiento_alta_esyop.md) y [`relevamiento_alta_rex.md`](relevamiento_alta_rex.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Primer trazado dedicado a Heinlein — y trae consigo una pista de alto valor, ya encontrada, nunca seguida.** Heinlein figura en el inventario como `"Solo infraestructura"` (ni siquiera está en la tabla funcional de la matriz, solo en el inventario técnico — la propia hoja Discrepancias lo dice: *"Heinlein y Maipú aparecen en el inventario técnico, pero no en la tabla funcional. Se agregaron para no perder visibilidad"*). Pero el 6 sep 2026, durante la sesión de Rex Argentina, un `v$pdbs` sobre `OPENDBPROD001`/`CDBOPEN03` listó una PDB llamada **`HEINLEIN_PROD`** — además de la `HEINLEIN_TEST` ya conocida — y quedó **deliberadamente sin consultar**, fuera de foco a pedido explícito en ese momento (`infra/findings.md`: *"quedó deliberadamente sin chequear... retomar si Heinlein vuelve a ser prioridad"*). Ese momento es ahora.

## Por qué Heinlein ahora (impacto sobre el resto del relevamiento)

- **La pregunta central ya tiene una pista concreta, sin costo de descubrimiento.** `HEINLEIN_PROD` es una PDB real y provisionada (confirmada por `v$pdbs`, no una suposición) en el mismo host ya conocido y accesible (`OPENDBPROD001`/`CDBOPEN03`, `su - oracle`, sin credencial nueva). Si tiene tráfico real, el `status: "Solo infraestructura"` del inventario queda desactualizado — mismo tipo de hallazgo que ya pasó con GIAR (la nota informal vs. el campo formal).
- **El ambiente de test ya está parcialmente cerrado, de rebote.** `heinleintest.condor.solutions` → `192.1.2.195:9001` (`OL8LABWL01`), **habilitado** en el NPM de `DOCKER-DEB` (visto 1 sep 2026), y el alias `HEINLEIN_TEST` en el `tnsnames.ora` de `OPENWLPROD01` confirma que apunta a `OPENDBPROD001`. Es config, no sesión en vivo — pero es más que lo que tenían GIAR/ROMAN/ESYOP antes de sus trazados.
- **`OL8LABWL01` nunca se accedió directamente**, aunque ya es "terreno conocido de oídas": es el mismo WebLogic que resultó ser el motor clásico real de **Rex Argentina** (`serzarex.condor.solutions`, tráfico confirmado en vivo el 6 sep). Esa confirmación se hizo enteramente desde el lado de la DB (`v$session` mostrando conexiones *desde* `ol8labwl01.localdomain`) — nadie entró por SSH a esa VM todavía. Es la primera vez que se intenta acceso directo.
- **Dato curioso sin explicar, capaz de reabrir la pregunta del "segundo sitio":** `inventory.json` marca `esxi_host: 192.1.3.252` para `OL8LABWL01` — el mismo host ESXi aislado donde viven `WL-GIAR`/`DB-GIAR`/`WL-ROMAN`/`FW` (rangos `172.18.5.x`/`10.10.1.x`) — pero la IP real de `OL8LABWL01` es `192.1.2.195`, del segmento principal. Si es correcto (no un error de carga del CSV), sugeriría que ese host ESXi "aislado" no está tan aislado de red como se pensaba. No es el objetivo de esta sesión, pero vale la pena anotarlo si surge naturalmente.
- **Bono lateral: `OL8CASLAWL01`.** Blind spot nombrado en `findings.md` — sigue la misma convención de nombre que `OL8LABWL01` (sufijo `WL01`), sin coincidir con ningún cliente de los 15 conocidos. "Casla" es el apodo de San Lorenzo, mismo patrón que "BOCA". Si el acceso a `OL8LABWL01` revela algo sobre convenciones de nombre o vecinos de red, podría aportar de paso — no es el foco.

## Estado de partida (14 sep 2026)

De `infra/inventory.json` → `clients[HEINLEIN]`, `infra/findings.md` y `verificacion_completitud_clientes.md` (Heinlein ~23%):

- **Cliente:** `Heinlein` (code `HEINLEIN`). `status`: `"Solo infraestructura"`. Sin `matrix_detail` real — todos los campos de productos/versión/charset en blanco, `sid_actual: CDBHEIN01` es el único dato. `observaciones`: *"Figura en inventario técnico, no en la tabla funcional de servicios por cliente."* `validacion_pendiente`: *"Completar servicios, versión DB, tamaño, charset y funcionalidades."*
- **WebLogic (capa 4, nunca accedido directamente):** `OL8LABWL01` — IP `192.1.2.195`, Oracle Linux 7, `esxi_host: 192.1.3.252` (ver nota arriba), **uptime 55 días** — segundo uptime más bajo del proyecto según `findings.md` (señal de incorporación/migración reciente, junto con Maipú y EBY). `resolved_by: name`, `match: true`.
- **Base de datos (capa 6, dos candidatos, ninguno con sesión propia):**
  - `HEINLEIN_TEST` → `OPENDBPROD001` (`10.77.7.11`), confirmado por `tnsnames.ora` de `OPENWLPROD01` (2 sep 2026), coincide con el dominio de test. Ambiente de test, no prueba producción.
  - **`HEINLEIN_PROD`** → misma VM, PDB confirmada real vía `v$pdbs` en `CDBOPEN03` (6 sep 2026, sesión de Rex Argentina) — **nunca consultada**, ni `v$session` ni `dba_tab_modifications`. Es el hallazgo central de esta sesión.
- **Dominio de entrada (capa 1, parcial):** `heinleintest.condor.solutions` → `192.1.2.195:9001`, **habilitado** en el NPM de `DOCKER-DEB` (visto 1 sep 2026). Sin dominio conocido de producción — mismo patrón de blind spot que tuvo GIAR antes de su trazado (deployment real sin ruta de entrada identificada).
- **Cuenta:** `admin_user: soportesmart` en el registro del cliente (patrón heredado, sin confirmar específicamente contra `192.1.2.195`). La DB (`OPENDBPROD001`/`CDBOPEN03`) ya es accesible por `su - oracle` desde las sesiones de GIAR/Rex — sin credencial nueva para ese lado.
- **Contexto de host compartido:** `OL8LABWL01` también sirve a **Rex Argentina** (motor clásico real, `serzarex.condor.solutions`) — mismo patrón de WL compartido que `WebLogic.191`/`OPENWLPROD01`, aunque a menor escala (2 clientes conocidos hasta ahora).

## El camino, capa por capa

| # | Capa | Estado (14 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | 🟡 **Parcial.** `heinleintest.condor.solutions` → `192.1.2.195:9001`, habilitado (test). Sin dominio de producción conocido. | Buscar en los NPM sin transcribir del todo (`OPENDOCKER04`, `VM-DOCKER-Clientes (1)`) alguna entrada `heinlein*`/`heinleinprod` — si no aparece, capa 1 de producción queda como blind spot (mismo patrón que GIAR). |
| 2 | Nginx Proxy Manager | 🟡 **Parcial**, mismo NPM (`DOCKER-DEB`, `192.1.1.37:81`) que confirmó el dominio de test. | Igual que capa 1. |
| 3 | Firewall / NAT | ⬜ **Sin trazar específicamente.** `DOCKER-DEB` expone su propio IP pública dedicada — no suele necesitar regla NAT por cliente (mismo patrón que EBY/ROMAN/BOCA en ese mismo NPM). | Baja prioridad — revisar si aparece alguna regla dedicada en `FWOPEN` al pasar (`grep -i heinlein` sobre `nat_rules` ya cargadas). |
| 4 | App — motor clásico | ⬜ **El trazado entero — sin ningún acceso directo previo.** `OL8LABWL01` solo se conoce de oídas (vía tráfico observado desde la DB de Rex). | **PRÓXIMO PASO.** SSH con `soportesmart`/`root`; `ps -ef \| grep -iE 'java\|weblogic\|forms'`, y si hay `sudo`, `formsweb.cfg` buscando secciones `[heinlein]`/`[heinleinprod]` reales — mismo patrón que cerró GIAR/ROMAN/ESYOP. |
| 5 | App — Docker/reportes | ⬜ **Sin datos.** Matriz sin campos de producto para este cliente (no está en la tabla funcional). | Ninguno — sin pista de dónde buscar. |
| 6 | Base de datos | 🟡 **`HEINLEIN_TEST` a nivel config (0.5); `HEINLEIN_PROD` sin consultar — el hallazgo central.** | **PRÓXIMO PASO, prioridad máxima.** `ALTER SESSION SET CONTAINER = HEINLEIN_PROD;` + `v$session` en `OPENDBPROD001`/`CDBOPEN03` (ya accesible, sin credencial nueva). Si sale vacío, `dba_tab_modifications` del schema de aplicación (probablemente `CONDOR`) para un último-DML — mismo truco que cerró ABB/GIAR sin depender de pescar una sesión en el instante exacto. |
| 7 | Almacenamiento | ⬜ **Sin trazar.** | Si la capa 4 da acceso a `OL8LABWL01`, `mount`/`cat /etc/fstab` ahí — mismo patrón que ESYOP/CEFAS/EBY. Baja prioridad hasta cerrar 4. |

## Orden de la sesión sugerido

Ordenado por costo marginal — primero lo que resuelve la pregunta central sin necesitar terreno nuevo.

### 1. `OPENDBPROD001`/`CDBOPEN03` — ya accesible, prioridad máxima

```
su - oracle
sqlplus / as sysdba
ALTER SESSION SET CONTAINER = HEINLEIN_PROD;
SELECT username, machine, program, status, COUNT(*)
FROM v$session
WHERE type='USER'
GROUP BY username, machine, program, status
ORDER BY 5 DESC;
```

Si sale vacío (o solo `SYS` de la propia consulta), seguir con el schema de aplicación (probablemente `CONDOR`, confirmar con `SELECT username FROM dba_users WHERE username NOT IN (...)` o `dba_segments` por tamaño) y correr `dba_tab_modifications` para un último-DML — no depende de pescar una sesión activa en el instante exacto.

### 2. `OL8LABWL01` (`192.1.2.195`) — terreno nuevo

```
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.2.195
# si rechaza:
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@192.1.2.195
ps -ef | grep -iE 'java|weblogic|forms'
sudo ss -tlnp
```

Si hay `sudo`, buscar `formsweb.cfg` (mismo árbol que Rex/GIAR/ROMAN en sus respectivos dominios) para ver si hay una sección `[heinlein]`/`[heinleinprod]` real, y los access logs de OHS/`WLS_FORMS` para buscar tráfico — mismo patrón que cerró ESYOP en la sesión anterior.

### 3. Correlación, si el paso 1 muestra algo

Si `HEINLEIN_PROD` tiene sesiones reales, repetir el `netstat -tn` en `OL8LABWL01` (paso 2) buscando la conexión hacia `10.77.7.11:1521` — mismo cierre "en vivo y en simultáneo" que funcionó para ESYOP.

## Qué cerraría esta sesión

Si el paso 1 encuentra tráfico real en `HEINLEIN_PROD`: el `status: "Solo infraestructura"` del inventario queda oficialmente en duda, con evidencia dura de producción activa — un hallazgo comparable al que tuvo GIAR (nota informal vs. campo formal), pero acá a favor de que SÍ hay uso real, no en contra. Si además el paso 2 confirma proceso Forms vivo en `OL8LABWL01`, capas 4 y 6 quedan cerradas de una — comparable al salto que tuvo ESYOP. Si en cambio `HEINLEIN_PROD` sale vacío (incluso después de `dba_tab_modifications`), es la primera señal dura de que Heinlein es genuinamente solo infraestructura de test — cierra la pregunta igual, en la otra dirección.
