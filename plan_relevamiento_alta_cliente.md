# Relevamiento de alta de cliente — camino punta a punta (CEFAS de referencia)

**Objetivo único de este archivo:** entender qué infraestructura necesita un cliente, capa por capa — entrada (nginx), firewall/NAT, aplicación, base de datos, y almacenamiento/procesamiento si aplica — recorriendo un cliente real de punta a punta. El resultado es una receta reusable para dar de alta un cliente nuevo, no un inventario exhaustivo. Los otros ítems de Tier 1 (Rex Argentina, EBY, ABB) siguen en `PLAN.md`, no acá — este archivo es solo el trazado punta a punta.

**Cliente de referencia: CEFAS.** Es el que más capas tiene documentadas ya hoy — WebLogic (`WebLogic.191`), DB Oracle (`CLIENTES-DB`), contenedores Docker dedicados (`VM-DOCKER-Clientes`), y encima está en medio de una migración de DB documentada en la matriz — buen caso real, no sintético.

## Bloqueadores actuales

- **SSH a los servidores Linux** (WebLogic, DB, Docker hosts sin Portainer) — no hay ninguna registrada en el material fuente.
- **Portainer** (panel web de `OPENDOCKER01`/`02`/`03`, puerto `9000`).
- **Nginx Proxy Manager** (panel web de los 4 hosts Docker con NPM, puerto `81`).
- ~~pfSense~~ — **desbloqueado (18 ago 2026):** acceso confirmado al dashboard de `FWOPEN` (`192.1.1.11`). Ya no es un bloqueador — ver paso 3 de la tabla.

El camino de abajo asume que **cuando lleguen las tres, se puede recorrer de punta a punta sin rediseñar nada** — está ordenado por capa, cada paso dice qué credencial lo desbloquea, y algunos pasos ya se pueden hacer hoy sin credenciales (marcados ✅).

## Qué se puede avanzar hoy, sin SSH/Portainer/NPM

- **`FWOPEN` (`192.1.1.11`) — confirmado, credenciales existen (18 ago 2026).** Ya podés entrar ahora mismo a Firewall → NAT → Port Forward y buscar cualquier regla que apunte a `192.1.1.191` (WebLogic) o `192.1.1.38` (Docker/NPM de CEFAS) — es el paso 3 de la tabla, ya desbloqueado.
- **Pantalla de login de `WebLogic.191` (`http://192.1.1.191:7001/console`) — probado, connection refused (18 ago 2026).** A diferencia de GIAR (mismo truco, puerto abierto), acá el puerto no respondió. No confirma que WebLogic esté caído — puede ser que el firewall no deje pasar ese puerto desde donde estás parado, que el proceso esté detenido, o que escuche en otro puerto tras la migración ("BD y WL migrados" según la matriz, pero no dice a qué IP se movió el WL). Vale la pena, ahora que hay acceso a `FWOPEN`, revisar ahí si hay una regla NAT para el `7001` de esa IP — si no hay ninguna, explica el refused sin necesitar tocar la VM.
- **Probar el puerto de Portainer (`:9000`) en `VM-DOCKER-Clientes` (`192.1.1.38`) igual, aunque no esté "confirmado".** Sin necesitar login, saber si responde ya sube `docker_detail.portainer_status` de "Relevado" a "confirmado presente, sin acceso".
- **`NUBE-OPEN-DOCKER` (`192.1.1.33`) — probado, Nextcloud responde pero rechaza por "dominio no de confianza" (18 ago 2026).** Es la protección de `trusted_domains` propia de Nextcloud (accedés por IP en vez del hostname que espera) — no es un bloqueador nuestro, y de todas formas Nextcloud no es lo que buscamos ahí. Sí confirma que el host está vivo y responde en la red. Para lo que importa (el contenedor `CEFAS` y el volumen `/opt/cefaslink`) sigue haciendo falta Portainer o SSH — probar `:9000` ahí también.

## Hipótesis a validar: ¿dos tecnologías, una en el host y otra en Docker?

Parece que sí, pero como dos **capas que coexisten para el mismo cliente**, no como dos alternativas excluyentes:

- **Motor clásico (WebLogic + Oracle DB, instalado directo en la VM, sin Docker).** Los 15 clientes tienen un par WL+DB en `inventory.json`, incluidos los que solo usan el producto "Work" (CEFAS, ABB, Enerflex, EBY, JOBS) — no es exclusivo de "Enterprise". Hipótesis: es el motor de datos/negocio central de Condor, universal.
- **Capa Docker (portal web ± Postgres propio).** Solo aparece para clientes con el producto "Work". La mayoría comparte un portal multi-tenant (`OPENDOCKER02`, "Portal Work en producción"), pero CEFAS tiene contenedores **dedicados** (`VM-DOCKER-Clientes`: frontend, backend, y un **PostgreSQL propio**, separado de su Oracle DB). No sabemos todavía si ese Postgres reemplaza datos que antes vivían en Oracle, o si son cosas distintas que conviven.

**No tenemos suficiente info para confirmarlo del todo** — es la pregunta que este trazado debería contestar en la práctica (paso 3b de abajo), no algo para asumir.

## El camino, capa por capa

| # | Capa | Qué ya sabemos | Bloqueo | Paso una vez desbloqueado |
|---|---|---|---|---|
| 1 | **Dominio de entrada** | No lo tenemos anotado en ningún lado todavía. | NPM | Ver paso 2 — el dominio sale de ahí mismo. |
| 2 | **Nginx Proxy Manager** | `VM-DOCKER-Clientes` (`192.1.1.38:81`) y su gemela (`VM-DOCKER-Clientes (1)`, accesible en `172.18.5.123`/`10.10.1.43`/`192.1.3.4`) sirven CEFAS. El panel de login ya respondió sin credencial (confirmado en vivo desde Piedras, 18 ago 2026). | 🔒 NPM | Entrar, filtrar Proxy Hosts por "cefas", anotar dominio público → IP:puerto interno. |
| 3 | **Firewall / NAT** | `FWOPEN` (`192.1.1.11`, mismo `/24` que los tres servidores de CEFAS). | ✅ **desbloqueado (18 ago 2026)** — credenciales confirmadas, acceso real al dashboard. | Firewall → NAT → Port Forward, buscar reglas para `192.1.1.191:7001` (WebLogic) y `192.1.1.38` (Docker/NPM) — la ausencia de una regla para el `7001` explicaría el connection refused de la fila 4a. |
| 4a | **App — motor clásico** | `WebLogic.191` (`192.1.1.191`, Oracle Linux 6, WL 11 según Relevamiento). La matriz dice "BD y WL migrados" pero con SID todavía sin cerrar (`CEFAS` vs `CEFASPDB` vs `prodcefas`, ver capa 5) — y ahora no sabemos ni la IP: el WL pudo migrar de servidor igual que la DB (ver fila 5). | 🔴 **Probado (18 ago 2026): connection refused** en `192.1.1.191:7001` — a diferencia de GIAR, acá no respondió ni la pantalla de login. Sin diagnóstico todavía: puede ser el firewall (ver fila 3), el proceso caído, o que WL se movió de IP en la migración. 🔒 consola completa (si el puerto llegara a responder): la cuenta compartida `soportesmart` ya fue rechazada una vez para GIAR, no reintentar a ciegas. | Revisar la regla NAT en `FWOPEN` primero (fila 3) antes de asumir que el WL está caído. Si hay regla y sigue sin responder, ahí sí es la VM. Con credencial de consola: Data Sources → URL JDBC — dice a cuál DB apunta hoy. |
| 4b | **App — capa Docker** | `VM-DOCKER-Clientes` (`192.1.1.38`, frontend/backend/`PostgreSQL` propio/`MariaDB`) y `NUBE-OPEN-DOCKER` (`192.1.1.33` — contenedor `CEFAS` + volumen `/opt/cefaslink`, probado en vivo: responde pero Nextcloud rechaza por dominio no confiable, no es bloqueo real). Portainer no confirmado en ninguno de los dos. | 🔒 SSH (o Portainer si resulta estar ahí — probar `:9000` en los dos) | `docker ps` / inspeccionar env vars de los contenedores CEFAS en los dos hosts — qué DB usan realmente (¿el Postgres propio, o hablan también con el Oracle de la capa 4a?), y qué es `cefaslink`. Esto es lo que valida o descarta la hipótesis de arriba. |
| 5 | **Base de datos** | `CLIENTES-DB` (`192.1.1.32`, Oracle, CentOS 7) — SID actual en disputa (`CEFAS` vs `CEFASPDB`). **Destino de migración identificado (18 ago 2026): `OPENDBPROD001` (`10.77.7.11`)** — resuelto por coincidencia exacta de IP contra `matrix_detail.ip_db_destino`, ya compartida con Heinlein (mismo patrón de instancia multi-cliente que otros DBs del proyecto). Falta confirmar el SID (`prodcefas` según la matriz) y si ya es la productiva. | 🔒 SSH + acceso Oracle | `cat /etc/oratab`, `sqlplus / as sysdba` → `SELECT name FROM v$database;` en **`OPENDBPROD001`**, no en `CLIENTES-DB` — es el candidato fuerte ahora. Cruzar contra el datasource de la fila 4a cuando se pueda. Cierra la `validacion_pendiente` que la matriz deja abierta para CEFAS. |
| 6 | **Almacenamiento / object store** | `VM-DOCKER-Clientes` monta un recurso NFS externo cuyo servidor nunca se identificó (`findings.md` → blind spot pendiente desde hace varias sesiones). La nota de migración de CEFAS menciona "revisar FSAL" — posible mismo hilo, sin confirmar. | 🔒 SSH | `mount` / `cat /etc/fstab` en `VM-DOCKER-Clientes`. Si el NFS resuelve acá, de paso cierra el blind spot que lleva abierto desde el primer relevamiento de Docker. |

## Al terminar

1. Completar `clients[].database.resolved` / `matrix_detail.validacion_pendiente` de CEFAS en `infra/inventory.json` con el SID y servidor real confirmados.
2. Agregar el bloque de proxy hosts/NAT descubierto (dominio → NPM → firewall → destino) — puede vivir en `docker_detail` de `VM-DOCKER-Clientes` o en un bloque nuevo, ver qué encaja mejor una vez que haya datos reales.
3. Si se confirma el servidor NFS, sacarlo de `blind_spots` en `inventory.json` y mover la entrada a "Resueltos" en `findings.md`.
4. **El paso que de verdad importa para el objetivo de este archivo:** una vez recorridas las 6 capas para CEFAS, escribir acá abajo la receta generalizada — qué recurso hay que crear en cada capa para dar de alta un cliente nuevo — validada contra un caso real en vez de inferida de la documentación.

## Receta generalizada (completar después de recorrer CEFAS)

*(Vacío a propósito — se llena con lo que confirme el trazado de arriba, no antes.)*
