# Transición de infraestructura — plan

## Hecho

- Parseado el export de vCenter (`ExportList.csv`): 129 VMs, 12 hosts ESXi, cruzado por nombre/IP contra los 13 clientes conocidos del CSV manual de Relevamiento.
- Construido `infra/inventory.json` como fuente de verdad estructurada: cada VM etiquetada con una categoría inferida, enlaces cliente↔servidor resueltos (con discrepancias marcadas, no corregidas en silencio).
- Quitadas las credenciales en texto plano del CSV de Relevamiento antes de versionar nada; inicializado un repo git privado, commiteado, y configurado `origin` a `git@github.com:gianfranco-s/smartsouth-opensolutions.git` (todavía sin push).
- Incorporada una segunda fuente, más completa: dos emails internos reenviados más un adjunto RAR (extraído con `unar`, guardado como texto plano/JSON bajo `source-files/extracted/`) que contiene una matriz de servicios por cliente más completa, un relevamiento de infraestructura Docker, y un análisis de arquitectura Azure.
- A partir de ese material:
  - **Confirmado** que Nginx Proxy Manager corre como contenedor en 4 de los 9 hosts Docker (resuelve la pregunta de "dónde está nginx" — no es un host dedicado).
  - **Confirmado** que `OPENVPNFW01` es el firewall pfSense (matcheado vía la IP del peer de VPN de Azure) — 1 de 9 candidatos a firewall confirmado, 8 siguen siendo conjeturas.
  - **Descubiertos** 2 clientes más que no estaban en los 13 originales (Rex Argentina, Argocean).
  - **Descubierto** que 2 de los 13 clientes originales (ABB, Arris/GIAR) ya figuran dados de baja internamente.
  - Mapeado el plano aparte de Azure/AKS donde realmente corren Condor Work/Enterprise/ProvIA, y marcado un hallazgo de seguridad real encontrado ahí (red plana, sin NSGs).
- Escritos `infra/topology.md` (diagramas Mermaid generados), `infra/findings.md` (vacíos priorizados), `CLAUDE.md` (orientación técnica/para agentes), y `README.md` (onboarding humano).
- Cruzadas todas las IPs/dominios mencionados en el material fuente contra `inventory.json` para detectar infraestructura real que no estuviera mapeada. Encontrado: una VM de Azure standalone (`10.66.66.33`, ORDS Core — no estaba ni en vSphere ni en la sección `azure`), una mención sin detalle de infraestructura en AWS, y servidor(es) NFS sin identificar detrás de dos hosts Docker. Sumado todo a `inventory.json` → `azure.core_vm` / `blind_spots` y a `infra/findings.md`.
- Re-priorizada `QUESTIONS.md` asumiendo una sola reunión con el equipo saliente: todo lo verificable por TeamViewer se movió a los próximos pasos de acá abajo; QUESTIONS.md quedó acotada a lo que solo el equipo saliente puede responder.
- **Acotado el alcance a on-premise.** Se decidió no seguir investigando activamente infraestructura en proveedores cloud (Azure/AWS) por ahora. Todo lo relacionado (sección `azure` de inventory.json, el diagrama Azure/AKS, los hallazgos y preguntas sobre la VM Core/AWS/segmentación de red) se movió a `cloud-infra/` — ver `cloud-infra/README.md` para cómo retomarlo si hace falta.
- Agregado "Piedras" como pregunta abierta: se mencionó verbalmente como sitio adicional, pero el único rastro técnico (`VEEAM-PIEDRAS`) está dentro del cluster principal, no en un sitio aparte — no coincide con lo esperado, así que queda como algo a verificar, no a dar por cierto.

## Próximos pasos

**Contexto clave: probablemente tengamos una sola reunión con el equipo saliente.** Todo lo que se pueda resolver entrando a un host por TeamViewer nosotros mismos va acá, no en QUESTIONS.md — esa lista queda reservada para lo que solo ellos pueden responder (decisiones de negocio, contactos, accesos). Ver `infra/findings.md` para el detalle completo de cada punto.

### A resolver nosotros mismos, por TeamViewer (no requiere al equipo saliente)

1. **Verificar cada ítem de la hoja "Discrepancias" de la matriz conectándonos directamente** en vez de esperar una respuesta: versión real de WebLogic en GIAR/ROMAN/JOBS (consola de administración o archivo de dominio), cuál IP de DB es la productiva en ABB, SID real en uso en CEFAS y BOCA, si el WL de EBY ya migró a `10.77.7.201` o sigue en el compartido, y si el charset de Enerflex es realmente `WE8ISO8859P15`.
2. **Resolver la identidad de la VM de base de datos de Rex Argentina** buscando un schema/SID "REX" en los servidores de base de datos accesibles.
3. **Resolver si `OPENDBPROD006` es realmente la base de EBY** — conectarse y comparar el SID contra lo esperado (`MBA` actual / `EBYPROD` destino, según la matriz).
4. **Identificar el/los servidor(es) NFS** que montan `OPENDOCKER.57` y `VM-DOCKER-Clientes` — correr `mount` o revisar `/etc/fstab` en esos dos hosts.
5. **Clasificar las ~31 VMs con patrón WL/DB sin mapear** — para cada una, determinar: componente de un cliente conocido, copia de no-producción, o cliente genuinamente sin documentar (así se encontró Argocean, así que puede haber más).
6. **Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`)** — sin ninguna señal en el nombre, hay que entrar a mirar.
7. **Verificar los 8 candidatos a firewall restantes** ahora que uno ya está confirmado como pfsense — pueden compartir configuración/patrones de acceso.
8. **Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`** — la conjetura anterior de que eran nginx resultó incorrecta; rol real todavía desconocido. De paso, confirmar si `portalDM` es un alias de `OPENPORTAL01` (mismo IP).
9. **Construir el mapa dominio → host proxy → servidor/puerto interno** a partir de las 4 instancias confirmadas de Nginx Proxy Manager y las reglas NAT de `pfsense` — no hace falta esperar a que el equipo saliente lo termine, lo podemos armar entrando a cada instancia.
10. **Investigar de forma pasiva si el segundo host ESXi (`192.1.3.252`) es un sitio separado** (ruteo, IPs públicas asociadas) antes de gastar tiempo de reunión en la pregunta.
11. **Revisar los jobs de backup de `VEEAM-PIEDRAS`** (repositorios, destinos de replicación) para ver si confirman un sitio adicional real detrás del nombre "Piedras", antes de preguntarlo en la reunión.

### Requiere al equipo saliente

Ver [QUESTIONS.md](QUESTIONS.md) — el acceso a cuentas reales de vCenter, el proceso de alta de clientes, y el estado de baja de ABB/GIAR son las prioridades altas para la única reunión que probablemente tengamos. Las preguntas sobre cloud (VM Core de Azure, AWS) quedaron estacionadas en `cloud-infra/questions-cloud.md`, fuera del alcance actual.
