# Preguntas para el equipo saliente

**Solo vamos a tener una o dos reuniones con el equipo saliente (probablemente una sola).** Este archivo tiene que quedar acotado a lo que *solo ellos* pueden responder — decisiones, contactos, accesos, estado de negocio. Todo lo que se pueda verificar entrando a un host por TeamViewer se resuelve nosotros mismos y vive en [PLAN.md](PLAN.md), no acá. Antes de cada reunión, revisar esta lista de arriba hacia abajo: si el tiempo se corta, lo de más abajo queda para la próxima (si la hay).

**Alcance: solo on-premise.** Las preguntas sobre Azure/AWS se estacionaron en [`cloud-infra/questions-cloud.md`](cloud-infra/questions-cloud.md) — la infraestructura cloud quedó fuera del relevamiento actual (ver `cloud-infra/README.md`).

- **¿Cuál es el proceso real para dar de alta a un cliente nuevo?** No encontramos nada que lo documente, y no hay forma de reconstruirlo entrando a un host — es puramente institucional.
- **Confirmar el estado real de ABB y Arris/GIAR, y si hay un cronograma de retención/eliminación de sus datos.** La fuente es contradictoria: una nota informal en la matriz dice que están "de baja", pero el campo formal de estado en la misma planilla dice "Mantenimiento solamente" para ambos. Es una decisión de negocio, no algo que podamos resolver mirando un servidor.
- **¿Qué es "Piedras"?** Ya no es solo un comentario verbal: el relevamiento de firewalls tiene una fila etiquetada "Open - Piedras" apuntando a `192.168.100.1` (un rango de IP que no aparece en ningún otro lado), pero ese dashboard no respondió durante el relevamiento. Vamos a intentar de nuevo por TeamViewer y revisar los destinos de replicación de `VEEAM-PIEDRAS` primero; preguntar solo si eso no aclara nada.

## Resueltas

_(ninguna todavía)_
