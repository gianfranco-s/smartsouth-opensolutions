# Relevamiento de alta de cliente — camino punta a punta (CEFAS de referencia)

**Objetivo único de este archivo:** entender qué infraestructura necesita un cliente, capa por capa — entrada (nginx), firewall/NAT, aplicación, base de datos, y almacenamiento/procesamiento si aplica — recorriendo un cliente real de punta a punta. El resultado es una receta reusable para dar de alta un cliente nuevo, no un inventario exhaustivo. Los otros ítems de Tier 1 (Rex Argentina, EBY, ABB) siguen en `PLAN.md`, no acá — este archivo es solo el trazado punta a punta.

**Cliente de referencia: CEFAS.** Es el que más capas tiene documentadas ya hoy — WebLogic (`WebLogic.191`), DB Oracle (`CLIENTES-DB`), contenedores Docker dedicados (`VM-DOCKER-Clientes`), y encima está en medio de una migración de DB documentada en la matriz — buen caso real, no sintético.

## Bloqueadores actuales

No tenemos ninguna de estas tres credenciales todavía:

- **SSH a los servidores Linux** (WebLogic, DB, Docker hosts sin Portainer) — no hay ninguna registrada en el material fuente.
- **Portainer** (panel web de `OPENDOCKER01`/`02`/`03`, puerto `9000`).
- **Nginx Proxy Manager** (panel web de los 4 hosts Docker con NPM, puerto `81`).

El camino de abajo asume que **cuando lleguen las tres, se puede recorrer de punta a punta sin rediseñar nada** — está ordenado por capa, cada paso dice qué credencial lo desbloquea, y algunos pasos ya se pueden hacer hoy sin credenciales (marcados ✅).

## Qué se puede avanzar hoy, sin ninguna de las tres credenciales

- **Pantalla de login de `WebLogic.191` (`http://192.1.1.191:7001/console`).** No hace falta credencial para verla — mismo truco que ya funcionó con GIAR (`findings.md`): la pantalla de login sola muestra la versión de WebLogic, y a veces el nombre del dominio. No es la consola completa, pero es gratis y confirma que el servidor está vivo.
- **Firewall del paso 3, acotado a uno solo por adyacencia de IP.** `FWOPEN` tiene `192.1.1.11` en el mismo `/24` que `WebLogic.191` (`.191`), `CLIENTES-DB` (`.32`) y `VM-DOCKER-Clientes` (`.38`). `FW`, la otra opción, solo tiene `192.1.3.1` — un segmento completamente distinto. No reemplaza confirmarlo en el dashboard, pero baja el candidato de dos a uno antes de necesitar la credencial de pfSense.
- **Probar el puerto de Portainer (`:9000`) en `VM-DOCKER-Clientes` igual, aunque no esté "confirmado".** Aunque no tengamos la credencial, con solo intentar la URL se sabe si el servicio responde o no — sube `docker_detail.portainer_status` de "Relevado" a "confirmado presente, sin acceso" sin gastar nada.
- **Un tercer lugar con rastro de CEFAS que no estaba en el plan: `NUBE-OPEN-DOCKER` (`192.1.1.33`).** El relevamiento de Docker lista un contenedor `CEFAS` ahí también, y un path de persistencia `/opt/cefaslink` — un volumen llamado literalmente "cefaslink", posible integración con el producto Condor Link. Mismo bloqueo que el resto (SSH/Portainer sin confirmar), pero vale la pena tenerlo anotado como tercer host a mirar, no solo los dos `VM-DOCKER-Clientes`.
- **La credencial de pfSense no está confirmada como bloqueada.** A diferencia de SSH/Portainer/NPM, no sabemos si la tenemos o no — vale la pena simplemente probar entrar al dashboard de `FWOPEN` antes de asumir que hace falta pedirla.

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
| 3 | **Firewall / NAT** | El segmento `192.1.1.x` está probablemente detrás de `FWOPEN` (`192.1.1.11`, mismo `/24` que los tres servidores de CEFAS) — `FW` es mucho menos probable, su única IP en `192.1.x` es `192.1.3.1`, otro segmento. Acotado a un candidato por adyacencia de IP, sin confirmar todavía en el dashboard. | ⚠️ Credencial pfSense no confirmada — a verificar antes de asumir que está bloqueada como las otras tres. | En `FWOPEN`: Firewall → NAT → Port Forward, buscar la regla que apunta al IP:puerto del paso 2. |
| 4a | **App — motor clásico** | `WebLogic.191` (`192.1.1.191`, Oracle Linux 6, WL 11 según Relevamiento). La matriz dice "BD y WL migrados" pero con SID todavía sin cerrar (`CEFAS` vs `CEFASPDB` vs `prodcefas`, ver capa 5). | ✅ **hacer ya** — pantalla de login del admin console alcanzable sin credencial (mismo patrón que GIAR — ver `findings.md`), confirma versión/dominio. 🔒 consola completa: la cuenta compartida `soportesmart` ya fue rechazada una vez para GIAR, no reintentar a ciegas. | Ya: `http://192.1.1.191:7001/console`, anotar lo que muestre la pantalla de login. Con credencial: Data Sources → leer la URL JDBC del datasource de CEFAS — dice a cuál DB apunta hoy en producción, la vieja (`CLIENTES-DB`) o la nueva (`10.77.7.11`/`prodcefas`). |
| 4b | **App — capa Docker** | `VM-DOCKER-Clientes` (frontend, backend, `PostgreSQL` propio, `MariaDB`) y, recién encontrado, también `NUBE-OPEN-DOCKER` (`192.1.1.33`) — corre un contenedor `CEFAS` y un volumen `/opt/cefaslink`, posible integración con Condor Link. Portainer no confirmado en ninguno de los dos — ✅ vale la pena probar `:9000` en ambos igual, aunque no esté "confirmado", solo para ver si el puerto responde. | 🔒 SSH (o Portainer si resulta estar ahí) | `docker ps` / inspeccionar env vars de los contenedores CEFAS en los dos hosts — qué DB usan realmente (¿el Postgres propio, o hablan también con el Oracle de la capa 4a?), y qué es `cefaslink`. Esto es lo que valida o descarta la hipótesis de arriba. |
| 5 | **Base de datos** | `CLIENTES-DB` (`192.1.1.32`, Oracle, CentOS 7) — SID actual en disputa (`CEFAS` vs `CEFASPDB`, ver Discrepancias en `findings.md`). Migración en curso hacia `10.77.7.11` / SID `prodcefas`, según la matriz. | 🔒 SSH + acceso Oracle | `cat /etc/oratab`, `sqlplus / as sysdba` → `SELECT name FROM v$database;` en la instancia que haya salido del datasource (paso 4a). Cierra la `validacion_pendiente` que la propia matriz deja abierta para CEFAS. |
| 6 | **Almacenamiento / object store** | `VM-DOCKER-Clientes` monta un recurso NFS externo cuyo servidor nunca se identificó (`findings.md` → blind spot pendiente desde hace varias sesiones). La nota de migración de CEFAS menciona "revisar FSAL" — posible mismo hilo, sin confirmar. | 🔒 SSH | `mount` / `cat /etc/fstab` en `VM-DOCKER-Clientes`. Si el NFS resuelve acá, de paso cierra el blind spot que lleva abierto desde el primer relevamiento de Docker. |

## Al terminar

1. Completar `clients[].database.resolved` / `matrix_detail.validacion_pendiente` de CEFAS en `infra/inventory.json` con el SID y servidor real confirmados.
2. Agregar el bloque de proxy hosts/NAT descubierto (dominio → NPM → firewall → destino) — puede vivir en `docker_detail` de `VM-DOCKER-Clientes` o en un bloque nuevo, ver qué encaja mejor una vez que haya datos reales.
3. Si se confirma el servidor NFS, sacarlo de `blind_spots` en `inventory.json` y mover la entrada a "Resueltos" en `findings.md`.
4. **El paso que de verdad importa para el objetivo de este archivo:** una vez recorridas las 6 capas para CEFAS, escribir acá abajo la receta generalizada — qué recurso hay que crear en cada capa para dar de alta un cliente nuevo — validada contra un caso real en vez de inferida de la documentación.

## Receta generalizada (completar después de recorrer CEFAS)

*(Vacío a propósito — se llena con lo que confirme el trazado de arriba, no antes.)*
