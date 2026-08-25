# Open Solutions — Mapa de infraestructura para la transición

Estamos tomando la infraestructura de un cliente nuevo (Open Solutions, el ecosistema de productos CONDOR) con muy poca documentación previa. Este repo es nuestro mapa compartido de lo que realmente hay. No hay acceso por API al lado on-premise — todo se releva a mano por TeamViewer — así que hay que tratarlo como un documento vivo, no como un export de una sola vez.

**Alcance actual: solo on-premise.** No estamos investigando activamente infraestructura en proveedores cloud (Azure/AWS) — lo que ya se había encontrado ahí quedó estacionado en [`cloud-infra/`](cloud-infra/README.md), separado del resto para no confundir lo activo con lo pausado.

## Por dónde empezar

1. Leer **[infra/findings.md](infra/findings.md)** — la lista priorizada de qué está confirmado, qué se descubrió recién, y qué verificar a continuación. Es la forma más rápida de ser útil.
2. Mirar por arriba **[infra/topology.md](infra/topology.md)** — el diagrama de qué cliente está en qué servidor WebLogic/DB.
3. **[infra/inventory.json](infra/inventory.json)** es la fuente de verdad de la que se genera todo lo demás — abrirlo si necesitás un detalle que los documentos de arriba no cubren.
4. **[CLAUDE.md](CLAUDE.md)** tiene el contexto completo de cómo se construyó esto y cómo extenderlo (escrito para trabajo asistido por IA, pero útil como contexto para cualquiera).

## Qué cubre esto

| Área | Fuente | Estado |
|---|---|---|
| VMs on-premise (129 en total, 12 hosts ESXi) | Export de vCenter | Verdad de base para "qué existe"; roles mayormente inferidos |
| 15 mapeos cliente → servidor de aplicación → DB | Relevamiento manual + una matriz interna de servicios por cliente | Sólido para estos 15; la propia matriz marca discrepancias sin resolver |
| Hosts Docker (9, incl. dónde corre Nginx Proxy Manager) | Relevamiento interno de Docker | Confirmado, con detalle a nivel contenedor |
| Firewall pfSense (7 de 9 candidatos) | Relevamiento manual con acceso real a cada dashboard, más 1 vía coincidencia de IP con un documento de Azure (ver `cloud-infra/`) | Confirmado para 7; quedan 2 sin verificar. El mismo relevamiento reveló que solo OpenVPN/UDP 2190 está expuesto a Internet — sin SSH/HTTP/HTTPS/admin pfSense expuestos |

Todo el material fuente — el export CSV crudo, la planilla armada a mano, dos emails internos, y documentos extraídos de un archivo adjunto — vive en `source-files/`. Es documentación interna de trabajo, no un hecho verificado; verificar cualquier cosa importante antes de actuar en base a ella.

## Vacíos conocidos (ver findings.md para el detalle)

- **El alta de un cliente nuevo no está documentada en ningún lado que hayamos encontrado.** Podemos inferir algo de forma a partir del alta reciente de Rex Argentina, pero no hay un procedimiento escrito — vale la pena preguntarle directamente al equipo saliente.
- **32 VMs con patrones de nombre de base de datos/WebLogic no están asociadas a ningún cliente conocido** (24 encendidas, 8 apagadas — las apagadas quedaron de menor prioridad) — podrían ser componentes extra de clientes que ya conocemos, copias de no-producción, o clientes genuinamente sin documentar. Necesita una pasada por TeamViewer para aclararlo.
- **La capa de ruteo de requests (qué dominio va a qué servidor/puerto interno) está incompleta** — ni el equipo interno que arrancó esto la había terminado. Así que rastrear "la app de un cliente está caída" hasta un servidor de DB/WL es rápido para los 15 clientes mapeados; rastrear "este dominio tira errores" hasta un destino de proxy específico, en general, todavía no.
- Dos de los 13 clientes originales (ABB, Arris/GIAR) tienen una nota informal en la matriz interna diciendo que ya están **dados de baja** — pero el campo formal de estado de esos mismos clientes, en la misma planilla, dice "Mantenimiento solamente". La fuente se contradice; confirmar con el equipo saliente antes de priorizar (o despriorizar) sus entornos.
- Se mencionó un sitio adicional llamado **"Piedras"**. Dos rastros independientes lo respaldan (una VM de backup con ese nombre, y un dashboard de firewall etiquetado "Open - Piedras" en un rango de IP que no aparece en ningún otro lado) pero ninguno lo confirma del todo — el dashboard no respondió durante el relevamiento.

## Cómo mantener esto actualizado

A medida que sesiones de TeamViewer confirmen o corrijan algo, editar `inventory.json` directamente y regenerar los diagramas Mermaid en `topology.md` a partir de ahí en vez de editarlos a mano — ver la sección "Cómo mantener esto actualizado" en `CLAUDE.md` para el enfoque exacto. Mover los ítems resueltos fuera de `findings.md` a medida que se confirman para que siga siendo una lista útil en vez de acumular preguntas viejas.

## Seguridad

Este es un repo **privado** — contiene nombres de clientes, IPs internas y (en `source-files/`) correspondencia interna real. Mantenerlo privado, y nunca commitear credenciales de ningún tipo — la planilla original de Relevamiento tenía una contraseña de admin en texto plano que se quitó antes de versionarla acá.


## Notas adicionales
Para conectarse por ssh a servers más viejos como WebLogic.191
```
ssh -oHostKeyAlgorithms=+ssh-rsa soportesmart@192.1.1.191
´´´
