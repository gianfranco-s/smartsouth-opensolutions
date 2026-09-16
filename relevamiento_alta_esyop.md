# Relevamiento de alta de cliente — camino punta a punta (ESYOP de referencia)

> ✅ **6/7 capas cerradas (14 sep 2026), en una sola sesión.** Sesión de usuario real capturada en vivo (`config=esyop`, puesto `PC-GUIDO`) en simultáneo con la conexión a la DB (`netstat` en vivo, `192.1.1.31:1521 ESTABLISHED`) — la mejor evidencia del proyecto hasta ahora. Detalle en "Cierre (14 sep 2026)" al final. Único cabo suelto: capa 5 (Jasper), baja prioridad.

**Objetivo:** el mismo que [`relevamiento_alta_cefas.md`](relevamiento_alta_cefas.md), [`relevamiento_alta_jobs.md`](relevamiento_alta_jobs.md), [`relevamiento_alta_eby.md`](relevamiento_alta_eby.md), [`relevamiento_alta_boca.md`](relevamiento_alta_boca.md), [`relevamiento_alta_abb.md`](relevamiento_alta_abb.md), [`relevamiento_alta_roman.md`](relevamiento_alta_roman.md), [`relevamiento_alta_giar.md`](relevamiento_alta_giar.md) y [`relevamiento_alta_argocean.md`](relevamiento_alta_argocean.md) — entender capa por capa qué infraestructura usa un cliente (dominio → NPM → firewall/NAT → app → DB → storage) recorriéndolo de punta a punta.

**Noveno trazado, el primero dedicado a ESYOP — hasta ahora solo había recibido un bono de rebote.** Ente Servicios y Obras Públicas (ESYOP) nunca tuvo una sesión propia: todo lo que se sabe salió de la sesión de **ABB** el 6 sep 2026, al confirmar que comparte el box de DB `192.1.1.31` (`DBClientes-12C.31`) con esa instancia. Eso le dio capa 6 a ~0.7 — pero capas 1, 2, 4, 5 y 7 siguen sin tocar. Elegido ahora porque, junto con DCVIAJES, Heinlein y Maipú, es de los clientes por debajo del 50% de completitud (`verificacion_completitud_clientes.md`), y es el que tiene más terreno ya conocido a favor: la DB está resuelta y accesible, y el firewall ya está cerrado — falta solo el salto a la capa 4.

## Por qué ESYOP ahora (impacto sobre el resto del relevamiento)

- **La capa 3 (firewall/NAT) ya está cerrada, sin sesión nueva.** Las 46 reglas de `FWOPEN` (transcriptas el 19 ago 2026) tienen una regla explícita `esyop acceso` (`WAN TCP/UDP:8906` → `192.1.1.19:8888`, `resolved_vm: WebLogic.19`) — y una segunda regla idéntica, `Weblogic TARANTO` (mismo destino exacto), que `infra/findings.md` ya identificó como un alias/nombre interno viejo de ESYOP, no un cliente aparte. Acceso directo por NAT, sin pasar por ningún NPM — mismo patrón que la exposición `:9998` que comparten ABB/BOCA.
- **La DB ya es terreno conocido y accesible.** `root@192.1.1.31` (usado para cerrar ABB) confirmó la instancia `esyop` viva, `READ WRITE`, charset `WE8ISO8859P1` (= matriz), schema de app `CONDOR` con último DML **04/09/2026** — en uso activo, contraste directo con ABB (apagado de hecho desde el 1-jul-2026) en el mismo box. No hace falta conseguir una credencial nueva para volver a esa DB si hace falta repetir la consulta.
- **Falta exactamente una pieza de terreno nuevo: `WebLogic.19` (`192.1.1.19`).** Nadie probó `soportesmart`/`root` ahí todavía. Es el único host de este trazado sin ningún acceso previo — y como está en el mismo segmento `192.1.1.x` donde `root`/`soportesmart` viene funcionando de forma consistente (a diferencia del segmento `10.77.7.x`, rechazado en ROMAN/EBY), es una apuesta razonable.
- **Cierra la duda de capa 1 de una vez.** No apareció ningún dominio `esyop.*` en ninguno de los NPM ya transcriptos (`DOCKER-DEB`, `VM-DOCKER-Clientes`) — el acceso parece ser directo por IP:puerto vía el NAT de `FWOPEN`, sin capa de proxy ni dominio amigable. Si `formsweb.cfg`/el listener de `WebLogic.19` confirman esto, capa 1 y capa 2 se cierran como "no aplica" en vez de quedar como blind spot.
- **Resto de "planos" en contexto:** de los cuatro clientes que `relevamiento_alta_abb.md` agrupó como "sin sesión propia" (DVAL, DCVIAJES, ESYOP, Argocean), Argocean ya tuvo su trazado dedicado (13-14 sep), DVAL está iniciado y bloqueado por credencial. ESYOP y DCVIAJES quedan como los dos con solo el bono de capa 6 — ESYOP tiene más camino allanado (NAT ya cerrado, DB con DML más reciente) por eso se elige primero.

## Estado de partida (14 sep 2026)

De `infra/inventory.json` → `clients[ESYOP]`, `infra/findings.md` y `verificacion_completitud_clientes.md` (ESYOP ~46%):

- **Cliente:** `Ente Servicios y Obras Públicas (ESYOP)` (code `ESYOP`). `status`: `"Pendiente de migración"`. Productos (matriz): Work `Sí`, Enterprise `Sí`, Jasper `Sí`, Discoverer `"No se"`; AFIP/Condor Link/Self Service/MicroStrategy en blanco. `version_condor: 2024`. Sin `observaciones` en la matriz.
- **WebLogic (capa 4, sin tocar):** `WebLogic.19` — IP `192.1.1.19`, Oracle Linux 6, `esxi_host: 192.1.1.223` (uno de los 7 hosts del cluster ya marcados con sobreasignación de RAM, ver `informe_capacidad_esxi.md` — dato de contexto, no bloqueante), uptime 198 días, `resolved_by: name`, `match: true`. `wl_version` reclamada: `11` (infra) / `"WL 11"` (funcional) — coinciden entre sí, a diferencia de ROMAN/JOBS/GIAR (que decían 10-11 y resultaron ser 12 reales); vale la pena confirmar igual, ya que el patrón del proyecto viene siendo "el dato técnico se queda corto".
- **Base de datos (capa 6, ~0.7):** `DBClientes-12C.31` (`192.1.1.31`), compartida con ABB. `resolved_by: teamviewer`, `match: true`, `sid_confirmed: ESYOP`, `app_schema: CONDOR`, `charset_confirmed: WE8ISO8859P1`. Confirmada en vivo el 6 sep 2026 como bono del trazado de ABB — instancia `esyop` (`ora_pmon_esyop`) viva, `READ WRITE`, último DML del schema `CONDOR` **04/09/2026**. Sin sesión de aplicación capturada desde `WebLogic.19` (la consulta fue un sábado) — por eso no llega a 1.0.
- **Matriz (`matrix_detail`):** `sid_actual: ESYOP`, `version_db: 12.2.0.1.0`, `edicion_db: SE`, `tamaño: 23G`, `charset: WE8ISO8859P1`, `host_fisico_db: 192.1.1.218`, `servidor_db_destino: "BD 10.77.7.14"`, `ip_db_destino: 10.77.7.14`, `sid_nuevo: PRODESYOP`. `validacion_pendiente`: *"Confirmar destino WL y alcance de migración"* — pregunta de negocio/estado, no un dato técnico en disputa.
- **Firewall/NAT — cerrada sin sesión nueva:** `FWOPEN`, dos reglas idénticas (`esyop acceso` y `Weblogic TARANTO`), ambas `WAN TCP/UDP:8906` → `192.1.1.19:8888`, `source: *`. Puerto de destino `8888`, no el `9001`/`7001` habitual de otros WL del parque — vale la pena confirmar qué escucha ahí exactamente (¿un puerto HTTP de Forms no estándar, o un proxy interno?).
- **Cuenta:** `admin_user: soportesmart` en el registro del cliente (heredado del patrón general, sin confirmar específicamente contra `192.1.1.19`). Sin ningún intento de acceso a ese host todavía.
- **Capa 1/2 (dominio/NPM):** sin dato — ningún dominio `esyop.*`/`taranto.*` apareció en los dumps ya transcriptos de `DOCKER-DEB` ni `VM-DOCKER-Clientes`. El acceso conocido es directo por NAT (`FWOPEN:8906`), no por proxy.
- **Capa 5 (Jasper):** matriz marca `Jasper: Sí`, pero `relevamiento_docker.txt` no menciona `esyop` en ningún host Docker — instancias de Jasper genéricas sin cliente asignado en el texto, sin confirmar cuál (si alguna) es la de ESYOP.

## El camino, capa por capa

| # | Capa | Estado (14 sep 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | ✅ **No aplica (confirmado).** Acceso directo por IP pública:puerto vía NAT de `FWOPEN`, sin dominio de por medio — el access log de OHS no muestra ningún `Host` de dominio, solo la IP de origen del cliente pegándole directo al puerto expuesto. | Ninguno. |
| 2 | Nginx Proxy Manager | ✅ **No aplica (confirmado)**, mismo motivo que capa 1. | Ninguno. |
| 3 | Firewall / NAT | ✅ **Cerrada.** `FWOPEN` — `esyop acceso`/`Weblogic TARANTO` (regla duplicada, mismo alias interno), `WAN TCP/UDP:8906` → `192.1.1.19:8888`, `source: *`. | Ninguno bloqueante. |
| 4 | App — motor clásico | ✅ **Cerrada con la mejor evidencia del proyecto — sesión de usuario real capturada en vivo (14 sep 2026).** SSH a `WebLogic.19` con `soportesmart` confirmó Forms & Reports 11.1.1 real (`ClassicDomain`, `WLS_FORMS`/`WLS_REPORTS` arriba desde feb-2026). El access log activo de OHS mostró `GET /forms/frmservlet?config=esyop` seguido de heartbeats `POST /forms/lservlet` cada ~2 min, origen `ifhost=PC-GUIDO`/`ifip=192.168.2.84` (puesto de trabajo real del cliente) — **4.439 hits de `lservlet` en el día**, no ruido de bots. `formsweb.cfg` real tiene sección `[esyop]` dedicada: `pageTitle=Condor Work ES&OP`, `userid=@esyop`, `form=/app/esyop/cdr2/menues/cdr2w.fmx`. | Ninguno — capa cerrada. |
| 5 | App — Docker/reportes | ⬜ **Sin trazar.** Matriz dice `Jasper: Sí`, pero `formsweb.cfg` no tiene ninguna referencia a Jasper (esperable — suele vivir en un servicio aparte). Sin contenedor identificado como propio de ESYOP en `relevamiento_docker.txt`. | Baja prioridad. Si se retoma: revisar los hosts Docker con "múltiples instancias de JasperReports" ya listados (`relevamiento_docker.txt`) buscando config/contenedor con nombre `esyop`. |
| 6 | Base de datos | ✅ **Cerrada a 1.0 — conexión capturada en vivo, en simultáneo con la sesión de usuario real.** `netstat -tn` en `WebLogic.19`, mientras la sesión de capa 4 seguía activa: `192.1.1.19:25918 → 192.1.1.31:1521 ESTABLISHED`. Confirma sin ambigüedad que el Forms real conecta a la instancia `esyop` ya identificada — no solo DML reciente, conexión activa observada en el instante. | Ninguno — capa cerrada. |
| 7 | Almacenamiento | ✅ **No aplica (confirmado).** `/etc/fstab` en `WebLogic.19` tiene un único montaje NFS, **comentado** (`#192.1.1.252:/cdr2/wrk → /var/www/html/selfservicebackend/report`); `mount` no muestra ningún NFS activo. Solo storage local. | Ninguno. |

**Resultado: 6 de 7 capas cerradas en una sola sesión** (1/2/7 como "no aplica" confirmado, 3/4/6 con evidencia directa en vivo). Queda solo capa 5 (Jasper), de bajo costo y baja prioridad — mismo criterio de cierre que se usó para GIAR.

## Orden de la sesión sugerido

Ordenado por costo marginal — primero lo que resuelve más de una capa a la vez.

### 1. `WebLogic.19` (`192.1.1.19`) — terreno nuevo, prioridad alta

```
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.1.19
# si rechaza:
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@192.1.1.19
ps -ef | grep -iE 'java|weblogic|forms'
sudo ss -tlnp | grep -E ':8888|:8906'
```

Si hay `sudo`, buscar `formsweb.cfg` (mismo patrón que EBY/ROMAN/GIAR en `OPENWLPROD01`) y access logs de `WLS_FORMS`/OHS para confirmar tráfico real, no solo proceso vivo.

### 2. `192.1.1.31` (`DBClientes-12C.31`) — ya accesible, sin credencial nueva

```
sqlplus / as sysdba   # via root@192.1.1.31, ORACLE_SID=esyop
SELECT username, machine, program, status, COUNT(*)
FROM v$session
GROUP BY username, machine, program, status
ORDER BY 5 DESC;
```

Buscar específicamente `machine` que matchee `192.1.1.19` (o su hostname). Si no aparece nada, repetir `dba_tab_modifications` del schema `CONDOR` para un DML más reciente que el ya conocido (04/09/2026) — no depende de pescar una sesión en el instante exacto.

### 3. Docker — capa 5, si hay tiempo

Repasar los hosts Docker con "múltiples instancias de JasperReports" ya listados en `relevamiento_docker.txt` (`OPENDOCKER01`/similares) buscando un contenedor o config con nombre `esyop`/`taranto`.

## Qué cerraría esta sesión

Si el paso 1 encuentra un proceso Forms vivo en `WebLogic.19` con `sudo`: capa 4 pasa a verificada, capa 1/2 se cierran como "no aplica" (acceso directo, sin proxy), y el paso 2 permite correlacionar con una sesión real en la DB — capa 6 sube a 1.0. Eso deja a ESYOP en 5/7 capas cerradas (falta solo 5 y 7, ambas de bajo costo), un salto comparable al que tuvo BOCA en su primera sesión formal.

## Cierre (14 sep 2026) — mejor resultado que el esperado, 6/7 en una sola sesión

El paso 1 salió mejor de lo previsto: no hizo falta correlacionar nada a mano, apareció una **sesión de usuario real en curso en el momento exacto de la consulta** — `GET /forms/frmservlet?config=esyop` desde `ifhost=PC-GUIDO`/`ifip=192.168.2.84`, con heartbeats sostenidos (4.439 `lservlet` en el día) y `formsweb.cfg` con sección `[esyop]` real (`pageTitle=Condor Work ES&OP`). El paso 2 se resolvió sin necesitar `sqlplus`: un `netstat -tn` en `WebLogic.19`, corrido mientras la sesión seguía viva, capturó la conexión `192.1.1.19:25918 → 192.1.1.31:1521 ESTABLISHED` — la DB real, en el instante, sin ambigüedad. `/etc/fstab` cerró capa 7 como "no aplica" (único NFS comentado, sin montar). El paso 3 (Jasper) dio negativo — sin referencia en `formsweb.cfg` — y queda pendiente de baja prioridad, no bloqueante.

**Estado final: 6 de 7 capas cerradas**, con la particularidad de que las capas 4 y 6 no quedaron solo "confirmadas" sino capturadas **en vivo y en simultáneo** — la evidencia más fuerte de uso real que dio el proyecto hasta ahora, sin necesitar repetir la consulta un día hábil (como sí hizo falta con ROMAN/GIAR). Único cabo suelto: identificar el contenedor Jasper de ESYOP (capa 5), de bajo costo si se retoma.
