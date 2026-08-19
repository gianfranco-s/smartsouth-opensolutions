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
2. **Resolver la identidad de la VM de base de datos de Rex Argentina** — cliente PROD actual, cero recursos mapeados hoy.
3. **Resolver la ruta completa de EBY** — ¿`OPENDBPROD006` es realmente su base? ¿su WL ya migró a `10.77.7.201` o sigue en el `192.1.2.54` compartido? Dos discrepancias de la misma hoja, mismo cliente — detalle abajo.
4. **ABB — cuál de las dos DBs es la productiva** (`192.1.1.31` / `DBClientes-12C.31` vs `192.1.1.190` / `DBClientes.190`) — detalle abajo.

### Tier 2 — extiende el mapa, atrapa desconocidos

5. **Clasificar las 32 VMs con patrón WL/DB sin mapear** (24 encendidas, 8 apagadas — arrancar por las encendidas) — componente de un cliente conocido, copia de no-producción, o cliente genuinamente sin documentar (así se encontró Argocean).
6. **Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`** — la conjetura de que eran nginx resultó incorrecta; podrían ser parte de la ruta real de algún cliente. De paso, confirmar si `portalDM` es un alias de `OPENPORTAL01`.
7. **Identificar el/los servidor(es) NFS** que montan `OPENDOCKER.57` y `VM-DOCKER-Clientes` — `mount` / `/etc/fstab`.
8. **Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`)**.

### Tier 3 — pausado, baja urgencia (no bloquea el mapeo de rutas)

- Versión de WebLogic en ROMAN, JOBS; SID en CEFAS, BOCA; charset en Enerflex — dato de higiene de la hoja Discrepancias, no bloquea nada operativo. Ya se abrió consola a `WL-CLIENTES` (ROMAN) en una sesión anterior; retomar desde ahí si se vuelve a priorizar. Detalle de método abajo.
- Últimos 2 candidatos a firewall (`OPENFWCLI02`, `VM_FW`).
- Si el segundo host ESXi (`192.1.3.252`) es un sitio separado.
- Piedras: revisar jobs de backup de `VEEAM-PIEDRAS`, reintentar `192.168.100.1`.

### Detalle paso a paso — Tier 1, ítem 3 (EBY)

**DB:** comparar el SID de `OPENDBPROD006` contra lo esperado (`MBA` actual / `EBYPROD` destino, según la matriz).

**WL:** `10.77.7.201` es literalmente `OPENWLPROD01` — el mismo WL de GIAR. Entrar a la consola ahí y ver si hay un dominio/aplicación desplegada para EBY. Después entrar a `WL12C-Desarrollo.2.54` (`192.1.2.54`) y ver si el deployment de EBY sigue activo ahí también. El que tenga sesiones/logs recientes de usuarios de EBY es el real.

**Actualización (19 ago 2026):** el panel NPM de `DOCKER-DEB` (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`) muestra que en realidad hay **tres** endpoints con dominio real para EBY, no dos: `eby-prod.condorwork.com.ar`/`eby-qa.condorwork.com.ar` → `10.77.7.201:9001`, `ebyprod.open.com.ar` → `10.77.8.201:9001`, y `yacyreta.condorwork.com.ar` → `192.1.1.191:80` (`WebLogic.191`, la VM que se pensaba dedicada a CEFAS). Ninguno de los dos candidatos originales de la hoja Discrepancias queda descartado por esto — hace falta revisar cuál de los tres tiene tráfico/sesiones reales antes de cerrar el ítem. Detalle completo en `infra/findings.md`.

### Detalle paso a paso — Tier 1, ítem 4 (ABB)

Camino más directo: en la consola de WebLogic de `WL12C-Desarrollo.2.54` (`192.1.2.54`), ir a Services → Data Sources, buscar el datasource de ABB, y leer su URL JDBC — ahí dice a cuál de las dos IPs apunta realmente. Como segundo chequeo, conectarse a cada una de las dos DBs y correr `SELECT sid, serial#, username, program FROM v$session WHERE username IS NOT NULL;` — la que tenga sesiones activas de la app es la productiva.

### Detalle paso a paso — Tier 3 (si se retoma)

El chequeo más rápido y confiable para la mayoría de estos es leer la URL de conexión del datasource JDBC en la consola de WebLogic — ahí figura literalmente a qué IP/SID/servicio se está conectando la aplicación en producción. La versión de WebLogic y el charset de Oracle requieren conectarse directo a cada servidor.

**ROMAN — versión real de WebLogic (¿11 o 10?).** `WL-CLIENTES` (`172.18.5.40`, host ESXi `192.1.3.252` — el candidato a segundo sitio). Consola de administración (puerto 7001, versión visible en la pantalla de login) o `java weblogic.version` / `ps -ef | grep -i weblogic` por consola.

**JOBS — versión real de WebLogic (¿12 o 11?).** `WL12C-PROD` (`192.1.1.1`). Mismo método que ROMAN.

**CEFAS — SID real (¿`CEFASPDB` o `CEFAS`?).** `CLIENTES-DB` (`192.1.1.32`, compartida con BOCA). `cat /etc/oratab` para ver qué instancias corren ahí, y por cada una `sqlplus / as sysdba` → `SELECT name FROM v$database;`. Cruzar contra el datasource JDBC en `WebLogic.191` (el WL de Cefas).

**BOCA — SID real (¿`BOCAPDB` o `BOCA`?).** Mismo servidor que CEFAS — aprovechar la misma conexión. Cruzar contra el datasource JDBC en `WL12C-Desarrollo.2.54` (el WL de Boca).

**Enerflex — ¿el charset es realmente `WE8ISO8859P15`?** `CLIENTES-DB2` (`192.1.1.51`, compartida con JOBS). `sqlplus / as sysdba` → `SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET';`.

**Al terminar cualquiera de estos:** actualizar `clients[].matrix_detail` en `infra/inventory.json` con el valor confirmado, y mover la fila correspondiente de la tabla de Discrepancias en `infra/findings.md` a una sección "Resueltos" con el valor real y la fecha.

### Requiere al equipo saliente

Ver [QUESTIONS.md](QUESTIONS.md) — el acceso a cuentas reales de vCenter, el proceso de alta de clientes, y el estado de baja de ABB/GIAR son las prioridades altas para la única reunión que probablemente tengamos. Las preguntas sobre cloud (VM Core de Azure, AWS) quedaron estacionadas en `cloud-infra/questions-cloud.md`, fuera del alcance actual.
