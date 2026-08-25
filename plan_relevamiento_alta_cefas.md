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
| 3 | Firewall / NAT | **Resuelto.** Regla real en `FWOPEN`: `WAN1:80`/`WAN1:443` → `192.1.1.38` ("Proxy Nginx Manager WAN1") — es la ruta real de entrada de `cefas.condorlink.com.ar`/`cefasbk.condorlink.com.ar`. El otro dominio (`cefas.condorwork.com.ar` → `192.1.1.191:80`) no tiene NAT directo propio — llega vía el mismo `WAN1:80`, ruteado por Host header dentro del NPM de `VM-DOCKER-Clientes`, no por una regla de firewall aparte. Detalle completo (45 reglas, `FWOPEN-nat-rules/nat_rules.csv`) en `inventory.json` → `vms[FWOPEN].nat_rules` — de paso corrigió un hallazgo de seguridad que estaba mal (`findings.md`: la exposición a Internet no es mínima) y encontró 10 IPs del mismo segmento sin ningún rastro en ExportList.csv (`inventory.json` → `blind_spots`). | Ninguno. |
| 4a | App — motor clásico | **Resuelto (25 ago 2026), y corregido: no es WebLogic JavaEE genérico.** Acceso SSH real (con `HostKeyAlgorithms=+ssh-rsa`, el host solo ofrece host keys viejos). El proceso real es **Oracle Forms & Reports 11g** — dominio `ClassicDomain` (`/app/oracle/mid/user_projects/domains/ClassicDomain`), managed servers `WLS_FORMS`/`WLS_REPORTS` bajo `Oracle_FRHome1`. No usa datasources de WebLogic (`config/jdbc/*.xml`) — Forms conecta directo a Oracle vía TNS/EZConnect. El `connection refused` del `7001` sigue explicado igual que antes (sin NAT a ese puerto). | Ninguno. |
| 4b | App — capa Docker (Self Service) | **Resuelto (25 ago 2026).** `config.yml` de `ss_back_cefas` (`/usr/src/backend/config.yml` dentro del contenedor, acceso SSH+root real a `VM-DOCKER-Clientes`) solo tiene configurado `jdbc:postgresql://postgres:5432/selfservice` — el Postgres interno `ss_pg_cefas`. Ninguna referencia a Oracle, host, driver ni credencial del motor clásico en todo el archivo. Self Service es **completamente autónomo** del motor WebLogic/Oracle de CEFAS — las dos capas conviven pero no comparten datos. | Ninguno. |
| 5 | Base de datos | **Resuelto del todo (25 ago 2026).** `netstat -tn` en `WebLogic.191` ya había confirmado que CEFAS usa hoy `192.1.1.32:1525` (`CLIENTES-DB`), no `OPENDBPROD001` (destino de migración, sin tráfico). Acceso conseguido a `CLIENTES-DB` (bloqueador de credencial resuelto), `ps -ef \| grep pmon` mostró tres instancias corriendo en el mismo host: `ora_pmon_BOCA`, `ora_pmon_CEFAS`, `ora_pmon_wl12prod` (esta última, candidata fuerte a la DB de `WL12C-PROD`/JOBS — ver `plan_relevamiento_alta_jobs.md`). `sqlplus / as sysdba` con `ORACLE_SID=CEFAS` → `SELECT name FROM v$database;` confirmó **`CEFAS`** — cierra la disputa `CEFAS` vs `CEFASPDB` a favor de `CEFAS`. | Ninguno. |
| 6 | Almacenamiento / object store | **Resuelto (25 ago 2026).** `mount`/`cat /etc/fstab` en `VM-DOCKER-Clientes` confirma NFSv4: `192.1.1.191:/clientes/cefas/cdr2/condorlink` → `/home/open/cefaslink/archivos` (el `uploadPath` de `ss_back_cefas`). **El servidor NFS es `WebLogic.191` mismo** — no un storage separado. Coincide con el disco `/dev/mapper/cdr2-cdr2_data1` visto en el banner de uso de disco de esa VM (capa 4a). Cierra el blind spot NFS abierto desde el primer relevamiento de Docker. | Ninguno. |

## Al terminar

1. Completar `clients[].database.resolved` / `matrix_detail.validacion_pendiente` de CEFAS en `infra/inventory.json` con el SID y servidor real confirmados.
2. Si se confirma el servidor NFS, sacarlo de `blind_spots` en `inventory.json` y mover la entrada a "Resueltos" en `findings.md`.
3. **Lo que de verdad importa:** una vez recorridas las 6 capas, escribir acá abajo la receta generalizada, cruzada con `plan_relevamiento_alta_jobs.md` — validada contra dos casos reales, no inferida de la documentación.

## Receta generalizada (completar después de cruzar con JOBS)

*(Vacío a propósito — se llena cuando los dos trazados converjan, no antes.)*
