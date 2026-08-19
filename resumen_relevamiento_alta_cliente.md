# Resumen — relevamiento de alta de cliente (CEFAS + JOBS)

Vistazo conjunto de los dos trazados punta a punta. Detalle completo, evidencia y pasos en [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md) y [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) — acá solo el estado.

## Panorama

| Capa | CEFAS | JOBS |
|---|---|---|
| Dominio de entrada | ✅ Resuelto | ✅ Resuelto |
| Nginx Proxy Manager | ✅ Resuelto | ✅ Resuelto |
| Firewall / NAT | ✅ Resuelto | ✅ Resuelto |
| App — motor clásico (WebLogic) | ✅ Resuelto | 🔍 Relevando |
| App — capa Docker / reportes | 🔍 Relevando | 🔍 Relevando |
| Base de datos | 🔍 Relevando | 🔍 Relevando |
| Almacenamiento / object store | 🔍 Relevando | *(sin evidencia todavía de que aplique)* |

Las tres primeras capas de los dos clientes se resolvieron sin sesión nueva, solo cruzando NPM + reglas NAT ya relevadas. Lo que falta en ambos necesita acceso de adentro (consola WebLogic, Portainer/SSH, `sqlplus`) — ninguna de las dos capas de aplicación/DB se puede cerrar solo con documentación.

## CEFAS

**Descubierto:**
- **Dominio de entrada** — dos rutas activas: `cefas.condorwork.com.ar` (motor clásico) y `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` (Self Service).
- **Nginx Proxy Manager** — `VM-DOCKER-Clientes`, 9 proxy hosts, confirmado con acceso SSH real (no solo capturas).
- **Firewall / NAT** — `WAN1:80`/`443` → `192.1.1.38`. El dominio del motor clásico no tiene regla NAT propia, entra por el mismo camino vía Host header.
- **App — motor clásico** — `WebLogic.191`, compartido con al menos 5 clientes más. El `connection refused` de la consola de admin quedó explicado: nunca tuvo NAT al puerto `7001`.

**Falta:**
- **Capa 4b (App — Self Service)** — relevando: si `ss_back_cefas` habla con el Oracle del motor clásico o solo con su Postgres propio (`ss_pg_cefas`).
- **Capa 5 (Base de datos)** — relevando: SID real en `OPENDBPROD001` (destino de migración) vs `CLIENTES-DB` (actual, acceso externo ya confirmado por el puerto `1525`).
- **Capa 6 (Almacenamiento)** — relevando: identificar el servidor NFS que monta `VM-DOCKER-Clientes`.

## JOBS

**Descubierto:**
- **Dominio de entrada** — dos rutas: `jobsprod.condorwork.com.ar` (dedicado) y `jobs.condorwork.com.ar` (compartido con ABB/Boca) — sin saber todavía cuál es la real.
- **Nginx Proxy Manager** — `DOCKER-DEB`, ya recorrido entero.
- **Firewall / NAT** — sin regla dedicada, entra por el mismo NAT del NPM de `DOCKER-DEB`.
- **Ambientes no productivos** — dev/test ya mapeados (`Database .44`, WL compartido) sin necesitar credenciales nuevas.

**Falta:**
- **Capa 4 (App — motor clásico)** — relevando: `WL12C-PROD`, confirmar versión real (discrepancia `11` vs `12`) y a qué DB apunta el datasource.
- **Capa 5 (App — Docker/reportes)** — relevando: confirmar en `OPENDOCKER01` si hay algo de JOBS más allá de Jasper.
- **Capa 6 (Base de datos)** — relevando: `CLIENTES-DB2` tiene NAT pero restringido por origen; confirmar SID real y si la migración a `10.77.7.13` arrancó.
