# Preguntas para el equipo saliente

Cosas que necesitamos que otra persona responda — el equipo saliente de Open Solutions/Smart South, o el cliente — en lugar de cosas que podemos resolver siguiendo con la investigación nosotros mismos. Agrupadas por tema; cada una enlaza a de dónde salió la pregunta. Actualizar este archivo a medida que se respondan las preguntas (mover a una sección "Resueltas" con la respuesta y la fecha, no simplemente borrar).

## Proceso / transición

- **¿Cuál es el proceso real para dar de alta a un cliente nuevo?** No encontramos nada que documente esto. Rex Argentina se incorporó recientemente y en la matriz figura solo con una referencia a la base de datos, sin WebLogic dedicado — ¿es ese el patrón normal (los clientes nuevos comparten instancias de WL existentes), o la configuración de Rex está incompleta/es atípica?
- **¿Hay un relevamiento específico de firewalls en curso?** Uno de los emails reenviados (Alexis Lombardi, 22 jul) dice "lo mismo de los PF y firewall que tienen" — lo que sugiere que se planeaba un relevamiento similar para firewalls. ¿Existe ya?
- **¿Se terminó alguna vez el inventario de ruteo de dominios de Nginx Proxy Manager?** El mismo hilo de emails dice "me falta revisar los demás Nginx para ver si hay más servicios" — es decir, ni el equipo interno había mapeado en ese momento cada dominio → servidor/puerto interno. Si eso se terminó después, nos ahorraría reconstruirlo desde cero.
- **¿Quién es "Desarrollo" y cómo los contactamos?** El relevamiento de infraestructura Docker marca reiteradamente cosas como "debe validarse con Desarrollo" (despliegues duplicados de Nextcloud, instancias de JasperReports posiblemente obsoletas, si distintos stacks de compose siguen vigentes). Vamos a necesitar ese contacto para cerrar esos puntos.

## Estado de clientes y conflictos de datos

- **Confirmar el estado de baja de ABB y Arris/GIAR.** La matriz interna de clientes marca a ambos como "de baja", con sus bases de datos retenidas solo temporalmente. ¿Sigue siendo así, y hay un cronograma de retención/eliminación de esos datos que debamos conocer?
- **¿Qué VM aloja la base de datos de Rex Argentina?** La matriz solo la nombra como "REX Producción" — no está resuelta a una VM específica en el export de vCenter.
- **EBY (Entidad Binacional Yacyretá) — ¿cuál es el servidor de base de datos correcto?** El CSV de Relevamiento dice `DB_YACY.22` en `192.1.1.22`; esa IP hoy pertenece a una VM llamada `OPENDBPROD006`. ¿Se renombró, o la base real de EBY está en otro lado?
- **La propia hoja "Discrepancias" de la matriz de clientes tiene varios conflictos sin resolver entre sus dos fuentes de datos** — vale la pena una revisión rápida con quien pueda resolverlos con autoridad:
  - GIAR, ROMAN, JOBS: qué versión de WebLogic corre realmente (cada una tiene dos respuestas que se contradicen)
  - ABB: cuál de las dos IPs de base de datos es producción y cuál es secundaria/histórica
  - CEFAS, BOCA: qué SID está realmente en uso (`CEFASPDB` vs `CEFAS`, `BOCAPDB` vs `BOCA`)
  - EBY: ¿la migración de WebLogic a `10.77.7.201` está realmente hecha, o sigue en el `192.1.2.54` compartido?
  - Enerflex: ¿el charset es realmente `WE8ISO8859P15`, o es un error de tipeo?

## Infraestructura que no podemos resolver sin ayuda

- **~31 VMs coinciden con patrones de nombre de base de datos/WebLogic pero no están asociadas a ningún cliente documentado.** En lugar de recorrerlas todas una por una por TeamViewer, ¿alguien del equipo saliente ya sabe qué son? (Lista completa en `infra/findings.md`.)
- **¿Qué es el segundo host ESXi (`192.1.3.252`)** — ¿un sitio físico separado, un colo, o una máquina standalone en el mismo datacenter? Aloja un rango de IPs distinto al del cluster principal de 11 hosts.
- **Las 12 VMs `OPENINFRxx` no tienen ninguna señal en el nombre** — ¿alguien conoce su función de memoria antes de que dediquemos tiempo de TeamViewer a cada una?
- **Nomenclatura de `opendocker03` / `portalDM`** — Relevamiento lista `portalDM` con una IP que coincide con `OPENPORTAL01`; ¿es un alias conocido, o es algo distinto que se nos está escapando?

## Acceso y seguridad

- **¿Podemos conseguir cuentas reales en lugar de depender de TeamViewer + documentos reenviados?** — vCenter, y por separado el portal/CLI de Azure para el lado de AKS, agilizarían mucho la verificación de todo lo que está en `infra/findings.md`.
- **La planilla original de Relevamiento tenía una única contraseña de administrador compartida para las bases de datos de los 13 clientes, en texto plano.** ¿Hay un plan de rotación de credenciales como parte de esta transición? La quitamos de lo que estamos versionando, pero vale la pena señalar la práctica de fondo.
- **Las redes de producción y dev/test de Azure no tienen NSGs y cada una usa una única subred plana** (hallazgo del análisis interno de Azure, no algo que hayamos verificado nosotros). ¿Es un riesgo conocido y aceptado, o vale la pena reportarlo como hallazgo propio?

## Resueltas

_(ninguna todavía)_
