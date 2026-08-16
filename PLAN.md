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

## Próximos pasos

**Contexto clave: probablemente tengamos una sola reunión con el equipo saliente.** Todo lo que se pueda resolver entrando a un host por TeamViewer nosotros mismos va acá, no en QUESTIONS.md — esa lista queda reservada para lo que solo ellos pueden responder (decisiones de negocio, contactos, accesos). Ver `infra/findings.md` para el detalle completo de cada punto.

### A resolver nosotros mismos, por TeamViewer (no requiere al equipo saliente)

1. **Verificar cada ítem de la hoja "Discrepancias" de la matriz conectándonos directamente** en vez de esperar una respuesta — detalle paso a paso abajo.
2. **Resolver la identidad de la VM de base de datos de Rex Argentina** buscando un schema/SID "REX" en los servidores de base de datos accesibles.
3. **Resolver si `OPENDBPROD006` es realmente la base de EBY** — conectarse y comparar el SID contra lo esperado (`MBA` actual / `EBYPROD` destino, según la matriz).
4. **Identificar el/los servidor(es) NFS** que montan `OPENDOCKER.57` y `VM-DOCKER-Clientes` — correr `mount` o revisar `/etc/fstab` en esos dos hosts.
5. **Clasificar las ~31 VMs con patrón WL/DB sin mapear** — para cada una, determinar: componente de un cliente conocido, copia de no-producción, o cliente genuinamente sin documentar (así se encontró Argocean, así que puede haber más).
6. **Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`)** — sin ninguna señal en el nombre, hay que entrar a mirar.
7. **Confirmar pfsense en los últimos 2 candidatos (`OPENFWCLI02`, `VM_FW`)** — el relevamiento de firewalls que se sumó ya confirmó los otros 7 de 9.
8. **Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`** — la conjetura anterior de que eran nginx resultó incorrecta; rol real todavía desconocido. De paso, confirmar si `portalDM` es un alias de `OPENPORTAL01` (mismo IP).
9. **Construir el mapa dominio → host proxy → servidor/puerto interno nosotros mismos**, a partir de las 4 instancias confirmadas de Nginx Proxy Manager y las reglas NAT de `pfsense` — decidido no preguntarle al equipo saliente si ya tienen uno armado, lo hacemos entrando a cada instancia.
10. **Investigar nosotros mismos si el segundo host ESXi (`192.1.3.252`) es un sitio separado** (ruteo, IPs públicas asociadas) — decidido no preguntarlo en la reunión.
11. **Revisar los jobs de backup de `VEEAM-PIEDRAS`** (repositorios, destinos de replicación) para ver si confirman un sitio adicional real detrás del nombre "Piedras", antes de preguntarlo en la reunión.
12. **Reintentar el acceso a `192.168.100.1`** (el dashboard "Open - Piedras" que no respondió en el relevamiento de firewalls) desde dentro de la red, por si el problema fue de ruteo/alcance y no que el host esté caído.

### Detalle paso a paso — ítem 1 (Discrepancias)

El chequeo más rápido y confiable para casi todos estos es leer la URL de conexión del datasource JDBC en la consola de WebLogic — ahí figura literalmente a qué IP/SID/servicio se está conectando la aplicación en producción, sin ambigüedad. La versión de WebLogic y el charset de Oracle requieren conectarse directo a cada servidor.

**GIAR — versión real de WebLogic: ✅ resuelto, `12.2.1.4.0` (ver `infra/findings.md`).** Confirmado desde la pantalla de login en `http://10.77.7.201:7001/console/login/LoginForm.jsp`, sin necesidad de entrar a la consola. Pendiente: la cuenta compartida (`soportesmart`) fue rechazada al intentar loguearse — probar usuario `weblogic` con la misma contraseña antes de dar por perdido el acceso a la consola en sí (haría falta para confirmar deployments, no solo versión).

**ROMAN — versión real de WebLogic (¿11 o 10?).** Conectarse a `WL-CLIENTES` (`172.18.5.40`, ojo que está en el host ESXi `192.1.3.252` — el candidato a segundo sitio). Mismo método que GIAR (consola o `weblogic.version`).

**JOBS — versión real de WebLogic (¿12 o 11?).** Conectarse a `WL12C-PROD` (`192.1.1.1`). Mismo método que GIAR.

**ABB — cuál DB es la productiva (`192.1.1.31` / `DBClientes-12C.31` vs `192.1.1.190` / `DBClientes.190`).** Camino más directo: en la consola de WebLogic de `WL12C-Desarrollo.2.54` (`192.1.2.54`), ir a Services → Data Sources, buscar el datasource de ABB, y leer su URL JDBC — ahí dice a cuál de las dos IPs apunta realmente. Como segundo chequeo, conectarse a cada una de las dos DBs y correr `SELECT sid, serial#, username, program FROM v$session WHERE username IS NOT NULL;` — la que tenga sesiones activas de la app es la productiva.

**CEFAS — SID real (¿`CEFASPDB` o `CEFAS`?).** Conectarse a `CLIENTES-DB` (`192.1.1.32`, compartida con BOCA). Correr `cat /etc/oratab` para ver qué instancias corren ahí, y por cada una `sqlplus / as sysdba` → `SELECT name FROM v$database;`. Cruzar contra el datasource JDBC en `WebLogic.191` (el WL de Cefas).

**BOCA — SID real (¿`BOCAPDB` o `BOCA`?).** Mismo servidor que CEFAS (`CLIENTES-DB`, `192.1.1.32`) — aprovechar la misma conexión. Cruzar contra el datasource JDBC en `WL12C-Desarrollo.2.54` (el WL de Boca).

**EBY — ¿el WL ya migró a `10.77.7.201` o sigue en el `192.1.2.54` compartido?** `10.77.7.201` es literalmente `OPENWLPROD01` — el mismo WL de GIAR. Entrar a la consola de WebLogic ahí y ver si hay un dominio/aplicación desplegada para EBY. Después entrar a `WL12C-Desarrollo.2.54` (`192.1.2.54`) y ver si el deployment de EBY sigue activo ahí también. El que tenga sesiones/logs recientes de usuarios de EBY es el real.

**Enerflex — ¿el charset es realmente `WE8ISO8859P15`?** Conectarse a `CLIENTES-DB2` (`192.1.1.51`, compartida con JOBS). `sqlplus / as sysdba` → `SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET';`.

**Al terminar cada uno:** actualizar `clients[].matrix_detail` en `infra/inventory.json` con el valor confirmado, y mover la fila correspondiente de la tabla de Discrepancias en `infra/findings.md` a una sección "Resueltos" con el valor real y la fecha.

### Requiere al equipo saliente

Ver [QUESTIONS.md](QUESTIONS.md) — el acceso a cuentas reales de vCenter, el proceso de alta de clientes, y el estado de baja de ABB/GIAR son las prioridades altas para la única reunión que probablemente tengamos. Las preguntas sobre cloud (VM Core de Azure, AWS) quedaron estacionadas en `cloud-infra/questions-cloud.md`, fuera del alcance actual.
