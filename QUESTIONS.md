# Preguntas para el equipo saliente

**Solo vamos a tener una o dos reuniones con el equipo saliente (probablemente una sola).** Este archivo tiene que quedar acotado a lo que *solo ellos* pueden responder — decisiones, contactos, accesos, estado de negocio. Todo lo que se pueda verificar entrando a un host por TeamViewer se resuelve nosotros mismos y vive en [PLAN.md](PLAN.md), no acá. Antes de cada reunión, revisar esta lista de arriba hacia abajo: si el tiempo se corta, lo de más abajo queda para la próxima (si la hay).

**Alcance: solo on-premise.** Las preguntas sobre Azure/AWS se estacionaron en [`cloud-infra/questions-cloud.md`](cloud-infra/questions-cloud.md) — la infraestructura cloud quedó fuera del relevamiento actual (ver `cloud-infra/README.md`).

- **¿Cuál es el proceso real para dar de alta a un cliente nuevo?** No encontramos nada que lo documente, y no hay forma de reconstruirlo entrando a un host — es puramente institucional.
- **Confirmar el estado real de ABB y Arris/GIAR, y si hay un cronograma de retención/eliminación de sus datos.** La fuente es contradictoria: una nota informal en la matriz dice que están "de baja", pero el campo formal de estado en la misma planilla dice "Mantenimiento solamente" para ambos. Es una decisión de negocio, no algo que podamos resolver mirando un servidor.
- **Credencial para los hosts de base de datos Oracle (distinta de la de aplicación/middleware).** La cuenta compartida `soportesmart` entra por SSH a los hosts de app/middleware (`WebLogic.191`, `OPENWLPROD01`, `WL12C-Desarrollo`, `docker-deb`) pero fue **rechazada en los tres hosts de DB probados** durante el trazado de EBY (2 sep 2026): `192.1.1.90` (`Database .90`), `192.1.1.22` (`OPENDBPROD006`) y `10.77.7.15` (`OPENDBPROD005`). No parece un problema de configuración SSH (mismos ajustes de host key/KEX que sí funcionaron en otros hosts viejos) — es una cuenta distinta o un acceso no otorgado. Bloquea la capa 6 (base de datos) de `plan_relevamiento_alta_eby.md` y probablemente de cualquier cliente cuya DB no sea `CLIENTES-DB`/`CLIENTES-DB2` (las únicas dos a las que sí se pudo entrar, sin que quede documentado con qué cuenta).

## Resueltas

- **¿Qué es "Piedras"?** (18 ago 2026) Confirmado como sitio real con host ESXi propio (`192.168.100.4`) y subred `192.168.100.0/24`, vía sesión de TeamViewer activa ahí + `ExportList-Piedras-Full.csv` (15 VMs). Detalle en `infra/findings.md` y `infra/topology.md` §3.
