# Transición de infraestructura — plan

## Hecho

- Parseado el export de vCenter (`ExportList.csv`): 129 VMs, 12 hosts ESXi, cruzado por nombre/IP contra los 13 clientes conocidos del CSV manual de Relevamiento.
- Construido `infra/inventory.json` como fuente de verdad estructurada: cada VM etiquetada con una categoría inferida, enlaces cliente↔servidor resueltos (con discrepancias marcadas, no corregidas en silencio).
- Quitadas las credenciales en texto plano del CSV de Relevamiento antes de versionar nada; inicializado un repo git privado, commiteado, y configurado `origin` a `git@github.com:gianfranco-s/smartsouth-opensolutions.git` (todavía sin push).
- Incorporada una segunda fuente, más completa: dos emails internos reenviados más un adjunto RAR (extraído con `unar`, guardado como texto plano/JSON bajo `source-files/extracted/`) que contiene una matriz de servicios por cliente más completa, un relevamiento de infraestructura Docker, y un análisis de arquitectura Azure.
- A partir de ese material:
  - **Confirmado** que Nginx Proxy Manager corre como contenedor en 4 de los 9 hosts Docker (resuelve la pregunta de "dónde está nginx" — no es un host dedicado).
  - **Confirmado** que `OPENVPNFW01` es el firewall pfSense (matcheado vía la IP del peer de VPN de Azure) — 1 de 9 candidatos a firewall confirmado, 8 siguen siendo conjeturas.
  - **Descubiertos** 2 clientes más que no estaban en los 13 originales (Rex Argentina, Argocean).
  - **Descubierto** que 2 de los 13 clientes originales (ABB, Arris/GIAR) ya figuran dados de baja internamente.
  - Mapeado el plano aparte de Azure/AKS donde realmente corren Condor Work/Enterprise/ProvIA, y marcado un hallazgo de seguridad real encontrado ahí (red plana, sin NSGs).
- Escritos `infra/topology.md` (diagramas Mermaid generados), `infra/findings.md` (vacíos priorizados), `CLAUDE.md` (orientación técnica/para agentes), y `README.md` (onboarding humano).
- Cruzadas todas las IPs/dominios mencionados en el material fuente contra `inventory.json` para detectar infraestructura real que no estuviera mapeada. Encontrado: una VM de Azure standalone (`10.66.66.33`, ORDS Core — no estaba ni en vSphere ni en la sección `azure`), una mención sin detalle de infraestructura en AWS, y servidor(es) NFS sin identificar detrás de dos hosts Docker. Sumado todo a `inventory.json` → `azure.core_vm` / `blind_spots` y a `infra/findings.md`.
- Re-priorizada `QUESTIONS.md` asumiendo una sola reunión con el equipo saliente: todo lo verificable por TeamViewer se movió a los próximos pasos de acá abajo; QUESTIONS.md quedó acotada a lo que solo el equipo saliente puede responder.
- **Acotado el alcance a on-premise.** Se decidió no seguir investigando activamente infraestructura en proveedores cloud (Azure/AWS) por ahora. Todo lo relacionado (sección `azure` de inventory.json, el diagrama Azure/AKS, los hallazgos y preguntas sobre la VM Core/AWS/segmentación de red) se movió a `cloud-infra/` — ver `cloud-infra/README.md` para cómo retomarlo si hace falta.
- Agregado "Piedras" como pregunta abierta: se mencionó verbalmente como sitio adicional, pero el único rastro técnico (`VEEAM-PIEDRAS`) está dentro del cluster principal, no en un sitio aparte — no coincide con lo esperado, así que queda como algo a verificar, no a dar por cierto.
- Incorporado un relevamiento manual de firewalls (`Relevamiento (sin claves) - Pfsense.csv`, agregado a `source-files/`) con acceso real a cada dashboard pfSense. **Confirmados 6 candidatos más** (`CliProFw01`, `DMFW01`, `FW`, `FWOPEN`, `OPENFWCLI001`, `OPENFWCLI10`) — quedan solo 2 sin confirmar (`OPENFWCLI02`, `VM_FW`) de los 9 originales. También confirma un hallazgo de seguridad positivo (sin puertos TCP expuestos a Internet, solo OpenVPN/UDP 2190) y aporta una segunda fuente independiente para "Piedras" (un dashboard etiquetado "Open - Piedras" en `192.168.100.1`, que no respondió durante el relevamiento).
- **Primera verificación en vivo por TeamViewer:** versión real de WebLogic de GIAR confirmada en `12.2.1.4.0` (ver `infra/findings.md`) — resuelve esa fila de la hoja Discrepancias a favor del valor técnico.

## Próximos pasos

**Objetivo activo: llegar a un mapeo completo cliente → ruta de recursos.** Hoy tenemos cliente → WebLogic → DB para los 15 clientes (`infra/topology.md` §1), pero falta la capa intermedia — dominio → proxy → firewall/NAT → servidor — que es la que de verdad permite rastrear un incidente rápido. "La app de X está caída" ya se resuelve rápido; "este dominio tira error" todavía no. Los ítems de abajo están ordenados por qué tan directamente cierran esa brecha, no por orden de descubrimiento.

**Contexto: probablemente una sola reunión con el equipo saliente.** Todo lo de acá se resuelve por TeamViewer nosotros mismos; `QUESTIONS.md` queda para lo que solo ellos pueden responder.

### Tier 1 — completa la ruta de recursos de un cliente

1. **Construir el mapa dominio → instancia Nginx Proxy Manager → servidor/puerto interno**, a partir de las 4 instancias confirmadas y las reglas NAT de `pfsense`. Esta es la pieza que realmente falta del mapeo completo.
2. **Resolver la identidad de la VM de base de datos de Rex Argentina** — cliente PROD actual, cero recursos mapeados hoy. **Actualización (19 ago 2026):** ya apareció la capa app — reglas NAT de `FWOPEN` ("SS Rex Front"/"SS Rex Back") apuntan a `192.1.1.57` (`OPENDOCKER.57`), mismo patrón "Self Service" que CEFAS. Falta la DB. **Actualización (2 sep 2026):** primeros datos de DB jamás encontrados para Rex, vía `tnsnames.ora` de `OPENWLPROD01` — dos alias candidatos, `PROD_REX`→`OPENDBPROD001` (`10.77.7.11`) y `PDBREXPROD`→`192.1.3.34` (VM sin identificar, nuevo blind spot). Además, `serzarex.condor.solutions` (NPM) → `OL8LABWL01` es candidato sin confirmar a motor clásico. Nada verificado en vivo todavía — ver `infra/findings.md` y `clients[279]` en `inventory.json`. **Actualización (6 sep 2026) — resuelto en vivo:** `v$session` sobre `PRODREX01` (`OPENDBPROD001`/`CDBOPEN03`, Container Database `CDBOPEN03`) muestra usuarios nominales reales (`MAIETA`, `CDELISE`, `MCORREA`, `JBRICEÑO`) conectados vía `frmweb`/`java` desde `ol8labwl01.localdomain` — confirma de una `OL8LABWL01` como motor clásico real y `OPENDBPROD001`/`PRODREX01` como la DB real en uso (no `PDBREXPROD`/`192.1.3.34`, que queda como candidato secundario sin tráfico visto). Bonus: segundo ambiente `QAREX01` en la misma CDB, sin tráfico visto todavía. **Ítem prácticamente cerrado** — solo falta storage/NAT dedicado si aplica.
3. **Resolver la ruta completa de EBY** — ¿`OPENDBPROD006` es realmente su base? ¿su WL ya migró a `10.77.7.201` o sigue en el `192.1.2.54` compartido? Dos discrepancias de la misma hoja, mismo cliente — detalle abajo.
4. ~~**ABB — cuál de las dos DBs es la productiva**~~ **RESUELTO (6 sep 2026)** — trazado completo, ver [`plan_relevamiento_alta_abb.md`](plan_relevamiento_alta_abb.md) y `infra/findings.md`. La DB productiva es **`192.1.1.31`** (`DBClientes-12C.31`, instancia `ABB`, schema de app `CONDOR`), confirmada por `sqlplus`/`dba_tab_modifications` — el plan de BOCA no pudo cerrarlo de rebote (`192.1.2.54` sin consola ni `sudo`), se hizo por `sqlplus` directo con `root@192.1.1.31`. `192.1.1.190` **no es DB de ABB** (solo sub‑bases históricas `abbhist`/`abbtubio`, apagadas; ese box es de DCVIAJES). Hallazgo colateral: **ABB está apagado de hecho desde el 1‑jul‑2026** (última sesión Forms y último DML ese día) — dato de apoyo para la pregunta de baja en `QUESTIONS.md`. Bonos: capa 6 de **ESYOP** verificada en vivo (co‑inquilina de `.31`, en uso activo) y de **DCVIAJES** verificada parcial (`.190`, viva y en uso).

4b. **ROMAN — trazado casi cerrado, sin usuarios reales** (iniciado 6 sep 2026, capa 1 cerrada 12/13 sep, ver [`plan_relevamiento_alta_roman.md`](plan_relevamiento_alta_roman.md)). Capas 1, 4, 6 (config), 7 resueltas: secciones `[csm]*` reales en `formsweb.cfg` de `OPENWLPROD01` (`pageTitle=CSM PRODUCCION`, `userid=@PRODCSM`), `PRODCSM`/`QACSM` → `OPENDBPROD03` (`10.77.7.30:1525`), sin NFS, WL `12.2.1.4.0` (cierra la fila de Discrepancias). **Capa 1 cerrada (12/13 sep):** `proxy-host-93`/`94` de `DOCKER-DEB` (NPM en contenedor `ssl-app-1`) — **0 requests `lservlet` en 5.097 totales**, 100% escaneo de bots. Coincide con el `access.log` de `WLS_FORMS` (0 `config=csm`) — **dos fuentes independientes confirman que ROMAN está configurado como producción de punta a punta pero sin un solo usuario real.** Falta: (a) capas 3 y 5, bajo costo, sin trazar; (b) `v$session` en `OPENDBPROD03` para el cierre 1.0 de capa 6 — **`ssh root@10.77.7.30` probado y rechazado (12 sep)**, el mismo `root` que cerró BOCA no sirve en el segmento `10.77.7.x` (tampoco en `.151`/`.15`) — ver `QUESTIONS.md`. Cabo aparte: clasificar `OPENDBDES011` (`10.77.7.151`, "Roman test" en vCenter), descartado de la ruta productiva pero sin trazar qué corre ahí.

4c. **GIAR — trazado punta a punta iniciado (12 sep 2026), ver [`plan_relevamiento_alta_giar.md`](plan_relevamiento_alta_giar.md)).** Elegido en vez de seguir con ROMAN — es el ítem 1 de la lista de prioridades de `findings.md` (¿ABB y GIAR de baja, o solo mantenimiento? ABB ya resuelto, GIAR falta). Dos stacks sin cerrar: **legado** (`WL-GIAR` `10.10.1.50` + `DB-GIAR` `10.10.1.9`, en el segundo sitio ESXi aislado `192.1.3.252`, nunca accedidos) y **nuevo** (alias `PRODGIAR`/`QAGIAR` en el `tnsnames.ora` de `OPENWLPROD01` → `OPENDBPROD001`/`10.77.7.11`; `PRODGIAR` existe como PDB `READ WRITE` pero solo se vieron sesiones `SYS` el 6-sep, sin `dba_tab_modifications` corrido todavía). **Hallazgo nuevo sin explotar:** `giarprod.condorenterprise.com.ar` (NPM `DOCKER-DEB`, habilitado) reenvía a `200.55.243.117:80` — IP pública que no es de `FWOPEN` ni de una VM app, es de la propia VM `FW` (`192.1.3.1`, pfSense confirmado del segmento aislado, nunca se entró a su dashboard). Revisar el NAT de `FW` es el paso que probablemente cierra de un tiro capas 3 y 4. Detalle completo y orden de sesión sugerido en el plan.

### Tier 2 — extiende el mapa, atrapa desconocidos

5. **Clasificar las 32 VMs con patrón WL/DB sin mapear** (24 encendidas, 8 apagadas — arrancar por las encendidas) — componente de un cliente conocido, copia de no-producción, o cliente genuinamente sin documentar (así se encontró Argocean).
6. **Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`** — la conjetura de que eran nginx resultó incorrecta; podrían ser parte de la ruta real de algún cliente. De paso, confirmar si `portalDM` es un alias de `OPENPORTAL01`.
7. **Identificar el/los servidor(es) NFS** que montan `OPENDOCKER.57` y `VM-DOCKER-Clientes` — `mount` / `/etc/fstab`.
8. **Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`)**.

### Tier 3 — pausado, baja urgencia (no bloquea el mapeo de rutas)

- Charset en Enerflex — dato de higiene de la hoja Discrepancias, no bloquea nada operativo. (Versión de WebLogic en ROMAN/JOBS y SID en CEFAS/BOCA ya resueltos — ver `infra/findings.md`.) Detalle de método abajo.
- Últimos 2 candidatos a firewall (`OPENFWCLI02`, `VM_FW`).
- Si el segundo host ESXi (`192.1.3.252`) es un sitio separado.
- Piedras: revisar jobs de backup de `VEEAM-PIEDRAS`, reintentar `192.168.100.1`.

### Detalle paso a paso — Tier 1, ítem 3 (EBY)

**DB:** comparar el SID de `OPENDBPROD006` contra lo esperado (`MBA` actual / `EBYPROD` destino, según la matriz).

**WL:** `10.77.7.201` es literalmente `OPENWLPROD01` — el mismo WL de GIAR. Entrar a la consola ahí y ver si hay un dominio/aplicación desplegada para EBY. Después entrar a `WL12C-Desarrollo.2.54` (`192.1.2.54`) y ver si el deployment de EBY sigue activo ahí también. El que tenga sesiones/logs recientes de usuarios de EBY es el real.

**Actualización (19 ago 2026):** el panel NPM de `DOCKER-DEB` (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`) muestra que en realidad hay **tres** endpoints con dominio real para EBY, no dos: `eby-prod.condorwork.com.ar`/`eby-qa.condorwork.com.ar` → `10.77.7.201:9001`, `ebyprod.open.com.ar` → `10.77.8.201:9001`, y `yacyreta.condorwork.com.ar` → `192.1.1.191:80` (`WebLogic.191`, la VM que se pensaba dedicada a CEFAS). Ninguno de los dos candidatos originales de la hoja Discrepancias queda descartado por esto — hace falta revisar cuál de los tres tiene tráfico/sesiones reales antes de cerrar el ítem. Detalle completo en `infra/findings.md`.

**Actualización (2 sep 2026) — trazado punta a punta en curso, ver [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md).** EBY se tomó como el próximo cliente a relevar por impacto (destraba ~9 co-inquilinos de los WL compartidos que toca). Capas 1-3 (dominio/NPM/firewall) cerradas. Resultado del ítem: **son dos stacks completos en paralelo, no un WL/DB ambiguo** — `yacyreta.condorwork.com.ar` → `WebLogic.191` → `Database .90` (sin cliente asignado, candidata sin confirmar) y `eby-prod.condorwork.com.ar` → `OPENWLPROD01` → `OPENDBPROD005`/`10.77.7.15` (destino de migración de la matriz, con archivos de ambiente `ebyprod.env`/`ebyqa.env`/`ebyaudit.env` dedicados encontrados en `OPENWLPROD01`, y 100% del tráfico Oracle real de ese box yendo ahí). **Actualización (2 sep 2026, cierre):** conseguida credencial `root` para `192.1.1.90` (confirmó `CDRADM`, DB compartida no exclusiva de EBY) y, más importante, `sudo` real en `OPENWLPROD01` permitió leer `tnsnames.ora` completo — **cierra capa 4/6 de EBY para la ruta `eby-prod`** (alias `EBYPROD`/`EBYQA`/`EBYAUDIT` → `10.77.7.15`/`OPENDBPROD005`, coincide con la matriz). **EBY queda en 6 de 7 capas.** El mismo archivo trajo alias de otros 5 clientes de un saque: **GIAR** (segunda DB candidata, `OPENDBPROD001`), **ROMAN** (primera DB real encontrada, `OPENDBPROD03`/`10.77.7.30`, confirma además la migración a `OPENWLPROD01` ya vista en el NPM), **Rex Argentina** (primera DB jamás mapeada — ver ítem 2 arriba), **Heinlein** (test confirmado) — y descartó `VINST`/`VINST2025`/`T2022` como sistemas internos, no clientes. Detalle completo en `infra/findings.md`. Falta: confirmar estado de GIAR (mismo box, ítem 1 abajo) y verificar en vivo los candidatos nuevos de ROMAN/GIAR/Rex.

**Actualización (12 sep 2026, cierre final) — ítem 3 completo, EBY 7/7.** `sqlplus` directo a `Database .90`/`CDRADM` (`root@192.1.1.90`) resolvió el único cabo suelto: de los 8 inquilinos de `WebLogic.191`, solo **`SIGO`** tiene schema propio ahí (2.6 GB, uso activo el mismo día) — ni EBY ni ningún otro. `Database .90` queda descartada como DB de EBY; la única DB real sigue siendo `OPENDBPROD005` (ruta `eby-prod`). Bono: resuelve de paso el blind spot de `SIGO`, uno de los clientes de `.191` sin VM mapeada. Detalle en `infra/findings.md` → "EBY — capa 6 cerrada del todo, 7/7". **Ítem 3 de Tier 1: cerrado.**

### Detalle paso a paso — Tier 1, ítem 4 (ABB) — ✅ RESUELTO (6 sep 2026)

El camino "leer el datasource en la consola de `192.1.2.54`" **no fue viable** — ese box no tiene consola de WebLogic ni `sudo` (se supo en la sesión de BOCA). Se resolvió por el segundo chequeo, directo a las DBs con `root@192.1.1.31` / `root@192.1.1.190`:

- **`192.1.1.31`** — instancia `ABB` viva (`ora_pmon_ABB`, non‑CDB, `READ WRITE`). Datos de la app en el schema **`CONDOR`** (~6.9 GB); `dba_tab_modifications` da último DML de `CONDOR` = **01/07/2026 17:24**, que calza exacto con la última sesión Forms del access log de `abb.condorwork.com.ar`. Charset `WE8ISO8859P1` (= matriz). → **es la DB productiva.**
- **`192.1.1.190`** — no tiene instancia `ABB` en `/etc/oratab`, solo `abbhist`/`abbtubio` (históricas, apagadas). Lo único levantado es `ora_pmon_DCVIAJES`. → **descartada; era ruido del inventario técnico.**
- **Colateral:** ABB sin una sola sesión ni DML desde el 1‑jul‑2026 — apagado de hecho (ver `QUESTIONS.md`, decisión de baja pendiente del equipo saliente).
- **Bonos:** ESYOP (co‑inquilina de `.31`, schema `CONDOR` con DML del 04/09/2026 → en uso) y DCVIAJES (`.190`, ídem) ganan verificación de capa 6.

Detalle completo en [`plan_relevamiento_alta_abb.md`](plan_relevamiento_alta_abb.md) y `infra/findings.md`.

### Detalle paso a paso — Tier 3 (si se retoma)

El chequeo más rápido y confiable para la mayoría de estos es leer la URL de conexión del datasource JDBC en la consola de WebLogic — ahí figura literalmente a qué IP/SID/servicio se está conectando la aplicación en producción. La versión de WebLogic y el charset de Oracle requieren conectarse directo a cada servidor.

**ROMAN — versión real de WebLogic (¿11 o 10?).** `WL-CLIENTES` (`172.18.5.40`, host ESXi `192.1.3.252` — el candidato a segundo sitio). Consola de administración (puerto 7001, versión visible en la pantalla de login) o `java weblogic.version` / `ps -ef | grep -i weblogic` por consola.

**JOBS — versión real de WebLogic (¿12 o 11?).** `WL12C-PROD` (`192.1.1.1`). Mismo método que ROMAN.

~~**CEFAS — SID real.**~~ **RESUELTO (25 ago 2026)** — `CEFAS`, no `CEFASPDB`. Ver `infra/findings.md`.

~~**BOCA — SID real (¿`BOCAPDB` o `BOCA`?).**~~ **RESUELTO (12 sep 2026)** — las dos eran correctas: `BOCA` es la CDB, `BOCAPDB` la PDB con los datos (schema `CONDOR`, ~22.5 GB, charset `WE8MSWIN1252`, uso activo confirmado por último DML el mismo día de la consulta). Ver `plan_relevamiento_alta_boca.md` e `infra/findings.md`.

**Enerflex — ¿el charset es realmente `WE8ISO8859P15`?** `CLIENTES-DB2` (`192.1.1.51`, compartida con JOBS). `sqlplus / as sysdba` → `SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET';`.

**Al terminar cualquiera de estos:** actualizar `clients[].matrix_detail` en `infra/inventory.json` con el valor confirmado, y mover la fila correspondiente de la tabla de Discrepancias en `infra/findings.md` a una sección "Resueltos" con el valor real y la fecha.

### Requiere al equipo saliente

Ver [QUESTIONS.md](QUESTIONS.md) — el acceso a cuentas reales de vCenter, el proceso de alta de clientes, y el estado de baja de ABB/GIAR son las prioridades altas para la única reunión que probablemente tengamos. Las preguntas sobre cloud (VM Core de Azure, AWS) quedaron estacionadas en `cloud-infra/questions-cloud.md`, fuera del alcance actual.
