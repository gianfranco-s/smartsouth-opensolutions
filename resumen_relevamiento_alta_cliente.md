# Resumen — relevamiento de alta de cliente (CEFAS + JOBS)

Vistazo conjunto de los dos trazados punta a punta. Detalle completo, evidencia y pasos en [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md) y [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md) — acá solo el estado.

## Panorama

| Capa | CEFAS | JOBS |
|---|---|---|
| Dominio de entrada | ✅ Resuelto | ✅ Resuelto |
| Nginx Proxy Manager | ✅ Resuelto | ✅ Resuelto |
| Firewall / NAT | ✅ Resuelto | ✅ Resuelto |
| App — motor clásico (WebLogic) | ✅ Resuelto | 🔍 Relevando |
| App — capa Docker / reportes | ✅ Resuelto | 🔍 Relevando |
| Base de datos | 🔍 Relevando | 🔍 Relevando |
| Almacenamiento / object store | ✅ Resuelto | *(sin evidencia todavía de que aplique)* |

Las tres primeras capas de los dos clientes se resolvieron sin sesión nueva, solo cruzando NPM + reglas NAT ya relevadas. Lo que falta en ambos necesita acceso de adentro (consola WebLogic, Portainer/SSH, `sqlplus`) — ninguna de las dos capas de aplicación/DB se puede cerrar solo con documentación.

## CEFAS

**Descubierto:**
- **Dominio de entrada** — dos rutas activas: `cefas.condorwork.com.ar` (motor clásico) y `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` (Self Service).
- **Nginx Proxy Manager** — `VM-DOCKER-Clientes`, 9 proxy hosts, confirmado con acceso SSH real (no solo capturas).
- **Firewall / NAT** — `WAN1:80`/`443` → `192.1.1.38`. El dominio del motor clásico no tiene regla NAT propia, entra por el mismo camino vía Host header.
- **App — motor clásico** — `WebLogic.191` resultó ser **Oracle Forms & Reports 11g** (dominio `ClassicDomain`), no un WebLogic JavaEE genérico — compartido con al menos 5 clientes más. El `connection refused` de la consola de admin quedó explicado: nunca tuvo NAT al puerto `7001`.
- **App — capa Docker (Self Service)** — `ss_back_cefas` solo tiene configurado `jdbc:postgresql://postgres:5432/selfservice` (su propio `ss_pg_cefas`); no habla con el Oracle del motor clásico. Las dos tecnologías conviven pero no comparten datos.
- **Base de datos — cuál usa hoy** — `netstat` en vivo en `WebLogic.191` confirma conexión activa a `192.1.1.32:1525` (`CLIENTES-DB`, la actual) y cero tráfico hacia `OPENDBPROD001` (destino de migración) — la migración de CEFAS todavía no cortó tráfico productivo.
- **Almacenamiento** — `VM-DOCKER-Clientes` monta por NFSv4 `192.1.1.191:/clientes/cefas/cdr2/condorlink` (el `uploadPath` de Self Service) — el servidor NFS es el mismo `WebLogic.191`, no un storage separado.

**Falta:**
- **Capa 5 (Base de datos) — SID exacto** — 🔒 **bloqueado por credencial.** Ni SSH ni consola VMware/Veeam a `CLIENTES-DB` (`192.1.1.32`) aceptan acceso, ni la credencial que funciona en las otras VMs. Pendiente para la reunión con el equipo saliente (ver `infra/findings.md`).

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
