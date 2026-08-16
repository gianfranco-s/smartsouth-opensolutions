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

## Próximos pasos

Más o menos en orden de prioridad — ver `infra/findings.md` para el detalle completo de cada uno:

1. **Confirmar el estado de baja de ABB y Arris/GIAR** con el equipo saliente antes de bajarles prioridad a sus entornos — ese estado hoy sale de un solo documento interno, sin confirmar.
2. **Resolver la identidad de la VM de base de datos de Rex Argentina** — es un cliente de producción actual sin VM mapeada todavía.
3. **Conseguir del equipo saliente el proceso de alta de un cliente nuevo.** Nada de lo recopilado hasta ahora lo documenta; solo podemos inferir la forma a partir de un ejemplo reciente (Rex Argentina).
4. **Clasificar las ~31 VMs con patrón WL/DB sin mapear** — para cada una, determinar: componente de un cliente conocido, copia de no-producción, o cliente genuinamente sin documentar (así se encontró Argocean, así que puede haber más).
5. **Construir el mapa dominio → host proxy → servidor/puerto interno.** El equipo interno que arrancó esto tampoco lo había terminado — sin él, rastrear "el dominio X tira error" hasta un servidor es lento. Candidatos: las 4 instancias confirmadas de Nginx Proxy Manager, reglas NAT de `pfsense`.
6. **Verificar los 8 candidatos a firewall restantes** ahora que uno ya está confirmado como pfsense — pueden compartir configuración/patrones de acceso.
7. **Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`)** — sin ninguna señal en el nombre.
8. **Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`** — la conjetura anterior de que eran nginx resultó incorrecta; rol real todavía desconocido.
9. Reportar el vacío de segmentación de red en Azure (sin NSGs, subred plana) a quien tenga a cargo la postura de seguridad — independiente del trabajo de mapeo de infraestructura, vale la pena reportarlo por su cuenta.

## Decisiones pendientes (necesitan una respuesta, no más investigación)

Ver [QUESTIONS.md](QUESTIONS.md) — ahí vive la lista completa de preguntas para el equipo saliente, incluyendo el acceso a Azure/vCenter y el estado del relevamiento de firewalls.
