# Informe infraestructura on-premise Open Solutions

Este documento resume el estado del relevamiento de infraestructura on-premise: el panorama general de sitios y clientes, los sistemas identificados como en desuso o candidatos a darse de baja, el estado real de las migraciones de base de datos en curso, y qué recursos podrían moverse a otro datacenter frente a las dificultades que implicaría ese traslado. Fuente: `infra/inventory.json` y `infra/findings.md`.

## Relevamiento general  TI

- **Tres sitios distintos**:
  * sitio principal (129 VMs), a su vez dividido en el cluster ESXi de 11 hosts (113 VMs, rango `192.1.1.x`) y un host standalone sin identificar (`192.1.3.252`, 16 VMs — aloja GIAR y ROMAN, visto en el campo "host ESXi" de export de vSphere)
  * el sitio físico "Piedras" (oficina separada, subred `192.168.100.x`, 15 VMs propias, host ESXi también separado).

- **15 clientes identificados**: Varios comparten la misma VM de aplicación o de base de datos. Por ejemplo `WebLogic.191` sirve a **8 clientes distintos**. Cualquier cambio sobre una VM compartida tiene radio de impacto multi-cliente.
  * ABB S.A. (ABB) — *nota de baja en disputa, evidencia técnica sugiere activo*
  * Arris de Argentina S.A. (GIAR) — *nota de baja en disputa, evidencia técnica sugiere activo*
  * Cefas S.A. (CEFAS)
  * Club Atlético Boca Juniors (BOCA)
  * CSM Ciencia al Servicio del Movimiento S.A. (ROMAN)
  * DC Viajes y Turismo S.A. (DCVIAJES)
  * Dominique Val S.A. (DVAL)
  * Enerflex Solutions Argentina SRL (ENERFLEX)
  * Ente Servicios y Obras Públicas (ESYOP)
  * Entidad Binacional Yacyretá (EBY)
  * Jobs Servicios de Recursos Humanos SRL (JOBS)
  * Heinlein
  * Maipú
  * Rex Argentina
  * Argocean
  
- **Exposición a Internet:** el firewall de borde (pfSense `OPENVPNFW01`) expone únicamente OpenVPN. Un segundo firewall interno (`FWOPEN`) tiene al menos 19 reglas NAT activas hacia adentro, entre ellas una que expone la consola de administración de vCenter (`192.1.1.29:443`) directamente a Internet.

- **Sistemas en desuso o candidatos a desuso**: ver "Recursos candidatos a dar de baja" más abajo.

## Tecnologías

- **Sistemas operativos**: mix de Windows (estaciones/jumphosts) y Linux — motores WebLogic/Forms & Reports mayormente en Oracle Linux 7, con versiones sueltas de OL4 a OL8 y RHEL 5/6/7; hosts Docker en su mayoría Ubuntu genérico (versión "22.04" solo confirmada puntualmente en `OPENDOCKER03`), con 2 en CentOS 7 y 2 en Debian 10 — y FreeBSD en los firewalls pfSense.
- **Dispositivos de red**: 10 VMs con categoría pfSense en total (7 confirmadas y activas; de las 3 restantes, 2 están apagadas, una de ellas en Piedras) y 4 instancias de Nginx Proxy Manager, corriendo como contenedor sobre hosts Docker — no es hardware dedicado.
- **Ruteo**: Internet → pfSense de borde (solo OpenVPN expuesto) → pfSense interno (NAT hacia los NPM) → NPM (ruteo por dominio/Host header) → motor de aplicación (WebLogic / Oracle Forms & Reports, o contenedores Docker) → base de datos (Oracle para el motor clásico, Postgres propio para Self Service).

## Una aplicación "tipo" — caso CEFAS
Ciclo de vida de la información:

1. **Ingreso**: dominio público → pfSense `FWOPEN` (NAT `WAN1:80/443` → NPM).
2. **Ruteo**: NPM (`VM-DOCKER-Clientes`) resuelve por Host header a uno de dos caminos.
3. **Procesamiento**: motor clásico (Oracle Forms & Reports en `WebLogic.191`) o Self Service (contenedores Docker propios).
4. **Almacenamiento**: Oracle (`CLIENTES-DB`) para el motor clásico, Postgres propio (`ss_pg_cefas`) para Self Service.
5. **Archivos/"object store"**: no hay un object store separado — los uploads van por un mount NFS que expone el propio `WebLogic.191`, no un storage centralizado.


# Migración de sistemas a Datacenter Smart South

**Motivación:** mejorar la confiabilidad de los servidores, incrementar seguridad y documentación.

**Dificultades:** el obstáculo principal es lo que hoy se refleja como un crecimiento anárquico de las diferentes capas de aplicación, y su relación con los recursos de infraestructura.

## Recursos que se podrían migrar

- **JOBS**: motor WebLogic (`WL12C-PROD`) y base de datos (`CLIENTES-DB2`) resuelven como dedicados a este cliente, sin compartir instancia con otros — parecería el caso más limpio para migrar sin afectar a terceros, pero todavía no se confirmó si el tráfico real de producción pasa por ahí o por el dominio alternativo (`jobs.condorwork.com.ar`) que cae en el WebLogic compartido con ABB/Boca.
- **Capas Self Service (Docker)**: cada cliente que las usa tiene su propio set de contenedores con Postgres propio (ej. `ss_front_cefas`/`ss_back_cefas`/`ss_pg_cefas` de CEFAS), sin compartir datos con el motor clásico — se pueden mover como bloque, cliente por cliente.
- **Ambientes de test/dev ya mapeados** (ej. `Database .44` de JOBS) — para validar el proceso de migración antes de tocar producción.
- **Backups Veeam**: `OPENBK` recibe, según una nota de backup, también el respaldo de Piedras — más simple de reapuntar que migrar cada VM productiva por separado. Existe un segundo servidor Veeam (`VEEAM-PIEDRAS`, pese al nombre está en el sitio principal) cuyo rol no está confirmado.

## Dificultades de la migración

Considerando que ningún servicio se puede migrar sin conocer primero el total de recursos de infraestructura que utiliza.

Problemas puntuales:
- **VMs compartidas**: `WebLogic.191` sirve a 8 clientes distintos, `WL12C-Desarrollo.2.54` a varios más.
- **Storage no separado de la aplicación, al menos en CEFAS**: el mismo `WebLogic.191` hace de servidor NFS para Self Service de CEFAS — no se puede mover ese storage como bloque independiente de la VM de aplicación.
- **Migraciones de base de datos a medio camino**: CEFAS y JOBS ya tienen un destino de migración documentado, pero el tráfico productivo verificado en vivo sigue en la base vieja.
- **`CLIENTES-DB` es una instancia Oracle compartida**: el mismo host corre al menos tres bases (`CEFAS`, `BOCA`, y `wl12prod` — candidata a ser la de JOBS) — migrar la base de un cliente implica coordinar con las otras que viven en el mismo host físico.

## Recursos candidatos a dar de baja

- **OpenRepo**: nota en vSphere confirma que no se usa (reemplazado por git) — bajo riesgo, siempre que se confirme que el código relevante ya está en el repositorio git actual.
- **OPENWLCLI01**: clon apagado de `OPENWLPROD01`, dejado así a propósito según su propia nota — bajo riesgo, el original sigue en pie y en uso.
- **`PiedrasWL01`**: su propia nota lo marca como WebLogic de prueba/licencia, no productivo — candidato de bajo riesgo dentro del sitio Piedras.
- **ABB y GIAR — probablemente activos, no candidatos a baja**: una nota suelta de la matriz los marca "de baja", pero la evidencia técnica directa apunta en sentido contrario: el dominio de ABB (`abb.condorwork.com.ar`) figura `status: "Online"` en el NPM real de `DOCKER-DEB`, con SSL vigente y creado en 2022 (no un resabio reciente); la consola WebLogic de GIAR (`OPENWLPROD01`) respondió en vivo al acceder por TeamViewer, confirmando el proceso corriendo. Ambas bases siguen retenidas. No dar de baja ninguno sin confirmar antes con el negocio — pero la nota aislada pesa menos que el tráfico/proceso real observado.
- **12 VMs sin rol identificado** (`infra_generic_unclear`) y el resto del sitio Piedras (13 de 15 VMs apagadas): no dar de baja ninguna sin auditar primero — al no conocerse su función, no se puede descartar que retengan datos o cumplan un rol operativo no documentado.
- **33 VMs apagadas en el sitio principal** según `ExportList.csv`, de las cuales solo `OpenRepo` y `OPENWLCLI01` (arriba) tienen contexto suficiente para explicar por qué — el resto únicamente se muestran como apagadas en vSphere, sin auditar todavía. Detalle completo en [`vms_apagadas.md`](vms_apagadas.md).

## Preguntas
* ¿Tenemos acceso al código fuente de la aplicación principal?
* ¿Cuáles son los archivos de configuración utilizados para levantar un cliente? Sean yml genéricos, docker-compose, etc.
* ¿Cómo se gestionan las licencias de Oracle y WebLogic?
* ¿Cuáles son los acuerdos de nivel de servicio por cliente?
