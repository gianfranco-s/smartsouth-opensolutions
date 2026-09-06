# Resumen — relevamiento de alta de cliente (CEFAS + JOBS + EBY + BOCA)

Vistazo conjunto de los cuatro trazados punta a punta. Detalle completo, evidencia y pasos en [`plan_relevamiento_alta_cefas.md`](plan_relevamiento_alta_cefas.md), [`plan_relevamiento_alta_jobs.md`](plan_relevamiento_alta_jobs.md), [`plan_relevamiento_alta_eby.md`](plan_relevamiento_alta_eby.md) y [`plan_relevamiento_alta_boca.md`](plan_relevamiento_alta_boca.md) — acá solo el estado.

## Panorama

| Capa | CEFAS | JOBS | EBY | BOCA |
|---|---|---|---|---|
| Dominio de entrada | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | 🟡 Casi cerrado sin sesión |
| Nginx Proxy Manager | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto |
| Firewall / NAT | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto | 🟡 Sin regla dedicada aparente |
| App — motor clásico (WebLogic) | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto (ruta `eby-prod`) | 🔴 Abierto — nunca accedido |
| App — capa Docker / reportes | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto — no aplica | 🟡 Identificada, sin verificar |
| Base de datos | ✅ Resuelto | ✅ Resuelto | ✅ Resuelto (ruta `eby-prod`) | 🟢 Cierre barato, host ya accesible |
| Almacenamiento / object store | ✅ Resuelto | *(no aplica a este cliente)* | ✅ Resuelto — no aplica | 🟡 Señal contradictoria a revisar |

**CEFAS y JOBS: trazados completos, 7/7.** **EBY: 6/7** — la única nota abierta es a qué cliente corresponde cada sesión en `Database .90`/`CDRADM`, la DB compartida de la ruta paralela `yacyreta` (no bloqueante, la ruta productiva real ya está confirmada de punta a punta). **BOCA: recién arrancado** (plan escrito, sin sesión nueva todavía) — elegido porque `WL12C-Desarrollo.2.54` es el último WebLogic multi-inquilino del parque sin acceder nunca, y una sola sesión ahí cierra de paso a ABB, y da evidencia para ESYOP/DCVIAJES según a qué DB apunte ABB.

## CEFAS

**Descubierto:**
- **Dominio de entrada** — dos rutas activas: `cefas.condorwork.com.ar` (motor clásico) y `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar` (Self Service).
- **Nginx Proxy Manager** — `VM-DOCKER-Clientes`, 9 proxy hosts, confirmado con acceso SSH real (no solo capturas).
- **Firewall / NAT** — `WAN1:80`/`443` → `192.1.1.38`. El dominio del motor clásico no tiene regla NAT propia, entra por el mismo camino vía Host header.
- **App — motor clásico** — `WebLogic.191` resultó ser **Oracle Forms & Reports 11g** (dominio `ClassicDomain`), no un WebLogic JavaEE genérico — compartido con al menos 7 clientes más (ver EBY abajo). El `connection refused` de la consola de admin quedó explicado: nunca tuvo NAT al puerto `7001`.
- **App — capa Docker (Self Service)** — `ss_back_cefas` solo tiene configurado `jdbc:postgresql://postgres:5432/selfservice` (su propio `ss_pg_cefas`); no habla con el Oracle del motor clásico. Las dos tecnologías conviven pero no comparten datos.
- **Base de datos — cuál usa hoy** — `netstat` en vivo en `WebLogic.191` confirma conexión activa a `192.1.1.32:1525` (`CLIENTES-DB`, la actual) y cero tráfico hacia `OPENDBPROD001` (destino de migración) — la migración de CEFAS todavía no cortó tráfico productivo.
- **Almacenamiento** — `VM-DOCKER-Clientes` monta por NFSv4 `192.1.1.191:/clientes/cefas/cdr2/condorlink` (el `uploadPath` de Self Service) — el servidor NFS es el mismo `WebLogic.191`, no un storage separado.
- **Base de datos — SID confirmado** — acceso logrado a `CLIENTES-DB` (`192.1.1.32`), `SELECT name FROM v$database;` devolvió **`CEFAS`** (no `CEFASPDB`). Trazado completo, las 7 capas resueltas.

**Falta:** nada — trazado de CEFAS completo.

## JOBS

**Descubierto:**
- **Dominio de entrada** — las dos rutas (`jobsprod.condorwork.com.ar` dedicado, `jobs.condorwork.com.ar` compartido con ABB/Boca) están **vivas en simultáneo**, cada una con una población de usuarios distinta — no es dedicado-real/compartido-legacy, confirmado por access logs de NPM.
- **Nginx Proxy Manager** — `DOCKER-DEB`, ya recorrido entero.
- **Firewall / NAT** — sin regla dedicada, entra por el mismo NAT del NPM de `DOCKER-DEB`.
- **App — motor clásico** — `WL12C-PROD` es Oracle Forms & Reports **12.2.1.4.0** (dominio `base_domain`, no `ClassicDomain`) — cierra la discrepancia WL 11/12 a favor del funcional. Managed servers identificados uno por uno (`AdminServer`, `WLS_FORMS1`, `WLS_REPORTS1`, `ORDS-Jobs`, `ORDS-Enerflex`, `ORDS-Open`), y su asignación a DB confirmada por PID (`sudo netstat -tnp`).
- **App — Docker/reportes** — `OPENDOCKER01` solo tiene `jasper-jobs-jasperreports-1` + su propia MariaDB — sin frontend/backend dedicado, a diferencia de CEFAS.
- **Base de datos** — `CLIENTES-DB2` (`192.1.1.51`) confirmada con NAT propio (restringido por origen), tráfico PID-a-PID verificado, y **SID exacto confirmado vía `tnsnames.ora`: `SERVICE_NAME=JOBS`**. Migración a `10.77.7.13`/`prodjobs` sigue sin VM ni NAT — tráfico productivo real sigue en `.51`.

**Falta:** nada — trazado de JOBS completo (7/7, sin capa de almacenamiento aplicable a este cliente).

## EBY

**Elegido por impacto, no por ser un caso limpio** — es el cliente que más infraestructura compartida toca de los 15 (destraba ~9 co-inquilinos). Resultó ser el trazado de mayor enredo real del parque.

**Descubierto:**
- **Dominio de entrada** — 10 proxy hosts reales en `DOCKER-DEB` (no 3-4 como se pensaba). Dos rutas Forms en **producción viva y concurrente**: `yacyreta.condorwork.com.ar` → `WebLogic.191` y `eby-prod.condorwork.com.ar` → `OPENWLPROD01` — ~1.5M requests cada una, mismo día. No es dedicado-vivo/compartido-legacy: **son dos stacks completos en paralelo**.
- **App — motor clásico** — confirmado para la ruta `eby-prod`: `OPENWLPROD01` es Forms & Reports 12.2.1 (`base_domain`), con 3 ambientes reales dedicados (`ebyprod`/`ebyqa`/`ebyaudit`, archivos `.env` + secciones de `formsweb.cfg` con sus `.fmx`). La ruta `yacyreta` (`WebLogic.191`, 11g) quedó sin poder leer su config específica por falta de sudo — no bloqueante.
- **Base de datos** — cerrada para la ruta `eby-prod`: `tnsnames.ora` real de `OPENWLPROD01` confirma alias `EBYPROD`/`EBYQA`/`EBYAUDIT` → `OPENDBPROD005` (`10.77.7.15`), coincide letra por letra con la matriz. La ruta `yacyreta` usa `Database .90`/`CDRADM`, una DB **compartida** (confirmado por `sqlplus` con credencial nueva) entre varios tenants de `WebLogic.191` — no exclusiva de EBY, nota abierta no bloqueante.
- **Almacenamiento y capa Docker** — ambos resueltos como "no aplica": sin mount NFS dedicado, sin instancia Jasper para EBY (a diferencia de CEFAS/JOBS/BOCA que sí tienen la suya).
- **Rédito colateral** — el mismo trazado (vía re-dump de NPM + `tnsnames.ora`) destrabó infraestructura nueva para **ROMAN** (WL y DB candidatos, primera vez con datos reales), **GIAR** (segunda DB candidata), **Rex Argentina** (primera DB jamás mapeada) y **Heinlein** (ambiente de test confirmado) — ninguno verificado en vivo todavía.

**Falta:** nada bloqueante. Nota abierta, no crítica: a qué cliente corresponde cada sesión activa en `Database .90`/`CDRADM` (ruta `yacyreta`).

## BOCA

**Cuarto trazado, elegido por impacto — no por ser complejo (al contrario).** Cadena más simple que queda (un WL, una DB, ya resueltos por nombre), pero tracearlo obliga a entrar por primera vez a `192.1.2.54` (`WL12C-Desarrollo`), el último WebLogic multi-inquilino sin acceder nunca — cierra de paso a **ABB** (Tier 1 #4) y da evidencia para **ESYOP**/**DCVIAJES** según a qué DB apunte ABB.

**Estado de partida:** dominio (4 proxy hosts en `DOCKER-DEB`) y NPM ya identificados sin sesión nueva. DB (`CLIENTES-DB`, `192.1.1.32`) ya es accesible — mismo host de CEFAS, con `ora_pmon_BOCA` ya visto corriendo ahí desde el 25 ago. Jasper (`cabjjasper`) ya localizado en `OPENDOCKER01`. Lo único genuinamente nuevo es el box `192.1.2.54`.

**Falta:** todo lo que depende de la sesión en `192.1.2.54` (capa 4, y de paso la clasificación fina de capas 1/3/5/7) y reconectar a `CLIENTES-DB` para el `SELECT` que cierra el SID (`BOCA` vs `BOCAPDB`) — ver `plan_relevamiento_alta_boca.md` para el detalle paso a paso.
