# Relevamiento de alta de cliente — camino punta a punta (CEFAS de referencia)

**Objetivo:** entender qué infraestructura necesita un cliente, capa por capa — entrada (nginx), firewall/NAT, aplicación, base de datos, almacenamiento — recorriendo un cliente real (CEFAS) de punta a punta, para terminar con una receta reusable de alta de cliente. Los otros ítems de Tier 1 (Rex Argentina, EBY, ABB) siguen en `PLAN.md`, no acá.

**Uno de dos trazados en paralelo.** Ver también [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) — mismo objetivo, con JOBS como cliente de referencia (cadena más dedicada, sirve de contraste). La receta final debería convalidarse contra los dos.

## Hipótesis validada: dos tecnologías, y sí conviven — pero no como se pensaba

**Confirmado (19 ago 2026), vía la config real de NPM en `VM-DOCKER-Clientes`:** CEFAS corre en las dos capas al mismo tiempo, ambas habilitadas hoy:

- **Motor clásico — `cefas.condorwork.com.ar` → `WebLogic.191` (`192.1.1.191:80`).** Compartido con otros clientes (`sigo.open.com.ar`, `uia.condorenterprise.com.ar`, `yacyreta.condorwork.com.ar`/EBY — ver `findings.md`), pero CEFAS sí está ahí. El intento anterior de ver esto solo por el panel de `DOCKER-DEB` (que no tiene el dominio de CEFAS) llevó a la conclusión incorrecta de que CEFAS se había ido de esta VM — no es así, solo estaba en el NPM equivocado.
- **Capa Docker — `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` → `VM-DOCKER-Clientes` (`192.1.1.38`, contenedores `ss_front_cefas`/`ss_back_cefas`).** No es un reemplazo del motor clásico ni un "Work" genérico — es específicamente el producto **Self Service** (`matrix_detail.productos.Self Service: "Sí"` para CEFAS), con su propio Postgres (`ss_pg_cefas`).

**Dato de higiene encontrado de paso:** la imagen del contenedor `ss_pg_cefas` tiene el tag `yacyreta-sfd` (EBY), no `cefas-sfd` como sus vecinos — probable copia del compose de EBY reusada sin actualizar el tag. Mismo patrón de contaminación por copy-paste que ya se había visto en la columna `Notas` de `ExportList.csv`.

## El camino, capa por capa

| # | Capa | Estado (19 ago 2026) | Próximo paso |
|---|---|---|---|
| 1 | Dominio de entrada | **Resuelto.** `cefas.condorwork.com.ar` (motor clásico) y `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` (Self Service) — sacados de la tabla `proxy_host` real de la mariadb interna de NPM en `VM-DOCKER-Clientes`, vía SSH. | Ninguno. |
| 2 | Nginx Proxy Manager | **Resuelto.** El NPM real de CEFAS es el de `VM-DOCKER-Clientes` (`192.1.1.38`), no el de `DOCKER-DEB` — 9 proxy hosts totales, incluye también `roman.condorwork.com.ar`/`argocean.condorenterprise.com.ar` (deshabilitados, ver `findings.md`). | Ninguno. |
| 3 | Firewall / NAT | `FWOPEN` (`192.1.1.11`) — acceso confirmado. | Firewall → NAT → Port Forward, buscar reglas para `192.1.1.191:80` y `192.1.1.38` (los dos destinos reales del paso 1). |
| 4a | App — motor clásico | `WebLogic.191` (`192.1.1.191`). Sirve `cefas.condorwork.com.ar` por el puerto `80` — pero la consola de admin (`7001`) sigue dando connection refused, sin explicar todavía por qué (puerto distinto no cubierto por la regla NAT, o la consola simplemente no está expuesta). | Revisar en `FWOPEN` si hay NAT para el `7001` de esa IP. Con acceso a consola: Data Sources → URL JDBC, contra cuál DB apunta hoy. |
| 4b | App — capa Docker (Self Service) | `ss_front_cefas` (`self-service-angular:cefas-sfd`), `ss_back_cefas` (`self-service-backend:cefas-sfd`), `ss_pg_cefas` (Postgres propio, ver nota de arriba) — todos en `VM-DOCKER-Clientes`, confirmados por nombre real de contenedor. | Confirmar si `ss_back_cefas` habla con el Oracle de la capa 4a o solo con su Postgres propio — cierra del todo si las dos capas comparten datos o son independientes. |
| 5 | Base de datos | `CLIENTES-DB` (`192.1.1.32`) es la actual, SID en disputa (`CEFAS` vs `CEFASPDB`). Destino de migración: `OPENDBPROD001` (`10.77.7.11`), ya compartida con Heinlein. | `sqlplus / as sysdba` → `SELECT name FROM v$database;` en `OPENDBPROD001`. Cruzar contra el datasource del paso 4a. |
| 6 | Almacenamiento / object store | `VM-DOCKER-Clientes` monta un NFS externo sin identificar (blind spot abierto desde el primer relevamiento de Docker). La nota de migración de CEFAS menciona "revisar FSAL" — posible mismo hilo. | `mount` / `cat /etc/fstab` en `VM-DOCKER-Clientes`. Si resuelve, cierra también el blind spot. |

## Al terminar

1. Completar `clients[].database.resolved` / `matrix_detail.validacion_pendiente` de CEFAS en `infra/inventory.json` con el SID y servidor real confirmados.
2. Si se confirma el servidor NFS, sacarlo de `blind_spots` en `inventory.json` y mover la entrada a "Resueltos" en `findings.md`.
3. **Lo que de verdad importa:** una vez recorridas las 6 capas, escribir acá abajo la receta generalizada, cruzada con `plan_relevamiento_alta_jobs.md` — validada contra dos casos reales, no inferida de la documentación.

## Receta generalizada (completar después de cruzar con JOBS)

*(Vacío a propósito — se llena cuando los dos trazados converjan, no antes.)*
