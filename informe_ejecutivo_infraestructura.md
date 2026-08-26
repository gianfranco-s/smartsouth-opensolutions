# Informe infraestructura on-premise Open Solutions

Este documento resume el estado del relevamiento de infraestructura on-premise: el panorama general de sitios y clientes, los sistemas identificados como en desuso o candidatos a darse de baja, el estado real de las migraciones de base de datos en curso, y qué recursos podrían moverse a otro datacenter frente a las dificultades que implicaría ese traslado. Fuente: `infra/inventory.json` y `infra/findings.md`.

## Relevamiento general  TI

- **Tres sitios distintos**:
  * el cluster principal (11 hosts ESXi, ~129 VMs, rango `192.1.1.x`)
  * el sitio físico "Piedras" (oficina separada, subred `192.168.100.x`, 15 VMs propias).
  * un host standalone sin identificar (`192.1.3.252`, aloja GIAR y ROMAN — visto en el campo "host ESXi" de export de vSphere)

- **15 clientes activos identificados**: Varios comparten la misma VM de aplicación o de base de datos. Por ejemplo `WebLogic.191` sirve a **8 clientes distintos**. Cualquier cambio sobre una VM compartida tiene radio de impacto multi-cliente.
  * ABB S.A. (ABB) — *dada de baja?*
  * Arris de Argentina S.A. (GIAR) — *dada de baja?*
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

- **Sistemas operativos**: mix de Windows (estaciones/jumphosts) y Linux (Oracle Linux 7 en motores WebLogic/Forms & Reports, Ubuntu 22.04 en hosts Docker) y FreeBSD (firewalls pfSense).
- **Dispositivos de red**: 9 firewalls pfSense (7 confirmados activos) y 4 instancias de Nginx Proxy Manager, corriendo como contenedor sobre hosts Docker — no es hardware dedicado.
- **Ruteo**: Internet → pfSense de borde (solo OpenVPN expuesto) → pfSense interno (NAT hacia los NPM) → NPM (ruteo por dominio/Host header) → motor de aplicación (WebLogic / Oracle Forms & Reports, o contenedores Docker) → base de datos Oracle.

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

- **JOBS**: motor WebLogic (`WL12C-PROD`) y base de datos (`CLIENTES-DB2`) son dedicados a este cliente, sin compartir instancia con otros — Parecería el caso más limpio para migrar sin afectar a terceros.
- **Sistemas autocontenidos**: en general basados en docker (ver sección de preguntas).
- **Ambientes de test/dev ya mapeados** (ej. `Database .44` de JOBS) — bajo riesgo, sirven para validar el proceso de migración antes de tocar producción.
- **Backups Veeam** (`OPENBK`, repositorio único que también recibe el backup de Piedras) — es un solo destino centralizado, más simple de reapuntar que migrar cada VM productiva por separado.

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
- **ABB y GIAR**: marcados "de baja" en una nota de la matriz, pero el campo formal de esa misma planilla dice "mantenimiento solamente" y ambas bases siguen retenidas — **alto riesgo de pérdida de información si se dan de baja sin resolver antes esa contradicción.**
- **12 VMs sin rol identificado** (`infra_generic_unclear`) y el resto del sitio Piedras (13 de 15 VMs apagadas): no dar de baja ninguna sin auditar primero — al no conocerse su función, no se puede descartar que retengan datos o cumplan un rol operativo no documentado.
- **33 VMs apagadas en el sitio principal** según `ExportList.csv`, de las cuales solo `OpenRepo` y `OPENWLCLI01` (arriba) tienen contexto suficiente para explicar por qué — el resto únicamente se muestran como apagadas en vSphere, sin auditar todavía. Detalle completo en [`vms_apagadas.md`](vms_apagadas.md).

## Preguntas
* ¿Tenemos acceso al código fuente de la aplicación principal?
* ¿Cuáles son los archivos de configuración utilizados para levantar un cliente? Sean yml genéricos, docker-compose, etc.
* ¿Cómo se gestionan las licencias de Oracle y WebLogic?
* ¿Cuáles son los acuerdos de nivel de servicio por cliente?
