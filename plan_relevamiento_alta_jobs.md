# Relevamiento de alta de cliente — camino punta a punta (JOBS de referencia)

**Objetivo:** el mismo que [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md) — entender capa por capa qué necesita un cliente (nginx → firewall → app → DB → storage), pero con **JOBS** como caso de contraste: cadena más dedicada (WL y DB propios, ya confirmados por nombre+IP), sin el enredo de WL compartido/migración a medio hacer que tiene CEFAS. La receta final debería salir de cruzar los dos, no de uno solo.

## Por qué JOBS

A diferencia de CEFAS, para JOBS **ya tenemos el dominio de entrada sin necesitar una sesión nueva** — apareció en el mismo CSV de `DOCKER-DEB` que ya se transcribió (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`). `jobsprod.condorwork.com.ar` apunta a `192.1.1.1:9001`, que es exactamente la IP de `WL12C-PROD`, el WebLogic que `inventory.json` ya tenía resuelto por nombre para JOBS — coincidencia limpia, sin ambigüedad.

## El camino, capa por capa

| # | Capa | Estado (19 ago 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | **Ya encontrado, sin sesión nueva:** `jobsprod.condorwork.com.ar` → `192.1.1.1:9001` (dedicado). También existe `jobs.condorwork.com.ar` → `192.1.2.54:9001`, el WL compartido con ABB/Boca — dos rutas distintas para el mismo cliente, sin saber todavía cuál es la que usan los usuarios reales. | Confirmar cuál de las dos tiene tráfico real (ver capa 4a). |
| 2 | Nginx Proxy Manager | `DOCKER-DEB` (`192.1.1.37:81`) — ya recorrido entero, es de ahí que salió el dominio. | Ninguno — esta capa ya está resuelta para JOBS. |
| 3 | Firewall / NAT | **Resuelto, sin regla dedicada.** `FWOPEN` no tiene ninguna regla NAT hacia `192.1.1.1:9001` — `jobsprod.condorwork.com.ar` entra por el mismo camino que el resto del NPM de `DOCKER-DEB`: `200.55.243.94:80`/`443` → `192.1.1.37`, ruteado por Host header adentro del NPM (mismo patrón que `cefas.condorwork.com.ar` en el otro trazado). | Ninguno. |
| 4 | App — motor clásico | `WL12C-PROD` (`192.1.1.1`, Oracle Linux 7) — **dedicado**, no compartido como el `WebLogic.191` de CEFAS. La propia matriz ya marca una discrepancia sin cerrar: versión de WL `11` (técnico) vs `12` (funcional) — ver Discrepancias en `findings.md`. | Login a la consola (mismo cuidado: `soportesmart` puede estar rechazada). Ver versión real en la pantalla de login, y Data Sources para confirmar contra cuál DB apunta hoy. |
| 5 | App — capa Docker/reportes | `jobsjasper.condorwork.com.ar` → `192.1.1.110:8098` (`OPENDOCKER01`) — instancia de Jasper dedicada, mismo patrón que `cefasjasper`/`cabjjasper` en el mismo host. A diferencia de CEFAS, no hay evidencia de contenedores "JOBS frontend/backend" dedicados en ningún host Docker — el patrón acá parece ser motor clásico + reportes, sin capa web propia. | Confirmar en Portainer/SSH de `OPENDOCKER01` si hay algo más de JOBS ahí aparte de Jasper. |
| 6 | Base de datos | `CLIENTES-DB2` (`192.1.1.51`, Oracle) — dedicada, confirmada por nombre, **y con NAT propio confirmado:** `FWOPEN` tiene una regla "acceso jobs" (`50555` → `192.1.1.51:1521`), restringida a un origen nombrado `JOBS_REDES_PUBLICAS` (no abierta a cualquiera). Hay otra igual para el ambiente de test (`50556` → `192.1.1.44:1521`, `Database .44 - Clientes TEST`). Migración pendiente hacia `10.77.7.13` / SID `prodjobs` según la matriz — **igual que el caso de CEFAS, esa IP todavía no resuelve a ninguna VM ni tiene regla NAT.** | `sqlplus` contra `192.1.1.51` (acceso interno, la regla NAT está restringida por origen) para confirmar SID/datasource real. Si `10.77.7.13` no existe todavía, puede que la migración de JOBS ni haya arrancado — a diferencia de CEFAS, que sí tiene su destino ya provisionado (`OPENDBPROD001`). |
| 7 | Ambientes no productivos, ya mapeados | `ords-jobsdev.open.com.ar` → `192.1.1.44:8080` (`Database .44 - Clientes TEST`, compartida) y `ords-jobst.open.com.ar` → `192.1.2.54:7002` (ORDS en el WL compartido). Da una vista rápida de dev/test sin necesitar credenciales nuevas. | Ninguno — ya está resuelto, dejarlo anotado para la receta final. |

## Al terminar

1. Completar `clients[].database.resolved` de JOBS en `infra/inventory.json` con el resultado real de la capa 6.
2. Resolver cuál de las dos rutas de la capa 1 (`jobsprod` dedicado vs `jobs` compartido) es la que usan los usuarios — puede que una sea legacy.
3. Cruzar esta receta con la de CEFAS (`plan_relevamiento_alta_cefas.md`) y escribir la versión generalizada en ambos archivos — qué es común a los dos (capas 1–3, típicamente) y qué varía por cliente (si tiene WL/Docker dedicado o compartido, si tiene migración pendiente).

## Receta generalizada (completar después de cruzar con CEFAS)

*(Vacío a propósito — se llena cuando los dos trazados converjan, no antes.)*
